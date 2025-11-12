from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from weasyprint import HTML
from io import BytesIO
import base64
import httpx
from playwright.async_api import async_playwright

app = FastAPI(title="HTML to PDF API", description="API para convertir páginas HTML a PDF")


class HTMLRequest(BaseModel):
    html_content: str
    """Contenido HTML a convertir a PDF"""


class HTMLBase64Request(BaseModel):
    html_base64: str
    """Contenido HTML codificado en base64 a convertir a PDF"""


class URLRequest(BaseModel):
    url: str
    """URL de la página HTML de la cual extraer el contenido"""


@app.get("/")
async def root():
    return {
        "message": "API HTML to PDF",
        "endpoints": {
            "/convert": "POST - Convierte HTML a PDF (envía html_content en JSON)",
            "/convert-base64": "POST - Convierte HTML a PDF (envía html_base64 en JSON)",
            "/convert-url": "POST - Convierte HTML a PDF desde una URL (ejecuta JavaScript)",
            "/docs": "Documentación interactiva de la API"
        }
    }


@app.post("/convert")
async def convert_html_to_pdf(request: HTMLRequest):
    """
    Convierte contenido HTML a PDF.
    
    Recibe el HTML en el campo 'html_content' y retorna el PDF como respuesta.
    """
    try:
        # Convertir HTML a PDF usando weasyprint
        html = HTML(string=request.html_content)
        pdf_bytes = html.write_pdf()
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=documento.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir HTML a PDF: {str(e)}")


@app.post("/convert-base64")
async def convert_html_base64_to_pdf(request: HTMLBase64Request):
    """
    Convierte contenido HTML (codificado en base64) a PDF.
    
    Recibe el HTML codificado en base64 en el campo 'html_base64' y retorna el PDF como respuesta.
    """
    try:
        # Decodificar el HTML desde base64
        html_content = base64.b64decode(request.html_base64).decode('utf-8')
        
        # Convertir HTML a PDF usando weasyprint
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf()
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=documento.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al convertir HTML a PDF: {str(e)}")


@app.post("/convert-url")
async def convert_url_to_pdf(request: URLRequest):
    """
    Convierte una página HTML a PDF usando Playwright para ejecutar JavaScript.
    
    Recibe una URL, abre la página en un navegador headless, espera a que se ejecute
    el JavaScript y genera el PDF exactamente como se ve en la web, en una sola página.
    """
    try:
        async with async_playwright() as p:
            # Iniciar el navegador en modo headless
            browser = await p.chromium.launch(headless=True)
            
            # Crear página sin restricciones iniciales para capturar el contenido real
            page = await browser.new_page()
            
            # Navegar a la URL y esperar a que todo se cargue completamente
            await page.goto(request.url, wait_until="networkidle", timeout=30000)
            
            # Esperar a que el DOM esté completamente listo
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")
            
            # Esperar más tiempo para que se ejecute cualquier JavaScript adicional
            await page.wait_for_timeout(3000)
            
            # Ancho A4 fijo: 8.27 pulgadas (210mm) = 794 píxeles a 96 DPI
            a4_width_px = 794
            width_inches = 8.27  # Ancho A4 fijo
            
            # Inyectar estilos primero para eliminar márgenes, padding y saltos de página
            # y forzar el ancho A4
            await page.add_style_tag(content=f"""
                @page {{
                    margin: 0 !important;
                    padding: 0 !important;
                    size: auto;
                }}
                * {{
                    page-break-inside: avoid !important;
                    page-break-after: avoid !important;
                    page-break-before: avoid !important;
                    break-inside: avoid !important;
                    break-after: avoid !important;
                    break-before: avoid !important;
                    orphans: 999 !important;
                    widows: 999 !important;
                }}
                html, body {{
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box;
                    overflow: visible !important;
                    height: auto !important;
                    min-height: auto !important;
                    max-height: none !important;
                    width: {a4_width_px}px !important;
                    max-width: {a4_width_px}px !important;
                }}
            """)
            
            # Esperar a que los estilos se apliquen
            await page.wait_for_timeout(500)
            
            # Ajustar el viewport al ancho A4 y altura inicial
            await page.set_viewport_size({
                'width': a4_width_px,
                'height': 2000  # Altura inicial, se ajustará después
            })
            
            # Esperar un momento para que el viewport se ajuste
            await page.wait_for_timeout(500)
            
            # Obtener la altura real del contenido con ancho A4 fijo
            content_height = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    
                    return Math.ceil(Math.max(
                        body.scrollHeight,
                        body.offsetHeight,
                        html.clientHeight,
                        html.scrollHeight,
                        html.offsetHeight
                    ));
                }
            """)
            
            # Ajustar viewport con ancho A4 y altura del contenido con buffer
            await page.set_viewport_size({
                'width': a4_width_px,
                'height': content_height + 100  # Buffer para asegurar captura completa
            })
            
            # Esperar un momento para que el viewport se ajuste
            await page.wait_for_timeout(500)
            
            # Recalcular altura final después de ajustar el viewport
            final_height = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    
                    return Math.ceil(Math.max(
                        body.scrollHeight,
                        body.offsetHeight,
                        html.clientHeight,
                        html.scrollHeight,
                        html.offsetHeight
                    ));
                }
            """)
            
            # Ajustar viewport con la altura final exacta
            await page.set_viewport_size({
                'width': a4_width_px,
                'height': final_height + 50  # Buffer adicional
            })
            
            # Esperar un momento final para que todo se estabilice
            await page.wait_for_timeout(500)
            
            # Recalcular una vez más para obtener la altura final precisa
            final_height = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    
                    return Math.ceil(Math.max(
                        body.scrollHeight,
                        body.offsetHeight,
                        html.clientHeight,
                        html.scrollHeight,
                        html.offsetHeight
                    ));
                }
            """)
            
            # Convertir altura a pulgadas (96 DPI estándar)
            height_inches = final_height / 96.0
            
            # Asegurar altura mínima razonable
            if height_inches < 1:
                height_inches = 11.69  # Altura A4 por defecto
            
            # Agregar un margen de seguridad a la altura para asegurar que todo quepa
            height_inches = height_inches + 0.2
            
            # Generar el PDF con dimensiones exactas del contenido (una sola página)
            pdf_bytes = await page.pdf(
                width=f"{width_inches}in",
                height=f"{height_inches}in",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=False,
                scale=1.0
            )
            
            await browser.close()
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=documento.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error al convertir HTML a PDF: {str(e)}"
        )

