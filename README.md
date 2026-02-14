# InterviewPilot 技术说明文档

**版本**: MVP-1.0  
**日期**: 2025-12-17  
**状态**: 已验证跑通  

---
面试信息录入：
<img width="2503" height="1166" alt="屏幕截图 2025-12-17 194431" src="https://github.com/user-attachments/assets/6d9c7642-de23-4f37-a27f-a3e55c06c7a9" />
时间轴视图：
<img width="2440" height="607" alt="屏幕截图 2025-12-17 201926" src="https://github.com/user-attachments/assets/b57a7c6b-abd0-4feb-89df-49b8f247b0ba" />
日历视图：
<img width="2255" height="474" alt="屏幕截图 2025-12-17 201322" src="https://github.com/user-attachments/assets/c76f39cc-f54a-4d8b-8744-faac9c947107" />
模块功能：
<img width="1108" height="541" alt="image" src="https://github.com/user-attachments/assets/a51bdd8e-9f65-468f-9a7c-e701b919bd8d" />
<img width="1108" height="508" alt="image" src="https://github.com/user-attachments/assets/67fafe25-86e5-4488-a948-86cc847c2fad" />

## 1. 项目概述
**InterviewPilot** 是一个面向求职者的全周期面试智能管理助手。它利用大语言模型（LLM）实现从非结构化面试信息录入、进度管理、个性化备战、复盘分析到 Offer 决策的全流程辅助。

### 核心价值
* **信息结构化**：将散乱的邮件/微信通知一键解析为结构化日历事件，自动提取时间、会议链接与 JD 摘要。
* **智能备战**：基于 JD 和公司背景生成针对性的模拟面试脚本 (Mock Script) 与 STAR 回答思路。
* **闭环复盘**：量化分析面试表现，生成能力画像与改进建议。

---

## 2. 技术栈架构

本项目采用 **轻量级单体架构**，便于快速部署和个人使用。

### 前端 (Frontend)
* **框架**: React 18 + Ant Design 5。
* **运行模式**: No-Build 模式。通过浏览器端 Babel (`@babel/standalone`) 实时编译 JSX，无需 Webpack/Vite 打包配置，修改即生效。
* **通信**: Fetch API (使用相对路径直接请求后端，自动适配端口)。

### 后端 (Backend)
* **框架**: FastAPI (Python)。
* **服务**: Uvicorn (ASGI Server)。
* **入口**: `run.py` (集成了静态文件托管与路由自检，解决路径依赖问题)。

### 数据层 (Data)
* **数据库**: SQLite (本地文件存储 `interviewpilot.db`)。
* **ORM**: SQLAlchemy (定义模型与操作)。

### AI 核心 (AI Core)
* **模型**: OpenAI GPT-4o-mini (或兼容的 LLM)。
* **客户端**: 自封装 `UniAPIClient`，统一处理 Prompt 和 JSON 清洗。

---

## 3. 目录结构

当前项目采用 **后端托管前端** 的结构，确保解决了静态资源路径和跨域问题。

```text
InterviewPilot/
├── app/                   # 核心代码目录
│   ├── agents/                # 智能体模块
│   │   ├── __init__.py
│   │   ├── agent_progress_commander.py  # 进度指挥官
│   │   ├── agent_interview_coach.py     # 备战教练 (含 Mock Script)
│   │   ├── agent_review_analyst.py      # 复盘分析师
│   │   └── agent_decision_advisor.py    # 决策顾问
│   │
│   ├── static/                # 前端静态资源 (由 FastAPI 托管)
│   │   ├── index.html         # 入口 HTML
│   │   └── app.js             # React 业务逻辑
│   │
│   ├── database.py            # 数据库连接会话
│   ├── models.py              # SQLAlchemy 数据模型
│   ├── orchestrator.py        # 智能体调度中枢
│   ├── parser.py              # 面试文本解析器
│   ├── llm_client.py       # LLM API 客户端
│   ├── run.py                 # 【启动入口】(包含路径修复与自检)
│   └── main.py                # (旧入口，已废弃或作为备用)
│
├── interviewpilot.db          # SQLite 数据库文件 (运行后自动生成)
└── requirements.txt           # 依赖列表

```
---

## 4. 核心功能模块实现

### 4.1 数据解析 (Parser)
功能: 将用户粘贴的文本转化为 JSON。

逻辑: parser.py 调用 LLM 提取 company, position, process。

增强字段: 最新版本增加了 time (具体时间段), link (会议链接), jd_summary (岗位摘要) 的提取 。

### 4.2 智能体调度 (Orchestrator)
功能: orchestrator.py 充当大脑，负责从数据库提取上下文（Context），分发给具体的 Agent，并将结果存回 AgentRun 表 。

上下文注入: 自动注入 company_name, jd_keywords, history_reviews 等信息，防止 AI 幻觉。

### 4.3 四大智能体 (Agents)
- **进度指挥官 (Progress)**: 计算面试倒计时，检测时间冲突 。

- **备战教练 (Coach)**:
  - 生成 Checklist。
  - 模拟面试脚本: 生成 "Q (问题) - Intent (意图) - STAR Guide (回答思路)" 结构化数据 。

- **复盘分析师 (Review)**: 基于用户复盘生成五维能力评分 (雷达图数据) 和改进建议 。

- **决策顾问 (Decision)**: 生成 Offer 多维对比矩阵 。

---
## 5. API 接口说明

后端服务运行在 http://127.0.0.1:8002 (由 run.py 配置) 。

### 面试管理
- **GET /interviews**: 获取所有面试列表（按时间倒序）。
- **POST /interviews**: 录入新面试（触发 Parser 解析）。
  - Input: `{"text": "原始文本"}`
- **POST /interviews/{id}/review**: 提交复盘信息。

### 智能体调用
- **POST /agents/{agent_type}/{interview_id}**
  - `agent_type`: progress | prep | review | decision
  - Output: 统一的 JSON 结构，由前端根据 type 渲染不同 UI 组件 。

---

## 6. 安装与运行指南

### 环境准备
- Python 3.10+
- OpenAI API Key (或兼容 Key)

### 步骤
1. **安装依赖:**
   ```bash
   pip install fastapi uvicorn sqlalchemy requests openai
   ```

2. **配置 Key:** 设置环境变量 `UNIAPI_KEY` 或 `OPENAI_API_KEY`。

3. **启动服务:**
   ```bash
   cd backend
   python run.py
   ```
   (注意：不要使用 `uvicorn main:app`，请使用 `python run.py` 以确保静态文件路径正确)

4. **访问应用:** 打开浏览器访问 http://127.0.0.1:8002。

