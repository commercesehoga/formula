# Formula Story Mode — ThunderStudy

AI tool that turns any formula/topic into a Story, Real-Life Analogy, or Memory Trick.
The frontend is static HTML. The AI call is proxied through a Cloudflare Pages Function
(`functions/api/generate.js`, served at `/api/generate`) so your **Groq API key stays on the
server and is never exposed in the browser**.

## Files

```
index.html               landing page (/)
home.html                the app, Formula Story Mode (/home)
about.html, faq.html, new.html (changelog), offline.html, 404.html
functions/api/generate.js  Pages Function that calls Groq  ->  /api/generate
sw.js, manifest.json, icons/, assets/og-image.png   PWA + sharing image
robots.txt, sitemap.xml, llms.txt, llms-full.txt, humans.txt, ads.txt, .well-known/security.txt
_redirects               Cloudflare Pages redirects
indexnow-submit.sh       notify search engines of new URLs
.dev.vars.example        template for local testing
```

`vercel.json` is a leftover from the old Vercel setup and is ignored by Cloudflare Pages.
It is safe to delete.

## Deploy to Cloudflare Pages

1. Push this folder to a GitHub repo (keep the folder structure; `functions/` must stay at the
   project root).
2. In the Cloudflare dashboard go to **Workers & Pages → Create → Pages → Connect to Git** and pick the repo.
3. Build settings: framework preset **None**, build command empty, output directory `/` (the
   project root).
4. Open **Settings → Variables and Secrets** and add `GROQ_API_KEY` (your key from
   https://console.groq.com/keys) as a Secret. Add it for Production, and for Preview if you use it.
5. Redeploy. Add your custom domain `formula.thunderstudy.indevs.in` under **Custom domains**.

## Local testing (optional)
```bash
cp .dev.vars.example .dev.vars   # then fill in your real key
npx wrangler pages dev .
```
This serves the static pages and the `/api/generate` function locally.

## How it works
- The page posts `{ topic, mode }` to `/api/generate`.
- `functions/api/generate.js` builds a prompt per mode (story / analogy / trick), calls Groq's
  OpenAI-compatible Chat Completions endpoint with `GROQ_API_KEY` from the Pages environment,
  and returns `{ text }` to the page.
- If `GROQ_API_KEY` isn't set, the function returns a clear error instead of crashing.

## Usage limits
Generations are capped at **5 per day and 15 per week**, to keep this sustainable on a free Groq tier.
- Enforced client-side (localStorage) by default, no extra setup.
- Optionally enforced server-side per IP: set `UPSTASH_REDIS_REST_URL` and
  `UPSTASH_REDIS_REST_TOKEN` (free Redis at https://console.upstash.com) so the limit can't be
  bypassed by clearing localStorage. If these aren't set, the function skips the extra check
  (fail-open).
- A "Browse Library" card on the page links to https://thunderstudy.indevs.in/formula, with
  ready-made formula stories for PCMB Class 11 & 12, JEE, NEET, SSC, NTA and Banking subjects.

## Model
The function tries Groq models in order and falls back automatically if one is unavailable or
rate-limited: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `llama-3.3-70b-versatile`,
`llama-3.1-8b-instant` (see `GROQ_MODELS` in `functions/api/generate.js`).
