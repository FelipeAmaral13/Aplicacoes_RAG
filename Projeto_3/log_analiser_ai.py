import os
import datetime
import chromadb
from chromadb.utils import embedding_functions
from mcp.server.fastmcp import FastMCP
from log import get_logger
from langchain_huggingface import HuggingFaceEmbeddings

logger = get_logger(__name__)

LOG_FILE = "server_logs.txt"

mcp = FastMCP("LogAnaliser AI")

embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

client = chromadb.Client()

try:
    client.delete_collection(name = "server_logs")
except:
    pass

collection = client.get_or_create_collection(name = "server_logs", embedding_function = embeddings)

def ingest_logs_from_file():
    """Lê o arquivo de texto definido em LOG_FILE, processa as linhas e as insere no banco vetorial ChromaDB."""
    if not os.path.exists(LOG_FILE):
        logger.error(f"ERRO: O arquivo '{LOG_FILE}' não foi encontrado.")
        logger.info("    Por favor, crie este arquivo na mesma pasta e adicione seus logs.")
        return

    logger.info(f"Lendo logs do arquivo: {LOG_FILE}...")
    
    with open(LOG_FILE, 'r', encoding = 'utf-8') as f:
        logs = [line.strip() for line in f.readlines() if line.strip()]

    if not logs:
        logger.warning("O arquivo de logs está vazio.")
        return

    logger.info(f"⚡ Gerando Embeddings para {len(logs)} linhas de log...")

    ids = [f"log_{i}" for i in range(len(logs))]
    metadatas = [{"source": LOG_FILE, "timestamp": datetime.datetime.now().isoformat()} for _ in logs]

    collection.add(documents = logs, metadatas = metadatas, ids = ids)
    logger.info(f"{len(logs)} logs foram ingeridos com sucesso no banco de dados Chroma.")

@mcp.tool()
def search_logs(query: str, top_k: int = 5):
    """
    Realiza uma busca semântica nos logs usando o ChromaDB e retorna os resultados mais relevantes.
    """
    logger.info(f"Recebendo consulta de busca: '{query}'")
    
    if collection.count() == 0:
        logger.warning("O banco de dados de logs está vazio. Por favor, ingira os logs antes de realizar buscas.")
        return "O banco de dados de logs está vazio. Por favor, ingira os logs antes de realizar buscas."
    

    results = collection.query(query_texts = [query], n_results = top_k)

    found_logs = results['documents'][0] if results['documents'] else []
    distances = results['distances'][0] if results['distances'] else []

    response = f"Resultados da busca para '{query}':\n"
    for i, (log, dist) in enumerate(zip(found_logs, distances)):
        relevance = round((1 - dist) * 100, 2)
        response += f"[{i}] [Relevância: {relevance}%] LOG: {log}\n"

        
    return response

@mcp.tool()
def get_log_count():
    """Retorna o número total de logs armazenados no banco de dados."""
    count = collection.count()
    logger.info(f"Número total de logs armazenados: {count}")
    return f"O sistema LogSense possui atualmente {count} entradas de log carregadas do arquivo '{LOG_FILE}'."

@mcp.tool()
def blockchain_log_entry(log_entry: str):
    """
    Simula o registro de uma entrada de log em uma blockchain.
    Esta função é um placeholder para demonstrar como logs poderiam ser imutavelmente registrados.
    """
    logger.info(f"Registrando log na blockchain: '{log_entry}'")
    # Simulação de hash e timestamp
    log_hash = hash(log_entry)
    timestamp = datetime.datetime.now().isoformat()
    return f"Log registrado na blockchain com hash: {log_hash} e timestamp: {timestamp}"

# if __name__ == "__main__":
#     ingest_logs_from_file()
#     mcp.run()