import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.clinical_trials.clinical_trials import ClinicalTrialsAPIClient
from utils.pipeline.run_management import get_next_run_number, is_disease_processed, save_processing_result
from data.models.disease import SimpleDisease, ClinicalTrialResult


def process_clinical_trials(diseases_file="data/input/etl/init_diseases/diseases_sample_10.json", 
                           run_number=None):
    """Process diseases through clinical trials API"""
    
    with open(diseases_file, 'r', encoding='utf-8') as f:
        diseases_data = json.load(f)
    
    diseases = [SimpleDisease(**disease) for disease in diseases_data]
    client = ClinicalTrialsAPIClient()
    data_type = "clinical_trials"
    
    processed_count = 0
    failed_diseases = []
    
    print(f"Processing {len(diseases)} diseases for clinical trials...")
    
    for disease in diseases:
        try:
            # Determine run number for this disease
            if run_number is None:
                current_run = get_next_run_number(data_type, disease.orpha_code)
            else:
                current_run = run_number
            
            # Check if already processed
            if is_disease_processed(disease.orpha_code, data_type, current_run):
                print(f"Skipping {disease.disease_name} (already processed in run {current_run})")
                continue
            
            print(f"Processing {disease.disease_name} (run {current_run})...")
            
            # Execute clinical trials query
            results = client._search_trials(
                query_term=disease.disease_name,
                query_locn="Spain",
                filter_overall_status=['RECRUITING', 'ACTIVE_NOT_RECRUITING'],
                max_results=100
            )
            
            # Create result object
            result = ClinicalTrialResult(
                disease_name=disease.disease_name,
                orpha_code=disease.orpha_code,
                trials=results,
                processing_timestamp=datetime.now(),
                run_number=current_run,
                total_trials_found=len(results)
            )
            
            # Save result
            save_processing_result(
                result.model_dump(mode='json'), 
                data_type, 
                disease.orpha_code, 
                current_run
            )
            
            processed_count += 1
            print(f"  Found {len(results)} trials")
            
        except Exception as e:
            print(f"Error processing {disease.disease_name}: {e}")
            failed_diseases.append(disease.orpha_code)
    
    print(f"\nProcessing complete: {processed_count} diseases processed, {len(failed_diseases)} failed")
    if failed_diseases:
        print(f"Failed diseases: {failed_diseases}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process diseases for clinical trials')
    parser.add_argument('--file', default="data/input/etl/init_diseases/diseases_sample_10.json",
                       help='Path to diseases JSON file')
    parser.add_argument('--run', type=int, help='Specific run number to use')
    
    args = parser.parse_args()
    
    process_clinical_trials(args.file, args.run) 