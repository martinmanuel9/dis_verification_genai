from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Agent name")
    model_name: str = Field(..., description="Model to use for this agent")
    system_prompt: str = Field(..., min_length=10, description="System prompt defining the agent's role")
    user_prompt_template: str = Field(..., min_length=10, description="User prompt template with {data_sample} placeholder")

class UpdateAgentRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200, description="Updated agent name")
    model_name: Optional[str] = Field(None, description="Updated model name")
    system_prompt: Optional[str] = Field(None, min_length=10, description="Updated system prompt")
    user_prompt_template: Optional[str] = Field(None, min_length=10, description="Updated user prompt template")
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated temperature")
    max_tokens: Optional[int] = Field(None, ge=100, le=4000, description="Updated max tokens")
    is_active: Optional[bool] = Field(None, description="Whether agent is active")
    
    @field_validator('user_prompt_template')
    def validate_prompt_template(cls, v):
        if v is not None and '{data_sample}' not in v:
            raise ValueError('User prompt template must contain {data_sample} placeholder')
        return v

class UpdateAgentResponse(BaseModel):
    message: str
    agent_id: int
    agent_name: str
    updated_fields: List[str]

class ComplianceCheckRequest(BaseModel):
    data_sample: str = Field(..., min_length=1, description="Legal content to analyze")
    agent_ids: List[int] = Field(..., min_items=1, description="List of agent IDs to use for analysis")

class RAGCheckRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="Legal query for RAG analysis")
    collection_name: str = Field(..., description="ChromaDB collection name")
    agent_ids: List[int] = Field(..., min_items=1, description="List of agent IDs to use for RAG analysis")

class RAGDebateSequenceRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="Legal content for multi-agent debate")
    collection_name: str = Field(..., description="ChromaDB collection name")
    agent_ids: List[int] = Field(..., min_items=1, description="List of agent IDs for debate sequence")
    session_id: Optional[str] = Field(None, description="Optional session ID for continuing a debate")

# Response models for better API documentation
class AgentResponse(BaseModel):
    agent_id: int
    agent_name: str
    model_name: str
    response: str
    processing_time: Optional[float] = None

class ComplianceCheckResponse(BaseModel):
    agent_responses: Dict[str, str]
    overall_compliance: bool
    session_id: Optional[str] = None
    debate_results: Optional[Dict[str, Any]] = None

class RAGCheckResponse(BaseModel):
    agent_responses: Dict[str, str]
    collection_used: str
    processing_time: Optional[float] = None

class RAGDebateSequenceResponse(BaseModel):
    session_id: str
    debate_chain: List[Dict[str, Any]]
    final_consensus: Optional[str] = None

class CreateAgentResponse(BaseModel):
    message: str
    agent_id: int
    agent_name: str

class GetAgentsResponse(BaseModel):
    agents: List[Dict[str, Any]]
    total_count: int

# Missing schema that agent_service.py expects
class ComplianceResultSchema(BaseModel):
    agent_responses: Dict[str, str]
    overall_compliance: bool
    session_id: Optional[str] = None
    debate_results: Optional[Dict[str, Any]] = None
    

class EvaluateRequest(BaseModel):
    document_id:     str = Field(...)
    collection_name: str = Field(...)
    prompt:          str = Field(...)
    top_k:           int = Field(5)
    model_name:      str = Field(...)

class EvaluateResponse(BaseModel):
    document_id:     str
    collection_name: str
    prompt:          str
    model_name:      str
    response:        str
    response_time_ms:int
    session_id:      str

# RAG Assessment Service Schemas
class RAGAssessmentRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query for RAG assessment")
    collection_name: str = Field(..., description="ChromaDB collection name")
    model_name: str = Field(default="gpt-3.5-turbo", description="Model to use for generation")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    include_quality_assessment: bool = Field(default=True, description="Include quality assessment")
    include_alignment_assessment: bool = Field(default=True, description="Include alignment assessment")
    include_classification_metrics: bool = Field(default=True, description="Include classification metrics")

class RAGPerformanceMetricsResponse(BaseModel):
    session_id: str
    query: str
    collection_name: str
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    documents_retrieved: int
    documents_used: int
    relevance_score: float
    context_length: int
    response_length: int
    model_name: str
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime

class RAGQualityAssessmentResponse(BaseModel):
    session_id: str
    relevance_score: float
    coherence_score: float
    factual_accuracy: float
    completeness_score: float
    context_utilization: float
    overall_quality: float
    assessment_method: str
    assessor_model: Optional[str] = None
    timestamp: datetime

class RAGAlignmentAssessmentResponse(BaseModel):
    session_id: str
    intent_alignment_score: float
    query_coverage_score: float
    instruction_adherence_score: float
    answer_type_classification: str
    expected_answer_type: str
    answer_type_match: bool
    tone_consistency_score: float
    scope_accuracy_score: float
    missing_elements: List[str]
    extra_elements: List[str]
    assessment_confidence: float
    timestamp: datetime

class RAGClassificationMetricsResponse(BaseModel):
    session_id: str
    query_classification: str
    response_classification: str
    classification_confidence: float
    domain_relevance: str
    complexity_level: str
    information_density: float
    actionability_score: float
    specificity_score: float
    citation_quality: float
    timestamp: datetime

class RAGAssessmentResponse(BaseModel):
    response: str
    performance_metrics: RAGPerformanceMetricsResponse
    quality_assessment: Optional[RAGQualityAssessmentResponse] = None
    alignment_assessment: Optional[RAGAlignmentAssessmentResponse] = None
    classification_metrics: Optional[RAGClassificationMetricsResponse] = None

class RAGAnalyticsRequest(BaseModel):
    time_period_hours: int = Field(default=24, ge=1, le=8760, description="Analysis period in hours")
    collection_name: Optional[str] = Field(None, description="Filter by collection name")

class RAGBenchmarkRequest(BaseModel):
    query_set: List[str] = Field(..., min_items=1, description="Set of test queries")
    collection_name: str = Field(..., description="Collection to test against")
    configurations: List[Dict[str, Any]] = Field(..., min_items=1, description="List of configurations to test")

class CollectionPerformanceRequest(BaseModel):
    collection_name: str = Field(..., description="Collection name to analyze")

class RAGMetricsExportRequest(BaseModel):
    format: str = Field(default="json", description="Export format")
    time_period_hours: int = Field(default=24, ge=1, le=8760, description="Export period in hours")