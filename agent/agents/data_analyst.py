from langchain_core.tools import tool

from agent.core import run_agent
from agent.tools import data_checkup
from agent.llm import llm
from agent.prompts import load_prompt



DATA_ANALYST_PROMPT = load_prompt("data_analyst")

@tool
def data_analyst(task: str) -> str:
    """数据分析专家。解读汇总结果，发现数据中的异常、逻辑矛盾与值得注意的模式，给出有依据的结论。
    可调用 data_checkup 核查明细数据的质量与逻辑一致性。

    适用场景：数据管线的第三步，接收聚合结果，产出分析发现。
    输入：包含聚合结果与清洗后数据路径的分析任务描述。
    返回：结构化的分析发现（异常点、洞察、结论）。
    """

    result = run_agent(
        task=task
        ,llm=llm
        ,tools=[data_checkup]
        ,system_prompt=
           DATA_ANALYST_PROMPT
        ,max_steps=5
        ,verbose= True
        )

    return result