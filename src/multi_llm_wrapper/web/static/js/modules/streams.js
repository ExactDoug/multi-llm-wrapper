import { state, resetSession, generateUUID } from './state.js';
import { setLoading, toggleInput } from './ui.js';
import { updateContent, handleStreamError, parseSSEData, createStreamUrl, checkContentOverflow } from './utils.js';

// Ensure content structure exists
function ensureContentStructure(llmWindow) {
    const llmContent = llmWindow.querySelector('.llm-content');
    if (!llmContent) {
        console.warn('llm-content div not found, creating...');
        const newContent = document.createElement('div');
        newContent.className = 'llm-content';
        llmWindow.appendChild(newContent);
    }

    let markdownBody = llmContent.querySelector('.markdown-body');
    if (!markdownBody) {
        console.warn('markdown-body div not found, creating...');
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
    console.log(`Trying to find content element for LLM ${llmIndex}`);

    // Debug the LLM window
    const llmWindow = document.querySelector(`#llm-${llmIndex}`);
    console.log(`LLM window ${llmIndex} HTML:`, llmWindow?.innerHTML);

    if (!llmWindow) {
        console.error(`LLM window ${llmIndex} not found`);
        return;
    }

    // Ensure content structure exists
    const contentElement = ensureContentStructure(llmWindow);
    console.log(`Markdown body found/created:`, contentElement);
    if (contentElement) {
        console.log(`Markdown body HTML:`, contentElement.innerHTML);
    }

    updateContent(contentElement, '');

    const url = createStreamUrl(`/stream/${llmIndex}`, {
        query,
        session_id: sessionId
    });

    const eventSource = new EventSource(url);
    state.activeStreams.set(llmIndex, eventSource);

    let accumulatedText = '';

    const streamTimeout = setTimeout(() => {
        console.log(`[LLM ${llmIndex}] Stream timeout`);
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
                checkAllStreamsComplete();
            } else if (data.type === 'error') {
                clearTimeout(streamTimeout);
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
        console.error('No session ID available for synthesis');
        setLoading(false);
        return;
    }

    console.log('Looking for synthesizer content');
    const synthesizer = document.querySelector('.synthesizer-section');
    if (!synthesizer) {
        console.error('Synthesizer section not found');
        setLoading(false);
        return;
    }

    const synthContent = synthesizer.querySelector('.synthesizer-content');
    if (!synthContent) {
        console.error('Synthesizer content not found');
        setLoading(false);
        return;
    }

    let synthesizerContent = synthContent.querySelector('.markdown-body');
    if (!synthesizerContent) {
        console.warn('Synthesizer markdown-body not found, creating...');
        synthesizerContent = document.createElement('div');
        synthesizerContent.className = 'markdown-body';
        synthContent.appendChild(synthesizerContent);
    }

    console.log('Synthesizer markdown body found/created:', synthesizerContent);
    console.log('Synthesizer markdown body HTML:', synthesizerContent.innerHTML);

    updateContent(synthesizerContent, '');

    const eventSource = new EventSource(`/synthesize/${sessionId}`);
    let accumulatedText = '';

    eventSource.onmessage = (event) => {
        try {
            const data = parseSSEData(event.data);
            if (!data) return;

            if (data.type === 'content' && data.content) {
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
    if (state.activeStreams.size === 0 && state.currentSessionId) {
        startSynthesis(state.currentSessionId);
    }
}

// Main query function
export async function sendQuery() {
    const userInput = document.getElementById('userInput');
    const query = userInput.value.trim();
    if (!query) return;

    setLoading(true);
    resetSession();
    state.currentSessionId = generateUUID();

    if (window.innerWidth <= 768) {
        toggleInput(true);
    }

    try {
        for (let i = 0; i < 9; i++) {
            startStream(i, query, state.currentSessionId);
        }
    } catch (error) {
        console.error('Error starting streams:', error);
        setLoading(false);
    }
}