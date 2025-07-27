#!/bin/bash
# robust-sequential-orchestrator.sh - Enhanced sequential test orchestrator with comprehensive logging

set -euo pipefail

# Configuration
CLAUDE_CMD="/home/dmortensen/.claude/local/claude --model sonnet"
WORKING_DIR="/mnt/c/dev/projects/github/multi-llm-wrapper"
LOG_DIR="./test-improvement-logs"
ANALYSIS_OUTPUT_DIR="./test-improvement-analysis"
STATUS_FILE="./test-improvement-status.json"
TIMEOUT_SECONDS=1800  # 30 minutes
MAX_RETRIES=2

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Initialize directories and files
mkdir -p "$LOG_DIR" "$ANALYSIS_OUTPUT_DIR"

# Enhanced logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "[$timestamp] [$level] $message" | tee -a "$LOG_DIR/robust-orchestrator.log"
    
    # Also log to JSON status if it's an important event
    case "$level" in
        "START"|"SUCCESS"|"FAILED"|"RETRY")
            update_status_log "$level" "$message"
            ;;
    esac
}

# JSON status logging
update_status_log() {
    local event_type="$1"
    local message="$2"
    local timestamp=$(date -Iseconds)
    
    # Create or update JSON log entry
    local json_entry=$(cat << EOF
{
  "timestamp": "$timestamp",
  "event": "$event_type",
  "message": "$message"
}
EOF
    )
    
    # Append to JSON log file
    echo "$json_entry" >> "$LOG_DIR/status-events.jsonl"
}

# Enhanced process cleanup
cleanup_stale_processes() {
    log "INFO" "Checking for stale processes..."
    
    # Kill any existing orchestrator processes
    if pgrep -f "sequential-test-orchestrator" > /dev/null; then
        log "WARN" "Killing existing orchestrator processes"
        pkill -f "sequential-test-orchestrator" || true
    fi
    
    # Kill stale Claude processes
    if pgrep -f "claude.*sonnet" > /dev/null; then
        log "WARN" "Killing stale Claude processes"
        pkill -f "claude.*sonnet" || true
    fi
    
    sleep 2
}

# Pre-execution validation
validate_environment() {
    log "INFO" "Running pre-flight environment validation..."
    
    if /home/dmortensen/check-environment.sh > "$LOG_DIR/environment-check.log" 2>&1; then
        log "SUCCESS" "Environment validation passed"
    else
        local exit_code=$?
        log "ERROR" "Environment validation failed (exit code: $exit_code)"
        log "ERROR" "Check $LOG_DIR/environment-check.log for details"
        
        if [ $exit_code -eq 2 ]; then
            log "ERROR" "Critical environment issues detected. Aborting."
            exit 1
        else
            log "WARN" "Environment warnings detected. Proceeding with caution."
        fi
    fi
}

