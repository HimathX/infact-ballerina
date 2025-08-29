from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Article(BaseModel):
    title: str = Field(..., description="Article title")
    content: str = Field(..., description="Article content")
    source: Optional[str] = Field(None, description="Article source")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    url: Optional[str] = Field(None, description="Article URL")
    image_url: Optional[str] = Field(None, description="Article image URL")


class ArticleResponse(BaseModel):
    title: str
    content: str
    facts: List[str]
    musings: List[str]
    context: List[str] = Field(default=[], description="Background context and historical information")
    background: List[str] = Field(default=[], description="Related background information")
    cluster_id: int
    cluster_name: str
    image_url: Optional[str] = Field(None, description="Article image URL")

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
    context: str = Field(default="", description="Background context paragraph")
    background: str = Field(default="", description="Historical background paragraph")
    generated_article: str = Field(default="", description="AI-generated comprehensive article")
    factual_summary: str = Field(default="", description="AI-generated factual summary")
    contextual_analysis: str = Field(default="", description="AI-generated contextual analysis")
    similarity_scores: List[float]
    image_url: Optional[str] = Field(None, description="Cluster representative image URL")
    sources: List[str] = Field(default=[], description="News sources in this cluster")
    article_urls: List[str] = Field(default=[], description="URLs of articles in this cluster")
    source_counts: Dict[str, int] = Field(default={}, description="Count of articles per source")
