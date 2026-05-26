# RAG 核心逻辑
import os
import uuid
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com"
)
# 2.本地 embedding 模型：负责文本向量化
embedding_model = SentenceTransformer("BAAI/bge-small-zh-v1.5")

# 3.ChromaDB：本地向量数据库
chroma_client = chromadb.PersistentClient(path="./chroma_db")

collection = chroma_client.get_or_create_collection(
    name =  "documents",
    metadata={"hnsw:space":"cosine"}
)


def read_txt_file(file_path: str) -> str:
    """
    读取txt/md文件
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def split_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    简单文本切块
    :param text:
    :param chunk_size: 每块多少字符
    :param overlap: 相邻块重叠多少字符
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap
    return chunks

def get_embedding(text: str, is_query: bool = False) -> List[float]:
    """
    使用本地BEG模型生成embedding
    is_query=True表示是用户问题
    """
    if is_query:
        text = "为这个句子生成表示以用于检索相关文章:" + text

    vector = embedding_model.encode(
        text,
        normalize_embeddings=True
    )

    return vector.tolist()

def add_document(file_path: str, filename: str):
    """
    文档入库
    读取文件->切块->embedding->写入chromadb
    """
    text = read_txt_file(file_path)
    chunks = split_text(text)

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):
        chunk_id = str(uuid.uuid4())
        embedding = get_embedding(chunk)

        ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(chunk)
        metadatas.append({
            "filename": filename,
            "chunk_index": index
        })
    collection.add(
        ids = ids,
        embeddings = embeddings,
        documents = documents,
        metadatas=metadatas
    )

    return {
        "filename": filename,
        "chunk_count": len(chunks),
    }


def search_relevant_chunks(question: str, top_k: int = 3) -> List[str]:
    """
    根据问题检索相关文档片段
    :param question:
    :param top_k:
    :return:
    """
    question_embedding = get_embedding(question, is_query=True)

    result = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k,
    )
    print(result)
    documents = result.get("documents", [[]])[0]

    return documents

def answer_question(question : str) -> dict:
    """
    RAG问答：
    1.检索相关片段
    2.拼接上下文
    3.调用DeepSeek生成答案
    """
    chunks = search_relevant_chunks(question)

    context = "\n\n".join([
        f"片段{i+1}:\n{chunk}"
        for i, chunk in enumerate(chunks)
    ])

    prompt = f"""
    你是一个文档问答助手。
    请只根据下面的文档片段回答用户问题。
    如果文档片段里没有答案，请回答：文档中没有找到相关信息。
    不要编造文档中不存在的内容。
    
    文档片段：
    {context}
    
    用户问题：
    {question}
    """

    response = deepseek_client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {
                "role":"system",
                "content": "你是一个严谨的企业知识库问答助手"
            },
            {
                "role":"user",
                "content": prompt
            }
        ],
        stream=False,
    )

    answer = response.choices[0].message.content

    return {
        "question": question,
        "answer": answer,
        "chunks": chunks,
    }


