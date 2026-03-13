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
        # Create or ensure socket doesn't collide
        socket_path = "/tmp/babinium_mpv_ipc"
        try:
            if os.path.exists(socket_path):
                os.remove(socket_path)
        except Exception:
            pass
            
        # mpv command optimizado para hardware viejo y enlaces directos
        cmd = [
            "mpv",
            "--ytdl=no",
            "--title=Babinium Play - Reproduciendo",
            "--no-video-unscaled",
            "--cache=yes",
            "--demuxer-max-bytes=20M", 
            "--demuxer-max-back-bytes=10M",
            f"--input-ipc-server={socket_path}"
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
        
        # Escribir comando en el log para depuración y cerrarlo enseguida
        with open(log_file, "a") as f:
            f.write(f"\n--- Iniciando reproducción directa ---\n")
            f.write(f"Comando: {' '.join(cmd)}\n")

        # Iniciar como proceso separado, pero vinculado a la sesión actual
        # Usamos DEVNULL para evitar un memory leak en los buffers stdout y stderr del proceso mpv.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return process
    except Exception as e:
        print(f"Error al iniciar mpv: {e}")
        return False

def send_mpv_command(command_dict):
    """
    Envía un comando JSON IPC al socket de mpv.
    Ejemplo: {"command": ["quit"]}
    """
    socket_path = "/tmp/babinium_mpv_ipc"
    if not os.path.exists(socket_path):
        return False
        
    try:
        import socket
        import json
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(socket_path)
        message = json.dumps(command_dict) + "\n"
        client.sendall(message.encode('utf-8'))
        client.close()
        return True
    except Exception as e:
        print(f"Error enviando comando a mpv: {e}")
        return False
