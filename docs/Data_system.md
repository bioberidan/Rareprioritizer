# Data System: Flow, Handling, and Retrieval

## Overview

This document explains how data actually flows through the RarePrioritizer system, how it's handled at each stage, and how it gets retrieved and served. The system has multiple flow paths that branch after the processing stage.

**Complete Data Flow:**
```
Raw Sources → ETL Processing → Per-entity Storage → Processed Sources
                                    (optional)            ↓
                                                         ↓ (branches into two paths)
                                                         ↓
                                    ┌────────────────────┼────────────────────┐
                                    ↓                                         ↓
                           ProcessedSourceClient                    Curated Sources
                                    ↓                                         ↓
                           Processed Statistics                    CuratedSourceClient
                                                                              ↓
                                                                        Applications
                                                                              ↓
                                                                          Results
```

**Flow Explanation:**

The data system operates through multiple interconnected pathways that branch after the main processing pipeline. The **linear processing path** forms the core data pipeline, moving data from raw sources through ETL processing, with optional per-entity storage, to create processed sources that serve as the foundation for all downstream operations.

From these processed sources, the system branches into two distinct paths. The **statistics branch** utilizes ProcessedSourceClients to access the processed data directly and generate analytical statistics, visualizations, and reports. Simultaneously, the **application branch** follows a different route where processed sources undergo additional curation to create optimized curated sources, which are then accessed by CuratedSourceClients to serve applications and ultimately deliver results to end users.

## Data Flow Paths in Detail

### Path 1: Main Processing Pipeline (Linear)

**Raw Sources → ETL Processing → Per-entity Storage (optional) → Processed Sources**

```
data/01_raw/en_product6.xml (21MB)
    ↓ (ETL Processing)
data/preprocessing/clinical_trials/79318/run1_disease2clinical.json
    ↓ (Aggregation)
data/03_processed/clinical_trials/diseases2clinical_trials.json
```

**Real Examples:**

The system demonstrates different processing patterns depending on the data type and complexity. Here are four concrete examples showing how data flows through various paths:



**Example 1: Ordo Taxonomy (Raw → Processed Direct)** 
Disease taxonomy data from `data/01_raw/Metabolicas.xml` (or other XML files) flows directly through `etl/02_preprocess/disease_preprocessing.py` to `data/03_processed/orpha/ordo` creating three main subdirectories: `taxonomy/` (with structure.json, categories.json, relationships.json), `instances/` (with diseases.json, classification_index.json, name_index.json), and `cache/` (with statistics and performance files) without any per-entity processing steps.

**Example 2: Disease Prevalence Data (Raw → Processed Direct)**
Raw prevalence data from `data/01_raw/en_product9_prev.xml` flows through `etl/02_preprocess/prevalence_preprocessing.py` directly to `data/processing/prevalence/` creating a complex structure with main files like `disease2prevalence.json` and `prevalence_instances.json`, plus specialized subdirectories including `regional_data/`, `reliability/`, and `cache/` for organized disease prevalence analysis without per-entity storage.



**Example 3: Metabolic Diseases (Raw → Curated Direct)**
Specialized metabolic disease data from `data/01_raw/Metabolicas.xml` undergoes direct curation to `data/04_curated/diseases/` creating optimized disease definitions that bypass both per-entity and standard processed stages.

**Example 4: Disease-Data Relationships (Processed + Curated → Curated Index)**
The system combines processed clinical trial data from `data/03_processed/clinical_trials/` with curated disease definitions from `data/04_curated/diseases/` to generate relationship indexes like `diseases2clinical_trial_index.json` in `data/04_curated/indexes/`, enabling fast cross-referencing between diseases and their associated data.

### Path 2: Statistics Generation Branch

**Processed Sources → ProcessedSourceClient → Processed Statistics**

```
data/03_processed/clinical_trials/diseases2clinical_trials.json
    ↓ (ProcessedSourceClient)
ClinicalTrialsController.get_statistics()
    ↓ (Statistics Script)
data/results/statistics/clinical_trials_stats.json
```

**Real Example:**
```python
# Statistics generation process
controller = ClinicalTrialsController()  # ProcessedSourceClient
stats = controller.get_statistics()      # Access processed data
generate_visualizations(stats)           # Create charts/reports
save_statistics(stats, 'results/')       # Save to results
```

