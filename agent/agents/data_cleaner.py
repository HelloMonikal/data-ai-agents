from langchain_core.tools import tool

from agent.core import run_agent
from agent.tools import data_checkup
from agent.llm import llm
from agent.prompts import load_prompt



CLEANER_PROMPT = load_prompt("cleaner")

@tool
def data_cleaner(task: str) -> str:
    """数据清洗专家。按固定规则清洗 CSV：缺失值填充、重复去重、日期格式化。
    只做无争议的标准化清洗，不处理异常值、不做分析。

    适用场景：数据管线的第一步，接收原始数据，输出干净数据。
    输入：包含 CSV 文件路径的清洗任务描述。
    返回：清洗后的 CSV 路径 + 操作日志（行数变化、填充统计、保留列名）。
    """

    result = run_agent(
        task=task
        ,llm=llm
        ,tools=[]
        ,system_prompt=CLEANER_PROMPT
        ,max_steps=5
        ,verbose= True
        )

    return result


