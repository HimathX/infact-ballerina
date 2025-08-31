// Utility functions for the Infact app

export function timeAgo(iso) {
    const now = new Date()
    const then = new Date(iso)
    const s = Math.floor((now - then) / 1000)
    const mins = Math.floor(s / 60)
    const hrs = Math.floor(mins / 60)
    const days = Math.floor(hrs / 24)
    if (s < 60) return 'just now'
    if (mins < 60) return `${mins}m ago`
    if (hrs < 24) return `${hrs}h ago`
    return `${days}d ago`
}

export function faviconLetter(domain) {
    const d = (domain || '').replace(/^www\./, '').trim()
    return d ? d[0].toUpperCase() : '•'
}

export function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image()
        img.onload = () => resolve(img)
        img.onerror = reject
        img.src = src
    })
}

export function formatFetchedTime() {
    const now = new Date()
    const pad = n => (n < 10 ? '0' + n : '' + n)
    return `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())} UTC`
}

// API functions to connect to Ballerina backend and Python pipeline
const API_BASE = '/news'  // Ballerina backend (port 9090)
const PYTHON_API_BASE = '/api/v1'  // Python FastAPI service (port 8000)

export async function fetchArticles(limit = 20, skip = 0) {
    try {
        const response = await fetch(`${API_BASE}/articles?limit=${limit}&skip=${skip}`)
        if (!response.ok) throw new Error('Failed to fetch articles')
        const data = await response.json()
        return data.data || []
    } catch (error) {
        console.error('Error fetching articles:', error)
        return []
    }
}

export async function fetchArticleById(id) {
    try {
        console.log('Fetching article by ID from:', `${API_BASE}/${id}`)

        // First try as an individual article
        let response = await fetch(`${API_BASE}/${id}`)
        if (response.ok) {
            const data = await response.json()
            console.log('Individual article response:', data)
            return data.article || data.data
        }

        // If not found, try as a cluster
        console.log('Article not found, trying as cluster:', `${API_BASE}/clusters/${id}`)
        response = await fetch(`${API_BASE}/clusters/${id}`)
        if (response.ok) {
            const data = await response.json()
            console.log('Cluster response:', data)
            const cluster = data.cluster || data.data

            // Transform cluster data to look like an article for the ArticleView component
            if (cluster) {
                return {
                    _id: cluster._id,
                    title: cluster.cluster_name || 'Untitled Cluster',
                    content: cluster.generated_article || cluster.factual_summary || '',
                    bullets: cluster.facts || [],
                    key_points: cluster.facts || [],
                    context: cluster.context || '',
                    background: cluster.background || '',
                    coverage: 'Cluster Analysis',
                    sources: cluster.sources || [],
                    url: null, // Clusters don't have original URLs
                    published_at: cluster.created_at || cluster.updated_at,
                    articles_count: cluster.articles_count || 0,
                    article_urls: cluster.article_urls || [],
                    source_counts: cluster.source_counts || {}
                }
            }
        }

        throw new Error(`Neither article nor cluster found for ID: ${id}`)
    } catch (error) {
        console.error('Error fetching article/cluster by ID:', error)
        return null
    }
}

export async function fetchAllClusters(limit = 20, skip = 0) {
    try {
        console.log('Fetching all clusters from:', `${API_BASE}/allClusters?limit=${limit}&skip=${skip}`)
        const response = await fetch(`${API_BASE}/allClusters?limit=${limit}&skip=${skip}`)
        if (!response.ok) throw new Error(`Failed to fetch clusters: ${response.status}`)
        const data = await response.json()
        console.log('All clusters response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching clusters:', error)
        return []
    }
}

export async function fetchTrendingTopics(daysBack = 7, minArticles = 3) {
    try {
        console.log('Fetching trending topics from:', `${API_BASE}/trending-topics?days_back=${daysBack}&min_articles=${minArticles}`)
        const response = await fetch(`${API_BASE}/trending-topics?days_back=${daysBack}&min_articles=${minArticles}`)
        if (!response.ok) throw new Error(`Failed to fetch trending topics: ${response.status}`)
        const data = await response.json()
        console.log('Trending topics response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching trending topics:', error)
        return []
    }
}

