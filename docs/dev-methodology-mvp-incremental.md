# Codified Development Plan Template

## Overview
This template provides a structured, incremental approach to software development that prioritizes stability, testability, and change control.

## Core Principles
- **Incremental Development**: Small, manageable changes that build toward the final product
- **MVP-First Approach**: Deliver working, user-facing functionality as early as possible while building toward the final architecture
- **Vertical Slice Priority**: Complete full-stack features (UI through data layer) before adding feature breadth
- **Early Wins Strategy**: Structure tasks so that initial phases deliver tangible, demonstrable functionality
- **Manual Testing**: Every change is manually tested before proceeding
- **Change Control**: No breaking changes; maintain functionality at all times
- **Git Discipline**: Commit after each verified change
- **KISS Philosophy**: Keep implementations simple and straightforward
- **No Unauthorized Deviations**: Stop and discuss rather than digress from the plan

## Development Methodology

### Step-by-Step Process
Each task in the development plan follows this exact sequence:

1. **Implement Small Change**
   - Make minimal, focused modifications to the codebase
   - Target specific functionality without breaking existing features
   - Keep changes atomic and purposeful

2. **Provide Testing Instructions**
   - Stop after implementing the change
   - Provide clear, step-by-step manual testing instructions
   - Specify what to look for to verify the change works
   - Include instructions to verify no existing functionality was broken

3. **Wait for Test Results**
   - Do not proceed until manual testing is complete
   - Await confirmation of test results from the developer

4. **Verify Success**
   - Confirm intended changes were implemented correctly
   - Confirm no existing functionality was broken
   - Address any issues before proceeding

5. **Git Commit**
   - Create a descriptive commit message
   - Commit the verified changes to version control

6. **Mark Step Complete**
   - Note the step as completed in the plan
   - Update progress tracking

7. **Request Permission to Continue**
   - Ask whether to proceed with the next step
   - Wait for explicit approval before continuing

### Plan Structure Requirements

#### Task Ordering
- **Simple to Complex with Early Functional Value**: Start with foundational, low-risk changes that deliver visible, working functionality as soon as possible
- **MVP-Driven Progression**: Prioritize tasks that create a minimal but complete user-facing feature early, then incrementally enhance
- **Vertical Slice Implementation**: Build end-to-end functionality (UI → API → Database) for core features before adding breadth
- **Dependency-Aware**: Ensure prerequisites are completed first
- **Refactor-Minimizing**: Structure to avoid rework in later stages
- **Non-Breaking**: Each step maintains existing functionality

#### Task Specifications
Each task must include:
- **Objective**: Clear description of what will be implemented
- **Files to Modify**: Specific files and approximate line counts
- **Expected Outcome**: What the change should accomplish
- **User-Facing Value**: Concrete functionality the user can see/interact with (especially in early phases)
- **Testing Criteria**: How to verify the change works correctly
- **Risk Assessment**: Potential impact on existing functionality
- **Architectural Alignment**: How this task fits into the final product vision without requiring refactoring

## Template Structure

### Project Information
- **Project Name**: [Project Name]
- **Version**: [Current Version]
- **Target Version**: [Target Version]
- **Start Date**: [Date]
- **Estimated Completion**: [Date]

### Development Environment
- **Repository Path**: [Full path to project]
- **Branch**: [Working branch name]
- **Dependencies**: [Key dependencies and versions]
- **Testing Environment**: [How to run/test the project]

### Implementation Tasks

#### Phase 1: MVP Foundation - Functional Core (Low Risk, High Visible Value)
**Goal**: Establish a working end-to-end feature that demonstrates core functionality

**Task 1.1**: [Minimal Working Feature Setup]
- **Objective**: Create the simplest possible working version of the primary feature
- **Files**: [Core files needed for basic functionality]
- **Changes**: [Minimum viable implementation]
- **Testing**: [Verify the feature works end-to-end, even if basic]
- **User-Facing Value**: [What the user can actually see/do after this task]
- **Status**: [ ] Not Started / [ ] In Progress / [ ] Complete

**Task 1.2**: [Essential Infrastructure]
- **Objective**: Add only the infrastructure necessary to support the MVP feature
- **Files**: [Supporting files for the core feature]
- **Changes**: [Infrastructure that directly enables the MVP]
- **Testing**: [Verify infrastructure supports the core feature]
- **User-Facing Value**: [How this improves the working feature]
- **Status**: [ ] Not Started / [ ] In Progress / [ ] Complete

#### Phase 2: MVP Enhancement - Vertical Feature Completion (Medium Risk)
**Goal**: Complete the vertical slice of the core feature before adding new features

**Task 2.1**: [Feature Polish & Edge Cases]
- **Objective**: Make the core feature production-ready
- **Files**: [Files to enhance the existing feature]
- **Changes**: [Error handling, validation, user experience improvements]
- **Testing**: [Comprehensive testing of the complete feature]
- **User-Facing Value**: [Reliable, polished version of the core feature]
- **Status**: [ ] Not Started / [ ] In Progress / [ ] Complete

#### Phase 3: Feature Breadth - Additional Functionality (Medium-High Risk)
**Goal**: Add additional features using the proven architecture pattern

[Continue with subsequent phases...]

#### Phase N: Advanced Features & Optimization (High Risk)
**Goal**: Complex features, performance optimization, advanced use cases

[Final phase with most complex changes...]

### Risk Mitigation
- **Backup Strategy**: [How to revert if needed]
- **Testing Strategy**: [Manual testing approach]
- **Rollback Plan**: [Steps to undo changes if necessary]

### Success Criteria
- [ ] All tasks completed without breaking existing functionality
- [ ] Manual testing passes for each change
- [ ] All changes committed to version control
- [ ] Final integration testing successful

## Communication Protocol

### When to Stop and Discuss
- Better implementation approach identified
- Unexpected complexity discovered
- Risk of breaking existing functionality
- Deviation from plan seems beneficial

### Status Reporting
After each completed task, provide:
- Summary of changes made
- Testing results confirmation
- Any issues encountered and resolved
- Next step preview

## Quality Gates
- **No Broken Functionality**: Existing features must continue working
- **Tested Changes**: Every change must pass manual testing
- **Clean Commits**: Each commit represents a working, tested state
- **Documentation**: Changes must be clearly documented

---

*This codified plan serves as our standard development methodology for all projects. It ensures quality, stability, and predictable progress while maintaining change control throughout the development process.*