# FastAPI 接口
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from rag_service import add_document, answer_question, hybrid_search, retrieve_with_rerank, search_relevant_chunks
from es_store import keyword_search_es
from history_service import init_histofy_db, list_qa_history, save_qa_history
from es_store import create_es_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("service startup")
    create_es_index()
    init_histofy_db()
    yield
    print("service shutdown")


app = FastAPI(lifespan=lifespan)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    question: str

@app.post("/api/rag/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    上传文档并写入向量数据库
    只支持 .txt / .md
    """
    filename = file.filename


    if not filename.endswith((".txt", ".md", ".pdf")):
        return {
            "code":400,
            "msg": "目前只支持 txt 和 markdown文件和pdf文件"
        }
    file_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    result = add_document(file_path, filename)

    return {
        "code": 200,
        "msg": "文档上传并入库成功",
        "data": result
    }


@app.post("/api/reg/chat")
def reg_chat(req: ChatRequest):
    """
    根据知识库回答问题
    """
    result = answer_question(req.question)

    return {
        "code": 200,
        "msg": "success",
        "data": result
    }


@app.post("/api/reg/key-word-search")
def keyword_search(req: ChatRequest):
    result = keyword_search_es(req.question)

    return {
        "code": 200,
        "msg": "success",
        "data": result
    }


@app.post("/api/reg/hybrid-search")
def hybrid_search_interface(req: ChatRequest):
    result = hybrid_search(req.question)

    return {
        "code": 200,
        "msg": "success",
        "data": result
    }

@app.post("/api/reg/rerank-search")
def rerank_search(req: ChatRequest):
    result = retrieve_with_rerank(req.question)
    return {
        "code": 200,
        "msg": "success",
        "data": result
    }


@app.post("/api/reg/vector-search")
def vector_search(req: ChatRequest):
    result = search_relevant_chunks(req.question)
    return {
        "code": 200,
        "msg": "success",
        "data": result
    }


@app.get("/api/reg/rag-history")
def rag_history(limit: int = 50):
    result = list_qa_history(limit)
    return {
        "code": 200,
        "message": "success",
        "data": result
    }

