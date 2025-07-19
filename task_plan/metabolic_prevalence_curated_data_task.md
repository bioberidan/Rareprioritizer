# Task Plan: Metabolic Disease Curated Prevalence Generation

**Date**: December 2024  
**Priority**: High  
**Estimated Time**: 1.5-2 hours  
**Type**: Curated Data Processing + Client Infrastructure + Statistics

---

## 📋 **Task Overview**

### **Three-Step Process**
1. **🏭 Curator Script**: Process raw metabolic diseases → Generate curated prevalence files
2. **🔌 Client Infrastructure**: Create CuratedMetabolicClient for data access
3. **📊 Statistics Module**: Generate analysis and reports for metabolic prevalence

### **Business Context**
- **Input**: 665 metabolic diseases from curated ORDO data
- **Output**: Spanish patient estimates for prevalence-based healthcare planning
- **Spanish Population**: 47 million inhabitants
- **Data Flow**: Curated Disease List → Processed Prevalence → Spanish Patients → Statistics

---

## 🏭 **Step 1: Curator Script - Data Processing**

### **Input Data Analysis**
- **Source File**: `data/04_curated/orpha/ordo/metabolic_disease_instances.json`

- **Data Structure**: 
  ```json
  [
    {"disease_name": "PMM2-CDG", "orpha_code": "79318"},
    {"disease_name": "MPI-CDG", "orpha_code": "79319"}
  ]
  ```
- **Count**: 665 metabolic diseases (2,662 lines in file)
- **Orpha Codes**: String format, need conversion to integers

### **Curator Processing Workflow**

#### **Step 1.1: Data Extraction**
- Load metabolic disease instances from curated JSON
- Extract orpha_codes and convert to integers
- Validate data completeness and format

#### **Step 1.2: Prevalence Lookup**
- Use `ProcessedPrevalenceClient` to query prevalence data
- Handle missing prevalence data gracefully (log warnings)
- Extract `mean_value_per_million` for each disease

#### **Step 1.3: Spanish Population Calculation**
- **Formula**: `spanish_patients = prevalence_per_million × 47`
- **Rounding**: Round to **integer** for patients
- **Handle Edge Cases**: Zero prevalence, very low prevalence

#### **Step 1.4: Output Generation**
Two JSON files with identical structure but different values:

**File 1**: `metabolic_diseases2prevalence_per_million.json`
```json
{
  79318: 2.5,
  79319: 1.8,
  321: 45.2
}
```

**File 2**: `metabolic_diseases2spanish_patient_number.json`
```json
{
  79318: 118,
  79319: 85,
  321: 2124
}
```

### **Curator Script Specification**
- **File**: `etl/04_curate/orpha/orphadata/curate_metabolic_prevalence.py`
- **Class**: `MetabolicPrevalenceCurator`
- **CLI Interface**: Support for custom output directories
- **Logging**: Comprehensive processing logs
- **Statistics**: Summary of processing results

### **Output Paths**
```
data/04_curated/orpha/orphadata/
├── metabolic_diseases2prevalence_per_million.json
└── metabolic_diseases2spanish_patient_number.json
```

### **Error Handling**
- **Missing Prevalence**: Log warning, skip disease, continue processing
- **Invalid Orpha Code**: Log error, skip disease
- **Zero Prevalence**: Include in output as 0.0
- **Processing Summary**: Report total processed, skipped, errors

---

## 🔌 **Step 2: Client Infrastructure - Data Access Layer**

### **CuratedMetabolicClient Design**

#### **File Location**
```
core/datastore/metabolic_prevalence_client.py
```

#### **Class Structure**
```python
class CuratedPrevalenceClient:
    """Client for accessing curated metabolic disease data and prevalence"""
    
    def __init__(self, 
                 ordo_data_dir: str = "data/04_curated/orpha/ordo",
                 orphadata_dir: str = "data/04_curated/orpha/orphadata"):
```

#### **Core Methods**

##### **Disease Data Access**
- `load_metabolic_diseases()` → Load disease instances from JSON
- `get_metabolic_orpha_codes()` → List of integer orpha codes
- `get_disease_name_by_orpha_code(code)` → Get disease name (with lazy loading from other sources)

