from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from agent.llm import llm


# ── 一个简单工具：查月度销售额（模型没法自己知道，逼它真调工具）──
@tool 
def get_sales(month:str) -> str:
    """查询指定月份的销售额。month 用中文月份，如 '三月'。"""
    fake = {"一月": 12000, "二月": 9500, "三月": 20300}
    return str(fake.get(month, "无数据"))

tools = [get_sales]
tools_by_name = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    message:list

# ── agent node = 你的 ai_msg = llm_with_tools.invoke(messages) ──
def agent(state:State) -> dict:
    ai_msg = llm_with_tools.invoke(state["message"])
    return {"message": state["message"] + [ai_msg]}  # 手动拼，故意不用 reducer（树4 再换）

def should_continue(state:State) -> str:
    last = state["message"][-1]
    if last.tool_calls: # 模型这轮想调工具 → 去 tools
        return "tools"
    return "end"

# ── tools node =  tools_by_name 查表 + ToolMessage 喂回 ──
def tool_node(state:State) -> dict:
    last = state["message"][-1]
    new_msgs = []
    for call in last.tool_calls:
        selected = tools_by_name[call["name"]]
        result = selected.invoke(call["args"])
        new_msgs.append(
            ToolMessage(content=str(result), tool_call_id=call["id"])
        )
    return {"message": state["message"] + new_msgs}

# ── 搭图：注意这是【带环】的图 ──
builder = StateGraph(State)
builder.add_node("agent", agent)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }  # 查表全覆盖：路由函数只会返回这两个（bug#18 记忆）
)
builder.add_edge("tools", "agent")   # ← 绕回去：这根边就是你 for 循环的"下一圈"


app = builder.compile()

if __name__ == "__main__":
    app.get_graph().print_ascii()
    result = app.invoke({"message":[HumanMessage(content="请帮我查三月的销售额")]} )
    for m in result["message"]:
        m.pretty_print()