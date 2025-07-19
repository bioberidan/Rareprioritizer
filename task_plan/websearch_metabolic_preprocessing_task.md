# Task Plan: WebSearch Metabolic Disease Preprocessing

**Date**: December 2024  
**Priority**: High  
**Estimated Time**: 6-7 hours  
**Type**: WebSearch Data Processing + Retry System + Run Management + General Utilities

---

## 📋 **Task Overview**

### **Purpose**
Create a websearch preprocessing script for metabolic diseases that leverages WebSearcher agents to gather comprehensive research data for each disease, following the established ETL patterns.

### **Key Features**
- **Input**: Curated metabolic disease sample from `data/04_curated/metabolic/`, specified in the yaml file
- **Processing**: WebSearcher agents for multiple research dimensions
- **Output**: Structured websearch results per disease in `data/02_preprocess/websearch/`
- **Configuration**: YAML-driven with flexible prompt selection
- **Management**: Integration with run management utilities
- **Aggregation**: Compatible with existing aggregation patterns

---

## 🔍 **Data Flow Analysis**

### **Input Data**
```
📁 data/04_curated/metabolic/
├── metabolic_disease_instances_sample_10.json
└── metabolic_disease_instances.json
```

**Sample Input Structure**:
```json
[
  {
    "disease_name": "Acrodermatitis enteropathica",
    "orpha_code": "37"
  },
  {
    "disease_name": "Niemann-Pick disease type C", 
    "orpha_code": "646"
  }
  // ... 8 more diseases
]
```

### **Output Data**
```
📁 data/02_preprocess/websearch/
├── 37/                                    # Acrodermatitis enteropathica
│   ├── run1_disease2websearch.json
│   ├── run2_disease2websearch.json       # If reprocessed
│   └── ...
├── 646/                                   # Niemann-Pick disease type C
│   ├── run1_disease2websearch.json
│   └── ...
└── [orphacode]/
    └── run[N]_disease2websearch.json
```

### **Configuration**
```
📁 etl/02_preprocess/websearch/
├── preprocess_metabolic.py           # Main script
├── conf/
│   └── config_metabolic.yaml         # Main configuration
└── prompts/                          # Available prompts
    ├── groups/
    ├── socioeconomic/
    └── ...
```

---

## 🔧 **Configuration Structure**

### **YAML Configuration (`etl/02_preprocess/websearch/conf/config_metabolic.yaml`)**
```yaml
websearch:
  metabolic:
    # Input configuration
    input:
      data_source: "data/04_curated/metabolic/metabolic_disease_instances_sample_10.json"
      use_sample: true
    
    # Processing configuration
    processing:
      # Analysis type selection (only one runs at a time)
      analysis_type: "socioeconomic"  # Options: "groups", "socioeconomic", "clinical"
      
      # Prompt configuration per analysis type
      prompts:
        groups: "groups_v2"
        socioeconomic: "socioeconomic_v2"
        clinical: "clinical_v1"  # Future
      
      # WebSearcher client configuration
      client:
        reasoning:
          effort: "medium"
        max_output_tokens: 8000
        timeout: 120
    
    # Retry configuration
    retry:
      max_attempts: 5
      initial_wait: 1
      max_wait: 60
      retry_on_empty: true
      retry_on_api_failure: true
    
    # Output configuration
    output:
      base_path: "data/02_preprocess/websearch"
      run_management: true
      skip_processed: true
      reprocess_empty: true
    
    # Logging and monitoring
    logging:
      level: "INFO"
      log_progress: true
      log_errors: true
```

---

## 🔄 **Run Management Logic**

### **Run Number Assignment**
- **Check Existing Runs**: For each disease, scan `data/02_preprocess/websearch/[orphacode]/` for existing runs
- **Skip Logic**: If disease has any run (run1, run2, run3, etc.) → skip processing unless `--force-reprocess` flag is specified
- **Increment Logic**: If processing, assign next run number (e.g., if run1 and run2 exist, create run3)
- **File Naming**: `run[N]_disease2websearch.json` where N is the next available run number

