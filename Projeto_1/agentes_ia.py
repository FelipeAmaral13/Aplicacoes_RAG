import os
from typing_extensions import TypedDict
from typing import Annotated, List, Literal

# Correção dos imports
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

class AgentPolicy:
    """Define a política do agente, incluindo o modelo, ferramentas e fluxo de trabalho."""
    def __init__(self, retriever):
        self.llm = ChatOpenAI(
            model_name='google/gemma-3-12b',
            openai_api_base="http://172.30.64.1:1234/v1",
            openai_api_key="lm-studio",
            temperature=0.0
        )
        
        self.retriever = retriever
        self.tools = [self.build_rag_tool()]
        self.model_with_tools = self.llm.bind_tools(self.tools)
        self.graph = self.build_graph()

    def build_rag_tool(self):
        """Define a ferramenta de RAG para consulta das políticas de segurança."""
        @tool
        def check_security_policy(query: str) -> str:
            """Consulta as políticas de segurança da empresa."""
            results = self.retriever.invoke(query)
            if not results:
                return "Nenhum resultado encontrado."
            return "\n\n".join([doc.page_content for doc in results])
        return check_security_policy
    
    def should_continue(self, state: AgentState) -> Literal["tools", END]:
        """Determina se o agente deve chamar uma ferramenta ou encerrar a conversa."""
        last_message = state['messages'][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    def call_model(self, state: AgentState):
        response = self.model_with_tools.invoke(state['messages'])
        return {"messages": [response]}

    def build_graph(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges("agent", self.should_continue)
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

def create_agent(retriever):
    return AgentPolicy(retriever).graph