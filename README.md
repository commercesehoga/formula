# Formula Story Mode — ThunderStudy

AI tool that turns any formula/topic into a Story, Real-Life Analogy, or Memory Trick.
The frontend is a single static HTML file. The AI call is proxied through a Vercel
serverless function (`/api/generate.js`) so your **Groq API key stays on the server
and is never exposed in the browser**.

## Files

```
formula-story.html   ← the app (static, no build step)
api/generate.js      ← serverless function that calls Groq
vercel.json          ← routes "/" to formula-story.html
package.json         ← project metadata (no dependencies needed)
.env.example          ← template for local testing
```

## Deploy to Vercel

### Option A — GitHub + Vercel dashboard (recommended)
1. Create a new GitHub repo and push all the files in this folder to it (keep the
   folder structure exactly as is — `api/generate.js` must stay inside an `api/` folder).
2. Go to https://vercel.com/new and import that repo.
3. Before the first deploy (or right after, then redeploy), open
   **Project → Settings → Environment Variables** and add:
   - `GROQ_API_KEY` → your key from https://console.groq.com/keys
   - (optional) `GROQ_MODEL` → e.g. `llama-3.3-70b-versatile`
4. Deploy. Your app will be live at `https://<your-project>.vercel.app/`.

### Option B — Vercel CLI
```bash
npm i -g vercel
cd formula-story-vercel
vercel link
vercel env add GROQ_API_KEY
vercel --prod
```

## Local testing (optional)
```bash
cp .env.example .env   # then fill in your real key
vercel dev
```
This serves both the static HTML and the `/api/generate` function locally.

## How it works
- The page posts `{ topic, mode }` to `/api/generate`.
- `api/generate.js` builds a prompt per mode (story / analogy / trick), calls
  Groq's OpenAI-compatible Chat Completions endpoint with your `GROQ_API_KEY`
  from the server environment, and returns `{ text }` back to the page.
- If `GROQ_API_KEY` isn't set, the function returns a clear error instead of crashing.

## Usage limits
Generations are capped at **5 per day and 15 per week**, to keep this sustainable on a free Groq tier.
- Enforced client-side (localStorage) by default — works out of the box, no extra setup.
- Optionally enforced server-side per IP too: set `UPSTASH_REDIS_REST_URL` and
  `UPSTASH_REDIS_REST_TOKEN` (free Redis at https://console.upstash.com) so the
  limit can't be bypassed by clearing localStorage. If these aren't set, the
  function simply skips the extra check (fail-open) — nothing breaks.
- A "Browse Library" card on the page links to https://thunderstudy.indevs.in/formula
  — ready-made formula stories for PCMB Class 11 & 12, JEE, NEET, SSC, NTA and
  Banking subjects, so common topics don't have to eat into someone's daily quota.

## Changing the model
Groq hosts several fast open models. Set `GROQ_MODEL` in your environment variables
to switch (defaults to `llama-3.3-70b-versatile`). See available models at
https://console.groq.com/docs/models
