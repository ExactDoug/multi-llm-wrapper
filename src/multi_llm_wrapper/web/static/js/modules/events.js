import { elements, toggleInput, handleResize, copyText } from './ui.js';
import { sendQuery } from './streams.js';
import { expandWindow, closeExpanded, handleOverlayClick, handleTouchMove } from './window.js';
import { state } from './state.js';

// Initialize all event listeners
export function initializeEventListeners() {
    // Input events
    elements.userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery();
        }
    });

    elements.sendButton.addEventListener('click', sendQuery);

    // Toggle input events
    elements.toggleInputBtn.addEventListener('click', () => {
        toggleInput(!state.isInputCollapsed);
    });

    // Follow-up button events
    elements.followUpBtn.addEventListener('click', () => {
        toggleInput(false);
        elements.userInput.focus();
    });

    // Overlay events
    elements.overlay.addEventListener('click', handleOverlayClick);

    // Mobile touch events
    document.addEventListener('touchmove', handleTouchMove, { passive: false });

    // Keyboard events
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && elements.overlay.style.display === 'flex') {
            closeExpanded();
        }
    });

    // Window resize events
    window.addEventListener('resize', handleResize);

    // Initialize expand window buttons
    initializeExpandButtons();

    // Initialize copy buttons
    initializeCopyButtons();

    // Initialize close expanded window button
    const closeExpandedBtn = document.getElementById('close-expanded');
    if (closeExpandedBtn) {
        closeExpandedBtn.addEventListener('click', closeExpanded);
    }
}

// Initialize copy buttons
function initializeCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', () => copyText(button));
    });
}

// Initialize expand window buttons
function initializeExpandButtons() {
    // Get all expand buttons
    const expandButtons = document.querySelectorAll('.expand-btn');
    
    expandButtons.forEach(button => {
        // For buttons with data-expand attribute
        const windowId = button.getAttribute('data-expand');
        if (windowId) {
            button.addEventListener('click', () => {
                console.log('Expanding window:', windowId);
                expandWindow(windowId);
            });
            return;
        }

        // For buttons with specific IDs
        if (button.id === 'query-expand') {
            button.addEventListener('click', () => expandWindow('query-input'));
        } else if (button.id === 'synthesis-expand') {
            button.addEventListener('click', () => expandWindow('master-synthesis'));
        }
    });
}