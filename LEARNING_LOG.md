# LEARNING_LOG — 手搓 AI Agent 学习档案

> 这份文档是「我们这场学习对话的外部长期记忆」。

> 它存在硬盘上，不受任何对话上下文窗口的限制。

> 开新对话时，把这份贴给 Claude（或放进 Project 知识库），即可瞬间「恢复记忆」。

> —— 这本身就是课程里学到的：重要的东西持久化到外部，不要只活在易失的上下文里。

>

> **最近更新：完成第2周·站3——子 Agent 专精分工（四专家管线）+ Pipeline vs Supervisor 两种编排定型 + LLM 共享单例。**

---

## 0. 学习者画像（给接手的 Claude 看）

- 背景：数据分析 / 大数据工程师（Hive、Spark、PySpark、Python、SQL、Presto），正在向 AI Agent 应用工程师转型，同时在找工作。
- 设备：MacBook（arm64）。
- LLM 提供方：**DeepSeek API**（`deepseek-chat`，`https://api.deepseek.com`），通过 LangChain 的 `ChatOpenAI` 接入（DeepSeek 兼容 OpenAI 格式），`temperature=0`。
- Python：**3.9**（基于 miniconda），项目内用 `venv` 隔离。⚠️ 3.9 不支持「f-string 内层用与外层相同的引号」。
- 学习风格（很重要）：
  - 偏好直接、无废话、假设有工程基础。
  - **靠"感觉不对劲"主动发现 bug 和概念漏洞**，会质疑、会追问到根因，不满足于"能跑"。
  - 喜欢先看"蓝图/全景"再钻细节。
  - 手敲代码（常配合 IDE 自动补全），重点在理解而非默写——验证标准是"能不能讲清逻辑、能不能改一个点并预测结果"，不是"能不能背着敲"。
  - 会主动重构、拆模块、主动质疑设计（不用别人提醒）。**会追问"改这个结构会不会有悖当初的设计原因"——重构前先还原原意图，不盲改。**

---

## 1. 项目结构（当前）

项目根：`~/projects/claude_tutorialbyclaude/first-agent/`（已是 Git 仓库，分支 main）

```

first-agent/

├── agent/ # 核心代码包

│ ├── __init__.py

│ ├── core.py # run_agent() —— 可复用的 ReAct 引擎

│ ├── llm.py # 【新】全项目共享的 LLM 单例（配置只在这一处）

│ ├── tools.py # data_checkup 工具

│ ├── memory.py # RAG 长期记忆（Chroma + sentence-transformers）

│ ├── history.py # 持久化(load/save) + 摘要压缩(compress_history)

│ │ # ⚠️ 走 A 路线后 chat.py 已不再用它，属遗留

│ ├── prompts/ # 【新】所有角色 prompt 集中（一角色一 .md）

│ │ ├── __init__.py # load_prompt(name) 读取器（用 Path(__file__) 定位，不依赖工作目录）

│ │ ├── cleaner.md

│ │ ├── aggregator.md

│ │ ├── data_analyst.md

│ │ ├── report_writer.md

│ │ └── supervisor.md

│ └── agents/ # 各个子 Agent（包成工具）

│ ├── __init__.py

│ ├── data_cleaner.py # 【新】清洗专家（tools=[]，只标准化、不碰异常值）

│ ├── aggregator.py # 【新】聚合专家（tools=[]，机械汇总、前置列校验）

│ ├── data_analyst.py # 分析专家（配 data_checkup，唯一"开放/动脑"的）

│ └── report_writer.py # 撰写专家（tools=[]，分析风：可综合串联、不无中生有）

├── scripts/ # 入口脚本（从项目根用 python -m scripts.xxx 运行）

│ ├── chat.py # 对话入口：Supervisor 模式（主管派单，闲聊直答）

│ ├── test_pipline.py # 【新】管线测试：Pipeline 模式（控制流串四棒顺序）

│ ├── test_engine.py # 测 run_agent 引擎

│ ├── test_nested.py # 测 Agent 套娃（站1）

│ └── test_supervisor.py # 测 Supervisor 编排（站2）

├── data/

│ └── sample.csv # 测试数据（20行9列销售数据）

├── learning_archive/ # 学习文物：step1~step10（不删，留作纪念）

├── memory_db/ # Chroma 持久化向量库（运行时生成，git忽略）

├── history.json # 对话历史持久化（运行时生成，git忽略；走A后已不再写入）

├── .env # DEEPSEEK_API_KEY（git忽略，已确认安全）

├── .gitignore # 忽略 .env / venv/ / memory_db/ / history.json / __pycache__

├── README.md

└── venv/ # 虚拟环境（git忽略）

运行方式：在项目根目录、激活 venv 后，python -m scripts.chat（对话）/ python -m scripts.test_pipline（测管线）

```

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
| 第2周 · 站4 | 换上 LangGraph 框架 | ⏭ **下一步** |
| 第2周 · 站5 | MCP 接真实工具 | ⏭ |
| 第3周 | 做产品（电商数据/求职/视频自动化三选一） | ⏭ |
| 第4周 | 部署上线 + 工作流固化 | ⏭ |

