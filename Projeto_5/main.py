import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from log import get_logger
from utils.tools import tool_inspect_permissions, tool_execute_containment

logger = get_logger(__name__)

class DetectiveAgent:
    def __init__(self):
        self.llm_detective = ChatOpenAI(
            model_name='google/gemma-3-12b',
            openai_api_base="http://172.30.64.1:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0
        )

        self.llm_responder =ChatOpenAI(
            model_name='google/gemma-3-12b',
            openai_api_base="http://172.30.64.1:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0
        )



    def analyze_incident(self, scan_data):
        logger.info("[*] Agente Detetive: Iniciando varredura de permissões...")
        scan_result = tool_inspect_permissions()
        logger.info(f"\n[DADOS BRUTOS DO SCAN]:\n{scan_result}")

        detective_prompt = ChatPromptTemplate.from_template(
            """
            Você é um detetive especializado em segurança de bancos de dados. 
            Analise os seguintes dados de varredura de permissões e identifique possíveis incidentes de segurança. 
            
            {scan_data}
            
            Se encontrar permissões concedidas a 'PUBLIC' em tabelas sensíveis, isso é um INCIDENTE CRÍTICO.
            Responda APENAS com um JSON no formato:
            {{
                "is_incident": true/false,
                "severity": "High/Medium/Low",
                "summary": "Resumo do que foi encontrado"
            }}
            """
        )

        chain_detective = detective_prompt | self.llm_detective
        analysis = chain_detective.invoke({"scan_data": scan_data})
        logger.info(f"\n[*] Análise do Agente Detetive:\n{analysis.content}")

        if "true" not in analysis.content.lower():
            logger.info("[-] Nenhum incidente detectado. Encerrando.")
            return 
    
        logger.info("\n[!] INCIDENTE CONFIRMADO. Acionando Agente de Resposta...")

        responder_prompt = ChatPromptTemplate.from_template(
            """
            Você é um Engenheiro de Resposta a Incidentes (DBA Security).
            O Agente Detetive encontrou o seguinte problema: {scan_data}
            
            Sua tarefa: Gerar o comando SQL PostgreSQL exato para REVOGAR (REVOKE) 
            as permissões inseguras encontradas para o grupo 'PUBLIC'.
            
            Regras:
            1. Retorne APENAS o código SQL.
            2. Não inclua markdown, explicações ou ```.
            3. O comando deve ser algo como: REVOKE ALL ON TABLE nome_tabela FROM PUBLIC;
            """
        )

        chain_responder = responder_prompt | self.llm_responder
        containment_plan = chain_responder.invoke({"scan_data": analysis})
        sql_command = containment_plan.content.strip()
        logger.info(f"\n[*] Comando de Contenção Gerado:\n{sql_command}")

        confirm = input("\n[HUMAN-IN-THE-LOOP] Autoriza a execução automática deste comando? (s/n): ")

        if confirm.lower() == 's':
            logger.info("[*] Executando comando de contenção...")
            execution_result = tool_execute_containment(sql_command)
            logger.info(f"\n[*] Resultado da Execução:\n{execution_result}")
            final_scan = tool_inspect_permissions()
            logger.info(f"\n[*] Verificação Pós-Contenção:\n{final_scan}")
        else:
            logger.info("[-] Execução do comando de contenção foi negada pelo usuário. Encerrando.")

if __name__ == "__main__":
    agent = DetectiveAgent()
    agent.analyze_incident(None)
