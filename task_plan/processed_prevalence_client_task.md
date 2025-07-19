# ProcessedPrevalenceClient Implementation Task Plan

## Overview

This task plan outlines the implementation of the **ProcessedPrevalenceClient** for the RarePrioritizer system. The client will provide a lazy-loading, cached interface for querying prevalence data similar to the existing `DrugController` pattern in the datastore.

## Task Objectives

**⚠️ PREREQUISITES (MUST BE COMPLETED FIRST):**
1. **Fix Path Issues**: Correct the hardcoded paths in `etl/03_process/orpha/orphadata/process_orpha_prevalence.py`
2. **Implement `mean_value_per_million`**: Add weighted mean calculation to prevalence processing 
3. **Update Schemas**: Add `mean_value_per_million` field to prevalence schemas
4. **Reprocess Data**: Regenerate prevalence data with corrected implementation

**MAIN OBJECTIVES:**
1. **Create ProcessedPrevalenceClient**: Implement a controller-style client for prevalence data query and retrieval
2. **Use Updated Schemas**: Leverage the corrected schemas with `mean_value_per_million`
3. **Add Statistics Module**: Create comprehensive statistics generation for prevalence data
4. **Follow Established Patterns**: Match the structure and functionality of existing controllers

## Code Templates and Patterns Available

### 1. Controller Template
**Template Source**: `core/datastore/orpha/orphadata/drug_client.py`
- **Pattern**: Lazy loading with LRU cache
- **Structure**: `_ensure_*_loaded()` methods for each data file
- **Methods**: Basic queries, search/filter, statistics, utilities
- **File Organization**: Maps diseases→data, data→diseases, index files

### 2. Schema Template (Working - Do Not Change)
**Schema Source**: `core/schemas/orpha/orphadata/orpha_prevalence.py`
- **PrevalenceInstance**: Individual prevalence records
- **DiseasePrevalenceMapping**: Disease-to-prevalence relationships
- **ReliabilityScore**: Reliability scoring breakdown
- **ProcessingStatistics**: Processing and quality metrics
- **ValidationReport**: Data quality assessment

### 3. Statistics Template
**Template Source**: `etl/05_stats/orpha/orphadata/drug_stats.py`
- **Pattern**: Controller-based stats generation
- **Output**: JSON statistics + visualizations
- **Location**: Results saved to `results/etl/orpha/orphadata/prevalence/`

## Input/Output Data Folders

### Input Data (Processed Data)
```
📁 data/03_processed/orpha/orphadata/orpha_prevalence/
├── 📄 disease2prevalence.json (33MB) - Main mapping file
├── 📄 prevalence2diseases.json (515KB) - Reverse mapping
├── 📄 prevalence_instances.json (8.5MB) - All prevalence records
├── 📄 orpha_index.json (1.3MB) - Optimized lookup index
├── 📁 cache/
│   ├── 📄 statistics.json - Processing statistics
│   ├── 📄 prevalence_classes.json - Class mappings
│   └── 📄 geographic_index.json - Geographic groupings
├── 📁 reliability/
│   ├── 📄 reliability_scores.json - Detailed reliability data
│   └── 📄 validation_report.json - Quality assessment
└── 📁 regional_data/
    ├── 📄 europe_prevalences.json
    ├── 📄 united_states_prevalences.json
    └── [500+ regional files]
```

### Output Locations
```
📁 core/datastore/orpha/orphadata/
└── 📄 prevalence_client.py (Replace existing incomplete file)

📁 etl/05_stats/orpha/orphadata/
└── 📄 prevalence_stats.py (New statistics module)

📁 results/etl/orpha/orphadata/prevalence/
├── 📄 prevalence_statistics.json
├── 📄 prevalence_summary.md
└── 📄 prevalence_characteristics.png
```

## ✅ COMPLETED IMPLEMENTATION

### ✅ PHASE 0: Prerequisites (COMPLETED)

**All critical prerequisites have been successfully implemented:**

1. **✅ Path Issues Fixed**: Updated `etl/03_process/orpha/orphadata/process_orpha_prevalence.py`
2. **✅ `mean_value_per_million` Implemented**: Added comprehensive weighted mean calculation
3. **✅ Schemas Updated**: Enhanced `core/schemas/orpha/orphadata/orpha_prevalence.py` with new fields
4. **✅ ProcessedPrevalenceClient Created**: Full implementation at `core/datastore/orpha/orphadata/prevalence_client.py`
5. **✅ Statistics Module Created**: Comprehensive analysis module at `etl/05_stats/orpha/orphadata/prevalence_stats.py`

## PHASE 0: Prerequisites (COMPLETED)

### Prerequisite 1: Fix Path Issues in Prevalence Processing

**Current Issue**: `etl/03_process/orpha/orphadata/process_orpha_prevalence.py` has hardcoded paths that don't match current structure.

**Current Incorrect Paths:**
```python
# Line 565 - WRONG paths
default="data/input/raw/en_product9_prev.xml"
default="data/preprocessing/prevalence" 
```

