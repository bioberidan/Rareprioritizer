#!/usr/bin/env python3
"""
Clinical Trials Curation Script

This script processes clinical trials data from the processed directory and generates
curated JSON files for regional accessibility analysis.

Input: data/03_processed/clinical_trials/
Output: data/04_curated/clinical_trials/

Generated Files:
- disease2eu_trial.json
- disease2all_trials.json  
- disease2spanish_trials.json
- clinicaltrial2name.json
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Set, Any
from datetime import datetime

# Import our schemas for validation
from core.schemas.clinical_trials.clinical_trials import (
    ClinicalTrialInstance, 
    TrialLocationInfo,
    CuratedTrialMapping,
    create_eu_countries_list,
    is_eu_accessible_trial,
    is_spanish_accessible_trial
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClinicalTrialsCurator:
    """
    Curator for clinical trials data - generates regional accessibility files
    """
    
    def __init__(self, input_dir: str = "data/03_processed/clinical_trials",
                 output_dir: str = "data/04_curated/clinical_trials"):
        """
        Initialize the clinical trials curator
        
        Args:
            input_dir: Directory containing processed clinical trials data
            output_dir: Directory for curated output files
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # EU countries for filtering
        self.eu_countries = set(create_eu_countries_list())
        
        logger.info(f"Initialized ClinicalTrialsCurator")
        logger.info(f"Input: {self.input_dir}")
        logger.info(f"Output: {self.output_dir}")
    
    def load_processed_data(self) -> Dict[str, Any]:
        """
        Load all processed clinical trials data
        
        Returns:
            Dict containing loaded data
        """
        logger.info("Loading processed clinical trials data...")
        
        # Load diseases2clinical_trials.json
        diseases2trials_file = self.input_dir / "diseases2clinical_trials.json"
        if not diseases2trials_file.exists():
            raise FileNotFoundError(f"Required file not found: {diseases2trials_file}")
        
        with open(diseases2trials_file, 'r', encoding='utf-8') as f:
            diseases2trials = json.load(f)
        
        # Load clinical_trials_index.json  
        trials_index_file = self.input_dir / "clinical_trials_index.json"
        if not trials_index_file.exists():
            raise FileNotFoundError(f"Required file not found: {trials_index_file}")
        
        with open(trials_index_file, 'r', encoding='utf-8') as f:
            trials_index = json.load(f)
        
        # Load clinical_trials2diseases.json
        trials2diseases_file = self.input_dir / "clinical_trials2diseases.json"
        if not trials2diseases_file.exists():
            raise FileNotFoundError(f"Required file not found: {trials2diseases_file}")
        
        with open(trials2diseases_file, 'r', encoding='utf-8') as f:
            trials2diseases = json.load(f)
        
        logger.info(f"Loaded {len(diseases2trials)} diseases with trials")
        logger.info(f"Loaded {len(trials_index)} unique trials")
        
        return {
            'diseases2trials': diseases2trials,
            'trials_index': trials_index,
            'trials2diseases': trials2diseases
        }
    
    def validate_and_normalize_trial(self, trial_data: Dict[str, Any]) -> ClinicalTrialInstance:
        """
        Validate and normalize trial data using Pydantic schema
        
        Args:
            trial_data: Raw trial data from processed files
            
        Returns:
            Validated ClinicalTrialInstance
        """
        # Normalize locations data
        locations = []
        for loc in trial_data.get('locations', []):
            location = TrialLocationInfo(
                facility=loc.get('facility'),
                city=loc.get('city'),
                state=loc.get('state'),
                country=loc.get('country'),
                zip_code=loc.get('zip'),
                status=loc.get('status')
            )
            locations.append(location)
        
        # Create normalized trial instance
        trial = ClinicalTrialInstance(
            nct_id=trial_data.get('nctId', trial_data.get('nct_id', '')),
            brief_title=trial_data.get('briefTitle', trial_data.get('brief_title', '')),
            official_title=trial_data.get('officialTitle', trial_data.get('official_title')),
            overall_status=trial_data.get('overallStatus', trial_data.get('overall_status', 'Unknown')),
            study_type=trial_data.get('studyType', trial_data.get('study_type')),
            phases=trial_data.get('phases', []),
            interventions=trial_data.get('interventions', []),
            enrollment=trial_data.get('enrollment'),
            locations=locations,
            diseases=trial_data.get('diseases', []),
            last_update=trial_data.get('lastUpdateDate', trial_data.get('last_update', '')),
            processing_metadata={'source': 'processed_data', 'curated_timestamp': datetime.now().isoformat()}
        )
        
        return trial
    
    def filter_eu_trials(self, diseases2trials: Dict[str, Dict], trials_index: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Filter trials accessible from EU countries
        
        Args:
            diseases2trials: Disease to trials mapping
            trials_index: Complete trials index
            
        Returns:
            Dict mapping disease codes to EU-accessible trial NCT IDs
        """
        logger.info("Filtering EU-accessible trials...")
        
        eu_trials = {}
        
        for orpha_code, disease_data in diseases2trials.items():
            eu_trial_ids = []
            
            # Get the trials list from disease data
            trials_list = disease_data.get('trials', [])
            
            for nct_id in trials_list:
                # nct_id is already a string (NCT ID)
                
                # Get full trial details from index
                trial_detail = trials_index.get(nct_id, {})
                
                # Validate and normalize trial data
                try:
                    normalized_trial = self.validate_and_normalize_trial(trial_detail)
                    
                    # Check if trial has EU locations
                    if is_eu_accessible_trial(normalized_trial):
                        eu_trial_ids.append(nct_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to validate trial {nct_id}: {e}")
                    
                    # Fallback: check locations manually
                    locations = trial_detail.get('locations', [])
                    if any(loc.get('country') in self.eu_countries for loc in locations):
                        eu_trial_ids.append(nct_id)
            
            if eu_trial_ids:
                eu_trials[orpha_code] = eu_trial_ids
        
        logger.info(f"Found {len(eu_trials)} diseases with EU-accessible trials")
        return eu_trials
    
    def filter_spanish_trials(self, diseases2trials: Dict[str, Dict], trials_index: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Filter trials accessible from Spain
        
        Args:
            diseases2trials: Disease to trials mapping
            trials_index: Complete trials index
            
        Returns:
            Dict mapping disease codes to Spanish-accessible trial NCT IDs
        """
        logger.info("Filtering Spanish-accessible trials...")
        
        spanish_trials = {}
        
        for orpha_code, disease_data in diseases2trials.items():
            spanish_trial_ids = []
            
            # Get the trials list from disease data
            trials_list = disease_data.get('trials', [])
            
            for nct_id in trials_list:
                # nct_id is already a string (NCT ID)
                
                # Get full trial details from index
                trial_detail = trials_index.get(nct_id, {})
                
                # Validate and normalize trial data
                try:
                    normalized_trial = self.validate_and_normalize_trial(trial_detail)
                    
                    # Check if trial has Spanish locations
                    if is_spanish_accessible_trial(normalized_trial):
                        spanish_trial_ids.append(nct_id)
                        
                except Exception as e:
                    logger.warning(f"Failed to validate trial {nct_id}: {e}")
                    
                    # Fallback: check locations manually
                    locations = trial_detail.get('locations', [])
                    if any(loc.get('country') == 'Spain' for loc in locations):
                        spanish_trial_ids.append(nct_id)
            
            if spanish_trial_ids:
                spanish_trials[orpha_code] = spanish_trial_ids
        
        logger.info(f"Found {len(spanish_trials)} diseases with Spanish-accessible trials")
        return spanish_trials
    
    def format_all_trials(self, diseases2trials: Dict[str, Dict]) -> Dict[str, List[str]]:
        """
        Format all trials mapping to simple disease -> NCT ID list
        
        Args:
            diseases2trials: Disease to trials mapping
            
        Returns:
            Dict mapping disease codes to all trial NCT IDs
        """
        logger.info("Formatting all trials mapping...")
        
        all_trials = {}
        
        for orpha_code, disease_data in diseases2trials.items():
            # Get the trials list from disease data
            trial_ids = disease_data.get('trials', [])
            
            if trial_ids:
                all_trials[orpha_code] = trial_ids
        
        logger.info(f"Found {len(all_trials)} diseases with trials")
        return all_trials
    
    def extract_trial_names(self, trials_index: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract trial ID to title mapping
        
        Args:
            trials_index: Complete trials index
            
        Returns:
            Dict mapping NCT IDs to trial titles
        """
        logger.info("Extracting trial names...")
        
        trial_names = {}
        
        for nct_id, trial_data in trials_index.items():
            # Prefer brief_title, fall back to official_title
            title = (trial_data.get('briefTitle') or 
                    trial_data.get('brief_title') or
                    trial_data.get('officialTitle') or 
                    trial_data.get('official_title') or
                    f"Clinical Trial {nct_id}")
            
            trial_names[nct_id] = title
        
        logger.info(f"Extracted {len(trial_names)} trial names")
        return trial_names
    
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
    
    def curate_trials(self) -> Dict[str, Dict[str, Any]]:
        """
        Main curation method - generate all required JSON files
        
        Returns:
            Dict containing all generated data
        """
        logger.info("Starting clinical trials curation...")
        
        # Load processed data
        processed_data = self.load_processed_data()
        diseases2trials = processed_data['diseases2trials']
        trials_index = processed_data['trials_index']
        
        # Generate curated files
        logger.info("Generating curated trial files...")
        
        # 1. EU-accessible trials
        eu_trials = self.filter_eu_trials(diseases2trials, trials_index)
        self.save_json_file(eu_trials, "disease2eu_trial.json")
        
        # 2. All trials  
        all_trials = self.format_all_trials(diseases2trials)
        self.save_json_file(all_trials, "disease2all_trials.json")
        
        # 3. Spanish-accessible trials
        spanish_trials = self.filter_spanish_trials(diseases2trials, trials_index)
        self.save_json_file(spanish_trials, "disease2spanish_trials.json")
        
        # 4. Trial names mapping
        trial_names = self.extract_trial_names(trials_index)
        self.save_json_file(trial_names, "clinicaltrial2name.json")
        
        # Generate summary
        summary = {
            "curation_metadata": {
                "total_diseases_with_trials": len(all_trials),
                "diseases_with_eu_trials": len(eu_trials),
                "diseases_with_spanish_trials": len(spanish_trials),
                "total_unique_trials": len(trial_names),
                "eu_coverage_percentage": (len(eu_trials) / len(all_trials) * 100) if all_trials else 0,
                "spanish_coverage_percentage": (len(spanish_trials) / len(all_trials) * 100) if all_trials else 0,
                "processing_timestamp": datetime.now().isoformat()
            }
        }
        
        self.save_json_file(summary, "clinical_trials_curation_summary.json")
        
        logger.info("Clinical trials curation completed successfully!")
        logger.info(f"Generated files in: {self.output_dir}")
        
        return {
            "disease2eu_trial": eu_trials,
            "disease2all_trials": all_trials,
            "disease2spanish_trials": spanish_trials,
            "clinicaltrial2name": trial_names,
            "summary": summary
        }


def main():
    """
    Main entry point for clinical trials curation
    """
    parser = argparse.ArgumentParser(description="Curate clinical trials data for regional accessibility")
    parser.add_argument("--input-dir", default="data/03_processed/clinical_trials",
                       help="Input directory with processed clinical trials data")
    parser.add_argument("--output-dir", default="data/04_curated/clinical_trials",
                       help="Output directory for curated data")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize curator
        curator = ClinicalTrialsCurator(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Run curation
        results = curator.curate_trials()
        
        # Print summary
        print("\n" + "="*60)
        print("CLINICAL TRIALS CURATION SUMMARY")
        print("="*60)
        
        metadata = results["summary"]["curation_metadata"]
        print(f"Total diseases with trials: {metadata['total_diseases_with_trials']}")
        print(f"Diseases with EU trials: {metadata['diseases_with_eu_trials']} ({metadata['eu_coverage_percentage']:.1f}%)")
        print(f"Diseases with Spanish trials: {metadata['diseases_with_spanish_trials']} ({metadata['spanish_coverage_percentage']:.1f}%)")
        print(f"Total unique trials: {metadata['total_unique_trials']}")
        print(f"\nFiles generated in: {args.output_dir}")
        print("- disease2eu_trial.json")
        print("- disease2all_trials.json") 
        print("- disease2spanish_trials.json")
        print("- clinicaltrial2name.json")
        print("- clinical_trials_curation_summary.json")
        
    except Exception as e:
        logger.error(f"Curation failed: {e}")
        raise


if __name__ == "__main__":
    main() 