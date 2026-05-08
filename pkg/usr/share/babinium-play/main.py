import sys
import os
import glob

# Prioritize local venv packages to use updated yt-dlp
base_dir = os.path.dirname(os.path.abspath(__file__))
venv_paths = glob.glob(os.path.join(base_dir, 'venv', 'lib', 'python*', 'site-packages'))
if venv_paths:
    sys.path.insert(0, sorted(venv_paths, reverse=True)[0])

import tkinter as tk
from gui import BatubeApp
def main():
    root = tk.Tk()
    app = BatubeApp(root)
    
    # Prevenir que la ventana consuma demasiados recursos redimensionando como loca
    root.minsize(800, 600)
    
    # Manejar el loop principal
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nSaliendo...")

if __name__ == "__main__":
    main()
