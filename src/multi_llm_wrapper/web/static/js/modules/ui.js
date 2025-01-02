import { state } from './state.js';
import { checkContentOverflow } from './utils.js';

// DOM Elements
export const elements = {
    userInput: document.getElementById('userInput'),
    sendButton: document.getElementById('sendButton'),
    overlay: document.getElementById('overlay'),
    inputSection: document.getElementById('inputSection'),
    toggleInputBtn: document.getElementById('toggleInput'),
    followUpBtn: document.getElementById('followUpBtn'),
    expandedWindowElement: document.querySelector('.expanded-window')
};

// Toggle input section visibility with animation
export function toggleInput(collapse) {
    state.isInputCollapsed = collapse;
    elements.inputSection.classList.toggle('collapsed', collapse);
    elements.toggleInputBtn.textContent = collapse ? '▶' : '▼';
    elements.toggleInputBtn.classList.toggle('collapsed', collapse);

    if (window.innerWidth <= 768) {
        elements.followUpBtn.style.display = 'block';
        requestAnimationFrame(() => {
            elements.followUpBtn.style.opacity = collapse ? '1' : '0';
            elements.followUpBtn.style.transform = collapse ? 'translateY(0)' : 'translateY(10px)';
        });
    }
}

// Copy text to clipboard with mobile support
export async function copyText(button) {
    // Find the closest container first
    const container = button.closest('.llm-window, .synthesizer-section');
    if (!container) {
        console.error('No container found for copy button');
        return;
    }

    // Find the markdown-body element
    const markdownBody = container.querySelector('.markdown-body');
    if (!markdownBody) {
        console.error('No markdown-body found in container');
        return;
    }

    // Get the content, preferring the stored markdown
    const textToCopy = markdownBody.getAttribute('data-markdown') || markdownBody.textContent.trim();
    if (!textToCopy) {
        console.error('No content found to copy');
        return;
    }

    try {
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(textToCopy);
            showCopyFeedback(button, true);
        } else {
            // Fallback for iOS
            const textArea = document.createElement('textarea');
            textArea.value = textToCopy;

            // Make the textarea invisible
            Object.assign(textArea.style, {
                position: 'fixed',
                left: '-999999px',
                top: '-999999px'
            });

            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                document.execCommand('copy');
                textArea.blur();
                showCopyFeedback(button, true);
            } catch (err) {
                console.error('Fallback: Copy failed', err);
                showCopyFeedback(button, false);
            } finally {
                document.body.removeChild(textArea);
            }
        }
    } catch (err) {
        console.error('Copy failed:', err);
        showCopyFeedback(button, false);
    }
}

// Helper function for copy feedback
function showCopyFeedback(button, success) {
    const originalText = button.textContent;
    const originalBg = button.style.backgroundColor;

    // Update button appearance
    button.textContent = success ? '✅' : '❌';
    button.style.transform = 'scale(1.2)';
    button.style.transition = 'transform 0.15s ease-in-out';
    button.style.backgroundColor = success ?
        'rgba(0, 255, 0, 0.1)' :
        'rgba(255, 0, 0, 0.1)';

    // Reset after animation
    setTimeout(() => {
        button.textContent = originalText;
        button.style.transform = 'scale(1)';
        button.style.backgroundColor = originalBg;
    }, 1000);
}

// Set loading state
export function setLoading(isLoading) {
    elements.userInput.disabled = isLoading;
    elements.sendButton.disabled = isLoading;
    elements.sendButton.classList.toggle('loading', isLoading);
}

// Initialize content overflow detection
export function initializeOverflowDetection() {
    const contentElements = document.querySelectorAll('.llm-content, .synthesizer-content');
    contentElements.forEach(element => {
        checkContentOverflow(element);
        // Create ResizeObserver to check overflow on content changes
        const resizeObserver = new ResizeObserver(() => checkContentOverflow(element));
        resizeObserver.observe(element);
    });
}

// Handle window resize
export function handleResize() {
    if (window.innerWidth > 768) {
        elements.followUpBtn.style.display = 'none';
        if (state.isInputCollapsed) {
            toggleInput(false);
        }
    }

    // Recheck content overflow on resize
    const contentElements = document.querySelectorAll('.llm-content, .synthesizer-content, .expanded-content');
    contentElements.forEach(checkContentOverflow);
}