import yt_dlp
import datetime
import csv
import os

class YouTubeEngine:
    def __init__(self):
        # yt-dlp basic options para extraer metadata sin descargar el video
        self.ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'http_headers': {
                'Accept-Language': 'es-419,es;q=0.9'
            }
        }

    def search_videos(self, query, max_results=10, offset=0):
        """
        Busca videos usando yt-dlp usando ytsearch.
        Permite usar 'offset' para simular paginación trayendo más desde el inicio y recortando.
        """
        import urllib.parse
        # Pedimos el doble para compensar los que filtramos (sin miniatura, etc)
        total_needed = (offset + max_results) * 2
        
        opts = dict(self.ydl_opts)
        opts['playlistend'] = total_needed
        
        encoded_query = urllib.parse.quote(query)
        search_query = f"https://www.youtube.com/results?search_query={encoded_query}&hl=es-419&gl=US"
            
        results = []
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(search_query, download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            # Filtrar para asegurar que es un video o una lista de reproducción
                            url = entry.get('url', '')
                            is_video = '/watch?' in url or '/shorts/' in url
                            is_playlist = '/playlist?' in url or (entry.get('_type') == 'playlist' and 'list=' in url)

                            if not (is_video or is_playlist):
                                continue
                            
                            # Si es un playlist que no tiene id en la url, intentar sacar el id de 'list='
                            import urllib.parse as up
                            p_id = entry.get('id')
                            if is_playlist and 'list=' in url:
                                qs = up.parse_qs(up.urlparse(url).query)
                                if 'list' in qs:
                                    p_id = qs['list'][0]
                                    
                            item_type = 'playlist' if is_playlist else 'video'
                                
                            thumbnail = self.get_best_thumbnail(entry.get('thumbnails', []))
                            if thumbnail:
                                item = {
                                    'id': p_id if is_playlist else entry.get('id'),
                                    'title': entry.get('title', 'Sin titulo'),
                                    'url': url,
                                    'duration': self.format_duration(entry.get('duration', 0)),
                                    'thumbnail': thumbnail,
                                    'uploader': entry.get('uploader', 'Canal desconocido'),
                                    'upload_date': self.format_date(entry.get('upload_date')),
                                    'type': item_type,
                                    'playlist_count': entry.get('n_entries') or entry.get('playlist_count') or entry.get('item_count') or 0
                                }
                                results.append(item)
            except Exception as e:
                print(f"Error en yt-dlp: {e}")
                
        # Retornamos solo los elementos desde el offset pedido hasta el final del paquete
        return results[offset:offset+max_results]

    def format_duration(self, seconds):
        if not seconds:
            return "N/A"
        return str(datetime.timedelta(seconds=int(seconds)))
        
    def format_date(self, val):
        try:
            # Si es timestamp numerico (epoch)
            if isinstance(val, (int, float)):
                return datetime.datetime.fromtimestamp(val).strftime('%d/%m/%Y')
            # Si es string YYYYMMDD
            elif isinstance(val, str) and len(val) == 8 and val.isdigit():
                return f"{val[6:8]}/{val[4:6]}/{val[0:4]}"
        except Exception:
            pass
        return "Fecha desconocida"

    def get_best_thumbnail(self, thumbnails):
        """
        Para 1GB de RAM, no queremos la miniatura 4K.
        Buscamos una resolucion cercana a 480x360 o 320x180 (hqdefault / mqdefault)
        """
        if not thumbnails:
            return None
        
        # Buscar algo cercano a width 320-480
        for tb in reversed(thumbnails):
            width = tb.get('width', 0)
            if width and 200 <= width <= 480:
                return tb.get('url')
                
        # Si no, devolver la mas chica
        return thumbnails[0].get('url')

    def parse_subscription_csv(self, file_path):
        """
        Lee el CSV exportado de Google Takeout y devuelve una lista de (Canal, URL)
        """
        channels = []
        if not os.path.exists(file_path):
            return channels
            
        try:
            # Usar utf-8-sig para manejar el BOM de archivos Windows/Google
            with open(file_path, newline='', encoding='utf-8-sig') as csvfile:
                # Intentamos detectar el delimitador (coma o punto y coma)
                sample = csvfile.read(2048) # Leer un poco más para estar seguros
                csvfile.seek(0)
                sniffer = csv.Sniffer()
                try:
                    dialect = sniffer.sniff(sample, delimiters=',;\t')
                except Exception:
                    dialect = 'excel'
                
                reader = csv.DictReader(csvfile, dialect=dialect)
                
                # Normalizamos las llaves (headers) para evitar problemas de espacios
                # o diferencias de mayúsculas/minúsculas
                for row in reader:
                    # Limpiar llaves y valores
                    clean_row = {str(k).strip(): str(v).strip() for k, v in row.items()}
                    
                    # Buscamos variaciones comunes de los nombres de columna
                    url = clean_row.get('Channel Url') or clean_row.get('URL del canal') or clean_row.get('Channel URL')
                    title = clean_row.get('Channel Title') or clean_row.get('Título del canal') or clean_row.get('Channel Name')
                    
                    if url:
                        channels.append({'title': title or 'Desconocido', 'url': url})
        except Exception as e:
            print(f"Error parseando CSV robusto: {e}")
            
        return channels
        
    def get_channel_videos(self, channel_url, max_results=5):
        """
        Obtiene los videos recientes de un canal especifico
        """
        results = []
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            try:
                # Usar url/videos para playlist de tab de videos
                info = ydl.extract_info(f"{channel_url}/videos", download=False)
                if 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if i >= max_results:
                            break
                        if entry:
                            # Filtrar canales/listas accidentales
                            url = entry.get('url', '')
                            if '/watch?' not in url and '/shorts/' not in url:
                                continue
                                
                            thumbnail = self.get_best_thumbnail(entry.get('thumbnails', []))
                            if thumbnail:
                                item = {
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Sin titulo'),
                                    'url': entry.get('url'),
                                    'duration': self.format_duration(entry.get('duration', 0)),
                                    'thumbnail': thumbnail,
                                    'uploader': entry.get('uploader', 'Canal desconocido'),
                                    'upload_date': self.format_date(entry.get('timestamp') or entry.get('upload_date'))
                                }
                                results.append(item)
            except Exception as e:
                print(f"Error yt-dlp (channel): {e}")
        return results

    def get_playlist_videos(self, playlist_url, max_results=100):
        """
        Obtiene los videos de una lista de reproducción específica.
        """
        results = []
        opts = dict(self.ydl_opts)
        opts['extract_flat'] = True  # Solo queremos metadata rápida
        opts['playlistend'] = max_results
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(playlist_url, download=False)
                if 'entries' in info:
                    for i, entry in enumerate(info['entries']):
                        if entry:
                            url = entry.get('url', '')
                            if '/watch?' not in url and '/shorts/' not in url:
                                continue
                                
                            # En listas, a veces no hay 'thumbnails' detallado, probamos variantes
                            thumbnails = entry.get('thumbnails', [])
                            thumbnail = self.get_best_thumbnail(thumbnails)
                            if not thumbnail and 'id' in entry:
                                thumbnail = f"https://i.ytimg.com/vi/{entry['id']}/hqdefault.jpg"
                                
                            if thumbnail:
                                item = {
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Sin titulo'),
                                    'url': url,
                                    'duration': self.format_duration(entry.get('duration', 0)),
                                    'thumbnail': thumbnail,
                                    'uploader': entry.get('uploader') or info.get('uploader', 'Canal desconocido'),
                                    'upload_date': self.format_date(entry.get('timestamp') or entry.get('upload_date')),
                                    'type': 'video'
                                }
                                results.append(item)
            except Exception as e:
                print(f"Error extrayendo playlist (yt-dlp): {e}")
                
        return results

    def get_latest_video_if_today(self, channel_url):
        """
        Extrae solo el último video del canal y verifica si es de hoy.
        """
        today_str = datetime.datetime.now().strftime("%Y%m%d")
        opts = dict(self.ydl_opts)
        opts['extract_flat'] = False # Necesario para el upload_date confiable
        opts['playlist_items'] = '1,2' # Revisamos los 2 primeros por seguridad
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(f"{channel_url}/videos", download=False)
                if 'entries' in info and len(info['entries']) > 0:
                    for entry in info['entries']:
                        if not entry: continue
                        
                        # Validar que es un video (revisar url y webpage_url)
                        url = entry.get('url') or entry.get('webpage_url') or ''
                        if '/watch?' not in url and '/shorts/' not in url:
                            continue
                            
                        u_date = entry.get('upload_date')
                        # Si coincide con hoy, lo devolvemos (solo si tiene miniatura)
                        if u_date == today_str:
                            thumbnail = self.get_best_thumbnail(entry.get('thumbnails', []))
                            if thumbnail:
                                return {
                                    'id': entry.get('id'),
                                    'title': entry.get('title', 'Sin titulo'),
                                    'url': url,
                                    'duration': self.format_duration(entry.get('duration', 0)),
                                    'thumbnail': thumbnail,
                                    'uploader': entry.get('uploader', 'Canal desconocido'),
                                    'upload_date': self.format_date(u_date)
                                }
            except Exception as e:
                print(f"Error checking channel {channel_url}: {e}")
        return None

    def get_stream_url(self, video_url, quality="360"):
        """
        Extrae el enlace directo de reproducción.
        Soporta DASH (video+audio separado) para permitir todas las resoluciones.
        Retorna un dict con { 'video': url, 'audio': url_audio o None }
        """
        q = str(quality).replace("p", "")
        # Formato: 
        # 1. Video MP4 (avc1) <= q + Audio M4A (mp4a) -> para maxima compatibilidad en hardware viejo
        # 2. Cualquier video <= q + mejor audio
        # 3. Formato unico best <= q (como fallback o lives)
        ytdl_format = f"bestvideo[height<={q}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={q}]+bestaudio/best[height<={q}]/best"
        
        opts = {
            'format': ytdl_format,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(video_url, download=False)
                
                # Obtener headers si existen, para evitar error 403 en mpv
                headers = info.get('http_headers', {})
                
                # Si yt-dlp combinó dos formatos (video + audio por separado)
                if 'requested_formats' in info and len(info['requested_formats']) >= 2:
                    return {
                        'video': info['requested_formats'][0]['url'],
                        'audio': info['requested_formats'][1]['url'],
                        'headers': info['requested_formats'][0].get('http_headers') or headers
                    }
                
                # Si es un formato único (como en directos o formatos viejos)
                return {
                    'video': info.get('url'),
                    'audio': None,
                    'headers': headers
                }
            except Exception as e:
                print(f"Error extrayendo stream URL: {e}")
                return None
