#!/bin/bash
# monitor-orchestrator.sh - Real-time monitoring dashboard for test orchestration

set -euo pipefail

# Configuration
WORKING_DIR="/mnt/c/dev/projects/github/multi-llm-wrapper"
LOG_DIR="$WORKING_DIR/test-improvement-logs"
ANALYSIS_DIR="$WORKING_DIR/test-improvement-analysis"

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Function to get orchestrator status
get_orchestrator_status() {
    local pids=$(pgrep -f "robust-sequential-orchestrator" 2>/dev/null || echo "")
    if [ -n "$pids" ]; then
        echo "RUNNING (PIDs: $pids)"
    else
        echo "NOT RUNNING"
    fi
}

# Function to get Claude subprocess status
get_claude_status() {
    # Find orchestrator processes first, then look for their Claude children
    local orchestrator_pids=$(pgrep -f "robust-sequential-orchestrator" 2>/dev/null || echo "")
    local claude_pids=""
    
    # For each orchestrator, find its Claude children
    for orch_pid in $orchestrator_pids; do
        if [ -n "$orch_pid" ]; then
            # Get children of this orchestrator and filter for Claude processes
            local children=$(ps --ppid $orch_pid -o pid=,comm= 2>/dev/null | grep claude | awk '{print $1}' | tr '\n' ' ')
            claude_pids="$claude_pids $children"
        fi
    done
    
    # Clean up extra spaces and check if we found any Claude processes
    claude_pids=$(echo $claude_pids | tr -s ' ' | sed 's/^ *//;s/ *$//')
    
    if [ -n "$claude_pids" ]; then
        echo "ACTIVE (PIDs: $claude_pids)"
    else
        echo "IDLE"
    fi
}

# Function to check if file is a backup file
is_backup_file() {
    local filename="$1"
    local basename=$(basename "$filename")
    
    # Check for all backup patterns with precise timestamp regex
    # Pattern: YYYYMMDD_HHMMSS (8 digits + underscore + 6 digits)
    if [[ "$basename" =~ _incomplete_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _failed_attempt[0-9]+_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _failed_final_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _empty_output_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _execution_error_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _ebadf_error_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _timeout_error_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _incomplete_analysis_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _timeout_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ _failed_exit[0-9]+_[0-9]{8}_[0-9]{6}\.md$ ]] || \
       [[ "$basename" =~ -ETP-WS-04-HVDev\.md$ ]]; then
        return 0  # Is a backup file
    fi
    return 1  # Not a backup file
}

# Function to get progress statistics
get_progress_stats() {
    cd "$WORKING_DIR"
    local total_tests=$(find tests -name "test_*.py" -type f | wc -l)
    local completed_analyses=0
    local failed_analyses=0
    local backup_count=0
    
    if [ -d "$ANALYSIS_DIR" ]; then
        # Enable nullglob to handle missing files gracefully
        shopt -s nullglob
        
        # Count completed analyses (files > 500 words), excluding backup files
        for file in "$ANALYSIS_DIR"/*.md; do
            if [[ -f "$file" ]]; then
                # Skip backup files
                if is_backup_file "$file"; then
                    backup_count=$((backup_count + 1))
                    continue
                fi
                
                local words
                if words=$(wc -w < "$file" 2>/dev/null); then
                    # Sanitize the wc output (remove any non-digit characters)
                    words="${words//[^0-9]/}"
                    words="${words:-0}"  # Default to 0 if empty
                    
                    if [[ "$words" -gt 500 ]]; then
                        completed_analyses=$((completed_analyses + 1))
                    elif [[ "$words" -gt 0 ]]; then
                        failed_analyses=$((failed_analyses + 1))
                    fi
                else
                    # Handle wc failure - treat as failed analysis
                    failed_analyses=$((failed_analyses + 1))
                fi
            fi
        done
        
        # Disable nullglob
        shopt -u nullglob
    fi
    
    echo "$completed_analyses $failed_analyses $total_tests $backup_count"
}

# Function to get current analysis info
get_current_analysis() {
    if [ -f "$LOG_DIR/robust-orchestrator.log" ]; then
        local current_test=$(tail -20 "$LOG_DIR/robust-orchestrator.log" | grep "Processing test" | tail -1 | sed 's/.*Processing test [0-9]*\/[0-9]*: \([^[:space:]]*\).*/\1/')
        if [ -n "$current_test" ]; then
            echo "$current_test"
        else
            echo "NONE"
        fi
    else
        echo "NONE"
    fi
}

# Function to get recent log entries
get_recent_logs() {
    local count=${1:-10}
    if [ -f "$LOG_DIR/robust-orchestrator.log" ]; then
        tail -$count "$LOG_DIR/robust-orchestrator.log" | while IFS= read -r line; do
            # Color-code log levels
            if [[ "$line" =~ \[SUCCESS\] ]]; then
                echo -e "${GREEN}$line${NC}"
            elif [[ "$line" =~ \[ERROR\]|\[FAILED\] ]]; then
                echo -e "${RED}$line${NC}"
            elif [[ "$line" =~ \[WARN\]|\[RETRY\] ]]; then
                echo -e "${YELLOW}$line${NC}"
            elif [[ "$line" =~ \[START\] ]]; then
                echo -e "${BLUE}$line${NC}"
            elif [[ "$line" =~ \[INFO\] ]]; then
                echo -e "${CYAN}$line${NC}"
            else
                echo "$line"
            fi
        done
    else
        echo "No log file found"
    fi
}

