# utils/validators.py
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from core.exceptions import DataValidationError

class ValidationUtils:
    """Utility class for common validation operations."""
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Student ID pattern (alphanumeric with underscores)
    STUDENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid, False otherwise
        """
        if not email or not isinstance(email, str):
            return False
        return bool(ValidationUtils.EMAIL_PATTERN.match(email.strip()))
    
    @staticmethod
    def validate_student_id(student_id: str) -> bool:
        """
        Validate student ID format.
        
        Args:
            student_id: Student ID to validate
            
        Returns:
            True if student ID is valid, False otherwise
        """
        if not student_id or not isinstance(student_id, str):
            return False