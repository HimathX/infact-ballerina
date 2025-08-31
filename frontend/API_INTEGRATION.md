# Frontend-Backend API Integration Guide

This document explains how the React frontend connects to the Python FastAPI backend.

## Backend Setup Required

### 1. Start Python FastAPI Backend
```bash
cd python-pipeline
python main.py
```
The API will be available at `http://localhost:8000`

### 2. API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation.

## Frontend Configuration

### Vite Proxy Setup
The frontend is configured to proxy API requests to the backend:

```javascript
// vite.config.js
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      secure: false,
    }
  }
}
```

## API Endpoints Used by Frontend

### 1. Trending Topics
- **Endpoint**: `GET /api/v1/clusters/trending-topics`
- **Usage**: Main trending news feed
- **Parameters**: 
  - `days_back=7` (default)
  - `min_articles=3` (default)

### 2. Recent Clusters
- **Endpoint**: `GET /api/v1/clusters/recent`
- **Usage**: "All" tab content
- **Parameters**:
  - `days_back=30`
  - `limit=50`

### 3. Search Clusters
- **Endpoint**: `POST /api/v1/clusters/search`
- **Usage**: Category-specific content (International, Local)
- **Body**: `{ "query": "search terms", "limit": 20 }`

### 4. Get Cluster by ID
- **Endpoint**: `GET /api/v1/clusters/{cluster_id}`
- **Usage**: Article detail view
- **Returns**: Full cluster data for article view

### 5. Cluster Statistics
- **Endpoint**: `GET /api/v1/clusters/stats`
- **Usage**: System metrics (optional)

### 6. Daily Digest
- **Endpoint**: `GET /api/v1/daily-digest`
- **Usage**: Daily summary (optional)

## Data Transformation

The frontend transforms cluster data from the backend into article format:

```javascript
// Example transformation
function transformClusterToArticle(cluster) {
    return {
        id: cluster.cluster_id,
        title: cluster.cluster_name,
        excerpt: cluster.factual_summary?.substring(0, 200) + '...',
        bullets: cluster.facts || [],
        category: ['Trending'],
        time: cluster.created_at,
        sources: cluster.sources?.map(source => ({
            name: source,
            domain: source.toLowerCase() + '.com',
            bias: 'neu',
            musings: 'Source coverage'
        })),
        content: [cluster.generated_article],
        context: cluster.contextual_analysis,
        background: cluster.background_info,
        coverage: `High — ${cluster.articles_count} articles processed`
    }
}
```

## Tab Mapping

- **Trending**: `/api/v1/clusters/trending-topics`
- **All**: `/api/v1/clusters/recent` (30 days)
- **International**: Search for "international global world"
- **Local**: Search for "local city state regional"
- **Blindspot**: Recent clusters (7 days)

## Error Handling

All API functions include error handling:

```javascript
try {
    const response = await fetch(url)
    if (!response.ok) throw new Error('API request failed')
    const data = await response.json()
    return data.clusters || []
} catch (error) {
    console.error('Error:', error)
    return []
}
```

## Development Workflow

1. **Start Backend**:
   ```bash
   cd python-pipeline
   python main.py
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access Application**:
   - Frontend: `http://localhost:5173`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## Sample API Responses

### Trending Topics Response
```json
{
  "clusters": [
    {
      "cluster_id": "65f8a9b2c1d4e7f234567890",
      "cluster_name": "AI Ethics and Regulation",
      "articles_count": 12,
      "sources": ["Reuters", "TechCrunch"],
      "keywords": ["AI", "ethics", "regulation"],
      "facts": [
        "EU AI Act received final approval",
        "OpenAI announced new safety measures"
      ],
      "generated_article": "Recent developments in AI regulation...",
      "factual_summary": "The European Union finalized AI legislation...",
      "contextual_analysis": "These developments occur amid growing concerns...",
      "created_at": "2025-08-29T14:30:00Z",
      "image_url": "https://example.com/image.jpg",
      "article_urls": ["https://reuters.com/...", "https://techcrunch.com/..."]
    }
  ]
}
```

### Cluster Detail Response
```json
{
  "cluster": {
    "cluster_id": "65f8a9b2c1d4e7f234567890",
    "cluster_name": "AI Ethics and Regulation",
    "articles_count": 12,
    "sources": ["Reuters", "TechCrunch", "MIT Technology Review"],
    "keywords": ["artificial intelligence", "ethics", "regulation"],
    "facts": [
      "The EU AI Act received final approval",
      "OpenAI announced new safety measures",
      "Tech companies formed ethics consortium"
    ],
    "musings": [
      "Industry experts see this as a turning point",
      "Critics argue regulations may stifle innovation"
    ],
    "generated_article": "Full neutral article content...",
    "factual_summary": "Comprehensive summary...",
    "contextual_analysis": "Detailed context...",
    "background_info": "Historical background...",
    "image_url": "https://example.com/image.jpg",
    "article_urls": ["https://reuters.com/...", "https://techcrunch.com/..."],
    "created_at": "2025-08-29T14:30:00Z"
  }
}
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Make sure both frontend and backend are running
2. **API Not Found**: Check that Python backend is running on port 8000
3. **Empty Content**: Verify backend has processed clusters in the database
4. **Network Errors**: Check console for specific error messages

### Debug Tips

- Open browser dev tools to monitor network requests
- Check `http://localhost:8000/docs` to test API endpoints directly
- Verify backend logs for processing errors
- Use the cluster stats endpoint to check system status

## Required Backend Setup

For the frontend to work properly, ensure your Python backend has:

1. **Environment Variables**: 
   - `GEMINI_API_KEY` for AI processing
   - `MONGODB_URL` for database connection

2. **Dependencies Installed**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Sample Data**: Run the scrape-process-store endpoint to populate the database:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/scrape-process-store?max_articles=20"
   ```
