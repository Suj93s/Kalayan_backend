from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.rag import answer_question

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Query(BaseModel):
    question: str
    tenant: str = None
    session_id: str = None


class IndexRequest(BaseModel):
    tenant: str
    url: str


@app.post("/chat")
def chat(query: Query):
    answer = answer_question(
        query.question
    )
    return {
        "answer": answer
    }


@app.post("/index-website")
def index_website(req: IndexRequest):
    return {"chunks_stored": 10}


@app.delete("/end-chat/{session_id}")
def end_chat(session_id: str):
    return {"status": "ok"}