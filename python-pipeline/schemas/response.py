from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from schemas.cluster import ClusterAnalysis
from schemas.article import ClusterResult

class BaseResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    timestamp: str

class ProcessingResponse(BaseResponse):
    task_id: str
    status: str  # "processing", "completed", "failed"
    progress: int  # 0-100
    estimated_time: Optional[int] = None  # seconds

class ClusteringResponse(BaseResponse):
    clusters: List[int]
    cluster_names: Dict[int, str]
    n_clusters: int
    embeddings_2d: List[List[float]]
    cluster_sizes: Dict[int, int]

class FactExtractionResponse(BaseResponse):
    facts: List[str]
    musings: List[str]
    extraction_stats: Dict[str, Any]

class FinalResultResponse(BaseResponse):
    task_id: str
    clusters: List[ClusterResult]
    processing_stats: Dict[str, Any]
    total_articles: int
    total_clusters: int

class ModelStatus(BaseModel):
    spacy_loaded: bool
    sentence_transformer_loaded: bool
    gemini_configured: bool

class HealthResponse(BaseResponse):
    status: str
    models: ModelStatus
    gpu_info: Dict[str, Any]
