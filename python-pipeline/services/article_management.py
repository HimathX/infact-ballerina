from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import Optional
import logging
from bson import ObjectId
from core.database import article_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["article-management"])

@router.get("/articles")
async def list_extracted_articles(
    limit: int = Query(50, ge=1, le=200, description="Maximum articles to return"),
    skip: int = Query(0, ge=0, description="Number of articles to skip"),
    sort_by: str = Query("extracted_at", description="Field to sort by"),
    sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending")
):
    """
    List all extracted articles from RSS feeds
    """
    try:
        # Query MongoDB for articles
        cursor = article_collection.find().sort(sort_by, sort_order).skip(skip).limit(limit)
        articles = []
        
        for doc in cursor:
            # Convert ObjectId to string
            doc['_id'] = str(doc['_id'])
            articles.append(doc)
        
        # Get total count
        total_count = article_collection.count_documents({})
        
        return {
            "success": True,
            "articles": articles,
            "total": total_count,
            "limit": limit,
            "skip": skip,
            "returned": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Failed to list articles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list articles: {str(e)}"
        )

@router.get("/articles/recent")
async def get_recent_extracted_articles(
    limit: int = Query(50, ge=1, le=200, description="Maximum articles to return"),
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    source: Optional[str] = Query(None, description="Filter by source")
):
    """
    Get recently extracted articles from RSS feeds
    """
    try:
        # Calculate date threshold
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Build query
        query: dict[str, object] = {
            "extracted_at": {"$gte": cutoff_date}
        }
        
        if source:
            query["source"] = {"$regex": source, "$options": "i"}

        # Query MongoDB
        cursor = article_collection.find(query).sort("extracted_at", -1).limit(limit)
        articles = []
        
        for doc in cursor:
            doc['_id'] = str(doc['_id'])
            articles.append(doc)
        
        total_count = article_collection.count_documents(query)
        
        return {
            "success": True,
            "articles": articles,
            "total": total_count,
            "days_back": days_back,
            "limit": limit,
            "source_filter": source,
            "returned": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Failed to get recent articles: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent articles: {str(e)}"
        )

@router.get("/articles/stats")
async def get_articles_statistics():
    """
    Get statistics about stored articles
    """
    try:
        total_count = article_collection.count_documents({})
        
        # Get articles by source
        pipeline = [
            {"$group": {"_id": "$source", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        sources_stats = list(article_collection.aggregate(pipeline))
        
        # Get recent activity (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        recent_count = article_collection.count_documents({
            "extracted_at": {"$gte": cutoff_date}
        })
        
        return {
            "success": True,
            "total_articles": total_count,
            "sources": sources_stats,
            "recent_articles_7_days": recent_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@router.get("/articles/{article_id}")
async def get_article_by_id(article_id: str):
    """
    Get a specific article by its ID
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid article ID format"
            )
        
        # Query MongoDB
        article = article_collection.find_one({"_id": ObjectId(article_id)})
        
        if not article:
            raise HTTPException(
                status_code=404,
                detail="Article not found"
            )
        
        # Convert ObjectId to string
        article['_id'] = str(article['_id'])
        
        return {
            "success": True,
            "article": article,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get article: {str(e)}"
        )

@router.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    """
    Delete a specific extracted article
    """
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(article_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid article ID format"
            )

        # Delete from MongoDB
        result = article_collection.delete_one({"_id": ObjectId(article_id)})

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Article not found"
            )

        logger.info(f"Article {article_id} deleted successfully")

        return {
            "success": True,
            "message": f"Article {article_id} deleted successfully",
            "deleted_count": result.deleted_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete article: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete article: {str(e)}"
        )