export async function fetchRecentArticles(limit = 20, daysBack = 7) {
    try {
        const response = await fetch(`${API_BASE}/recent?limit=${limit}&days_back=${daysBack}`)
        if (!response.ok) throw new Error('Failed to fetch recent articles')
        const data = await response.json()
        return data.data || []
    } catch (error) {
        console.error('Error fetching recent articles:', error)
        return []
    }
}

export async function searchClusters(query, limit = 20, sources = [], keywords = []) {
    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query,
                limit,
                sources,
                keywords
            })
        })
        if (!response.ok) throw new Error('Failed to search clusters')
        const data = await response.json()
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error searching clusters:', error)
        return []
    }
}

export async function getWeeklyDigest() {
    try {
        console.log('Fetching weekly digest from:', `${API_BASE}/weekly-digest`)
        const response = await fetch(`${API_BASE}/weekly-digest`)
        if (!response.ok) throw new Error(`Failed to fetch weekly digest: ${response.status}`)
        const data = await response.json()
        console.log('Weekly digest response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching weekly digest:', error)
        return []
    }
}

export async function getClusterById(clusterId) {
    try {
        console.log('Fetching cluster by ID from:', `${API_BASE}/clusters/${clusterId}`)
        const response = await fetch(`${API_BASE}/clusters/${clusterId}`)
        if (!response.ok) throw new Error(`Failed to fetch cluster: ${response.status}`)
        const data = await response.json()
        console.log('Cluster by ID response:', data)
        return data.cluster || data.data
    } catch (error) {
        console.error('Error fetching cluster by ID:', error)
        return null
    }
}

export async function getClusterArticles(clusterId, sortBy = 'published_at', sortOrder = -1) {
    try {
        console.log('Fetching cluster articles from:', `${API_BASE}/clusters/${clusterId}/articles?sort_by=${sortBy}&sort_order=${sortOrder}`)
        const response = await fetch(`${API_BASE}/clusters/${clusterId}/articles?sort_by=${sortBy}&sort_order=${sortOrder}`)
        if (!response.ok) throw new Error(`Failed to fetch cluster articles: ${response.status}`)
        const data = await response.json()
        console.log('Cluster articles response:', data)
        return data.articles || data.data || []
    } catch (error) {
        console.error('Error fetching cluster articles:', error)
        return []
    }
}

export async function getArticleStats() {
    try {
        console.log('Fetching article stats from:', `${API_BASE}/stats`)
        const response = await fetch(`${API_BASE}/stats`)
        if (!response.ok) throw new Error(`Failed to fetch stats: ${response.status}`)
        const data = await response.json()
        console.log('Article stats response:', data)
        return data
    } catch (error) {
        console.error('Error fetching article stats:', error)
        return null
    }
}

export async function getArticleCount() {
    try {
        console.log('Fetching article count from:', `${API_BASE}/count`)
        const response = await fetch(`${API_BASE}/count`)
        if (!response.ok) throw new Error(`Failed to fetch count: ${response.status}`)
        const data = await response.json()
        console.log('Article count response:', data)
        return data.count || 0
    } catch (error) {
        console.error('Error fetching article count:', error)
        return 0
    }
}

export async function deleteArticle(articleId) {
    try {
        console.log('Deleting article:', `${API_BASE}/${articleId}`)
        const response = await fetch(`${API_BASE}/${articleId}`, {
            method: 'DELETE'
        })
        if (!response.ok) throw new Error(`Failed to delete article: ${response.status}`)
        const data = await response.json()
        console.log('Delete article response:', data)
        return data
    } catch (error) {
        console.error('Error deleting article:', error)
        return null
    }
}

export async function submitManualFeed(articles) {
    try {
        console.log('Submitting manual feed:', `${API_BASE}/feed-manual`)
        const response = await fetch(`${API_BASE}/feed-manual`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ articles })
        })
        if (!response.ok) throw new Error(`Failed to submit manual feed: ${response.status}`)
        const data = await response.json()
        console.log('Manual feed response:', data)
        return data
    } catch (error) {
        console.error('Error submitting manual feed:', error)
        return null
    }
}

