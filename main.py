import tkinter as tk
import os
import re
from dotenv import load_dotenv
from parser_sql import ParserSQL
from validador_db import ValidadorDB
from algebra_relacional import AlgebraRelacional
from gerador_grafo import GeradorGrafo
from otimizador import OtimizadorConsulta
from processador_consultas import ProcessadorConsultas

load_dotenv()

janela = tk.Tk()
janela.title("Processador de Consultas")
janela.geometry("1000x800")

scroll_pagina = tk.Scrollbar(janela, orient=tk.VERTICAL)
scroll_pagina.pack(side=tk.RIGHT, fill=tk.Y)

canvas_pagina = tk.Canvas(janela, highlightthickness=0, yscrollcommand=scroll_pagina.set)
canvas_pagina.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scroll_pagina.config(command=canvas_pagina.yview)

conteudo = tk.Frame(canvas_pagina)
id_conteudo = canvas_pagina.create_window((0, 0), window=conteudo, anchor="nw")

def ajustar_area_rolavel(event):
    canvas_pagina.configure(scrollregion=canvas_pagina.bbox("all"))

def ajustar_largura_conteudo(event):
    canvas_pagina.itemconfig(id_conteudo, width=event.width)

def rolar_pagina(event):
    if isinstance(event.widget, tk.Text):
        return
    canvas_pagina.yview_scroll(int(-event.delta / 120), "units")

conteudo.bind("<Configure>", ajustar_area_rolavel)
canvas_pagina.bind("<Configure>", ajustar_largura_conteudo)
janela.bind_all("<MouseWheel>", rolar_pagina)

frame_dir = tk.Frame(conteudo)
frame_dir.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

frame_esq = tk.Frame(conteudo)
frame_esq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

def criar_quadro_grafo(pai, titulo):
    tk.Label(pai, text=titulo, font=("Arial", 10, "bold")).pack()

    frame_quadro = tk.Frame(pai, relief=tk.SUNKEN, bd=2)
    frame_quadro.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

    barra_y = tk.Scrollbar(frame_quadro, orient=tk.VERTICAL)
    barra_y.pack(side=tk.RIGHT, fill=tk.Y)
    barra_x = tk.Scrollbar(frame_quadro, orient=tk.HORIZONTAL)
    barra_x.pack(side=tk.BOTTOM, fill=tk.X)

    canvas = tk.Canvas(frame_quadro, bg="white", height=600,
                       yscrollcommand=barra_y.set,
                       xscrollcommand=barra_x.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    barra_y.config(command=canvas.yview)
    barra_x.config(command=canvas.xview)
    return canvas

canvas_nao_otimizado = criar_quadro_grafo(frame_esq, "Grafo Não Otimizado")
canvas_otimizado = criar_quadro_grafo(frame_esq, "Grafo Otimizado")

tk.Label(frame_dir, text="Digite sua consulta SQL:").pack(pady=10)
caixa_texto = tk.Text(frame_dir, height=8, width=50)
caixa_texto.pack()

def atualizar_resultado(texto):
    caixa_resultado.config(state=tk.NORMAL)
    caixa_resultado.delete("1.0", tk.END)
    caixa_resultado.tag_configure("subscrito", offset="-4", font=("Arial", 9, "italic"))
    partes = re.split(r'(_\{.*?\})', texto)
    
    for parte in partes:
        if parte.startswith('_{') and parte.endswith('}'):
            texto_interno = parte[2:-1]
            
            caixa_resultado.insert(tk.END, texto_interno + " ", "subscrito")
        else:
            caixa_resultado.insert(tk.END, parte)
            
    caixa_resultado.config(state=tk.DISABLED)

def desenhar_grafo(resultado, dados_otimizados):
    # Grafo Não Otimizado
    gerador = GeradorGrafo(canvas_nao_otimizado, resultado)
    gerador.desenhar_nao_otimizado()
    canvas_nao_otimizado.xview_moveto(0)
    canvas_nao_otimizado.yview_moveto(0)
    
    # Grafo Otimizado
    gerador_otim = GeradorGrafo(canvas_otimizado, resultado)
    gerador_otim.desenhar_otimizado(dados_otimizados)
    canvas_otimizado.xview_moveto(0)
    canvas_otimizado.yview_moveto(0)

def iniciar_processamento():
    consulta_digitada = caixa_texto.get("1.0", tk.END).strip()
    
    if not consulta_digitada:
        atualizar_resultado("Por favor, digite uma consulta SQL antes de processar.")
        return

    analisador = ParserSQL()
    resultado = analisador.fazer_parse(consulta_digitada)
    
    erros = list(resultado["ERROS"])
    
    if not erros:
        usuario = os.getenv("DB_USER")
        senha = os.getenv("DB_PASSWORD")
        
        validador = ValidadorDB(user=usuario, password=senha) 
        erros = validador.validar_consulta(resultado)
        if not erros:
            resultado = validador.qualificar_campos(resultado)
        validador.fechar_conexao()
    
    if erros:
        texto_saida = "❌ ERROS DE VALIDAÇÃO ENCONTRADOS:\n\n"
        for erro in erros:
            texto_saida += f"- {erro}\n"
        atualizar_resultado(texto_saida)
        canvas_nao_otimizado.delete("all")
        canvas_otimizado.delete("all")
    else:
        conversor_algebra = AlgebraRelacional(resultado)
        expressao_matematica = conversor_algebra.gerar_expressao_completa()
        
        otimizador = OtimizadorConsulta(resultado)
        dados_otimizados = otimizador.otimizar()
        expressao_otimizada = conversor_algebra.gerar_expressao_otimizada(dados_otimizados)
        
        texto_saida = "✅ CONSULTA VÁLIDA COM SUCESSO!\n\n"
        texto_saida += f"Resultado do Parse:\n{resultado}\n\n"
        texto_saida += f"Álgebra Relacional:\n{expressao_matematica}\n\n"
        texto_saida += f"Álgebra Relacional Otimizada:\n{expressao_otimizada}\n\n"
        
        texto_saida += "Ordem das folhas (restritividade + junções sem produto cartesiano):\n"
        seletividades = dados_otimizados.get("seletividades", {})
        for i, tabela in enumerate(dados_otimizados.get("ordem_tabelas", []), start=1):
            texto_saida += f"{i}. {tabela} (seletividade estimada: {seletividades.get(tabela, 1.0):.3f})\n"
        
        for juncao in dados_otimizados.get("juncoes", []):
            if juncao["cartesiano"]:
                texto_saida += f"⚠ Produto cartesiano inevitável com {juncao['nova_tabela']} (sem predicado de junção)\n"
        
        processador = ProcessadorConsultas(resultado, dados_otimizados)
        texto_saida += f"\nPlano de Execução:\n{processador.gerar_texto_plano()}"
        
        atualizar_resultado(texto_saida)
        
        desenhar_grafo(resultado, dados_otimizados)
        

tk.Button(frame_dir, text="Processar", command=iniciar_processamento).pack(pady=10)

tk.Label(frame_dir, text="Resultado do Processamento:").pack(pady=5)
frame_resultado = tk.Frame(frame_dir)
frame_resultado.pack()

barra_resultado = tk.Scrollbar(frame_resultado, orient=tk.VERTICAL)
barra_resultado.pack(side=tk.RIGHT, fill=tk.Y)

caixa_resultado = tk.Text(frame_resultado, height=25, width=50, state=tk.DISABLED, bg="#f0f0f0", wrap=tk.WORD,
                          yscrollcommand=barra_resultado.set)
caixa_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
barra_resultado.config(command=caixa_resultado.yview)

janela.mainloop()