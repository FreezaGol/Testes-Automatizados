# src/main.py
import logging
import configparser
import json
import sys

# Módulos da automação
from logger_config import setup_logger
from db_handler import DBHandler

# Módulos de Teste
from tests import test_dav_creation_new
from tests import test_load_assembly

# Mapeamento dos testes disponíveis
AVAILABLE_TESTS = {
    "1": {
        "name": "Criação de Documento Auxiliar de Venda (DAV)",
        "function": test_dav_creation_new.run
    },
    "2": {
        "name": "Montagem de carga",
        "function": test_load_assembly.run
    },
    # Adicione futuros testes aqui
}

def display_menu():
    """Exibe o menu de testes para o usuário."""
    print("\n" + "="*50)
    print(" MENU DE TESTES DE AUTOMAÇÃO GUARDIAN")
    print("="*50)
    print("IMPORTANTE: A aplicação Guardian já deve estar aberta e logada.")
    print("="*50)
    for key, test in AVAILABLE_TESTS.items():
        print(f" {key} - {test['name']}")
    print(" Q - Sair")
    print("-"*50)
    return input("Escolha o teste que deseja executar: ").strip().upper()

def main():
    setup_logger()
    logging.info("================ INICIANDO TEST RUNNER ================")
    db_handler = None

    try:
        # Carregar configurações
        config = configparser.ConfigParser()
        config.read('config/config.ini')
        with open('config/selectors.json', 'r', encoding='utf-8') as f:
            selectors = json.load(f)

        # Instanciar DBHandler
        db_handler = DBHandler(config['Database'])
        
        # Loop do Menu
        while True:
            choice = display_menu()
            if choice == 'Q':
                break
            
            selected_test = AVAILABLE_TESTS.get(choice)
            if selected_test:
                # Executa a função do teste selecionado
                selected_test["function"](db_handler, selectors, config)
            else:
                print("Opção inválida. Tente novamente.")

    except Exception as e:
        logging.critical(f"Falha crítica na execução: {e}", exc_info=True)
    finally:
        if db_handler:
            db_handler.close_pool()
        logging.info("================ FINALIZANDO EXECUÇÃO ================\n")

if __name__ == "__main__":
    main()