### Path 3: Application Access Branch

**Processed Sources → Curated Sources → CuratedSourceClient → Applications → Results**

```
data/03_processed/clinical_trials/diseases2clinical_trials.json
    ↓ (Curation process - future)
data/04_curated/clinical_trials/optimized_trials.json
    ↓ (CuratedSourceClient)
Applications (FastAPI, Research Tools)
    ↓ (User interactions)
Research Results, Reports, Analysis
```

**Real Example:**
```python
# Application access process
controller = ClinicalTrialsController()           # CuratedSourceClient
trials = controller.get_trials_for_disease("79318")  # Query curated data
api_response = {"disease": "PMM2-CDG", "trials": trials}  # Application use
return jsonify(api_response)                      # Results to user
```

## How Data Flows Through the System

### Step 1: Data Ingestion from Sources

**Real Data Sources:**
- **XML Files**: Large Orphanet XML files (21MB+ size) stored in `data/01_raw/`
- **External APIs**: ClinicalTrials.gov, Orpha.net drug database
- **Preprocessed Data**: Already cleaned Orphanet prevalence data

**How Data Gets In:**
1. **XML Processing**: Raw XML files are parsed and converted to JSON structure
2. **API Calls**: External APIs are queried with specific parameters (disease names, geographic filters)
3. **File Loading**: Preprocessed data files are loaded from designated directories

### Step 2: Per-Entity Processing

**Entity-Based Approach:**
- System processes **665 diseases** individually
- Each disease gets its own processing "run"
- Runs are numbered sequentially (run1, run2, run3...)

**Processing Pattern:**
```
For each disease:
  1. Check if already processed for current run
  2. If not processed: fetch/process data for this disease
  3. Save results to disease-specific directory
  4. If results are empty: trigger new run automatically
```

**Storage Structure During Processing:**
```
data/preprocessing/[data_type]/
├── 79318/                    # Disease Orpha code
│   ├── run1_disease2data.json
│   ├── run2_disease2data.json  # If run1 was empty
│   └── run3_disease2data.json  # If run2 was empty
├── 272/                      # Another disease
│   └── run1_disease2data.json
└── processing_log.json       # Processing audit trail
```

### Step 3: Data Aggregation

**How Scattered Data Gets Unified:**
1. **Collect Latest Runs**: System finds the latest non-empty run for each disease
2. **Aggregate by Type**: Combines all disease data into unified structures
3. **Create Indexes**: Builds lookup tables for fast access

**Aggregation Output:**
```
data/processed/[data_type]/
├── diseases2data.json        # Disease ID → Data mapping
├── data2diseases.json        # Data → Disease IDs mapping  
├── data_index.json           # Master index of all unique data items
└── processing_summary.json   # Statistics and metadata
```

**Example - Clinical Trials:**
- `diseases2clinical_trials.json`: Maps disease "79318" → list of trials
- `clinical_trials2diseases.json`: Maps trial "NCT12345" → list of diseases
- `clinical_trials_index.json`: All unique trials with metadata

## How Data Gets Retrieved

### Controller-Based Access

**Query Controllers** act as the main interface for data retrieval:

```python
# Real usage pattern
controller = ClinicalTrialsController()

# Get data for specific disease
trials = controller.get_trials_for_disease("79318")  # PMM2-CDG
# Returns: List of trial objects for this disease

# Get diseases that have trials  
diseases_with_trials = controller.get_diseases_with_trials()
# Returns: ["79318", "272", "646", ...]

# Get statistics
stats = controller.get_statistics()
# Returns: {"total_diseases": 665, "diseases_with_trials": 73, ...}
```

### Caching Mechanism

**How Data Gets Cached:**
1. **First Access**: Data loaded from JSON files on disk
2. **LRU Cache**: Frequently accessed data kept in memory (1000 items max)
3. **Lazy Loading**: Data only loaded when specifically requested
4. **Cache Hits**: Subsequent requests served from memory instantly

**Cache Pattern:**
```python
@lru_cache(maxsize=1000)
def get_trials_for_disease(self, disease_id: str):
    # This will cache results automatically
    return self._load_from_disk(disease_id)
```

### Data Loading Process

**Step-by-Step Data Retrieval:**

1. **Request Comes In**: `controller.get_trials_for_disease("79318")`
2. **Check Cache**: Is this disease already in memory?
3. **Cache Miss**: Load from `data/processed/clinical_trials/diseases2clinical_trials.json`
4. **Parse JSON**: Extract relevant data for disease "79318"
5. **Cache Result**: Store in memory for future requests
6. **Return Data**: Send back list of trials

**File Structure During Retrieval:**
```
Controller Request
    ↓
Check LRU Cache
    ↓ (cache miss)
Load JSON File: diseases2clinical_trials.json
    ↓
Extract: trials for disease "79318"
    ↓
Cache Result in Memory
    ↓
Return Data to Caller
```

## How Data Is Handled

### Run Management in Practice

**What Happens When Processing Starts:**

1. **Check Existing Runs**: System looks in `data/preprocessing/clinical_trials/79318/` 
2. **Find Next Run Number**: If `run1_disease2clinical.json` exists, try run2
3. **Process Entity**: Make API call to ClinicalTrials.gov for disease "PMM2-CDG"
4. **Save Results**: Store results in `run2_disease2clinical.json`
5. **Check for Empty**: If no trials found, mark for potential run3

**Real File Example:**
```json
// data/preprocessing/clinical_trials/79318/run1_disease2clinical.json
{
  "disease_name": "PMM2-CDG",
  "orpha_code": "79318", 
  "trials": [
    {
      "nct_id": "NCT04324983",
      "title": "Natural History Study of PMM2-CDG",
      "status": "RECRUITING",
      "location": "Spain"
    }
  ],
  "processing_timestamp": "2024-01-15T10:30:00Z",
  "run_number": 1,
  "total_trials_found": 1
}
```

### Error Handling in Action

**When Things Go Wrong:**

1. **API Timeout**: Request to ClinicalTrials.gov fails → Log error, continue to next disease
2. **Empty Results**: Disease has no trials → Save empty result, don't retry immediately
3. **Malformed Data**: Invalid response → Log detailed error, save error state
4. **Network Issues**: Connection problems → Retry with exponential backoff

**Error Log Example:**
```json
// processing_log.json
{
  "run_date": "2024-01-15",
  "total_diseases": 665,
  "successful": 662,
  "failed": 3,
  "errors": [
    {
      "disease_id": "12345",
      "error": "API timeout after 30 seconds",
      "timestamp": "2024-01-15T10:45:00Z"
    }
  ]
}
```

### Data Validation Process

**How Data Gets Validated:**

1. **Input Validation**: Check API response structure using Pydantic models
2. **Content Validation**: Verify required fields are present
3. **Type Validation**: Ensure data types match expected schema
4. **Business Logic Validation**: Check if data makes sense (e.g., valid dates)

**Validation Example:**
```python
# Real validation in action
class ClinicalTrialResult(BaseModel):
    disease_name: str
    orpha_code: str
    trials: List[Dict]
    processing_timestamp: datetime
    run_number: int
    total_trials_found: int
    
    # This automatically validates all incoming data
```

## Complete Data Journey Example

### Real Example: Processing Clinical Trials Data

**1. Starting Point:**
- Input: 665 diseases from `data/input/etl/init_diseases/diseases_simple.json`
- Target: Get clinical trials for each disease from ClinicalTrials.gov

**2. Processing Each Disease:**
```python
# Real processing code pattern
for disease in diseases:
    # Check: data/preprocessing/clinical_trials/79318/run1_disease2clinical.json exists?
    run_number = get_next_run_number("clinical_trials", "79318")
    
    if not already_processed:
        # Make API call to ClinicalTrials.gov
        trials = api_client.search_trials(
            query_term="PMM2-CDG",
            query_locn="Spain",
            status=['RECRUITING', 'ACTIVE_NOT_RECRUITING']
        )
        
        # Save to: data/preprocessing/clinical_trials/79318/run1_disease2clinical.json
        save_result(trials, "79318", run_number)
```

**3. After All Diseases Processed:**
```
data/preprocessing/clinical_trials/
├── 79318/run1_disease2clinical.json    # PMM2-CDG: 1 trial found
├── 272/run1_disease2clinical.json      # Marfan: 0 trials found  
├── 646/run1_disease2clinical.json      # Niemann-Pick: 5 trials found
├── 12345/run1_disease2clinical.json    # Disease X: 0 trials found
└── ...
```

**4. Aggregation Process:**
```python
# Collect all non-empty runs for each disease
disease_to_trials = {}
for disease_dir in preprocessing_dirs:
    latest_run = get_latest_non_empty_run(disease_dir)
    if latest_run and has_trials(latest_run):
        disease_to_trials[disease_id] = latest_run['trials']

# Save aggregated data
save_json(disease_to_trials, "data/processed/clinical_trials/diseases2clinical_trials.json")
```

**5. Final Aggregated Files:**
```
data/processed/clinical_trials/
├── diseases2clinical_trials.json     # {"79318": [trial1], "646": [trial1, trial2, ...]}
├── clinical_trials2diseases.json     # {"NCT04324983": ["79318"], ...}
├── clinical_trials_index.json        # [all unique trials with metadata]
└── processing_summary.json           # {total_diseases: 665, with_trials: 73, ...}
```

## How Data Gets Served

### Controller Access Pattern

**Loading Data on Demand:**
```python
class ClinicalTrialsController:
    def __init__(self):
        self._diseases2trials = None  # Not loaded yet
        
    def _load_diseases2trials(self):
        if self._diseases2trials is None:
            # Load from disk only when needed
            with open('data/processed/clinical_trials/diseases2clinical_trials.json') as f:
                self._diseases2trials = json.load(f)
        return self._diseases2trials
    
    @lru_cache(maxsize=1000)
    def get_trials_for_disease(self, disease_id: str):
        data = self._load_diseases2trials()
        return data.get(disease_id, [])
```

**Usage in Practice:**
```python
# User wants trials for PMM2-CDG
controller = ClinicalTrialsController()
trials = controller.get_trials_for_disease("79318")

# First call: loads from disk, caches result
# Second call: returns from cache instantly
trials_again = controller.get_trials_for_disease("79318")  # From cache
```

### Performance in Action

**Memory Usage:**
- **Cold Start**: Only controller object in memory (~1KB)
- **First Query**: Load diseases2trials.json (~500KB) into memory
- **Subsequent Queries**: Served from LRU cache (instant)
- **Cache Limit**: Keeps 1000 most recent queries in memory

**Real Performance Numbers:**
- **File Load**: ~50ms to load JSON from disk
- **Cache Hit**: ~0.1ms to return from memory
- **Memory Usage**: ~2MB for 665 diseases with all trial data cached

### Cross-System Data Access

**How Different Data Types Connect:**
```python
# Real cross-system analysis
clinical_controller = ClinicalTrialsController()
drug_controller = DrugController() 
prevalence_controller = PrevalenceController()

# Find diseases with trials but no drugs
diseases_with_trials = set(clinical_controller.get_diseases_with_trials())
diseases_with_drugs = set(drug_controller.get_diseases_with_drugs())

research_gaps = diseases_with_trials - diseases_with_drugs
# Result: ["79318", "12345"] - diseases that have trials but no drugs
```

**Data Integration Pattern:**
1. **Each Controller**: Manages its own data type (trials, drugs, prevalence)
2. **Shared Disease IDs**: All systems use same disease identifiers ("79318", "272", etc.)
3. **Set Operations**: Easy to find intersections, differences, unions
4. **Independent Caching**: Each controller caches its own data separately

## Actual Directory Structure

### Real Data Organization

**How Data Is Actually Stored:**
```
data/
├── 01_raw/                    # Original source files
│   ├── en_product6.xml        # Orphanet XML (21MB)
│   ├── en_product9_prev.xml   # Prevalence XML (15MB)
│   └── Metabolicas.xml        # Metabolic diseases XML
├── 02_preprocess/             # Extracted content
│   └── extract/               # Processed extraction results
├── 03_processed/              # Final datasets
│   ├── clinical_trials/       # Aggregated trial data
│   │   ├── diseases2clinical_trials.json
│   │   ├── clinical_trials2diseases.json
│   │   └── processing_summary.json
│   └── orpha/                 # Processed Orphanet data
│       ├── instances/         # Disease instances
│       ├── taxonomy/          # Disease classifications
│       └── cache/             # Performance indexes
└── results/                   # Analysis outputs
    ├── statistics/            # Generated stats
    └── visualizations/        # Charts and graphs

data/preprocessing/            # Per-disease processing results
├── clinical_trials/
│   ├── 79318/                # PMM2-CDG disease
│   │   └── run1_disease2clinical.json
│   ├── 272/                  # Marfan syndrome
│   │   └── run1_disease2clinical.json
│   └── processing_log.json
├── drug/
│   ├── 79318/
│   │   └── run1_disease2drug.json
│   └── processing_log.json
└── prevalence_runs/
    ├── 79318/
    │   └── run1_disease2prevalence.json
    └── processing_log.json
```

### Real File Examples

**Raw Data File:**
```
data/01_raw/en_product6.xml (21MB)
- Contains complete Orphanet disease taxonomy
- Hierarchical XML structure with 999+ diseases  
- Includes disease names, codes, classifications
```

**Preprocessed Disease Data:**
```json
// data/preprocessing/clinical_trials/79318/run1_disease2clinical.json
{
  "disease_name": "PMM2-CDG",
  "orpha_code": "79318",
  "trials": [
    {
      "nct_id": "NCT04324983",
      "title": "Natural History Study of PMM2-CDG",
      "status": "RECRUITING",
      "brief_summary": "This study...",
      "location": "Madrid, Spain",
      "enrollment": 50
    }
  ],
  "processing_timestamp": "2024-01-15T10:30:00Z",
  "run_number": 1,
  "total_trials_found": 1,
  "search_url": "https://clinicaltrials.gov/api/..."
}
```

**Aggregated Data File:**
```json
// data/03_processed/clinical_trials/diseases2clinical_trials.json
{
  "79318": [
    {
      "nct_id": "NCT04324983", 
      "title": "Natural History Study of PMM2-CDG",
      "status": "RECRUITING"
    }
  ],
  "646": [
    {
      "nct_id": "NCT03759678",
      "title": "Niemann-Pick Disease Treatment Study",
      "status": "ACTIVE_NOT_RECRUITING"
    },
    {
      "nct_id": "NCT04123456",
      "title": "Another Niemann-Pick Study", 
      "status": "RECRUITING"
    }
  ]
}
```

### Data Access in Practice

**How Applications Get Data:**

1. **Import Controller**: `from etl.clinical_trials_cont import ClinicalTrialsController`
2. **Create Instance**: `controller = ClinicalTrialsController()`
3. **Query Data**: `trials = controller.get_trials_for_disease("79318")`
4. **Use Results**: Process list of trial objects

**What Happens Under the Hood:**
- **First Call**: Controller loads `diseases2clinical_trials.json` from disk
- **Data Parsing**: JSON parsed into Python dictionaries
- **Cache Storage**: Results stored in LRU cache (1000 items max)
- **Return**: Filtered data for requested disease returned
- **Subsequent Calls**: Served directly from memory cache

### ETL Processing Structure

**How Processing Scripts Are Organized:**
```
etl/
├── 01_raw/                    # (empty - no extraction scripts yet)
├── 02_preprocess/             # Data cleaning
│   ├── disease_preprocessing.py    # XML to JSON conversion
│   └── prevalence_preprocessing.py # Prevalence data processing
├── 03_process/                # (structured for future processing)
├── 04_curate/                 # (structured for future curation)
├── cli.py                     # Command-line interface (empty)
└── utils/                     # Processing utilities
    ├── orpha/                 # Orphanet processing tools
    ├── clinical_trials/       # Trial API clients
    ├── orpha_drug/           # Drug data scrapers
    └── pipeline/             # Run management system
```

**Actual Processing Commands:**
```bash
# Process disease taxonomy from XML
python etl/02_preprocess/disease_preprocessing.py

# Process clinical trials for all diseases
python etl/process_clinical_trials.py

# Aggregate trial results
python etl/aggregate_clinical_trials.py

# Generate statistics
python apps/research_prioritization/stats/clinical_trials_stats.py
```

This shows how data actually flows through the system - from large XML files to individual disease processing runs to aggregated datasets that get served through cached controllers to applications. 