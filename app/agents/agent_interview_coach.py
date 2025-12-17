import json
from llm_client import UniAPIClient

client = UniAPIClient()

SYSTEM_PROMPT = """
你是一名资深面试教练。请根据用户提供的【公司】、【职位】和【JD】，生成一份结构化的面试准备方案。
必须严格返回 JSON 格式，不要包含 Markdown 标记（如 ```json）。结构如下：
{
  "checklist": ["复习XX知识点", "准备XX案例"...],
  "mock_script": [
    {
      "question": "面试官可能会问的问题",
      "intent": "考察意图",
      "star_guide": "回答要点（Situation/Task/Action/Result）"
    }
  ]
}
"""

def run_coach_agent(context: dict) -> dict:
    company = context.get("company", {}).get("name", "目标公司")
    position = context.get("position", {}).get("title", "该职位")
    jd = context.get("position", {}).get("jd_keywords", [])
    
    user_msg = f"""
    目标公司：{company}
    目标职位：{position}
    JD关键词：{', '.join(jd) if isinstance(jd, list) else jd}
    
    请生成：
    1. 5项具体的准备清单 (checklist)
    2. 3个高频模拟面试题 (mock_script)，包含考察意图和回答思路。
    """
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]
    
    raw_json = client.chat_completion(messages, temperature=0.5)
    
    # 简单的清洗逻辑，防止 markdown
    cleaned_json = raw_json.strip().replace("```json", "").replace("```", "")
    
    return json.loads(cleaned_json)