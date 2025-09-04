# test_find_address_dialog.py
import time
#import logging
from pywinauto import Desktop, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuração do Teste ---
#logging.basicConfig(level=print, format='%(asctime)s - %(levelname)s - %(message)s')
backend = "win32"

# --- ▼▼▼ VERIFIQUE E AJUSTE ESTES SELETORES ▼▼▼ ---
# Seletor para a Janela Principal (o "avô")
main_window_selector = {
    "title_re": "Space Guardian.*",
    "class_name": "2.52_16P9c000000"
}

# Seletor para o Painel Intermediário (o "pai")
# Use o inspetor para descobrir as propriedades corretas deste painel
intermediate_panel_selector = {
    "title_re": "Space Guardian.*", # Muitas vezes o painel tem o mesmo nome 
    "control_type": "Window"
    }

# Seletor para a Janela de Endereços que você quer testar
address_dialog_selector = {
    "title": "Solicitação de Autorização para permissão.*",
    "class_name": "2.52_16P9c000000"
}
# --- ▲▲▲ FIM DOS SELETORES ▲▲▲ ---

# --- Lógica Principal do Teste ---
if __name__ == "__main__":
    print("\n--- INICIANDO TESTE ABRANGENTE DE LOCALIZAÇÃO DE JANELA ---")
    print("\n==> AÇÃO NECESSÁRIA:")
    print("    1. Abra a aplicação Guardian e faça o login.")
    print("    2. Navegue até o ponto em que a janela de 'Endereços' esteja visível.")
    print("\n    O teste começará em 3 segundos...")
    
    time.sleep(3)
    
    print("\nIniciando busca...")
    found_window = False

    try:
        desktop = Desktop(backend=backend)
        
        print("Procurando pela janela principal...")
        main_window = desktop.window(**main_window_selector)
        if not main_window.exists():
            raise ElementNotFoundError("Janela Principal não foi encontrada.")
        print("-> Janela principal encontrada.")

        # ====================================================================
        # TENTATIVA 1: Procurar como JANELA FILHA DIRETA
        # ====================================================================
        try:
            print(f"TENTATIVA 1: Procurando como FILHA DIRETA da principal...")
            address_window = main_window.child_window(**address_dialog_selector)
            address_window.wait('visible', timeout=2)
            print("✅ SUCESSO! A janela foi encontrada como JANELA FILHA.")
            found_window = True
        except (ElementNotFoundError, timings.TimeoutError):
            print("AVISO: Não encontrada como filha direta.")

        # ====================================================================
        # TENTATIVA 2: Procurar como JANELA PRINCIPAL (se a primeira falhou)
        # ====================================================================
        if not found_window:
            try:
                print(f"TENTATIVA 2: Procurando como JANELA PRINCIPAL (top-level)...")
                address_window = desktop.window(**address_dialog_selector)
                address_window.wait('visible', timeout=2)
                print("✅ SUCESSO! A janela foi encontrada como JANELA PRINCIPAL.")
                found_window = True
            except (ElementNotFoundError, timings.TimeoutError):
                print("AVISO: Não encontrada como janela principal.")

        # ====================================================================
        # TENTATIVA 3: Procurar ANINHADA DENTRO DE UM PAINEL (se as outras falharam)
        # ====================================================================
        if not found_window:
            try:
                print(f"TENTATIVA 3: Procurando ANINHADA DENTRO DE UM PAINEL...")
                panel = main_window.child_window(**intermediate_panel_selector)
                panel.wait('visible', timeout=2)
                print("-> Painel intermediário encontrado.")
                
                address_window = panel.child_window(**address_dialog_selector)
                address_window.wait('visible', timeout=2)
                print("✅ SUCESSO! A janela foi encontrada ANINHADA DENTRO do painel.")
                found_window = True
            except (ElementNotFoundError, timings.TimeoutError):
                print("❌ FALHA FINAL: A janela não foi encontrada em nenhuma das três tentativas.")

        if found_window:
            print("\nInteragindo com a janela encontrada para confirmar...")
            address_window.set_focus()
            address_window.type_keys('{ESC}') # Envia ESC para fechar a janela como teste
            print("-> Interação (tecla ESC) enviada com sucesso.")


    except Exception as e:
        print(f"❌ FALHA: Ocorreu um erro inesperado durante o teste: {e}")

    print("\n--- TESTE FINALIZADO ---")
    input("Pressione Enter para sair.")