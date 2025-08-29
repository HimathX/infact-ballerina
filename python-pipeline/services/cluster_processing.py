from fastapi import APIRouter, HTTPException, Request, Query
from typing import List, Optional, Dict, Any
import time
import uuid
import logging
from datetime import datetime, timedelta
from bson import ObjectId
from schemas.article import Article, ClusterResult
from schemas.cluster_storage import (
    ProcessingWithStorageRequest, ProcessingWithStorageResponse
)
from utils.cluster_storage import ClusterStorageManager
from core.database import article_collection, clusters_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["cluster-processing"])

# Initialize cluster storage manager
cluster_storage = ClusterStorageManager()

# Task storage for completed processing operations
processing_task_storage: Dict[str, Dict[str, Any]] = {}

def create_task_id() -> str:
    """Generate a unique task ID"""
    return str(uuid.uuid4())

def validate_cluster_request(request: ProcessingWithStorageRequest) -> None:
    """Enhanced validation for cluster storage requests"""
    if len(request.articles) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 articles required for clustering"
        )
    
    # Validate article content
    for i, article in enumerate(request.articles):
        if not article.title or not article.title.strip():
            raise HTTPException(
                status_code=400,
                detail=f"Article {i+1} must have a non-empty title"
            )
        
        if not article.content or len(article.content.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail=f"Article {i+1} content must be at least 50 characters"
            )

