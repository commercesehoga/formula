// Vercel Serverless Function: /api/generate
// Formula Story Mode — ThunderStudy
//
// Required Vercel environment variable:
//   GROQ_API_KEY
//
// Model is intentionally fixed to Groq's Llama 3.1 8B Instant to avoid
// accidental use of a larger/rate-limited model through an old GROQ_MODEL var.

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'llama-3.1-8b-instant';

const DAILY_LIMIT = 5;
const WEEKLY_LIMIT = 15;

function getClientIp(req) {
  const xff = req.headers && req.headers['x-forwarded-for'];
  if (xff) return String(xff).split(',')[0].trim();
  if (req.headers && req.headers['x-real-ip']) return String(req.headers['x-real-ip']);
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

async function checkServerRateLimit(ip) {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return null;

  const dayKey = `fs:rl:day:${ip}`;
  const weekKey = `fs:rl:week:${ip}`;

  try {
    const r = await fetch(`${url}/pipeline`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify([
        ['INCR', dayKey],
        ['EXPIRE', dayKey, '86400', 'NX'],
        ['INCR', weekKey],
        ['EXPIRE', weekKey, '604800', 'NX']
      ])
    });
    if (!r.ok) return null;
    const results = await r.json();
    const dayCount = Number(results?.[0]?.result);
    const weekCount = Number(results?.[2]?.result);
    if (!Number.isFinite(dayCount) || !Number.isFinite(weekCount)) return null;
    return { dayCount, weekCount };
  } catch {
    return null;
  }
}

const MODE_CONFIG = {
  story: {
    label: 'Story Mode',
    sections: ['THE FORMULA', 'THE STORY', 'WHY IT WORKS', 'KEY VARIABLES', 'EXAM TIP'],
    brief: 'Write a short, vivid, emotionally memorable STORY with characters, conflict and a clear scene that encodes how the formula/concept works so a student remembers it.'
  },
  analogy: {
    label: 'Real-Life Analogy',
    sections: ['THE FORMULA', 'THE ANALOGY', 'THE CONNECTION', 'HOW TO USE IT', 'EXAM TIP'],
    brief: 'Explain the formula/concept with one strong everyday REAL-LIFE ANALOGY familiar to an Indian student and map each part of the formula to the analogy.'
  },
  trick: {
    label: 'Memory Trick',
    sections: ['THE FORMULA', 'THE MEMORY TRICK', 'VISUALIZATION', 'QUICK CHECK', 'COMMON MISCONCEPTION', 'PRACTICE IT'],
    brief: 'Give a punchy mnemonic, acronym, rhyme or word-association to recall the formula, plus a quick mental visualization and tiny self-check question.'
  }
};

function send(res, status, payload) {
  res.status(status).setHeader('Cache-Control', 'no-store');
  res.json(payload);
}

module.exports = async (req, res) => {
  if (req.method === 'OPTIONS') {
    res.status(204).setHeader('Access-Control-Allow-Origin', '*')
      .setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
      .setHeader('Access-Control-Allow-Headers', 'Content-Type')
      .end();
    return;
  }

  if (req.method !== 'POST') {
    send(res, 405, { error: 'Method not allowed. Use POST.' });
    return;
  }

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    send(res, 500, {
      error: 'Server is missing GROQ_API_KEY. Add it in Vercel → Settings → Environment Variables, then redeploy.'
    });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') {
    try { body = JSON.parse(body); } catch { body = {}; }
  }

  const topic = String(body?.topic || '').trim().slice(0, 200);
  const modeKey = MODE_CONFIG[body?.mode] ? body.mode : 'story';

  if (!topic) {
    send(res, 400, { error: 'Please provide a topic or formula.' });
    return;
  }

  const usage = await checkServerRateLimit(getClientIp(req));
  if (usage) {
    if (usage.dayCount > DAILY_LIMIT) {
      send(res, 429, { error: `Daily limit reached (${DAILY_LIMIT}/day). Please try again tomorrow.` });
      return;
    }
    if (usage.weekCount > WEEKLY_LIMIT) {
      send(res, 429, { error: `Weekly limit reached (${WEEKLY_LIMIT}/week). Please try again next week.` });
      return;
    }
  }

  const config = MODE_CONFIG[modeKey];
  const systemPrompt = `You are Formula Story Mode, an AI study aid for Indian competitive exam students.
Given a formula, theorem or concept from Physics, Chemistry, Maths, Biology, Economics or Accountancy, produce a short exam-relevant memory aid.

Rules:
- Plain text only. No Markdown, emojis or numbered lists.
- Use EXACTLY these section headers, in this order: ${config.sections.join(', ')}.
- Under THE FORMULA, write only the formula itself and short variable names.
- Keep the entire answer under 220 words.
- Be concrete, accurate and specific to the topic.
- Tone: clear, encouraging and exam-focused.
- ${config.brief}`;

  const userPrompt = `Topic / formula: ${topic}\nMode: ${config.label}`;

  const requestBody = {
    model: MODEL,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt }
    ],
    temperature: 0.75,
    max_tokens: 650
  };

  // One short retry for temporary 429/5xx responses. The frontend still
  // receives a useful status if Groq remains unavailable.
  let lastStatus = 502;
  let lastMessage = 'Groq API request failed. Please try again.';
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const groqRes = await fetch(GROQ_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${apiKey}`
        },
        body: JSON.stringify(requestBody)
      });

      const data = await groqRes.json().catch(() => ({}));

      if (groqRes.ok) {
        const text = String(data?.choices?.[0]?.message?.content || '').trim();
        if (!text) {
          send(res, 502, { error: 'Empty response from AI. Please try again.' });
          return;
        }
        send(res, 200, { text, model: MODEL });
        return;
      }

      lastStatus = groqRes.status;
      lastMessage = String(data?.error?.message || 'Groq API request failed.');

      if ((groqRes.status === 429 || groqRes.status >= 500) && attempt === 0) {
        const retryAfter = Number(groqRes.headers.get('retry-after'));
        const waitMs = Number.isFinite(retryAfter)
          ? Math.min(Math.max(retryAfter * 1000, 700), 5000)
          : 1200;
        await new Promise(resolve => setTimeout(resolve, waitMs));
        continue;
      }

      send(res, lastStatus, { error: lastMessage });
      return;
    } catch {
      if (attempt === 0) {
        await new Promise(resolve => setTimeout(resolve, 700));
        continue;
      }
      send(res, 502, { error: 'Failed to reach Groq API. Please try again in a moment.' });
      return;
    }
  }

  send(res, lastStatus, { error: lastMessage });
};
