from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import logging
from utils.cluster_storage import ClusterStorageManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["cluster-maintenance"])

# Initialize cluster storage manager
cluster_storage = ClusterStorageManager()

@router.post("/cleanup")
async def cleanup_old_clusters(
    days_to_keep: int = Query(30, ge=7, le=365, description="Number of days of data to keep")
):
    """Clean up old clusters and articles"""
    try:
        deleted_count = await cluster_storage.cleanup_old_clusters(days_to_keep=days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} old clusters",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up clusters: {str(e)}")