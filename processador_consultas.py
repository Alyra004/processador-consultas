class NoOperador:
    def __init__(self, tipo, simbolo, parametro="", filhos=None):
        self.tipo = tipo            
        self.simbolo = simbolo
        self.parametro = parametro  
        self.filhos = filhos or []
        self.resultado = None       


class ProcessadorConsultas:
    SIMBOLO_PROJECAO = "π"
    SIMBOLO_SELECAO = "σ"
    SIMBOLO_JUNCAO = "⨝"
    SIMBOLO_CARTESIANO = "X"

    def __init__(self, dados_parse, dados_otimizados):
        self.campos_select = dados_parse.get("SELECT", [])
        self.tabelas_from = dados_parse.get("FROM", [])
        self.dados_otimizados = dados_otimizados
        self.raiz = None

    def _montar_folha(self, tabela):
        no = NoOperador("tabela", "", tabela)

        condicoes = self.dados_otimizados.get("selecoes", {}).get(tabela, [])
        if condicoes:
            no = NoOperador("selecao", self.SIMBOLO_SELECAO, " AND ".join(condicoes), [no])

        colunas = self.dados_otimizados.get("projecoes", {}).get(tabela, [])
        if colunas and "*" not in self.campos_select:
            no = NoOperador("projecao", self.SIMBOLO_PROJECAO, ", ".join(colunas), [no])

        return no

    def construir_grafo(self):
        ordem = self.dados_otimizados.get("ordem_tabelas") or self.tabelas_from
        if not ordem:
            return None

        juncoes = self.dados_otimizados.get("juncoes", [])
        no_atual = self._montar_folha(ordem[0])

        for k, tabela in enumerate(ordem[1:]):
            folha = self._montar_folha(tabela)
            condicao = juncoes[k]["condicao"] if k < len(juncoes) else ""
            if condicao:
                no_atual = NoOperador("juncao", self.SIMBOLO_JUNCAO, condicao, [no_atual, folha])
            else:
                no_atual = NoOperador("produto", self.SIMBOLO_CARTESIANO, "", [no_atual, folha])

        if "*" not in self.campos_select:
            no_atual = NoOperador("projecao", self.SIMBOLO_PROJECAO, ", ".join(self.campos_select), [no_atual])

        self.raiz = no_atual
        return self.raiz

    def _descricao_entrada(self, no):
        return no.parametro if no.tipo == "tabela" else no.resultado

    def gerar_ordem_execucao(self):
        if self.raiz is None:
            self.construir_grafo()
        if self.raiz is None:
            return []

        passos = []

        def visitar(no):
            for filho in no.filhos:
                visitar(filho)

            if no.tipo == "tabela":
                return

            no.resultado = f"R{len(passos) + 1}"
            entradas = [self._descricao_entrada(f) for f in no.filhos]

            if no.tipo in ("selecao", "projecao"):
                expressao = f"{no.simbolo}_{{{no.parametro}}}({entradas[0]})"
                acao = "Seleção" if no.tipo == "selecao" else "Projeção"
            elif no.tipo == "juncao":
                expressao = f"{entradas[0]} {no.simbolo}_{{{no.parametro}}} {entradas[1]}"
                acao = "Junção"
            else:
                expressao = f"{entradas[0]} {no.simbolo} {entradas[1]}"
                acao = "Produto Cartesiano"

            passos.append({
                "resultado": no.resultado,
                "operacao": acao,
                "expressao": expressao
            })

        visitar(self.raiz)

        if not passos:
            passos.append({
                "resultado": "R1",
                "operacao": "Leitura",
                "expressao": self.raiz.parametro
            })

        return passos

    def gerar_texto_plano(self):
        passos = self.gerar_ordem_execucao()
        linhas = []
        for i, passo in enumerate(passos, start=1):
            linhas.append(f"{i}. [{passo['operacao']}] {passo['resultado']} ← {passo['expressao']}")
        if passos:
            linhas.append(f"Resultado final: {passos[-1]['resultado']}")
        return "\n".join(linhas)
