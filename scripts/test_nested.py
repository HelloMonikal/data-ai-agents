import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agent.core import run_agent
from agent.agents.data_analyst import data_analyst


load_dotenv()
llm = ChatOpenAI(
    model_name="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    , temperature=0
)

result = run_agent(
    task="帮我看看 data/sample.csv 这份数据怎么样，有什么需要注意的"
    ,llm=llm
    ,tools=[data_analyst]
    ,system_prompt=(
            "你是一个协调者。遇到数据相关的任务，"
            "交给你的数据分析师工具去处理，然后把结论清晰地转达给用户。"
        )
    ,verbose=True
)

print("\n=== 主 Agent 最终回答 ===")
print(result)
