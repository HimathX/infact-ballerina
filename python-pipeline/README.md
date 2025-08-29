# InFact Platform (Backend)

A FastAPI application that processes news articles to remove sensationalism through AI-powered clustering and fact extraction. The system takes multiple news articles about similar topics, clusters them, extracts factual information, and generates neutral, desensationalized articles.

For more detailed information about the InFact pipeline and its implementation, visit: https://github.com/LazySeaHorse/Infact

## Features

- **NLP Processing Pipeline**: Text preprocessing with spaCy, semantic embeddings, and KMeans clustering
- **Fact vs Opinion Classification**: Uses NER, sentiment analysis, and rule-based classification
- **AI Article Generation**: Integration with Google Gemini API for neutral article generation
- **RESTful API**: Async FastAPI with background processing and task tracking
- **Scalable Architecture**: Modular design with proper error handling and validation
- **RSS Feed Integration**: Automated news extraction from configurable sources
- **Cluster Management**: Tools for creating, analyzing and maintaining article clusters
- **MongoDB Integration**: Persistent storage for articles and clusters with similarity-based merging
- **URL Tracking**: Store and retrieve original news article URLs within clusters
- **Advanced Analytics**: Sentiment analysis, trending topics, and cluster statistics

## Tech Stack

- **Backend**: FastAPI (0.115+), Python 3.11+
- **NLP**: spaCy 3.7+, sentence-transformers 3.0+, scikit-learn 1.3+, gensim 4.3+
- **AI**: Google Gemini API
- **Processing**: TF-IDF, LDA topic modeling, KMeans clustering
- **Database**: MongoDB via pymongo
- **Web Scraping**: feedparser, beautifulsoup4, aiohttp
- **Visualization**: plotly, matplotlib, seaborn (for analytics)

## Installation

1. **Clone the repository**
   ```bash
   cd ground_news_api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set up environment variables**
   ```bash
   copy .env.example .env
   # Edit .env with your Google Gemini API key
   ```

6. **Get Google Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key
   - Add it to your `.env` file

## Usage

### Starting the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

### Basic Usage Example

```python
import requests

# Sample articles with URLs
articles = [
    {
        "title": "Tech Company Announces Major Layoffs",
        "content": "A major technology company announced today that it will be laying off 10,000 employees...",
        "source": "TechNews",
        "url": "https://technews.com/2024/01/15/tech-company-layoffs"
    },
    {
        "title": "Tech Giant Cuts Workforce Dramatically", 
        "content": "In a shocking move, the tech giant has decided to terminate thousands of workers...",
        "source": "BusinessDaily",
        "url": "https://businessdaily.com/2024/01/15/tech-giant-workforce-cuts"
    }
]

# Process articles with storage
response = requests.post(
    "http://localhost:8000/api/v1/process-with-storage",
    json={"articles": articles, "n_clusters": 3}
)

task_id = response.json()["task_id"]

# Check processing status
status = requests.get(f"http://localhost:8000/api/v1/articles/task/{task_id}")

# Search for existing clusters
search_response = requests.post(
    "http://localhost:8000/api/v1/clusters/search",
    json={"query": "tech layoffs", "limit": 10}
)

