# ThunderStudy Formula Story Mode

Vercel-ready Formula Story Mode powered by Groq.

## Deployment
1. Import this folder into Vercel.
2. Add `GROQ_API_KEY` in Project Settings → Environment Variables.
3. Redeploy.
4. Open the deployed domain.

The app uses `llama-3.1-8b-instant` on Groq. The model is fixed in `/api/generate.js` so an old `GROQ_MODEL` environment variable cannot accidentally switch it back.

The frontend calls the Vercel serverless endpoint at `/api/generate`.
