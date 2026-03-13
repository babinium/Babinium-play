import sys
import os

# Prioritize local venv packages to use updated yt-dlp
venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv', 'lib', 'python3.12', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

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
