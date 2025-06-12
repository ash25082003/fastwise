# repositories/setup_repository.py
import logging
from typing import Dict, Any, List

from .base_repository import BaseRepository
from core.exceptions import DataValidationError

from neo4j import Transaction

logger = logging.getLogger(__name__)

class SetupRepository(BaseRepository):
    """Repository for database schema setup and data population."""

    def create_constraints_and_indexes(self) -> None:
        """
        Create all necessary constraints and indexes for optimal performance.
        """
        logger.info("Setting up database constraints and indexes...")
        
        constraints_and_indexes = [
            # Unique constraints
            "CREATE CONSTRAINT student_id_unique IF NOT EXISTS FOR (s:Student) REQUIRE s.student_id IS UNIQUE",
            "CREATE CONSTRAINT question_id_unique IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE",
            "CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT subconcept_name_unique IF NOT EXISTS FOR (sc:SubConcept) REQUIRE sc.name IS UNIQUE",
            "CREATE CONSTRAINT solution_approach_name_unique IF NOT EXISTS FOR (sa:solution_approach) REQUIRE sa.name IS UNIQUE",
            
            # Performance indexes
            "CREATE INDEX student_id_index IF NOT EXISTS FOR (s:Student) ON (s.student_id)",
            "CREATE INDEX question_id_index IF NOT EXISTS FOR (q:Question) ON (q.id)",
            "CREATE INDEX concept_name_index IF NOT EXISTS FOR (c:Concept) ON (c.name)",
            "CREATE INDEX question_difficulty_index IF NOT EXISTS FOR (q:Question) ON (q.difficulty)",
            "CREATE INDEX question_step_index IF NOT EXISTS FOR (q:Question) ON (q.step_number, q.sub_step_number, q.sequence_number)",
            "CREATE INDEX student_last_active_index IF NOT EXISTS FOR (s:Student) ON (s.last_active)",
        ]
        
        for query in constraints_and_indexes:
            try:
                self.execute_write_query(query)
                logger.info(f"Successfully executed: {query[:50]}...")
            except Exception as e:
                logger.warning(f"Could not execute setup query: {e}")

    def populate_question_and_concepts_transaction(self, tx: Transaction, item: Dict[str, Any]) -> None:
        """
        Transaction function to create a question and its related concepts.
        This method is designed to be used with execute_transaction.
        
        Args:
            tx: Neo4j transaction object
            item: Dictionary containing question data
        """
        try:
            self._validate_question_data(item)
            
            # Create the main question node
            self._create_question_node(tx, item)
            
            # Create and link standard concepts
            self._create_standard_concepts(tx, item)
            
            # Create and link subconcepts
            self._create_subconcepts(tx, item)
            
            # Create solution approaches
            self._create_solution_approaches(tx, item)
            
            logger.debug(f"Successfully populated question: {item['id']}")
            
        except Exception as e:
            logger.error(f"Failed to populate question {item.get('id', 'N/A')}: {e}")
            raise
        
    def _validate_question_data(self, item: Dict[str, Any]) -> None:
        """
        Validate that the question data contains all required fields.
        """
        required_fields = ['id', 'question_title', 'question', 'difficulty', 
                          'step_no', 'sub_step_no', 'sl_no']
        
        missing_fields = [field for field in required_fields if field not in item]
        if missing_fields:
            raise DataValidationError(f"Missing required fields: {missing_fields}")


    def _create_question_node(self, tx: Transaction, item: Dict[str, Any]) -> None:
        """Create the main question node."""
        query = """
        MERGE (q:Question {id: $id})
        SET q.question_title = $question_title,
            q.question = $question,
            q.difficulty = $difficulty,
            q.step_number = $step_no,
            q.sub_step_number = $sub_step_no,
            q.sequence_number = $sl_no,
            q.created_at = datetime(),
            q.updated_at = datetime()
        """
        
        parameters = {
            'id': item['id'],
            'question_title': item['question_title'],
            'question': item['question'],
            'difficulty': item['difficulty'],
            'step_no': item['step_no'],
            'sub_step_no': item['sub_step_no'],
            'sl_no': item['sl_no']
        }
        
        tx.run(query, parameters)
        logger.debug(f"Created question node: {item['id']}")

    def _create_standard_concepts(self, tx: Transaction, item: Dict[str, Any]) -> None:
        """Create and link standard concepts to the question."""
        concepts = item.get('sub_concepts', [])
        if not concepts:
            return
            
        for concept_name in concepts:
            if concept_name and concept_name.strip():
                # Create concept if it doesn't exist
                concept_query = """
                MERGE (c:Concept {name: $concept_name})
                SET c.created_at = coalesce(c.created_at, datetime()),
                    c.updated_at = datetime()
                """
                tx.run(concept_query, {'concept_name': concept_name.strip()})
                
                # Link question to concept
                link_query = """
                MATCH (q:Question {id: $question_id})
                MATCH (c:Concept {name: $concept_name})
                MERGE (q)-[:INVOLVES_CONCEPT]->(c)
                """
                tx.run(link_query, {
                    'question_id': item['id'],
                    'concept_name': concept_name.strip()
                })
                
        logger.debug(f"Created {len(concepts)} concept links for question: {item['id']}")

    def _create_subconcepts(self, tx: Transaction, item: Dict[str, Any]) -> None:
        """Create and link subconcepts to the question."""
        subconcepts = item.get('sub_concepts', [])
        if not subconcepts:
            return
            
        for subconcept_name in subconcepts:
            if subconcept_name and subconcept_name.strip():
                # Create subconcept if it doesn't exist
                subconcept_query = """
                MERGE (sc:SubConcept {name: $subconcept_name})
                SET sc.created_at = coalesce(sc.created_at, datetime()),
                    sc.updated_at = datetime()
                """
                tx.run(subconcept_query, {'subconcept_name': subconcept_name.strip()})
                
                # Link question to subconcept
                link_query = """
                MATCH (q:Question {id: $question_id})
                MATCH (sc:SubConcept {name: $subconcept_name})
                MERGE (q)-[:INVOLVES_SUBCONCEPT]->(sc)
                """
                tx.run(link_query, {
                    'question_id': item['id'],
                    'subconcept_name': subconcept_name.strip()
                })
                
        logger.debug(f"Created {len(subconcepts)} subconcept links for question: {item['id']}")

    def _create_solution_approaches(self, tx: Transaction, item: Dict[str, Any]) -> None:
        """Create and link solution approaches to the question."""
        approaches = item.get('solution_approaches', [])
        if not approaches:
            return

        for approach in approaches:
            approach_name = approach.get('approach_name', '').strip()
            explanation = approach.get('explanation', '').strip()

            if approach_name:
                # Create or update the SolutionApproach node with name and explanation
                approach_query = """
                MERGE (sa:SolutionApproach {name: $approach_name})
                SET sa.explanation = $explanation,
                    sa.created_at = coalesce(sa.created_at, datetime()),
                    sa.updated_at = datetime()
                """
                tx.run(approach_query, {
                    'approach_name': approach_name,
                    'explanation': explanation
                })

                # Link the question to the solution approach
                link_query = """
                MATCH (q:Question {id: $question_id})
                MATCH (sa:SolutionApproach {name: $approach_name})
                MERGE (q)-[:HAS_SOLUTION_APPROACH]->(sa)
                """
                tx.run(link_query, {
                    'question_id': item['id'],
                    'approach_name': approach_name
                })

        logger.debug(f"Created {len(approaches)} solution approach links for question: {item['id']}")

    def _validate_data_items(self, data: List[Dict[str, Any]], validate_only: bool = False) -> Dict[str, Any]:
        """
        Validate a list of data items and return validation results.
        
        Args:
            data: List of data items to validate
            validate_only: If True, only validate structure without processing
            
        Returns:
            Dictionary containing validation results
        """
        valid_items = []
        invalid_items = []
        invalid_item_ids = []
        
        for item in data:
            try:
                self._validate_question_data(item)
                valid_items.append(item)
            except DataValidationError as e:
                invalid_items.append(item)
                invalid_item_ids.append(item.get('id', 'N/A'))
                logger.warning(f"Invalid item {item.get('id', 'N/A')}: {e}")
        
        return {
            'valid_items': valid_items,
            'invalid_items': invalid_items,
            'invalid_item_ids': invalid_item_ids
        }

    def clear_all_data(self) -> None:
        """
        Clear all data from the database. Use with caution!
        """
        logger.warning("Clearing all data from the database...")
        
        clear_queries = [
            "MATCH (n) DETACH DELETE n",  # Delete all nodes and relationships
        ]
        
        for query in clear_queries:
            self.execute_write_query(query)
            
        logger.info("Database cleared successfully")

    def get_database_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the database contents.
        """
        stats_query = """
        MATCH (n)
        WITH labels(n) AS nodeLabels
        UNWIND nodeLabels AS label
        RETURN label, count(*) AS count
        ORDER BY count DESC
        """
        
        relationship_query = """
        MATCH ()-[r]->()
        RETURN type(r) AS relationship_type, count(r) AS count
        ORDER BY count DESC
        """
        
        node_stats = self.execute_query(stats_query)
        relationship_stats = self.execute_query(relationship_query)
        
        return {
            'nodes': {stat['label']: stat['count'] for stat in node_stats},
            'relationships': {stat['relationship_type']: stat['count'] for stat in relationship_stats}
        }