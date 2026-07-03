from langchain_openai import ChatOpenAI
from langchain_core.tools import tool 
from agent.core import run_agent
from agent.llm import llm
from agent.prompts import load_prompt

REPORT_WRITTER_PROMPT = load_prompt("report_writter")

@tool 
def report_writer(topic: str) -> str:
    """报告撰写专家。把分析发现组织成结构清晰、语言正式的书面报告。
    只做表达与结构，不做新的分析或计算。

    适用场景：数据管线的第四步（最后一步），接收分析发现，产出正式报告。
    输入：分析师给出的发现与结论。
    返回：正式报告文本。
    """

    result = run_agent(
        task=f"请把以下内容整理成一份正式、专业、结构清晰的书面报告：\n\n{topic}"
        ,llm=llm.bind(temperature=0.3)
        ,tools=[]
        ,system_prompt=REPORT_WRITTER_PROMPT
        ,max_steps=3
)


    return result