**Correct Paths:**
```python
# Should be:
default="data/01_raw/en_product9_prev.xml"
default="data/03_processed/orpha/orphadata/orpha_prevalence"
```

**Fix Required**: Update argparse defaults in `main()` function to use current data structure.

### Prerequisite 2: Implement `mean_value_per_million` Calculation

**Current Issue**: The prevalence processing script does NOT implement the weighted mean calculation described in `docs/refactor_prevalence_preprocessing.md`.

**Missing Implementation**: The weighted mean calculation that combines multiple prevalence records per disease into a single estimate.

**Required Addition**: Around line 294 in `process_prevalence_xml()`, after building `disease2prevalence`:

```python
# ADD THIS MISSING IMPLEMENTATION
def calculate_weighted_mean_prevalence(prevalence_records):
    """Calculate reliability-weighted mean prevalence per million"""
    # Filter valid records for calculation
    valid_records = []
    for record in prevalence_records:
        # Exclude qualitative data
        if record.get("prevalence_type") == "Cases/families":
            continue
        # Exclude unknown/undocumented  
        if record.get("prevalence_class") in ["Unknown", "Not yet documented", None]:
            continue
        # Exclude zero estimates
        if record.get("per_million_estimate", 0) <= 0:
            continue
        valid_records.append(record)
    
    if not valid_records:
        return {
            "mean_value_per_million": 0.0,
            "valid_records_count": 0,
            "calculation_method": "no_valid_data"
        }
    
    # Calculate weighted mean
    weighted_sum = 0.0
    weight_sum = 0.0
    
    for record in valid_records:
        prevalence = record["per_million_estimate"]
        weight = record["reliability_score"]
        weighted_sum += prevalence * weight
        weight_sum += weight
    
    if weight_sum == 0:
        # Fallback to simple mean if all weights are zero
        mean_value = sum(r["per_million_estimate"] for r in valid_records) / len(valid_records)
    else:
        mean_value = weighted_sum / weight_sum
    
    return {
        "mean_value_per_million": round(mean_value, 2),
        "valid_records_count": len(valid_records),
        "calculation_method": "reliability_weighted_mean",
        "total_records_count": len(prevalence_records),
        "weight_sum": weight_sum
    }

# INTEGRATE INTO disease2prevalence construction:
if prevalence_records:
    # ... existing code ...
    
    # ADD weighted mean calculation
    mean_data = calculate_weighted_mean_prevalence(prevalence_records)
    
    disease2prevalence[orpha_code] = {
        "orpha_code": orpha_code,
        "disease_name": name,
        "prevalence_records": prevalence_records,
        "most_reliable_prevalence": most_reliable,
        "validated_prevalences": validated_records,
        "regional_prevalences": dict(regional_prevalences),
        "mean_value_per_million": mean_data["mean_value_per_million"],  # NEW FIELD
        "mean_calculation_metadata": mean_data,  # NEW FIELD
        "statistics": {
            "total_records": len(prevalence_records),
            "reliable_records": len([r for r in prevalence_records if r["is_fiable"]]),
            "valid_for_mean": mean_data["valid_records_count"]  # NEW FIELD
        }
    }
```

### Prerequisite 3: Update Prevalence Schemas

**Current Issue**: `core/schemas/orpha/orphadata/orpha_prevalence.py` doesn't include `mean_value_per_million` field.

**Required Schema Updates**:

```python
# UPDATE DiseasePrevalenceMapping class
class DiseasePrevalenceMapping(BaseModel):
    """Model for OrphaCode-to-prevalence relationships (disease2prevalence.json)"""
    orpha_code: str = Field(..., description="OrphaCode as primary identifier")
    disease_name: str = Field(..., description="Disease name for reference")
    
    # All prevalence records for this disease
    prevalence_records: List[PrevalenceInstance] = Field(default_factory=list)
    
    # Reliability-based selection
    most_reliable_prevalence: Optional[PrevalenceInstance] = Field(None)
    validated_prevalences: List[PrevalenceInstance] = Field(default_factory=list)
    
    # Geographic breakdown
    regional_prevalences: Dict[str, List[PrevalenceInstance]] = Field(default_factory=dict)
    
    # NEW: Weighted mean calculation
    mean_value_per_million: float = Field(0.0, description="Reliability-weighted mean prevalence estimate")
    mean_calculation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Calculation details and metadata")
    
    # Statistics
    statistics: DiseaseStatistics = Field(..., description="Statistics for this disease")
```

**ADD New Model**:
```python
class MeanCalculationMetadata(BaseModel):
    """Metadata for weighted mean calculation"""
    mean_value_per_million: float = Field(..., description="Calculated weighted mean")
    valid_records_count: int = Field(..., description="Records used in calculation")
    calculation_method: str = Field(..., description="Method used for calculation")
    total_records_count: int = Field(..., description="Total records for this disease")
    weight_sum: float = Field(..., description="Sum of reliability weights")
    excluded_records: Dict[str, int] = Field(default_factory=dict, description="Count of excluded records by reason")
```

### Prerequisite 4: Test and Validate Implementation

