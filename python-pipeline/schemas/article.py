from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Article(BaseModel):
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    source: Optional[str] = Field(None, description="Article source")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    url: Optional[str] = Field(None, description="Article URL")


class ArticleResponse(BaseModel):
    title: str
    content: str
    facts: List[str]
    musings: List[str]
    cluster_id: int
    cluster_name: str

class ProcessingRequest(BaseModel):
    articles: List[Article] = Field(..., description="List of articles to process")
    n_clusters: Optional[int] = Field(None, ge=3, le=15, description="Number of clusters")
    similarity_threshold: Optional[float] = Field(0.7, ge=0.1, le=1.0, description="Similarity threshold for deduplication")

class ClusterResult(BaseModel):
    cluster_id: int
    cluster_name: str
    articles_count: int
    facts: List[str]
    musings: List[str]
    generated_article: str
    similarity_scores: List[float]
