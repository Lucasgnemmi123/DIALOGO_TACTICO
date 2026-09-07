La aplicación utiliza archivos locales y guarda las reuniones en el almacenamiento del navegador del dispositivo.

Para instalarla, servir la carpeta por HTTPS (o localhost para pruebas), abrirla una vez con conexión y esperar a que termine de instalarse el service worker. Después puede abrirse, recargarse y guardar reuniones sin internet. La primera descarga requiere conexión; borrar los datos del sitio elimina tanto la caché offline como los registros locales.

Al publicar cambios, incrementar la versión en `service-worker.js` e incluir cualquier recurso nuevo en su precaché. La instalación descarga todos los recursos antes de activar la nueva versión. Para ver una actualización ya instalada, recargar el tablero.

Logo de Aramark: https://www.aramark.com/aramark-logo.svg, descargado el 7 de septiembre de 2026 y almacenado como `aramark-logo.svg`. Se usa localmente, sin consultar el sitio de Aramark durante el uso del tablero.

Verificación: `python scripts/check-pwa.py` (requiere Playwright y Chrome instalado). Comprueba carga y navegación offline, guardado, recursos locales y disposición del encabezado.
