import { useState, useRef, useEffect } from 'react'

const Expander = ({ id, title, content, preferences }) => {
    const [isExpanded, setIsExpanded] = useState(false)
    const bodyRef = useRef(null)
    const [height, setHeight] = useState(0)

    useEffect(() => {
        if (bodyRef.current) {
            setHeight(bodyRef.current.scrollHeight)
        }
    }, [content])

    const toggle = () => {
        setIsExpanded(!isExpanded)
    }

    const handleClick = () => {
        toggle()
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            toggle()
        }
    }

    return (
        <section className={`expander ${isExpanded ? 'expanded' : ''}`}>
            <div
                className="exp-head"
                tabIndex="0"
                onClick={handleClick}
                onKeyDown={handleKeyDown}
            >
                <div className="exp-title">{title}</div>
                <div className="exp-toggle">{isExpanded ? 'Collapse' : 'Expand'}</div>
            </div>
            <div
                className="exp-body"
                ref={bodyRef}
                style={{
                    height: isExpanded ? (preferences.reduceMotion ? 'auto' : `${height}px`) : '0px',
                    opacity: isExpanded ? 1 : 0
                }}
            >
                <div className="exp-body-inner">
                    <p>{content}</p>
                </div>
            </div>
        </section>
    )
}

export default Expander
