# LEARNING_LOG — 手搓 AI Agent 学习档案

> 这份文档是「我们这场学习对话的外部长期记忆」。

> 它存在硬盘上，不受任何对话上下文窗口的限制。

> 开新对话时，把这份贴给 Claude（或放进 Project 知识库），即可瞬间「恢复记忆」。

> —— 这本身就是课程里学到的：重要的东西持久化到外部，不要只活在易失的上下文里。

>

> **最近更新：完成第2周·站4——LangGraph 五棵树全通（state/node/边 · 条件边 · 带环 ReAct · reducer/MessagesState · checkpointer）。环境迁移：Python 3.9→3.11（Homebrew，纯 venv、弃 conda），补上 requirements.txt。下一步：capstone——四专家管线迁 LangGraph。**

---

## 0. 学习者画像（给接手的 Claude 看）

- 背景：数据分析 / 大数据工程师（Hive、Spark、PySpark、Python、SQL、Presto），正在向 AI Agent 应用工程师转型，同时在找工作。目标定位「数据 × AI 复合岗」——能建生产级 Agent 的数据工程师，框架为「AI 能力升级数据工作」而非转行。
- 设备：MacBook（arm64）。
- LLM 提供方：**DeepSeek API**（`deepseek-chat`，`https://api.deepseek.com`），通过 LangChain 的 `ChatOpenAI` 接入（DeepSeek 兼容 OpenAI 格式），`temperature=0`。
- Python：**3.11（Homebrew 装的本体，项目内纯 venv 隔离，已弃用 conda）**。曾用 3.9/miniconda，因 LangChain v1.1 / LangGraph 1.1 砍掉 3.9（需 3.10+）而迁移，详见第 6 节。
- 学习风格（很重要）：
  - 偏好直接、无废话、假设有工程基础。
  - **靠"感觉不对劲"主动发现 bug 和概念漏洞**，会质疑、会追问到根因，不满足于"能跑"。
  - 喜欢先看"蓝图/全景"（森林）再钻细节（树）；每个新机制先脱离主系统单独跑通再接回。
  - 手敲代码（常配合 IDE 自动补全），重点在理解而非默写——验证标准是"能不能讲清逻辑、能不能改一个点并预测结果"，不是"能不能背着敲"。
  - 会主动重构、拆模块、主动质疑设计（不用别人提醒）。**会追问"改这个结构会不会有悖当初的设计原因"——重构前先还原原意图，不盲改。**
  - **"改一点→预测→验证"是他默认的实验方式**，每个实验先写预测再跑、拿结果对账（站4 五棵树全程如此）。

---

## 1. 项目结构（当前）

项目根：`~/projects/claude_tutorialbyclaude/data-ai-agents/`（已是 Git 仓库，分支 main；GitHub 仓库名 `data-ai-agents`）

```

data-ai-agents/

├── agent/ # 核心代码包

│ ├── __init__.py

│ ├── core.py # run_agent() —— 可复用的 ReAct 引擎

│ ├── llm.py # 全项目共享的 LLM 单例（配置只在这一处）

│ ├── tools.py # data_checkup 工具

│ ├── memory.py # RAG 长期记忆（Chroma + sentence-transformers）

│ ├── history.py # 持久化(load/save) + 摘要压缩(compress_history)

│ │ # ⚠️ 走 A 路线后 chat.py 已不再用它，属遗留

│ ├── prompts/ # 所有角色 prompt 集中（一角色一 .md）

│ │ ├── __init__.py # load_prompt(name) 读取器（Path(__file__) 定位，不依赖工作目录）

│ │ ├── cleaner.md / aggregator.md / data_analyst.md / report_writer.md / supervisor.md

│ └── agents/ # 各个子 Agent（包成工具）

│ ├── __init__.py

│ ├── data_cleaner.py # 清洗专家（tools=[]，只标准化、不碰异常值）

│ ├── aggregator.py # 聚合专家（tools=[]，机械汇总、前置列校验）

│ ├── data_analyst.py # 分析专家（配 data_checkup，唯一"开放/动脑"的）

│ └── report_writer.py # 撰写专家（tools=[]，分析风：可综合串联、不无中生有）

├── scripts/ # 入口脚本（从项目根用 python -m scripts.xxx 运行）

│ ├── chat.py # 对话入口：Supervisor 模式（主管派单，闲聊直答）

│ ├── test_pipline.py # 管线测试：Pipeline 模式（控制流串四棒顺序）

│ ├── test_engine.py # 测 run_agent 引擎

│ ├── test_nested.py # 测 Agent 套娃（站1）

│ ├── test_supervisor.py # 测 Supervisor 编排（站2）

│ ├── lg_tree1_min_graph.py # 【站4】最小图：纯函数、零 LLM（state/node/硬边）

│ ├── lg_tree2_conditional.py # 【站4】条件边：纯规则路由（node想/edge派、查表全覆盖）

│ ├── lg_tree3_react.py # 【站4】ReAct 环重画成图（LLM 进场，认出 run_agent）

│ ├── lg_tree4_reducer.py # 【站4】reducer + MessagesState（add_messages 守配对）

│ ├── lg_tree5_checkpointer.py # 【站4】checkpointer + thread_id（跨 invoke 持久化）

│ └── test_langgraph.py # 站4 期间的草稿位（写新树时用，定稿后另存 lg_*）

├── data/

│ └── sample.csv # 测试数据（20行9列销售数据）

├── learning_archive/ # 学习文物：step1~step10（不删，留作纪念）

├── memory_db/ # Chroma 持久化向量库（运行时生成，git忽略）

├── history.json # 对话历史持久化（运行时生成，git忽略；走A后已不再写入）

├── requirements.txt # 【新】全量 pip freeze 锁文件（venv 误删后重建时补上，见第6节）

├── .env # DEEPSEEK_API_KEY（git忽略，已确认安全）

├── .gitignore # 忽略 .env / venv/ / memory_db/ / history.json / __pycache__

├── README.md

└── venv/ # 虚拟环境（Python 3.11，git忽略）

```

