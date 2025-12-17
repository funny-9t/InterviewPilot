const { useState, useEffect } = React;
const {
  Calendar, Timeline, Button, Drawer, Form, Input, 
  Rate, Card, Tabs, Divider, List, Checkbox, 
  Table, Tag, Alert, Collapse, Typography, Space, Tooltip
} = antd;

const { Title, Text } = Typography;

// 日期处理函数
function normalizeDate(dateStr) {
  if (!dateStr) return "";
  const isoMatch = dateStr.match(/^(\d{4}-\d{2}-\d{2})/);
  if (isoMatch) return isoMatch[1];
  const cnMatch = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (cnMatch) {
    const [, y, m, d] = cnMatch;
    return `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
  }
  return "";
}

function formatDisplayDate(dateStr, timeStr) {
  const date = normalizeDate(dateStr);
  if (!date) return dateStr;
  const [y, m, d] = date.split('-');
  const cnDate = `${y}年${Number(m)}月${Number(d)}日`;
  
  if (timeStr) return `${cnDate} ${timeStr}`;
  if (dateStr.includes('T') && !timeStr) {
      const timePart = dateStr.split('T')[1];
      if (timePart) return `${cnDate} ${timePart.substring(0, 5)}`;
  }
  return cnDate;
}

function App() {
  const [interviews, setInterviews] = useState([]);
  const [current, setCurrent] = useState(null); 
  const [open, setOpen] = useState(false);      
  const [activeTab, setActiveTab] = useState("calendar"); 
  const [agentTab, setAgentTab] = useState("progress");   
  const [agentResult, setAgentResult] = useState(null);
  const [agentLoading, setAgentLoading] = useState(false);
  const [inputText, setInputText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => { load(); }, []);

  // 自动滚动定位效果
  useEffect(() => {
    if (activeTab === "timeline" && current) {
      // 稍微延迟一下，确保 DOM 渲染完毕
      setTimeout(() => {
        const el = document.getElementById(`interview-card-${current.id}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }, 100);
    }
  }, [activeTab, current]);

  async function load() {
    try {
      const res = await fetch("/interviews");
      const data = await res.json();
      setInterviews(data);
    } catch (e) { console.error("加载失败", e); }
  }

  function allEvents() {
    return interviews.flatMap(iv =>
      iv.interview_data.process.timeline.map(t => {
        const date = normalizeDate(t.date);
        if (!date) return null;
        return {
          date, 
          title: `${iv.interview_data.company.name} · ${t.stage}`,
          time: t.time || "", 
          interviewId: iv.id,
          raw: iv
        };
      }).filter(Boolean)
    );
  }

  async function submitInterview() {
    if (!inputText.trim()) return;
    setSubmitting(true);
    try {
      const res = await fetch("/interviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText })
      });
      if (!res.ok) throw new Error();
      setInputText("");
      load();
    } catch { alert("解析失败，请检查后端日志"); } 
    finally { setSubmitting(false); }
  }

  async function submitReview(values) {
    await fetch(`/interviews/${current.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values)
    });
    setOpen(false);
    load(); 
  }

  async function runAgent(endpoint) {
    if (!current) return;
    setAgentLoading(true);
    setAgentResult(null);
    try {
      const body = endpoint === "review" ? { text: "用户触发分析" } : {};
      const res = await fetch(`/agents/${endpoint}/${current.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      setAgentResult(data);
    } catch { alert("智能体调用失败"); } 
    finally { setAgentLoading(false); }
  }

  return (
    <>
      <Card title=" 📥  面试信息录入" style={{ marginBottom: 24 }}>
        <Input.TextArea
          rows={3}
          placeholder="粘贴面试通知邮件、JD、微信聊天记录..."
          value={inputText}
          onChange={e => setInputText(e.target.value)}
        />
        <div style={{ marginTop: 12, textAlign: "right" }}>
          <Button type="primary" loading={submitting} onClick={submitInterview}>AI 解析并存入</Button>
        </div>
      </Card>

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={[
        {
          key: "calendar",
          label: " 📅  面试日历",
          children: (
            <Calendar
              // 智能跳转逻辑
              onSelect={(value, info) => {

                if (info && info.source !== 'date') return;

                const dateStr = value.format("YYYY-MM-DD");
                const dayEvents = allEvents().filter(e => e.date === dateStr);

                if (dayEvents.length > 0) {
                    setCurrent(dayEvents[0].raw);
                    setActiveTab("timeline");
                }
              }}
              cellRender={value => {
                const date = value.format("YYYY-MM-DD");
                const events = allEvents().filter(e => e.date === date);
                if (events.length === 0) return null;
                return (
                  <div>
                    {events.map((e, idx) => (
                      <div key={idx} 
                           style={{ fontSize: 12, background: "#e6f4ff", marginBottom: 4, padding: "2px 4px", borderRadius: 4, cursor: 'pointer' }}
                           onClick={(ev) => { 
                               ev.stopPropagation(); // 防止冒泡，优先执行具体的事件点击
                               setCurrent(e.raw); 
                               setActiveTab("timeline"); 
                           }}
                      >
                        <div style={{fontWeight: 'bold'}}>{e.title}</div>
                        {e.time && <div style={{fontSize: 10, color:'#666'}}>⏰ {e.time}</div>}
                      </div>
                    ))}
                  </div>
                );
              }}
            />
          )
        },
        {
          key: "timeline",
          label: " 🧭  面试时间轴",
          children: (
            <div>
              {interviews.length === 0 && <p style={{color:'#999', textAlign:'center'}}>暂无记录，请录入。</p>}
              {interviews.map(iv => (
                <Card
                  key={iv.id}
                  // 给卡片绑定 ID，用于自动滚动定位
                  id={`interview-card-${iv.id}`}
                  title={`${iv.interview_data.company.name} - ${iv.interview_data.position.title}`}
                  style={{ marginBottom: 16, border: current?.id === iv.id ? '2px solid #1677ff' : '' }}
                  onClick={() => setCurrent(iv)}
                  extra={
                    <Space>
                      <Button size="small" onClick={(e) => { e.stopPropagation(); setCurrent(iv); setOpen(true); }}>📝 写复盘</Button>
                      <Button size="small" type={current?.id === iv.id ? "primary" : "default"} onClick={(e) => { e.stopPropagation(); setCurrent(iv); setActiveTab("agents"); }}>🚀 智能助手</Button>
                    </Space>
                  }
                >
                  <div style={{marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid #f0f0f0'}}>
                    <Space size={[0, 8]} wrap>
                        {iv.interview_data.position.department && <Tag icon="🏢">{iv.interview_data.position.department}</Tag>}
                        {iv.interview_data.position.jd_keywords?.map((k, i) => <Tag key={i} color="geekblue">{k}</Tag>)}
                    </Space>
                    {iv.interview_data.position.jd_summary && (
                        <div style={{marginTop: 8, color: '#888', fontSize: 13}}>
                           📄 岗位摘要: {iv.interview_data.position.jd_summary}
                        </div>
                    )}
                  </div>

                  <Timeline items={iv.interview_data.process.timeline.map(t => ({
                    color: t.status === '完成' ? 'green' : 'blue',
                    children: (
                      <div style={{paddingBottom: 8}}>
                        <div style={{fontWeight: 'bold', fontSize: 15, marginBottom: 4}}>
                           🔵 {formatDisplayDate(t.date, t.time)} · {t.stage}
                        </div>
                        {t.link && (
                            <div style={{marginTop: 4, fontSize: 13}}>
                                🔗 <a href={t.link} target="_blank" onClick={e=>e.stopPropagation()}>进入面试会议 / 详情链接</a>
                            </div>
                        )}
                      </div>
                    )
                  }))} />
                </Card>
              ))}
            </div>
          )
        },
        {
          key: "agents",
          label: " 🤖  智能体工作台",
          children: current ? (
            <div style={{display:'flex', gap: 24}}>
                <Card style={{width: 200, height: 'fit-content'}}>
                    <div style={{marginBottom: 16, fontWeight:'bold'}}>{current.interview_data.company.name}</div>
                    <Space direction="vertical" style={{width:'100%'}}>
                        <Button block type={agentTab === "progress" ? "primary" : "text"} onClick={() => {setAgentTab("progress"); runAgent("progress")}}>进度指挥官</Button>
                        <Button block type={agentTab === "prep" ? "primary" : "text"} onClick={() => {setAgentTab("prep"); runAgent("prep")}}>备战教练</Button>
                        <Button block type={agentTab === "review" ? "primary" : "text"} onClick={() => {setAgentTab("review"); runAgent("review")}}>复盘分析师</Button>
                        <Button block type={agentTab === "decision" ? "primary" : "text"} onClick={() => {setAgentTab("decision"); runAgent("decision")}}>决策顾问</Button>
                    </Space>
                </Card>
                <Card style={{flex:1}} loading={agentLoading}>
                    {!agentResult && !agentLoading && <div style={{textAlign:'center', color:'#999', marginTop: 50}}>点击左侧按钮启动智能体</div>}
                    
                    {agentResult && agentTab === "progress" && (
                        <>
                            <Divider orientation="left">智能提醒</Divider>
                            <Alert message="近期安排" description={<ul style={{paddingLeft:20}}>{agentResult.reminders?.map((r, i)=><li key={i}>{r}</li>)}</ul>} type="info" showIcon />
                        </>
                    )}
                    
                    {agentResult && agentTab === "prep" && (
                        <>
                            <Divider orientation="left">准备清单</Divider>
                            <List bordered dataSource={agentResult.checklist || []} renderItem={item=><List.Item><Checkbox>{item}</Checkbox></List.Item>} />
                            <Divider orientation="left">模拟面试题库</Divider>
                            {agentResult.mock_script ? (
                                <Collapse items={agentResult.mock_script.map((item, idx) => ({
                                    key: idx, label: <span style={{fontWeight:'bold'}}>Q{idx+1}: {item.question}</span>,
                                    children: (<div><Tag color="blue">考察意图</Tag> {item.intent}<div style={{marginTop:12, background:'#f5f5f5', padding:12}}><strong>💡 回答思路：</strong>{item.star_guide}</div></div>)
                                }))} />
                            ) : <p>暂无数据</p>}
                        </>
                    )}

                    {agentResult && agentTab === "review" && (
                        <>
                            <Divider orientation="left">能力画像</Divider>
                            <div style={{display:'flex', gap:16, flexWrap:'wrap'}}>{Object.entries(agentResult.skills||{}).map(([k,v])=>(<Card key={k} size="small" title={k} style={{width:120}}><Rate disabled defaultValue={v} style={{fontSize:12}}/></Card>))}</div>
                            <Alert style={{marginTop:24}} message="核心薄弱点" type="warning" showIcon description={agentResult.weakness} />
                            <Divider orientation="left">改进建议</Divider>
                            <List dataSource={agentResult.actions||[]} renderItem={(item,i)=><List.Item><Text mark>{i+1}.</Text> {item}</List.Item>} />
                        </>
                    )}

                    {agentResult && agentTab === "decision" && (
                        <>
                            <Divider orientation="left">Offer 分析</Divider>
                            {agentResult.matrix && <Table dataSource={agentResult.matrix.rows} columns={agentResult.matrix.columns} pagination={false} bordered rowKey="dim"/>}
                            {agentResult.recommendation && <Alert style={{marginTop:16}} message="建议" description={agentResult.recommendation} type="success" showIcon />}
                        </>
                    )}
                </Card>
            </div>
          ) : (
            <div style={{textAlign:'center', marginTop: 50}}>
                <p>👈 请先在“面试时间轴”中选择一个面试记录</p>
                <Button onClick={() => setActiveTab("timeline")}>去选择</Button>
            </div>
          )
        }
      ]} />
      <Drawer title="📝 面试复盘" open={open} onClose={() => setOpen(false)} width={400}>
        <Form onFinish={submitReview} layout="vertical">
          <Form.Item name="summary" label="复盘总结" rules={[{required:true}]}><Input.TextArea rows={6}/></Form.Item>
          <Form.Item name="score" label="自我评分"><Rate /></Form.Item>
          <Form.Item name="improvement" label="一句话改进点"><Input.TextArea rows={2}/></Form.Item>
          <Button type="primary" htmlType="submit" block>保存复盘</Button>
        </Form>
      </Drawer>
    </>
  );
}
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);