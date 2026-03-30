"""
Módulo responsável pela lógica central do sistema RAG (Retrieval-Augmented Generation).
Gerencia o carregamento de documentos, divisão em partes semânticas (chunks),
criação do banco de dados vetorial e a orquestração da cadeia de perguntas e respostas.
"""

from typing import List, Optional
import logfire
from langsmith import traceable

from langchain_community.document_loaders import PDFPlumberLoader
from langchain.docstore.document import Document
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains.llm import LLMChain
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains import RetrievalQA


class RAGSystem:
    """
    Classe que encapsula o pipeline RAG.
    Integra ferramentas de observabilidade (Logfire) e rastreamento (LangSmith)
    em cada etapa crítica do processo.
    """

    def __init__(
        self,
        path_file: str,
        model_name: str = "qwen/qwen3-4b-2507@Q4_k_M",
        api_base: str = "http://192.168.0.129:1234/v1",
        api_key: str = "lm-studio",
        k_retrieval: int = 2
    ):
        """
        Inicializa as configurações do sistema RAG.

        Args:
            path_file (str): Caminho absoluto ou relativo para o arquivo PDF.
            model_name (str): Nome do modelo LLM a ser consumido (padrão local via LM Studio).
            api_base (str): URL base da API compatível com OpenAI.
            api_key (str): Chave de API para autenticação.
            k_retrieval (int): Número de documentos relevantes a serem recuperados na busca vetorial.
        """
        self.path_file = path_file
        self.model_name = model_name
        self.api_base = api_base
        self.api_key = api_key
        self.k_retrieval = k_retrieval

        logfire.debug("Inicializando HuggingFaceEmbeddings")
        # Modelo de embeddings utilizado tanto para o SemanticChunker quanto para o FAISS
        self.embedder = HuggingFaceEmbeddings()
        
        self.retriever: Optional[VectorStoreRetriever] = None
        self.qa_chain: Optional[RetrievalQA] = None

        logfire.info("RAGSystem inicializado", model_name=model_name, k_retrieval=k_retrieval, file_path=path_file)


    @traceable(run_type="tool", name="RAG_LoadDocuments")
    def load_documents(self) -> List[Document]:
        """
        Extrai o texto do arquivo PDF especificado.
        
        Returns:
            List[Document]: Lista de objetos Document do LangChain contendo o texto e metadados.
        """
        with logfire.span("Carregando Documentos PDF", path=self.path_file):
            try:
                logfire.debug("Instanciando PDFPlumberLoader")
                loader = PDFPlumberLoader(self.path_file)
                docs = loader.load()
                logfire.info("Documentos PDF carregados com sucesso", num_pages=len(docs))
                return docs
            except Exception as e:
                logfire.error("Erro crítico ao carregar documentos PDF", error=str(e), exc_info=True)
                raise e


    @traceable(run_type="tool", name="RAG_ChunkDocuments")
    def chunk_documents(self, docs: List[Document]) -> List[Document]:
        """
        Divide os documentos extraídos em pedaços (chunks) menores usando similaridade semântica.
        Isso garante que sentenças relacionadas permaneçam juntas, melhorando o contexto para o LLM.

        Args:
            docs (List[Document]): Documentos originais carregados.

        Returns:
            List[Document]: Documentos divididos semanticamente.
        """
        with logfire.span("Dividindo Documentos em Chunks (SemanticChunker)"):
            try:
                logfire.debug("Instanciando SemanticChunker com embeddings", num_docs_input=len(docs))
                splitter = SemanticChunker(self.embedder)
                chunks = splitter.split_documents(docs)
                logfire.info("Chunks semânticos criados", num_chunks=len(chunks))
                
                if chunks:
                    logfire.debug("Tamanho do primeiro chunk gerado", size=len(chunks[0].page_content))
                    
                return chunks
            except Exception as e:
                logfire.error("Erro ao processar chunks semânticos", error=str(e), exc_info=True)
                raise e


    @traceable(run_type="retriever", name="RAG_BuildVectorStore")
    def build_vectorstore(self, docs: List[Document]) -> VectorStoreRetriever:
        """
        Processa os chunks semânticos gerando embeddings e armazena-os em um banco vetorial (FAISS).
        Configura o banco para atuar como um 'retriever' baseado em similaridade.

        Args:
            docs (List[Document]): Chunks de texto.

        Returns:
            VectorStoreRetriever: Interface de busca para recuperar textos relevantes.
        """
        with logfire.span("Construindo VectorStore FAISS"):
            try:
                logfire.debug("Gerando vetores no FAISS a partir dos chunks", num_chunks=len(docs))
                vectordb = FAISS.from_documents(docs, self.embedder)
                # Configura a busca para retornar os 'k' resultados mais similares
                retriever = vectordb.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": self.k_retrieval}
                )
                logfire.info("VectorStore FAISS e Retriever criados", k=self.k_retrieval)
                return retriever
            except Exception as e:
                logfire.error("Falha ao construir índice vetorial FAISS", error=str(e), exc_info=True)
                raise e


    @traceable(run_type="chain", name="RAG_BuildLLMChain")
    def build_llm_chain(self) -> StuffDocumentsChain:
        """
        Constrói a cadeia de processamento de linguagem natural (LLM).
        Define as instruções de sistema (prompt) e a forma como os documentos recuperados
        serão inseridos (stuffed) no contexto do modelo.

        Returns:
            StuffDocumentsChain: Cadeia pronta para receber contexto e gerar respostas.
        """
        with logfire.span("Construindo Cadeias de LLM e Documentos"):
            try:
                logfire.debug("Instanciando ChatOpenAI", api_base=self.api_base, model=self.model_name)
                # Configuração do LLM (apontando para o LM Studio local)
                llm = ChatOpenAI(
                    model_name=self.model_name,
                    openai_api_base=self.api_base,
                    openai_api_key=self.api_key,
                    temperature=0.0, # Zero alucinação, resposta determinística
                    max_tokens=1024
                )

                # Prompt rigoroso para limitar o escopo da IA
                system_prompt = (
                    "1. Use os seguintes pedaços de contexto para responder à pergunta no final, sempre em Português do Brasil.\n"
                    "2. Se você não sabe a resposta, apenas diga 'Eu não sei', mas não invente uma resposta.\n"
                    "3. Mantenha a resposta concisa e limitada a 3 ou 4 parágrafos.\n"
                    "Contexto: {context}\n"
                    "Pergunta: {question}\n"
                    "Resposta:"
                )
                prompt_template = PromptTemplate.from_template(system_prompt)
                llm_chain = LLMChain(llm=llm, prompt=prompt_template, verbose=True)

                # Formatação de como cada documento individual será apresentado ao LLM
                document_prompt = PromptTemplate(
                    input_variables=["page_content", "source"],
                    template="Contexto:\n{page_content}\nFonte: {source}"
                )

                # Combina o LLM com o formatador de documentos
                chain = StuffDocumentsChain(
                    llm_chain=llm_chain,
                    document_variable_name="context",
                    document_prompt=document_prompt,
                    verbose=True
                )
                logfire.info("Cadeia StuffDocumentsChain construída com sucesso")
                return chain
            except Exception as e:
                logfire.error("Falha ao construir a cadeia do LLM", error=str(e), exc_info=True)
                raise e


    @traceable(run_type="chain", name="RAG_BuildPipeline")
    def build_pipeline(self):
        """
        Orquestra a montagem completa da arquitetura:
        Carregamento -> Chunking -> VectorStore -> RetrievalQA.
        Deve ser executado antes de qualquer tentativa de consulta.
        """
        with logfire.span("Construindo Pipeline RAG Completo"):
            try:
                logfire.debug("Iniciando orquestração da pipeline")
                docs = self.load_documents()
                chunks = self.chunk_documents(docs)
                self.retriever = self.build_vectorstore(chunks)
                documents_chain = self.build_llm_chain()

                # RetrievalQA liga o Retriever (busca) com a Document Chain (geração de texto)
                self.qa_chain = RetrievalQA(
                    combine_documents_chain=documents_chain,
                    retriever=self.retriever,
                    verbose=True,
                    return_source_documents=True # Importante para auditoria da resposta
                )
                logfire.info("Pipeline RAG de ponta a ponta pronta para inferência")
            except Exception as e:
                logfire.error("Interrupção na montagem da pipeline RAG", error=str(e), exc_info=True)
                raise e


    @traceable(run_type="chain", name="RAG_RunQuery")
    def run_query(self, question: str):
        """
        Interface principal de inferência. Recebe a pergunta do usuário e 
        devolve a resposta gerada baseada no contexto recuperado do PDF.

        Args:
            question (str): Pergunta submetida pelo usuário final.

        Returns:
            dict: Dicionário contendo o 'result' (resposta do LLM) e 'source_documents' (fontes).
        """
        with logfire.span("Executando Consulta RAG", query=question):
            if not self.qa_chain:
                logfire.error("Tentativa de consulta rejeitada: Pipeline ausente")
                raise RuntimeError("O pipeline não foi construído. Execute `build_pipeline()` primeiro.")
            
            try:
                logfire.debug("Enviando payload para a cadeia QA", input_query=question)
                # O método invoke garante compatibilidade com as versões recentes do LangChain
                response = self.qa_chain.invoke({"query": question})
                logfire.info("Consulta executada com sucesso", 
                             num_source_docs_retrieved=len(response.get("source_documents", [])))
                return response
            except Exception as e:
                logfire.error("Falha na inferência da cadeia QA", error=str(e), exc_info=True)
                raise e