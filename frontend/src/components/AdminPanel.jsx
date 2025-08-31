import { useState } from 'react'
import {
    getArticleStats,
    getArticleCount,
    fetchNewsApiArticles,
    extractRssArticles,
    submitManualFeed,
    scrapeProcessStore,
    processArticlesWithStorage,
    getWeeklyDigest,
    deleteArticle,
    // New API functions
    getDailyDigest,
    getClusterStats,
    getTrendingTopicsPython,
    getRecentClusters,
    processArticlesWithStoragePython,
    scrapeProcessStorePython,
    getSystemHealth,
    searchWithFilters,
    getClusterAnalytics
} from '../utils'

const AdminPanel = ({ onClose }) => {
    const [activeSection, setActiveSection] = useState('stats')
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    const handleApiCall = async (apiFunction, ...args) => {
        setLoading(true)
        setError(null)
        try {
            const response = await apiFunction(...args)
            setResult(response)
        } catch (err) {
            setError(err.message)
        }
        setLoading(false)
    }

    const sections = {
        stats: {
            title: 'Statistics & Health',
            actions: [
                {
                    name: 'Get System Health',
                    action: () => handleApiCall(getSystemHealth)
                },
                {
                    name: 'Get Article Stats',
                    action: () => handleApiCall(getArticleStats)
                },
                {
                    name: 'Get Article Count',
                    action: () => handleApiCall(getArticleCount)
                },
                {
                    name: 'Get Cluster Stats',
                    action: () => handleApiCall(getClusterStats)
                }
            ]
        },
        digest: {
            title: 'Content Digest',
            actions: [
                {
                    name: 'Get Daily Digest',
                    action: () => handleApiCall(getDailyDigest)
                },
                {
                    name: 'Get Weekly Digest',
                    action: () => handleApiCall(getWeeklyDigest)
                },
                {
                    name: 'Get Recent Clusters',
                    action: () => handleApiCall(getRecentClusters, 3, 20)
                },
                {
                    name: 'Get Trending (Python API)',
                    action: () => handleApiCall(getTrendingTopicsPython, 7, 3)
                }
            ]
        },
        search: {
            title: 'Advanced Search',
            actions: [
                {
                    name: 'Search Technology News',
                    action: () => handleApiCall(searchWithFilters, 'technology AI innovation', {
                        limit: 10,
                        sources: [],
                        keywords: ['tech', 'innovation', 'AI']
                    })
                },
                {
                    name: 'Search Business News',
                    action: () => handleApiCall(searchWithFilters, 'business finance market', {
                        limit: 10,
                        sources: [],
                        keywords: ['business', 'finance', 'economy']
                    })
                },
                {
                    name: 'Search International News',
                    action: () => handleApiCall(searchWithFilters, 'international global world', {
                        limit: 10,
                        sources: [],
                        keywords: ['international', 'global', 'world']
                    })
                }
            ]
        },
        newsApi: {
            title: 'News API',
            actions: [
                {
                    name: 'Fetch Tech Articles',
                    action: () => handleApiCall(fetchNewsApiArticles, 'technology', 10)
                },
                {
                    name: 'Fetch Business Articles',
                    action: () => handleApiCall(fetchNewsApiArticles, 'business', 10)
                }
            ]
        },
        rss: {
            title: 'RSS Extraction',
            actions: [
                {
                    name: 'Extract RSS (Last 2 Days)',
                    action: () => handleApiCall(extractRssArticles, {
                        from_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
                        to_date: new Date().toISOString().split('T')[0],
                        max_articles: 10,
                        strip_html: true,
                        fetch_full_content: true,
                        remove_duplicates: true
                    })
                }
            ]
        },
        processing: {
            title: 'Article Processing',
            actions: [
                {
                    name: 'Auto Scrape & Process (Ballerina)',
                    action: () => handleApiCall(scrapeProcessStore, 5, false, 7, 20)
                },
                {
                    name: 'Auto Scrape & Process (Python)',
                    action: () => handleApiCall(scrapeProcessStorePython, 7, 50)
                },
                {
                    name: 'Process Sample Articles (Python)',
                    action: () => handleApiCall(processArticlesWithStoragePython, {
                        articles: [
                            {
                                title: 'Sample AI Article',
                                content: 'This is a sample article about artificial intelligence developments.',
                                source: 'TechNews',
                                url: 'https://example.com/ai-article'
                            }
                        ],
                        n_clusters: 3,
                        store_clusters: true
                    })
                }
            ]
        },
        manual: {
            title: 'Manual Operations',
            actions: [
                {
                    name: 'Submit Sample Article',
                    action: () => handleApiCall(submitManualFeed, [{
                        title: 'Sample Test Article',
                        content: 'This is a test article submitted through the manual feed.',
                        source: 'Admin Panel',
                        url: 'https://example.com/test',
                        published_at: new Date().toISOString()
                    }])
                }
            ]
        }
    }

    return (
        <div className="admin-panel" style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
        }}>
            <div style={{
                backgroundColor: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                width: '90%',
                maxWidth: '800px',
                maxHeight: '80%',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column'
            }}>
                <div style={{
                    padding: '20px',
                    borderBottom: '1px solid var(--border)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <h2>API Admin Panel</h2>
                    <button onClick={onClose} style={{
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        color: 'var(--text)'
                    }}>×</button>
                </div>

                <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
                    {/* Sidebar */}
                    <div style={{
                        width: '200px',
                        borderRight: '1px solid var(--border)',
                        padding: '20px'
                    }}>
                        {Object.keys(sections).map(key => (
                            <button
                                key={key}
                                onClick={() => setActiveSection(key)}
                                style={{
                                    display: 'block',
                                    width: '100%',
                                    padding: '10px',
                                    margin: '5px 0',
                                    border: '1px solid var(--border)',
                                    backgroundColor: activeSection === key ? 'var(--accent)' : 'transparent',
                                    color: activeSection === key ? 'white' : 'var(--text)',
                                    cursor: 'pointer',
                                    borderRadius: '4px'
                                }}
                            >
                                {sections[key].title}
                            </button>
                        ))}
                    </div>

                    {/* Content */}
                    <div style={{ flex: 1, padding: '20px', overflow: 'auto' }}>
                        <h3>{sections[activeSection].title}</h3>

                        <div style={{ marginBottom: '20px' }}>
                            {sections[activeSection].actions.map((action, index) => (
                                <button
                                    key={index}
                                    onClick={action.action}
                                    disabled={loading}
                                    style={{
                                        padding: '10px 15px',
                                        margin: '5px 10px 5px 0',
                                        border: '1px solid var(--border)',
                                        backgroundColor: 'var(--accent)',
                                        color: 'white',
                                        cursor: 'pointer',
                                        borderRadius: '4px',
                                        opacity: loading ? 0.6 : 1
                                    }}
                                >
                                    {loading ? 'Loading...' : action.name}
                                </button>
                            ))}
                        </div>

                        {/* Results */}
                        {error && (
                            <div style={{
                                padding: '15px',
                                backgroundColor: '#fee',
                                border: '1px solid #fcc',
                                borderRadius: '4px',
                                marginBottom: '15px',
                                color: '#c33'
                            }}>
                                <strong>Error:</strong> {error}
                            </div>
                        )}

                        {result && (
                            <div style={{
                                backgroundColor: 'var(--card-bg)',
                                border: '1px solid var(--border)',
                                borderRadius: '4px',
                                padding: '15px'
                            }}>
                                <h4>Result:</h4>
                                <pre style={{
                                    backgroundColor: '#f5f5f5',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    overflow: 'auto',
                                    maxHeight: '300px',
                                    fontSize: '12px'
                                }}>
                                    {JSON.stringify(result, null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default AdminPanel
