
from dotenv import load_dotenv
from typing import Any

from sentence_transformers import CrossEncoder
load_dotenv()

reranker_model = None

def get_reranker_model():
    """
    懒加载 reranker 模型.
    第一次调用时才加载，避免项目启动慢.
    """
    global reranker_model
    if reranker_model is None:
        reranker_model=  CrossEncoder(
            r"D:\Models\bge-reranker-base",
        )

    return reranker_model


def rerank_chunks(
        question: str,
        candidates: list[dict[str, Any]],
        top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    对 hybrid_search 召回的候选 chunks 进行重排序

    输出：
    按 rerank_score 从高到低排序后的 top_n chunks。
    """

    if not candidates:
        return []

    model = get_reranker_model()

    pairs = [
        [question, item["document"]]
        for item in candidates
    ]

    scores = model.predict(pairs)

    reranked = []

    for item, score in zip(candidates, scores):
        new_item = item.copy()
        new_item["rerank_score"] = float(score)
        reranked.append(new_item)

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:top_k]