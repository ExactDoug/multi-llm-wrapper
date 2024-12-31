import { state, resetSession, generateUUID } from './state.js';
import { setLoading, toggleInput } from './ui.js';
import { updateContent, handleStreamError, parseSSEData, createStreamUrl, checkContentOverflow } from './utils.js';

// Start SSE stream for an LLM
export function startStream(llmIndex, query, sessionId) {
    const contentElement = document.querySelector(`#llm-${llmIndex} .llm-content`);
    contentElement.textContent = '';

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
                    document.querySelector('.expanded-content') : null;
                updateContent(contentElement, accumulatedText, expandedContent);
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

    const synthesizerContent = document.querySelector('.synthesizer-content');
    synthesizerContent.textContent = '';

    const eventSource = new EventSource(`/synthesize/${sessionId}`);
    let accumulatedText = '';

    eventSource.onmessage = (event) => {
        try {
            const data = parseSSEData(event.data);
            if (!data) return;

            if (data.type === 'content' && data.content) {
                accumulatedText += data.content;
                const expandedContent = state.expandedWindow === 'master-synthesis' ?
                    document.querySelector('.expanded-content') : null;
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