import { useState } from 'react'

const SourcesList = ({ sources }) => {
    const [expandedSources, setExpandedSources] = useState(new Set())

    const faviconLetter = (domain) => {
        const d = (domain || '').replace(/^www\./, '').trim()
        return d ? d[0].toUpperCase() : '•'
    }

    const toggleSource = (index) => {
        setExpandedSources(prev => {
            const newSet = new Set(prev)
            if (newSet.has(index)) {
                newSet.delete(index)
            } else {
                newSet.add(index)
            }
            return newSet
        })
    }

    const handleSourceClick = (index) => {
        toggleSource(index)
    }

    const handleSourceKeyDown = (e, index) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            toggleSource(index)
        }
    }

    return (
        <div className="sources">
            {sources.map((source, index) => {
                const isExpanded = expandedSources.has(index)

                return (
                    <div key={index} className={`source ${isExpanded ? 'expanded' : ''}`}>
                        <div
                            className="source-head"
                            tabIndex="0"
                            onClick={() => handleSourceClick(index)}
                            onKeyDown={(e) => handleSourceKeyDown(e, index)}
                        >
                            <div className="favicon" title={source.domain} aria-label={source.domain}>
                                {faviconLetter(source.domain)}
                            </div>
                            <div className="source-title">{source.name}</div>
                            <div className="source-mute">{source.domain}</div>
                            <div className="bias-pill">
                                <span>Bias</span>
                                <span className={`dot ${source.bias}`} title={source.bias}></span>
                            </div>
                        </div>

                        <div
                            className="source-body"
                            style={{
                                height: isExpanded ? 'auto' : '0px',
                                opacity: isExpanded ? 1 : 0
                            }}
                        >
                            <p>"{source.musings}"</p>
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

export default SourcesList
