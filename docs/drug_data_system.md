# Drug Data System Documentation

## Overview

The Drug Data System is a comprehensive ETL pipeline designed to systematically collect, process, and analyze drug/treatment data for rare diseases from Orpha.net. The system processes 665 rare diseases from the Orpha taxonomy and provides structured data for research prioritization decisions, mirroring the clinical trials system architecture.

## System Architecture

### Core Components

#### 1. Data Source Management
- **Source Database**: Orpha.net drug database
- **Disease Taxonomy**: Orpha.net taxonomy (665 diseases)
- **Filtering Logic**: Same diseases as clinical trials system
- **Data Scope**: Comprehensive drug information including regulatory status, manufacturers, and regional availability

#### 2. ETL Pipeline
```
Disease Extraction → Drug Data Processing → Data Aggregation → Query Interface → Statistical Analysis
```

#### 3. Data Flow Architecture
```
Orpha Taxonomy (999 diseases)
    ↓ [Filter by disorder type]
diseases_simple.json (665 diseases)
    ↓ [ETL Processing]
Per-disease JSON files (data/preprocessing/drug/)
    ↓ [Aggregation]
Consolidated datasets (data/processed/drug/)
    ↓ [Query Interface]
Research Applications
```

## Implementation Details

### 1. Disease Source Reuse

**Purpose**: Reuse existing disease dataset from clinical trials system
**Input**: `data/input/etl/init_diseases/diseases_simple.json`
**Strategy**: Identical disease set ensures consistency across systems

**Shared Data Structure**:
```json
[
  {
    "disease_name": "PMM2-CDG",
    "orpha_code": "79318"
  },
  {
    "disease_name": "Marfan syndrome",
    "orpha_code": "272"
  }
]
```

### 2. Drug API Client (`utils/orpha_drug/orpha_drug.py`)

**Purpose**: Interface with Orpha.net drug database
**Source**: Based on `trash_code/orpha_scraper.py`

**Key Components**:
- `OrphaDrugAPIClient`: Main API client class
- `DrugParser`: HTML parsing for drug information
- Rate limiting and respectful scraping practices

**Search Parameters**:
- `disease_name`: Disease name from diseases_simple.json
- `orphacode`: Orphan code for the disease
- `region`: Geographic region filter (optional)
- `status`: Drug status filter (default: "all")

**Rate Limiting**:
- 0.5 second delays between requests (reduced from original 1.5s)
- Respectful user-agent headers
- Session management for connection reuse

### 3. ETL Processing (`etl/process_drug_data.py`)

**Purpose**: Process diseases through Orpha.net API with run management

**Key Features**:
- Sequential processing (no parallelism)
- Per-disease run numbering (mirrors clinical trials system)
- Error handling and logging
- Progress tracking
- Empty run detection and reprocessing

**Processing Logic**:
```python
for disease in diseases:
    run_number = get_next_run_number("drug", disease.orpha_code)
    if not is_disease_processed(disease.orpha_code, "drug", run_number):
        results = api_client.search(
            disease_name=disease.disease_name,
            orphacode=disease.orpha_code
        )
        save_processing_result(results, "drug", disease.orpha_code, run_number)
```

**Output Structure**:
```
data/preprocessing/drug/
├── 79318/                               # PMM2-CDG
│   ├── run1_disease2drug.json
│   └── run2_disease2drug.json           # If run1 was empty
├── 272/                                 # Marfan syndrome
│   └── run1_disease2drug.json
└── processing_log.json
```

### 4. Run Management Integration

**Purpose**: Reuse universal run management system
**Module**: `utils/pipeline/run_management.py`

**Enhanced Features**:
- `should_reprocess_disease()`: Empty run detection specific to drug data
- Same per-disease run numbering as clinical trials
- Automatic reprocessing for empty runs
- Consistent error handling patterns

**Empty Run Logic**:
- Detects runs with no valid drug data
- Triggers automatic reprocessing (run2, run3, etc.)
- Maintains audit trail of processing attempts

### 5. Data Aggregation (`etl/aggregate_drug_data.py`)

**Purpose**: Consolidate per-disease/per-run data into unified structures

**Strategy**: Latest non-empty run selection to avoid data loss

**Output Files** (in `data/processed/drug/`):
- `diseases2drug.json`: Disease → Drug mapping
- `drug2diseases.json`: Drug → Diseases mapping
- `drug_index.json`: Master index of all unique drugs
- `processing_summary.json`: Processing statistics and metadata

### 6. Query Interface (`etl/drug_controller.py`)

**Purpose**: OrphaTaxonomy-style interface with lazy loading

**Architecture**:
- LRU caching for performance
- On-demand data loading
- Rich query methods
- Cross-referencing capabilities

**Key Query Methods**:
```python
controller = DrugController()

# Basic queries
drugs = controller.get_drugs_for_disease("646")
diseases = controller.get_diseases_for_drug("Miglustat")

# Filtered queries
approved_drugs = controller.search_drugs_by_status("approved")
eu_drugs = controller.search_drugs_by_region("EU")

# Analytics
top_diseases = controller.get_diseases_with_most_drugs(10)
stats = controller.get_statistics()
```

