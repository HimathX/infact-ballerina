const FeedSidebar = ({ providers }) => {
    return (
        <aside className="feed-sidebar">
            <h3 className="block-title">News Providers</h3>
            <div className="providers-list">
                {providers.map((provider, index) => (
                    <div key={index} className="provider">
                        <div className="provider-header">
                            <div className="favicon">{provider.favicon}</div>
                            <div>
                                <div className="provider-name">{provider.name}</div>
                                <div className="provider-domain">{provider.domain}</div>
                            </div>
                        </div>
                        <div className="provider-details">
                            <div className="provider-owner">Owned by {provider.owner}</div>
                            <div className="provider-type">{provider.type}</div>
                        </div>
                    </div>
                ))}
            </div>
        </aside>
    )
}

export default FeedSidebar
