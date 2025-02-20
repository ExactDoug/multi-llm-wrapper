# Brave Search Knowledge Aggregator Project Prompt Template

## Project Overview
This project involves the development and implementation of the Brave Search Knowledge Aggregator. The primary goal is to create a streaming-first architecture that integrates with the Brave Search API, focusing on performance, memory management, and error recovery.

## Key Documentation
- @/docs/brave-dev/action-plan.md: Outlines the tasks, status, and next steps for the project.
- @/docs/brave-dev/state-as-of-2025-02-16/project-state-overview.md: Provides a high-level status of the project, including completed and in-progress components.
- @/docs/brave-dev/state-as-of-2025-02-16/project-development-state.md: Details the current development status, blockers, and next steps.
- @/docs/brave-dev/state-as-of-2025-02-16/project-state-integration.md: Describes the integration architecture and testing infrastructure.
- @/docs/brave-dev/state-as-of-2025-02-16/project-state-technical.md: Covers the technical implementation details, including code patterns and frameworks.

## Critical Requirements
1. **Performance Targets**:
   - First Status: < 100ms
   - First Result: < 1s
   - Source Selection: < 3s
   - Memory Usage: < 10MB per request
   - Error Rate: < 1%

2. **Resource Constraints**:
   - API Rate Limit: 20 requests/second
   - Connection Timeout: 30 seconds
   - Max Results Per Query: 20

## Development Focus Areas
1. **Async Iterator Pattern**:
   - Fix initialization pattern
   - Implement proper cleanup
   - Verify resource management
   - Test error propagation

2. **Memory Management**:
   - Finalize buffer controls
   - Implement cleanup triggers
   - Verify leak prevention
   - Test resource tracking

3. **Error Recovery**:
   - Complete partial results handling
   - Implement state recovery
   - Test error propagation
   - Verify cleanup on failure

4. **Performance Validation**:
   - Response timing
   - Memory usage
   - Throughput testing
   - Resource monitoring

## Testing Infrastructure
- **Test Server**: Running on port 8001 with feature flags enabled for streaming, memory tracking, and error injection.
- **Performance Testing Framework**: Includes load testing and error injection capabilities.
- **Test Scenarios**: Covers streaming behavior, memory management, and error handling.

## Progress Tracking
- **Action Plan**: Updated as tasks are completed.
- **Progress Log**: Maintained in the action plan document.
- **Commit Messages**: Reference the action plan and relevant documentation.

## Standard Prompt for New Chats
When starting a new chat for this project, please reference this prompt template and the associated documentation to ensure all relevant context is considered. This ensures consistency and maintains focus on the project goals and requirements.

## Example Use Case
When beginning a new task or discussion, start with:
"Referring to the action plan and associated documentation, I will focus on [specific task] to ensure [specific goal] is achieved, adhering to the performance and resource constraints outlined in the project requirements."