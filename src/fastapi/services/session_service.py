"""
Session Service

This module provides business logic for session operations, replacing
the utility functions from database.py with repository-based implementations.

Provides backward-compatible function signatures for existing code.
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from repositories import UnitOfWork
from models.enums import SessionType, AnalysisType
from models.session import AgentSession
from core.exceptions import NotFoundException

logger = logging.getLogger("SESSION_SERVICE")


class SessionService:
    """
    Service layer for session operations.

    Provides business logic for:
    - Session creation and completion
    - Session history retrieval
    - Session details with responses
    """

    def __init__(self, db: Session):
        """
        Initialize the session service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.uow = UnitOfWork(db)

    def log_agent_session(
        self,
        session_id: str,
        session_type: SessionType,
        analysis_type: AnalysisType,
        user_query: str,
        collection_name: Optional[str] = None
    ) -> AgentSession:
        """
        Log the start of an agent session.

        Backward-compatible with database.py's log_agent_session function.

        Args:
            session_id: Unique session identifier
            session_type: Type of session (SessionType enum)
            analysis_type: Type of analysis (AnalysisType enum)
            user_query: User's query
            collection_name: ChromaDB collection (for RAG sessions)

        Returns:
            Created AgentSession
        """
        try:
            session = self.uow.sessions.create_session(
                session_id=session_id,
                session_type=session_type,
                analysis_type=analysis_type,
                user_query=user_query,
                collection_name=collection_name
            )
            self.uow.commit()
            logger.info(f"Agent session logged: {session_id}, type: {session_type.value}")
            return session
        except Exception as e:
            logger.error(f"Error logging agent session: {e}")
            self.uow.rollback()
            raise

    def complete_agent_session(
        self,
        session_id: str,
        overall_result: Dict[str, Any],
        agent_count: int,
        total_response_time_ms: Optional[int] = None,
        status: str = 'completed',
        error_message: Optional[str] = None
    ) -> Optional[AgentSession]:
        """
        Mark an agent session as completed and log summary.

        Backward-compatible with database.py's complete_agent_session function.

        Args:
            session_id: Session identifier
            overall_result: Summary of results
            agent_count: Number of agents involved
            total_response_time_ms: Total processing time
            status: Final status ('completed', 'failed', etc.)
            error_message: Error message if failed

        Returns:
            Updated AgentSession or None if not found
        """
        try:
            session = self.uow.sessions.complete_session(
                session_id=session_id,
                overall_result=overall_result,
                agent_count=agent_count,
                total_response_time_ms=total_response_time_ms,
                status=status,
                error_message=error_message
            )
            if session:
                self.uow.commit()
                logger.info(f"Session completed: {session_id}, status: {status}")
            else:
                logger.warning(f"Session {session_id} not found for completion")
            return session
        except Exception as e:
            logger.error(f"Error completing agent session: {e}")
            self.uow.rollback()
            raise

    def get_session_history(
        self,
        limit: int = 50,
        session_type: Optional[SessionType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent agent session history.

        Backward-compatible with database.py's get_session_history function.

        Args:
            limit: Maximum number of sessions
            session_type: Filter by session type

        Returns:
            List of session dictionaries with summary info
        """
        try:
            sessions = self.uow.sessions.get_history(
                limit=limit,
                session_type=session_type
            )

            result = []
            for session in sessions:
                session_data = {
                    "session_id": session.session_id,
                    "session_type": session.session_type.value,
                    "analysis_type": session.analysis_type.value,
                    "user_query": session.user_query[:200] + "..." if len(session.user_query) > 200 else session.user_query,
                    "collection_name": session.collection_name,
                    "created_at": session.created_at,
                    "completed_at": session.completed_at,
                    "status": session.status,
                    "agent_count": session.agent_count,
                    "total_response_time_ms": session.total_response_time_ms
                }
                result.append(session_data)

            return result
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific session.

        Backward-compatible with database.py's get_session_details function.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session info and responses, or None if not found
        """
        try:
            return self.uow.sessions.get_details(session_id)
        except Exception as e:
            logger.error(f"Error getting session details: {e}")
            return None

    def get_active_sessions(self, limit: int = 100) -> List[AgentSession]:
        """
        Get all active (not completed) sessions.

        Args:
            limit: Maximum number of sessions

        Returns:
            List of active AgentSession objects
        """
        try:
            return self.uow.sessions.get_active_sessions(limit=limit)
        except Exception as e:
            logger.error(f"Error getting active sessions: {e}")
            return []


# Backward-compatible module-level functions
def log_agent_session(
    session_id: str,
    session_type: SessionType,
    analysis_type: AnalysisType,
    user_query: str,
    collection_name: Optional[str] = None
) -> None:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using SessionService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = SessionService(db)
        service.log_agent_session(
            session_id=session_id,
            session_type=session_type,
            analysis_type=analysis_type,
            user_query=user_query,
            collection_name=collection_name
        )
    finally:
        db.close()


def complete_agent_session(
    session_id: str,
    overall_result: Dict[str, Any],
    agent_count: int,
    total_response_time_ms: Optional[int] = None,
    status: str = 'completed',
    error_message: Optional[str] = None
) -> None:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using SessionService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = SessionService(db)
        service.complete_agent_session(
            session_id=session_id,
            overall_result=overall_result,
            agent_count=agent_count,
            total_response_time_ms=total_response_time_ms,
            status=status,
            error_message=error_message
        )
    finally:
        db.close()


def get_session_history(
    limit: int = 50,
    session_type: Optional[SessionType] = None
) -> List[Dict[str, Any]]:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using SessionService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = SessionService(db)
        return service.get_session_history(limit=limit, session_type=session_type)
    finally:
        db.close()


def get_session_details(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Module-level function for backward compatibility with database.py.

    Creates its own database session for compatibility with existing code.
    Prefer using SessionService class for new code.
    """
    from core.database import get_db
    db = next(get_db())
    try:
        service = SessionService(db)
        return service.get_session_details(session_id)
    finally:
        db.close()
