# Integración de la API PDF con PHP

Esta guía explica cómo integrar la API de conversión HTML a PDF desde una aplicación PHP.

## Endpoint Disponible

**URL del endpoint:** `http://127.0.0.1:8080/convert-url`

**Método:** `POST`

**Content-Type:** `application/json`

## Formato de la Petición

La API espera recibir un JSON con la siguiente estructura:

```json
{
    "url": "http://localhost:8000/meurelatorio/pdf?formulario_id=1&usuario_id=4"
}
```

## Ejemplos de Implementación en PHP

### Opción 1: Usando cURL (Recomendado)

```php
<?php
/**
 * Función para generar PDF desde una URL
 * 
 * @param string $url La URL de la página a convertir
 * @param string $apiUrl La URL de la API (por defecto: http://127.0.0.1:8080/convert-url)
 * @return string|false Contenido del PDF o false en caso de error
 */
function generarPDFDesdeURL($url, $apiUrl = 'http://127.0.0.1:8080/convert-url') {
    // Preparar los datos
    $data = json_encode([
        'url' => $url
    ]);
    
    // Inicializar cURL
    $ch = curl_init($apiUrl);
    
    // Configurar opciones de cURL
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Content-Length: ' . strlen($data)
        ],
        CURLOPT_POSTFIELDS => $data,
        CURLOPT_TIMEOUT => 60, // Timeout de 60 segundos
        CURLOPT_CONNECTTIMEOUT => 10
    ]);
    
    // Ejecutar la petición
    $pdfContent = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    
    curl_close($ch);
    
    // Verificar errores
    if ($error) {
        error_log("Error en cURL: " . $error);
        return false;
    }
    
    if ($httpCode !== 200) {
        error_log("Error HTTP: " . $httpCode);
        return false;
    }
    
    return $pdfContent;
}

// Ejemplo de uso
$url = "http://localhost:8000/meurelatorio/pdf?formulario_id=1&usuario_id=4";
$pdf = generarPDFDesdeURL($url);

if ($pdf !== false) {
    // Enviar el PDF al navegador
    header('Content-Type: application/pdf');
    header('Content-Disposition: attachment; filename="reporte.pdf"');
    header('Content-Length: ' . strlen($pdf));
    echo $pdf;
    exit;
} else {
    echo "Error al generar el PDF";
}
?>
```

### Opción 2: Usando file_get_contents con stream_context

```php
<?php
function generarPDFDesdeURL($url, $apiUrl = 'http://127.0.0.1:8080/convert-url') {
    $data = json_encode(['url' => $url]);
    
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => [
                'Content-Type: application/json',
                'Content-Length: ' . strlen($data)
            ],
            'content' => $data,
            'timeout' => 60
        ]
    ];
    
    $context = stream_context_create($options);
    $pdfContent = @file_get_contents($apiUrl, false, $context);
    
    if ($pdfContent === false) {
        return false;
    }
    
    return $pdfContent;
}

// Ejemplo de uso
$url = "http://localhost:8000/meurelatorio/pdf?formulario_id=1&usuario_id=4";
$pdf = generarPDFDesdeURL($url);

if ($pdf !== false) {
    header('Content-Type: application/pdf');
    header('Content-Disposition: attachment; filename="reporte.pdf"');
    echo $pdf;
    exit;
}
?>
```

### Opción 3: Usando Guzzle HTTP (Si está disponible)

```php
<?php
require 'vendor/autoload.php'; // Si usas Composer

use GuzzleHttp\Client;

function generarPDFDesdeURL($url, $apiUrl = 'http://127.0.0.1:8080/convert-url') {
    $client = new Client([
        'timeout' => 60.0
    ]);
    
    try {
        $response = $client->post($apiUrl, [
            'json' => ['url' => $url],
            'headers' => [
                'Content-Type' => 'application/json'
            ]
        ]);
        
        if ($response->getStatusCode() === 200) {
            return $response->getBody()->getContents();
        }
        
        return false;
    } catch (\Exception $e) {
        error_log("Error: " . $e->getMessage());
        return false;
    }
}

// Ejemplo de uso
$url = "http://localhost:8000/meurelatorio/pdf?formulario_id=1&usuario_id=4";
$pdf = generarPDFDesdeURL($url);

if ($pdf !== false) {
    header('Content-Type: application/pdf');
    header('Content-Disposition: attachment; filename="reporte.pdf"');
    echo $pdf;
    exit;
}
?>
```

## Ejemplo Completo: Controlador Laravel

