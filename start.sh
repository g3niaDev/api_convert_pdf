#!/bin/bash
set -e

# En Nix, las librerías deberían estar disponibles automáticamente
# Pero si es necesario, podemos agregar rutas comunes de Nix
if [ -d "/nix/store" ]; then
  # Buscar y agregar librerías de glib, pango, cairo, etc.
  for libdir in /nix/store/*-glib-*/lib /nix/store/*-pango-*/lib /nix/store/*-cairo-*/lib /nix/store/*-gobject-introspection-*/lib; do
    if [ -d "$libdir" ]; then
      export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${libdir}"
    fi
  done
fi

# Iniciar la aplicación
exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}

