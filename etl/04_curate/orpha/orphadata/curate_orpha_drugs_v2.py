#!/usr/bin/env python3
"""
Orpha Drugs Curation Script V2

This script processes Orpha drugs data from the preprocessed directory and generates
curated JSON files for regional and type-based accessibility analysis.

Uses the new boolean-based schema and simple function approach (similar to process_orpha_drugs.py).

Input: data/02_preprocess/orpha/orphadata/orpha_drugs/
Output: data/04_curated/orpha/orphadata/

Generated Files:
- disease2eu_tradename_drugs.json
- disease2all_tradename_drugs.json  
- disease2usa_tradename_drugs.json
- disease2eu_medical_product_drugs.json
- disease2all_medical_product_drugs.json
- disease2usa_medical_product_drugs.json
- drug2name.json
- orpha_drugs_curation_summary.json
"""

import json
import os
import sys
import logging
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# Import our new V2 schemas
from core.schemas.orpha.orphadata.orpha_drugs_v2 import (
    DrugInstanceV2,
    DiseaseDataV2,
    CurationSummaryV2,
    is_tradename_drug_v2,
    is_medical_product_v2,
    is_available_in_region_v2,
    filter_drugs_by_criteria_v2,
    extract_drug_ids_v2,
    create_drug_name_mapping_v2,
    validate_disease_data_v2
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_latest_non_empty_run(disease_dir: Path) -> Tuple[Optional[int], Optional[Dict]]:
    """Get the latest run with non-empty drugs for a disease"""
    run_files = list(disease_dir.glob("run*_disease2orpha_drugs.json"))
    
    if not run_files:
        return None, None
    
    # Sort by run number (descending) to get latest first
    run_files.sort(key=lambda f: int(f.name.split("_")[0].replace("run", "")), reverse=True)
    
    for run_file in run_files:
        try:
            with open(run_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('total_drugs_found', 0) > 0:
                    run_number = int(run_file.name.split("_")[0].replace("run", ""))
                    return run_number, data
        except Exception as e:
            logger.warning(f"Error reading {run_file}: {e}")
    
    return None, None


def load_disease_data_v2(disease_dir: Path) -> Optional[DiseaseDataV2]:
    """Load and validate disease data using new V2 schema"""
    run_number, run_data = get_latest_non_empty_run(disease_dir)
    
    if run_data is None:
        return None
    
    try:
        # Validate using V2 schema
        disease_data = validate_disease_data_v2(run_data)
        return disease_data
    except Exception as e:
        logger.warning(f"Failed to validate disease data for {disease_dir.name}: {e}")
        return None


def aggregate_drugs_by_criteria(diseases_data: Dict[str, DiseaseDataV2], 
                              drug_type: str, 
                              region: str) -> Dict[str, List[str]]:
    """Filter and aggregate drugs by type and region"""
    logger.info(f"Filtering {drug_type} drugs available in {region}...")
    
    filtered_drugs = {}
    
    for orpha_code, disease_data in diseases_data.items():
        # Filter drugs by criteria
        matching_drugs = filter_drugs_by_criteria_v2(disease_data.drugs, drug_type, region)
        
        if matching_drugs:
            # Extract drug IDs
            drug_ids = extract_drug_ids_v2(matching_drugs)
            filtered_drugs[orpha_code] = drug_ids
    
    logger.info(f"Found {len(filtered_drugs)} diseases with {drug_type} drugs ({region})")
    return filtered_drugs


def generate_drug_name_mapping(diseases_data: Dict[str, DiseaseDataV2]) -> Dict[str, str]:
    """Create drug ID to name mapping"""
    logger.info("Generating drug name mapping...")
    
    drug_names = create_drug_name_mapping_v2(diseases_data)
    
    logger.info(f"Generated mapping for {len(drug_names)} unique drugs")
    return drug_names


def save_curated_file(data: Dict[str, Any], filename: str, output_dir: Path) -> None:
    """Save curated data to JSON file with error handling"""
    output_file = output_dir / filename
    
    # Check if file already exists and warn
    if output_file.exists():
        logger.warning(f"File already exists, overwriting: {output_file}")
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {filename}: {len(data)} entries")
        
    except Exception as e:
        logger.error(f"Failed to save {filename}: {e}")
        raise


def curate_orpha_drugs_v2(input_dir: str = "data/02_preprocess/orpha/orphadata/orpha_drugs",
                         output_dir: str = "data/04_curated/orpha/orphadata") -> Dict[str, Any]:
    """Main curation function - aggregate drug data and generate curated files"""
    
    preprocessing_dir = Path(input_dir)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting Orpha drugs curation V2...")
    logger.info(f"Input: {preprocessing_dir}")
    logger.info(f"Output: {output_dir_path}")
    
    # Data structures for aggregation
    diseases_data = {}
    processing_stats = {
        "total_diseases_processed": 0,
        "diseases_with_drugs": 0,
        "total_unique_drugs": 0,
        "processing_timestamp": datetime.now().isoformat(),
        "empty_diseases": []
    }
    
    # Process each disease directory
    logger.info("Loading disease data...")
    for disease_dir in preprocessing_dir.iterdir():
        if not disease_dir.is_dir():
            continue
            
        orpha_code = disease_dir.name
        processing_stats["total_diseases_processed"] += 1
        
        # Load disease data with V2 schema
        disease_data = load_disease_data_v2(disease_dir)
        
        if disease_data is None:
            processing_stats["empty_diseases"].append(orpha_code)
            logger.debug(f"No valid data found for disease {orpha_code}")
            continue
        
        if len(disease_data.drugs) > 0:
            processing_stats["diseases_with_drugs"] += 1
            diseases_data[orpha_code] = disease_data
            
            logger.debug(f"Processed {disease_data.disease_name} ({orpha_code}): {len(disease_data.drugs)} drugs")
    
    logger.info(f"Loaded {len(diseases_data)} diseases with drugs")
    
    # Generate drug name mapping
    drug_names = generate_drug_name_mapping(diseases_data)
    processing_stats["total_unique_drugs"] = len(drug_names)
    
    # Generate all curated files
    logger.info("Generating curated drug files...")
    
    # Define all combinations of drug types and regions
    drug_types = ["tradename", "medical_product"]
    regions = ["eu", "usa", "all"]
    
    curated_files = {}
    coverage_stats = {
        "tradename_coverage": {},
        "medical_product_coverage": {}
    }
    
    # Generate filtered drug files
    for drug_type in drug_types:
        for region in regions:
            # Generate filtered data
            filtered_drugs = aggregate_drugs_by_criteria(diseases_data, drug_type, region)
            
            # Save to file
            filename = f"disease2{region}_{drug_type}_drugs.json"
            save_curated_file(filtered_drugs, filename, output_dir_path)
            
            # Store for return
            curated_files[filename.replace('.json', '')] = filtered_drugs
            
            # Store coverage stats
            if drug_type == "tradename":
                coverage_stats["tradename_coverage"][region] = len(filtered_drugs)
            else:
                coverage_stats["medical_product_coverage"][region] = len(filtered_drugs)
    
    # Save drug name mapping
    save_curated_file(drug_names, "drug2name.json", output_dir_path)
    curated_files["drug2name"] = drug_names
    
    # Generate summary
    summary = {
        "curation_metadata": {
            **processing_stats,
            **coverage_stats,
        }
    }
    
    save_curated_file(summary, "orpha_drugs_curation_summary.json", output_dir_path)
    curated_files["summary"] = summary
    
    # Print completion summary
    logger.info("Orpha drugs curation V2 completed successfully!")
    logger.info(f"Generated files in: {output_dir_path}")
    logger.info(f"Total diseases processed: {processing_stats['total_diseases_processed']}")
    logger.info(f"Diseases with drugs: {processing_stats['diseases_with_drugs']}")
    logger.info(f"Total unique drugs: {processing_stats['total_unique_drugs']}")
    logger.info(f"Empty diseases: {len(processing_stats['empty_diseases'])}")
    
    return curated_files


def main():
    """
    Main entry point for Orpha drugs curation V2
    """
    parser = argparse.ArgumentParser(description="Curate Orpha drugs data V2 for regional and type accessibility")
    parser.add_argument("--input-dir", default="data/02_preprocess/orpha/orphadata/orpha_drugs",
                       help="Input directory with preprocessed Orpha drugs data")
    parser.add_argument("--output-dir", default="data/04_curated/orpha/orphadata",
                       help="Output directory for curated data")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Run curation
        results = curate_orpha_drugs_v2(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Print summary
        print("\n" + "="*60)
        print("ORPHA DRUGS CURATION V2 SUMMARY")
        print("="*60)
        
        metadata = results["summary"]["curation_metadata"]
        print(f"Total diseases processed: {metadata['total_diseases_processed']}")
        print(f"Diseases with drugs: {metadata['diseases_with_drugs']}")
        print(f"Total unique drugs: {metadata['total_unique_drugs']}")
        
        print(f"\nTradename Drug Coverage:")
        trad_cov = metadata['tradename_coverage']
        print(f"  EU: {trad_cov['eu']} diseases")
        print(f"  USA: {trad_cov['usa']} diseases")
        print(f"  All regions: {trad_cov['all']} diseases")
        
        print(f"\nMedical Product Coverage:")
        med_cov = metadata['medical_product_coverage']
        print(f"  EU: {med_cov['eu']} diseases")
        print(f"  USA: {med_cov['usa']} diseases")
        print(f"  All regions: {med_cov['all']} diseases")
        
        print(f"\nFiles generated in: {args.output_dir}")
        print("- disease2eu_tradename_drugs.json")
        print("- disease2all_tradename_drugs.json") 
        print("- disease2usa_tradename_drugs.json")
        print("- disease2eu_medical_product_drugs.json")
        print("- disease2all_medical_product_drugs.json")
        print("- disease2usa_medical_product_drugs.json")
        print("- drug2name.json")
        print("- orpha_drugs_curation_summary.json")
        
    except Exception as e:
        logger.error(f"Curation failed: {e}")
        raise


if __name__ == "__main__":
    main() 