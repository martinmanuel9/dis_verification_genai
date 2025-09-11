# services/multi_agent_test_plan_service.py
"""
Multi-Agent Test Plan Generation Service - Based on mil_test_plan_gen.ipynb

Architecture:
1. Multiple Actor Agents per section using GPT-4 (can scale by adding more agents)
2. Critic Agent synthesizes actor outputs per section using GPT-4 
3. Final Critic Agent consolidates all sections using GPT-4
4. Redis Pipeline for intermediate storage and scaling
5. ChromaDB integration for section retrieval
"""

import json
import logging
import os
import re
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import redis
import requests
from docx import Document
import base64
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import asyncio

from services.llm_service import LLMService

logger = logging.getLogger(__name__)

@dataclass
class ActorResult:
    """Result from a single actor agent"""
    agent_id: str
    model_name: str
    section_title: str
    rules_extracted: str
    processing_time: float

@dataclass
class CriticResult:
    """Result from critic agent synthesis"""
    section_title: str
    synthesized_rules: str
    dependencies: List[str]
    conflicts: List[str]
    test_procedures: List[Dict[str, Any]]
    actor_count: int

@dataclass
class FinalTestPlan:
    """Final consolidated test plan"""
    title: str
    pipeline_id: str
    total_sections: int
    total_requirements: int
    total_test_procedures: int
    consolidated_markdown: str
    processing_status: str
    sections: List[CriticResult]
    # Models actually used in this run (for reporting/UI)
    actor_models: List[str] | None = None
    critic_model: str | None = None
    final_critic_model: str | None = None

