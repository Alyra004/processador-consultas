import re

class OtimizadorConsulta:
    def __init__(self, dados_parse):
        self.dados = dados_parse
        self.tabelas = dados_parse.get("FROM", [])
        self.campos_select = dados_parse.get("SELECT", [])
        todas_condicoes = list(dados_parse.get("ON", []))

        if dados_parse.get("WHERE"):
            todas_condicoes.append(dados_parse.get("WHERE"))
        self.condicoes_brutas = []

        for bloco in todas_condicoes:
            fragmentos = [c.strip() for c in re.split(r'\s+AND\s+', bloco, flags=re.IGNORECASE)]
            self.condicoes_brutas.extend(fragmentos)

        self.selecoes_por_tabela = {tabela: [] for tabela in self.tabelas}
        self.condicoes_juncao = []
        self.projecoes_por_tabela = {tabela: set() for tabela in self.tabelas}

    def aplicar_heuristica_selecao(self):
        
        for condicao in self.condicoes_brutas:
            tabelas_envolvidas = []
            
            for tabela in self.tabelas:
                if f"{tabela}.".upper() in condicao.upper():
                    tabelas_envolvidas.append(tabela)
                    
            if len(tabelas_envolvidas) == 1:
                tabela_alvo = tabelas_envolvidas[0]
                self.selecoes_por_tabela[tabela_alvo].append(condicao)
                
            elif len(tabelas_envolvidas) == 2:
                self.condicoes_juncao.append({
                    "tabelas": tabelas_envolvidas,
                    "condicao": condicao
                })
            else: #fallback
                self.condicoes_juncao.append({
                    "tabelas": self.tabelas,
                    "condicao": condicao
                })

    def aplicar_heuristica_projecao(self):
        
        for campo in self.campos_select:
            if campo == "*":
                continue
                
            for tabela in self.tabelas:
                if campo.upper().startswith(f"{tabela}.".upper()):
                    self.projecoes_por_tabela[tabela].add(campo)
                    break

        for condicao in self.condicoes_brutas:
            palavras = re.split(r'[ >=<()]+', condicao)
            
            for palavra in palavras:
                for tabela in self.tabelas:
                    if palavra.upper().startswith(f"{tabela}.".upper()):
                        self.projecoes_por_tabela[tabela].add(palavra)
                        break

        for tabela in self.projecoes_por_tabela:
            self.projecoes_por_tabela[tabela] = list(self.projecoes_por_tabela[tabela])

    def otimizar(self):
        self.aplicar_heuristica_selecao()
        self.aplicar_heuristica_projecao()
        
        return {
            "selecoes": self.selecoes_por_tabela,
            "projecoes": self.projecoes_por_tabela,
            "juncoes": self.condicoes_juncao
        }