import { useState, useEffect } from 'react'

const TopBar = ({ theme, onToggleTheme, onShowAbout, onShowSettings, onLogoClick }) => {
    const [lastFetched, setLastFetched] = useState('')

    useEffect(() => {
        const updateFetchedTime = () => {
            const now = new Date()
            const pad = n => (n < 10 ? '0' + n : '' + n)
            const timeString = `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())} UTC`
            setLastFetched('Fetched ' + timeString)
        }

        updateFetchedTime()
    }, [])

    const SunIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="5" />
            <path d="M12,1V3" />
            <path d="M12,21v2" />
            <path d="m4.22,4.22,1.42,1.42" />
            <path d="m18.36,18.36,1.42,1.42" />
            <path d="M1,12H3" />
            <path d="M21,12h2" />
            <path d="m4.22,19.78,1.42-1.42" />
            <path d="m18.36,5.64,1.42-1.42" />
        </svg>
    )

    const InfoIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="M9,9h0a3,3,0,0,1,6,0c0,2-3,3-3,3" />
            <path d="M12,17h0" />
        </svg>
    )

    const SettingsIcon = () => (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="3" />
            <path d="M12,1V5" />
            <path d="M12,19v4" />
            <path d="m4.22,4.22,2.83,2.83" />
            <path d="m16.95,16.95,2.83,2.83" />
            <path d="M1,12H5" />
            <path d="M19,12h4" />
            <path d="m4.22,19.78,2.83-2.83" />
            <path d="m16.95,7.05,2.83-2.83" />
        </svg>
    )

    return (
        <header className="topbar" role="banner">
            <div className="brand">
                <button
                    className="plainlink"
                    aria-label="Go to feed"
                    onClick={onLogoClick}
                >
                    <span className="logo">Infact</span>
                </button>
                <span className="subtitle">de‑sensationalized news</span>
            </div>
            <div className="actions">
                <span className="time-tag" aria-live="polite">
                    {lastFetched}
                </span>
                <button
                    title="About Infact"
                    aria-label="About"
                    onClick={onShowAbout}
                >
                    <InfoIcon />
                </button>
                <button
                    title="Settings"
                    aria-label="Settings"
                    onClick={onShowSettings}
                >
                    <SettingsIcon />
                </button>
                <button
                    aria-pressed={theme === 'dark' ? 'true' : 'false'}
                    title="Toggle dark/light theme"
                    aria-label="Toggle theme"
                    onClick={onToggleTheme}
                >
                    <SunIcon />
                </button>
            </div>
        </header>
    )
}

export default TopBar
