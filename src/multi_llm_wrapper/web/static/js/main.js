// Initialize marked for markdown rendering
marked.setOptions({
    breaks: true,
    gfm: true,
    headerIds: false
});

// Global state
let activeStreams = new Map(); // Track active SSE connections
let expandedWindow = null; // Track currently expanded window
let isInputCollapsed = false; // Track input section state
let currentSessionId = null; // Track current session ID

// DOM Elements
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const overlay = document.getElementById('overlay');
const inputSection = document.getElementById('inputSection');
const toggleInputBtn = document.getElementById('toggleInput');
const followUpBtn = document.getElementById('followUpBtn');
const expandedWindowElement = document.querySelector('.expanded-window');

// Initialize content overflow detection
function initializeOverflowDetection() {
    const contentElements = document.querySelectorAll('.llm-content, .synthesizer-content');
    contentElements.forEach(element => {
        checkContentOverflow(element);
        // Create ResizeObserver to check overflow on content changes
        const resizeObserver = new ResizeObserver(() => checkContentOverflow(element));
        resizeObserver.observe(element);
    });
}

// Check content overflow and update UI accordingly
function checkContentOverflow(element) {
    const hasHorizontalOverflow = element.scrollWidth > element.clientWidth;
    element.classList.toggle('has-overflow', hasHorizontalOverflow);
}

// Handle text input
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuery();
    }
});

sendButton.addEventListener('click', sendQuery);

// Toggle input section visibility with animation
toggleInputBtn.addEventListener('click', () => {
    toggleInput(!isInputCollapsed);
});

// Follow-up button handler
followUpBtn.addEventListener('click', () => {
    toggleInput(false);
    userInput.focus();
});

function toggleInput(collapse) {
    isInputCollapsed = collapse;
    inputSection.classList.toggle('collapsed', collapse);
    toggleInputBtn.textContent = collapse ? '▶' : '▼';
    toggleInputBtn.classList.toggle('collapsed', collapse);

    if (window.innerWidth <= 768) {
        followUpBtn.style.display = 'block';
        requestAnimationFrame(() => {
            followUpBtn.style.opacity = collapse ? '1' : '0';
            followUpBtn.style.transform = collapse ? 'translateY(0)' : 'translateY(10px)';
        });
    }
}

// Reset session state
function resetSession() {
    currentSessionId = null;
    closeAllStreams();
    clearAllResponses();
}

// Generate UUID for session ID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0,
            v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Copy text to clipboard
async function copyText(button) {
    const section = button.closest('.llm-window, .synthesizer-section');
    const contentDiv = section.querySelector('.markdown-body');
    const textToCopy = contentDiv.textContent.trim();

    try {
        await navigator.clipboard.writeText(textToCopy);
        // Store original text content
        const originalText = button.textContent;
        button.textContent = '✅';

        // Animation classes
        button.style.transform = 'scale(1.2)';
        button.style.transition = 'transform 0.15s ease-in-out';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.transform = 'scale(1)';
        }, 1000);
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
}

// Main query function
async function sendQuery() {
    const query = userInput.value.trim();
    if (!query) return;

    setLoading(true);
    resetSession();
    currentSessionId = generateUUID();

    if (window.innerWidth <= 768) {
        toggleInput(true);
    }

    try {
        for (let i = 0; i < 9; i++) {
            startStream(i, query, currentSessionId);
        }
    } catch (error) {
        console.error('Error starting streams:', error);
        setLoading(false);
    }
}

// Start SSE stream for an LLM
function startStream(llmIndex, query, sessionId) {
    const contentElement = document.querySelector(`#llm-${llmIndex} .llm-content`);
    contentElement.textContent = '';

    const url = new URL(`/stream/${llmIndex}`, window.location.origin);
    url.searchParams.append('query', query);
    url.searchParams.append('session_id', sessionId);

    const eventSource = new EventSource(url.toString());
    activeStreams.set(llmIndex, eventSource);

    let accumulatedText = '';

    const streamTimeout = setTimeout(() => {
        console.log(`[LLM ${llmIndex}] Stream timeout`);
        eventSource.close();
        activeStreams.delete(llmIndex);
        checkAllStreamsComplete();
    }, 30000);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'content' && data.content) {
                accumulatedText += data.content;
                contentElement.innerHTML = marked.parse(accumulatedText);
                contentElement.scrollTop = contentElement.scrollHeight;
                checkContentOverflow(contentElement);

                if (expandedWindow === `llm-${llmIndex}`) {
                    const expandedContent = document.querySelector('.expanded-content');
                    expandedContent.innerHTML = marked.parse(accumulatedText);
                    checkContentOverflow(expandedContent);
                }
            } else if (data.type === 'done') {
                clearTimeout(streamTimeout);
                eventSource.close();
                activeStreams.delete(llmIndex);
                checkAllStreamsComplete();
            } else if (data.type === 'error') {
                clearTimeout(streamTimeout);
                contentElement.innerHTML = marked.parse(`Error: ${data.message}`);
                eventSource.close();
                activeStreams.delete(llmIndex);
                checkAllStreamsComplete();
            }
        } catch (error) {
            clearTimeout(streamTimeout);
            console.error(`[LLM ${llmIndex}] Error:`, error);
            eventSource.close();
            activeStreams.delete(llmIndex);
            checkAllStreamsComplete();
        }
    };

    eventSource.onerror = (error) => {
        console.error(`Stream ${llmIndex} error:`, error);
        eventSource.close();
        activeStreams.delete(llmIndex);
        setLoading(false);
    };
}

