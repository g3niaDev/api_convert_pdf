#!/bin/bash
set -e

# Iniciar la aplicación
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

