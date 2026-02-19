import os
import json
from log_analiser_ai import search_logs, blockchain_log_entry, ingest_logs_from_file
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatOpenAI(
            model_name='google/gemma-3-12b',
            openai_api_base="http://172.30.64.1:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0,
            max_tokens=500
        )

def main():
    ingest_logs_from_file()  # Ingestão inicial dos logs para o banco de dados
    print("Iniciando o Agente de Segurança Autônomo ...")
    
    # --- PASSO 1: COLETA DE DADOS (Observação) ---
    print("\n1. OBSERVANDO: Coletando e analisando logs do sistema...")
    
    # Simulando a coleta de logs relevantes para análise
    consulta_logs = "Tentativas de ataque, sql injection ou login falho"
    resposta_logs = search_logs(consulta_logs)
    
    print(f"   Logs Relevantes Encontrados:\n{resposta_logs}")
    
    # --- PASSO 2: RACIOCÍNIO (Análise e Decisão) ---
    prompt_sistema = """
        Você é um Analista de Segurança Sênior Autônomo (Cybersecurity Agent).
        Sua tarefa é analisar logs de servidor e decidir se uma ação defensiva é necessária.

        REGRAS DE DECISÃO:
        1. Se identificar um ataque claro (SQL Injection, Brute Force confirmado, etc.) com um IP de origem, você DEVE ordenar o bloqueio.
        2. Se forem apenas erros comuns ou sem IP de origem claro, ordene apenas MONITORAR.

        FORMATO DE RESPOSTA OBRIGATÓRIO (JSON):
        {{
            "analise": "Breve explicação do que você encontrou",
            "decisao": "BLOQUEAR" ou "MONITORAR",
            "ip_alvo": "IP para bloquear (ou null se não houver)",
            "motivo_bloqueio": "Explicação curta para o firewall"
        }}
        """

    prompt_usuario = f"""
    Aqui estão os logs recuperados do sistema:
    
    {resposta_logs}
    
    Qual é a sua decisão? Responda apenas com o JSON.
    """

    print("\n2. PENSANDO: Analisando padrões de ataque e decidindo ação...")

    try:
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=prompt_sistema),
            HumanMessage(content=prompt_usuario)
        ])

        resposta = llm.invoke(prompt.format_messages())

        decisao = json.loads(resposta.content)
        print(f"   Análise do Agente: {decisao['analise']}")
        print(f"   Decisão Tomada: {decisao['decisao']}")

        # --- PASSO 3: AÇÃO (Execução de Ferramentas) ---
        print("\n3. AGINDO: Executando protocolos...")
        if decisao['decisao'] == "BLOQUEAR" and decisao['ip_alvo']:
            print(f"   AMEAÇA CRÍTICA CONFIRMADA. Iniciando bloqueio de {decisao['ip_alvo']}...")
            resultado_blockchain = blockchain_log_entry(f"Bloqueio de IP: {decisao['ip_alvo']} por motivo: {decisao['motivo_bloqueio']}")
            print(f"   Log registrado na blockchain: {resultado_blockchain}")
        else:
            print("   Nenhuma ação de bloqueio necessária. Continuando monitoramento...")

    except json.JSONDecodeError:
        print("   ERRO: O LLM não retornou um JSON válido. Verifique a resposta do modelo.")
        print(f"   Resposta Recebida: {resposta.content}")  

if __name__ == "__main__":
    main()