### **Examples**
```bash
# Disease 37 has no runs → create run1_disease2websearch.json
# Disease 646 has run1 → skip (unless --force-reprocess)
# Disease 37 with --force-reprocess and existing run1, run2 → create run3_disease2websearch.json
```

### **Override Behavior**
- **Default**: Skip diseases with any existing runs
- **With --force-reprocess**: Process anyway, increment run number
- **Run-specific**: Use `--run N` to force specific run number (overwrites if exists)

---

## 🔁 **Retry and Error Handling**

### **Retry Utility Function**
**Location**: `rareprioritizer/core/infrastructure/utils/retry.py`
```python
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

def retry_it(func, attempts=3):
    """General retry decorator with exponential backoff and jitter."""
    return retry(
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=1, max=60)
    )(func)()
```

### **Empty Search Detection**
**Enhancement to Prompt Classes**:
```python
# In each prompt model class (GroupsResponse, SocioeconomicImpactResponse)
class GroupsResponse(BaseModel):
    # ... existing fields ...
    
    def is_empty_search(self) -> bool:
        """Check if response represents an empty search result."""
        return len(self.groups) == 0
    
class SocioeconomicImpactResponse(BaseModel):
    # ... existing fields ...
    
    def is_empty_search(self) -> bool:
        """Check if response represents an empty search result."""
        return (self.score == 0 and 
                len(self.socioeconomic_impact_studies) == 0)
```

### **Retry Conditions**
1. **API Failures**: Network errors, rate limits, timeout errors
2. **Empty Searches**: When `response.is_empty_search()` returns `True`
3. **Parsing Errors**: JSON parsing or validation failures
4. **Configurable**: Max attempts, wait times, retry conditions via YAML

### **Retry Integration**
```python
def run_groups_analysis_with_retry(disease: dict, config: dict) -> dict:
    """Run groups analysis with retry logic."""
    
    @retry_it(attempts=config['retry']['max_attempts'])
    def _search_with_retry():
        result = run_groups_analysis(disease, config)
        if config['retry']['retry_on_empty'] and result.is_empty_search():
            raise EmptySearchError("Empty search result, retrying...")
        return result
    
    return _search_with_retry()
```

---

## 🏗️ **Script Architecture**

### **File Structure**
```
📁 etl/02_preprocess/websearch/
├── preprocess_metabolic.py               # Main script
├── conf/
│   └── config_metabolic.yaml             # Main configuration
├── prompts/                              # Existing prompt system
│   ├── groups/
│   ├── socioeconomic/
│   └── prompt_registry.py
└── utils/
    ├── yaml_config.py               # YAML validation functions try to be as general and reusable as possible
    └── io.py                        # Data I/O, try to be as universal and generalizable as possible
```

### **Core Functions**

#### **1. Main Processing Functions**
```python
def load_config(config_path: str = "etl/02_preprocess/websearch/conf/config_metabolic.yaml") -> dict:
    """Load and validate YAML configuration using general yaml_config utility."""

def load_diseases(input_file: str) -> List[dict]:
    """Load diseases from curated metabolic data using general io utility."""

def check_existing_runs(orphacode: str, base_path: str) -> List[int]:
    """Check existing run numbers for a disease."""

def get_next_run_number(orphacode: str, base_path: str) -> int:
    """Get next available run number for a disease."""

def should_skip_disease(orphacode: str, base_path: str, force_reprocess: bool) -> bool:
    """Determine if disease should be skipped based on existing runs."""

def process_diseases(diseases: List[dict], config: dict, force_reprocess: bool = False) -> dict:
    """Process all diseases through websearch analysis with run management."""

def process_single_disease(disease: dict, analysis_type: str, config: dict, run_number: int) -> dict:
    """Process single disease with specified analysis type and retry logic."""
```

#### **2. Analysis Functions with Retry**
```python
def run_groups_analysis(disease: dict, config: dict) -> GroupsResponse:
    """Run CIBERER research groups analysis for a disease."""

def run_socioeconomic_analysis(disease: dict, config: dict) -> SocioeconomicImpactResponse:
    """Run socioeconomic impact analysis for a disease."""

def run_clinical_analysis(disease: dict, config: dict) -> ClinicalResponse:
    """Run clinical research analysis for a disease (future)."""

def run_analysis_with_retry(analysis_func: callable, disease: dict, config: dict) -> dict:
    """Wrapper to run any analysis with retry logic."""

def select_analysis(analysis_type: str, disease: dict, config: dict) -> dict:
    """Select and run the appropriate analysis based on type with retry."""
```