@router.post("/process-with-storage", response_model=ProcessingWithStorageResponse)
async def process_articles_with_storage(
    request: ProcessingWithStorageRequest,
    bg_request: Request
):
    """Process articles through NLP pipeline and optionally store in database with smart clustering"""
    
    # Validate request
    validate_cluster_request(request)
    
    start_time = time.time()
    task_id = create_task_id()
    
    try:
        nlp_processor = bg_request.app.state.nlp_processor
        
        logger.info(f"Starting cluster processing with storage for task {task_id}")
        
        # Process articles through NLP pipeline
        processed_clusters = await nlp_processor.process_articles(
            request.articles, 
            request.n_clusters
        )
        
        storage_results = []
        clusters_stored = 0
        clusters_merged = 0
        
        if request.store_clusters:
            # Group articles by cluster for storage
            clustered_articles = await _group_articles_by_cluster(
                processed_clusters, 
                request.articles, 
                nlp_processor
            )
            
            # Store each cluster
            for cluster_result, articles_in_cluster in clustered_articles:
                try:
                    cluster_id, action = await cluster_storage.store_or_merge_cluster(
                        cluster_result=cluster_result,
                        articles=articles_in_cluster,
                        force_new=request.force_new_clusters
                    )
                    
                    if action == "created":
                        clusters_stored += 1
                    elif action == "merged":
                        clusters_merged += 1
                    
                    # Create detailed article summaries (truncate content for response)
                    article_summaries = []
                    for article in articles_in_cluster:
                        article_summary = {
                            "title": article.title,
                            "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,  # Truncate for response
                            "source": article.source,
                            "published_at": article.published_at.isoformat() if article.published_at else None,
                            "url": article.url,
                            "image_url": article.image_url
                        }
                        article_summaries.append(article_summary)
                    
                    storage_results.append({
                        "cluster_id": cluster_id,
                        "cluster_name": cluster_result.cluster_name,
                        "action": action,
                        "articles_count": len(articles_in_cluster),
                        "facts_count": len(cluster_result.facts),
                        "musings_count": len(cluster_result.musings),
                        "articles": article_summaries,
                        "facts": cluster_result.facts,
                        "musings": cluster_result.musings,
                        "sources": list(set([a.source for a in articles_in_cluster if a.source])),
                        "article_urls": [a.url for a in articles_in_cluster if a.url],
                        "generated_article": cluster_result.generated_article[:1000] + "..." if len(cluster_result.generated_article) > 1000 else cluster_result.generated_article,
                        "similarity_scores": cluster_result.similarity_scores,
                        "cluster_analysis": {
                            "factual_summary": cluster_result.factual_summary[:500] + "..." if len(cluster_result.factual_summary) > 500 else cluster_result.factual_summary,
                            "contextual_analysis": cluster_result.contextual_analysis[:500] + "..." if len(cluster_result.contextual_analysis) > 500 else cluster_result.contextual_analysis,
                            "context": cluster_result.context[:500] + "..." if len(cluster_result.context) > 500 else cluster_result.context,
                            "background": cluster_result.background[:500] + "..." if len(cluster_result.background) > 500 else cluster_result.background
                        }
                    })
                
                except Exception as e:
                    logger.error(f"Failed to store cluster: {str(e)}")
                    # Create detailed article summaries even for failed clusters
                    article_summaries = []
                    for article in articles_in_cluster:
                        article_summary = {
                            "title": article.title,
                            "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                            "source": article.source,
                            "published_at": article.published_at.isoformat() if article.published_at else None,
                            "url": article.url,
                            "image_url": article.image_url
                        }
                        article_summaries.append(article_summary)
                    
                    storage_results.append({
                        "cluster_name": cluster_result.cluster_name,
                        "action": "failed",
                        "error": str(e),
                        "articles_count": len(articles_in_cluster),
                        "articles": article_summaries,
                        "facts": cluster_result.facts,
                        "musings": cluster_result.musings,
                        "attempted_storage": True
                    })
        
        # Store task result
        processing_task_storage[task_id] = {
            "status": "completed",
            "progress": 100,
            "result": {
                "articles": len(request.articles),
                "processed_clusters": len(processed_clusters),
                "clusters_stored": clusters_stored,
                "clusters_merged": clusters_merged,
                "storage_results": storage_results
            },
            "created_at": datetime.now(),
            "completed_at": datetime.now()
        }
        
        logger.info(f"Cluster processing with storage completed for task {task_id}")
        
        processing_time = time.time() - start_time
        
        # Prepare comprehensive response
        response_data = {
            "success": True,
            "task_id": task_id,
            "status": "completed",
            "message": f"Processed {len(request.articles)} articles into {len(processed_clusters)} clusters and stored in database",
            "clusters_processed": len(processed_clusters),
            "clusters_stored": clusters_stored,
            "clusters_merged": clusters_merged,
            "storage_results": storage_results,
            "timestamp": datetime.now().isoformat(),
            "processing_time": processing_time,
            "summary": {
                "total_articles_processed": len(request.articles),
                "total_clusters_created": len(processed_clusters),
                "successful_storage_operations": clusters_stored + clusters_merged,
                "failed_operations": len([r for r in storage_results if r.get("action") == "failed"]),
                "total_facts_extracted": sum(len(r.get("facts", [])) for r in storage_results),
                "total_musings_extracted": sum(len(r.get("musings", [])) for r in storage_results),
                "unique_sources": len(set(source for r in storage_results for source in r.get("sources", []))),
                "articles_with_urls": len([r for r in storage_results for a in r.get("articles", []) if a.get("url")])
            }
        }
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in scrape-process-store pipeline: {str(e)}"
        logger.error(f"Pipeline failed for task {task_id}: {error_msg}")
        
        # Store error in task storage
        processing_task_storage[task_id] = {
            "status": "failed",
            "progress": 0,
            "error": str(e),
            "created_at": datetime.now(),
            "failed_at": datetime.now()
        }
        
        raise HTTPException(status_code=500, detail=error_msg)

