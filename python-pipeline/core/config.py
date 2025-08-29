from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Infact"
    
    # AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SENTENCE_MODEL_NAME: str = "all-mpnet-base-v2"
    SPACY_MODEL: str = "en_core_web_sm"
    
    # Processing Configuration
    MAX_ARTICLES_PER_REQUEST: int = 50
    DEFAULT_CLUSTERS: int = 7
    MIN_CLUSTERS: int = 3
    MAX_CLUSTERS: int = 15
    
    # New settings needed by nlp_processor
    USE_GPU: bool = False  # Set to True if you want to use GPU
    MAX_TEXT_LENGTH: int = 5000  # Maximum text length for processing
    EMBEDDING_BATCH_SIZE: int = 32  # Batch size for embeddings
    
    # Content limits
    MAX_FACTS_PER_CLUSTER: int = 15
    MAX_MUSINGS_PER_CLUSTER: int = 10
    MAX_CONTEXT_PER_CLUSTER: int = 10
    MAX_BACKGROUND_PER_CLUSTER: int = 10

settings = Settings()