运行方式：在项目根目录、激活 venv 后，`python -m scripts.chat`（对话）/ `python -m scripts.test_pipline`（测管线）/ `python -m scripts.lg_tree5_checkpointer`（跑某棵树）。

> **五个 `lg_tree*.py` 是"活文物"**：都是干净定稿、随时能 `-m` 跑来回看，暂留 `scripts/`（`lg_` 前缀聚堆、和 `test_*` 分开）。等整站 LangGraph 彻底结束、确定不再回头对照时，再一次性挪进 `learning_archive/` 退役封存（规模逼出来再动，不提前猜）。

---

## 2. 学习进度总览

| 阶段 | 内容 | 状态 |
|------|------|------|
| 第1周 · 地基 | Claude Code 环境、ReAct 内核、数据工具 | ✅ |
| 第1周 · 记忆主线 | 持久化 → 摘要压缩 → RAG 检索 | ✅ |
| 工程重构 | 散文件 → 正经 Python 包结构 | ✅ |
| 第2周 · 站1 | Agent 即工具（套娃） | ✅ |
| 第2周 · 站2 | Supervisor 编排（多专家协作） | ✅ |
| 第2周 · 方向二 | 多 Agent 团队接入对话循环（chat.py，方式A） | ✅ |
| 工程 · Git | 引入版本管理 | ✅ |
| 工程 · 清僵尸 | 清理 chat.py 会话历史残留（走 A 路线） | ✅ |
| 工程 · 配置集中 | prompt 抽成 prompts/、LLM 收成共享单例 | ✅ |
| 第2周 · 站3 | 子 Agent 专精分工（四专家 + Pipeline/Supervisor 两模式） | ✅ |
| 工程 · 环境迁移 | Python 3.9→3.11、弃 conda 纯 venv、补 requirements.txt | ✅ |
| 第2周 · 站4 | LangGraph 五棵树（state/node/边 · 条件边 · ReAct环 · reducer · checkpointer） | ✅ |
| 第2周 · 站4 capstone | 四专家管线迁 LangGraph（纯函数 node + 结构化 state + 边定序） | ⏭ **下一步** |
| 第2周 · 站5 | MCP 接真实工具 | ⏭ |
| 第3周 | 做产品（电商数据/求职/视频自动化三选一） | ⏭ |
| 第4周 | 部署上线 + 工作流固化 | ⏭ |

当前进度：约整月 55%。最硬的地基已打完，多 Agent 两种编排 + LangGraph 五大机制均已手写验证；下一步把两者合流（capstone）。

---

## 3. 核心机制（已掌握，手写并验证过）

### 3.1 ReAct 循环（Agent 的心脏）

- **Thought → Action → Observation** 三步循环：

  - **Thought** = 模型决定要不要调工具、调哪个、传什么参数（`ai_msg.tool_calls`）。

  - **Action** = 程序真正执行工具（`selected_tool.invoke(args)` 这个执行动作本身）。

  - **Observation** = 工具返回结果（`result`，包装成 `ToolMessage` 喂回历史）。

- **模型每开口一次 = 一次 Thought**。"最终回答"那次 invoke 也是 Thought——只是结论是"够了，不调工具了"。

- **循环终止 = 某轮 Thought 不再返回 tool_calls**（`if not ai_msg.tool_calls: break`）。圈数由模型判断。

- 生产化：`for step in range(max_steps)` 代替 `while True`，加最大轮数保险。

- **（站4 认出）** 这整个循环 = LangGraph 里一张两节点带条件边的图（agent⇄tools + 回边），`max_steps` = runtime 的 `recursion_limit`。见 3.8。

### 3.2 工具机制

- `@tool` 装饰器 + 文档字符串把函数变成工具。**文档字符串是"接口契约"**，模型靠它判断何时用，比函数体还重要。

- **docstring 焊死在函数上，不能像 prompt 那样抽走**：`@tool` 靠读函数的 `__doc__` 生成工具描述，docstring 是装饰器语法的一部分，物理上必须长在函数正下方。抽走 = 工具契约丢失。（对比：system_prompt 是运行时数据，可以抽去 prompts/ 集中管理。）

- 多工具调度：`tools_by_name = {t.name: t for t in tools}` 按名字查表分发，不能写死。

- `llm.bind_tools(tools)`（会翻译成 API 格式，翻译工具）≠ `llm.bind(temperature=...)`（覆盖普通参数，不翻译）。两个方法名像，职责不同。

