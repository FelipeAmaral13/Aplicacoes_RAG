# Analise de Logs por RAG-Agentico

O **ThreatRAG Sentinel** é uma solução avançada de análise de logs de segurança que utiliza Inteligência Artificial Generativa e a arquitetura **RAG (Retrieval-Augmented Generation)** para identificar ameaças em tempo real. Ao combinar o modelo **Gemma-3** com o framework **LangGraph**, o sistema não apenas detecta anomalias, mas também fornece recomendações baseadas em uma base de conhecimento interna.

##  Arquitetura do Sistema

O projeto utiliza um pipeline de agentes inteligentes para processar e analisar os dados através de um grafo de estados:

1.  **Agente de Pré-processamento**: Responsável pela filtragem e redução de ruído dos logs, mantendo apenas linhas suspeitas como erros 4xx, 5xx, tentativas de SQLi e Path Traversal.
2.  **Agente Analista (RAG)**: Recupera contexto de uma base de conhecimento local via busca vetorial e gera um relatório detalhado utilizando o modelo Gemma-3.
3.  **Relatório Final**: Produz um report em Markdown contendo Resumo Executivo, Identificação de Ameaças, IOCs (IPs e Endpoints), TTPs (MITRE ATT&CK) e Recomendações Priorizadas.

### Tecnologias Principais
* **LLM**: Google Gemma-3-12b via interface compatível com OpenAI (LM Studio).
* **Orquestração**: LangGraph para a gestão do fluxo de agentes.
* **Banco de Vetores**: ChromaDB para armazenamento persistente de documentos.
* **Embeddings**: HuggingFace (`all-MiniLM-L6-v2`).
* **Backend**: Flask (Python) com suporte a CORS.
* **Frontend**: Interface responsiva com Glassmorphism, CSS puro e Vanilla JavaScript.

<img width="1917" height="916" alt="Image" src="https://github.com/user-attachments/assets/d93df33f-a651-42e6-bb67-1e0890994f45" />


<img width="1914" height="922" alt="Image" src="https://github.com/user-attachments/assets/777a77ec-729a-4790-adcd-851f4fa40212" />


<img width="1913" height="920" alt="Image" src="https://github.com/user-attachments/assets/b5429d83-ebaf-4c59-869a-281ef85caa85" />

---

## Instalação e Configuração

### Pré-requisitos
* Python 3.10+
* LM Studio configurado com o modelo `google/gemma-3-12b` no endereço `http://192.168.0.5:1234`.

### Passo a Passo

1.  **Clone o repositório**:
    ```bash
    git clone [https://github.com/felipeamaral13/threat-rag-sentinel.git](https://github.com/felipeamaral13/threat-rag-sentinel.git)
    cd threat-rag-sentinel
    ```

2.  **Instale as dependências**:
    ```bash
    pip install flask flask-cors langchain langchain-openai langchain-chroma langchain-huggingface langgraph chromadb
    ```

3.  **Prepare a Base de Conhecimento**:
    Insira documentos de referência (arquivos `.txt` ou `.md`) no diretório `./knowledge_base`. O sistema criará o banco de vetores automaticamente na primeira execução.

4.  **Inicie a aplicação**:
    ```bash
    python app.py
    ```

5.  **Acesse a interface**:
    Navegue para `http://localhost:5000`.

---

## 📊 Estrutura de Arquivos

* `app.py`: Ponto de entrada da aplicação Flask e definição dos endpoints da API como `/api/analyze` e `/api/stats`.
* `rag_agent.py`: Implementação do `RAGAgent`, lógica do LangGraph e configuração do Retriever.
* `log.py`: Configuração de logging centralizado com rotação de arquivos para monitoramento do sistema.
* `static/`: Arquivos estáticos incluindo a lógica de interface em `app.js` e estilização em `styles.css`.
* `templates/index.html`: Estrutura principal da interface do usuário.

---

## 🔒 Segurança e Performance

* **Lazy Initialization**: O agente RAG é inicializado sob demanda para otimizar o consumo de memória do servidor.
* **Persistent Storage**: Utiliza um diretório persistente para o ChromaDB (`./rag_store`), evitando a necessidade de reprocessar a base de conhecimento a cada reinicialização.
* **Logging Robusto**: Registra todas as etapas do processo, desde o input bruto até a conclusão da análise, facilitando o debugging.
