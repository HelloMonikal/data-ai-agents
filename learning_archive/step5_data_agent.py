import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, ToolMessage
from tools import data_checkup

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    ,temperature=0
)


tools = [data_checkup]
tools_by_name = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools=tools)

messages = [HumanMessage("帮我看看 sample.csv 这份数据有什么问题")]

step = 0
while True:
    step += 1
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if not ai_msg.tool_calls:
        print(f"模型决定收尾,第{step}最终回答",ai_msg.content)
        break

    print(f"第{step}轮模型决定调用工具{[tc['name'] for tc in ai_msg.tool_calls]}")

    for tool_call in ai_msg.tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        result = selected_tool.invoke(tool_call["args"])
        print(f"  工具返回（前200字）: {result[:200]}...")
        messages.append(ToolMessage(tool_call_id=tool_call["id"], content=result))