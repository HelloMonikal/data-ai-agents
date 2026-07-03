import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.tools import tool
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
        # 使用 eval 计算表达式的值


    
llm_with_tool = llm.bind_tools([calculator])
response = llm_with_tool.invoke("帮我算一下 2331 乘以 456 等于几")

print("模型回复内容",response.content)
print("模型想调用的工具",response.tool_calls)