#### **3. Utility Functions**
```python
def create_empty_search_error(analysis_type: str, disease_name: str) -> Exception:
    """Create custom exception for empty search results."""

def validate_analysis_result(result: dict, analysis_type: str) -> bool:
    """Validate analysis result and check for empty responses."""

def log_retry_attempt(disease_name: str, analysis_type: str, attempt: int, error: str):
    """Log retry attempts for monitoring."""
```

#### **3. Result Functions**
```python
def create_websearch_result(disease: dict, analysis_type: str, analysis_result: dict, 
                           processing_time: float, run_number: int, error: str = None) -> dict:
    """Create websearch result dictionary for a single disease."""
    result = {
        "disease_name": disease["disease_name"],
        "orpha_code": disease["orpha_code"],
        "processing_timestamp": datetime.now().isoformat(),
        "run_number": run_number,
        "analysis_type": analysis_type,
        "processing_duration": processing_time,
        "success": error is None,
        "error_details": error
    }
    
    # Add analysis-specific results
    if analysis_type == "groups":
        result["groups_analysis"] = analysis_result
    elif analysis_type == "socioeconomic":
        result["socioeconomic_analysis"] = analysis_result
    elif analysis_type == "clinical":
        result["clinical_analysis"] = analysis_result
    
    return result

def validate_result(result: dict) -> bool:
    """Validate websearch result structure."""
```

---

## 📊 **Output Examples**

### **Single Disease Result - Socioeconomic Analysis (`run1_disease2websearch.json`)**
```json
{
  "disease_name": "Acrodermatitis enteropathica",
  "orpha_code": "37",
  "processing_timestamp": "2024-12-14T10:30:00Z",
  "run_number": 1,
  "analysis_type": "socioeconomic",
  "processing_duration": 23.45,
  "success": true,
  "error_details": null,
  
  "socioeconomic_analysis": {
    "orphacode": "37",
    "disease_name": "Acrodermatitis enteropathica", 
    "socioeconomic_impact_studies": [
      {
        "cost": 15000,
        "measure": "Annual treatment cost including zinc supplementation",
        "label": "Economic burden of zinc deficiency disorders in Europe",
        "source": "https://eurordis.org/...",
        "country": "Spain",
        "year": "2022"
      }
    ],
    "score": 5,
    "evidence_level": "Medium evidence",
    "justification": "Quantitative data from European patient organization report specific to Spain."
  }
}
```

### **Single Disease Result - Groups Analysis (`run2_disease2websearch.json`)**
```json
{
  "disease_name": "Acrodermatitis enteropathica",
  "orpha_code": "37",
  "processing_timestamp": "2024-12-14T11:15:00Z",
  "run_number": 2,
  "analysis_type": "groups",
  "processing_duration": 32.18,
  "success": true,
  "error_details": null,
  
  "groups_analysis": {
    "orphacode": "37",
    "disease_name": "Acrodermatitis enteropathica",
    "groups": [
      {
        "unit_id": "U758",
        "official_name": "Rare Diseases Research Unit",
        "host_institution": "Hospital Universitario La Paz",
        "city": "Madrid",
        "principal_investigators": [
          {"name": "Dr. María González", "role": "Principal Investigator"}
        ],
        "justification": "Published research on zinc deficiency disorders including acrodermatitis enteropathica",
        "sources": [
          {"label": "CIBERER Annual Report 2023", "url": "https://ciberer.es/..."}
        ],
        "disease_related_publications": [
          {
            "pmid": "34567890",
            "title": "Zinc transporter mutations in acrodermatitis enteropathica",
            "year": 2023,
            "journal": "J Med Genet",
            "url": "https://pubmed.ncbi.nlm.nih.gov/34567890"
          }
        ]
      }
    ]
  }
}
```