// Check if all streams are complete
function checkAllStreamsComplete() {
    if (activeStreams.size === 0 && currentSessionId) {
        startSynthesis(currentSessionId);
    }
}

// Start synthesis
function startSynthesis(sessionId) {
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
            const data = JSON.parse(event.data);

            if (data.type === 'content' && data.content) {
                accumulatedText += data.content;
                synthesizerContent.innerHTML = marked.parse(accumulatedText);
                synthesizerContent.scrollTop = synthesizerContent.scrollHeight;
                checkContentOverflow(synthesizerContent);

                if (expandedWindow === 'master-synthesis') {
                    const expandedContent = document.querySelector('.expanded-content');
                    expandedContent.innerHTML = marked.parse(accumulatedText);
                    checkContentOverflow(expandedContent);
                }
            } else if (data.type === 'done') {
                eventSource.close();
                setLoading(false);
            } else if (data.type === 'error') {
                synthesizerContent.innerHTML = marked.parse(`Error: ${data.message}`);
                eventSource.close();
                setLoading(false);
            }
        } catch (error) {
            console.error('[Synthesis] Error:', error);
            eventSource.close();
            setLoading(false);
        }
    };

    eventSource.onerror = (error) => {
        console.error('Synthesis error:', error);
        eventSource.close();
        setLoading(false);
    };
}

// Expand/collapse window functions with smooth transitions
function expandWindow(windowId) {
    let contentElement, titleText;

    if (windowId === 'query-input') {
        contentElement = document.querySelector('#userInput');
        titleText = 'Query / Prompt';
    } else if (windowId === 'master-synthesis') {
        contentElement = document.querySelector('.synthesizer-content');
        titleText = 'Master Synthesis';
    } else {
        contentElement = document.querySelector(`#${windowId} .llm-content`);
        titleText = document.querySelector(`#${windowId} .llm-title`).textContent;
    }

    const expandedContent = document.querySelector('.expanded-content');
    const expandedTitle = document.querySelector('.expanded-title');
    expandedTitle.textContent = titleText;

    // Handle query input differently
    if (windowId === 'query-input') {
        expandedContent.innerHTML = `
            <div style="display: flex; flex-direction: column; height: 100%;">
                <textarea class="expanded-query" style="flex: 1; margin-bottom: 1rem;">${contentElement.value}</textarea>
                <button id="expanded-send" class="send-button" style="align-self: flex-end;">Send</button>
            </div>
        `;

        // Sync expanded textarea with original
        const expandedTextarea = expandedContent.querySelector('.expanded-query');
        expandedTextarea.addEventListener('input', () => {
            contentElement.value = expandedTextarea.value;
        });

        // Handle send button click
        const expandedSendButton = expandedContent.querySelector('#expanded-send');
        expandedSendButton.addEventListener('click', () => {
            closeExpanded();
            if (window.innerWidth <= 768) {
                toggleInput(true);
            }
            sendQuery();
        });
    } else {
        expandedContent.innerHTML = contentElement.innerHTML;
    }

    expandedWindow = windowId;
    overlay.style.display = 'flex';

    requestAnimationFrame(() => {
        overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';

        // Focus expanded textarea if it exists
        const expandedTextarea = expandedContent.querySelector('.expanded-query');
        if (expandedTextarea) {
            expandedTextarea.focus();
        }
    });
}

function closeExpanded() {
    overlay.classList.remove('visible');

    setTimeout(() => {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
        expandedWindow = null;
    }, 300);
}

// Utility functions
function setLoading(isLoading) {
    userInput.disabled = isLoading;
    sendButton.disabled = isLoading;
    sendButton.classList.toggle('loading', isLoading);
}

function closeAllStreams() {
    activeStreams.forEach(stream => stream.close());
    activeStreams.clear();
}

function clearAllResponses() {
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

// Event Listeners
overlay.addEventListener('click', (e) => {
    // Only close if clicking the dark overlay background itself
    if (e.target === overlay) {
        // Never auto-close for query input
        if (expandedWindow === 'query-input') {
            return;
        }
        // For LLM content only close via X button
        if (expandedWindow && expandedWindow.startsWith('llm-')) {
            return;
        }
        // For synthesis only close via X button
        if (expandedWindow === 'master-synthesis') {
            return;
        }
    }
});

// Ensure expanded content is scrollable on mobile
document.addEventListener('touchmove', (e) => {
    const expandedContent = document.querySelector('.expanded-content');
    if (expandedContent && expandedContent.contains(e.target)) {
        e.stopPropagation();
    }
}, { passive: false });

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && overlay.style.display === 'flex') {
        closeExpanded();
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
        followUpBtn.style.display = 'none';
        if (isInputCollapsed) {
            toggleInput(false);
        }
    }

    // Recheck content overflow on resize
    const contentElements = document.querySelectorAll('.llm-content, .synthesizer-content, .expanded-content');
    contentElements.forEach(checkContentOverflow);
});

// Initialize overflow detection on page load
document.addEventListener('DOMContentLoaded', initializeOverflowDetection);