class MultiAgentTestPlanService:
    def __init__(self, llm_service: LLMService, chroma_url: str):
        self.llm_service = llm_service
        self.chroma_url = chroma_url.rstrip("/")
        
        # Redis setup for pipeline
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Agent configuration using GPT-4 (scalable via env)
        # Configure actors by comma-separated ACTOR_MODELS (e.g., "gpt-4,gpt-4o-mini")
        # or by ACTOR_AGENT_COUNT (repeats "gpt-4" N times). Defaults to 3 GPT-4 actors.
        actor_models_env = os.getenv("ACTOR_MODELS")
        if actor_models_env:
            self.actor_models = [m.strip() for m in actor_models_env.split(",") if m.strip()]
        else:
            try:
                count = int(os.getenv("ACTOR_AGENT_COUNT", "3"))
            except ValueError:
                count = 3
            base_model = os.getenv("ACTOR_BASE_MODEL", "gpt-4")
            self.actor_models = [base_model for _ in range(max(1, count))]

        self.critic_model = os.getenv("CRITIC_MODEL", "gpt-4")
        self.final_critic_model = os.getenv("FINAL_CRITIC_MODEL", self.critic_model)

        # Keep originals for potential fallback logging
        self._original_actor_models = list(self.actor_models)
        self._original_critic_model = self.critic_model

        # Pipeline retention (seconds). Keep progress so UI can re-open later.
        try:
            self.pipeline_ttl_seconds = int(os.getenv("PIPELINE_TTL_SECONDS", str(60 * 60 * 24 * 7)))  # 7 days
        except ValueError:
            self.pipeline_ttl_seconds = 60 * 60 * 24 * 7
        
        logger.info(f"MultiAgentTestPlanService initialized with {len(self.actor_models)} GPT-4 actor agents")
        self._test_redis_connection()
        
        # Timeouts (tunable via env to accommodate slower local models like Ollama)
        # Total time to wait for all actor futures in a section (seconds)
        try:
            self.actor_collect_timeout = int(os.getenv("ACTOR_COLLECT_TIMEOUT_SEC", "900"))
        except Exception:
            self.actor_collect_timeout = 900
        # Per-actor result timeout when fetching future.result (seconds)
        try:
            self.actor_result_timeout = int(os.getenv("ACTOR_RESULT_TIMEOUT_SEC", "600"))
        except Exception:
            self.actor_result_timeout = 600
    
    def _test_redis_connection(self):
        """Test Redis connection and setup pipeline keys"""
        try:
            self.redis_client.ping()
            logger.info("Redis connection successful")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
    
    def generate_multi_agent_test_plan(self, 
                                     source_collections: List[str], 
                                     source_doc_ids: List[str],
                                     doc_title: str = "Test Plan") -> FinalTestPlan:
        """
        Main entry point for multi-agent test plan generation
        """
        logger.info("=== STARTING MULTI-AGENT TEST PLAN GENERATION ===")
        start_time = time.time()
        
        # Generate unique pipeline ID for this run
        pipeline_id = f"pipeline_{uuid.uuid4().hex[:12]}"
        
        try:
            # 0. Validate model availability and fallback to llama if needed
            self._maybe_fallback_to_llama(pipeline_id)

            # 1. Extract document sections from ChromaDB
            sections = self._extract_document_sections(source_collections, source_doc_ids)
            
            # Last-resort sectioning if nothing extracted: reconstruct and size-split
            if not sections:
                logger.warning("No sections extracted; attempting last-resort reconstruction + size split")
                sections = self._last_resort_build_sections(source_collections, source_doc_ids)
            
            # If still empty, record a FALLBACK pipeline and return fallback plan (with pipeline_id)
            if not sections:
                logger.error("No sections could be extracted; returning FALLBACK plan")
                # Initialize minimal pipeline meta so UI can track FALLBACK
                try:
                    self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                        "id": pipeline_id,
                        "title": doc_title,
                        "status": "FALLBACK",
                        "total_sections": 0,
                        "sections_processed": 0,
                        "created_at": datetime.now().isoformat(),
                        "completed_at": datetime.now().isoformat(),
                        "actor_agents": len(self.actor_models),
                    })
                    self.redis_client.zadd("pipeline:recent", {pipeline_id: time.time()})
                except Exception as e:
                    logger.warning(f"Failed to record FALLBACK pipeline meta: {e}")
                return self._create_fallback_test_plan(doc_title, pipeline_id=pipeline_id)
            
            logger.info(f"Processing {len(sections)} sections with multi-agent pipeline")
            
            # 2. Initialize Redis pipeline for this run
            self._initialize_pipeline(pipeline_id, sections, doc_title)
            # Record model configuration in meta for UI
            try:
                self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                    "actor_models": json.dumps(self.actor_models),
                    "critic_model": self.critic_model,
                    "final_critic_model": self.final_critic_model,
                })
            except Exception:
                pass
            
            # 3. Mark pipeline as processing
            try:
                self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                    "status": "PROCESSING"
                })
                self.redis_client.zadd("pipeline:processing", {pipeline_id: time.time()})
            except Exception as e:
                logger.warning(f"Failed to mark pipeline processing: {e}")

            # 4. Deploy actor agents for each section (parallel processing)
            # Sort sections to preserve numeric outline order when present
            ordered_sections = self._sort_sections_by_numeric_index(sections)
            section_results = self._deploy_section_agents(pipeline_id, ordered_sections)
            
            # 5. Deploy final critic agent to consolidate everything
            # If aborted, do not run final critic; return partial/aborted plan
            if self._is_aborted(pipeline_id):
                logger.warning(f"Pipeline {pipeline_id} aborted; skipping final critic")
                self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                    "status": "ABORTED",
                    "completed_at": datetime.now().isoformat(),
                })
                self.redis_client.zrem("pipeline:processing", pipeline_id)
                aborted_markdown = f"# {doc_title}\n\nProcess aborted. {len(section_results)} sections completed before abort."
                final_plan = FinalTestPlan(
                    title=doc_title,
                    pipeline_id=pipeline_id,
                    total_sections=len(section_results),
                    total_requirements=sum(len(r.test_procedures) for r in section_results),
                    total_test_procedures=sum(len(r.test_procedures) for r in section_results),
                    consolidated_markdown=aborted_markdown,
                    processing_status="ABORTED",
                    sections=section_results,
                    actor_models=self.actor_models,
                    critic_model=self.critic_model,
                    final_critic_model=self.final_critic_model,
                )
                # If purge_on_abort flag set, purge all keys except abort flag
                try:
                    meta = self.redis_client.hgetall(f"pipeline:{pipeline_id}:meta") or {}
                    if meta.get("purge_on_abort") == "1":
                        self._purge_pipeline_keys(pipeline_id)
                except Exception as e:
                    logger.warning(f"Purge on abort failed: {e}")
            else:
                final_plan = self._deploy_final_critic_agent(pipeline_id, section_results, doc_title)
            
            # 6. Mark pipeline for retention (do not hard-delete so UI can view progress)
            self._cleanup_pipeline(pipeline_id)
            # Remove from processing set
            try:
                self.redis_client.zrem("pipeline:processing", pipeline_id)
            except Exception:
                pass
            
            elapsed_time = time.time() - start_time
            logger.info(f"Multi-agent test plan generation completed in {elapsed_time:.2f}s")
            
            return final_plan
            
        except Exception as e:
            logger.error(f"Multi-agent test plan generation failed: {e}")
            self._cleanup_pipeline(pipeline_id)
            try:
                self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                    "status": "FAILED",
                    "error": str(e)
                })
                self.redis_client.zrem("pipeline:processing", pipeline_id)
            except Exception:
                pass
            return self._create_fallback_test_plan(doc_title, pipeline_id=pipeline_id)
    
    def _extract_document_sections(self, source_collections: List[str], source_doc_ids: List[str]) -> Dict[str, str]:
        """Extract sections from ChromaDB with caching and performance optimizations.

        Strategy:
        - Check section cache first for identical requests
        - If explicit document IDs are provided, reconstruct full document(s) and split into natural sections.
        - Otherwise, group by metadata-based 'section_title' or page and combine chunks.
        """
        # OPTIMIZATION: Check cache first
        # Note: Accessing document service cache through the multi-agent service would require refactoring
        # For now, we'll focus on other optimizations
        
        sections: Dict[str, str] = {}

        # 1) Preferred path: reconstruct by provided document IDs
        if source_doc_ids:
            for collection_name in source_collections:
                for doc_id in source_doc_ids:
                    try:
                        resp = requests.get(
                            f"{self.chroma_url}/documents/reconstruct/{doc_id}",
                            params={"collection_name": collection_name},
                            timeout=180,
                        )
                        if not resp.ok:
                            logger.warning(f"Reconstruct failed for doc_id={doc_id} in {collection_name}: {resp.status_code}")
                            continue
                        data = resp.json()
                        content = data.get("reconstructed_content") or ""
                        doc_name = data.get("document_name") or str(doc_id)
                        if content and len(content.strip()) > 50:
                            self._create_document_sections(doc_name, content, sections)
                            logger.info(f"Reconstructed {doc_name}: sections now {len(sections)}")
                    except Exception as e:
                        logger.error(f"Reconstruct error for {doc_id} in {collection_name}: {e}")

            if sections:
                logger.info(f"Extracted {len(sections)} sections via reconstruct path")
                return sections

        # 2) Fallback path: metadata grouping from the collection
        for collection_name in source_collections:
            try:
                response = requests.get(
                    f"{self.chroma_url}/documents",
                    params={"collection_name": collection_name},
                    timeout=60
                )

                if not response.ok:
                    logger.error(f"Failed to fetch from collection {collection_name}")
                    continue

                data = response.json()
                docs = data.get("documents", [])
                metas = data.get("metadatas", [])
                ids = data.get("ids", [])

                logger.info(f"Collection {collection_name} has {len(docs)} documents")

                # Group by document and section with improved metadata handling
                document_sections: Dict[str, List[str]] = {}
                for doc_id, doc, meta in zip(ids, docs, metas):
                    doc_name = (
                        (meta.get("document_name") or meta.get("filename") or meta.get("source"))
                        or doc_id
                    )

                    section_title = (
                        meta.get("section_title") or meta.get("heading") or meta.get("title")
                        or f"Section {meta.get('page_number', meta.get('page', 'Unknown'))}"
                    )

                    # Filter by explicit IDs if specified
                    if source_doc_ids:
                        if doc_id not in source_doc_ids and not any(str(x) in str(doc_name) for x in source_doc_ids):
                            continue

                    key = f"{doc_name} - {section_title}"
                    document_sections.setdefault(key, [])
                    document_sections[key].append(doc)

                # Combine chunks for each section
                for section_key, chunks in document_sections.items():
                    combined_content = "\n\n".join(chunk for chunk in chunks if chunk and chunk.strip())
                    if len(combined_content.strip()) > 100:  # Only substantial content
                        sections[section_key] = combined_content

            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {e}")

        logger.info(f"Extracted {len(sections)} sections for multi-agent processing (fallback path)")
        return sections

    def _parse_numeric_prefix(self, title: str) -> Optional[List[int]]:
        """Extract a numeric tuple from a leading outline like '1.2.3' in a section title.
        Handles keys such as 'DocName - 1.2 Title' by inspecting the part after the first ' - '."""
        try:
            import re
            core = title.split(' - ', 1)[-1].strip() if ' - ' in title else title.strip()
            m = re.match(r"^(\d+(?:\.\d+)*)\b", core)
            if not m:
                return None
            return [int(x) for x in m.group(1).split('.')]
        except Exception:
            return None

    def _sort_sections_by_numeric_index(self, sections: Dict[str, str]) -> Dict[str, str]:
        """Stable sort of sections by leading numeric outline. Items without numeric prefixes follow in original order."""
        from collections import OrderedDict
        items = list(sections.items())
        with_idx = []
        without_idx = []
        for k, v in items:
            idx = self._parse_numeric_prefix(k)
            (with_idx if idx is not None else without_idx).append((k, v, idx))
        with_idx.sort(key=lambda x: x[2])
        ordered = OrderedDict()
        for k, v, _ in with_idx + without_idx:
            ordered[k] = v
        return ordered

    def _create_document_sections(self, doc_name: str, full_document: str, sections: Dict[str, str]):
        """Create logical sections from a reconstructed full document using natural headers.

        - Prefer numbered headers, ALL-CAPS, APPENDIX/CHAPTER/SECTION markers
        - Split very large sections into sub-blocks to keep units testable
        """
        natural_sections = self._extract_natural_sections(full_document)

        # Capture distinct APPENDIX blocks if present
        appendix_pattern = re.compile(r"^APPENDIX\s+[A-Z](?:\s*[-–]\s*.*)?$", re.MULTILINE)
        appendix_matches = list(appendix_pattern.finditer(full_document))
        if appendix_matches:
            for idx, m in enumerate(appendix_matches):
                start = m.start()
                end = appendix_matches[idx + 1].start() if idx + 1 < len(appendix_matches) else len(full_document)
                title = m.group(0).strip()
                body = full_document[start:end].strip()
                if title not in natural_sections:
                    natural_sections[title] = body

        if len(natural_sections) > 1:
            for section_title, section_content in natural_sections.items():
                section_key = f"{doc_name} - {section_title}"
                content = (section_content or "").strip()
                if len(content) > 8000:
                    subsections = self._split_large_section_for_testing(content, section_title)
                    for subsection_title, subsection_content in subsections.items():
                        sections[f"{section_key} - {subsection_title}"] = subsection_content
                else:
                    sections[section_key] = content
        else:
            # Fallback to size-based split if no natural sections found
            if len(full_document) > 6000:
                parts = self._split_large_section_for_testing(full_document, "Complete Document")
                for idx, (t, c) in enumerate(parts.items(), start=1):
                    sections[f"{doc_name} - Part {idx}"] = c
            else:
                sections[f"{doc_name} - Complete Document"] = (full_document or "").strip()

    def _extract_natural_sections(self, document_text: str) -> Dict[str, str]:
        """Heuristic extraction of natural sections from text"""
        sections: Dict[str, str] = {}
        lines = document_text.split('\n')
        current_section_title = "Introduction"
        current_section_content: List[str] = []

        for line in lines:
            line_clean = line.strip()
            is_section_header = False
            header_title = ""

            if line_clean:
                # Markdown headings from reconstruction (##, ###)
                if line_clean.startswith("## ") or line_clean.startswith("### "):
                    is_section_header = True
                    # Keep original heading text
                    header_title = line_clean[3:].strip() if line_clean.startswith("## ") else line_clean[4:].strip()
                # Numbered sections like 1., 1.1, 2.3.4 followed by ALL CAPS words
                elif re.match(r'^\d+(\.\d+)*\.?\s+[A-Z][A-Z\s]+', line_clean):
                    is_section_header = True
                    header_title = line_clean
                # ALL CAPS short headers
                elif (line_clean.isupper() and len(line_clean.split()) <= 8 and len(line_clean) > 5 and not line_clean.endswith('.') and not line_clean.startswith(('THE ', 'THIS ', 'THESE '))):
                    is_section_header = True
                    header_title = line_clean
                # APPENDIX/CHAPTER/SECTION/PART
                elif line_clean.startswith(('APPENDIX', 'CHAPTER', 'SECTION', 'PART')):
                    is_section_header = True
                    header_title = line_clean
                # Short keyword headers
                elif (any(k in line_clean.upper() for k in ['REQUIREMENTS','SPECIFICATIONS','PROCEDURES','TESTING','CONFIGURATION']) and len(line_clean.split()) <= 6 and not line_clean.endswith('.') and (line_clean.startswith(tuple('0123456789')) or line_clean.isupper())):
                    is_section_header = True
                    header_title = line_clean

            if is_section_header and current_section_content:
                sections[current_section_title] = '\n'.join(current_section_content)
                current_section_title = header_title
                current_section_content = [line]
            elif is_section_header and not current_section_content:
                current_section_title = header_title
                current_section_content = [line]
            else:
                current_section_content.append(line)

        if current_section_content:
            sections[current_section_title] = '\n'.join(current_section_content)

        return sections

    def _split_large_section_for_testing(self, content: str, section_title: str) -> Dict[str, str]:
        """Split large sections into smaller units for more focused processing."""
        subsections: Dict[str, str] = {}

        # Numbered subsections first (e.g., 4.1, 4.2)
        subsection_pattern = re.compile(r'^(\d+\.\d+(?:\.\d+)*)\s+(.+)$', re.MULTILINE)
        matches = list(subsection_pattern.finditer(content))
        if len(matches) > 1:
            for i, match in enumerate(matches):
                start = match.start()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                subsection_num = match.group(1)
                subsection_name = match.group(2)[:50]
                subsection_content = content[start:end].strip()
                if len(subsection_content) > 500:
                    subsections[f"{subsection_num} {subsection_name}"] = subsection_content

        # Paragraph/block split fallback
        if not subsections:
            paragraphs = content.split('\n\n')
            current_block = ""
            block_num = 1
            for paragraph in paragraphs:
                if len(current_block + paragraph) > 5000:
                    if current_block.strip():
                        subsections[f"Block {block_num}"] = current_block.strip()
                        block_num += 1
                        current_block = paragraph + "\n\n"
                    else:
                        current_block += paragraph + "\n\n"
                else:
                    current_block += paragraph + "\n\n"
            if current_block.strip():
                subsections[f"Block {block_num}"] = current_block.strip()

        return subsections
    
    def _initialize_pipeline(self, pipeline_id: str, sections: Dict[str, str], doc_title: str):
        """Initialize Redis pipeline with sections and metadata"""
        # Pre-allocate a deterministic proposed document id for easier tracking in the UI
        proposed_doc_id = f"testplan_multiagent_{pipeline_id}"
        pipeline_data = {
            "id": pipeline_id,
            "title": doc_title,
            "status": "INITIALIZING",
            "total_sections": len(sections),
            "sections_processed": 0,
            "created_at": datetime.now().isoformat(),
            "actor_agents": len(self.actor_models),
            "proposed_document_id": proposed_doc_id,
            "doc_tracking": "INIT"
        }
        
        # Store pipeline metadata
        self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping=pipeline_data)
        # Track recent pipelines for quick listing in UI
        try:
            now_ts = time.time()
            self.redis_client.zadd("pipeline:recent", {pipeline_id: now_ts})
        except Exception as e:
            logger.warning(f"Failed to zadd pipeline: {e}")
        
        # Store sections for processing
        for idx, (section_title, section_content) in enumerate(sections.items()):
            section_data = {
                "title": section_title,
                "content": section_content,
                "status": "PENDING",
                "index": idx
            }
            self.redis_client.hset(f"pipeline:{pipeline_id}:section:{idx}", mapping=section_data)
        
        # Initialize result queues
        self.redis_client.delete(f"pipeline:{pipeline_id}:actor_results")
        self.redis_client.delete(f"pipeline:{pipeline_id}:critic_results")
        
        logger.info(f"Pipeline {pipeline_id} initialized with {len(sections)} sections")
    
    def _deploy_section_agents(self, pipeline_id: str, sections: Dict[str, str]) -> List[CriticResult]:
        """Deploy multiple agents per section with optimized parallel processing"""
        logger.info(f"Deploying agents for {len(sections)} sections")
        
        section_results = []
        
        # Optimize: Increase max_workers based on section count and available resources
        max_workers = min(32, max(16, len(sections) * 2))  # Scale workers with sections
        
        # Process sections in batches to avoid overwhelming the system
        batch_size = min(8, len(sections))  # Process in smaller batches
        section_items = list(sections.items())
        
        for batch_start in range(0, len(section_items), batch_size):
            batch_end = min(batch_start + batch_size, len(section_items))
            current_batch = section_items[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: sections {batch_start+1}-{batch_end}")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_section = {}
                
                for idx, (section_title, section_content) in enumerate(current_batch, batch_start):
                    # Respect abort flag: stop submitting new work
                    if self._is_aborted(pipeline_id):
                        logger.warning(f"Abort requested for pipeline {pipeline_id}; stopping new submissions at section {idx}")
                        # Mark remaining sections as aborted
                        for remaining_idx in range(idx, len(section_items)):
                            self.redis_client.hset(f"pipeline:{pipeline_id}:section:{remaining_idx}", "status", "ABORTED")
                        break
                    
                    future = executor.submit(
                        self._process_section_with_multi_agents, 
                        pipeline_id, idx, section_title, section_content
                    )
                    future_to_section[future] = (idx, section_title)
                
                # Collect results as they complete with extended timeout and graceful partial handling
                try:
                    for future in as_completed(future_to_section, timeout=max(900, len(current_batch)*300)):
                        idx, section_title = future_to_section[future]
                        try:
                            critic_result = future.result(timeout=max(600, len(current_batch)*120))
                            if critic_result:
                                section_results.append(critic_result)
                                logger.info(f"Section {idx+1}/{len(sections)} completed: {section_title}")
                            else:
                                logger.warning(f"Section {idx+1} failed or aborted: {section_title}")
                        except Exception as e:
                            logger.error(f"Section processing error for '{section_title}': {e}")
                except Exception as te:
                    # Timeout waiting for entire batch; collect any finished and continue to next batch
                    logger.warning(f"Batch processing timeout after {batch_end-batch_start} sections: {te}")
                    for fut, (idx, section_title) in future_to_section.items():
                        if fut.done():
                            try:
                                critic_result = fut.result(timeout=1)
                                if critic_result:
                                    section_results.append(critic_result)
                            except Exception:
                                pass
        
        logger.info(f"Completed processing {len(section_results)} sections")
        return section_results
    
    def _process_section_with_multi_agents(self, 
                                         pipeline_id: str, 
                                         section_idx: int,
                                         section_title: str, 
                                         section_content: str) -> Optional[CriticResult]:
        """Process a single section with optimized multi-agent workflow"""
        
        # Respect abort flag early
        if self._is_aborted(pipeline_id):
            self.redis_client.hset(f"pipeline:{pipeline_id}:section:{section_idx}", "status", "ABORTED")
            return None

        # Update section status
        self.redis_client.hset(f"pipeline:{pipeline_id}:section:{section_idx}", "status", "PROCESSING")
        
        try:
            # OPTIMIZATION: Reduce from 3 actors to 2 for faster processing
            effective_actors = min(2, len(self.actor_models))
            limited_models = self.actor_models[:effective_actors]
            
            # 1. Deploy optimized actor agents in parallel
            actor_results = self._run_actor_agents(section_title, section_content)
            
            # Store actor results in Redis (reduced storage with TTL)
            for result in actor_results[:2]:  # Only store first 2 results
                result_key = f"pipeline:{pipeline_id}:actor:{section_idx}:{result.agent_id}"
                result_data = {
                    "agent_id": result.agent_id,
                    "model_name": result.model_name,
                    "section_title": result.section_title,
                    "rules_extracted": result.rules_extracted[:3000],  # Truncate to reduce memory
                    "processing_time": result.processing_time
                }
                self.redis_client.hset(result_key, mapping=result_data)
                self.redis_client.expire(result_key, 7200)  # 2 hour TTL
            
            # 2. Deploy optimized critic agent
            critic_result = self._run_critic_agent(section_title, section_content, actor_results)
            
            # Store critic result in Redis
            if critic_result:
                critic_key = f"pipeline:{pipeline_id}:critic:{section_idx}"
                critic_data = {
                    "section_title": critic_result.section_title,
                    "synthesized_rules": critic_result.synthesized_rules,
                    "dependencies": json.dumps(critic_result.dependencies),
                    "conflicts": json.dumps(critic_result.conflicts),
                    "test_procedures": json.dumps(critic_result.test_procedures),
                    "actor_count": critic_result.actor_count
                }
                self.redis_client.hset(critic_key, mapping=critic_data)
                self.redis_client.expire(critic_key, 86400)  # 24 hour TTL
                
                # Update section status
                self.redis_client.hset(f"pipeline:{pipeline_id}:section:{section_idx}", "status", "COMPLETED")
                # Increment processed counter on meta
                try:
                    self.redis_client.hincrby(f"pipeline:{pipeline_id}:meta", "sections_processed", 1)
                except Exception:
                    pass
                
                return critic_result
            
        except Exception as e:
            logger.error(f"Error processing section {section_title}: {e}")
            self.redis_client.hset(f"pipeline:{pipeline_id}:section:{section_idx}", "status", "FAILED")
        
        return None
    

    def _is_aborted(self, pipeline_id: str) -> bool:
        try:
            return self.redis_client.get(f"pipeline:{pipeline_id}:abort") == "1"
        except Exception:
            return False
    
    def _run_actor_agents(self, section_title: str, section_content: str) -> List[ActorResult]:
        """Run optimized actor agents with reduced parallel calls and faster processing"""
        actor_results = []
        
        # OPTIMIZATION: Use only 2 actors instead of all for faster completion
        effective_models = self.actor_models[:2]
        
        with ThreadPoolExecutor(max_workers=min(4, len(effective_models))) as executor:
            futures = []
            
            for idx, model in enumerate(effective_models):
                agent_id = f"actor_{idx}_{uuid.uuid4().hex[:6]}"  # Shorter ID
                future = executor.submit(
                    self._run_single_actor, agent_id, model, section_title, section_content
                )
                futures.append(future)
            
            # Collect actor results with configurable timeouts
            try:
                for future in as_completed(futures, timeout=self.actor_collect_timeout):
                    try:
                        result = future.result(timeout=self.actor_result_timeout)
                        if result:
                            actor_results.append(result)
                    except Exception as e:
                        logger.error(f"Optimized actor agent failed: {e}")
            except Exception as te:
                # Timeout waiting for all actors; proceed with partial results
                logger.warning(f"Actor collection timeout for section '{section_title}': {te}")
                # Collect any already-finished futures safely
                for fut in futures:
                    if fut.done():
                        try:
                            result = fut.result(timeout=1)
                            if result:
                                actor_results.append(result)
                        except Exception:
                            pass
                # Optionally cancel remaining
                for fut in futures:
                    if not fut.done():
                        try:
                            fut.cancel()
                        except Exception:
                            pass
        
        logger.info(f"Completed {len(actor_results)} optimized actor agents for section: {section_title}")
        return actor_results
    
    
    def _run_single_actor(self, agent_id: str, model: str, section_title: str, section_content: str) -> Optional[ActorResult]:
        """Run a single optimized actor agent with shorter prompts for faster processing"""
        start_time = time.time()
        
        try:
            # OPTIMIZATION: Short and highly-constrained output for local models
            prompt = f"""Extract the essential, testable requirements from this section and produce a very concise test plan.

Section: {section_title}
Content: {section_content[:3000]}...

Rules:
- List at most 3-5 key requirements (bullets).
- Then list at most 5 numbered test procedures.
- Each procedure must be concise (<= 20 words) and actionable.
- No long explanations. Keep total output under 200 words.

Format:
## Requirements
- [Requirement]
- [Requirement]

## Test Procedures
1. [Step]
2. [Step]
"""
            
            response = self.llm_service.query_direct(
                model_name=model,
                query=prompt
            )[0]
            
            processing_time = time.time() - start_time
            
            return ActorResult(
                agent_id=agent_id,
                model_name=model,
                section_title=section_title,
                rules_extracted=response[:2000],  # Truncate for faster processing
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Optimized Actor {agent_id} failed: {e}")
            return None
    
    
    def _run_critic_agent(self, section_title: str, section_content: str, actor_results: List[ActorResult]) -> Optional[CriticResult]:
        """Run optimized critic agent with faster synthesis"""
        
        if not actor_results:
            logger.warning(f"No actor results to critique for section: {section_title}")
            return None
        
        try:
            # OPTIMIZATION: Combine actor outputs more efficiently
            combined_results = ""
            for result in actor_results[:2]:  # Only use first 2 results
                combined_results += f"\n{result.rules_extracted[:1000]}\n"  # Truncate each result
            
            # OPTIMIZATION: Keep synthesis brief and capped
            prompt = f"""Synthesize these requirements into a concise test plan section.

Section: {section_title}
Actor Results: {combined_results[:2000]}...

Rules:
- Summarize only the 3-5 most important requirements.
- Provide at most 5 numbered test procedures, each <= 20 words.
- Keep the entire section under 250 words.

Format:
## {section_title}
**Requirements:** [3-5 concise bullets]
**Test Procedures:**
1. [Short step]
2. [Short step]
"""
            
            response = self.llm_service.query_direct(
                model_name=self.critic_model,
                query=prompt
            )[0]
            
            # Simplified extraction for faster processing
            test_procedures = self._extract_test_procedures_fast(response)
            dependencies = []  # Skip dependency extraction for speed
            conflicts = []     # Skip conflict extraction for speed
            
            return CriticResult(
                section_title=section_title,
                synthesized_rules=response,
                dependencies=dependencies,
                conflicts=conflicts,
                test_procedures=test_procedures,
                actor_count=len(actor_results)
            )
            
        except Exception as e:
            logger.error(f"Optimized Critic agent failed for section {section_title}: {e}")
            return None
    
    
    def _extract_test_procedures_fast(self, markdown: str) -> List[Dict[str, Any]]:
        """Fast test procedure extraction"""
        procedures = []
        lines = markdown.split('\n')
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line):
                procedures.append({
                    "id": f"test_{len(procedures)+1}",
                    "description": line,
                    "type": "functional"
                })
                if len(procedures) >= 5:  # Limit to first 5 for brevity
                    break
        
        return procedures
    
    def _deploy_final_critic_agent(self, pipeline_id: str, section_results: List[CriticResult], doc_title: str) -> FinalTestPlan:
        """Deploy final GPT-4 critic agent to consolidate all sections"""
        logger.info("Deploying final GPT-4 critic agent for consolidation")
        
        try:
            # Sort results by numeric outline if present in titles
            def keyfn(sr: CriticResult):
                try:
                    import re
                    m = re.match(r"^(\d+(?:\.\d+)*)\b", sr.section_title.strip())
                    return [int(x) for x in m.group(1).split('.')] if m else [10**6]
                except Exception:
                    return [10**6]
            ordered_results = sorted(section_results, key=keyfn)
            # Prepare all section results for final critic
            sections_summary = []
            all_sections_content = ""
            
            for result in ordered_results:
                sections_summary.append({
                    "title": result.section_title,
                    "dependencies_count": len(result.dependencies),
                    "conflicts_count": len(result.conflicts),
                    "test_procedures_count": len(result.test_procedures),
                    "actor_count": result.actor_count
                })
                
                all_sections_content += f"\n\n## {result.section_title}\n"
                all_sections_content += result.synthesized_rules
                all_sections_content += "\n" + "="*60
            
            # OPTIMIZATION: Streamlined final critic prompt for faster processing and brevity
            prompt = f"""Create a concise test plan from these sections.

Title: {doc_title}
Sections: {len(ordered_results)}

{all_sections_content[:8000]}...

Rules:
- Keep the entire plan under 600 words total.
- For each section, list at most 5 procedures, each <= 20 words.
- Avoid verbosity; prefer imperative steps.

Format: Brief numbered sections with key procedures only."""
            
            response = self.llm_service.query_direct(
                model_name=self.final_critic_model,
                query=prompt
            )[0]
            
            # Apply final deduplication
            final_markdown = self._final_global_deduplicate(response)
            
            # Calculate totals
            total_requirements = sum(len(result.test_procedures) for result in ordered_results)
            total_test_procedures = total_requirements  # Each requirement becomes a test procedure
            
            # Store final result in Redis
            final_result_key = f"pipeline:{pipeline_id}:final_result"
            final_data = {
                "title": doc_title,
                "consolidated_markdown": final_markdown,
                "total_sections": len(ordered_results),
                "total_requirements": total_requirements,
                "total_test_procedures": total_test_procedures,
                "processing_status": "COMPLETED",
                "completed_at": datetime.now().isoformat()
            }
            self.redis_client.hset(final_result_key, mapping=final_data)
            # Update pipeline meta status and bump recency
            try:
                self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                    "status": "COMPLETED",
                    "completed_at": final_data["completed_at"],
                })
                self.redis_client.zadd("pipeline:recent", {pipeline_id: time.time()})
            except Exception as e:
                logger.warning(f"Failed to update pipeline meta completion: {e}")
            
            return FinalTestPlan(
                title=doc_title,
                pipeline_id=pipeline_id,
                total_sections=len(ordered_results),
                total_requirements=total_requirements,
                total_test_procedures=total_test_procedures,
                consolidated_markdown=final_markdown,
                processing_status="COMPLETED",
                sections=ordered_results,
                actor_models=self.actor_models,
                critic_model=self.critic_model,
                final_critic_model=self.final_critic_model,
            )
            
        except Exception as e:
            logger.error(f"Final GPT-4 critic agent failed: {e}")
            return FinalTestPlan(
                title=doc_title,
                pipeline_id=pipeline_id,
                total_sections=len(section_results),
                total_requirements=0,
                total_test_procedures=0,
                consolidated_markdown=f"# {doc_title}\n\nFinal critic agent failed: {str(e)}",
                processing_status="FAILED",
                sections=section_results
            )
    
    def _deduplicate_markdown(self, text: str) -> str:
        """Deduplicate sentences within markdown sections (from notebook)"""
        output = []
        section_boundary = lambda l: l.startswith("## ") or (l.startswith("**") and l.endswith("**"))
        
        def process_block(block):
            local_seen = set()
            for sentence in re.split(r'(?<=[.!?]) +', block):
                sent = sentence.strip()
                norm = re.sub(r'\s+', ' ', sent.lower())
                if not sent or norm in local_seen:
                    continue
                output.append(sent)
                local_seen.add(norm)
        
        current_block = []
        for line in text.split('\n'):
            if section_boundary(line):
                process_block(' '.join(current_block))
                current_block = []
                output.append(line)
            elif line.strip() == "":
                process_block(' '.join(current_block))
                current_block = []
                output.append(line)
            else:
                current_block.append(line.strip())
        
        process_block(' '.join(current_block))
        return '\n'.join(output)
    
    def _final_global_deduplicate(self, text: str) -> str:
        """Remove duplicate lines globally (from notebook)"""
        seen = set()
        out = []
        
        for line in text.split('\n'):
            sentences = re.split(r'(?<=[.!?]) +', line) if len(line) > 120 else [line]
            unique_sentences = []
            
            for s in sentences:
                norm = re.sub(r'\s+', ' ', s.strip().lower())
                if norm and norm not in seen:
                    unique_sentences.append(s)
                    seen.add(norm)
                elif not s.strip():
                    unique_sentences.append(s)
            
            joined = ' '.join(unique_sentences).strip()
            if joined or not line.strip():
                out.append(joined)
        
        return '\n'.join(out)
    
    def _extract_dependencies_from_markdown(self, markdown: str) -> List[str]:
        """Extract dependencies from markdown format"""
        dependencies = []
        in_dependencies = False
        
        for line in markdown.split('\n'):
            if line.strip().startswith('**Dependencies:**'):
                in_dependencies = True
                continue
            elif line.strip().startswith('**') and in_dependencies:
                break
            elif in_dependencies and line.strip().startswith('- '):
                dependencies.append(line.strip()[2:])
        
        return dependencies
    
    def _extract_conflicts_from_markdown(self, markdown: str) -> List[str]:
        """Extract conflicts from markdown format"""
        conflicts = []
        in_conflicts = False
        
        for line in markdown.split('\n'):
            if line.strip().startswith('**Conflicts:**'):
                in_conflicts = True
                continue
            elif line.strip().startswith('**') and in_conflicts:
                break
            elif in_conflicts and line.strip().startswith('- '):
                conflicts.append(line.strip()[2:])
        
        return conflicts
    
    def _extract_test_procedures_from_markdown(self, markdown: str) -> List[Dict[str, Any]]:
        """Extract test procedures from markdown format"""
        procedures = []
        in_test_rules = False
        
        for line in markdown.split('\n'):
            if line.strip().startswith('**Test Rules:**'):
                in_test_rules = True
                continue
            elif line.strip().startswith('**') and in_test_rules:
                break
            elif in_test_rules and re.match(r'^\d+\.', line.strip()):
                procedures.append({
                    "id": f"test_{len(procedures)+1}",
                    "description": line.strip(),
                    "type": "functional"
                })
        
        return procedures
    
    def _cleanup_pipeline(self, pipeline_id: str):
        """Mark pipeline keys with an expiration instead of hard deletion so UI can inspect later."""
        try:
            pattern = f"pipeline:{pipeline_id}:*"
            keys = self.redis_client.keys(pattern)
            for k in keys:
                try:
                    self.redis_client.expire(k, self.pipeline_ttl_seconds)
                except Exception:
                    pass
            # Also keep the meta record updated and expiring
            self.redis_client.expire(f"pipeline:{pipeline_id}:meta", self.pipeline_ttl_seconds)
            logger.info(f"Retained {len(keys)} Redis keys for pipeline {pipeline_id} with TTL={self.pipeline_ttl_seconds}s")
        except Exception as e:
            logger.error(f"Error retaining pipeline {pipeline_id}: {e}")

    def _purge_pipeline_keys(self, pipeline_id: str):
        try:
            pattern = f"pipeline:{pipeline_id}:*"
            keys = self.redis_client.keys(pattern) or []
            keep_key = f"pipeline:{pipeline_id}:abort"
            to_delete = [k for k in keys if k != keep_key]
            if to_delete:
                self.redis_client.delete(*to_delete)
            # Remove from index sets
            try:
                self.redis_client.zrem("pipeline:recent", pipeline_id)
                self.redis_client.zrem("pipeline:processing", pipeline_id)
            except Exception:
                pass
            logger.info(f"Purged pipeline {pipeline_id} keys: {len(to_delete)} deleted")
        except Exception as e:
            logger.error(f"Error purging pipeline {pipeline_id}: {e}")

    def cleanup_pipeline_all(self, pipeline_id: str, remove_generated: bool = True) -> Dict[str, Any]:
        """One-call cleanup: optionally remove generated doc from Chroma and purge all Redis keys for the pipeline."""
        result: Dict[str, Any] = {"pipeline_id": pipeline_id, "removed_doc": False, "purged": False}
        try:
            # Remove generated doc if requested
            if remove_generated:
                try:
                    meta = self.redis_client.hgetall(f"pipeline:{pipeline_id}:meta") or {}
                    doc_id = meta.get("generated_document_id")
                    collection = meta.get("collection", os.getenv("GENERATED_TESTPLAN_COLLECTION", "generated_test_plan"))
                    if doc_id:
                        try:
                            response = requests.post(
                                f"{self.chroma_url}/documents/remove",
                                json={"collection_name": collection, "ids": [doc_id]},
                                timeout=15,
                            )
                            result["removed_doc"] = bool(response.ok)
                            if not response.ok:
                                result["remove_error"] = response.text
                        except Exception as e:
                            result["remove_error"] = str(e)
                except Exception as e:
                    result["remove_error"] = str(e)

            # Purge Redis keys
            try:
                self._purge_pipeline_keys(pipeline_id)
                result["purged"] = True
            except Exception as e:
                result["purge_error"] = str(e)
        except Exception as e:
            result["error"] = str(e)
        return result

    def abort_pipeline(self, pipeline_id: str, purge: bool = True, remove_generated: bool = True) -> Dict[str, Any]:
        """Abort a running pipeline, optionally purge Redis keys and remove any generated doc in Chroma."""
        result = {"pipeline_id": pipeline_id, "aborted": False, "purged": False, "removed_doc": False}
        try:
            # Signal abort
            self.redis_client.set(f"pipeline:{pipeline_id}:abort", "1")
            self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={"status": "ABORTED"})
            result["aborted"] = True
        except Exception as e:
            logger.warning(f"Failed to set abort flag: {e}")

        # Remove generated doc if any
        if remove_generated:
            try:
                meta = self.redis_client.hgetall(f"pipeline:{pipeline_id}:meta") or {}
                doc_id = meta.get("generated_document_id")
                collection = meta.get("collection", os.getenv("GENERATED_TESTPLAN_COLLECTION", "generated_test_plan"))
                if doc_id:
                    try:
                        response = requests.post(
                            f"{self.chroma_url}/documents/remove",
                            json={"collection_name": collection, "ids": [doc_id]},
                            timeout=15,
                        )
                        if response.ok:
                            result["removed_doc"] = True
                        else:
                            logger.warning(f"Failed to remove generated doc {doc_id}: {response.status_code} {response.text}")
                    except Exception as e:
                        logger.warning(f"Remove generated doc error: {e}")
            except Exception as e:
                logger.warning(f"Could not read pipeline meta for removal: {e}")

        # Purge pipeline keys
        if purge:
            try:
                self._purge_pipeline_keys(pipeline_id)
                result["purged"] = True
            except Exception as e:
                logger.warning(f"Failed to purge pipeline keys: {e}")

        return result

    # ===========================
    # Model availability + fallback
    # ===========================
    def _maybe_fallback_to_llama(self, pipeline_id: str):
        """If OpenAI models are configured but unavailable or quota-exceeded, switch to llama models.

        Strategy:
        - If any actor/critic model starts with 'gpt' but OPEN_AI_API_KEY is missing -> fallback to llama
        - Else, attempt a very small direct query with critic model; on exception -> fallback to llama
        - Record fallback in Redis pipeline meta
        """
        try:
            needs_openai = any(str(m).lower().startswith("gpt") for m in (self.actor_models + [self.critic_model, self.final_critic_model]))
            if not needs_openai:
                return

            openai_key = os.getenv("OPEN_AI_API_KEY")
            if not openai_key:
                self._apply_llama_fallback(pipeline_id, reason="missing_openai_key")
                return

            # Quick probe with critic model
            try:
                # Keep it very short; do not log history
                _ = self.llm_service.query_direct(self.critic_model, "Return OK.", session_id=None, log_history=False)
                # If success, keep current models
                return
            except Exception as e:
                # Any failure here triggers fallback
                self._apply_llama_fallback(pipeline_id, reason=f"probe_failed: {str(e)[:120]}")
        except Exception as e:
            # Never fail generation due to fallback logic
            logger.warning(f"Model fallback check error: {e}")

    def _apply_llama_fallback(self, pipeline_id: str, reason: str = "unavailable"):
        try:
            logger.warning(f"Falling back to llama models due to: {reason}")
            self.actor_models = ["llama" for _ in self.actor_models]
            self.critic_model = "llama"
            self.final_critic_model = "llama"
            # Record in Redis
            self.redis_client.hset(f"pipeline:{pipeline_id}:meta", mapping={
                "model_fallback": "llama",
                "fallback_reason": reason,
                "original_actor_models": json.dumps(self._original_actor_models),
                "original_critic_model": self._original_critic_model,
                "actor_agents": len(self.actor_models),
            })
        except Exception as e:
            logger.warning(f"Failed to record model fallback: {e}")
    
    def _create_fallback_test_plan(self, doc_title: str, pipeline_id: Optional[str] = None) -> FinalTestPlan:
        """Create fallback test plan"""
        fallback_markdown = f"""# {doc_title}

## Fallback Mode Notice
This test plan was generated in fallback mode due to section extraction issues.

## Multi-Agent Architecture
- 3x GPT-4 Actor Agents per section
- 1x GPT-4 Critic Agent per section  
- 1x GPT-4 Final Critic Agent for consolidation
- Redis pipeline for scaling

## Next Steps
1. Fix ChromaDB section extraction
2. Verify collection names and document IDs
3. Re-run multi-agent pipeline with GPT-4 agents
"""
        
        return FinalTestPlan(
            title=doc_title,
            pipeline_id=pipeline_id or f"fallback_{uuid.uuid4().hex[:8]}",
            total_sections=0,
            total_requirements=0,
            total_test_procedures=0,
            consolidated_markdown=fallback_markdown,
            processing_status="FALLBACK",
            sections=[],
            actor_models=self.actor_models,
            critic_model=self.critic_model,
            final_critic_model=self.final_critic_model,
        )

    def _last_resort_build_sections(self, source_collections: List[str], source_doc_ids: List[str]) -> Dict[str, str]:
        """Attempt to reconstruct full documents and split into sections if standard extraction found nothing."""
        sections: Dict[str, str] = {}
        try:
            # Prefer explicit doc IDs
            if source_doc_ids:
                for collection_name in source_collections:
                    for doc_id in source_doc_ids:
                        try:
                            resp = requests.get(
                                f"{self.chroma_url}/documents/reconstruct/{doc_id}",
                                params={"collection_name": collection_name},
                                timeout=240,
                            )
                            if not resp.ok:
                                continue
                            data = resp.json()
                            content = (data.get("reconstructed_content") or "").strip()
                            name = data.get("document_name") or str(doc_id)
                            if content and len(content) > 50:
                                self._create_document_sections(name, content, sections)
                        except Exception:
                            continue
            # If still empty, try pulling a few documents from the collection and combine
            if not sections and source_collections:
                for collection_name in source_collections:
                    try:
                        response = requests.get(
                            f"{self.chroma_url}/documents",
                            params={"collection_name": collection_name},
                            timeout=60,
                        )
                        if not response.ok:
                            continue
                        data = response.json() or {}
                        docs = data.get("documents", [])
                        metas = data.get("metadatas", [])
                        ids = data.get("ids", [])
                        # Combine by document_name
                        by_doc: Dict[str, List[str]] = {}
                        for doc, meta in zip(docs, metas):
                            name = (meta.get("document_name") or meta.get("filename") or meta.get("source") or "Unknown")
                            by_doc.setdefault(name, []).append(doc)
                        for name, parts in list(by_doc.items())[:5]:
                            content = "\n\n".join([p for p in parts if p])
                            if content and len(content) > 50:
                                self._create_document_sections(name, content, sections)
                    except Exception:
                        continue
        except Exception:
            pass
        return sections
    
    def export_to_word(self, test_plan: FinalTestPlan) -> str:
        """Export test plan to Word document"""
        doc = Document()
        doc.add_heading(test_plan.title, level=0)
        
        # Add multi-agent architecture info
        doc.add_heading('Multi-Agent Architecture', level=2)
        doc.add_paragraph("This test plan was generated using:")
        # Use Word list formatting only; do not include literal bullet characters
        doc.add_paragraph("3x GPT-4 Actor Agents per section", style='List Bullet')
        doc.add_paragraph("1x GPT-4 Critic Agent per section for synthesis", style='List Bullet')  
        doc.add_paragraph("1x GPT-4 Final Critic Agent for consolidation", style='List Bullet')
        doc.add_paragraph("Redis pipeline for scalable processing", style='List Bullet')
        
        # Store test plan reference for detailed section processing
        self._current_test_plan = test_plan
        
        # Convert markdown to Word with detailed section-by-section format
        self._convert_markdown_to_docx(test_plan.consolidated_markdown, doc)
        
        # Clean up reference
        self._current_test_plan = None
        
        # Add statistics
        doc.add_heading('Test Plan Statistics', level=2)
        doc.add_paragraph(f"Total sections processed: {test_plan.total_sections}")
        doc.add_paragraph(f"Total requirements: {test_plan.total_requirements}")
        doc.add_paragraph(f"Total test procedures: {test_plan.total_test_procedures}")
        doc.add_paragraph(f"Processing status: {test_plan.processing_status}")
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Serialize and encode
        buf = io.BytesIO()
        doc.save(buf)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    
    def _convert_markdown_to_docx(self, markdown_content: str, doc: Document):
        """Convert markdown to detailed Word document with section-by-section requirements and test procedures"""
        
        # Instead of using the consolidated markdown, rebuild from individual sections
        # to preserve the detailed section-by-section format
        sections_processed = 0
        
        # Try to access individual sections from the test plan if available
        if hasattr(self, '_current_test_plan') and self._current_test_plan and hasattr(self._current_test_plan, 'sections'):
            sections = self._current_test_plan.sections
            
            for section_result in sections:
                sections_processed += 1
                
                # Add section header preserving original numbering when present
                section_title = section_result.section_title
                try:
                    import re as _re
                    m = _re.match(r"^\s*(\d+(?:\.\d+)+)\s+(.*)", section_title)
                    heading_text = f"{m.group(1)} {m.group(2)}" if m else section_title
                except Exception:
                    heading_text = section_title
                doc.add_heading(heading_text, level=1)
                
                # Add the original requirement text from the source document
                doc.add_heading("Requirement", level=2)
                # Get original content from the synthesized rules (contains source requirement)
                synthesized_content = section_result.synthesized_rules
                
                # Extract the main content (skip markdown formatting)
                requirement_text = self._extract_requirement_text(synthesized_content)
                doc.add_paragraph(requirement_text)
                
                # Add test procedures section
                doc.add_heading("Test Procedures", level=2)
                
                if section_result.test_procedures:
                    for i, procedure in enumerate(section_result.test_procedures, 1):
                        # Add each test procedure as a numbered item
                        procedure_text = procedure.get('description', str(procedure))
                        # Remove any existing numbering and add clean numbering
                        clean_procedure = procedure_text.lstrip('0123456789. ')
                        doc.add_paragraph(f"{i}. {clean_procedure}", style='List Number')
                else:
                    doc.add_paragraph("No specific test procedures defined for this requirement.")
                
                # Add dependencies if any
                if section_result.dependencies:
                    doc.add_heading("Dependencies", level=3)
                    for dep in section_result.dependencies:
                        doc.add_paragraph(f"• {dep}", style='List Bullet')
                
                # Add conflicts if any
                if section_result.conflicts:
                    doc.add_heading("Conflicts", level=3)
                    for conflict in section_result.conflicts:
                        doc.add_paragraph(f"• {conflict}", style='List Bullet')
                
                # Add spacing between sections
                doc.add_paragraph("")
        else:
            # Fallback to parsing markdown if sections not available
            lines = markdown_content.split('\n')
            current_section = None
            in_test_rules = False
            
            for line in lines:
                l = line.strip()
                if not l:
                    continue
                    
                if l.startswith('# '):
                    continue  # Skip main title as already added
                elif l.startswith('## '):  # Section heading
                    sections_processed += 1
                    section_name = l.replace("##", "").strip()
                    doc.add_heading(f"Section {sections_processed}: {section_name}", level=1)
                    current_section = section_name
                    in_test_rules = False
                elif l.startswith('**Original Requirement:**'):
                    doc.add_heading("Requirement", level=2)
                    requirement_text = l.replace('**Original Requirement:**', '').strip()
                    if requirement_text:
                        doc.add_paragraph(requirement_text)
                elif l.startswith('**Dependencies:**'):
                    doc.add_heading("Dependencies", level=3)
                elif l.startswith('**Conflicts:**'):
                    doc.add_heading("Conflicts", level=3)
                elif l.startswith('**Test Rules:**'):
                    doc.add_heading("Test Procedures", level=2)
                    in_test_rules = True
                elif l.startswith(("-", "*", "•")):
                    doc.add_paragraph(l.lstrip("-*• ").strip(), style='List Bullet')
                elif l[:1].isdigit() and l[1:2] in ('.', ')'):
                    if in_test_rules:
                        doc.add_paragraph(l, style='List Number')
                    else:
                        doc.add_paragraph(l)
                elif "**" in l:  # Handle bold text
                    parts = l.split("**")
                    p = doc.add_paragraph()
                    toggle = False
                    for part in parts:
                        run = p.add_run(part)
                        if toggle:
                            run.bold = True
                        toggle = not toggle
                else:
                    doc.add_paragraph(l)
    
    def _extract_requirement_text(self, synthesized_content: str) -> str:
        """Extract the original requirement text from synthesized markdown content"""
        
        # First, try to find the "Original Requirement:" section
        if "**Original Requirement:**" in synthesized_content:
            lines = synthesized_content.split('\n')
            requirement_lines = []
            in_requirement_section = False
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('**Original Requirement:**'):
                    in_requirement_section = True
                    # Include the requirement text on the same line if present
                    requirement_part = line.replace('**Original Requirement:**', '').strip()
                    if requirement_part:
                        requirement_lines.append(requirement_part)
                    continue
                elif line.startswith('**') and in_requirement_section:
                    # End of requirement section
                    break
                elif in_requirement_section and line:
                    requirement_lines.append(line)
            
            if requirement_lines:
                return ' '.join(requirement_lines).strip()
        
        # Fallback: extract content between section header and first major section
        lines = synthesized_content.split('\n')
        requirement_lines = []
        started = False
        
        for line in lines:
            line = line.strip()
            
            # Start after the section title
            if line.startswith('##'):
                started = True
                continue
            elif line.startswith(('**Dependencies:**', '**Conflicts:**', '**Test Rules:**')):
                break
            elif started and line and not line.startswith('**'):
                requirement_lines.append(line)
        
        requirement_text = ' '.join(requirement_lines).strip()
        return requirement_text if requirement_text else "Requirement text not available in synthesized content."
    
    def save_to_chromadb(self, test_plan: FinalTestPlan, session_id: str, pipeline_id: Optional[str] = None) -> Dict[str, Any]:
        """Save generated test plan to ChromaDB (single collection) with idempotency per pipeline.

        If a generated_document_id is already recorded in pipeline meta, re-use it and do not create a duplicate.
        """
        try:
            # First, ensure the target collection exists
            target_collection = os.getenv("GENERATED_TESTPLAN_COLLECTION", "generated_test_plan")
            self._ensure_collection_exists(target_collection)

            # Determine pipeline id
            pid = pipeline_id or getattr(test_plan, 'pipeline_id', None)

            # If a document was already saved for this pipeline, return that
            if pid:
                try:
                    meta = self.redis_client.hgetall(f"pipeline:{pid}:meta") or {}
                    existing_id = meta.get("generated_document_id")
                    if existing_id:
                        return {
                            "document_id": existing_id,
                            "collection_name": meta.get("collection", target_collection),
                            "saved": True,
                            "generated_at": meta.get("completed_at") or datetime.now().isoformat(),
                            "architecture": "multi_agent_gpt4",
                            "reused": True
                        }
                except Exception:
                    pass

                # Acquire a short-lived lock to avoid concurrent double-save
                try:
                    lock_key = f"pipeline:{pid}:saving_lock"
                    if not self.redis_client.set(lock_key, "1", nx=True, ex=60):
                        # Someone else is saving; wait briefly then return recorded id if present
                        time.sleep(1)
                        meta = self.redis_client.hgetall(f"pipeline:{pid}:meta") or {}
                        existing_id = meta.get("generated_document_id")
                        if existing_id:
                            return {
                                "document_id": existing_id,
                                "collection_name": meta.get("collection", target_collection),
                                "saved": True,
                                "generated_at": meta.get("completed_at") or datetime.now().isoformat(),
                                "architecture": "multi_agent_gpt4",
                                "reused": True
                            }
                except Exception:
                    pass

            # Update pipeline meta to reflect saving begins
            try:
                if pid:
                    self.redis_client.hset(f"pipeline:{pid}:meta", mapping={"doc_tracking": "SAVING"})
            except Exception:
                pass

            # Create document content
            doc_content = f"Title: {test_plan.title}\n\n"
            doc_content += f"Architecture: Multi-Agent GPT-4 Pipeline\n"
            doc_content += f"Sections: {test_plan.total_sections}\n"
            doc_content += f"Requirements: {test_plan.total_requirements}\n" 
            doc_content += f"Test Procedures: {test_plan.total_test_procedures}\n\n"
            doc_content += test_plan.consolidated_markdown
            
            # Prepare metadata
            metadata = {
                "title": test_plan.title,
                "type": "generated_test_plan",
                "architecture": "multi_agent_gpt4",
                "session_id": session_id,
                "generated_at": datetime.now().isoformat(),
                "total_sections": test_plan.total_sections,
                "total_requirements": test_plan.total_requirements,
                "total_test_procedures": test_plan.total_test_procedures,
                "processing_status": test_plan.processing_status,
                "agent_types": "3x_gpt4_actors_1x_gpt4_critic_1x_final_critic",
                "word_count": len(doc_content.split()),
                "char_count": len(doc_content)
            }
            
            # Generate deterministic document ID for this pipeline so UI can track it
            doc_id = f"testplan_multiagent_{(pid or session_id)}"
            
            # Save to ChromaDB
            payload = {
                "collection_name": target_collection, 
                "documents": [doc_content],
                "metadatas": [metadata],
                "ids": [doc_id]
            }
            
            response = requests.post(
                f"{self.chroma_url}/documents/add",
                json=payload,
                timeout=30
            )
            
            if response.ok:
                logger.info(f"Saved multi-agent test plan to ChromaDB ({target_collection}): {doc_id}")
                # Record generated doc in pipeline meta if pipeline_id provided
                try:
                    if pid:
                        self.redis_client.hset(f"pipeline:{pid}:meta", mapping={
                            "generated_document_id": doc_id,
                            "collection": target_collection,
                            "doc_tracking": "SAVED",
                        })
                        self.redis_client.zadd("pipeline:recent", {pid: time.time()})
                except Exception as e:
                    logger.warning(f"Failed to record generated doc in pipeline meta: {e}")

                return {
                    "document_id": doc_id,
                    "collection_name": target_collection,
                    "saved": True,
                    "generated_at": metadata["generated_at"],
                    "architecture": "multi_agent_gpt4"
                }
            else:
                logger.error(f"Failed to save to ChromaDB: {response.status_code} - {response.text}")
                return {"saved": False, "error": response.text}

        except Exception as e:
            logger.error(f"Error saving to ChromaDB: {e}")
            return {"saved": False, "error": str(e)}
    
    def _ensure_generated_documents_collection_exists(self):
        """Deprecated no-op: use _ensure_collection_exists with GENERATED_TESTPLAN_COLLECTION instead."""
        try:
            self._ensure_collection_exists(os.getenv("GENERATED_TESTPLAN_COLLECTION", "generated_test_plan"))
        except Exception:
            pass

    def _ensure_collection_exists(self, name: str):
        """Ensure an arbitrary collection exists."""
        try:
            list_response = requests.get(f"{self.chroma_url}/collections", timeout=10)
            if list_response.ok:
                collections = list_response.json().get("collections", [])
                if name not in collections:
                    requests.post(
                        f"{self.chroma_url}/collection/create",
                        params={"collection_name": name},
                        timeout=10
                    )
        except Exception as e:
            logger.warning(f"Unable to ensure collection {name}: {e}")
