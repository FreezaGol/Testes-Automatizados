import logging
import time
import pyautogui
from pywinauto import Desktop, timings
from pywinauto.findwindows import ElementNotFoundError
import subprocess
import json
import os
import sys
import random

def _select_from_grid(items_df, title, text_column, code_column):
    """
    Chama um subprocesso PySide6 e captura a seleção do usuário via stdout.
    """
    if items_df.empty:
        logging.warning(f"Nenhum item encontrado para a seleção: {title}")
        return None

    items_for_gui = [
        {'code': str(row[code_column]), 'display': f"{row[code_column]} - {row[text_column]}"}
        for _, row in items_df.iterrows()
    ]
    data_to_pass = {'title': title, 'items': items_for_gui}
    data_file = 'temp_gui_data.json'

    try:
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_pass, f)

        # --- MUDANÇA PRINCIPAL ---
        # Usa o mesmo executável python e captura a saída
        python_executable = sys.executable
        process = subprocess.run(
            [python_executable, 'src/selection_gui.py'],
            check=True,
            capture_output=True, # Captura a saída do terminal
            text=True            # Decodifica a saída como texto
        )
        
        # O resultado é a saída padrão do script, com espaços/quebras de linha removidos
        selected_code = process.stdout.strip()

        if selected_code:
            logging.info(f"Usuário selecionou o código: {selected_code}")
        else:
            logging.error("Nenhum item foi selecionado ou a janela foi fechada.")
        
        return selected_code

    except Exception as e:
        logging.error(f"Ocorreu um erro ao exibir a GUI de seleção: {e}")
        return None
    finally:
        if os.path.exists(data_file):
            os.remove(data_file)

# =============================================================================
# FUNÇÃO PARA SELEÇÃO MÚLTIPLA
# =============================================================================
def _select_multiple_items_from_grid(items_df, title, headers):
    """
    Chama um subprocesso PySide6 para exibir uma GUI de seleção múltipla.
    """
    if items_df.empty:
        logging.warning(f"Nenhum item encontrado para a seleção: {title}")
        return []

    # Prepara os dados para a GUI, garantindo que as chaves corretas existam
    # O dicionário de cada item terá as chaves que a GUI espera
    items_for_gui = []
    for _, row in items_df.iterrows():
        items_for_gui.append({
            'codigo_produto': str(row['codigo_produto']),
            'código': str(row['codigo_produto']),
            'produto': str(row['nome_produto']),
            'estoque': str(row['estoquedisponivel'])
        })
    
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
        
        selected_codes = json.loads(process.stdout.strip())

        if selected_codes:
            logging.info(f"Usuário selecionou {len(selected_codes)} itens: {selected_codes}")
        else:
            logging.warning("Nenhum item foi selecionado.")
        
        return selected_codes

    except Exception as e:
        logging.error(f"Ocorreu um erro ao exibir a GUI de seleção múltipla: {e}")
        return []
    finally:
        if os.path.exists(data_file):
            os.remove(data_file)

# =============================================================================
# FUNÇÃO PARA TRATAR DIÁLOGOS COM ALT+N
# =============================================================================
def _handle_optional_dialog(dialog_selector, keystroke, timeout=1):
    """
    Verifica se um diálogo opcional aparece e envia uma combinação de teclas.
    """
    try:
        desktop = Desktop(backend="win32")
        dialog = desktop.window(**dialog_selector)
        dialog.wait('visible', timeout=timeout)
        logging.info(f"Diálogo '{dialog_selector.get('title')}' encontrado.")
        
        dialog.set_focus()
        dialog.type_keys(keystroke)
        logging.info(f"--> Combinação de teclas '{keystroke}' enviada com sucesso.")
        #time.sleep(1)
        
    except (ElementNotFoundError, timings.TimeoutError):
        logging.info(f"Diálogo opcional '{dialog_selector.get('title')}' não apareceu. Prosseguindo...")
    except Exception as e:
        logging.warning(f"Não foi possível interagir com o diálogo opcional: {e}")

