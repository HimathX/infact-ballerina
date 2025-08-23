import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ground News API"
    
    # AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SENTENCE_MODEL_NAME: str = "all-mpnet-base-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    
    # Processing Configuration
    MAX_ARTICLES_PER_REQUEST: int = 50
    DEFAULT_CLUSTERS: int = 7
    MAX_CLUSTERS: int = 15
    MIN_CLUSTERS: int = 3
    EMBEDDING_BATCH_SIZE: int = 32
    MAX_FACTS_PER_CLUSTER: int = 10
    MAX_MUSINGS_PER_CLUSTER: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Performance Configuration
    USE_GPU: bool = True
    MAX_TEXT_LENGTH: int = 1000000
    
    class Config:
        env_file = ".env"

settings = Settings()
