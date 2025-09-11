import os
import time
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from services.llm_utils import get_llm, _resolve_ollama_model
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from typing import Optional

from services.database import (
    SessionLocal,
    ChatHistory
)

class LLMService:
    def __init__(self):
        self.chromadb_dir = os.getenv("CHROMADB_PERSIST_DIRECTORY", "/app/chroma_db_data")
        self.embedding_function = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.n_results = int(os.getenv("N_RESULTS", "3"))
        self.openai_api_key = os.getenv("OPEN_AI_API_KEY")
        self.compliance_agents = []

    def get_llm_service(self, model_name: str):
        # Delegate to unified loader; it supports GPT-*, llama, llama2, llama3.1, and common OSS models
        return get_llm(model_name=model_name)

    def get_retriever(self, collection_name: str, metadata_filter: Optional[dict] = None):
        db = Chroma(
            persist_directory=self.chromadb_dir,
            collection_name=collection_name,
            embedding_function=self.embedding_function
        )
        # LangChain Chroma retriever expects "filter" (server API uses "where")
        search_kwargs = {"k": self.n_results}
        if metadata_filter:
            search_kwargs["filter"] = metadata_filter
        return db.as_retriever(search_kwargs=search_kwargs)

    def query_model(
        self,
        model_name: str,
        query: str,
        collection_name: str,
        query_type: str = "rag",
        session_id: Optional[str] = None,
        log_history: bool = True,
        metadata_filter: Optional[dict] = None,
    ) -> str:
        retriever = self.get_retriever(collection_name, metadata_filter=metadata_filter)
        llm = self.get_llm_service(model_name)

        prompt = ChatPromptTemplate.from_template(
            "{context}\n\nQuestion: {input}"
        )
        
        document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
        chain = create_retrieval_chain(retriever=retriever, combine_docs_chain=document_chain)

        start_time = time.time()
        result = chain.invoke({"input": query})
        response_time_ms = int((time.time() - start_time) * 1000)

        # Save chat history (optional)
        if log_history:
            session = SessionLocal()
            try:
                history = ChatHistory(
                    user_query=query,
                    response=result.get("answer", "No response generated."),
                    model_used=model_name,
                    collection_name=collection_name,
                    query_type=query_type,
                    response_time_ms=response_time_ms,
                    langchain_used=True,
                    session_id=session_id,
                    source_documents=[doc.page_content for doc in result.get("context", [])] if result.get("context") else []
                )
                session.add(history)
                session.commit()
            except Exception as e:
                print(f"Failed to save chat history: {e}")
                session.rollback()
            finally:
                session.close()

        return result.get("answer", "No response generated."), response_time_ms

    def query_direct(self, model_name: str, query: str, session_id: Optional[str] = None, log_history: bool = True) -> str:
        """
        Direct query to LLM without RAG retrieval.
        Used for test plan generation where we analyze section content directly.
        """
        llm = self.get_llm_service(model_name)
        
        start_time = time.time()
        
        # For direct queries, we use the LLM without retrieval
        result = llm.invoke(query)
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Save to chat history if session_id provided
        if session_id and log_history:
            session = SessionLocal()
            try:
                history = ChatHistory(
                    user_query=query[:500],  # Truncate long queries
                    response=result.content[:1000] if hasattr(result, 'content') else str(result)[:1000],
                    model_used=model_name,
                    collection_name="direct_query",  # Use placeholder since it's required
                    query_type="direct",
                    response_time_ms=response_time_ms,
                    langchain_used=True,
                    session_id=session_id,
                    source_documents=[]  # No source documents for direct queries
                )
                session.add(history)
                session.commit()
            except Exception as e:
                print(f"Failed to save chat history for direct query: {e}")
                session.rollback()
            finally:
                session.close()
        
        # Return just the content, maintaining compatibility with existing code
        content = result.content if hasattr(result, 'content') else str(result)
        return content, response_time_ms

    def health_check(self):
        """Check service health and model availability."""
        health_status = {
            "status": "healthy",
            "chromadb_status": "connected",
            "models": {},
            "timestamp": time.time()
        }
        try:
            # Test ChromaDB connection
            test_db = Chroma(
                persist_directory=self.chromadb_dir, 
                collection_name="health_check",
                embedding_function=self.embedding_function
            )
            health_status["chromadb_status"] = "connected"
        except Exception as e:
            health_status["chromadb_status"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        # Test available models (simplified: single LLaMA default)
        for model in ["gpt-4", "gpt-3.5-turbo", "gpt-oss", "llama"]:
            try:
                llm = self.get_llm_service(model)
                health_status["models"][model] = "available"
            except Exception as e:
                health_status["models"][model] = "unavailable: %s" % str(e)
                health_status["status"] = "degraded"

        # Ollama status and models
        ollama_info = {
            "status": "unknown",
            "base_url": os.getenv("LLM_OLLAMA_HOST", "http://ollama:11434"),
            "available_models": [],
            "resolved": {},
            "missing": [],
            "pull_attempts": []
        }
        base = ollama_info["base_url"].rstrip("/")
        try:
            r = requests.get("%s/api/tags" % base, timeout=5)
            if r.ok:
                ollama_info["status"] = "connected"
                data = r.json() or {}
                ollama_info["available_models"] = [m.get("name", "") for m in data.get("models", [])]
            else:
                ollama_info["status"] = "error: %s" % r.status_code
        except Exception as e:
            ollama_info["status"] = "error: %s" % str(e)

        # Resolved targets (single canonical LLaMA)
        for name in ["llama"]:
            try:
                ollama_info["resolved"][name] = _resolve_ollama_model(name, base)
            except Exception as e:
                ollama_info["resolved"][name] = "error: %s" % str(e)

        avail_lower = [m.lower() for m in ollama_info.get("available_models", [])]
        for _, tag in ollama_info.get("resolved", {}).items():
            if isinstance(tag, str) and tag.lower() not in avail_lower:
                ollama_info["missing"].append(tag)

        autopull = os.getenv("OLLAMA_AUTOPULL", "true").lower() in ("1", "true", "yes")
        if autopull and ollama_info["missing"] and ollama_info["status"].startswith("connected"):
            for tag in ollama_info["missing"]:
                try:
                    pr = requests.post("%s/api/pull" % base, json={"name": tag}, timeout=120)
                    if pr.ok:
                        ollama_info["pull_attempts"].append({"tag": tag, "status": "pulled"})
                    else:
                        ollama_info["pull_attempts"].append({"tag": tag, "status": "error:%s" % pr.status_code, "detail": pr.text[:200]})
                except Exception as e:
                    ollama_info["pull_attempts"].append({"tag": tag, "status": "exception:%s" % str(e)})

            # Refresh
            try:
                r2 = requests.get("%s/api/tags" % base, timeout=5)
                if r2.ok:
                    data2 = r2.json() or {}
                    ollama_info["available_models"] = [m.get("name", "") for m in data2.get("models", [])]
                    avail_lower = [m.lower() for m in ollama_info["available_models"]]
                    ollama_info["missing"] = [t for t in ollama_info["missing"] if t.lower() not in avail_lower]
            except Exception:
                pass

        health_status["ollama"] = ollama_info
        return health_status