# =============================================================================
# FUNÇÃO PRINCIPAL DO TESTE
# =============================================================================
def run(db_handler, selectors, config):
    """
    Executa o fluxo de teste de criação de DAV em uma janela já aberta.
    """
    logging.info("### INICIANDO TESTE: Criação de Documento Auxiliar de Venda (DAV) ###")
    
    try:
        # PASSO 1: ENCONTRAR E CONECTAR À JANELA PRINCIPAL JÁ ABERTA
        logging.info("Procurando pela janela principal do Guardian...")
        desktop = Desktop(backend="win32")
        main_window = desktop.window(**selectors['main_window'])
        main_window.wait('visible', timeout=5)
        logging.info("Janela principal do Guardian encontrada e pronta para automação.")
        main_window.set_focus()
        
        # A lógica da automação começa aqui
        # 3. Navegar para "Vendas" (ALT+V)
        main_window.type_keys('%V')
        logging.info("Passo 3: Navegado para a seção 'Vendas'.")
        #time.sleep(2)

        # 4. Abrir tela de inclusão de Documento (ENTER)
        main_window.type_keys('{ENTER}')
        logging.info("Passo 4: Tela de inclusão de DAV aberta.")
        #time.sleep(2)

        # 5. Abrir a inclusão do DAV (F2)
        logging.info("Passo 5: Procurando pela janela filha de Inclusão de DAV...")
        dav_window = main_window.child_window(**selectors['dav_inclusion_window'])
        dav_window.wait('visible', timeout=1)
        dav_window.set_focus()
        logging.info("   -> Janela de Inclusão de DAV encontrada. Pressionando F2...")
        dav_window.type_keys('{F2}')
        #time.sleep(1)
        
        # 5.1. Verificar diálogo de créditos
        _handle_optional_dialog(selectors['confirmation_dialog'], "%n") # %n = ALT+N

        # 6. Selecionar natureza de operação
        logging.info("Passo 6: Buscando naturezas de operação...")
        naturezas_df = db_handler.get_naturezas_operacao()
        cod_natureza = _select_from_grid(naturezas_df, "Seleção de Natureza", "descricao", "codigo_natureza")
        if not cod_natureza: raise ValueError("Nenhuma natureza selecionada.")
        
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(cod_natureza, with_spaces=True)
        logging.info(f"   -> Natureza '{cod_natureza}' inserida.")


        # 7. Verificar Nat_DatEmisPed
        logging.info("Passo 7: Verificando Nat_DatEmisPed...")
        dat_emis_ped = db_handler.check_field_value('natoper', 'Nat_DatEmisPed', 'Nat_Codigo', cod_natureza)
        if dat_emis_ped == 1:
            logging.info("   -> Nat_DatEmisPed = 1. Pressionando ENTER 3x.")
            dav_window.type_keys('{ENTER 3}')
        else:
            logging.info("   -> Nat_DatEmisPed != 1. Pressionando ENTER 2x.")
            dav_window.type_keys('{ENTER 1}')
        #time.sleep(1)

        # 8. Selecionar cliente
        logging.info("Passo 8: Buscando clientes...")
        clientes_df = db_handler.get_clientes()
        selected_cliente_code = _select_from_grid(clientes_df, "Seleção de Cliente", "nome_cliente", "codigo_cliente")
        if not selected_cliente_code: raise ValueError("Nenhum cliente selecionado.")
        
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(selected_cliente_code)
        logging.info(f"   -> Cliente '{selected_cliente_code}' inserido.")
        dav_window.type_keys('{ENTER}')
        #time.sleep(1)
        
        # 9. Lógica do vendedor
        logging.info("Passo 9: Verificando configuração do vendedor...")
        cfg_vendedor = db_handler.check_field_value('natoper', 'Nat_cfgvendedor', 'Nat_Codigo', cod_natureza)
        logging.info(f"   -> Valor de Nat_cfgvendedor: {cfg_vendedor}")
        if cfg_vendedor == 1:
            logging.info("   -> CfgVendedor = 1. Pressionando ENTER para selecionar vendedor padrão.")
            dav_window.type_keys('{ENTER}')
        elif cfg_vendedor == 2:
            logging.info("   -> CfgVendedor = 2. Pulando campo de vendedor com ENTER.")
            dav_window.type_keys('{ENTER}')
        elif cfg_vendedor == 3:
            logging.info("   -> CfgVendedor = 3. Buscando vendedores...")
            vendedores_df = db_handler.get_vendedores()
            cod_vendedor = _select_from_grid(vendedores_df, "Seleção de Vendedor", "nome_vendedor", "codigo_colaborador")
            if not cod_vendedor: raise ValueError("Nenhum vendedor selecionado.")
            dav_window.type_keys('^a{DELETE}')
            dav_window.type_keys(cod_vendedor)
            dav_window.type_keys('{ENTER}')
            logging.info(f"   -> Vendedor '{cod_vendedor}' inserido.")
        else:
            dav_window.type_keys('{ENTER}')
        #time.sleep(1)

        # 10. Verificar diálogo de créditos novamente
        _handle_optional_dialog(selectors['confirmation_dialog'],"%n")


        # 11. Verificar campo "ID STUFF" por imagem
        logging.info("Passo 11: Verificando se campo 'ID STUFF' existe na tela...")
        try:
            location = pyautogui.locateOnScreen(config['Images']['id_stuff_image_path'], confidence=0.8)
            if location:
                logging.info("   -> Imagem 'ID STUFF' encontrada. Pressionando ENTER 5x.")
                dav_window.type_keys('{ENTER 5}')
            else:
                logging.info("   -> Imagem 'ID STUFF' não encontrada. Pressionando ENTER 2x.")
                dav_window.type_keys('{ENTER 2}')
        except Exception as img_err:
            logging.warning(f"   -> Erro ao tentar localizar imagem. Assumindo que não existe. Pressionando ENTER 3x. Erro: {img_err}")
            dav_window.type_keys('{ENTER 3}')
        #time.sleep(1)

        # 12. Selecionar forma de pagamento
        logging.info("Passo 12: Buscando formas de pagamento...")
        formas_pg_df = db_handler.get_formas_pagamento(selected_cliente_code)
        if formas_pg_df.empty:
            logging.info("   -> Nenhuma forma de pg. específica para o cliente, buscando formas gerais.")
            formas_pg_df = db_handler.get_all_formas_pagamento()
        
        selected_forma_pg_code = _select_from_grid(formas_pg_df, "Seleção de Forma de Pagamento", "descricao", "codigo_forma")
        if not selected_forma_pg_code: raise ValueError("Nenhuma forma de pagamento selecionada.")
        
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(selected_forma_pg_code)
        logging.info(f"   -> Forma de pagamento '{selected_forma_pg_code}' inserida.")
        
        # 13. Pressionar ENTER
        logging.info("Passo 13: Pressionando ENTER.")
        dav_window.type_keys('{ENTER}')
        #time.sleep(1)

        # 14. Selecionar condição de pagamento
        logging.info("Passo 14: Buscando condições de pagamento...")
        condicoes_pg_df = db_handler.get_condicoes_pagamento(selected_cliente_code, selected_forma_pg_code)
        if condicoes_pg_df.empty:
            logging.info("   -> Nenhuma condição compatível encontrada, buscando em todas as condições.")
            condicoes_pg_df = db_handler.get_all_condicoes_pagamento(selected_forma_pg_code)
        
        cod_condicao = _select_from_grid(condicoes_pg_df, "Seleção de Condição de Pagamento", "descricao", "codigo_condicao")
        if not cod_condicao: raise ValueError("Nenhuma condição de pagamento selecionada.")
        
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(cod_condicao)
        logging.info(f"   -> Condição de pagamento '{cod_condicao}' inserida.")

        # 15. Finaliza etapa de lançamento de condições
        logging.info("Passo 15: Pressionando ENTER 4x para lançar os itens.")
        dav_window.type_keys('{ENTER 5}')
        logging.info("Processo de preenchimento inicial do DAV finalizado com sucesso!")

        # 16. Verificar existencia da caixa de diálogo Aliquota de Comissão
        logging.info("Passo 16: Verificando a existencia da caixa de diálogo Aliquota de Comissão ")
        Pa5_DigComisDav = db_handler.check_field_value('parametro5', 'Pa5_DigComisDav', None, None)
        if Pa5_DigComisDav == 1 :
            _handle_optional_dialog(selectors['confirmation_dialog'],"%(s)")
        else :
            logging.info("Sistema não permite lançar comissão no DAV pulando para o proximo passo")
 
        # 17. INICIAR O LANÇAMENTO DOS ITENS
        logging.info("Passo 17: Iniciando lançamento de itens...")
        
        # 17.1. Busca produtos e padroniza os nomes das colunas
        products_df = db_handler.get_available_products()

        if not products_df.empty:
            products_df.columns = products_df.columns.str.lower()
        
        # Cria um mapa de estoque para consulta rápida: {'codigo': estoque}
        stock_map = dict(zip(
            products_df['codigo_produto'].astype(str).str.strip(), 
            products_df['estoquedisponivel']
        ))
        
        headers = ["Selecionar", "Código", "Produto", "Estoque"]
        
        selected_products = _select_multiple_items_from_grid(products_df, "Seleção de Produtos para Lançamento", headers)

        if not selected_products:
            raise ValueError("Nenhum produto foi selecionado para lançamento. Teste interrompido.")

        # 17.2. Busca a contagem de unidades para os itens selecionados
        logging.info("Buscando contagem de unidades para os produtos selecionados...")
        unit_counts_df = db_handler.get_product_unit_counts(selected_products)
        
        unit_counts_map = {}
        if not unit_counts_df.empty:
            unit_counts_map = dict(zip(unit_counts_df.iloc[:, 0], unit_counts_df.iloc[:, 1]))
        else:
            logging.warning("A consulta de contagem de unidades não retornou resultados.")

        # 17.3. Loop para lançar cada produto selecionado
        logging.info("Iniciando loop para lançar os produtos na tela de DAV...")
        for product_code_raw in selected_products:
            product_code = product_code_raw.strip()
            logging.info(f"  -> Lançando produto: {product_code}")
            
            # Digita o código do produto
            dav_window.type_keys(product_code, with_spaces=True)

            # Verificação da tela de preço sugerido 
            pa2_vultpreco = db_handler.check_field_value('parametro2', 'pa2_vultpreco', None, None)
            if pa2_vultpreco == 1:
                dav_window.type_keys('{ENTER}')
                _handle_optional_dialog(selectors['last_price_pratice'],"{ENTER}")

            # Pressiona ENTER de acordo com o número de unidades
            unit_count = unit_counts_map.get(product_code, 1)
            logging.info(f"Produto tem {unit_count} unidade(s) mapeada(s).")
            if unit_count > 1:
                dav_window.type_keys('{ENTER 2}')
            else:
                dav_window.type_keys('{ENTER}')
            #time.sleep(0.5)
            
            # --- LÓGICA DE QUANTIDADE ALEATÓRIA ---
            available_stock = int(float(stock_map.get(product_code, 1)))
            
            if available_stock < 1:
                available_stock = 1
                logging.warning(f"Estoque para o produto {product_code} é zero ou negativo. Usando quantidade 1.")

            random_quantity = random.randint(1, available_stock)
            logging.info(f"     Estoque disponível: {available_stock}. Quantidade sorteada: {random_quantity}")
            
            # Digita a quantidade aleatória
            dav_window.type_keys(str(random_quantity))

            # Pressiona ENTER 3x para gravar o item no pedido
            logging.info("Pressionando ENTER 3x para gravar o item.")
            dav_window.type_keys('{ENTER 3}')
            #time.sleep(1)

        logging.info("Todos os itens selecionados foram lançados com sucesso.")
        
        logging.info("### TESTE CONCLUÍDO: Criação de DAV ###")

    except Exception as e:
        logging.error(f"Ocorreu um erro durante o teste de criação de DAV: {e}", exc_info=True)