from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from schemas.article import Article, ClusterResult

class StoredCluster(BaseModel):
    """Model for a stored cluster in the database"""
    cluster_id: str = Field(..., description="Unique cluster identifier")
    cluster_name: str = Field(..., description="Human-readable cluster name")
    keywords: List[str] = Field(default=[], description="Key terms extracted from cluster")
    facts: List[str] = Field(default=[], description="Facts extracted from articles")
    musings: List[str] = Field(default=[], description="Opinions/musings from articles")
    generated_article: str = Field(default="", description="AI-generated summary article")
    articles_count: int = Field(default=0, description="Number of articles in cluster")
    sources: List[str] = Field(default=[], description="News sources represented")
    embedding: List[float] = Field(default=[], description="Cluster embedding vector")
    similarity_scores: List[float] = Field(default=[], description="Internal similarity scores")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    article_ids: List[str] = Field(default=[], description="IDs of articles in this cluster")
    image_url: Optional[str] = Field(None, description="Representative image URL for the cluster")
    
class ClusterStorageRequest(BaseModel):
    """Request model for storing clusters"""
    cluster_result: ClusterResult
    articles: List[Article]
    force_new_cluster: bool = Field(False, description="Force creation of new cluster even if similar exists")

class ClusterSearchRequest(BaseModel):
    """Request model for searching clusters"""
    query: str = Field(..., description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum results to return")
    days_back: Optional[int] = Field(30, ge=1, le=365, description="Days to look back")
    sources: Optional[List[str]] = Field(None, description="Filter by sources")

class StorageResponse(BaseModel):
    """Response model for cluster storage operations"""
    success: bool
    cluster_id: str
    action: str  # 'created', 'merged', 'updated'
    message: str
    similarity_info: Optional[Dict] = None
    timestamp: str

class ClusterListResponse(BaseModel):
    """Response model for cluster listings"""
    clusters: List[Dict[str, Any]]
    total_count: int
    timestamp: str

class ClusterStatsResponse(BaseModel):
    """Response model for cluster statistics"""
    statistics: Dict[str, Any]
    timestamp: str

class SimilarCluster(BaseModel):
    """Model for similar cluster results"""
    cluster_id: str
    cluster_name: str
    similarity_score: float
    keywords: List[str]
    articles_count: int
    created_at: datetime
    sources: List[str]

class ClusterMergeRequest(BaseModel):
    """Request model for merging clusters"""
    source_cluster_id: str
    target_cluster_id: str
    keep_target: bool = Field(True, description="Whether to keep target cluster name/details")
    merge_strategy: str = Field("combine", description="How to merge: 'combine', 'replace', 'selective'")

class ClusterTimelineItem(BaseModel):
    """Model for cluster timeline entries"""
    cluster_id: str
    cluster_name: str
    action: str  # 'created', 'updated', 'merged'
    articles_count: int
    timestamp: datetime
    sources: List[str]
    keywords: List[str]

class TrendingTopic(BaseModel):
    """Model for trending topic analysis"""
    cluster_id: str
    cluster_name: str
    articles_count: int
    growth_rate: float  # Article addition rate
    keywords: List[str]
    sources: List[str]
    last_updated: datetime
    facts_count: int
    musings_count: int
    trending_score: float  # Composite score for trending

class ClusterAnalytics(BaseModel):
    """Model for cluster analytics data"""
    total_clusters: int
    total_articles: int
    clusters_by_source: Dict[str, int]
    clusters_by_day: Dict[str, int]
    top_keywords: List[Dict[str, Any]]
    average_cluster_size: float
    largest_cluster: Dict[str, Any]
    most_active_sources: List[Dict[str, Any]]
    cluster_growth_trend: List[Dict[str, Any]]

class ProcessingWithStorageRequest(BaseModel):
    """Request model for processing articles with storage"""
    articles: List[Article]
    n_clusters: Optional[int] = Field(None, ge=2, le=15, description="Number of clusters")
    force_new_clusters: bool = Field(False, description="Force creation of new clusters")
    store_clusters: bool = Field(True, description="Whether to store results in database")
    merge_similar: bool = Field(True, description="Whether to merge with similar existing clusters")
    similarity_threshold: float = Field(0.8, ge=0.5, le=1.0, description="Threshold for considering clusters similar")

class ProcessingWithStorageResponse(BaseModel):
    """Response model for processing with storage"""
    task_id: str
    status: str
    message: str
    clusters_processed: int
    clusters_stored: int
    clusters_merged: int
    storage_results: List[Dict[str, Any]]
    timestamp: str
    processing_time: Optional[float] = None
