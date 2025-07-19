"""
General data I/O utility.

This module provides universal and generalizable functions for loading and saving
data in various formats (JSON, CSV, etc.) across different preprocessing scripts.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import os

logger = logging.getLogger(__name__)


def load_json_data(file_path: str, encoding: str = 'utf-8') -> Union[Dict, List]:
    """
    Load JSON data from file with error handling.
    
    Args:
        file_path: Path to JSON file
        encoding: File encoding (default: utf-8)
        
    Returns:
        Dictionary or list containing JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded JSON data from {file_path}")
        return data
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading JSON {file_path}: {e}")
        raise


def save_json_data(data: Union[Dict, List], file_path: str, 
                  encoding: str = 'utf-8', indent: int = 2,
                  ensure_ascii: bool = False) -> None:
    """
    Save data to JSON file with error handling.
    
    Args:
        data: Data to save (dict or list)
        file_path: Path where to save the file
        encoding: File encoding (default: utf-8)
        indent: JSON indentation (default: 2)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
        
        logger.info(f"Successfully saved JSON data to {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        raise


def load_csv_data(file_path: str, encoding: str = 'utf-8', 
                 delimiter: str = ',') -> List[Dict[str, str]]:
    """
    Load CSV data as list of dictionaries.
    
    Args:
        file_path: Path to CSV file
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
        
    Returns:
        List of dictionaries with column names as keys
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding=encoding, newline='') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = list(reader)
        
        logger.info(f"Successfully loaded CSV data from {file_path} ({len(data)} rows)")
        return data
        
    except Exception as e:
        logger.error(f"Error loading CSV {file_path}: {e}")
        raise


def save_csv_data(data: List[Dict[str, Any]], file_path: str,
                 encoding: str = 'utf-8', delimiter: str = ',') -> None:
    """
    Save list of dictionaries to CSV file.
    
    Args:
        data: List of dictionaries to save
        file_path: Path where to save the file
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
    """
    if not data:
        logger.warning(f"No data to save to {file_path}")
        return
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        fieldnames = data[0].keys()
        
        with open(file_path, 'w', encoding=encoding, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Successfully saved CSV data to {file_path} ({len(data)} rows)")
        
    except Exception as e:
        logger.error(f"Error saving CSV to {file_path}: {e}")
        raise


def ensure_directory_exists(directory_path: str) -> Path:
    """
    Ensure directory exists, create if necessary.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(directory_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {'exists': False}
    
    stat = file_path.stat()
    
    return {
        'exists': True,
        'size_bytes': stat.st_size,
        'size_mb': round(stat.st_size / 1024 / 1024, 2),
        'modified_time': datetime.fromtimestamp(stat.st_mtime),
        'is_file': file_path.is_file(),
        'is_directory': file_path.is_dir(),
        'extension': file_path.suffix,
        'name': file_path.name,
        'stem': file_path.stem
    }


def list_files_in_directory(directory_path: str, pattern: str = "*",
                           recursive: bool = False) -> List[Path]:
    """
    List files in directory with optional pattern matching.
    
    Args:
        directory_path: Path to directory
        pattern: File pattern to match (default: "*" for all files)
        recursive: Whether to search recursively (default: False)
        
    Returns:
        List of file paths
    """
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        logger.warning(f"Directory not found: {directory_path}")
        return []
    
    if recursive:
        files = list(dir_path.rglob(pattern))
    else:
        files = list(dir_path.glob(pattern))
    
    # Filter to only files (not directories)
    files = [f for f in files if f.is_file()]
    
    logger.info(f"Found {len(files)} files in {directory_path} with pattern '{pattern}'")
    return files


def safe_file_operation(operation: str, file_path: str, 
                       max_attempts: int = 3) -> bool:
    """
    Perform file operation with retry logic.
    
    Args:
        operation: Operation type ('read', 'write', 'delete')
        file_path: Path to file
        max_attempts: Maximum retry attempts
        
    Returns:
        True if operation succeeded, False otherwise
    """
    for attempt in range(max_attempts):
        try:
            file_path = Path(file_path)
            
            if operation == 'read':
                return file_path.exists() and file_path.is_file()
            elif operation == 'write':
                file_path.parent.mkdir(parents=True, exist_ok=True)
                return True
            elif operation == 'delete':
                if file_path.exists():
                    file_path.unlink()
                return True
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            logger.warning(f"File operation {operation} failed on attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                logger.error(f"File operation {operation} failed after {max_attempts} attempts")
                return False
    
    return False


def create_timestamped_filename(base_name: str, extension: str = ".json") -> str:
    """
    Create filename with timestamp.
    
    Args:
        base_name: Base filename without extension
        extension: File extension (default: .json)
        
    Returns:
        Filename with timestamp
        
    Example:
        create_timestamped_filename("metabolic_results") 
        # Returns: "metabolic_results_20241214_103045.json"
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}{extension}"


def backup_file(file_path: str, backup_suffix: str = ".bak") -> Optional[str]:
    """
    Create backup of existing file.
    
    Args:
        file_path: Path to file to backup
        backup_suffix: Suffix for backup file (default: .bak)
        
    Returns:
        Path to backup file if successful, None otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        logger.warning(f"Cannot backup non-existent file: {file_path}")
        return None
    
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
    
    try:
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"Failed to create backup of {file_path}: {e}")
        return None 