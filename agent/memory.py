import os

os.environ["HF_HUB_OFFLINE"] = "1"          # 强制离线，只用本地缓存
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import chromadb

from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
_client = chromadb.PersistentClient(path="./memory_db")
_collection = _client.get_or_create_collection(
    "long_term_memory"
    ,metadata={"hnsw:space": "cosine"}
)

SIMILAIRITY_THRESHOLD = 0.3

def save_memory(text):
    """把一条记忆存进向量库"""
    vec = _model.encode(text).tolist()
    count = _collection.count()
    _collection.add(
        documents=[text],
        embeddings=[vec],
        ids=[f"mem_{count}"],
    )

def search_memory(query, n_results=3):
    """在向量库中搜索与query相似的记忆,只返回相似度高的"""

    if _collection.count() == 0:
        return []
    
    query_vec = _model.encode(query).tolist()
    results = _collection.query(
        query_embeddings=[query_vec],
        n_results=min(n_results, _collection.count()),
    )

    docs = results["documents"][0]
    distance = results["distances"][0]

    relevant = []
    for doc, score in zip(docs, distance):
        similarity = 1 - score
        if similarity >= SIMILAIRITY_THRESHOLD:
            relevant.append((doc))
    return relevant