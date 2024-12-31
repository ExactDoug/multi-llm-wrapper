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
    const section = button.closest('.llm-window, .synthesizer-section');
    const contentDiv = section.querySelector('.markdown-body');
    const textToCopy = contentDiv.textContent.trim();

    try {
        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(textToCopy);
        } else {
            // Fallback for iOS
            const textArea = document.createElement('textarea');
            textArea.value = textToCopy;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            try {
                document.execCommand('copy');
                textArea.blur();
            } catch (err) {
                console.error('Fallback: Oops, unable to copy', err);
            }

            document.body.removeChild(textArea);
        }

        // Visual feedback
        const originalText = button.textContent;
        button.textContent = '✅';
        button.style.transform = 'scale(1.2)';
        button.style.transition = 'transform 0.15s ease-in-out';

        // Add touch feedback for mobile
        button.style.opacity = '0.7';
        button.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';

        setTimeout(() => {
            button.textContent = originalText;
            button.style.transform = 'scale(1)';
            button.style.opacity = '1';
            button.style.backgroundColor = 'transparent';
        }, 1000);
    } catch (err) {
        console.error('Failed to copy: ', err);
        // Show error feedback
        const originalText = button.textContent;
        button.textContent = '❌';
        button.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.backgroundColor = 'transparent';
        }, 1000);
    }
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