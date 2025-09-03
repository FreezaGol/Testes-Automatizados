# diagnose_dav_screen.py
import time
import logging
from pywinauto import Desktop, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração do Teste ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "win32"

# --- ▼▼▼ VERIFIQUE E AJUSTE ESTES SELETORES COM OS VALORES DO SEU selectors.json ▼▼▼ ---
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_89c000000"
}
dav_inclusion_selector = {
    "title": "Consulta de Pedidos - Documento Auxiliar de vendas", # Exemplo, ajuste se necessário
}
dialog_selector = {
    "title": "Confirmação",
    "class_name": "#32770"
}
# --- ▲▲▲ FIM DOS SELETORES ▲▲▲ ---

def handle_dialog_with_keystroke(dialog_selector, keystroke="%n", timeout=1):
    """
    Procura por um diálogo de nível principal e envia uma combinação de teclas.
    """
    try:
        desktop = Desktop(backend=backend)
        dialog = desktop.window(**dialog_selector)
        dialog.wait('visible', timeout=timeout)
        logging.info(f"Diálogo '{dialog_selector.get('title')}' encontrado. Enviando teclas...")
        dialog.set_focus()
        dialog.type_keys(keystroke)
        logging.info("-> Teclas enviadas com sucesso.")
        time.sleep(1)
    except (ElementNotFoundError, timings.TimeoutError):
        logging.info(f"Diálogo opcional '{dialog_selector.get('title')}' não apareceu.")
    except Exception as e:
        logging.warning(f"Não foi possível interagir com o diálogo opcional: {e}")

# --- Lógica Principal do Teste ---
if __name__ == "__main__":
    print("\n--- INICIANDO DIAGNÓSTICO COMPLETO DA TELA DE DAV ---")
    print("\n==> AÇÃO NECESSÁRIA:")
    print("    1. Abra a aplicação Guardian e faça o login.")
    print("    2. Deixe a aplicação na tela principal.")
    print("    3. O teste começará em 5 segundos...")
    time.sleep(5)

    try:
        desktop = Desktop(backend=backend)

        # 1. Encontrar a janela principal
        logging.info("Passo 1: Encontrando a janela principal...")
        main_window = desktop.window(**main_window_selector)
        if not main_window.exists(): raise ElementNotFoundError("Janela Principal não foi encontrada.")
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # 2. Navegar para a tela de inclusão de DAV
        logging.info("Passo 2: Navegando para a tela de vendas (ALT+V, ENTER)...")
        main_window.type_keys('%V{ENTER}')
        time.sleep(2)

        # 3. Encontrar a janela de DAV e pressionar F2
        logging.info("Passo 3: Encontrando a janela de inclusão de DAV...")
        dav_window = main_window.child_window(**dav_inclusion_selector)
        if not dav_window.exists(): raise ElementNotFoundError("Janela de Inclusão de DAV não encontrada.")
        dav_window.set_focus()
        logging.info("-> Janela de inclusão de DAV encontrada. Pressionando F2...")
        dav_window.type_keys('{F2}')
        time.sleep(1)

        # 4. Tratar a caixa de diálogo de confirmação
        logging.info("Passo 4: Verificando e tratando a caixa de diálogo de confirmação...")
        handle_dialog_with_keystroke(dialog_selector)

        # 5. DIAGNÓSTICO FINAL: Inspecionar a tela de DAV
        logging.info("Passo 5: A tela de DAV deve estar pronta. Inspecionando todos os seus controles...")
        time.sleep(1) # Pausa final para garantir que a tela está pronta
        dav_window.set_focus()

        print("\n" + "="*80)
        print(" MAPA DE CONTROLES DA TELA DE INCLUSÃO DE DAV")
        print("="*80)

        # O comando mágico: imprime todos os controles filhos da janela de DAV
        dav_window.print_control_identifiers()

        print("="*80)

    except Exception as e:
        logging.error(f"O teste de diagnóstico falhou: {e}", exc_info=True)

    print("\n--- DIAGNÓSTICO FINALIZADO ---")
    input("Pressione Enter para sair.")