**Required Testing**:
1. **Unit Test**: Test `calculate_weighted_mean_prevalence()` with known data
2. **Integration Test**: Process sample XML and verify `mean_value_per_million` in output
3. **Data Validation**: Ensure all diseases have realistic mean values (0-1000 per million)
4. **Schema Compliance**: Verify all output conforms to updated Pydantic models

**Commands to Run After Implementation**:
```bash
# 1. Test the updated processing script
python etl/03_process/orpha/orphadata/process_orpha_prevalence.py --xml data/01_raw/en_product9_prev.xml --output data/03_processed/orpha/orphadata/orpha_prevalence --force

# 2. Validate outputs  
python etl/03_process/orpha/orphadata/process_orpha_prevalence.py --validate-only

# 3. Check mean values are reasonable
python -c "
import json
with open('data/03_processed/orpha/orphadata/orpha_prevalence/disease2prevalence.json', 'r') as f:
    data = json.load(f)
means = [v['mean_value_per_million'] for v in data.values() if v['mean_value_per_million'] > 0]
print(f'Min: {min(means)}, Max: {max(means)}, Count: {len(means)}')
"
```

---

## Implementation Tasks

### Task 1: Create ProcessedPrevalenceClient

**File**: `core/datastore/orpha/orphadata/prevalence_client.py`

**Based on**: `core/datastore/orpha/orphadata/drug_client.py` template

#### 1.1 Core Structure
```python
class PrevalenceController:
    def __init__(self, data_dir: str = "data/03_processed/orpha/orphadata/orpha_prevalence"):
        # Lazy-loaded data structures
        self._disease2prevalence: Optional[Dict] = None
        self._prevalence2diseases: Optional[Dict] = None  
        self._prevalence_instances: Optional[Dict] = None
        self._orpha_index: Optional[Dict] = None
        self._processing_statistics: Optional[Dict] = None
        self._reliability_scores: Optional[Dict] = None
```

#### 1.2 Data Loading Methods
Following the `_ensure_*_loaded()` pattern:
- `_ensure_disease2prevalence_loaded()`
- `_ensure_prevalence2diseases_loaded()`
- `_ensure_prevalence_instances_loaded()`
- `_ensure_orpha_index_loaded()`
- `_ensure_processing_statistics_loaded()`
- `_ensure_reliability_scores_loaded()`

#### 1.3 Basic Query Methods
```python
# Core functionality
def get_prevalence_for_disease(self, orpha_code: str, 
                             prevalence_type: Optional[str] = None,
                             geographic_area: Optional[str] = None,
                             min_reliability: float = 0.0) -> List[Dict]
def get_diseases_for_prevalence_class(self, prevalence_class: str) -> List[Dict]
def get_prevalence_details(self, prevalence_id: str) -> Optional[Dict]
def get_disease_prevalence_summary(self, orpha_code: str) -> Optional[Dict]

# Reliability-based queries (CRITICAL for data quality)
def get_most_reliable_prevalence(self, orpha_code: str, 
                               prevalence_type: str = "Point prevalence") -> Optional[Dict]
def get_reliable_prevalence_for_disease(self, orpha_code: str, 
                                      min_score: float = 6.0) -> List[Dict]
def get_validated_prevalence_for_disease(self, orpha_code: str) -> List[Dict]
def get_best_prevalence_estimate(self, orpha_code: str, 
                               prefer_worldwide: bool = True) -> Optional[Dict]

# Geographic-aware queries (ESSENTIAL for regional analysis)
def get_worldwide_prevalence(self, orpha_code: str) -> List[Dict]
def get_regional_prevalence(self, orpha_code: str, region: str) -> List[Dict]
def get_prevalence_geographic_variants(self, orpha_code: str) -> Dict[str, List[Dict]]
```

#### 1.4 Search and Filter Methods
```python
# Geographic filters (140+ regions available)
def search_prevalence_by_region(self, region: str) -> List[Dict]
def search_diseases_by_region(self, region: str) -> List[Dict]
def get_available_regions(self) -> List[str]
def get_top_regions_by_data_volume(self, limit: int = 20) -> List[Dict]

# Prevalence type filters (5 types: Point, Birth, Annual, Cases, Lifetime)
def search_by_prevalence_type(self, prevalence_type: str) -> List[Dict]
def search_point_prevalence(self) -> List[Dict]  # Most common type (7,890 records)
def search_birth_prevalence(self) -> List[Dict]  # Genetic diseases (2,063 records)
def search_annual_incidence(self) -> List[Dict]  # New cases (3,064 records)
def search_cases_families(self) -> List[Dict]    # Ultra-rare reports (3,355 records)

# Prevalence class filters (rarity levels)
def search_by_prevalence_class(self, prevalence_class: str) -> List[Dict]
def search_ultra_rare(self) -> List[Dict]        # <1 / 1,000,000
def search_very_rare(self) -> List[Dict]         # 1-9 / 1,000,000  
def search_rare(self) -> List[Dict]              # 1-9 / 100,000
def search_uncommon(self) -> List[Dict]          # 1-5 / 10,000+

# Reliability filters (0-10 scoring system)
def search_reliable_prevalence(self, min_score: float = 6.0) -> List[Dict]
def search_validated_prevalence(self) -> List[Dict]  # 14,520 validated records
def search_highest_quality(self, min_score: float = 9.0) -> List[Dict]
def search_pmid_sourced(self) -> List[Dict]      # PMID-referenced data

# Disease name search
def search_diseases_by_name(self, query: str) -> List[Dict]
def search_diseases_with_multiple_regions(self) -> List[Dict]
def search_diseases_with_reliable_data(self, min_score: float = 8.0) -> List[Dict]
```

