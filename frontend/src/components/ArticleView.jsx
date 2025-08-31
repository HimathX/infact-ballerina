import { useState, useEffect } from 'react'
import { fetchArticleById } from '../utils'
import Expander from './Expander'
import SourcesList from './SourcesList'

const ArticleView = ({ articleId, onBack, preferences }) => {
    const [article, setArticle] = useState(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const loadArticle = async () => {
            setLoading(true)
            try {
                const fetchedArticle = await fetchArticleById(articleId)
                setArticle(fetchedArticle)
            } catch (error) {
                console.error('Error loading article:', error)
            }
            setLoading(false)
        }

        if (articleId) {
            loadArticle()
        }
    }, [articleId])

    if (loading) {
        return (
            <div style={{
                padding: '60px 24px',
                textAlign: 'center',
                color: 'var(--muted)',
                fontSize: '14px'
            }}>
                Loading article...
            </div>
        )
    }

    if (!article) {
        return (
            <div style={{
                padding: '60px 24px',
                textAlign: 'center',
                color: 'var(--muted)',
                fontSize: '14px'
            }}>
                Article not found
            </div>
        )
    }

    return (
        <section className="article-view" style={{ display: 'block' }} aria-label="Article view">
            <div className="backrow">
                <button className="backlink" onClick={onBack}>← Back</button>
                <span className="muted">Reading</span>
            </div>

            <div className="article-grid">
                <article className="main">
                    <h1 className="article-title">{article.title}</h1>

                    <div className="keyfacts">
                        <h3>Key Facts</h3>
                        <ul>
                            {(article.bullets || article.key_points || []).map((bullet, index) => (
                                <li key={index}>{bullet}</li>
                            ))}
                        </ul>
                    </div>

                    {article.content && (
                        <div className="article-content">
                            {Array.isArray(article.content) ? (
                                article.content.map((paragraph, index) => (
                                    <p key={index}>{paragraph}</p>
                                ))
                            ) : (
                                <div dangerouslySetInnerHTML={{ __html: article.content.replace(/\n/g, '<br/>') }} />
                            )}
                        </div>
                    )}

                    {article.url && (
                        <div className="original-source">
                            <h4>Original Article</h4>
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                                {article.url}
                            </a>
                        </div>
                    )}

                    {article.article_urls && article.article_urls.length > 0 && (
                        <div className="cluster-sources">
                            <h4>Source Articles ({article.articles_count || article.article_urls.length})</h4>
                            <ul>
                                {article.article_urls.slice(0, 10).map((url, index) => (
                                    <li key={index}>
                                        <a href={url} target="_blank" rel="noopener noreferrer">
                                            {url.length > 80 ? url.substring(0, 80) + '...' : url}
                                        </a>
                                    </li>
                                ))}
                                {article.article_urls.length > 10 && (
                                    <li>... and {article.article_urls.length - 10} more articles</li>
                                )}
                            </ul>
                        </div>
                    )}

                    <div className="coverage">
                        Coverage Completeness: {article.coverage || 'Unknown'}
                    </div>
                </article>

                <aside className="sidebar">
                    <Expander
                        id="context"
                        title="Context"
                        content={article.context || ''}
                        preferences={preferences}
                    />

                    <Expander
                        id="background"
                        title="Background"
                        content={article.background || ''}
                        preferences={preferences}
                    />

                    <h4 className="block-title">Original Sources</h4>
                    <SourcesList sources={article.sources || []} />

                    {article.source_counts && Object.keys(article.source_counts).length > 0 && (
                        <div className="source-stats">
                            <h4 className="block-title">Source Distribution</h4>
                            {Object.entries(article.source_counts).map(([source, count]) => (
                                <div key={source} style={{ marginBottom: '4px', fontSize: '12px' }}>
                                    <strong>{source}:</strong> {count} article{count !== 1 ? 's' : ''}
                                </div>
                            ))}
                        </div>
                    )}
                </aside>
            </div>
        </section>
    )
}

export default ArticleView