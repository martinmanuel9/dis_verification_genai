import uuid
import os
import requests
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
import time
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from services.database import ComplianceAgent, DebateSession, ChatHistory, SessionLocal
from services.llm_service import LLMService
from services.agent_service import AgentService
from services.rag_service import RAGService 
from services.generate_docs_service import DocumentService
from services.evaluate_doc_service import EvaluationService
from services.rag_assessment_service import RAGAssessmentService
from services.word_export_service import WordExportService
from schemas.database_schema import (
    ComplianceCheckRequest,
    RAGCheckRequest,
    RAGDebateSequenceRequest,
    CreateAgentRequest,
    CreateAgentResponse,
    GetAgentsResponse,
    UpdateAgentRequest,
    UpdateAgentResponse,
    EvaluateRequest,
    EvaluateResponse,
    RAGAssessmentRequest,
    RAGAssessmentResponse,
    RAGAnalyticsRequest,
    RAGBenchmarkRequest,
    CollectionPerformanceRequest,
    RAGMetricsExportRequest
)
from langchain_core.messages import HumanMessage
from starlette.concurrency import run_in_threadpool
import base64
import redis


import logging
logger = logging.getLogger("FASTAPI_ROUTER")

router = APIRouter()

llm_service = LLMService()
rag_service = RAGService()
agent_service = AgentService()
rag_assessment_service = RAGAssessmentService(rag_service=rag_service, llm_service=llm_service)
word_export_service = WordExportService()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    query: str
    model: str
    use_rag: bool = False
    collection_name: Optional[str] = None


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Fixed chat endpoint that handles both OpenAI and Ollama responses."""
    try:
        session_id = str(uuid.uuid4())
        
        if request.use_rag and request.collection_name:
            # --- RAG mode: fetch docs via your RAGService, then run a retrieval chain
            start = time.time()
            answer, response_time = rag_service.process_query_with_rag(
                query_text=request.query,
                collection_name=request.collection_name,
                model_name=request.model,
            )
            
            print(f"RAG response in router: {answer} (took {response_time} ms)")
            
            # Save chat history
            try:
                history = ChatHistory(
                    user_query=request.query,
                    response=answer,
                    model_used=request.model,
                    query_type="rag",
                    response_time_ms=response_time,
                    langchain_used=True,
                    session_id=session_id
                )
                db.add(history)
                db.commit()
            except Exception as e:
                print(f"Failed to save chat history: {e}")
                db.rollback()
            
            return {
                "response": answer,
                "response_time_ms": response_time,
                "session_id": session_id,
                "type": "rag"
            }
        else:
            # Direct LLM mode
            start_time = time.time()
            llm = llm_service.get_llm_service(request.model)
            
            response = llm.invoke([HumanMessage(content=request.query)])
            
            # OllamaLLM returns string directly, ChatOpenAI returns object with .content
            if hasattr(response, 'content'):
                answer = response.content
            else:
                answer = response
                
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Save chat history
            try:
                history = ChatHistory(
                    user_query=request.query,
                    response=answer,
                    model_used=request.model,
                    query_type="direct",
                    response_time_ms=response_time_ms,
                    langchain_used=True,
                    session_id=session_id
                )
                db.add(history)
                db.commit()
            except Exception as e:
                print(f"Failed to save chat history: {e}")
                db.rollback()
            
            return {
                "response": answer,
                "response_time_ms": response_time_ms,
                "session_id": session_id,
                "type": "direct"
            }
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/chat-history")
def get_chat_history(db: Session = Depends(get_db)):
    records = db.query(ChatHistory).all()
    return [
        {
            "id": record.id,
            "user_query": record.user_query,
            "response": record.response,
            "timestamp": record.timestamp
        } for record in records
    ]

@router.post("/compliance-check")
async def compliance_check(request: ComplianceCheckRequest, db: Session = Depends(get_db)):
    try:
        result = agent_service.run_compliance_check(
            data_sample=request.data_sample,
            agent_ids=request.agent_ids,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generated-testplans")
async def list_generated_testplans(limit: int = Query(20, ge=1, le=200)):
    """List recent test plan runs indexed in Redis with basic metadata"""
    try:
        rhost = os.getenv("REDIS_HOST", "redis")
        rport = int(os.getenv("REDIS_PORT", 6379))
        rcli = redis.Redis(host=rhost, port=rport, decode_responses=True)
        ids = rcli.zrevrange("doc:recent", 0, limit - 1) or []
        results = []
        for doc_id in ids:
            meta = rcli.hgetall(f"doc:{doc_id}:meta") or {}
            section_count = rcli.scard(f"doc:{doc_id}:sections")
            results.append({
                "redis_document_id": doc_id,
                "title": meta.get("title", "Comprehensive Test Plan"),
                "collection": meta.get("collection"),
                "created_at": meta.get("created_at"),
                "completed_at": meta.get("completed_at"),
                "status": meta.get("status", "UNKNOWN"),
                "section_count": int(section_count) if section_count is not None else None,
                "total_testable_items": int(meta.get("total_testable_items", "0") or 0),
                "total_test_procedures": int(meta.get("total_test_procedures", "0") or 0),
                "generated_document_id": meta.get("generated_document_id")
            })
        return {"count": len(results), "runs": results}
    except Exception as e:
        logger.error(f"Failed to list generated test plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag-check")
async def rag_check(request: RAGCheckRequest, db: Session = Depends(get_db)):
    try:
        result = rag_service.run_rag_check( 
            query_text=request.query_text,
            collection_name=request.collection_name,
            agent_ids=request.agent_ids,
            db=db
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag-debate-sequence")
async def rag_debate_sequence(request: RAGDebateSequenceRequest, db: Session = Depends(get_db)):
    try:
        session_id, chain = rag_service.run_rag_debate_sequence(  
            db=db,
            session_id=request.session_id,
            agent_ids=request.agent_ids,
            query_text=request.query_text,
            collection_name=request.collection_name
        )
        return {"session_id": session_id, "debate_chain": chain}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-agent", response_model=CreateAgentResponse)
async def create_agent(request: CreateAgentRequest, db: Session = Depends(get_db)):
    """Create a new compliance agent"""
    try:
        # Check if agent name already exists
        existing_agent = db.query(ComplianceAgent).filter(
            ComplianceAgent.name == request.name
        ).first()
        
        if existing_agent:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent with name '{request.name}' already exists"
            )
        
        # Validate that user_prompt_template contains {data_sample}
        if "{data_sample}" not in request.user_prompt_template:
            raise HTTPException(
                status_code=400,
                detail="User prompt template must contain {data_sample} placeholder"
            )
        
        # Create new agent with only the fields that exist in your database
        new_agent = ComplianceAgent(
            name=request.name,
            model_name=request.model_name,
            system_prompt=request.system_prompt,
            user_prompt_template=request.user_prompt_template,
            temperature=getattr(request, 'temperature', 0.7),
            max_tokens=getattr(request, 'max_tokens', 300),
            created_by=getattr(request, 'created_by', 'streamlit'),
            is_active=True,
            total_queries=0,
            chain_type='basic',
            memory_enabled=False,
            tools_enabled={}
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        print(f"Agent created successfully: ID={new_agent.id}, Name={new_agent.name}")
        
        return CreateAgentResponse(
            message=f"Agent '{request.name}' created successfully",
            agent_id=new_agent.id,
            agent_name=new_agent.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating agent: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create agent: {str(e)}"
        )

@router.get("/get-agents", response_model=GetAgentsResponse)
async def get_agents(db: Session = Depends(get_db)):
    """Get all compliance agents"""
    try:
        agents = db.query(ComplianceAgent).all()
        
        # Convert agents to dict format
        agents_data = []
        for agent in agents:
            agent_dict = {
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
                "chain_type": agent.chain_type,
                "memory_enabled": agent.memory_enabled,
                "tools_enabled": agent.tools_enabled
            }
            agents_data.append(agent_dict)
        
        print(f"Retrieved {len(agents_data)} agents")
        
        return GetAgentsResponse(
            agents=agents_data,
            total_count=len(agents_data)
        )
        
    except Exception as e:
        print(f"Error getting agents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agents: {str(e)}"
        )

@router.put("/update-agent/{agent_id}", response_model=UpdateAgentResponse)
async def update_agent(agent_id: int, request: UpdateAgentRequest, db: Session = Depends(get_db)):
    """Update an existing compliance agent"""
    try:
        # Find the agent
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Track which fields are being updated
        updated_fields = []
        
        # Update only provided fields
        if request.name is not None:
            # Check if new name already exists (excluding current agent)
            existing_agent = db.query(ComplianceAgent).filter(
                ComplianceAgent.name == request.name,
                ComplianceAgent.id != agent_id
            ).first()
            
            if existing_agent:
                raise HTTPException(
                    status_code=400,
                    detail=f"Agent with name '{request.name}' already exists"
                )
            
            agent.name = request.name
            updated_fields.append("name")
        
        if request.model_name is not None:
            agent.model_name = request.model_name
            updated_fields.append("model_name")
        
        if request.system_prompt is not None:
            agent.system_prompt = request.system_prompt
            updated_fields.append("system_prompt")
        
        if request.user_prompt_template is not None:
            agent.user_prompt_template = request.user_prompt_template
            updated_fields.append("user_prompt_template")
        
        if request.temperature is not None:
            agent.temperature = request.temperature
            updated_fields.append("temperature")
        
        if request.max_tokens is not None:
            agent.max_tokens = request.max_tokens
            updated_fields.append("max_tokens")
        
        if request.is_active is not None:
            agent.is_active = request.is_active
            updated_fields.append("is_active")
        
        # Update the updated_at timestamp
        agent.updated_at = datetime.now(timezone.utc)
        updated_fields.append("updated_at")
        
        db.commit()
        db.refresh(agent)
        
        print(f"Agent updated successfully: ID={agent.id}, Name={agent.name}, Updated fields={updated_fields}")
        
        return UpdateAgentResponse(
            message=f"Agent '{agent.name}' updated successfully",
            agent_id=agent.id,
            agent_name=agent.name,
            updated_fields=updated_fields
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating agent: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent: {str(e)}"
        )

@router.get("/get-agent/{agent_id}")
async def get_agent_by_id(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent by ID"""
    try:
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        agent_dict = {
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
            "chain_type": agent.chain_type,
            "memory_enabled": agent.memory_enabled,
            "tools_enabled": agent.tools_enabled
        }
        
        return agent_dict
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting agent by ID: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve agent: {str(e)}"
        )

