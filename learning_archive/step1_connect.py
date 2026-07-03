import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    ,temperature=0

)

response = llm.invoke("23 乘 456 等于几")
print(response.content)
