from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io import BytesIO
import base64
import httpx
import math
import traceback
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar dependencias con manejo de errores
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Playwright no está disponible: {e}")
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError as e:
    logger.error(f"PIL/Pillow no está disponible: {e}")
    PIL_AVAILABLE = False
    Image = None

app = FastAPI(title="HTML to PDF API", description="API para convertir páginas HTML a PDF")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://emotive.g3nia.com",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HTMLRequest(BaseModel):
    html_content: str
    """Contenido HTML a convertir a PDF"""


class HTMLBase64Request(BaseModel):
    html_base64: str
    """Contenido HTML codificado en base64 a convertir a PDF"""


class URLRequest(BaseModel):
    url: str
    """URL de la página HTML de la cual extraer el contenido"""


class URLImageRequest(BaseModel):
    url: str
    """URL de la imagen a convertir a PDF"""


@app.get("/")
async def root():
    return {
        "message": "API HTML to PDF",
        "endpoints": {
            "/convert": "POST - Convierte HTML a PDF (envía html_content en JSON)",
            "/convert-base64": "POST - Convierte HTML a PDF (envía html_base64 en JSON)",
            "/convert-url": "POST - Convierte HTML a PDF desde una URL (ejecuta JavaScript)",
            "/convert-url-a4": "POST - Convierte una página web desde URL a PDF dividiéndola automáticamente en múltiples páginas A4",
            "/health": "GET - Verifica el estado de la API y dependencias",
            "/docs": "Documentación interactiva de la API"
        }
    }


@app.get("/health")
async def health_check():
    """Verifica el estado de la API y sus dependencias"""
    status = {
        "status": "ok",
        "playwright": "available" if PLAYWRIGHT_AVAILABLE else "not available",
        "pillow": "available" if PIL_AVAILABLE else "not available"
    }
    
    if not PLAYWRIGHT_AVAILABLE or not PIL_AVAILABLE:
        status["status"] = "degraded"
    
    return status


