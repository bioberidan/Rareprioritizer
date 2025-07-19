#!/usr/bin/env python3
"""
WebSearch Metabolic Disease Preprocessing Script

This script processes metabolic diseases through websearch analysis using
WebSearcher agents with retry logic, run management, and configuration-driven
analysis type selection.

Usage:
    python preprocess_metabolic.py --analysis socioeconomic
    python preprocess_metabolic.py --analysis groups --force-reprocess
    python preprocess_metabolic.py --analysis groups --dry-run --verbose
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

try:
    # Try relative imports (when run as module)
    from .utils.processing import (
        load_config, load_diseases, process_diseases, create_processing_summary_report
    )
    from .utils.yaml_config import get_nested_config, merge_configs
    from .utils.run_management import list_all_disease_runs, get_disease_run_summary
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    # Add both current directory and project root to Python path
    current_dir = Path(__file__).parent
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(project_root))
    
    from utils.processing import (
        load_config, load_diseases, process_diseases, create_processing_summary_report
    )
    from utils.yaml_config import get_nested_config, merge_configs
    from utils.run_management import list_all_disease_runs, get_disease_run_summary


def setup_logging(level: str = "INFO", verbose: bool = False) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        verbose: Enable verbose logging
    """
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


def validate_analysis_type(analysis_type: str) -> str:
    """
    Validate analysis type.
    
    Args:
        analysis_type: Analysis type to validate
        
    Returns:
        Validated analysis type
        
    Raises:
        ValueError: If analysis type is invalid
    """
    valid_types = ['groups', 'socioeconomic', 'clinical']
    
    if analysis_type not in valid_types:
        raise ValueError(f"Invalid analysis type '{analysis_type}'. Valid types: {valid_types}")
    
    return analysis_type


def override_config_from_args(config: dict, args: argparse.Namespace) -> dict:
    """
    Override configuration with command line arguments.
    
    Args:
        config: Base configuration
        args: Command line arguments
        
    Returns:
        Updated configuration
    """
    overrides = {}
    
    # Override analysis type
    if args.analysis:
        overrides['websearch'] = {
            'metabolic': {
                'processing': {
                    'analysis_type': args.analysis
                }
            }
        }
    
    # Override input file
    if args.input:
        if 'websearch' not in overrides:
            overrides['websearch'] = {'metabolic': {}}
        if 'metabolic' not in overrides['websearch']:
            overrides['websearch']['metabolic'] = {}
        overrides['websearch']['metabolic']['input'] = {'data_source': args.input}
    
    # Override output path
    if args.output:
        if 'websearch' not in overrides:
            overrides['websearch'] = {'metabolic': {}}
        if 'metabolic' not in overrides['websearch']:
            overrides['websearch']['metabolic'] = {}
        overrides['websearch']['metabolic']['output'] = {'base_path': args.output}
    
    # Override retry attempts
    if args.max_retries:
        if 'websearch' not in overrides:
            overrides['websearch'] = {'metabolic': {}}
        if 'metabolic' not in overrides['websearch']:
            overrides['websearch']['metabolic'] = {}
        overrides['websearch']['metabolic']['retry'] = {'max_attempts': args.max_retries}
    
    if overrides:
        config = merge_configs(config, overrides)
        logging.info("Configuration overridden with command line arguments")
    
    return config


