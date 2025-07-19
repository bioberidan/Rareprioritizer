import os
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
    

def get_next_run_number(data_type: str, orphacode: str) -> int:
    """Check existing run files for specific disease and return next number"""
    disease_dir = Path(f"data/preprocessing/{data_type}/{orphacode}")
    if not disease_dir.exists():
        return 1
    
    run_files = list(disease_dir.glob("run*_disease2*.json"))
    if not run_files:
        return 1
    
    run_numbers = []
    for file in run_files:
        try:
            run_num = int(file.name.split("_")[0].replace("run", ""))
            run_numbers.append(run_num)
        except:
            continue
    
    return max(run_numbers) + 1 if run_numbers else 1


def is_disease_processed(orphacode: str, data_type: str, run_number: int) -> bool:
    """Check if disease already processed in current run"""
    output_path = create_output_path(data_type, orphacode, run_number)
    return Path(output_path).exists()


def create_output_path(data_type: str, orphacode: str, run_number: int, base_path: str = "data/02_preprocess") -> str:
    """Generate output path for disease processing result"""
    return f"{base_path}/{data_type}/{orphacode}/run{run_number}_disease2{data_type}.json"


def save_processing_result(data: dict, data_type: str, orphacode: str, run_number: int, base_path: str = "data/02_preprocess"):
    """Save processing result to appropriate location"""
    output_path = create_output_path(data_type, orphacode, run_number, base_path)
    output_dir = Path(output_path).parent
    logger.info(f"Saving result to {output_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def should_reprocess_disease(data_type: str, orphacode: str, run_number: int) -> bool:
    """Check if existing run is empty and should be reprocessed"""
    output_path = create_output_path(data_type, orphacode, run_number)
    if not Path(output_path).exists():
        return True
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the data is empty or has no meaningful content
        if data_type == "drug":
            drugs = data.get('drugs', [])
            return len(drugs) == 0
        elif data_type == "clinical_trials":
            trials = data.get('trials', [])
            return len(trials) == 0
        
        return False
    except:
        return True  # If file is corrupted, reprocess 