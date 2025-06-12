# Tutr - Personalized Learning Recommendation System

A Neo4j-based personalized learning recommendation system that suggests questions to students based on their progress and mastery of concepts.

## Features

- **Personalized Recommendations**: AI-driven question recommendations based on student progress
- **Progress Tracking**: Track student attempts and mastery of questions and concepts
- **Concept Mapping**: Hierarchical concept and subconcept relationships
- **Curriculum Sequencing**: Questions ordered by educational curriculum sequence
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Data Validation**: Robust input validation and error handling
- **Modular Architecture**: Clean separation of concerns with repositories and services

## Architecture

```
src/
├── config/           # Configuration management
├── core/            # Core database and exceptions
├── models/          # Data models (Student, Question, Concept)
├── repositories/    # Data access layer
├── services/        # Business logic layer
├── utils/           # Utility functions and validators
└── main.py         # Application entry point
```

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd tutr
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup Neo4j Database**
   - Install Neo4j Desktop or use Neo4j Aura
   - Create a new database
   - Note the connection details (URI, username, password)

4. **Configure Environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. **Prepare Data**
   - Place your questions JSON file in the `data/` directory
   - Update `DATA_FILE` path in `.env` if needed

## Usage

### Basic Usage

```python
from main import TutrApplication

# Initialize application
app = TutrApplication()
app.initialize()

# Setup database with questions (first time only)
app.setup_database(clear_existing=True)

# Create a student
app.data_population_service.create_sample_student("student_123")

# Get recommendation
recommendation = app.get_recommendation_for_student("student_123")
print(f"Recommended: {recommendation['title']}")

# Mark question as completed
app.complete_question_for_student("student_123", recommendation['id'], is_mastered=True)

# Shutdown
app.shutdown()
```

### Advanced Usage

```python
from core.database import DatabaseManager
from repositories.student_repository import StudentRepository
from services.recommendation_service import RecommendationService
from config.settings import db_config

# Initialize components separately
db_manager = DatabaseManager()
db_manager.initialize_connection(db_config.uri, db_config.username, db_config.password)

student_repo = StudentRepository(db_manager)
question_repo = QuestionRepository(db_manager)

recommendation_service = RecommendationService(db_manager, student_repo, question_repo)

# Get recommendations by concept
concept_questions = recommendation_service.get_questions_by_concept(
    "student_123", 
    "Algebra", 
    limit=5
)
```

## Data Format

### Questions JSON Format

```json
[
  {
    "id": "q001",
    "title": "Basic Addition",
    "content": "What is 2 + 3?",
    "difficulty": "Easy",
    "stepNumber": 1,
    "subStepNumber": 1,
    "sequenceNumber": 1,
    "standardConcepts": ["Addition", "Basic Math"],
    "keyConcepts": ["Numbers"],
    "solutionApproaches": [
      {
        "name": "Direct Calculation",
        "explanation": "Add the numbers directly"
      }
    ]
  }
]
```

## API Reference

### RecommendationService

#### `get_next_recommended_question(student_id: str, limit: int = 1)`
Get the next recommended question for a student.

**Parameters:**
- `student_id`: Student identifier
- `limit`: Maximum number of recommendations

**Returns:** Question dictionary or None

#### `complete_question(student_id: str, question_id: str, is_mastered: bool = True)`
Mark a question as completed by a student.

**Parameters:**
- `student_id`: Student identifier  
- `question_id`: Question identifier
- `is_mastered`: Whether the student mastered the question

### StudentRepository

#### `create_or_update_student(student: Student)`
Create a new student or update existing one.

#### `find_student_by_id(student_id: str)`
Find student by ID.

#### `get_student_progress_summary(student_id: str)`
Get comprehensive progress summary.

## Configuration

Environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j database URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `password` |
| `DATA_FILE` | Path to questions JSON | `data/questions.json` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_RECOMMENDATIONS` | Max recommendations per request | `20` |

## Logging

The application uses Python's logging module with the following features:

- **Console Output**: Real-time logging to stdout
- **File Logging**: Persistent logs saved to `tutr.log`
- **Configurable Levels**: Set via `LOG_LEVEL` environment variable
- **Structured Messages**: Consistent formatting with timestamps

## Error Handling

Custom exception hierarchy:

- `TutrException`: Base application exception
- `DatabaseConnectionError`: Database connection issues
- `StudentNotFoundError`: Student not found in database
- `QuestionNotFoundError`: Question not found in database
- `DataValidationError`: Data validation failures

## Database Schema

### Nodes
- **Student**: Student information and progress
- **Question**: Educational questions with metadata
- **Concept**: High-level learning concepts
- **SubConcept**: Specific skills within concepts

### Relationships
- **ATTEMPTED**: Student attempted a question
- **MASTERED**: Student mastered a question/concept
- **REQUIRES_CONCEPT**: Question requires a concept
- **REQUIRES_SUBCONCEPT**: Question requires a subconcept
- **HAS_SUBCONCEPT**: Concept contains subconcepts

## Development

### Adding New Features

1. **Models**: Add new data models in `models/`
2. **Repositories**: Create repository classes for data access
3. **Services**: Implement business logic in service classes
4. **Validation**: Add validators in `utils/validators.py`

### Testing

```bash
# Run tests (you'll need to create these)
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/
```

### Code Quality

The codebase follows these principles:

- **PEP 8**: Python style guidelines
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Docstrings for all public methods
- **Error Handling**: Proper exception handling
- **Separation of Concerns**: Clear architectural boundaries

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check Neo4j is running
   - Verify connection credentials in `.env`
   - Ensure network connectivity

2. **Data File Not Found**
   - Check `DATA_FILE` path in `.env`
   - Ensure JSON file exists and is readable

3. **Validation Errors**
   - Check data format matches expected schema
   - Verify required fields are present

4. **Performance Issues**
   - Ensure database indexes are created
   - Check query complexity
   - Monitor memory usage

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure code follows style guidelines
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

## Migration from Legacy Code

If you're migrating from an existing codebase:

1. **Backup existing data** from your Neo4j database
2. **Update imports** to use new module structure
3. **Replace hardcoded values** with configuration
4. **Update method calls** to use new naming conventions
5. **Add error handling** where previously missing
6. **Test thoroughly** with your existing data

### Migration Script Example

```python
# migration_script.py
from main import TutrApplication

def migrate_legacy_data():
    app = TutrApplication()
    app.initialize()
    
    # Your migration logic here
    # - Convert old data format
    # - Update relationships
    # - Validate data integrity
    
    app.shutdown()

if __name__ == "__main__":
    migrate_legacy_data()
```