# Formula Story Mode — ThunderStudy

AI tool that turns any formula/topic into a Story, Real-Life Analogy, or Memory Trick.
The frontend is static HTML. The AI call is proxied through a Cloudflare Pages Function
(`functions/api/generate.js`, served at `/api/generate`) so your **Tiny API key stays on the
server and is never exposed in the browser**.

## Files

```
index.html               landing page (/)
app.html                 the app, Formula Story Mode (/app). /home redirects here
hi.html                  Hindi landing page (/hi)
formula.html             formula library hub (/formula)
formula/<slug>.html      one page per formula (/formula/ohms-law ...)
physics-formulas.html, chemistry-formulas.html, maths-formulas.html, biology-formulas.html
how-it-works.html, examples.html, about.html, faq.html, new.html (changelog)
status.html              live status (noindex), offline.html, 404.html
functions/api/generate.js  Pages Function that calls the Tiny model  ->  /api/generate (GET = health check)
_build/formulas.json     the formula data   _build/build.py   page generator
sw.js, manifest.json, icons/, assets/og-image.png   PWA + sharing image
robots.txt, sitemap.xml, llms.txt, llms-full.txt, humans.txt, ads.txt, .well-known/security.txt
_headers, _redirects, _routes.json   Cloudflare Pages config
indexnow-submit.sh       notify search engines of new URLs
.dev.vars.example        template for local testing
```

## Add or edit formula pages
1. Add an entry to `_build/formulas.json` (copy an existing one).
2. Run `python3 _build/build.py` from the project root. It rebuilds the library pages, the sitemap and the llms files.
3. Commit, push, then run `./indexnow-submit.sh`.
The header, footer and styles of generated pages are copied from `about.html`.


## Deploy to Cloudflare Pages

1. Push this folder to a GitHub repo (keep the folder structure; `functions/` must stay at the
   project root).
2. In the Cloudflare dashboard go to **Workers & Pages → Create → Pages → Connect to Git** and pick the repo.
3. Build settings: framework preset **None**, build command empty, output directory `/` (the
   project root).
4. Open **Settings → Variables and Secrets** and add `TINY_API_KEY` (your Tiny model key; the old name `GROQ_API_KEY` still works) as a Secret. Add it for Production, and for Preview if you use it.
5. Redeploy. Add your custom domain `formula.thunderstudy.indevs.in` under **Custom domains**.

## Local testing (optional)
```bash
cp .dev.vars.example .dev.vars   # then fill in your real key
npx wrangler pages dev .
```
This serves the static pages and the `/api/generate` function locally.

## How it works
- The page posts `{ topic, mode }` to `/api/generate`.
- `functions/api/generate.js` builds a prompt per mode (story / analogy / trick), calls the Tiny model's
  OpenAI-compatible Chat Completions endpoint with `TINY_API_KEY` from the Pages environment,
  and returns `{ text }` to the page.
- If `TINY_API_KEY` isn't set, the function returns a clear error instead of crashing.

## Usage limits
Generations are capped at **5 per day and 15 per week**, to keep this sustainable on a free Tiny model tier.
- Enforced client-side (localStorage) by default, no extra setup.
- Optionally enforced server-side per IP: set `UPSTASH_REDIS_REST_URL` and
  `UPSTASH_REDIS_REST_TOKEN` (free Redis at https://console.upstash.com) so the limit can't be
  bypassed by clearing localStorage. If these aren't set, the function skips the extra check
  (fail-open).
- A "Browse Library" card on the page links to https://thunderstudy.indevs.in/formula, with
  ready-made formula stories for PCMB Class 11 & 12, JEE, NEET, SSC, NTA and Banking subjects.

## Model
The function tries Tiny models in order and falls back automatically if one is unavailable or
rate-limited: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `llama-3.3-70b-versatile`,
`llama-3.1-8b-instant` (see `TINY_MODELS` in `functions/api/generate.js`).


## Tiny states and images
The app shows Tiny charging while a story is generated, and Tiny sleeping when something fails. The home pages show Tiny waving in a "Powered by Tiny model" section (links to https://tiny.wondermayank.in). Images are WebP files in `images/tiny/` (`tiny-charging.webp`, `tiny-sleep.webp`, `tiny-wave.webp`). Shared UI styles live in `assets/formula-ui.css`.
