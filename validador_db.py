import mysql.connector
from mysql.connector import Error

class ValidadorDB:
    def __init__(self, host='localhost', user='root', password='', database='BD_Vendas'):
        self.conexao = None
        try:
            self.conexao = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
        except Error as e:
            print(f"Erro ao conectar com o banco: {e}")

    def validar_tabela(self, nome_tabela):
        if self.conexao and self.conexao.is_connected():
            cursor = self.conexao.cursor()
            query = "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'BD_Vendas' AND TABLE_NAME = %s"
            cursor.execute(query, (nome_tabela,))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado[0] > 0
        return False

    def validar_campo(self, nome_tabela, nome_campo):
        if self.conexao and self.conexao.is_connected():
            cursor = self.conexao.cursor()
            query = "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'BD_Vendas' AND TABLE_NAME = %s AND COLUMN_NAME = %s"
            cursor.execute(query, (nome_tabela, nome_campo))
            resultado = cursor.fetchone()
            cursor.close()
            return resultado[0] > 0
        return False

    def validar_consulta(self, dados_parse):
        erros = []
        tabelas = dados_parse.get("FROM", [])
        campos = dados_parse.get("SELECT", [])

        for tabela in tabelas:
            if not self.validar_tabela(tabela):
                erros.append(f"Erro: A tabela '{tabela}' não existe no banco de dados.")

        for campo in campos:
            if campo == "*":
                continue 
            
            campo_real = campo.split(".")[-1].strip()
            
            campo_valido = False
            for tabela in tabelas:
                if self.validar_campo(tabela, campo_real):
                    campo_valido = True
                    break
            
            if not campo_valido:
                erros.append(f"Erro: O campo '{campo}' não foi encontrado nas tabelas especificadas.")

        return erros

    def fechar_conexao(self):
        if self.conexao and self.conexao.is_connected():
            self.conexao.close()