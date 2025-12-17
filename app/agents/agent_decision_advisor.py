import json
from llm_client import UniAPIClient

client = UniAPIClient()

SYSTEM_PROMPT = """
你是一名职业规划顾问。请分析该职位的机会。
必须严格返回 JSON 格式，无 Markdown。结构如下：
{
  "matrix": {
    "columns": [{"title": "维度", "dataIndex": "dim"}, {"title": "评分", "dataIndex": "score"}, {"title": "分析", "dataIndex": "analysis"}],
    "rows": [
       {"dim": "薪资待遇", "score": "85分", "analysis": "简短评价"},
       {"dim": "成长空间", "score": "90分", "analysis": "简短评价"}
    ]
  },
  "recommendation": "基于当前信息的整体决策建议（100字以内）"
}
"""

def run_decision_agent(context: dict) -> dict:
    company = context.get("company", {}).get("name", "")
    position = context.get("position", {}).get("title", "")
    
    user_msg = f"""
    请分析以下 Offer 机会的优劣势：
    公司：{company}
    职位：{position}
    
    请构建分析矩阵（包含薪资、成长、强度、文化四个维度），并给出职业发展建议。
    """
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]
    
    raw_json = client.chat_completion(messages, temperature=0.5)
    cleaned_json = raw_json.strip().replace("```json", "").replace("```", "")
    
    return json.loads(cleaned_json)