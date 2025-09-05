# test/test_auth_button_clicks.py
# TESTE ISOLADO - VERSÃO COM .invoke() PARA ACIONAR OS BOTÕES

import time
import logging
from pywinauto import Application, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "uia"

# --- Seletores ---
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_16P9c000000"
}
authorization_dialog_selector = {
    "title_re": "Solicitação de Autorização.*",
    "control_type": "Window"
}
authorization_authorize_button_selector = {
    "title": "Autorizar >>",
    "control_type": "Button"
}
authorization_confirm_button_selector = {
    "title": "Confirma Autorização",
    "control_type": "Button"
}

if __name__ == "__main__":
    print("\n--- INICIANDO TESTE COM .invoke() NA JANELA DE AUTORIZAÇÃO ---")

    try:
        # 1. Conectar à aplicação
        logging.info(f"Conectando à aplicação usando o backend '{backend}'...")
        app = Application(backend=backend).connect(**main_window_selector)
        main_window = app.window(**main_window_selector)
        main_window.wait('visible', timeout=10)
        main_window.set_focus()
        logging.info("-> Janela principal do Guardian encontrada.")

        # --- AÇÃO MANUAL DO USUÁRIO ---
        print("\n" + "="*60)
        print("==> AÇÃO NECESSÁRIA AGORA:")
        print("    1. Navegue e preencha o DAV até que a janela de")
        print("       'Solicitação de Autorização' ESTEJA VISÍVEL NA TELA.")
        print("="*60)
        input("--> Após a janela de autorização aparecer, pressione Enter aqui para o teste começar...")

        # --- LÓGICA DE TESTE AUTOMATIZADO ---
        logging.info("Iniciando busca pela janela de autorização e seus botões...")
        
        try:
            # 1. Encontrar a janela de diálogo de autorização
            auth_dialog = main_window.child_window(**authorization_dialog_selector)
            auth_dialog.wait('visible', timeout=5)
            logging.info(f"✅ SUCESSO! Janela de autorização encontrada: '{auth_dialog.window_text()}'")
            
            # 2. Encontrar e acionar o primeiro botão: "<< Autorizar"
            authorize_button = auth_dialog.child_window(**authorization_authorize_button_selector)
            authorize_button.wait('ready', timeout=3)
            logging.info("✅ SUCESSO! Botão '<< Autorizar' encontrado. Acionando com .invoke()...")
            authorize_button.invoke() # <-- MUDANÇA AQUI
            logging.info("--> Ação 'invoke' no botão '<< Autorizar' enviada.")
            time.sleep(1)

            # 3. Encontrar e acionar o segundo botão: "Confirma Autorização"
            confirm_button = auth_dialog.child_window(**authorization_confirm_button_selector)
            confirm_button.wait('ready', timeout=3)
            logging.info("✅ SUCESSO! Botão 'Confirma Autorização' encontrado. Acionando com .invoke()...")
            confirm_button.invoke() # <-- MUDANÇA AQUI
            logging.info("--> Ação 'invoke' no botão 'Confirma Autorização' enviada.")
            
            print("\nO teste com .invoke() foi executado com sucesso!")

        except (ElementNotFoundError, timings.TimeoutError) as e:
            logging.error(f"❌ FALHA: Um controle esperado não foi encontrado. Erro: {e}")
        except Exception as e_inner:
            logging.error(f"❌ FALHA: Ocorreu um erro durante a interação com os botões: {e_inner}")

    except Exception as e_outer:
        logging.error(f"❌ FALHA GERAL: Ocorreu um erro inesperado: {e_outer}", exc_info=True)

    print("\n--- TESTE FINALIZADO ---")
    input("Pressione Enter para sair.")