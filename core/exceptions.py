#core/exceptions.py
class TutrException(Exception):
    """Base exception for the Tutr application."""
    pass

class DatabaseConnectionError(TutrException):
    """Raised when database connection fails."""
    pass

class StudentNotFoundError(TutrException):
    """Raised when a student is not found."""
    pass

class QuestionNotFoundError(TutrException):
    """Raised when a question is not found."""
    pass

class DataValidationError(TutrException):
    """Raised when data validation fails."""
    pass