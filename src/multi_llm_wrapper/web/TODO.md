# Multi-LLM Wrapper Web Interface TODOs

## JavaScript Refactoring

### Split main.js into Modules
Current main.js is getting large and should be split into logical modules for better maintainability and more efficient AI/LLM interactions:

```
src/multi_llm_wrapper/web/static/js/
├── modules/
│   ├── stream.js         # SSE and stream handling
│   ├── ui.js            # UI interactions (expand/collapse, etc.)
│   ├── synthesis.js     # Synthesis functionality
│   ├── markdown.js      # Markdown processing
│   └── utils.js         # Utility functions
└── main.js              # Entry point and initialization
```

Benefits:
- Reduced token usage for AI/LLM operations
- Better code organization
- Easier maintenance
- More focused updates
- Improved testing capabilities

### Implementation Plan
1. Create module structure
2. Split functionality into logical groups
3. Implement ES6 module system
4. Update build process if needed
5. Add module documentation
6. Update imports in main.js

## Future Improvements

### Performance
- [ ] Implement code-splitting for better initial load time
- [ ] Add service worker for offline capabilities
- [ ] Optimize asset loading
- [ ] Consider using Web Workers for heavy processing

### Accessibility
- [x] Add keyboard shortcuts for common actions
- [x] Improve screen reader support
- [x] Enhance focus management
- [x] Add more ARIA labels and descriptions

### UI/UX
- [ ] Add loading indicators for each LLM window
- [ ] Implement error boundaries
- [ ] Add retry mechanisms for failed requests
- [x] Improve mobile touch interactions
- [ ] Fix unordered list padding in mobile view

### Testing
- [ ] Add unit tests for JavaScript modules
- [ ] Implement E2E testing
- [ ] Add accessibility testing
- [ ] Performance testing suite

### Documentation
- [ ] Add JSDoc comments
- [ ] Create API documentation
- [ ] Add usage examples
- [ ] Document testing procedures

## Completed Improvements
- [x] Split CSS into logical modules
- [x] Implement fixed-width containers
- [x] Add horizontal scroll indicators
- [x] Improve expand/collapse animations
- [x] Add responsive design improvements
- [x] Fix accessibility issues with overlay focus
- [x] Add query expansion functionality
- [x] Include original query in synthesis
- [x] Fix numbered list padding in mobile view