export async function fetchNewsApiArticles(query, pageSize = 20) {
    try {
        console.log('Fetching News API articles:', `${API_BASE}/fetchArticles`)
        const response = await fetch(`${API_BASE}/fetchArticles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, pageSize })
        })
        if (!response.ok) throw new Error(`Failed to fetch News API articles: ${response.status}`)
        const data = await response.json()
        console.log('News API articles response:', data)
        return data
    } catch (error) {
        console.error('Error fetching News API articles:', error)
        return null
    }
}

export async function extractRssArticles(extractionParams) {
    try {
        console.log('Extracting RSS articles:', `${API_BASE}/rss-extract`)
        const response = await fetch(`${API_BASE}/rss-extract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(extractionParams)
        })
        if (!response.ok) throw new Error(`Failed to extract RSS articles: ${response.status}`)
        const data = await response.json()
        console.log('RSS extraction response:', data)
        return data
    } catch (error) {
        console.error('Error extracting RSS articles:', error)
        return null
    }
}

export async function processArticlesWithStorage(processingRequest) {
    try {
        console.log('Processing articles with storage:', `${API_BASE}/process-with-storage`)
        const response = await fetch(`${API_BASE}/process-with-storage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(processingRequest)
        })
        if (!response.ok) throw new Error(`Failed to process articles: ${response.status}`)
        const data = await response.json()
        console.log('Process articles response:', data)
        return data
    } catch (error) {
        console.error('Error processing articles:', error)
        return null
    }
}

export async function scrapeProcessStore(nClusters, forceNewClusters, daysBack, maxArticles) {
    try {
        const params = new URLSearchParams()
        if (nClusters) params.append('n_clusters', nClusters.toString())
        if (forceNewClusters !== undefined) params.append('force_new_clusters', forceNewClusters.toString())
        if (daysBack) params.append('days_back', daysBack.toString())
        if (maxArticles) params.append('max_articles', maxArticles.toString())

        const url = `${API_BASE}/scrape-process-store?${params.toString()}`
        console.log('Auto scrape-process-store:', url)

        const response = await fetch(url, { method: 'POST' })
        if (!response.ok) throw new Error(`Failed to scrape-process-store: ${response.status}`)
        const data = await response.json()
        console.log('Scrape-process-store response:', data)
        return data
    } catch (error) {
        console.error('Error in scrape-process-store:', error)
        return null
    }
}

// Transform article data to match frontend expectations
export function transformArticleData(item) {
    // Handle both cluster and article data structures
    return {
        id: item._id || item.id || Math.random().toString(36),
        title: item.cluster_name || item.title || 'Untitled',
        excerpt: item.summary || (Array.isArray(item.facts) ? item.facts.slice(0, 2).join('. ') + '...' : '') || '',
        bullets: item.facts || item.key_points || item.bullets || [],
        category: item.categories || ['All'],
        time: item.created_at || item.published_at || item.extracted_at || new Date().toISOString(),
        imageQuery: item.cluster_name || item.title || 'news',
        sources: item.sources || [],
        content: item.content ? [item.content] : (item.facts || []),
        context: item.context || '',
        background: item.background || '',
        coverage: item.coverage || 'Medium'
    }
}

// =================== ADDITIONAL API ENDPOINTS FROM PYTHON PIPELINE ===================

// Daily digest endpoint
export async function getDailyDigest() {
    try {
        console.log('Fetching daily digest from:', `${PYTHON_API_BASE}/daily-digest`)
        const response = await fetch(`${PYTHON_API_BASE}/daily-digest`)
        if (!response.ok) throw new Error(`Failed to fetch daily digest: ${response.status}`)
        const data = await response.json()
        console.log('Daily digest response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching daily digest:', error)
        return []
    }
}

// Cluster statistics endpoint
export async function getClusterStats() {
    try {
        console.log('Fetching cluster stats from:', `${PYTHON_API_BASE}/clusters/stats`)
        const response = await fetch(`${PYTHON_API_BASE}/clusters/stats`)
        if (!response.ok) throw new Error(`Failed to fetch cluster stats: ${response.status}`)
        const data = await response.json()
        console.log('Cluster stats response:', data)
        return data
    } catch (error) {
        console.error('Error fetching cluster stats:', error)
        return null
    }
}

// Advanced cluster search with additional parameters
export async function searchClustersAdvanced(searchParams) {
    try {
        console.log('Advanced cluster search:', `${PYTHON_API_BASE}/clusters/search`)
        const response = await fetch(`${PYTHON_API_BASE}/clusters/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchParams)
        })
        if (!response.ok) throw new Error(`Failed to search clusters: ${response.status}`)
        const data = await response.json()
        console.log('Advanced search response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error in advanced cluster search:', error)
        return []
    }
}