##### **Prevalence Data Access**
- `load_prevalence_data()` → Load prevalence per million mapping
- `get_disease_prevalence_per_million(orpha_code)` → Prevalence for specific disease
- `get_spanish_patients_number(orpha_code)` → Spanish patients for specific disease

##### **Bulk Operations**
- `get_all_metabolic_prevalences()` → Dictionary of all prevalences
- `get_all_spanish_patients()` → Dictionary of all Spanish patient counts
- `get_diseases_with_prevalence()` → Only diseases that have prevalence data
- `get_diseases_without_prevalence()` → Diseases missing prevalence data

#### **Data Loading Pattern**
- **Lazy Loading**: Load data only when first accessed
- **Caching**: Store loaded data in memory after first load
- **Error Handling**: Graceful handling of missing files and data
- **Validation**: Ensure data integrity and format consistency

#### **Performance Features**
- **Memory Efficient**: Only load data when needed
- **Fast Lookup**: Use dictionaries for O(1) access
- **Batch Operations**: Support for bulk data retrieval

---

## 📊 **Step 3: Statistics Module - Analysis & Reporting**

### **Metabolic Disease Statistics**

#### **File Location**
```
etl/05_stats/metabolic/metabolic_prevalence_stats.py
```

#### **Class Structure**
```python
class MetabolicPrevalenceStatsAnalyzer:
    """Statistical analysis for metabolic disease prevalence and Spanish patients"""
    
    def __init__(self, client: CuratedMetabolicClient):
        self.client = client
```

#### **Analysis Categories**

##### **Coverage Analysis**
- Total metabolic diseases analyzed
- Diseases with prevalence data vs. missing data
- Coverage percentage and gaps

##### **Prevalence Distribution Analysis**
- Descriptive statistics (mean, median, std, quartiles)
- Distribution plots and histograms
- Outlier detection for metabolic diseases

##### **Spanish Patient Analysis**
- Total estimated Spanish patients for metabolic diseases
- Distribution of patient counts across diseases
- Top diseases by Spanish patient count
- Rare vs. common metabolic diseases

##### **Comparative Analysis**
- Metabolic diseases vs. all rare diseases
- High-burden vs. low-burden metabolic conditions
- Geographic and demographic insights

#### **Output Generation**
- **JSON Reports**: Detailed statistical summaries
- **Visualizations**: Distribution plots, bar charts, comparative graphs
- **CSV Exports**: Data tables for further analysis
- **Summary Dashboard**: Key metrics and insights

### **Integration with Analysis Pipeline**
```python
# Usage Example
from core.datastore.metabolic_prevalence_client import CuratedMetabolicClient
from etl.05_stats.metabolic.metabolic_prevalence_stats import MetabolicPrevalenceStatsAnalyzer

client = CuratedMetabolicClient()
analyzer = MetabolicPrevalenceStatsAnalyzer(client)
analyzer.generate_comprehensive_report()
```





---

## 📋 **Detailed Implementation Steps**

### **Prerequisites**
- Controller refactoring completed (see `controller_refactoring_task.md`)
- `ProcessedPrevalenceClient` available for use
- Curated metabolic disease data available

---


---

### **Implementation Phase Structure**

#### **Phase A: Curator Script (40 minutes)**
Create the data processing pipeline that generates curated prevalence files.

#### **Phase B: Client Infrastructure (30 minutes)**  
Build the data access layer for metabolic disease prevalence data.

#### **Phase C: Statistics Module (20 minutes)**
Develop analysis and reporting capabilities.

---

### **Phase A: Curator Script Implementation**

#### **Step A.1: Directory Setup (5 minutes)**
- [ ] Create `etl/04_curate/orpha/orphadata/` directory
- [ ] Create `data/04_curated/orpha/orphadata/` directory
- [ ] Add appropriate `__init__.py` files

#### **Step A.2: Implement MetabolicPrevalenceCurator (25 minutes)**
- [ ] Create `curate_metabolic_prevalence.py` with CLI interface
- [ ] Implement data loading from `metabolic_disease_instances.json`
- [ ] Add orpha_code validation and integer conversion
- [ ] Integrate with `ProcessedPrevalenceClient` for prevalence lookup
- [ ] Implement Spanish patient calculation (prevalence × 47, rounded to integer)
- [ ] Add comprehensive error handling and logging

