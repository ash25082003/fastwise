#models/question.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SolutionApproach:
    name: str
    explanation: str

@dataclass
class Question:
    id: str
    title: str
    content: str
    difficulty: str
    step_number: int
    sub_step_number: int
    sequence_number: int
    standard_concepts: List[str]
    sub_concepts: List[str]
    solution_approaches: List[SolutionApproach]

    @property
    def display_order(self) -> tuple:
        """Return tuple for sorting questions in display order."""
        return (self.step_number, self.sub_step_number, self.sequence_number)