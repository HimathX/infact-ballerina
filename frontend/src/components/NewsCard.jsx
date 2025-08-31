import { useState, useEffect } from 'react'
import { articleImages } from '../data'

const NewsCard = ({ article, index, isFeatured, isTall, onClick, preferences }) => {
    const [imageLoaded, setImageLoaded] = useState(false)
    const [imageError, setImageError] = useState(false)

    useEffect(() => {
        const imageUrl = articleImages[article.id]
        if (imageUrl) {
            const img = new Image()
            img.onload = () => setImageLoaded(true)
            img.onerror = () => setImageError(true)
            img.src = imageUrl
        }
    }, [article.id])

    const timeAgo = (iso) => {
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

    const faviconLetter = (domain) => {
        const d = (domain || '').replace(/^www\./, '').trim()
        return d ? d[0].toUpperCase() : '•'
    }

    let cardClass = 'card parallax-container'
    if (isFeatured) cardClass += ' featured'
    if (isTall) cardClass += ' tall'

    // Bias counts for the mini legend
    const counts = { neg: 0, neu: 0, pos: 0 }
    article.sources.forEach(s => counts[s.bias]++)

    const handleClick = () => {
        onClick()
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onClick()
        }
    }

    return (
        <article
            className={cardClass}
            role="article"
            tabIndex="0"
            style={{
                animationDelay: `${index * 0.1}s`,
                transform: preferences.reduceMotion ? 'none' : undefined
            }}
            onClick={handleClick}
            onKeyDown={handleKeyDown}
        >
            <div className={`img ${!imageLoaded && !imageError ? 'loading' : ''}`} aria-hidden="true">
                {imageLoaded ? (
                    <img
                        src={articleImages[article.id]}
                        alt=""
                        style={{ display: 'block' }}
                    />
                ) : imageError ? (
                    <div
                        style={{
                            background: `linear-gradient(135deg, #${Math.floor(Math.random() * 16777215).toString(16)}, #${Math.floor(Math.random() * 16777215).toString(16)})`,
                            width: '100%',
                            height: '100%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontSize: '12px'
                        }}
                    >
                        Image
                    </div>
                ) : (
                    'Loading...'
                )}
            </div>

            <div className="body">
                <div className="title">{article.title}</div>
                <div className="excerpt">{article.excerpt}</div>

                <div className="bottom">
                    <div className="favicons" aria-label="Source sites">
                        {article.sources.slice(0, 3).map((source, idx) => (
                            <div
                                key={idx}
                                className="favicon"
                                title={source.domain}
                                aria-label={source.domain}
                            >
                                {faviconLetter(source.domain)}
                            </div>
                        ))}
                    </div>

                    <div className="bias-mini" title="Bias indicators (source tones)">
                        <span>Bias:</span>
                        <span className="dot neg" title={`Negative: ${counts.neg}`}></span>
                        <span className="dot neu" title={`Neutral: ${counts.neu}`}></span>
                        <span className="dot pos" title={`Positive: ${counts.pos}`}></span>
                    </div>

                    <div className="timestamp">{timeAgo(article.time)}</div>
                </div>
            </div>

            <div className="hoverfacts">
                <h5>Key Facts</h5>
                <ul>
                    {article.bullets.slice(0, 3).map((fact, idx) => (
                        <li key={idx}>{fact}</li>
                    ))}
                </ul>
            </div>
        </article>
    )
}

export default NewsCard
