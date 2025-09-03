import mysql.connector
from mysql.connector import pooling
import pandas as pd
import logging
import time

class DBHandler:
    def __init__(self, config):
        # Dentro da função __init__ em db_handler.py
        try:
            # Usamos config.get('port', 3306) para usar a porta do arquivo .ini
            # ou a porta 3306 como padrão se não for encontrada.
            db_port = int(config.get('port', 3306))

            self.pool = pooling.MySQLConnectionPool(
                pool_name=config['pool_name'],
                pool_size=int(config['pool_size']),
                host=config['host'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                port=db_port,
                auth_plugin='mysql_native_password',  
                ssl_disabled=True                     
            )
            logging.info(f"Pool de conexões com MySQL para {config['host']}:{db_port} criado com sucesso.")
            # ...
        except mysql.connector.Error as err:
            logging.error(f"Erro ao criar o pool de conexões com o MySQL: {err}")
            raise

    def execute_query(self, query, params=None):
        """Executa uma query SELECT e retorna um DataFrame do Pandas."""
        try:
            with self.pool.get_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    logging.info(f"Executando query: {query.strip().splitlines()[0]}...")
                    cursor.execute(query, params)
                    result = cursor.fetchall()
                    return pd.DataFrame(result) if result else pd.DataFrame()
        except mysql.connector.Error as err:
            logging.error(f"Erro ao executar query: {err}\nQuery: {query}")
            return pd.DataFrame()

    def get_db_version(self):
        query = "SELECT NOV_VERSAO FROM novidade ORDER BY nov_codigo DESC LIMIT 1;"
        return self.execute_query(query)

    def get_naturezas_operacao(self):
        query = """
        SELECT n.Nat_Codigo AS codigo_natureza, n.Nat_Desc AS descricao
        FROM natoper n JOIN classificanatop c ON n.NAT_CNTCODIGOS = c.CNT_CODIGO
        WHERE n.NAT_LIBERAVENDA = 1 AND c.CNT_TIPONATOP = 'V' AND n.Nat_Ativo = 1
        AND n.Nat_LanPreVenda = 1 AND c.CNT_Devolucao = 0 AND c.CNT_DEVOLNF = 0
        AND n.Nat_MDFCODIGO = 55 AND n.NAT_VENDAFUTURA = 0 AND n.NAT_CODIGO <> 'ORC'
        ORDER BY n.Nat_Desc;
        """
        return self.execute_query(query)

    def check_field_value(self, table, field, condition_field, condition_value):
        if condition_field is not None and "parametro" not in field :
            query = f"SELECT {field} FROM {table} WHERE {condition_field} = %s"
            df = self.execute_query(query, (condition_value,))
        else :
            query = f"SELECT {field} FROM {table}"
            df = self.execute_query(query)
        if not df.empty:
            return df.iloc[0][field]
        return None

    def get_clientes(self):
        query = """
        SELECT p.PES_CODIGO AS codigo_cliente, p.pes_razao AS nome_cliente
        FROM cliente c JOIN pessoa p ON c.CLI_PESCODIGO = p.PES_CODIGO
        WHERE c.cli_limitecre > 0 AND p.PES_ATIVO = 1 AND c.cli_bloqfin = 0
        AND c.CLI_SITUAC1 = '' AND c.CLI_SITUAC2 = '' AND c.CLI_SITUAC3 = '' AND c.CLI_SITUAC4 = ''
        ORDER BY p.pes_razao;
        """
        return self.execute_query(query)

    def get_vendedores(self):
        query = """
        SELECT c.CLB_CODIGO AS codigo_colaborador, c.CLB_RAZAO AS nome_vendedor
        FROM vendedor v JOIN colaborador c ON v.ven_clbcodigo = c.CLB_CODIGO
        JOIN cargo cg ON c.CLB_CRGCODIGO = cg.CRG_CODIGO
        WHERE c.CLB_ATIVO = 1 ORDER BY c.CLB_RAZAO;
        """
        return self.execute_query(query)

    def get_formas_pagamento(self, cliente_codigo):
        query = """
        SELECT DISTINCT fp.FPG_CODIGO AS codigo_forma, fp.FPG_DESC AS descricao
        FROM pessoa p
        JOIN (
            SELECT CLI_PESCODIGO, CLI_FPGCODIGO FROM cliente
            UNION
            SELECT FPE_PESCODIGO, FPE_FPGCODIGO FROM formapgpessoa
        ) AS formas_liberadas ON p.PES_CODIGO = formas_liberadas.CLI_PESCODIGO
        JOIN formapagto fp ON formas_liberadas.CLI_FPGCODIGO = fp.FPG_CODIGO
        WHERE p.PES_ATIVO = 1 AND fp.FPG_ATIVO = 1 AND p.PES_CODIGO = %s
        ORDER BY fp.FPG_DESC;
        """
        return self.execute_query(query, (cliente_codigo,))

    def get_all_formas_pagamento(self):
        query = """
        SELECT FPG_CODIGO AS codigo_forma, FPG_DESC AS descricao FROM formapagto
        WHERE FPG_ATIVO = 1 AND fpg_habvenda = 1 AND fpg_receber = 1 ORDER BY FPG_DESC;
        """
        return self.execute_query(query)
        
    def get_condicoes_pagamento(self, cliente_codigo, forma_pagamento_codigo):
        query = """
        SELECT DISTINCT cp.CPG_CODIGO as codigo_condicao, cp.CPG_DESC AS descricao
        FROM (
            SELECT CLI_PESCODIGO, CLI_CPGCODIGO FROM cliente
            UNION
            SELECT CPE_PESCODIGO, CPE_CPGCODIGO FROM condpgpessoa
        ) AS condicoes_liberadas
        JOIN pessoa p ON condicoes_liberadas.CLI_PESCODIGO = p.PES_CODIGO
        JOIN condpagto cp ON condicoes_liberadas.CLI_CPGCODIGO = cp.CPG_CODIGO
        WHERE p.PES_ATIVO = 1 AND cp.CPG_ATIVO = 1 AND p.PES_CODIGO = %s
        AND NOT EXISTS (
            SELECT 1 FROM condnforma cnf
            WHERE cnf.cnf_cpgcodigo = condicoes_liberadas.CLI_CPGCODIGO
            AND cnf.cnf_fpgcodigo = %s
        )
        ORDER BY cp.CPG_DESC;
        """
        return self.execute_query(query, (cliente_codigo, forma_pagamento_codigo))

    def get_all_condicoes_pagamento(self, forma_pagamento_codigo):
        query = """
        SELECT cp.CPG_CODIGO AS codigo_condicao, cp.CPG_DESC AS descricao
        FROM condpagto cp
        WHERE cp.CPG_ATIVO = 1 AND NOT EXISTS (
            SELECT 1 FROM condnforma cnf
            WHERE cnf.cnf_cpgcodigo = cp.CPG_CODIGO AND cnf.cnf_fpgcodigo = %s
        )
        ORDER BY cp.CPG_DESC;
        """
        return self.execute_query(query, (forma_pagamento_codigo,))
    
    def get_available_products(self):
        query = """
        SELECT codigo_produto, nome_produto, EstoqueDisponivel
        FROM (
            SELECT
                pf.pfi_procodigo AS codigo_produto, p.pro_desc AS nome_produto,
                (COALESCE(SUM(lp.lpd_estfisico), 0) - pf.pfi_estpenentre) AS EstoqueDisponivel
            FROM produto p
            INNER JOIN produtofilial pf ON p.pro_codigo = pf.pfi_procodigo
            INNER JOIN unidadepro up ON p.pro_codigo = up.unp_procodigo AND up.unp_padestoque = 1
            LEFT JOIN localfilial lf ON pf.pfi_filcodigo = lf.lcf_filcodigo
            LEFT JOIN localprod lp ON lf.lcf_lcecodigo = lp.lpd_lcecodigo AND pf.pfi_procodigo = lp.lpd_procodigo
            WHERE p.pro_ativo = 1 AND (pf.pfi_inativo <> 1 OR pf.pfi_inativo IS NULL) AND p.pro_contlote = 0
            GROUP BY pf.pfi_procodigo, p.pro_desc, pf.pfi_estpenentre
            UNION ALL
            SELECT
                pf.pfi_procodigo AS codigo_produto, p.pro_desc AS nome_produto,
                (COALESCE(SUM(pl.ple_estfisico), 0) - pf.pfi_estpenentre) AS EstoqueDisponivel
            FROM produto p
            INNER JOIN produtofilial pf ON p.pro_codigo = pf.pfi_procodigo
            INNER JOIN unidadepro up ON p.pro_codigo = up.unp_procodigo AND up.unp_padestoque = 1
            LEFT JOIN localfilial lf ON pf.pfi_filcodigo = lf.lcf_filcodigo
            LEFT JOIN produtolote pl ON lf.lcf_lcecodigo = pl.ple_lcecodigo AND pf.pfi_procodigo = pl.ple_procodigo
            WHERE p.pro_ativo = 1 AND (pf.pfi_inativo <> 1 OR pf.pfi_inativo IS NULL) AND p.pro_contlote = 1
            GROUP BY pf.pfi_procodigo, p.pro_desc, pf.pfi_estpenentre
        ) AS EstoqueCalculado
        WHERE EstoqueDisponivel > 0
        ORDER BY codigo_produto;
        """
        return self.execute_query(query)
    
    def get_product_unit_counts(self, product_codes):
        if not product_codes:
            return pd.DataFrame()
        
        # Formata a lista de códigos para a cláusula IN do SQL
        format_strings = ','.join(['%s'] * len(product_codes))
        query = f"""
        SELECT
            p.pro_codigo AS codigo_produto,
            COUNT(up.unp_unidade) AS total_unidades_ativas
        FROM produto p
        JOIN unidadepro up ON p.pro_codigo = up.unp_procodigo
        WHERE up.unp_ativo = 1 AND p.pro_ativo = 1 AND p.pro_codigo IN ({format_strings})
        GROUP BY p.pro_codigo, p.pro_desc
        ORDER BY p.pro_codigo;
        """
        return self.execute_query(query, tuple(product_codes))
    
    def get_sales_orders_for_today(self):
        """Busca os pedidos de venda emitidos na data atual."""
        # Obtém a data atual no formato YYYYMMDD
        today_date = time.strftime('%Y%m%d')
        
        query = """
        SELECT ped_numero, ped_spvcodigo 
        FROM pedidos
        INNER JOIN natoper ON Ped_NatCodigo = Nat_Codigo
        INNER JOIN classificanatop ON NAT_CNTCODIGOS = CNT_CODIGO
        WHERE Ped_DtEmissao = %s 
          AND NAT_LIBERAVENDA = 1 
          AND CNT_TIPONATOP = 'V' 
          AND Nat_Ativo = 1
          AND Nat_LanPreVenda = 1 
          AND CNT_Devolucao = 0 
          AND CNT_DEVOLNF = 0
          AND Nat_MDFCODIGO = 55 
          AND NAT_VENDAFUTURA = 0 
          AND NAT_CODIGO <> 'ORC';
        """
        # Passa a data como um parâmetro para a query
        return self.execute_query(query, (today_date,))

    def close_pool(self):
        """Fecha todas as conexões no pool."""
        # Esta função é chamada implicitamente quando o programa termina, mas é uma boa prática.
        logging.info("Fechando pool de conexões com o MySQL.")

