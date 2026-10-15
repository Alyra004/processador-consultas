import tkinter as tk
import os
from dotenv import load_dotenv
from parser_sql import ParserSQL
from validador_db import ValidadorDB

load_dotenv()

janela = tk.Tk()
janela.title("Processador de Consultas")
janela.geometry("1000x800")

tk.Label(janela, text="Digite sua consulta SQL:").pack(pady=10)
caixa_texto = tk.Text(janela, height=8, width=80)
caixa_texto.pack()

def atualizar_resultado(texto):
    caixa_resultado.config(state=tk.NORMAL)
    caixa_resultado.delete("1.0", tk.END)
    caixa_resultado.insert(tk.END, texto)
    caixa_resultado.config(state=tk.DISABLED)

def iniciar_processamento():
    consulta_digitada = caixa_texto.get("1.0", tk.END).strip()
    
    if not consulta_digitada:
        atualizar_resultado("Por favor, digite uma consulta SQL antes de processar.")
        return

    analisador = ParserSQL()
    resultado = analisador.fazer_parse(consulta_digitada)
    
    usuario = os.getenv("DB_USER")
    senha = os.getenv("DB_PASSWORD")
    
    validador = ValidadorDB(user=usuario, password=senha) 
    erros = validador.validar_consulta(resultado)
    validador.fechar_conexao()
    
    if erros:
        texto_saida = "❌ ERROS DE VALIDAÇÃO ENCONTRADOS:\n\n"
        for erro in erros:
            texto_saida += f"- {erro}\n"
    else:
        texto_saida = "✅ CONSULTA VÁLIDA COM SUCESSO!\n\n"
        texto_saida += f"Resultado do Parse:\n{resultado}"
        
    atualizar_resultado(texto_saida)

tk.Button(janela, text="Processar", command=iniciar_processamento).pack(pady=10)

tk.Label(janela, text="Resultado do Processamento:").pack(pady=5)
caixa_resultado = tk.Text(janela, height=8, width=80, state=tk.DISABLED, bg="#f0f0f0")
caixa_resultado.pack()

frame_grafos = tk.Frame(janela)
frame_grafos.pack(pady=15, fill=tk.BOTH, expand=True, padx=20)

frame_esq = tk.Frame(frame_grafos)
frame_esq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
tk.Label(frame_esq, text="Grafo Não Otimizado", font=("Arial", 10, "bold")).pack()
canvas_nao_otimizado = tk.Canvas(frame_esq, bg="white", relief=tk.SUNKEN, bd=2)
canvas_nao_otimizado.pack(fill=tk.BOTH, expand=True)

frame_dir = tk.Frame(frame_grafos)
frame_dir.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
tk.Label(frame_dir, text="Grafo Otimizado", font=("Arial", 10, "bold")).pack()
canvas_otimizado = tk.Canvas(frame_dir, bg="white", relief=tk.SUNKEN, bd=2)
canvas_otimizado.pack(fill=tk.BOTH, expand=True)

janela.mainloop()