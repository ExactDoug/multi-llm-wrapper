import { initializeOverflowDetection } from './modules/ui.js';
import { initializeEventListeners } from './modules/events.js';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    // Initialize overflow detection
    initializeOverflowDetection();
    
    // Initialize event listeners
    initializeEventListeners();
});