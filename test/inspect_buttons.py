# test/diagnose_auth_buttons_uia.py
# VERSÃO REFORMULADA - Usando o backend 'uia' para encontrar controles customizados.

import time
import logging
from pywinauto import Application, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ▼▼▼ MUDANÇA PRINCIPAL: USANDO O BACKEND 'UIA' ▼▼▼
backend = "uia"

# --- Seletores ---
# OBS: Seletores para 'uia' podem ser diferentes. Vamos começar com os que temos.
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_16P9c000000"
}
authorization_dialog_selector = {
    "title_re": "Solicitação de Autorização.*",
    "class_name": "2.52_16P9c000000"
}

if __name__ == "__main__":
    print("\n--- DIAGNÓSTICO DE BOTÕES (BACKEND 'UIA') ---")

    try:
        # 1. Conectar à aplicação usando o backend 'uia'
        logging.info(f"Conectando à aplicação usando o backend '{backend}'...")
        # Com 'uia', é mais robusto conectar diretamente ao processo em execução
        app = Application(backend=backend).connect(**main_window_selector)
        main_window = app.window(**main_window_selector)
        main_window.wait('visible', timeout=10)
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # --- AÇÃO MANUAL DO USUÁRIO ---
        print("\n" + "="*60)
        print("==> AÇÃO NECESSÁRIA AGORA:")
        print("    1. Navegue e preencha o DAV até que a janela de")
        print("       'Solicitação de Autorização' ESTEJA VISÍVEL NA TELA.")
        print("="*60)
        input("--> Após a janela de autorização aparecer, pressione Enter aqui...")

        # --- DIAGNÓSTICO DOS CONTROLES INTERNOS COM 'UIA' ---
        logging.info("Buscando a janela de autorização para inspecionar seus botões...")
        try:
            # A busca continua sendo a partir da janela principal
            auth_window = main_window.child_window(**authorization_dialog_selector)
            auth_window.wait('visible', timeout=5)
            logging.info(f"Janela de autorização encontrada: '{auth_window.window_text()}'")

            print("\n" + "="*80)
            print("==> MAPA DE CONTROLES (UIA) DA JANELA DE AUTORIZAÇÃO <==")
            print("="*80)
            
            # Imprime a árvore de controles que o backend 'uia' consegue ver
            auth_window.print_control_identifiers()

            print("="*80)
            logging.info("Mapa de controles gerado acima. Procure pelo botão 'Confirmar' ou 'Autorizar'.")

        except (ElementNotFoundError, timings.TimeoutError):
            logging.error("❌ FALHA: A janela de autorização não foi encontrada com o backend 'uia'.")

    except Exception as e:
        logging.error(f"❌ FALHA GERAL: Ocorreu um erro inesperado: {e}", exc_info=True)

    print("\n--- DIAGNÓSTICO FINALIZADO ---")
    input("Pressione Enter para sair.")