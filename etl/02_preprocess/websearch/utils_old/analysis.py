"""
Analysis functions with retry logic for websearch preprocessing.

This module provides functions for running different types of analysis
(groups, socioeconomic, clinical) with retry logic and error handling.
"""

import logging
from typing import Dict, Any, Union
from datetime import datetime

from core.infrastructure.agents import WebSearcher
from core.infrastructure.utils.retry import (
    EmptySearchError, AnalysisError, APIError, create_retry_wrapper
)
from core.infrastructure.prompts import Prompter

# Register prompts by importing the prompt registry  
# This triggers the @register_prompt decorators
import importlib
importlib.import_module('etl.02_preprocess.websearch.prompts.prompt_registry')

logger = logging.getLogger(__name__)


def run_groups_analysis(disease: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run CIBERER research groups analysis for a disease.
    
    Args:
        disease: Disease dictionary with 'disease_name' and 'orpha_code'
        config: Configuration dictionary
        
    Returns:
        Dictionary containing groups analysis result
        
    Raises:
        EmptySearchError: If search returns empty results
        AnalysisError: If analysis processing fails
        APIError: If API call fails
    """
    # Get prompt alias from config
    prompt_alias = config['websearch']['metabolic']['processing']['prompts']['groups']
    client_config = config['websearch']['metabolic']['processing']['client']
    
    # Initialize WebSearcher
    searcher = WebSearcher(
        prompt_alias=prompt_alias,
        client_kwargs=client_config
    )
    
    # Prepare template data
    template_data = {
        'disease_name': disease['disease_name'],
        'orphacode': disease['orpha_code']
    }
    
    logger.info(f"Running groups analysis for {disease['disease_name']} (ORPHA:{disease['orpha_code']})")
    
    # Execute search
    result = searcher.search(template_data)
    
    # Check for empty search
    if hasattr(result, 'is_empty_search') and result.is_empty_search():
        raise EmptySearchError(f"Groups analysis returned empty results for {disease['disease_name']}")
    
    # Convert to dictionary
    if hasattr(result, 'model_dump'):
        result_dict = result.model_dump()
    elif hasattr(result, 'dict'):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    
    logger.info(f"Groups analysis completed for {disease['disease_name']}")
    return result_dict


def run_socioeconomic_analysis(disease: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run socioeconomic impact analysis for a disease.
    
    Args:
        disease: Disease dictionary with 'disease_name' and 'orpha_code'
        config: Configuration dictionary
        
    Returns:
        Dictionary containing socioeconomic analysis result
        
    Raises:
        EmptySearchError: If search returns empty results
        AnalysisError: If analysis processing fails
        APIError: If API call fails
    """
    # Get prompt alias from config
    prompt_alias = config['websearch']['metabolic']['processing']['prompts']['socioeconomic']
    client_config = config['websearch']['metabolic']['processing']['client']
    
    # Initialize WebSearcher
    searcher = WebSearcher(
        prompt_alias=prompt_alias,
        client_kwargs=client_config
    )
    
    # Prepare template data
    template_data = {
        'disease_name': disease['disease_name'],
        'orphacode': disease['orpha_code']
    }
    
    logger.info(f"Running socioeconomic analysis for {disease['disease_name']} (ORPHA:{disease['orpha_code']})")
    
    # Execute search
    result = searcher.search(template_data)
    
    # Check for empty search
    if hasattr(result, 'is_empty_search') and result.is_empty_search():
        raise EmptySearchError(f"Socioeconomic analysis returned empty results for {disease['disease_name']}")
    
    # Convert to dictionary
    if hasattr(result, 'model_dump'):
        result_dict = result.model_dump()
    elif hasattr(result, 'dict'):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    
    logger.info(f"Socioeconomic analysis completed for {disease['disease_name']}")
    return result_dict


def run_clinical_analysis(disease: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run clinical research analysis for a disease (future implementation).
    
    Args:
        disease: Disease dictionary with 'disease_name' and 'orpha_code'
        config: Configuration dictionary
        
    Returns:
        Dictionary containing clinical analysis result
        
    Raises:
        NotImplementedError: Clinical analysis not yet implemented
    """
    logger.warning(f"Clinical analysis not yet implemented for {disease['disease_name']}")
    raise NotImplementedError("Clinical analysis is not yet implemented")


def run_analysis_with_retry(analysis_func: callable, disease: Dict[str, str], 
                           config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper to run any analysis with retry logic.
    
    Args:
        analysis_func: Analysis function to run
        disease: Disease dictionary
        config: Configuration dictionary
        
    Returns:
        Analysis result dictionary
        
    Raises:
        AnalysisError: If analysis fails after all retries
    """
    retry_config = config['websearch']['metabolic']['retry']
    max_attempts = retry_config['max_attempts']
    retry_on_empty = retry_config['retry_on_empty']
    retry_on_api_failure = retry_config['retry_on_api_failure']
    
    # Create retry wrapper
    retry_wrapper = create_retry_wrapper(
        analysis_func,
        attempts=max_attempts,
        retry_on_empty=retry_on_empty,
        retry_on_api_failure=retry_on_api_failure
    )
    
    return retry_wrapper(disease, config)


def select_analysis(analysis_type: str, disease: Dict[str, str], 
                   config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select and run the appropriate analysis based on type with retry.
    
    Args:
        analysis_type: Type of analysis ("groups", "socioeconomic", "clinical")
        disease: Disease dictionary
        config: Configuration dictionary
        
    Returns:
        Analysis result dictionary
        
    Raises:
        ValueError: If analysis type is invalid
        AnalysisError: If analysis fails
    """
    analysis_functions = {
        'groups': run_groups_analysis,
        'socioeconomic': run_socioeconomic_analysis,
        'clinical': run_clinical_analysis
    }
    
    if analysis_type not in analysis_functions:
        valid_types = list(analysis_functions.keys())
        raise ValueError(f"Invalid analysis type '{analysis_type}'. Valid types: {valid_types}")
    
    analysis_func = analysis_functions[analysis_type]
    
    logger.info(f"Selected {analysis_type} analysis for {disease['disease_name']}")
    
    # Run with retry logic
    return run_analysis_with_retry(analysis_func, disease, config)


def create_empty_search_error(analysis_type: str, disease_name: str) -> EmptySearchError:
    """
    Create custom exception for empty search results.
    
    Args:
        analysis_type: Type of analysis that failed
        disease_name: Name of the disease
        
    Returns:
        EmptySearchError instance
    """
    return EmptySearchError(f"{analysis_type.title()} analysis returned empty results for {disease_name}")


def validate_analysis_result(result: Dict[str, Any], analysis_type: str) -> bool:
    """
    Validate analysis result and check for empty responses.
    
    Args:
        result: Analysis result dictionary
        analysis_type: Type of analysis
        
    Returns:
        True if result is valid, False otherwise
    """
    if not isinstance(result, dict):
        logger.warning(f"Analysis result is not a dictionary: {type(result)}")
        return False
    
    # Basic validation
    required_fields = ['orphacode', 'disease_name']
    for field in required_fields:
        if field not in result:
            logger.warning(f"Missing required field '{field}' in {analysis_type} analysis result")
            return False
    
    # Type-specific validation
    if analysis_type == 'groups':
        if 'groups' not in result:
            logger.warning("Missing 'groups' field in groups analysis result")
            return False
        if not isinstance(result['groups'], list):
            logger.warning("'groups' field should be a list")
            return False
    
    elif analysis_type == 'socioeconomic':
        required_socio_fields = ['score', 'evidence_level', 'socioeconomic_impact_studies']
        for field in required_socio_fields:
            if field not in result:
                logger.warning(f"Missing required field '{field}' in socioeconomic analysis result")
                return False
    
    logger.debug(f"Analysis result validation passed for {analysis_type}")
    return True


def log_retry_attempt(disease_name: str, analysis_type: str, 
                     attempt: int, error: str) -> None:
    """
    Log retry attempts for monitoring.
    
    Args:
        disease_name: Name of the disease
        analysis_type: Type of analysis
        attempt: Current attempt number
        error: Error message
    """
    logger.warning(f"Retry attempt {attempt} for {analysis_type} analysis of {disease_name}: {error}")


def create_analysis_metadata(disease: Dict[str, str], analysis_type: str, 
                           start_time: datetime, end_time: datetime,
                           success: bool, error: str = None) -> Dict[str, Any]:
    """
    Create metadata for analysis result.
    
    Args:
        disease: Disease dictionary
        analysis_type: Type of analysis
        start_time: Analysis start time
        end_time: Analysis end time
        success: Whether analysis succeeded
        error: Error message if failed
        
    Returns:
        Metadata dictionary
    """
    duration = (end_time - start_time).total_seconds()
    
    metadata = {
        'analysis_type': analysis_type,
        'processing_timestamp': end_time.isoformat(),
        'processing_duration': round(duration, 2),
        'success': success,
        'error_details': error
    }
    
    return metadata 