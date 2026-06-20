// /api/generate.js
// Vercel Serverless Function — calls Groq's OpenAI-compatible Chat Completions API.
//
// Required environment variable (set in Vercel → Project → Settings → Environment Variables):
//   GROQ_API_KEY    Your Groq API key from https://console.groq.com/keys
//
// Optional:
//   GROQ_MODEL      Defaults to "llama-3.3-70b-versatile"

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';
const MODEL = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';

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
        temperature: 0.85,
        max_tokens: 900
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
