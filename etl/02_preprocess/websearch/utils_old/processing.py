"""
Main processing logic for websearch metabolic preprocessing.

This module provides functions for processing diseases, managing results,
and handling the overall workflow with run management integration.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add local imports
from .yaml_config import load_yaml_config, get_nested_config, validate_required_keys
from .io import load_json_data, save_json_data, ensure_directory_exists
from .run_management import (
    should_skip_disease, get_next_run_number, get_run_file_path,
    ensure_disease_directory, is_run_file_valid
)
from .analysis import select_analysis, validate_analysis_result, create_analysis_metadata

logger = logging.getLogger(__name__)


def load_config(config_path: str = "etl/02_preprocess/websearch/conf/config_metabolic.yaml") -> Dict[str, Any]:
    """
    Load and validate YAML configuration using general yaml_config utility.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required keys are missing
    """
    config = load_yaml_config(config_path)
    
    # Validate required configuration keys
    required_keys = [
        ['websearch', 'metabolic', 'input', 'data_source'],
        ['websearch', 'metabolic', 'processing', 'analysis_type'],
        ['websearch', 'metabolic', 'retry', 'max_attempts'],
        ['websearch', 'metabolic', 'output', 'base_path']
    ]
    
    validate_required_keys(config, required_keys, "metabolic websearch")
    
    logger.info(f"Configuration loaded successfully from {config_path}")
    return config


def load_diseases(input_file: str) -> List[Dict[str, str]]:
    """
    Load diseases from curated metabolic data using general io utility.
    
    Args:
        input_file: Path to input JSON file
        
    Returns:
        List of disease dictionaries
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If data format is invalid
    """
    diseases_data = load_json_data(input_file)
    
    if not isinstance(diseases_data, list):
        raise ValueError(f"Expected list of diseases, got {type(diseases_data)}")
    
    # Validate disease data structure
    for i, disease in enumerate(diseases_data):
        if not isinstance(disease, dict):
            raise ValueError(f"Disease {i} is not a dictionary: {type(disease)}")
        
        required_fields = ['disease_name', 'orpha_code']
        for field in required_fields:
            if field not in disease:
                raise ValueError(f"Disease {i} missing required field '{field}'")
    
    logger.info(f"Loaded {len(diseases_data)} diseases from {input_file}")
    return diseases_data


def process_single_disease(disease: Dict[str, str], analysis_type: str, 
                          config: Dict[str, Any], run_number: int) -> Dict[str, Any]:
    """
    Process single disease with specified analysis type and retry logic.
    
    Args:
        disease: Disease dictionary
        analysis_type: Type of analysis to run
        config: Configuration dictionary
        run_number: Run number for this processing
        
    Returns:
        Complete websearch result dictionary
        
    Raises:
        AnalysisError: If analysis fails after retries
    """
    start_time = datetime.now()
    
    logger.info(f"Processing {disease['disease_name']} (ORPHA:{disease['orpha_code']}) with {analysis_type} analysis (run {run_number})")
    
    # Run analysis with retry logic
    analysis_result = select_analysis(analysis_type, disease, config)
    
    # Validate result
    if not validate_analysis_result(analysis_result, analysis_type):
        raise ValueError(f"Analysis result validation failed for {analysis_type}")
    
    end_time = datetime.now()
    
    # Create metadata
    metadata = create_analysis_metadata(
        disease, analysis_type, start_time, end_time, success=True
    )
    
    # Create complete result
    result = create_websearch_result(
        disease, analysis_type, analysis_result, 
        metadata['processing_duration'], run_number
    )
    
    logger.info(f"Successfully processed {disease['disease_name']} in {metadata['processing_duration']:.2f}s")
    return result


def create_websearch_result(disease: Dict[str, str], analysis_type: str, 
                           analysis_result: Dict[str, Any], processing_time: float,
                           run_number: int, error: str = None) -> Dict[str, Any]:
    """
    Create websearch result dictionary for a single disease.
    
    Args:
        disease: Disease dictionary
        analysis_type: Type of analysis
        analysis_result: Result from analysis
        processing_time: Processing duration in seconds
        run_number: Run number
        error: Error message if failed
        
    Returns:
        Complete websearch result dictionary
    """
    result = {
        "disease_name": disease["disease_name"],
        "orpha_code": disease["orpha_code"],
        "processing_timestamp": datetime.now().isoformat(),
        "run_number": run_number,
        "analysis_type": analysis_type,
        "processing_duration": processing_time,
        "success": error is None,
        "error_details": error
    }
    
    # Add analysis-specific results
    if analysis_type == "groups" and analysis_result:
        result["groups_analysis"] = analysis_result
    elif analysis_type == "socioeconomic" and analysis_result:
        result["socioeconomic_analysis"] = analysis_result
    elif analysis_type == "clinical" and analysis_result:
        result["clinical_analysis"] = analysis_result
    
    return result


def save_disease_result(result: Dict[str, Any], base_path: str) -> str:
    """
    Save disease result to appropriate file location.
    
    Args:
        result: Websearch result dictionary
        base_path: Base path for output
        
    Returns:
        Path to saved file
        
    Raises:
        Exception: If saving fails
    """
    orphacode = result['orpha_code']
    run_number = result['run_number']
    
    # Ensure disease directory exists
    ensure_disease_directory(orphacode, base_path)
    
    # Get file path
    file_path = get_run_file_path(orphacode, base_path, run_number)
    
    # Save result
    save_json_data(result, file_path)
    
    logger.info(f"Saved result to {file_path}")
    return file_path


def process_diseases(diseases: List[Dict[str, str]], config: Dict[str, Any], 
                    force_reprocess: bool = False, specific_run: Optional[int] = None,
                    dry_run: bool = False) -> Dict[str, Any]:
    """
    Process all diseases through websearch analysis with run management.
    
    Args:
        diseases: List of disease dictionaries
        config: Configuration dictionary
        force_reprocess: Whether to force reprocessing
        specific_run: Specific run number to use
        dry_run: Whether to perform dry run
        
    Returns:
        Processing summary dictionary
    """
    analysis_type = config['websearch']['metabolic']['processing']['analysis_type']
    base_path = config['websearch']['metabolic']['output']['base_path']
    
    summary = {
        'total_diseases': len(diseases),
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'analysis_type': analysis_type,
        'start_time': datetime.now().isoformat(),
        'processed_diseases': [],
        'skipped_diseases': [],
        'failed_diseases': []
    }
    
    logger.info(f"Starting processing of {len(diseases)} diseases with {analysis_type} analysis")
    
    for disease in diseases:
        orphacode = disease['orpha_code']
        disease_name = disease['disease_name']
        
        # Check if should skip
        if not force_reprocess and not specific_run:
            if should_skip_disease(orphacode, base_path, force_reprocess):
                summary['skipped'] += 1
                summary['skipped_diseases'].append({
                    'orphacode': orphacode,
                    'disease_name': disease_name,
                    'reason': 'existing_runs'
                })
                continue
        
        # Determine run number
        if specific_run:
            run_number = specific_run
            logger.info(f"Using specific run number {run_number} for {disease_name}")
        else:
            run_number = get_next_run_number(orphacode, base_path)
            logger.info(f"Using next run number {run_number} for {disease_name}")
        
        if dry_run:
            logger.info(f"DRY RUN: Would process {disease_name} (ORPHA:{orphacode}) with {analysis_type} analysis (run {run_number})")
            summary['processed'] += 1
            summary['processed_diseases'].append({
                'orphacode': orphacode,
                'disease_name': disease_name,
                'run_number': run_number,
                'dry_run': True
            })
            continue
        
        # Process disease - let exceptions propagate to caller
        try:
            result = process_single_disease(disease, analysis_type, config, run_number)
            file_path = save_disease_result(result, base_path)
            
            summary['processed'] += 1
            summary['processed_diseases'].append({
                'orphacode': orphacode,
                'disease_name': disease_name,
                'run_number': run_number,
                'file_path': file_path,
                'processing_duration': result['processing_duration']
            })
            
        except Exception as e:
            logger.error(f"Processing failed for {disease_name}: {e}")
            summary['failed'] += 1
            summary['failed_diseases'].append({
                'orphacode': orphacode,
                'disease_name': disease_name,
                'run_number': run_number,
                'error': str(e)
            })
    
    summary['end_time'] = datetime.now().isoformat()
    summary['total_duration'] = (
        datetime.fromisoformat(summary['end_time']) - 
        datetime.fromisoformat(summary['start_time'])
    ).total_seconds()
    
    # Log summary
    logger.info(f"Processing complete: {summary['processed']} processed, "
                f"{summary['skipped']} skipped, {summary['failed']} failed")
    
    return summary


def validate_result(result: Dict[str, Any]) -> bool:
    """
    Validate websearch result structure.
    
    Args:
        result: Websearch result dictionary
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = [
        'disease_name', 'orpha_code', 'processing_timestamp',
        'run_number', 'analysis_type', 'processing_duration',
        'success', 'error_details'
    ]
    
    for field in required_fields:
        if field not in result:
            logger.warning(f"Missing required field '{field}' in result")
            return False
    
    # Validate data types
    if not isinstance(result['run_number'], int):
        logger.warning("'run_number' should be an integer")
        return False
    
    if not isinstance(result['processing_duration'], (int, float)):
        logger.warning("'processing_duration' should be a number")
        return False
    
    if not isinstance(result['success'], bool):
        logger.warning("'success' should be a boolean")
        return False
    
    # Validate analysis-specific fields
    analysis_type = result['analysis_type']
    if result['success']:
        if analysis_type == 'groups' and 'groups_analysis' not in result:
            logger.warning("Missing 'groups_analysis' in successful groups result")
            return False
        elif analysis_type == 'socioeconomic' and 'socioeconomic_analysis' not in result:
            logger.warning("Missing 'socioeconomic_analysis' in successful socioeconomic result")
            return False
    
    return True


