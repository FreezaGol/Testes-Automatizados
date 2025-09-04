# test_find_dialog_after_f2.py
import time
import logging
from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração do Teste ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "win32"

# --- Seletores (copiados do seu config.json) ---
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_16P9c000000"
}
# Use o seletor que você descobriu para a janela de inclusão de DAV
dav_inclusion_selector = {
    "title": "Consulta de Pedidos - Documento Auxiliar de vendas", # Exemplo, ajuste se necessário
}

# --- Lógica do Teste ---
if __name__ == "__main__":
    print("\n--- INICIANDO TESTE DE DIAGNÓSTICO DE DIÁLOGO ---")
    print("\n==> AÇÃO NECESSÁRIA:")
    print("    1. Abra a aplicação Guardian e faça o login.")
    print("    2. Deixe a aplicação na tela principal.")
    print("    3. O teste começará em 5 segundos...")
    time.sleep(5)

    try:
        desktop = Desktop(backend=backend)

        # 1. Encontrar a janela principal
        logging.info("Procurando pela janela principal...")
        main_window = desktop.window(**main_window_selector)
        if not main_window.exists():
            raise ElementNotFoundError("Janela Principal não foi encontrada.")
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # 2. Navegar até a tela de inclusão de DAV
        logging.info("Navegando para a tela de vendas (ALT+V, ENTER)...")
        main_window.type_keys('%V')
        time.sleep(1)
        main_window.type_keys('{ENTER}')
        time.sleep(2)

        # 3. Encontrar a janela de DAV e pressionar F2
        logging.info("Procurando pela janela de inclusão de DAV...")
        dav_window = main_window.child_window(**dav_inclusion_selector)
        if not dav_window.exists():
            raise ElementNotFoundError("Janela de Inclusão de DAV não encontrada.")
        dav_window.set_focus()
        logging.info("-> Janela de inclusão de DAV encontrada. Pressionando F2...")
        dav_window.type_keys('{F2}')

        # --- DIAGNÓSTICO FINAL ---
        logging.info("!!! DIAGNÓSTICO: Pausando por 3 segundos para o diálogo aparecer...")
        time.sleep(3)

        logging.info("!!! DIAGNÓSTICO: Listando TODAS as janelas visíveis no Desktop...")
        all_windows = desktop.windows()

        found_something = False
        print("\n--- LISTA DE JANELAS ENCONTRADAS ---")
        for w in all_windows:
            if w.is_visible() and w.window_text():
                print(f"  -> Título: '{w.window_text()}', Classe: '{w.class_name()}'")
                found_something = True

        if not found_something:
            print("  -> Nenhuma janela com título visível foi encontrada.")

        logging.info("!!! DIAGNÓSTICO: Fim da inspeção.")

    except Exception as e:
        logging.error(f"O teste falhou: {e}", exc_info=True)

    print("\n--- TESTE FINALIZADO ---")
    input("Pressione Enter para sair.")