# Enhanced subprocess execution with comprehensive logging
execute_claude_analysis() {
    local test_name="$1"
    local test_file="$2"
    local rag_analysis="$3"
    local output_file="$4"
    local attempt="$5"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local debug_log="$LOG_DIR/debug_${test_name}_${timestamp}.log"
    local subprocess_log="$LOG_DIR/subprocess_${test_name}_${timestamp}.log" 
    local prompt_file="$LOG_DIR/prompt_${test_name}_${timestamp}.txt"
    
    # Create comprehensive prompt
    cat > "$prompt_file" << EOF
# Test Improvement Analysis: $test_name

You are conducting a systematic 11-step test improvement analysis for the test file: $test_file

## Your Task
Perform comprehensive analysis following this exact 11-step process:

### Step 1: Execute Existing Test
- Run the current test and document its pass/fail status
- Capture any error messages, warnings, or output
- Note execution time and resource usage
- Document current test behavior and reliability

### Step 2: Document Test Results  
- Provide detailed analysis of test execution results
- Document any issues found during execution
- Note dependencies, requirements, or setup needed
- Assess current test stability and consistency

### Step 3: Compare with RAG Analysis
- Read and analyze the corresponding RAG research file: $rag_analysis
- Compare current test state with RAG analysis findings
- Identify alignment or discrepancies between current state and analysis
- Note which RAG recommendations are already implemented vs. missing

### Step 4: Determine Improvement Scope
- Based on RAG analysis, determine what needs improvement:
  - Test code modifications needed
  - Source code modifications needed  
  - Both test and source code changes
- Provide clear rationale for the scope determination

### Step 5: Explain Rationale
- Provide detailed explanation for why changes are needed
- Reference specific issues identified in steps 1-3
- Connect recommendations to business value and quality improvements
- Prioritize changes based on impact and effort

### Step 6: Plan Test Modifications (if needed)
- Detail specific test changes required
- Assign complexity level: Low/Medium/High
- Estimate implementation effort in hours
- Assess likelihood of new issues or unexpected problems
- Provide specific code examples of improvements needed

### Step 7: Plan Code Modifications (if needed)  
- Detail specific source code changes required
- Assign complexity level: Low/Medium/High
- Estimate implementation effort in hours
- Assess likelihood of new issues or unexpected problems
- Identify potential breaking changes or compatibility issues

### Step 8: Assess Cross-Test Impact
- Review other tests that might be affected by proposed code changes
- Identify tests that may need updates due to code modifications
- Map dependencies and potential ripple effects
- Recommend coordination strategy for related changes

### Step 9: Generate Implementation Plan
- Create step-by-step implementation roadmap
- Define testing and validation approach
- Specify rollback strategy if needed
- Include quality gates and checkpoints

### Step 10: Create Risk Mitigation Strategy
- Identify potential risks in implementation
- Provide specific mitigation strategies for each risk
- Define early warning indicators
- Plan contingency approaches

### Step 11: Document Comprehensive Findings
- Summarize all analysis in structured format
- Provide executive summary of recommendations
- Include effort estimates and timeline
- Create actionable next steps with owners

## Output Format
Provide your analysis in structured markdown format with clear sections for each step. Include specific code examples, effort estimates, and actionable recommendations.

## Context Files
- Test file location: $test_file
- RAG analysis location: $rag_analysis
- Working directory: $WORKING_DIR

## Quality Expectations
IMPORTANT: This analysis must be comprehensive and detailed. Write AT LEAST 800 words with specific technical details, code examples, metrics, and actionable recommendations. Do not provide a brief summary - provide a thorough technical analysis covering all 11 steps in detail.

## Critical Output Instructions
YOU MUST OUTPUT THE COMPLETE ANALYSIS DIRECTLY TO STDOUT. Do not provide meta-summaries, completion confirmations, or executive summaries claiming you completed the work. Output the actual detailed 11-step analysis content starting with "# Test Improvement Analysis: [test_name]" and including all sections through Step 11.

Begin your comprehensive 11-step analysis now and output it directly:
EOF
    
    log "INFO" "Starting Claude analysis for $test_name (attempt $attempt)"
    log "INFO" "Prompt file: $prompt_file"
    log "INFO" "Debug log: $debug_log"
    log "INFO" "Subprocess log: $subprocess_log"
    log "INFO" "Output file: $output_file"
    
    # Record process start
    local start_time=$(date +%s)
    local claude_pid=""
    
    # Execute with simplified redirection - direct output to file, errors to debug log
    # Removed timeout command as it was causing hanging issues
    $CLAUDE_CMD \
        --dangerously-skip-permissions \
        --print -- "$(cat "$prompt_file")" \
        > "$output_file" 2> "$debug_log" &
    
    claude_pid=$!
    log "INFO" "Claude subprocess started with PID: $claude_pid"
    
    # Monitor the process
    local exit_code=0
    if wait $claude_pid; then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "Claude subprocess completed (PID: $claude_pid, exit code: $exit_code, duration: ${duration}s)"
    
    # Analyze results
    if [ $exit_code -eq 0 ]; then
        local word_count=$(wc -w < "$output_file" 2>/dev/null || echo 0)
        local line_count=$(wc -l < "$output_file" 2>/dev/null || echo 0)
        
        if [ "$word_count" -gt 500 ] && [ "$line_count" -gt 10 ]; then
            log "SUCCESS" "Analysis completed successfully for $test_name (${word_count} words, ${line_count} lines, ${duration}s)"
            return 0
        else
            log "WARN" "Analysis may be incomplete for $test_name (${word_count} words, ${line_count} lines)"
            
            # Create specific backup based on failure type
            local timestamp=$(date +%Y%m%d_%H%M%S)
            local backup_file=""
            
            if [ "$word_count" -eq 0 ]; then
                # Empty output file
                backup_file="${output_file%.md}_empty_output_${timestamp}.md"
                log "ERROR" "Empty output detected for $test_name - creating backup"
            elif grep -q "Execution error" "$output_file" 2>/dev/null; then
                # Execution error content
                backup_file="${output_file%.md}_execution_error_${timestamp}.md"
                log "ERROR" "Execution error detected in $test_name output"
            elif grep -q "EBADF" "$debug_log" 2>/dev/null; then
                # File descriptor error
                backup_file="${output_file%.md}_ebadf_error_${timestamp}.md"
                log "ERROR" "EBADF error detected in $test_name - file descriptor issue"
            elif grep -q "timeout" "$debug_log" 2>/dev/null; then
                # Timeout in debug log
                backup_file="${output_file%.md}_timeout_error_${timestamp}.md"
                log "ERROR" "Timeout occurred for $test_name"
            else
                # Generic incomplete analysis
                backup_file="${output_file%.md}_incomplete_analysis_${timestamp}.md"
                log "ERROR" "Incomplete analysis for $test_name"
            fi
            
            # Create the backup if output file exists
            if [ -f "$output_file" ] && [ -n "$backup_file" ]; then
                cp "$output_file" "$backup_file"
                log "INFO" "Created failure backup: $backup_file"
            fi
            
            return 1
        fi
    elif [ $exit_code -eq 124 ]; then
        log "ERROR" "Analysis timed out for $test_name after ${TIMEOUT_SECONDS}s"
        # Create timeout backup
        if [ -f "$output_file" ]; then
            local backup_file="${output_file%.md}_timeout_$(date +%Y%m%d_%H%M%S).md"
            cp "$output_file" "$backup_file"
            log "INFO" "Created timeout backup: $backup_file"
        fi
        return 2
    else
        log "ERROR" "Analysis failed for $test_name (exit code: $exit_code)"
        # Create general failure backup
        if [ -f "$output_file" ]; then
            local backup_file="${output_file%.md}_failed_exit${exit_code}_$(date +%Y%m%d_%H%M%S).md"
            cp "$output_file" "$backup_file"
            log "INFO" "Created failure backup: $backup_file"
        fi
        return 1
    fi
}

