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
from services.test_card_service import TestCardService
from services.markdown_sanitization_service import MarkdownSanitizationService
from services.pairwise_synthesis_service import PairwiseSynthesisService
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
import logging
from typing import Dict, Any
import uuid
import base64
import redis
from datetime import datetime
from schemas.test_card import (
    TestCardRequest,
    TestCardResponse,
    TestCardBatchRequest,
    TestCardBatchResponse,
    ExportTestPlanWithCardsRequest,
    ExportTestPlanWithCardsResponse,
)

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
    agent_set_id:         int                   = None  # Required agent set for orchestration

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
        req.doc_title,
        req.agent_set_id
    )
    return {"documents": docs}

class OptimizedTestPlanRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    doc_title:            Optional[str]         = "Comprehensive Test Plan"
    max_workers:          Optional[int]         = 4
    sectioning_strategy:  Optional[str]         = "auto"
    chunks_per_section:   Optional[int]         = 5
    agent_set_id:         int                   = None  # Required agent set for orchestration

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
            req.doc_title,
            req.agent_set_id
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

def get_test_card_service() -> TestCardService:
    """Dependency provider for TestCardService"""
    return TestCardService(llm_service=LLMService())

def get_word_export_service() -> WordExportService:
    """Dependency provider for WordExportService"""
    return WordExportService()

def get_pairwise_synthesis_service() -> PairwiseSynthesisService:
    """Dependency provider for PairwiseSynthesisService"""
    return PairwiseSynthesisService(llm_service=LLMService())

def get_redis_client() -> redis.Redis:
    """Dependency provider for Redis client"""
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