def show_disease_status(config: dict) -> None:
    """
    Show status of diseases and existing runs.
    
    Args:
        config: Configuration dictionary
    """
    base_path = config['websearch']['metabolic']['output']['base_path']
    disease_runs = list_all_disease_runs(base_path)
    
    if not disease_runs:
        print("No existing disease runs found.")
        return
    
    print(f"\nExisting Disease Runs in {base_path}:")
    print("=" * 60)
    
    for orphacode, summary in disease_runs.items():
        print(f"ORPHA:{orphacode}")
        print(f"  Runs: {summary['existing_runs']}")
        print(f"  Next run: {summary['next_run_number']}")
        print(f"  Directory: {summary['disease_directory']}")
        
        for run_file in summary['run_files']:
            status = "✓" if run_file['is_valid'] else "✗"
            size_mb = run_file['file_size'] / 1024 / 1024
            print(f"    {status} run{run_file['run_number']} ({size_mb:.2f} MB)")
        print()


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='WebSearch Metabolic Disease Preprocessing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --analysis socioeconomic
  %(prog)s --analysis groups --force-reprocess
  %(prog)s --analysis clinical --dry-run
  %(prog)s --analysis groups --run 2 --verbose
  %(prog)s --status
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--analysis',
        choices=['groups', 'socioeconomic', 'clinical'],
        help='Analysis type to run (required unless using --status)'
    )
    
    # Configuration arguments
    # Set default config path based on execution context
    default_config = 'conf/config_metabolic.yaml' if Path('conf/config_metabolic.yaml').exists() else 'etl/02_preprocess/websearch/conf/config_metabolic.yaml'
    
    parser.add_argument(
        '--config',
        default=default_config,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--input',
        help='Path to input JSON file (overrides config)'
    )
    
    parser.add_argument(
        '--output',
        help='Base output directory (overrides config)'
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
        '--status',
        action='store_true',
        help='Show status of existing disease runs and exit'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def initial_log(analysis_type: str, input_file: str, config: dict, args: argparse.Namespace) -> None:
    """
    Log initial processing configuration.
    
    Args:
        analysis_type: Type of analysis being performed
        input_file: Path to input file
        config: Configuration dictionary
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Processing Configuration:")
    logger.info(f"  Analysis Type: {analysis_type}")
    logger.info(f"  Input File: {input_file}")
    logger.info(f"  Output Path: {config['websearch']['metabolic']['output']['base_path']}")
    logger.info(f"  Force Reprocess: {args.force_reprocess}")
    logger.info(f"  Specific Run: {args.run}")
    logger.info(f"  Max Retries: {config['websearch']['metabolic']['retry']['max_attempts']}")
    logger.info(f"  Dry Run: {args.dry_run}")

def process_single_disease(disease_data: dict, searcher: WebSearcher) -> dict:
    logger.info(f"running search for {disease_data['disease_name']}")
    result = searcher.search(disease_data)
    logger.info(f"search completed for {disease_data['disease_name']}, go to test if empty")
    # Check for empty search
    if hasattr(result, 'is_empty_search') and result.is_empty_search():
        raise EmptySearchError(f"Groups analysis returned empty results for {disease['disease_name']}")
    
    if hasattr(result, 'model_dump'):
        result_dict = result.model_dump()
    elif hasattr(result, 'dict'):
        result_dict = result.dict()
    else:
        result_dict = dict(result)
    
    logger.info(f"search completed for {disease_data['disease_name']}")
    return result_dict


def main():
    """Main function for metabolic websearch preprocessing."""
    
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not args.status and not args.analysis:
        parser.error("--analysis is required unless using --status")
    
    # Load configuration
    config = load_config(args.config)
    
    # Setup logging
    log_level = get_nested_config(config, ['websearch', 'metabolic', 'logging', 'level'], 'INFO')
    setup_logging(log_level, args.verbose)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting WebSearch Metabolic Disease Preprocessing")
    
    # Override config with command line arguments
    config = override_config_from_args(config, args)
    
    # Handle status request
    if args.status:
        show_disease_status(config)
        return 0
    
    # Validate analysis type
    analysis_type = validate_analysis_type(args.analysis)
    logger.info(f"Selected analysis type: {analysis_type}")
    
    # Load diseases
    input_file = config['websearch']['metabolic']['input']['data_source']
    diseases = load_diseases(input_file)
    logger.info(f"Loaded {len(diseases)} diseases from {input_file}")
    
    # Show what will be processed



    
    if args.dry_run or args.verbose:
        initial_log(analysis_type, input_file, config, args)


    force_reprocess=args.force_reprocess
    specific_run=args.run
    dry_run=args.dry_run   


    retry_config = config['websearch']['metabolic']['retry']
    max_attempts = retry_config['max_attempts']
    retry_on_empty = retry_config['retry_on_empty']
    retry_on_api_failure = retry_config['retry_on_api_failure']

    process_disease_with_retry = create_retry_wrapper(
    process_single_disease,
    attempts=max_attempts,
    retry_on_empty=retry_on_empty,
    retry_on_api_failure=retry_on_api_failure
    )

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

    prompt_alias = config['websearch']['metabolic']['processing']['prompts']['groups']
    client_config = config['websearch']['metabolic']['processing']['client']
    

    searcher = WebSearcher(
        prompt_alias=prompt_alias,
        client_kwargs=client_config
    )
       
    for disease in diseases:
        orphacode = disease['orpha_code']
        disease_name = disease['disease_name']
    
    
        logger.info(f"Running {analysis_type} analysis for {disease_name} (ORPHA:{orphacode})")
    
        # Check if should skip
        if not force_reprocess and not specific_run:
            if should_skip_disease(orphacode, base_path, force_reprocess):
                summary['skipped'] += 1
                summary['skipped_diseases'].append({
                    'orphacode': orphacode,
                    'disease_name': disease_name,
                    'reason': 'existing_runs'
                })
                print(f"Skipping {disease_name} (ORPHA:{orphacode}) because it already has runs")
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
        
        result = process_disease_with_retry(disease, searcher)
        file_path = save_disease_result(result, base_path)



    
    
    # Create and display summary report
    report = create_processing_summary_report(summary)
    print(report)
    
    # Save summary report if not dry run
    if not args.dry_run:
        from .utils.io import create_timestamped_filename
        report_filename = create_timestamped_filename(
            f"metabolic_{analysis_type}_summary", ".txt"
        )
        report_path = Path(config['websearch']['metabolic']['output']['base_path']) / "reports" / report_filename
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Summary report saved to {report_path}")
    
    # Exit with appropriate code
    if summary['failed'] > 0:
        logger.warning(f"Processing completed with {summary['failed']} failures")
        return 1
    else:
        logger.info("Processing completed successfully")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 