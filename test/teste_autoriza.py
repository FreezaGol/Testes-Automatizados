# test/test_final_authorization.py
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
authorization_dialog_selector = {
    "title_re": "Solicitação de Autorização.*"
  #  "class_name": "2.52_16P9c000000"
}

if __name__ == "__main__":
    print("\n--- INICIANDO TESTE FINAL COM HIERARQUIA CORRETA ---")

    try:
        # 1. Conectar à aplicação
        logging.info("Conectando à janela principal do Guardian...")
        desktop = Desktop(backend=backend)
        main_window = desktop.window(**main_window_selector)
        main_window.wait('visible', timeout=10)
        main_window.set_focus()
        logging.info("-> Janela principal encontrada.")

        # --- AÇÃO MANUAL DO USUÁRIO ---
        print("\n" + "="*60)
        print("==> AÇÃO NECESSÁRIA AGORA:")
        print("    1. Navegue até a tela de DAV.")
        print("    2. Preencha os dados e insira um produto até que a janela de")
        print("       'Solicitação de Autorização' ESTEJA VISÍVEL NA TELA.")
        print("="*60)
        input("--> Após a janela de autorização aparecer, pressione Enter aqui...")

        # --- TENTATIVA DE DETECÇÃO COM A LÓGICA CORRETA ---
        logging.info("Iniciando a busca pela janela de autorização (como filha da janela principal)...")
        found_window = False
        try:
            # A LÓGICA CORRETA: Buscar como filha da JANELA PRINCIPAL
            auth_window = main_window.child_window(**authorization_dialog_selector)
            auth_window.wait('visible', timeout=5)
            
            logging.info(f"✅ SUCESSO! A janela de autorização foi encontrada.")
            logging.info(f"   -> Título exato: '{auth_window.window_text()}'")
            found_window = True
            
            # Teste de interação
            auth_window.set_focus()
            auth_window.type_keys('{ESC}') # Envia ESC para fechar a janela
            logging.info("-> Interação (tecla ESC) enviada com sucesso.")

        except (ElementNotFoundError, timings.TimeoutError):
            logging.error("❌ FALHA: A janela de autorização não foi encontrada como filha da janela principal.")
            logging.error("   Isto é inesperado. Verifique se a janela estava realmente visível.")

    except Exception as e:
        logging.error(f"❌ FALHA GERAL: Ocorreu um erro inesperado: {e}", exc_info=True)

    print("\n--- TESTE FINALIZADO ---")
    input("Pressione Enter para sair.")