### **Aggregated Results Structure (Future)**
```
📁 data/03_processed/websearch/
├── metabolic_groups_aggregated.json      # All diseases groups analysis combined
├── metabolic_socioeconomic_aggregated.json # All diseases socioeconomic analysis combined
├── metabolic_clinical_aggregated.json    # All diseases clinical analysis combined (future)
└── processing_statistics.json           # Run statistics per analysis type
```

---

## 🚀 **Implementation Plan**

### **Phase 1: Core Infrastructure & Utilities (2 hours)**

#### **Step 1.1: Retry Utility System**
- [ ] Create `rareprioritizer/core/infrastructure/utils/retry.py` with `retry_it()` function
- [ ] Add custom exception classes (`EmptySearchError`, `AnalysisError`)
- [ ] Test retry functionality with different failure scenarios

#### **Step 1.2: General Utilities**
- [ ] Create `etl/02_preprocess/websearch/utils/yaml_config.py` for general YAML handling
- [ ] Create `etl/02_preprocess/websearch/utils/io.py` for general data I/O operations
- [ ] Make utilities reusable across different preprocessing scripts

#### **Step 1.3: Configuration System**
- [ ] Create `etl/02_preprocess/websearch/conf/config_metabolic.yaml` with retry configuration
- [ ] Add analysis type selection and retry parameters
- [ ] Test configuration loading and validation

#### **Step 1.4: Prompt Enhancement**
- [ ] Add `is_empty_search()` method to `GroupsResponse` class
- [ ] Add `is_empty_search()` method to `SocioeconomicImpactResponse` class
- [ ] Add `is_empty_search()` method to future `ClinicalResponse` class
- [ ] Test empty response detection logic

### **Phase 2: Run Management System (1 hour)**

#### **Step 2.1: Run Detection & Management**
- [ ] Implement `check_existing_runs()` function to scan for existing run files
- [ ] Implement `get_next_run_number()` function for run increment logic
- [ ] Implement `should_skip_disease()` function with override logic
- [ ] Test run number assignment and skip logic

#### **Step 2.2: File System Integration**
- [ ] Integrate with existing run management utilities pattern
- [ ] Implement file naming convention `run[N]_disease2websearch.json`
- [ ] Add force reprocess and run-specific override functionality
- [ ] Test with various run scenarios

### **Phase 3: Analysis Integration with Retry (1.5 hours)**

#### **Step 3.1: Core Analysis Functions**
- [ ] Create `run_groups_analysis()` with WebSearcher integration
- [ ] Create `run_socioeconomic_analysis()` with WebSearcher integration
- [ ] Create `run_clinical_analysis()` stub for future implementation
- [ ] Test individual analysis functions

#### **Step 3.2: Retry Wrapper System**
- [ ] Implement `run_analysis_with_retry()` wrapper function
- [ ] Add retry logic for API failures and empty searches
- [ ] Implement configurable retry parameters (attempts, wait times)
- [ ] Add retry attempt logging and monitoring

#### **Step 3.3: Analysis Selection**
- [ ] Implement `select_analysis()` with conditional logic (if socioeconomic, if groups, if clinical)
- [ ] Add error handling for invalid analysis types
- [ ] Test analysis selection and retry integration

### **Phase 4: Main Processing Logic (1 hour)**

#### **Step 4.1: Disease Processing**
- [ ] Implement `process_single_disease()` with run management and retry
- [ ] Implement `process_diseases()` with batch processing and skip logic
- [ ] Add progress tracking and status reporting
- [ ] Test single and batch disease processing

#### **Step 4.2: Result Management**
- [ ] Implement `create_websearch_result()` with enhanced metadata
- [ ] Add validation and error details in results
- [ ] Implement result saving with run management
- [ ] Test result creation and persistence

### **Phase 5: CLI and Integration (45 minutes)**

#### **Step 5.1: Command Line Interface**
- [ ] Create `preprocess_metabolic.py` with enhanced argument parsing
- [ ] Add `--analysis`, `--force-reprocess`, `--run` arguments
- [ ] Implement dry-run mode and verbose logging
- [ ] Test CLI with various parameter combinations

