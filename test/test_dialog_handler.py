# test_dialog_with_keystroke.py
import time
import logging
from pywinauto import Desktop, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração do Teste ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "win32"

# --- ▼▼▼ VERIFIQUE SE ESTES SELETORES ESTÃO ATUALIZADOS ▼▼▼ ---
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_39c000000"
}
dav_inclusion_selector = {
    "title": "Consulta de Pedidos - Documento Auxiliar de vendas", # Exemplo, ajuste
}
dialog_selector = {
    "title": "Confirmação",
    "class_name": "#32770"
}
# --- ▲▲▲ FIM DOS SELETORES ▲▲▲ ---

def find_and_send_keystroke_to_dialog(dialog_selector, keystroke, timeout=1):
    """
    Procura por um diálogo de nível principal e envia uma combinação de teclas para ele.
    """
    try:
        logging.info(f"Procurando pelo diálogo de nível principal com seletor: {dialog_selector}")
        desktop = Desktop(backend=backend)
        dialog = desktop.window(**dialog_selector)
        dialog.wait('visible', timeout=timeout)
        logging.info(f"✅ SUCESSO! Diálogo '{dialog_selector.get('title')}' encontrado.")

        # Foca na janela de diálogo e envia a combinação de teclas
        dialog.set_focus()
        logging.info(f"Enviando a combinação de teclas: '{keystroke}'...")
        dialog.type_keys(keystroke)
        logging.info("   -> Combinação de teclas enviada com sucesso.")
        return True

    except (ElementNotFoundError, timings.TimeoutError):
        logging.error("❌ FALHA: O diálogo não foi encontrado no tempo esperado.")
        return False
    except Exception as e:
        logging.error(f"❌ FALHA: Ocorreu um erro inesperado: {e}")
        return False

# --- Lógica Principal do Teste ---
if __name__ == "__main__":
    print("\n--- INICIANDO TESTE DE DIÁLOGO COM ENVIO DE TECLAS (ALT+N) ---")
    print("\n==> AÇÃO NECESSÁRIA:")
    print("    1. Abra a aplicação Guardian e faça o login.")
    print("    2. Deixe a aplicação na tela principal.")
    print("    3. O teste começará em 5 segundos...")
    time.sleep(5)

    try:
        desktop = Desktop(backend=backend)

        # 1. Encontrar a janela principal
        logging.info("Encontrando a janela principal...")
        main_window = desktop.window(**main_window_selector)
        if not main_window.exists(): raise ElementNotFoundError("Janela Principal não foi encontrada.")
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # 2. Navegar e acionar o diálogo
        logging.info("Navegando e abrindo a janela de DAV...")
        main_window.type_keys('%V{ENTER}')
        time.sleep(2)

        dav_window = main_window.child_window(**dav_inclusion_selector)
        if not dav_window.exists(): raise ElementNotFoundError("Janela de Inclusão de DAV não encontrada.")
        dav_window.set_focus()

        logging.info("Pressionando F2 para acionar o diálogo de confirmação...")
        dav_window.type_keys('{F2}')
        time.sleep(2) # Pausa para o diálogo aparecer

        # 3. Chama a função que queremos testar
        # "%n" é a forma como pywinauto representa a combinação ALT+N
        find_and_send_keystroke_to_dialog(dialog_selector, "%n")

    except Exception as e:
        logging.error(f"O teste falhou: {e}", exc_info=True)

    print("\n--- TESTE FINALIZADO ---")
    input("Pressione Enter para sair.")