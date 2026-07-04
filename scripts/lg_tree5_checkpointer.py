
from langgraph.graph import StateGraph, START, END ,MessagesState
from langgraph.checkpoint.memory import InMemorySaver
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


def agent(state: MessagesState) -> dict:
    ai_msg = llm_with_tools.invoke(state["messages"])
    return {"messages": [ai_msg]}

def should_continue(state: MessagesState) -> str:
    return "tools" if state["messages"][-1].tool_calls else "end"


def tool_node(state: MessagesState) -> dict:
    last = state["messages"][-1]
    new_msgs = []

    for call in last.tool_calls:
        selected = tools_by_name[call["name"]]
        result = selected.invoke(call["args"])
        new_msgs.append(
            ToolMessage(content=str(result), tool_call_id=call["id"])
        )
    return {"messages": new_msgs}

builder = StateGraph(MessagesState)
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

checkpointer = InMemorySaver()
app = builder.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    # ★变化4：invoke 时必须带 thread_id，checkpointer 靠它认"哪条会话"
    config = {"configurable": {"thread_id": "user-1"}}
    config2 = {"configurable": {"thread_id": "user-2"}}   # 新开一条线

    print("===== 第 1 次 invoke =====")
    r1 = app.invoke({"messages": [HumanMessage(content="我叫小杜，请记住。顺便查下三月销售额。")]},config)
    r1["messages"][-1].pretty_print()


    print("===== 第 2 次 invoke ===== （同一个 thread_id，不重复说三月）=====)")
    r2 = app.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config)
    
    # print("===== 第 2 次 invoke ===== （不同 thread_id，不重复说三月）=====)")
    # r2 = app.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config2)

    r2["messages"][-1].pretty_print()


    print(f"\n最终这条会话共积累了 {len(r2['messages'])} 条消息")
