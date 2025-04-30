from pathlib import Path
import json
from typing import TypedDict
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain.chains import LLMChain
from langgraph.graph import StateGraph, END

# Carga variables de entorno desde .env
load_dotenv()

# Configuración global
MODEL_NAME = "gpt-4o"
PROMPTS_DIR = Path(__file__).parent / "prompts"

# Mensaje sistema para forzar español
system_es = SystemMessagePromptTemplate.from_template(
    "Eres un asistente que RESPONDE SIEMPRE EN ESPAÑOL, SIN MEZCLAR OTROS IDIOMAS."
)

def load_chat_prompt(name: str) -> ChatPromptTemplate:
    text = (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    human = HumanMessagePromptTemplate.from_template(text)
    return ChatPromptTemplate.from_messages([system_es, human])

# Cadenas LLM
classifier_chain = LLMChain(
    llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.0),
    prompt=load_chat_prompt("classifier"),
)
domain_chains = {
    1: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("legal")),
    2: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("accounting")),
    3: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("medical")),
    4: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("generic")),
}

# Esquema de estado
class QAState(TypedDict):
    question: str
    category_id: int
    category_label: str
    answer: str

graph = StateGraph(state_schema=QAState)

# Nodo de clasificación
def classify_node(state: QAState) -> QAState:
    raw = classifier_chain.run(question=state["question"])
    parsed = json.loads(raw)
    state["category_id"] = parsed["id"]
    # Etiqueta por defecto
    label_map = {1: "Legal", 2: "Contable", 3: "Médica", 4: "Genérica"}
    state["category_label"] = parsed.get("label", label_map[state["category_id"]])
    return state

graph.add_node("classifier", classify_node)

# Nodos de cada dominio
def domain_node(chain: LLMChain):
    def _node(state: QAState) -> QAState:
        state["answer"] = chain.run(question=state["question"])
        return state
    return _node

for idx, ch in domain_chains.items():
    name = {1: "legal", 2: "accounting", 3: "medical", 4: "generic"}[idx]
    graph.add_node(name, domain_node(ch))

# Enrutador
def router(state: QAState) -> str:
    return {1: "legal", 2: "accounting", 3: "medical"}.get(state["category_id"], "generic")

graph.add_conditional_edges("classifier", router)
for dom in ("legal", "accounting", "medical", "generic"):
    graph.add_edge(dom, END)

graph.set_entry_point("classifier")
app_agent = graph.compile()
