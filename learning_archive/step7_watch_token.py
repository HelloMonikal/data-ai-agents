import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    ,temperature=0
)

messages= []

for i in range(1, 6):
    messages.append(HumanMessage(f"这是我的第 {i} 个问题，请简短回答。顺便重复一遍：苹果香蕉橙子葡萄西瓜。"))
    response = llm.invoke(messages)
    messages.append(response)

    usage = response.response_metadata.get("token_usage",{})
    print(f"第 {i} 轮 | "
          f"发送(prompt): {usage.get('prompt_tokens')} tokens | "
          f"当前 messages 长度: {len(messages)} 条")