#### **Step 5.2: Testing & Validation**
- [ ] Test complete workflow with 10 sample diseases
- [ ] Validate retry behavior on simulated failures
- [ ] Test run management with existing files
- [ ] Validate output format and structure

---

## 🔧 **CLI Interface**

### **Command Structure**
```bash
# Basic usage with default configuration (socioeconomic analysis)
python etl/02_preprocess/websearch/preprocess_metabolic.py

# Run groups analysis
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis groups

# Run socioeconomic analysis explicitly
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis socioeconomic

# Run clinical analysis (future)
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis clinical

# Custom configuration file
python etl/02_preprocess/websearch/preprocess_metabolic.py --config custom_config.yaml --analysis groups

# Specific data source
python etl/02_preprocess/websearch/preprocess_metabolic.py --input data/04_curated/metabolic/metabolic_disease_instances.json --analysis socioeconomic

# Force reprocessing
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis groups --force-reprocess

# Specific run number
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis socioeconomic --run 2

# Dry run mode
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis groups --dry-run
```

### **Arguments**
- `--analysis`: Analysis type to run ("groups", "socioeconomic", "clinical") - **REQUIRED**
- `--config`: Path to YAML configuration file
- `--input`: Path to input JSON file (overrides config)
- `--output`: Base output directory (overrides config)
- `--run`: Specific run number to use (overwrites if exists)
- `--force-reprocess`: Reprocess even if results exist (increments run number)
- `--dry-run`: Show what would be processed without execution
- `--verbose`: Enable verbose logging
- `--max-retries`: Override retry attempts from config

### **Run Management Examples**
```bash
# Disease 37 has no runs → will create run1_disease2websearch.json
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis socioeconomic --verbose

# Disease 37 already has run1 → will skip (show skip message)
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis socioeconomic

# Disease 37 has run1, force reprocess → will create run2_disease2websearch.json  
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis socioeconomic --force-reprocess

# Force specific run number → will overwrite run1_disease2websearch.json if exists
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis groups --run 1

# Dry run to see what would be processed
python etl/02_preprocess/websearch/preprocess_metabolic.py --analysis groups --dry-run --verbose
```

### **Error and Retry Scenarios**
```bash
# Example: Disease fails with empty search, will retry up to 5 times
INFO: Processing Acrodermatitis enteropathica (run 1)...
WARNING: Empty search result for groups analysis, retrying... (attempt 1/5)
WARNING: Empty search result for groups analysis, retrying... (attempt 2/5)
INFO: Groups analysis successful on attempt 3
INFO: Result saved to data/02_preprocess/websearch/37/run1_disease2websearch.json

# Example: API failure with exponential backoff
INFO: Processing Niemann-Pick disease type C (run 1)...
ERROR: API failure (rate limit), retrying in 2.3 seconds... (attempt 1/5)
ERROR: API failure (timeout), retrying in 4.7 seconds... (attempt 2/5)
INFO: Socioeconomic analysis successful on attempt 3

# Example: Max retries exceeded, disease marked as failed
ERROR: Max retries exceeded for CK syndrome socioeconomic analysis
ERROR: Disease 251383 failed after 5 attempts: EmptySearchError
```

---

## 📈 **Success Metrics**

### **Processing Metrics**
- [ ] All 10 sample diseases processed successfully for each analysis type
- [ ] Run management correctly skips diseases with existing runs (unless force override)
- [ ] Run numbering correctly increments (run1, run2, run3, etc.)
- [ ] Configuration system works with analysis type selection and retry parameters
- [ ] Force reprocess flag properly overrides skip logic

### **Data Quality Metrics**
- [ ] Groups analysis returns valid CIBERER research units when selected
- [ ] Socioeconomic analysis provides impact scores and evidence when selected
- [ ] Empty search detection correctly identifies and retries empty responses
- [ ] All output JSON validates against expected schemas
- [ ] Retry logic successfully recovers from API failures and empty searches