### 3.3 三层记忆系统（按"信息住在哪"分类）

| 层 | 机制 | context 内/外 | 特点 |

|----|------|--------------|------|

| 会话内记忆 | `messages` 列表 | 内（全量） | 精确有上限，关了就丢 |

| 持久化 | 存 `history.json` + 读回 | 内 | 手搓版 --continue |

| 摘要压缩 | `compress_history` → SystemMessage | 内（压缩） | 聊久不爆，但**有损丢细节** |

| RAG 检索 | Chroma 向量库按相似度捞原文 | **外**（按需） | 容量无限、细节不丢 |

- **硬区分是位置（内/外），软标签是寿命（long/short）**。摘要="桌角便利贴"，RAG="书柜"。

- 每一站都是上一站局限逼出：列表会丢→持久化；会爆→摘要；有损→RAG。

- **⚠️ 现状（走 A 路线后）**：上表三层是在**单 Agent** 时代手写并验证过的；转多 Agent（Supervisor + 无状态 `run_agent`）后，**主程序已主动拔掉 in-context 三层**，跨轮连续性暂时只靠 RAG（把检索结果拼进 task 传入）。这是刻意的解耦，不是缺失。

- **（站4 已落地）** 当初预告的"对话状态在站4 重新安家"已完成：会话历史迁到 LangGraph 的 **MessagesState + checkpointer**（见 3.8 与第 4 节"记忆版图对应"）。摘要压缩这一层暂无 LangGraph 对应物，等真聊到爆再说。

### 3.4 run_agent 引擎（多 Agent 基础零件）

- `run_agent(task, llm, tools, system_prompt, max_steps, verbose)` —— 把内层 ReAct 循环抽成函数。

- **关键：从 print 改成 return**——结果交还调用者（可能是另一个 Agent）。

- 同一引擎，换不同 tools / system_prompt，驱动不同 Agent。**主 Agent 和子 Agent 都用它。**

- **run_agent 本质是"选择器"**：它的价值在于让 LLM 从**多个**工具里推理该调谁。只有一个候选、且确定要调它时，套 run_agent 是冗余——直接 `.invoke` 执行即可。见 3.5 的 Pipeline vs Supervisor。

### 3.5 多 Agent 协作 —— 两种编排模式（站3 定型）

- **Agent 即工具（站1）**：把整个 Agent 用 `@tool` 包成函数，内部调 run_agent。外层看它就是普通工具 → Thought 循环**套娃**。

- **Supervisor 模式（站2 / chat.py）**：主管 Agent 手握**多个**专家工具，用 LLM **判断**派谁、何时派、如何整合。`run_agent(tools=[全部专家], system_prompt=主管prompt)` 一次调用。**适合无硬性顺序的协作。**

- **Pipeline 模式（站3 / test_pipline.py）**：专家顺序**写死**，用控制流串起来，前一棒输出拼进后一棒 task。`for expert in pipeline: expert.invoke(task)`。**适合有硬依赖顺序的场景（如数仓分层 ODS→DWD→DWS→ADS）。**

- **两者的本质区别 = 硬依赖交给谁**：Supervisor 把"该调谁"交给 LLM 判断（软）；Pipeline 把顺序交给 Python 控制流强制（硬）。**类比数据工程：调度依赖（DAG）从不靠在 SQL 里写"请按顺序"，靠调度系统的依赖边强制。** 硬依赖靠结构保证，不靠嘱咐。

- **软/硬错配是站3 最大的坑**：让 LLM（软指令）去遵守"清洗必须在汇总前"这种硬依赖 → 会静默跳步、甚至幻觉"我已经做过了"，产出看着完整实则跳步的假货。原则：**硬依赖（顺序、必经）交给控制流；软判断（要不要启动、异常怎么办）交给 LLM。**（站4 把这条正式落成：普通边=硬、条件边=软，同图。见 3.8。）

- **专精 > 全能**：每专家只配该有的工具。

- **要不要给专家配工具，看职责开放度**：职责确定（清洗、聚合=写死规则）→ 不需要工具、甚至不需要 LLM；职责开放（分析=不知道会发现什么，observation 不可预测）→ 才需要工具 + 多轮 ReAct。本项目里只有 data_analyst 配了 data_checkup。

- **协作能涌现更深洞察**：站2 实测中，分析师+撰写员叠加推理出"检查 revenue=quantity×unit_price 逻辑关系"——单 Agent 未必想到。

- **多 Agent 记忆架构**：短期工作记忆各自独立、用完即弃（子Agent无状态最常用）；长期知识共享一个库（架构A，memory.py 本就是共享单例）。给每Agent各建一套=过度设计。

### 3.6 职责边界设计（站3 核心：边界活在 prompt 里）

- 每个专家的 prompt 都要写两半：**「我管什么」+「我明确不管、交给谁」**。上一个的"不管"正好接上下一个的"管" → 四段严丝合缝，无重叠也无缝。**读一套多 Agent prompt，要盯"接缝"，不是盯单个。**

