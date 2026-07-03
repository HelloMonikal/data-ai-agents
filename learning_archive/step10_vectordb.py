
import chromadb
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
client = chromadb.Client()
collection = client.create_collection("memories", metadata={"hnsw:space": "cosine"}, )

memories = [
    "用户的名字叫小杜",
    "sample.csv 有 20 行 9 列，存在缺失值和异常值",
    "用户在学习 Agent 开发，用的是 DeepSeek 的模型",
    "用户喜欢摩托车旅行",
]
vectors_np = model.encode(memories)
vectors = vectors_np.tolist()

collection.add(
    documents=memories,
    embeddings=vectors,
    ids=[str(i) for i in range(len(memories))],
)
print(f"已存入 {len(memories)} 条记忆到向量数据库中。")

query = "我叫什么名字"
query_vec_np = model.encode(query)
query_vec = query_vec_np.tolist()

results = collection.query(
    query_embeddings=[query_vec],
    n_results=3,
)
print(f"问题{query}\n最接近的记忆是：")
for doc in results["documents"][0]:
    print(f"- {doc}")

for text,score in zip(memories,cos_sim(query_vec_np,vectors_np)[0]):
    print(f"相似度 {score:.3f} | {text}")

