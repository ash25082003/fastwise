# repositories/student_repository.py
from typing import Optional, List
import logging

from .base_repository import BaseRepository
from models.student import Student
from core.exceptions import StudentNotFoundError

logger = logging.getLogger(__name__)

class StudentRepository(BaseRepository):
    """Repository for student-related database operations."""

    def create_or_update_student(self, student: Student) -> None:
        """Create a new student or update existing one."""
        query = """
        MERGE (s:Student {student_id: $student_id})
        ON CREATE SET 
            s.created_at = datetime(),
            s.name = $name,
            s.email = $email,
            s.last_active = datetime()
        ON MATCH SET
            s.name = $name,
            s.email = $email,
            s.last_active = datetime()
        """
        
        parameters = {
            'student_id': student.student_id,
            'name': student.name,
            'email': student.email
        }
        
        logger.info(f"Creating/updating student: {student.student_id}")
        self.execute_write_query(query, parameters)

    def find_student_by_id(self, student_id: str) -> Optional[Student]:
        """Retrieve student by ID."""
        query = """
        MATCH (s:Student {student_id: $student_id})
        RETURN s.student_id as student_id, s.name as name, s.email as email,
               s.created_at as created_at, s.last_active as last_active
        """
        
        logger.info(f"Finding student by ID: {student_id}")
        results = self.execute_query(query, {'student_id': student_id})
        
        if not results:
            return None
            
        data = results[0]
        return Student(
            student_id=data['student_id'],
            name=data['name'],
            email=data['email'],
            created_at=data.get('created_at'),
            last_active=data.get('last_active')
        )

    def mark_question_as_attempted(self, student_id: str, question_id: str) -> None:
        """Record that a student has attempted a question."""
        query = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (q:Question {id: $question_id})
        MERGE (s)-[r:ATTEMPTED]->(q)
        SET r.timestamp = datetime(), s.last_active = datetime()
        """
        
        parameters = {'student_id': student_id, 'question_id': question_id}
        logger.info(f"Marking question {question_id} as attempted by student {student_id}")
        self.execute_write_query(query, parameters)

    def mark_question_as_mastered(self, student_id: str, question_id: str) -> None:
        """Record that a student has mastered a question."""
        query = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (q:Question {id: $question_id})
        MERGE (s)-[r:MASTERED]->(q)
        SET r.timestamp = datetime(), s.last_active = datetime()
        """
        
        parameters = {'student_id': student_id, 'question_id': question_id}
        logger.info(f"Marking question {question_id} as mastered by student {student_id}")
        self.execute_write_query(query, parameters)

    def mark_subconcepts_as_mastered(self, student_id: str, question_id: str) -> None:
        """Mark all subconcepts of a question as mastered by the student."""
        query = """
        MATCH (s:Student {student_id: $student_id})
        MATCH (q:Question {id: $question_id})
        WITH s, q.sub_concepts AS subconcept_names
        UNWIND subconcept_names AS subconcept_name
        MATCH (sc:SubConcept {name: subconcept_name})
        MERGE (s)-[:MASTERED]->(sc)
        SET s.last_active = datetime()
        """
        
        parameters = {'student_id': student_id, 'question_id': question_id}
        logger.info(f"Marking subconcepts of question {question_id} as mastered by student {student_id}")
        self.execute_write_query(query, parameters)

    def get_student_progress_summary(self, student_id: str) -> dict:
        """Get comprehensive progress summary for a student."""
        query = """
        MATCH (s:Student {student_id: $student_id})
        OPTIONAL MATCH (s)-[:ATTEMPTED]->(attempted:Question)
        OPTIONAL MATCH (s)-[:MASTERED]->(mastered:Question)
        OPTIONAL MATCH (s)-[:MASTERED]->(mastered_concepts:Concept)
        RETURN s.student_id as student_id,
               count(DISTINCT attempted) as attempted_count,
               count(DISTINCT mastered) as mastered_count,
               count(DISTINCT mastered_concepts) as mastered_concepts_count,
               collect(DISTINCT attempted.id) as attempted_questions,
               collect(DISTINCT mastered.id) as mastered_questions
        """
        
        results = self.execute_query(query, {'student_id': student_id})
        return results[0] if results else {}