- **三面承重墙**（本项目四专家的边界）：

  1. **cleaner 不碰异常值 ↔ analyst 发现异常**：清洗的"修正异常"和分析的"发现异常"是**同一批数据点的争夺**；上游缩尾=销毁下游要分析的证据。对应数仓：DWD 只做标准化，业务异常判断留 ADS。**"发现"类和"修正"类职责必须分开，且修正不能跑在发现前。**

  2. **aggregator 只陈述事实 ↔ analyst 解读事实**：同一批数字，aggregator 只许"按 SUM 降序如实列"，不许说"贡献最大"（带判断）；解读留给分析师。**"陈述"和"解读"劈成两个专家。**

  3. **analyst 产出发现 ↔ writer 表达**：writer 定为"分析风"——**准许综合已有的**（串联发现 A/B、提炼主线），**禁止发明没有的**（引入分析师没给的数字/无据结论）。判据："你写的每句，追问'有没有分析师给的依据？'"。

- **缝要主动补**：aggregator 加**前置列校验**（分组前先确认 group_by/metrics 列存在，不存在就明确报错，别让 pandas 抛 KeyError 后被当正常结果传下去）。

### 3.7 方向二 & 两文件分家（chat.py vs test_pipline.py）

- **chat.py = 对话入口 = Supervisor 模式**：单次 `run_agent(tools=[四专家], system_prompt=supervisor_prompt)`，主管自己判断"闲聊直接答 / 要跑数据才派专家"。管线**不该**焊进闲聊入口（否则"你好"也拖过四个专家 = scope 错）。

- **test_pipline.py = 管线测试 = Pipeline 模式**：无条件 `for expert in pipeline: expert.invoke(task)` 顺序跑四棒。

- **这两个文件的差异，就是站3 学到的东西的活教材，留着当对照。**

- chat.py 每轮三件事：①search_memory 检索 → ②拼task交run_agent → ③提炼fact存save_memory。

- 两文件的 RAG 记忆部分完全重复——**已知，暂不抽**。等第3周有第三第四个入口都要这套时，再抽成公共函数（规模逼出来，不是现在猜）。

### 3.8 LangGraph（站4，手写五棵树验证过）

**主线一句话**：LangGraph 把手写的"命令式循环"翻成"声明式的图"——你 `add_node`/`add_edge` 把结构画出来、`compile()` 冻成 app、`invoke()` 交给 runtime 跑循环。**控制反转是唯一真正的新肌肉**；state/node/边/带环ReAct/checkpointer 五件里四件都是站1-3 手搓过的东西的"认出"。

**图 = 节点 + 边**

- **node** = `state -> dict` 的函数，返回**增量**（"我改白板哪个字段"），由 runtime 合并进 state。可以是 LLM node，也可以是**纯函数 node**（痛②的解药：cleaner/aggregator 该从"套 LLM 的假专家"降级成纯函数 node）。

- **普通边** `add_edge("a","b")` = 无条件直连、硬序 = 站3 的 Pipeline。

- **条件边** `add_conditional_edges(源node, 路由函数, 查表字典)` 三件套 = 软判断 = Supervisor / ReAct 的 `if not tool_calls: break`。路由函数 `state -> str` 只读 state、吐**方向标签**（**不改 state**）；字典把标签翻成 node 名；**字典必须覆盖路由函数所有可能返回值，否则 KeyError**（见 bug#18）。

- **贯穿判据：node 想、edge 派**。（node 做判断、把结论写进 state；边只读结论、指方向。路由函数要薄，薄到几乎只读一个字段。）

**state 合并与 reducer（树1、树4）**

- **默认合并 = 覆盖**（新值盖旧值，不报错）。想追加得手动 `state["x"] + [...]` 读旧拼新——又笨又易忘，忘了=静默丢数据（bug#17）。

- **reducer = 字段级合并策略**，声明在字段上：`messages: Annotated[list, add_messages]`（`Annotated[类型, 合并策略]`）。挂上 `add_messages` 后 node 只 `return {"messages": [新消息]}` 就自动**追加**，且**按消息 id 智能合并、自动守 `AIMessage↔ToolMessage` 配对**（bug#5 的工业解）。

- **MessagesState** = `Annotated[list, add_messages]` 的官方快捷方式。三种用法：`StateGraph(MessagesState)` 直接用 / `class State(MessagesState)` 继承再加字段 / 手写那行。**先手写再揭快捷方式——认出黑盒里装的是已会的东西**（同"先手搓 run_agent 再上框架"的学法）。

**带环的 ReAct 图（树3）= 手搓 run_agent 的认出**

- `agent` node（LLM 想，`llm_with_tools.invoke`）→ 条件边 `should_continue`（读最后一条消息有无 `tool_calls` → `"tools"` 或 `"end"`）→ `tools` node（`tools_by_name` 查表执行 + `ToolMessage(tool_call_id=...)` 喂回）→ `add_edge("tools","agent")` **回边**。

- 逐行对应手搓版：agent node = `ai=llm.invoke`；条件边 = `if not tool_calls: break`；tools node = 查表分发+ToolMessage（bug#2/#3 原样搬）；回边 = for 循环的"下一圈"。循环归 runtime。

- **那根 `tools→agent` 回边是命根**：删掉它，工具结果没人"再想一轮"，永远变不成自然语言终答（亲手删过验证）。这是第一张**带环**的图（树1-2 都是无环 DAG）。

