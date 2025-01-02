import { initializeOverflowDetection } from './modules/ui.js';
import { initializeEventListeners } from './modules/events.js';
import { updateStatusDisplay } from './modules/status.js';

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
});