## Data Models

### Pydantic Models (`data/models/disease.py`)

```python
class DrugInfo(BaseModel):
    name: str
    status: Optional[str] = None
    manufacturer: Optional[str] = None
    indication: Optional[str] = None
    regions: List[str] = []
    substance_id: Optional[str] = None
    regulatory_id: Optional[str] = None
    links: List[Dict] = []
    details: List[str] = []

class DrugResult(BaseModel):
    disease_name: str
    orpha_code: str
    drugs: List[DrugInfo]
    processing_timestamp: datetime
    run_number: int
    total_drugs_found: int
    search_url: Optional[str] = None
    search_params: Dict = {}
```

## Data Parsing and Extraction

### DrugParser Class (`utils/orpha_drug/orpha_drug.py`)

**Purpose**: Parse HTML content from Orpha.net drug pages

**Key Methods**:
- `parse_search_results()`: Parse complete search results page
- `parse_drugs()`: Extract drug information from containers
- `parse_disease_info()`: Extract disease context information
- `parse_result_count()`: Parse total number of results

**Extracted Data Points**:
- Drug name and substance information
- Regulatory status and approval information
- Manufacturer and company details
- Geographic availability (regions)
- Links to detailed information
- Indication and usage information

### Data Extraction Strategy

**Multi-Strategy Parsing**:
- Multiple HTML parsing strategies for robustness
- Fallback mechanisms for different page structures
- Substance URL and ID extraction
- Regulatory information parsing
- Geographic region identification

**Quality Assurance**:
- Validation of extracted data
- Duplicate detection and removal
- Consistency checks across data points
- Error logging for manual review

## Processing Results

### Success Metrics
- **Total Diseases**: 665
- **Processing Success Rate**: 100% (0 failures)
- **Diseases with Drugs**: 407 (61.2%)
- **Total Unique Drugs**: 885
- **Empty Diseases**: 258 (38.8%)

### Drug Characteristics
- **Approved Drugs**: 466 (52.7%)
- **Investigational Drugs**: 0 (categorization varies)
- **Geographic Coverage**: 100% US, 12.2% EU
- **Average Drugs per Disease**: 2.17 (for diseases with drugs)

### Top Diseases by Drug Count
1. **Paroxysmal nocturnal hemoglobinuria**: 50 drugs
2. **Gaucher disease**: 45 drugs
3. **Fabry disease**: 39 drugs
4. **Mucopolysaccharidosis type 3**: 38 drugs
5. **X-linked adrenoleukodystrophy**: 32 drugs

## Statistical Analysis (`apps/research_prioritization/stats/drug_stats.py`)

### Generated Analysis
- **Basic Statistics**: Drug coverage, disease distribution, success rates
- **Disease Analysis**: Drug distribution, top diseases, concentration metrics
- **Drug Characteristics**: Status, manufacturers, regulatory information
- **Geographic Analysis**: Regional availability, market distribution
- **Regulatory Analysis**: Approval status, regulatory pathways
- **Cross-referencing**: Disease-drug relationship analysis

### Visualization Output
- `basic_overview.png`: Key metrics and overview charts
- `disease_distribution.png`: Drug distribution analysis
- `drug_characteristics.png`: Drug status, manufacturers, regulatory info
- `regulatory_status.png`: Approval status and regulatory analysis
- `top_diseases.png`: Top diseases by drug availability
- `regional_distribution.png`: Geographic drug availability
- `dashboard.png`: Comprehensive dashboard view

### Key Insights
- **Drug Availability**: 61.2% of rare diseases have available drugs
- **Regulatory Status**: 52.7% of drugs are approved
- **Geographic Disparities**: Significant US-EU availability differences
- **Disease Coverage**: Strong correlation between disease research and drug availability

## Usage Examples

### Basic Processing
```bash
# 1. Process drug data (reuses existing diseases)
python etl/process_drug_data.py

# 2. Aggregate results
python etl/aggregate_drug_data.py

# 3. Generate statistics
python apps/research_prioritization/stats/drug_stats.py
```

### Query Interface Usage
```python
from etl.drug_controller import DrugController

# Initialize controller
controller = DrugController()

# Basic disease lookup
drugs = controller.get_drugs_for_disease("646")  # Niemann-Pick disease
print(f"Found {len(drugs)} drugs for Niemann-Pick disease")

# Find diseases with most drugs
top_diseases = controller.get_diseases_with_most_drugs(10)
for disease in top_diseases:
    print(f"{disease['disease_name']}: {disease['drug_count']} drugs")

# Status filtering
approved_drugs = controller.search_drugs_by_status("approved")
print(f"Found {len(approved_drugs)} approved drugs")

# Regional filtering
eu_drugs = controller.search_drugs_by_region("EU")
print(f"Found {len(eu_drugs)} drugs available in EU")
```

