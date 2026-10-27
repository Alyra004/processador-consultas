import tkinter as tk
import tkinter.font as tkfont

class GeradorGrafo:
    FONTE_SIMBOLO = ("Arial", 14, "bold")
    FONTE_JUNCAO = ("Segoe UI Symbol", 14, "bold")
    SIMBOLO_JUNCAO = "⋈"
    FONTE_SUB = ("Arial", 9)
    FONTE_TABELA = ("Arial", 12)

    def __init__(self, canvas, dados_parse):
        self.canvas = canvas
        self.dados = dados_parse
        self.canvas.delete("all")

    def _fonte_simbolo(self, simbolo):
        if simbolo == self.SIMBOLO_JUNCAO:
            return self.FONTE_JUNCAO
        return self.FONTE_SIMBOLO

    def _largura_texto_no(self, simbolo, subscrito=""):
        largura = tkfont.Font(font=self._fonte_simbolo(simbolo)).measure(simbolo)
        if subscrito:
            largura += tkfont.Font(font=self.FONTE_SUB).measure(subscrito) + 4
        return largura

    def _desenhar_no(self, x, y, simbolo, subscrito=""):
        id_simbolo = self.canvas.create_text(x, y, text=simbolo, font=self._fonte_simbolo(simbolo), anchor=tk.W)
        id_sub = None
        if subscrito:
            id_sub = self.canvas.create_text(x, y + 6, text=subscrito, font=self.FONTE_SUB, anchor=tk.W)

        bbox_simbolo = self.canvas.bbox(id_simbolo)
        largura_simbolo = bbox_simbolo[2] - bbox_simbolo[0]
        largura_sub = 0
        if id_sub:
            self.canvas.move(id_sub, largura_simbolo + 2, 0)
            bbox_sub = self.canvas.bbox(id_sub)
            largura_sub = bbox_sub[2] - bbox_sub[0] + 2

        largura_total = largura_simbolo + largura_sub
        deslocamento = -largura_total / 2
        self.canvas.move(id_simbolo, deslocamento, 0)
        if id_sub:
            self.canvas.move(id_sub, deslocamento, 0)

        return y - 14, y + 18

    def _desenhar_tabela(self, x, y, nome):
        id_texto = self.canvas.create_text(x, y, text=nome, font=self.FONTE_TABELA)
        bbox = self.canvas.bbox(id_texto)
        return bbox[1] - 2

    def _linha(self, x_filho, topo_filho, x_pai, base_pai, arrow=tk.LAST):
        self.canvas.create_line(x_filho, topo_filho, x_pai, base_pai, width=1, fill="black", arrow=arrow)

    def desenhar_nao_otimizado(self):
        tabelas = self.dados.get("FROM", []) or ["(vazio)"]
        condicoes_on = self.dados.get("ON", [])
        condicao_where = self.dados.get("WHERE", "")
        campos = self.dados.get("SELECT", [])

        todas_condicoes = list(condicoes_on)
        if condicao_where:
            todas_condicoes.append(condicao_where)
        condicao_unida = " AND ".join(todas_condicoes)

        espaco_x = 300
        passo_y = 90
        margem_x = 150
        qtd_juncoes = len(tabelas) - 1

        y_atual = 40

        y_proj = y_atual
        y_atual += passo_y

        y_sel = None
        if condicao_unida:
            y_sel = y_atual
            y_atual += passo_y

        y_juncoes = []
        for _ in range(qtd_juncoes):
            y_juncoes.append(y_atual)
            y_atual += passo_y
        y_juncoes.reverse()

        y_tabelas = y_atual

        x_tabelas = [margem_x + i * espaco_x for i in range(len(tabelas))]

        x_juncoes = []
        x_esq = x_tabelas[0]
        for k in range(qtd_juncoes):
            x_j = (x_esq + x_tabelas[k + 1]) / 2
            x_juncoes.append(x_j)
            x_esq = x_j

        topos_tabelas = [self._desenhar_tabela(x_tabelas[i], y_tabelas, tabelas[i]) for i in range(len(tabelas))]

        bases_juncoes = []
        topos_juncoes = []
        for k in range(qtd_juncoes):
            simbolo, sub = "X", ""
            topo, base = self._desenhar_no(x_juncoes[k], y_juncoes[k], simbolo, sub)
            topos_juncoes.append(topo)
            bases_juncoes.append(base)

            if k == 0:
                self._linha(x_tabelas[0], topos_tabelas[0], x_juncoes[k], base)
            else:
                self._linha(x_juncoes[k - 1], topos_juncoes[k - 1], x_juncoes[k], base)
            self._linha(x_tabelas[k + 1], topos_tabelas[k + 1], x_juncoes[k], base)

        if qtd_juncoes > 0:
            x_filho, topo_filho = x_juncoes[-1], topos_juncoes[-1]
        else:
            x_filho, topo_filho = x_tabelas[0], topos_tabelas[0]

        if y_sel is not None:
            topo_sel, base_sel = self._desenhar_no(x_filho, y_sel, "σ", condicao_unida)
            self._linha(x_filho, topo_filho, x_filho, base_sel)
            topo_filho = topo_sel

        #if campos != ["*"]:
        topo_proj, base_proj = self._desenhar_no(x_filho, y_proj, "π", ", ".join(campos))
        self._linha(x_filho, topo_filho, x_filho, base_proj)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0] - 30, bbox[1] - 30, bbox[2] + 30, bbox[3] + 30))

    def desenhar_otimizado(self, dados_otimizados):
        tabelas = self.dados.get("FROM", []) or ["(vazio)"]
        
        selecoes = dados_otimizados.get("selecoes", {})
        projecoes = dados_otimizados.get("projecoes", {})
        juncoes = dados_otimizados.get("juncoes", [])
        campos_finais = self.dados.get("SELECT", [])

        espaco_minimo = 40
        passo_y = 80
        margem_x = 60
        qtd_juncoes = len(tabelas) - 1

        y_tabelas = 40 + (qtd_juncoes * passo_y) + (passo_y * 3)

        larguras_pilares = []
        for tabela in tabelas:
            largura = tkfont.Font(font=self.FONTE_TABELA).measure(tabela)
            condicoes_tabela = selecoes.get(tabela, [])
            if condicoes_tabela:
                largura = max(largura, self._largura_texto_no("σ", " AND ".join(condicoes_tabela)))
            colunas_tabela = projecoes.get(tabela, [])
            if colunas_tabela and "*" not in campos_finais:
                largura = max(largura, self._largura_texto_no("π", ", ".join(colunas_tabela)))
            larguras_pilares.append(largura)

        x_tabelas = []
        x_cursor = margem_x
        for largura in larguras_pilares:
            x_tabelas.append(x_cursor + largura / 2)
            x_cursor += largura + espaco_minimo

        topos_pilares = []
        x_pilares = list(x_tabelas)

        for i, tabela in enumerate(tabelas):
            x_atual = x_tabelas[i]
            y_atual = y_tabelas
            
            topo_atual = self._desenhar_tabela(x_atual, y_atual, tabela)
            
            condicoes_tabela = selecoes.get(tabela, [])
            if condicoes_tabela:
                condicao_unida = " AND ".join(condicoes_tabela)
                y_atual -= passo_y
                topo_sel, base_sel = self._desenhar_no(x_atual, y_atual, "σ", condicao_unida)
                self._linha(x_atual, topo_atual, x_atual, base_sel)
                topo_atual = topo_sel
                
            colunas_tabela = projecoes.get(tabela, [])
            if colunas_tabela and "*" not in campos_finais:
                colunas_unidas = ", ".join(colunas_tabela)
                y_atual -= passo_y
                topo_proj, base_proj = self._desenhar_no(x_atual, y_atual, "π", colunas_unidas)
                self._linha(x_atual, topo_atual, x_atual, base_proj)
                topo_atual = topo_proj
                
            topos_pilares.append(topo_atual)

        y_atual_j = 40 + passo_y
        y_juncoes = []
        for _ in range(qtd_juncoes):
            y_juncoes.append(y_atual_j)
            y_atual_j += passo_y
        y_juncoes.reverse()

        x_juncoes = []
        x_esq = x_pilares[0]
        for k in range(qtd_juncoes):
            x_j = (x_esq + x_pilares[k + 1]) / 2
            x_juncoes.append(x_j)
            x_esq = x_j

        bases_juncoes = []
        topos_juncoes = []
        for k in range(qtd_juncoes):
            condicao_sub = ""
            if k < len(juncoes):
                condicao_sub = juncoes[k]["condicao"]

            simbolo_no = self.SIMBOLO_JUNCAO if condicao_sub else "X"
            topo, base = self._desenhar_no(x_juncoes[k], y_juncoes[k], simbolo_no, condicao_sub)
            topos_juncoes.append(topo)
            bases_juncoes.append(base)

            if k == 0:
                self._linha(x_pilares[0], topos_pilares[0], x_juncoes[k], base)
            else:
                self._linha(x_juncoes[k - 1], topos_juncoes[k - 1], x_juncoes[k], base)
            self._linha(x_pilares[k + 1], topos_pilares[k + 1], x_juncoes[k], base)

        if qtd_juncoes > 0:
            x_filho, topo_filho = x_juncoes[-1], topos_juncoes[-1]
        else:
            x_filho, topo_filho = x_pilares[0], topos_pilares[0]

        topo_proj_final, base_proj_final = self._desenhar_no(x_filho, 40, "π", ", ".join(campos_finais))
        self._linha(x_filho, topo_filho, x_filho, base_proj_final)

        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(bbox[0] - 30, bbox[1] - 30, bbox[2] + 30, bbox[3] + 30))