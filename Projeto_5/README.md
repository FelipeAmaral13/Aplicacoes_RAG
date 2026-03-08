# IncidentOps AI - Agente de Deteccao e Contencao de Incidentes em PostgreSQL

Projeto de automacao com IA para identificar permissoes inseguras em banco PostgreSQL e sugerir/execucar contencao via SQL.

O fluxo simula um incidente classico de seguranca de dados: permissao indevida para `PUBLIC` em tabela sensivel.

## Objetivo

- Detectar automaticamente permissoes de risco no PostgreSQL.
- Classificar o incidente com apoio de LLM.
- Gerar comando de contencao (`REVOKE ... FROM PUBLIC`).
- Executar a contencao com aprovacao humana (`human-in-the-loop`).

## Arquitetura

O projeto possui dois papeis de agente:

- Agente Detetive: analisa o resultado do scan de permissoes.
- Agente de Resposta: gera o SQL exato para mitigar o incidente.

Fluxo resumido:

1. Scan de permissoes no banco (`information_schema.role_table_grants`).
2. Analise por LLM para confirmar incidente.
3. Geracao do comando SQL de contencao.
4. Confirmacao manual no terminal (`s/n`).
5. Execucao do SQL e nova verificacao.

## Estrutura do Projeto

```text
.
|-- main.py                # Orquestra os agentes e o fluxo de incidente
|-- utils/tools.py         # Conexao DB, scan de permissoes e execucao SQL
|-- log.py                 # Logger com rotacao de arquivo
|-- docker-compose.yml     # Banco PostgreSQL vulneravel para laboratorio
|-- init.sql               # Cria tabela sensivel e aplica GRANT inseguro
|-- requirements.txt       # Dependencias Python
|-- pyproject.toml         # Metadados do projeto
|-- logs/                  # Logs de execucao
`-- README.md
```

## Tecnologias

- Python 3.12+
- PostgreSQL 17 (Docker)
- LangChain
- psycopg2
- python-dotenv

## Pre-requisitos

- Docker e Docker Compose
- Python 3.12 ou superior
- Pip (ou ambiente Conda/venv)
- Endpoint OpenAI-compativel ativo (ex.: LM Studio), pois o agente usa `ChatOpenAI`

## Configuracao

### 1. Configurar variaveis de ambiente

Crie/edite o arquivo `.env` na raiz do projeto com:

```env
DB_NAME=incidentops
DB_USER=postgres
DB_PASS=postgres
DB_HOST=localhost
DB_PORT=5432
```

Observacao: o arquivo `utils/tools.py` carrega o `.env` explicitamente a partir da raiz do projeto.

### 2. Subir o banco de dados com Docker

```bash
docker-compose up -d
```

O container cria automaticamente uma tabela sensivel e aplica a vulnerabilidade de teste:

- Tabela: `salarios_confidenciais`
- Vulnerabilidade: `GRANT ALL PRIVILEGES ... TO PUBLIC`

### 3. Criar ambiente Python e instalar dependencias

Opcao com `venv`:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install langchain-openai
```

Opcao com `conda`:

```bash
conda create --name agentopsp5 python=3.13 -y
conda activate agentopsp5
pip install -r requirements.txt
pip install langchain-openai
```

### 4. Ajustar endpoint do modelo (se necessario)

O arquivo `main.py` esta configurado para usar um endpoint OpenAI-compativel local:

- `openai_api_base="http://172.30.64.1:1234/v1"`

Se seu endpoint for diferente, ajuste esse valor em `main.py` antes de executar.

## Execucao

Com banco e ambiente prontos:

```bash
python main.py
```

Durante a execucao, o sistema pergunta:

```text
[HUMAN-IN-THE-LOOP] Autoriza a execucao automatica deste comando? (s/n):
```

- Digite `s` para executar a contencao.
- Digite `n` para apenas registrar a recomendacao sem executar.

## Logs

Os logs sao gravados em:

- `logs/log.log`

Com rotacao automatica de arquivo (5 MB, ate 5 backups).

## Exemplo de incidente detectado

Permissao de risco identificada:

- `grantee = PUBLIC`
- `table = salarios_confidenciais`
- `privilege = ALL`

Comando de contencao esperado (exemplo):

```sql
REVOKE ALL ON TABLE salarios_confidenciais FROM PUBLIC;
```

## Troubleshooting rapido

- Erro de conexao com banco: verifique se o container esta em execucao com `docker ps`.
- Erro de autenticacao no banco: valide `DB_USER`, `DB_PASS` e `DB_NAME` no `.env`.
- Variaveis ausentes: confirme se o `.env` esta na raiz e contem `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT`.
- `ModuleNotFoundError` para `langchain_openai`: rode `pip install langchain-openai`.
- Falha de chamada ao modelo: verifique se o endpoint em `main.py` esta ativo e acessivel.

## Melhorias futuras

- Validacao mais robusta do JSON de saida do LLM.
- Whitelist/blacklist de comandos SQL permitidos.
- Testes automatizados (unitarios e integracao).
- Exportacao de evidencias para SIEM/SOAR.

