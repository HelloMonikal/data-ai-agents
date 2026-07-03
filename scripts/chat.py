from langchain_core.messages import SystemMessage
from agent.memory import save_memory, search_memory
from agent.core import run_agent
from agent.agents.data_cleaner import data_cleaner
from agent.agents.aggregator import aggregator
from agent.agents.data_analyst import data_analyst
from agent.agents.report_writer import report_writer
from agent.llm import llm
from agent.prompts import load_prompt



supervisor_tools = [data_cleaner, aggregator,data_analyst, report_writer]
supervisor_prompt = load_prompt("supervisor")

while True:

    #用户发起对话
    user_input = input("你: ")
    if user_input.strip() in ("exit", "quit","退出"):
        break

    #rag检索用户问题的记忆,把记忆加载到memory_note里
    related = search_memory(user_input)
    memory_note = ""
    if related:
        memory_note = "[相关记忆]\n" + "\n".join(f" - {m}" for m in related)
        print(f"  [检索到 {len(related)} 条相关记忆]")
    task = user_input
    if memory_note:
        task = f"{memory_note}\n\n用户问题：{user_input}"

    # 运行supervisor_tools agent,让它去决定用哪些工具agent,多个reAct循环发生在这里
    answer = run_agent(
        task=task
        ,llm=llm
        ,tools=supervisor_tools
        ,system_prompt=supervisor_prompt
        ,verbose=True
    )
    print("助手:", answer)


    # 把这一回合会话的用户以及助手回答用llm总结,存进向量库(RAG记忆)
    extract_prompt = [SystemMessage(
       f"从这轮对话提炼最多一条值得长期记住的事实（用户的信息、偏好、或重要结论），"
       f"一句话，没有就回答'无'。\n用户说: {user_input}\n助手答: {answer}"
    )]
    fact = llm.invoke(extract_prompt).content
    if "无" not in fact:
        save_memory(fact)