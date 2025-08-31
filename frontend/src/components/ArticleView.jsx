import { useState } from 'react'
import { articles } from '../data'
import Expander from './Expander'
import SourcesList from './SourcesList'

const ArticleView = ({ articleId, onBack, preferences }) => {
    const article = articles.find(a => a.id === articleId)

    if (!article) {
        return <div>Article not found</div>
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
                            {article.bullets.map((bullet, index) => (
                                <li key={index}>{bullet}</li>
                            ))}
                        </ul>
                    </div>

                    <div className="article-content">
                        {article.content.map((paragraph, index) => (
                            <p key={index}>{paragraph}</p>
                        ))}
                    </div>

                    <div className="coverage">
                        Coverage Completeness: {article.coverage}
                    </div>
                </article>

                <aside className="sidebar">
                    <Expander
                        id="context"
                        title="Context"
                        content={article.context}
                        preferences={preferences}
                    />

                    <Expander
                        id="background"
                        title="Background"
                        content={article.background}
                        preferences={preferences}
                    />

                    <h4 className="block-title">Original Sources</h4>
                    <SourcesList sources={article.sources} />
                </aside>
            </div>
        </section>
    )
}

export default ArticleView