- **图能可视化（声明式红利，手搓 while 做不到）**：`app.get_graph().print_ascii()`（零依赖，可能需 `grandalf`）/ `draw_mermaid_png()`（默认走 mermaid.ink 联网渲染，注重本地就别用）。注意 **ASCII 画不好回边**（带环图的回指边会被吞掉）。

**checkpointer + thread_id（树5）= load/save_history 的工业版**

- `app = builder.compile(checkpointer=InMemorySaver())` 让图**跨 invoke** 记忆。**必须关键字传参**（bug#20）。

- `thread_id`（`config={"configurable":{"thread_id":"user-1"}}`）= **会话身份**，按线分档：同 id → 捞回上轮 state 接着走；换 id → 全新空会话（记忆归零）。补上了单文件 history.json 做不到的多会话隔离。

- `InMemorySaver`（学习/测试，进程关就没）→ `SqliteSaver`/`PostgresSaver`（生产，换一行 import，机制一样）。

- **两层记忆咬合**：reducer/messages 管**一次 invoke 内**的累积；checkpointer 管**跨 invoke** 的存读。合起来才是连续对话。（`len(messages)` 反映的是这条 thread 累积的全部 state，含 ReAct 中间的 tool_calls / Tool 消息。）

**三痛对应（站3 三痛 → 站4 解药，capstone 落地）**

- 痛①纯文本丢结构化 → state 具名字段（capstone 里放 `cleaned_path`/`group_by`）。

- 痛②确定活儿套 LLM 出假结果 → 纯函数 node。

- 痛③硬序 vs 软判断 → 普通边（硬）+ 条件边（软）同图。

---

## 4. 概念顿悟（追问出来的，比代码值钱）

- **invoke ≠ 调模型**：invoke 是通用"执行"动词，作用看点号前是谁。llm.invoke=调模型(返回AIMessage)；tool.invoke=执行函数/Agent(返回str)。
- **三种消息谁来造**：Human/ToolMessage 要自己 import 构造（替人/工具发言）；AIMessage 是模型返回的，接输出时不用导入。
- **observation 的开放性**：observation 不是确定的返回值，而是"行动后从环境获得的反馈"——可能成功/失败报错/环境变化。**正因它开放不可预测，才需要会推理的 LLM 而非 if-else。这是 Agent 必须用 LLM 的根本原因。**（站3 反用：职责确定→不需要工具/LLM；开放→才需要。）
- **规则驱动 vs 推理驱动**：工具(规则)报逐列事实；Agent(推理)跨列推断出工具没写规则的洞察。
- **模型对自己的认知来自训练数据+system prompt，不来自实际处境**：DeepSeek 自称"Claude"（身份污染），也不知道自己挂着 RAG。
- **python -m 与包机制**：`python 文件路径` 以文件所在目录找包；`python -m 模块路径`（点号）以当前目录（根）找包。import 平级包必须用 -m 且站根目录。`__init__.py` 标记文件夹为包。`-m` 后面是**写死的模块路径**，换文件名/加目录，运行命令要跟着改（站4 归档时又撞一次）。
- **Python 环境**：机器上多个 Python 本体（系统/miniconda/Homebrew），每个之上再建隔离环境（venv）。`which python` 查当前用哪个，看 `(venv)` 确认激活，一个项目只用一套。**venv 只干"隔离"、不装 Python 版本**——`python -m venv` 是克隆当前本体，变不出新版本；换 Python 版本要先换本体（brew/pyenv/官方包），再 `pythonX.Y -m venv`。
- **无状态 `run_agent` 逼出的架构后果**：`run_agent` 每次调用内部 `messages=[]` 全新起，只吃 `task` 一个字符串、返回一个字符串——**它从不读外层的 messages**。这一个设计决定，直接让 `chat.py` 那条 in-context 记忆链路整条从模型大脑上断线。→ 顿悟：**记忆住在哪、什么时候该换住处，是随架构变的**；对话状态的重新安家应交给 LangGraph state（MessagesState），而不是给手搓循环焊 history 参数。**（站4 已验证：确实交给了 MessagesState + checkpointer。）**
- **"把 Agent 当工具传给外层 run_agent" ≠ "顺序执行这个 Agent"**：前者是让 LLM 主管决定要不要调它（Supervisor，适合无硬序）；后者是控制流直接 `.invoke` 执行它（Pipeline，适合硬序）。站3 的崩溃就是想要 Pipeline、却写成了 Supervisor——**结构选错，不是代码写错。**
- **该不该做成单例，不看"听起来该共享"，看那个对象是不是"造起来贵"或"持有该共享的状态"**：贵/有状态（DB 连接池、加载进内存的 embedding 模型）→ 单例是刚需；轻/无状态（ChatOpenAI 这种 API 客户端）→ 单例只是"最简写法"。**共享的是"配置默认值"这一份事实，个性化用 `.bind(...)` 从单例派生覆盖。**
- **纯文本在专家间传递会丢"结构化信息"**：管线里上一棒输出以字符串塞进下一棒 task，"数据存哪个文件、按哪列分组"混在自然语言里靠 LLM 去捞，脆弱。真实管线需要传**结构化字段**（路径、schema、分组键）。→ 这正是 LangGraph state 要治的痛（`{"cleaned_path":..., "group_by":...}` 明确传递）。**capstone 落地点。**
- **确定性的活儿套 LLM 会产出"嘴上干活"的假结果**：cleaner/aggregator 的 `tools=[]` 且活儿确定，于是它们只让 LLM"描述"了清洗/聚合，并没真读写 CSV——中间文件根本不存在。→ 它们本该是**纯 pandas 函数**，不该套 LLM。capstone 里改成纯函数 node。
- **【站4 新】记忆版图对应（手搓 → LangGraph）**：`messages` 列表 + 手动 append → state 的 messages 字段 + `add_messages` reducer；`load/save_history`（history.json 跨会话）→ **checkpointer + thread_id**；摘要压缩层暂无对应。**账本没变（都是 messages），换的是"维护它的手法"（手动拼 → reducer）和"存处"（json → checkpointer）。** 注意区分：**messages 是账本、reducer 是记账规则，别划等号**；messages/reducer 管一次 invoke 内、checkpointer 管跨 invoke。
- **【站4 新】反事实探针（验机制别被 LLM 蒙对骗了）**：验一个记忆/上下文机制到底生没生效，必须用"**机制不生效就必然答错**"的探针，堵死模型靠"工具+关键词+常识"蒙对的后路。实例：验 checkpointer 时"那二月呢？"会被 LLM 从"工具+月份词"现场推出来（**假阳性**，误以为它记得）；换成"我叫什么名字？"（无工具可查、无关键词可推、答案只存在于上轮历史）才真正把 thread_id 逼现形——同 thread 答"小杜"、`len=6`，换 thread 答"不知道"、`len=2`。**别把 LLM 的联想力当成你的机制在生效。**
- **【站4 新】同图多次运行输出可变（LLM 非确定性）**：图结构确定（声明式），但图里流的内容由 LLM 决定、不保证每次一样。曾见工具跑完、agent 却返回**空的终答 AIMessage**（既无 tool_calls 也无正文），流程正确走完但没吐人话。生产要考虑"终答为空"的兜底。**别把 LLM 输出当确定性系统来读**（与"反事实探针"同源：LLM 的表现 ≠ 系统状态）。
- **【站4 新】commit 与开新会话的判据**：commit 看"**状态完不完整**"（完整可跑态哪怕在学习期就该提，尤其大改前留干净档可回退；一个 commit 说一件事），不是"够不够里程碑"。开新会话看"**上下文满没满 + 有没有干净的外部恢复点**"——LEARNING_LOG 就是自己的 checkpointer，开新会话 = 带同一个 thread_id 重新 invoke。半成品别 commit、完整态该 commit，两回事。

