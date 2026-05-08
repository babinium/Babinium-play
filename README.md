# Babinium-play

<p align="center">
  <img src="Babinium-play.png" width="48%" />
  <img src="Babinium-play2.png" width="48%" />
</p>

**Babinium-play** es un reproductor de música y videos de YouTube ligero y minimalista. Aunque está optimizado para distribuciones Linux **derivadas de Debian y Ubuntu** (como AntiX, Zorin OS Lite, Linux Mint, etc.), es compatible con otros sistemas Linux. Está diseñado para funcionar de manera eficiente incluso en equipos con recursos limitados.

## Características principales

- **Búsqueda Integrada**: Busca videos y música directamente desde la aplicación sin necesidad de abrir un navegador.
- **Mejoras en el flujo de reproducción**: Experiencia de reproducción principal más robusta y fluida.
- **Reproducción de Listas**: Capacidad de cargar y reproducir listas de reproducción (playlists) de manera continua.
- **Sección de Favoritos**: Guarda tus videos y listas de reproducción preferidas para acceder a ellos rápidamente en cualquier momento.
- **Reproducción Ligera**: Utiliza un motor optimizado para reproducir contenido de YouTube de forma fluida.
- **Interfaz Sencilla**: Una GUI intuitiva construida con Python que prioriza la velocidad y la facilidad de uso.
- **Sin Publicidad Interruptiva**: Una experiencia de visualización y escucha más limpia.

## Requisitos

Si instalas Babinium Play usando el paquete `.deb`, no necesitas instalar las dependencias manualmente. `apt` se encarga de resolverlas.

El paquete `.deb` declara estas dependencias del sistema:

- `python3`
- `python3-tk`
- `python3-pil`
- `python3-pil.imagetk`
- `mpv`
- `ca-certificates`

El paquete incluye una versión reciente de `yt-dlp` como código Python puro dentro de la aplicación. Esto evita problemas en distribuciones livianas o estables que suelen traer un `yt-dlp` viejo en sus repositorios.

## Instalación

### Opción 1: Paquete .deb (Recomendado para principiantes)
Esta es la forma más sencilla de instalar Babinium-play en sistemas basados en Debian/Ubuntu (como AntiX o Zorin OS):

1. Ve a la sección de [Releases](https://github.com/babinium/Babinium-play/releases) y descarga el archivo `.deb` más reciente.
2. Abre una terminal en la carpeta donde lo descargaste y ejecuta:
   ```bash
   sudo apt install ./babinium-play_1.2.1_all.deb
   ```
   Si el nombre del archivo cambia en una versión futura, reemplázalo por el nombre del `.deb` que descargaste.

Esto instalará automáticamente las dependencias necesarias y agregará Babinium Play al menú de aplicaciones.

### Opción 2: Desde el código fuente (Para otros sistemas o desarrolladores)
Si no utilizas una distribución basada en Debian, o si prefieres ejecutarlo manualmente, puedes usar esta opción:

1. Clona el repositorio:
   ```bash
   git clone https://github.com/babinium/Babinium-play.git
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Asegúrate de tener `mpv` y Tkinter instalados en tu sistema. En Debian/Ubuntu/AntiX:
   ```bash
   sudo apt install python3-tk python3-pil python3-pil.imagetk mpv ca-certificates
   ```
4. Ejecuta la aplicación:
   ```bash
   python main.py
   ```

---
Desarrollado por [babinium](https://github.com/babinium).
