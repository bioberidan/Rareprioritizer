# Initial Diseases Dataset

## Data Source
- **Source File**: `data/processed/orpha/ordo/instances/diseases.json`
- **Source System**: Orpha taxonomy (Orphanet)
- **Last Updated**: [To be filled when extraction runs]
- **Total Source Records**: [To be filled when extraction runs]

## Filtering Criteria
- **Included Disorder Types**: "Disease", "Malformation syndrome"
- **Excluded Disorder Types**: "Clinical subtype", "Etiological subtype"
- **Filtering Logic**: Extract diseases where `metadata.disorder_type` matches included types

## Used Files (provide explanation)
- **diseases_simple.json**: Filtered and simplified disease list containing only disease names and Orpha codes
- **diseases_sample_10.json**: Random sample of 10 diseases for testing purposes
- **select_random_diseases.py**: Script to regenerate random sample with configurable seed

## Statistics
- **Total Diseases Extracted**: [To be filled when extraction runs]
- **Diseases with "Disease" type**: [To be filled when extraction runs]
- **Diseases with "Malformation syndrome" type**: [To be filled when extraction runs]

## Usage

To regenerate the dataset:

1. Extract all diseases: `python etl/extract_diseases.py`
2. Generate random sample: `python etl/select_random_diseases.py`

## Data Structure

Each disease entry contains:
```json
{
  "disease_name": "PMM2-CDG",
  "orpha_code": "79318"
}
``` 