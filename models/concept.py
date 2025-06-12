#models/concept.py
from dataclasses import dataclass
from typing import List

@dataclass
class SubConcept:
    name: str
    parent_concept: str

@dataclass
class Concept:
    name: str
    sub_concepts: List[SubConcept]

    def __post_init__(self):
        if self.sub_concepts is None:
            self.sub_concepts = []