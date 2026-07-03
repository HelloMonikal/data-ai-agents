
from langchain_core.tools import tool

from agent.core import run_agent
from agent.tools import data_checkup
from agent.llm import llm
from agent.prompts import load_prompt


AGGREGATOR_PROMPT = load_prompt("aggregator")
@tool
def aggregator(task: str) -> str:
    """数据聚合专家。按指定维度分组，计算 SUM/AVG/COUNT 与占比，输出排序后的汇总。
    只做确定性的机械汇总，不做解读、不下结论。

    适用场景：数据管线的第二步，接收清洗后的数据，输出汇总结果。
    输入：包含 CSV 路径、分组列名、指标列名的聚合任务描述。
    返回：聚合后的 CSV 路径 + 汇总说明（分组数、按 SUM 降序的前 3 组）。
    """

    result = run_agent(
        task=task
        ,llm=llm
        ,tools=[]
        ,system_prompt=AGGREGATOR_PROMPT
        ,max_steps=5
        ,verbose= True
        )

    return result