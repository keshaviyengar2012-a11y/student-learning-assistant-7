"""Boards, grades, subjects and the official syllabus topics (data/syllabus.json)."""
from __future__ import annotations

import json
from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def _data() -> dict:
    return json.loads((config.DATA_DIR / "syllabus.json").read_text(encoding="utf-8"))


def boards() -> list[str]:
    return _data()["boards"]


def grades() -> list[int]:
    return _data()["grades"]


def subject_name(subject_id: str) -> str:
    return next((s["name"] for s in _data()["subjects"] if s["id"] == subject_id), subject_id)


def syllabus(board: str, grade: int) -> dict | None:
    """The official syllabus for this board and grade, or None if there is none built in."""
    return next((s for s in _data()["syllabuses"] if s["board"] == board and s["grade"] == int(grade)), None)


def subjects(board: str, grade: int) -> list[str]:
    syl = syllabus(board, grade)
    if syl:
        return list(syl["subjects"].keys())
    ids = [s["id"] for s in _data()["subjects"]]
    return ids if int(grade) >= 9 else [i for i in ids if i != "advmath"]


def topics(board: str, grade: int, subject_id: str) -> list[dict]:
    syl = syllabus(board, grade)
    return list(syl["subjects"].get(subject_id, [])) if syl else []
