# Tools Directory Structure

This directory contains organized tools and utilities for the multi-llm-wrapper project.

## Directory Structure

### `/orchestration/`
Contains tools for managing Claude subprocess orchestration and test automation.

- **`configs/`** - Configuration files
  - `.mcp.json` - Project-scoped MCP server configuration
  
- **`scripts/`** - Orchestration scripts
  - `robust-sequential-orchestrator.sh` - Main test improvement orchestration script
  - `monitor-orchestrator.sh` - Real-time monitoring dashboard
  
- **`test-improvement-analysis/`** - Generated test improvement analysis reports
- **`test-improvement-logs/`** - Orchestration execution logs
- **`test-improvement-status/`** - Progress tracking files

### `/testing/`
Contains test files, debugging information, and test utilities.

- **`analysis-files/`** - Test analysis and documentation files
- **`debug/`** - Debug logs and troubleshooting files
- **`temp-files/`** - Temporary test files and utilities
- **`test_env/`** - Test environment setup

## Usage

The orchestration system is designed to analyze and improve test files across the project using Claude subprocess automation. The main orchestrator script can be run from the project root directory and will automatically use the project-scoped MCP configuration.

## Key Features

- **Parallel Test Analysis**: Processes multiple test files concurrently
- **Progress Tracking**: Real-time status monitoring and reporting
- **Resource Management**: Optimized MCP configuration to prevent log bloat
- **Comprehensive Reporting**: Detailed analysis files for each test improvement