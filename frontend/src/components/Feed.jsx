import { useState, useEffect } from 'react'
import { getFilteredContent, transformArticleData } from '../utils'
import NewsCard from './NewsCard'
import FeedSidebar from './FeedSidebar'

const Feed = ({ activeTab, onArticleClick, preferences }) => {
    const [articles, setArticles] = useState([])
    const [isTransitioning, setIsTransitioning] = useState(false)
    const [loading, setLoading] = useState(true)

    // Fetch content based on active tab
    useEffect(() => {
        const loadContent = async () => {
            setLoading(true)
            setIsTransitioning(true)
            try {
                // Use the new enhanced filtering function
                const fetchedData = await getFilteredContent(activeTab, {
                    limit: 50,
                    daysBack: 7,
                    minArticles: 3
                })

                console.log(`Data fetched for ${activeTab}:`, fetchedData)

                // Transform data to article format
                const transformedArticles = fetchedData.map(transformArticleData)
                setArticles(transformedArticles)
            } catch (error) {
                console.error('Error loading content:', error)
                setArticles([])
            }
            setLoading(false)

            // Remove transition after a short delay
            setTimeout(() => {
                setIsTransitioning(false)
            }, 300)
        }

        loadContent()
    }, [activeTab])

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
                Loading {activeTab} news...
            </div>
        )
    }

    if (articles.length === 0) {
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
                {articles.map((article, index) => {
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
