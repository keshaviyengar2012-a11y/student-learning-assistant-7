"""Student profiles for the terminal version, saved as JSON in students/.
(The web app saves progress in each student's own browser.)"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field

from . import config


@dataclass
class Student:
    name: str
    grade: int
    board: str
    subjects: list[str] = field(default_factory=lambda: ["math"])
    doubts: list[dict] = field(default_factory=list)

    @property
    def id(self) -> str:
        return re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-") or "student"


def path_for(student_id: str):
    return config.STUDENTS_DIR / f"{student_id}.json"


def save(student: Student) -> None:
    config.STUDENTS_DIR.mkdir(exist_ok=True)
    path_for(student.id).write_text(json.dumps(asdict(student), indent=2), encoding="utf-8")


def load(student_id: str) -> Student | None:
    p = path_for(student_id)
    return Student(**json.loads(p.read_text(encoding="utf-8"))) if p.exists() else None


def all_students() -> list[str]:
    return sorted(p.stem for p in config.STUDENTS_DIR.glob("*.json"))
