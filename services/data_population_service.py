# services/data_population_service.py
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from core.database import DatabaseManager
from repositories.setup_repository import SetupRepository
from core.exceptions import DataValidationError

logger = logging.getLogger(__name__)

class DataPopulationService:
    """
    Service for populating the graph database from external data sources.
    Handles data loading, validation, and batch processing.
    """
    
    def __init__(self, db_manager: DatabaseManager, setup_repo: SetupRepository):
        self.db_manager = db_manager
        self.setup_repo = setup_repo

    def populate_from_json_file(self, file_path: str, batch_size: int = 100) -> Dict[str, Any]:
        """
        Load data from a JSON file and populate the graph database in batches.
        
        Args:
            file_path: Path to the JSON file containing question data
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary containing processing statistics
        """
        logger.info(f"Starting data population from file: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        try:
            # Load and validate JSON data
            data = self._load_json_data(file_path)
            logger.info(f"Loaded {len(data)} items from JSON file")
            
            # Process data in batches
            stats = self._process_data_in_batches(data, batch_size)
            
            logger.info(f"Data population completed. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Data population failed: {e}")
            raise

    def populate_from_data_list(self, data: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """
        Populate the graph database from a list of data items.
        
        Args:
            data: List of dictionaries containing question data
            batch_size: Number of items to process in each batch
            
        Returns:
            Dictionary containing processing statistics
        """
        logger.info(f"Starting data population from data list with {len(data)} items")
        
        try:
            stats = self._process_data_in_batches(data, batch_size)
            logger.info(f"Data population completed. Stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Data population from list failed: {e}")
            raise

    def validate_data_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Validate the structure of data in a JSON file without importing it.
        
        Args:
            file_path: Path to the JSON file to validate
            
        Returns:
            Dictionary containing validation results
        """
        logger.info(f"Validating data structure in file: {file_path}")
        
        try:
            data = self._load_json_data(file_path)
            return self._validate_data_items(data, validate_only=True)
            
        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            raise

    def _load_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load and parse JSON data from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if not isinstance(data, list):
                raise DataValidationError("JSON file must contain an array of objects")
                
            return data
            
        except json.JSONDecodeError as e:
            raise DataValidationError(f"Invalid JSON format: {e}")
        except IOError as e:
            raise DataValidationError(f"Could not read file: {e}")

    def _process_data_in_batches(self, data: List[Dict[str, Any]], batch_size: int) -> Dict[str, Any]:
        """Process data items in batches for better performance and error handling."""
        total_items = len(data)
        processed_items = 0
        failed_items = 0
        failed_item_ids = []
        
        # First, validate all data items
        validation_result = self._validate_data_items(data)
        if validation_result['invalid_items']:
            logger.warning(f"Found {len(validation_result['invalid_items'])} invalid items")
        
        # Process valid items in batches
        valid_data = validation_result['valid_items']
        
        for i in range(0, len(valid_data), batch_size):
            batch = valid_data[i:i + batch_size]
            batch_stats = self._process_batch(batch)
            
            processed_items += batch_stats['processed']
            failed_items += batch_stats['failed']
            failed_item_ids.extend(batch_stats['failed_ids'])
            
            logger.info(f"Processed batch {i//batch_size + 1}: "
                       f"{batch_stats['processed']}/{len(batch)} items successful")

        return {
            'total_items': total_items,
            'processed_items': processed_items,
            'failed_items': failed_items,
            'invalid_items': len(validation_result['invalid_items']),
            'failed_item_ids': failed_item_ids,
            'invalid_item_ids': validation_result['invalid_item_ids']
        }

    def _process_batch(self, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a single batch of data items."""
        processed = 0
        failed = 0
        failed_ids = []
        
        for item in batch:
            try:
                # Process each item in its own transaction
                self.db_manager.execute_transaction(
                    self.setup_repo.populate_question_and_concepts_transaction,
                    item
                )
                processed += 1
                
            except Exception as e:
                failed += 1
                item_id = item.get('id', 'N/A')
                failed_ids.append(item_id)
                logger.error(f"Failed to process item {item_id}: {e}")
        
        return {
            'processed': processed,
            'failed': failed,
            'failed_ids': failed_ids
        }

    def _validate_data_items(self, data: List[Dict[str, Any]], validate_only: bool = False) -> Dict[str, Any]:
        """
        Validate a list of data items and return validation results.
        
        Args:
            data: List of data items to validate
            validate_only: If True, only validate structure without processing
            
        Returns:
            Dictionary containing validation results
        """
        # Delegate to the repository for validation
        return self.setup_repo._validate_data_items(data, validate_only)

    def _validate_item_fields(self, item: Dict[str, Any]) -> None:
        """Validate individual item fields for correct types and values."""
        
        # Validate ID is not empty
        if not item.get('id') or not str(item['id']).strip():
            raise DataValidationError("ID cannot be empty")
        
        # Validate numeric fields
        numeric_fields = ['step_no', 'sub_step_no', 'sl_no']
        for field in numeric_fields:
            if not isinstance(item.get(field), (int, float)) or item[field] < 0:
                raise DataValidationError(f"Field {field} must be a non-negative number")
        
        # Validate string fields are not empty
        string_fields = ['question_title', 'question']
        for field in string_fields:
            if not item.get(field) or not str(item[field]).strip():
                raise DataValidationError(f"Field {field} cannot be empty")
        
        # Validate list fields if present
        list_fields = ['standard_concepts', 'sub_concepts', 'solution_approaches']
        for field in list_fields:
            if field in item and not isinstance(item[field], list):
                raise DataValidationError(f"Field {field} must be a list")
        
        # Validate solution approaches structure
        if 'solution_approaches' in item:
            for i, approach in enumerate(item['solution_approaches']):
                if not isinstance(approach, dict):
                    raise DataValidationError(f"Solution approach {i} must be a dictionary")
                if 'approach_name' not in approach:
                    raise DataValidationError(f"Solution approach {i} missing 'approach_name'")

    def get_population_summary(self) -> Dict[str, Any]:
        """Get a summary of the current database population."""
        return self.setup_repo.get_database_statistics()