// Get trending topics with Python API
export async function getTrendingTopicsPython(daysBack = 7, minArticles = 3) {
    try {
        console.log('Fetching trending topics from Python API:', `${PYTHON_API_BASE}/clusters/trending-topics?days_back=${daysBack}&min_articles=${minArticles}`)
        const response = await fetch(`${PYTHON_API_BASE}/clusters/trending-topics?days_back=${daysBack}&min_articles=${minArticles}`)
        if (!response.ok) throw new Error(`Failed to fetch trending topics: ${response.status}`)
        const data = await response.json()
        console.log('Python trending topics response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching trending topics from Python API:', error)
        return []
    }
}

// Get recent clusters from Python API
export async function getRecentClusters(daysBack = 3, limit = 20) {
    try {
        console.log('Fetching recent clusters from Python API:', `${PYTHON_API_BASE}/clusters/recent?days_back=${daysBack}&limit=${limit}`)
        const response = await fetch(`${PYTHON_API_BASE}/clusters/recent?days_back=${daysBack}&limit=${limit}`)
        if (!response.ok) throw new Error(`Failed to fetch recent clusters: ${response.status}`)
        const data = await response.json()
        console.log('Recent clusters response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error fetching recent clusters:', error)
        return []
    }
}

// Process articles with storage (main processing pipeline)
export async function processArticlesWithStoragePython(processingRequest) {
    try {
        console.log('Processing articles with Python pipeline:', `${PYTHON_API_BASE}/process-with-storage`)
        const response = await fetch(`${PYTHON_API_BASE}/process-with-storage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(processingRequest)
        })
        if (!response.ok) throw new Error(`Failed to process articles: ${response.status}`)
        const data = await response.json()
        console.log('Python process articles response:', data)
        return data
    } catch (error) {
        console.error('Error processing articles with Python pipeline:', error)
        return null
    }
}

// Automated scrape-process-store pipeline
export async function scrapeProcessStorePython(daysBack = 7, maxArticles = 100) {
    try {
        console.log('Auto scrape-process-store with Python:', `${PYTHON_API_BASE}/scrape-process-store?days_back=${daysBack}&max_articles=${maxArticles}`)
        const response = await fetch(`${PYTHON_API_BASE}/scrape-process-store?days_back=${daysBack}&max_articles=${maxArticles}`, {
            method: 'POST'
        })
        if (!response.ok) throw new Error(`Failed to scrape-process-store: ${response.status}`)
        const data = await response.json()
        console.log('Python scrape-process-store response:', data)
        return data
    } catch (error) {
        console.error('Error in Python scrape-process-store:', error)
        return null
    }
}

// Get system health status
export async function getSystemHealth() {
    try {
        console.log('Checking system health:', '/health')
        const response = await fetch('/health')
        if (!response.ok) throw new Error(`Health check failed: ${response.status}`)
        const data = await response.json()
        console.log('System health response:', data)
        return data
    } catch (error) {
        console.error('Error checking system health:', error)
        return null
    }
}

// Enhanced search with filters and pagination
export async function searchWithFilters(query, filters = {}) {
    try {
        const searchParams = {
            query,
            limit: filters.limit || 20,
            sources: filters.sources || [],
            keywords: filters.keywords || [],
            date_from: filters.dateFrom,
            date_to: filters.dateTo,
            min_articles: filters.minArticles,
            sort_by: filters.sortBy || 'created_at',
            sort_order: filters.sortOrder || -1
        }

        console.log('Enhanced search with filters:', searchParams)
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchParams)
        })
        if (!response.ok) throw new Error(`Search failed: ${response.status}`)
        const data = await response.json()
        console.log('Enhanced search response:', data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error('Error in enhanced search:', error)
        return []
    }
}

// Get cluster analytics
export async function getClusterAnalytics(clusterId) {
    try {
        console.log('Fetching cluster analytics:', `${API_BASE}/clusters/${clusterId}/analytics`)
        const response = await fetch(`${API_BASE}/clusters/${clusterId}/analytics`)
        if (!response.ok) throw new Error(`Failed to fetch cluster analytics: ${response.status}`)
        const data = await response.json()
        console.log('Cluster analytics response:', data)
        return data
    } catch (error) {
        console.error('Error fetching cluster analytics:', error)
        return null
    }
}

// Export cluster data
export async function exportClusterData(clusterId, format = 'json') {
    try {
        console.log('Exporting cluster data:', `${API_BASE}/clusters/${clusterId}/export?format=${format}`)
        const response = await fetch(`${API_BASE}/clusters/${clusterId}/export?format=${format}`)
        if (!response.ok) throw new Error(`Failed to export cluster data: ${response.status}`)

        if (format === 'json') {
            const data = await response.json()
            return data
        } else {
            const blob = await response.blob()
            return blob
        }
    } catch (error) {
        console.error('Error exporting cluster data:', error)
        return null
    }
}

// Bulk operations
export async function bulkDeleteArticles(articleIds) {
    try {
        console.log('Bulk deleting articles:', `${API_BASE}/articles/bulk-delete`)
        const response = await fetch(`${API_BASE}/articles/bulk-delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ article_ids: articleIds })
        })
        if (!response.ok) throw new Error(`Failed to bulk delete articles: ${response.status}`)
        const data = await response.json()
        console.log('Bulk delete response:', data)
        return data
    } catch (error) {
        console.error('Error in bulk delete:', error)
        return null
    }
}

