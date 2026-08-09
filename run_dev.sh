#!/usr/bin/env bash
# Ejecuta la app en modo desarrollo (Linux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activar virtualenv si existe
if [ -d .venv ]; then
    source .venv/bin/activate
elif [ -d venv ]; then
    source venv/bin/activate
fi

python -m src.main "$@"
