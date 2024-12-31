// Initialize marked for markdown rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false
});

// Check content overflow and update UI accordingly
export function checkContentOverflow(element) {
    const hasHorizontalOverflow = element.scrollWidth > element.clientWidth;
    element.classList.toggle('has-overflow', hasHorizontalOverflow);
}

// Update content with markdown parsing
export function updateContent(element, content, expandedContent = null) {
    element.innerHTML = marked.parse(content);
    element.scrollTop = element.scrollHeight;
    checkContentOverflow(element);

    if (expandedContent) {
        expandedContent.innerHTML = marked.parse(content);
        checkContentOverflow(expandedContent);
    }
}

// Handle errors in streams
export function handleStreamError(error, contentElement, eventSource, callback) {
    console.error('Stream error:', error);
    if (contentElement) {
        contentElement.innerHTML = marked.parse(`Error: ${error.message || 'Unknown error'}`);
    }
    if (eventSource) {
        eventSource.close();
    }
    if (callback) {
        callback();
    }
}

// Parse SSE data
export function parseSSEData(data) {
    try {
        return JSON.parse(data);
    } catch (error) {
        console.error('Error parsing SSE data:', error);
        return null;
    }
}

// Create URL with parameters
export function createStreamUrl(baseUrl, params) {
    const url = new URL(baseUrl, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
    });
    return url.toString();
}