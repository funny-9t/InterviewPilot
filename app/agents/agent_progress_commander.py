import json
import datetime
from llm_client import UniAPIClient

client = UniAPIClient()

def run_progress_agent(context: dict) -> dict:
    """
    输入 context: { "process": { "timeline": [...] }, "company": ... }
    输出: { "reminders": ["..."], "conflicts": [] }
    """
    
    # 1. Python 逻辑处理时间计算 (比 LLM 更准更快)
    timeline = context.get("process", {}).get("timeline", [])
    today = datetime.date.today()
    
    reminders = []
    upcoming_event = None
    
    for stage in timeline:
        # 假设 date 格式为 YYYY-MM-DD
        try:
            event_date = datetime.datetime.strptime(stage["date"], "%Y-%m-%d").date()
            delta = (event_date - today).days
            
            if delta == 0:
                reminders.append(f"【今天】{stage['stage']}：保持自信，检查网络环境！")
                upcoming_event = stage
            elif delta == 1:
                reminders.append(f"【明天】{stage['stage']}：请查收准备包，复习简历。")
                upcoming_event = stage
            elif delta > 0 and delta <= 3:
                reminders.append(f"【{delta}天后】{stage['stage']}：还有时间准备。")
                upcoming_event = stage
        except:
            continue

    # 2. 调用 LLM 生成一句 "暖心/策略性" 提醒 (仅当有即将到来的面试时)
    if upcoming_event:
        prompt = f"""
        用户即将参加 {context['company'].get('name')} 的 {upcoming_event['stage']}。
        请生成一条简短的（30字以内）鼓励或策略性提醒。
        直接返回内容，不要引号。
        """
        try:
            ai_tip = client.chat_completion([{"role": "user", "content": prompt}], max_tokens=60)
            reminders.append(f"💡 AI建议：{ai_tip}")
        except:
            pass # 容错

    return {
        "reminders": reminders if reminders else ["暂无近期面试安排"],
        "conflicts": [] # MVP 暂略过复杂日历冲突检测
    }