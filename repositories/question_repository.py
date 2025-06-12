# repositories/question_repository.py
from typing import List, Dict, Any, Optional
import logging

from .base_repository import BaseRepository
from models.question import Question, SolutionApproach
from core.exceptions import QuestionNotFoundError

logger = logging.getLogger(__name__)

class QuestionRepository(BaseRepository):
    """Repository for question-related database operations."""

    def find_unmastered_questions_for_student(self, student_id: str, limit: int = 20) -> List[Question]:
        """
        Find questions that the student hasn't mastered yet, ordered by curriculum sequence.
        
        Args:
            student_id: ID of the student
            limit: Maximum number of questions to return
            
        Returns:
            List of question dictionaries
        """
        query = """
        MATCH (q:Question)
        WHERE NOT EXISTS {
            MATCH (s:Student {student_id: $student_id})-[:MASTERED]->(q)
        }
        RETURN q.id as id, q.title as title, q.content as content,
               q.difficulty as difficulty, q.step_number as step_number,
               q.substep_number as sub_step_number, q.sequence_number as sequence_number,
               q.standard_concepts as standard_concepts, q.sub_concepts as sub_concepts,
               q.solution_approaches as solution_approaches
        ORDER BY q.step_number ASC, q.substep_number ASC, q.sequence_number ASC
        LIMIT $limit
        """
        
        parameters = {'student_id': student_id, 'limit': limit}
        logger.info(f"Finding unmastered questions for student {student_id}")
        return self.execute_query(query, parameters)

    def find_questions_by_concept_for_student(
        self, 
        student_id: str, 
        concept_name: str, 
        limit: int = 10
    ) -> List[Question]:
        """
        Find questions related to a specific concept that the student hasn't mastered.
        
        Args:
            student_id: ID of the student
            concept_name: Name of the concept
            limit: Maximum number of questions to return
            
        Returns:
            List of question dictionaries
        """
        query = """
        MATCH (q:Question)
        WHERE (concept_name IN q.standard_concepts OR concept_name IN q.sub_concepts)
        AND NOT EXISTS {
            MATCH (s:Student {student_id: $student_id})-[:MASTERED]->(q)
        }
        RETURN q.id as id, q.title as title, q.content as content,
               q.difficulty as difficulty, q.step_number as step_number,
               q.substep_number as sub_step_number, q.sequence_number as sequence_number,
               q.standard_concepts as standard_concepts, q.sub_concepts as sub_concepts,
               q.solution_approaches as solution_approaches
        ORDER BY q.step_number ASC, q.substep_number ASC, q.sequence_number ASC
        LIMIT $limit
        """
        
        parameters = {
            'student_id': student_id,
            'concept_name': concept_name,
            'limit': limit
        }
        
        logger.info(f"Finding questions for concept '{concept_name}' for student {student_id}")
        return self.execute_query(query, parameters)

    def find_question_by_id(self, question_id: str) -> Optional[Question]:
        """
        Find a question by its ID.
        
        Args:
            question_id: ID of the question
            
        Returns:
            Question object if found, None otherwise
        """
        query = """
        MATCH (q:Question {id: $question_id})
        RETURN q.id as id, q.title as title, q.content as content,
               q.difficulty as difficulty, q.step_number as step_number,
               q.substep_number as sub_step_number, q.sequence_number as sequence_number,
               q.standard_concepts as standard_concepts, q.sub_concepts as sub_concepts,
               q.solution_approaches as solution_approaches
        """
        
        results = self.execute_query(query, {'question_id': question_id})
        
        if not results:
            return None
        
        data = results[0]
        return self._build_question_from_data(data)

    def get_all_questions(self, limit: Optional[int] = None) -> List[Question]:
        """
        Get all questions from the database.
        
        Args:
            limit: Optional limit on number of questions to return
            
        Returns:
            List of Question objects
        """
        query = """
        MATCH (q:Question)
        RETURN q.id as id, q.title as title, q.content as content,
               q.difficulty as difficulty, q.step_number as step_number,
               q.substep_number as sub_step_number, q.sequence_number as sequence_number,
               q.standard_concepts as standard_concepts, q.sub_concepts as sub_concepts,
               q.solution_approaches as solution_approaches
        ORDER BY q.step_number ASC, q.substep_number ASC, q.sequence_number ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        results = self.execute_query(query)
        return [self._build_question_from_data(data) for data in results]

    def create_question(self, question: Question) -> None:
        """
        Create a new question in the database.
        
        Args:
            question: Question object to create
        """
        query = """
        CREATE (q:Question {
            id: $id,
            title: $title,
            content: $content,
            difficulty: $difficulty,
            step_number: $step_number,
            substep_number: $sub_step_number,
            sequence_number: $sequence_number,
            standard_concepts: $standard_concepts,
            sub_concepts: $sub_concepts,
            solution_approaches: $solution_approaches
        })
        """
        
        parameters = {
            'id': question.id,
            'title': question.title,
            'content': question.content,
            'difficulty': question.difficulty,
            'step_number': question.step_number,
            'sub_step_number': question.sub_step_number,
            'sequence_number': question.sequence_number,
            'standard_concepts': question.standard_concepts,
            'sub_concepts': question.sub_concepts,
            'solution_approaches': [
                {'name': approach.name, 'explanation': approach.explanation}
                for approach in question.solution_approaches
            ]
        }
        
        logger.info(f"Creating question: {question.id}")
        self.execute_write_query(query, parameters)

    def _build_question_from_data(self, data: Dict[str, Any]) -> Question:
        """
        Build a Question object from database result data.
        
        Args:
            data: Database result dictionary
            
        Returns:
            Question object
        """
        solution_approaches = []
        if data.get('solution_approaches'):
            for approach_data in data['solution_approaches']:
                if isinstance(approach_data, dict):
                    solution_approaches.append(SolutionApproach(
                        name=approach_data.get('name', ''),
                        explanation=approach_data.get('explanation', '')
                    ))
        
        return Question(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            difficulty=data['difficulty'],
            step_number=data['step_number'],
            sub_step_number=data['sub_step_number'],
            sequence_number=data['sequence_number'],
            standard_concepts=data.get('standard_concepts', []),
            sub_concepts=data.get('sub_concepts', []),
            solution_approaches=solution_approaches
        )