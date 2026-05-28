# RAG 核心逻辑
import os
import uuid
from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import chromadb
import fitz

import es_store
from es_store import create_es_index, keyword_search_es, index_chunk_to_es
from reranker import rerank_chunks
from history_service import save_qa_history

load_dotenv()



deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url = "https://api.deepseek.com"
)
# 2.本地 embedding 模型：负责文本向量化
embedding_model = SentenceTransformer(
    r"D:\Models\bge-small-zh-v1.5",
    local_files_only=True
)

# 3.ChromaDB：本地向量数据库
chroma_client = chromadb.PersistentClient(path="chroma_db")

collection = chroma_client.get_or_create_collection(
    name =  "documents",
    metadata={"hnsw:space":"cosine"}
)

def read_document(file_path: str) -> List[dict]:
    if file_path.endswith(".pdf"):
        return read_pdf_file(file_path)
    else:
        return read_txt_file(file_path)


def read_txt_file(file_path: str) -> List[dict]:
    """
    读取txt/md文件
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        return [
            {
                "text": text,
                "metadata": {
                    "page":-1,
                    "file_type": file_path.split(".")[-1]
                }
            }
        ]


def read_pdf_file(file_path: str) -> list[dict]:
    """
    读取文本型 PDF
    """
    pages = []
    with fitz.open(file_path) as pdf:
        for page_index, page in enumerate(pdf):
            text = page.get_text("text", sort=True).strip()
            if text:
                pages.append({
                    "text": text,
                    "metadata": {
                        "page": page_index+1,
                        "file_type": ".pdf",
                    }
                })
    if not pages:
        raise ValueError("PDF中没有提取到文本,可能是扫描版Pdf或图片版pdf")
    return pages


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
    document_units = read_document(file_path)
    # chunks = split_text(text)

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    chunk_index = 0

    for unit in document_units:
        text = unit["text"]
        base_metadata = unit["metadata"]
        chunks = split_text(text)
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            embedding = get_embedding(chunk)

            metadata = {
                **base_metadata,
                "chunk_index": chunk_index,
                "file_name": filename
            }

            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append(metadata)
            documents.append(chunk)

            # 写入elasticsearch
            index_chunk_to_es(chunk_id, chunk, metadata)

            chunk_index += 1


    collection.add(
        ids = ids,
        embeddings = embeddings,
        documents = documents,
        metadatas = metadatas
    )

    return {
        "filename": filename,
        "chunk_count": len(documents),
    }


def search_relevant_chunks(question: str, top_k: int = 5) -> List[dict]:
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
        include=["documents", "metadatas", "distances"]
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks = []

    for document, metadata, distance in zip(documents, metadatas, distances):
        chunks.append({
            "document": document,
            "metadata": metadata,
            "retrieval_type": "vector",
            "distance": distance
        })
    return chunks

def hybrid_search(
        question: str,
        vector_k: int = 5,
        keyword_k: int = 5,
        final_k: int = 8
) -> List[dict]:
    """
    混合召回
    1.chromadb向量检索
    2.elasticsearch bm25关键词检索
    3.根据chunk_id去重合并
    """
    vector_result = search_relevant_chunks(question, top_k=vector_k)
    keywords_result = keyword_search_es(question, top_k=keyword_k)

    merged = []
    chunk_set = set()

    for item in vector_result + keywords_result:
        chunk_index = item['metadata']["chunk_index"]
        if chunk_index not in chunk_set:
            merged.append(item)
            chunk_set.add(chunk_index)

    return merged[:final_k]


def retrieve_with_rerank(
        question: str,
        vector_k: int = 10,
        keyword_k: int = 10,
        top_n: int = 5,
) -> list[dict]:
    """
    混合召回 + rerank.
    """
    candidates = hybrid_search(question, vector_k=vector_k, keyword_k=keyword_k, final_k=vector_k+keyword_k)

    final_chunks = rerank_chunks(question, candidates, top_n)

    # chunks编号
    for index, chunk in enumerate(final_chunks):
        chunk["source_id"] = f"S{index}"

    return final_chunks


def answer_question(question : str) -> dict:
    """
    RAG问答：
    1.检索相关片段
    2.拼接上下文
    3.调用DeepSeek生成答案
    """
    # chunks = search_relevant_chunks(question)
    chunks = retrieve_with_rerank(question)


    context = "\n\n".join([
        f"片段{i+1}:\n{chunk}"
        for i, chunk in enumerate(chunks)
    ])



    prompt = f"""
    你是一个严谨的文档问答助手。
    请只根据下面的文档片段回答用户问题。
    
    要求：
    1. 如果文档片段中没有答案，请回答：文档中没有找到相关信息。
    2. 不要编造文档中不存在的内容。
    3. 回答中的关键结论后面尽量标注来源编号，例如 [S1]、[S2]。
    4. 只能使用下面提供的来源编号，不能编造来源编号。
    
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

    save_qa_history(question, answer, chunks)


    return {
        "question": question,
        "answer": answer,
        "chunks": chunks,
    }


