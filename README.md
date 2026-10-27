# Processador de Consultas SQL

Trabalho da disciplina de Banco de Dados: um processador de consultas com interface gráfica. Ele recebe uma consulta SQL, faz o parse e a validação contra o banco `BD_Vendas`, converte para álgebra relacional, aplica heurísticas de otimização, desenha os grafos de operadores (original e otimizado) e mostra o plano de execução.

## Funcionalidades

- **Interface gráfica** (Tkinter) com campo para digitar a consulta SQL
- **Parser** com expressões regulares para `SELECT`, `FROM`, `WHERE`, `INNER JOIN ... ON`
- **Validação léxica e sintática** dos comandos e operadores (`=`, `>`, `<`, `<=`, `>=`, `<>`, `AND`, `(`, `)`)
- **Validação semântica** de tabelas e campos contra o schema do MySQL
- **Conversão para álgebra relacional** (expressão original e otimizada)
- **Grafo de operadores não otimizado e otimizado** exibidos na interface
- **Heurísticas de otimização**:
  - redução de tuplas (seleções empurradas para as folhas)
  - redução de atributos (projeções empurradas para as folhas)
  - reordenação das folhas pela seleção mais restritiva
  - eliminação de produtos cartesianos
- **Plano de execução** com a ordem das operações e os resultados intermediários

## Estrutura do Projeto

| Arquivo | Responsabilidade |
|---|---|
| `main.py` | Interface gráfica e orquestração do fluxo de processamento |
| `parser_sql.py` | Parse da string SQL e validação léxica/sintática |
| `validador_db.py` | Validação de tabelas e campos no banco `BD_Vendas` e qualificação de campos (`Tabela.campo`) |
| `algebra_relacional.py` | Conversão para álgebra relacional (original e otimizada) |
| `otimizador.py` | Aplicação das heurísticas de otimização |
| `gerador_grafo.py` | Desenho dos grafos de operadores no canvas |
| `processador_consultas.py` | Construção do grafo em memória e geração do plano de execução |

## Fluxo de Processamento

```mermaid
flowchart TD
    A["Consulta SQL digitada na interface"] --> B["Parser (parser_sql.py)"]
    B -->|erros léxicos/sintáticos| X["Exibe erros"]
    B --> C["Validação no banco (validador_db.py)"]
    C -->|tabela/campo inválido| X
    C --> D["Álgebra relacional (algebra_relacional.py)"]
    D --> E["Otimização por heurísticas (otimizador.py)"]
    E --> F["Grafos não otimizado e otimizado (gerador_grafo.py)"]
    E --> G["Plano de execução (processador_consultas.py)"]
    F --> H["Exibição na interface"]
    G --> H
```

## Validações Realizadas

**Parser (léxico/sintático)**
- A consulta deve começar com `SELECT` e conter `FROM`
- Campos e tabelas vazios (ex.: vírgula sobrando) são rejeitados
- `INNER JOIN` sem tabela e `ON`/`WHERE` sem condição são rejeitados
- Parênteses desbalanceados
- Símbolos inválidos (ex.: `!=`, `==`, `#`)
- Operadores fora do escopo do trabalho: `OR`, `NOT`, `LIKE`, `IN`, `BETWEEN`, `IS`, `NULL`

**Banco de dados (semântico)**
- Existência das tabelas no schema `BD_Vendas`
- Campos do `SELECT`, `ON` e `WHERE`:
  - `Tabela.campo`: a tabela precisa fazer parte da consulta e o campo precisa pertencer a ela
  - `campo`: precisa existir em exatamente uma das tabelas da consulta (caso contrário, é **ambíguo**)
- Falha de conexão com o banco

## Heurísticas de Otimização

### 1. Redução de tuplas (seleção)
Cada condição do `WHERE`/`ON` que envolve só uma tabela vira uma seleção `σ` posicionada logo acima da tabela correspondente. Assim as tuplas são filtradas antes das junções.

### 2. Redução de atributos (projeção)
Para cada tabela é criada uma projeção `π` com apenas os atributos usados no `SELECT` final ou nas condições de junção/seleção.

### 3. Seleções mais restritivas primeiro
As folhas da árvore são reordenadas pela **seletividade estimada** (fração de tuplas que satisfaz o predicado):

| Predicado | Seletividade |
|---|---|
| Igualdade na chave primária (`Tabela.idTabela = x`) | 0,001 |
| `=` | 0,1 |
| `<`, `>`, `<=`, `>=` | 1/3 |
| `<>` | 0,9 |

Quando uma tabela tem várias seleções, as seletividades são multiplicadas. A tabela com o menor valor é processada primeiro.

### 4. Evitar produto cartesiano
A árvore é montada de forma gulosa (*left-deep*): a cada passo, entre as tabelas restantes, é escolhida a mais restritiva **que possua predicado de junção** com as tabelas já unidas. O produto cartesiano (`X`) só aparece quando nenhuma condição liga as tabelas, e nesse caso a interface exibe um aviso.

## Plano de Execução

O grafo otimizado é construído em memória como uma árvore de nós `NoOperador` e percorrido em **pós-ordem**, ou seja, cada operador só é executado depois dos seus filhos. Cada operação gera um resultado intermediário `R1, R2, ...`.

Exemplo de saída:

```
1. [Seleção]  R1 ← σ Status.idStatus = 1 (Status)
2. [Projeção] R2 ← π Status.idStatus (R1)
3. [Projeção] R3 ← π Pedido.Cliente_idCliente, Pedido.Status_idStatus, Pedido.idPedido (Pedido)
4. [Junção]   R4 ← R2 ⨝ Status.idStatus = Pedido.Status_idStatus R3
5. [Projeção] R5 ← π Cliente.Nome, Cliente.idCliente (Cliente)
6. [Junção]   R6 ← R4 ⨝ Cliente.idCliente = Pedido.Cliente_idCliente R5
7. [Projeção] R7 ← π Cliente.Nome, Pedido.idPedido (R6)
Resultado final: R7
```