---

## 5. 踩过并理解的 Bug（都是静默坑，不报"你错了"）

1. **函数忘记 return**：算了但成功路径没 return → 返回 None。try/except 各分支都要 return。

2. **消息角色用错**：喂回工具结果用 ToolMessage（带 tool_call_id），不是 AIMessage。

3. **写死工具调度**：写死工具名，多工具时全调成同一个。用 tools_by_name 按 name 查表。"能跑≠写对了"。

4. **空文件不是合法 JSON**：os.path.exists 挡不住"存在但为空"。用 try/except (FileNotFoundError, JSONDecodeError) 兜底。

5. **切片切断 AIMessage↔ToolMessage 配对**：压缩历史按数量切片可能切散配对 → API 报 400。切点落 ToolMessage 上时往后挪（while+isinstance）。**改历史必须尊重消息内部结构。**（站4 再遇同一 400，见 #19。）

6. **Chroma 默认用 L2 不是余弦**：不指定排序和余弦不一致且不报错。`metadata={"hnsw:space":"cosine"}`。

7. **Chroma 返回"距离"不是"相似度"**：距离=1-相似度，越小越相关，方向相反。`similarity = 1 - dist` 再比阈值。

8. **低分排序是噪声**：看绝对分数不只看排名；设阈值（如0.3）宁缺毋滥，避免噪声污染 context。

9. **脏输入污染记忆**：终端方向键/粘贴残渣带入乱码 input 还被存进 RAG。输入做校验（空的continue、太短不存）。

10. **f-string 引号（3.9）**：外双引号时内层字典键用单引号 `['name']`；或先算到变量再放进 f-string。**（3.9 时代坑；已迁 3.11，此约束解除，保留作历史。）**

11. **忘激活 venv / 用错运行方式**：ModuleNotFoundError 先查 `(venv)` 在不在、是不是该用 `python -m`。

12. **RAG 只增不改，无法处理记忆冲突**：改名"小红"改不掉——旧记忆"小杜"没删、且被反复强化相似度更高，模型只能嘴上答应实际无能为力（没有删记忆的工具）。**这是 RAG 记忆系统的核心难题。** 解法方向：加时间戳优先最新 / 存前检测冲突并覆盖 / 给 Agent 一个"删除/更新记忆"的工具。

13. **僵尸代码（基础版）**：走 A 路线下，会话历史那套整个失效但还在空转，误导性强（`last_answer = messages[-1].content` 取到的是用户输入不是回答）。**重构要果断删掉不再起作用的代码，别占位留着。**

