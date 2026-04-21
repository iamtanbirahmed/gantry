#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT="$PROJECT_ROOT/docs/images/screenshot.svg"

mkdir -p "$(dirname "$OUTPUT")"
cd "$PROJECT_ROOT"

uv run python scripts/take_screenshot.py "$OUTPUT"
