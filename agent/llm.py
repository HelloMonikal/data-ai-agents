"""全项目共享的 LLM 单例。配置只在这里出现一次——改模型/温度只动这一处。"""


import os
from langchain_openai import ChatOpenAI
from  dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model_name="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    , temperature=0)


