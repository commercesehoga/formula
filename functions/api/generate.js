// /functions/api/generate.js  ->  served at  /api/generate
// Cloudflare Pages Function — calls Groq's OpenAI-compatible Chat Completions API.
//
// Required environment variable (Cloudflare dashboard → Workers & Pages → your project
// → Settings → Variables and Secrets; add it as a Secret, then redeploy):
//   GROQ_API_KEY    Your Groq API key from https://console.groq.com/keys
//
// Optional:
//   GROQ_MODEL                  Ignored; models are tried in order from GROQ_MODELS below
//   UPSTASH_REDIS_REST_URL      Enables real per-IP daily/weekly limit enforcement
//   UPSTASH_REDIS_REST_TOKEN    (free tier at https://console.upstash.com — REST API, no SDK needed)
//
// The page already enforces 5/day + 15/week client-side via localStorage. That's
// enough for normal use, but anyone can clear localStorage to bypass it. Adding
// the two UPSTASH_* env vars below makes this function enforce the same limits
// per IP address server-side too. Without them, the function still works fine —
// it just skips the extra check (fail-open).

const GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions';

// Ordered fallback chain — tried top to bottom. If Groq closes/decommissions a model,
// or one is rate-limited / erroring / returns nothing, the next one is used automatically.
// gpt-oss models are reasoning models: max_completion_tokens also has to cover their
// thinking, so they get +800 headroom and reasoning_effort 'low'. Llama models reject
// reasoning_effort, so extras are per-model.
const GROQ_MODELS = [
  { id: 'openai/gpt-oss-120b',     extraTokens: 800, extra: { reasoning_effort: 'low' } },
  { id: 'openai/gpt-oss-20b',      extraTokens: 800, extra: { reasoning_effort: 'low' } },
  { id: 'llama-3.3-70b-versatile', extraTokens: 0,   extra: {} }, // being closed by Groq — last-resort only
  { id: 'llama-3.1-8b-instant',    extraTokens: 0,   extra: {} }
];
const deadModels = new Set(); // models Groq reported as gone; skipped for the life of this warm instance
const DAILY_LIMIT = 5;
const WEEKLY_LIMIT = 15;

function getClientIp(request) {
  const cf = request.headers.get('cf-connecting-ip');
  if (cf) return cf.trim();
  const xff = request.headers.get('x-forwarded-for');
  if (xff) return String(xff).split(',')[0].trim();
  return 'unknown';
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' }
  });
}

// Increments per-IP day/week counters in Upstash Redis via one pipelined REST
// call. Returns null (meaning "skip check") if Upstash isn't configured or
// unreachable, so the function always fails open rather than blocking users
// because of a Redis hiccup.
async function checkServerRateLimit(ip, env) {
  const url = env.UPSTASH_REDIS_REST_URL;
  const token = env.UPSTASH_REDIS_REST_TOKEN;
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

export async function onRequest(context) {
  const { request, env } = context;

  if (request.method !== 'POST') {
    return json({ error: 'Method not allowed. Use POST.' }, 405);
  }

  const apiKey = env.GROQ_API_KEY;
  if (!apiKey) {
    return json({
      error:
        'Server is missing GROQ_API_KEY. Add it in your Cloudflare Pages project under Settings → Variables and Secrets, then redeploy.'
    }, 500);
  }

  let body = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  const topic = (body && body.topic ? String(body.topic) : '').trim().slice(0, 200);
  const modeKey = body && MODE_CONFIG[body.mode] ? body.mode : 'story';

  if (!topic) {
    return json({ error: 'Please provide a topic or formula.' }, 400);
  }

  const ip = getClientIp(request);
  const usage = await checkServerRateLimit(ip, env);
  if (usage) {
    if (usage.dayCount > DAILY_LIMIT) {
      return json({
        error: `Daily limit reached (${DAILY_LIMIT}/day). Browse the ready-made formula library instead, or try again tomorrow.`
      }, 429);
    }
    if (usage.weekCount > WEEKLY_LIMIT) {
      return json({
        error: `Weekly limit reached (${WEEKLY_LIMIT}/week). Browse the ready-made formula library instead, or try again next week.`
      }, 429);
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
    // Walk the model chain. Ends with `text` set (success), or `groqRes`/`data` holding the
    // last failed response, which the error handling below turns into a message.
    let groqRes = null;
    let data = {};
    let text = '';
    let lastNetworkErr = null;

    for (const model of GROQ_MODELS) {
      if (deadModels.has(model.id)) continue;

      try {
        groqRes = await fetch(GROQ_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${apiKey}`
          },
          signal: AbortSignal.timeout(15000),
          body: JSON.stringify({
            model: model.id,
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: userPrompt }
            ],
            temperature: 0.7,
            max_completion_tokens: 1200 + model.extraTokens,
            ...model.extra
          })
        });
      } catch (netErr) {
        console.warn(`Groq network error/timeout on ${model.id}, trying next model:`, netErr.message);
        lastNetworkErr = netErr;
        groqRes = null;
        continue;
      }

      data = await groqRes.json().catch(() => ({}));

      if (groqRes.ok) {
        text = data && data.choices && data.choices[0] && data.choices[0].message
          ? String(data.choices[0].message.content || '').trim()
          : '';
        if (text) break;
        console.warn(`Empty response from ${model.id}, trying next model`);
        continue;
      }

      const errMsg = (data && data.error && data.error.message) || '';
      console.error(`Groq error on ${model.id}:`, groqRes.status, errMsg);

      // A bad/forbidden key fails identically on every model — don't burn the chain.
      if (groqRes.status === 401 || groqRes.status === 403) break;

      // Model closed / decommissioned → never try it again on this instance.
      if (groqRes.status === 404 || /decommission|deprecat|does not exist|not found/i.test(errMsg)) {
        deadModels.add(model.id);
      }
      // Anything else (429, 413 TPM, 5xx, …) → next model. Each model has its own rate-limit bucket.
    }
    if (!groqRes) throw lastNetworkErr || new Error('No Groq model available');

    if (!groqRes.ok) {
      const message = (data && data.error && data.error.message) || 'Groq API request failed.';
      return json({ error: message }, groqRes.status);
    }

    if (!text) {
      return json({ error: 'Empty response from AI. Please try again.' }, 502);
    }

    return json({ text }, 200);
  } catch (err) {
    return json({ error: 'Failed to reach Groq API. Please try again in a moment.' }, 500);
  }
}
