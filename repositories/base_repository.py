#repositories/base_repository.py
import logging
from abc import ABC
from typing import Any, Dict, List
from neo4j import Driver, Session

from core.database import DatabaseManager
from core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """Base repository class with common database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a read query and return results."""
        parameters = parameters or {}
        
        try:
            with self.db_manager.get_session() as session:
                result = session.run(query, parameters)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise DatabaseConnectionError(f"Query failed: {e}") from e
    
    def execute_write_query(self, query: str, parameters: Dict[str, Any] = None) -> None:
        """Execute a write query."""
        parameters = parameters or {}
        
        try:
            with self.db_manager.get_session() as session:
                session.run(query, parameters)
        except Exception as e:
            logger.error(f"Write query execution failed: {e}")
            raise DatabaseConnectionError(f"Write query failed: {e}") from e
    
    def execute_transaction(self, transaction_func, *args, **kwargs):
        """Execute a function within a transaction."""
        try:
            with self.db_manager.get_session() as session:
                return session.execute_write(transaction_func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction execution failed: {e}")
            raise DatabaseConnectionError(f"Transaction failed: {e}") from e