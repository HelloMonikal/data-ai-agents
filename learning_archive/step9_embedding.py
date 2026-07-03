
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim
# 加载一个小而好用的开源 embedding 模型（第一次会自动下载）
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

query = "这份数据有什么问题" 

candidates = ["这份数据有什么问题"
             ,"sample_csv存在缺失值和异常值"
             ,"今天天气不错适合出门"
             ,"数据质量检查发现了一些问题"
             ,
             ]


query_vector = model.encode(query)
cand_vecs = model.encode(candidates)

for text,score in zip(candidates,cos_sim(query_vector,cand_vecs)[0]):
    print(f"相似度 {score:.3f} | {text}")


# print("原文:", text)
# print("向量长度:", len(vector))        # 这段文字被翻译成了多少个数字
# print("向量前10个数字:", vector[:10])  # 瞄一眼这串数字长什么样