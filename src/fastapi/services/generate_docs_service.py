# services/document_service.py
import io
import uuid
import base64
import requests
from typing import List, Optional, Union, Dict, Any
from docx import Document
import fitz
import markdown
import os
import mimetypes
from bs4 import BeautifulSoup
from services.rag_service import RAGService
from services.agent_service import AgentService
from services.llm_service import LLMService
from services.database import SessionLocal, ComplianceAgent

class TemplateParser:
    @staticmethod
    def extract_headings_from_docx(path: str) -> List[str]:
        doc = Document(path)
        return [p.text for p in doc.paragraphs
                if p.style.name.startswith("Heading") and p.text.strip()]

    @staticmethod
    def extract_headings_from_pdf(path: str, size_threshold: float = 16.0) -> List[str]:
        doc = fitz.open(path)
        headings = []
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                if block["type"] != 0: continue
                for line in block["lines"]:
                    size = line["spans"][0]["size"]
                    text = "".join(s["text"] for s in line["spans"]).strip()
                    if size >= size_threshold and text:
                        headings.append(text)
        return headings

    @staticmethod
    def extract_headings_from_html(html: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        headings = []
        for level in range(1,7):
            for tag in soup.find_all(f"h{level}"):
                text = tag.get_text(strip=True)
                if text:
                    headings.append(text)
        return headings

    @staticmethod
    def extract_headings_from_markdown(md: str) -> List[str]:
        lines = md.splitlines()
        return [l.lstrip("# ").strip() for l in lines
                if l.startswith("#")]
        
    @staticmethod
    def extract_headings_from_text(text: str) -> List[str]:
        return [
            line.lstrip("# ").strip()
            for line in text.splitlines()
            if line.startswith("# ")
        ]

    @classmethod
    def extract(cls, path_or_str: str, is_path: bool=True) -> List[str]:
        if not is_path:
            return cls.extract_headings_from_text(path_or_str)

        # ext = os.path.splitext(path_or_str if is_path else "")[1].lower()
        ext = os.path.splitext(path_or_str)[1].lower()
        
        if ext == ".docx":
            return cls.extract_headings_from_docx(path_or_str)
        if ext == ".docx":
            return cls.extract_headings_from_docx(path_or_str)
        if ext == ".pdf":
            return cls.extract_headings_from_pdf(path_or_str)
        if ext in {".html", ".htm"}:
            html = open(path_or_str).read() if is_path else path_or_str
            return cls.extract_headings_from_html(html)
        if ext == ".md" or (not is_path and "\n" in path_or_str):
            md = open(path_or_str).read() if is_path else path_or_str
            return cls.extract_headings_from_markdown(md)
        raise ValueError(f"Unsupported template format: {ext!r}")
class DocumentService:
    def __init__(
        self,
        rag_service: RAGService,
        agent_service: AgentService,
        llm_service: LLMService,
        chroma_url: str,
        agent_api_url: str,
    ):
        self.rag = rag_service
        self.agent = agent_service
        self.llm = llm_service
        self.chroma_url = chroma_url.rstrip("/")
        self.agent_api = agent_api_url.rstrip("/")

    def _fetch_templates(self, collection: str) -> List[str]:
        resp = requests.get(f"{self.chroma_url}/documents",
                            params={"collection_name": collection})
        resp.raise_for_status()
        return resp.json().get("documents", [])

    def _retrieve_context(self, tmpl: str, sources: List[str], top_k: int) -> str:
        pieces = []
        for coll in sources:
            docs, ok = self.rag.get_relevant_documents(tmpl, coll)
            if ok:
                pieces += docs[:top_k]
        return "\n\n".join(pieces)

    def _invoke_agent(
        self,
        prompt: str,
        agent_id: int,
        collection: str,
        ) -> str:
        """
        Use your LLMService.query_model to do a RAG-enabled completion.
        We assume that in your DB you can look up the ComplianceAgent
        to get its `model_name`
        """
        session = SessionLocal()
        try:
            agent = session.query(ComplianceAgent).get(agent_id)
            model_name = agent.model_name.lower()
        finally:
            session.close()

        # ask your LLMService to do RAG over `collection` + `prompt`
        answer, _ = self.llm.query_model(
            model_name=model_name,
            query=prompt,
            collection_name=collection,
            query_type="rag",
        )
        return answer
    
    def _fetch_templates(self, collection: str) -> List[str]:
        resp = requests.get(f"{self.chroma_url}/documents",
                            params={"collection_name": collection})
        resp.raise_for_status()
        return resp.json().get("documents", [])


    def generate_documents(
        self,
        template_collection: str,
        template_doc_ids:    Optional[List[str]] = None,
        source_collections:  Optional[List[str]] = None,
        source_doc_ids:      Optional[List[str]] = None,
        agent_ids:           List[int]           = [],
        use_rag:             bool                = True,
        top_k:               int                 = 5,
        doc_title:          Optional[str]        = None,
    ) -> List[dict]:
        out = []
        # load agents once
        self.agent.load_selected_compliance_agents(agent_ids)

        # get raw markdown/text for each template
        tpl_texts = self._fetch_templates(template_collection)

        for tpl_text in tpl_texts:
            # extract all Markdown headings (#, ##, ###, etc.)
            headings = TemplateParser.extract_headings_from_markdown(tpl_text)

            # create a fresh .docx
            doc = Document()
            title = doc_title or "Generated Test Plan"
            doc.add_heading(title, level=1)

            # now fill in each section
            for heading in headings:
                # 1) RAG‐retrieve your source context for this heading
                ctx_pieces = []
                if use_rag and source_collections and source_doc_ids:
                    for coll, sid in zip(source_collections, source_doc_ids):
                        docs, ok = self.rag.get_relevant_documents(sid, coll)
                        if ok:
                            ctx_pieces += docs[:top_k]
                context = "\n\n".join(ctx_pieces)

                # 2) build the per-section prompt
                prompt = f"""### Section: {heading}

    Using the following source material, write the content for this section of the test plan:

    {context}
    """

                # 3) call your agent
                agent_meta = next(a for a in self.agent.compliance_agents if a["id"] == agent_ids[0])
                
                # Use a consistent session_id for this document generation
                doc_session_id = str(uuid.uuid4())
                
                # Create a proper database session and agent session for proper logging
                db_session = SessionLocal()
                try:
                    
                    # Create an agent session for proper foreign key relationships
                    from services.database import log_agent_session, SessionType, AnalysisType
                    log_agent_session(
                        session_id=doc_session_id,
                        session_type=SessionType.SINGLE_AGENT,
                        analysis_type=AnalysisType.DIRECT_LLM,
                        user_query=f"Document generation for section: {heading}"
                    )
                    
                    result = self.agent._invoke_chain(
                        agent=agent_meta,
                        data_sample=prompt,
                        session_id=doc_session_id,
                        db=db_session
                    )
                except Exception as e:
                    print(f"Error invoking agent: {e}")
                    # Fallback: create a simple response
                    result = {"reason": f"Error generating content for {heading}. Please try again."}
                finally:
                    db_session.close()
                response_md = result["reason"]

                # 4) convert the Markdown response into *real* docx
                html = markdown.markdown(response_md)
                soup = BeautifulSoup(html, "html.parser")
                doc.add_heading(heading, level=2)
                
                # Process all elements in the HTML
                for el in soup.find_all(True):  # Find all elements, not just direct contents
                    if not el.name:
                        continue
                        
                    # Handle heading tags (h1, h2, h3, h4, h5, h6)
                    if el.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        try:
                            lvl = int(el.name[1])  # Extract level from h1, h2, etc.
                            # Ensure heading level is reasonable for Word doc (max level 9)
                            lvl = min(lvl, 9)
                            doc.add_heading(el.get_text(strip=True), level=lvl)
                        except (ValueError, IndexError) as e:
                            print(f"Warning: Could not parse heading level from {el.name}: {e}")
                            doc.add_paragraph(el.get_text(strip=True))
                    
                    # Handle paragraph tags
                    elif el.name == "p":
                        text = el.get_text(strip=True)
                        if text:  # Only add non-empty paragraphs
                            doc.add_paragraph(text)
                    
                    # Handle unordered lists
                    elif el.name == "ul":
                        for li in el.find_all("li", recursive=False):  # Only direct li children
                            text = li.get_text(strip=True)
                            if text:
                                doc.add_paragraph(f"• {text}")
                    
                    # Handle ordered lists
                    elif el.name == "ol":
                        for idx, li in enumerate(el.find_all("li", recursive=False), 1):  # Only direct li children
                            text = li.get_text(strip=True)
                            if text:
                                doc.add_paragraph(f"{idx}. {text}")
                    
                    # Handle line breaks
                    elif el.name == "br":
                        doc.add_paragraph("")  # Add empty paragraph for line break
                    
                    # Handle other elements as plain text
                    elif el.name in ["strong", "b", "em", "i", "span", "div"]:
                        text = el.get_text(strip=True)
                        if text and not el.find_parent(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
                            # Only add as paragraph if not already inside another handled element
                            doc.add_paragraph(text)

            # 5) serialize to base64 & collect
            buf = io.BytesIO()
            doc.save(buf)
            
            # Extract plain text from the document for vector storage
            doc_text = self._extract_text_from_docx_object(doc)
            
            # Store in vector database for future RAG queries
            generated_doc_info = self._save_to_vector_store(
                title=title,
                content=doc_text,
                template_collection=template_collection,
                agent_ids=agent_ids,
                session_id=doc_session_id
            )
            
            out.append({
                "title":    title,
                "docx_b64": base64.b64encode(buf.getvalue()).decode("utf-8"),
                "document_id": generated_doc_info.get("document_id"),
                "collection_name": generated_doc_info.get("collection_name"),
                "generated_at": generated_doc_info.get("generated_at")
            })

        return out
    
    def _extract_text_from_docx_object(self, doc) -> str:
        """Extract plain text from a python-docx Document object"""
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text.strip())
        return "\n\n".join(text_parts)
    
    def _save_to_vector_store(self, title: str, content: str, template_collection: str, 
                            agent_ids: List[int], session_id: str) -> Dict[str, Any]:
        """Save generated document to ChromaDB vector store"""
        try:
            from datetime import datetime
            import json
            
            # Create a collection name for generated documents
            generated_collection = "generated_documents"
            
            # First, ensure the collection exists
            try:
                # Check if collection exists by listing collections
                list_response = requests.get(
                    f"{self.chroma_url}/collections",
                    timeout=5
                )
                
                if list_response.ok:
                    collections = list_response.json().get("collections", [])
                    if generated_collection not in collections:
                        # Collection doesn't exist, create it using the proper endpoint
                        print(f"Creating collection '{generated_collection}'...")
                        create_response = requests.post(
                            f"{self.chroma_url}/collection/create",
                            params={"collection_name": generated_collection},
                            timeout=10
                        )
                        
                        if create_response.ok:
                            print(f"✅ Collection '{generated_collection}' created successfully")
                        else:
                            print(f"Failed to create collection: {create_response.status_code} - {create_response.text}")
                    else:
                        print(f"Collection '{generated_collection}' already exists")
                else:
                    print(f"Failed to list collections: {list_response.status_code} - {list_response.text}")
                        
            except Exception as e:
                print(f"Collection setup error: {e}")
            
            # Create unique document ID
            doc_id = f"gen_doc_{session_id}_{title.replace(' ', '_').replace('/', '_')}"
            
            # Prepare metadata
            metadata = {
                "title": title,
                "type": "generated_document",
                "template_collection": template_collection,
                "agent_ids": json.dumps(agent_ids),
                "session_id": session_id,
                "generated_at": datetime.now().isoformat(),
                "word_count": len(content.split()),
                "char_count": len(content)
            }
            
            # Store in ChromaDB via API
            payload = {
                "collection_name": generated_collection,
                "documents": [content],
                "metadatas": [metadata],
                "ids": [doc_id]
            }
            
            response = requests.post(
                f"{self.chroma_url}/documents/add",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                print(f"✅ Saved generated document to vector store: {doc_id}")
                return {
                    "document_id": doc_id,
                    "collection_name": generated_collection,
                    "generated_at": metadata["generated_at"],
                    "saved": True
                }
            else:
                print(f"❌ Failed to save to vector store: {response.status_code} - {response.text}")
                return {"saved": False, "error": response.text}
                
        except Exception as e:
            print(f"❌ Error saving to vector store: {e}")
            return {"saved": False, "error": str(e)}