当前进度：约整月 45%，最硬的地基已打完，多 Agent 两种编排模式已定型。

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

- **⚠️ 现状（走 A 路线后）**：上表三层是在**单 Agent** 时代手写并验证过的；转多 Agent（Supervisor + 无状态 `run_agent`）后，**主程序已主动拔掉 in-context 三层**，跨轮连续性暂时只靠 RAG（把检索结果拼进 task 传入）。这是刻意的解耦，不是缺失——对话状态计划在站4用 LangGraph state 重新安置。代价：RAG-only 期间模型不记得"上一句刚问过啥"，等亲自感到痛再决定要不要加"最近 N 轮拼字符串"的轻量中间层。

### 3.4 run_agent 引擎（多 Agent 基础零件）

- `run_agent(task, llm, tools, system_prompt, max_steps, verbose)` —— 把内层 ReAct 循环抽成函数。

- **关键：从 print 改成 return**——结果交还调用者（可能是另一个 Agent）。

- 同一引擎，换不同 tools / system_prompt，驱动不同 Agent。**主 Agent 和子 Agent 都用它。**

- **run_agent 本质是"选择器"**：它的价值在于让 LLM 从**多个**工具里推理该调谁。只有一个候选、且确定要调它时，套 run_agent 是冗余（雇个经理管一个只能做一件事的员工）——直接 `.invoke` 执行即可。见 3.5 的 Pipeline vs Supervisor。

### 3.5 多 Agent 协作 —— 两种编排模式（站3 定型）

- **Agent 即工具（站1）**：把整个 Agent 用 `@tool` 包成函数，内部调 run_agent。外层看它就是普通工具 → Thought 循环**套娃**。

- **Supervisor 模式（站2 / chat.py）**：主管 Agent 手握**多个**专家工具，用 LLM **判断**派谁、何时派、如何整合。`run_agent(tools=[全部专家], system_prompt=主管prompt)` 一次调用。**适合无硬性顺序的协作。**

- **Pipeline 模式（站3 / test_pipline.py）**：专家顺序**写死**，用控制流串起来，前一棒输出拼进后一棒 task。`for expert in pipeline: expert.invoke(task)`。**适合有硬依赖顺序的场景（如数仓分层 ODS→DWD→DWS→ADS）。**

- **两者的本质区别 = 硬依赖交给谁**：Supervisor 把"该调谁"交给 LLM 判断（软）；Pipeline 把顺序交给 Python 控制流强制（硬）。**类比数据工程：调度依赖（DAG）从不靠在 SQL 里写"请按顺序"，靠调度系统的依赖边强制。** 硬依赖靠结构保证，不靠嘱咐。

- **软/硬错配是站3 最大的坑**：让 LLM（软指令）去遵守"清洗必须在汇总前"这种硬依赖 → 会静默跳步、甚至幻觉"我已经做过了"，产出看着完整实则跳步的假货。原则：**硬依赖（顺序、必经）交给控制流；软判断（要不要启动、异常怎么办）交给 LLM。**

- **专精 > 全能**：每专家只配该有的工具。判据见下条。

- **要不要给专家配工具，看职责开放度**（复用 observation 开放性那条顿悟）：职责确定（清洗、聚合=写死规则）→ 不需要工具、甚至不需要 LLM；职责开放（分析=不知道会发现什么，observation 不可预测）→ 才需要工具 + 多轮 ReAct。本项目里只有 data_analyst 配了 data_checkup。

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

---

## 4. 概念顿悟（追问出来的，比代码值钱）

