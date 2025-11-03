from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import time
import uuid
import logging
import sys
from pathlib import Path

# New dependency injection imports
from core.dependencies import (
    get_db,
    get_chat_repository,
    get_llm_service,
    get_rag_service
)
from repositories import ChatRepository
from services.llm_service import LLMService
from services.rag_service import RAGService

# Add parent directory to path to import llm_config module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from llm_config.llm_config import validate_model, get_model_config, llm_env

logger = logging.getLogger("CHAT_API_LOGGER")

chat_api_router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    model: str
    use_rag: bool = False
    collection_name: Optional[str] = None
    
@chat_api_router.post("")
def chat(
    request: ChatRequest,
    chat_repo: ChatRepository = Depends(get_chat_repository),
    llm_service: LLMService = Depends(get_llm_service),
    rag_service: RAGService = Depends(get_rag_service),
    db: Session = Depends(get_db)
):
    """
    Chat endpoint that handles both direct LLM and RAG-enhanced responses.

    Validates model availability and API keys before processing to provide
    early error feedback to users.

    Uses new dependency injection pattern with repositories and services.
    """
    try:
        session_id = str(uuid.uuid4())

        # ========================================================================
        # EARLY MODEL VALIDATION - Fail fast if model is unsupported or misconfigured
        # ========================================================================
        is_valid, validation_error = validate_model(request.model)
        if not is_valid:
            logger.error(f"Model validation failed: {validation_error}")
            raise HTTPException(status_code=400, detail=validation_error)

        # Validate API keys for the model's provider
        model_config = get_model_config(request.model)
        keys_valid, key_error = llm_env.validate_provider_keys(model_config.provider)
        if not keys_valid:
            logger.error(f"API key validation failed for {model_config.provider}: {key_error}")
            raise HTTPException(
                status_code=500,
                detail=f"{key_error}. Please configure the required API key in your environment."
            )

        logger.info(f"Processing chat request with model={request.model}, use_rag={request.use_rag}")

        if request.use_rag and request.collection_name:
            # RAG mode: fetch docs via RAGService, then run a retrieval chain
            answer, response_time = rag_service.process_query_with_rag(
                query_text=request.query,
                collection_name=request.collection_name,
                model_name=request.model,
            )

            # Save chat history using repository
            chat_repo.create_chat_entry(
                user_query=request.query,
                response=answer,
                model_used=request.model,
                collection_name=request.collection_name,
                query_type="rag",
                response_time_ms=response_time,
                session_id=session_id
            )
            db.commit()

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

            # Save chat history using repository
            chat_repo.create_chat_entry(
                user_query=request.query,
                response=answer,
                model_used=request.model,
                collection_name=None,
                query_type="direct",
                response_time_ms=response_time_ms,
                session_id=session_id
            )
            db.commit()

            return {
                "response": answer,
                "response_time_ms": response_time_ms,
                "session_id": session_id,
                "type": "direct"
            }

    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@chat_api_router.get("/history")
def get_chat_history(
    limit: int = 100,
    offset: int = 0,
    chat_repo: ChatRepository = Depends(get_chat_repository)
):
    """
    Get chat history.

    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        chat_repo: Chat repository (injected)

    Returns:
        List of chat history entries
    """
    history = chat_repo.get_all(skip=offset, limit=limit, order_by="timestamp")
    return [
        {
            "id": entry.id,
            "user_query": entry.user_query,
            "response": entry.response,
            "model_used": entry.model_used,
            "collection_name": entry.collection_name,
            "query_type": entry.query_type,
            "response_time_ms": entry.response_time_ms,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "session_id": entry.session_id
        }
        for entry in history
    ]