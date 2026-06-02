#!/bin/bash
# Gmail Cleanup Agent launcher
# Usage: ./run.sh [--dry-run]
#
# Requires: Claude Code CLI (`claude`) with Gmail MCP connected
# Gmail MCP is configured via Claude Code settings (claude.ai integration)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_PROMPT="$SCRIPT_DIR/cleanup_agent.md"

if [[ ! -f "$AGENT_PROMPT" ]]; then
  echo "Error: cleanup_agent.md not found in $SCRIPT_DIR"
  exit 1
fi

ALLOWED_TOOLS="mcp__claude_ai_Gmail__search_threads,mcp__claude_ai_Gmail__get_thread,mcp__claude_ai_Gmail__label_thread,mcp__claude_ai_Gmail__label_message,mcp__claude_ai_Gmail__list_labels"

echo "Starting Gmail Cleanup Agent..."
echo "Prompt: $AGENT_PROMPT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

claude \
  --allowedTools "$ALLOWED_TOOLS" \
  --dangerously-skip-permissions \
  -p "$(cat "$AGENT_PROMPT")"