- **invoke ≠ 调模型**：invoke 是通用"执行"动词，作用看点号前是谁。llm.invoke=调模型(返回AIMessage)；tool.invoke=执行函数/Agent(返回str)。
- **三种消息谁来造**：Human/ToolMessage 要自己 import 构造（替人/工具发言）；AIMessage 是模型返回的，接输出时不用导入。
- **observation 的开放性**：observation 不是确定的返回值，而是"行动后从环境获得的反馈"——可能成功/失败报错/环境变化。**正因它开放不可预测，才需要会推理的 LLM 而非 if-else。这是 Agent 必须用 LLM 的根本原因。**（站3 反用：职责确定→不需要工具/LLM；开放→才需要。）
- **规则驱动 vs 推理驱动**：工具(规则)报逐列事实；Agent(推理)跨列推断出工具没写规则的洞察。
- **模型对自己的认知来自训练数据+system prompt，不来自实际处境**：DeepSeek 自称"Claude"（身份污染），也不知道自己挂着 RAG。
- **python -m 与包机制**：`python 文件路径` 以文件所在目录找包；`python -m 模块路径`（点号）以当前目录（根）找包。import 平级包必须用 -m 且站根目录。`__init__.py` 标记文件夹为包。
- **Python 环境**：机器上多个 Python 本体（系统/miniconda），每个之上再建隔离环境（venv）。`which python` 查当前用哪个，看 `(venv)` 确认激活，一个项目只用一套。
- **无状态 `run_agent` 逼出的架构后果**：`run_agent` 每次调用内部 `messages=[]` 全新起，只吃 `task` 一个字符串、返回一个字符串——**它从不读外层的 messages**。这一个设计决定，直接让 `chat.py` 那条 in-context 记忆链路整条从模型大脑上断线。→ 顿悟：**记忆住在哪、什么时候该换住处，是随架构变的**；无状态-每次调用是多 Agent 的业界标准，对话状态的重新安家应交给站4 的 LangGraph state（内置 MessagesState），而不是现在给手搓循环焊 history 参数（那会在换框架时全拆重来）。
- **"把 Agent 当工具传给外层 run_agent" ≠ "顺序执行这个 Agent"**：前者是让 LLM 主管决定要不要调它（Supervisor，适合无硬序）；后者是控制流直接 `.invoke` 执行它（Pipeline，适合硬序）。站3 的崩溃就是想要 Pipeline、却写成了 Supervisor——**结构选错，不是代码写错。** run_agent 是选择器，无选择就别套它。
- **该不该做成单例，不看"听起来该共享"，看那个对象是不是"造起来贵"或"持有该共享的状态"**：贵/有状态（DB 连接池、加载进内存的 embedding 模型 SentenceTransformer）→ 单例是刚需；轻/无状态（ChatOpenAI 这种 API 客户端，不加载权重、无状态）→ 单例只是"最简写法"，不是性能刚需。**共享的是"配置默认值"这一份事实，个性化用 `.bind(temperature=...)` 从单例派生覆盖，而不是"各造一份"。**
- **纯文本在专家间传递会丢"结构化信息"**：管线里上一棒输出以字符串塞进下一棒 task，"数据存在哪个文件、该按哪列分组"这类信息混在自然语言里，靠 LLM 去捞，脆弱。真实管线需要传**结构化字段**（路径、schema、分组键）。→ 这正是 LangGraph state 要治的痛（state 里放 `{"cleaned_path":..., "group_by":...}` 明确传递）。**站4 的"认出"预埋点。**
- **确定性的活儿套 LLM 会产出"嘴上干活"的假结果**：cleaner/aggregator 的 `tools=[]` 且活儿是确定的，于是它们只是让 LLM"描述"了清洗/聚合，并没有真读写 CSV——中间文件根本不存在（"结果不知道在哪"的真相）。→ 它们本该是**纯 pandas 函数**，不该套 LLM。站4 LangGraph 里会把它们从"LLM 专家"改成"纯函数 node"。

---

## 5. 踩过并理解的 Bug（都是静默坑，不报"你错了"）

1. **函数忘记 return**：算了但成功路径没 return → 返回 None。try/except 各分支都要 return。

2. **消息角色用错**：喂回工具结果用 ToolMessage（带 tool_call_id），不是 AIMessage。

3. **写死工具调度**：写死工具名，多工具时全调成同一个。用 tools_by_name 按 name 查表。"能跑≠写对了"。

4. **空文件不是合法 JSON**：os.path.exists 挡不住"存在但为空"。用 try/except (FileNotFoundError, JSONDecodeError) 兜底。

