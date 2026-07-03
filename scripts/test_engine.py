import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agent.core import run_agent
from agent.tools import data_checkup


load_dotenv()

llm = ChatOpenAI(
    model_name="deepseek-chat"
    ,api_key=os.environ.get("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    , temperature=0)

result = run_agent(
    task="帮我检查data/sample.csv这份数据的质量"
    ,llm=llm
    ,tools=[data_checkup]
    ,system_prompt="你是一个数据分析专家，擅长解读数据质量报告。"
    ,verbose=True
)

print("\n=== 最终返回 ===")
print(result)