from fastapi import APIRouter, HTTPException, Depends
import requests
from typing import Optional, List
from pydantic import BaseModel
from repositories.chromadb_repository  import document_service_dep
# New dependency injection imports
from core.dependencies import get_db, get_db_session, get_chat_repository
from repositories import ChatRepository
from services.evaluate_doc_service import EvaluationService
from models.agent import ComplianceAgent
from services.rag_service import RAGService
from services.llm_service import LLMService
from schemas import EvaluateRequest, EvaluateResponse
import os
from services.word_export_service import WordExportService
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
import logging 
from typing import Dict, Any
import uuid
import base64
import redis
from datetime import datetime

logger = logging.getLogger("DOC_GEN_API_LOGGER")
doc_gen_api_router = APIRouter(prefix="/doc_gen", tags=["doc_gen"])

class GenerateRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    use_rag:              bool                  = True
    top_k:                int                   = 5
    doc_title:            str                   = None
    pairwise_merge:       Optional[bool]        = False
    actor_models:         Optional[List[str]]   = None
    critic_model:         Optional[str]         = None
    coverage_strategy:    Optional[str]         = "rag_by_heading"  # rag_by_heading | full_document | hybrid
    max_actor_workers:    Optional[int]         = 4
    critic_batch_size:    Optional[int]         = 15
    critic_batch_char_cap: Optional[int]        = 8000
    sectioning_strategy:  Optional[str]         = "auto"   # auto | by_chunks | by_metadata | by_pages
    chunks_per_section:   Optional[int]         = 5

@doc_gen_api_router.post("/generate_documents")
async def generate_documents(
    req: GenerateRequest,
    doc_service: document_service_dep = Depends(document_service_dep)):
    logger.info("Received /generate_documents ⇒ %s", req)
    # Note: DocumentService.generate_test_plan is now used for document generation
    # The additional parameters in GenerateRequest are preserved for backward compatibility
    # but are not currently used by the underlying service
    docs = await run_in_threadpool(
        doc_service.generate_test_plan,
        req.source_collections,
        req.source_doc_ids,
        req.doc_title
    )
    return {"documents": docs}

class OptimizedTestPlanRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    doc_title:            Optional[str]         = "Comprehensive Test Plan"
    max_workers:          Optional[int]         = 4
    sectioning_strategy:  Optional[str]         = "auto"
    chunks_per_section:   Optional[int]         = 5

@doc_gen_api_router.post("/generate_optimized_test_plan")
async def generate_optimized_test_plan(
    req: OptimizedTestPlanRequest, 
    doc_service: document_service_dep = Depends(document_service_dep)):
    """
    Generate test plan using the new optimized multi-agent workflow:
    1. Extract rules/requirements per section with caching
    2. Generate test steps per section
    3. Consolidate into comprehensive test plan
    4. Critic review and approval
    5. O(log n) performance optimization
    """
    logger.info("Received /generate_optimized_test_plan ⇒ %s", req)
    
    try:
        docs = await run_in_threadpool(
            doc_service.generate_test_plan,
            req.source_collections,
            req.source_doc_ids,
            req.doc_title
        )
        return {"documents": docs}
    except Exception as e:
        logger.error(f"Error in optimized test plan generation: {e}")
        raise HTTPException(status_code=500, detail=f"Test plan generation failed: {str(e)}")
    
class PreviewRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    sectioning_strategy:  Optional[str]         = "auto"
    chunks_per_section:   Optional[int]         = 5
    use_rag:              Optional[bool]        = True
    top_k:                Optional[int]         = 5


