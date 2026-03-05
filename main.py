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
