import tracemalloc
import gc
import sys
import os

# Agregamos la ruta del proyecto actual
sys.path.append('/home/babinium/Documentos/Babinium-play')
from youtube_engine import YouTubeEngine

def test_engine_leak():
    print("--- Probando YouTubeEngine ---")
    tracemalloc.start()
    
    gc.collect()
    print("1. Memoria Base:", tracemalloc.get_traced_memory())
    
    engine = YouTubeEngine()
    
    print("2. Despues de instanciar Engine:", tracemalloc.get_traced_memory())
    
    print("Realizando Búsqueda 1...")
    res1 = engine.search_videos("linux", max_results=20)
    print("3. Despues de Busqueda 1:", tracemalloc.get_traced_memory())
    
    snapshot1 = tracemalloc.take_snapshot()
    
    print("Realizando Búsqueda 2...")
    res2 = engine.search_videos("python programacion", max_results=20)
    print("4. Despues de Busqueda 2:", tracemalloc.get_traced_memory())
    
    print("Realizando Búsqueda 3...")
    res3 = engine.search_videos("musica relax", max_results=20)
    print("5. Despues de Busqueda 3:", tracemalloc.get_traced_memory())
    
    snapshot2 = tracemalloc.take_snapshot()
    
    print("Diferencias principales en memoria entre B1 y B3:")
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    for stat in top_stats[:10]:
        print(stat)
        
    # Limpiando variables fuertes
    del res1, res2, res3
    gc.collect()
    print("6. Despues de borrar resultados y GC:", tracemalloc.get_traced_memory())
    
    tracemalloc.stop()

if __name__ == "__main__":
    test_engine_leak()
