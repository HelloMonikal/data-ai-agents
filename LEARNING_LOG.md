# LEARNING_LOG — 手搓 AI Agent 学习档案

> 这份文档是「我们这场学习对话的外部长期记忆」。
> 它存在硬盘上，不受任何对话上下文窗口的限制。
> 开新对话时，把这份贴给 Claude（或放进 Project 知识库），即可瞬间「恢复记忆」。
> —— 这本身就是课程里学到的：重要的东西持久化到外部，不要只活在易失的上下文里。
>
> **最近更新：完成第2周「方向二」——多 Agent 团队接入对话循环 + 引入 Git 管理。**

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
  - 会主动重构、拆模块、主动质疑设计（不用别人提醒）。

---

## 1. 项目结构（当前）

项目根：`~/projects/claude_tutorialbyclaude/first-agent/`（已是 Git 仓库，分支 main）

```
first-agent/
├── agent/                      # 核心代码包
│   ├── __init__.py
│   ├── core.py                 # run_agent() —— 可复用的 ReAct 引擎
│   ├── tools.py                # data_checkup 工具
│   ├── memory.py               # RAG 长期记忆（Chroma + sentence-transformers）
│   ├── history.py              # 持久化(load/save) + 摘要压缩(compress_history)
│   │                           #   ⚠️ 方向二(方式A)下 chat.py 已不再用它，属遗留
│   └── agents/                 # 各个子 Agent（包成工具）
│       ├── __init__.py
│       ├── data_analyst.py     # 数据分析师子 Agent（配 data_checkup）
│       └── report_writer.py    # 报告撰写员子 Agent（tools=[]，纯写）
├── scripts/                    # 入口脚本（从项目根用 python -m scripts.xxx 运行）
│   ├── chat.py                 # 主对话程序：多Agent团队 + RAG记忆（当前主程序）
│   ├── test_engine.py          # 测 run_agent 引擎
│   ├── test_nested.py          # 测 Agent 套娃（站1）
│   └── test_supervisor.py      # 测 Supervisor 编排（站2）
├── data/
│   └── sample.csv              # 测试数据（20行9列销售数据）
├── learning_archive/           # 学习文物：step1~step10（不删，留作纪念）
├── memory_db/                  # Chroma 持久化向量库（运行时生成，git忽略）
├── history.json                # 对话历史持久化（运行时生成，git忽略）
├── .env                        # DEEPSEEK_API_KEY（git忽略，已确认安全）
├── .gitignore                  # 忽略 .env / venv/ / memory_db/ / history.json / __pycache__
├── README.md
└── venv/                       # 虚拟环境（git忽略）

运行方式：在项目根目录、激活 venv 后，python -m scripts.chat
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
| **待办：清理 chat.py 僵尸代码** | 会话历史相关逻辑已失效需删除 | ⏭ **下一步** |
| 第2周 · 站3 | 子 Agent 专精分工 | ⏭ |
| 第2周 · 站4 | 换上 LangGraph 框架 | ⏭ |
| 第2周 · 站5 | MCP 接真实工具 | ⏭ |
| 第3周 | 做产品（电商数据/求职/视频自动化三选一） | ⏭ |
| 第4周 | 部署上线 + 工作流固化 | ⏭ |

当前进度：约整月 40%，最硬的地基已打完。

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
- 多工具调度：`tools_by_name = {t.name: t for t in tools}` 按名字查表分发，不能写死。
- `llm.bind_tools(tools)`（会翻译成 API 格式）≠ `llm.bind(tools=...)`（不翻译，会报序列化错）。

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

### 3.5 多 Agent 协作
- **Agent 即工具（站1）**：把整个 Agent 用 `@tool` 包成函数，内部调 run_agent。外层看它就是普通工具 → Thought 循环**套娃**。
- **Supervisor 模式（站2）**：主管 Agent 手下多个专精专家（都是工具化的 Agent）。主管决策（派谁/何时/整合），专家执行；信息经主管中心化流动。
- **专精 > 全能**：每专家只配该有的工具（分析师配 data_checkup，撰写员 tools=[]）。
- **协作能涌现更深洞察**：站2 实测中，分析师+撰写员叠加推理出"检查 revenue=quantity×unit_price 逻辑关系"——单 Agent 未必想到。
- **多 Agent 记忆架构**：短期工作记忆各自独立、用完即弃（子Agent无状态最常用）；长期知识共享一个库（架构A，memory.py 本就是共享单例）。给每Agent各建一套=过度设计。

### 3.6 方向二：多 Agent 接入对话循环（当前 chat.py）
- 把 chat.py 内层"单Agent调一个工具"的 ReAct 循环，**替换成一次 run_agent 调用**（tools=[data_analyst, report_writer]，即 Supervisor 团队）。
- **方式 A（当前采用）**：每次提问独立处理，会话内逐句上下文**舍弃**，靠 RAG 长期记忆兜底。检索到的记忆拼进 task 字符串传给 run_agent。
- **方式 B（未来可选）**：让 run_agent 支持传入历史 messages 保留完整会话上下文，更复杂。
- chat.py 当前循环三件事：①search_memory 检索 → ②拼task交run_agent → ③提炼fact存save_memory。
- system_prompt 里要给主管"闲聊可直接回答、不必派专家"的自由，否则对"你好"也派专家显得傻。

---

## 4. 概念顿悟（追问出来的，比代码值钱）

- **invoke ≠ 调模型**：invoke 是通用"执行"动词，作用看点号前是谁。llm.invoke=调模型(返回AIMessage)；tool.invoke=执行函数(返回str)。
- **三种消息谁来造**：Human/ToolMessage 要自己 import 构造（替人/工具发言）；AIMessage 是模型返回的，接输出时不用导入。
- **observation 的开放性**：observation 不是确定的返回值，而是"行动后从环境获得的反馈"——可能成功/失败报错/环境变化。**正因它开放不可预测，才需要会推理的 LLM 而非 if-else。这是 Agent 必须用 LLM 的根本原因。**
- **规则驱动 vs 推理驱动**：工具(规则)报逐列事实；Agent(推理)跨列推断出工具没写规则的洞察。
- **模型对自己的认知来自训练数据+system prompt，不来自实际处境**：DeepSeek 自称"Claude"（身份污染），也不知道自己挂着 RAG。
- **python -m 与包机制**：`python 文件路径` 以文件所在目录找包；`python -m 模块路径`（点号）以当前目录（根）找包。import 平级包必须用 -m 且站根目录。`__init__.py` 标记文件夹为包。
- **Python 环境**：机器上多个 Python 本体（系统/miniconda），每个之上再建隔离环境（venv）。`which python` 查当前用哪个，看 `(venv)` 确认激活，一个项目只用一套。
- **无状态 `run_agent` 逼出的架构后果**：`run_agent` 每次调用内部 `messages=[]` 全新起，只吃 `task` 一个字符串、返回一个字符串——**它从不读外层的 messages**。这一个设计决定，直接让 `chat.py` 那条"会话内记忆 + 持久化 + 摘要压缩"的 in-context 链路**整条从模型大脑上断线**（存进 history.json 的甚至是一份只有用户发言、没有助手回复的残缺对话）。旧架构（单 Agent）里 ReAct 循环直接跑在同一个 `messages` 上，三层记忆天然挂在它身上；换成 Supervisor + `run_agent` 那一刻，chat 层的历史变成一个**独立的、需要另想办法注入 task 的新概念**。→ 顿悟：**记忆住在哪、什么时候该换住处，是随架构变的**；无状态-每次调用是多 Agent 的业界标准，对话状态的重新安家应交给站4的 LangGraph state（内置 MessagesState），而不是现在给手搓循环焊 history 参数（那会在换框架时全拆重来）。

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
12. **【新】RAG 只增不改，无法处理记忆冲突**：改名"小红"改不掉——旧记忆"小杜"没删、且被反复强化相似度更高，模型只能嘴上答应实际无能为力（没有删记忆的工具）。**这是 RAG 记忆系统的核心难题。** 解法方向：加时间戳优先最新 / 存前检测冲突并覆盖 / 给 Agent 一个"删除/更新记忆"的工具。
13. **【新】僵尸代码**：方向二方式A下，会话历史那套（messages累积、compress_history、save_history、load_history）整个失效但还在空转，误导性强（`last_answer = messages[-1].content` 取到的是用户输入不是回答）。**重构要果断删掉不再起作用的代码，别占位留着。**
14. **【新】Git 两条铁律**：①.gitignore 名字必须和实际文件夹精确匹配（`.venv`≠`venv`，写错导致整个 venv 被追踪）；②已被追踪的文件 .gitignore 拦不住，要 `git rm -r --cached <path>` 手动移除（--cached 只松手不删硬盘文件）。
15. **重构后的僵尸代码有"上下游"之分**：把逻辑搬进包后，`chat.py` 里的旧尸体不会报错、还能跑（最阴的静默坑）。而且拔的时候有先后——先拔掉"消费者"（`compress_history`/`save_history`/`load_history`）不等于拔干净，上游的"生产者"（`messages` 初始化、循环里的 `messages.append`）会变成**只写不读**的半路尸体卡在中间。同类：`tools_by_name`/`llm_with_tools`（旧内联 ReAct 循环的零件，逻辑已进 `run_agent`）、`last_answer`（赋值后没人读、注释还写反了）。→ 判据始终是同一句：**这个变量/这行，现在还有谁读它？** 没有下游读者就是尸体，不管它上面 append 得多热闹。

---

## 6. 关键技术配置备忘

- **embedding 模型**：`paraphrase-multilingual-MiniLM-L12-v2`（支持中文，384维）。
- **离线加速**：memory.py **顶部、在 `from sentence_transformers import` 之前**设 `os.environ["HF_HUB_OFFLINE"]="1"` 和 `["TRANSFORMERS_OFFLINE"]="1"`，否则每次启动联网检查 huggingface 卡住重试。（注意顺序，放 import 后无效。）
- **向量库**：`chromadb.PersistentClient(path="./memory_db")` + cosine。
- **运行时路径**：history.json / memory_db 相对路径，**始终在项目根目录启动**。
- **API key**：放 .env，`load_dotenv()` 读，.env 进 .gitignore（已确认未被追踪）。
- **Git**：常用三动作 —— `git add .`（选）→ `git commit -m "说明"`（存档）→ 需要时回退。commit 前先 `git status` 确认 .env 不在清单里。

---

## 7. 下一步（明确的待办）

1. **（可选进阶）解决 RAG 记忆冲突**：给 Agent 加"更新/删除记忆"工具，让它能真改而非嘴上答应。这是很好的进阶练习，直击 bug #12。
2. **站3 · 专精分工**：加更多专家（研究员/清洗师等），体会"专才>全才"、职责边界的工程价值。
3. **站4 · LangGraph**：把手搓 run_agent 换成工业级框架，理解 state/node/edge——因已手写内核，是"认出"而非"从零学"。
4. 站4 额外目标：**用 state（MessagesState）给对话历史重新安家**，补上走 A 时拔掉的 in-context 会话记忆——因为已手写过、也亲手拔过这条链路，到时是"认出它该住哪"而非从零设计。
5. **站5 · MCP**：让 Agent 连真实外部服务。
6. 之后第3周做产品、第4周部署。

---

## 8. 教学约定（给接手的 Claude）

- 一次一个概念，手敲为主，每个新机制先脱离主系统单独跑通再接入。
- 鼓励"改一个点、预测结果、再验证"的实验。
- 把学习者的 bug 和质疑当作讲点，必要时据此调整教学路径（他的好问题已多次重塑教学路线）。
- 学习者用 **DeepSeek**（不是 Claude API），写 Agent 走 LangChain 的 ChatOpenAI + base_url 指向 DeepSeek。
- 不要重复造已有零件；优先复用 run_agent 引擎。
- 已引入 Git，做大改动前提醒/习惯性 commit 存档。
- 语言：中文交流。
