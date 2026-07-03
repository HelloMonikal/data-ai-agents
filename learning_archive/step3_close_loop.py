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

tools = [calculator]
tools_by_name = {tool.name: tool for tool in tools}


llm_with_tools = llm.bind_tools([calculator])

messages =  [HumanMessage("先算 123 乘以 456，再把结果加上 1000")]


# 模型决定要用工具 thought
ai_msg = llm_with_tools.invoke(messages)
messages.append(ai_msg)
print("1 模型回复内容",ai_msg.tool_calls)


# 真正执行内容 action
for tool_call in ai_msg.tool_calls:
    selected_tool = tools_by_name[tool_call["name"]]
    result = selected_tool.invoke(tool_call["args"])
    print("2 工具执行结果",result)
    messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

final = llm_with_tools.invoke(messages)
print("3 模型最终回复内容",final.content)

print("模型其实还想调工具:", final.tool_calls)