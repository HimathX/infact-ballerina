from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from schemas.article import Article
from schemas.rss_feeds import (
    RSSExtractionRequest, 
    # RSSExtractionResponse  # removed - endpoint will return List[Article]
)
from utils.data_collection.rss_extractor import RSSExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["rss-extraction"])

# Default feed URLs
feed_urls = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://www.france24.com/en/rss",
    "https://www.rt.com/rss/news/",
    "https://www.cgtn.com/subscribe/rss/section/world.xml",
    "https://feeds.reuters.com/reuters/topNews",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

@router.post("/extract", response_model=List[Article])
async def extract_rss_feeds(request: RSSExtractionRequest):
    """
    Extract articles from RSS feeds and return a plain list of Article objects.
    (No database storage performed.)
    """
    try:
        extractor = RSSExtractor()
        
        from_date = request.from_date
        to_date = request.to_date
        
        logger.info(f"Starting RSS extraction for {len(feed_urls)} feeds")
        logger.info(f"Date range: {from_date} to {to_date}")
        
        # Process feeds
        all_articles = await extractor.process_feeds(
            feed_urls=feed_urls,
            from_date=from_date,
            to_date=to_date,
            max_articles=request.max_articles,
            strip_html=request.strip_html,
            fetch_full_content=request.fetch_full_content,
            remove_duplicates=request.remove_duplicates,
            include_metadata=request.include_metadata,
            verbose=request.verbose
        )
        
        # Build list of Article models (no DB operations)
        articles_out: List[Article] = []
        for article_data in all_articles:
            try:
                article = Article(
                    title=article_data.get('title', ''),
                    content=article_data.get('content', ''),
                    url=article_data.get('url'),
                    published_at=article_data.get('published_date'),
                    source=article_data.get('author'),
                    image_url=article_data.get('image_url')
                )
                articles_out.append(article)
            except Exception as e:
                logger.warning(f"Skipping malformed article data: {e}")
                continue

        # Return plain list of articles (matches response_model=List[Article])
        return articles_out
    except Exception as e:
        logger.error(f"Failed to extract RSS feeds: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract RSS feeds: {str(e)}"
        )