5. **切片切断 AIMessage↔ToolMessage 配对**：压缩历史按数量切片可能切散配对 → API 报 400。切点落 ToolMessage 上时往后挪（while+isinstance）。**改历史必须尊重消息内部结构。**

6. **Chroma 默认用 L2 不是余弦**：不指定排序和余弦不一致且不报错。`metadata={"hnsw:space":"cosine"}`。

7. **Chroma 返回"距离"不是"相似度"**：距离=1-相似度，越小越相关，方向相反。`similarity = 1 - dist` 再比阈值。

8. **低分排序是噪声**：看绝对分数不只看排名；设阈值（如0.3）宁缺毋滥，避免噪声污染 context。

9. **脏输入污染记忆**：终端方向键/粘贴残渣带入乱码 input 还被存进 RAG。输入做校验（空的continue、太短不存）。

10. **f-string 引号（3.9）**：外双引号时内层字典键用单引号 `['name']`；或先算到变量再放进 f-string。

11. **忘激活 venv / 用错运行方式**：ModuleNotFoundError 先查 `(venv)` 在不在、是不是该用 `python -m`。

12. **RAG 只增不改，无法处理记忆冲突**：改名"小红"改不掉——旧记忆"小杜"没删、且被反复强化相似度更高，模型只能嘴上答应实际无能为力（没有删记忆的工具）。**这是 RAG 记忆系统的核心难题。** 解法方向：加时间戳优先最新 / 存前检测冲突并覆盖 / 给 Agent 一个"删除/更新记忆"的工具。

13. **僵尸代码（基础版）**：走 A 路线下，会话历史那套（messages累积、compress_history、save_history、load_history）整个失效但还在空转，误导性强（`last_answer = messages[-1].content` 取到的是用户输入不是回答）。**重构要果断删掉不再起作用的代码，别占位留着。**

14. **Git 两条铁律**：①.gitignore 名字必须和实际文件夹精确匹配（`.venv`≠`venv`，写错导致整个 venv 被追踪）；②已被追踪的文件 .gitignore 拦不住，要 `git rm -r --cached <path>` 手动移除（--cached 只松手不删硬盘文件）。`__pycache__/` + `*.pyc` 也要 ignore（派生物不进版本控制，和源码是两码事）。

15. **重构后的僵尸代码有"上下游"之分**：拔掉"消费者"（compress/save/load）不等于拔干净，上游的"生产者"（`messages` 初始化、循环里的 append）会变成**只写不读**的半路尸体。同类：`tools_by_name`/`llm_with_tools`、`last_answer`。→ 判据始终是：**这个变量/这行，现在还有谁读它？** 没有下游读者就是尸体。（站3 又撞两次：test_pipline 里只导不用的 `load_prompt`；旧 chat.py 里定义了却没引用的 `supervisor_prompt` —— 身份混乱的信号：想当 chat 却写成了 pipeline。）

16. **Pipeline 写成了"四个迷你 Supervisor"（站3 大翻车）**：想让四专家顺序跑，却给每一棒都套了个 `run_agent(tools=[单个专家])` 外层主管，还注释掉了 system_prompt。后果：①冗余的外层主管（只有一个工具、没得选）；②没角色指令 → 乱调工具，调到不在工具箱的名字 → `KeyError`；③反复 data_checkup 耗尽 max_steps；④每棒各写一份完整报告。**根因是结构选错**：pipeline 每棒无需选择，应直接 `expert.invoke(task)`（专家肚子里已有 run_agent），不该在外面再套选择器。

---

## 6. 关键技术配置备忘

- **LLM 共享单例**：`agent/llm.py` 造一次 `llm = ChatOpenAI(...)`，全项目 import 它。配置只在这一处（改 model/temperature 只动一个文件）。要局部不同温度：`llm.bind(temperature=0.7)` 从单例派生副本，不动单例、不重复配置。单例名字不加下划线（它就是要给别人 import 的）。
- **embedding 模型**：`paraphrase-multilingual-MiniLM-L12-v2`（支持中文，384维）。**必须是单例**（加载权重到内存几百 MB，每次 new 会拖垮）——确认 memory.py 里只 new 了一次。
- **离线加速**：memory.py **顶部、在 `from sentence_transformers import` 之前**设 `os.environ["HF_HUB_OFFLINE"]="1"` 和 `["TRANSFORMERS_OFFLINE"]="1"`，否则每次启动联网检查 huggingface 卡住重试。（注意顺序，放 import 后无效。）
- **prompt 集中管理**：`agent/prompts/` 一角色一 `.md`，`load_prompt(name)` 用 `Path(__file__).parent` 定位（不依赖工作目录，比相对路径稳）。存 `.md` 不存 `.py`：无引号转义负担，长 prompt 带规则时 markdown 还利于自己读。
- **向量库**：`chromadb.PersistentClient(path="./memory_db")` + cosine。
- **运行时路径**：history.json / memory_db 相对路径，**始终在项目根目录启动**。
- **API key**：放 .env，`load_dotenv()` 读，.env 进 .gitignore（已确认未被追踪）。
- **Git**：常用三动作 —— `git add .`（选）→ `git commit -m "说明"`（存档）→ 需要时回退。commit 前先 `git status` 确认 .env 不在清单里。

