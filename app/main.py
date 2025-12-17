import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import get_db, init_db
from models import Interview, InterviewReview
from orchestrator import Orchestrator
from parser import parse_interview_text

# 1. 路径修复核心逻辑 (保留这部分成功的代码)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="InterviewPilot Backend")

# 2. CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 数据模型定义
class TextInput(BaseModel):
    text: str

class ReviewInput(BaseModel):
    summary: str
    score: int
    improvement: str

# 4. 业务 API 接口
@app.get("/interviews")
def get_interviews(db: Session = Depends(get_db)):
    init_db() # 确保表存在
    interviews = db.query(Interview).order_by(Interview.created_at.desc()).all()
    return interviews

@app.post("/interviews")
def create_interview(item: TextInput, db: Session = Depends(get_db)):
    try:
        # 这里为了 MVP 演示，简单处理异常
        parsed_data = parse_interview_text(item.text)
        db_interview = Interview(original_text=item.text, interview_data=parsed_data)
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        return db_interview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解析失败: {str(e)}")

@app.post("/interviews/{interview_id}/review")
def add_review(interview_id: int, review: ReviewInput, db: Session = Depends(get_db)):
    db_review = InterviewReview(
        interview_id=interview_id,
        summary=review.summary,
        score=review.score,
        improvement=review.improvement
    )
    db.add(db_review)
    db.commit()
    return {"status": "ok"}

@app.post("/agents/{agent_type}/{interview_id}")
async def run_agent_endpoint(agent_type: str, interview_id: int, payload: dict = Body(default={}), db: Session = Depends(get_db)):
    orchestrator = Orchestrator(db)
    try:
        result = orchestrator.dispatch(interview_id, agent_type, user_input=payload)
        return result
    except Exception as e:
        print(f"❌ Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. 静态文件托管 (前端页面)
# 挂载 /static 路径，供 HTML 引用 /static/app.js
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 根路由返回 index.html
@app.get("/")
async def read_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return {"error": "index.html not found"}
    return FileResponse(index_path)