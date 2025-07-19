"""
Metabolic Disease Prevalence Curator

This module processes metabolic diseases from curated ORDO data and generates
Spanish patient estimates using prevalence data from ProcessedPrevalenceClient.

Spanish population: 47 million inhabitants
Formula: spanish_patients = prevalence_per_million × 47

Input: data/04_curated/orpha/ordo/metabolic_disease_instances.json
Output: 
  - metabolic_diseases2prevalence_per_million.json
  - metabolic_diseases2spanish_patient_number.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from datetime import datetime

from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetabolicPrevalenceCurator:
    """Curator for metabolic disease prevalence data and Spanish patient estimates"""
    
    def __init__(self, 
                 metabolic_diseases_path: str = "data/04_curated/orpha/ordo/metabolic_disease_instances.json",
                 output_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the metabolic prevalence curator
        
        Args:
            metabolic_diseases_path: Path to metabolic disease instances JSON
            output_dir: Directory for output files
        """
        self.metabolic_diseases_path = Path(metabolic_diseases_path)
        self.output_dir = Path(output_dir)
        self.spanish_population = 47  # 47 million inhabitants
        
        # Initialize ProcessedPrevalenceClient
        self.prevalence_client = ProcessedPrevalenceClient()
        
        # Processing statistics
        self.stats = {
            'total_diseases': 0,
            'diseases_processed': 0,
            'diseases_with_prevalence': 0,
            'diseases_without_prevalence': 0,
            'diseases_with_zero_prevalence': 0,
            'errors': 0,
            'processing_start': None,
            'processing_end': None,
            'skipped_diseases': []
        }
        
        logger.info(f"Metabolic prevalence curator initialized")
        logger.info(f"Input: {self.metabolic_diseases_path}")
        logger.info(f"Output: {self.output_dir}")
    
    def load_metabolic_diseases(self) -> List[Dict]:
        """
        Load metabolic disease instances from JSON file
        
        Returns:
            List of disease dictionaries with disease_name and orpha_code
        """
        if not self.metabolic_diseases_path.exists():
            raise FileNotFoundError(f"Metabolic diseases file not found: {self.metabolic_diseases_path}")
        
        with open(self.metabolic_diseases_path, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        logger.info(f"Loaded {len(diseases)} metabolic diseases")
        self.stats['total_diseases'] = len(diseases)
        
        return diseases
    
    def get_prevalence_for_disease(self, orpha_code: str) -> Optional[float]:
        """
        Get mean prevalence per million for a disease
        
        Args:
            orpha_code: Orpha code as string
            
        Returns:
            Mean prevalence per million or None if not available
        """
        try:
            # Convert orpha_code to string if not already
            orpha_code_str = str(orpha_code)
            
            # Get prevalence summary for the disease
            prevalence_summary = self.prevalence_client.get_disease_prevalence_summary(orpha_code_str)
            
            if not prevalence_summary:
                return None
            
            # Get mean_value_per_million from the summary
            mean_value = prevalence_summary.get('mean_value_per_million')
            
            if mean_value is not None and mean_value >= 0:
                return float(mean_value)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error getting prevalence for disease {orpha_code}: {e}")
            return None
    
    def calculate_spanish_patients(self, prevalence_per_million: float) -> int:
        """
        Calculate Spanish patient count from prevalence per million
        
        Args:
            prevalence_per_million: Prevalence per million population
            
        Returns:
            Number of Spanish patients (rounded to integer)
        """
        spanish_patients = prevalence_per_million * self.spanish_population
        return round(spanish_patients)
    
    def process_metabolic_diseases(self) -> Tuple[Dict[int, float], Dict[int, int]]:
        """
        Process all metabolic diseases and generate prevalence and Spanish patient data
        
        Returns:
            Tuple of (prevalence_dict, spanish_patients_dict)
        """
        logger.info("Starting metabolic disease processing...")
        self.stats['processing_start'] = datetime.now()
        
        # Load metabolic diseases
        diseases = self.load_metabolic_diseases()
        
        # Initialize output dictionaries
        prevalence_dict = {}  # {orpha_code_int: prevalence_per_million}
        spanish_patients_dict = {}  # {orpha_code_int: spanish_patient_count}
        
        for disease in diseases:
            disease_name = disease.get('disease_name', 'Unknown')
            orpha_code_str = disease.get('orpha_code', '')
            
            try:
                # Convert orpha_code to integer
                orpha_code_int = int(orpha_code_str)
                
                # Get prevalence data
                prevalence = self.get_prevalence_for_disease(orpha_code_str)
                
                if prevalence is not None:
                    # Calculate Spanish patients
                    spanish_patients = self.calculate_spanish_patients(prevalence)
                    
                    # Store in dictionaries
                    prevalence_dict[orpha_code_int] = prevalence
                    spanish_patients_dict[orpha_code_int] = spanish_patients
                    
                    self.stats['diseases_with_prevalence'] += 1
                    
                    if prevalence == 0.0:
                        self.stats['diseases_with_zero_prevalence'] += 1
                        logger.debug(f"Zero prevalence for {disease_name} ({orpha_code_str})")
                    
                    logger.debug(f"Processed {disease_name} ({orpha_code_str}): "
                               f"{prevalence:.2f}/million → {spanish_patients} Spanish patients")
                
                else:
                    # No prevalence data available
                    self.stats['diseases_without_prevalence'] += 1
                    self.stats['skipped_diseases'].append({
                        'disease_name': disease_name,
                        'orpha_code': orpha_code_str,
                        'reason': 'No prevalence data'
                    })
                    logger.warning(f"No prevalence data for {disease_name} ({orpha_code_str})")
                
                self.stats['diseases_processed'] += 1
                
                # Progress logging every 100 diseases
                if self.stats['diseases_processed'] % 100 == 0:
                    logger.info(f"Processed {self.stats['diseases_processed']}/{self.stats['total_diseases']} diseases...")
                
            except ValueError as e:
                # Invalid orpha_code format
                self.stats['errors'] += 1
                self.stats['skipped_diseases'].append({
                    'disease_name': disease_name,
                    'orpha_code': orpha_code_str,
                    'reason': f'Invalid orpha_code: {e}'
                })
                logger.error(f"Invalid orpha_code for {disease_name}: {orpha_code_str} - {e}")
                
            except Exception as e:
                # Other processing errors
                self.stats['errors'] += 1
                self.stats['skipped_diseases'].append({
                    'disease_name': disease_name,
                    'orpha_code': orpha_code_str,
                    'reason': f'Processing error: {e}'
                })
                logger.error(f"Error processing {disease_name} ({orpha_code_str}): {e}")
        
        self.stats['processing_end'] = datetime.now()
        
        logger.info(f"Processing completed!")
        logger.info(f"Total diseases: {self.stats['total_diseases']}")
        logger.info(f"Diseases with prevalence: {self.stats['diseases_with_prevalence']}")
        logger.info(f"Diseases without prevalence: {self.stats['diseases_without_prevalence']}")
        logger.info(f"Diseases with zero prevalence: {self.stats['diseases_with_zero_prevalence']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        return prevalence_dict, spanish_patients_dict
    
    def save_output_files(self, prevalence_dict: Dict[int, float], spanish_patients_dict: Dict[int, int]) -> None:
        """
        Save the generated dictionaries to JSON files
        
        Args:
            prevalence_dict: Orpha codes to prevalence per million mapping
            spanish_patients_dict: Orpha codes to Spanish patient count mapping
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # File paths
        prevalence_file = self.output_dir / "metabolic_diseases2prevalence_per_million.json"
        spanish_patients_file = self.output_dir / "metabolic_diseases2spanish_patient_number.json"
        
        # Save prevalence per million file
        with open(prevalence_file, 'w', encoding='utf-8') as f:
            json.dump(prevalence_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved prevalence data: {prevalence_file} ({len(prevalence_dict)} diseases)")
        
        # Save Spanish patients file
        with open(spanish_patients_file, 'w', encoding='utf-8') as f:
            json.dump(spanish_patients_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved Spanish patients data: {spanish_patients_file} ({len(spanish_patients_dict)} diseases)")
    
    def generate_processing_summary(self) -> Dict:
        """
        Generate comprehensive processing summary
        
        Returns:
            Dictionary with processing statistics and summary
        """
        if self.stats['processing_start'] and self.stats['processing_end']:
            processing_time = (self.stats['processing_end'] - self.stats['processing_start']).total_seconds()
        else:
            processing_time = 0
        
        coverage_percentage = (self.stats['diseases_with_prevalence'] / self.stats['total_diseases'] * 100 
                             if self.stats['total_diseases'] > 0 else 0)
        
        summary = {
            'processing_timestamp': datetime.now().isoformat(),
            'input_file': str(self.metabolic_diseases_path),
            'output_directory': str(self.output_dir),
            'spanish_population_millions': self.spanish_population,
            'statistics': {
                'total_metabolic_diseases': self.stats['total_diseases'],
                'diseases_processed': self.stats['diseases_processed'],
                'diseases_with_prevalence': self.stats['diseases_with_prevalence'],
                'diseases_without_prevalence': self.stats['diseases_without_prevalence'],
                'diseases_with_zero_prevalence': self.stats['diseases_with_zero_prevalence'],
                'processing_errors': self.stats['errors'],
                'prevalence_coverage_percentage': round(coverage_percentage, 2),
                'processing_time_seconds': round(processing_time, 2)
            },
            'skipped_diseases': self.stats['skipped_diseases'][:10],  # First 10 for brevity
            'total_skipped': len(self.stats['skipped_diseases'])
        }
        
        return summary
    
    def run_curation(self) -> None:
        """
        Run the complete curation process
        """
        try:
            logger.info("="*60)
            logger.info("METABOLIC DISEASE PREVALENCE CURATION")
            logger.info("="*60)
            
            # Process diseases
            prevalence_dict, spanish_patients_dict = self.process_metabolic_diseases()
            
            # Save output files
            self.save_output_files(prevalence_dict, spanish_patients_dict)
            
            # Generate and save processing summary
            summary = self.generate_processing_summary()
            summary_file = self.output_dir / "metabolic_prevalence_processing_summary.json"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved processing summary: {summary_file}")
            
            logger.info("="*60)
            logger.info("CURATION COMPLETED SUCCESSFULLY")
            logger.info("="*60)
            
            # Print key statistics
            print(f"\n📊 METABOLIC DISEASE CURATION SUMMARY")
            print(f"Total diseases processed: {summary['statistics']['total_metabolic_diseases']}")
            print(f"Diseases with prevalence: {summary['statistics']['diseases_with_prevalence']}")
            print(f"Coverage: {summary['statistics']['prevalence_coverage_percentage']}%")
            print(f"Processing time: {summary['statistics']['processing_time_seconds']}s")
            print(f"Output files saved to: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Curation failed: {e}")
            raise


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Curate metabolic disease prevalence data for Spanish patients")
    
    parser.add_argument(
        '--input',
        default="data/04_curated/orpha/ordo/metabolic_disease_instances.json",
        help="Path to metabolic disease instances JSON file"
    )
    
    parser.add_argument(
        '--output',
        default="data/04_curated/orpha/orphadata",
        help="Output directory for curated files"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run curator
    curator = MetabolicPrevalenceCurator(
        metabolic_diseases_path=args.input,
        output_dir=args.output
    )
    
    curator.run_curation()


if __name__ == "__main__":
    main() 