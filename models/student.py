#models/student.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Student:
    student_id: str
    name: str
    email: str
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    mastered_questions: List[str] = None
    attempted_questions: List[str] = None

    def __post_init__(self):
        if self.mastered_questions is None:
            self.mastered_questions = []
        if self.attempted_questions is None:
            self.attempted_questions = []