"""Show Your Working — a study tutor for Grades 6 to 10.

assistant.config      reads settings from .env
assistant.llm         talks to Claude (the API key lives only here, on the server)
assistant.tutor       safety rules, cleaning requests, per-student limits
assistant.curriculum  boards, grades, subjects and official syllabus topics
assistant.profile     student profiles saved in the students/ folder (CLI)
assistant.web         the web server that hosts the app for everyone
assistant.cli         a terminal version for asking doubts
"""
__version__ = "1.0.0"
