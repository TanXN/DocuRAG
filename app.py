# FastAPI 接口
import os

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from rag_service import add_document, answer_question

app = FastAPI()

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


    if not filename.endswith((".txt", ".md")):
        return {
            "code":400,
            "msg": "目前只支持 txt 和 markdown文件"
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
