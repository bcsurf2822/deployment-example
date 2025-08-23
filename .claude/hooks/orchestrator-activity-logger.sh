#!/bin/bash
# Task-Orchestrator Activity Logger Hook
# Tracks all orchestration activities for daily review

# Get current timestamp
timestamp=$(date '+%Y-%m-%d %H:%M:%S')

# Create logs directory if it doesn't exist
mkdir -p .claude/logs

# Read input from stdin
input=$(cat)

# Extract relevant information using jq
subagent_name=$(echo "$input" | jq -r '.subagent_name // empty')
tool_name=$(echo "$input" | jq -r '.tool_name // empty') 
prompt=$(echo "$input" | jq -r '.prompt // empty')
event_type=$(echo "$input" | jq -r '.event_type // empty')

# Determine log message based on context
log_message=""

# Handle different hook events
case "$event_type" in
    "SubagentStop")
        if [[ "$subagent_name" == "task-orchestrator" ]]; then
            log_message="Subagents Task Done"
        elif [[ -n "$subagent_name" ]]; then
            log_message="Received update from $subagent_name agent"
        fi
        ;;
    "UserPromptSubmit")
        # Check if task-orchestrator is likely being activated
        if [[ "$prompt" =~ (use subagents|complex|multiple|coordinate|delegate) ]]; then
            log_message="Subagents Task Start"
        fi
        ;;
    "PreToolUse")
        # Check if task-orchestrator is delegating via Task tool
        if [[ "$tool_name" == "Task" ]]; then
            task_description=$(echo "$input" | jq -r '.tool_input.description // empty')
            if [[ -n "$task_description" ]]; then
                log_message="Delegating task: $task_description"
            else
                log_message="Delegating task to subagent"
            fi
        fi
        ;;
esac

# Write to log if we have a message
if [[ -n "$log_message" ]]; then
    echo "[$timestamp] task-orchestrator $log_message" >> .claude/logs/orchestrator-activity.log
fi

# Also handle specific agent completions
if [[ "$event_type" == "SubagentStop" && -n "$subagent_name" && "$subagent_name" != "task-orchestrator" ]]; then
    # Log individual agent completions
    echo "[$timestamp] $subagent_name Task completed" >> .claude/logs/orchestrator-activity.log
fi

# Check for orchestrator utilization patterns in prompts
if [[ "$prompt" =~ frontend.*backend|backend.*frontend|rag.*pipeline|multiple.*agents ]]; then
    agents_mentioned=""
    [[ "$prompt" =~ frontend ]] && agents_mentioned="frontend-specialist"
    [[ "$prompt" =~ backend ]] && agents_mentioned="$agents_mentioned backend-engineer"
    [[ "$prompt" =~ rag|pipeline|document ]] && agents_mentioned="$agents_mentioned rag-pipeline-engineer"
    
    if [[ -n "$agents_mentioned" ]]; then
        echo "[$timestamp] task-orchestrator Utilizing subagents:$agents_mentioned" >> .claude/logs/orchestrator-activity.log
    fi
fi

# Always return success to avoid blocking
echo "{}"