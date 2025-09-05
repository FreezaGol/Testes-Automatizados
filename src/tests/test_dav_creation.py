# src/tests/test_dav_creation.py
import logging
import time
import pandas as pd
import pyautogui
import sys
import subprocess
import json
import os
import random
from pywinauto import Application, Desktop, timings
from pywinauto.findwindows import ElementNotFoundError

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
# FUNÇÃO PARA VERIFICAR SE A TELA AUTORIZAÇÕES APARECEU
# =============================================================================
def _check_for_authorization_win32(main_window, selectors, timeout=2):
    """
    Verifica de forma robusta com 'win32' se a janela de autorização existe.
    Usa o seletor simplificado (sem class_name) e um timeout razoável.
    Retorna True se a janela for encontrada, False caso contrário.
    """
    try:
        # IMPORTANTE: Usando o seletor que provou funcionar, sem class_name.
        selector = {"title_re": selectors['authorization_dialog']['title_re']}
        
        auth_dialog = main_window.child_window(**selector)
        auth_dialog.wait('visible', timeout=timeout)
        logging.info("Pré-verificação (win32): Janela de autorização detectada.")
        return True
    except timings.TimeoutError:
        logging.info("Pré-verificação (win32): Janela de autorização não apareceu no tempo esperado.")
        return False
    except Exception as e:
        logging.warning(f"Pré-verificação (win32): Ocorreu um erro inesperado. {e}")
        return False
# =============================================================================
# FUNÇÃO PARA TRATAR AUTORIZAÇÕES COM button.invoke
# =============================================================================
def _handle_authorization_dialog(selectors, timeout=0.3):
    """
    Verifica se a janela de autorização aparece e aciona os botões de autorização
    e confirmação usando o backend 'uia' e o método '.invoke()'.
    A conexão UIA é criada aqui dentro para garantir a detecção correta.
    """
    try:
        # Conexão específica com backend UIA feita no momento do uso para máxima confiabilidade
        logging.info("Conectando com backend 'uia' para tratar a janela de autorização...")
        app_uia = Application(backend="uia").connect(**selectors['main_window'])
        main_window_uia = app_uia.window(**selectors['main_window'])

        # 1. Encontrar a janela de diálogo de autorização
        auth_dialog = main_window_uia.child_window(**selectors['authorization_dialog'])
        auth_dialog.wait('visible', timeout=timeout)
        logging.info(f"Janela de autorização encontrada: '{auth_dialog.window_text()}'")
        auth_dialog.set_focus()

        # 2. Encontrar e acionar o primeiro botão: "<< Autorizar"
        authorize_button = auth_dialog.child_window(**selectors['authorization_authorize_button'])
        authorize_button.wait('ready', timeout=0.3)
        logging.info("Botão '<< Autorizar' encontrado. Acionando com .invoke()...")
        authorize_button.invoke()
        logging.info("--> Ação 'invoke' no botão '<< Autorizar' enviada.")
        #time.sleep(0.5)

        # 3. Encontrar e acionar o segundo botão: "Confirma Autorização"
        confirm_button = auth_dialog.child_window(**selectors['authorization_confirm_button'])
        confirm_button.wait('ready', timeout=0.3)
        logging.info("Botão 'Confirma Autorização' encontrado. Acionando com .invoke()...")
        confirm_button.invoke()
        logging.info("--> Ação 'invoke' no botão 'Confirma Autorização' enviada.")
        #time.sleep(0.5)

    except (ElementNotFoundError, timings.TimeoutError):
        logging.info("Janela de autorização não apareceu. Prosseguindo...")
    except Exception as e:
        logging.warning(f"Não foi possível interagir com a janela de autorização: {e}", exc_info=True)

