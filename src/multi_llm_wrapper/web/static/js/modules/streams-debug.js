// Streams Debugging Utilities
//
// This module provides debugging tools for stream handling and content updates.
// Enable DEBUG_MODE to see detailed console output about content structure and updates.
// Useful during development and troubleshooting of LLM windows and content streaming.

export const DEBUG_MODE = false; // Set to true to enable debug logging

export function logLLMWindowSearch(llmIndex) {
    if (!DEBUG_MODE) return;
    console.log(`Trying to find content element for LLM ${llmIndex}`);
}

export function logLLMWindowHTML(llmIndex, html) {
    if (!DEBUG_MODE) return;
    console.log(`LLM window ${llmIndex} HTML:`, html);
}

export function logContentStructure(type, found = true) {
    if (!DEBUG_MODE) return;
    const action = found ? "found" : "not found, creating";
    console.warn(`${type} div ${action}...`);
}

export function logMarkdownBody(element) {
    if (!DEBUG_MODE) return;
    console.log(`Markdown body found/created:`, element);
    if (element) {
        console.log(`Markdown body HTML:`, element.innerHTML);
    }
}

export function logStreamTimeout(llmIndex) {
    if (!DEBUG_MODE) return;
    console.log(`[LLM ${llmIndex}] Stream timeout`);
}

export function logSynthesizerSearch() {
    if (!DEBUG_MODE) return;
    console.log('Looking for synthesizer content');
}

export function logError(message) {
    // Always log errors regardless of DEBUG_MODE
    console.error(message);
}