# Despliegue en Railway

Este proyecto está configurado para desplegarse en Railway.

## Archivos de configuración

- `Procfile`: Define el comando de inicio
- `start.sh`: Script que instala Playwright y inicia la aplicación
- `nixpacks.toml`: Configuración de Nixpacks para Railway
- `railway.json`: Configuración adicional de Railway
- `.railwayignore`: Archivos a ignorar durante el despliegue

## Pasos para desplegar

1. **Crear cuenta en Railway**
   - Ve a [railway.app](https://railway.app)
   - Crea una cuenta o inicia sesión

2. **Crear un nuevo proyecto**
   - Haz clic en "New Project"
   - Selecciona "Deploy from GitHub repo" (si tienes el código en GitHub)
   - O selecciona "Empty Project" y luego conecta tu repositorio

3. **Configurar el proyecto**
   - Railway detectará automáticamente que es un proyecto Python
   - Usará el `Procfile` para iniciar la aplicación
   - Instalará las dependencias de `requirements.txt`

4. **Variables de entorno (opcional)**
   - Railway configurará automáticamente el puerto con la variable `PORT`
   - No necesitas configurar variables adicionales

5. **Desplegar**
   - Railway desplegará automáticamente cuando hagas push a tu repositorio
   - O puedes hacer clic en "Deploy" manualmente

## Notas importantes

- **Playwright**: El script `start.sh` instala automáticamente Chromium y sus dependencias
- **Puerto**: Railway proporciona automáticamente la variable `PORT`, la aplicación la usa
- **Tiempo de construcción**: La primera vez puede tardar varios minutos debido a la instalación de Playwright

## Verificar el despliegue

Una vez desplegado, Railway te proporcionará una URL. Puedes verificar que funciona visitando:
- `https://tu-url.railway.app/` - Debería mostrar la información de la API
- `https://tu-url.railway.app/docs` - Documentación interactiva de la API

## Solución de problemas

Si el despliegue falla:
1. Verifica los logs en Railway
2. Asegúrate de que `requirements.txt` esté actualizado
3. Verifica que el script `start.sh` tenga permisos de ejecución
4. Revisa que Playwright se esté instalando correctamente

