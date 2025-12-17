import os
import uvicorn
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# 引入之前的业务模块
from database import get_db, init_db
from models import Interview, InterviewReview
from orchestrator import Orchestrator
from parser import parse_interview_text

# 1. 核心路径配置 (保持这个不动，它是成功的关键)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="InterviewPilot Final")

# 2. CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 数据模型
class TextInput(BaseModel):
    text: str

class ReviewInput(BaseModel):
    summary: str
    score: int
    improvement: str

# 4. 业务接口区
@app.get("/interviews")
def get_interviews(db: Session = Depends(get_db)):
    init_db()  # 确保数据库表存在
    interviews = db.query(Interview).order_by(Interview.created_at.desc()).all()
    return interviews

@app.post("/interviews")
def create_interview(item: TextInput, db: Session = Depends(get_db)):
    try:
        # 调用 parser 解析
        parsed_data = parse_interview_text(item.text)
        db_interview = Interview(original_text=item.text, interview_data=parsed_data)
        db.add(db_interview)
        db.commit()
        db.refresh(db_interview)
        return db_interview
    except Exception as e:
        print(f"解析错误: {e}")
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
async def run_agent_endpoint(
    agent_type: str, 
    interview_id: int, 
    payload: dict = Body(default={}), 
    db: Session = Depends(get_db)
):
    orchestrator = Orchestrator(db)
    try:
        result = orchestrator.dispatch(interview_id, agent_type, user_input=payload)
        return result
    except Exception as e:
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 5. 静态文件托管区 (成功逻辑)

# 确保 static 存在
if not STATIC_DIR.exists():
    os.makedirs(STATIC_DIR)

# 挂载 /static 目录
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 根路由 -> index.html
@app.get("/")
async def read_index():
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

# 兜底路由 -> app.js (防止前端写错路径)
@app.get("/app.js")
async def read_app_js_fallback():
    return FileResponse(STATIC_DIR / "app.js")

# 6. 启动入口 (保持 8002 端口)
if __name__ == "__main__":
    print(f"🚀 服务正在启动，请访问: http://127.0.0.1:8002")
    uvicorn.run("run:app", host="127.0.0.1", port=8002, reload=True)