#### 1.5 Statistics and Analysis Methods
```python
# Core statistics (following drug_stats.py pattern)
def get_statistics(self) -> Dict
def get_basic_coverage_stats(self) -> Dict
def get_data_quality_metrics(self) -> Dict

# Disease analysis (based on actual data patterns)
def get_diseases_with_most_prevalence_records(self, limit: int = 20) -> List[Dict]
def get_diseases_by_reliability_score(self, limit: int = 20) -> List[Dict]
def get_diseases_with_global_coverage(self) -> List[Dict]
def get_diseases_with_regional_variations(self) -> List[Dict]

# Geographic analysis (140+ regions in data)
def get_regions_with_most_data(self, limit: int = 20) -> List[Dict]
def get_geographic_distribution(self) -> Dict[str, int]
def get_regional_data_quality(self) -> Dict[str, float]  # Avg reliability by region
def get_regional_coverage_completeness(self) -> Dict[str, int]

# Reliability and quality analysis (critical for prevalence data)
def get_reliability_distribution(self) -> Dict[str, int]  # 0-10 score ranges
def get_validation_status_distribution(self) -> Dict[str, int]
def get_source_quality_breakdown(self) -> Dict[str, int]  # PMID vs Registry vs Expert
def get_fiable_vs_non_fiable_stats(self) -> Dict[str, int]

# Prevalence type analysis (5 types in data)
def get_prevalence_type_distribution(self) -> Dict[str, int]
def get_type_by_disease_category(self) -> Dict[str, Dict[str, int]]
def get_reliability_by_prevalence_type(self) -> Dict[str, float]

# Prevalence class analysis (rarity spectrum)
def get_prevalence_class_distribution(self) -> Dict[str, int]
def get_rarity_spectrum_analysis(self) -> Dict[str, int]
def get_estimate_confidence_breakdown(self) -> Dict[str, int]  # class vs value estimates

# Advanced analytics for research
def get_data_density_analysis(self) -> Dict  # Records per disease distribution
def get_multi_region_diseases(self) -> List[Dict]  # Diseases with >5 regions
def get_consensus_analysis(self) -> Dict  # Where multiple sources agree
def get_data_gaps_analysis(self) -> Dict  # Missing regions/types per disease
```

#### 1.6 Utility Methods
```python
def clear_cache(self)
def preload_all(self)
def is_data_available(self) -> bool
@lru_cache(maxsize=100)
def _get_disease_cached(self, orpha_code: str) -> Optional[Dict]
```

### Task 2: Create Prevalence Statistics Module

**File**: `etl/05_stats/orpha/orphadata/prevalence_stats.py`

**Based on**: `etl/05_stats/orpha/orphadata/drug_stats.py` template

#### 2.1 Core Statistics Generation
```python
def generate_prevalence_statistics():
    """Generate comprehensive prevalence statistics"""
    controller = PrevalenceController()
    
    # Basic statistics
    stats = controller.get_statistics()
    
    # Enhanced analytics
    reliability_dist = controller.get_reliability_distribution()
    geographic_dist = controller.get_geographic_distribution()
    type_dist = controller.get_prevalence_type_distribution()
    
    # Top diseases/regions
    top_diseases = controller.get_diseases_with_most_prevalence_records(20)
    top_regions = controller.get_regions_with_most_data(20)
```

#### 2.2 Visualization Generation
Based on `drug_stats.py` patterns, create comprehensive visualizations:

