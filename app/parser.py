import json
from llm_client import UniAPIClient

client = UniAPIClient()

# 升级后的 Prompt：增加了 time, link, jd_summary 字段
SYSTEM_PROMPT = """
你是一个面试信息抽取助手。请从用户提供的文本中，提取【完整、结构化】的面试信息。
严格返回 JSON，不要任何解释文字。

JSON 结构定义如下：
{
  "company": {
    "name": "公司名称",
    "industry": "行业 (如互联网/金融)",
    "scale": "规模"
  },
  "position": {
    "title": "岗位名称",
    "department": "部门",
    "jd_keywords": ["技术栈1", "核心要求2"], 
    "jd_summary": "职位描述的简短摘要 (50字以内)"
  },
  "process": {
    "current_stage": "当前阶段",
    "timeline": [
      {
        "stage": "面试轮次 (如：技术一面)", 
        "date": "YYYY-MM-DD", 
        "time": "HH:MM (具体时间，如 14:00-15:00，没提到则留空)",
        "link": "会议/面试链接 (URL，没提到则留空)",
        "status": "未开始/已完成"
      }
    ]
  }
}
"""

def parse_interview_text(text: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text}
    ]
    response = client.chat_completion(messages)
    
    # 清洗可能存在的 Markdown 标记
    cleaned_response = response.strip().replace("```json", "").replace("```", "")
    
    try:
        return json.loads(cleaned_response)
    except json.JSONDecodeError:
        # 简单的容错返回
        return {
            "company": {"name": "解析失败", "industry": "", "scale": ""},
            "position": {"title": "未知职位", "jd_keywords": []},
            "process": {"timeline": []}
        }