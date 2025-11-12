#!/bin/bash
set -e

# Instalar dependencias de Python
pip install --upgrade pip
pip install -r requirements.txt

# Instalar navegadores de Playwright
playwright install chromium
playwright install-deps chromium

