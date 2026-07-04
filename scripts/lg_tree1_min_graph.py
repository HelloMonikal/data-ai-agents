# scripts/test_langgraph.py  （树2：条件边 —— 纯规则、零 LLM）
# 目的：看清"一个路由函数读 state、决定下一个 node 走谁"。

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    task: str
    route: str       # triage 写进来的判定，留痕让你肉眼看见决策
    result: str      # 最终产物


# ── node：triage 做"判断工作"，把结论写进 state ──
def triage(state: State) -> dict:
    keywords = ["数据", "销售", "报表", "统计"]
    hit = any(k in state["task"] for k in keywords)
    decision = "data" if hit else "chat"
    print(f"[triage] task={state['task']!r} → 判定为 {decision}")
    return {"route": decision}


def run_data(state: State) -> dict:
    print("[run_data] 走数据分支：假装派了四专家")
    return {"result": "已跑数据管线"}


def run_chat(state: State) -> dict:
    print("[run_chat] 走闲聊分支：直接答")
    return {"result": "你好，我在"}


# ── 路由函数：读 state，返回"往哪走"的 KEY（一个字符串，不是 state 增量）──
def route_after_triage(state: State) -> str:
    return state["route"]


# ── 搭图 ──
builder = StateGraph(State)
builder.add_node("triage", triage)
builder.add_node("run_data", run_data)
builder.add_node("run_chat", run_chat)

builder.add_edge(START, "triage")

# 条件边：从 triage 出来，用 route_after_triage 的返回值查表决定去哪
builder.add_conditional_edges(
    "triage",
    route_after_triage,
    {
        "data": "run_data",   # 路由函数返回 "data" → 去 run_data
        "chat": "run_chat",   # 返回 "chat"       → 去 run_chat
    },
)

builder.add_edge("run_data", END)
builder.add_edge("run_chat", END)

app = builder.compile()

if __name__ == "__main__":
    for task in ["把销售数据跑一遍", "今天天气不错"]:
        print(f"\n===== 输入：{task} =====")
        final = app.invoke({"task": task, "route": "", "result": ""})
        print("最终 state：", final)