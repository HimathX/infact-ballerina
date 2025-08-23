from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import logging
from schemas.cluster_storage import (
    ClusterListResponse, ClusterSearchRequest
)
from utils.cluster_storage import ClusterStorageManager
from core.database import article_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["cluster-retrieval"])

# Initialize cluster storage manager
cluster_storage = ClusterStorageManager()

@router.get("/recent", response_model=ClusterListResponse)
async def get_recent_clusters(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(50, ge=1, le=200, description="Maximum clusters to return")
):
    """Get recently created/updated clusters"""
    try:
        clusters = cluster_storage.get_recent_clusters(days_back=days_back, limit=limit)
        
        return ClusterListResponse(
            clusters=clusters,
            total_count=len(clusters),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving recent clusters: {str(e)}")

@router.get("/cluster/{cluster_id}")
async def get_cluster_by_id(cluster_id: str):
    """Get a specific cluster by its ID"""
    try:
        cluster = cluster_storage.get_cluster_by_id(cluster_id)
        
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        
        return {
            "success": True,
            "cluster": cluster,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cluster: {str(e)}")

@router.post("/search", response_model=ClusterListResponse)
async def search_clusters(request: ClusterSearchRequest):
    """Search clusters by keywords, cluster name, or facts"""
    try:
        clusters = cluster_storage.search_clusters(
            query=request.query,
            limit=request.limit
        )
        
        return ClusterListResponse(
            clusters=clusters,
            total_count=len(clusters),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching clusters: {str(e)}")

@router.get("/cluster/{cluster_id}/articles")
async def get_cluster_articles(
    cluster_id: str,
    sort_by: str = Query("published_at", description="Sort articles by field"),
    sort_order: int = Query(-1, description="Sort order: 1 for ascending, -1 for descending")
):
    """Get all articles belonging to a specific cluster"""
    try:
        # First check if cluster exists
        cluster = cluster_storage.get_cluster_by_id(cluster_id)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        
        # Get article IDs from cluster
        article_ids = cluster.get('article_ids', [])
        if not article_ids:
            return {
                "success": True,
                "cluster_name": cluster['cluster_name'],
                "articles": [],
                "total_count": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Query articles from articles collection
        cursor = article_collection.find(
            {"_id": {"$in": article_ids}},
        ).sort([(sort_by, sort_order)])
        
        # Convert to Article objects
        articles = []
        for doc in cursor:
            published_at = doc.get('published_at')
            
            article = {
                "title": doc.get('title', ''),
                "content": doc.get('content', ''),
                "source": doc.get('source'),
                "published_at": published_at.isoformat() if published_at else None,
                "url": doc.get('url'),
                "cluster_id": str(doc.get('cluster_id')),
                "_id": str(doc.get('_id'))
            }
            articles.append(article)
        
        # Get total count
        total_count = len(article_ids)
        
        return {
            "success": True,
            "cluster_name": cluster['cluster_name'],
            "articles": articles,
            "total_count": total_count,
            "page": {
                "total_pages": 1
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving articles for cluster: {str(e)}"
        )

@router.get("/cluster/{cluster_id}/summary")
async def get_cluster_summary(cluster_id: str):
    """Get a summary of a specific cluster including key metrics"""
    try:
        cluster = cluster_storage.get_cluster_by_id(cluster_id)
        
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")
        
        # Get article count
        article_ids = cluster.get('article_ids', [])
        articles_count = len(article_ids)
        
        # Get facts and musings counts
        facts_count = len(cluster.get('facts', []))
        musings_count = len(cluster.get('musings', []))
        
        # Get top keywords (limit to 10)
        keywords = cluster.get('keywords', [])[:10]
        
        # Get sources
        sources = cluster.get('sources', [])
        
        summary = {
            "cluster_id": cluster_id,
            "cluster_name": cluster.get('cluster_name', ''),
            "articles_count": articles_count,
            "facts_count": facts_count,
            "musings_count": musings_count,
            "keywords": keywords,
            "sources": sources,
            "created_at": cluster.get('created_at'),
            "updated_at": cluster.get('updated_at')
        }
        
        # Convert datetime objects to ISO format strings
        for field in ['created_at', 'updated_at']:
            if summary.get(field):
                if hasattr(summary[field], 'isoformat'):
                    summary[field] = summary[field].isoformat()
                else:
                    summary[field] = str(summary[field])
        
        return {
            "success": True,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cluster summary: {str(e)}")

@router.get("/clusters/by-source")
async def get_clusters_by_source(
    source: str = Query(..., description="Source name to filter by"),
    limit: int = Query(50, ge=1, le=200, description="Maximum clusters to return")
):
    """Get clusters that contain articles from a specific source"""
    try:
        # Use cluster storage manager to find clusters by source
        clusters = cluster_storage.get_clusters_by_source(source=source, limit=limit)   # type: ignore
        
        return {
            "success": True,
            "clusters": clusters,
            "source": source,
            "total_count": len(clusters),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving clusters by source: {str(e)}")

@router.get("/clusters/stats")
async def get_cluster_statistics():
    """Get overall cluster statistics"""
    try:
        stats = cluster_storage.get_cluster_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving cluster statistics: {str(e)}")

@router.get("/health")
async def cluster_storage_health():
    """Health check for cluster storage system"""
    try:
        # Test database connection
        stats = cluster_storage.get_cluster_statistics()
        
        return {
            "status": "healthy",
            "database_connected": True,
            "total_clusters": stats.get("total_clusters", 0),
            "total_articles": stats.get("total_articles", 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy", 
            "database_connected": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/trending-topics")
async def get_trending_topics(
    days_back: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    min_articles: int = Query(3, ge=1, le=50, description="Minimum articles per topic")
):
    """Get trending topics based on recent cluster activity"""
    
    try:
        recent_clusters = cluster_storage.get_recent_clusters(days_back=days_back, limit=200)
        
        # Filter clusters with minimum articles
        trending_clusters = [
            cluster for cluster in recent_clusters 
            if cluster.get('articles_count', 0) >= min_articles
        ]
        
        # Sort by article count and recency
        def sort_key(cluster):
            articles_count = cluster.get('articles_count', 0)
            # Handle different datetime formats for updated_at
            updated_at = cluster.get('updated_at', cluster.get('created_at'))
            if updated_at:
                if hasattr(updated_at, 'timestamp'):
                    timestamp = updated_at.timestamp()
                else:
                    try:
                        timestamp = datetime.fromisoformat(str(updated_at)).timestamp()
                    except:
                        timestamp = 0
            else:
                timestamp = 0
            return (articles_count, timestamp)
        
        trending_clusters.sort(key=sort_key, reverse=True)
        
        # Format response
        trending = []
        for cluster in trending_clusters[:10]:  # Top 10 trending
            trending_info = {
                "cluster_id": str(cluster.get('_id', cluster.get('id', ''))),
                "cluster_name": cluster.get('cluster_name', ''),
                "articles_count": cluster.get('articles_count', 0),
                "keywords": cluster.get('keywords', [])[:5],  # Top 5 keywords
                "sources": cluster.get('sources', []),
                "facts_count": len(cluster.get('facts', [])),
                "musings_count": len(cluster.get('musings', []))
            }
            
            # Add last_updated if available
            updated_at = cluster.get('updated_at', cluster.get('created_at'))
            if updated_at:
                if hasattr(updated_at, 'isoformat'):
                    trending_info["last_updated"] = updated_at.isoformat()
                else:
                    trending_info["last_updated"] = str(updated_at)
            
            trending.append(trending_info)
        
        return {
            "success": True,
            "trending_topics": trending,
            "total_trending": len(trending),
            "period": f"Last {days_back} days",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting trending topics: {str(e)}")