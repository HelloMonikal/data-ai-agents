import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools  import tool
from langchain_core.messages import HumanMessage, ToolMessage


load_dotenv()
llm = ChatOpenAI(
    model="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    ,temperature=0
)


@tool
def calculator(expression: str) -> str:
    """
    计算器工具，接收一个数学表达式，比如123*456,输入是字符串的算式。
    """
    try:
        result = eval(expression)
        return f"计算结果是{result}"
    except Exception as e:
        return f"计算出错: {e}"

@tool
def get_string_len(text: str) -> str:
    """
    计算字符串长度的工具，接收一个字符串，返回其长度。
    """
    try:
        return f"字符串长度是{len(text)}"
    except Exception as e:
        return f"计算出错: {e}"



tools = [calculator,get_string_len]
tools_by_name = {tool.name: tool for tool in tools}


llm_with_tools = llm.bind_tools(tools)

messages =  [HumanMessage("帮我算一下 100 除以 0 等于几")]


step = 0
while True:
    step += 1
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if not ai_msg.tool_calls:
        print(f"模型决定收尾,第{step}轮模型回复内容",ai_msg.content)
        break

    print(f"第{step}轮模型决定调用工具{[tc['name'] for tc in ai_msg.tool_calls]}")


    for tool_call in ai_msg.tool_calls:
        selected_tool = tools_by_name[tool_call["name"]]
        result = selected_tool.invoke(tool_call["args"])
        print(f"  [Observation] 喂回给模型的观察值 → {result}")  # 让它显形
        print(f"执行工具{tool_call['name']}{tool_call['args']} -> {result}")
        messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

