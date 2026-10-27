import re
import mysql.connector
from mysql.connector import Error

class ValidadorDB:
    def __init__(self, host='localhost', user='root', password='', database='BD_Vendas'):
        self.conexao = None
        self.tabela_dos_campos = {}
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

    def esta_conectado(self):
        return self.conexao is not None and self.conexao.is_connected()

    def validar_referencia_campo(self, campo, tabelas, clausula):
        if "." in campo:
            nome_tabela, nome_campo = [parte.strip() for parte in campo.split(".", 1)]
            tabelas_consulta = [tabela.upper() for tabela in tabelas]

            if nome_tabela.upper() not in tabelas_consulta:
                return f"Erro: A tabela '{nome_tabela}' do campo '{campo}' ({clausula}) não faz parte da consulta."
            if not self.validar_campo(nome_tabela, nome_campo):
                return f"Erro: O campo '{nome_campo}' ({clausula}) não pertence à tabela '{nome_tabela}'."
            return None

        tabelas_com_campo = [tabela for tabela in tabelas if self.validar_campo(tabela, campo)]

        if not tabelas_com_campo:
            return f"Erro: O campo '{campo}' ({clausula}) não foi encontrado nas tabelas especificadas."
        if len(tabelas_com_campo) > 1:
            return f"Erro: O campo '{campo}' ({clausula}) é ambíguo, existe nas tabelas {', '.join(tabelas_com_campo)}."

        self.tabela_dos_campos[campo] = tabelas_com_campo[0]
        return None

    def validar_consulta(self, dados_parse):
        if not self.esta_conectado():
            return ["Erro: Não foi possível conectar ao banco de dados BD_Vendas."]

        erros = []
        tabelas = dados_parse.get("FROM", [])

        for tabela in tabelas:
            if not self.validar_tabela(tabela):
                erros.append(f"Erro: A tabela '{tabela}' não existe no banco de dados.")

        if erros:
            return erros

        campos_por_clausula = [("SELECT", campo) for campo in dados_parse.get("SELECT", []) if campo != "*"]
        campos_por_clausula += [("ON/WHERE", campo) for campo in dados_parse.get("CAMPOS_CONDICOES", [])]

        for clausula, campo in campos_por_clausula:
            erro = self.validar_referencia_campo(campo, tabelas, clausula)
            if erro:
                erros.append(erro)

        return erros

    def _qualificar_texto(self, texto):
        partes = re.split(r"('[^']*'|\"[^\"]*\")", texto)

        for i, parte in enumerate(partes):
            if parte.startswith(("'", '"')):
                continue
            for campo, tabela in self.tabela_dos_campos.items():
                parte = re.sub(r'(?<![\w.])' + re.escape(campo) + r'(?![\w.])', f"{tabela}.{campo}", parte)
            partes[i] = parte

        return "".join(partes)

    def qualificar_campos(self, dados_parse):
        dados_qualificados = dict(dados_parse)
        dados_qualificados["SELECT"] = [self._qualificar_texto(campo) for campo in dados_parse.get("SELECT", [])]
        dados_qualificados["ON"] = [self._qualificar_texto(condicao) for condicao in dados_parse.get("ON", [])]
        dados_qualificados["WHERE"] = self._qualificar_texto(dados_parse.get("WHERE", ""))
        dados_qualificados["CAMPOS_CONDICOES"] = [self._qualificar_texto(campo) for campo in dados_parse.get("CAMPOS_CONDICOES", [])]
        return dados_qualificados

    def fechar_conexao(self):
        if self.conexao and self.conexao.is_connected():
            self.conexao.close()