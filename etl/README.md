# ETL Pipeline: Rare Disease Data Processing System

## Overview

The ETL (Extract, Transform, Load) pipeline is the backbone of the RarePrioritizer system, responsible for processing raw rare disease data from multiple sources into structured, analysis-ready datasets. The system uses a 5-stage pipeline architecture with robust run management and error handling capabilities.

**Complete ETL Pipeline Flow:**
```
Raw Data Sources → 01_raw → 02_preprocess → 03_process → 04_curate → 05_stats
                      ↓           ↓            ↓           ↓           ↓
                   Extract → Clean & Parse → Aggregate → Optimize → Analyze
```

**Pipeline Explanation:**

The ETL system processes data through five distinct stages, each with specific responsibilities. Raw data from various sources (XML files, APIs, external databases) is first extracted and stored, then preprocessed to clean and structure the data per-disease, aggregated into unified datasets, curated for quality and consistency, and finally analyzed to generate statistics and insights.

## Directory Structure

```
etl/
├── 01_raw/                     # Data extraction (future)
│   ├── metabolic/             # Metabolic disease extraction
│   └── orpha/                 # Orphanet data extraction
├── 02_preprocess/             # Data cleaning and per-disease processing
│   ├── clinical_trials/       # Clinical trials preprocessing
│   ├── orpha/                 # Orphanet data preprocessing  
│   └── websearch/             # Web search data preprocessing
├── 03_process/                # Data aggregation and unification
│   ├── clinical_trials/       # Clinical trials aggregation
│   ├── orpha/                 # Orphanet data processing
│   └── websearcher/           # Web search aggregation
├── 04_curate/                 # Data optimization and quality assurance
│   ├── clinical_trials/       # Clinical trials curation
│   ├── orpha/                 # Orphanet data curation
│   └── websearch/             # Web search curation
├── 05_stats/                  # Statistics and analysis generation
│   ├── clinical_trials/       # Clinical trials statistics
│   ├── metabolic/             # Metabolic disease statistics
│   ├── orpha/                 # Orphanet statistics
│   └── websearch/             # Web search statistics
├── utils/                     # ETL utilities and tools
│   ├── run_management.py      # Run tracking and management
│   └── README.md              # Utilities documentation
└── cli.py                     # Command-line interface (future)
```

## Data Types Processed

The ETL pipeline processes multiple data types for rare disease research:

### Core Data Types
- **`clinical_trials`**: Clinical trials from ClinicalTrials.gov API
- **`orpha`**: Orphanet disease taxonomy, prevalence, and gene data
- **`websearch`**: Socioeconomic impact studies from web searches
- **`drug`**: Drug and treatment information from Orphanet
- **`metabolic`**: Specialized metabolic disease data

### Data Processing Scope
- **665 Diseases**: Complete metabolic disease subset processing
- **4,078+ Diseases**: Full Orphanet taxonomy coverage
- **Per-Disease Processing**: Individual disease-level data extraction
- **Cross-Reference Integration**: Multi-source data linking

## ETL Pipeline Stages

### Stage 1: 01_raw - Data Extraction

**Purpose**: Extract raw data from external sources and store locally.

**Current Sources**:
- **XML Files**: Large Orphanet XML files (21MB+)
  - `en_product6.xml`: Disease-gene associations
  - `en_product9_prev.xml`: Disease prevalence data
  - `Metabolicas.xml`: Metabolic diseases taxonomy
- **External APIs**: ClinicalTrials.gov, Orphanet drug database
- **Preprocessed Data**: Already cleaned data files

**Output**: Raw data files stored in `data/01_raw/`

### Stage 2: 02_preprocess - Data Cleaning & Parsing

**Purpose**: Clean, parse, and structure raw data on a per-disease basis.

**Key Features**:
- **Per-Disease Processing**: Each disease processed independently
- **Run Management**: Automatic run numbering and tracking
- **Error Handling**: Graceful failure handling with retry capability
- **Data Validation**: Schema validation using Pydantic models

