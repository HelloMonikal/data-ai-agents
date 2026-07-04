from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from agent.llm import llm

@tool
def get_sales(month: str) -> str:
    """查询指定月份的销售额。month 用中文月份，如 '三月'。"""
    fake = {"一月": 12000, "二月": 9500, "三月": 20300}
    return str(fake.get(month, "无数据"))

tools = [get_sales]
tools_by_name = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

# ★变化点1：messages 字段挂上 add_messages reducer
class State(TypedDict):
    messages: Annotated[list, add_messages]  # 这里的 add_message reducer 会把新消息 append 到 list 里

def agent(state: State) -> dict:
    ai_msg = llm_with_tools.invoke(state["messages"])
    return {"messages": [ai_msg]}  # ★变化点2：这里不用手动拼了，reducer 会自动 append

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    return "tools" if last.tool_calls else "end"

def tool_node(state: State) -> dict:
    last = state["messages"][-1]
    new_msgs = []
    for call in last.tool_calls:
        selected = tools_by_name[call["name"]]
        result = selected.invoke(call["args"])
        new_msgs.append(
            ToolMessage(content=str(result), tool_call_id=call["id"])
        )
    return {"messages": new_msgs}

builder = StateGraph(State)

builder.add_node("agent",agent)
builder.add_node("tools",tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools"
        ,"end" : END
    }
)
builder.add_edge("tools", "agent")
app = builder.compile()

if __name__ == "__main__":
    result = app.invoke({"messages": [HumanMessage(content="请问三月的销售额是多少？")]})
    for m in result["messages"]:
        m.pretty_print()