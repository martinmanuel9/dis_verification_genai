"""
Compliance Service

This module provides business logic for compliance and agent response operations,
replacing the utility functions from database.py with repository-based implementations.

Provides backward-compatible function signatures for existing code.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging

from repositories import UnitOfWork
from models.response import ComplianceResult, AgentResponse
from models.agent import ComplianceAgent

logger = logging.getLogger("COMPLIANCE_SERVICE")


class ComplianceService:
    """
    Service layer for compliance and agent response operations.

    Provides business logic for:
    - Compliance result logging
    - Agent response logging
    - Agent performance tracking
    - Response retrieval
    """

    def __init__(self, db: Session):
        """
        Initialize the compliance service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.uow = UnitOfWork(db)

    def log_compliance_result(
        self,
        agent_id: int,
        data_sample: str,
        confidence_score: Optional[float],
        reason: str,
        raw_response: str,
        processing_method: str,
        response_time_ms: int,
        model_used: str,
        session_id: Optional[str] = None
    ) -> ComplianceResult:
        """
        Log a compliance result and update agent performance.

        Backward-compatible with database.py's log_compliance_result function.

        Args:
            agent_id: Agent identifier
            data_sample: Input data that was analyzed
            confidence_score: Confidence score
            reason: Reasoning for the result
            raw_response: Raw LLM response
            processing_method: Processing method used
            response_time_ms: Response time in milliseconds
            model_used: Model identifier
            session_id: Optional session identifier

        Returns:
            Created ComplianceResult
        """
        try:
            result = self.uow.compliance.create_result(
                agent_id=agent_id,
                data_sample=data_sample,
                confidence_score=confidence_score,
                reason=reason,
                raw_response=raw_response,
                processing_method=processing_method,
                response_time_ms=response_time_ms,
                model_used=model_used,
                session_id=session_id
            )

            # Update agent performance metrics
            self.update_agent_performance(agent_id, response_time_ms, success=True)

            self.uow.commit()
            logger.info(f"Compliance result logged: agent={agent_id}, session={session_id}")
            return result

        except Exception as e:
            logger.error(f"Error logging compliance result: {e}")
            self.uow.rollback()
            raise

    def log_agent_response(
        self,
        session_id: str,
        agent_id: int,
        response_text: str,
        processing_method: str,
        response_time_ms: int,
        model_used: str,
        sequence_order: Optional[int] = None,
        rag_used: bool = False,
        documents_found: int = 0,
        rag_context: Optional[str] = None,
        confidence_score: Optional[float] = None,
        analysis_summary: Optional[str] = None
    ) -> Optional[int]:
        """
        Log an individual agent response and return the response ID.

        Backward-compatible with database.py's log_agent_response function.

        Args:
            session_id: Session identifier
            agent_id: Agent identifier
            response_text: Response text
            processing_method: Method used for processing
            response_time_ms: Response time in milliseconds
            model_used: Model identifier
            sequence_order: Order in debate sequence
            rag_used: Whether RAG was used
            documents_found: Number of documents retrieved
            rag_context: Retrieved RAG context
            confidence_score: Confidence score
            analysis_summary: Analysis summary

        Returns:
            Agent response ID or None if failed
        """
        try:
            response = self.uow.responses.create_response(
                session_id=session_id,
                agent_id=agent_id,
                response_text=response_text,
                processing_method=processing_method,
                response_time_ms=response_time_ms,
                model_used=model_used,
                sequence_order=sequence_order,
                rag_used=rag_used,
                documents_found=documents_found,
                rag_context=rag_context,
                confidence_score=confidence_score,
                analysis_summary=analysis_summary
            )
            self.uow.commit()
            logger.info(f"Agent response logged: ID={response.id}, session={session_id}, agent={agent_id}")
            return response.id

        except Exception as e:
            logger.error(f"Error logging agent response: {e}")
            self.uow.rollback()
            return None

    def update_agent_performance(
        self,
        agent_id: int,
        response_time_ms: int,
        success: bool = True
    ) -> Optional[ComplianceAgent]:
        """
        Update agent performance metrics with optimized database access.

        Backward-compatible with database.py's update_agent_performance function.

        Args:
            agent_id: Agent identifier
            response_time_ms: Response time in milliseconds
            success: Whether the query was successful

        Returns:
            Updated ComplianceAgent or None if not found
        """
        try:
            agent = self.uow.agents.get(agent_id)
            if not agent:
                logger.warning(f"Agent {agent_id} not found for performance update")
                return None

            # Update total queries
            agent.total_queries = (agent.total_queries or 0) + 1

            # Update average response time (rolling average)
            if agent.avg_response_time_ms is None:
                agent.avg_response_time_ms = float(response_time_ms)
            else:
                total_time = agent.avg_response_time_ms * (agent.total_queries - 1) + response_time_ms
                agent.avg_response_time_ms = total_time / agent.total_queries

            # Update success rate (rolling average)
            if agent.success_rate is None:
                agent.success_rate = 1.0 if success else 0.0
            else:
                total_successes = agent.success_rate * (agent.total_queries - 1) + (1 if success else 0)
                agent.success_rate = total_successes / agent.total_queries

            # Save changes (don't commit here, let the caller manage the transaction)
            updated_agent = self.uow.agents.update(agent)

            logger.debug(
                f"Updated performance for agent {agent_id}: "
                f"queries={updated_agent.total_queries}, "
                f"avg_time={updated_agent.avg_response_time_ms:.1f}ms, "
                f"success_rate={updated_agent.success_rate:.2%}"
            )

            return updated_agent

        except Exception as e:
            logger.error(f"Error updating performance for agent {agent_id}: {e}")
            raise

    def get_compliance_results_by_session(
        self,
        session_id: str
    ) -> List[ComplianceResult]:
        """
        Get all compliance results for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of ComplianceResult objects
        """
        try:
            return self.uow.compliance.get_by_session(session_id)
        except Exception as e:
            logger.error(f"Error retrieving compliance results: {e}")
            return []

    def get_compliance_results_by_agent(
        self,
        agent_id: int,
        limit: int = 100
    ) -> List[ComplianceResult]:
        """
        Get compliance results by agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of results

        Returns:
            List of ComplianceResult objects
        """
        try:
            return self.uow.compliance.get_by_agent(agent_id, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving compliance results: {e}")
            return []

    def get_agent_responses_by_session(
        self,
        session_id: str
    ) -> List[AgentResponse]:
        """
        Get all agent responses for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of AgentResponse objects
        """
        try:
            return self.uow.responses.get_by_session(session_id)
        except Exception as e:
            logger.error(f"Error retrieving agent responses: {e}")
            return []

    def get_agent_responses_by_agent(
        self,
        agent_id: int,
        limit: int = 100
    ) -> List[AgentResponse]:
        """
        Get responses by agent.

        Args:
            agent_id: Agent identifier
            limit: Maximum number of responses

        Returns:
            List of AgentResponse objects
        """
        try:
            return self.uow.responses.get_by_agent(agent_id, limit=limit)
        except Exception as e:
            logger.error(f"Error retrieving agent responses: {e}")
            return []


# Backward-compatible module-level functions
def log_compliance_result(
    agent_id: int,
    data_sample: str,
    confidence_score: Optional[float],
    reason: str,
    raw_response: str,
    processing_method: str,
    response_time_ms: int,
    model_used: str,
    session_id: Optional[str] = None
) -> None:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using ComplianceService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = ComplianceService(db)
        service.log_compliance_result(
            agent_id=agent_id,
            data_sample=data_sample,
            confidence_score=confidence_score,
            reason=reason,
            raw_response=raw_response,
            processing_method=processing_method,
            response_time_ms=response_time_ms,
            model_used=model_used,
            session_id=session_id
        )
    finally:
        db.close()


def log_agent_response(
    session_id: str,
    agent_id: int,
    response_text: str,
    processing_method: str,
    response_time_ms: int,
    model_used: str,
    sequence_order: Optional[int] = None,
    rag_used: bool = False,
    documents_found: int = 0,
    rag_context: Optional[str] = None,
    confidence_score: Optional[float] = None,
    analysis_summary: Optional[str] = None
) -> Optional[int]:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using ComplianceService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = ComplianceService(db)
        return service.log_agent_response(
            session_id=session_id,
            agent_id=agent_id,
            response_text=response_text,
            processing_method=processing_method,
            response_time_ms=response_time_ms,
            model_used=model_used,
            sequence_order=sequence_order,
            rag_used=rag_used,
            documents_found=documents_found,
            rag_context=rag_context,
            confidence_score=confidence_score,
            analysis_summary=analysis_summary
        )
    finally:
        db.close()


def update_agent_performance(
    agent_id: int,
    response_time_ms: int,
    success: bool = True
) -> None:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using ComplianceService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = ComplianceService(db)
        service.update_agent_performance(
            agent_id=agent_id,
            response_time_ms=response_time_ms,
            success=success
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Performance update error for agent {agent_id}: {e}")
    finally:
        db.close()