clusters = search_response.json()["clusters"]
```

## Sample Cluster Output

Here's an example of what a processed cluster looks like:

```json
{
  "cluster_id": "cluster_2024_tech_layoffs_001",
  "cluster_name": "Tech Industry Layoffs and Economic Impact",
  "keywords": ["layoffs", "technology", "economic downturn", "job cuts"],
  "facts": [
    "Meta announced layoffs of 11,000 employees in November 2022",
    "Amazon plans to cut over 18,000 jobs across multiple divisions"
  ],
  "musings": [
    "The tech industry's rapid hiring during the pandemic may have led to over-staffing",
    "Some analysts suggest these layoffs are more about efficiency than economic necessity"
  ],
  "articles_count": 15,
  "sources": ["TechCrunch", "Bloomberg", "Wall Street Journal"],
  "article_urls": [
    "https://techcrunch.com/2024/01/15/meta-announces-largest-layoffs",
    "https://bloomberg.com/news/articles/2024-01-15/amazon-plans-cut-jobs"
  ],
  "generated_article": "The technology sector is experiencing unprecedented workforce reductions...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## API Endpoints

### Health Check
- `GET /api/v1/health/` - Check API and model status

### Article Processing
- `POST /api/v1/articles/process` - Process articles through complete pipeline
- `GET /api/v1/articles/task/{task_id}` - Get processing task status

### Cluster Management
- `POST /api/v1/process-with-storage` - Process articles and store clusters in database
- `POST /api/v1/scrape-process-store` - Scrape RSS feeds, process, and store clusters
- `POST /api/v1/clusters/search` - Search for existing clusters by keywords
- `GET /api/v1/clusters/list` - List all clusters with pagination
- `GET /api/v1/clusters/stats` - Get cluster statistics and analytics
- `POST /api/v1/clusters/merge` - Merge two similar clusters
- `DELETE /api/v1/clusters/{cluster_id}` - Delete a cluster

### Individual Processing Steps
- `POST /api/v1/processing/preprocess` - Preprocess article text
- `POST /api/v1/processing/cluster` - Cluster articles by similarity
- `POST /api/v1/processing/extract-facts` - Extract facts and opinions

## Configuration

Edit `config.py` or use environment variables:

```python
# Processing Configuration
MAX_ARTICLES_PER_REQUEST = 50
DEFAULT_CLUSTERS = 7
MAX_CLUSTERS = 15
MIN_CLUSTERS = 3
SIMILARITY_THRESHOLD = 0.7

# Performance Configuration  
USE_GPU = True
EMBEDDING_BATCH_SIZE = 32
MAX_TEXT_LENGTH = 1000000
```

## Architecture

```
python-pipeline/
├── main.py                 # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── core/
│   ├── config.py          # Configuration settings
│   └── database.py        # MongoDB connection and setup
├── schemas/               # Pydantic models
│   ├── article.py         # Article-related schemas
│   ├── cluster.py         # Clustering schemas
│   ├── cluster_storage.py # Cluster storage schemas
│   ├── response.py        # Response schemas
│   └── rss_feeds.py       # RSS feed schemas
├── services/              # API route handlers
│   ├── article_management.py     # Article CRUD operations
│   ├── cluster_processing.py     # Cluster processing endpoints
│   ├── cluster_maintainance.py   # Cluster maintenance tools
│   ├── cluster_retrievel.py      # Cluster search and retrieval
│   └── news_extraction.py        # RSS feed processing
├── utils/                 # Core processing logic
│   ├── cluster_storage.py        # Cluster storage management
│   ├── cluster_storage_utils.py  # Cluster utility functions
│   ├── image_service.py          # Image processing for clusters
│   └── data_processing/
│       ├── nlp_processor.py      # Main NLP processing coordinator
│       ├── clustering.py         # Article clustering algorithms
│       ├── fact_extractor.py     # Fact vs opinion classification
│       └── ai_generator.py       # AI article generation
└── modules/               # Ballerina integration modules
```

## Processing Pipeline

1. **Text Preprocessing**: Tokenization, lemmatization, stop word removal
2. **Embedding Generation**: Semantic embeddings using sentence-transformers
3. **Clustering**: KMeans clustering with TF-IDF feature enhancement
4. **Similarity Checking**: Compare new clusters with existing ones in database
5. **Cluster Merging**: Automatically merge similar clusters or create new ones
6. **Fact Extraction**: NER + sentiment analysis for fact/opinion separation
7. **Deduplication**: Fuzzy matching to merge similar facts
8. **Article Generation**: AI-powered neutral article creation
9. **Storage & Indexing**: Persist clusters with MongoDB for efficient retrieval
10. **URL Tracking**: Maintain links to original news sources

## Database Schema

### Stored Clusters
Each cluster in MongoDB contains:
- `cluster_id`: Unique identifier
- `cluster_name`: Human-readable name
- `keywords`: Extracted key terms
- `facts`: List of factual statements
- `musings`: List of opinions/analysis
- `generated_article`: AI-generated neutral article
- `articles_count`: Number of articles in cluster
- `sources`: News sources represented
- `article_urls`: URLs of original articles
- `embedding`: Vector representation for similarity
- `similarity_scores`: Internal similarity metrics
- `created_at`/`updated_at`: Timestamps

### Articles
Individual articles stored with:
- `title`, `content`, `source`, `url`
- `published_at`: Publication timestamp
- `cluster_id`: Reference to parent cluster
- `created_at`: Storage timestamp

## Error Handling

The API includes comprehensive error handling:
- Input validation with Pydantic
- Model loading fallbacks
- Graceful degradation when AI services are unavailable
- Detailed error messages for debugging

## Performance Features

- **GPU Acceleration**: Automatic GPU detection and usage
- **Batch Processing**: Efficient embedding generation
- **Async Processing**: Non-blocking background tasks
- **Resource Management**: Proper model loading and cleanup

## Production Deployment

For production deployment:

1. **Set up proper CORS origins** in `main.py`
2. **Use a production ASGI server**:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
3. **Configure environment variables** for production
4. **Set up task queue** (Redis + Celery) for heavy processing
5. **Add monitoring and logging**

## Troubleshooting

### Common Issues

1. **spaCy model not found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

2. **CUDA out of memory**:
   Set `USE_GPU=false` in config or reduce `EMBEDDING_BATCH_SIZE`

3. **Gemini API errors**:
   Check your API key and usage limits

4. **MongoDB connection issues**:
   Ensure MongoDB is running and connection string is correct

5. **Missing MIN_CLUSTERS/MAX_CLUSTERS error**:
   This has been fixed - ensure you have the latest config.py

6. **Cluster processing failures**:
   Check that all required dependencies are installed and models are downloaded

### Development

To run in development mode with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section
- Open an issue on GitHub
