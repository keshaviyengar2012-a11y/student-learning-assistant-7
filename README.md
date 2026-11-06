# Show Your Working — student learning assistant

A study tutor for Grades 6–10: set practice papers on the official syllabus,
get them marked, and ask doubts. Anyone with the link can use it — no Claude
account needed. Claude is reached through **your** API key, which stays on the server.

```
student-learning-assistant/
├── app.py              Vercel entrypoint: the app + /api/claude + /api/health
├── assistant/
│   ├── __init__.py
│   ├── cli.py          ask doubts in the terminal
│   ├── config.py       reads settings from .env / environment
│   ├── curriculum.py   boards, grades, official syllabus topics
│   ├── llm.py          the only file that talks to Claude
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
3. Open **Environment Variables** and add `ANTHROPIC_API_KEY` = your key from console.anthropic.com.
4. Click **Deploy**. Share the address Vercel gives you, e.g. `https://student-learning-assistant-7.vercel.app`.

Check it: open `/api/health` on your address — it should say `"key_set": true`.
Added or changed the key later? Go to **Deployments → ⋯ → Redeploy** so it takes effect.

## Run it on your computer (VS Code)
1. Copy `.env.example` to `.env` and paste your key after `ANTHROPIC_API_KEY=`.
2. In the terminal: `python -m assistant.web`, then open **http://127.0.0.1:8000**.
   The terminal tests Claude at start-up and tells you exactly what to fix if it is not working.

Terminal version: `python -m assistant.cli`  
Tests: `python -m unittest`

## Good to know
- **Cost:** every doubt and paper uses your API credit. Set a monthly spend limit at console.anthropic.com.
- **Limits:** each student can make about 40 requests an hour (`PER_STUDENT_PER_HOUR`). On Vercel this is counted per server copy, so the spend limit is your real safety net.
- **Safety:** every request tells Claude its users are school students and keeps it to studying.
  Read Anthropic's usage policy before sharing widely — apps used by under-18s need extra safeguards.
- **Progress** in the web app is saved in each student's own browser.
- **Your key** lives only in `.env` (never uploaded — it is in `.gitignore`) and in Vercel's settings.
