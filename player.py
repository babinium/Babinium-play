import subprocess
import os

def play_video(stream_data, quality="360"):
    """
    Inicia mpv en un nuevo proceso y reproduce el enlace directo.
    stream_data puede ser un dict (DASH) o un string (URL directa).
    """
    try:
        headers = None
        if isinstance(stream_data, dict):
            video_url = stream_data.get('video')
            audio_url = stream_data.get('audio')
            headers = stream_data.get('headers')
        else:
            video_url = stream_data
            audio_url = None

        if not video_url:
            return False

        # Log path
        log_file = "/tmp/babinium-play-mpv.log"
        
        # mpv command optimizado para hardware viejo y enlaces directos
        cmd = [
            "mpv",
            "--ytdl=no",
            "--title=Babinium Play - Reproduciendo",
            "--no-video-unscaled",
            "--cache=yes",
            "--demuxer-max-bytes=20M", 
            "--demuxer-max-back-bytes=10M"
        ]

        if headers:
            for k, v in headers.items():
                if k.lower() == 'user-agent':
                    cmd.append(f"--user-agent={v}")
                else:
                    cmd.append(f"--http-header-fields-append={k}: {v}")

        if audio_url:
            cmd.append(f"--audio-file={audio_url}")
        
        cmd.append(video_url)
        
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
