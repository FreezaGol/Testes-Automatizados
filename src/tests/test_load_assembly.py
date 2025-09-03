# src/tests/test_load_assembly.py
import logging
import time
import pandas as pd
import sys
import subprocess
import json
import os
from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError

# Para este teste, vamos precisar da função de seleção múltipla.
# A melhor prática a longo prazo seria mover esta função para um arquivo 'utils.py',
# mas por enquanto, podemos simplesmente copiá-la para cá para manter o teste autônomo.

def _select_multiple_items_from_grid(items_df, title, headers):
    if items_df.empty:
        logging.warning(f"Nenhum item encontrado para a seleção: {title}")
        return pd.DataFrame() # Retorna um DataFrame vazio

    items_for_gui = items_df.to_dict('records')
    data_to_pass = {'title': title, 'items': items_for_gui, 'headers': headers}
    data_file = 'temp_gui_data.json'

    try:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_pass, f, default=str)

        python_executable = sys.executable
        process = subprocess.run(
            [python_executable, 'src/multi_selection_gui.py'],
            check=True, capture_output=True, text=True
        )
        
        selected_codes_str = json.loads(process.stdout.strip())
        # Converte os códigos de volta para o tipo original do DataFrame para o filtro funcionar
        original_dtype = items_df['ped_numero'].dtype
        selected_codes = [pd.Series(selected_codes_str, dtype=original_dtype)]
        
        if selected_codes:
            logging.info(f"Usuário selecionou {len(selected_codes_str)} itens.")
            # Retorna as linhas completas do DataFrame que foram selecionadas
            return items_df[items_df['ped_numero'].isin(selected_codes[0])]
        else:
            logging.warning("Nenhum item foi selecionado.")
            return pd.DataFrame()

    except Exception as e:
        logging.error(f"Ocorreu um erro ao exibir a GUI de seleção múltipla: {e}")
        return pd.DataFrame()
    finally:
        if os.path.exists(data_file):
            os.remove(data_file)


def run(db_handler, selectors, config):
    """
    Executa o fluxo de teste de montagem de carga.
    """
    logging.info("### INICIANDO TESTE: Montagem de Carga ###")
    
    try:
        # --- FASE 1: COLETA DE DADOS ---
        logging.info("Buscando pedidos de venda do dia...")
        orders_df = db_handler.get_sales_orders_for_today()
        
        if orders_df.empty:
            logging.warning("Nenhum pedido de venda encontrado para a data de hoje. Teste encerrado.")
            return

        headers = ["Selecionar", "Pedido", "Série"]
        orders_df.rename(columns={'ped_numero': 'pedido', 'ped_spvcodigo': 'série'}, inplace=True)
        
        selected_orders_df = _select_multiple_items_from_grid(orders_df, "Seleção de Pedidos para Carga", headers)

        if selected_orders_df.empty:
            raise ValueError("Nenhum pedido foi selecionado. Teste interrompido.")

        logging.info("--- FASE 2: AUTOMAÇÃO DA INTERFACE ---")

        desktop = Desktop(backend="win32")
        main_window = desktop.window(**selectors['main_window'])
        main_window.set_focus()
        logging.info("Janela principal do Guardian encontrada.")
        
        # 1. Abrir tela de logística
        main_window.type_keys('%l') # ALT+L, depois ENTER
        main_window.type_keys('{ENTER}')
        logging.info("Passo 1: Navegado para a tela de Logística.")
        time.sleep(2)

        # Encontra a janela de logística (pode ser a mesma principal ou uma nova)
        # Se for uma janela filha, use main_window.child_window(...)
        logistics_window = main_window.child_window(**selectors['logistics_window'])
        logistics_window.wait('visible', timeout=3)
        
        # 2. F2 para incluir a carga
        logistics_window.type_keys('{F2}')
        logging.info("Passo 2: Inclusão de nova carga iniciada.")
        time.sleep(1)

        # Encontra a janela de montagem de carga
        # load_window = desktop.window(**selectors['load_assembly_window'])
        # load_window.wait('visible', timeout=3)
        # load_window.set_focus()

        # 3. Pressionar ENTER 2x
        logistics_window.type_keys('{ENTER 2}')
        logging.info("Passo 3: Pressionado ENTER 2x.")
        time.sleep(1)

        # 4. Loop para incluir os pedidos
        logging.info("Passo 4: Iniciando inclusão dos pedidos selecionados...")
        num_pedidos = len(selected_orders_df)
        for i, row in enumerate(selected_orders_df.itertuples()):
            pedido = str(row.pedido)
            serie = str(row.série)
            logging.info(f"  -> Lançando Pedido: {pedido}, Série: {serie}")

            if i == 0:
                # Primeira inclusão: Pedido -> ENTER -> Série
                logistics_window.type_keys(pedido + "{ENTER}" + serie)
            else:
                # Demais inclusões: Série -> ENTER -> Pedido
                logistics_window.type_keys(serie + "{ENTER}" + pedido)
            
            # 4.1. Pressionar ENTER 4x para ir para a próxima linha
            # Não pressiona após o último item
            if i < num_pedidos - 1:
                logging.info("     Pressionando ENTER 4x para próximo item.")
                logistics_window.type_keys('{ENTER 4}')
                time.sleep(0.5)
        
        logging.info("Todos os pedidos foram incluídos na carga com sucesso!")
        time.sleep(5)
        
        logging.info("### TESTE CONCLUÍDO: Montagem de Carga ###")

    except Exception as e:
        logging.error(f"Ocorreu um erro durante o teste de montagem de carga: {e}", exc_info=True)