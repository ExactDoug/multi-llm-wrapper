import { state } from './state.js';
import { elements, toggleInput } from './ui.js';
import { checkContentOverflow } from './utils.js';
import { sendQuery } from './streams.js';

// Expand window functions with smooth transitions
export function expandWindow(windowId) {
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

    state.expandedWindow = windowId;
    elements.overlay.style.display = 'flex';

    // Set the source information for proper status updates
    const expandedWindow = document.querySelector('.expanded-window');
    expandedWindow.setAttribute('data-source', windowId);

    requestAnimationFrame(() => {
        elements.overlay.classList.add('visible');
        document.body.style.overflow = 'hidden';

        // Focus expanded textarea if it exists
        const expandedTextarea = expandedContent.querySelector('.expanded-query');
        if (expandedTextarea) {
            expandedTextarea.focus();
        }
    });
}

// Close expanded window
export function closeExpanded() {
    elements.overlay.classList.remove('visible');

    setTimeout(() => {
        elements.overlay.style.display = 'none';
        document.body.style.overflow = '';
        state.expandedWindow = null;
    }, 300);
}

// Handle overlay click
export function handleOverlayClick(e) {
    // Only close if clicking the dark overlay background itself
    if (e.target === elements.overlay) {
        // Never auto-close for query input
        if (state.expandedWindow === 'query-input') {
            return;
        }
        // For LLM content only close via X button
        if (state.expandedWindow && state.expandedWindow.startsWith('llm-')) {
            return;
        }
        // For synthesis only close via X button
        if (state.expandedWindow === 'master-synthesis') {
            return;
        }
    }
}

// Ensure expanded content is scrollable on mobile
export function handleTouchMove(e) {
    const expandedContent = document.querySelector('.expanded-content');
    if (expandedContent && expandedContent.contains(e.target)) {
        e.stopPropagation();
    }
}