**Processing Pattern**:
```python
for disease in diseases:
    run_number = get_next_run_number("clinical_trials", orphacode)
    if not is_disease_processed(orphacode, "clinical_trials", run_number):
        results = process_disease_data(disease)
        save_processing_result(results, "clinical_trials", orphacode, run_number)
```

**Output Structure**:
```
data/preprocessing/{data_type}/
├── {orphacode}/
│   ├── run1_disease2{data_type}.json
│   ├── run2_disease2{data_type}.json  # If reprocessing needed
│   └── run{n}_disease2{data_type}.json
└── processing_log.json
```

**Examples**:
- **Clinical Trials**: `preprocess_clinical_trials.py` - Query ClinicalTrials.gov API for each disease
- **Orpha Data**: Process XML to extract gene associations, prevalence data
- **Web Search**: Extract socioeconomic impact studies for diseases

### Stage 3: 03_process - Data Aggregation

**Purpose**: Aggregate per-disease data into unified, structured datasets.

**Key Features**:
- **Latest Run Selection**: Automatically selects latest non-empty run for each disease
- **Bidirectional Mapping**: Creates both disease→data and data→disease mappings
- **Index Generation**: Builds comprehensive lookup indexes
- **Quality Metrics**: Tracks processing statistics and data quality

**Aggregation Logic**:
```python
def aggregate_data():
    diseases2data = {}
    data2diseases = {}
    
    for disease_dir in preprocessing_dirs:
        run_number, run_data = get_latest_non_empty_run(disease_dir)
        if run_data and has_valid_data(run_data):
            diseases2data[disease_id] = run_data
            # Build reverse mappings...
```

**Output Structure**:
```
data/03_processed/{data_type}/
├── diseases2{data_type}.json        # Disease → Data mapping
├── {data_type}2diseases.json        # Data → Diseases mapping
├── {data_type}_index.json           # Master index
└── processing_summary.json          # Statistics
```

**Examples**:
- **Clinical Trials**: `process_clinical_trials.py` - Aggregate all disease clinical trials
- **Orpha Genes**: `process_orpha_genes.py` - Create gene-disease association datasets
- **Prevalence**: `process_orpha_prevalence.py` - Unify prevalence data with reliability scoring

### Stage 4: 04_curate - Data Optimization

**Purpose**: Optimize processed data for specific use cases and ensure quality.

**Key Features**:
- **Disease Subset Filtering**: Focus on specific disease populations (e.g., 665 metabolic diseases)
- **Quality Filtering**: Apply data quality criteria and validation rules
- **Schema Normalization**: Standardize data formats using Pydantic models
- **Performance Optimization**: Create optimized datasets for fast access

**Curation Process**:
```python
def curate_data():
    # Load target disease subset
    target_diseases = load_metabolic_diseases()
    
    # Filter and validate data
    curated_data = {}
    for disease_id in target_diseases:
        if disease_id in processed_data:
            validated_data = validate_and_normalize(processed_data[disease_id])
            curated_data[disease_id] = validated_data
```

**Output Structure**:
```
data/04_curated/{data_type}/
├── {curated_dataset}.json           # Optimized datasets
├── curation_summary.json            # Curation metadata
└── quality_report.json              # Quality metrics
```

**Examples**:
- **Clinical Trials**: `curate_clinical_trials.py` - Validate and normalize trial data
- **Orpha Genes**: `curate_orpha_genes.py` - Filter disease-causing genes only
- **Drugs**: `curate_orpha_drugs.py` - Standardize drug information

### Stage 5: 05_stats - Statistics & Analysis

**Purpose**: Generate comprehensive statistics and analysis reports.

**Key Features**:
- **Coverage Analysis**: Data coverage across disease populations
- **Quality Metrics**: Data quality and reliability assessments
- **Distribution Analysis**: Statistical distributions and patterns
- **Visualization Generation**: Charts, graphs, and visual reports

