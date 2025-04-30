from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .multi_agent import app_agent, QAState

class Question(BaseModel):
    question: str

class Answer(BaseModel):
    question: str
    category_id: int
    category_label: str
    answer: str

api = FastAPI(title="Entropia QA")

@api.post("/qa", response_model=Answer)
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Empty question")
    res: QAState = app_agent.invoke({"question": q.question})
    return {
        "question": q.question,
        "category_id": res["category_id"],
        "category_label": res["category_label"],
        "answer": res["answer"],
    }