### **Performance & Reliability Metrics**
- [ ] Single analysis processing completes within reasonable time (< 5 minutes for 10 diseases)
- [ ] Retry mechanism handles failures gracefully with exponential backoff
- [ ] Analysis selection logic works correctly (if socioeconomic, if groups, if clinical)
- [ ] Run management prevents unnecessary reprocessing per analysis type
- [ ] Memory usage remains stable during processing with retry attempts
- [ ] Configurable retry parameters work as expected (attempts, wait times)

### **Utility & Reusability Metrics**
- [ ] General utilities (yaml_config.py, io.py) are reusable across other scripts
- [ ] Retry utility (retry_it) works with different function types
- [ ] Empty search detection works consistently across all analysis types
- [ ] Configuration structure supports easy extension for new analysis types

---

## 🔄 **Integration with Existing System**

### **Data Flow Integration**
```
📊 Curated Metabolic Data
    ↓
🔍 WebSearch Preprocessing (NEW)
    ↓  
📁 Preprocessed WebSearch Results
    ↓
🔄 Aggregation Processing (FUTURE)
    ↓
📊 Final Analysis & Statistics
```

### **Compatibility Requirements**
- [ ] Output format compatible with existing aggregation scripts
- [ ] Run management follows established patterns
- [ ] Configuration integrates with existing YAML structure
- [ ] Error handling aligns with current logging practices

### **Future Extensibility**
- [ ] Easy addition of new analysis types (clinical, biomarker)
- [ ] Configurable prompt selection per analysis
- [ ] Support for different input data formats
- [ ] Integration with web UI for monitoring

---

## 🎯 **Deliverables**

### **Code Deliverables**
1. `etl/02_preprocess/websearch/preprocess_metabolic.py` - Main script with retry and run management
2. `etl/02_preprocess/websearch/conf/config_metabolic.yaml` - Configuration with retry parameters
3. `etl/02_preprocess/websearch/utils/yaml_config.py` - General YAML configuration utility
4. `etl/02_preprocess/websearch/utils/io.py` - General data I/O utility
5. `rareprioritizer/core/infrastructure/utils/retry.py` - General retry utility
6. Enhanced prompt classes with `is_empty_search()` methods
7. Updated documentation and examples

### **Data Deliverables**
1. Processed websearch results for 10 sample metabolic diseases
2. Example output files demonstrating structure
3. Processing statistics and logs

### **Documentation Deliverables**
1. Updated task plan with implementation details
2. Configuration documentation
3. Integration examples and usage patterns
4. Error handling and troubleshooting guide

---

## ⚠️ **Risks and Mitigations**

### **Technical Risks**
- **API Rate Limits**: Implement proper delays and retry mechanisms
- **Large Response Sizes**: Configure appropriate token limits per analysis
- **Network Failures**: Add comprehensive error handling and recovery
- **Memory Usage**: Implement batch processing and memory monitoring

### **Data Risks**
- **Inconsistent Responses**: Validate all API responses against schemas
- **Missing Disease Names**: Handle diseases without clear research presence
- **Prompt Failures**: Graceful degradation when specific prompts fail
- **Storage Limitations**: Monitor disk usage and implement cleanup strategies

### **Integration Risks**
- **Configuration Conflicts**: Thorough testing with existing config structure
- **Run Management Issues**: Validate integration with existing utilities
- **Output Format Changes**: Ensure backward compatibility with aggregation
- **Dependencies**: Pin versions of WebSearcher and prompt system

---

## 📝 **Next Steps After Implementation**

### **Immediate Follow-up**
1. **Aggregation Script**: Create aggregation processor for websearch results
2. **Statistics Module**: Generate analysis and reports across diseases  
3. **Monitoring Dashboard**: Track processing progress and quality metrics
4. **Documentation**: Complete user guides and API documentation

### **Future Enhancements**
1. **Additional Analyses**: Clinical research, biomarker studies, drug development
2. **Real-time Processing**: Stream processing for new disease additions
3. **Quality Metrics**: Automated validation of websearch result quality
4. **UI Integration**: Web interface for monitoring and management

### **Long-term Vision**
1. **Multi-source Integration**: Combine websearch with database sources
2. **Predictive Analytics**: Use historical data to predict research gaps
3. **Automated Prioritization**: Score diseases based on multiple factors
4. **Collaborative Platform**: Enable researcher input and validation 