#!/usr/bin/env python3
"""
Curate Orpha Prevalence Data

This script curates prevalence data for a subset of diseases, selecting the best
prevalence class based on reliability and prevalence type priorities.

Usage:
    python curate_orpha_prevalence.py --disease-subset path/to/subset.json 
                                     --input path/to/prevalence.json 
                                     --output path/to/output/dir
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import existing clients
from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient


class OrphaPrevalenceCurator:
    """
    Curates prevalence data for a disease subset, selecting optimal prevalence classes
    based on reliability and prevalence type priorities.
    """
    
    def __init__(self, disease_subset_path: str, processed_prevalence_path: str, output_dir: str):
        self.disease_subset_path = Path(disease_subset_path)
        self.processed_prevalence_path = Path(processed_prevalence_path)
        self.output_dir = Path(output_dir)
        
        # Initialize ProcessedPrevalenceClient
        self.prevalence_client = ProcessedPrevalenceClient()
        
        # Processing statistics
        self.stats = {
            'total_diseases': 0,
            'diseases_with_prevalence': 0,
            'diseases_without_prevalence': 0,
            'prevalence_class_distribution': {},
            'selection_method_counts': {
                'point_prevalence': 0,
                'worldwide_fallback': 0,
                'regional_fallback': 0,
                'birth_prevalence_fallback': 0,
                'cases_families_fallback': 0,
                'no_data': 0
            }
        }
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def load_disease_subset(self) -> List[Dict[str, str]]:
        """Load disease subset from JSON file"""
        self.logger.info(f"Loading disease subset from {self.disease_subset_path}")
        
        if not self.disease_subset_path.exists():
            raise FileNotFoundError(f"Disease subset file not found: {self.disease_subset_path}")
        
        with open(self.disease_subset_path, 'r', encoding='utf-8') as f:
            disease_subset = json.load(f)
        
        self.logger.info(f"Loaded {len(disease_subset)} diseases from subset")
        return disease_subset

    def load_processed_prevalence(self) -> Dict[str, Any]:
        """Load processed prevalence data from JSON file"""
        self.logger.info(f"Loading processed prevalence data from {self.processed_prevalence_path}")
        
        if not self.processed_prevalence_path.exists():
            raise FileNotFoundError(f"Processed prevalence file not found: {self.processed_prevalence_path}")
        
        with open(self.processed_prevalence_path, 'r', encoding='utf-8') as f:
            prevalence_data = json.load(f)
        
        self.logger.info(f"Loaded prevalence data for {len(prevalence_data)} diseases")
        return prevalence_data

    def birth2point(self, birth_category: str) -> str:
        """
        Convert birth prevalence category to estimated point prevalence category.
        
        Uses conservative one-step down mapping to account for disease mortality.
        """
        mapping = {
            ">1 / 1000":           "6-9 / 10 000",
            "6-9 / 10 000":        "1-5 / 10 000", 
            "1-5 / 10 000":        "1-9 / 100 000",
            "1-9 / 100 000":       "1-9 / 1 000 000",
            "1-9 / 1 000 000":     "<1 / 1 000 000",
            "<1 / 1 000 000":      "<1 / 1 000 000",
            "Unknown":             "Unknown",
            "Not yet documented":  "Unknown"
        }
        return mapping.get(birth_category, "Unknown")

    def select_best_prevalence_class(self, disease_data: Dict) -> Optional[str]:
        """
        Select the best prevalence class based on priority rules:
        1. Use most_reliable_prevalence if it's point prevalence
        2. Otherwise apply choice-based method (worldwide -> regional)
        3. Birth prevalence fallback estimation
        """
        try:
            # Check if we have most_reliable_prevalence
            most_reliable = disease_data.get('most_reliable_prevalence')
            if most_reliable and most_reliable.get('prevalence_type') == 'Point prevalence':
                self.stats['selection_method_counts']['point_prevalence'] += 1
                return most_reliable.get('prevalence_class')
            
            # Fallback to choice-based method
            prevalence_records = disease_data.get('prevalence_records', [])
            if not prevalence_records:
                self.stats['selection_method_counts']['no_data'] += 1
                return None
            
            # Filter reliable records (reliability_score >= 6.0)
            reliable_records = [r for r in prevalence_records if r.get('reliability_score', 0) >= 6.0]
            
            if not reliable_records:
                reliable_records = prevalence_records  # Use all if none are reliable
            
            # Priority 2: Worldwide records (skip Unknown/Not yet documented)
            worldwide_records = [r for r in reliable_records if r.get('geographic_area') == 'Worldwide']
            if worldwide_records:
                best_record = max(worldwide_records, key=lambda x: x.get('reliability_score', 0))
                prevalence_class = best_record.get('prevalence_class')
                if prevalence_class and prevalence_class not in ['Unknown', 'Not yet documented']:
                    self.stats['selection_method_counts']['worldwide_fallback'] += 1
                    return prevalence_class
            
            # Priority 3: Regional records (skip Unknown/Not yet documented)
            regional_records = [r for r in reliable_records if r.get('geographic_area') != 'Worldwide']
            if regional_records:
                best_record = max(regional_records, key=lambda x: x.get('reliability_score', 0))
                prevalence_class = best_record.get('prevalence_class')
                if prevalence_class and prevalence_class not in ['Unknown', 'Not yet documented']:
                    self.stats['selection_method_counts']['regional_fallback'] += 1
                    return prevalence_class
            
            # Priority 4: Birth prevalence fallback
            birth_prevalence_records = [r for r in prevalence_records 
                                       if r.get('prevalence_type') == 'Prevalence at birth']
            
            if birth_prevalence_records:
                # Use most reliable birth prevalence record
                best_birth_record = max(birth_prevalence_records, 
                                       key=lambda x: x.get('reliability_score', 0))
                birth_class = best_birth_record.get('prevalence_class')
                
                if birth_class:
                    estimated_point_class = self.birth2point(birth_class)
                    if estimated_point_class != "Unknown":
                        self.stats['selection_method_counts']['birth_prevalence_fallback'] += 1
                        return estimated_point_class
            
            # Priority 5: Cases/families fallback - map to smallest prevalence class
            cases_families_records = [r for r in prevalence_records 
                                     if r.get('prevalence_type') == 'Cases/families']
            
            if cases_families_records:
                # Conservative approach: assign smallest prevalence class
                self.stats['selection_method_counts']['cases_families_fallback'] += 1
                return "<1 / 1 000 000"
            
            # No suitable records found
            self.stats['selection_method_counts']['no_data'] += 1
            return None
            
        except Exception as e:
            self.logger.warning(f"Error selecting prevalence class: {e}")
            self.stats['selection_method_counts']['no_data'] += 1
            return None

    def process_disease_subset(self) -> Dict[str, str]:
        """
        Process the disease subset and generate orphacode -> prevalence_class mapping
        """
        self.logger.info("Starting disease subset processing")
        
        # Load disease subset
        disease_subset = self.load_disease_subset()
        
        # Load processed prevalence data
        prevalence_data = self.load_processed_prevalence()
        
        # Generate mapping
        disease2prevalence = {}
        
        for disease_info in disease_subset:
            disease_code = disease_info['orpha_code']
            self.stats['total_diseases'] += 1
            
            if disease_code in prevalence_data:
                prevalence_class = self.select_best_prevalence_class(prevalence_data[disease_code])
                
                if prevalence_class and prevalence_class not in ['Unknown', 'Not yet documented']:
                    disease2prevalence[disease_code] = prevalence_class
                    self.stats['diseases_with_prevalence'] += 1
                    
                    # Update prevalence class distribution
                    self.stats['prevalence_class_distribution'][prevalence_class] = \
                        self.stats['prevalence_class_distribution'].get(prevalence_class, 0) + 1
                else:
                    # No usable prevalence data found - do not write to curated file
                    self.stats['diseases_without_prevalence'] += 1
            else:
                # No prevalence data available - do not write to curated file
                self.stats['diseases_without_prevalence'] += 1
        
        self.logger.info(f"Processing complete. {self.stats['diseases_with_prevalence']} diseases with prevalence, "
                        f"{self.stats['diseases_without_prevalence']} without")
        
        return disease2prevalence

    def generate_processing_summary(self, disease2prevalence: Dict[str, str]) -> Dict:
        """Generate processing summary statistics"""
        summary = {
            'processing_metadata': {
                'timestamp': datetime.now().isoformat(),
                'disease_subset_path': str(self.disease_subset_path),
                'processed_prevalence_path': str(self.processed_prevalence_path),
                'output_dir': str(self.output_dir)
            },
            'dataset_statistics': {
                'total_diseases_in_subset': self.stats['total_diseases'],
                'diseases_with_prevalence': self.stats['diseases_with_prevalence'],
                'diseases_without_prevalence': self.stats['diseases_without_prevalence'],
                'coverage_percentage': (self.stats['diseases_with_prevalence'] / self.stats['total_diseases']) * 100 if self.stats['total_diseases'] > 0 else 0
            },
            'selection_method_distribution': self.stats['selection_method_counts'],
            'prevalence_class_distribution': self.stats['prevalence_class_distribution'],
            'output_files': {
                'disease2prevalence': str(self.output_dir / "disease2prevalence.json"),
                'processing_summary': str(self.output_dir / "orpha_prevalence_curation_summary.json")
            }
        }
        
        return summary

    def save_outputs(self, disease2prevalence: Dict[str, str], summary: Dict) -> None:
        """Save outputs to JSON files"""
        # Save main output
        output_file = self.output_dir / "disease2prevalence.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(disease2prevalence, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved disease2prevalence mapping to {output_file}")
        
        # Save processing summary
        summary_file = self.output_dir / "orpha_prevalence_curation_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved processing summary to {summary_file}")

    def run(self) -> None:
        """Run the complete curation process"""
        try:
            self.logger.info("Starting orpha prevalence curation process")
            
            # Process disease subset
            disease2prevalence = self.process_disease_subset()
            
            # Generate summary statistics
            summary = self.generate_processing_summary(disease2prevalence)
            
            # Save outputs
            self.save_outputs(disease2prevalence, summary)
            
            self.logger.info("Curation process completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during curation process: {e}")
            raise


def main():
    """Main function with CLI interface - all paths configurable"""
    parser = argparse.ArgumentParser(description="Curate orpha prevalence data for disease subset")
    
    # All arguments are required - no hardcoded defaults
    parser.add_argument(
        '--disease-subset',
        required=True,
        help="Path to disease subset JSON file"
    )
    
    parser.add_argument(
        '--input',
        required=True, 
        help="Path to processed prevalence data JSON file"
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help="Output directory for curated files"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Create and run curator
    curator = OrphaPrevalenceCurator(
        disease_subset_path=args.disease_subset,
        processed_prevalence_path=args.input,
        output_dir=args.output
    )
    
    curator.run()


if __name__ == "__main__":
    main() 