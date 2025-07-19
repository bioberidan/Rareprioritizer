import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from core.infrastructure.orpha_drug.orpha_drug import OrphaDrugAPIClient
from core.infrastructure.pipeline.run_management import get_next_run_number, is_disease_processed, should_reprocess_disease, save_processing_result
from core.schemas.old import SimpleDisease, DrugResult


def process_drug_data(diseases_file="data/input/etl/init_diseases/diseases_sample_10.json", 
                     run_number=None):
    """Process diseases through Orpha.net drug database"""
    
    with open(diseases_file, 'r', encoding='utf-8') as f:
        diseases_data = json.load(f)
    
    diseases = [SimpleDisease(**disease) for disease in diseases_data]
    client = OrphaDrugAPIClient(delay=0.5)
    data_type = "orpha_drugs"
    
    processed_count = 0
    failed_diseases = []
    
    print(f"Processing {len(diseases)} diseases for drug data...")
    base_path = "data/02_preprocess/orpha/orphadata/"
    for disease in diseases:
        try:
            # Determine run number for this disease
            if run_number is None:
                current_run = get_next_run_number(data_type, disease.orpha_code)
            else:
                current_run = run_number
            
            # Check if already processed and has meaningful data
            if is_disease_processed(disease.orpha_code, data_type, current_run):
                if not should_reprocess_disease(data_type, disease.orpha_code, current_run):
                    print(f"Skipping {disease.disease_name} (already processed in run {current_run})")
                    continue
                else:
                    print(f"Reprocessing {disease.disease_name} (run {current_run} was empty)")
            
            print(f"Processing {disease.disease_name} (run {current_run})...")
            
            # Execute drug search query
            results = client.search(
                disease_name=disease.disease_name,
                orphacode=disease.orpha_code
            )
            
            # Extract drug data or handle errors
            if 'error' in results:
                print(f"  Error in search: {results['error']}")
                drugs_data = []
                search_url = ""
                search_params = {}
            else:
                drugs_data = results.get('drugs', [])
                search_url = results.get('url', '')
                search_params = results.get('search_params', {})
            
            # Create result object
            result = DrugResult(
                disease_name=disease.disease_name,
                orpha_code=disease.orpha_code,
                drugs=drugs_data,
                processing_timestamp=datetime.now(),
                run_number=current_run,
                total_drugs_found=len(drugs_data),
                search_url=search_url,
                search_params=search_params
            )
            
            # Save result
            save_processing_result(
                result.model_dump(mode='json'), 
                data_type, 
                disease.orpha_code, 
                current_run,
                base_path
            )
            
            processed_count += 1
            print(f"  Found {len(drugs_data)} drugs")
            
        except Exception as e:
            print(f"Error processing {disease.disease_name}: {e}")
            failed_diseases.append(disease.orpha_code)
    
    print(f"\nProcessing complete: {processed_count} diseases processed, {len(failed_diseases)} failed")
    if failed_diseases:
        print(f"Failed diseases: {failed_diseases}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process diseases for drug data')
    parser.add_argument('--file', default="data/input/etl/init_diseases/diseases_sample_10.json",
                       help='Path to diseases JSON file')
    parser.add_argument('--run', type=int, help='Specific run number to use')
    
    args = parser.parse_args()
    
    process_drug_data(args.file, args.run) 