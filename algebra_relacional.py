class AlgebraRelacional:
    def __init__(self, dados_parse):
        self.campos_select = dados_parse.get("SELECT", [])
        self.tabelas_from = dados_parse.get("FROM", [])
        self.condicoes_on = dados_parse.get("ON", [])
        self.condicoes_where = dados_parse.get("WHERE", "")
        
        self.simbolo_projecao = "π"
        self.simbolo_selecao = "σ"
        self.simbolo_juncao = "⨝"
        self.simbolo_cartesiano = "X"

    def montar_bloco_tabelas(self):
        if len(self.tabelas_from) == 1:
            return self.tabelas_from[0]
            
        texto_tabelas = f" {self.simbolo_cartesiano} ".join(self.tabelas_from)
        
        return f"({texto_tabelas})"

    def montar_bloco_selecao(self, texto_tabelas):
        todas_condicoes = list(self.condicoes_on)
        if self.condicoes_where:
            todas_condicoes.append(self.condicoes_where)
            
        if not todas_condicoes:
            return texto_tabelas
            
        condicao_unida = " AND ".join(todas_condicoes)
        texto_selecao = f"{self.simbolo_selecao}_{{{condicao_unida}}}({texto_tabelas})"
        return texto_selecao

    def montar_bloco_projecao(self, texto_selecao):
        if self.campos_select == ["*"]:
            return texto_selecao

        campos_texto = ", ".join(self.campos_select)
        
        texto_projecao = f"{self.simbolo_projecao}_{{{campos_texto}}}({texto_selecao})"
        return texto_projecao

    def gerar_expressao_completa(self):
        passo_1_tabelas = self.montar_bloco_tabelas()
        passo_2_selecao = self.montar_bloco_selecao(passo_1_tabelas)
        passo_final = self.montar_bloco_projecao(passo_2_selecao)
        return passo_final

    def montar_folha_otimizada(self, tabela, dados_otimizados):
        texto = tabela
        condicoes = dados_otimizados.get("selecoes", {}).get(tabela, [])
        if condicoes:
            texto = f"{self.simbolo_selecao}_{{{' AND '.join(condicoes)}}}({texto})"
        colunas = dados_otimizados.get("projecoes", {}).get(tabela, [])
        if colunas and "*" not in self.campos_select:
            texto = f"{self.simbolo_projecao}_{{{', '.join(colunas)}}}({texto})"
        return texto

    def gerar_expressao_otimizada(self, dados_otimizados):
        ordem = dados_otimizados.get("ordem_tabelas") or self.tabelas_from
        if not ordem:
            return ""

        juncoes = dados_otimizados.get("juncoes", [])
        texto = self.montar_folha_otimizada(ordem[0], dados_otimizados)

        for k, tabela in enumerate(ordem[1:]):
            folha = self.montar_folha_otimizada(tabela, dados_otimizados)
            condicao = juncoes[k]["condicao"] if k < len(juncoes) else ""
            if condicao:
                texto = f"({texto} {self.simbolo_juncao}_{{{condicao}}} {folha})"
            else:
                texto = f"({texto} {self.simbolo_cartesiano} {folha})"

        return self.montar_bloco_projecao(texto)