Si estás usando Laravel, aquí tienes un ejemplo de controlador:

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class ReporteController extends Controller
{
    /**
     * Genera un PDF del reporte
     */
    public function generarPDF(Request $request)
    {
        $formularioId = $request->input('formulario_id');
        $usuarioId = $request->input('usuario_id');
        
        // Construir la URL del reporte
        $url = url("/meurelatorio/pdf?formulario_id={$formularioId}&usuario_id={$usuarioId}");
        
        // URL de la API PDF
        $apiUrl = env('PDF_API_URL', 'http://127.0.0.1:8080/convert-url');
        
        // Preparar la petición
        $data = json_encode(['url' => $url]);
        
        $ch = curl_init($apiUrl);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Content-Length: ' . strlen($data)
            ],
            CURLOPT_POSTFIELDS => $data,
            CURLOPT_TIMEOUT => 60,
        ]);
        
        $pdf = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error || $httpCode !== 200) {
            Log::error("Error al generar PDF: " . ($error ?: "HTTP $httpCode"));
            return response()->json(['error' => 'Error al generar el PDF'], 500);
        }
        
        return response($pdf, 200)
            ->header('Content-Type', 'application/pdf')
            ->header('Content-Disposition', 'attachment; filename="reporte.pdf"');
    }
}
```

## Ejemplo Completo: Función PHP Simple

```php
<?php
/**
 * Genera un PDF desde una URL y lo descarga
 */
function descargarPDF($formularioId, $usuarioId) {
    // Construir la URL del reporte
    $urlReporte = "http://localhost:8000/meurelatorio/pdf?formulario_id={$formularioId}&usuario_id={$usuarioId}";
    
    // URL de la API PDF
    $apiUrl = "http://127.0.0.1:8080/convert-url";
    
    // Preparar los datos JSON
    $data = json_encode([
        'url' => $urlReporte
    ]);
    
    // Inicializar cURL
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $apiUrl);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, [
        'Content-Type: application/json',
        'Content-Length: ' . strlen($data)
    ]);
    curl_setopt($ch, CURLOPT_TIMEOUT, 60);
    
    // Ejecutar la petición
    $pdfContent = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    // Verificar si hubo errores
    if ($error) {
        die("Error en la petición: " . $error);
    }
    
    if ($httpCode !== 200) {
        die("Error HTTP: " . $httpCode);
    }
    
    // Enviar el PDF al navegador
    header('Content-Type: application/pdf');
    header('Content-Disposition: attachment; filename="reporte_' . $formularioId . '_' . $usuarioId . '.pdf"');
    header('Content-Length: ' . strlen($pdfContent));
    echo $pdfContent;
    exit;
}

// Ejemplo de uso
if (isset($_GET['formulario_id']) && isset($_GET['usuario_id'])) {
    descargarPDF($_GET['formulario_id'], $_GET['usuario_id']);
} else {
    echo "Faltan parámetros: formulario_id y usuario_id";
}
?>
```

## Requisitos Importantes

1. **La URL debe ser accesible**: La API debe poder acceder a la URL que le proporciones. Si tu aplicación PHP está en `localhost:8000`, asegúrate de que la API pueda alcanzarla.

2. **La página debe tener un div con class="content"**: La API extrae el contenido del `<div class="content">` de la página. Asegúrate de que tu página HTML tenga este elemento.

3. **Timeout**: La API tiene un timeout de 30 segundos para obtener la página. Si tu página tarda más en cargar, puede fallar.

4. **CORS (si es necesario)**: Si la API está en un dominio diferente, puede que necesites configurar CORS en la API.

## Manejo de Errores

La API puede devolver los siguientes códigos de error:

- **400**: Error al obtener la URL (la URL no es accesible o hay un error HTTP)
- **404**: No se encontró un div con class='content' en la página
- **500**: Error al convertir HTML a PDF

Ejemplo de manejo de errores:

```php
$pdf = generarPDFDesdeURL($url);

if ($pdf === false) {
    // Manejar el error
    http_response_code(500);
    echo json_encode(['error' => 'No se pudo generar el PDF']);
    exit;
}

// Si todo está bien, enviar el PDF
header('Content-Type: application/pdf');
echo $pdf;
```

## Notas Adicionales

- El PDF se genera en formato A4
- El contenido se ajusta automáticamente para caber en una sola página
- Los estilos CSS de la página original se preservan en la medida de lo posible
- La API extrae solo el contenido del `<div class="content">`, ignorando headers, footers y otros elementos

