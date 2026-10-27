import re

class ParserSQL:
    def __init__(self):
        self.campos_select = []
        self.tabelas_from = []
        self.condicoes_on = []
        self.condicoes_where = ""
        self.operadores = []
        self.campos_condicoes = []
        self.erros = []
        
        self.operadores_validos = ['=', '>', '<', '<=', '>=', '<>', 'AND', '(', ')']
        self.operadores_nao_suportados = ['OR', 'NOT', 'LIKE', 'IN', 'BETWEEN', 'IS', 'NULL']
        self.padrao_campo = r'[A-Za-z_]\w*(\.[A-Za-z_]\w*)?'
        self.padrao_numero = r'-?\d+(\.\d+)?'

    def _buscar(self, consulta, palavra, inicio=0):
        return re.compile(r'\b' + palavra + r'\b', re.IGNORECASE).search(consulta, inicio)

    def _separar_tokens(self, bloco):
        tratado = re.sub(r"'[^']*'|\"[^\"]*\"", ' #TEXTO# ', bloco)
        
        tratado = tratado.replace('>=', ' #MAIOR_IGUAL# ')
        tratado = tratado.replace('<=', ' #MENOR_IGUAL# ')
        tratado = tratado.replace('<>', ' #DIFERENTE# ')
        
        tratado = tratado.replace('=', ' = ').replace('>', ' > ').replace('<', ' < ')
        tratado = tratado.replace('(', ' ( ').replace(')', ' ) ')
        
        tratado = tratado.replace('#MAIOR_IGUAL#', ' >= ')
        tratado = tratado.replace('#MENOR_IGUAL#', ' <= ')
        tratado = tratado.replace('#DIFERENTE#', ' <> ')
        
        return tratado.split()

    def _analisar_condicao(self, bloco, clausula):
        if not bloco:
            self.erros.append(f"Erro Sintático: Cláusula {clausula} sem condição.")
            return
        
        if bloco.count('(') != bloco.count(')'):
            self.erros.append(f"Erro Sintático: Parênteses desbalanceados na cláusula {clausula} -> '{bloco}'")
        
        for token in self._separar_tokens(bloco):
            token_maiusculo = token.upper()
            
            if token_maiusculo in self.operadores_validos:
                self.operadores.append(token_maiusculo)
            elif token == '#TEXTO#' or re.fullmatch(self.padrao_numero, token):
                continue
            elif token_maiusculo in self.operadores_nao_suportados:
                self.erros.append(f"Erro Sintático: Operador não suportado na cláusula {clausula} -> '{token}'")
            elif re.fullmatch(self.padrao_campo, token):
                if token not in self.campos_condicoes:
                    self.campos_condicoes.append(token)
            else:
                self.erros.append(f"Erro Léxico: Operador ou símbolo inválido na cláusula {clausula} -> '{token}'")

    def fazer_parse(self, consulta_sql):
        consulta = " ".join(consulta_sql.split()).rstrip(";").strip()

        m_select = self._buscar(consulta, "SELECT")
        m_from = self._buscar(consulta, "FROM")
        m_where = self._buscar(consulta, "WHERE")
        padrao_inner = r"INNER\s+JOIN"

        idx_where = m_where.start() if m_where else -1

        if not m_select or m_select.start() != 0:
            self.erros.append("Erro Sintático: A consulta deve começar com o comando SELECT.")
        if not m_from:
            self.erros.append("Erro Sintático: Cláusula FROM não encontrada.")

        if m_select and m_from:
            bloco_select = consulta[m_select.end() : m_from.start()].strip()
            self.campos_select = [campo.strip() for campo in bloco_select.split(",")]
            if "" in self.campos_select:
                self.erros.append("Erro Sintático: Campo vazio ou ausente na cláusula SELECT.")

        if m_from:
            primeiro_inner = self._buscar(consulta, padrao_inner, m_from.end())
            limite_from = len(consulta)
            
            if primeiro_inner:
                limite_from = primeiro_inner.start()
            elif idx_where != -1:
                limite_from = idx_where
                
            bloco_from = consulta[m_from.end() : limite_from].strip()
            self.tabelas_from = [tabela.strip() for tabela in bloco_from.split(",")]
            if "" in self.tabelas_from:
                self.erros.append("Erro Sintático: Tabela vazia ou ausente na cláusula FROM.")
                self.tabelas_from = [tabela for tabela in self.tabelas_from if tabela]

        m_inner = self._buscar(consulta, padrao_inner)
        
        while m_inner:
            m_proximo = self._buscar(consulta, padrao_inner, m_inner.end())
            idx_proximo = m_proximo.start() if m_proximo else -1
            
            m_on = self._buscar(consulta, "ON", m_inner.end())
            if m_on and idx_proximo != -1 and m_on.start() > idx_proximo:
                m_on = None
            if m_on and idx_where != -1 and m_on.start() > idx_where:
                m_on = None
            
            limite_join = len(consulta)
            if m_on:
                limite_join = m_on.start()
            elif idx_proximo != -1:
                limite_join = idx_proximo
            elif idx_where != -1:
                limite_join = idx_where
                
            tabela_join = consulta[m_inner.end() : limite_join].strip()
            
            if not tabela_join:
                self.erros.append("Erro Sintático: INNER JOIN sem tabela informada.")
            elif tabela_join not in self.tabelas_from:
                self.tabelas_from.append(tabela_join)
                
            if m_on:
                limite_on = len(consulta)
                if idx_proximo != -1:
                    limite_on = idx_proximo
                elif idx_where != -1:
                    limite_on = idx_where
                
                condicao = consulta[m_on.end() : limite_on].strip()
                self._analisar_condicao(condicao, "ON")
                if condicao:
                    self.condicoes_on.append(condicao)
                
            m_inner = m_proximo

        if m_where:
            self.condicoes_where = consulta[m_where.end() :].strip()
            self._analisar_condicao(self.condicoes_where, "WHERE")

        return {
            "SELECT": self.campos_select,
            "FROM": self.tabelas_from,
            "ON": self.condicoes_on,
            "WHERE": self.condicoes_where,
            "OPERADORES": self.operadores,
            "CAMPOS_CONDICOES": self.campos_condicoes,
            "ERROS": self.erros
        }