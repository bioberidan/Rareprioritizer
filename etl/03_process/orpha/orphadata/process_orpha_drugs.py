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
    """Get the latest run with non-empty drugs for a disease"""
    run_files = list(disease_dir.glob("run*_disease2drug.json"))
    
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


def aggregate_drug_data(preprocessing_dir_path: str, output_dir_path: str):
    """Aggregate drug data from all disease runs"""
    
    preprocessing_dir = Path(preprocessing_dir_path)
    output_dir = Path(output_dir_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Data structures for aggregation
    diseases2drugs = {}
    drugs2diseases = defaultdict(lambda: {
        "drug_name": "",
        "substance_id": "",
        "regulatory_id": "",
        "status": "",
        "manufacturer": "",
        "indication": "",
        "regions": [],
        "diseases": [],
        "substance_url": "",
        "regulatory_url": ""
    })
    
    drug_index = {}
    processing_stats = {
        "total_diseases_processed": 0,
        "diseases_with_drugs": 0,
        "total_unique_drugs": 0,
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
        drugs = run_data.get('drugs', [])
        
        if len(drugs) > 0:
            processing_stats["diseases_with_drugs"] += 1
            
            # Build disease → drugs mapping
            drug_ids = []
            for drug in drugs:
                drug_name = drug.get('name', 'Unknown')
                substance_id = drug.get('substance_id', '')
                
                # Create unique drug identifier
                drug_id = substance_id if substance_id else f"drug_{len(drug_index)}"
                drug_ids.append(drug_id)
                
                # Build drug → diseases mapping
                if drug_id not in drugs2diseases:
                    drugs2diseases[drug_id] = {
                        "drug_name": drug_name,
                        "substance_id": substance_id,
                        "regulatory_id": drug.get('regulatory_id', ''),
                        "status": drug.get('status', ''),
                        "manufacturer": drug.get('manufacturer', ''),
                        "indication": drug.get('indication', ''),
                        "regions": drug.get('regions', []),
                        "diseases": [],
                        "substance_url": drug.get('substance_url', ''),
                        "regulatory_url": drug.get('regulatory_url', '')
                    }
                    
                    # Store full drug details in index
                    drug_index[drug_id] = drug
                
                # Add disease to drug's disease list (avoid duplicates)
                disease_entry = {
                    "orpha_code": orpha_code,
                    "disease_name": disease_name
                }
                
                if disease_entry not in drugs2diseases[drug_id]["diseases"]:
                    drugs2diseases[drug_id]["diseases"].append(disease_entry)
            
            # Add to diseases mapping
            diseases2drugs[orpha_code] = {
                "disease_name": disease_name,
                "orpha_code": orpha_code,
                "drugs_count": len(drug_ids),
                "last_processed_run": run_number,
                "drugs": drug_ids
            }
            
            logger.info(f"Processed {disease_name} ({orpha_code}): {len(drug_ids)} drugs from run {run_number}")
    
    # Convert defaultdict to regular dict for JSON serialization
    drugs2diseases = dict(drugs2diseases)
    processing_stats["total_unique_drugs"] = len(drugs2diseases)
    processing_stats["diseases_by_run"] = dict(processing_stats["diseases_by_run"])
    
    # Save aggregated data
    with open(output_dir / "diseases2drugs.json", 'w', encoding='utf-8') as f:
        json.dump(diseases2drugs, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "drugs2diseases.json", 'w', encoding='utf-8') as f:
        json.dump(drugs2diseases, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "drug_index.json", 'w', encoding='utf-8') as f:
        json.dump(drug_index, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "processing_summary.json", 'w', encoding='utf-8') as f:
        json.dump(processing_stats, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n=== Drug Data Aggregation Complete ===")
    print(f"Total diseases processed: {processing_stats['total_diseases_processed']}")
    print(f"Diseases with drugs: {processing_stats['diseases_with_drugs']}")
    print(f"Total unique drugs: {processing_stats['total_unique_drugs']}")
    print(f"Empty diseases: {len(processing_stats['empty_diseases'])}")
    print(f"Output saved to: {output_dir}")
    
    return processing_stats


if __name__ == "__main__":
    preprocessing_dir_path = "data/02_preprocess/orpha/orphadata/orpha_drugs"
    output_dir_path = "data/03_process/orpha/orphadata/orpha_drugs"
    aggregate_drug_data(preprocessing_dir_path, output_dir_path) 