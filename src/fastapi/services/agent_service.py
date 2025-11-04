import os
import uuid
import time
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from datetime import datetime
from services.database import (
    SessionLocal, ComplianceAgent, DebateSession, log_compliance_result,log_agent_response, 
    log_agent_session, log_agent_response, complete_agent_session,
    SessionType, AnalysisType
)
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from schemas import ComplianceResultSchema

class ComplianceResult(BaseModel):
    # compliant: bool = Field(description="Whether the content is compliant")
    reason: str = Field(description="Explanation for the compliance decision")
    confidence: Optional[float] = Field(default=None, description="Confidence score")

class AgentService:
    """AgentService using LangChain for compliance verification and debate."""

    def __init__(self):
        self.compliance_agents: List[Dict[str, Any]] = []
        
        try:
            from services.llm_service import LLMService
            self.llm_service = LLMService()
            print("Using LLMService (same as Direct Chat)")
            
            # Test that it works
            test_llm = self.llm_service.get_llm_service("gpt-4")
            print("LLMService connection verified")
            
        except Exception as e:
            print(f"LLMService failed, falling back to llm_utils: {e}")
            self.llm_service = None
        
        if not self.llm_service:
            self.llms = {}
        
        try:
            self.compliance_parser = PydanticOutputParser(pydantic_object=ComplianceResultSchema)
            print("Compliance parser initialized")
        except Exception as e:
            print(f"Failed to initialize compliance parser: {e}")
        

    
    def get_llm_for_agent(self, model_name: str):
        """Get LLM using the same method as Direct Chat"""
        model_name = model_name.lower()
        
        # Try LLMService first (same as Direct Chat)
        if self.llm_service:
            try:
                return self.llm_service.get_llm_service(model_name)
            except Exception as e:
                print(f"LLMService failed for {model_name}, using fallback: {e}")
        
        # Fallback to llm_utils (also same as Direct Chat)
        if hasattr(self, 'llms') and model_name in self.llms:
            return self.llms[model_name]
        
        # Last resort - direct llm_utils call
        try:
            from services.llm_utils import get_llm
            return get_llm(model_name)
        except Exception as e:
            raise ValueError(f"Cannot get LLM for model {model_name}: {e}")
        
    def load_selected_compliance_agents(self, agent_ids: List[int]) -> None:
        """Load agents - NO CHANGE needed here"""
        session = SessionLocal()
        try:
            self.compliance_agents = []
            agents = session.query(ComplianceAgent).filter(ComplianceAgent.id.in_(agent_ids)).all()
            for agent in agents:
                model_name = agent.model_name.lower().strip()
                
                # Store raw prompts for direct LLM calls (no complex chains)
                self.compliance_agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "model_name": model_name,
                    "system_prompt": agent.system_prompt,
                    "user_prompt_template": agent.user_prompt_template
                })
                
            print(f"Loaded {len(self.compliance_agents)} agents")
        finally:
            session.close()

    def run_compliance_check(self, data_sample: str, agent_ids: List[int], db: Session) -> Dict[str, Any]:
        """Main compliance check - WORKS with unified LLM path"""
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        session_type = SessionType.MULTI_AGENT_DEBATE if len(agent_ids) > 1 else SessionType.SINGLE_AGENT
        log_agent_session(
            session_id=session_id,
            session_type=session_type,
            analysis_type=AnalysisType.DIRECT_LLM,
            user_query=data_sample
        )
        
        self.load_selected_compliance_agents(agent_ids)
        
        # Run parallel checks first
        results = self.run_parallel_checks(data_sample, session_id, db)
        
        # Set up debate sessions
        for idx, agent in enumerate(self.compliance_agents):
            db.add(DebateSession(session_id=session_id, compliance_agent_id=agent["id"], debate_order=idx + 1))
        db.commit()
        
        # Run debate
        debate_results = self.run_debate(session_id, data_sample, db)
        
        total_time = int((time.time() - start_time) * 1000)
        complete_agent_session(
            session_id=session_id,
            overall_result={
                "details": results,
                "debate_results": debate_results
            },
            agent_count=len(agent_ids),
            total_response_time_ms=total_time,
            status='completed'
        )
        
        return {
            "details": results,
            "debate_results": debate_results,
            "session_id": session_id
        }

    def run_parallel_checks(self, data_sample: str, session_id: str, db: Session) -> Dict[int, Dict[str, Any]]:
        """Run multiple agents in parallel - WORKS with unified LLM path"""
        results = {}
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._invoke_chain, agent, data_sample, session_id, db): i 
                for i, agent in enumerate(self.compliance_agents)
            }
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
        return results

    def _invoke_chain(self, agent: Dict[str, Any], data_sample: str, session_id: str, db: Session) -> Dict[str, Any]:
        """Single agent invocation - uses same LLM path as Direct Chat"""
        start_time = time.time()
        
        try:
            model_name = agent["model_name"]
            
            # Get LLM using the SAME method as Direct Chat
            llm = self.get_llm_for_agent(model_name)
            
            # Build prompt (same as Direct Chat approach)
            formatted_user_prompt = agent["user_prompt_template"].replace("{data_sample}", data_sample)
            full_prompt = f"{agent['system_prompt']}\n\n{formatted_user_prompt}"
            
            # Call LLM (EXACT same method as Direct Chat)
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=full_prompt)])
            
            # Handle response (same as Direct Chat)
            if hasattr(response, 'content'):
                raw_text = response.content
            else:
                raw_text = str(response)
            
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log the response
            log_agent_response(
                session_id=session_id,
                agent_id=agent["id"],
                response_text=raw_text,
                processing_method="direct_llm_unified",
                response_time_ms=response_time_ms,
                model_used=agent["model_name"],
                analysis_summary=raw_text[:200]
            )
            
            log_compliance_result(
                agent_id=agent["id"],
                data_sample=data_sample,
                confidence_score=None,
                reason=raw_text,
                raw_response=raw_text,
                processing_method="direct_llm_unified",
                response_time_ms=response_time_ms,
                model_used=agent["model_name"],
                session_id=session_id
            )
            
            return {
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "reason": raw_text,
                "confidence": None,
                "method": "direct_llm_unified"
            }
            
        except Exception as e:
            response_time_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Error processing with agent {agent['name']}: {str(e)}"
            print(f"Error in _invoke_chain: {e}")
            
            return {
                "agent_id": agent["id"],
                "agent_name": agent["name"],
                "reason": error_msg,
                "confidence": None,
                "method": "error"
            }

    def has_legal_research_enabled(self, agent_id: int, db: Session) -> bool:
        """Check if an agent has legal research tool enabled"""
        agent = db.query(ComplianceAgent).filter(ComplianceAgent.id == agent_id).first()
        if not agent or not agent.tools_enabled:
            return False
        
        tools = agent.tools_enabled if isinstance(agent.tools_enabled, dict) else {}
        return tools.get("legal_research", False)
    
    def run_agent_legal_research(self, legal_query: str, agent_ids: List[int], 
                               collection_name: str = "agent_legal_research",
                               sources: List[str] = None, db: Session = None) -> Dict[str, Any]:
        """
        Have agents perform legal research, analyze results, and store in ChromaDB.
        Only agents with legal_research tool enabled will participate.
        """
        session_id = str(uuid.uuid4())
        start_time = time.time()
        
        if not self.legal_research_service:
            raise Exception("Legal research service not available")
        
        # Filter agents to only those with legal research enabled
        legal_enabled_agents = [
            agent_id for agent_id in agent_ids 
            if self.has_legal_research_enabled(agent_id, db)
        ]
        
        if not legal_enabled_agents:
            raise Exception("No agents have legal research capability enabled")
        
        # Default sources
        if sources is None:
            sources = ["caselaw", "courtlistener", "serpapi"]
        
        # Log agent session
        from services.database import log_agent_session, SessionType, AnalysisType, complete_agent_session
        log_agent_session(
            session_id=session_id,
            session_type=SessionType.RAG_ANALYSIS,
            analysis_type=AnalysisType.RAG_ENHANCED,
            user_query=legal_query
        )
        
        self.load_selected_compliance_agents(legal_enabled_agents)
        
        try:
            # Step 1: Perform legal research
            print(f"Agent legal research starting for: {legal_query}")
            legal_results = self.legal_research_service.comprehensive_legal_search(
                query=legal_query,
                analyze_relevance=True,
                model_name=self.compliance_agents[0]["model_name"] if self.compliance_agents else "gpt-4"
            )
            
            # Step 2: Have agents analyze the legal findings
            agent_analyses = {}
            for agent in self.compliance_agents:
                try:
                    # Prepare legal context for agent analysis
                    legal_context = self._prepare_legal_context(legal_results, legal_query)
                    
                    # Get agent's analysis of the legal research
                    analysis_prompt = f"""
                    You are a legal analysis agent. Based on the legal research conducted, provide your expert analysis.
                    
                    Research Query: {legal_query}
                    
                    Legal Research Results:
                    {legal_context}
                    
                    Please provide:
                    1. Key legal findings and precedents
                    2. Relevant case law analysis
                    3. Legal implications and recommendations
                    4. Jurisdictional considerations
                    """
                    
                    # Use agent's existing prompt template as context
                    formatted_prompt = agent["user_prompt_template"].replace(
                        "{data_sample}", analysis_prompt
                    )
                    full_prompt = f"{agent['system_prompt']}\n\n{formatted_prompt}"
                    
                    # Get LLM and invoke
                    llm = self.get_llm_for_agent(agent["model_name"])
                    from langchain_core.messages import HumanMessage
                    response = llm.invoke([HumanMessage(content=full_prompt)])
                    
                    analysis_text = response.content if hasattr(response, 'content') else str(response)
                    agent_analyses[agent["name"]] = analysis_text
                    
                    # Log agent response
                    log_agent_response(
                        session_id=session_id,
                        agent_id=agent["id"],
                        response_text=analysis_text,
                        processing_method="legal_research_analysis",
                        response_time_ms=int((time.time() - start_time) * 1000),
                        model_used=agent["model_name"],
                        analysis_summary=f"Legal research analysis for: {legal_query}"
                    )
                    
                except Exception as e:
                    agent_analyses[agent["name"]] = f"Error in legal analysis: {str(e)}"
                    print(f"Error in agent legal analysis: {e}")
            
            # Step 3: Store legal research results in ChromaDB
            stored_docs = 0
            storage_results = {}
            
            if legal_results["cases"]:
                try:
                    storage_results = self._store_legal_results_in_chromadb(
                        legal_results, legal_query, collection_name, agent_analyses
                    )
                    stored_docs = storage_results.get("documents_stored", 0)
                except Exception as e:
                    storage_results = {"error": f"Failed to store in ChromaDB: {str(e)}"}
                    print(f"Error storing legal results: {e}")
            
            total_time = int((time.time() - start_time) * 1000)
            
            # Complete session
            complete_agent_session(
                session_id=session_id,
                overall_result={
                    "legal_research": legal_results,
                    "agent_analyses": agent_analyses,
                    "storage_results": storage_results
                },
                agent_count=len(agent_ids),
                total_response_time_ms=total_time,
                status='completed'
            )
            
            return {
                "session_id": session_id,
                "legal_query": legal_query,
                "legal_research_results": legal_results,
                "agent_analyses": agent_analyses,
                "storage_results": storage_results,
                "documents_stored": stored_docs,
                "collection_name": collection_name,
                "total_time_ms": total_time
            }
            
        except Exception as e:
            # Complete session with error
            complete_agent_session(
                session_id=session_id,
                overall_result={"error": str(e)},
                agent_count=len(agent_ids),
                total_response_time_ms=int((time.time() - start_time) * 1000),
                status='error'
            )
            raise e
    
    def _prepare_legal_context(self, legal_results: Dict[str, Any], query: str) -> str:
        """Prepare legal research context for agent analysis"""
        context = f"Query: {query}\n"
        context += f"Total cases found: {legal_results['total_cases_found']}\n\n"
        
        # Add top 5 most relevant cases
        top_cases = legal_results["cases"][:5]
        for i, case in enumerate(top_cases, 1):
            context += f"Case {i}: {case['title']}\n"
            context += f"Court: {case['court']}\n"
            context += f"Date: {case['date']}\n"
            context += f"Citation: {case['citation']}\n"
            context += f"Relevance: {case['relevance_score']:.1%}\n"
            context += f"Summary: {case['snippet']}\n"
            context += f"URL: {case['url']}\n\n"
        
        return context
    
    def _store_legal_results_in_chromadb(self, legal_results: Dict[str, Any], 
                                       query: str, collection_name: str,
                                       agent_analyses: Dict[str, str]) -> Dict[str, Any]:
        """Store legal research results and agent analyses in ChromaDB"""
        import requests
        
        chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
        
        documents = []
        metadatas = []
        ids = []
        
        # Store legal cases
        for i, case in enumerate(legal_results["cases"][:10]):  # Top 10 cases
            doc_id = f"legal_case_{hash(case['title']) % 100000}_{i}"
            
            # Create document content with case details
            content = f"# {case['title']}\n\n"
            content += f"**Court:** {case['court']}\n"
            content += f"**Date:** {case['date']}\n"
            content += f"**Citation:** {case['citation']}\n"
            content += f"**Relevance Score:** {case['relevance_score']:.1%}\n\n"
            content += f"**Case Summary:**\n{case['snippet']}\n\n"
            content += f"**Source Query:** {query}\n"
            content += f"**URL:** {case['url']}\n"
            
            documents.append(content)
            metadatas.append({
                "source": "agent_legal_research",
                "query": query,
                "case_title": case['title'],
                "court": case['court'],
                "date": case['date'],
                "citation": case['citation'],
                "relevance_score": case['relevance_score'],
                "url": case['url'],
                "document_type": "legal_case",
                "created_at": datetime.now().isoformat()
            })
            ids.append(doc_id)
        
        # Store agent analyses as separate documents
        for agent_name, analysis in agent_analyses.items():
            doc_id = f"agent_analysis_{hash(f'{agent_name}_{query}') % 100000}"
            
            content = f"# Agent Legal Analysis: {agent_name}\n\n"
            content += f"**Research Query:** {query}\n"
            content += f"**Analysis Date:** {datetime.now().isoformat()}\n\n"
            content += f"**Agent Analysis:**\n{analysis}\n"
            
            documents.append(content)
            metadatas.append({
                "source": "agent_legal_analysis",
                "query": query,
                "agent_name": agent_name,
                "document_type": "agent_analysis",
                "created_at": datetime.now().isoformat()
            })
            ids.append(doc_id)
        
        # Store in ChromaDB
        payload = {
            "collection_name": collection_name,
            "documents": documents,
            "metadatas": metadatas,
            "ids": ids
        }
        
        response = requests.post(
            f"{chroma_url}/documents/add",
            json=payload,
            timeout=30
        )
        
        if response.ok:
            return {
                "success": True,
                "documents_stored": len(documents),
                "legal_cases_stored": len(legal_results["cases"][:10]),
                "agent_analyses_stored": len(agent_analyses),
                "collection_name": collection_name
            }
        else:
            raise Exception(f"Failed to store in ChromaDB: {response.text}")


    def run_debate(self, session_id: str, data_sample: str, db: Session) -> Dict[str, str]:
        """Run debate sequence - WORKS with unified LLM path"""
        agents = self._load_debate_agents(session_id)
        results = {}
        
        print(f"Starting debate with {len(agents)} agents")
        
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._debate, agent, data_sample, session_id, db, idx+1): agent["name"] 
                for idx, agent in enumerate(agents)
            }
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                
        print(f"Debate completed: {len(results)} responses")
        return results

    def _load_debate_agents(self, session_id: str) -> List[Dict[str, Any]]:
        """Load debate agents in order - NO CHANGE needed"""
        session = SessionLocal()
        debate_agents = []
        try:
            records = session.query(DebateSession).filter(
                DebateSession.session_id == session_id
            ).order_by(DebateSession.debate_order).all()
            
            for record in records:
                agent = record.compliance_agent
                model_name = agent.model_name.lower()
                
                debate_agents.append({
                    "id": agent.id,
                    "name": agent.name,
                    "model_name": model_name,
                    "system_prompt": agent.system_prompt,
                    "user_prompt_template": agent.user_prompt_template
                })
                
        finally:
            session.close()
        return debate_agents

    def _debate(self, agent: Dict[str, Any], data_sample: str, session_id: str, db: Session, sequence_order: int = None) -> str:
        """Single debate round - WORKS with unified LLM path"""
        start_time = time.time()
        
        try:
            model_name = agent["model_name"]
            
            # Get LLM using the SAME method as Direct Chat
            llm = self.get_llm_for_agent(model_name)
            
            # Build prompt for debate context
            formatted_user_prompt = agent["user_prompt_template"].replace("{data_sample}", data_sample)
            full_prompt = f"{agent['system_prompt']}\n\n{formatted_user_prompt}"
            
            # Call LLM (same as Direct Chat)
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=full_prompt)])
            
            # Handle response (same as Direct Chat)
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
                
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Log debate response
            log_agent_response(
                session_id=session_id,
                agent_id=agent["id"],
                response_text=response_text,
                processing_method="debate_unified",
                response_time_ms=response_time_ms,
                model_used=agent["model_name"],
                sequence_order=sequence_order
            )
            
            log_compliance_result(
                agent_id=agent["id"],
                data_sample=data_sample,
                confidence_score=None,
                reason="Debate response",
                raw_response=response_text,
                processing_method="debate_unified",
                response_time_ms=response_time_ms,
                model_used=agent["model_name"],
                session_id=session_id
            )
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error during debate with {agent['name']}: {str(e)}"
            print(f"Error in _debate: {e}")
            return error_msg