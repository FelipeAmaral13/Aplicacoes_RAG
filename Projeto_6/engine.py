import asyncio
import zmq
import zmq.asyncio
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field, ValidationError


class TriageResult(BaseModel):
    is_threat: bool = Field(description="True se for ameaça, False se for seguro")
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(
        description="Use APENAS: LOW, MEDIUM, HIGH, CRITICAL"
    )
    category: str = Field(description="Ex: SQL Injection, Leaked Key, Misconfig")
    reasoning: str = Field(description="Explicação curta")


class RemediationResult(BaseModel):
    action_plan: str = Field(description="Explicação do que fazer")
    code_fix: str = Field(description="Comando ou código exato para corrigir")

class SecurityEngine:
    LLM_TIMEOUT = 120.0
    def __init__(self):
        self.llm = ChatOpenAI(
            model_name="google/gemma-3-12b",
            openai_api_base="http://172.30.64.1:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0,
        )
        self.ctx = zmq.asyncio.Context()
        self.sub_socket = self.ctx.socket(zmq.SUB)
        self.sub_socket.connect("tcp://localhost:5555")
        self.sub_socket.subscribe("")
        self.pub_socket = self.ctx.socket(zmq.PUB)
        self.pub_socket.bind("tcp://*:5556")

    async def agent_run_triage(self, log_data: dict) -> TriageResult | None:
        print(f"[Triagem] Analisando: {log_data['source']}...")

        parser = JsonOutputParser(pydantic_object=TriageResult)
        prompt = PromptTemplate(
            template="""
                Classifique o seguinte log de segurança em termos de ameaça, severidade, categoria e raciocínio:
                Log: {log}
                Origem: {source}
                Responda apenas com um JSON seguindo o formato:
                {fmt}
                """,
            input_variables=["log", "source"],
            partial_variables={"fmt": parser.get_format_instructions()},
        )

        chain = prompt | self.llm | parser
        try:
            res = await asyncio.wait_for(
                chain.ainvoke(
                    {
                        "log": log_data["message"],
                        "source": log_data["source"],
                    }
                ),
                timeout=self.LLM_TIMEOUT,
            )
            return TriageResult(**res)

        except ValidationError as e:
            print(f"[Triagem] LLM retornou schema inválido: {e}")
            return None

        except asyncio.TimeoutError:
            print(f"[Triagem] Timeout após {self.LLM_TIMEOUT}s para: {log_data['source']}")
            return None

        except Exception as e:
            print(f"[Triagem] Erro inesperado: {e}")
            return None

    async def agent_run_remediation(self, log_data: dict, triage: TriageResult) -> RemediationResult | None:
        print(f"[Engenheiro] Criando fix para: {triage.category}...")

        parser = JsonOutputParser(pydantic_object=RemediationResult)
        prompt = PromptTemplate(
            template="""
                Dado o resultado da triagem de segurança, forneça um plano de ação e um código de correção específico:
                Ameaça: {category}
                Severidade: {severity}
                Raciocínio: {reasoning}

                Se for AWS S3 -> Forneça comando CLI 'aws s3api put-bucket-acl...' para remover public access.
                Se for SQL Injection -> Mostre código Python parametrizado ou regra de WAF.
                Se for Payload Detected -> Mostre código Python parametrizado ou regra de WAF.
                Se for Leaked Key -> Mostre comando para revogar a chave (aws iam delete-access-key).
                Se for K8s Privileged -> Mostre o YAML corrigido (securityContext: privileged: false).

                Responda apenas com um JSON seguindo o formato:
                {fmt}
                """,
            input_variables=["category", "severity", "reasoning"],
            partial_variables={"fmt": parser.get_format_instructions()},
        )

        chain = prompt | self.llm | parser

        try:
            res = await asyncio.wait_for(
                chain.ainvoke(
                    {
                        "category": triage.category,
                        "severity": triage.severity,
                        "reasoning": triage.reasoning,
                    }
                ),
                timeout=self.LLM_TIMEOUT,
            )

            return RemediationResult(**res)

        except ValidationError as e:
            print(f"[Remediação] LLM retornou schema inválido: {e}")
            return None

        except asyncio.TimeoutError:
            print(f"[Remediação] Timeout após {self.LLM_TIMEOUT}s para: {triage.category}")
            return None

        except Exception as e:
            print(f"[Remediação] Erro inesperado: {e}")
            return None


    async def start(self):
        print("[Security Engine] ATIVADO. Aguardando eventos...")

        try:
            while True:
                event = await self.sub_socket.recv_json()
                triage = await self.agent_run_triage(event)
                if not (triage and triage.is_threat):
                    continue

                trigger_fix = (
                    triage.severity in {"MEDIUM", "HIGH", "CRITICAL"}
                    or any(k in triage.category for k in ["S3", "Key"])
                )

                remediation = (
                    await self.agent_run_remediation(event, triage)
                    if trigger_fix
                    else None
                )

                alert_packet = {
                    "type": "ALERT",
                    "original_event": event,
                    "triage": triage.model_dump(),
                    "remediation": remediation.model_dump() if remediation else None,
                }

                await self.pub_socket.send_json(alert_packet)

                print(
                    f" -> ALERTA PUBLICADO: {triage.category} "
                    f"| Fix Gerado: {remediation is not None}"
                )

                if remediation:
                    print(f"   Plano de Ação : {remediation.action_plan}")
                    print(f"   Fix Sugerido  : {remediation.code_fix}")

        finally:
            print("Encerrando Engine — liberando recursos ZMQ...")
            self.sub_socket.close()
            self.pub_socket.close()
            self.ctx.term()


if __name__ == "__main__":
    engine = SecurityEngine()
    try:
        asyncio.run(engine.start())

    except KeyboardInterrupt:
        print("Engine Encerrada.")

    except Exception as e:
        print(f"Erro inesperado: {e}")