@doc_gen_api_router.post("/preview-sections")
async def preview_sections(
    req: PreviewRequest,
    doc_service: document_service_dep = Depends(document_service_dep)):
    try:    
        sections = await run_in_threadpool(
            doc_service._extract_document_sections,
            req.source_collections,
            req.source_doc_ids,
            req.use_rag,
            req.top_k,
            req.sectioning_strategy,
            req.chunks_per_section,
        )
        names = list(sections.keys())
        return {"count": len(names), "section_names": names[:500]}
    except Exception as e:
        logger.error(f"Preview sections failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@doc_gen_api_router.get("/generated-documents")
async def get_generated_documents():
    """Get list of all generated documents from vector store"""
    try:
        # Query the generated_documents collection
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
        response = requests.get(
            f"{chroma_url}/documents",
            params={"collection_name": "generated_documents"},
            timeout=10
        )
        
        if response.status_code == 404:
            return {"documents": [], "message": "No generated documents found"}
        
        response.raise_for_status()
        data = response.json()
        
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        ids = data.get("ids", [])
        
        # Combine document info
        generated_docs = []
        for doc_id, content, metadata in zip(ids, documents, metadatas):
            generated_docs.append({
                "document_id": doc_id,
                "title": metadata.get("title", "Untitled"),
                "generated_at": metadata.get("generated_at", "Unknown"),
                "template_collection": metadata.get("template_collection", "Unknown"),
                "agent_ids": metadata.get("agent_ids", "[]"),
                "session_id": metadata.get("session_id", ""),
                "word_count": metadata.get("word_count", 0),
                "char_count": metadata.get("char_count", 0),
                "preview": content[:300] + "..." if len(content) > 300 else content
            })
        
        # Sort by generation date (newest first)
        generated_docs.sort(key=lambda x: x["generated_at"], reverse=True)
        
        return {
            "documents": generated_docs,
            "total_count": len(generated_docs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@doc_gen_api_router.post("/export-testplan-word")
async def export_testplan_word(
    payload: Dict[str, Any],
    word_export_service: WordExportService = Depends(WordExportService)):
    """
    Export a generated test plan (stored in ChromaDB) to a Word document.
    Body: {"document_id": str, "collection_name": str?}
    Defaults to collection 'generated_test_plan' if not provided.
    """
    try:
        document_id = payload.get("document_id")
        collection_name = payload.get("collection_name") or os.getenv("GENERATED_TESTPLAN_COLLECTION", "generated_test_plan")
        if not document_id:
            raise HTTPException(status_code=400, detail="document_id is required")

        # Fetch documents from Chroma and find the one we need
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
        resp = requests.get(f"{chroma_url}/documents", params={"collection_name": collection_name}, timeout=30)
        if not resp.ok:
            raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch collection: {resp.text}")
        data = resp.json()
        ids = data.get("ids", [])
        docs = data.get("documents", [])
        metas = data.get("metadatas", [])

        try:
            idx = ids.index(document_id)
        except ValueError:
            raise HTTPException(status_code=404, detail="Document not found in collection")

        content = docs[idx] or ""
        title = (metas[idx] or {}).get("title") or "Generated Test Plan"

        # Export using WordExportService
        word_bytes = word_export_service.export_markdown_to_word(title, content)
        b64 = base64.b64encode(word_bytes).decode("utf-8")
        filename = f"{title.replace(' ', '_')}.docx"
        return {"filename": filename, "content_b64": b64}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export test plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@doc_gen_api_router.get("/export-pipeline-word/{pipeline_id}")
async def export_pipeline_word(
    pipeline_id: str, 
    word_export_service: WordExportService = Depends(WordExportService)):
    """
    Export the final consolidated test plan for a given pipeline ID from Redis
    as a Word document (no Chroma dependency).
    """
    try:
        rhost = os.getenv("REDIS_HOST", "redis")
        rport = int(os.getenv("REDIS_PORT", 6379))
        rcli = redis.Redis(host=rhost, port=rport, decode_responses=True)

        key = f"pipeline:{pipeline_id}:final_result"
        if not rcli.exists(key):
            raise HTTPException(status_code=404, detail="Pipeline final result not found")

        final_data = rcli.hgetall(key)
        title = final_data.get("title") or "Generated Test Plan"
        markdown = final_data.get("consolidated_markdown") or ""
        if not markdown:
            raise HTTPException(status_code=400, detail="No consolidated content available to export")

        word_bytes = word_export_service.export_markdown_to_word(title, markdown)
        b64 = base64.b64encode(word_bytes).decode("utf-8")
        filename = f"{title.replace(' ', '_')}.docx"
        return {"filename": filename, "content_b64": b64}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@doc_gen_api_router.delete("/generated-documents/{document_id}")
async def delete_generated_document(document_id: str):
    """Delete a generated document from vector store"""
    try:
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")

        # Delete from ChromaDB
        payload = {
            "collection_name": "generated_documents",
            "ids": [document_id]
        }
        
        response = requests.post(
            f"{chroma_url}/documents/delete",
            json=payload,
            timeout=10
        )
        
        if response.ok:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete document: {response.text}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_evaluation_service() -> EvaluationService:
    """Dependency provider for EvaluationService"""
    return EvaluationService(
        rag=RAGService(),
        llm=LLMService()
    )

@doc_gen_api_router.post("/evaluate_doc", response_model=EvaluateResponse)
async def evaluate_doc(
    req: EvaluateRequest,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    db: Session = Depends(get_db),
    eval_service: EvaluationService = Depends(get_evaluation_service)):
    try:
        # generate a session_id so you can track history
        doc_session_id = str(uuid.uuid4())

        answer, rt_ms = eval_service.evaluate_document(
            document_id     = req.document_id,
            collection_name = req.collection_name,
            prompt          = req.prompt,
            top_k           = req.top_k,
            model_name      = req.model_name,
            session_id      = doc_session_id,
        )
        # Save chat history
        try:
            chat_repo.create_chat_entry(
                user_query=req.prompt,
                response=answer,
                model_used=req.model_name,
                collection_name=req.collection_name,
                query_type="rag",
                response_time_ms=rt_ms,
                session_id=doc_session_id
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to save evaluation history: {e}")
            db.rollback()

        return EvaluateResponse(
            document_id     = req.document_id,
            collection_name = req.collection_name,
            prompt          = req.prompt,
            model_name      = req.model_name,
            response        = answer,
            response_time_ms= rt_ms,
            session_id      = doc_session_id,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@doc_gen_api_router.post("/export-agents-word")
async def export_agents_to_word(
    agent_ids: List[int] = None,
    export_format: str = "detailed",
    word_export_service: WordExportService = Depends(WordExportService),
    db: Session = Depends(get_db_session)):
    """
    Export agent configurations to a Word document.
    
    Args:
        agent_ids: Optional list of specific agent IDs to export. If None, exports all agents.
        export_format: "summary" or "detailed" export format
    """
    try:
        # Get agents from database
        if agent_ids:
            agents_query = db.query(ComplianceAgent).filter(ComplianceAgent.id.in_(agent_ids))
        else:
            agents_query = db.query(ComplianceAgent).all()
        
        agents = agents_query.all() if hasattr(agents_query, 'all') else agents_query
        
        if not agents:
            raise HTTPException(status_code=404, detail="No agents found")
        
        # Convert to dict format for export
        agents_data = []
        for agent in agents:
            agents_data.append({
                "id": agent.id,
                "name": agent.name,
                "model_name": agent.model_name,
                "system_prompt": agent.system_prompt,
                "user_prompt_template": agent.user_prompt_template,
                "temperature": agent.temperature,
                "max_tokens": agent.max_tokens,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
                "created_by": agent.created_by,
                "is_active": agent.is_active,
                "total_queries": agent.total_queries,
                "avg_response_time_ms": agent.avg_response_time_ms,
                "success_rate": agent.success_rate,
                "chain_type": agent.chain_type
            })
        
        # Generate Word document
        word_bytes = word_export_service.export_agents_to_word(agents_data, export_format)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agents_export_{timestamp}.docx"
        
        # Return as base64 for frontend download
        word_b64 = base64.b64encode(word_bytes).decode('utf-8')
        
        return {
            "filename": filename,
            "content_b64": word_b64,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "agents_exported": len(agents_data),
            "export_format": export_format
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export agents to Word: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@doc_gen_api_router.post("/export-chat-history-word")
async def export_chat_history_to_word(
    session_id: Optional[str] = None,
    limit: int = 50,
    word_export_service: WordExportService = Depends(WordExportService),
    chat_repo: ChatRepository = Depends(get_chat_repository)
):
    """
    Export chat history to a Word document.

    Args:
        session_id: Optional session ID to filter by
        limit: Maximum number of chat records to export
    """
    try:
        # Query chat history
        chat_records = chat_repo.get_all(limit=limit, order_by="timestamp")

        if not chat_records:
            raise HTTPException(status_code=404, detail="No chat history found")
        
        # Convert to dict format
        chat_data = []
        for chat in chat_records:
            chat_data.append({
                "id": chat.id,
                "user_query": chat.user_query,
                "response": chat.response,
                "model_used": chat.model_used,
                "query_type": chat.query_type,
                "response_time_ms": chat.response_time_ms,
                "timestamp": chat.timestamp,
                "session_id": chat.session_id,
            })
        
        # Generate Word document
        word_bytes = word_export_service.export_chat_history_to_word(chat_data, session_id)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_suffix = f"_session_{session_id[:8]}" if session_id else ""
        filename = f"chat_history{session_suffix}_{timestamp}.docx"
        
        # Return as base64
        word_b64 = base64.b64encode(word_bytes).decode('utf-8')
        
        return {
            "filename": filename,
            "content_b64": word_b64,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "records_exported": len(chat_data),
            "session_filter": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export chat history to Word: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@doc_gen_api_router.post("/export-simulation-word")
async def export_agent_simulation_to_word(
    simulation_data: Dict[str, Any],
    word_export_service: WordExportService = Depends(WordExportService)):
    """
    Export agent simulation results to a Word document.
    
    Args:
        simulation_data: Dictionary containing simulation results
    """
    try:
        # Generate Word document
        word_bytes = word_export_service.export_agent_simulation_to_word(simulation_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = simulation_data.get('session_id', 'unknown')[:8]
        filename = f"agent_simulation_{session_id}_{timestamp}.docx"
        
        # Return as base64
        word_b64 = base64.b64encode(word_bytes).decode('utf-8')
        
        return {
            "filename": filename,
            "content_b64": word_b64,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "session_id": simulation_data.get('session_id'),
            "simulation_type": simulation_data.get('type', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Failed to export agent simulation to Word: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@doc_gen_api_router.post("/export-rag-assessment-word")
async def export_rag_assessment_to_word(
    assessment_data: Dict[str, Any],
    word_export_service: WordExportService = Depends(WordExportService)):
    """
    Export RAG assessment results to a Word document.
    
    Args:
        assessment_data: Dictionary containing RAG assessment results
    """
    try:
        # Generate Word document
        word_bytes = word_export_service.export_rag_assessment_to_word(assessment_data)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = assessment_data.get('performance_metrics', {}).get('session_id', 'unknown')[:8]
        filename = f"rag_assessment_{session_id}_{timestamp}.docx"
        
        # Return as base64
        word_b64 = base64.b64encode(word_bytes).decode('utf-8')
        
        return {
            "filename": filename,
            "content_b64": word_b64,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "session_id": assessment_data.get('performance_metrics', {}).get('session_id')
        }
        
    except Exception as e:
        logger.error(f"Failed to export RAG assessment to Word: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@doc_gen_api_router.post("/export-reconstructed-word")
async def export_reconstructed_document_to_word(
    reconstructed: Dict[str, Any],
    word_export_service: WordExportService = Depends(WordExportService)):
    """Export a reconstructed document (from ChromaDB) to a Word document using the central WordExportService."""
    try:
        word_bytes = word_export_service.export_reconstructed_document_to_word(reconstructed)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = reconstructed.get('document_name') or 'reconstructed_document'
        # sanitize filename
        safe_base = "".join(c for c in base if c.isalnum() or c in (' ', '_', '-')).strip() or 'reconstructed_document'
        filename = f"{safe_base}_{timestamp}.docx"
        word_b64 = base64.b64encode(word_bytes).decode('utf-8')
        return {
            "filename": filename,
            "content_b64": word_b64,
            "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
    except Exception as e:
        logger.error(f"Failed to export reconstructed document to Word: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@doc_gen_api_router.get("/export-word-demo")
async def word_export_demo():
    """
    Demo endpoint showing example usage of Word export capabilities.
    """
    return {
        "demo": "Word Export Service",
        "description": "Export agents, chat history, and simulation results to Word documents",
        "available_exports": [
            {
                "endpoint": "POST /doc_gen/export-agents-word",
                "description": "Export agent configurations",
                "parameters": {
                    "agent_ids": "Optional list of specific agent IDs",
                    "export_format": "summary or detailed"
                }
            },
            {
                "endpoint": "POST /doc_gen/export-chat-history-word",
                "description": "Export chat conversation history",
                "parameters": {
                    "session_id": "Optional session ID filter",
                    "limit": "Maximum records to export"
                }
            },
            {
                "endpoint": "POST /doc_gen/export-simulation-word",
                "description": "Export agent simulation results",
                "parameters": {
                    "simulation_data": "Complete simulation results dictionary"
                }
            },
            {
                "endpoint": "POST /doc_gen/export-rag-assessment-word",
                "description": "Export RAG assessment results",
                "parameters": {
                    "assessment_data": "Complete assessment results dictionary"
                }
            }
        ],
        "features": [
            "Professional Word document formatting",
            "Structured data presentation with tables",
            "Session-based organization",
            "Performance metrics inclusion",
            "Base64 encoding for easy frontend integration",
            "Automatic filename generation with timestamps"
        ],
        "example_usage": {
            "export_all_agents": {
                "endpoint": "POST /doc_gen/export-agents-word",
                "payload": {
                    "export_format": "detailed"
                }
            },
            "export_specific_session": {
                "endpoint": "POST /doc_gen/export-chat-history-word",
                "payload": {
                    "session_id": "abc123def456",
                    "limit": 25
                }
            }
        }
    }