class ParserSQL:
    def __init__(self):
        self.campos_select = []
        self.tabelas_from = []
        self.condicoes_where = ""
        self.operadores = []
        self.operadores_validos = ['=', '>', '<', '<=', '>=', '<>', 'AND', '(', ')']

    def fazer_parse(self, consulta_sql):
        consulta = " ".join(consulta_sql.split())
        consulta_upper = consulta.upper()

        idx_select = consulta_upper.find("SELECT")
        idx_from = consulta_upper.find("FROM")
        idx_inner = consulta_upper.find("INNER JOIN")
        idx_on = consulta_upper.find("ON")
        idx_where = consulta_upper.find("WHERE")

        if idx_select != -1 and idx_from != -1:
            bloco_select = consulta[idx_select + 7 : idx_from].strip()
            self.campos_select = [campo.strip() for campo in bloco_select.split(",")]

        if idx_from != -1:
            limite_from = len(consulta)
            if idx_inner != -1:
                limite_from = idx_inner
            elif idx_where != -1:
                limite_from = idx_where
                
            bloco_from = consulta[idx_from + 4 : limite_from].strip()
            self.tabelas_from = [tabela.strip() for tabela in bloco_from.split(",")]

        if idx_inner != -1:
            limite_join = len(consulta)
            if idx_on != -1:
                limite_join = idx_on
            elif idx_where != -1:
                limite_join = idx_where
                
            tabela_join = consulta[idx_inner + 10 : limite_join].strip()
            
            if tabela_join not in self.tabelas_from:
                self.tabelas_from.append(tabela_join)

        if idx_where != -1:
            bloco_where = consulta[idx_where + 5 :].strip()
            self.condicoes_where = bloco_where
            
            where_tratado = bloco_where
            where_tratado = where_tratado.replace('>=', ' >= ')
            where_tratado = where_tratado.replace('<=', ' <= ')
            where_tratado = where_tratado.replace('<>', ' <> ')
            where_tratado = where_tratado.replace('=', ' = ')
            where_tratado = where_tratado.replace('>', ' > ')
            where_tratado = where_tratado.replace('<', ' < ')
            where_tratado = where_tratado.replace('(', ' ( ')
            where_tratado = where_tratado.replace(')', ' ) ')
            
            tokens_where = where_tratado.split()
            
            for token in tokens_where:
                if token.upper() in self.operadores_validos:
                    self.operadores.append(token.upper())

        return {
            "SELECT": self.campos_select,
            "FROM": self.tabelas_from,
            "WHERE": self.condicoes_where,
            "OPERADORES": self.operadores
        }