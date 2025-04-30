from pathlib import Path
import json
import re
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

# Load environment variables from .env
load_dotenv()

# Global configuration
MODEL_NAME = "gpt-4o"
PROMPTS_DIR = Path(__file__).parent / "prompts"

# System message to enforce Spanish
system_es = SystemMessagePromptTemplate.from_template(
    "Eres un asistente que RESPONDE SIEMPRE EN ESPAÑOL, SIN MEZCLAR OTROS IDIOMAS."
)

def load_chat_prompt(name: str) -> ChatPromptTemplate:
    text = (PROMPTS_DIR / f"{name}.txt").read_text(encoding="utf-8")
    human = HumanMessagePromptTemplate.from_template(text)
    return ChatPromptTemplate.from_messages([system_es, human])

# LLM chains
classifier_chain = LLMChain(
    llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2),
    prompt=load_chat_prompt("classifier"),
)
domain_chains = {
    1: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("legal")),
    2: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("accounting")),
    3: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("medical")),
    4: LLMChain(llm=ChatOpenAI(model_name=MODEL_NAME, temperature=0.2), prompt=load_chat_prompt("generic")),
}

# Define state type
class QAState(TypedDict):
    question: str
    category_id: int
    category_label: str
    answer: str

# Build the state graph (now with state_schema to satisfy langgraph)
graph = StateGraph(state_schema=QAState)

def classify_node(state: QAState) -> QAState:
    # Run the classifier chain and strip whitespace
    raw = classifier_chain.run(question=state["question"]).strip()

    # Try to extract the JSON object from the raw response
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            parsed = json.loads(json_str)
            # Assign parsed values
            state["category_id"] = int(parsed.get("id", 4))
            # Default label map if model omitted 'label'
            label_map = {1: "Legal", 2: "Contable", 3: "Médica", 4: "Genérica"}
            state["category_label"] = parsed.get("label", label_map[state["category_id"]])
            return state
        except json.JSONDecodeError:
            # Fall back to generic if JSON still invalid
            pass

    # Fallback: if no JSON found or parse failed, default to Generic
    state["category_id"] = 4
    state["category_label"] = "Genérica"
    return state

graph.add_node("classifier", classify_node)

# Domain nodes
def domain_node(chain: LLMChain):
    def _node(state: QAState) -> QAState:
        state["answer"] = chain.run(question=state["question"])
        return state
    return _node

for idx, ch in domain_chains.items():
    name = {1: "legal", 2: "accounting", 3: "medical", 4: "generic"}[idx]
    graph.add_node(name, domain_node(ch))

# Router directs based on category_id
def router(state: QAState) -> str:
    return {1: "legal", 2: "accounting", 3: "medical"}.get(state["category_id"], "generic")

graph.add_conditional_edges("classifier", router)
for dom in ("legal", "accounting", "medical", "generic"):
    graph.add_edge(dom, END)

graph.set_entry_point("classifier")
app_agent = graph.compile()

