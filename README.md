# Show Your Working — student learning assistant

A study tutor for Grades 6–10: set practice papers on the official syllabus,
get them marked, and ask doubts. Anyone with the link can use it — no Claude
account needed. Claude is reached through **your** API key, which stays on the server.

```
student-learning-assistant/
├── assistant/
│   ├── __init__.py
│   ├── cli.py          ask doubts in the terminal
│   ├── config.py       reads settings from .env
│   ├── curriculum.py   boards, grades, official syllabus topics
│   ├── llm.py          the only file that talks to Claude
│   ├── profile.py      student profiles for the terminal version
│   ├── tutor.py        safety rules + per-student limits
│   └── web.py          the web server
├── data/syllabus.json  official topics (NCERT, Cambridge IGCSE, Lower Secondary)
├── show your working/index.html   the app
├── students/           terminal profiles (not uploaded)
├── tests/
├── .env.example
├── .gitignore
├── render.yaml
└── README.md
```

## Run it on your computer (VS Code)
1. Get an API key at **console.anthropic.com** (add credit, set a monthly spend limit).
2. Copy `.env.example` to `.env` and paste your key after `ANTHROPIC_API_KEY=`.
3. In the VS Code terminal:
   ```
   python -m assistant.web
   ```
4. Open **http://127.0.0.1:8000**.

Terminal version: `python -m assistant.cli`  
Tests: `python -m unittest`

## Put it online for your friends (Render, free tier)
GitHub Pages cannot run Python, so the code lives on GitHub and Render runs it.
1. Push this folder to GitHub from VS Code (Source Control → Publish to GitHub).
   `.env` is in `.gitignore`, so your key is **not** uploaded — check this before you publish.
2. On **render.com**: New → Blueprint → pick your repo. It reads `render.yaml`.
3. When it asks for `ANTHROPIC_API_KEY`, paste your key. Click Apply.
4. Share the address Render gives you, e.g. `https://show-your-working.onrender.com`.

Check it is working: open `/health` on your address — it should say `"key_set": true`.

## Good to know
- **Cost:** every doubt and paper uses your API credit. Your spend limit caps it.
- **Limits:** each student can make 40 requests an hour (`PER_STUDENT_PER_HOUR`).
- **Safety:** every request tells Claude its users are school students and keeps it to studying.
  Read Anthropic's usage policy before sharing widely — apps used by under-18s need extra safeguards.
- **Progress** in the web app is saved in each student's own browser.