# Process individual test with retry logic
process_test_with_retry() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .py | sed 's/^test_//')
    local output_file="$ANALYSIS_OUTPUT_DIR/${test_name}_improvement_analysis.md"
    
    log "START" "Processing test: $test_name"
    
    # Find RAG analysis
    local rag_analysis=$(find tests/documentation/rag-research -name "*${test_name}*_rag_analysis.md" | head -1)
    
    if [ -z "$rag_analysis" ] || [ ! -f "$rag_analysis" ]; then
        log "ERROR" "No RAG analysis found for $test_name"
        return 1
    fi
    
    log "INFO" "Found RAG analysis: $rag_analysis"
    
    # Check if already completed
    if [ -f "$output_file" ] && [ -s "$output_file" ]; then
        local word_count=$(wc -w < "$output_file" 2>/dev/null || echo 0)
        if [ "$word_count" -gt 500 ]; then
            log "SUCCESS" "$test_name already completed (${word_count} words)"
            return 0
        else
            log "WARN" "Existing analysis incomplete for $test_name (${word_count} words) - will retry"
            # Preserve the incomplete attempt instead of deleting it
            local backup_file="${output_file%.md}_incomplete_$(date +%Y%m%d_%H%M%S).md"
            mv "$output_file" "$backup_file"
            log "INFO" "Preserved incomplete attempt as: $backup_file"
        fi
    fi
    
    # Attempt analysis with retries
    for attempt in $(seq 1 $MAX_RETRIES); do
        log "INFO" "Attempt $attempt/$MAX_RETRIES for $test_name"
        
        if execute_claude_analysis "$test_name" "$test_file" "$rag_analysis" "$output_file" "$attempt"; then
            log "SUCCESS" "Successfully completed $test_name on attempt $attempt"
            return 0
        else
            local result=$?
            if [ $attempt -lt $MAX_RETRIES ]; then
                # Backup the failed attempt before retrying
                if [ -f "$output_file" ] && [ -s "$output_file" ]; then
                    local backup_file="${output_file%.md}_failed_attempt${attempt}_$(date +%Y%m%d_%H%M%S).md"
                    cp "$output_file" "$backup_file"
                    log "INFO" "Backed up failed attempt $attempt as: $backup_file"
                fi
                log "RETRY" "Analysis failed for $test_name on attempt $attempt, retrying..."
                sleep 5
            else
                # Backup the final failed attempt
                if [ -f "$output_file" ] && [ -s "$output_file" ]; then
                    local backup_file="${output_file%.md}_failed_final_$(date +%Y%m%d_%H%M%S).md"
                    cp "$output_file" "$backup_file"
                    log "INFO" "Backed up final failed attempt as: $backup_file"
                fi
                log "FAILED" "Analysis failed for $test_name after $MAX_RETRIES attempts"
                return $result
            fi
        fi
    done
}