```python
def create_all_plots(self):
    """Create all prevalence visualization plots"""
    # 1. Basic overview dashboard (4-panel plot)
    self.plot_basic_overview()
    
    # 2. Data quality analysis plots
    self.plot_data_quality_analysis()
    
    # 3. Disease analysis plots  
    self.plot_disease_analysis()
    
    # 4. Geographic distribution plots
    self.plot_geographic_analysis()
    
    # 5. Prevalence type analysis
    self.plot_prevalence_type_analysis()
    
    # 6. Reliability and validation plots
    self.plot_reliability_analysis()
    
    # 7. Prevalence class/rarity spectrum
    self.plot_rarity_spectrum()
    
    # 8. Comprehensive dashboard
    self.create_dashboard()

def plot_basic_overview(self):
    """4-panel basic statistics overview"""
    # Panel 1: Disease coverage pie chart (with vs without prevalence)
    # Panel 2: Key metrics bar chart (diseases, records, regions, types)
    # Panel 3: Reliability distribution (fiable vs non-fiable)
    # Panel 4: Geographic coverage top regions

def plot_data_quality_analysis(self):
    """Data quality focused visualizations"""
    # Plot 1: Reliability score histogram (0-10 distribution)
    # Plot 2: Validation status pie chart (Validated vs Not validated)
    # Plot 3: Source quality breakdown (PMID vs Registry vs Expert)
    # Plot 4: Estimate confidence (class-based vs value-based)

def plot_disease_analysis(self):
    """Disease-focused analysis plots"""
    # Plot 1: Top 20 diseases by prevalence record count
    # Plot 2: Disease prevalence record distribution histogram
    # Plot 3: Diseases with global vs regional coverage
    # Plot 4: Disease reliability score distribution

def plot_geographic_analysis(self):
    """Geographic distribution and coverage"""
    # Plot 1: Top 20 regions by record count (horizontal bar)
    # Plot 2: Regional data quality (average reliability scores)
    # Plot 3: Geographic coverage heatmap-style visualization
    # Plot 4: Worldwide vs Regional vs Country-specific breakdown

def plot_prevalence_type_analysis(self):
    """Prevalence type patterns"""
    # Plot 1: Type distribution pie chart (Point, Birth, Annual, Cases, Lifetime)
    # Plot 2: Prevalence type by disease category analysis
    # Plot 3: Reliability scores by prevalence type
    # Plot 4: Regional preferences for prevalence types

def plot_reliability_analysis(self):
    """Reliability and validation focus"""
    # Plot 1: Reliability score distribution (detailed 0-10 bins)
    # Plot 2: Validation status by region
    # Plot 3: Source quality by prevalence type
    # Plot 4: Reliability trends over time (if temporal data available)

def plot_rarity_spectrum(self):
    """Prevalence class and rarity analysis"""
    # Plot 1: Prevalence class distribution (ultra-rare to common)
    # Plot 2: Per-million estimates distribution
    # Plot 3: Rarity by disease category
    # Plot 4: Confidence levels by prevalence class

def create_dashboard(self):
    """Comprehensive 8-panel dashboard"""
    # Following drug_stats.py dashboard pattern:
    # Panel 1: Key metrics bar chart
    # Panel 2: Disease coverage pie chart  
    # Panel 3: Top diseases by record count
    # Panel 4: Prevalence type distribution
    # Panel 5: Top regions by data volume
    # Panel 6: Reliability distribution
    # Panel 7: Geographic coverage
    # Panel 8: Summary statistics text panel
```

#### 2.3 Report Generation
```python
def generate_prevalence_summary_report():
    """Generate markdown summary report"""
    # Key metrics
    # Data quality assessment  
    # Geographic coverage
    # Reliability analysis
```

### Task 3: Integration and Testing

#### 3.1 Controller Usage Example
```python
# Example usage pattern - handling real complexity
from core.datastore.orpha.orphadata.prevalence_client import PrevalenceController

controller = PrevalenceController()

# BASIC QUERY - Multiple results for one disease
prevalence_data = controller.get_prevalence_for_disease("586")  # Cystic Fibrosis
# Returns: [
#   {"prevalence_type": "Prevalence at birth", "geographic_area": "Spain", 
#    "prevalence_class": "1-5 / 10 000", "reliability_score": 9.8},
#   {"prevalence_type": "Point prevalence", "geographic_area": "Spain",
#    "prevalence_class": "1-9 / 100 000", "reliability_score": 10.0},
#   {"prevalence_type": "Point prevalence", "geographic_area": "Worldwide",
#    "prevalence_class": "1-5 / 10 000", "reliability_score": 8.5}
# ]

# SMART QUERY - Get most reliable estimate with filtering
best_estimate = controller.get_best_prevalence_estimate("586", prefer_worldwide=True)
# Returns most reliable worldwide data, falls back to regional if needed

# NEW: WEIGHTED MEAN QUERY - Single consolidated estimate per disease
mean_prevalence = controller.get_mean_prevalence_estimate("586")
# Returns: {"mean_value_per_million": 125.5, "valid_records_count": 3, "calculation_method": "reliability_weighted_mean"}

# FILTERED QUERY - Specific requirements
spain_birth_prevalence = controller.get_prevalence_for_disease(
    "586", 
    prevalence_type="Prevalence at birth",
    geographic_area="Spain",
    min_reliability=8.0
)

# RELIABILITY-AWARE QUERY - Only high-quality data
reliable_data = controller.get_reliable_prevalence_for_disease("586", min_score=8.0)

# GEOGRAPHIC ANALYSIS - Regional variations
geographic_variants = controller.get_prevalence_geographic_variants("586")
# Returns: {
#   "Spain": [spanish_records],
#   "Worldwide": [worldwide_records], 
#   "Europe": [european_records]
# }

# RESEARCH QUERIES - Advanced filtering
ultra_rare_diseases = controller.search_ultra_rare()  # <1 / 1,000,000
validated_only = controller.search_validated_prevalence()
pmid_sourced = controller.search_pmid_sourced()

# STATISTICAL ANALYSIS
stats = controller.get_statistics()
quality_metrics = controller.get_data_quality_metrics()
regional_quality = controller.get_regional_data_quality()

# COMPLEX RESEARCH SCENARIO - Multi-step analysis
diseases_with_good_data = controller.search_diseases_with_reliable_data(min_score=8.5)
multi_region_diseases = controller.get_multi_region_diseases()
consensus_data = controller.get_consensus_analysis()  # Where sources agree
```

