"""
Citation Service

This module provides business logic for RAG citation operations, replacing
the utility functions from database.py with repository-based implementations.

Provides backward-compatible function signatures for existing code.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from repositories import UnitOfWork
from models.citation import RAGCitation

logger = logging.getLogger("CITATION_SERVICE")


class CitationService:
    """
    Service layer for RAG citation operations.

    Provides business logic for:
    - Bulk citation creation
    - Citation retrieval by response/session
    - Quality tier filtering
    """

    def __init__(self, db: Session):
        """
        Initialize the citation service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.uow = UnitOfWork(db)

    def log_rag_citations(
        self,
        agent_response_id: int,
        metadata_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Log RAG citation metadata for explainability and audit trail.

        Backward-compatible with database.py's log_rag_citations function.

        Args:
            agent_response_id: The ID of the agent response this citation belongs to
            metadata_list: List of citation metadata dicts from RAG service

        Returns:
            True if successful, False otherwise

        Example metadata structure:
            {
                'document_index': 1,
                'distance': 0.234,
                'similarity_score': 0.876,  # Optional for backward compatibility
                'similarity_percentage': 87.6,  # Optional
                'excerpt': 'First 300 chars...',
                'full_length': 1500,
                'quality_tier': 'High',
                'metadata': {
                    'document_name': 'file.pdf',
                    'page_number': 5,
                    'section_title': 'Chapter 2'
                }
            }
        """
        try:
            success = self.uow.citations.bulk_create_citations(
                agent_response_id=agent_response_id,
                metadata_list=metadata_list
            )
            if success:
                self.uow.commit()
                logger.info(f"Successfully logged {len(metadata_list)} citations for response {agent_response_id}")
            return success
        except Exception as e:
            logger.error(f"Error logging RAG citations: {e}")
            self.uow.rollback()
            return False

    def get_rag_citations(self, agent_response_id: int) -> List[Dict[str, Any]]:
        """
        Get all RAG citations for a specific agent response.

        Backward-compatible with database.py's get_rag_citations function.

        Args:
            agent_response_id: The ID of the agent response

        Returns:
            List of citation dictionaries
        """
        try:
            return self.uow.citations.get_by_response_id(agent_response_id)
        except Exception as e:
            logger.error(f"Error retrieving RAG citations: {e}")
            return []

    def get_session_citations(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all RAG citations for all responses in a session.

        Backward-compatible with database.py's get_session_citations function.

        Args:
            session_id: The session ID

        Returns:
            List of citation dictionaries with response info
        """
        try:
            return self.uow.citations.get_by_session_id(session_id)
        except Exception as e:
            logger.error(f"Error retrieving session citations: {e}")
            return []

    def get_top_citations(
        self,
        agent_response_id: int,
        limit: int = 5
    ) -> List[RAGCitation]:
        """
        Get top N citations by similarity (lowest distance) for a response.

        Args:
            agent_response_id: Agent response identifier
            limit: Number of top citations to retrieve

        Returns:
            List of RAGCitation objects ordered by distance (ascending)
        """
        try:
            return self.uow.citations.get_top_citations(
                agent_response_id=agent_response_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving top citations: {e}")
            return []

    def get_citations_by_quality(
        self,
        quality_tier: str,
        limit: int = 100
    ) -> List[RAGCitation]:
        """
        Get citations by quality tier.

        Args:
            quality_tier: Quality tier ('Excellent', 'High', 'Good', 'Fair', 'Low')
            limit: Maximum number of citations

        Returns:
            List of RAGCitation objects
        """
        try:
            return self.uow.citations.get_by_quality_tier(
                quality_tier=quality_tier,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error retrieving citations by quality: {e}")
            return []


# Backward-compatible module-level functions
def log_rag_citations(
    agent_response_id: int,
    metadata_list: List[Dict[str, Any]]
) -> bool:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using CitationService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = CitationService(db)
        return service.log_rag_citations(
            agent_response_id=agent_response_id,
            metadata_list=metadata_list
        )
    finally:
        db.close()


def get_rag_citations(agent_response_id: int) -> List[Dict[str, Any]]:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using CitationService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = CitationService(db)
        return service.get_rag_citations(agent_response_id)
    finally:
        db.close()


def get_session_citations(session_id: str) -> List[Dict[str, Any]]:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using CitationService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = CitationService(db)
        return service.get_session_citations(session_id)
    finally:
        db.close()
