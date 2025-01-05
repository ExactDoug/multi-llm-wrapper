import { state, resetSession, generateUUID } from './state.js';
import { setLoading, toggleInput } from './ui.js';
import { updateContent, handleStreamError, parseSSEData, createStreamUrl, checkContentOverflow } from './utils.js';
import { updateStatusDisplay, initializeStatusTracking } from './status.js';
import {
    logLLMWindowSearch,
    logLLMWindowHTML,
    logContentStructure,
    logMarkdownBody,
    logStreamTimeout,
    logSynthesizerSearch,
    logError
} from './streams-debug.js';

// Ensure content structure exists
function ensureContentStructure(llmWindow) {
    const llmContent = llmWindow.querySelector('.llm-content');
    if (!llmContent) {
        logContentStructure('llm-content', false);
        const newContent = document.createElement('div');
        newContent.className = 'llm-content';
        llmWindow.appendChild(newContent);
    }

    let markdownBody = llmContent.querySelector('.markdown-body');
    if (!markdownBody) {
        logContentStructure('markdown-body', false);
        markdownBody = document.createElement('div');
        markdownBody.className = 'markdown-body';
        llmContent.appendChild(markdownBody);
    }
    return markdownBody;
}

// Update LLM title
function updateLLMTitle(llmIndex, newTitle) {
    const titleElement = document.querySelector(`#llm-${llmIndex} .title-text`);
    if (titleElement) {
        titleElement.textContent = newTitle;
    }
}

// Start SSE stream for an LLM
export function startStream(llmIndex, query, sessionId) {
    logLLMWindowSearch(llmIndex);

    const llmWindow = document.querySelector(`#llm-${llmIndex}`);
    logLLMWindowHTML(llmIndex, llmWindow?.innerHTML);

    if (!llmWindow) {
        logError(`LLM window ${llmIndex} not found`);
        return;
    }

    const contentElement = ensureContentStructure(llmWindow);
    logMarkdownBody(contentElement);

    updateContent(contentElement, '');

    const url = createStreamUrl(`/stream/${llmIndex}`, {
        query,
        session_id: sessionId
    });

    const eventSource = new EventSource(url);
    state.activeStreams.set(llmIndex, eventSource);

    let accumulatedText = '';

    const streamTimeout = setTimeout(() => {
        logStreamTimeout(llmIndex);
        if (!state.llmStatus[llmIndex]) {
            state.llmStatus[llmIndex] = {
                complete: false,
                startTime: Date.now()
            };
        }
        state.llmStatus[llmIndex].complete = true;
        eventSource.close();
        state.activeStreams.delete(llmIndex);
        checkAllStreamsComplete();
    }, 30000);

    eventSource.onmessage = (event) => {
        try {
            const data = parseSSEData(event.data);
            if (!data) return;

            if (data.type === 'content' && data.content) {
                accumulatedText += data.content;
                const expandedContent = state.expandedWindow === `llm-${llmIndex}` ?
                    document.querySelector('.expanded-window > .expanded-content > .markdown-body') : null;
                updateContent(contentElement, accumulatedText, expandedContent);
            } else if (data.type === 'title') {
                updateLLMTitle(llmIndex, data.title);
            } else if (data.type === 'done') {
                clearTimeout(streamTimeout);
                eventSource.close();
                state.activeStreams.delete(llmIndex);
                if (!state.llmStatus[llmIndex]) {
                    state.llmStatus[llmIndex] = {
                        complete: false,
                        startTime: Date.now()
                    };
                }
                state.llmStatus[llmIndex].complete = true;
                checkAllStreamsComplete();
            } else if (data.type === 'error') {
                clearTimeout(streamTimeout);
                if (!state.llmStatus[llmIndex]) {
                    state.llmStatus[llmIndex] = {
                        complete: false,
                        startTime: Date.now()
                    };
                }
                state.llmStatus[llmIndex].complete = true;
                handleStreamError(
                    { message: data.message },
                    contentElement,
                    eventSource,
                    () => {
                        state.activeStreams.delete(llmIndex);
                        checkAllStreamsComplete();
                    }
                );
            }
        } catch (error) {
            clearTimeout(streamTimeout);
            if (!state.llmStatus[llmIndex]) {
                state.llmStatus[llmIndex] = {
                    complete: false,
                    startTime: Date.now()
                };
            }
            state.llmStatus[llmIndex].complete = true;
            handleStreamError(
                error,
                contentElement,
                eventSource,
                () => {
                    state.activeStreams.delete(llmIndex);
                    checkAllStreamsComplete();
                }
            );
        }
    };

    eventSource.onerror = (error) => {
        if (!state.llmStatus[llmIndex]) {
            state.llmStatus[llmIndex] = {
                complete: false,
                startTime: Date.now()
            };
        }
        state.llmStatus[llmIndex].complete = true;
        handleStreamError(
            error,
            contentElement,
            eventSource,
            () => {
                state.activeStreams.delete(llmIndex);
                setLoading(false);
            }
        );
    };
}

