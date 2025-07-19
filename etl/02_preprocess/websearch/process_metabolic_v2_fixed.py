#!/usr/bin/env python3
"""
WebSearch Metabolic Disease Preprocessing Script - Fixed Version

This script processes metabolic diseases through websearch analysis using
simplified configuration and minimal utility functions.

Usage:
    python process_metabolic_v2_fixed.py --analysis groups
    python process_metabolic_v2_fixed.py --analysis groups --force-reprocess
    python process_metabolic_v2_fixed.py --analysis groups --dry-run --verbose
"""

#!/usr/bin/env python3

import sys
import logging
import argparse
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

try:
    # Try relative imports (when run as module)
    from ....core.infrastructure.utils.retry import create_retry_wrapper, EmptySearchError
    from ....core.infrastructure.agents.web_searcher import WebSearcher
    from ....core.infrastructure.prompts.prompter import Prompter
except ImportError:
    # Fallback for direct execution
    current_dir = Path(__file__).parent
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from core.infrastructure.utils.retry import create_retry_wrapper, EmptySearchError
    from core.infrastructure.agents.web_searcher import WebSearcher
    from core.infrastructure.prompts.prompter import Prompter

# Register prompts by importing the prompt registry  
import importlib
try:
    importlib.import_module('etl.02_preprocess.websearch.prompts.prompt_registry')
except ImportError:
    # Try different path
    importlib.import_module('prompts.prompt_registry')


# ============================================================================
# MINIMAL UTILITY FUNCTIONS (copied from existing modules)
# ============================================================================

def load_simplified_config(config_path: str) -> dict:
    """Load simplified configuration without nested metabolic key."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required keys
    required_keys = ['input', 'output', 'prompt_alias', 'analysis_type', 'retry', 'client']
    for key in required_keys:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")
    
    return config


def load_diseases(input_file: str) -> list:
    """Load diseases from JSON file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
    
    # Validate structure
    if not isinstance(diseases, list):
        raise ValueError(f"Expected list of diseases, got {type(diseases)}")
    
    for disease in diseases:
        if 'disease_name' not in disease or 'orpha_code' not in disease:
            raise ValueError("Disease missing required fields: disease_name, orpha_code")
    
    return diseases


def should_skip_disease(orphacode: str, base_path: Path, force_reprocess: bool) -> bool:
    """Check if disease should be skipped based on existing runs."""
    if force_reprocess:
        return False
    
    disease_dir = base_path / orphacode
    if not disease_dir.exists():
        return False
    
    # Check for existing run files (same pattern as process_metabolic.py)
    run_files = list(disease_dir.glob("run*.json"))
    return len(run_files) > 0


def get_next_run_number(orphacode: str, base_path: Path) -> int:
    """Get the next run number for a disease."""
    disease_dir = base_path / orphacode
    if not disease_dir.exists():
        return 1
    
    run_files = list(disease_dir.glob("run*.json"))
    if not run_files:
        return 1
    
    # Extract run numbers and find the maximum
    run_numbers = []
    for file_path in run_files:
        try:
            run_num = int(file_path.stem.replace('run', ''))
            run_numbers.append(run_num)
        except ValueError:
            continue
    
    return max(run_numbers) + 1 if run_numbers else 1


