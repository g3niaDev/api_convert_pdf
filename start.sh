#!/bin/bash
# Instalar navegadores de Playwright
playwright install chromium
playwright install-deps chromium

# Iniciar la aplicación
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

