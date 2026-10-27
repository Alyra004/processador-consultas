import re

class OtimizadorConsulta:
    # Seletividade estimada por operador (fração de tuplas que satisfaz o predicado).
    # Quanto menor o valor, mais restritiva é a operação.
    SELETIVIDADE_OPERADOR = {
        "=": 0.1,
        "<": 1 / 3,
        ">": 1 / 3,
        "<=": 1 / 3,
        ">=": 1 / 3,
        "<>": 0.9,
    }
    SELETIVIDADE_CHAVE_PRIMARIA = 0.001  # igualdade na PK retorna no máximo uma tupla

    def __init__(self, dados_parse):
        self.dados = dados_parse
        self.tabelas = dados_parse.get("FROM", [])
        self.campos_select = dados_parse.get("SELECT", [])
        todas_condicoes = list(dados_parse.get("ON", []))

        if dados_parse.get("WHERE"):
            todas_condicoes.append(dados_parse.get("WHERE"))
        self.condicoes_brutas = []

        for bloco in todas_condicoes:
            fragmentos = [self._limpar_parenteses(c.strip()) for c in re.split(r'\s+AND\s+', bloco, flags=re.IGNORECASE)]
            self.condicoes_brutas.extend([f for f in fragmentos if f])

        self.selecoes_por_tabela = {tabela: [] for tabela in self.tabelas}
        self.condicoes_juncao = []
        self.projecoes_por_tabela = {tabela: set() for tabela in self.tabelas}

        self.seletividade_tabela = {tabela: 1.0 for tabela in self.tabelas}
        self.ordem_tabelas = list(self.tabelas)
        self.juncoes_ordenadas = []

    def _limpar_parenteses(self, condicao):
        # Remove parênteses que ficaram desbalanceados após dividir por AND
        while condicao.startswith("(") and condicao.count("(") > condicao.count(")"):
            condicao = condicao[1:].strip()
        while condicao.endswith(")") and condicao.count(")") > condicao.count("("):
            condicao = condicao[:-1].strip()
        while condicao.startswith("(") and condicao.endswith(")"):
            interno = condicao[1:-1].strip()
            if interno.count("(") != interno.count(")"):
                break
            condicao = interno
        return condicao

    def _tabelas_da_condicao(self, condicao):
        tabelas_envolvidas = []
        for tabela in self.tabelas:
            if re.search(r'(?<![\w])' + re.escape(tabela) + r'\.', condicao, re.IGNORECASE):
                tabelas_envolvidas.append(tabela)
        return tabelas_envolvidas

    def _estimar_seletividade(self, condicao, tabela=None):
        m = re.search(r'(<=|>=|<>|=|<|>)', condicao)
        if not m:
            return 1.0
        operador = m.group(1)

        if operador == "=" and tabela:
            lados = [lado.strip() for lado in condicao.split("=", 1)]
            chave_primaria = f"{tabela}.id{tabela}".upper()
            if any(lado.upper() == chave_primaria for lado in lados):
                return self.SELETIVIDADE_CHAVE_PRIMARIA

        return self.SELETIVIDADE_OPERADOR.get(operador, 1.0)

    def aplicar_heuristica_selecao(self):
        
        for condicao in self.condicoes_brutas:
            tabelas_envolvidas = self._tabelas_da_condicao(condicao)
                    
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
            self.projecoes_por_tabela[tabela] = sorted(self.projecoes_por_tabela[tabela])

    def aplicar_heuristica_restritividade(self):
        # Estima o quão restritiva é cada folha (tabela + suas seleções)
        for tabela in self.tabelas:
            seletividade = 1.0
            for condicao in self.selecoes_por_tabela.get(tabela, []):
                seletividade *= self._estimar_seletividade(condicao, tabela)
            self.seletividade_tabela[tabela] = seletividade

        # Ordenação estável: em caso de empate mantém a ordem original do FROM
        self.ordem_tabelas = sorted(self.tabelas, key=lambda t: self.seletividade_tabela[t])

    def aplicar_heuristica_evitar_produto_cartesiano(self):
        if not self.tabelas:
            return

        restantes = list(self.ordem_tabelas)
        ordem_final = [restantes.pop(0)]
        juncoes_pendentes = list(self.condicoes_juncao)
        self.juncoes_ordenadas = []

        while restantes:
            melhor_tabela = None
            melhor_custo = None

            # Procura, entre as tabelas restantes, as que possuem predicado de
            # junção com o conjunto já unido, escolhendo a mais restritiva.
            for tabela in restantes:
                conjunto = set(ordem_final) | {tabela}
                conds = [j for j in juncoes_pendentes
                         if tabela in j["tabelas"] and set(j["tabelas"]) <= conjunto]
                if not conds:
                    continue

                seletividade_juncao = 1.0
                for j in conds:
                    seletividade_juncao *= self._estimar_seletividade(j["condicao"])
                custo = self.seletividade_tabela[tabela] * seletividade_juncao

                if melhor_custo is None or custo < melhor_custo:
                    melhor_tabela, melhor_custo = tabela, custo

            # Nenhuma tabela conectada: produto cartesiano é inevitável,
            # usa a próxima mais restritiva.
            if melhor_tabela is None:
                melhor_tabela = restantes[0]

            restantes.remove(melhor_tabela)
            ordem_final.append(melhor_tabela)

            conjunto = set(ordem_final)
            aplicadas = [j for j in juncoes_pendentes if set(j["tabelas"]) <= conjunto]
            for j in aplicadas:
                juncoes_pendentes.remove(j)

            self.juncoes_ordenadas.append({
                "tabelas": list(ordem_final),
                "nova_tabela": melhor_tabela,
                "condicao": " AND ".join(j["condicao"] for j in aplicadas),
                "cartesiano": not aplicadas
            })

        self.ordem_tabelas = ordem_final

    def otimizar(self):
        self.aplicar_heuristica_selecao()
        self.aplicar_heuristica_projecao()
        self.aplicar_heuristica_restritividade()
        self.aplicar_heuristica_evitar_produto_cartesiano()
        
        return {
            "selecoes": self.selecoes_por_tabela,
            "projecoes": self.projecoes_por_tabela,
            "juncoes": self.juncoes_ordenadas,
            "ordem_tabelas": self.ordem_tabelas,
            "seletividades": self.seletividade_tabela
        }