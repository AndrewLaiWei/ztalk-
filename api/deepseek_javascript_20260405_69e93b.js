export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const { scene, history, userInput } = req.body;
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

  // 场景系统提示词（让AI扮演特定角色）
  const scenePrompts = {
    wine: `你是一个酒桌文化中的强势领导，喜欢用感情绑架逼人喝酒。说话要带压迫感，比如“不喝就是看不起我”。`,
    marry: `你是一个爱管闲事的长辈亲戚，喜欢催婚、比较、道德绑架。说话要带“你看别人家孩子”。`,
    work: `你是一个职场中爱抢功劳、甩锅的同事。说话要阴阳怪气、推卸责任。`,
    rent: `你是一个只谈利益的房东，涨价不讲感情，喜欢威胁“不租就搬走”。`,
    interview: `你是一个HR，利用信息不对称压价，说“你经验不足”。`,
    client: `你是一个无理取闹的甲方，喜欢提模糊要求如“五彩斑斓的黑”。`
  };

  // 第一步：判断用户是否赢了
  const judgePrompt = `场景：${scenePrompts[scene]}。对话历史：${JSON.stringify(history)}。用户最新回应："${userInput}"。请判断用户是否成功反驳或压制了对手。只输出一个单词：WIN 或 LOSE。`;

  const judgeRes = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'perplexity/llama-3.1-8b-instruct-r1-1776',
      messages: [{ role: 'user', content: judgePrompt }],
      temperature: 0.3,
      max_tokens: 10
    })
  });
  const judgeData = await judgeRes.json();
  const result = judgeData.choices[0].message.content.trim().toUpperCase();

  let teaching = [];
  let nextOpponentLine = '';

  if (result === 'LOSE') {
    // 生成三个教学话术
    const teachPrompt = `用户输了。请给出3个更好的回怼话术（每行一个），直接输出，不要序号。`;
    const teachRes = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'perplexity/llama-3.1-8b-instruct-r1-1776',
        messages: [{ role: 'user', content: teachPrompt }],
        temperature: 0.7,
        max_tokens: 200
      })
    });
    const teachData = await teachRes.json();
    teaching = teachData.choices[0].message.content.split('\n').filter(l => l.trim());
  } else {
    // 赢了，生成对手下一句挑衅
    const nextPrompt = `用户赢了上一轮。现在你作为对手，要继续刁难，生成下一句挑衅或施压的话，只输出一句话。`;
    const nextRes = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${OPENROUTER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'perplexity/llama-3.1-8b-instruct-r1-1776',
        messages: [{ role: 'user', content: nextPrompt }],
        temperature: 0.8,
        max_tokens: 100
      })
    });
    const nextData = await nextRes.json();
    nextOpponentLine = nextData.choices[0].message.content.trim();
  }

  return res.status(200).json({ result, teaching, nextOpponentLine });
}