@doc_gen_api_router.post("/evaluate_doc", response_model=EvaluateResponse)
async def evaluate_doc(
    req: EvaluateRequest,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    db: Session = Depends(get_db),
    eval_service: EvaluationService = Depends(get_evaluation_service)):
    try:
        # generate a session_id so you can track history
        doc_session_id = str(uuid.uuid4())

        # Evaluate document with citation support
        answer, rt_ms, metadata_list, formatted_citations = eval_service.evaluate_document(
            document_id     = req.document_id,
            collection_name = req.collection_name,
            prompt          = req.prompt,
            top_k           = req.top_k,
            model_name      = req.model_name,
            session_id      = doc_session_id,
            include_citations = True,
        )

        # Combine answer with formatted citations for storage (same as chat)
        full_response = answer
        if formatted_citations:
            full_response = answer + "\n\n" + formatted_citations

        # Save chat history with citations included
        try:
            chat_repo.create_chat_entry(
                user_query=req.prompt,
                response=full_response,
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

        # Prepare citation data for response
        citations = []
        if metadata_list:
            for meta in metadata_list:
                # Extract citation information from metadata
                citation_data = {
                    "document_index": meta.get("document_index"),
                    "distance": meta.get("distance"),
                    "quality_tier": meta.get("quality_tier"),
                    "distance_explanation": meta.get("distance_explanation"),
                    "excerpt": meta.get("metadata", {}).get("text", meta.get("document_text", ""))[:500],  # First 500 chars
                    "source_file": meta.get("metadata", {}).get("document_name", ""),
                    "page_number": meta.get("metadata", {}).get("page_number"),
                    "section_name": meta.get("metadata", {}).get("section_title"),
                }
                citations.append(citation_data)

        return EvaluateResponse(
            document_id     = req.document_id,
            collection_name = req.collection_name,
            prompt          = req.prompt,
            model_name      = req.model_name,
            response        = answer,
            response_time_ms= rt_ms,
            session_id      = doc_session_id,
            citations       = citations if citations else None,
            formatted_citations = formatted_citations if formatted_citations else None,
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


# ============================================================================
# TEST CARD GENERATION ENDPOINTS (Phase 2)
# ============================================================================

@doc_gen_api_router.post("/generate-test-card", response_model=TestCardResponse)
async def generate_test_card(
    req: TestCardRequest,
    test_card_service: TestCardService = Depends(get_test_card_service)
):
    """
    Generate a test card from test rules markdown.

    Converts test procedures and rules into an executable test card with:
    - Test ID
    - Test Title
    - Step-by-step procedures
    - Expected results
    - Acceptance criteria
    - Pass/Fail tracking checkboxes

    Args:
        req: Test card request with section title and rules markdown

    Returns:
        Test card in requested format (markdown_table, json, or docx_table)

    Example:
        ```json
        {
            "section_title": "4.1 Power Supply Requirements",
            "rules_markdown": "## Requirements\n**Test Rules:**\n1. Verify voltage...",
            "format": "markdown_table"
        }
        ```
    """
    try:
        logger.info(f"Generating test card for section: {req.section_title}")

        test_card_content = await run_in_threadpool(
            test_card_service.generate_test_card_from_rules,
            section_title=req.section_title,
            rules_markdown=req.rules_markdown,
            format=req.format
        )

        # Count tests based on format
        test_count = 0
        if req.format == "markdown_table":
            # Count rows starting with | TC-
            test_count = len([line for line in test_card_content.split('\n')
                            if line.strip().startswith('| TC-')])
        elif req.format == "json":
            import json
            try:
                test_cards = json.loads(test_card_content)
                test_count = len(test_cards)
            except json.JSONDecodeError:
                test_count = 0

        logger.info(f"Generated {test_count} test cards for {req.section_title}")

        return TestCardResponse(
            section_title=req.section_title,
            test_card_content=test_card_content,
            format=req.format,
            test_count=test_count
        )

    except Exception as e:
        logger.error(f"Test card generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Test card generation failed: {str(e)}")


@doc_gen_api_router.post("/generate-test-cards-batch", response_model=TestCardBatchResponse)
async def generate_test_cards_batch(
    req: TestCardBatchRequest,
    test_card_service: TestCardService = Depends(get_test_card_service),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Generate test cards for multiple sections in a pipeline.

    Retrieves section data from Redis pipeline and generates test cards
    for all sections or a specified subset.

    Args:
        req: Batch request with pipeline ID and optional section filter

    Returns:
        Dictionary mapping section titles to test card content

    Example:
        ```json
        {
            "pipeline_id": "pipeline_abc123def456",
            "format": "markdown_table",
            "section_titles": ["Section 4.1", "Section 4.2"]  // optional
        }
        ```
    """
    try:
        logger.info(f"Generating test cards for pipeline: {req.pipeline_id}")

        # Generate test cards for all sections in pipeline
        test_cards = await run_in_threadpool(
            test_card_service.generate_test_cards_for_pipeline,
            pipeline_id=req.pipeline_id,
            redis_client=redis_client,
            format=req.format
        )

        # Filter by section titles if specified
        if req.section_titles:
            test_cards = {
                title: content
                for title, content in test_cards.items()
                if title in req.section_titles
            }

        # Count total tests
        total_tests = 0
        for content in test_cards.values():
            if req.format == "markdown_table":
                total_tests += len([line for line in content.split('\n')
                                  if line.strip().startswith('| TC-')])
            elif req.format == "json":
                import json
                try:
                    total_tests += len(json.loads(content))
                except json.JSONDecodeError:
                    pass

        logger.info(f"Generated test cards for {len(test_cards)} sections, {total_tests} total tests")

        return TestCardBatchResponse(
            pipeline_id=req.pipeline_id,
            test_cards=test_cards,
            total_sections=len(test_cards),
            total_tests=total_tests,
            format=req.format
        )

    except Exception as e:
        logger.error(f"Batch test card generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@doc_gen_api_router.post("/export-test-plan-with-cards", response_model=ExportTestPlanWithCardsResponse)
async def export_test_plan_with_cards(
    req: ExportTestPlanWithCardsRequest,
    test_card_service: TestCardService = Depends(get_test_card_service),
    word_export_service: WordExportService = Depends(get_word_export_service),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Export test plan with embedded test cards to Word document.

    Features:
    - Includes test card tables after each section
    - Supports Pandoc export (professional formatting with TOC)
    - Supports python-docx export (standard formatting)
    - Automatic markdown sanitization
    - Optional reference document for styling

    Args:
        req: Export request with pipeline ID and formatting options

    Returns:
        Word document as base64-encoded bytes with metadata

    Example:
        ```json
        {
            "pipeline_id": "pipeline_abc123def456",
            "include_test_cards": true,
            "export_format": "pandoc",
            "include_toc": true,
            "number_sections": true
        }
        ```
    """
    try:
        logger.info(f"Exporting test plan with cards: {req.pipeline_id}, format={req.export_format}")

        # Get test plan from Redis
        final_data = redis_client.hgetall(f"pipeline:{req.pipeline_id}:final_result")
        if not final_data:
            raise HTTPException(status_code=404, detail=f"Pipeline result not found: {req.pipeline_id}")

        title = final_data.get("title", "Test Plan")
        markdown = final_data.get("consolidated_markdown", "")

        if not markdown:
            raise HTTPException(status_code=404, detail="No markdown content found in pipeline")

        # Enhance markdown with test cards if requested
        if req.include_test_cards:
            logger.info("Adding test cards to markdown...")
            enhanced_markdown = await _add_test_cards_to_markdown(
                markdown=markdown,
                test_card_service=test_card_service,
                pipeline_id=req.pipeline_id,
                redis_client=redis_client
            )
        else:
            enhanced_markdown = markdown

        # Export based on format
        if req.export_format == "pandoc":
            logger.info("Exporting with Pandoc...")
            word_bytes = await run_in_threadpool(
                word_export_service.export_markdown_to_word_with_pandoc,
                title=title,
                markdown_content=enhanced_markdown,
                reference_docx=req.reference_docx,
                include_toc=req.include_toc,
                number_sections=req.number_sections
            )
        else:
            logger.info("Exporting with python-docx...")
            # Use existing export_markdown_to_word method if available
            # For now, we'll use Pandoc with fallback
            word_bytes = await run_in_threadpool(
                word_export_service.export_markdown_to_word_with_pandoc,
                title=title,
                markdown_content=enhanced_markdown,
                reference_docx=None,
                include_toc=False,
                number_sections=False
            )

        # Encode to base64
        b64 = base64.b64encode(word_bytes).decode("utf-8")

        # Generate filename
        safe_title = title.replace(' ', '_').replace('/', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_with_test_cards_{timestamp}.docx"

        logger.info(f"Export complete: {len(word_bytes)} bytes, filename={filename}")

        return ExportTestPlanWithCardsResponse(
            filename=filename,
            content_b64=b64,
            format=req.export_format,
            includes_test_cards=req.include_test_cards,
            file_size_bytes=len(word_bytes)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export with test cards failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# ============================ PAIRWISE SYNTHESIS ============================

class PairwiseSynthesisRequest(BaseModel):
    """Request for pairwise section synthesis"""
    pipeline_id: str
    synthesis_mode: str = "pairwise"  # "pairwise" or "consecutive"
    max_workers: int = 4

    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_id": "pipeline_abc123def456",
                "synthesis_mode": "pairwise",
                "max_workers": 4
            }
        }


class PairwiseSynthesisResponse(BaseModel):
    """Response from pairwise synthesis"""
    pipeline_id: str
    synthesis_mode: str
    original_sections: int
    synthesized_sections: int
    sections: Dict[str, str]  # section_title -> synthesized_content

    class Config:
        json_schema_extra = {
            "example": {
                "pipeline_id": "pipeline_abc123",
                "synthesis_mode": "pairwise",
                "original_sections": 10,
                "synthesized_sections": 5,
                "sections": {
                    "Section 4.1 & 4.2 Combined": "Synthesized content...",
                    "Section 4.3 & 4.4 Combined": "Synthesized content..."
                }
            }
        }


@doc_gen_api_router.post("/pairwise-synthesis", response_model=PairwiseSynthesisResponse)
async def pairwise_synthesis(
    req: PairwiseSynthesisRequest,
    pairwise_service: PairwiseSynthesisService = Depends(get_pairwise_synthesis_service),
    redis_client: redis.Redis = Depends(get_redis_client)
):
    """
    Apply pairwise synthesis to an existing pipeline's sections.

    This reduces redundancy by combining adjacent sections and identifying
    cross-section dependencies. Based on the notebook's approach.

    Synthesis Modes:
    - **pairwise**: Combine non-overlapping pairs (1+2, 3+4, 5+6...)
    - **consecutive**: Combine overlapping pairs (1+2, 2+3, 3+4...)

    Args:
        req: Pairwise synthesis request

    Returns:
        Synthesized sections

    Example:
        Original: 10 sections
        Pairwise mode: 5 combined sections
        Consecutive mode: 9 combined sections
    """
    try:
        logger.info(f"Starting pairwise synthesis for pipeline: {req.pipeline_id} (mode: {req.synthesis_mode})")

        # Synthesize sections from pipeline
        synthesized_sections = await run_in_threadpool(
            pairwise_service.synthesize_with_redis_pipeline,
            req.pipeline_id,
            redis_client,
            req.synthesis_mode,
            req.max_workers
        )

        if not synthesized_sections:
            logger.warning(f"No sections synthesized for pipeline: {req.pipeline_id}")
            raise HTTPException(
                status_code=404,
                detail=f"No sections found for pipeline or synthesis failed: {req.pipeline_id}"
            )

        # Count original sections
        pattern = f"pipeline:{req.pipeline_id}:critic:*"
        original_keys = redis_client.keys(pattern)
        original_count = len(original_keys)

        logger.info(f"Pairwise synthesis complete: {original_count} → {len(synthesized_sections)} sections")

        # Optionally: Store synthesized sections back to Redis with new keys
        # For now, just return them
        for section_title, content in synthesized_sections.items():
            # Store with pairwise prefix for retrieval
            key = f"pipeline:{req.pipeline_id}:pairwise:{section_title}"
            redis_client.hset(key, mapping={
                "section_title": section_title,
                "synthesized_content": content,
                "synthesis_mode": req.synthesis_mode,
                "timestamp": datetime.now().isoformat()
            })

        return PairwiseSynthesisResponse(
            pipeline_id=req.pipeline_id,
            synthesis_mode=req.synthesis_mode,
            original_sections=original_count,
            synthesized_sections=len(synthesized_sections),
            sections=synthesized_sections
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pairwise synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pairwise synthesis failed: {str(e)}")


async def _add_test_cards_to_markdown(
    markdown: str,
    test_card_service: TestCardService,
    pipeline_id: str,
    redis_client: redis.Redis
) -> str:
    """
    Add test card tables after each section in markdown.

    Strategy:
    1. Parse markdown to identify sections
    2. For each section, get critic result from Redis
    3. Generate test card from critic's synthesized rules
    4. Insert test card table after section

    Args:
        markdown: Original markdown content
        test_card_service: Test card service instance
        pipeline_id: Redis pipeline ID
        redis_client: Redis client instance

    Returns:
        Enhanced markdown with test cards inserted
    """
    try:
        # Get all section critic results from Redis
        pattern = f"pipeline:{pipeline_id}:critic:*"
        critic_keys = redis_client.keys(pattern)

        logger.info(f"Found {len(critic_keys)} critic sections for pipeline {pipeline_id}")

        sections_with_cards = {}
        for key in critic_keys:
            try:
                critic_data = redis_client.hgetall(key)
                section_title = critic_data.get("section_title", "")
                synthesized_rules = critic_data.get("synthesized_rules", "")

                if section_title and synthesized_rules:
                    # Generate test card
                    test_card = await run_in_threadpool(
                        test_card_service.generate_test_card_from_rules,
                        section_title=section_title,
                        rules_markdown=synthesized_rules,
                        format="markdown_table"
                    )
                    sections_with_cards[section_title] = test_card
                    logger.debug(f"Generated test card for: {section_title}")
            except Exception as e:
                logger.warning(f"Failed to generate test card for key {key}: {e}")
                continue

        if not sections_with_cards:
            logger.warning("No test cards generated, returning original markdown")
            return markdown

        # Insert test cards into markdown
        lines = markdown.split('\n')
        enhanced_lines = []
        current_section = None
        section_content_started = False

        for i, line in enumerate(lines):
            enhanced_lines.append(line)

            # Detect main section headers (## level)
            if line.startswith('## '):
                section_header = line[3:].strip()

                # If we just finished a section, insert its test card
                if current_section and current_section in sections_with_cards:
                    enhanced_lines.insert(-1, '\n### Test Card\n')
                    enhanced_lines.insert(-1, sections_with_cards[current_section])
                    enhanced_lines.insert(-1, '\n')

                current_section = section_header
                section_content_started = True

            # Check if this is the last line - insert test card for final section
            if i == len(lines) - 1 and current_section and current_section in sections_with_cards:
                enhanced_lines.append('\n### Test Card\n')
                enhanced_lines.append(sections_with_cards[current_section])
                enhanced_lines.append('\n')

        enhanced_markdown = '\n'.join(enhanced_lines)
        logger.info(f"Enhanced markdown: added {len(sections_with_cards)} test cards")

        return enhanced_markdown

    except Exception as e:
        logger.error(f"Failed to add test cards to markdown: {e}")
        # Return original markdown on error
        return markdown