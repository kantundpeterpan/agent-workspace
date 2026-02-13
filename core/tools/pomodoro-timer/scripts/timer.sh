#!/bin/bash
# Pomodoro Timer for Pair Programming Sessions
# Usage: timer.sh <action> [duration] [phase]

TIMER_FILE="/tmp/agent-pomodoro.json"

action="${1:-status}"
duration="${2:-25}"
phase="${3:-implement}"

case "$action" in
  start)
    end_time=$(($(date +%s) + duration * 60))
    echo "{\"phase\": \"$phase\", \"duration\": $duration, \"end_time\": $end_time, \"status\": \"running\"}" > "$TIMER_FILE"
    echo "⏱️  Timer started: $duration min ($phase phase)"
    ;;
  
  status)
    if [ ! -f "$TIMER_FILE" ]; then
      echo "No active timer"
      exit 0
    fi
    
    current_time=$(date +%s)
    end_time=$(jq -r '.end_time' "$TIMER_FILE")
    phase=$(jq -r '.phase' "$TIMER_FILE")
    status=$(jq -r '.status' "$TIMER_FILE")
    
    if [ "$status" = "paused" ]; then
      echo "⏸️  Timer paused in $phase phase"
      exit 0
    fi
    
    remaining=$((end_time - current_time))
    
    if [ $remaining -le 0 ]; then
      echo "✅ Timer complete! ($phase phase finished)"
      rm -f "$TIMER_FILE"
    else
      minutes=$((remaining / 60))
      seconds=$((remaining % 60))
      echo "⏱️  $minutes:$(printf %02d $seconds) remaining ($phase phase)"
    fi
    ;;
  
  stop)
    if [ -f "$TIMER_FILE" ]; then
      rm -f "$TIMER_FILE"
      echo "🛑 Timer stopped"
    else
      echo "No active timer"
    fi
    ;;
  
  pause)
    if [ -f "$TIMER_FILE" ]; then
      jq '.status = "paused"' "$TIMER_FILE" > "${TIMER_FILE}.tmp" && mv "${TIMER_FILE}.tmp" "$TIMER_FILE"
      echo "⏸️  Timer paused"
    else
      echo "No active timer"
    fi
    ;;
  
  resume)
    if [ -f "$TIMER_FILE" ]; then
      jq '.status = "running"' "$TIMER_FILE" > "${TIMER_FILE}.tmp" && mv "${TIMER_FILE}.tmp" "$TIMER_FILE"
      echo "▶️  Timer resumed"
    else
      echo "No active timer"
    fi
    ;;
  
  *)
    echo "Usage: timer.sh {start|status|stop|pause|resume} [duration] [phase]"
    exit 1
    ;;
esac