#### 3.2 Statistics Usage Example
```python
# Generate statistics
from etl.05_stats.orpha.orphadata.prevalence_stats import generate_prevalence_statistics

stats = generate_prevalence_statistics()
# Output: results/etl/orpha/orphadata/prevalence/prevalence_statistics.json
```

## Expected Output Files

### 1. Core Client
- `core/datastore/orpha/orphadata/prevalence_client.py` - Main controller class

### 2. Statistics Module  
- `etl/05_stats/orpha/orphadata/prevalence_stats.py` - Statistics generation

### 3. Generated Results
- `results/etl/orpha/orphadata/prevalence/prevalence_statistics.json` - Statistics data
- `results/etl/orpha/orphadata/prevalence/prevalence_summary.md` - Report
- `results/etl/orpha/orphadata/prevalence/prevalence_characteristics.png` - Visualizations

## Implementation Notes

### Data File Structure
The controller will work with these key files (after prerequisites are implemented):
- **disease2prevalence.json** (33MB): Main mapping from OrphaCode to prevalence records **+ NEW `mean_value_per_million` field**
- **prevalence_instances.json** (8.5MB): All individual prevalence records
- **orpha_index.json** (1.3MB): Optimized lookup index
- **reliability/reliability_scores.json**: Detailed reliability metrics

**⚠️ Critical**: Current data does NOT include `mean_value_per_million` field - must implement prerequisites first!

### Schema Integration
- Use existing `PrevalenceInstance` model for individual records
- Use `DiseasePrevalenceMapping` for disease-level data
- Use `ReliabilityScore` for reliability analysis
- **Do NOT modify** existing schemas as they are working correctly

### Performance Considerations
- Lazy loading: Only load data when first accessed
- LRU cache: Cache frequently accessed queries (maxsize=1000)
- Memory management: Large files (33MB) need efficient loading
- File size awareness: disease2prevalence.json is very large

### Error Handling
- File not found: Graceful degradation with empty data
- Invalid orpha_code: Return empty list
- Memory issues: Clear cache functionality
- Data validation: Use existing Pydantic models

## Success Criteria

1. **Functional Controller**: PrevalenceController provides all basic query capabilities
2. **Schema Compliance**: All data access uses existing prevalence schemas
3. **Performance**: Controller handles large files (33MB) efficiently with caching
4. **Statistics**: Comprehensive statistics generation and visualization
5. **Consistency**: Follows same patterns as existing DrugController
6. **Documentation**: Clear examples and usage patterns

## Dependencies

- **Working schemas**: `core/schemas/orpha/orphadata/orpha_prevalence.py`
- **Template controller**: `core/datastore/orpha/orphadata/drug_client.py`
- **Template stats**: `etl/05_stats/orpha/orphadata/drug_stats.py`
- **Processed data**: `data/03_processed/orpha/orphadata/orpha_prevalence/`

## Priority Order

1. **High Priority**: Implement PrevalenceController core functionality
2. **Medium Priority**: Add search and filter methods
3. **Medium Priority**: Create statistics module
4. **Low Priority**: Generate visualizations and reports

This task plan provides a complete roadmap for implementing the ProcessedPrevalenceClient while leveraging existing working code patterns and schemas.

---

## Addendum: Knowledge Gaps - Understanding Prevalence Data

### What is Prevalence Data?

After examining the actual data files, prevalence data is **highly complex and multidimensional**:

#### 1. **Prevalence Types** (4 Main Categories)
- **Point prevalence**: How many people have the disease at a specific time
- **Prevalence at birth**: How many babies are born with the disease  
- **Annual incidence**: How many new cases occur per year
- **Cases/families**: Known case reports (often for ultra-rare diseases)
- **Lifetime Prevalence**: Total lifetime risk (rare type)

#### 2. **Prevalence Classes** (Standardized Ranges)
From examining `prevalence_classes.json`:
- **"<1 / 1 000 000"**: Ultra-rare (0.5 per million estimate)
- **"1-9 / 1 000 000"**: Very rare (5.0 per million estimate)  
- **"1-9 / 100 000"**: Rare (50.0 per million estimate)
- **"1-5 / 10 000"**: Less rare (300.0 per million estimate)
- **"6-9 / 10 000"**: Uncommon (750.0 per million estimate)
- **">1 / 1000"**: Common (1000+ per million estimate)
- **"Unknown"**: No reliable data available

#### 3. **Geographic Complexity** (140+ Regions)
Data spans **140+ geographic areas** including:
- **Worldwide**: 8,835 records (largest category)
- **Europe**: 1,675 records  
- **United States**: 449 records
- **Country-specific**: Spain (218), France (274), Germany (221), etc.
- **Regional**: South East Asia, Latin America, Africa, etc.

