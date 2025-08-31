import { useState, useEffect } from 'react'
import { articles, providers } from '../data'
import NewsCard from './NewsCard'
import FeedSidebar from './FeedSidebar'

const Feed = ({ activeTab, onArticleClick, preferences }) => {
    const [filteredArticles, setFilteredArticles] = useState([])
    const [isTransitioning, setIsTransitioning] = useState(false)

    useEffect(() => {
        setIsTransitioning(true)

        setTimeout(() => {
            const filtered = articles.filter(article => {
                if (activeTab === 'All') return true
                return article.category.includes(activeTab)
            })
            setFilteredArticles(filtered)

            setTimeout(() => {
                setIsTransitioning(false)
            }, 50)
        }, 150)
    }, [activeTab])

    // Determine featured cards (first and every 4th)
    const featuredIndices = new Set([0, 4, 8])
    const tallIndices = new Set([2, 6])

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

            <FeedSidebar providers={providers} />
        </section>
    )
}

export default Feed