### Research Applications
```python
# Drug availability analysis
all_diseases = controller.get_all_diseases()
diseases_with_drugs = controller.get_diseases_with_drugs()
gap_diseases = [d for d in all_diseases if d not in diseases_with_drugs]
print(f"Drug gaps: {len(gap_diseases)} diseases without drugs")

# Manufacturer analysis
drugs_by_manufacturer = controller.get_drugs_by_manufacturer()
for manufacturer, drugs in drugs_by_manufacturer.items():
    print(f"{manufacturer}: {len(drugs)} drugs")

# Cross-system analysis (with clinical trials)
from etl.clinical_trials_cont import ClinicalTrialsController
trials_controller = ClinicalTrialsController()

# Find diseases with drugs but no trials
diseases_with_drugs = set(controller.get_diseases_with_drugs())
diseases_with_trials = set(trials_controller.get_diseases_with_trials())
drug_no_trial = diseases_with_drugs - diseases_with_trials
print(f"Diseases with drugs but no trials: {len(drug_no_trial)}")
```

## Performance Optimization

### Caching Strategy
- **LRU Cache**: Frequently accessed queries cached
- **Lazy Loading**: Data loaded only when needed
- **Memory Management**: Minimal memory footprint until access

### Rate Limiting
- **0.5 Second Delays**: Respectful scraping practices
- **Session Management**: Persistent connections
- **Error Handling**: Graceful degradation on scraping issues

### Scalability Considerations
- **Current Capacity**: 665 diseases processed successfully
- **Extension Ready**: Easy to add new data fields
- **Performance**: Optimized for large-scale processing

## Data Quality Assurance

### Validation Mechanisms
- **Schema Validation**: Pydantic models ensure data integrity
- **Completeness Checking**: Empty run detection and reprocessing
- **Cross-validation**: Consistency checks across data sources

### Error Handling
- **Graceful Degradation**: Continue processing despite individual failures
- **Detailed Logging**: Comprehensive audit trails
- **Manual Review**: Failed case identification and resolution

### Reproducibility
- **Deterministic Processing**: Consistent results across runs
- **Version Control**: All code and configurations tracked
- **Audit Trails**: Complete processing history maintained

## Integration with Clinical Trials System

### Shared Components
- **Disease Dataset**: Identical 665 diseases
- **Run Management**: Same per-disease run numbering
- **Directory Structure**: Parallel preprocessing/processed directories
- **Data Models**: Consistent Pydantic model patterns

### Cross-System Analysis
- **Disease Coverage Comparison**: Drugs vs. trials availability
- **Gap Analysis**: Diseases with drugs but no trials (and vice versa)
- **Priority Setting**: Combined drug availability and trial activity
- **Research Opportunities**: Diseases with neither drugs nor trials

### Unified Query Interface
```python
# Combined analysis example
from etl.drug_controller import DrugController
from etl.clinical_trials_cont import ClinicalTrialsController

drug_controller = DrugController()
trial_controller = ClinicalTrialsController()

# Find diseases with both drugs and trials
diseases_with_drugs = set(drug_controller.get_diseases_with_drugs())
diseases_with_trials = set(trial_controller.get_diseases_with_trials())
both_systems = diseases_with_drugs & diseases_with_trials
print(f"Diseases with both drugs and trials: {len(both_systems)}")
```

## Maintenance and Operations

### Regular Operations
- **Data Refresh**: Periodic reprocessing for updated drug information
- **Quality Monitoring**: Regular validation of data integrity
- **Performance Monitoring**: System health assessments

### Troubleshooting
- **Log Analysis**: Comprehensive logging for issue diagnosis
- **Failed Run Recovery**: Automatic retry mechanism
- **Data Validation**: Built-in consistency checks

### System Updates
- **Website Changes**: Adaptation to Orpha.net HTML structure updates
- **Feature Additions**: Extension for new data fields
- **Performance Improvements**: Ongoing optimization

## Future Enhancements

### Planned Improvements
- **Real-time Updates**: Automated data refresh mechanisms
- **Advanced Filtering**: More sophisticated query capabilities
- **Integration APIs**: RESTful interfaces for external systems
- **Machine Learning**: Drug-disease relationship prediction

### Expansion Opportunities
- **Additional Data Sources**: Integration with other drug databases
- **Temporal Analysis**: Historical drug approval trends
- **Comparative Studies**: Cross-disease drug development analysis
- **Regulatory Tracking**: Detailed regulatory pathway analysis

## Technical Implementation Details

### HTML Parsing Strategy
- **Multi-Strategy Approach**: Multiple parsing methods for robustness
- **Container Detection**: Flexible drug container identification
- **Data Extraction**: Comprehensive drug information extraction
- **Link Processing**: Substance and regulatory link extraction

### Data Transformation
- **Normalization**: Consistent data formatting
- **Validation**: Data quality checks and validation
- **Enrichment**: Additional metadata extraction
- **Consistency**: Cross-reference validation

### Error Recovery
- **Parsing Failures**: Graceful handling of parsing errors
- **Network Issues**: Retry mechanisms for network failures
- **Data Validation**: Comprehensive validation with error reporting
- **Manual Review**: Flagging of problematic cases

---

*This documentation reflects the current production implementation of the Drug Data System. The system is actively used for research prioritization and provides comprehensive drug information for rare disease research planning.* 