#### **Step A.3: Output Generation & Testing (10 minutes)**
- [ ] Generate `metabolic_diseases2prevalence_per_million.json`
- [ ] Generate `metabolic_diseases2spanish_patient_number.json`
- [ ] Validate JSON structure `{orphacode: value}`
- [ ] Test with sample data and verify calculations

---

### **Phase B: Client Infrastructure Implementation**

#### **Step B.1: Create CuratedMetabolicClient (20 minutes)**
- [ ] Create `core/datastore/metabolic_prevalence_client.py`
- [ ] Implement lazy loading pattern for metabolic diseases
- [ ] Add prevalence data access methods
- [ ] Implement disease name lookup with lazy loading
- [ ] Add bulk operations for efficient data retrieval

#### **Step B.2: Data Integration & Validation (10 minutes)**
- [ ] Test client with generated curated data
- [ ] Verify all methods work correctly
- [ ] Add comprehensive error handling for missing data
- [ ] Test performance with full dataset

---

### **Phase C: Statistics Module Implementation**

#### **Step C.1: Create MetabolicPrevalenceStatsAnalyzer (15 minutes)**
- [ ] Create `etl/05_stats/metabolic/metabolic_prevalence_stats.py`
- [ ] Implement coverage analysis (diseases with/without prevalence)
- [ ] Add prevalence distribution analysis
- [ ] Create Spanish patient analysis and rankings
- [ ] Add comparative analysis capabilities

#### **Step C.2: Output Generation & Testing (5 minutes)**
- [ ] Generate JSON reports and visualizations
- [ ] Test integration with CuratedMetabolicClient
- [ ] Verify statistical calculations and outputs
- [ ] Create sample dashboard and summary reports

---

## 🔍 **Quality Assurance & Validation**

### **Curator Script Validation**
- [ ] **Data Completeness**: All 665 metabolic diseases processed
- [ ] **Prevalence Coverage**: Report on missing prevalence data percentage
- [ ] **Calculation Accuracy**: Spanish patients = round(prevalence × 47)
- [ ] **JSON Format**: Correct structure `{orphacode: value}` with integer keys
- [ ] **Data Types**: Orpha codes as integers, Spanish patients as integers
- [ ] **File Generation**: Both output files created successfully
- [ ] **Error Handling**: Missing prevalence logged but processing continues

### **Client Infrastructure Validation**
- [ ] **Lazy Loading**: Data loaded only when accessed
- [ ] **Caching**: Subsequent calls use cached data
- [ ] **Bulk Operations**: Efficient retrieval of all data
- [ ] **Disease Name Lookup**: Works with lazy loading from other sources
- [ ] **Error Handling**: Graceful handling of missing files and data
- [ ] **Performance**: Fast lookup operations with large datasets

### **Statistics Module Validation**
- [ ] **Coverage Analysis**: Accurate reporting of data availability
- [ ] **Distribution Analysis**: Correct statistical calculations
- [ ] **Spanish Patient Analysis**: Proper ranking and totals
- [ ] **Comparative Analysis**: Valid comparisons with broader dataset
- [ ] **Output Generation**: JSON, visualizations, and reports created
- [ ] **Integration**: Seamless work with CuratedMetabolicClient

---

## 📊 **Expected Outcomes**

### **Quantitative Results**
- **Processed Diseases**: 665 metabolic diseases
- **Prevalence Coverage**: Expected 60-80% (based on current data availability)
- **Spanish Patients**: ~400-530 diseases with patient estimates
- **Output File Sizes**: ~50-100KB each JSON file
- **Spanish Patients Range**: 1 to 2,000+ patients per disease

### **Data Products Created**
- **Curated JSON Files**: Two structured data files for prevalence and Spanish patients
- **Data Access Layer**: CuratedMetabolicClient for efficient data retrieval
- **Statistical Reports**: Comprehensive analysis of metabolic disease burden
- **Visualizations**: Distribution plots and comparative analysis charts

### **Healthcare Planning Value**
- **Resource Allocation**: Direct Spanish patient estimates for each metabolic disease
- **Burden Assessment**: Total metabolic disease patient population estimates
- **Priority Identification**: Ranking of diseases by Spanish patient count
- **Coverage Analysis**: Understanding of data gaps and completeness

