from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from services import article_processing_router, cluster_storage_router, article_management_router, cluster_maintainance_router, news_extraction_router
from utils.data_processing.nlp_processor import NLPProcessor

# Load environment variables
load_dotenv()

# Global NLP processor instance
nlp_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global nlp_processor
    nlp_processor = NLPProcessor()
    await nlp_processor.initialize()
    app.state.nlp_processor = nlp_processor
    yield
    # Shutdown
    # Clean up resources if needed
    pass


app = FastAPI(
    title="Ground News API",
    description="Desensationalizing news through AI-powered clustering and fact extraction",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(article_processing_router)
app.include_router(cluster_storage_router)
app.include_router(article_management_router)
app.include_router(cluster_maintainance_router)
app.include_router(news_extraction_router)

@app.get("/")
async def root():
    return {
        "message": "Ground News API", 
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8091, 
        reload=True
    )
