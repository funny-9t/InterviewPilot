# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Interview(Base):
    """
    存储面试核心信息
    对应 parser.py 的输出结构：{company, position, process}
    """
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 原始文本 (用户粘贴的邮件/消息)
    original_text = Column(Text, nullable=True)
    
    # 结构化数据 (parser 解析后的 JSON)
    # 包含: company(name, industry...), position(title, jd...), process(timeline...)
    interview_data = Column(JSON, nullable=False)

    # 关联
    reviews = relationship("InterviewReview", back_populates="interview")
    agent_runs = relationship("AgentRun", back_populates="interview")

class InterviewReview(Base):
    """
    存储用户的复盘数据
    """
    __tablename__ = "interview_reviews"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    created_at = Column(DateTime, default=datetime.now)

    summary = Column(Text)       # 复盘总结
    score = Column(Integer)      # 自评 1-5
    improvement = Column(Text)   # 改进点
    
    interview = relationship("Interview", back_populates="reviews")

class AgentRun(Base):
    """
    存储智能体运行记录 (用于前端回显和历史追溯)
    """
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    created_at = Column(DateTime, default=datetime.now)

    agent_name = Column(String)  # e.g., "progress", "coach", "review", "decision"
    input_context = Column(JSON) # 喂给 Agent 的上下文快照
    output_result = Column(JSON) # Agent 返回的结构化结果
    
    interview = relationship("Interview", back_populates="agent_runs")