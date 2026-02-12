from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from log import get_logger

logger = get_logger(__name__)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class RAG:
    """Classe para implementar um agente RAG (Retrieval-Augmented Generation) usando LangChain."""

    def __init__(self, pdf_path: str):
        """Inicializa o agente RAG com o caminho do PDF a ser processado."""
        self.pdf_path = pdf_path
        self.retriever = self._get_retriever()

    def _get_retriever(self):
        """Processa o PDF, divide em chunks, gera embeddings e cria um retriever."""

        logger.info(f"Processando o PDF: {self.pdf_path}")
        
        loader = PyPDFLoader(self.pdf_path)
        documents = loader.load()
        
        if not documents:
            logger.error("Erro: Não foi possível carregar o documento PDF.")
            return None

        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 150)
        chunks = text_splitter.split_documents(documents)
        
        if not chunks:
            logger.error("Erro: Não foi possível dividir o documento em chunks.")
            return None

        logger.info(f"Documento dividido em {len(chunks)} chunks.")

        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL, cache_folder="./cache")
        vectorstore = FAISS.from_documents(chunks, embeddings)

        return vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 4})
    

# if __name__ == "__main__":
#     rag = RAG("Politica.pdf")
#     retriever = rag.retriever
#     if retriever:
#         query = "Quais são as principais diretrizes da política de privacidade?"
#         results = retriever.invoke(query)
#         for i, doc in enumerate(results):
#             logger.info(f"Resultado {i+1}: {doc.page_content[:200]}...")