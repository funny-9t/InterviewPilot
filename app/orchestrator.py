# orchestrator.py
from sqlalchemy.orm import Session
from models import Interview, AgentRun, InterviewReview
import json
from datetime import datetime

# 导入具体的 Agent 函数 (稍后在 agents/ 目录实现)
# from agents.agent_progress_commander import run_progress_agent
# from agents.agent_interview_coach import run_coach_agent
# from agents.agent_review_analyst import run_review_agent
# from agents.agent_decision_advisor import run_decision_agent

# 为了演示，先定义占位符，待会生成 Agent 代码时替换
def run_progress_agent(context): return {"reminders": ["模拟提醒"], "conflicts": []}
def run_coach_agent(context): return {"checklist": ["模拟清单"]}
def run_review_agent(context): return {"skills": {}, "weakness": "无"}
def run_decision_agent(context): return {"matrix": {}, "recommendation": "无"}

class Orchestrator:
    def __init__(self, db: Session):
        self.db = db

    def dispatch(self, interview_id: int, agent_type: str, user_input: dict = None):
        """
        核心调度方法
        1. 获取面试记录
        2. 组装 Context
        3. 调用对应 Agent
        4. 存储运行结果
        """
        # 1. 获取数据
        interview = self.db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"面试 ID {interview_id} 不存在")

        # 2. 组装上下文 (Context Assembly)
        # 将结构化数据提取出来，供 LLM 理解
        context = {
            "company": interview.interview_data.get("company", {}),
            "position": interview.interview_data.get("position", {}),
            "process": interview.interview_data.get("process", {}),
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "user_input": user_input or {}
        }

        # 如果是复盘或决策 Agent，还需要历史复盘数据
        if agent_type in ["review", "decision"]:
            reviews = self.db.query(InterviewReview).filter(
                InterviewReview.interview_id == interview_id
            ).all()
            context["history_reviews"] = [
                {"summary": r.summary, "score": r.score, "improvement": r.improvement} 
                for r in reviews
            ]

        # 3. 路由分发
        result = {}
        if agent_type == "progress":
            # 这里我们需要 import 真实的 agent 函数
            from agents.agent_progress_commander import run_progress_agent
            result = run_progress_agent(context)
            
        elif agent_type == "prep":
            from agents.agent_interview_coach import run_coach_agent
            result = run_coach_agent(context)
            
        elif agent_type == "review":
            from agents.agent_review_analyst import run_review_agent
            result = run_review_agent(context)
            
        elif agent_type == "decision":
            from agents.agent_decision_advisor import run_decision_agent
            result = run_decision_agent(context)
            
        else:
            raise ValueError(f"未知的 Agent 类型: {agent_type}")

        # 4. 存储运行记录 (AgentRun)
        agent_run = AgentRun(
            interview_id=interview_id,
            agent_name=agent_type,
            input_context=context, # 存下来，方便 debug
            output_result=result
        )
        self.db.add(agent_run)
        self.db.commit()
        self.db.refresh(agent_run)

        return result