import json
import random
from pathlib import Path


def select_random_diseases(input_file="data/input/etl/init_diseases/diseases_simple.json", 
                          output_file="data/input/etl/init_diseases/diseases_sample_10.json",
                          sample_size=10, seed=42):
    """Select random diseases for testing"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        diseases = json.load(f)
    
    random.seed(seed)
    selected_diseases = random.sample(diseases, min(sample_size, len(diseases)))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_diseases, f, indent=2, ensure_ascii=False)
    
    print(f"Selected {len(selected_diseases)} random diseases to {output_file}")
    
    for disease in selected_diseases:
        print(f"  - {disease['disease_name']} ({disease['orpha_code']})")
    
    return selected_diseases


if __name__ == "__main__":
    select_random_diseases() 