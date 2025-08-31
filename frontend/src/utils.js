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

// API functions to connect to Ballerina backend
const API_BASE = '/news'

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
        const response = await fetch(`${API_BASE}/${id}`)
        if (!response.ok) throw new Error(`Failed to fetch article: ${response.status}`)
        const data = await response.json()
        console.log('Article by ID response:', data)
        return data.article || data.data
    } catch (error) {
        console.error('Error fetching article by ID:', error)
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

export async function searchClusters(query, limit = 20) {
    try {
        const response = await fetch(`${API_BASE}/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, limit })
        })
        if (!response.ok) throw new Error('Failed to search clusters')
        const data = await response.json()
        return data.data || []
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