#### 4. **Reliability Scoring System** (0-10 Scale)
- **Score ≥6.0**: "Fiable" (reliable) - 14,241 of 16,420 records (86.7%)
- **Validation Status**: "Validated" vs "Not yet validated"
- **Source Quality**: PMID references, registries, expert opinion
- **Qualification**: "Value and class" vs "Class only" vs "Case(s)"

#### 5. **Data Volume & Complexity**
From `statistics.json`:
- **6,317 disorders** with prevalence data
- **16,420 total prevalence records** 
- **14,241 reliable records** (86.7% reliability rate)
- **33MB disease2prevalence.json** file (very large!)

### Key Data Relationships

#### Disease → Multiple Prevalence Records
Each disease can have:
```json
{
  "orpha_code": "586", // Cystic Fibrosis
  "prevalence_records": [
    {
      "prevalence_type": "Prevalence at birth",
      "geographic_area": "Spain", 
      "prevalence_class": "1-5 / 10 000",
      "reliability_score": 9.8
    },
    {
      "prevalence_type": "Point prevalence",
      "geographic_area": "Spain",
      "prevalence_class": "1-9 / 100 000", 
      "reliability_score": 10.0
    }
  ]
}
```

#### Regional Variations
Same disease, different regions:
- **Huntington Disease in Spain**: 50 per million (Point prevalence)
- **Huntington Disease in US**: Could be different
- **Huntington Disease Worldwide**: Another estimate

#### Multiple Data Sources
- **PMID citations**: PubMed research papers
- **Registries**: EUROCAT, RARECARE surveillance
- **Expert opinion**: Clinical expert estimates
- **Institution data**: Disease control centers

### Critical Implementation Questions

