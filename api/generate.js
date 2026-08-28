// /api/generate.js
// Vercel Serverless Function — calls Groq's OpenAI-compatible Chat Completions API.
//
// Required environment variable (set in Vercel → Project → Settings → Environment Variables):
//   GROQ_API_KEY    Your Groq API key from https://console.groq.com/keys
//
// Optional:
//   GROQ_MODEL                  Ignored; this project uses "qwen/qwen3.6-27b"
//   UPSTASH_REDIS_REST_URL      Enables real per-IP daily/weekly limit enforcement
//   UPSTASH_REDIS_REST_TOKEN    (free tier at https://console.upstash.com — REST API, no SDK needed)
//
// The page already enforces 5/day + 15/week client-side via localStorage. That's
// enough for normal use, but anyone can clear localStorage to bypass it. Adding
// the two UPSTASH_* env vars below makes this function enforce the same limits
// per IP address server-side too. Without them, the function still works fine —
// it just skips the extra check (fail-open).

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = 'qwen/qwen3.6-27b';
const DAILY_LIMIT = 5;
const WEEKLY_LIMIT = 15;

function getClientIp(req) {
  const xff = req.headers['x-forwarded-for'];
  if (xff) return String(xff).split(',')[0].trim();
  if (req.headers['x-real-ip']) return String(req.headers['x-real-ip']);
  return (req.socket && req.socket.remoteAddress) || 'unknown';
}

// Increments per-IP day/week counters in Upstash Redis via one pipelined REST
// call. Returns null (meaning "skip check") if Upstash isn't configured or
// unreachable, so the function always fails open rather than blocking users
// because of a Redis hiccup.
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
    const dayCount = results && results[0] && Number(results[0].result);
    const weekCount = results && results[2] && Number(results[2].result);
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
    brief:
      'Write a short, vivid, emotionally memorable STORY (characters, conflict, a clear scene) that encodes how the formula/concept works, so a student recalls the formula by recalling the story.'
  },
  analogy: {
    label: 'Real-Life Analogy',
    sections: ['THE FORMULA', 'THE ANALOGY', 'THE CONNECTION', 'HOW TO USE IT', 'EXAM TIP'],
    brief:
      'Explain the formula/concept using one strong, everyday REAL-LIFE ANALOGY (something an Indian student sees daily — markets, cricket, trains, cooking, traffic, etc.) and map each part of the formula to a part of the analogy.'
  },
  trick: {
    label: 'Memory Trick',
    sections: ['THE FORMULA', 'THE MEMORY TRICK', 'VISUALIZATION', 'QUICK CHECK', 'COMMON MISCONCEPTION', 'PRACTICE IT'],
    brief:
      'Give a punchy MNEMONIC / MEMORY TRICK (acronym, rhyme, or word-association) to instantly recall the formula, plus a quick mental visualization and a tiny self-check question.'
  }
};

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed. Use POST.' });
    return;
  }

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) {
    res.status(500).json({
      error:
        'Server is missing GROQ_API_KEY. Add it in your Vercel project under Settings → Environment Variables, then redeploy.'
    });
    return;
  }

  let body = req.body;
  if (typeof body === 'string') {
    try {
      body = JSON.parse(body);
    } catch {
      body = {};
    }
  }
  const topic = (body && body.topic ? String(body.topic) : '').trim().slice(0, 200);
  const modeKey = body && MODE_CONFIG[body.mode] ? body.mode : 'story';

  if (!topic) {
    res.status(400).json({ error: 'Please provide a topic or formula.' });
    return;
  }

  const ip = getClientIp(req);
  const usage = await checkServerRateLimit(ip);
  if (usage) {
    if (usage.dayCount > DAILY_LIMIT) {
      res.status(429).json({
        error: `Daily limit reached (${DAILY_LIMIT}/day). Browse the ready-made formula library instead, or try again tomorrow.`
      });
      return;
    }
    if (usage.weekCount > WEEKLY_LIMIT) {
      res.status(429).json({
        error: `Weekly limit reached (${WEEKLY_LIMIT}/week). Browse the ready-made formula library instead, or try again next week.`
      });
      return;
    }
  }

  const config = MODE_CONFIG[modeKey];

  const systemPrompt = `You are Formula Story Mode, an AI study aid built for Indian competitive exam students (SSC, CUET, Banking, JEE/NEET, UPSC). Given a formula, theorem, or concept from Physics, Chemistry, Maths, or Biology, you produce a short, exam-relevant explanation that students will actually remember.

Rules:
- Output PLAIN TEXT only — no Markdown symbols (#, *, **, _ , backticks), no numbered lists, no emojis.
- Structure the output using EXACTLY these section headers, each in capital letters on its own line, in this order: ${config.sections.join(', ')}.
- Under "THE FORMULA", write only the formula itself on the line(s) directly below the header (symbols and short variable names, nothing else).
- Keep the whole response under 280 words. Be concrete and specific to the topic given — never generic filler.
- Tone: clear, encouraging, exam-focused, written for a student preparing under time pressure.
- ${config.brief}`;

  const userPrompt = `Topic / formula: ${topic}\nMode: ${config.label}`;

  try {
    const groqRes = await fetch(GROQ_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: MODEL,
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt }
        ],
        temperature: 0.7,
        max_completion_tokens: 1200,
        reasoning_effort: 'none'
      })
    });

    const data = await groqRes.json().catch(() => ({}));

    if (!groqRes.ok) {
      const message = (data && data.error && data.error.message) || 'Groq API request failed.';
      res.status(groqRes.status).json({ error: message });
      return;
    }

    const text = data && data.choices && data.choices[0] && data.choices[0].message
      ? String(data.choices[0].message.content || '').trim()
      : '';

    if (!text) {
      res.status(502).json({ error: 'Empty response from AI. Please try again.' });
      return;
    }

    res.status(200).json({ text });
  } catch (err) {
    res.status(500).json({ error: 'Failed to reach Groq API. Please try again in a moment.' });
  }
};
