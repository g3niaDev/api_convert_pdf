# API HTML to PDF

API en Python que convierte páginas HTML a PDF usando FastAPI y WeasyPrint.

## Instalación

1. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor

```bash
uvicorn app:app --reload
```

El servidor estará disponible en `http://localhost:8000`

### Documentación

Accede a la documentación interactiva en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /convert

Convierte HTML a PDF. Recibe el HTML directamente en el cuerpo de la petición.

**Ejemplo con curl:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Content-Type: application/json" \
  -d '{"html_content": "<html><body><h1>Hola Mundo</h1></body></html>"}' \
  --output documento.pdf
```

**Ejemplo con Python:**
```python
import requests

html = "<html><body><h1>Hola Mundo</h1><p>Este es un PDF generado desde HTML.</p></body></html>"
response = requests.post("http://localhost:8000/convert", json={"html_content": html})

with open("documento.pdf", "wb") as f:
    f.write(response.content)
```

### POST /convert-base64

Convierte HTML a PDF. Recibe el HTML codificado en base64.

**Ejemplo con curl:**
```bash
echo -n "<html><body><h1>Hola Mundo</h1></body></html>" | base64 | \
  xargs -I {} curl -X POST "http://localhost:8000/convert-base64" \
  -H "Content-Type: application/json" \
  -d "{\"html_base64\": \"{}\"}" \
  --output documento.pdf
```

## Notas

- WeasyPrint soporta CSS3 y puede renderizar estilos complejos
- Para usar fuentes personalizadas o recursos externos, asegúrate de que sean accesibles desde el servidor
- El PDF se genera en memoria y se retorna directamente en la respuesta