**Output Structure**:
```
data/05_stats/{data_type}/
├── {data_type}_statistics.json      # Statistical summaries
├── coverage_analysis.json           # Coverage reports
├── quality_metrics.json             # Quality assessments
└── visualizations/                  # Charts and graphs
```

## Run Management System

The ETL pipeline uses a sophisticated run management system to handle processing reliability and enable reprocessing.

### Key Features

**Per-Disease Run Tracking**: Each disease maintains independent run sequences
```
data/preprocessing/clinical_trials/79318/
├── run1_disease2clinical_trials.json  # First attempt
├── run2_disease2clinical_trials.json  # Reprocessing if needed
└── run3_disease2clinical_trials.json  # Additional reprocessing
```

**Automatic Run Detection**: System automatically determines next run number
```python
run_number = get_next_run_number("clinical_trials", "79318")  # Returns: 2
```

**Empty Run Handling**: System detects empty results and enables reprocessing
```python
if should_reprocess_disease("clinical_trials", "79318", run_number):
    # Reprocess with new run number
```

**Latest Run Selection**: Aggregation uses latest non-empty run for each disease
```python
run_number, run_data = get_latest_non_empty_run(disease_dir)
```

### Usage Examples

**Check Processing Status**:
```python
from etl.utils.run_management import is_disease_processed, get_next_run_number

run_num = get_next_run_number("clinical_trials", "79318")
if is_disease_processed("79318", "clinical_trials", run_num):
    print("Already processed")
```

**Save Processing Results**:
```python
from etl.utils.run_management import save_processing_result

results = {"disease_name": "PMM2-CDG", "trials": [...]}
save_processing_result(results, "clinical_trials", "79318", run_num)
```

## Running ETL Processes

### Stage-by-Stage Execution

**Preprocessing (Stage 2)**:
```bash
# Clinical trials preprocessing
python etl/02_preprocess/clinical_trials/preprocess_clinical_trials.py

# Orpha data preprocessing  
python etl/02_preprocess/orpha/process_diseases.py
```

**Processing/Aggregation (Stage 3)**:
```bash
# Aggregate clinical trials
python etl/03_process/clinical_trials/process_clinical_trials.py

# Process Orpha genes
python etl/03_process/orpha/orphadata/process_orpha_genes.py
```

**Curation (Stage 4)**:
```bash
# Curate clinical trials
python etl/04_curate/clinical_trials/curate_clinical_trials.py

# Curate gene associations
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py
```

**Statistics (Stage 5)**:
```bash
# Generate clinical trials statistics
python etl/05_stats/clinical_trials/clinical_trials_stats.py

# Generate gene statistics
python etl/05_stats/orpha/orphadata/orpha_genes_stats.py
```

### Configuration

ETL processes can be configured through YAML files and command-line arguments:

**Configuration File**: `etl/03_process/config.yaml`
```yaml
# ETL processing configuration
processing:
  batch_size: 100
  timeout: 30
  max_retries: 3
```

**Command-Line Options**:
```bash
# Custom input/output paths
python process_clinical_trials.py --input custom_diseases.json --output custom_output/

# Verbose logging
python process_orpha_genes.py --verbose

# Force reprocessing
python preprocess_clinical_trials.py --force
```

## Data Flow Examples

### Clinical Trials Processing Flow

**Complete Flow**:
```
1. Raw API calls → data/preprocessing/clinical_trials/79318/run1_disease2clinical_trials.json
2. Aggregation → data/03_processed/clinical_trials/diseases2clinical_trials.json
3. Curation → data/04_curated/clinical_trials/curated_trials.json
4. Statistics → data/05_stats/clinical_trials/trials_statistics.json
```

