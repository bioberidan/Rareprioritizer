import json
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_latest_non_empty_run(disease_dir: Path) -> tuple:
    """Get the latest run with non-empty trials for a disease"""
    run_files = list(disease_dir.glob("run*_disease2clinical_trials.json"))
    
    if not run_files:
        return None, None
    
    # Sort by run number (descending) to get latest first
    run_files.sort(key=lambda f: int(f.name.split("_")[0].replace("run", "")), reverse=True)
    
    for run_file in run_files:
        try:
            with open(run_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('total_trials_found', 0) > 0:
                    run_number = int(run_file.name.split("_")[0].replace("run", ""))
                    return run_number, data
        except Exception as e:
            logger.warning(f"Error reading {run_file}: {e}")
    
    return None, None


def aggregate_clinical_trials():
    """Aggregate clinical trials data from all disease runs"""
    
    preprocessing_dir = Path("data/preprocessing/clinical_trials")
    output_dir = Path("data/processed/clinical_trials")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Data structures for aggregation
    diseases2trials = {}
    trials2diseases = defaultdict(lambda: {
        "nct_id": "",
        "brief_title": "",
        "official_title": "",
        "overall_status": "",
        "study_type": "",
        "phases": [],
        "interventions": [],
        "enrollment": 0,
        "diseases": [],
        "locations_spain": False,
        "last_update": ""
    })
    
    clinical_trials_index = {}
    processing_stats = {
        "total_diseases_processed": 0,
        "diseases_with_trials": 0,
        "total_unique_trials": 0,
        "processing_timestamp": datetime.now().isoformat(),
        "diseases_by_run": defaultdict(int),
        "empty_diseases": []
    }
    
    # Process each disease directory
    for disease_dir in preprocessing_dir.iterdir():
        if not disease_dir.is_dir():
            continue
            
        orpha_code = disease_dir.name
        processing_stats["total_diseases_processed"] += 1
        
        # Get latest non-empty run
        run_number, run_data = get_latest_non_empty_run(disease_dir)
        
        if run_data is None:
            processing_stats["empty_diseases"].append(orpha_code)
            logger.info(f"No valid data found for disease {orpha_code}")
            continue
        
        processing_stats["diseases_by_run"][f"run{run_number}"] += 1
        
        # Extract disease info
        disease_name = run_data.get('disease_name', 'Unknown')
        trials = run_data.get('trials', [])
        
        if len(trials) > 0:
            processing_stats["diseases_with_trials"] += 1
            
            # Build disease → trials mapping
            trial_nct_ids = []
            for trial in trials:
                nct_id = trial.get('nctId', '')
                if nct_id:
                    trial_nct_ids.append(nct_id)
                    
                    # Build trial → diseases mapping
                    if nct_id not in trials2diseases:
                        trials2diseases[nct_id] = {
                            "nct_id": nct_id,
                            "brief_title": trial.get('briefTitle', ''),
                            "official_title": trial.get('officialTitle', ''),
                            "overall_status": trial.get('overallStatus', ''),
                            "study_type": trial.get('studyType', ''),
                            "phases": trial.get('phases', []),
                            "interventions": trial.get('interventions', []),
                            "enrollment": trial.get('enrollment', 0),
                            "diseases": [],
                            "locations_spain": any('Spain' in str(loc.get('country', '')) 
                                                 for loc in trial.get('locations', [])),
                            "last_update": trial.get('lastUpdateDate', '')
                        }
                        
                        # Store full trial details in index
                        clinical_trials_index[nct_id] = trial
                    
                    # Add disease to trial's disease list (avoid duplicates)
                    disease_entry = {
                        "orpha_code": orpha_code,
                        "disease_name": disease_name
                    }
                    
                    if disease_entry not in trials2diseases[nct_id]["diseases"]:
                        trials2diseases[nct_id]["diseases"].append(disease_entry)
            
            # Add to diseases mapping
            diseases2trials[orpha_code] = {
                "disease_name": disease_name,
                "orpha_code": orpha_code,
                "trials_count": len(trial_nct_ids),
                "last_processed_run": run_number,
                "trials": trial_nct_ids
            }
            
            logger.info(f"Processed {disease_name} ({orpha_code}): {len(trial_nct_ids)} trials from run {run_number}")
    
    # Convert defaultdict to regular dict for JSON serialization
    trials2diseases = dict(trials2diseases)
    processing_stats["total_unique_trials"] = len(trials2diseases)
    processing_stats["diseases_by_run"] = dict(processing_stats["diseases_by_run"])
    
    # Save aggregated data
    with open(output_dir / "diseases2clinical_trials.json", 'w', encoding='utf-8') as f:
        json.dump(diseases2trials, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "clinical_trials2diseases.json", 'w', encoding='utf-8') as f:
        json.dump(trials2diseases, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "clinical_trials_index.json", 'w', encoding='utf-8') as f:
        json.dump(clinical_trials_index, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "processing_summary.json", 'w', encoding='utf-8') as f:
        json.dump(processing_stats, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n=== Clinical Trials Aggregation Complete ===")
    print(f"Total diseases processed: {processing_stats['total_diseases_processed']}")
    print(f"Diseases with trials: {processing_stats['diseases_with_trials']}")
    print(f"Total unique trials: {processing_stats['total_unique_trials']}")
    print(f"Empty diseases: {len(processing_stats['empty_diseases'])}")
    print(f"Output saved to: {output_dir}")
    
    return processing_stats


if __name__ == "__main__":
    aggregate_clinical_trials() 