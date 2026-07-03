from langchain_core.messages import HumanMessage,ToolMessage,SystemMessage

def run_agent(task, llm, tools, system_prompt=None, max_steps=10,verbose=False):
    """运行一个ReAct Agent, 跑完整个思考-行动循环，返回最终回答。
    
    task: 要完成的任务（字符串）
    llm: 语言模型
    tools: 这个 Agent 能用的工具列表
    system_prompt: 给这个 Agent 的角色设定（可选）
    max_steps: 最多循环几轮（防止失控）
    verbose: 是否打印中间过程    
    """
    tools_by_name = {t.name: t for t in tools}
    llm_with_tools = llm.bind_tools(tools)

    messages = []
    if system_prompt:
        messages.append(SystemMessage(system_prompt))
    messages.append(HumanMessage(task))

    for step in range(1,max_steps+1):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)

        if not ai_msg.tool_calls:
            return ai_msg.content

        if verbose:
            print(f"第{step}轮, 模型决定调用工具: {[tc['name'] for tc in ai_msg.tool_calls]}")

        for tool_call in ai_msg.tool_calls:
            selected_tool = tools_by_name[tool_call["name"]]
            result = selected_tool.invoke(tool_call["args"])
            if verbose:
                print(f"{tool_call['name']} -> {result[:80]}...")
            messages.append(ToolMessage(tool_call_id=tool_call["id"], content=result))

    return "达到最大步数, 未能完成任务"