**Example Data Transformation**:
```json
// Stage 2: Per-disease processing
{
  "disease_name": "PMM2-CDG",
  "orpha_code": "79318",
  "trials": [{"nct_id": "NCT04324983", "title": "PMM2-CDG Study"}],
  "run_number": 1
}

// Stage 3: Aggregated data
{
  "79318": {
    "disease_name": "PMM2-CDG",
    "trials_count": 1,
    "trials": ["NCT04324983"]
  }
}

// Stage 4: Curated data (validated and normalized)
{
  "79318": {
    "disease_name": "PMM2-CDG", 
    "curated_trials": [
      {
        "nct_id": "NCT04324983",
        "brief_title": "PMM2-CDG Study",
        "overall_status": "RECRUITING",
        "locations": [...]
      }
    ]
  }
}
```

### Web Search Processing Flow

**Socioeconomic Impact Studies**:
```
1. Web search → data/preprocessing/websearch/79318/run1_disease2websearch.json
2. Aggregation → data/03_processed/websearch/diseases2websearch.json  
3. Curation → data/04_curated/websearch/socioeconomic_studies.json
4. Statistics → data/05_stats/websearch/impact_analysis.json
```

## Error Handling & Monitoring

### Error Handling Strategies

**Graceful Failure**: Individual disease failures don't stop entire processing
```python
failed_diseases = []
for disease in diseases:
    try:
        process_disease(disease)
    except Exception as e:
        logger.error(f"Failed to process {disease.name}: {e}")
        failed_diseases.append(disease)
        continue  # Continue with next disease
```

**Retry Mechanism**: Automatic retry with exponential backoff
```python
@retry(max_attempts=3, backoff_factor=2)
def process_with_api(disease):
    return api_client.fetch_data(disease)
```

**Comprehensive Logging**: Detailed logging for debugging and monitoring
```python
logger.info(f"Processing {disease.name} (run {run_number})")
logger.warning(f"Empty results for {disease.name}, will retry")
logger.error(f"API failure for {disease.name}: {error}")
```

### Monitoring & Maintenance

**Processing Reports**: Each run generates detailed processing reports
```json
{
  "total_diseases": 665,
  "processed": 652,
  "failed": 13,
  "success_rate": "98.0%",
  "processing_time": "1736.7 seconds",
  "failed_diseases": ["ORPHA:926", "ORPHA:2195"]
}
```

**Data Quality Metrics**: Continuous monitoring of data quality
```json
{
  "coverage": {
    "diseases_with_clinical_trials": 73,
    "diseases_with_genes": 549,
    "diseases_with_prevalence": 421
  },
  "quality": {
    "validated_records": 95.2,
    "reliable_prevalence_data": 67.8
  }
}
```

## Integration with System

### Data Access Integration

The ETL pipeline integrates seamlessly with the broader system through standardized interfaces:

**Controller Access**:
```python
# Access processed data
from core.infrastructure.clinical_trials import ClinicalTrialsController
controller = ClinicalTrialsController()
trials = controller.get_trials_for_disease("79318")

# Access curated data  
from core.datastore.clinical_trials import CuratedClinicalTrialsClient
client = CuratedClinicalTrialsClient()
curated_trials = client.get_curated_trials("79318")
```

**API Integration**:
```python
# FastAPI endpoints use ETL data
@app.get("/diseases/{disease_id}/trials")
def get_disease_trials(disease_id: str):
    controller = ClinicalTrialsController()
    return controller.get_trials_for_disease(disease_id)
```

### Application Usage

**Research Prioritization**: ETL data feeds into prioritization algorithms
```python
# Use ETL data for disease prioritization
clinical_data = clinical_controller.get_all_diseases_with_trials()
prevalence_data = prevalence_controller.get_disease_prevalences()
prioritization_score = calculate_priority(clinical_data, prevalence_data)
```

**Statistics Generation**: ETL statistics used for research insights
```python
# Generate research reports using ETL statistics
stats = load_etl_statistics()
research_report = generate_insights(stats)
```

## Performance & Scalability

### Performance Characteristics

