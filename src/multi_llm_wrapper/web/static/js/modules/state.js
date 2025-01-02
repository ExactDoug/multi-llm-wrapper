import { checkContentOverflow } from './utils.js';
import { llmTitles, initializeStatusTracking } from './status.js';

// Global state management
export const state = {
    activeStreams: new Map(), // Track active SSE connections
    expandedWindow: null, // Track currently expanded window
    isInputCollapsed: false, // Track input section state
    currentSessionId: null, // Track current session ID
    llmStatus: {} // Track LLM completion status
};

export function initializeStatus() {
    state.llmStatus = initializeStatusTracking();
}

export function resetSession() {
    state.currentSessionId = null;
    closeAllStreams();
    clearAllResponses();
    initializeStatus();
}

// Close all active streams
export function closeAllStreams() {
    state.activeStreams.forEach(stream => stream.close());
    state.activeStreams.clear();
}

// Clear all response content
export function clearAllResponses() {
    for (let i = 0; i < 9; i++) {
        const contentElement = document.querySelector(`#llm-${i} .llm-content`);
        const titleElement = document.querySelector(`#llm-${i} .llm-title`);

        if (contentElement) {
            contentElement.textContent = '';
            checkContentOverflow(contentElement);
        }
        if (titleElement) {
            titleElement.textContent = llmTitles[i] || `LLM ${i + 1}`;
        }
    }

    const synthesizerContent = document.querySelector('.synthesizer-content');
    if (synthesizerContent) {
        synthesizerContent.textContent = '';
        checkContentOverflow(synthesizerContent);
    }
}

// Generate UUID for session ID
export function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}