#!/usr/bin/env python3
"""
Orpha Drugs Curation Script

This script processes Orpha drugs data from the processed directory and generates
curated JSON files for regional and type-based accessibility analysis.

Input: data/03_processed/orpha/orphadata/orpha_drugs/
Output: data/04_curated/orpha/orphadata/

Generated Files:
- disease2eu_tradename_drugs.json
- disease2all_tradename_drugs.json  
- disease2usa_tradename_drugs.json
- disease2eu_medical_product_drugs.json
- disease2all_medical_product_drugs.json
- disease2usa_medical_product_drugs.json
- drug2name.json
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any
from datetime import datetime

# Import our schemas for validation
from core.schemas.orpha.orphadata.orpha_drugs import (
    DrugInstance,
    DrugMapping,
    CuratedDrugMapping,
    is_tradename_drug,
    is_medical_product,
    is_available_in_region
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrphaDrugsCurator:
    """
    Curator for Orpha drugs data - generates regional and type-based accessibility files
    """
    
    def __init__(self, input_dir: str = "data/03_processed/orpha/orphadata/orpha_drugs",
                 output_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the Orpha drugs curator
        
        Args:
            input_dir: Directory containing processed Orpha drugs data
            output_dir: Directory for curated output files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized OrphaDrugsCurator")
        logger.info(f"Input: {self.input_dir}")
        logger.info(f"Output: {self.output_dir}")
    
    def load_processed_data(self) -> Dict[str, Any]:
        """
        Load all processed Orpha drugs data
        
        Returns:
            Dict containing loaded data
        """
        logger.info("Loading processed Orpha drugs data...")
        
        # Load diseases2drugs.json
        diseases2drugs_file = self.input_dir / "diseases2drugs.json"
        if not diseases2drugs_file.exists():
            raise FileNotFoundError(f"Required file not found: {diseases2drugs_file}")
        
        with open(diseases2drugs_file, 'r', encoding='utf-8') as f:
            diseases2drugs = json.load(f)
        
        # Load drug_index.json  
        drugs_index_file = self.input_dir / "drug_index.json"
        if not drugs_index_file.exists():
            raise FileNotFoundError(f"Required file not found: {drugs_index_file}")
        
        with open(drugs_index_file, 'r', encoding='utf-8') as f:
            drugs_index = json.load(f)
        
        # Load drugs2diseases.json
        drugs2diseases_file = self.input_dir / "drugs2diseases.json"
        if not drugs2diseases_file.exists():
            raise FileNotFoundError(f"Required file not found: {drugs2diseases_file}")
        
        with open(drugs2diseases_file, 'r', encoding='utf-8') as f:
            drugs2diseases = json.load(f)
        
        logger.info(f"Loaded {len(diseases2drugs)} diseases with drugs")
        logger.info(f"Loaded {len(drugs_index)} unique drugs")
        
        return {
            'diseases2drugs': diseases2drugs,
            'drugs_index': drugs_index,
            'drugs2diseases': drugs2diseases
        }
    
    def validate_and_normalize_drug(self, drug_data: Dict[str, Any]) -> DrugInstance:
        """
        Validate and normalize drug data using Pydantic schema
        
        Args:
            drug_data: Raw drug data from processed files
            
        Returns:
            Validated DrugInstance
        """
        # Create normalized drug instance
        drug = DrugInstance(
            drug_id=drug_data.get('drug_id', drug_data.get('id', '')),
            substance_id=drug_data.get('substance_id'),
            drug_name=drug_data.get('drug_name', drug_data.get('name', '')),
            status=drug_data.get('status', 'Unknown'),
            drug_type=drug_data.get('drug_type'),
            regions=drug_data.get('regions', []),
            substance_url=drug_data.get('substance_url'),
            regulatory_id=drug_data.get('regulatory_id'),
            regulatory_url=drug_data.get('regulatory_url'),
            manufacturer=drug_data.get('manufacturer'),
            indication=drug_data.get('indication'),
            diseases=drug_data.get('diseases', []),
            links=drug_data.get('links', []),
            details=drug_data.get('details', []),
            processing_metadata={'source': 'processed_data', 'curated_timestamp': datetime.now().isoformat()}
        )
        
        return drug
    
    def filter_drugs_by_criteria(self, diseases2drugs: Dict[str, Any], 
                                drugs_index: Dict[str, Any],
                                status_filter: str, 
                                region_filter: str) -> Dict[str, List[str]]:
        """
        Filter drugs by status and region criteria
        
        Args:
            diseases2drugs: Disease to drugs mapping
            drugs_index: Complete drugs index
            status_filter: Drug status filter ("Tradename", "Medicinal product")
            region_filter: Region filter ("US", "EU", "ALL")
            
        Returns:
            Dict mapping disease codes to filtered drug IDs
        """
        logger.info(f"Filtering {status_filter} drugs accessible from {region_filter}...")
        
        filtered_drugs = {}
        
        for orpha_code, disease_data in diseases2drugs.items():
            # Get the drugs list from disease data
            drugs_list = disease_data.get('drugs', [])
            if not drugs_list:
                continue
            
            filtered_drug_ids = []
            
            for drug_id in drugs_list:
                # Get full drug details from index
                drug_detail = drugs_index.get(drug_id, {})
                
                # Validate and normalize drug data
                try:
                    normalized_drug = self.validate_and_normalize_drug(drug_detail)
                    
                    # Check status filter
                    status_match = False
                    if status_filter == "Tradename" and is_tradename_drug(normalized_drug):
                        status_match = True
                    elif status_filter == "Medicinal product" and is_medical_product(normalized_drug):
                        status_match = True
                    
                    # Check region filter  
                    region_match = is_available_in_region(normalized_drug, region_filter)
                    
                    if status_match and region_match:
                        filtered_drug_ids.append(drug_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to validate drug {drug_id}: {e}")
                    
                    # Fallback: check manually
                    status = drug_detail.get('status', '')
                    regions = drug_detail.get('regions', [])
                    
                    status_match = (status == status_filter)
                    region_match = (region_filter.upper() == "ALL" or 
                                  region_filter.upper() in [r.upper() for r in regions])
                    
                    if status_match and region_match:
                        filtered_drug_ids.append(drug_id)
            
            if filtered_drug_ids:
                filtered_drugs[orpha_code] = filtered_drug_ids
        
        logger.info(f"Found {len(filtered_drugs)} diseases with {status_filter} drugs ({region_filter})")
        return filtered_drugs
    
    def extract_drug_names(self, drugs_index: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract drug ID to name mapping
        
        Args:
            drugs_index: Complete drugs index
            
        Returns:
            Dict mapping drug IDs to drug names
        """
        logger.info("Extracting drug names...")
        
        drug_names = {}
        
        for drug_id, drug_data in drugs_index.items():
            # Get drug name
            name = (drug_data.get('drug_name') or 
                   drug_data.get('name') or
                   f"Drug {drug_id}")
            
            drug_names[drug_id] = name
        
        logger.info(f"Extracted {len(drug_names)} drug names")
        return drug_names
    
    def save_json_file(self, data: Dict[str, Any], filename: str) -> None:
        """
        Save data to JSON file with error handling
        
        Args:
            data: Data to save
            filename: Output filename
        """
        output_file = self.output_dir / filename
        
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
    
    def curate_drugs(self) -> Dict[str, Dict[str, Any]]:
        """
        Main curation method - generate all required JSON files
        
        Returns:
            Dict containing all generated data
        """
        logger.info("Starting Orpha drugs curation...")
        
        # Load processed data
        processed_data = self.load_processed_data()
        diseases2drugs = processed_data['diseases2drugs']
        drugs_index = processed_data['drugs_index']
        
        # Generate curated files
        logger.info("Generating curated drug files...")
        
        # 1. EU tradename drugs
        eu_tradename_drugs = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Tradename", "EU"
        )
        self.save_json_file(eu_tradename_drugs, "disease2eu_tradename_drugs.json")
        
        # 2. All tradename drugs
        all_tradename_drugs = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Tradename", "ALL"
        )
        self.save_json_file(all_tradename_drugs, "disease2all_tradename_drugs.json")
        
        # 3. USA tradename drugs
        usa_tradename_drugs = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Tradename", "US"
        )
        self.save_json_file(usa_tradename_drugs, "disease2usa_tradename_drugs.json")
        
        # 4. EU medical product drugs
        eu_medical_products = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Medicinal product", "EU"
        )
        self.save_json_file(eu_medical_products, "disease2eu_medical_product_drugs.json")
        
        # 5. All medical product drugs
        all_medical_products = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Medicinal product", "ALL"
        )
        self.save_json_file(all_medical_products, "disease2all_medical_product_drugs.json")
        
        # 6. USA medical product drugs
        usa_medical_products = self.filter_drugs_by_criteria(
            diseases2drugs, drugs_index, "Medicinal product", "US"
        )
        self.save_json_file(usa_medical_products, "disease2usa_medical_product_drugs.json")
        
        # 7. Drug names mapping
        drug_names = self.extract_drug_names(drugs_index)
        self.save_json_file(drug_names, "drug2name.json")
        
        # Generate summary
        summary = {
            "curation_metadata": {
                "total_diseases_with_drugs": len(diseases2drugs),
                "total_unique_drugs": len(drug_names),
                "tradename_coverage": {
                    "eu": len(eu_tradename_drugs),
                    "usa": len(usa_tradename_drugs),
                    "all": len(all_tradename_drugs)
                },
                "medical_product_coverage": {
                    "eu": len(eu_medical_products),
                    "usa": len(usa_medical_products),
                    "all": len(all_medical_products)
                },
                "processing_timestamp": datetime.now().isoformat()
            }
        }
        
        self.save_json_file(summary, "orpha_drugs_curation_summary.json")
        
        logger.info("Orpha drugs curation completed successfully!")
        logger.info(f"Generated files in: {self.output_dir}")
        
        return {
            "disease2eu_tradename_drugs": eu_tradename_drugs,
            "disease2all_tradename_drugs": all_tradename_drugs,
            "disease2usa_tradename_drugs": usa_tradename_drugs,
            "disease2eu_medical_product_drugs": eu_medical_products,
            "disease2all_medical_product_drugs": all_medical_products,
            "disease2usa_medical_product_drugs": usa_medical_products,
            "drug2name": drug_names,
            "summary": summary
        }


def main():
    """
    Main entry point for Orpha drugs curation
    """
    parser = argparse.ArgumentParser(description="Curate Orpha drugs data for regional and type accessibility")
    parser.add_argument("--input-dir", default="data/03_processed/orpha/orphadata/orpha_drugs",
                       help="Input directory with processed Orpha drugs data")
    parser.add_argument("--output-dir", default="data/04_curated/orpha/orphadata",
                       help="Output directory for curated data")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize curator
        curator = OrphaDrugsCurator(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Run curation
        results = curator.curate_drugs()
        
        # Print summary
        print("\n" + "="*60)
        print("ORPHA DRUGS CURATION SUMMARY")
        print("="*60)
        
        metadata = results["summary"]["curation_metadata"]
        print(f"Total diseases with drugs: {metadata['total_diseases_with_drugs']}")
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