#!/usr/bin/env bash
# Script para iniciar fácilmente la app Shiny en Python

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Iniciando Atlas Territorial LAFT (Shiny for Python)..."

if command -v uv >/dev/null 2>&1; then
    uv run shiny run app.py --reload
elif [ -f ".venv/bin/shiny" ]; then
    .venv/bin/shiny run app.py --reload
else
    python3 -m shiny run app.py --reload
fi
