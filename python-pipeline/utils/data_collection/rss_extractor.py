import feedparser
import asyncio
import aiohttp
import time as time_module
from datetime import datetime, date, timezone, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
import logging
import warnings
from urllib.parse import urljoin, urlparse

# Suppress warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    logger.warning('newspaper3k not available, will use basic content extraction')
    NEWSPAPER_AVAILABLE = False

class RSSExtractor:
    """
    Async RSS feed article extractor with comprehensive features
    """
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def extract_source_name_from_url(self, url: str) -> Optional[str]:
        """Extract source name from URL"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Map common domains to their proper names
            domain_mapping = {
                'france24.com': 'FRANCE24',
                'aljazeera.com': 'Al Jazeera',
                'reuters.com': 'Reuters',
                'bbc.co.uk': 'BBC',
                'bbc.com': 'BBC',
                'cnn.com': 'CNN',
                'rt.com': 'RT',
                'cgtn.com': 'CGTN',
                'dw.com': 'Deutsche Welle',
                'theguardian.com': 'The Guardian',
                'nytimes.com': 'The New York Times',
                'washingtonpost.com': 'The Washington Post',
                'ap.org': 'Associated Press',
                'news.yahoo.com': 'Yahoo News',
                'nbcnews.com': 'NBC News',
                'abcnews.go.com': 'ABC News',
                'foxnews.com': 'Fox News',
                'economist.com': 'The Economist',
                'wsj.com': 'The Wall Street Journal',
                'bloomberg.com': 'Bloomberg',
                'cnbc.com': 'CNBC'
            }
            
            # Check if domain is in our mapping
            if domain in domain_mapping:
                return domain_mapping[domain]
            
            # For other domains, try to extract a clean name
            domain_parts = domain.split('.')
            if len(domain_parts) >= 2:
                # Take the main part (before .com, .org, etc.)
                main_part = domain_parts[0]
                # Capitalize and clean up
                return main_part.upper()
            
            return domain.upper()
            
        except Exception as e:
            logger.warning(f"Could not extract source name from URL {url}: {str(e)}")
            return None
    
    def extract_source_name_from_feed(self, feed) -> Optional[str]:
        """Extract source name from feed metadata"""
        try:
            # Try to get from feed title
            if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                title = feed.feed.title
                if title:
                    # Clean up the title to extract source name
                    # Remove common suffixes like "RSS", "Feed", "News", etc.
                    title = re.sub(r'\s+(RSS|Feed|News|Headlines|Latest)\s*$', '', title, flags=re.IGNORECASE)
                    return title.strip()
            
            # Try to get from feed description or other metadata
            if hasattr(feed, 'feed') and hasattr(feed.feed, 'description'):
                desc = feed.feed.description
                if desc and len(desc) < 100:  # Only use short descriptions
                    return desc.strip()
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not extract source name from feed: {str(e)}")
            return None
    
    def strip_html_tags(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        
        soup = BeautifulSoup(text, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style", "img", "video", "audio"]):
            script.decompose()
        
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text
    
    def parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds"""
        if not date_string:
            return None
        
        # Common date formats in RSS
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S GMT',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d %H:%M:%S',
            '%a, %d %b %Y %H:%M:%S +0000',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string.replace(' GMT', ' +0000'), fmt)
            except ValueError:
                continue
        
        # Fallback to feedparser's date parser
        try:
            import time as time_module
            parsed_time = feedparser._parse_date(date_string) #type:ignore
            if parsed_time:
                return datetime.fromtimestamp(time_module.mktime(parsed_time))
        except:
            pass
        
        logger.warning(f"Could not parse date: {date_string}")
        return None
    
    async def fetch_full_article_async(self, url: str) -> Optional[str]:
        """Asynchronously fetch full article content"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove unwanted elements
                    for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                        element.decompose()
                    
                    # Try to find main content using common selectors
                    content_selectors = [
                        'article',
                        'main',
                        '[role="main"]',
                        '.article-content',
                        '.post-content',
                        '.entry-content',
                        '.content',
                        '.story-body',
                        '.article-body'
                    ]
                    
                    content = None
                    for selector in content_selectors:
                        content = soup.select_one(selector)
                        if content:
                            break
                    
                    if content:
                        text = content.get_text(strip=True)
                    else:
                        # Fallback to body text
                        text = soup.get_text(strip=True)
                    
                    # Clean up and limit text
                    text = re.sub(r'\s+', ' ', text)
                    return text[:5000]  # Limit to 5000 characters
                    
        except Exception as e:
            logger.warning(f"Failed to fetch full article from {url}: {str(e)}")
        
        return None
    
    def fetch_full_article_newspaper(self, url: str) -> Optional[str]:
        """Fetch full article content using newspaper3k (sync)"""
        if not NEWSPAPER_AVAILABLE:
            return None
        
        try:
            article = Article(url)  #type:ignore
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            logger.warning(f"Newspaper3k failed for {url}: {str(e)}")
            return None
    
    def is_within_date_range(self, article_date: datetime, from_date: date, to_date: date) -> bool:
        """Check if article date is within specified range"""
        if not article_date:
            return False
        
        # Convert dates to datetime with timezone awareness
        from_dt = datetime.combine(from_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        to_dt = datetime.combine(to_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Make article_date timezone-aware if it isn't
        if article_date.tzinfo is None:
            article_date = article_date.replace(tzinfo=timezone.utc)
        
        return from_dt <= article_date <= to_dt
    
    async def process_single_feed(self, feed_url: str, from_date: date, to_date: date, 
                                 max_articles: int, strip_html: bool, fetch_full_content: bool,
                                 include_metadata: bool, min_content_length: int, verbose: bool) -> Dict[str, Any]:
        """Process a single RSS feed and extract articles"""
        articles = []
        stats = {
            "url": feed_url,
            "success": True,
            "error": None,
            "total_entries": 0,
            "extracted_articles": 0,
            "processing_time": 0
        }
        
        start_time = time_module.time()
        
        try:
            if verbose:
                logger.info(f"📡 Fetching: {feed_url}")
            
            # Parse the feed
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and verbose:
                logger.warning(f"⚠️ Feed parsing issues for {feed_url}: {feed.bozo_exception}")
            
            # Extract source name for fallback author
            fallback_author = None
            
            # Try to get source name from feed metadata first
            fallback_author = self.extract_source_name_from_feed(feed)
            
            # If not found, extract from URL
            if not fallback_author:
                fallback_author = self.extract_source_name_from_url(feed_url)
            
            if verbose and fallback_author:
                logger.info(f"  📰 Using '{fallback_author}' as fallback author for {feed_url}")
            
            stats["total_entries"] = len(feed.entries)
            article_count = 0
            
            for entry in feed.entries:
                if article_count >= max_articles:
                    break
                
                try:
                    # Get publication date
                    pub_date = None
                    if hasattr(entry, 'published'):
                        pub_date = self.parse_date(entry.published)  #type:ignore
                    elif hasattr(entry, 'updated'):
                        pub_date = self.parse_date(entry.updated)  #type:ignore
                    
                    # Check date range
                    if not self.is_within_date_range(pub_date, from_date, to_date):  #type:ignore
                        continue
                    
                    # Extract title
                    title = entry.get('title', 'No Title').strip()  #type:ignore

                    # Extract URL
                    article_url = entry.get('link', '')
                    
                    # Extract content
                    content = ""
                    
                    # Try to get full content if enabled
                    if fetch_full_content and article_url:
                        # Try async fetch first
                        full_content = await self.fetch_full_article_async(article_url)  #type:ignore
                        if not full_content and NEWSPAPER_AVAILABLE:
                            # Fallback to newspaper3k (sync)
                            full_content = self.fetch_full_article_newspaper(article_url)  #type:ignore
                        
                        if full_content:
                            content = full_content
                    
                    # Fallback to feed content if no full content retrieved
                    if not content:
                        if hasattr(entry, 'content') and entry.content:
                            content = entry.content[0].get('value', '')
                        elif hasattr(entry, 'summary'):
                            content = entry.summary
                        elif hasattr(entry, 'description'):
                            content = entry.description
                    
                    # Strip HTML if enabled
                    if strip_html and content: 
                        content = self.strip_html_tags(content)  #type:ignore
                    
                    # Clean up content
                    content = self.clean_content(content)  #type:ignore
                    
                    # Check minimum content length
                    if len(content.strip()) < min_content_length:
                        continue
                    
                    # Extract metadata if enabled
                    author = None
                    tags = []
                    
                    if include_metadata:
                        # Extract author
                        if hasattr(entry, 'author') and entry.author:
                            author = entry.author.strip() #type:ignore
                        elif hasattr(entry, 'author_detail') and entry.author_detail:
                            author_name = entry.author_detail.get('name', '')  #type:ignore
                            author = author_name.strip()
                        
                        # If no author found, use the fallback source name
                        if not author and fallback_author:
                            author = fallback_author
                        
                        # Extract tags/categories
                        if hasattr(entry, 'tags'):
                            tags = [tag.get('term', '') for tag in entry.tags if tag.get('term')]
                    else:
                        # Even if metadata is disabled, use fallback author if no author exists
                        if hasattr(entry, 'author') and entry.author:
                            author = entry.author.strip()  #type:ignore
                        elif hasattr(entry, 'author_detail') and entry.author_detail:
                            author_name = entry.author_detail.get('name', '')  #type:ignore
                            if author_name:
                                author = author_name.strip()
                        
                        # Use fallback if no author found
                        if not author and fallback_author:
                            author = fallback_author
                    
                    # Create article object
                    article = {
                        "title": title,
                        "content": content.strip(),
                        "url": article_url,
                        "published_date": pub_date,
                        "author": author,
                        "tags": tags
                    }
                    
                    articles.append(article)
                    article_count += 1
                    
                    if verbose:
                        author_info = f" (Author: {author})" if author else ""
                        logger.info(f"  ✓ Added: {title[:50]}...{author_info}")
                
                except Exception as e:
                    logger.warning(f"Error processing entry from {feed_url}: {str(e)}")
                    continue
            
            stats["extracted_articles"] = len(articles)
            
            if verbose:
                logger.info(f"  📊 Extracted {len(articles)} articles from {feed_url}")
        
        except Exception as e:
            stats["success"] = False
            stats["error"] = str(e)
            logger.error(f"❌ Error processing {feed_url}: {str(e)}")
        
        finally:
            stats["processing_time"] = time_module.time() - start_time
        
        return {"articles": articles, "stats": stats}
    
    def clean_content(self, content: str) -> str:
        """Clean and normalize article content"""
        if not content:
            return ""
        
        # Remove image references and URLs
        content = re.sub(r'\[Image[^\]]*\]', '', content)
        content = re.sub(r'http[s]?://[^\s]+\.(jpg|jpeg|png|gif|bmp|svg|webp)', '', content)
        
        # Clean up whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles based on title similarity"""
        if not articles:
            return []
        
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_normalized = re.sub(r'[^\w\s]', '', article['title'].lower()).strip()
            if title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_articles.append(article)
        
        return unique_articles
    
    async def process_feeds(self, feed_urls: List[str], from_date: date, to_date: date,
                          max_articles: int = 10, strip_html: bool = True, 
                          fetch_full_content: bool = True, remove_duplicates: bool = True,
                          include_metadata: bool = True, min_content_length: int = 50,
                          verbose: bool = False) -> List[Dict[str, Any]]:
        """Process multiple RSS feeds concurrently"""
        
        start_time = time_module.time()
        
        # Create aiohttp session
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            self.session = session
            
            # Process feeds concurrently
            tasks = []
            for feed_url in feed_urls:
                task = self.process_single_feed(
                    feed_url, from_date, to_date, max_articles, strip_html,
                    fetch_full_content, include_metadata, min_content_length, verbose
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect articles and stats
            all_articles = []
            feed_stats = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Feed processing failed for {feed_urls[i]}: {result}")
                    feed_stats.append({
                        "url": feed_urls[i],
                        "success": False,
                        "error": str(result),
                        "total_entries": 0,
                        "extracted_articles": 0
                    })
                else:
                    all_articles.extend(result["articles"]) #type:ignore
                    feed_stats.append(result["stats"]) #type:ignore
            
            # Remove duplicates if enabled
            if remove_duplicates and all_articles:
                original_count = len(all_articles)
                all_articles = self.remove_duplicates(all_articles)
                if verbose:
                    logger.info(f"🔍 Removed {original_count - len(all_articles)} duplicates")
            
            # Sort articles by publication date (newest first)
            all_articles.sort(
                key=lambda x: x.get('published_date') or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            
            processing_time = time_module.time() - start_time
            
            if verbose:
                logger.info(f"✅ Processing complete! Found {len(all_articles)} articles in {processing_time:.2f}s")
            
            return all_articles
    
    async def validate_feeds(self, feed_urls: List[str]) -> List[Dict[str, Any]]:
        """Validate RSS feed URLs to check accessibility and basic info"""
        
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            
            results = []
            
            for feed_url in feed_urls:
                result = {
                    "url": feed_url,
                    "valid": False,
                    "status_code": None,
                    "error": None,
                    "title": None,
                    "description": None,
                    "total_entries": 0,
                    "last_updated": None
                }
                
                try:
                    # Test HTTP accessibility
                    async with session.get(feed_url) as response:
                        result["status_code"] = response.status
                        
                        if response.status == 200:
                            # Parse feed
                            content = await response.text()
                            feed = feedparser.parse(content)
                            
                            if not feed.bozo:
                                result["valid"] = True
                                result["title"] = feed.feed.get('title', 'No Title')  #type:ignore
                                result["description"] = feed.feed.get('description', '') #type:ignore
                                result["total_entries"] = len(feed.entries)
                                
                                # Get last updated date
                                if hasattr(feed.feed, 'updated'):
                                    result["last_updated"] = self.parse_date(feed.feed.updated) #type:ignore
                            else:
                                result["error"] = f"Feed parsing error: {feed.bozo_exception}"
                        else:
                            result["error"] = f"HTTP {response.status}"
                
                except Exception as e:
                    result["error"] = str(e)
                
                results.append(result)
            
            return results
    
    async def get_feed_info(self, feed_url: str) -> Dict[str, Any]:
        """Get detailed information about a specific RSS feed"""
        
        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=15)
        ) as session:
            
            try:
                async with session.get(feed_url) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}")
                    
                    content = await response.text()
                    feed = feedparser.parse(content)
                    
                    if feed.bozo:
                        raise Exception(f"Feed parsing error: {feed.bozo_exception}")
                    
                    # Extract basic feed info
                    info = {
                        "url": feed_url, 
                        "title": feed.feed.get('title', 'No Title'), #type:ignore
                        "description": feed.feed.get('description', ''), #type:ignore
                        "language": feed.feed.get('language', ''), #type:ignore
                        "last_updated": None,
                        "total_entries": len(feed.entries),
                        "recent_entries": []
                    }
                    
                    # Get last updated date
                    if hasattr(feed.feed, 'updated'):
                        info["last_updated"] = self.parse_date(feed.feed.updated) #type:ignore
                     
                    # Get recent entries (up to 5)
                    for entry in feed.entries[:5]:
                        entry_info = {
                            "title": entry.get('title', 'No Title'),
                            "published": None,
                            "url": entry.get('link', '')
                        }
                        
                        # Get publication date
                        if hasattr(entry, 'published'):
                            pub_date = self.parse_date(entry.published) #type:ignore
                            if pub_date:
                                entry_info["published"] = pub_date.isoformat()
                        
                        info["recent_entries"].append(entry_info)
                    
                    return info
            
            except Exception as e:
                raise Exception(f"Failed to get feed info: {str(e)}")
    
    @staticmethod
    def get_extraction_stats(feed_stats: List[Dict[str, Any]], 
                           total_articles: int, processing_time: float) -> Dict[str, Any]:
        """Generate comprehensive extraction statistics"""
        
        successful_feeds = sum(1 for stat in feed_stats if stat["success"])
        failed_feeds = len(feed_stats) - successful_feeds
        total_entries = sum(stat["total_entries"] for stat in feed_stats)
        feeds_with_errors = [stat["url"] for stat in feed_stats if not stat["success"]]
        
        return {
            "total_feeds_processed": len(feed_stats),
            "successful_feeds": successful_feeds,
            "failed_feeds": failed_feeds,
            "total_articles_found": total_entries,
            "articles_after_filtering": total_articles,
            "processing_time_seconds": round(processing_time, 2),
            "feeds_with_errors": feeds_with_errors,
            "extraction_timestamp": datetime.now(),
            "average_articles_per_feed": round(total_articles / max(successful_feeds, 1), 2)
        }

# Utility functions for standalone use
async def extract_rss_articles(feed_urls: List[str], from_date: date, to_date: date,
                              **kwargs) -> List[Dict[str, Any]]:
    """Standalone function to extract RSS articles"""
    extractor = RSSExtractor()
    return await extractor.process_feeds(feed_urls, from_date, to_date, **kwargs)

async def validate_rss_feeds(feed_urls: List[str]) -> List[Dict[str, Any]]:
    """Standalone function to validate RSS feeds"""
    extractor = RSSExtractor()
    return await extractor.validate_feeds(feed_urls)

def get_default_feed_urls() -> List[str]:
    """Get a list of popular RSS feeds for testing"""
    return [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://www.france24.com/en/rss",
        "https://www.rt.com/rss/news/",
        "https://www.cgtn.com/subscribe/rss/section/world.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://www.aljazeera.com/xml/rss/all.xml"
    ]

def create_date_range(days_back: int = 3) -> tuple:
    """Create a date range from days_back to today"""
    to_date = date.today()
    from_date = to_date - timedelta(days=days_back)
    return from_date, to_date