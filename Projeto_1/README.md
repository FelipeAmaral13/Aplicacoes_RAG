# RAG Agêntico com LangGraph & Flask

Este projeto implementa um sistema de **Retrieval-Augmented Generation (RAG)** avançado, utilizando uma arquitetura de **agente cíclico**. Ao contrário de sistemas RAG lineares tradicionais, este agente utiliza o **LangGraph** para raciocinar e decidir se precisa consultar o documento PDF antes de responder ao usuário.

## Tecnologias Utilizadas

* **Backend:** Flask (Python)
* **Orquestração de IA:** [LangChain](https://www.langchain.com/) & [LangGraph](https://langchain-ai.github.io/langgraph/)
* **LLM Local:** Gemma 3 (via LM Studio ou servidor compatível com OpenAI API)
* **Banco de Vetores:** FAISS (Facebook AI Similarity Search)
* **Embeddings:** HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)
* **Frontend:** Vanilla JavaScript, HTML5 e CSS3 (UI responsiva com suporte a Markdown)

## Arquitetura do Sistema

O fluxo de trabalho do agente segue um grafo de estados cíclico:
1.  **Agent (Node):** O LLM analisa o histórico e decide se possui informação suficiente ou se precisa invocar ferramentas.
2.  **Tools (Node):** Se necessário, o agente invoca a ferramenta `check_security_policy` para buscar contextos relevantes no PDF processado.
3.  **Loop:** O resultado da busca é anexado ao histórico de mensagens e o agente decide se agora pode responder ou se precisa de mais buscas.

## Pré-requisitos

* Python 3.10+
* **LM Studio** rodando o modelo `Gemma 3` (Configurado em: `http://172.30.64.1:1234/v1`)
* Pastas de sistema: `uploads/` e `logs/`

## Instalação e Execução

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/felipeamaral13/rag-agentico-langgraph.git](https://github.com/felipeamaral13/rag-agentico-langgraph.git)
    cd rag-agentico-langgraph
    ```

2.  **Crie o ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # ou
    venv\Scripts\activate     # Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicie a aplicação:**
    ```bash
    python app.py
    ```
    Acesse em seu navegador: `http://127.0.0.1:5000`

## Estrutura de Arquivos

* `app.py`: Servidor Flask e gerenciamento de endpoints API.
* `agentes_ia.py`: Core do agente, definição do grafo LangGraph e lógica de decisão.
* `rag.py`: Pipeline de ingestão, chunking e criação da base vetorial FAISS.
* `log.py`: Central de logs com rotação automática de arquivos.
* `static/js/app.js`: Interface do usuário e comunicação assíncrona com o backend.

## Observações de Configuração

* **Network:** O IP `172.30.64.1` é comum em ambientes WSL2. Se o LM Studio estiver na mesma máquina Windows/Mac que o Flask, altere para `localhost` no arquivo `agentes_ia.py`.
* **Logs:** Em caso de erro no upload ou processamento, verifique o arquivo `logs/log.log` para detalhes técnicos.
* **Embeddings:** Na primeira execução, o sistema fará o download automático do modelo de embeddings do HuggingFace (aprox. 80MB).

---
**Desenvolvido como um MVP de Agente de IA para análise de documentos corporativos.**