# Function to get system resource usage
get_system_resources() {
    local mem_usage="N/A"
    local disk_usage="N/A"
    local cpu_load="N/A"
    
    if command -v free &> /dev/null; then
        mem_usage=$(free | awk '/^Mem:/ {printf "%.1f%%", $3/$2 * 100.0}')
    fi
    
    if command -v df &> /dev/null; then
        disk_usage=$(df "$WORKING_DIR" | awk 'NR==2 {print $5}')
    fi
    
    if [ -f /proc/loadavg ]; then
        cpu_load=$(cut -d' ' -f1 /proc/loadavg)
    fi
    
    echo "$mem_usage $disk_usage $cpu_load"
}

# Function to display dashboard
show_dashboard() {
    clear
    
    # Header
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                       Test Orchestration Monitor                                  ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    # Status section
    local orchestrator_status=$(get_orchestrator_status)
    local claude_status=$(get_claude_status)
    local current_analysis=$(get_current_analysis)
    
    echo -e "${CYAN}┌─ Process Status ─────────────────────────────────────────────────────────────┐${NC}"
    printf "│ Orchestrator: %-20s │ Claude Subprocess: %-25s │\n" "$orchestrator_status" "$claude_status"
    printf "│ Current Analysis: %-58s │\n" "$current_analysis"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
    
    # Progress section
    read completed failed total backup_count <<< $(get_progress_stats)
    local remaining=$((total - completed - failed))
    local success_rate=$(echo "scale=1; $completed * 100 / $total" | bc -l 2>/dev/null || echo "0.0")
    
    echo -e "${CYAN}┌─ Progress Statistics ────────────────────────────────────────────────────────┐${NC}"
    printf "│ Total Tests: %-6s │ Completed: %-6s │ Failed: %-6s │ Remaining: %-6s │\n" "$total" "$completed" "$failed" "$remaining"
    printf "│ Success Rate: %-6s%% │ Previous Attempts: %-6s │\n" "$success_rate" "$backup_count"
    printf "│ Progress: "
    
    # Progress bar
    local bar_width=65
    local progress=$((completed * bar_width / total))
    printf "["
    for i in $(seq 1 $bar_width); do
        if [ $i -le $progress ]; then
            printf "█"
        else
            printf "░"
        fi
    done
    printf "] │\n"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
    
    # System resources section
    read mem_usage disk_usage cpu_load <<< $(get_system_resources)
    echo -e "${CYAN}┌─ System Resources ───────────────────────────────────────────────────────────┐${NC}"
    printf "│ Memory Usage: %-10s │ Disk Usage: %-10s │ CPU Load: %-10s │\n" "$mem_usage" "$disk_usage" "$cpu_load"
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
    
    # Recent logs section
    echo -e "${CYAN}┌─ Recent Logs (Last 10 entries) ──────────────────────────────────────────────┐${NC}"
    get_recent_logs 10 | sed 's/^/│ /' | head -10
    echo -e "${CYAN}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
    echo
    
    # Instructions
    echo -e "${YELLOW}Commands: [q]uit | [r]efresh | [l]ogs | [f]ull status | [h]elp${NC}"
    echo -e "Last updated: $(date)"
}

# Interactive mode
interactive_monitor() {
    while true; do
        show_dashboard
        
        # Wait for user input or timeout after 10 seconds for auto-refresh
        read -t 10 -n 1 -r input 2>/dev/null || input=""
        
        case $input in
            q|Q) 
                echo -e "\n${GREEN}Exiting monitor...${NC}"
                exit 0
                ;;
            r|R)
                continue  # Refresh (default behavior)
                ;;
            l|L)
                echo -e "\n${CYAN}=== Full Log Tail ===${NC}"
                if [ -f "$LOG_DIR/robust-orchestrator.log" ]; then
                    tail -50 "$LOG_DIR/robust-orchestrator.log" | get_recent_logs
                else
                    echo "No log file found"
                fi
                echo -e "\n${YELLOW}Press any key to return to dashboard...${NC}"
                read -n 1 -r
                ;;
            f|F)
                echo -e "\n${CYAN}=== Full Status Report ===${NC}"
                echo "Orchestrator Processes:"
                ps aux | grep -E "(robust-sequential-orchestrator|sequential-test-orchestrator)" | grep -v grep || echo "None running"
                echo
                echo "Claude Processes:"
                ps aux | grep -E "claude.*sonnet" | grep -v grep | grep -v "pts" || echo "None running"
                echo
                echo "Analysis Files:"
                if [ -d "$ANALYSIS_DIR" ]; then
                    ls -lh "$ANALYSIS_DIR"/*.md 2>/dev/null | wc -l | xargs echo "Count:"
                    ls -lh "$ANALYSIS_DIR"/*.md 2>/dev/null | head -5
                else
                    echo "Analysis directory not found"
                fi
                echo -e "\n${YELLOW}Press any key to return to dashboard...${NC}"
                read -n 1 -r
                ;;
            h|H)
                echo -e "\n${CYAN}=== Help ===${NC}"
                echo "q - Quit the monitor"
                echo "r - Refresh the dashboard (also happens automatically every 10s)"
                echo "l - Show full log tail (last 50 entries)"
                echo "f - Show full status report with process and file details"
                echo "h - Show this help"
                echo -e "\n${YELLOW}Press any key to return to dashboard...${NC}"
                read -n 1 -r
                ;;
        esac
    done
}

# Main function
main() {
    if [ "${1:-}" = "--once" ]; then
        show_dashboard
    else
        # Check if required commands exist
        for cmd in bc; do
            if ! command -v "$cmd" &> /dev/null; then
                echo "Warning: $cmd not found - some features may not work properly"
            fi
        done
        
        echo -e "${GREEN}Starting Test Orchestration Monitor...${NC}"
        echo -e "${YELLOW}Press 'h' for help, 'q' to quit${NC}"
        sleep 2
        
        interactive_monitor
    fi
}

# Run main function
main "$@"