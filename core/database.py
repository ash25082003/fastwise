#core/database.py
import logging
from typing import Optional,Callable,Any
from neo4j import GraphDatabase, Driver
from contextlib import contextmanager

from .exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages Neo4j database connections using singleton pattern.
    Provides connection pooling and transaction management.
    """
    _instance: Optional['DatabaseManager'] = None
    _driver: Optional[Driver] = None

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize_connection(self, uri: str, username: str, password: str) -> None:
        """Initialize the Neo4j driver connection."""
        if self._driver is not None:
            logger.warning("Database connection already initialized")
            return

        try:
            logger.info("Initializing Neo4j database connection...")
            self._driver = GraphDatabase.driver(uri, auth=(username, password))
            self._driver.verify_connectivity()
            logger.info("Database connection established successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}") from e

    def get_driver(self) -> Driver:
        """Get the active database driver."""
        if self._driver is None:
            raise DatabaseConnectionError("Database not initialized. Call initialize_connection() first.")
        return self._driver

    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        if self._driver is None:
            raise DatabaseConnectionError("Database not initialized")
        
        session = self._driver.session()
        try:
            yield session
        finally:
            session.close()

    def close_connection(self) -> None:
        """Close the database connection."""
        if self._driver is not None:
            logger.info("Closing database connection")
            self._driver.close()
            self._driver = None
    
    def execute_transaction(self, transaction_function: Callable, *args, **kwargs) -> Any:
        """
        Execute a transaction function with automatic retry and rollback on failure.
        
        Args:
            transaction_function: Function that takes a transaction object as first parameter
            *args: Additional arguments to pass to the transaction function
            **kwargs: Additional keyword arguments to pass to the transaction function
            
        Returns:
            Result from the transaction function
            
        Raises:
            Exception: If transaction fails after retries
        """
        if not self._driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        try:
            with self._driver.session() as session:
                # Use write_transaction for data modification operations
                result = session.write_transaction(transaction_function, *args, **kwargs)
                logger.debug("Transaction completed successfully")
                return result
                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
    
    def execute_read_transaction(self, transaction_function: Callable, *args, **kwargs) -> Any:
        """
        Execute a read-only transaction.
        
        Args:
            transaction_function: Function that takes a transaction object as first parameter
            *args: Additional arguments to pass to the transaction function
            **kwargs: Additional keyword arguments to pass to the transaction function
            
        Returns:
            Result from the transaction function
        """
        if not self._driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        try:
            with self._driver.session() as session:
                result = session.read_transaction(transaction_function, *args, **kwargs)
                logger.debug("Read transaction completed successfully")
                return result
                
        except Exception as e:
            logger.error(f"Read transaction failed: {e}")
            raise
    
    def execute_write_query(self, query: str, parameters: dict = None) -> Any:
        """
        Execute a single write query outside of a transaction.
        Use this for simple operations that don't require transaction management.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Query result
        """
        if not self._driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                # Consume the result to ensure it's executed
                return result.consume()
                
        except Exception as e:
            logger.error(f"Write query failed: {e}")
            raise
    
    def execute_read_query(self, query: str, parameters: dict = None) -> list:
        """
        Execute a single read query and return results as a list.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of query results
        """
        if not self._driver:
            raise RuntimeError("Database connection not established. Call connect() first.")
        
        try:
            with self._driver.session() as session:
                result = session.run(query, parameters or {})
                return [record for record in result]
                
        except Exception as e:
            logger.error(f"Read query failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self._driver:
                return False
            
            self._driver.verify_connectivity()
            return True
            
        except Exception as e:
            logger.warning(f"Database health check failed: {e}")
            return False

    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        self.close_connection()