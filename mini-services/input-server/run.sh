#!/bin/bash
# Auto-restart wrapper for input-server (Linux/macOS)
cd "$(dirname "$0")"
while true; do
  echo "[wrapper $(date +%T)] starting input-server..."
  INPUT_DEBUG=1 bun index.ts
  echo "[wrapper $(date +%T)] input-server exited ($?), restarting in 2s..."
  sleep 2
done
