// Utility functions for the Infact app

export function timeAgo(iso) {
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

export function faviconLetter(domain) {
    const d = (domain || '').replace(/^www\./, '').trim()
    return d ? d[0].toUpperCase() : '•'
}

export function loadImage(src) {
    return new Promise((resolve, reject) => {
        const img = new Image()
        img.onload = () => resolve(img)
        img.onerror = reject
        img.src = src
    })
}

export function formatFetchedTime() {
    const now = new Date()
    const pad = n => (n < 10 ? '0' + n : '' + n)
    return `${now.getUTCFullYear()}-${pad(now.getUTCMonth() + 1)}-${pad(now.getUTCDate())} ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())} UTC`
}