### **Architecture Benefits**
- **Curated Data Pattern**: Establishes template for future curated data types
- **Three-Layer Architecture**: Clear separation of curator → client → stats
- **Reusable Components**: Client and stats patterns applicable to other disease domains
- **Scalable Infrastructure**: Ready for additional metabolic analysis needs

---

## 🚨 **Risks & Mitigation Strategies**

### **Technical Risks**
- **Missing Prevalence Data**: 
  - **Risk**: Some metabolic diseases may not have prevalence data
  - **Mitigation**: Log missing data, continue processing, provide coverage report
  
- **Refactoring Errors**:
  - **Risk**: Missed Controller references breaking existing functionality
  - **Mitigation**: Comprehensive grep search, systematic testing, incremental updates

- **Data Format Issues**:
  - **Risk**: Inconsistent orpha_code formats or invalid data
  - **Mitigation**: Robust parsing, data validation, error logging

### **Process Risks**
- **Breaking Changes**: 
  - **Risk**: Analysis scripts fail after refactoring
  - **Mitigation**: Test each script individually, maintain backup references

- **Incomplete Implementation**:
  - **Risk**: Partial implementation leaves system in inconsistent state
  - **Mitigation**: Complete refactoring phase before starting new development

---

## 📁 **Complete File Path Reference**

### **Input Files**
```
data/04_curated/orpha/ordo/metabolic_disease_instances.json
data/03_processed/orpha/orphadata/orpha_prevalence/
├── disease2prevalence.json
├── prevalence2diseases.json
└── [other prevalence data files used by ProcessedPrevalenceClient]
```

### **Generated Output Files**
```
data/04_curated/orpha/orphadata/
├── metabolic_diseases2prevalence_per_million.json
└── metabolic_diseases2spanish_patient_number.json
```

### **New Infrastructure Files Created**
```
# Phase A: Curator Script
etl/04_curate/orpha/orphadata/
├── __init__.py
└── curate_metabolic_prevalence.py

# Phase B: Client Infrastructure  
core/datastore/
└── metabolic_prevalence_client.py

# Phase C: Statistics Module
etl/05_stats/metabolic/
├── __init__.py
└── metabolic_prevalence_stats.py
```

### **Directory Structure Created**
```
etl/04_curate/orpha/orphadata/       # Curator scripts
data/04_curated/orpha/orphadata/     # Curated data files
etl/05_stats/metabolic/              # Metabolic-specific statistics
```

### **Dependencies**
```
# Requires (from controller refactoring task):
core/datastore/orpha/orphadata/prevalence_client.py (ProcessedPrevalenceClient)
```

---

## ⏱️ **Implementation Timeline**

### **Phase A: Curator Script (40 minutes)**
- Directory setup: 5 minutes
- MetabolicPrevalenceCurator implementation: 25 minutes
- Output generation & testing: 10 minutes

### **Phase B: Client Infrastructure (30 minutes)**
- CuratedMetabolicClient creation: 20 minutes
- Data integration & validation: 10 minutes

### **Phase C: Statistics Module (20 minutes)**
- MetabolicPrevalenceStatsAnalyzer implementation: 15 minutes
- Output generation & testing: 5 minutes

**Total Estimated Time**: 1.5 hours

### **Sequential Dependencies**
- **Phase A** must complete before Phase B (client needs curated data files)
- **Phase B** must complete before Phase C (stats needs client)
- All phases can be developed incrementally with testing at each step

---

## 🎯 **Summary**

This task implements a complete three-step pipeline for metabolic disease prevalence data curation:

1. **🏭 Curator**: Processes raw metabolic diseases and generates Spanish patient estimates
2. **🔌 Client**: Provides clean data access layer for curated metabolic prevalence data  
3. **📊 Statistics**: Delivers comprehensive analysis and reporting capabilities

The implementation establishes a reusable pattern for curated data processing that can be extended to other disease domains and data types.

**Related Tasks**: 
- Complete `controller_refactoring_task.md` first to ensure `ProcessedPrevalenceClient` is available
- This task is independent and focuses solely on metabolic disease curation

*This task creates the first curated data processing pipeline in the RarePrioritizer system, establishing patterns for future curated data types.* 