# Show Your Working — student learning assistant

A study tutor for Grades 6–10: set practice papers on the official syllabus,
get them marked, and ask doubts. Anyone with the link can use it — no account
needed. Answers come from Google Gemini through **your** API key, which stays on the server.

```
student-learning-assistant/
├── app.py              Vercel entrypoint: the app + /api/tutor + /api/health
├── assistant/
│   ├── __init__.py
│   ├── cli.py          ask doubts in the terminal
│   ├── config.py       reads settings from .env / environment
│   ├── curriculum.py   boards, grades, official syllabus topics
│   ├── llm.py          the only file that talks to Gemini
│   ├── profile.py      student profiles for the terminal version
│   ├── tutor.py        safety rules + per-student limits
│   └── web.py          the API logic + a local web server
├── data/syllabus.json  official topics (NCERT, Cambridge IGCSE, Lower Secondary)
├── public/index.html   the app (Vercel serves this at /)
├── students/           terminal profiles (not uploaded)
├── tests/
├── .vercelignore
├── .env.example
├── .gitignore
└── README.md
```

## Put it online with Vercel
1. Go to **vercel.com**, sign in with GitHub, click **Add New → Project** and import this repo.
2. Vercel detects Python and finds `app.py` by itself. Leave the build settings empty.
3. Open **Environment Variables** and add `GEMINI_API_KEY` = your key from **aistudio.google.com → Get API key**.
4. Click **Deploy**. Share the address Vercel gives you, e.g. `https://student-learning-assistant-7.vercel.app`.

Check it: open `/api/health` on your address — it should say `"key_set": true`.
Added or changed the key later? Go to **Deployments → ⋯ → Redeploy** so it takes effect.

## Run it on your computer (VS Code)
1. Copy `.env.example` to `.env` and paste your key after `GEMINI_API_KEY=`.
2. In the terminal: `python -m assistant.web`, then open **http://127.0.0.1:8000**.
   The terminal tests Gemini at start-up and tells you exactly what to fix if it is not working.

Terminal version: `python -m assistant.cli`  
Tests: `python -m unittest`

## Good to know
- **Cost:** Gemini has a free tier with daily limits. If you turn on billing for more use, set a budget in Google Cloud so costs stay capped.
- **Models:** `gemini-3.8-flash` for papers and doubts, `gemini-3.5-flash-lite` for quick jobs. Change `MODEL` / `QUICK_MODEL` in Vercel or `.env`.
- **Limits:** each student can make about 40 requests an hour (`PER_STUDENT_PER_HOUR`). On Vercel this is counted per server copy, so the spend limit is your real safety net.
- **Safety:** every request tells Gemini its users are school students and keeps it to studying.
  Read Google's Gemini API terms before sharing widely — apps used by under-18s need extra care, and you are responsible for them.
- **Progress** in the web app is saved in each student's own browser.
- **Your key** lives only in `.env` (never uploaded — it is in `.gitignore`) and in Vercel's settings.
