import os
import sys
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from log import get_logger

logger = get_logger(__name__)

class AgentConfig(TypedDict):
    raw_logs: str
    cleaned_logs: str
    retrieved_context: str
    analysis_report: str

class RAGAgent:
    def __init__(self):
        # Configuração do LLM (Gemma-3 via LM Studio)
        self.llm = ChatOpenAI(
            model_name='google/gemma-3-12b',
            openai_api_base="http://192.168.0.5:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0,
            max_tokens=500
        )
        
        # Inicialização única dos Embeddings e Retriever para performance
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.retriever = self._setup_retriever()
        
        # Compilação do grafo na inicialização
        self.app = self._build_graph()

    def _setup_retriever(self):
        """Configura o banco de vetores Chroma de forma persistente."""
        persist_dir = os.environ.get("RAG_PERSIST_DIR", "./rag_store")
        kb_dir = os.environ.get("RAG_KB_DIR", "./knowledge_base")

        if os.path.exists(persist_dir) and os.path.exists(os.path.join(persist_dir, "chroma.sqlite3")):
            logger.info("Carregando store de vetores Chroma existente...")
            vector_store = Chroma(persist_directory=persist_dir, embedding_function=self.embeddings)
        else:
            logger.info("Criando nova base de conhecimento...")
            texts, metadatas = self._load_kb_documents(kb_dir)
            vector_store = Chroma.from_texts(
                texts=texts, 
                embedding=self.embeddings, 
                metadatas=metadatas, 
                persist_directory=persist_dir
            )
        
        return vector_store.as_retriever(search_kwargs={"k": 5})

    def _load_kb_documents(self, kb_dir):
        """Varre o diretório da base de conhecimento por arquivos suportados."""
        texts, metadatas = [], []
        if os.path.isdir(kb_dir):
            for root, _, files in os.walk(kb_dir):
                for fname in files:
                    if fname.lower().endswith((".txt", ".md")):
                        fpath = os.path.join(root, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                                if content.strip():
                                    texts.append(content)
                                    metadatas.append({"source": fpath})
                        except Exception as e:
                            logger.warning(f"Erro ao ler {fpath}: {e}")
        
        if not texts:
            logger.warning("KB vazia. Usando placeholder de segurança.")
            texts = ["Procedimentos padrão: Investigar 404 repetidos e bloquear IPs de SQLi."]
            metadatas = [{"source": "default_policy"}]
            
        return texts, metadatas

    def process_data_agent(self, state: AgentConfig) -> dict:
        """Filtra logs usando lógica programática (muito mais rápido que LLM)."""
        logger.info("Iniciando pré-processamento de logs via Regex...")
        
        raw_lines = state["raw_logs"].split('\n')
        suspicious_lines = []
        
        # Padrões comuns de ataques e erros
        patterns = [' 40', ' 50', 'SELECT', 'UNION', 'etc/passwd', 'admin', '../']
        
        for line in raw_lines:
            if any(p in line for p in patterns):
                suspicious_lines.append(line.strip())
                
        cleaned = "\n".join(suspicious_lines)
        if not cleaned:
            cleaned = "Nenhuma atividade suspeita detectada."
            
        return {"cleaned_logs": cleaned}

    def analysis_data_agent(self, state: AgentConfig) -> dict:
        """Agente analista que utiliza RAG para gerar o relatório final."""
        logger.info("Iniciando análise de ameaças com RAG...")
        
        # Recuperação de contexto
        unique_errors = list(set([line for line in state['cleaned_logs'].split('\n') if line]))[:5]
        query = f"Análise de vulnerabilidade e remediação para: {' '.join(unique_errors)}"
        docs = self.retriever.invoke(query)
        context = "\n\n".join([f"[Fonte: {d.metadata.get('source')}] {d.page_content}" for d in docs])

        system_prompt = """
        Você é o 'ThreatRAG Sentinel'. Gere um relatório em Markdown com:
        1. Resumo Executivo
        2. Ameaças Identificadas
        3. IOCs (IPs, Endpoints)
        4. TTPs (MITRE ATT&CK)
        5. Recomendações Priorizadas
        Use o contexto RAG fornecido para embasar suas recomendações.
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Logs Suspeitos:\n{logs}\n\nContexto Interno:\n{context}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"logs": state["cleaned_logs"], "context": context})

        return {"retrieved_context": context, "analysis_report": response.content}

    def _build_graph(self):
        """Constrói a estrutura do LangGraph."""
        workflow = StateGraph(AgentConfig)
        
        workflow.add_node("preprocessor", self.process_data_agent)
        workflow.add_node("analyst", self.analysis_data_agent)
        
        workflow.set_entry_point("preprocessor")
        workflow.add_edge("preprocessor", "analyst")
        workflow.add_edge("analyst", END)
        
        return workflow.compile()

    def execute(self, raw_logs: str) -> dict:
        """Executa o pipeline completo."""
        logger.info("Executando workflow de análise...")
        inputs = {"raw_logs": raw_logs}
        return self.app.invoke(inputs)

# # Exemplo de uso
# if __name__ == "__main__":
#     agent = RAGAgent()
#     log_data = """
#     192.168.1.10 - - [12/Feb/2026:10:00:01] "GET /index.php HTTP/1.1" 200 452
#     10.0.0.5 - - [12/Feb/2026:10:00:05] "GET /admin' OR '1'='1 HTTP/1.1" 404 120
#     192.168.1.10 - - [12/Feb/2026:10:00:10] "GET /style.css HTTP/1.1" 200 1240
#     """
#     result = agent.execute(log_data)
#     print(result["analysis_report"])