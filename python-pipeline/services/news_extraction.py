from fastapi import APIRouter, HTTPException, Query, Body
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from bson import ObjectId
from schemas.article import Article
from schemas.rss_feeds import (
    RSSExtractionRequest, 
    RSSExtractionResponse
)
from utils.data_collection.rss_extractor import RSSExtractor
from core.database import article_collection

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

@router.post("/extract", response_model=RSSExtractionResponse)
async def extract_rss_feeds(request: RSSExtractionRequest):
    """
    Extract articles from RSS feeds and store them in MongoDB (Synchronous)
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
        
        # Store articles in MongoDB
        stored_articles = []
        for article_data in all_articles:
            article = Article(
                title=article_data['title'],
                content=article_data['content'],
                url=article_data['url'],
                published_at=article_data['published_date'],
                source=article_data['author'],
            )
            article_dict = article.dict()
            article_dict['extracted_at'] = datetime.now()

            # Check for duplicates by title or URL
            existing = article_collection.find_one({
                "$or": [
                    {"title": article_dict["title"]},
                    {"url": article_dict["url"]}
                ]
            })
            if existing:
                logger.info(f"Duplicate found, skipping: {article_dict['title']}")
                continue

            # Insert into MongoDB
            try:
                result = article_collection.insert_one(article_dict)
                if result.inserted_id:
                    stored_articles.append(article)
            except Exception as e:
                logger.error(f"Failed to store article: {str(e)}")

        return RSSExtractionResponse(
            success=True,
            message=f"Successfully extracted {len(all_articles)} articles",
            articles=stored_articles,
            total_articles=len(all_articles)
        )
    except Exception as e:
        logger.error(f"Failed to extract RSS feeds: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract RSS feeds: {str(e)}"
        )

@router.post("/feed-manual")
async def feed_articles_manually(
    articles: List[Article] = Body(..., description="List of articles to add")
):
    """
    Manually add articles to the database.
    """
    inserted = []
    skipped = []
    for article in articles:
        article_dict = article.dict()
        article_dict['extracted_at'] = datetime.now()
        
        # Check for duplicates by title or URL
        existing = article_collection.find_one({
            "$or": [
                {"title": article_dict["title"]},
                {"url": article_dict["url"]}
            ]
        })
        if existing:
            skipped.append(article_dict["title"])
            continue
        
        try:
            result = article_collection.insert_one(article_dict)
            if result.inserted_id:
                inserted.append(article_dict["title"])
        except Exception as e:
            continue
    
    return {
        "success": True,
        "inserted": inserted,
        "skipped_duplicates": skipped,
        "total_received": len(articles),
        "total_inserted": len(inserted)
    }