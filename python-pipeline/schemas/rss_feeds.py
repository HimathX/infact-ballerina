from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from schemas.article import Article

class TaskStatus(str, Enum):
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RSSExtractionRequest(BaseModel):
    """
    Request model for RSS feed extraction
    """
    from_date: date = Field(
        ..., 
        description="Start date for article extraction (YYYY-MM-DD)"
    )
    to_date: date = Field(
        ..., 
        description="End date for article extraction (YYYY-MM-DD)"
    )
    max_articles: int = Field(
        default=10,
        ge=1,
        le=10000,
        description="Maximum number of articles to extract per feed"
    )
    strip_html: bool = Field(
        default=True,
        description="Whether to strip HTML tags from content"
    )
    fetch_full_content: bool = Field(
        default=True,
        description="Attempt to fetch full article content (slower but more complete)"
    )
    remove_duplicates: bool = Field(
        default=True,
        description="Remove duplicate articles based on title"
    )
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include article metadata (author, tags, etc.)"
    )
    min_content_length: int = Field(
        default=50,
        ge=0,
        description="Minimum content length to include article"
    )
    
    @validator('from_date', 'to_date')
    def validate_dates(cls, v):
        if v > date.today():
            raise ValueError('Date cannot be in the future')
        return v
    
    @validator('to_date')
    def validate_date_range(cls, v, values):
        if 'from_date' in values and v < values['from_date']:
            raise ValueError('to_date must be after from_date')
        return v


class RSSExtractionResponse(BaseModel):
    """
    Response model for RSS feed extraction
    """
    total_articles: int = Field(..., description="Total number of articles extracted")
    
class ExtractionStatus(BaseModel):
    """
    Status model for async extraction tasks
    """
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="When the task was created")
    articles: List[Article] = Field(default=[], description="Extracted articles (if completed)")
    total_articles: int = Field(default=0, description="Total number of articles")
    message: str = Field(default="", description="Status message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(default=None, description="When task completed")
    failed_at: Optional[datetime] = Field(default=None, description="When task failed")
    progress: Optional[Dict[str, Any]] = Field(default=None, description="Progress information")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class FeedValidationResult(BaseModel):
    """
    Result of feed URL validation
    """
    url: str = Field(..., description="Feed URL")
    valid: bool = Field(..., description="Whether the feed is valid and accessible")
    status_code: Optional[int] = Field(default=None, description="HTTP status code")
    error: Optional[str] = Field(default=None, description="Error message if invalid")
    title: Optional[str] = Field(default=None, description="Feed title if valid")
    description: Optional[str] = Field(default=None, description="Feed description if valid")
    total_entries: Optional[int] = Field(default=None, description="Number of entries in feed")
    last_updated: Optional[datetime] = Field(default=None, description="When feed was last updated")

class FeedInfo(BaseModel):
    """
    Basic information about an RSS feed
    """
    url: str = Field(..., description="Feed URL")
    title: str = Field(..., description="Feed title")
    description: Optional[str] = Field(default=None, description="Feed description")
    language: Optional[str] = Field(default=None, description="Feed language")
    last_updated: Optional[datetime] = Field(default=None, description="When feed was last updated")
    total_entries: int = Field(..., description="Total number of entries")
    recent_entries: List[Dict[str, str]] = Field(default=[], description="Recent entry titles and dates")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ErrorResponse(BaseModel):
    """
    Standard error response
    """
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="When error occurred")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ExtractionStats(BaseModel):
    """
    Detailed statistics about extraction process
    """
    total_feeds_processed: int = Field(..., description="Number of feeds processed")
    successful_feeds: int = Field(..., description="Number of feeds successfully processed")
    failed_feeds: int = Field(..., description="Number of feeds that failed")
    total_articles_found: int = Field(..., description="Total articles found before filtering")
    articles_after_filtering: int = Field(..., description="Articles after date/content filtering")
    articles_after_deduplication: int = Field(..., description="Articles after removing duplicates")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    feeds_with_errors: List[str] = Field(default=[], description="URLs of feeds that had errors")
    extraction_timestamp: datetime = Field(default_factory=datetime.now, description="When extraction was performed")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }