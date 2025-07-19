# Orpha Drugs Curation V2 Task Plan

## Overview
Create `curate_orpha_drugs_v2.py` script that processes Orpha drugs data from preprocessed directories and generates curated JSON files for regional and type-based accessibility analysis. Uses simple functions (like `process_orpha_drugs.py`) instead of complex classes.

## Input Data Structure

### Source Directory
- **Path**: `data/02_preprocess/orpha/orphadata/orpha_drugs/`
- **Structure**: 
  ```
  data/02_preprocess/orpha/orphadata/orpha_drugs/
  ├── 5/
  │   └── run1_disease2orpha_drugs.json
  ├── 14/
  │   └── run1_disease2orpha_drugs.json
  ├── 37/
  │   └── run1_disease2orpha_drugs.json
  └── ... (665+ disease directories)
  ```

### New JSON Schema
Each `run*_disease2orpha_drugs.json` file contains:
```json
{
  "disease_name": "Long chain 3-hydroxyacyl-CoA dehydrogenase deficiency",
  "orpha_code": "5",
  "drugs": [
    {
      "name": "Triheptanoin",
      "substance_url": "/en/drug/substance/317333?name=5&mode=orpha&region=&status=all",
      "substance_id": "317333",
      "regulatory_url": "/en/drug/regulatory/444892?name=5&mode=orpha&region=",
      "regulatory_id": "444892",
      "is_tradename": false,
      "is_medical_product": true,
      "is_available_in_us": false,
      "is_available_in_eu": true,
      "is_specific": true
    }
  ],
  "processing_timestamp": "2025-07-07T06:03:27.933468",
  "run_number": 1,
  "total_drugs_found": 10
}
```

## Output Files

### Target Directory
- **Path**: `data/04_curated/orpha/orphadata/`

### Generated Files
1. `disease2eu_tradename_drugs.json` - EU tradename drugs by disease
2. `disease2all_tradename_drugs.json` - All tradename drugs by disease
3. `disease2usa_tradename_drugs.json` - USA tradename drugs by disease
4. `disease2eu_medical_product_drugs.json` - EU medical products by disease
5. `disease2all_medical_product_drugs.json` - All medical products by disease
6. `disease2usa_medical_product_drugs.json` - USA medical products by disease
7. `drug2name.json` - Drug ID to name mapping
8. `orpha_drugs_curation_summary.json` - Processing summary and statistics

## Schema Updates Required

### New Schema File
- **Path**: `core/schemas/orpha/orphadata/orpha_drugs_v2.py`
- **Purpose**: Define Pydantic models for new boolean-based drug schema

### New Models Needed
```python
class DrugInstanceV2(BaseModel):
    """New drug instance model with boolean flags"""
    name: str
    substance_url: Optional[str]
    substance_id: Optional[str]
    regulatory_url: Optional[str]
    regulatory_id: Optional[str]
    is_tradename: bool
    is_medical_product: bool
    is_available_in_us: bool
    is_available_in_eu: bool
    is_specific: bool

class DiseaseDataV2(BaseModel):
    """Disease data with drugs using new schema"""
    disease_name: str
    orpha_code: str
    drugs: List[DrugInstanceV2]
    processing_timestamp: str
    run_number: int
    total_drugs_found: int
```

### Helper Functions
```python
def is_tradename_drug_v2(drug: DrugInstanceV2) -> bool:
    return drug.is_tradename

def is_medical_product_v2(drug: DrugInstanceV2) -> bool:
    return drug.is_medical_product

def is_available_in_region_v2(drug: DrugInstanceV2, region: str) -> bool:
    if region.upper() == "ALL":
        return True
    elif region.upper() in ["US", "USA"]:
        return drug.is_available_in_us
    elif region.upper() in ["EU", "EUROPE"]:
        return drug.is_available_in_eu
    return False
```

## Script Architecture

### Main Script Path
- **Location**: `etl/04_curate/orpha/orphadata/curate_orpha_drugs_v2.py`

### Function Structure
Following `process_orpha_drugs.py` pattern:

```python
def get_latest_non_empty_run(disease_dir: Path) -> tuple:
    """Get the latest run with non-empty drugs for a disease"""

def load_disease_data_v2(disease_dir: Path) -> DiseaseDataV2:
    """Load and validate disease data using new schema"""

def aggregate_drugs_by_criteria(diseases_data: Dict, drug_type: str, region: str) -> Dict:
    """Filter and aggregate drugs by type and region"""

def generate_drug_name_mapping(diseases_data: Dict) -> Dict[str, str]:
    """Create drug ID to name mapping"""

def save_curated_file(data: Dict, filename: str, output_dir: Path):
    """Save curated data to JSON file"""

def curate_orpha_drugs_v2(input_dir: str, output_dir: str) -> Dict:
    """Main curation function"""
```

## Processing Logic

### 1. Data Loading
- Scan `data/02_preprocess/orpha/orphadata/orpha_drugs/` for disease directories
- For each disease directory, get latest non-empty run file
- Load and validate JSON data using new schema
- Aggregate all disease data

### 2. Drug Filtering and Categorization
For each combination of (drug_type, region):
- **Drug Types**: `tradename`, `medical_product`
- **Regions**: `EU`, `USA`, `ALL`

Filter logic:
```python
# For tradename drugs in EU
eu_tradename_drugs = {
    orpha_code: [drug.substance_id for drug in disease.drugs 
                if drug.is_tradename and drug.is_available_in_eu]
    for orpha_code, disease in diseases_data.items()
}
```

### 3. Output Generation
Generate 6 main output files:
- `disease2{region}_{type}_drugs.json` for each combination
- Each file maps `orpha_code` → `[drug_ids]`
- Additional `drug2name.json` mapping `drug_id` → `drug_name`

### 4. Summary Statistics
Generate `orpha_drugs_curation_summary.json` with:
- Total diseases processed
- Total unique drugs
- Coverage statistics by region and type
- Processing metadata

## Implementation Steps

### Step 1: Update Schema
- [ ] Create `core/schemas/orpha/orphadata/orpha_drugs_v2.py`
- [ ] Define `DrugInstanceV2` and `DiseaseDataV2` models
- [ ] Add helper functions for filtering

### Step 2: Main Script Functions
- [ ] `get_latest_non_empty_run()` - Similar to process script
- [ ] `load_disease_data_v2()` - Load with new schema validation
- [ ] `aggregate_drugs_by_criteria()` - Filter by type/region using boolean flags
- [ ] `generate_drug_name_mapping()` - Create drug ID to name mapping
- [ ] `save_curated_file()` - Save JSON with error handling

### Step 3: Main Processing Function
- [ ] `curate_orpha_drugs_v2()` - Main aggregation logic
- [ ] Process all disease directories
- [ ] Generate all 6 drug filtering combinations
- [ ] Generate drug name mapping
- [ ] Generate summary statistics
- [ ] Save all output files

### Step 4: CLI Interface
- [ ] Add argument parsing for input/output directories
- [ ] Add verbose logging option
- [ ] Add summary output to console

## Expected Output Structure

### Regional Drug Files
```json
{
  "5": ["317333", "604812"],
  "14": ["123456"],
  "37": []
}
```

### Drug Name Mapping
```json
{
  "317333": "Triheptanoin",
  "604812": "Sodium (4-{(E)-3-(4-fluorophenyl)...)",
  "615857": "DOJOLVI"
}
```

### Summary Statistics
```json
{
  "curation_metadata": {
    "total_diseases_with_drugs": 450,
    "total_unique_drugs": 1250,
    "tradename_coverage": {
      "eu": 200,
      "usa": 180,
      "all": 220
    },
    "medical_product_coverage": {
      "eu": 380,
      "usa": 350,
      "all": 400
    },
    "processing_timestamp": "2025-01-15T10:30:00"
  }
}
```

## Quality Assurance

### Data Validation
- Validate each disease file against new schema
- Log warnings for invalid or missing data
- Track processing statistics and errors

### Output Verification
- Verify all 6 output files are generated
- Check file sizes and record counts
- Generate comprehensive processing log

### Performance Considerations
- Process files in parallel where possible
- Use generators for large datasets
- Implement progress tracking for long operations

## Dependencies

### Required Imports
```python
import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# New schema imports
from core.schemas.orpha.orphadata.orpha_drugs_v2 import (
    DrugInstanceV2,
    DiseaseDataV2,
    is_tradename_drug_v2,
    is_medical_product_v2,
    is_available_in_region_v2
)
```

### Script Location
- **Main script**: `etl/04_curate/orpha/orphadata/curate_orpha_drugs_v2.py`
- **Schema file**: `core/schemas/orpha/orphadata/orpha_drugs_v2.py`

This plan provides a complete roadmap for implementing the new curation script with the updated schema and simple function-based approach. 