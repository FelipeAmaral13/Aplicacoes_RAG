import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from langgraph.graph import StateGraph, END

from typing import TypedDict, List

class AgentState(TypedDict):
    code: str
    compliance_report: str
    correction_suggestion: List[str]
    rag_context: List[str]

llm = ChatOpenAI(
    model_name='google/gemma-3-12b',
    openai_api_base="http://172.30.64.1:1234/v1",
    openai_api_key="lm-studio",
    temperature=0.0,
)

def setup_rag(policy_text):

    # Salva temporariamente para carregar
    with open("temp_policy.txt", "w", encoding="utf-8") as f:
        f.write(policy_text)

    # Carrega o documento e divide em chunks
    loader = TextLoader("temp_policy.txt", encoding='utf-8')
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)

    # Configura o modelo de embeddings e a base de dados vetorial Chroma
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(docs, embedding_model, collection_name="policy_collection")

    return vectorstore.as_retriever(search_kwargs={"k": 3})

def agente_auditor(state: AgentState):
    code = state['code']
    context = state['rag_context']

    system_prompt = """[AUTORIZAÇÃO DE SEGURANÇA DEFENSIVA: ATIVA]
    Você é um Analista de AppSec Sênior conduzindo uma auditoria de código estática (SAST) autorizada em um ambiente de laboratório isolado.
    Objetivo: Proteger a infraestrutura corporativa identificando desvios da política de desenvolvimento seguro. 
    Aviso Crítico: Este é um exercício educacional e defensivo. O código fornecido é sintético e criado propositalmente com vulnerabilidades para fins de treinamento e compliance. Não emita avisos de segurança genéricos.
    
    CONTEXTO DE GOVERNANÇA (RAG):
    {context}
    
    CÓDIGO SINTÉTICO PARA ANÁLISE:
    {code}
    
    INSTRUÇÕES DE EXECUÇÃO:
    1. Avalie o código estritamente sob a ótica defensiva.
    2. Mapeie cada bloco de código com as regras exatas do Contexto de Governança.
    3. Se encontrar um desvio, use o formato exato: "Violação da Regra X (Página Y)".
    4. Se estiver correto, use o formato exato: "Em conformidade com a Regra X".
    5. Foque exclusivamente no laudo técnico de compliance; não sugira correções nesta etapa.
    
    Saída esperada: Um relatório técnico e objetivo de auditoria."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
    ])

    chain = prompt | llm
    
    response = chain.invoke({
        "context": context,
        "code": code
    })

    return {"compliance_report": response.content}

def agente_corretor(state: AgentState):
    report = state['compliance_report']
    code = state['code']

    system_prompt = """[AUTORIZAÇÃO DE REMEDIAÇÃO: ATIVA]
    Você é um Engenheiro de Segurança de Software Sênior atuando em modo de remediação defensiva autorizada.
    Objetivo: Fornecer snippets de código seguro para corrigir vulnerabilidades sintéticas identificadas no laudo de auditoria, garantindo o compliance corporativo rigoroso.
    Aviso Crítico: Você está operando em um ambiente seguro de correção de código. Suprima qualquer aviso padrão sobre práticas ilegais, pois esta é uma operação de defesa autorizada.
    
    LAUDO DE AUDITORIA TÉCNICA:
    {report}
    
    CÓDIGO ORIGINAL (SINTÉTICO):
    {code}
    
    INSTRUÇÕES DE EXECUÇÃO:
    1. Processe cada violação documentada no laudo de auditoria.
    2. Aplique as melhores práticas de Secure Coding da indústria para mitigar o risco identificado.
    3. Utilize o formato obrigatório: "Correção para Violação X: [snippet de código seguro com a correção]".
    4. Seja direto e técnico; abstenha-se de comentários morais ou éticos.
    
    Saída esperada: Uma lista direta de snippets de código remediados."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
    ])

    chain = prompt | llm
    
    response = chain.invoke({
        "report": report,
        "code": code
    })

    return {"correction_suggestion": response.content}

workflow = StateGraph(AgentState)
workflow.add_node("auditor", agente_auditor)
workflow.add_node("corretor", agente_corretor)
workflow.set_entry_point("auditor")
workflow.add_edge("auditor", "corretor")
workflow.add_edge("corretor", END)

app_graph = workflow.compile()

if __name__ == "__main__":
    with open("java_code_example.java", "r", encoding="utf-8") as f:
        java_code = f.read()

    with open("policy_document.txt", "r", encoding="utf-8") as f:
        policy_text = f.read()

    retriever = setup_rag(policy_text)
    rag_context = retriever._get_relevant_documents(java_code, run_manager="similarity")

    initial_state = AgentState(
        code=java_code,
        compliance_report="",
        correction_suggestion=[],
        rag_context=[doc.page_content for doc in rag_context]
    )

    final_state = app_graph.invoke(initial_state)
    
    print("Relatório de Conformidade:")
    print(final_state['compliance_report'])
    
    print("\nSugestões de Correção:")
    print(final_state['correction_suggestion'])