async def _group_articles_by_cluster(processed_clusters: List[ClusterResult], articles: List[Article], nlp_processor) -> List[tuple]:
    """Group articles by their assigned cluster using embeddings similarity"""
    try:
        if not processed_clusters or not articles:
            return []
        
        # Extract embeddings for all articles
        article_texts = [f"{article.title} {article.content}" for article in articles]
        article_embeddings = nlp_processor._extract_embeddings(article_texts)
        
        clustered_articles = []
        
        for cluster_result in processed_clusters:
            # Find articles closest to this cluster
            cluster_articles = []
            
            # For now, use a simple assignment strategy
            # In production, you'd use the actual cluster assignments from the clustering algorithm
            articles_per_cluster = max(1, len(articles) // len(processed_clusters))
            
            # Get cluster index
            cluster_index = processed_clusters.index(cluster_result)
            start_idx = cluster_index * articles_per_cluster
            
            if cluster_index == len(processed_clusters) - 1:
                # Last cluster gets remaining articles
                end_idx = len(articles)
            else:
                end_idx = start_idx + articles_per_cluster
            
            # Ensure we don't go out of bounds
            start_idx = min(start_idx, len(articles))
            end_idx = min(end_idx, len(articles))
            
            cluster_articles = articles[start_idx:end_idx]
            
            if cluster_articles:  # Only add if we have articles
                clustered_articles.append((cluster_result, cluster_articles))
        
        # If some articles weren't assigned, add them to the first cluster
        total_assigned = sum(len(articles) for _, articles in clustered_articles)
        if total_assigned < len(articles) and clustered_articles:
            remaining_articles = articles[total_assigned:]
            first_cluster, first_articles = clustered_articles[0]
            clustered_articles[0] = (first_cluster, first_articles + remaining_articles)
        
        return clustered_articles
        
    except Exception as e:
        logger.error(f"Error grouping articles by cluster: {str(e)}")
        raise Exception(f"Error grouping articles by cluster: {str(e)}")

@router.post("/scrape-process-store")
async def scrape_process_and_store(
    bg_request: Request,
    n_clusters: Optional[int] = None,
    force_new_clusters: bool = False,
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back for articles"),
    max_articles: int = Query(1000, ge=10, le=10000, description="Maximum articles to process")
):
    """Complete pipeline: Scrape -> Process -> Store"""
    
    task_id = create_task_id()
    
    try:
        # Calculate date threshold
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Build query filter for recent articles
        query = {
            "published_at": {"$gte": cutoff_date}
        }
        
        logger.info(f"Starting scrape-process-store pipeline for task {task_id}")
        
        # Get recent articles from database
        cursor = article_collection.find(query).limit(max_articles).sort("published_at", -1)
        
        # Convert to Article objects
        scraped_articles = []
        for doc in cursor:
            try:
                published_at = doc.get('published_at')
                
                article = Article(
                    title=doc.get('title', ''),
                    content=doc.get('content', ''),
                    source=doc.get('source'),
                    published_at=published_at,
                    url=doc.get('url'),
                    image_url=doc.get('image_url')
                )
                scraped_articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to convert document to Article: {str(e)}")
                continue
        
        # If no recent articles found, try without date filter
        if not scraped_articles:
            logger.warning(f"No articles found in the last {days_back} days, trying all articles")
            cursor = article_collection.find({}).limit(max_articles).sort("_id", -1)
            
            for doc in cursor:
                try:
                    published_at = doc.get('published_at')
                    
                    article = Article(
                        title=doc.get('title', ''),
                        content=doc.get('content', ''),
                        source=doc.get('source'),
                        published_at=published_at,
                        url=doc.get('url'),
                        image_url=doc.get('image_url')
                    )
                    scraped_articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to convert document to Article: {str(e)}")
                    continue
        
        if not scraped_articles:
            raise HTTPException(
                status_code=404, 
                detail="No articles found in database"
            )
        
        if len(scraped_articles) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 articles required for clustering"
            )
        
        # Process through NLP pipeline
        nlp_processor = bg_request.app.state.nlp_processor
        processed_clusters = await nlp_processor.process_articles(scraped_articles, n_clusters)
        
        # Group articles by cluster
        clustered_articles = await _group_articles_by_cluster(
            processed_clusters, 
            scraped_articles, 
            nlp_processor
        )
        
        # Store clusters
        storage_results = []
        clusters_stored = 0
        clusters_merged = 0
        
        for cluster_result, articles_in_cluster in clustered_articles:
            try:
                cluster_id, action = await cluster_storage.store_or_merge_cluster(
                    cluster_result=cluster_result,
                    articles=articles_in_cluster,
                    force_new=force_new_clusters
                )
                
                if action == "created":
                    clusters_stored += 1
                elif action == "merged":
                    clusters_merged += 1
                
                storage_results.append({
                    "cluster_id": cluster_id,
                    "action": action,
                    "articles": articles_in_cluster
                })

            except Exception as e:
                logger.error(f"Failed to store or merge cluster: {str(e)}")
                continue

        logger.info(f"Cluster processing completed for task {task_id}: {len(storage_results)} clusters processed")
        return {
            "success": True,
            "task_id": task_id,
            "clusters_stored": clusters_stored,
            "clusters_merged": clusters_merged,
            "storage_results": storage_results
        }

    except Exception as e:
        logger.error(f"Cluster processing failed for task {task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))