# =============================================================================
# FUNÇÃO PRINCIPAL DO TESTE 
# =============================================================================
def run(db_handler, selectors, config):
    """
    Executa o fluxo de teste de criação de DAV com coleta de dados antecipada.
    """
    logging.info("### INICIANDO TESTE: Criação de Documento Auxiliar de Venda (DAV) ###")
    
    try:
        # =============================================================================
        # FASE 1: COLETA DE DADOS (SELEÇÕES DO USUÁRIO)
        # =============================================================================
        logging.info("--- FASE 1: Coletando todas as informações necessárias ---")

        # --- NOVA LÓGICA DE SELEÇÃO DE FILIAL ---
        selected_filial_code = None
        filial_count = db_handler.get_active_filiais_count()
        if filial_count > 1:
            logging.info("Múltiplas filiais ativas encontradas. Solicitando seleção do usuário.")
            filiais_df = db_handler.get_active_filiais()
            selected_filial_code = _select_from_grid(filiais_df, "Seleção de Filial", "nome_filial", "codigo_filial")
            if not selected_filial_code: raise ValueError("Seleção de Filial foi cancelada.")
            logging.info(f"Trabalhando com a filial: {selected_filial_code}")
        elif filial_count == 1:
             selected_filial_code = 1
             logging.info(f"Encontrada uma única filial ativa: {selected_filial_code}. Selecionada automaticamente.")
        else:
            logging.info("Nenhuma filial ativa encontrada. O filtro de filial não será aplicado.")

        # 1. Selecionar natureza de operação
        naturezas_df = db_handler.get_naturezas_operacao()
        cod_natureza = _select_from_grid(naturezas_df, "Seleção de Natureza", "descricao", "codigo_natureza")
        if not cod_natureza: raise ValueError("Seleção de Natureza foi cancelada.")

        # 2. Selecionar cliente
        clientes_df = db_handler.get_clientes()
        selected_cliente_code = _select_from_grid(clientes_df, "Seleção de Cliente", "nome_cliente", "codigo_cliente")
        if not selected_cliente_code: raise ValueError("Seleção de Cliente foi cancelada.")

        # 3. Lógica do vendedor (se necessário)
        cod_vendedor = None
        cfg_vendedor = db_handler.check_field_value('natoper', 'Nat_cfgvendedor', 'Nat_Codigo', cod_natureza)
        if cfg_vendedor == 3:
            vendedores_df = db_handler.get_vendedores()
            cod_vendedor = _select_from_grid(vendedores_df, "Seleção de Vendedor", "nome_vendedor", "codigo_colaborador")
            if not cod_vendedor: raise ValueError("Seleção de Vendedor foi cancelada.")

        # 4. Selecionar forma de pagamento
        formas_pg_df = db_handler.get_formas_pagamento(selected_cliente_code)
        if formas_pg_df.empty:
            formas_pg_df = db_handler.get_all_formas_pagamento()
        selected_forma_pg_code = _select_from_grid(formas_pg_df, "Seleção de Forma de Pagamento", "descricao", "codigo_forma")
        if not selected_forma_pg_code: raise ValueError("Seleção de Forma de Pagamento foi cancelada.")

        # 5. Selecionar condição de pagamento
        condicoes_pg_df = db_handler.get_condicoes_pagamento(selected_cliente_code, selected_forma_pg_code)
        if condicoes_pg_df.empty:
            condicoes_pg_df = db_handler.get_all_condicoes_pagamento(selected_forma_pg_code)
        cod_condicao = _select_from_grid(condicoes_pg_df, "Seleção de Condição de Pagamento", "descricao", "codigo_condicao")
        if not cod_condicao: raise ValueError("Seleção de Condição de Pagamento foi cancelada.")
        
        # 6. Selecionar produtos para lançamento
        products_df = db_handler.get_available_products(selected_filial_code)
        if not products_df.empty:
            products_df.columns = products_df.columns.str.lower()
        
        stock_map = dict(zip(products_df['codigo_produto'].astype(str).str.strip(), products_df['estoquedisponivel']))
        headers = ["Selecionar", "Código", "Produto", "Estoque"]
        selected_products = _select_multiple_items_from_grid(products_df, "Seleção de Produtos para Lançamento", headers)
        if not selected_products: raise ValueError("Nenhum produto foi selecionado.")

        # 7. Buscar dados auxiliares para os produtos selecionados
        unit_counts_df = db_handler.get_product_unit_counts(selected_products)
        unit_counts_map = {}
        if not unit_counts_df.empty:
            unit_counts_map = dict(zip(unit_counts_df.iloc[:, 0].astype(str).str.strip(), unit_counts_df.iloc[:, 1]))

        logging.info("--- FASE 1 CONCLUÍDA: Todos os dados foram coletados. ---")
        logging.info("A automação da interface começará em 3 segundos...")
        time.sleep(3)

        # =============================================================================
        # FASE 2: AUTOMAÇÃO DA INTERFACE (USANDO SUA LÓGICA EXISTENTE)
        # =============================================================================
        
        logging.info("--- FASE 2: Iniciando automação da interface do Guardian ---")
        
        desktop = Desktop(backend="win32")
        main_window = desktop.window(**selectors['main_window'])
        main_window.wait('visible', timeout=5)
        logging.info("Janela principal do Guardian encontrada e pronta para automação.")
        main_window.set_focus()

        # 3. Navegar para "Vendas" (ALT+V)
        main_window.type_keys('%V')
        logging.info("Passo 3: Navegado para a seção 'Vendas'.")

        # 4. Abrir tela de inclusão de Documento (ENTER)
        main_window.type_keys('{ENTER}')
        logging.info("Passo 4: Tela de inclusão de DAV aberta.")

        # 5. Abrir a inclusão do DAV (F2)
        logging.info("Passo 5: Procurando pela janela filha de Inclusão de DAV...")
        dav_window = main_window.child_window(**selectors['dav_inclusion_window'])
        dav_window.wait('visible', timeout=1)
        dav_window.set_focus()
        logging.info("   -> Janela de Inclusão de DAV encontrada. Pressionando F2...")
        dav_window.type_keys('{F2}')
        
        # 5.1. Verificar diálogo de créditos
        _handle_optional_dialog(selectors['confirmation_dialog'], "%n")

        # 6. Selecionar natureza de operação
        logging.info("Passo 6: Inserindo Natureza de Operação pré-selecionada...")
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

        # 8. Selecionar cliente
        logging.info("Passo 8: Inserindo Cliente pré-selecionado...")
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(selected_cliente_code)
        logging.info(f"   -> Cliente '{selected_cliente_code}' inserido.")
        dav_window.type_keys('{ENTER}')
        #time.sleep(1)  
            
        # 8.1. Advertencia Inscrição Estadual do Contribuinte NÃO está Habilitada 
        _handle_optional_dialog(selectors['warning_dialog'], "{ENTER}") 

        # 8.2. Advertencia Inscrição Estadual do Contribuinte NÃO está Habilitada 
        _handle_optional_dialog(selectors['notification_dialog'], "{ENTER}")  


        # 8.5 Verifica se o dialogo de endereços irá aparecer
        #pa4_buscendpad = db_handler.check_field_value('parametro4', 'pa4_buscendpad', None, None)
        #time.sleep(1)
        #if pa4_buscendpad == 0 :
        try :
            adress_window = main_window.child_window(**selectors['adress_dialog'])
            adress_window.wait('visible', timeout=1)
            adress_window.set_focus()
            logging.info(f"Tela de endereços encontrada enviando 3x TAB + 1x ENTER")
            adress_window.type_keys('{TAB}{TAB}{TAB}{ENTER}')
        except :
            logging.info(f"Tela de endereços não foi encontrada script continua")

        # 9. Lógica do vendedor
        logging.info("Passo 9: Verificando configuração do vendedor...")
        logging.info(f"   -> Valor de Nat_cfgvendedor: {cfg_vendedor}")
        if cfg_vendedor == 1:
            logging.info("   -> CfgVendedor = 1. Pressionando ENTER para selecionar vendedor padrão e ENTER 2X para chegar ao lançamento da forma de pagamento.")
            dav_window.type_keys('{ENTER 2}')
        elif cfg_vendedor == 2:
            logging.info("   -> CfgVendedor = 2. Pulando campo de vendedor com ENTER.")
            dav_window.type_keys('{ENTER}')
        elif cfg_vendedor == 3:
            logging.info("   -> CfgVendedor = 3. Inserindo Vendedor pré-selecionado...")
            dav_window.type_keys('^a{DELETE}')
            dav_window.type_keys(cod_vendedor)
            dav_window.type_keys('{ENTER 2}')
            logging.info(f"   -> Vendedor '{cod_vendedor}' inserido.")
        else:
            dav_window.type_keys('{ENTER}')

        # 10. Verificar diálogo de créditos novamente
        _handle_optional_dialog(selectors['confirmation_dialog'],"%n")

        # 11. Verificar campo "ID STUFF" por imagem
     #   logging.info("Passo 11: Verificando se campo 'ID STUFF' existe na tela...")
     #   try:
     #       location = pyautogui.locateOnScreen(config['Images']['id_stuff_image_path'], confidence=0.8)
     #       if location:
     #           logging.info("   -> Imagem 'ID STUFF' encontrada. Pressionando ENTER 5x.")
     #           dav_window.type_keys('{ENTER 5}')
     #       else:
     #           logging.info("   -> Imagem 'ID STUFF' não encontrada. Pressionando ENTER 2x.")
     #           dav_window.type_keys('{ENTER 2}')
     #   except Exception as img_err:
     #       logging.warning(f"   -> Erro ao tentar localizar imagem. Assumindo que não existe. Pressionando ENTER 3x. Erro: {img_err}")
        

        # 12. Selecionar forma de pagamento
        logging.info("Passo 12: Inserindo Forma de Pagamento pré-selecionada...")
        dav_window.type_keys('{ENTER}')
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(selected_forma_pg_code)
        logging.info(f"   -> Forma de pagamento '{selected_forma_pg_code}' inserida.")
        
        # 13. Pressionar ENTER
        logging.info("Passo 13: Pressionando ENTER.")
        dav_window.type_keys('{ENTER}')

        # 14. Selecionar condição de pagamento
        logging.info("Passo 14: Inserindo Condição de Pagamento pré-selecionada...")
        dav_window.type_keys('^a{DELETE}')
        dav_window.type_keys(cod_condicao)
        logging.info(f"   -> Condição de pagamento '{cod_condicao}' inserida.")

        # 15. Finaliza etapa de lançamento de condições
        logging.info("Passo 15: Pressionando ENTER 5x para lançar os itens.")
        dav_window.type_keys('{ENTER 5}')
        logging.info("Processo de preenchimento inicial do DAV finalizado com sucesso!")
        time.sleep(0.5)
        # 16. Verificar existencia da caixa de diálogo Aliquota de Comissão
        logging.info("Passo 16: Verificando a existencia da caixa de diálogo Aliquota de Comissão ")

        Pa5_DigComisDav = db_handler.check_field_value(
            table='parametro5', 
            field='pa5_digcomisDav', 
            filial_code=selected_filial_code
        )

        if Pa5_DigComisDav == 1 :
            _handle_optional_dialog(selectors['confirmation_dialog'],"%(s)")
        else :
            logging.info("Sistema não permite lançar comissão no DAV pulando para o proximo passo")
 
        # 17. INICIAR O LANÇAMENTO DOS ITENS
        logging.info("Passo 17: Iniciando lançamento de itens...")
        logging.info("Iniciando loop para lançar os produtos na tela de DAV...")
        for product_code_raw in selected_products:
            product_code = product_code_raw.strip()
            logging.info(f"   -> Lançando produto: {product_code}")
            
            dav_window.type_keys(product_code, with_spaces=True)

            pa2_vultpreco = db_handler.check_field_value(
                table='parametro2', 
                field='pa2_vultpreco', 
                filial_code=selected_filial_code
            )

            if pa2_vultpreco == 1:
                #dav_window.type_keys('{ENTER}')
                _handle_optional_dialog(selectors['last_price_pratice'],"{ENTER}")

            # Verifica quantas unidades o produto tem para definir quantos ENTERS são necessários
            # para selecionar a unidade
            unit_count = unit_counts_map.get(product_code)
            logging.info(f"Produto tem {unit_count} unidade(s) mapeada(s).")
            if unit_count > 1:
                dav_window.set_focus()
                time.sleep(0.2)
                dav_window.type_keys('{ENTER}')
                time.sleep(0.2)
                dav_window.type_keys('{ENTER}')
            else:
                dav_window.set_focus()
                time.sleep(0.2)
                dav_window.type_keys('{ENTER}')

            # Verifica se há lançamento de lote ou local de estoque na natureza
            lanc_lotloc_ped = db_handler.check_field_value('natoper', 'Nat_LcLtPeds', 'Nat_Codigo', cod_natureza) 
            if lanc_lotloc_ped == 1 : 
                dav_window.set_focus()
                time.sleep(0.2)
                dav_window.type_keys('{ENTER}')

            # Define e lança a quantidade de cada item
            available_stock = int(float(stock_map.get(product_code, 1)))
            if available_stock < 1:
                available_stock = 1
                logging.warning(f"Estoque para o produto {product_code} é zero ou negativo. Usando quantidade 1.")
            
            if available_stock >= 20 :    
                random_quantity = random.randint(1, 20)
            else :
                random_quantity = random.randint(1, available_stock)
                
            logging.info(f"Estoque disponível: {available_stock}. Quantidade sorteada: {random_quantity}")
            
            dav_window.set_focus()
            dav_window.type_keys(str(random_quantity))
            time.sleep(0.2)  
  
            # Verifica se os campos de desconto e acréscimo estarão disponíveis 
            pa2_infacreped = db_handler.check_field_value(
                table='parametro2', 
                field='pa2_infacreped', 
                filial_code=selected_filial_code
            )

            pa2_infdescped = db_handler.check_field_value(
                table='parametro2', 
                field='pa2_infdescped', 
                filial_code=selected_filial_code
            )

            if pa2_infacreped == 1 and pa2_infdescped == 1 :
                dav_window.set_focus()
                time.sleep(0.5)
                dav_window.type_keys("{ENTER}")
                logging.info("Verificando se a janela de autorização apareceu...")
                # 1. Faz a verificação rápida com 'win32'
                if _check_for_authorization_win32(main_window, selectors):
                    # 2. Só se a verificação rápida for positiva, chama a função 'uia' para interagir
                    _handle_authorization_dialog(selectors) 
                time.sleep(0.5)
                dav_window.type_keys("{ENTER 5}")
                

                #Se exister o campo tipo de entrega que aparece quando o pa4_tipoentit = 1
                pa4_tipoentit = db_handler.check_field_value(
                    table='parametro4', 
                    field='pa4_tipoentit', 
                    filial_code=selected_filial_code
                )  

                if pa4_tipoentit == 1 :
                   time.sleep(0.5) 
                   dav_window.type_keys("{F1}")
                   input("Deixe o cursor em um tipo de entrega e pressione ENTER e continuar o fluxo")
                   dav_window.set_focus()
                   logging.info("Pressionando ENTER 2x para gravar o item.")
                   dav_window.type_keys('{ENTER 2}')
                    # Atenção : Pedido possui item(s) para entrega, o tipo de entrega será alterado
                   _handle_optional_dialog(selectors['atention_dialog'], "{ENTER}")  
                else :
                    logging.info("Pressionando ENTER 3x para gravar o item.")
                    dav_window.set_focus()
                    dav_window.type_keys('{ENTER 3}')
                    
            elif pa2_infacreped == 0 and pa2_infdescped == 0 : 
                    logging.info("Pressionando ENTER 3x para gravar o item.")
                    dav_window.set_focus()
                    dav_window.type_keys('{ENTER 3}')
                    
        logging.info("Todos os itens selecionados foram lançados com sucesso.")
        logging.info("### TESTE CONCLUÍDO: Criação de DAV ###")

    except Exception as e:
        logging.error(f"Ocorreu um erro durante o teste de criação de DAV: {e}", exc_info=True)