from typing import Optional
from pydantic import Field
from services.rag_service import RAGService
from services.llm_service import LLMService

class EvaluationService:
    def __init__(self, rag: RAGService, llm: LLMService):
        self.rag = rag
        self.llm = llm

    def evaluate_document(
        self,
        document_id: str,
        collection_name: str,
        prompt: str,
        top_k: Optional[int] = Field(5),
        model_name: Optional[str] = Field(...),
        session_id: str = None,
    ):
        # 1) RAG‐fetch the most relevant chunks of your document
        # Build a query that filters by document_id
        where_filter = {"document_id": document_id} if document_id else None

        result = self.rag.get_relevant_documents(
            query=prompt,
            collection_name=collection_name,
            n_results=top_k,
            where=where_filter
        )

        # Check if the query was successful
        if result.get("status") == "error":
            raise Exception(f"Failed to retrieve documents: {result.get('message')}")

        # Extract documents from the result
        documents = result.get("results", {}).get("documents", [])

        if not documents:
            raise Exception(f"No documents found for document_id: {document_id}")

        context = "\n\n".join(documents[:top_k])

        # 2) stitch your user's prompt onto those chunks
        full_prompt = f"""
Here's the relevant context from document `{document_id}`:

{context}

---
Now: {prompt}
""".strip()

        # 3) call LLMService with the specified model
        answer, rt_ms = self.llm.query_model(
            model_name=model_name,
            query=full_prompt,
            collection_name=collection_name,
            query_type="rag",
            session_id=session_id
        )

        return answer, rt_ms
