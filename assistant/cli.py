"""Ask doubts from the terminal.  Run:  python -m assistant.cli"""
from datetime import datetime

from . import curriculum, profile, tutor
from .llm import LLMError


def choose(prompt: str, options: list[str]) -> str:
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        pick = input(f"{prompt} (1-{len(options)}): ").strip()
        if pick.isdigit() and 1 <= int(pick) <= len(options):
            return options[int(pick) - 1]


def setup() -> profile.Student:
    saved = profile.all_students()
    if saved:
        print("Saved students:", ", ".join(saved))
        name = input("Your name (or a saved one): ").strip()
        existing = profile.load(profile.Student(name, 6, "").id)
        if existing:
            return existing
    else:
        name = input("Your name: ").strip()
    grade = int(choose("Grade", [str(g) for g in curriculum.grades()]))
    board = choose("Board", curriculum.boards())
    s = profile.Student(name=name or "Student", grade=grade, board=board,
                        subjects=curriculum.subjects(board, grade))
    profile.save(s)
    return s


def main():
    print("Show Your Working — ask a doubt (type 'quit' to leave)\n")
    student = setup()
    subject = choose("Subject", student.subjects)
    names = [t["name"] for t in curriculum.topics(student.board, student.grade, subject)]
    topic = choose("Topic", names + ["Not sure / something else"]) if names else "General"
    intro = (f"Student: grade {student.grade}, {student.board}. Subject: {curriculum.subject_name(subject)}. "
             f"Topic: {topic}. Clear their doubt by teaching the idea in under 140 words. "
             "If they send a homework question, guide them without giving the final answer.")
    turns = []
    while True:
        q = input("\nYour doubt: ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        if not q:
            continue
        turns.append({"role": "user", "content": q})
        try:
            res = tutor.handle({"messages": [{"role": "user", "content": intro}] + turns}, "cli")
        except LLMError as e:
            print("  ⚠", e.message)
            turns.pop()
            continue
        print("\n" + res["text"])
        turns.append({"role": "assistant", "content": res["text"]})
        student.doubts.insert(0, {"q": q, "a": res["text"], "topic": topic, "at": datetime.now().isoformat()})
        profile.save(student)


if __name__ == "__main__":
    main()
