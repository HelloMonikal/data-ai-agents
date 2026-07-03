import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from agent.core import run_agent
from agent.agents.data_analyst import data_analyst
from agent.agents.report_writer import report_writer

load_dotenv()

llm = ChatOpenAI(
    model="deepseek-chat"
    ,api_key=os.getenv("DEEPSEEK_API_KEY")
    ,base_url="https://api.deepseek.com"
    ,temperature=0)

result = run_agent(
    task="帮我分析 data/sample.csv，并把分析结果整理成一份正式的数据质量报告"
    ,llm=llm
    ,tools=[
        data_analyst,report_writer]
    ,system_prompt=("你是一个项目主管，手下有两个专家：\n"
            "- data_analyst：负责分析数据、检查数据质量\n"
            "- report_writer：负责把结论整理成正式报告\n"
            "根据任务，决定调用哪些专家、按什么顺序。"
            "通常先让分析师得出结论，再让撰写员整理成报告。"
            "最后把最终报告交给用户。"
    ),
    verbose=True,
)
print("\n=== 主管交付的最终成果 ===")
print(result)