#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

docker compose up -d db

echo "PostgreSQL is starting via docker compose. Use 'docker compose logs -f db' to monitor logs." 
