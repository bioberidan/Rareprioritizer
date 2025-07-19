"""
Run management utilities for websearch preprocessing.

This module provides functions for managing run numbers, detecting existing runs,
and implementing skip logic for processed diseases.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
import re

logger = logging.getLogger(__name__)


def check_existing_runs(orphacode: str, base_path: str) -> List[int]:
    """
    Check existing run numbers for a disease.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        
    Returns:
        List of existing run numbers (sorted)
    """
    disease_dir = Path(base_path) / orphacode
    
    if not disease_dir.exists():
        logger.debug(f"No directory found for disease {orphacode}")
        return []
    
    run_numbers = []
    pattern = re.compile(r'^run(\d+)_disease2websearch\.json$')
    
    try:
        for file in disease_dir.iterdir():
            if file.is_file():
                match = pattern.match(file.name)
                if match:
                    run_num = int(match.group(1))
                    run_numbers.append(run_num)
    except Exception as e:
        logger.warning(f"Error checking runs for disease {orphacode}: {e}")
        return []
    
    run_numbers.sort()
    logger.debug(f"Found existing runs for disease {orphacode}: {run_numbers}")
    return run_numbers


def get_next_run_number(orphacode: str, base_path: str) -> int:
    """
    Get next available run number for a disease.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        
    Returns:
        Next available run number
    """
    existing_runs = check_existing_runs(orphacode, base_path)
    
    if not existing_runs:
        next_run = 1
    else:
        next_run = max(existing_runs) + 1
    
    logger.debug(f"Next run number for disease {orphacode}: {next_run}")
    return next_run


def should_skip_disease(orphacode: str, base_path: str, force_reprocess: bool = False) -> bool:
    """
    Determine if disease should be skipped based on existing runs.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        force_reprocess: Whether to force reprocessing
        
    Returns:
        True if disease should be skipped, False otherwise
    """
    existing_runs = check_existing_runs(orphacode, base_path)
    
    if not existing_runs:
        # No existing runs, should process
        logger.debug(f"No existing runs for disease {orphacode}, will process")
        return False
    
    if force_reprocess:
        # Force reprocess flag set, don't skip
        logger.debug(f"Force reprocess enabled for disease {orphacode}, will process with new run")
        return False
    
    # Has existing runs and no force flag, should skip
    logger.info(f"Disease {orphacode} has existing runs {existing_runs}, skipping (use --force-reprocess to override)")
    return True


def get_run_file_path(orphacode: str, base_path: str, run_number: int) -> str:
    """
    Get file path for a specific run.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        run_number: Run number
        
    Returns:
        Full file path for the run
    """
    disease_dir = Path(base_path) / orphacode
    filename = f"run{run_number}_disease2websearch.json"
    return str(disease_dir / filename)


def ensure_disease_directory(orphacode: str, base_path: str) -> Path:
    """
    Ensure disease directory exists.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        
    Returns:
        Path to disease directory
    """
    disease_dir = Path(base_path) / orphacode
    disease_dir.mkdir(parents=True, exist_ok=True)
    return disease_dir


def is_run_file_valid(file_path: str) -> bool:
    """
    Check if run file exists and is valid.
    
    Args:
        file_path: Path to run file
        
    Returns:
        True if file exists and is valid, False otherwise
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False
    
    try:
        # Check if file has content
        if file_path.stat().st_size == 0:
            logger.warning(f"Run file {file_path} is empty")
            return False
        
        # Could add JSON validation here if needed
        return True
        
    except Exception as e:
        logger.warning(f"Error validating run file {file_path}: {e}")
        return False


def get_disease_run_summary(orphacode: str, base_path: str) -> dict:
    """
    Get summary of runs for a disease.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        
    Returns:
        Dictionary with run summary information
    """
    existing_runs = check_existing_runs(orphacode, base_path)
    disease_dir = Path(base_path) / orphacode
    
    summary = {
        'orphacode': orphacode,
        'has_runs': len(existing_runs) > 0,
        'run_count': len(existing_runs),
        'existing_runs': existing_runs,
        'next_run_number': get_next_run_number(orphacode, base_path),
        'disease_directory': str(disease_dir),
        'directory_exists': disease_dir.exists()
    }
    
    # Add file info for each run
    summary['run_files'] = []
    for run_num in existing_runs:
        file_path = get_run_file_path(orphacode, base_path, run_num)
        summary['run_files'].append({
            'run_number': run_num,
            'file_path': file_path,
            'is_valid': is_run_file_valid(file_path),
            'file_size': Path(file_path).stat().st_size if Path(file_path).exists() else 0
        })
    
    return summary


def clean_invalid_runs(orphacode: str, base_path: str, 
                      backup: bool = True) -> List[int]:
    """
    Clean invalid or empty run files for a disease.
    
    Args:
        orphacode: ORPHA code of the disease
        base_path: Base path for websearch results
        backup: Whether to backup files before deletion
        
    Returns:
        List of run numbers that were cleaned
    """
    existing_runs = check_existing_runs(orphacode, base_path)
    cleaned_runs = []
    
    for run_num in existing_runs:
        file_path = get_run_file_path(orphacode, base_path, run_num)
        
        if not is_run_file_valid(file_path):
            if backup:
                # Create backup before deletion
                backup_path = f"{file_path}.invalid.bak"
                try:
                    import shutil
                    shutil.move(file_path, backup_path)
                    logger.info(f"Moved invalid run file to backup: {backup_path}")
                except Exception as e:
                    logger.warning(f"Failed to backup invalid file {file_path}: {e}")
            else:
                # Direct deletion
                try:
                    Path(file_path).unlink()
                    logger.info(f"Deleted invalid run file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete invalid file {file_path}: {e}")
                    continue
            
            cleaned_runs.append(run_num)
    
    if cleaned_runs:
        logger.info(f"Cleaned {len(cleaned_runs)} invalid runs for disease {orphacode}: {cleaned_runs}")
    
    return cleaned_runs


def list_all_disease_runs(base_path: str) -> dict:
    """
    List all diseases and their runs in the base path.
    
    Args:
        base_path: Base path for websearch results
        
    Returns:
        Dictionary mapping orphacodes to run summaries
    """
    base_path = Path(base_path)
    
    if not base_path.exists():
        logger.warning(f"Base path does not exist: {base_path}")
        return {}
    
    disease_runs = {}
    
    try:
        for disease_dir in base_path.iterdir():
            if disease_dir.is_dir() and disease_dir.name.isdigit():
                orphacode = disease_dir.name
                summary = get_disease_run_summary(orphacode, str(base_path))
                disease_runs[orphacode] = summary
    except Exception as e:
        logger.error(f"Error listing disease runs: {e}")
    
    return disease_runs 