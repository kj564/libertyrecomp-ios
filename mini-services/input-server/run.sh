#!/bin/bash
cd "$(dirname "$0")"
while true; do
  echo "[wrapper] starting input-server..."
  INPUT_DEBUG=1 bun index.ts 2>&1
  echo "[wrapper] input-server exited ($?), restarting in 1s..."
  sleep 1
done
