#!/usr/bin/env python3
"""
Main script for processing Orphanet XML data into separated JSON structure

Usage:
    python disease_preprocessing.py
    
Or with custom paths:
    python disease_preprocessing.py --xml path/to/input.xml --output path/to/output
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.orpha.xml_converter import OrphaXMLConverter, convert_orpha_xml
from utils.orpha.exceptions import OrphaException


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('disease_preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)


def validate_outputs(output_dir: str) -> bool:
    """
    Validate that all required output files were generated
    
    Args:
        output_dir: Directory containing the processed files
        
    Returns:
        bool: True if all files are valid, False otherwise
    """
    output_path = Path(output_dir)
    
    required_files = [
        output_path / "taxonomy" / "structure.json",
        output_path / "taxonomy" / "categories.json",
        output_path / "taxonomy" / "relationships.json",
        output_path / "taxonomy" / "metadata.json",
        output_path / "instances" / "diseases.json",
        output_path / "instances" / "classification_index.json",
        output_path / "instances" / "name_index.json",
        output_path / "cache" / "paths.json",
        output_path / "cache" / "statistics.json"
    ]
    
    all_valid = True
    for file_path in required_files:
        if not file_path.exists():
            logger.error(f"Required file missing: {file_path}")
            all_valid = False
        else:
            # Check if file is valid JSON
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"✓ Valid: {file_path.relative_to(output_path)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {file_path}: {e}")
                all_valid = False
    
    return all_valid


def generate_statistics(output_dir: str) -> dict:
    """
    Generate comprehensive statistics about the processed data
    
    Args:
        output_dir: Directory containing the processed files
        
    Returns:
        dict: Statistics about the processed data
    """
    output_path = Path(output_dir)
    
    # Load statistics from cache
    stats_path = output_path / "cache" / "statistics.json"
    if stats_path.exists():
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    else:
        stats = {}
    
    # Add file sizes
    file_sizes = {}
    for subdir in ["taxonomy", "instances", "cache"]:
        dir_path = output_path / subdir
        if dir_path.exists():
            for file_path in dir_path.glob("*.json"):
                size_mb = file_path.stat().st_size / (1024 * 1024)
                file_sizes[str(file_path.relative_to(output_path))] = f"{size_mb:.2f} MB"
    
    stats["file_sizes"] = file_sizes
    
    # Calculate total size
    total_size_mb = sum(
        (output_path / subdir).stat().st_size / (1024 * 1024)
        for subdir in ["taxonomy", "instances", "cache"]
        if (output_path / subdir).exists()
    )
    stats["total_size_mb"] = f"{total_size_mb:.2f} MB"
    
    return stats


def print_summary(stats: dict) -> None:
    """Print a summary of the processing results"""
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    print(f"\nTotal nodes: {stats.get('total_nodes', 'N/A')}")
    print(f"  - Categories: {stats.get('total_categories', 'N/A')}")
    print(f"  - Diseases: {stats.get('total_diseases', 'N/A')}")
    print(f"\nMax depth: {stats.get('max_depth', 'N/A')}")
    print(f"Average diseases per category: {stats.get('avg_diseases_per_category', 'N/A')}")
    
    if 'diseases_by_level' in stats:
        print("\nDiseases by level:")
        for level, count in sorted(stats['diseases_by_level'].items(), key=lambda x: int(x[0])):
            print(f"  Level {level}: {count} diseases")
    
    if 'categories_by_level' in stats:
        print("\nCategories by level:")
        for level, count in sorted(stats['categories_by_level'].items(), key=lambda x: int(x[0])):
            print(f"  Level {level}: {count} categories")
    
    if 'file_sizes' in stats:
        print("\nFile sizes:")
        for file_path, size in sorted(stats['file_sizes'].items()):
            print(f"  {file_path}: {size}")
    
    print(f"\nTotal size: {stats.get('total_size_mb', 'N/A')}")
    print("="*60)


def main():
    """Main function to orchestrate the disease preprocessing"""
    parser = argparse.ArgumentParser(
        description="Process Orphanet XML data into separated JSON structure"
    )
    parser.add_argument(
        "--xml",
        default="data/input/raw/Metabolicas.xml",
        help="Path to the input XML file (default: data/input/raw/Metabolicas.xml)"
    )
    parser.add_argument(
        "--output",
        default="data/processed",
        help="Output directory for processed files (default: data/processed)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing output files"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing output files without processing"
    )
    
    args = parser.parse_args()
    
    # Convert paths to Path objects
    xml_path = Path(args.xml)
    output_dir = Path(args.output)
    
    # Validate only mode
    if args.validate_only:
        logger.info("Running in validation-only mode")
        if validate_outputs(str(output_dir)):
            logger.info("✓ All output files are valid")
            stats = generate_statistics(str(output_dir))
            print_summary(stats)
            return 0
        else:
            logger.error("✗ Validation failed")
            return 1
    
    # Check if XML file exists
    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return 1
    
    # Check if output already exists
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        logger.warning(f"Output directory {output_dir} already contains files")
        response = input("Do you want to overwrite? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            return 0
    
    try:
        # Start processing
        start_time = datetime.now()
        logger.info(f"Starting disease preprocessing")
        logger.info(f"Input XML: {xml_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Convert XML to JSON
        convert_orpha_xml(str(xml_path), str(output_dir))
        
        # Validate outputs
        if not validate_outputs(str(output_dir)):
            logger.error("Output validation failed")
            return 1
        
        # Generate and display statistics
        stats = generate_statistics(str(output_dir))
        print_summary(stats)
        
        # Calculate processing time
        duration = datetime.now() - start_time
        logger.info(f"✓ Processing completed successfully in {duration.total_seconds():.1f} seconds")
        
        # Save final report
        report_path = output_dir / "processing_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            report = {
                "processing_date": datetime.now().isoformat(),
                "input_file": str(xml_path),
                "output_directory": str(output_dir),
                "duration_seconds": duration.total_seconds(),
                "statistics": stats
            }
            json.dump(report, f, indent=2)
        
        logger.info(f"Processing report saved to {report_path}")
        
        return 0
        
    except OrphaException as e:
        logger.error(f"Processing failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 