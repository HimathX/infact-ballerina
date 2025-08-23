from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ClusterInfo(BaseModel):
    cluster_id: int
    name: str
    size: int
    articles: List[int]  # Article indices
    centroid: List[float]

class ClusterAnalysis(BaseModel):
    cluster_id: int
    name: str
    keywords: List[str]
    article_count: int
    avg_sentiment: float
    topic_coherence: float

class TopicModel(BaseModel):
    topic_id: int
    words: List[str]
    weights: List[float]
    coherence_score: float
