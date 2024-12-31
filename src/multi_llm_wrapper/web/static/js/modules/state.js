import { checkContentOverflow } from './utils.js';

// Global state management
export const state = {
    activeStreams: new Map(), // Track active SSE connections
    expandedWindow: null, // Track currently expanded window
    isInputCollapsed: false, // Track input section state
    currentSessionId: null // Track current session ID
};

// Reset session state
export function resetSession() {
    state.currentSessionId = null;
    closeAllStreams();
    clearAllResponses();
}

// Close all active streams
export function closeAllStreams() {
    state.activeStreams.forEach(stream => stream.close());
    state.activeStreams.clear();
}

// Clear all response content
export function clearAllResponses() {
    const llmTitles = {
        0: 'Claude 3 Opus',
        1: 'Claude 3 Sonnet',
        2: 'GPT-4',
        3: 'GPT-3.5 Turbo',
        4: 'Groq Mixtral',
        5: 'Groq LLaMA 3',
        6: 'Perplexity Sonar Small',
        7: 'Perplexity Sonar Large',
        8: 'Google Gemini 1.5 Flash'
    };

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