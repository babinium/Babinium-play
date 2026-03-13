import tkinter as tk
import urllib.request
import io
from PIL import Image, ImageTk

def test_load_image():
    root = tk.Tk()
    label = tk.Label(root, text="Cargando...")
    label.pack()

    url = 'https://i.ytimg.com/vi/fgQKO6GhJtA/hq720_custom_1.jpg?sqp=CJya0c0G-oaymwEcCOgCEMoBSFXyq4qpAw4IARUAAIhCGAFwAcABBg==&rs=AOn4CLAjyxAiIno-hCmvVE7ndIVjQOHVuA'
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as raw_data:
            img_data = raw_data.read()
        print(f"Bytes bajados: {len(img_data)}")
        with Image.open(io.BytesIO(img_data)) as image:
            image.thumbnail((160, 90), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            print("Photoimage creada")
            label.config(image=photo, text="")
            label.image = photo
    except Exception as e:
        print(f"Error asincrono en carga de imagen: {e}")
        
    root.after(2000, root.destroy)
    root.mainloop()

if __name__ == "__main__":
    test_load_image()