# Main orchestration function
main() {
    log "INFO" "=== Starting Robust Sequential Test Orchestration ==="
    log "INFO" "Timestamp: $(date)"
    log "INFO" "Timeout per analysis: ${TIMEOUT_SECONDS}s"
    log "INFO" "Max retries per test: $MAX_RETRIES"
    
    # Change to working directory
    cd "$WORKING_DIR" || {
        log "FAILED" "Cannot change to working directory: $WORKING_DIR"
        exit 1
    }
    
    # Verify project-scoped MCP config exists
    if [ ! -f ".mcp.json" ]; then
        log "WARNING" "No .mcp.json found in project directory - using global MCP servers"
    else
        log "INFO" "Using project-scoped MCP configuration from .mcp.json"
    fi
    
    # Clean up any stale processes
    cleanup_stale_processes
    
    # Validate environment
    validate_environment
    
    # Get all test files using safe array population
    local test_files=()
    mapfile -t test_files < <(find tests -name "test_*.py" -type f | sort)
    local total=${#test_files[@]}
    
    log "INFO" "Found $total test files to analyze"
    
    # Debug: Show first few test files
    log "INFO" "First few test files:"
    for i in {0..2}; do
        if [ $i -lt $total ]; then
            log "INFO" "  [$i] ${test_files[$i]}"
        fi
    done
    
    # Initialize counters
    local completed=0
    local skipped=0
    local failed=0
    
    log "INFO" "Starting test processing loop..."
    
    # Process each test
    for test_file in "${test_files[@]}"; do
        local test_name=$(basename "$test_file" .py | sed 's/^test_//')
        
        completed=$((completed + 1))
        log "INFO" "${BLUE}=== Processing test $completed/$total: $test_name ===${NC}"
        
        if process_test_with_retry "$test_file"; then
            log "SUCCESS" "✓ Completed $test_name"
        else
            local result=$?
            if [ $result -eq 1 ]; then
                skipped=$((skipped + 1))
                log "WARN" "⚠ Skipped $test_name"
            else
                failed=$((failed + 1))
                log "ERROR" "✗ Failed $test_name"
            fi
        fi
        
        # Brief pause between tests
        sleep 2
    done
    
    # Final summary
    local successful=$((total - skipped - failed))
    log "INFO" "=== Orchestration Complete ==="
    log "INFO" "Total tests: $total"
    log "INFO" "Successful: $successful"
    log "INFO" "Skipped: $skipped" 
    log "INFO" "Failed: $failed"
    log "INFO" "Analysis files: $ANALYSIS_OUTPUT_DIR"
    log "INFO" "Logs directory: $LOG_DIR"
    
    if [ $failed -eq 0 ]; then
        log "SUCCESS" "All tests processed successfully!"
        exit 0
    else
        log "WARN" "$failed tests failed - check logs for details"
        exit 1
    fi
}

# Handle signals gracefully
trap 'log "WARN" "Orchestration interrupted"; cleanup_stale_processes; exit 130' INT TERM

# Run main function
main "$@"