def create_processing_summary_report(summary: Dict[str, Any], 
                                   output_path: Optional[str] = None) -> str:
    """
    Create detailed processing summary report.
    
    Args:
        summary: Processing summary dictionary
        output_path: Optional path to save report
        
    Returns:
        Report text
    """
    report_lines = [
        "=" * 60,
        "WEBSEARCH METABOLIC PREPROCESSING SUMMARY",
        "=" * 60,
        f"Analysis Type: {summary['analysis_type']}",
        f"Total Diseases: {summary['total_diseases']}",
        f"Processed: {summary['processed']}",
        f"Skipped: {summary['skipped']}",
        f"Failed: {summary['failed']}",
        f"Total Duration: {summary['total_duration']:.2f} seconds",
        f"Start Time: {summary['start_time']}",
        f"End Time: {summary['end_time']}",
        ""
    ]
    
    if summary['processed_diseases']:
        report_lines.extend([
            "PROCESSED DISEASES:",
            "-" * 20
        ])
        for disease in summary['processed_diseases']:
            if disease.get('dry_run'):
                report_lines.append(f"  • {disease['disease_name']} (ORPHA:{disease['orphacode']}) - DRY RUN")
            else:
                report_lines.append(f"  • {disease['disease_name']} (ORPHA:{disease['orphacode']}) - "
                                  f"run{disease['run_number']} - {disease['processing_duration']:.2f}s")
        report_lines.append("")
    
    if summary['skipped_diseases']:
        report_lines.extend([
            "SKIPPED DISEASES:",
            "-" * 17
        ])
        for disease in summary['skipped_diseases']:
            report_lines.append(f"  • {disease['disease_name']} (ORPHA:{disease['orphacode']}) - "
                              f"Reason: {disease['reason']}")
        report_lines.append("")
    
    if summary['failed_diseases']:
        report_lines.extend([
            "FAILED DISEASES:",
            "-" * 16
        ])
        for disease in summary['failed_diseases']:
            report_lines.append(f"  • {disease['disease_name']} (ORPHA:{disease['orphacode']}) - "
                              f"Error: {disease['error']}")
        report_lines.append("")
    
    report_text = "\n".join(report_lines)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logger.info(f"Processing report saved to {output_path}")
    
    return report_text 