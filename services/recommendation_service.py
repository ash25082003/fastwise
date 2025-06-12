#services/recommendation_service.py
import logging
from typing import Optional, List, Dict, Any

from core.database import DatabaseManager
from repositories.student_repository import StudentRepository
from repositories.question_repository import QuestionRepository
from models.question import Question
from core.exceptions import StudentNotFoundError

logger = logging.getLogger(__name__)

class RecommendationService:
    """Service for generating personalized question recommendations."""
    
    def __init__(
        self, 
        db_manager: DatabaseManager,
        student_repo: StudentRepository,
        question_repo: QuestionRepository
    ):
        self.db_manager = db_manager
        self.student_repo = student_repo
        self.question_repo = question_repo

    def get_next_recommended_question(self, student_id: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get the next recommended question for a student based on their progress.
        """
        logger.info(f"Generating recommendation for student: {student_id}")
        
        # Verify student exists
        student = self.student_repo.find_student_by_id(student_id)
        if not student:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")

        # Get unmastered questions ordered by curriculum sequence
        questions = self.question_repo.find_unmastered_questions_for_student(
            student_id, limit=20
        )
        
        if not questions:
            logger.info(f"No new questions available for student {student_id}")
            return None

        # Apply recommendation logic (currently just returns first question)
        recommended = self._apply_recommendation_logic(questions, student)
        return recommended[0] if recommended else None

    def get_questions_by_concept(
        self, 
        student_id: str, 
        concept_name: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get questions related to a specific concept that the student hasn't mastered.
        """
        logger.info(f"Finding questions for concept '{concept_name}' for student '{student_id}'")
        
        # Verify student exists
        student = self.student_repo.find_student_by_id(student_id)
        if not student:
            raise StudentNotFoundError(f"Student with ID {student_id} not found")

        return self.question_repo.find_questions_by_concept_for_student(
            student_id, concept_name, limit
        )

    def complete_question(self, student_id: str, question_id: str, is_mastered: bool = True) -> None:
        """
        Mark a question as completed by a student.
        Updates both attempt and mastery status if specified.
        """
        logger.info(f"Recording completion of question {question_id} by student {student_id}")
        
        def complete_question_transaction(tx, student_id: str, question_id: str, is_mastered: bool):
            # Always mark as attempted
            self.student_repo.mark_question_as_attempted(student_id, question_id)
            
            if is_mastered:
                # Mark question as mastered
                self.student_repo.mark_question_as_mastered(student_id, question_id)
                # Mark related subconcepts as mastered
                self.student_repo.mark_subconcepts_as_mastered(student_id, question_id)

        self.db_manager.execute_transaction(
            complete_question_transaction, 
            student_id, 
            question_id, 
            is_mastered
        )

    def _apply_recommendation_logic(
        self, 
        questions: List[Dict[str, Any]], 
        student
    ) -> List[Dict[str, Any]]:
        """
        Apply recommendation algorithm to rank questions.
        Currently implements basic sequential ordering.
        """
        # Basic implementation: return questions in curriculum order
        # TODO: Implement more sophisticated recommendation logic
        # - Difficulty matching based on student performance
        # - Concept prerequisite checking
        # - Learning path optimization
        
        return questions