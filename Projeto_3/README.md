# Proj_3 — Agente Autônomo de Segurança para Análise de Logs

Projeto de demonstração de um agente de cibersegurança que:

- lê logs de servidor de um arquivo local;
- armazena os logs em banco vetorial (ChromaDB);
- faz busca semântica por eventos suspeitos;
- usa um LLM para decidir entre **BLOQUEAR** ou **MONITORAR**;
- registra a ação em um log “tipo blockchain” (simulado).

---

## Visão Geral

O fluxo principal está no `main.py`:

1. Ingestão dos logs do arquivo `server_logs.txt`.
2. Busca semântica por indícios de ataque (ex.: SQL Injection, login falho).
3. Análise por LLM com saída obrigatória em JSON.
4. Execução da ação:
	- se crítico: bloqueio simulado + registro blockchain;
	- caso contrário: monitoramento.

<img width="1555" height="611" alt="Image" src="https://github.com/user-attachments/assets/338f4c3b-049b-45d9-93e8-20f6a31d6855" />

---

## Tecnologias

- Python 3.12+
- LangChain
- ChromaDB
- Sentence Transformers (`all-MiniLM-L6-v2`)
- FastMCP
- Modelo LLM via API compatível OpenAI (ex.: LM Studio local)

Dependências declaradas em `pyproject.toml`.

---

## Estrutura do Projeto

```text
Proj_3/
├── main.py                 # Orquestra ingestão, busca, raciocínio e ação
├── log_analiser_ai.py      # Ferramentas MCP + ChromaDB + embeddings
├── log.py                  # Configuração de logging (arquivo + console)
├── server_logs.txt         # Base de logs de entrada
├── logs/                   # Arquivos de log gerados em execução
├── pyproject.toml          # Dependências e metadados do projeto
└── README.md
```

---

## Pré-requisitos

1. Python **3.12** ou superior.
2. Ambiente virtual ativo.
3. Endpoint de LLM compatível com OpenAI disponível.

> No estado atual do código, o `main.py` está configurado para usar:
>
> - `model_name='google/gemma-3-12b'`
> - `openai_api_base='http://172.30.64.1:1234/v1'`
> - `openai_api_key='lm-studio'`

Se necessário, ajuste esses valores diretamente no `main.py`.

---

## Instalação

No diretório do projeto:

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e .
```

---

## Como Executar

1. Garanta que o arquivo `server_logs.txt` exista e tenha linhas de log.
2. Inicie o endpoint LLM local/remoto compatível com OpenAI.
3. Execute:

```bash
python main.py
```

---

## Exemplo de Fluxo Esperado

Durante a execução, você verá etapas como:

- inicialização do agente;
- ingestão e indexação dos logs;
- logs relevantes encontrados pela busca semântica;
- decisão do agente (`BLOQUEAR` ou `MONITORAR`);
- registro da ação (simulado) em blockchain.

---

## Logging

O módulo `log.py` configura:

- saída no console;
- arquivo rotativo em `logs/log.log`;
- rotação com limite de 5 MB e até 5 backups.

---

## Observações Técnicas

- A função `blockchain_log_entry` é **simulação** para demonstração.
- A coleção `server_logs` é recriada ao iniciar o módulo `log_analiser_ai.py`.
- O arquivo `server_logs.txt` vazio ou ausente impede a ingestão.

---