def save_disease_result(result: dict, orphacode: str, run_number: int, base_path: Path) -> Path:
    """Save disease analysis result to file."""
    disease_dir = base_path / orphacode
    disease_dir.mkdir(parents=True, exist_ok=True)
    
    # Use same naming pattern as process_metabolic.py
    file_path = disease_dir / f"run{run_number}.json"
    
    # Add metadata to result
    result['metadata'] = {
        'processing_timestamp': datetime.now().isoformat(),
        'run_number': run_number,
        'orphacode': orphacode
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    return file_path


def create_simple_summary_report(summary: dict) -> str:
    """Create a simple summary report."""
    duration = "Unknown"
    if 'start_time' in summary and 'end_time' in summary:
        try:
            start = datetime.fromisoformat(summary['start_time'])
            end = datetime.fromisoformat(summary['end_time'])
            duration = f"{(end - start).total_seconds():.1f} seconds"
        except:
            pass
    
    success_rate = 0
    if summary['total_diseases'] > 0:
        success_rate = (summary['processed'] / summary['total_diseases'] * 100)
    
    report = f"""
Processing Summary Report
========================

Analysis Type: {summary.get('analysis_type', 'Unknown')}
Start Time: {summary.get('start_time', 'Unknown')}
End Time: {summary.get('end_time', 'Unknown')}
Duration: {duration}

Results:
- Total Diseases: {summary['total_diseases']}
- Processed: {summary['processed']}
- Skipped: {summary['skipped']}
- Failed: {summary['failed']}

Success Rate: {success_rate:.1f}%
"""
    
    if summary['failed_diseases']:
        report += "\nFailed Diseases:\n"
        for disease in summary['failed_diseases']:
            report += f"- {disease['disease_name']} (ORPHA:{disease['orphacode']}): {disease['error']}\n"
    
    return report


# ============================================================================
# CORE PROCESSING FUNCTIONS
# ============================================================================

def process_single_disease(disease_data: dict, searcher: WebSearcher) -> dict:
    """Process a single disease with WebSearcher."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Running search for {disease_data['disease_name']}")
    result = searcher.search(disease_data)
    logger.info(f"Search completed for {disease_data['disease_name']}")
    
    # Check for empty search
    if hasattr(result, 'is_empty_search') and result.is_empty_search():
        raise EmptySearchError(f"Analysis returned empty results for {disease_data['disease_name']}")
    
    # Convert to dictionary
    if hasattr(result, 'model_dump'):
        result_dict = result.model_dump()
    elif hasattr(result, 'dict'):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    
    logger.info(f"Search processing completed for {disease_data['disease_name']}")
    return result_dict


def setup_logging(level: str = "INFO", verbose: bool = False) -> None:
    """Setup logging configuration."""
    if verbose:
        level = "DEBUG"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='WebSearch Metabolic Disease Preprocessing (Simplified)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analysis groups
  %(prog)s --analysis groups --force-reprocess
  %(prog)s --analysis groups --dry-run
  %(prog)s --prompt-alias custom_prompt --verbose
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--analysis',
        choices=['groups', 'socioeconomic', 'clinical'],
        required=True,
        help='Analysis type to run'
    )
    
    # Configuration arguments
    default_config = 'conf/config_metabolic_simple.yaml'
    parser.add_argument(
        '--config',
        default=default_config,
        help='Path to simplified YAML configuration file'
    )
    
    parser.add_argument(
        '--input',
        help='Path to input JSON file (overrides config)'
    )
    
    parser.add_argument(
        '--output',
        help='Base output directory (overrides config)'
    )
    
    parser.add_argument(
        '--prompt-alias',
        help='Override prompt alias from config'
    )
    
    # Run management arguments
    parser.add_argument(
        '--run',
        type=int,
        help='Specific run number to use (overwrites if exists)'
    )
    
    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Reprocess even if results exist (increments run number)'
    )
    
    # Processing arguments
    parser.add_argument(
        '--max-retries',
        type=int,
        help='Override retry attempts from config'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be processed without execution'
    )
    
    # Utility arguments
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def override_config_from_args(config: dict, args: argparse.Namespace) -> dict:
    """Override configuration with command line arguments."""
    overrides = {}
    
    # Override analysis type
    if args.analysis:
        overrides['analysis_type'] = args.analysis
    
    # Override prompt alias
    if args.prompt_alias:
        overrides['prompt_alias'] = args.prompt_alias
    
    # Override input file
    if args.input:
        overrides['input'] = {'data_source': args.input}
    
    # Override output path
    if args.output:
        overrides['output'] = {'base_path': args.output}
    
    # Override retry attempts
    if args.max_retries:
        if 'retry' not in overrides:
            overrides['retry'] = config.get('retry', {}).copy()
        overrides['retry']['max_attempts'] = args.max_retries
    
    if overrides:
        # Simple merge for flat structure
        for key, value in overrides.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                config[key].update(value)
            else:
                config[key] = value
        logging.info("Configuration overridden with command line arguments")
    
    return config


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function for metabolic websearch preprocessing."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Load configuration using simplified structure
    config = load_simplified_config(args.config)
    
    # Setup logging
    log_level = config.get('logging', {}).get('level', 'INFO')
    setup_logging(log_level, args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting WebSearch Metabolic Disease Preprocessing (Simplified)")
    
    # Override config with command line arguments
    config = override_config_from_args(config, args)
    
    # Load diseases using simplified config structure
    input_file = config['input']['data_source']
    diseases = load_diseases(input_file)
    logger.info(f"Loaded {len(diseases)} diseases from {input_file}")
    
    # Define base_path using simplified config structure
    base_path = Path(config['output']['base_path'])
    
    # Show configuration if verbose
    if args.dry_run or args.verbose:
        logger.info(f"Analysis Type: {args.analysis}")
        logger.info(f"Input File: {input_file}")
        logger.info(f"Output Path: {base_path}")
        logger.info(f"Prompt Alias: {config['prompt_alias']}")
        logger.info(f"Force Reprocess: {args.force_reprocess}")
        logger.info(f"Dry Run: {args.dry_run}")

    # Initialize processing variables
    force_reprocess = args.force_reprocess
    specific_run = args.run
    dry_run = args.dry_run   

    # Setup retry logic using simplified config structure
    retry_config = config['retry']
    max_attempts = retry_config['max_attempts']
    retry_on_empty = retry_config['retry_on_empty']
    retry_on_api_failure = retry_config['retry_on_api_failure']

    process_disease_with_retry = create_retry_wrapper(
        process_single_disease,
        attempts=max_attempts,
        retry_on_empty=retry_on_empty,
        retry_on_api_failure=retry_on_api_failure
    )

    # Initialize summary
    summary = {
        'total_diseases': len(diseases),
        'processed': 0,
        'skipped': 0,
        'failed': 0,
        'analysis_type': args.analysis,
        'start_time': datetime.now().isoformat(),
        'processed_diseases': [],
        'skipped_diseases': [],
        'failed_diseases': []
    }

    # Initialize WebSearcher using simplified config structure
    prompt_alias = config['prompt_alias']
    client_config = config['client']
    
    searcher = WebSearcher(
        prompt_alias=prompt_alias,
        client_kwargs=client_config
    )
       
    # Main processing loop
    for disease in diseases:
        orphacode = disease['orpha_code']
        disease_name = disease['disease_name']
        
        logger.info(f"Processing {disease_name} (ORPHA:{orphacode})")
        
        # Check if should skip
        if not force_reprocess and not specific_run:
            if should_skip_disease(orphacode, base_path, force_reprocess):
                summary['skipped'] += 1
                summary['skipped_diseases'].append({
                    'orphacode': orphacode,
                    'disease_name': disease_name,
                    'reason': 'existing_runs'
                })
                logger.info(f"Skipping {disease_name} - already processed")
                continue
        
        # Determine run number
        if specific_run:
            run_number = specific_run
            logger.info(f"Using specific run number {run_number} for {disease_name}")
        else:
            run_number = get_next_run_number(orphacode, base_path)
            logger.info(f"Using next run number {run_number} for {disease_name}")
        
        if dry_run:
            logger.info(f"DRY RUN: Would process {disease_name} (run {run_number})")
            summary['processed'] += 1
            summary['processed_diseases'].append({
                'orphacode': orphacode,
                'disease_name': disease_name,
                'run_number': run_number,
                'dry_run': True
            })
            continue
        
        # Process disease with retry
        result = process_disease_with_retry(disease, searcher)
        
        # Save result
        file_path = save_disease_result(result, orphacode, run_number, base_path)
        
        summary['processed'] += 1
        summary['processed_diseases'].append({
            'orphacode': orphacode,
            'disease_name': disease_name,
            'run_number': run_number,
            'file_path': str(file_path),
            'success': True
        })
        
        logger.info(f"Successfully processed {disease_name}")
    
    # Finalize summary
    summary['end_time'] = datetime.now().isoformat()
    
    # Create and display summary report
    report = create_simple_summary_report(summary)
    print(report)
    
    # Log completion
    logger.info(f"Processing complete: {summary['processed']} processed, "
               f"{summary['skipped']} skipped, {summary['failed']} failed")
    
    # Return appropriate exit code
    return 1 if summary['failed'] > 0 else 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 