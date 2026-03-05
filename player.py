import subprocess
import os

def play_video(stream_url, quality="360"):
    """
    Inicia mpv en un nuevo proceso y reproduce el enlace directo.
    No bloquea la ejecución del hilo actual.
    """
    try:
        # Log path
        log_file = "/tmp/babinium-play-mpv.log"
        
        # mpv command optimizado para hardware viejo y enlaces directos
        cmd = [
            "mpv",
            # Desactivamos ytdl interno ya que pasamos el enlace directo
            "--ytdl=no",
            # Título de la ventana
            "--title=Babinium Play - Reproduciendo",
            # Optimización para hardware bajo
            "--no-video-unscaled",
            "--cache=yes",
            "--demuxer-max-bytes=20M", 
            "--demuxer-max-back-bytes=10M",
            stream_url
        ]
        
        # Escribir comando en el log para depuración
        with open(log_file, "a") as f:
            f.write(f"\n--- Iniciando reproducción directa ---\n")
            f.write(f"Comando: {' '.join(cmd)}\n")

        # Iniciar como proceso separado
        log_output = open(log_file, "a")
        process = subprocess.Popen(
            cmd,
            stdout=log_output,
            stderr=log_output,
            start_new_session=True
        )
        return process
    except Exception as e:
        print(f"Error al iniciar mpv: {e}")
        return False
