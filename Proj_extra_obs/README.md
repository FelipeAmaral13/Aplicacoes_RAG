# Shift Extras RAG

Aplicacao de perguntas e respostas sobre PDF usando RAG (Retrieval-Augmented Generation) com interface em Streamlit.

O fluxo principal e:

1. Usuario faz upload de um PDF.
2. O sistema extrai o texto e divide em chunks semanticos.
3. Os chunks sao vetorizados e indexados com FAISS.
4. Uma pergunta do usuario busca os trechos mais relevantes.
5. O LLM gera a resposta em Portugues (pt-BR) com base no contexto recuperado.

## Stack

- Python 3.12+
- Streamlit (UI)
- LangChain (orquestracao RAG)
- FAISS (busca vetorial)
- HuggingFace Embeddings (vetorizacao)
- PDFPlumber (leitura de PDF)
- ChatOpenAI client apontando para endpoint compativel com OpenAI (ex.: LM Studio)
- Observabilidade com Logfire e LangSmith

## Estrutura do projeto

```
.
|-- main.py
|-- pyproject.toml
`-- src/
		`-- rag_system.py
```

## Como executar

### 1) Instalar o uv

Windows (PowerShell):

```powershell
pip install uv
```

### 2) Criar e ativar ambiente virtual com uv

Windows (PowerShell):

```powershell
uv venv .venv --python 3.12
.\.venv\Scripts\Activate.ps1
```

### 3) Instalar dependencias com uv

```powershell
uv sync
```

### 4) Configurar variaveis de ambiente

Crie um arquivo `.env` na raiz do projeto.

Exemplo minimo:

```env
LANGCHAIN_API_KEY=seu_token_langchain
LOGFIRE_API_KEY=seu_token_logfire
LANGSMITH_TRACING = true
LANGCHAIN_TRACING_V2 = true
LANGSMITH_ENDPOINT = https://api.smith.langchain.com
LANGSMITH_API_KEY = seu_token_langchain
LANGSMITH_PROJECT = "nome-do-projeto"
```

Observacoes:

- O app chama `load_dotenv()`, entao o `.env` e carregado na inicializacao.
- Se as chaves nao estiverem definidas, o sistema mostra avisos na interface e o tracing pode ficar parcial.

### 5) Subir a aplicacao

```powershell
streamlit run main.py
```

Depois abra a URL mostrada no terminal (normalmente `http://localhost:8501`).

## Como usar

1. Faça upload de um arquivo PDF na interface.
2. Aguarde a construcao do pipeline RAG.
3. Digite uma pergunta sobre o conteudo do PDF.
4. Clique em **Responder**.
5. Veja a resposta e as fontes usadas (com pagina e trecho).

## Arquitetura resumida

### `main.py`

- Interface Streamlit.
- Gerencia upload do PDF.
- Persiste instancia do RAG em `st.session_state`.
- Envia perguntas e renderiza resposta + fontes.

### `src/rag_system.py`

- `load_documents()`: extrai paginas do PDF com `PDFPlumberLoader`.
- `chunk_documents()`: gera chunks com `SemanticChunker`.
- `build_vectorstore()`: indexa chunks em FAISS e cria retriever.
- `build_llm_chain()`: configura prompt e cadeia do LLM.
- `build_pipeline()`: orquestra pipeline completo.
- `run_query()`: executa consulta e retorna `result` + `source_documents`.

## Parametros importantes (RAGSystem)

No construtor da classe `RAGSystem` voce pode ajustar:

- `model_name`: modelo servido no endpoint OpenAI-compatible.
- `api_base`: URL da API (padrao atual aponta para rede local).
- `api_key`: chave de acesso da API.
- `k_retrieval`: quantidade de documentos recuperados na busca.

## Prompt e comportamento da resposta

O prompt atual instrui o modelo a:

- responder em Portugues do Brasil;
- nao inventar informacao (responder "Eu nao sei" quando necessario);
- manter respostas concisas (3 a 4 paragrafos).

## Observabilidade

- **Logfire**: spans e logs durante upload, pipeline e inferencia.
- **LangSmith**: tracing das etapas decoradas com `@traceable`.

Se `LANGSMITH_TRACING` nao estiver como `true`, o tracing automatico pode nao aparecer.

## Solucao de problemas

- Erro ao responder sem upload:
	- Carregue um PDF antes de clicar em **Responder**.

- Falha de conexao com o LLM:
	- Verifique se o endpoint em `api_base` esta ativo e acessivel.
	- Confirme se o `model_name` existe no servidor (ex.: LM Studio).

- Lentidao no primeiro processamento:
	- E esperado no primeiro carregamento por causa de embeddings e indexacao vetorial.

- Tracing/Logs incompletos:
	- Confirme variaveis `LANGSMITH_API_KEY`, `LANGCHAIN_API_KEY`, `LANGSMITH_TRACING` e `LOGFIRE_API_KEY`.

## Melhorias futuras sugeridas

- Persistir indice FAISS em disco para evitar rebuild a cada upload.
- Suportar multiplos formatos (DOCX, TXT, HTML).
- Adicionar cache de embeddings e de documentos.
- Criar testes automatizados para pipeline e interface.

