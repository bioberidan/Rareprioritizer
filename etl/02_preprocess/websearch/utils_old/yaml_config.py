"""
General YAML configuration utility.

This module provides reusable functions for loading, validating, and managing
YAML configuration files across different preprocessing scripts.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import os

logger = logging.getLogger(__name__)


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file with error handling.
    
    Args:
        config_path: Path to YAML configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Successfully loaded configuration from {config_path}")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {config_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config {config_path}: {e}")
        raise


def get_nested_config(config: Dict[str, Any], keys: List[str], 
                     default: Any = None) -> Any:
    """
    Get nested configuration value with dot notation support.
    
    Args:
        config: Configuration dictionary
        keys: List of keys for nested access (e.g., ['websearch', 'metabolic', 'retry'])
        default: Default value if key path doesn't exist
        
    Returns:
        Configuration value or default
        
    Example:
        config = {'websearch': {'metabolic': {'retry': {'max_attempts': 5}}}}
        value = get_nested_config(config, ['websearch', 'metabolic', 'retry', 'max_attempts'])
        # Returns: 5
    """
    current = config
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def validate_required_keys(config: Dict[str, Any], required_keys: List[List[str]], 
                          config_name: str = "configuration") -> None:
    """
    Validate that required configuration keys exist.
    
    Args:
        config: Configuration dictionary
        required_keys: List of key paths that must exist
        config_name: Name for error messages
        
    Raises:
        ValueError: If required keys are missing
        
    Example:
        validate_required_keys(config, [
            ['websearch', 'metabolic', 'input', 'data_source'],
            ['websearch', 'metabolic', 'processing', 'analysis_type']
        ])
    """
    missing_keys = []
    
    for key_path in required_keys:
        if get_nested_config(config, key_path) is None:
            missing_keys.append('.'.join(key_path))
    
    if missing_keys:
        raise ValueError(f"Missing required {config_name} keys: {', '.join(missing_keys)}")


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries with override support.
    
    Args:
        base_config: Base configuration
        override_config: Configuration values to override
        
    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


def expand_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expand environment variables in configuration values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configuration with expanded environment variables
        
    Example:
        config = {'input': {'data_source': '${DATA_DIR}/metabolic.json'}}
        # If DATA_DIR=/data, returns: {'input': {'data_source': '/data/metabolic.json'}}
    """
    if isinstance(config, dict):
        return {key: expand_env_vars(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        return os.path.expandvars(config)
    else:
        return config


def create_default_config_structure() -> Dict[str, Any]:
    """
    Create a default configuration structure template.
    
    Returns:
        Default configuration dictionary structure
    """
    return {
        'input': {
            'data_source': '',
            'use_sample': True
        },
        'processing': {
            'analysis_type': 'socioeconomic',
            'prompts': {},
            'client': {
                'reasoning': {'effort': 'medium'},
                'max_output_tokens': 8000,
                'timeout': 120
            }
        },
        'retry': {
            'max_attempts': 5,
            'initial_wait': 1,
            'max_wait': 60,
            'retry_on_empty': True,
            'retry_on_api_failure': True
        },
        'output': {
            'base_path': 'data/02_preprocess',
            'run_management': True,
            'skip_processed': True,
            'reprocess_empty': True
        },
        'logging': {
            'level': 'INFO',
            'log_progress': True,
            'log_errors': True
        }
    }


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration dictionary to YAML file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
    """
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Configuration saved to {config_path}")
        
    except Exception as e:
        logger.error(f"Error saving configuration to {config_path}: {e}")
        raise 