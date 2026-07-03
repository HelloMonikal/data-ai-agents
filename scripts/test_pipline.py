from langchain_core.messages import SystemMessage
from agent.memory import save_memory, search_memory
from agent.agents.data_cleaner import data_cleaner
from agent.agents.aggregator import aggregator
from agent.agents.data_analyst import data_analyst
from agent.agents.report_writer import report_writer
from agent.llm import llm



pipeline = [data_cleaner, aggregator,data_analyst, report_writer]

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

    for expert in pipeline:
        # 运行每个专家agent,让它去处理任务,多个reAct循环发生在这里
        answer = expert.invoke(task)
        print(f"{expert.name} 完成")
        task = task + "\n\n" + f"上一步{expert.name}的输出:\n{answer}"

    # 把这一回合会话的用户以及助手回答用llm总结,存进向量库(RAG记忆)
    extract_prompt = [SystemMessage(
       f"从这轮对话提炼最多一条值得长期记住的事实（用户的信息、偏好、或重要结论），"
       f"一句话，没有就回答'无'。\n前几轮: {task}\n 最后助手答: {answer}"
    )]
    fact = llm.invoke(extract_prompt).content
    if "无" not in fact:
        save_memory(fact)