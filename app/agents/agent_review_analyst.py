import json
from llm_client import UniAPIClient

client = UniAPIClient()

SYSTEM_PROMPT = """
你是一名面试复盘专家。请根据用户的【复盘总结】和【自评分】，分析其表现。
必须严格返回 JSON 格式，无 Markdown。结构如下：
{
  "skills": {
    "专业能力": 4,
    "沟通表达": 3,
    "逻辑思维": 5
  },
  "weakness": "用一句话总结最核心的薄弱点",
  "actions": ["具体改进动作1", "具体改进动作2"]
}
"""

def run_review_agent(context: dict) -> dict:
    # 获取最新的复盘记录（Orchestrator 传入的 context['history_reviews'] 是列表）
    # 我们主要分析用户刚刚输入的 user_input，或者最近的一条
    user_input = context.get("user_input", {})
    review_text = user_input.get("summary", "用户未提供详细总结")
    self_score = user_input.get("score", 3)
    
    user_msg = f"""
    用户自评：{self_score}/5
    复盘内容：{review_text}
    
    请根据内容推测其能力维度得分（1-5分），找出短板并给出行动建议。
    """
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg}
    ]
    
    raw_json = client.chat_completion(messages, temperature=0.3)
    cleaned_json = raw_json.strip().replace("```json", "").replace("```", "")
    
    return json.loads(cleaned_json)