# inspect_children.py (versão final)
from pywinauto import Application

# O seletor da sua janela principal que sabemos que funciona
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_39c000000"
}
backend = "win32"

print("--- INICIANDO INSPEÇÃO DE CONTROLES FILHOS ---")
print("A aplicação 'Guardian' deve estar aberta na tela de login.")

try:
    # Conecta à aplicação que já está rodando
    app = Application(backend=backend).connect(**main_window_selector)

    # Seleciona a janela principal
    main_win = app.window(**main_window_selector)

    print("\n[+] Mapa de todos os controles dentro da Janela Principal:\n")
    
    # O comando mágico: imprime todos os controles filhos e suas propriedades
    # como o backend 'win32' os enxerga.
    main_win.print_control_identifiers()
    
except Exception as e:
    print(f"\n❌ FALHA: Ocorreu um erro: {e}")

print("\n--- INSPEÇÃO FINALIZADA ---")
input("Pressione Enter para sair.")