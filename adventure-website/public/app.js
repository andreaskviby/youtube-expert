// Adventure in Sicily - Main App

// Video data will be injected during build
const VIDEOS_BY_POPULARITY = window.VIDEOS_BY_POPULARITY || [];
const VIDEOS_BY_DATE = window.VIDEOS_BY_DATE || [];
const VIDEOS = window.VIDEOS_BY_DATE || []; // Default for search
const CHANNEL = window.CHANNEL || {};

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Format number with K/M suffix
function formatNumber(num) {
    num = parseInt(num);
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
    return num.toString();
}

// Create video card HTML
function createVideoCard(video, showViews = false) {
    const slug = createSlug(video.title);
    const viewsHtml = showViews && video.views ?
        `<span class="views">${formatNumber(video.views)} views</span>` : '';

    return `
        <a href="/episodes/${slug}/" class="video-card">
            <div class="video-thumbnail">
                <img src="${video.thumbnail}" alt="${video.title}" loading="lazy">
                <div class="play-overlay"></div>
            </div>
            <div class="video-info">
                <h3>${video.title}</h3>
                <div class="video-meta">
                    ${viewsHtml}
                    <span class="date">${formatDate(video.published)}</span>
                </div>
            </div>
        </a>
    `;
}

// Create URL slug from title
function createSlug(title) {
    return title
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .substring(0, 50);
}

// Filter videos by search query
function filterVideos(query, videos = VIDEOS_BY_DATE) {
    if (!query) return videos;
    const q = query.toLowerCase();
    return videos.filter(v =>
        v.title.toLowerCase().includes(q) ||
        v.description.toLowerCase().includes(q)
    );
}

// Load POPULAR videos on homepage
function loadLatestVideos() {
    const container = document.getElementById('latest-videos');
    if (!container || !VIDEOS_BY_POPULARITY.length) return;

    // Show top 6 most popular videos
    const popularVideos = VIDEOS_BY_POPULARITY.slice(0, 6);
    container.innerHTML = popularVideos.map(v => createVideoCard(v, true)).join('');
}

// Load all videos on episodes page (sorted by date)
function loadAllVideos(query = '') {
    const container = document.getElementById('all-videos');
    if (!container || !VIDEOS_BY_DATE.length) return;

    const filtered = filterVideos(query, VIDEOS_BY_DATE);

    if (filtered.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align:center; padding: 60px 20px; background: #F5F0EB; border-radius: 12px;">
                <span style="font-size: 3rem;">🎬</span>
                <h3 style="color: #48372f; margin: 20px 0 15px;">No episodes about "${query}" yet!</h3>
                <p style="color: #666; margin-bottom: 20px;">
                    But we love making content our viewers want to see.<br>
                    Tell us what you're looking for and we might make an episode about it!
                </p>
                <a href="https://www.youtube.com/@weboughtanadventureinsicily/community"
                   target="_blank"
                   style="display: inline-block; background: #C4713B; color: white; padding: 12px 25px; border-radius: 25px; text-decoration: none; font-weight: 600;">
                    Request This Topic
                </a>
                <p style="color: #999; font-size: 0.9rem; margin-top: 20px;">
                    Or try a different search term above
                </p>
            </div>
        `;
    } else {
        container.innerHTML = filtered.map(v => createVideoCard(v, true)).join('');
    }

    // Update result count
    const countEl = document.getElementById('result-count');
    if (countEl) {
        countEl.textContent = `Showing ${filtered.length} of ${VIDEOS_BY_DATE.length} episodes`;
    }
}

// Get URL parameter
function getUrlParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param) || '';
}

// Search functionality
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const container = document.getElementById('all-videos');
    if (!searchInput || !container) return;

    // Check for URL parameter
    const urlQuery = getUrlParam('q');
    if (urlQuery) {
        searchInput.value = urlQuery;
        loadAllVideos(urlQuery);
    } else {
        loadAllVideos();
    }

    // Handle typing
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;
        loadAllVideos(query);

        // Update URL without reload
        const url = new URL(window.location);
        if (query) {
            url.searchParams.set('q', query);
        } else {
            url.searchParams.delete('q');
        }
        window.history.replaceState({}, '', url);
    });
}

// Update stats
function updateStats() {
    const subCount = document.getElementById('subscriber-count');
    const videoCount = document.getElementById('video-count');
    const viewCount = document.getElementById('view-count');

    if (CHANNEL.subscribers && subCount) {
        subCount.textContent = formatNumber(CHANNEL.subscribers);
    }
    if (CHANNEL.videoCount && videoCount) {
        videoCount.textContent = CHANNEL.videoCount;
    }
    if (CHANNEL.totalViews && viewCount) {
        viewCount.textContent = formatNumber(CHANNEL.totalViews);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadLatestVideos();
    initSearch();
    updateStats();
});