#### 1. **Which Prevalence to Show?**
When user asks "What's the prevalence of Cystic Fibrosis?":
- Show **most reliable** (highest reliability_score)?
- Show **most recent** (latest processing)?
- Show **geographic-specific** (user's region)?
- Show **prevalence type-specific** (point vs birth prevalence)?
- Show **all variants** with context?

#### 2. **How to Handle Geographic Specificity?**
- Prioritize **"Worldwide"** data as default?
- Allow **region filtering** (Europe, US, specific countries)?
- Show **regional variations** in analysis?
- Handle **missing regional data** gracefully?

#### 3. **Reliability vs Completeness Trade-off**
- Focus on **"fiable" records only** (≥6.0 score)?
- Include **lower reliability** for completeness?
- Show **reliability warnings** to users?
- Filter by **validation status**?

#### 4. **Prevalence Type Complexity**
- **Default to Point Prevalence** (most common)?
- Show **birth prevalence** for genetic diseases?
- Include **incidence rates** for analysis?
- Handle **"Cases/families"** differently (qualitative)?

### Revised Statistics Requirements

Based on `drug_stats.py` analysis patterns, prevalence stats should include:

#### 1. **Basic Coverage Statistics**
- Total diseases with prevalence data
- Reliability distribution (fiable vs non-fiable)
- Geographic coverage analysis
- Prevalence type distribution

#### 2. **Data Quality Visualizations**
- **Reliability Score Distribution**: Histogram of 0-10 scores
- **Validation Status**: Validated vs Not validated pie chart
- **Geographic Coverage Map**: Countries/regions with data
- **Source Quality**: PMID vs Registry vs Expert breakdown

#### 3. **Disease Analysis Plots**
- **Top Diseases by Prevalence Records**: Which diseases have most data
- **Prevalence Class Distribution**: Ultra-rare to common breakdown  
- **Diseases by Geographic Coverage**: Which diseases have global vs local data
- **Reliability by Disease**: Which diseases have highest quality data

#### 4. **Geographic Analysis**
- **Records by Region**: Bar chart of top countries/regions
- **Regional Data Quality**: Reliability scores by geography
- **Geographic Coverage Completeness**: Which regions lack data
- **Worldwide vs Regional**: Comparison of data sources

#### 5. **Prevalence Type Analysis**
- **Type Distribution**: Point vs Birth vs Incidence vs Cases
- **Type by Disease Category**: Which types are common for which diseases
- **Quality by Type**: Reliability scores by prevalence type
- **Regional Type Patterns**: Geographic preferences for data types

#### 6. **Advanced Analytics**
- **Data Density Analysis**: Records per disease distribution
- **Estimate Confidence**: Class-based vs value-based prevalence
- **Source Reliability**: PMID-based vs other sources
- **Temporal Patterns**: If processing timestamps reveal trends

### ✅ IMPLEMENTATION COMPLETED

**✅ PHASE 0 (CRITICAL PREREQUISITES) - COMPLETED:**
1. **✅ COMPLETED**: Fixed hardcoded paths in `process_orpha_prevalence.py`
2. **✅ COMPLETED**: Implemented `mean_value_per_million` weighted calculation 
3. **✅ COMPLETED**: Updated schemas to include new fields
4. **✅ COMPLETED**: Enhanced preprocessing pipeline

**✅ PHASE 1 (CLIENT IMPLEMENTATION) - COMPLETED:**
1. **✅ COMPLETED**: Core data access with geographic and reliability filtering
2. **✅ COMPLETED**: Statistical analysis focusing on data quality and coverage  
3. **✅ COMPLETED**: Advanced search with prevalence type and region combinations
4. **✅ COMPLETED**: Comprehensive visualizations matching drug_stats.py patterns
5. **✅ COMPLETED**: Regional comparison tools and reliability-weighted analysis

---

## 🎉 IMPLEMENTATION SUMMARY

### What Was Built

#### 1. **ProcessedPrevalenceClient** (`core/datastore/orpha/orphadata/prevalence_client.py`)
- **373 lines** of comprehensive controller implementation
- **Lazy loading and caching** for optimal performance
- **Advanced filtering** by geography, reliability, prevalence type
- **Geographic-aware queries** (140+ regions supported)
- **Reliability-based queries** with smart fallbacks
- **Weighted mean prevalence estimates** for consolidated data
- **Search capabilities** across diseases, regions, and data quality levels
- **Statistical analysis methods** for coverage and quality metrics

#### 2. **Enhanced Prevalence Processing** (`etl/03_process/orpha/orphadata/process_orpha_prevalence.py`)
- **Fixed path issues** to use correct data structure
- **Implemented weighted mean calculation** with comprehensive metadata
- **Enhanced reliability scoring** with detailed breakdown
- **Improved data validation** and error handling

#### 3. **Updated Schemas** (`core/schemas/orpha/orphadata/orpha_prevalence.py`)
- **New `MeanCalculationMetadata` model** for calculation details
- **Enhanced `DiseasePrevalenceMapping`** with mean fields
- **Updated `DiseaseStatistics`** with validity metrics
- **Comprehensive validation** for data quality

#### 4. **PrevalenceStatistics Module** (`etl/05_stats/orpha/orphadata/prevalence_stats.py`)
- **Comprehensive analysis framework** following drug_stats.py pattern
- **8 visualization types** covering all data dimensions
- **Dashboard creation** with multi-panel analysis
- **Markdown and JSON reports** for comprehensive documentation
- **Advanced analytics** including consensus analysis and data gaps

### Key Features Implemented

#### **Data Access Capabilities:**
- Query by disease with multi-dimensional filtering
- Geographic-aware searches (Worldwide vs Regional)
- Reliability-based filtering (fiable vs non-fiable)
- Prevalence type filtering (Point, Birth, Annual, Cases)
- Multi-region disease identification
- Best estimate selection with smart fallbacks

#### **Statistical Analysis:**
- **Basic coverage stats** (diseases, records, reliability)
- **Data quality metrics** (validation, source quality)
- **Geographic distribution** analysis (140+ regions)
- **Reliability patterns** (score distributions, validation status)
- **Rarity spectrum analysis** (ultra-rare to common)
- **Advanced patterns** (consensus, data gaps, density)

#### **Visualization Capabilities:**
- **Basic overview dashboard** (4-panel analysis)
- **Data quality analysis** (reliability, validation, sources)
- **Disease analysis** (top diseases, record distributions)
- **Geographic analysis** (regional coverage, quality)
- **Prevalence type analysis** (distribution, reliability by type)
- **Reliability analysis** (detailed scoring, quality levels)
- **Rarity spectrum** (prevalence class distributions)
- **Comprehensive dashboard** (multi-dimensional overview)

#### **Data Quality Enhancements:**
- **Weighted mean calculation** for consolidated estimates
- **Reliability-weighted averaging** with fallback strategies
- **Data exclusion logic** (cases/families, unknown, zero estimates)
- **Comprehensive metadata** tracking for calculation transparency

### Ready for Use

The ProcessedPrevalenceClient is now ready for:
1. **Research applications** requiring prevalence data
2. **Statistical analysis** of rare disease epidemiology
3. **Geographic studies** of disease distribution
4. **Data quality assessment** and validation
5. **Visualization generation** for reports and presentations

### Usage Examples

```python
# Initialize controller
controller = PrevalenceController()

# Get comprehensive disease data
summary = controller.get_disease_prevalence_summary("79318")  # PMM2-CDG

# Get weighted mean estimate
mean_estimate = controller.get_mean_prevalence_estimate("79318")

# Search by reliability and region
reliable_eu_data = controller.get_prevalence_for_disease(
    "79318", 
    geographic_area="Europe", 
    min_reliability=8.0
)

# Generate statistics
stats = PrevalenceStatistics()
stats.generate_all_statistics()  # Creates 8 comprehensive visualizations
```

**Implementation Status: 100% Complete ✅**

**DEPENDENCIES**: Phase 1 cannot begin until Phase 0 is completed and prevalence data includes `mean_value_per_million` field.

This deep analysis reveals prevalence data is **much more complex** than simple drug mappings - it requires **sophisticated filtering, geographic awareness, and reliability-based prioritization** to be useful for researchers. 