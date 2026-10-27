import re

class ParserSQL:
    def __init__(self):
        self.campos_select = []
        self.tabelas_from = []
        self.condicoes_on = []
        self.condicoes_where = ""
        self.operadores = []
        self.erros = []
        
        self.operadores_validos = ['=', '>', '<', '<=', '>=', '<>', 'AND', '(', ')']

    def _buscar(self, consulta, palavra, inicio=0):
        return re.compile(r'\b' + palavra + r'\b', re.IGNORECASE).search(consulta, inicio)

    def fazer_parse(self, consulta_sql):
        consulta = " ".join(consulta_sql.split())

        m_select = self._buscar(consulta, "SELECT")
        m_from = self._buscar(consulta, "FROM")
        m_where = self._buscar(consulta, "WHERE")
        padrao_inner = r"INNER\s+JOIN"

        idx_where = m_where.start() if m_where else -1

        if m_select and m_from:
            bloco_select = consulta[m_select.end() : m_from.start()].strip()
            self.campos_select = [campo.strip() for campo in bloco_select.split(",")]

        if m_from:
            primeiro_inner = self._buscar(consulta, padrao_inner, m_from.end())
            limite_from = len(consulta)
            
            if primeiro_inner:
                limite_from = primeiro_inner.start()
            elif idx_where != -1:
                limite_from = idx_where
                
            bloco_from = consulta[m_from.end() : limite_from].strip()
            self.tabelas_from = [tabela.strip() for tabela in bloco_from.split(",")]

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
            
            if tabela_join not in self.tabelas_from:
                self.tabelas_from.append(tabela_join)
                
            if m_on:
                limite_on = len(consulta)
                if idx_proximo != -1:
                    limite_on = idx_proximo
                elif idx_where != -1:
                    limite_on = idx_where
                
                condicao = consulta[m_on.end() : limite_on].strip()
                self.condicoes_on.append(condicao)
                
            m_inner = m_proximo

        if m_where:
            bloco_where = consulta[m_where.end() :].strip()
            self.condicoes_where = bloco_where
            
            where_tratado = bloco_where
            
            where_tratado = where_tratado.replace('>=', ' #MAIOR_IGUAL# ')
            where_tratado = where_tratado.replace('<=', ' #MENOR_IGUAL# ')
            where_tratado = where_tratado.replace('<>', ' #DIFERENTE# ')
            
            where_tratado = where_tratado.replace('=', ' = ').replace('>', ' > ').replace('<', ' < ')
            where_tratado = where_tratado.replace('(', ' ( ').replace(')', ' ) ')
            
            where_tratado = where_tratado.replace('#MAIOR_IGUAL#', ' >= ')
            where_tratado = where_tratado.replace('#MENOR_IGUAL#', ' <= ')
            where_tratado = where_tratado.replace('#DIFERENTE#', ' <> ')
            
            tokens_where = where_tratado.split()
            
            for token in tokens_where:
                if token.upper() in self.operadores_validos:
                    self.operadores.append(token.upper())
                else:
                    token_limpo = token.replace('.', '').replace("'", "").replace('"', '').replace('-', '').replace('_', '')
                    
                    if not token_limpo.isalnum() and token_limpo != "":
                        self.erros.append(f"Erro Léxico: Operador ou símbolo inválido encontrado -> '{token}'")

        return {
            "SELECT": self.campos_select,
            "FROM": self.tabelas_from,
            "ON": self.condicoes_on,
            "WHERE": self.condicoes_where,
            "OPERADORES": self.operadores,
            "ERROS": self.erros
        }