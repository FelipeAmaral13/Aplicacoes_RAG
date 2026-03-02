# Proj_4 — Auditoria de Compliance com RAG + LangGraph

Pipeline de **auditoria estática de código (SAST) orientada por política interna**, com dois agentes:

- **Agente Auditor**: analisa o código e gera um laudo de conformidade.
- **Agente Corretor**: propõe snippets de remediação com base no laudo.

O projeto usa **RAG (Retrieval-Augmented Generation)** para recuperar trechos relevantes da política corporativa antes da análise.

## Como funciona

1. Carrega o código-fonte Java de `java_code_example.java`.
2. Carrega a política em `policy_document.txt`.
3. Divide a política em chunks e indexa no Chroma com embeddings (`all-MiniLM-L6-v2`).
4. Recupera os trechos mais relevantes da política para o código analisado.
5. Executa um grafo LangGraph com dois nós:
	 - `auditor` → gera relatório de conformidade.
	 - `corretor` → gera sugestões de correção.
6. Exibe no terminal:
	 - Relatório de Conformidade
	 - Sugestões de Correção

## Estrutura do projeto

- `main.py`: orquestração do pipeline (RAG + agentes + LangGraph).
- `java_code_example.java`: código sintético com vulnerabilidades para teste.
- `policy_document.txt`: política de desenvolvimento seguro usada como base de compliance.
- `temp_policy.txt`: arquivo temporário gerado em runtime para indexação.
- `pyproject.toml`: metadados e dependências do projeto.

## Requisitos

- Python **3.12+**
- Um endpoint compatível com OpenAI ativo em:
	- `http://172.30.64.1:1234/v1`
- Modelo configurado no código:
	- `google/gemma-3-12b`

> Observação: o endpoint/API key estão definidos diretamente em `main.py` (padrão para ambiente local/lab).

## Instalação

No diretório do projeto:

```bash
python -m venv .venv
```

### Windows (PowerShell)

```powershell
& .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e .
```

### Linux/macOS

```bash
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Execução

Com o ambiente virtual ativo:

```bash
python main.py
```

Saída esperada (resumo):

- Bloco `Relatório de Conformidade:` com violações e conformidades mapeadas às regras.
- Bloco `Sugestões de Correção:` com snippets de remediação.

## Personalização rápida

- Para analisar outro código, substitua o conteúdo de `java_code_example.java`.
- Para alterar critérios de compliance, edite `policy_document.txt`.
- Para trocar modelo/endpoint local, ajuste a criação de `ChatOpenAI` em `main.py`.

## Dependências principais

- `langchain`
- `langgraph`
- `langchain-openai`
- `langchain-community`
- `langchain-huggingface`
- `chromadb`
- `sentence-transformers`

## Troubleshooting

- **Erro de conexão com LLM**: verifique se o servidor local (ex.: LM Studio) está ativo no host/porta configurados.
- **Lentidão no primeiro run**: embeddings/modelos podem ser baixados na primeira execução.
- **Erro de versão do Python**: confirme que está usando Python 3.12+ (`python --version`).

## Observação de segurança

Este projeto é voltado para **uso educacional e defensivo** em laboratório, com código sintético propositalmente vulnerável para treinamento de AppSec/compliance.
