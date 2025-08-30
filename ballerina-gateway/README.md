# Ballerina News Gateway

A comprehensive news aggregation and clustering service built with Ballerina, featuring intelligent article processing, clustering capabilities, and RESTful API endpoints for news management.

## Features

- **News Article Extraction**: Fetch articles from News API and RSS feeds
- **Intelligent Clustering**: AI-powered article clustering using external Python services
- **Duplicate Detection**: Automatic duplicate article detection and filtering
- **RESTful API**: Comprehensive REST endpoints for article and cluster management
- **MongoDB Integration**: Persistent storage with optimized queries
- **Real-time Processing**: Asynchronous processing for long-running operations
- **Search & Analytics**: Advanced search capabilities and trending topic analysis

## Prerequisites

- [Ballerina](https://ballerina.io/) 2201.8.0 or later
- [MongoDB](https://www.mongodb.com/) 4.4 or later
- Python FastAPI service (for clustering functionality)
- News API key from [NewsAPI.org](https://newsapi.org/)

## Installation

### Clone the repository

```bash
git clone <repository-url>
cd ballerina_gateway
```

### Configure environment variables

Create a `Config.toml` file in the project root:

```toml
[ballerina_gateway.config]
mongoUri = "mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority"
databaseName = "newsstore"

[ballerina_gateway.utils]
newsApiKey = "your-news-api-key-here"
```

### Install dependencies

```bash
bal build
```

### Start external services

- Ensure MongoDB is running
- Start the Python FastAPI clustering service on [http://127.0.0.1:8091](http://127.0.0.1:8091)

## Quick Start

### Run the service

```bash
bal run
```

Service will be available at `http://localhost:9090/news`

### Test the API

```bash
# Get article statistics
curl http://localhost:9090/news/stats

# Fetch articles from News API
curl -X POST http://localhost:9090/news/fetchArticles \
  -H "Content-Type: application/json" \
  -d '{"query": "technology", "pageSize": 10}'
```

## API Documentation

### Article Management

#### Fetch Articles from News API

```http
POST /news/fetchArticles
Content-Type: application/json

{
  "query": "artificial intelligence",
  "pageSize": 20
}
```

#### Get Articles with Pagination

```http
GET /news/articles?limit=20&skip=0&sort_by=extracted_at&sort_order=-1
```

#### Get Recent Articles

```http
GET /news/recent?limit=10&days_back=7&source=BBC
```

#### Get Article by ID

```http
GET /news/{article_id}
```

#### Delete Article

```http
DELETE /news/{article_id}
```

#### Get Article Statistics

```http
GET /news/stats
```

### RSS Extraction

#### Extract Articles from RSS Feeds

```http
POST /news/rss-extract
Content-Type: application/json

{
  "from_date": "2025-08-22",
  "to_date": "2025-08-24",
  "max_articles": 50,
  "strip_html": true,
  "fetch_full_content": true,
  "remove_duplicates": true,
  "include_metadata": true,
  "verbose": false,
  "min_content_length": 100
}
```

### Manual Article Feed

#### Submit Articles Manually

```http
POST /news/feed-manual
Content-Type: application/json

{
  "articles": [
    {
      "title": "Breaking News Title",
      "content": "Article content here...",
      "source": "News Source",
      "url": "https://example.com/article",
      "image_url": "https://example.com/image.jpg",
      "published_at": "2025-08-30T10:00:00Z"
    }
  ]
}
```

### Clustering & Processing

#### Process Articles with Clustering

```http
POST /news/process-with-storage
Content-Type: application/json

{
  "articles": [
    {
      "title": "Article Title",
      "content": "Article content...",
      "source": "Source Name",
      "published_at": "2025-08-30T10:00:00Z",
      "url": "https://example.com/article",
      "image_url": "https://example.com/image.jpg"
    }
  ],
  "n_clusters": 3,
  "store_clusters": true,
  "force_new_clusters": false
}
```

#### Auto Processing (Scrape, Process & Store)

```http
POST /news/scrape-process-store?n_clusters=5&days_back=7&max_articles=100&force_new_clusters=false
```

### Cluster Management

#### Get All Clusters

```http
GET /news/allClusters?limit=20&skip=0&sort_by=created_at&sort_order=-1
```

#### Get Cluster by ID

```http
GET /news/clusters/{cluster_id}
```

#### Get Articles in Cluster

```http
GET /news/clusters/{cluster_id}/articles?sort_by=published_at&sort_order=-1
```

#### Search Clusters

```http
POST /news/search
Content-Type: application/json

{
  "query": "climate change",
  "limit": 10,
  "sources": ["BBC", "CNN"],
  "keywords": ["environment", "global warming"]
}
```

#### Get Trending Topics

```http
GET /news/trending-topics?days_back=30&min_articles=5
```

#### Get Weekly Digest

```http
GET /news/weekly-digest
```

## Architecture

### Project Structure

```
ballerina_gateway/
├── main.bal                                # Main service file
├── modules/
│   ├── config/
│   │   └── config.bal                      # Database configuration
│   ├── types/
│   │   ├── cluster_managent.bal            # Cluster-related types
│   │   ├── cluster_processing_types.bal    # Processing types
│   │   ├── news_management.bal             # News management types
│   │   └── new_extraction_types.bal        # Extraction types
│   └── utils/
│       ├── article_management_utils.bal    # Article operations
│       ├── cluster_management.bal          # Cluster operations
│       ├── cluster_processing_utils.bal    # Processing utilities
│       ├── news_extraction_utils.bal       # Extraction utilities
│       └── validation.bal                  # Input validation
├── Config.toml                             # Configuration file
└── Ballerina.toml                          # Project metadata
```

### Key Components

- **HTTP Service Layer**: RESTful endpoints with comprehensive error handling
- **Business Logic Layer**: Article processing, clustering, and analytics
- **Data Access Layer**: MongoDB operations with connection pooling
- **External Integrations**: News API, RSS extraction service, Python clustering service
- **Validation Layer**: Input sanitization and parameter validation

## Configuration

### Environment Variables

- `MONGO_URI`: MongoDB connection string
- `NEWS_API_KEY`: News API authentication key
- `DB_NAME`: Database name (default: "newsstore")

### Service Configuration

- **Port**: 9090
- **Timeout**: 15 minutes for long-running operations
- **Request Limits**: 10MB max entity body size
- **Connection Pooling**: Optimized for MongoDB operations

## Security Features

- Input validation and sanitization
- MongoDB injection prevention
- Request size limits
- Timeout protection
- Error handling without information leakage

## Monitoring & Logging

- Comprehensive logging with structured format
- Error tracking and debugging information
- Performance metrics for database operations
- Request/response logging for external services

## Testing

```bash
# Run tests
bal test

# Run with coverage
bal test --code-coverage
```

## Deployment

### Docker Deployment

```dockerfile
FROM ballerina/ballerina:2201.8.0
COPY . /app
WORKDIR /app
RUN bal build
EXPOSE 9090
CMD ["bal", "run", "target/bin/ballerina_gateway.jar"]
```

### Production Considerations

- Use environment-specific configuration files
- Enable connection pooling for MongoDB
- Configure proper logging levels
- Set up health checks and monitoring
- Use reverse proxy for load balancing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## API Response Format

All API responses follow a consistent format:

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2025-08-30T10:00:00Z"
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "timestamp": "2025-08-30T10:00:00Z"
}
```

## Troubleshooting

### Common Issues

#### MongoDB Connection Issues

- Verify connection string in `Config.toml`
- Check network connectivity
- Ensure MongoDB service is running

#### External Service Timeouts

- Verify Python clustering service is running on port 8091
- Check RSS extraction service availability
- Review timeout configurations

#### Memory Issues

- Monitor heap usage during large article processing
- Adjust JVM parameters if needed
- Consider pagination for large datasets

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ballerina](https://ballerina.io/) for the excellent integration platform
- [MongoDB](https://www.mongodb.com/) for reliable data storage
- [NewsAPI](https://newsapi.org/) for news data access
- Contributors and maintainers

For more information, please refer to the [API documentation](docs/api.md) or contact the development team.