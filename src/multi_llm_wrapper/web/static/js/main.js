[Previous content up to the copyText function, which we'll replace with:]

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

[Rest of the file content remains the same]