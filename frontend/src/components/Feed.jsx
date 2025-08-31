import { useState, useEffect } from 'react'
import { fetchTrendingTopics, fetchRecentArticles, fetchAllClusters, searchClusters, transformArticleData } from '../utils'
import NewsCard from './NewsCard'
import FeedSidebar from './FeedSidebar'

const Feed = ({ activeTab, onArticleClick, preferences }) => {
    const [articles, setArticles] = useState([])
    const [filteredArticles, setFilteredArticles] = useState([])
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [loading, setLoading] = useState(true)

    // Fetch content based on active tab
    useEffect(() => {
        const loadContent = async () => {
            setLoading(true)
            try {
                let fetchedData = []

                switch (activeTab) {
                    case 'Trending':
                        fetchedData = await fetchTrendingTopics(7, 3)
                        break
                    case 'All':
                        fetchedData = await fetchAllClusters(50, 0)
                        break
                    case 'International':
                        fetchedData = await searchClusters('international global world')
                        break
                    case 'Local':
                        fetchedData = await searchClusters('local city state regional')
                        break
                    case 'Blindspot':
                        fetchedData = await fetchRecentArticles(20, 7)
                        break
                    default:
                        fetchedData = await fetchRecentArticles(20, 7)
                }

                // Transform data to article format
                const transformedArticles = fetchedData.map(transformArticleData)
                setArticles(transformedArticles)
            } catch (error) {
                console.error('Error loading content:', error)
                setArticles([])
            }
            setLoading(false)
        }

        loadContent()
    }, [activeTab])

    useEffect(() => {
        setIsTransitioning(true)

        setTimeout(() => {
            // Filter articles based on active tab
            const filtered = articles.filter(article => {
                if (activeTab === 'All') return true
                if (activeTab === 'Trending') return true // All trending articles
                return article.category && article.category.includes(activeTab)
            })
            setFilteredArticles(filtered)

            setTimeout(() => {
                setIsTransitioning(false)
            }, 50)
        }, 150)
    }, [activeTab, articles])

    // Determine featured cards (first and every 4th)
    const featuredIndices = new Set([0, 4, 8])
    const tallIndices = new Set([2, 6])

    if (loading) {
        return (
            <div className="loading" style={{
                padding: '60px 24px',
                textAlign: 'center',
                color: 'var(--muted)',
                fontSize: '14px'
            }}>
                Loading news articles...
            </div>
        )
    }

    if (filteredArticles.length === 0) {
        return (
            <div className="no-content" style={{
                padding: '60px 24px',
                textAlign: 'center',
                color: 'var(--muted)',
                fontSize: '14px'
            }}>
                No articles found for {activeTab}. Try a different category.
            </div>
        )
    }

    return (
        <section className="feed" aria-label="News feed">
            <div className={`grid ${isTransitioning ? 'transitioning' : ''}`}>
                {filteredArticles.map((article, index) => {
                    const isFeatured = featuredIndices.has(index)
                    const isTall = tallIndices.has(index)

                    return (
                        <NewsCard
                            key={article.id}
                            article={article}
                            index={index}
                            isFeatured={isFeatured}
                            isTall={isTall}
                            onClick={() => onArticleClick(article.id)}
                            preferences={preferences}
                        />
                    )
                })}
            </div>

            <FeedSidebar providers={[]} />
        </section>
    )
}

export default Feed
