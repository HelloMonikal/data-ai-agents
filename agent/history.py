import json
from langchain_core.messages import messages_to_dict, messages_from_dict, SystemMessage,ToolMessage


HISTORY_FILE = "history.json"
KEEP_RECENT = 4
TRIGER = 6

def save_history(messages):
    """把 messages 列表序列化存到硬盘"""
    data = messages_to_dict(messages)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return messages_from_dict(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def compress_history(messages,llm):
    """把旧对话压缩成摘要,只保留最近4条原文"""
    if len(messages) <= TRIGER:
        return messages

    split = len(messages) - KEEP_RECENT
    while split < len(messages) and isinstance(messages[split], ToolMessage):
        split += 1

    old = messages[:split]
    recent = messages[split:]

    summary_prompt = old + [
        SystemMessage("请把以上对话总结成一段简短的前情提要，保留关键信息（人名、需求、已完成的事），用第三人称。")
                            ]
    summary = llm.invoke(summary_prompt)

    return [SystemMessage(f"[前情提要] {summary.content}")] + recent