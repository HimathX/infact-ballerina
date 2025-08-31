const TabStrip = ({ activeTab, onTabChange }) => {
    const tabs = ['Trending', 'All', 'Blindspot', 'Local', 'International']

    return (
        <nav className="tabstrip" role="navigation" aria-label="Sections">
            <div className="tabs">
                {tabs.map(tab => (
                    <button
                        key={tab}
                        className="tab"
                        data-tab={tab}
                        aria-selected={activeTab === tab ? 'true' : 'false'}
                        onClick={() => onTabChange(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </div>
        </nav>
    )
}

export default TabStrip
