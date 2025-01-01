// Update content with markdown parsing
export function updateContent(element, content, expandedContent = null) {
    if (!element) {
        console.warn('No element provided to updateContent');
        return;
    }

    // Store raw markdown for copy functionality and update content
    element.setAttribute('data-markdown', content);
    element.innerHTML = marked.parse(content);

    // Handle expanded content if present
    if (expandedContent) {
        expandedContent.setAttribute('data-markdown', content);
        expandedContent.innerHTML = marked.parse(content);
    }

    // Get the parent container for scrolling
    const container = element.closest('.llm-content, .synthesizer-content');
    if (container) {
        container.scrollTop = container.scrollHeight;
        checkContentOverflow(container);
    }

    // Also check overflow on the element itself
    checkContentOverflow(element);
}

// Check if content overflows and add class if needed
export function checkContentOverflow(element) {
    if (!element) return;

    const hasOverflow = element.scrollHeight > element.clientHeight;
    element.classList.toggle('has-overflow', hasOverflow);
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

// Create stream URL with query parameters
export function createStreamUrl(endpoint, params) {
    const url = new URL(endpoint, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        url.searchParams.append(key, value);
    });
    return url.toString();
}

// Handle stream errors
export function handleStreamError(error, contentElement, eventSource, cleanup) {
    console.error('Stream error:', error);
    if (contentElement) {
        const errorMessage = error.message || 'An error occurred while processing your request.';
        contentElement.innerHTML = `<div class="error-message">${errorMessage}</div>`;
    }
    if (eventSource) {
        eventSource.close();
    }
    if (cleanup) {
        cleanup();
    }
}