## Instalação e Execução

### Pré-requisitos
- Python 3.10+
- MySQL com o schema `BD_Vendas` criado (scripts fornecidos no enunciado do trabalho)

### Passos

1. Crie e ative o ambiente virtual:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
2. Instale as dependências:
   ```powershell
   pip install mysql-connector-python python-dotenv
   ```
3. Configure as credenciais do MySQL:
   Como o arquivo `.env` está no `.gitignore` por segurança, ao executar o projeto em outra máquina (como na máquina do professor/avaliador), é **obrigatório** criar ou configurar o arquivo `.env` na raiz do projeto com as credenciais do MySQL Workbench local:
   ```env
   DB_USER=root
   DB_PASSWORD=sua_senha_do_workbench
   ```
   *(Você pode renomear ou copiar o arquivo `.env.example` para `.env` e preencher sua senha).*

   > [!IMPORTANT]
   > Se o `.env` não for configurado ou a senha estiver incorreta para a instância local do MySQL, a validação acusará erro de conexão com o banco `BD_Vendas`.

4. Execute a aplicação:
   ```powershell
   python main.py
   ```

## Exemplos de Consultas

**Consulta válida com junções e seleção**
```sql
SELECT Cliente.Nome, Pedido.idPedido FROM Cliente
INNER JOIN Pedido ON Cliente.idCliente = Pedido.Cliente_idCliente
INNER JOIN Status ON Status.idStatus = Pedido.Status_idStatus
WHERE Status.idStatus = 1
```
Ordem otimizada: `Status → Pedido → Cliente`, sem produto cartesiano.

**Seleção mais restritiva**
```sql
SELECT Produto.Nome, Categoria.Descricao FROM Produto
INNER JOIN Categoria ON Produto.Categoria_idCategoria = Categoria.idCategoria
WHERE Produto.Preco > 100 AND Categoria.idCategoria = 2
```
`Categoria` vem primeiro (igualdade na chave primária).

**Consultas inválidas**

| Consulta | Erro |
|---|---|
| `SELEC * FROM Produto` | A consulta deve começar com SELECT |
| `SELECT Nome FROM Produto WHERE Preco != 10` | Símbolo inválido `!` |
| `SELECT Nome FROM Produto WHERE Preco > 1 OR Preco < 5` | Operador não suportado `OR` |
| `SELECT Produto.Email FROM Produto` | `Email` não pertence a `Produto` |
| `SELECT Nome FROM Cliente INNER JOIN Produto ON ...` | `Nome` é ambíguo |

## Banco de Dados Exemplo (BD_Vendas)

| Tabela | Campos |
|---|---|
| Categoria | idCategoria, Descricao |
| Produto | idProduto, Nome, Descricao, Preco, QuantEstoque, Categoria_idCategoria |
| TipoCliente | idTipoCliente, Descricao |
| Cliente | idCliente, Nome, Email, Nascimento, Senha, TipoCliente_idTipoCliente, DataRegistro |
| TipoEndereco | idTipoEndereco, Descricao |
| Endereco | idEndereco, EnderecoPadrao, Logradouro, Numero, Complemento, Bairro, Cidade, UF, CEP, TipoEndereco_idTipoEndereco, Cliente_idCliente |
| Telefone | Numero, Cliente_idCliente |
| Status | idStatus, Descricao |
| Pedido | idPedido, Status_idStatus, DataPedido, ValorTotalPedido, Cliente_idCliente |
| Pedido_has_Produto | idPedidoProduto, Pedido_idPedido, Produto_idProduto, Quantidade, PrecoUnitario |

## Atendimento aos Critérios de Avaliação

| Critério | Nota | Onde |
|---|---|---|
| Interface gráfica existente e funcional | 1,5 | `main.py` |
| Local para inserir a string com a consulta SQL | 1,0 | `main.py` |
| A string é parseada | 1,0 | `parser_sql.py` |
| Campos e comandos errados são validados | 1,0 | `parser_sql.py`, `validador_db.py` |
| Grafo otimizado de operadores mostrado na GUI | 1,0 | `gerador_grafo.py` |
| Ordem de execução da consulta (plano de execução) | 1,5 | `processador_consultas.py` |
| Heurística de redução de tuplas apresentada no grafo | 1,0 | `otimizador.py`, `gerador_grafo.py` |
| Heurística de redução de atributos apresentada no grafo | 1,0 | `otimizador.py`, `gerador_grafo.py` |
| Demais heurísticas | 1,0 | `otimizador.py` |

## Cronograma de Entregas

| Entrega | Data |
|---|---|
| Interface gráfica existente e funcional | 15/10/26 |
| A string é parseada | 15/10/26 |
| Campos e comandos errados são validados | 15/10/26 |
| Conversão para álgebra relacional | 20/10/26 |
| Grafo não otimizado | 20/10/26 |
| Aplicação da heurística de projeção e seleção | 22/10/26 |
| Demais heurísticas | 27/10/26 |

## Limitações

- Não há suporte a aliases de tabelas (`FROM Cliente c`) nem a `OR`, `LIKE`, `IN`, subconsultas, `GROUP BY` ou `ORDER BY`, conforme o escopo do trabalho
- Datas e textos devem estar entre aspas (`'2020-01-01'`)
- A seletividade é estimada pelo tipo de operador, sem estatísticas reais do banco