---

## 7. 下一步（明确的待办）

1. **站4 · LangGraph（下一站）**：把手搓 run_agent 换成工业级框架，理解 state/node/edge——因已手写内核，是"认出"而非"从零学"。带着站3 撞出的三个痛点进场，逐一对应：

   - 痛点①**纯文本传递丢结构化信息** → LangGraph `state` 明确传递结构化字段。

   - 痛点②**cleaner/aggregator 套 LLM 是浪费、产出假结果** → 在 LangGraph 里把它们改成**纯函数 node**（非 LLM node）。

   - 痛点③**硬顺序 vs 软判断** → `edge`（普通边=硬顺序）+ 条件边（conditional edge=软分支）统一成一张图。

2. **站4 额外目标**：用 state（MessagesState）给对话历史重新安家，补上走 A 时拔掉的 in-context 会话记忆——已手写过也亲手拔过，到时是"认出它该住哪"而非从零设计。

3. **（可选进阶）解决 RAG 记忆冲突**：给 Agent 加"更新/删除记忆"工具，让它能真改而非嘴上答应。直击 bug #12。

4. **站5 · MCP**：让 Agent 连真实外部服务。数据运维/排障团队（读任务状态、查上下游血缘、找流水线堵塞、检测表结构变化）属于这里——因为它要连真实的元数据/血缘/调度系统。

5. 之后第3周做产品、第4周部署。

---

## 8. 教学约定（给接手的 Claude）

- 一次一个概念，手敲为主，每个新机制先脱离主系统单独跑通再接入（新专家先在 test_pipline 里跑，别直接改 chat.py）。
- 鼓励"改一个点、预测结果、再验证"的实验。
- **不替他写核心设计部分**：划边界、写 prompt 内容这类"判断题"要他自己做，Claude 只挑毛病（重叠/缝）。能跑的产物不值钱，判断才值钱。给标准范本前先确认他已自己做过一遍。
- 把学习者的 bug 和质疑当作讲点，必要时据此调整教学路径（他的好问题已多次重塑教学路线）。
- **他会追问"改这个结构会不会有悖当初的设计意图"**——遇到这类质疑，先陪他还原原设计的原因，再判断该不该改，别直接推平。
- 学习者用 **DeepSeek**（不是 Claude API），写 Agent 走 LangChain 的 ChatOpenAI + base_url 指向 DeepSeek。
- 不要重复造已有零件；优先复用 run_agent 引擎、llm 单例、load_prompt。
- 已引入 Git，做大改动前提醒/习惯性 commit 存档。
- 语言：中文交流。

---

## 附：关于 skill / 新特性（已澄清，非主线）

- 学习者问过 Anthropic **Agent Skills**。已厘清：Skill 是 Anthropic/Claude 生态的机制（跨 Claude.ai / Claude Code / API / Agent SDK，靠 Claude runtime 自动发现加载），**用 DeepSeek 手搓的 Agent 没法直接用**。

- 对他有价值的三个入口：①**概念迁移**（能力模块化 + progressive disclosure 渐进披露，可手搓进自研框架——他的 LEARNING_LOG 和 run_agent+prompt 已是雏形，这条贴主线）；②在 Claude Code 里给数仓项目写个真 SKILL.md（最低成本、立刻有用）；③搞清它在版图里的坐标（skill=知识/工作流层，MCP=工具访问层，互补）。

- 结论：**skill 不进主线**（绑 Claude，生产上他用 DeepSeek），入口①天然是站3/站4 的一部分，入口②可当轻量支线插空做。

- plugins = Claude Code 的 skill 分发/安装机制（了解即可）；subagents = "Agent 即工具"的产品化版本（可对照站1/站2）。