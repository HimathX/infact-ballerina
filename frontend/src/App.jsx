import { useState, useEffect } from 'react'
import './infact.css'
import TopBar from './components/TopBar'
import TabStrip from './components/TabStrip'
import Feed from './components/Feed'
import ArticleView from './components/ArticleView'
import Modal from './components/Modal'

function App() {
  const [activeTab, setActiveTab] = useState('Trending')
  const [currentArticle, setCurrentArticle] = useState(null)
  const [theme, setTheme] = useState('light')
  const [showAboutModal, setShowAboutModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [preferences, setPreferences] = useState({
    reduceMotion: false,
    compact: false
  })

  // Load theme and preferences on mount
  useEffect(() => {
    // Load theme
    const savedTheme = localStorage.getItem('infact:theme')
    if (savedTheme) {
      setTheme(savedTheme)
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setTheme('dark')
    }

    // Load preferences
    try {
      const savedPrefs = JSON.parse(localStorage.getItem('infact:prefs') || '{}')
      setPreferences(prev => ({ ...prev, ...savedPrefs }))
    } catch (e) {
      // ignore
    }
  }, [])

  // Apply theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('infact:theme', theme)
  }, [theme])

  // Apply preferences
  useEffect(() => {
    document.documentElement.style.setProperty('--gutter', preferences.compact ? '16px' : '24px')
    localStorage.setItem('infact:prefs', JSON.stringify(preferences))
  }, [preferences])

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const openArticle = (articleId) => {
    setCurrentArticle(articleId)
  }

  const backToFeed = () => {
    setCurrentArticle(null)
    window.scrollTo({ top: 0, behavior: preferences.reduceMotion ? 'auto' : 'smooth' })
  }

  return (
    <div className="App">
      <TopBar
        theme={theme}
        onToggleTheme={toggleTheme}
        onShowAbout={() => setShowAboutModal(true)}
        onShowSettings={() => setShowSettingsModal(true)}
        onLogoClick={backToFeed}
      />

      <TabStrip
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      <main className="page">
        {currentArticle ? (
          <ArticleView
            articleId={currentArticle}
            onBack={backToFeed}
            preferences={preferences}
          />
        ) : (
          <Feed
            activeTab={activeTab}
            onArticleClick={openArticle}
            preferences={preferences}
          />
        )}
      </main>

      <Modal
        isOpen={showAboutModal}
        onClose={() => setShowAboutModal(false)}
        title="About Infact"
      >
        <p>Infact aggregates reporting and foregrounds verifiable facts. The interface intentionally de‑emphasizes sensational framing.</p>
        <p className="muted">Design cues: are.na's wireframe minimalism meets Swiss grid discipline. Colors are monochrome, with a restrained deep‑brown accent.</p>
      </Modal>

      <Modal
        isOpen={showSettingsModal}
        onClose={() => setShowSettingsModal(false)}
        title="Settings"
      >
        <p className="muted">These are placeholder settings.</p>
        <div style={{ display: 'grid', gap: '10px', marginTop: '12px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              checked={preferences.reduceMotion}
              onChange={(e) => setPreferences(prev => ({ ...prev, reduceMotion: e.target.checked }))}
            />
            Reduce motion
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              checked={preferences.compact}
              onChange={(e) => setPreferences(prev => ({ ...prev, compact: e.target.checked }))}
            />
            Compact layout
          </label>
        </div>
      </Modal>
    </div>
  )
}

export default App