@router.delete("/delete-agent/{agent_id}")
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    """Delete a compliance agent and handle foreign key relationships"""
    try:
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        agent_name = agent.name
        
        # Delete all debate sessions that reference this agent
        debate_sessions_deleted = db.query(DebateSession).filter(
            DebateSession.compliance_agent_id == agent_id
        ).delete(synchronize_session=False)
        
        # Delete all compliance results that reference this agent
        from services.database import ComplianceResult  # Import if not already imported
        compliance_results_deleted = db.query(ComplianceResult).filter(
            ComplianceResult.agent_id == agent_id
        ).delete(synchronize_session=False)
        
        print(f"Deleting agent {agent_id}: Removed {debate_sessions_deleted} debate sessions and {compliance_results_deleted} compliance results")
        
        # Now delete the agent
        db.delete(agent)
        db.commit()
        
        print(f"Agent deleted successfully: ID={agent_id}, Name={agent_name}")
        
        return {
            "message": f"Agent '{agent_name}' deleted successfully",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "cleanup_info": {
                "debate_sessions_deleted": debate_sessions_deleted,
                "compliance_results_deleted": compliance_results_deleted
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting agent: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete agent: {str(e)}"
        )

@router.patch("/toggle-agent-status/{agent_id}")
async def toggle_agent_status(agent_id: int, db: Session = Depends(get_db)):
    """Toggle agent active/inactive status"""
    try:
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Toggle the status
        agent.is_active = not agent.is_active
        agent.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(agent)
        
        status = "activated" if agent.is_active else "deactivated"
        print(f"Agent {status}: ID={agent.id}, Name={agent.name}")
        
        return {
            "message": f"Agent '{agent.name}' {status} successfully",
            "agent_id": agent.id,
            "agent_name": agent.name,
            "is_active": agent.is_active,
            "updated_at": agent.updated_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error toggling agent status: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to toggle agent status: {str(e)}"
        )

@router.get("/health")
async def health_check():
    try:
        health = llm_service.health_check()
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """Get information about a specific collection"""
    try:
        info = rag_service.query_collection_info(collection_name)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



from services.database import (
    get_session_history, get_session_details, SessionType, AnalysisType
)

@router.get("/session-history")
async def get_agent_session_history(
    limit: int = 50, 
    session_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get recent agent session history"""
    try:
        # Convert string to enum if provided
        type_filter = None
        if session_type:
            try:
                type_filter = SessionType(session_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid session_type. Valid options: {[t.value for t in SessionType]}"
                )
        
        history = get_session_history(limit=limit, session_type=type_filter)
        
        return {
            "sessions": history,
            "total_returned": len(history),
            "available_session_types": [t.value for t in SessionType],
            "available_analysis_types": [t.value for t in AnalysisType]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-details/{session_id}")
async def get_agent_session_details(session_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific session"""
    try:
        details = get_session_details(session_id)
        
        if not details:
            raise HTTPException(
                status_code=404,
                detail=f"Session with ID {session_id} not found"
            )
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agent-performance/{agent_id}")
async def get_agent_performance_metrics(agent_id: int, db: Session = Depends(get_db)):
    """Get performance metrics for a specific agent"""
    try:
        # Check if agent exists
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent with ID {agent_id} not found"
            )
        
        # Get agent response statistics
        from services.database import AgentResponse
        
        total_responses = db.query(AgentResponse).filter(
            AgentResponse.agent_id == agent_id
        ).count()
        
        if total_responses == 0:
            return {
                "agent_id": agent_id,
                "agent_name": agent.name,
                "total_responses": 0,
                "message": "No response data available for this agent"
            }
        
        responses = db.query(AgentResponse).filter(
            AgentResponse.agent_id == agent_id
        ).all()
        
        # Response time statistics
        response_times = [r.response_time_ms for r in responses if r.response_time_ms]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # RAG usage statistics
        rag_responses = [r for r in responses if r.rag_used]
        rag_usage_rate = len(rag_responses) / total_responses if total_responses > 0 else 0
        
        # Processing method breakdown
        method_counts = {}
        for response in responses:
            method = response.processing_method
            method_counts[method] = method_counts.get(method, 0) + 1
        
        # Recent activity (last 10 responses)
        recent_responses = db.query(AgentResponse).filter(
            AgentResponse.agent_id == agent_id
        ).order_by(AgentResponse.created_at.desc()).limit(10).all()
        
        recent_activity = []
        for response in recent_responses:
            recent_activity.append({
                "session_id": response.session_id,
                "created_at": response.created_at,
                "processing_method": response.processing_method,
                "response_time_ms": response.response_time_ms,
                "rag_used": response.rag_used,
                "documents_found": response.documents_found,
                "response_preview": response.response_text[:200] + "..." if len(response.response_text) > 200 else response.response_text
            })
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "model_name": agent.model_name,
            "performance_metrics": {
                "total_responses": total_responses,
                "avg_response_time_ms": round(avg_response_time, 2),
                "rag_usage_rate": round(rag_usage_rate * 100, 2),  # as percentage
                "processing_method_breakdown": method_counts
            },
            "recent_activity": recent_activity,
            "agent_info": {
                "created_at": agent.created_at,
                "total_queries": agent.total_queries,
                "success_rate": agent.success_rate,
                "is_active": agent.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session-analytics")
async def get_session_analytics(days: int = 7, db: Session = Depends(get_db)):
    """Get analytics about agent sessions over the specified number of days"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from services.database import AgentSession, AgentResponse
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Session counts by type
        session_counts = db.query(
            AgentSession.session_type,
            func.count(AgentSession.id).label('count')
        ).filter(
            AgentSession.created_at >= start_date
        ).group_by(AgentSession.session_type).all()
        
        # Session counts by analysis type
        analysis_counts = db.query(
            AgentSession.analysis_type,
            func.count(AgentSession.id).label('count')
        ).filter(
            AgentSession.created_at >= start_date
        ).group_by(AgentSession.analysis_type).all()
        
        # Average response times
        avg_response_time = db.query(
            func.avg(AgentSession.total_response_time_ms)
        ).filter(
            AgentSession.created_at >= start_date,
            AgentSession.total_response_time_ms.isnot(None)
        ).scalar()
        
        # Most active agents
        active_agents = db.query(
            AgentResponse.agent_id,
            ComplianceAgent.name,
            func.count(AgentResponse.id).label('response_count')
        ).join(
            ComplianceAgent, AgentResponse.agent_id == ComplianceAgent.id
        ).filter(
            AgentResponse.created_at >= start_date
        ).group_by(
            AgentResponse.agent_id, ComplianceAgent.name
        ).order_by(
            func.count(AgentResponse.id).desc()
        ).limit(10).all()
        
        # RAG usage statistics
        total_responses = db.query(AgentResponse).filter(
            AgentResponse.created_at >= start_date
        ).count()
        
        rag_responses = db.query(AgentResponse).filter(
            AgentResponse.created_at >= start_date,
            AgentResponse.rag_used == True
        ).count()
        
        rag_usage_rate = (rag_responses / total_responses * 100) if total_responses > 0 else 0
        
        return {
            "analytics_period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "session_statistics": {
                "by_session_type": {sc.session_type.value: sc.count for sc in session_counts},
                "by_analysis_type": {ac.analysis_type.value: ac.count for ac in analysis_counts},
                "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else 0
            },
            "agent_activity": [
                {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.name,
                    "response_count": agent.response_count
                }
                for agent in active_agents
            ],
            "rag_statistics": {
                "total_responses": total_responses,
                "rag_responses": rag_responses,
                "rag_usage_rate": round(rag_usage_rate, 2)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    

doc_service = DocumentService(
    rag_service=rag_service,
    agent_service=agent_service,
    llm_service=llm_service,
    chroma_url=os.getenv("CHROMA_URL", "http://localhost:8020"),
    agent_api_url=os.getenv("FASTAPI_URL", "http://localhost:9020")
)


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

@router.post("/generate_documents")
async def generate_documents(req: GenerateRequest):
    logger.info("Received /generate_documents ⇒ %s", req)
    docs = await run_in_threadpool(
        doc_service.generate_documents,
        req.source_collections,
        req.source_doc_ids,
        req.use_rag,
        req.top_k,
        req.doc_title,
        req.pairwise_merge,
        req.actor_models,
        req.critic_model,
        req.coverage_strategy,
        req.max_actor_workers,
        req.critic_batch_size,
        req.critic_batch_char_cap,
        req.sectioning_strategy,
        req.chunks_per_section
    )
    return {"documents": docs}

class OptimizedTestPlanRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    doc_title:            Optional[str]         = "Comprehensive Test Plan"
    max_workers:          Optional[int]         = 4
    sectioning_strategy:  Optional[str]         = "auto"
    chunks_per_section:   Optional[int]         = 5

@router.post("/generate_optimized_test_plan")
async def generate_optimized_test_plan(req: OptimizedTestPlanRequest):
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
            doc_service.generate_optimized_test_plan,
            req.source_collections,
            req.source_doc_ids,
            req.doc_title,
            req.max_workers,
            req.sectioning_strategy,
            req.chunks_per_section
        )
        return {"documents": docs}
    except Exception as e:
        logger.error(f"Error in optimized test plan generation: {e}")
        raise HTTPException(status_code=500, detail=f"Test plan generation failed: {str(e)}")

# Note: MIL-style generation is handled via /generate_documents in generate_docs_service

class PreviewRequest(BaseModel):
    source_collections:   Optional[List[str]]   = None
    source_doc_ids:       Optional[List[str]]   = None
    sectioning_strategy:  Optional[str]         = "auto"
    chunks_per_section:   Optional[int]         = 5
    use_rag:              Optional[bool]        = True
    top_k:                Optional[int]         = 5

@router.post("/preview-sections")
async def preview_sections(req: PreviewRequest):
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



eval_svc = EvaluationService(
    rag=rag_service,
    llm=llm_service
)

@router.get("/generated-documents")
async def get_generated_documents():
    """Get list of all generated documents from vector store"""
    try:
        # Query the generated_documents collection
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8020")
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

@router.delete("/generated-documents/{document_id}")
async def delete_generated_document(document_id: str):
    """Delete a generated document from vector store"""
    try:
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8020")
        
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

@router.post("/evaluate_doc", response_model=EvaluateResponse)
async def evaluate_doc(req: EvaluateRequest, db: Session = Depends(get_db)):
    try:
        # generate a session_id so you can track history
        doc_session_id = str(uuid.uuid4())

        answer, rt_ms = eval_svc.evaluate_document(
            document_id     = req.document_id,
            collection_name = req.collection_name,
            prompt          = req.prompt,
            top_k           = req.top_k,
            model_name      = req.model_name,
            session_id      = doc_session_id,      
        )
        # Save chat history
        try:
            eval_history = ChatHistory(
                user_query=req.prompt,
                response=answer,
                model_used=req.model_name,
                query_type="rag",
                response_time_ms=rt_ms,
                langchain_used=True,
                session_id=doc_session_id
            )
            db.add(eval_history)
            db.commit()
        except Exception as e:
            print(f"Failed to save evaluation history: {e}")
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
        raise HTTPException(status_code=500, detail=str(e))

# =====================================================
# RAG Assessment Service Endpoints
# =====================================================

@router.post("/rag-assessment", response_model=RAGAssessmentResponse)
async def rag_assessment(request: RAGAssessmentRequest, db: Session = Depends(get_db)):
    """
    Perform comprehensive RAG assessment with performance and quality metrics.
    """
    try:
        logger.info(f"RAG assessment requested for query: {request.query[:100]}...")
        
        response, performance_metrics, quality_assessment, alignment_assessment, classification_metrics = rag_assessment_service.assess_rag_query(
            query=request.query,
            collection_name=request.collection_name,
            model_name=request.model_name,
            top_k=request.top_k,
            include_quality_assessment=request.include_quality_assessment,
            include_alignment_assessment=request.include_alignment_assessment,
            include_classification_metrics=request.include_classification_metrics
        )
        
        # Convert dataclasses to response models
        from dataclasses import asdict
        
        performance_response = RAGAssessmentResponse.model_validate({
            "response": response,
            "performance_metrics": asdict(performance_metrics),
            "quality_assessment": asdict(quality_assessment) if quality_assessment else None,
            "alignment_assessment": asdict(alignment_assessment) if alignment_assessment else None,
            "classification_metrics": asdict(classification_metrics) if classification_metrics else None
        })
        
        return performance_response
        
    except Exception as e:
        logger.error(f"RAG assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG assessment failed: {str(e)}")

@router.post("/rag-analytics")
async def get_rag_analytics(request: RAGAnalyticsRequest, db: Session = Depends(get_db)):
    """
    Get comprehensive RAG performance analytics for specified time period.
    """
    try:
        analytics = rag_assessment_service.get_performance_analytics(
            time_period_hours=request.time_period_hours,
            collection_name=request.collection_name
        )
        
        return analytics
        
    except Exception as e:
        logger.error(f"RAG analytics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG analytics failed: {str(e)}")

@router.post("/rag-benchmark")
async def rag_benchmark(request: RAGBenchmarkRequest, db: Session = Depends(get_db)):
    """
    Benchmark different RAG configurations on a set of queries.
    """
    try:
        logger.info(f"RAG benchmark requested for {len(request.query_set)} queries on collection: {request.collection_name}")
        
        benchmark_results = rag_assessment_service.benchmark_rag_configuration(
            query_set=request.query_set,
            collection_name=request.collection_name,
            configurations=request.configurations
        )
        
        return benchmark_results
        
    except Exception as e:
        logger.error(f"RAG benchmark failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG benchmark failed: {str(e)}")

@router.get("/rag-collection-performance/{collection_name}")
async def get_collection_performance(collection_name: str, db: Session = Depends(get_db)):
    """
    Get performance metrics specific to a collection.
    """
    try:
        performance_data = rag_assessment_service.get_collection_performance(collection_name)
        return performance_data
        
    except Exception as e:
        logger.error(f"Collection performance analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Collection performance analysis failed: {str(e)}")

@router.post("/rag-export-metrics")
async def export_rag_metrics(request: RAGMetricsExportRequest, db: Session = Depends(get_db)):
    """
    Export RAG metrics data for external analysis.
    """
    try:
        export_data = rag_assessment_service.export_metrics(
            format=request.format,
            time_period_hours=request.time_period_hours
        )
        
        return export_data
        
    except Exception as e:
        logger.error(f"RAG metrics export failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG metrics export failed: {str(e)}")

@router.get("/rag-health")
async def rag_assessment_health():
    """
    Health check for RAG Assessment Service.
    """
    try:
        # Get basic stats from the assessment service
        current_sessions = len(rag_assessment_service.performance_metrics)
        quality_assessments = len(rag_assessment_service.quality_assessments)
        
        return {
            "service": "RAG Assessment Service",
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "active_sessions": current_sessions,
                "quality_assessments": quality_assessments
            },
            "endpoints": [
                "/rag-assessment",
                "/rag-analytics", 
                "/rag-benchmark",
                "/rag-collection-performance/{collection_name}",
                "/rag-export-metrics",
                "/rag-health"
            ]
        }
        
    except Exception as e:
        logger.error(f"RAG assessment health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/rag-assessment-demo")
async def rag_assessment_demo():
    """
    Demo endpoint showing example usage of RAG Assessment Service.
    """
    return {
        "demo": "RAG Assessment Service",
        "description": "Comprehensive RAG performance monitoring and quality evaluation",
        "key_features": [
            "Performance metrics tracking (response time, retrieval time, generation time)",
            "Quality assessment (relevance, coherence, factual accuracy, completeness)",
            "Analytics and benchmarking across time periods",
            "Collection-specific performance analysis",
            "Configuration benchmarking and optimization",
            "Metrics export for external analysis"
        ],
        "example_usage": {
            "assess_single_query": {
                "endpoint": "POST /rag-assessment",
                "payload": {
                    "query": "What are the key legal implications of this contract?",
                    "collection_name": "legal_contracts",
                    "model_name": "gpt-3.5-turbo",
                    "top_k": 5,
                    "include_quality_assessment": True
                }
            },
            "get_analytics": {
                "endpoint": "POST /rag-analytics",
                "payload": {
                    "time_period_hours": 24,
                    "collection_name": "legal_contracts"
                }
            },
            "benchmark_configs": {
                "endpoint": "POST /rag-benchmark",
                "payload": {
                    "query_set": [
                        "Analyze this contract for risks",
                        "What are the compliance requirements?"
                    ],
                    "collection_name": "legal_docs",
                    "configurations": [
                        {"model_name": "gpt-3.5-turbo", "top_k": 5},
                        {"model_name": "gpt-4", "top_k": 3},
                        {"model_name": "gpt-4o", "top_k": 5}
                        
                    ]
                }
            }
        }
    }

# =====================================================
# Word Export Endpoints  
# =====================================================

@router.post("/export-agents-word")
async def export_agents_to_word(agent_ids: List[int] = None, export_format: str = "detailed", db: Session = Depends(get_db)):
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

@router.post("/export-chat-history-word")
async def export_chat_history_to_word(
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Export chat history to a Word document.
    
    Args:
        session_id: Optional session ID to filter by
        limit: Maximum number of chat records to export
    """
    try:
        # Query chat history
        query = db.query(ChatHistory)
        
        if session_id:
            query = query.filter(ChatHistory.session_id == session_id)
        
        chat_records = query.order_by(ChatHistory.timestamp.desc()).limit(limit).all()
        
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
                "langchain_used": chat.langchain_used
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

@router.post("/export-simulation-word")
async def export_agent_simulation_to_word(simulation_data: Dict[str, Any]):
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

@router.post("/export-rag-assessment-word")
async def export_rag_assessment_to_word(assessment_data: Dict[str, Any]):
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

@router.post("/export-reconstructed-word")
async def export_reconstructed_document_to_word(reconstructed: Dict[str, Any]):
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

@router.get("/export-word-demo")
async def word_export_demo():
    """
    Demo endpoint showing example usage of Word export capabilities.
    """
    return {
        "demo": "Word Export Service",
        "description": "Export agents, chat history, and simulation results to Word documents",
        "available_exports": [
            {
                "endpoint": "POST /export-agents-word",
                "description": "Export agent configurations",
                "parameters": {
                    "agent_ids": "Optional list of specific agent IDs",
                    "export_format": "summary or detailed"
                }
            },
            {
                "endpoint": "POST /export-chat-history-word", 
                "description": "Export chat conversation history",
                "parameters": {
                    "session_id": "Optional session ID filter",
                    "limit": "Maximum records to export"
                }
            },
            {
                "endpoint": "POST /export-simulation-word",
                "description": "Export agent simulation results",
                "parameters": {
                    "simulation_data": "Complete simulation results dictionary"
                }
            },
            {
                "endpoint": "POST /export-rag-assessment-word",
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
                "endpoint": "POST /export-agents-word",
                "payload": {
                    "export_format": "detailed"
                }
            },
            "export_specific_session": {
                "endpoint": "POST /export-chat-history-word", 
                "payload": {
                    "session_id": "abc123def456",
                    "limit": 25
                }
            }
        }
    }