// Start synthesis stream
export function startSynthesis(sessionId) {
    if (!sessionId) {
        logError('No session ID available for synthesis');
        setLoading(false);
        return;
    }

    logSynthesizerSearch();
    const synthesizer = document.querySelector('.synthesizer-section');
    if (!synthesizer) {
        logError('Synthesizer section not found');
        setLoading(false);
        return;
    }

    const synthContent = synthesizer.querySelector('.synthesizer-content');
    if (!synthContent) {
        logError('Synthesizer content not found');
        setLoading(false);
        return;
    }

    let synthesizerContent = synthContent.querySelector('.markdown-body');
    if (!synthesizerContent) {
        logContentStructure('Synthesizer markdown-body', false);
        synthesizerContent = document.createElement('div');
        synthesizerContent.className = 'markdown-body';
        synthContent.appendChild(synthesizerContent);
    }

    logMarkdownBody(synthesizerContent);

    const eventSource = new EventSource(`/synthesize/${sessionId}`);
    let accumulatedText = '';

    eventSource.onmessage = (event) => {
        try {
            const data = parseSSEData(event.data);
            if (!data) return;

            if (data.type === 'content' && data.content) {
                if (!accumulatedText) {  // Only clear on first content
                    updateContent(synthesizerContent, '');
                }
                accumulatedText += data.content;
                const expandedContent = state.expandedWindow === 'master-synthesis' ?
                    document.querySelector('.expanded-window > .expanded-content > .markdown-body') : null;
                updateContent(synthesizerContent, accumulatedText, expandedContent);
            } else if (data.type === 'done') {
                eventSource.close();
                setLoading(false);
            } else if (data.type === 'error') {
                handleStreamError(
                    { message: data.message },
                    synthesizerContent,
                    eventSource,
                    () => setLoading(false)
                );
            }
        } catch (error) {
            handleStreamError(
                error,
                synthesizerContent,
                eventSource,
                () => setLoading(false)
            );
        }
    };

    eventSource.onerror = (error) => {
        handleStreamError(
            error,
            synthesizerContent,
            eventSource,
            () => setLoading(false)
        );
    };
}

// Check if all streams are complete
function checkAllStreamsComplete() {
    // Ensure all LLMs and Brave Search have a status
    for (let i = 0; i < 10; i++) {
        if (!state.llmStatus[i]) {
            state.llmStatus[i] = {
                complete: false,
                startTime: Date.now()
            };
        }
    }

    // Update status display before checking completion
    updateStatusDisplay(state.llmStatus);

    if (state.activeStreams.size === 0 && state.currentSessionId) {
        // All streams are complete, start synthesis
        startSynthesis(state.currentSessionId);
    }
}

// Main query function
export async function sendQuery() {
    const userInput = document.getElementById('userInput');
    const query = userInput.value.trim();
    if (!query) return;

    setLoading(true);
    resetSession();  // This now includes proper status reset
    state.currentSessionId = generateUUID();

    // Initialize status tracking for new query
    state.llmStatus = initializeStatusTracking();
    updateStatusDisplay(state.llmStatus);  // Show initial status

    if (window.innerWidth <= 768) {
        toggleInput(true);
    }

    try {
        for (let i = 0; i < 10; i++) {
            startStream(i, query, state.currentSessionId);
        }
    } catch (error) {
        logError(`Error starting streams: ${error}`);
        setLoading(false);
    }
}