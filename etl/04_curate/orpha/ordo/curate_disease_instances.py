import json
from pathlib import Path


def extract_diseases():
    """Extract and filter diseases from processed Orpha data"""
    
    source_file = "data/processed/orpha/ordo/instances/diseases.json"
    output_file = "data/input/etl/init_diseases/diseases_simple.json"
    
    with open(source_file, 'r', encoding='utf-8') as f:
        diseases_data = json.load(f)
    
    filtered_diseases = []
    
    for disease_id, disease_info in diseases_data.items():
        disorder_type = disease_info.get('metadata', {}).get('disorder_type', '')
        
        if disorder_type in ["Disease", "Malformation syndrome"]:
            filtered_diseases.append({
                "disease_name": disease_info['name'],
                "orpha_code": disease_info['id']
            })
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_diseases, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted {len(filtered_diseases)} diseases to {output_file}")
    
    return filtered_diseases


if __name__ == "__main__":
    extract_diseases() 