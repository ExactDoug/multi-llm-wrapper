// File: src/multi_llm_wrapper/web/static/js/modules/status.js

export const llmTitles = {
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

export function updateStatusDisplay(statuses) {
    console.log('Updating status display:', statuses);

    const updateMarkdownBody = (element) => {
        if (!element) return;

        let statusHTML = '### Waiting for responses from:\n\n';

        Object.entries(statuses || {}).forEach(([index, status]) => {
            const icon = status?.complete ? '✓' : '⟳';
            const statusText = status?.complete ? 'Complete' : 'In Progress';
            // Add explicit line breaks after each status
            statusHTML += `${icon} ${llmTitles[index] || `LLM ${parseInt(index) + 1}`} - ${statusText}\n\n`;
        });

        statusHTML += '*Synthesis will begin once all responses are received.*\n';

        try {
            element.innerHTML = marked.parse(statusHTML);
        } catch (error) {
            console.error('Error setting status display:', error);
        }
    };

    // Update main view
    const synthesizerSection = document.querySelector('.synthesizer-section');
    if (synthesizerSection) {
        const synthesizerContent = synthesizerSection.querySelector('.synthesizer-content');
        if (synthesizerContent) {
            let markdownBody = synthesizerContent.querySelector('.markdown-body');
            if (!markdownBody) {
                markdownBody = document.createElement('div');
                markdownBody.className = 'markdown-body';
                synthesizerContent.appendChild(markdownBody);
            }
            updateMarkdownBody(markdownBody);
        }
    }

    // Ensure expanded view gets the same updates
    const expandedWindow = document.querySelector('.expanded-window');
    const expandedContent = expandedWindow?.querySelector('.expanded-content');
    if (expandedContent && expandedWindow.getAttribute('data-source') === 'master-synthesis') {
        let expandedMarkdownBody = expandedContent.querySelector('.markdown-body');
        if (!expandedMarkdownBody) {
            expandedMarkdownBody = document.createElement('div');
            expandedMarkdownBody.className = 'markdown-body';
            expandedContent.appendChild(expandedMarkdownBody);
        }
        updateMarkdownBody(expandedMarkdownBody);
    }
}

export function initializeStatusTracking() {
    const statuses = {};
    Object.keys(llmTitles).forEach(index => {
        statuses[index] = {
            complete: false,
            startTime: Date.now()
        };
    });
    return statuses;
}