**Processing Speed**:
- **Clinical Trials**: ~1.5 hours for 665 diseases (API limited)
- **Orpha XML**: ~2 minutes for 4,078 diseases (local processing)
- **Aggregation**: ~10 seconds for most data types
- **Curation**: ~30 seconds for quality filtering

**Memory Usage**:
- **Preprocessing**: ~100MB per disease batch
- **Aggregation**: ~500MB for large datasets  
- **Curation**: ~200MB for validation processes
- **Statistics**: ~1GB for visualization generation

**Storage Requirements**:
- **Raw Data**: ~60MB (XML files)
- **Preprocessed**: ~2GB (per-disease files)
- **Processed**: ~100MB (aggregated files)
- **Curated**: ~50MB (optimized datasets)

### Scalability Considerations

**Horizontal Scaling**: Per-disease processing enables parallel execution
```python
# Future: Parallel processing capability
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_disease, disease) for disease in diseases]
```

**Incremental Processing**: Only process changed/new data
```python
# Check for updates and process incrementally
new_diseases = get_updated_diseases_since(last_run_date)
process_diseases(new_diseases)
```

## Troubleshooting

### Common Issues

**Empty Run Results**: Disease processing returns no data
```bash
# Check run files
ls data/preprocessing/clinical_trials/79318/
# Expected: run1_disease2clinical_trials.json with content

# Reprocess if empty
python etl/02_preprocess/clinical_trials/preprocess_clinical_trials.py
```

**API Rate Limiting**: External API requests fail
```python
# Check processing logs for rate limit errors
tail -f data/preprocessing/clinical_trials/processing_log.json

# Wait and rerun - system will continue from last processed disease
```

**Missing Dependencies**: Import errors or missing packages
```bash
# Install required packages
pip install -r requirements.txt

# Check Python path
export PYTHONPATH=/path/to/rareprioritizer:$PYTHONPATH
```

**File Permission Errors**: Cannot write to output directories
```bash
# Check and fix permissions
chmod -R 755 data/
mkdir -p data/preprocessing/clinical_trials/
```

### Debug Commands

**Check Processing Status**:
```bash
# Count processed diseases
find data/preprocessing/clinical_trials -name "run*" | wc -l

# Check failed diseases
grep "ERROR" data/preprocessing/clinical_trials/processing_log.json

# Verify aggregated data
jq '.total_diseases_processed' data/03_processed/clinical_trials/processing_summary.json
```

**Data Validation**:
```bash
# Validate JSON files
python -m json.tool data/03_processed/clinical_trials/diseases2clinical_trials.json

# Check data coverage
python -c "
import json
with open('data/03_processed/clinical_trials/processing_summary.json') as f:
    data = json.load(f)
    print(f'Success rate: {data[\"diseases_with_trials\"]}/{data[\"total_diseases_processed\"]}')
"
```

## Future Enhancements

### Planned Improvements

**Command-Line Interface**: Complete CLI implementation in `cli.py`
```bash
# Future CLI usage
python etl/cli.py preprocess --data-type clinical_trials --diseases-file custom.json
python etl/cli.py aggregate --data-type all --output-dir custom/
python etl/cli.py curate --subset metabolic --quality-filter high
```

**Parallel Processing**: Multi-threaded disease processing
```python
# Planned parallel processing capability
etl_config = {
    "parallel_workers": 4,
    "batch_size": 50,
    "max_memory_usage": "2GB"
}
```

**Real-time Processing**: Stream processing for continuous data updates
```python
# Future real-time capability
from etl.streaming import DataStreamProcessor
processor = DataStreamProcessor()
processor.start_continuous_processing()
```

**Enhanced Monitoring**: Real-time dashboards and alerting
```python
# Planned monitoring integration
from etl.monitoring import ETLMonitor
monitor = ETLMonitor()
monitor.setup_alerts(email="admin@rareprioritizer.org")
```

---

This ETL system provides a robust, scalable foundation for processing rare disease data while maintaining data quality and enabling flexible reprocessing strategies. The modular design allows for easy extension to new data types and processing requirements. 