14. **Git 两条铁律**：①.gitignore 名字必须和实际文件夹精确匹配（`.venv`≠`venv`）；②已被追踪的文件 .gitignore 拦不住，要 `git rm -r --cached <path>` 手动移除。`__pycache__/` + `*.pyc` 也要 ignore。

15. **重构后的僵尸代码有"上下游"之分**：拔掉"消费者"不等于拔干净，上游的"生产者"会变成**只写不读**的半路尸体。判据始终是：**这个变量/这行，现在还有谁读它？** 没有下游读者就是尸体。

16. **Pipeline 写成了"四个迷你 Supervisor"（站3 大翻车）**：想让四专家顺序跑，却给每一棒都套 `run_agent(tools=[单个专家])` 外层主管，还注释掉 system_prompt。后果：冗余主管 / 乱调工具 KeyError / 反复 data_checkup 耗尽 max_steps / 每棒各写一份报告。**根因是结构选错**：pipeline 每棒无需选择，应直接 `expert.invoke(task)`。

17. **【站4·树1】默认覆盖忘拼旧值 → 静默丢数据**：LangGraph state 默认合并是**覆盖不是追加**。node 只 `return {"x": 新值}`、字段又没挂 reducer → 旧值被冲掉，不报错。想追加：手动 `state["x"]+[...]`，或给字段挂 reducer（`add_messages`）。

18. **【站4·树2】条件边查表漏项 → KeyError**：`add_conditional_edges` 的字典必须覆盖路由函数**所有**可能返回值。漏一个平时不报，直到某次输入恰好走到那条缺失分支才当场 `KeyError`（静默坑变现场坑）。判据：写完条件边回头数"路由函数还能返回啥？字典都接住没？"

19. **【站4·树4】孤儿 ToolMessage → 400（bug#5 第三次现身）**：`Messages with role 'tool' must be a response to a preceding message with 'tool_calls'`。ToolMessage 必须紧跟带对应 `tool_call_id` 的 AIMessage。**切散（#5）、覆盖冲掉（摘掉 reducer + node 只 return 新值）都会破坏配对 → 同一个 400。** 病根统一：拿掉了 ToolMessage 的前置 AIMessage。`add_messages` 按 id 合并、自动守配对是工业解——**正反双向验过**（挂上→跑通；摘掉→立刻炸）。

20. **【站4·树5】`compile(checkpointer)` 位置传参侥幸对**：checkpointer 要**关键字**传 `compile(checkpointer=checkpointer)`。位置传参赌"第一个参数恰好是它"，版本一变就崩。同 #3 的"能跑≠写对了"。

---

## 6. 关键技术配置备忘

- **Python / 环境（已迁移）**：从 3.9（miniconda）迁到 **3.11**——`brew install python@3.11` 装本体，`python3.11 -m venv venv` + `source venv/bin/activate`，**纯 venv、弃 conda**。原因：LangChain v1.1 / LangGraph 1.1 已砍 Python 3.9（需 3.10+）。miniconda 未卸载，退化为"躺着的一个本体"，`conda config --set auto_activate_base false` 关掉自动激活 base。
- **依赖清单（venv 曾误删的教训）**：升级时误删过 venv（当时无 requirements.txt）。代码没丢（在 git / GitHub，venv 本就被 ignore），只需重建环境。教训——**依赖要持久化成清单**（= 环境版的 history.json；呼应本 log 开篇原则）。现策略：**全量 `pip freeze > requirements.txt`**（复现性最强，选择3）；想要"七行可读版"再上 `pip-tools`/`uv`（规模逼出来再上，别手抠花名册）。**`import` 就是依赖的规格**：`grep -rh "^import \|^from " agent/ scripts/` 可捞出。直接依赖 7 个：`langchain-core`、`langchain-openai`、`langgraph`、`chromadb`、`sentence-transformers`、`pandas`、`python-dotenv`；`torch`(经 sentence-transformers)、`opentelemetry-*`/`onnxruntime`(经 chromadb) 等是传递依赖，100+ 个是这俩重家伙的必然，`pip install pipdeptree && pipdeptree` 可看依赖树。
- **langchain 1.x 兼容**：站1-3 用的 `langchain_core.messages` / `langchain_core.tools.@tool` / `langchain_openai.ChatOpenAI` 在 1.x 稳；1.x 破坏性改动集中在**高层造 Agent 的 API**（`create_react_agent`→`langchain.agents.create_agent`、middleware），**手搓派不受影响**。迁 3.11 后跑 `test_engine`/`test_pipline`/`chat` 实测通过。
- **LangGraph 关键 import / 配置**：`from langgraph.graph import StateGraph, START, END, MessagesState`；`from langgraph.graph.message import add_messages`；`from langgraph.checkpoint.memory import InMemorySaver`；`compile(checkpointer=...)`；`invoke(input, config={"configurable":{"thread_id":...}})`。可视化 `app.get_graph().print_ascii()`（零依赖，可能需 `grandalf`）。
- **LLM 共享单例**：`agent/llm.py` 造一次 `llm = ChatOpenAI(...)`，全项目 import。要局部不同温度：`llm.bind_tools(...)` / `llm.bind(temperature=...)` 从单例派生，不动单例。
- **embedding 模型**：`paraphrase-multilingual-MiniLM-L12-v2`（中文，384维）。**必须单例**（加载权重几百 MB）。缓存在 `~/.cache/huggingface`（在 venv 外，删 venv 不动它）。
- **离线加速**：memory.py **顶部、在 `from sentence_transformers import` 之前** 设 `os.environ["HF_HUB_OFFLINE"]="1"` 和 `["TRANSFORMERS_OFFLINE"]="1"`（顺序错=无效）。
- **prompt 集中管理**：`agent/prompts/` 一角色一 `.md`，`load_prompt(name)` 用 `Path(__file__).parent` 定位。
- **向量库**：`chromadb.PersistentClient(path="./memory_db")` + cosine。**始终在项目根目录启动**（相对路径）。
- **API key**：放 .env，`load_dotenv()` 读，.env 进 .gitignore（已确认未被追踪）。
- **Git**：`git status`（先看 .env 不在清单）→ `git add .` → `git commit -m "说明"`。**一个 commit 说一件事；完整可跑态就该提，大改前留干净档。**