// Advanced filtering for feed
export async function getFilteredContent(tab, filters = {}) {
    try {
        let endpoint
        let params = {}

        switch (tab.toLowerCase()) {
            case 'trending':
                endpoint = 'trending-topics'
                params = {
                    days_back: filters.daysBack || 7,
                    min_articles: filters.minArticles || 3
                }
                break
            case 'recent':
                endpoint = 'recent'
                params = {
                    limit: filters.limit || 20,
                    days_back: filters.daysBack || 7
                }
                break
            case 'international':
                return await searchWithFilters('international global world foreign', filters)
            case 'local':
                return await searchWithFilters('local city state regional domestic', filters)
            case 'technology':
                return await searchWithFilters('technology tech innovation digital AI', filters)
            case 'business':
                return await searchWithFilters('business finance economy market', filters)
            case 'politics':
                return await searchWithFilters('politics government policy election', filters)
            case 'health':
                return await searchWithFilters('health medical healthcare medicine', filters)
            case 'science':
                return await searchWithFilters('science research study discovery', filters)
            case 'sports':
                return await searchWithFilters('sports game match tournament', filters)
            default:
                endpoint = 'allClusters'
                params = {
                    limit: filters.limit || 50,
                    skip: filters.skip || 0
                }
        }

        const queryString = new URLSearchParams(params).toString()
        const url = `${API_BASE}/${endpoint}${queryString ? '?' + queryString : ''}`

        console.log(`Fetching filtered content for ${tab}:`, url)
        const response = await fetch(url)
        if (!response.ok) throw new Error(`Failed to fetch ${tab} content: ${response.status}`)
        const data = await response.json()
        console.log(`${tab} content response:`, data)
        return data.clusters || data.data || []
    } catch (error) {
        console.error(`Error fetching ${tab} content:`, error)
        return []
    }
}
