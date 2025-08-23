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

# Sample articles
articles = [
    {
        "title": "Tech Company Announces Major Layoffs",
        "content": "A major technology company announced today that it will be laying off 10,000 employees...",
        "source": "TechNews"
    },
    {
        "title": "Tech Giant Cuts Workforce Dramatically", 
        "content": "In a shocking move, the tech giant has decided to terminate thousands of workers...",
        "source": "BusinessDaily"
    }
]

# Process articles
response = requests.post(
    "http://localhost:8000/api/v1/articles/process",
    json={"articles": articles, "n_clusters": 3}
)

task_id = response.json()["task_id"]

# Check processing status
status = requests.get(f"http://localhost:8000/api/v1/articles/task/{task_id}")
```

## API Endpoints

### Health Check
- `GET /api/v1/health/` - Check API and model status

### Article Processing
- `POST /api/v1/articles/process` - Process articles through complete pipeline
- `GET /api/v1/articles/task/{task_id}` - Get processing task status

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
ground_news_api/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── routers/               # API route handlers
│   ├── articles.py        # Article processing endpoints
│   ├── processing.py      # Individual processing steps
│   └── health.py          # Health check endpoints
├── schemas/               # Pydantic models
│   ├── article.py         # Article-related schemas
│   ├── cluster.py         # Clustering schemas
│   └── response.py        # Response schemas
├── utils/                 # Core processing logic
│   ├── nlp_processor.py   # Main NLP processing coordinator
│   ├── clustering.py      # Article clustering algorithms
│   ├── fact_extractor.py  # Fact vs opinion classification
│   └── ai_generator.py    # AI article generation
└── models/                # Future database models
```

## Processing Pipeline

1. **Text Preprocessing**: Tokenization, lemmatization, stop word removal
2. **Embedding Generation**: Semantic embeddings using sentence-transformers
3. **Clustering**: KMeans clustering with TF-IDF feature enhancement
4. **Fact Extraction**: NER + sentiment analysis for fact/opinion separation
5. **Deduplication**: Fuzzy matching to merge similar facts
6. **Article Generation**: AI-powered neutral article creation

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