---

## 7. 下一步（明确的待办）

1. **站4 capstone · 四专家管线迁 LangGraph（下一站，最高杠杆，直接进作品集）**：把站3 的四专家管线用 LangGraph 重搭，一次性除三痛——

   - cleaner/aggregator → **纯函数 node**（非 LLM，真读写 CSV）｜痛②

   - state 放 `cleaned_path`/`group_by`/schema 等**结构化字段**替代纯文本传递｜痛①

   - 硬边定序（cleaner→aggregator→analyst→writer）+ 必要处条件边｜痛③

   - analyst 保持 LLM node（唯一"开放/动脑"的）。

   - 这是**电商/物流数据 agent** 的骨架（用 SF Express 背景）。

   - **判断题密集区**（放哪些 state 字段、四专家怎么连边、谁降级纯函数）——按教学约定**自己定、Claude 挑缝**。

   - 建议**开新会话做**：贴本 log 恢复记忆，说"站4 完成，开 capstone"。

2. **站4 已完成的额外目标 ✅**：会话历史已用 MessagesState + checkpointer 重新安家（走 A 时拔掉的 in-context 记忆补回）。

3. **（可选进阶）解决 RAG 记忆冲突**：给 Agent 加"更新/删除记忆"工具，直击 bug#12。

4. **站5 · MCP**：让 Agent 连真实外部服务（数据运维/血缘/调度：读任务状态、查上下游血缘、找流水线堵塞、检测表结构变化）。

5. 之后第3周做产品、第4周部署。

**简历待填**（复合岗定位）：姓名、电话、邮箱、GitHub/作品集链接，两个性能指标（context 压缩比、单章通过率）。LangGraph 已列技能——现已完成五棵树，可如实写"手写实现 state/node/条件边/reducer/checkpointer"，capstone 完成后补"用 LangGraph 重构多 Agent 数据管线"。

---

## 8. 教学约定（给接手的 Claude）

- 一次一个概念，手敲为主，每个新机制先脱离主系统单独跑通再接入（先看森林蓝图，再一棵树一棵树单独跑通、再接回主系统）。
- 鼓励"改一个点、预测结果、再验证"的实验——**他会先写预测再跑、拿结果对账**，尊重这个节奏。
- **不替他写核心设计部分**：划边界、写 prompt 内容、定 state 字段、连专家边这类"判断题"要他自己做，Claude 只挑毛病（重叠/缝）。能跑的产物不值钱，判断才值钱。给标准范本前先确认他已自己做过一遍。（例外：boilerplate/新语法骨架可以给，让他省在不重要的地方、把脑力压在机制上——他会明说"给我骨架"。）
- 把学习者的 bug 和质疑当作讲点，必要时据此调整教学路径（他的好问题已多次重塑教学路线）。
- **他会追问"改这个结构会不会有悖当初的设计意图"**——遇到这类质疑，先陪他还原原设计的原因，再判断该不该改，别直接推平。
- 学习者用 **DeepSeek**（不是 Claude API），写 Agent 走 LangChain 的 ChatOpenAI + base_url 指向 DeepSeek。
- 不要重复造已有零件；优先复用 run_agent 引擎、llm 单例、load_prompt。
- 已引入 Git，做大改动前提醒/习惯性 commit 存档。
- 语言：中文交流。

---

## 附：关于 skill / 新特性（已澄清，非主线）

- 学习者问过 Anthropic **Agent Skills**。已厘清：Skill 是 Anthropic/Claude 生态的机制（跨 Claude.ai / Claude Code / API / Agent SDK，靠 Claude runtime 自动发现加载），**用 DeepSeek 手搓的 Agent 没法直接用**。

- 对他有价值的三个入口：①**概念迁移**（能力模块化 + progressive disclosure，可手搓进自研框架——他的 LEARNING_LOG 和 run_agent+prompt 已是雏形，这条贴主线）；②在 Claude Code 里给数仓项目写个真 SKILL.md（最低成本、立刻有用）；③搞清它在版图里的坐标（skill=知识/工作流层，MCP=工具访问层，互补）。

- 结论：**skill 不进主线**（绑 Claude，生产上他用 DeepSeek）。plugins = Claude Code 的 skill 分发/安装机制（了解即可）；subagents = "Agent 即工具"的产品化版本（可对照站1/站2）。