# main.py
import logging
from core.database import DatabaseManager
from repositories.setup_repository import SetupRepository
from repositories.student_repository import StudentRepository
from repositories.question_repository import QuestionRepository
from services.data_population_service import DataPopulationService
from services.recommendation_service import RecommendationService
from models.student import Student
from core.exceptions import StudentNotFoundError, DataValidationError, DatabaseConnectionError
from config.settings import db_config, app_config
import sys
from pathlib import Path
import json

# Configure logging
logging.basicConfig(level=app_config.log_level, stream=sys.stdout,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        db_manager.initialize_connection(
            uri=db_config.uri, username=db_config.username, password=db_config.password
        )

        # Setup repositories
        setup_repo = SetupRepository(db_manager)
        student_repo = StudentRepository(db_manager)

        # Create necessary constraints and indexes
        setup_repo.create_constraints_and_indexes()

        # Populate initial data
        data_population_service = DataPopulationService(db_manager, setup_repo)
        data_population_service.populate_from_json_file(file_path=app_config.data_file_path)

        
        student_id = "ashish_b"
        student = Student(student_id=student_id, name="Ashish Bhardwaj", email="ashish.bhardwaj@fastwise.com")
        student_repo.create_or_update_student(student)

    except (StudentNotFoundError, DataValidationError, DatabaseConnectionError) as e:
        logger.error(f"Error occurred: {e}")
    finally:
        db_manager.close_connection()

if __name__ == "__main__":
    main()
    logger.info("Application started successfully")