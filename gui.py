import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import io
import requests
import urllib.request
import re
from PIL import Image, ImageTk
import os
import shutil
import pathlib
from youtube_engine import YouTubeEngine
from player import play_video

class BatubeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Babinium Play")
        self.root.geometry("850x600")
        
        # Engine
        self.engine = YouTubeEngine()
        
        # State
        self.result_frames: list[tk.Frame] = []
        self.selected_index: int = -1
        self.is_playing: bool = False
        self.playing_frame: tk.Frame | None = None
        
        # Paginación
        self.current_query: str = ""
        self.current_offset: int = 0
        self.results_per_page: int = 10
        self.all_subs_channels: list[dict] = []
        self.current_sub_idx: int = 0
        self.subscription_file: str | None = None
        
        # Elementos UI principales declarados con hints
        self.subs_btn: tk.Button | None = None
        self.progress_frame: tk.Frame | None = None
        self.progress: ttk.Progressbar | None = None
        self.load_more_btn: tk.Button | None = None
        self.search_entry: tk.Entry | None = None
        self.search_entry_name: str = ""
        self.import_btn: tk.Button | None = None
        self.canvas: tk.Canvas | None = None
        self.scrollbar: tk.Scrollbar | None = None
        self.scrollable_frame: tk.Frame | None = None
        self.status_bar: tk.Label | None = None
        
        # Variables de control de UI (deben estar antes de setup_ui)
        self.search_var: tk.StringVar = tk.StringVar()
        self.quality_var: tk.StringVar = tk.StringVar(value="360p")
        self.status_var: tk.StringVar = tk.StringVar(value="Listo")
        
        # Colores Tema Oscuro Pastel
        self.bg_main = "#2b2b36"       # Fondo principal oscuro suave
        self.bg_panel = "#383846"      # Paneles y frames de contenido
        self.fg_text = "#e3e3e8"       # Texto claro principal
        self.fg_muted = "#a5a5b4"      # Texto secundario/apagado
        self.bg_entry = "#424254"      # Fondo de las cajas de texto
        self.bg_button = "#5a5a72"     # Fondo botones interactivos
        self.bg_select = "#4c4c6d"     # Resalte seleccionados
        self.bg_playing = "#cfa85e"    # Amarillo pastel oscuro para video cargando
        self.fg_playing = "#1c1c24"    # Texto oscuro sobre el amarillo
        
        self.root.config(bg=self.bg_main)
        
        # Variables globales de control
        self.image_cache = []
        self.config_dir = os.path.join(pathlib.Path.home(), ".config", "babinium-play")
        os.makedirs(self.config_dir, exist_ok=True)
        self.persist_file = os.path.join(self.config_dir, "subscriptions.csv")
        
        # UI Setup
        self.setup_ui()
        
        # Le decimos al linter (Pyre) que después de setup_ui todos estos ya no son None
        assert self.subs_btn is not None
        assert self.import_btn is not None
        assert self.canvas is not None
        assert self.scrollbar is not None
        assert self.scrollable_frame is not None
        assert self.progress is not None
        assert self.progress_frame is not None
        assert self.status_bar is not None
        assert self.search_entry is not None
        
        # Cargar suscripciones previas si existen
        self.check_saved_subscriptions()
        
        # Bindings globales de teclado (Flechas)
        self.root.bind("<Up>", self.nav_up)
        self.root.bind("<Down>", self.nav_down)
        
        # El Enter se manejará a nivel de Frame/Canvas para evitar robar eventos del Entry
        # self.root.bind("<Return>", self.handle_enter)

    def check_saved_subscriptions(self):
        """Si existe el archivo persistido, lo cargamos"""
        if os.path.exists(self.persist_file):
            print(f"Cargando suscripciones persistidas desde: {self.persist_file}")
            threading.Thread(target=self._async_import_subs, args=(self.persist_file,), daemon=True).start()

    def setup_ui(self):
        # Top Frame for search and controls
        top_frame = tk.Frame(self.root, padx=5, pady=5, bg=self.bg_main)
        top_frame.pack(fill=tk.X)
        
        # Row 1: Search and Filters
        row1 = tk.Frame(top_frame, bg=self.bg_main)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        # Search Bar
        self.search_entry = tk.Entry(row1, textvariable=self.search_var, width=30, bg=self.bg_entry, fg=self.fg_text, insertbackground=self.fg_text, relief=tk.FLAT)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<Return>', self.search_from_entry)
        self.search_entry_name = str(self.search_entry)
        
        search_btn = tk.Button(row1, text="Buscar", command=self.do_search, bg=self.bg_button, fg=self.fg_text, relief=tk.FLAT, activebackground=self.bg_select, activeforeground=self.fg_text)
        search_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Row 2: Quality and Subscriptions
        row2 = tk.Frame(top_frame, bg=self.bg_main)
        row2.pack(fill=tk.X)
        
        # Quality Selector
        quality_frame = tk.Frame(row2, bg=self.bg_main)
        quality_frame.pack(side=tk.LEFT)
        tk.Label(quality_frame, text="Calidad:", bg=self.bg_main, fg=self.fg_text).pack(side=tk.LEFT)
        
        tk.Label(row2, text="Calidad:", bg=self.bg_main, fg=self.fg_muted).pack(side=tk.LEFT, padx=(0, 5))
        quality_combo = ttk.Combobox(row2, textvariable=self.quality_var, values=["144", "240", "360", "480", "720", "1080"], width=5, state="readonly")
        quality_combo.pack(side=tk.LEFT, padx=(0, 15))
        
        # Subscriptions Controls
        subs_controls = tk.Frame(row2, bg=self.bg_main)
        subs_controls.pack(side=tk.LEFT, padx=10)
        
        self.subs_btn = tk.Button(subs_controls, text="Actualizar Hoy", command=self.load_subscriptions, bg=self.bg_button, fg=self.fg_text, relief=tk.FLAT, activebackground=self.bg_select, activeforeground=self.fg_text)
        self.subs_btn.pack(side=tk.LEFT, padx=2)
        
        self.import_btn = tk.Button(subs_controls, text="Importar CSV", command=self.import_new_csv, bg=self.bg_panel, fg=self.fg_muted, relief=tk.FLAT, activebackground=self.bg_select, activeforeground=self.fg_text)
        self.import_btn.pack(side=tk.RIGHT, padx=10)
        
        # Barra Inferior para Status y Progress, justo debajo de controles
        bottom_bar = tk.Frame(top_frame, bg=self.bg_panel)
        bottom_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.status_bar = tk.Label(bottom_bar, textvariable=self.status_var, bd=0, anchor=tk.W, bg=self.bg_panel, fg=self.fg_muted, padx=10, pady=2)
        if self.status_bar:
            self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
        self.progress_frame = tk.Frame(bottom_bar, bg=self.bg_panel)
        # Siempre mostramos el frame de progreso a la derecha
        self.progress_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=150, mode='determinate')
        if self.progress and self.progress_frame:
            self.progress.pack(side=tk.RIGHT, padx=10, pady=2)
            
        # Center Frame for results (Scrollable)
        self.canvas = tk.Canvas(self.root, bg=self.bg_main, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        # Hacemos que el frame scrolleable comparta el color de fondo principal
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_main)

        if self.canvas and self.scrollbar and self.scrollable_frame:
            self.scrollable_frame.bind(
                "<Configure>",
                lambda e: self.canvas.configure(
                    scrollregion=self.canvas.bbox("all")
                )
            )

            # Insertamos con anchor "n" (North/Arriba al Medio)
            self.canvas_window = self.canvas.create_window((self.canvas.winfo_width()/2, 0), window=self.scrollable_frame, anchor="n")
            
            # Cada vez que el Canvas cambie de tamaño, ajustamos la posición X del frame al medio del Canvas
            def _on_canvas_configure(event):
                if self.canvas and self.canvas_window:
                    self.canvas.coords(self.canvas_window, (event.width / 2, 0))
                    
            self.canvas.bind("<Configure>", _on_canvas_configure)

            self.canvas.configure(yscrollcommand=self.scrollbar.set)

            self.canvas.pack(side="left", fill="both", expand=True)
            self.scrollbar.pack(side="right", fill="y")
        
        # Mouse Wheel Binding para scroll
        if self.canvas:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            # Para Linux (X11) usa Button-4 y Button-5
            self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _on_mousewheel(self, event):
        # Desplazamiento normal (Windows/MacOS)
        if self.canvas:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def _on_mousewheel_linux(self, event):
        # Desplazamiento en Linux
        if self.canvas:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def nav_up(self, event):
        if not self.result_frames or self.selected_index <= 0:
            return
        self.update_selection(self.selected_index - 1)
        self.ensure_visible()

    def nav_down(self, event):
        max_idx = len(self.result_frames) if (hasattr(self, 'load_more_btn') and self.load_more_btn) else len(self.result_frames) - 1
        if not self.result_frames or self.selected_index >= max_idx:
            return
        self.update_selection(self.selected_index + 1)
        self.ensure_visible()

    def update_selection(self, new_index):
        # Deselect old
        if 0 <= self.selected_index < len(self.result_frames):
            old_frame = self.result_frames[self.selected_index]['frame']
            # Conservar color amarillo si es el marco reproductor actual
            bg_color = self.bg_playing if old_frame == getattr(self, 'playing_frame', None) else self.bg_panel
            old_frame.config(borderwidth=1, relief=tk.FLAT, bg=bg_color)
        elif hasattr(self, 'load_more_btn') and self.load_more_btn and self.selected_index == len(self.result_frames):
            self.load_more_btn.config(relief=tk.FLAT, bg=self.bg_button)
            
        # Select new
        self.selected_index = new_index
        if 0 <= self.selected_index < len(self.result_frames):
            new_frame = self.result_frames[self.selected_index]['frame']
            # Conservar color amarillo si es el marco reproductor actual
            bg_color = self.bg_playing if new_frame == getattr(self, 'playing_frame', None) else self.bg_select
            new_frame.config(borderwidth=1, relief=tk.SOLID, bg=bg_color) # Resaltado pastel
            new_frame.focus_set() # Obligatorio para redirigir el enter a este cuadro
        elif hasattr(self, 'load_more_btn') and self.load_more_btn and self.selected_index == len(self.result_frames):
            self.load_more_btn.config(relief=tk.SOLID, borderwidth=2, bg=self.bg_select)
            self.load_more_btn.focus_set()

    def ensure_visible(self):
        """Asegura que el ítem seleccionado con el teclado esté visible en el Canvas"""
        frame = None
        if 0 <= self.selected_index < len(self.result_frames):
            frame = self.result_frames[self.selected_index]['frame']
        elif hasattr(self, 'load_more_btn') and self.load_more_btn and self.selected_index == len(self.result_frames):
            frame = self.load_more_btn
            
        if frame and self.canvas:
            # Obtener las coordenadas relativas del frame respecto al canvas
            frame_y = frame.winfo_y()
            frame_h = frame.winfo_height()
            canvas_h = self.canvas.winfo_height()
            
            # Calcular las proporciones de scroll
            bbox = self.canvas.bbox("all")
            if not bbox: return
            total_h = bbox[3]
            
            if total_h > 0:
                # Mover si está fuera de vista por arriba
                if frame_y < self.canvas.canvasy(0):
                    self.canvas.yview_moveto(frame_y / total_h)
                # Mover si está fuera de vista por abajo
                elif (frame_y + frame_h) > self.canvas.canvasy(canvas_h):
                    self.canvas.yview_moveto((frame_y + frame_h - canvas_h) / total_h)

    def search_from_entry(self, event=None):
        self.do_search()
        return "break" # Evita que el evento suba hasta el parent (root)

    def handle_enter(self, event=None):
        # Aislado! Solo se llama si un frame de la lista tiene el foco.
        self.play_selected()
            
    def play_selected(self, event=None):
        if 0 <= self.selected_index < len(self.result_frames):
            item = self.result_frames[self.selected_index]
            self.play(item['url'], item['frame'])

    def do_search(self):
        query = self.search_var.get().strip()
        if not query:
            return
            
        if self.status_var:
            self.status_var.set("Buscando...")
        
        # Iniciar animación progress bar (ficticia para búsquedas)
        if self.progress:
            self.progress.configure(mode='indeterminate')
            self.progress.start(10)
            
        self.clear_results()
        
        # Reiniciar Estado de Paginación
        self.current_query = query
        self.current_offset = 0
        
        # Ocultar o eliminar botón "Cargar más viejos" si existe
        self._remove_load_more_btn()
        
        # Run search in thread to avoid freezing GUI
        threading.Thread(target=self._async_search, args=(query, 0), daemon=True).start()
        
    def load_more(self):
        if not self.current_query:
            return
            
        if self.status_var:
            self.status_var.set("Cargando más videos...")
            
        # Iniciar animación progress bar (ficticia para búsquedas)
        if self.progress:
            self.progress.configure(mode='indeterminate')
            self.progress.start(10)
            
        self._remove_load_more_btn()
        
        # Sumamos 10 al offset
        self.current_offset += self.results_per_page
        
        # Run search in thread
        threading.Thread(target=self._async_search, args=(self.current_query, self.current_offset), daemon=True).start()

    def _async_search(self, query, offset):
        try:
            results = self.engine.search_videos(
                query, 
                max_results=20, 
                offset=offset
            )
            
            self.root.after(0, self.display_results, results, offset > 0)
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Error: {e}"))

    def load_subscriptions(self):
        # Si ya tenemos canales cargados, simplemente actualizamos
        if self.all_subs_channels:
            self._start_update_today()
        else:
            self.import_new_csv()

    def import_new_csv(self):
        # Siempre abre el diálogo de archivo
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV de suscripciones",
            filetypes=(("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*"))
        )
        if not file_path:
            return
        
        self.subscription_file = file_path
        if self.status_var:
            self.status_var.set("Importando lista de canales...")
        threading.Thread(target=self._async_import_subs, args=(file_path,), daemon=True).start()

    def _async_import_subs(self, file_path):
        try:
            channels = self.engine.parse_subscription_csv(file_path)
            if not channels:
                self.root.after(0, lambda: messagebox.showinfo("Información", "No se encontraron canales válidos."))
                if self.status_var:
                    self.root.after(0, lambda: self.status_var.set("Listo"))
                return
            
            self.all_subs_channels = channels
            
            # Persistir si no es ya el archivo de persistencia
            if file_path != self.persist_file:
                try:
                    shutil.copy2(file_path, self.persist_file)
                except Exception as e:
                    print(f"Error persistiendo suscripciones: {e}")
            
            # Se quita la actualización automática a petición del usuario.
            # Debe presionar el botón de "Actualizar Hoy" manualmente.
            if self.status_var:
                self.root.after(0, lambda: self.status_var.set(f"Suscripciones cargadas ({len(channels)} canales)."))
            
        except Exception as e:
            if self.status_var:
                self.root.after(0, lambda: self.status_var.set(f"Error importando subs: {e}"))

    def _start_update_today(self):
        self.clear_results()
        if self.status_var:
            self.status_var.set("Buscando videos de hoy...")
        if self.progress_frame and self.progress:
            self.progress['value'] = 0
            self.progress['maximum'] = len(self.all_subs_channels)
        threading.Thread(target=self._async_update_today, daemon=True).start()

    def _async_update_today(self):
        try:
            found_videos = []
            total = len(self.all_subs_channels)
            
            for i, channel in enumerate(self.all_subs_channels):
                # Actualizar progreso
                if self.progress:
                    self.root.after(0, lambda v=i+1: self.progress.configure(value=v))
                if self.status_var:
                    self.root.after(0, lambda c=channel['title']: self.status_var.set(f"Revisando ({i+1}/{total}): {c}"))
                
                video = self.engine.get_latest_video_if_today(channel['url'])
                if video:
                    found_videos.append(video)
            
            if found_videos:
                self.root.after(0, lambda: self.display_results(found_videos))
                if self.status_var:
                    self.root.after(0, lambda: self.status_var.set(f"¡Listo! Se encontraron {len(found_videos)} videos de hoy."))
            else:
                if self.status_var:
                    self.root.after(0, lambda: self.status_var.set("No hay videos nuevos hoy en tus suscripciones."))
                self.root.after(0, lambda: messagebox.showinfo("Babinium Play", "No se encontraron videos subidos el día de hoy en tus canales."))
                
        except Exception as e:
            if self.status_var:
                self.root.after(0, lambda: self.status_var.set(f"Error actualizando: {e}"))
        finally:
            # Reset progreso al terminar
            if self.progress:
                self.root.after(3000, lambda: self.progress.configure(value=0))

    def _remove_load_more_btn(self):
        if hasattr(self, 'load_more_btn') and self.load_more_btn:
            self.load_more_btn.destroy()
            self.load_more_btn = None
            
    def clear_results(self):
        self._remove_load_more_btn()
        if self.scrollable_frame:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
        self.image_cache.clear()
        self.result_frames = []
        self.selected_index = -1

    def _fetch_date_async(self, url, lbl_widget):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'es-419,es;q=0.9'
            }
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req).read().decode('utf-8')
            match = re.search(r'"publishDate":"([^"]+)"', html)
            if match:
                raw_date = match.group(1)
                # Parsear YYYY-MM-DD
                parts = raw_date.split('T')[0].split('-')
                if len(parts) == 3:
                    lbl_widget.config(text=f"Subido: {parts[2]}/{parts[1]}/{parts[0]}")
                    return
        except Exception:
            pass
        lbl_widget.config(text="Subido: Fecha desconocida")

    def display_results(self, results, append=False):
        # Detener animación de progreso si estaba corriendo
        if self.progress:
            self.progress.stop()
            self.progress.configure(mode='determinate', value=0)
            
        if not append:
            self.clear_results()
            
        if not results and not append:
            if self.status_var:
                self.status_var.set("No se encontraron resultados.")
            return

        start_idx = len(self.result_frames) # donde empezamos a guardar nuevos items

        for idx, item in enumerate(results):
            frame = tk.Frame(self.scrollable_frame, pady=5, padx=5, relief=tk.FLAT, borderwidth=1, bg=self.bg_panel)
            frame.pack(fill=tk.X, expand=True, pady=2, padx=5) # padding exterior entre items
            
            # Area miniatura
            lbl_img = tk.Label(frame, text="Sin Miniatura\n(Cargando..)", width=20, height=6, bg="#1c1c24", fg=self.fg_muted)
            lbl_img.pack(side=tk.LEFT, padx=5)
            
            if item.get('thumbnail'):
                threading.Thread(target=self._load_image_async, args=(item['thumbnail'], lbl_img), daemon=True).start()
                
            # Area info
            info_frame = tk.Frame(frame, bg=self.bg_panel)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            
            title_lbl = tk.Label(info_frame, text=item.get('title'), font=("Arial", 11, "bold"), anchor="w", justify=tk.LEFT, wraplength=400, bg=self.bg_panel, fg=self.fg_text)
            title_lbl.pack(fill=tk.X)
            
            uploader_lbl = tk.Label(info_frame, text=item.get('uploader'), font=("Arial", 9), anchor="w", bg=self.bg_panel, fg=self.fg_playing)
            uploader_lbl.pack(fill=tk.X)
            
            upload_date_lbl = tk.Label(info_frame, text="Subido: Cargando...", font=("Arial", 8), anchor="w", bg=self.bg_panel, fg=self.fg_muted)
            upload_date_lbl.pack(fill=tk.X)
            
            # Lanzamos subproceso ultra rapido para extraer fecha sin congelar interfaz
            if item.get('url'):
                threading.Thread(target=self._fetch_date_async, args=(item['url'], upload_date_lbl), daemon=True).start()
            
            duration_lbl = tk.Label(info_frame, text=f"Duración: {item.get('duration')}", font=("Arial", 8), anchor="w", bg=self.bg_panel, fg=self.fg_muted)
            duration_lbl.pack(fill=tk.X)
            
            # Guardamos la referencia para el uso del teclado
            curr_idx = start_idx + idx
            self.result_frames.append({'frame': frame, 'url': item.get('url'), 'index': curr_idx})
            
            # Añadimos los eventos de ratón
            for w in (frame, lbl_img, info_frame, title_lbl, uploader_lbl, upload_date_lbl, duration_lbl):
                w.bind("<Button-1>", lambda e, url=item.get('url'), f=frame, i=curr_idx: self.on_item_click(url, f, i))
                
            # Añadimos el evento <Return> localmente a este cuadro (si se navegó con flechas, tendrá foco)
            frame.bind("<Return>", lambda e: self.play_selected())
                
        if self.status_var:
            self.status_var.set(f"Mostrando {len(self.result_frames)} resultados.")
        
        # Botón para cargar más
        if results and len(results) >= 1:
            self._remove_load_more_btn() 
            # Botón con color llamativo (Naranja/Rojo) para asegurar que se vea en AntiX
            self.load_more_btn = tk.Button(self.scrollable_frame, text=">>> MOSTRAR MÁS VIDEOS <<<", 
                                          command=self.load_more, bg="#ff5722", fg="#ffffff", 
                                          activebackground="#e64a19", relief=tk.RAISED, borderwidth=4,
                                          font=("Arial", 12, "bold"), pady=15)
            self.load_more_btn.pack(fill=tk.X, expand=True, pady=20, padx=10)
            # Vincular Enter
            self.load_more_btn.bind("<Return>", lambda e: self.load_more())
            
        # Forzar actualización agresiva de scroll
        self.root.update_idletasks()
        # Pequeño delay de 100ms para asegurar que el motor de renderizado de AntiX se entere
        if self.canvas:
            self.root.after(100, lambda: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Seleccionar automáticamente el primero solo si es búsqueda nueva
        if self.result_frames and not append:
            self.update_selection(0)

    def on_item_click(self, url, frame, index):
        self.update_selection(index)
        self.play(url, frame)

    def _load_image_async(self, url, label_widget):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                img_data = response.content
                image = Image.open(io.BytesIO(img_data))
                image.thumbnail((160, 90))
                photo = ImageTk.PhotoImage(image)
                self.root.after(0, self._set_image, label_widget, photo)
        except Exception:
            pass

    def _set_image(self, label_widget, photo):
        self.image_cache.append(photo)
        label_widget.config(image=photo, text="", width=160, height=90)

    def play(self, url, source_frame):
        if self.is_playing:
            if self.status_var:
                self.status_var.set("Ya hay un video reproduciéndose...")
            return
            
        self.is_playing = True
        self.playing_frame = source_frame
        
        quality = self.quality_var.get()
        if self.status_var:
            self.status_var.set(f"Cargando video en mpv ({quality})...")
            
        # Animación de carga
        if self.progress:
            self.progress.configure(mode='indeterminate')
            self.progress.start(10)
        
        # Colorear recuadro de amarillo oscuro para indicar estado "Cargando"
        source_frame.config(bg=self.bg_playing)
        
        # Reproducir asincronamente para no bloquear la gui mientras arranca el proceso
        threading.Thread(target=self._async_play, args=(url, quality, source_frame), daemon=True).start()

    def _async_play(self, url, quality, source_frame):
        if self.status_var:
            self.root.after(0, lambda: self.status_var.set(f"Extrayendo enlace directo ({quality}p)..."))
        stream_data = self.engine.get_stream_url(url, quality=quality)
        
        if not stream_data or not stream_data.get('video'):
            self.root.after(0, lambda: messagebox.showerror("Error", stream_data.get('error', "No se pudo extraer el enlace del video.")))
            self.root.after(0, lambda: source_frame.config(bg=self.bg_panel))
            if self.progress:
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.progress.configure(mode='determinate', value=0))
            self.is_playing = False
            self.playing_frame = None
            return

        if self.status_var:
            self.root.after(0, lambda: self.status_var.set(f"Abriendo mpv..."))
            
        process = play_video(stream_data, quality=quality)
        
        # Detener animación cuando mpv termina de cargar/arrancar
        if self.progress:
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: self.progress.configure(mode='determinate', value=0))

        if not process:
            self.root.after(0, lambda: messagebox.showerror("Error", "No se pudo abrir mpv."))
            self.root.after(0, lambda: source_frame.config(bg=self.bg_panel)) # Restaurar a seleccionado normal
            self.is_playing = False
            self.playing_frame = None
        else:
            if self.status_var:
                self.root.after(0, lambda: self.status_var.set("Reproduciendo en mpv."))
            # Esperar a que el proceso de mpv termine
            process.wait()
            # Una vez que se cierra mpv, restaurar el color del frame en la GUI principal
            def restore_bg():
                if self.result_frames and self.selected_index >= 0 and self.selected_index < len(self.result_frames):
                    is_selected = self.result_frames[self.selected_index]['frame'] == source_frame
                    source_frame.config(bg=self.bg_select if is_selected else self.bg_panel)
                else:
                    source_frame.config(bg=self.bg_panel)
            
            self.root.after(0, restore_bg)
            
            if self.status_var:
                self.root.after(0, lambda: self.status_var.set("Listo")) 
            self.is_playing = False
            self.playing_frame = None
