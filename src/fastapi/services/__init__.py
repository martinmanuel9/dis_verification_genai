"""
Services package.

This package contains business logic services that coordinate operations
across multiple repositories using the Unit of Work pattern.

Services provide:
- High-level business operations
- Transaction coordination via Unit of Work
- Data transformation and validation
- Integration with external services

Usage:
    from services import AgentService, SessionService
    from core.database import get_db

    # In a FastAPI route
    def create_analysis(
        data: AnalysisRequest,
        db: Session = Depends(get_db)
    ):
        service = SessionService(db)
        result = service.create_and_complete_session(data)
        return result
"""

from services.session_service import SessionService
from services.citation_service import CitationService
from services.compliance_service import ComplianceService

__all__ = [
    "SessionService",
    "CitationService",
    "ComplianceService",
]
