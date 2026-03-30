"""
Interface de usuário em Streamlit para o sistema RAG.
Gerencia o upload de arquivos, o estado da sessão (session_state)
e a apresentação das respostas e auditoria de fontes.
"""

import streamlit as st
from src.rag_system import RAGSystem
import tempfile
import os

from dotenv import load_dotenv
load_dotenv()

# Ferramentas de Observabilidade
import logfire
from langsmith import traceable
from langsmith import Client as LangSmithClient 

# Evita alertas de deadlocks durante o processo de tokenização do HuggingFace
os.environ['TOKENIZERS_PARALLELISM'] = 'True'

# Coleta das chaves de ambiente para as plataformas de monitoramento
langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
langchain_api_key_env = os.getenv("LANGCHAIN_API_KEY")
LOGFIRE_API_KEY = os.getenv("LOGFIRE_API_KEY")

# Inicialização do Logfire
try:
    logfire.configure() 
    print("Log - Logfire configurado.") 
except Exception as e:
     print(f"Log - Alerta: Falha ao configurar Logfire automaticamente: {e}")

# Verificações de integridade do ambiente para garantir que o tracking funcionará
if not langsmith_api_key or not langchain_api_key_env:
    st.warning("LANGSMITH_API_KEY e/ou LANGCHAIN_API_KEY não definidas. O tracing do LangSmith pode não funcionar completamente.")

if not LOGFIRE_API_KEY:
     st.warning("LOGFIRE_API_KEY não definida. Logs para Pydantic LogFire Cloud não funcionarão.")

if os.getenv("LANGSMITH_TRACING", "false").lower() != "true":
    st.warning("Variável de ambiente LANGSMITH_TRACING não está como 'true'. O tracing automático pode estar desativado.")

if not langchain_api_key_env:
     st.warning("Variável de ambiente LANGCHAIN_API_KEY não definida. Tracing do LangSmith inoperante.")


# Configuração básica da página Streamlit
st.set_page_config(page_title="Assistente RAG", layout="centered")

st.title("Assistente RAG com PDF")

# Componente para inserção do documento
uploaded_file = st.file_uploader("Faça upload de um arquivo PDF", type="pdf")

# Manutenção do estado da sessão: impede que o RAG seja reconstruído a cada interação na tela
if "rag" not in st.session_state:
    logfire.debug("Inicializando objeto RAG no estado da sessão")
    st.session_state.rag = None

# Fluxo de execução pós-upload
if uploaded_file:
    # Acompanha o tempo e escopo do processamento do arquivo
    span_upload = logfire.span("Processamento de Arquivo PDF", filename=uploaded_file.name, file_size=uploaded_file.size)
    with span_upload:
        # Grava o binário em disco temporariamente para que o PDFPlumberLoader possa ler
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        st.success("PDF carregado com sucesso.")
        logfire.info("Arquivo PDF armazenado localmente para processamento", path=tmp_path)
        
        with st.spinner("Construindo o pipeline RAG..."):
            try:
                logfire.debug("Iniciando RAGSystem no frontend")
                # Instancia e constrói a cadeia apenas uma vez
                rag = RAGSystem(path_file=tmp_path)
                rag.build_pipeline()
                
                # Salva o pipeline na sessão para persistir entre as requisições do usuário
                st.session_state.rag = rag
                logfire.info("Objeto RAG salvo no estado da sessão com sucesso")
            except Exception as e:
                logfire.error("Erro crítico na montagem do RAG via interface", error=str(e), exc_info=True)
                st.error("Erro interno ao construir o assistente.")

# Interface de consulta
question = st.text_input("Digite sua pergunta sobre o conteúdo do PDF")

# Disparo da inferência
if st.button("Responder") and question:
    logfire.debug("Botão de submissão acionado pelo usuário")
    
    # Prevenção de erros caso o usuário tente perguntar antes do upload
    if st.session_state.rag is None:
        logfire.warn("Usuário tentou perguntar sem carregar o PDF")
        st.error("Carregue um PDF primeiro.")
    else:
        # Rastreia o tempo total entre a pergunta e a renderização na interface
        span_chat = logfire.span("Processamento de Pergunta do Usuário", query=question)
        with span_chat:
            with st.spinner("Gerando resposta..."):
                try:
                    logfire.info("Enviando solicitação para inferência no backend RAG")
                    # Executa a busca vetorial e a geração de texto
                    response = st.session_state.rag.run_query(question)

                    # Exibe a resposta final processada pelo LLM
                    st.markdown("### Resposta:")
                    st.write(response["result"])

                    # Processo de explicabilidade: exibe ao usuário os trechos exatos recuperados do PDF
                    st.markdown("### Fontes utilizadas:")
                    for doc in response.get("source_documents", []):
                        st.markdown(f"- Página: `{doc.metadata.get('page', 'Desconhecida')}`")
                        st.markdown(f"> {doc.page_content[:300]}...")
                    
                    logfire.info("Resposta do LLM e referências renderizadas na interface")

                except Exception as e:
                    logfire.error("Falha ao gerar e exibir resposta na interface", error=str(e), exc_info=True)
                    st.error(f"Ocorreu um erro no processamento da sua pergunta: {e}")