@app.post("/convert")
async def convert_html_to_pdf(request: HTMLRequest):
    """
    Convierte contenido HTML a PDF usando Playwright.
    
    Recibe el HTML en el campo 'html_content' y retorna el PDF como respuesta.
    """
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Cargar el HTML usando data URL
            html_encoded = base64.b64encode(request.html_content.encode('utf-8')).decode('utf-8')
            data_url = f"data:text/html;base64,{html_encoded}"
            
            await page.goto(data_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Obtener dimensiones del contenido
            dimensions = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    return {
                        width: Math.ceil(Math.max(body.scrollWidth, html.scrollWidth)),
                        height: Math.ceil(Math.max(body.scrollHeight, html.scrollHeight))
                    };
                }
            """)
            
            await page.set_viewport_size({'width': dimensions['width'], 'height': dimensions['height']})
            await page.wait_for_timeout(500)
            
            # Generar PDF
            pdf_bytes = await page.pdf(
                width=f"{dimensions['width'] / 96.0}in",
                height=f"{(dimensions['height'] / 96.0) + 0.2}in",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=False
            )
            
            await browser.close()
        
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
    Convierte contenido HTML (codificado en base64) a PDF usando Playwright.
    
    Recibe el HTML codificado en base64 en el campo 'html_base64' y retorna el PDF como respuesta.
    """
    try:
        # Decodificar el HTML desde base64
        html_content = base64.b64decode(request.html_base64).decode('utf-8')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Cargar el HTML usando data URL
            html_encoded = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
            data_url = f"data:text/html;base64,{html_encoded}"
            
            await page.goto(data_url, wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Obtener dimensiones del contenido
            dimensions = await page.evaluate("""
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    return {
                        width: Math.ceil(Math.max(body.scrollWidth, html.scrollWidth)),
                        height: Math.ceil(Math.max(body.scrollHeight, html.scrollHeight))
                    };
                }
            """)
            
            await page.set_viewport_size({'width': dimensions['width'], 'height': dimensions['height']})
            await page.wait_for_timeout(500)
            
            # Generar PDF
            pdf_bytes = await page.pdf(
                width=f"{dimensions['width'] / 96.0}in",
                height=f"{(dimensions['height'] / 96.0) + 0.2}in",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=False
            )
            
            await browser.close()
        
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


@app.post("/convert-url-a4")
async def convert_url_image_to_a4_pdf(request: URLImageRequest):
    """
    Convierte una página web desde una URL a PDF dividiéndola automáticamente en múltiples páginas A4.
    
    La página web se captura como imagen, se divide automáticamente en secciones que caben en formato A4,
    y se genera un PDF con múltiples páginas. El número de páginas se calcula automáticamente según el tamaño.
    """
    logger.info(f"Iniciando conversión de URL a PDF A4: {request.url}")
    
    # Validar dependencias
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Playwright no está instalado. Ejecuta: pip install playwright && playwright install chromium"
        )
    
    if not PIL_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PIL/Pillow no está instalado. Ejecuta: pip install Pillow"
        )
    
    # Validar URL
    if not request.url or not request.url.strip():
        raise HTTPException(
            status_code=400,
            detail="La URL no puede estar vacía"
        )
    
    try:
        async with async_playwright() as p:
            # Iniciar el navegador en modo headless
            browser = await p.chromium.launch(headless=True)
            
            # Crear contexto con opciones para manejar errores de red
            context = await browser.new_context(
                ignore_https_errors=True,
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Navegar a la URL y esperar a que todo se cargue completamente
            try:
                response = await page.goto(
                    request.url, 
                    wait_until="networkidle", 
                    timeout=60000  # Aumentar timeout a 60 segundos
                )
                
                # Verificar si la respuesta es válida
                if response is None:
                    await browser.close()
                    raise HTTPException(
                        status_code=400,
                        detail=f"No se pudo cargar la URL: {request.url}. La página no respondió o la URL no es accesible."
                    )
                
                # Verificar código de estado HTTP
                if response.status >= 400:
                    await browser.close()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error HTTP {response.status} al acceder a la URL: {request.url}"
                    )
                    
            except Exception as nav_error:
                await browser.close()
                error_msg = str(nav_error)
                if "net::ERR_ABORTED" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error al acceder a la URL: {request.url}. La conexión fue abortada. Verifica que la URL sea accesible desde el servidor."
                    )
                elif "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error: No se pudo resolver el nombre de dominio de la URL: {request.url}"
                    )
                elif "net::ERR_CONNECTION_REFUSED" in error_msg:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error: La conexión fue rechazada para la URL: {request.url}. Verifica que el servidor esté accesible."
                    )
                elif "Timeout" in error_msg or "timeout" in error_msg:
                    raise HTTPException(
                        status_code=408,
                        detail=f"Timeout: La URL tardó demasiado en cargar: {request.url}"
                    )
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error al navegar a la URL: {request.url}. Detalles: {error_msg}"
                    )
            
            # Esperar a que el DOM esté completamente listo
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")
            
            # Esperar más tiempo para que se ejecute cualquier JavaScript adicional
            await page.wait_for_timeout(3000)
            
            # Ancho A4 fijo: 8.27 pulgadas (210mm) = 794 píxeles a 96 DPI
            a4_width_px = 794
            width_inches = 8.27  # Ancho A4 fijo
            
            # Inyectar estilos para forzar el ancho A4
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
                }}
                html, body {{
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box;
                    overflow: visible !important;
                    height: auto !important;
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
            
            # Esperar a que todas las imágenes se carguen
            try:
                await page.evaluate("""
                    () => {
                        return Promise.all(
                            Array.from(document.images).map(img => {
                                if (img.complete) return Promise.resolve();
                                return new Promise((resolve, reject) => {
                                    img.onload = resolve;
                                    img.onerror = resolve; // Continuar aunque haya errores
                                    setTimeout(resolve, 5000); // Timeout de 5 segundos por imagen
                                });
                            })
                        );
                    }
                """)
            except Exception:
                # Si hay error esperando imágenes, continuar de todas formas
                pass
            
            # Obtener la altura real del contenido con ancho A4 fijo
            try:
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
                
                # Validar altura
                if not content_height or content_height <= 0:
                    await browser.close()
                    raise HTTPException(
                        status_code=500,
                        detail="No se pudo obtener la altura válida de la página"
                    )
                
                # Limitar altura máxima para evitar problemas de memoria
                max_height = 50000
                content_height = min(content_height, max_height)
                
                logger.info(f"Altura del contenido con ancho A4: {content_height}px")
                
            except Exception as dim_error:
                await browser.close()
                logger.error(f"Error al obtener altura: {str(dim_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al obtener la altura de la página: {str(dim_error)}"
                )
            
            # Ajustar viewport con ancho A4 y altura del contenido
            try:
                await page.set_viewport_size({
                    'width': a4_width_px,
                    'height': content_height + 100  # Buffer para asegurar captura completa
                })
                
                # Esperar a que el viewport se ajuste
                await page.wait_for_timeout(1000)
            except Exception as viewport_error:
                await browser.close()
                logger.error(f"Error al ajustar viewport: {str(viewport_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al ajustar el viewport: {str(viewport_error)}"
                )
            
            # Capturar la página completa como imagen PNG
            try:
                screenshot_bytes = await page.screenshot(
                    full_page=True,
                    type='png'
                )
                
                if not screenshot_bytes or len(screenshot_bytes) == 0:
                    await browser.close()
                    raise HTTPException(
                        status_code=500,
                        detail="La captura de pantalla está vacía"
                    )
                    
            except Exception as screenshot_error:
                await browser.close()
                logger.error(f"Error al capturar screenshot: {str(screenshot_error)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al capturar la página como imagen: {str(screenshot_error)}"
                )
            
            await browser.close()
        
        # Abrir la imagen capturada con PIL para obtener sus dimensiones
        try:
            image = Image.open(BytesIO(screenshot_bytes))
            img_width, img_height = image.size
            
            if img_width <= 0 or img_height <= 0:
                raise HTTPException(
                    status_code=500,
                    detail="Las dimensiones de la imagen capturada son inválidas"
                )
        except Exception as img_error:
            logger.error(f"Error al procesar imagen: {str(img_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al procesar la imagen capturada: {str(img_error)}"
            )
        
        # Verificar tamaño de la imagen
        screenshot_size_mb = len(screenshot_bytes) / (1024 * 1024)
        logger.info(f"Tamaño de la imagen capturada: {screenshot_size_mb:.2f} MB ({img_width}x{img_height}px)")
        
        # Convertir la imagen a base64 para usar en HTML
        image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        image_data_url = f"data:image/png;base64,{image_base64}"
        
        # Verificar tamaño del data URL
        data_url_size_mb = len(image_data_url) / (1024 * 1024)
        logger.info(f"Tamaño del data URL: {data_url_size_mb:.2f} MB")
        
        # Dimensiones A4 en píxeles (a 96 DPI)
        # A4: 210mm x 297mm = 8.27in x 11.69in = 794px x 1123px a 96 DPI
        a4_width_px = 794
        a4_height_px = 1123
        
        # Verificar que el ancho de la imagen sea A4 (puede haber pequeñas diferencias por redondeo)
        if abs(img_width - a4_width_px) > 10:
            logger.warning(f"El ancho de la imagen ({img_width}px) no coincide con A4 ({a4_width_px}px). Ajustando cálculo.")
        
        # Solo dividir verticalmente, el ancho ya es A4
        pages_horizontal = 1  # Siempre 1 porque el ancho ya es A4
        pages_vertical = math.ceil(img_height / a4_height_px)
        total_pages = pages_horizontal * pages_vertical
        
        logger.info(f"Imagen: {img_width}x{img_height}px. Páginas necesarias: {pages_vertical} verticales x {pages_horizontal} horizontal = {total_pages} páginas")
        
        # Crear HTML con múltiples páginas A4, cada una mostrando una sección de la imagen
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @page {{
                    size: A4;
                    margin: 0;
                }}
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                }}
                .page {{
                    width: 210mm;
                    height: 297mm;
                    page-break-after: always;
                    overflow: hidden;
                    position: relative;
                    background: white;
                    box-sizing: border-box;
                }}
                .page:last-child {{
                    page-break-after: auto;
                }}
                .image-section {{
                    position: absolute;
                    width: {img_width}px;
                    height: {img_height}px;
                    background-image: url('{image_data_url}');
                    background-repeat: no-repeat;
                    background-size: {img_width}px {img_height}px;
                }}
            </style>
        </head>
        <body>
        """
        
        # Crear cada página con su sección correspondiente de la imagen
        for row in range(pages_vertical):
            for col in range(pages_horizontal):
                # Calcular la posición de inicio de esta sección
                x_offset = -col * a4_width_px
                y_offset = -row * a4_height_px
                
                html_content += f"""
                <div class="page">
                    <div class="image-section" style="background-position: {x_offset}px {y_offset}px;"></div>
                </div>
                """
        
        html_content += """
        </body>
        </html>
        """
        
        # Verificar el tamaño del HTML
        html_size = len(html_content.encode('utf-8'))
        html_size_mb = html_size / (1024 * 1024)
        logger.info(f"Tamaño del HTML generado: {html_size_mb:.2f} MB")
        
        # Advertir si el HTML es muy grande
        if html_size_mb > 50:
            logger.warning(f"El HTML es muy grande ({html_size_mb:.2f} MB), esto puede causar problemas de memoria")
        
        # Convertir el HTML a PDF usando Playwright
        try:
            logger.info(f"Generando PDF con {pages_horizontal}x{pages_vertical} páginas ({total_pages} total)")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                # Crear contexto con viewport A4
                context = await browser.new_context(
                    viewport={'width': 794, 'height': 1123}  # Dimensiones A4 en píxeles
                )
                page = await context.new_page()
                
                # Usar set_content en lugar de goto para evitar problemas con data URLs grandes
                try:
                    await page.set_content(html_content, wait_until="networkidle", timeout=60000)
                    await page.wait_for_load_state("domcontentloaded")
                    # Esperar a que las imágenes se carguen
                    await page.wait_for_timeout(3000)
                except Exception as html_load_error:
                    await browser.close()
                    error_msg = str(html_load_error)
                    logger.error(f"Error al cargar HTML para PDF: {error_msg}")
                    
                    # Mensaje más específico según el tipo de error
                    if "timeout" in error_msg.lower():
                        raise HTTPException(
                            status_code=500,
                            detail=f"Timeout al cargar el HTML. La imagen puede ser demasiado grande. Error: {error_msg}"
                        )
                    elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error de memoria. La imagen es demasiado grande para procesar. Error: {error_msg}"
                        )
                    else:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Error al cargar el HTML para generar el PDF: {error_msg}"
                        )
                
                # Generar PDF con formato A4
                try:
                    pdf_bytes = await page.pdf(
                        format="A4",
                        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                        print_background=True,
                        prefer_css_page_size=True
                    )
                    
                    if not pdf_bytes or len(pdf_bytes) == 0:
                        await browser.close()
                        raise HTTPException(
                            status_code=500,
                            detail="El PDF generado está vacío"
                        )
                        
                except Exception as pdf_error:
                    await browser.close()
                    logger.error(f"Error al generar PDF: {str(pdf_error)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error al generar el PDF: {str(pdf_error)}"
                    )
                
                await browser.close()
        except HTTPException:
            raise
        except Exception as pdf_gen_error:
            logger.error(f"Error inesperado al generar PDF: {str(pdf_gen_error)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error inesperado al generar el PDF: {str(pdf_gen_error)}"
            )
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=web_a4.pdf"
            }
        )
    except HTTPException:
        # Re-lanzar HTTPException sin modificar
        raise
    except Exception as e:
        # Log el error completo para debugging
        error_trace = traceback.format_exc()
        error_type = type(e).__name__
        logger.error(f"Error inesperado en convert-url-a4 (tipo: {error_type}): {str(e)}")
        logger.error(f"Traceback completo:\n{error_trace}")
        
        # Proporcionar más información según el tipo de error
        error_detail = str(e)
        if "chromium" in error_detail.lower() or "browser" in error_detail.lower():
            error_detail += ". Asegúrate de que Playwright esté instalado correctamente: playwright install chromium"
        elif "memory" in error_detail.lower() or "out of memory" in error_detail.lower():
            error_detail += ". La página es demasiado grande. Intenta con una página más pequeña."
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al convertir URL a PDF ({error_type}): {error_detail}"
        )

@app.post("/convert-url-paginated")
async def convert_url_to_pdf_paginated(request: URLRequest):
    """
    Convierte una página HTML a PDF usando Playwright, paginado automáticamente en tamaño A4.
    
    Recibe una URL y genera el PDF con el ancho A4 estándar, dividiendo el contenido
    en múltiples páginas según sea necesario para la impresión.
    """
    try:
        async with async_playwright() as p:
            # 1. Iniciar el navegador y crear la página
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # 2. Navegar a la URL y esperar carga completa
            await page.goto(request.url, wait_until="networkidle", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_load_state("networkidle")
            
            # Esperar un tiempo prudente para el renderizado final de JS
            await page.wait_for_timeout(3000)
            
            # Ancho A4 fijo: 8.27 pulgadas
            a4_width_px = 794
            
            # 3. Inyectar estilos para impresión limpia y ancho A4
            # NOTA: Permitimos los saltos de página y forzamos el ancho para renderizado.
            await page.add_style_tag(content=f"""
                @page {{
                    /* Permitir que el motor de impresión defina el tamaño de la página (A4 por defecto) */
                    
                    padding: 0;
                    size: A4;
                }}
                /* Ajustes de CSS para asegurar que los elementos no corten las páginas */
                * {{
                    /* Recomendación: permitir la paginación, pero intentar mantener los bloques */
                    break-inside: auto !important;
                    page-break-inside: auto !important;
                    orphans: 3 !important; /* Evitar que queden 1 o 2 líneas al final de una página */
                    widows: 3 !important;
                }}
                /* Forzar el ancho del contenedor principal al ancho A4 para el renderizado inicial */
                html, body {{
                    margin: 0 !important;
                    padding: 0 !important;
                    box-sizing: border-box;
                    width: {a4_width_px}px !important;
                    max-width: {a4_width_px}px !important;
                }}
            """)
            
            # Esperar a que los estilos se apliquen
            await page.wait_for_timeout(500)
            
            # 4. Ajustar el viewport *SOLO* al ancho A4 y una altura inicial grande
            # **YA NO ES NECESARIO CALCULAR LA ALTURA EXACTA**
            await page.set_viewport_size({
                'width': a4_width_px,
                'height': 5000 # Solo necesita una altura inicial grande para renderizar todo
            })
            
            # Esperar estabilización
            await page.wait_for_timeout(1000)
            
            # 5. Generar el PDF Paginado
            # Los parámetros clave son:
            # - prefer_css_page_size: True -> Le dice a Playwright que use la configuración @page (tamaño A4)
            # - width/height: ELIMINADOS -> El navegador calculará la paginación según el tamaño A4
            pdf_bytes = await page.pdf(
                margin={"top": "0in", "right": "0in", "bottom": "0in", "left": "0in"},
                print_background=True,
                prefer_css_page_size=True, # ¡CLAVE! Usar el tamaño A4 del CSS
                scale=1.0
            )
            
            await browser.close()
        
        # Retornar el PDF como respuesta
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": "attachment; filename=Relatorio_E_MO_TI_VE.pdf"
            }
        )
    except Exception as e:
        # Se mantiene el manejo de errores
        await browser.close() # Asegurar cierre en caso de excepción
        raise HTTPException(
            status_code=500, 
            detail=f"Error al convertir HTML a PDF: {str(e)}"
        )