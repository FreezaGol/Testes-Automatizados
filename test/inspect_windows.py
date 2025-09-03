# inspect_windows.py
import time
from pywinauto import Desktop

print("Inspecionando todas as janelas visíveis em 3 segundos...")
time.sleep(3)

print("\n--- JANELAS ENCONTRADAS ---")
desktop = Desktop(backend="win32")
for w in desktop.windows():
    if w.window_text() and w.is_visible():
        print(f"Título: '{w.window_text()}', Classe: '{w.class_name()}'")
print("\n--- FIM DA INSPEÇÃO ---")
input("Pressione Enter para sair.")