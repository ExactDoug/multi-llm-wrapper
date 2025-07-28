import { initializeOverflowDetection } from './modules/ui.js';
import { initializeEventListeners } from './modules/events.js';
import { updateStatusDisplay } from './modules/status.js';

// Check service status and show warning if needed
async function checkServiceStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        if (!status.llm_service_available) {
            showConfigWarning(status.message);
        }
    } catch (error) {
        console.error('Failed to check service status:', error);
    }
}

function showConfigWarning(message) {
    // Create warning element if it doesn't exist
    let warning = document.getElementById('config-warning');
    if (!warning) {
        warning = document.createElement('div');
        warning.id = 'config-warning';
        warning.className = 'config-warning';
        warning.innerHTML = `
            <span class="warning-icon">⚠️</span>
            <span class="warning-text">${message}</span>
            <button class="warning-close" onclick="this.parentElement.style.display='none'">×</button>
        `;
        document.body.insertBefore(warning, document.body.firstChild);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize overflow detection
    initializeOverflowDetection();

    // Initialize event listeners
    initializeEventListeners();

    // Ensure synthesizer section is ready
    const synthesizer = document.querySelector('.synthesizer-section .synthesizer-content .markdown-body');
    if (!synthesizer) {
        console.error('Could not find synthesizer section during initialization');
    } else {
        console.log('Found synthesizer section during initialization');
    }
    
    // Check service status on page load
    checkServiceStatus();
});