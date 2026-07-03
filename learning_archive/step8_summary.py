from langchain_core.messages import SystemMessage

KEEP_RECENT = 4
TRIGER = 6

def compress_history(messages,llm):
    """把旧对话压缩成摘要,只保留最近4条原文"""
    if len(messages) <= TRIGER:
        return messages

    old = messages[:-KEEP_RECENT]
    recent = messages[-KEEP_RECENT:]

    summary_prompt = old + [SystemMessage("请把以上对话总结成一段简短的前情提要，保留关键信息（人名、需求、已完成的事），用第三人称。")]
    summary = llm.invoke(summary_prompt)

    return [SystemMessage(f"[前情提要] {summary.content}")] + recent