// Copy button touch handlers
function addTouchHandlers() {
    document.querySelectorAll('.copy-btn').forEach(button => {
        // Remove existing handlers
        button.removeEventListener('touchend', handleTouch);
        // Add touch handler
        button.addEventListener('touchend', handleTouch, {passive: false});
    });
}

function handleTouch(e) {
    if (!this.touchMoved) {
        e.preventDefault();
        e.stopPropagation();
        
        // Call the global copyText function
        copyText(this);

        // Add animation similar to desktop
        this.style.transform = 'scale(1.2)';
        this.style.transition = 'transform 0.15s ease-in-out';
        
        setTimeout(() => {
            this.style.transform = 'scale(1)';
        }, 150);
    }
    this.touchMoved = false;
}

// Track touch movement
document.addEventListener('touchmove', () => {
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.touchMoved = true;
    });
}, {passive: true});

// Initial setup
addTouchHandlers();

// Handle dynamically added buttons
const observer = new MutationObserver(() => {
    addTouchHandlers();
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});