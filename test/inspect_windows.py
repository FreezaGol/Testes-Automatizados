# test/diagnose_hierarchy.py
import time
import logging
from pywinauto import Desktop, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "win32"

# --- Seletores ---
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_16P9c000000"
}
dav_inclusion_selector = {
    "title": "Consulta de Pedidos - Documento Auxiliar de vendas"
}
confirmation_dialog_selector = {
    "title": "Confirmação",
    "class_name": "#32770"
}

if __name__ == "__main__":
    print("\n--- INICIANDO DIAGNÓSTICO DEFINITIVO DE HIERARQUIA DE CONTROLES ---")

    try:
        # 1. Conectar à aplicação
        logging.info("Conectando à janela principal do Guardian...")
        desktop = Desktop(backend=backend)
        main_window = desktop.window(**main_window_selector)
        main_window.wait('visible', timeout=10)
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # 2. Navegar até a tela de DAV
        logging.info("Navegando para a tela de vendas e inclusão de DAV...")
        main_window.type_keys('%V{ENTER}')
        time.sleep(2)
        
        dav_window = main_window.child_window(**dav_inclusion_selector)
        dav_window.wait('visible', timeout=5)
        dav_window.set_focus()
        dav_window.type_keys('{F2}')
        time.sleep(1)

        # 3. Tratar o diálogo de confirmação inicial (se houver)
        try:
            confirmation_dialog = desktop.window(**confirmation_dialog_selector)
            confirmation_dialog.wait('visible', timeout=2)
            confirmation_dialog.type_keys('%n')
            time.sleep(1)
        except (ElementNotFoundError, timings.TimeoutError):
            logging.info("Diálogo de confirmação inicial não apareceu. Prosseguindo...")

        # --- AÇÃO MANUAL DO USUÁRIO ---
        print("\n" + "="*60)
        print("==> AÇÃO NECESSÁRIA AGORA:")
        print("    1. Preencha o DAV e insira um produto que dispare a")
        print("       janela de 'Solicitação de Autorização'.")
        print("="*60)
        input("--> ASSIM QUE A JANELA DE AUTORIZAÇÃO ESTIVER VISÍVEL, pressione Enter aqui...")

        # --- DIAGNÓSTICO COMPLETO ---
        print("\n" + "="*80)
        print("==> MAPA COMPLETO DE CONTROLES DA JANELA PRINCIPAL <==")
        print("="*80)
        logging.info("Gerando o mapa de controles... Isso pode levar alguns segundos.")
        
        # O comando mágico: imprime a árvore de todos os controles filhos da JANELA PRINCIPAL
        main_window.print_control_identifiers(depth=10) # Aumentamos a profundidade da busca

        print("="*80)
        logging.info("Mapa de controles gerado acima.")
        logging.info("Procure no texto acima pela janela 'Solicitação de Autorização' e anote a sua hierarquia de 'child_window'.")

    except Exception as e:
        logging.error(f"❌ FALHA GERAL: Ocorreu um erro inesperado: {e}", exc_info=True)

    print("\n--- DIAGNÓSTICO FINALIZADO ---")
    input("Pressione Enter para sair.")