# Task Plan: Clinical Trials Curated Data Analysis

**Date**: December 2024  
**Priority**: High  
**Estimated Time**: 2-2.5 hours  
**Type**: Curated Data Processing + Client Infrastructure + Statistics

---

## 📋 **Task Overview**

### **Three-Step Process**
1. **🏭 Curator Script**: Process clinical trials data → Generate curated trial accessibility files
2. **🔌 Client Infrastructure**: Create CuratedClinicalTrialsClient for data access
3. **📊 Statistics Module**: Generate analysis and reports for trial accessibility

### **Business Context**
- **Input**: Processed clinical trials data in `data/03_processed/clinical_trials/`
- **Output**: Disease-focused clinical trial accessibility metrics with regional focus
- **Data Source**: 665 diseases processed, 73 with trials, 317 unique trials
- **Regional Coverage**: Spanish and EU trial accessibility from database
- **Data Flow**: Processed Trial Data → Disease-Centric Aggregation → Regional Analysis → Statistics

---

## 🔍 **Data Source Analysis**

### **Available Input Data**
- **Clinical Trials**: `data/02_preprocess/clinical_trials/` (~600+ directories)
- **Processed Trials**: `data/03_processed/clinical_trials/` (aggregated data)
- **Trial Metadata**: Status, phases, interventions, locations
- **Disease Context**: ORDO disease instances for mapping validation

### **Required Processing**
- Extract trial-disease relationships from preprocessed data
- Map trial phases and status by disease
- Calculate Spanish trial accessibility (geographic proximity + inclusion criteria)
- Calculate EU trial accessibility (European trials available)
- Generate trial availability statistics by disease

---

## 🏭 **Phase A: Curator Script - Clinical Trials Data Processing**

### **Input Data Processing**
- **Source**: Clinical trials from `data/02_preprocess/clinical_trials/` directories
- **Disease Mapping**: Link trials to Orpha disease codes
- **Geographic Filtering**: Spanish and EU trial locations and accessibility
- **Phase Analysis**: Extract trial phases (Phase I, II, III, IV)

### **ClinicalTrialsCurator Implementation**
- **File**: `etl/04_curate/clinical_trials/curate_clinical_trials.py`
- **Class**: `ClinicalTrialsCurator`
- **CLI Interface**: Support for custom output directories
- **Logging**: Comprehensive processing logs
- **Statistics**: Summary of processing results

### **Processing Workflow**
1. **Trial Data Aggregation**: Load data from all trial directories
2. **Disease Mapping**: Link trials to integer Orpha codes
3. **Geographic Analysis**: Filter for Spanish and EU accessible trials
4. **Phase Processing**: Extract and categorize trial phases
5. **Accessibility Calculation**: Calculate trial accessibility scores per disease
6. **Output Generation**: Generate structured JSON files

---

## 📊 **Generated JSON Files with Examples**

### **File 1: `orpha_diseases2spanish_trial_count.json`**
**Description**: Number of Spanish-accessible trials per disease
```json
{
  "79318": 2,
  "79319": 0,
  "321": 5,
  "156": 1,
  "1234": 8
}
```

### **File 2: `orpha_diseases2eu_trial_count.json`**
**Description**: Number of EU-accessible trials per disease
```json
{
  "79318": 4,
  "79319": 1,
  "321": 7,
  "156": 2,
  "1234": 12
}
```

### **File 3: `orpha_diseases2trial_accessibility_score.json`**
**Description**: Trial accessibility score (0-100) for Spanish patients
```json
{
  "79318": 65,
  "79319": 15,
  "321": 85,
  "156": 30,
  "1234": 90
}
```

### **File 4: `orpha_diseases2phase3_trial_count.json`**
**Description**: Number of Phase III trials per disease (most clinically relevant)
```json
{
  "79318": 1,
  "79319": 0,
  "321": 3,
  "156": 0,
  "1234": 4
}
```

### **File 5: `orpha_diseases2active_trial_count.json`**
**Description**: Number of currently active/recruiting trials per disease
```json
{
  "79318": 1,
  "79319": 0,
  "321": 2,
  "156": 1,
  "1234": 5
}
```

### **File 6: `orpha_diseases2trial_list.json`**
**Description**: Disease ID to list of trial IDs (like user requested: "1987: [trial1, trial2, trial3...]")
```json
{
  "101109": ["NCT06472557", "NCT06953583"],
  "111": ["NCT06056297"],
  "139": ["NCT06362486", "NCT06392386", "NCT06021522", "NCT06197035"],
  "324": ["NCT05280548", "NCT04020055", "NCT03737214", "NCT06328608"],
  "333": ["NCT01804686", "NCT04245839", "NCT06479135"]
}
```

### **File 7: `orpha_trials2trial_titles.json`**
**Description**: Trial ID to trial title/study name mapping
```json
{
  "NCT06472557": "Spinocerebellar Ataxia Type 27B Natural History Study (SCA27B-NHS)",
  "NCT06953583": "A Study to Learn More About the Effects and Long-Term Safety of BIIB141 (Omaveloxolone)",
  "NCT06056297": "A Study of Mavorixafor in Participants With Congenital and Acquired Primary Autoimmune",
  "NCT01797055": "Apotransferrin in Atransferrinemia",
  "NCT06362486": "Stress in Pregnancy During the Covid19 Pandemic and Impact on the Newborn Neurodevelopment"
}
```

### **File 8: `orpha_diseases2disease_names.json`**
**Description**: Disease ID to disease name mapping (same as drugs)
```json
{
  "101109": "Spinocerebellar ataxia type 28",
  "111": "Barth syndrome",
  "139": "CHILD syndrome",
  "324": "Fabry disease",
  "333": "Farber disease"
}
```

---

## 🔌 **Phase B: Client Infrastructure - Data Access Layer**

### **CuratedClinicalTrialsClient Design**

#### **File Location**
```
core/datastore/clinical_trials_client.py
```

#### **Class Structure**
```python
class CuratedClinicalTrialsClient:
    """Client for accessing curated clinical trials accessibility data"""
    
    def __init__(self, 
                 clinical_trials_dir: str = "data/04_curated/clinical_trials"):
        self.clinical_trials_dir = Path(clinical_trials_dir)
        self._spanish_trial_data = None
        self._eu_trial_data = None
        self._accessibility_data = None
        self._phase3_trial_data = None
        self._active_trial_data = None
        self._trial_list_data = None
        self._trial_titles_data = None
        self._disease_names_data = None
```

#### **Core Data Loading Methods**
```python
    def load_spanish_trial_data(self) -> Dict[int, int]:
        """Load Spanish trial count data"""
        
    def load_eu_trial_data(self) -> Dict[int, int]:
        """Load EU trial count data"""
        
    def load_accessibility_data(self) -> Dict[int, int]:
        """Load trial accessibility scores"""
        
    def load_phase3_trial_data(self) -> Dict[int, int]:
        """Load Phase III trial counts"""
        
    def load_active_trial_data(self) -> Dict[int, int]:
        """Load active trial counts"""
        
    def load_trial_list_data(self) -> Dict[int, List[str]]:
        """Load disease to trial list mappings"""
        
    def load_trial_titles_data(self) -> Dict[str, str]:
        """Load trial ID to trial title mappings"""
        
    def load_disease_names_data(self) -> Dict[int, str]:
        """Load disease ID to disease name mappings"""
```

#### **Individual Disease Access Methods**
```python
    def get_spanish_trial_count(self, orpha_code: int) -> int:
        """Get Spanish trial count for specific disease"""
        
    def get_eu_trial_count(self, orpha_code: int) -> int:
        """Get EU trial count for specific disease"""
        
    def get_trial_accessibility_score(self, orpha_code: int) -> int:
        """Get trial accessibility score for specific disease"""
        
    def get_phase3_trial_count(self, orpha_code: int) -> int:
        """Get Phase III trial count for specific disease"""
        
    def get_active_trial_count(self, orpha_code: int) -> int:
        """Get active trial count for specific disease"""
        
    def get_trial_list(self, orpha_code: int) -> List[str]:
        """Get list of trial IDs for specific disease"""
        
    def get_trial_title(self, trial_id: str) -> str:
        """Get trial title for specific trial ID"""
        
    def get_disease_name(self, orpha_code: int) -> str:
        """Get disease name for specific disease ID"""
```

#### **Bulk Data Access Methods**
```python
    def get_all_spanish_trial_counts(self) -> Dict[int, int]:
        """Get all Spanish trial counts"""
        
    def get_all_eu_trial_counts(self) -> Dict[int, int]:
        """Get all EU trial counts"""
        
    def get_all_accessibility_scores(self) -> Dict[int, int]:
        """Get all trial accessibility scores"""
        
    def get_all_phase3_trial_counts(self) -> Dict[int, int]:
        """Get all Phase III trial counts"""
        
    def get_all_active_trial_counts(self) -> Dict[int, int]:
        """Get all active trial counts"""
        
    def get_all_trial_lists(self) -> Dict[int, List[str]]:
        """Get all disease to trial list mappings"""
        
    def get_all_trial_titles(self) -> Dict[str, str]:
        """Get all trial ID to trial title mappings"""
        
    def get_all_disease_names(self) -> Dict[int, str]:
        """Get all disease ID to disease name mappings"""
```

#### **Analysis Methods**
```python
    def get_diseases_with_trials(self) -> List[int]:
        """Get diseases that have trials available"""
        
    def get_diseases_without_trials(self) -> List[int]:
        """Get diseases with no trials available"""
        
    def get_diseases_with_spanish_trials(self) -> List[int]:
        """Get diseases with Spanish-accessible trials"""
        
    def get_diseases_with_eu_trials(self) -> List[int]:
        """Get diseases with EU-accessible trials"""
        
    def get_diseases_with_phase3_trials(self) -> List[int]:
        """Get diseases with Phase III trials"""
        
    def get_high_accessibility_diseases(self, min_score: int = 70) -> List[int]:
        """Get diseases with high trial accessibility scores"""
        
    def get_spanish_vs_eu_trial_gap(self) -> Dict[int, int]:
        """Calculate trial accessibility gap between Spain and EU"""
```

#### **Enhanced Analysis Methods**
```python
    def get_trial_statistics_summary(self) -> Dict:
        """Generate comprehensive trial statistics summary"""
        
    def get_diseases_by_spanish_trial_count(self, min_trials: int = 1) -> List[int]:
        """Get diseases with minimum Spanish trial count"""
        
    def get_diseases_by_accessibility_range(self, min_score: int, max_score: int) -> List[int]:
        """Get diseases within accessibility score range"""
        
    def get_trial_phase_distribution_analysis(self) -> Dict:
        """Analyze trial phase distribution across diseases"""
        
    def get_diseases_with_active_recruitment(self) -> List[int]:
        """Get diseases with currently recruiting trials"""
```

---

## 📊 **Phase C: Statistics Module - Analysis & Reporting**

### **ClinicalTrialsStatsAnalyzer**

#### **File Location**
```
etl/05_stats/clinical_trials/clinical_trials_stats.py
```

#### **Class Structure**
```python
class ClinicalTrialsStatsAnalyzer:
    """Statistical analysis for clinical trials accessibility and availability"""
    
    def __init__(self, client: CuratedClinicalTrialsClient):
        self.client = client
```

#### **Analysis Categories**

##### **Coverage Analysis**
- Total diseases with trial data
- Spanish vs. EU trial accessibility coverage
- Phase III trial coverage (most clinically relevant)
- Active trial recruitment coverage

##### **Trial Distribution Analysis**
- Descriptive statistics for trial counts per disease
- Accessibility score distribution analysis
- Spanish-EU trial accessibility gap analysis
- Outlier detection for trial availability

##### **Phase Analysis**
- Trial phase distribution by disease
- Phase III vs. other phase availability
- Active recruitment vs. completed trials
- Spanish clinical trial participation insights

##### **Comparative Analysis**
- Spanish vs. EU trial accessibility comparison
- Phase III vs. all trial availability
- High-prevalence vs. rare disease trial coverage
- Active vs. historical trial patterns

#### **Output Generation**
- **JSON Reports**: Detailed statistical summaries
- **Visualizations**: Distribution plots, accessibility maps, phase charts
- **CSV Exports**: Trial accessibility data for further analysis
- **Dashboard**: Key trial accessibility metrics and insights

---

## 📋 **Implementation Steps**

### **Phase A: Curator Script (60 minutes)**
- [ ] Analyze clinical trials data structure in preprocessed directories
- [ ] Implement ClinicalTrialsCurator with trial-disease mapping
- [ ] Add Spanish and EU geographic accessibility filtering
- [ ] Implement trial phase and status processing
- [ ] Generate 8 structured JSON files (5 count files + 3 mapping files)
- [ ] Add comprehensive error handling and logging

### **Phase B: Client Infrastructure (45 minutes)**
- [ ] Create CuratedClinicalTrialsClient following prevalence pattern
- [ ] Implement lazy loading for all 5 data types
- [ ] Add individual disease access methods
- [ ] Implement bulk operations for efficient data retrieval
- [ ] Add analysis methods for trial accessibility insights
- [ ] Test client with generated curated data

### **Phase C: Statistics Module (30 minutes)**
- [ ] Create ClinicalTrialsStatsAnalyzer
- [ ] Implement coverage and distribution analysis
- [ ] Add Spanish vs. EU comparative analysis
- [ ] Create outlier detection for trial accessibility
- [ ] Generate JSON reports and visualizations
- [ ] Test integration with CuratedClinicalTrialsClient

---

## 🎯 **Expected Outcomes**

### **Quantitative Results**
- **Processed Diseases**: All diseases with trial mappings
- **Spanish Trial Coverage**: Percentage of diseases with Spanish-accessible trials
- **EU Trial Coverage**: Percentage of diseases with EU-accessible trials
- **Phase III Coverage**: Diseases with Phase III trials
- **Accessibility Range**: Trial accessibility scores from 0-100

### **Data Products Created**
- **8 Curated JSON Files**: 5 count files + 3 mapping files (trial lists, trial titles, disease names)
- **Data Access Layer**: CuratedClinicalTrialsClient for efficient data retrieval
- **Statistical Reports**: Comprehensive trial accessibility analysis
- **Visualizations**: Distribution plots and accessibility analysis charts

### **Healthcare Planning Value**
- **Spanish Trial Access**: Direct assessment of trial accessibility for Spanish patients
- **EU Comparison**: Understanding of Spain's position in EU clinical research
- **Research Gaps**: Identification of diseases lacking clinical trials
- **Phase III Focus**: Emphasis on most clinically relevant trials
- **Active Opportunities**: Current trial recruitment for Spanish patients

---

## 📁 **File Structure**

### **Curated Data Output**
```
data/04_curated/clinical_trials/
├── orpha_diseases2spanish_trial_count.json
├── orpha_diseases2eu_trial_count.json
├── orpha_diseases2trial_accessibility_score.json
├── orpha_diseases2phase3_trial_count.json
├── orpha_diseases2active_trial_count.json
├── orpha_diseases2trial_list.json
├── orpha_trials2trial_titles.json
└── orpha_diseases2disease_names.json
```

### **Infrastructure Files**
```
# Phase A: Curator Script
etl/04_curate/clinical_trials/
└── curate_clinical_trials.py

# Phase B: Client Infrastructure  
core/datastore/
└── clinical_trials_client.py

# Phase C: Statistics Module
etl/05_stats/clinical_trials/
├── __init__.py
└── clinical_trials_stats.py
```

### **Results Output**
```
results/etl/clinical_trials/
├── clinical_trials_statistics.json
├── clinical_trials_accessibility_analysis.png
├── spanish_vs_eu_trial_comparison.png
└── clinical_trials_outlier_analysis.png
```

---

## 🔍 **Quality Assurance & Validation**

### **Curator Script Validation**
- [ ] **Data Completeness**: All available trial-disease mappings processed
- [ ] **Geographic Accuracy**: Correct Spanish and EU trial filtering
- [ ] **Phase Accuracy**: Proper trial phase classifications
- [ ] **JSON Format**: Correct orphacode:value structure with integer keys
- [ ] **Accessibility Calculation**: Accurate scoring methodology
- [ ] **File Generation**: All 5 output files created successfully

### **Client Infrastructure Validation**
- [ ] **Lazy Loading**: Data loaded only when accessed
- [ ] **Caching**: Subsequent calls use cached data
- [ ] **Bulk Operations**: Efficient retrieval of all data
- [ ] **Error Handling**: Graceful handling of missing files and data
- [ ] **Performance**: Fast lookup operations with large datasets
- [ ] **Consistency**: Matches prevalence client patterns

### **Statistics Module Validation**
- [ ] **Coverage Analysis**: Accurate reporting of trial accessibility
- [ ] **Distribution Analysis**: Correct statistical calculations
- [ ] **Comparative Analysis**: Valid Spain vs. EU comparisons
- [ ] **Outlier Detection**: Meaningful trial accessibility outliers
- [ ] **Output Generation**: JSON, visualizations, and reports created
- [ ] **Integration**: Seamless work with CuratedClinicalTrialsClient

---

## ⏱️ **Implementation Timeline**

### **Phase A: Curator Script (75 minutes)**
- Data analysis and validation: 15 minutes
- ClinicalTrialsCurator implementation: 35 minutes
- Mapping files generation (trial lists, titles): 15 minutes
- Output generation & testing: 10 minutes

### **Phase B: Client Infrastructure (45 minutes)**
- CuratedClinicalTrialsClient creation: 30 minutes
- Data integration & validation: 15 minutes

### **Phase C: Statistics Module (30 minutes)**
- ClinicalTrialsStatsAnalyzer implementation: 20 minutes
- Output generation & testing: 10 minutes

**Total Estimated Time**: 2.5 hours

---

## 🚨 **Risks & Mitigation Strategies**

### **Technical Risks**
- **Trial Data Quality**: 
  - **Risk**: Preprocessed trial data may be incomplete or inconsistent
  - **Mitigation**: Validate data structure, provide coverage reports
  
- **Geographic Mapping**:
  - **Risk**: Trial location data may not accurately reflect Spanish accessibility
  - **Mitigation**: Use multiple criteria (location, inclusion, language), document methodology

- **Phase Classification**:
  - **Risk**: Trial phases may be inconsistently reported
  - **Mitigation**: Implement standardization logic, focus on Phase III for reliability

### **Data Risks**
- **Disease Mapping**: 
  - **Risk**: Trial-disease mappings may be incorrect or incomplete
  - **Mitigation**: Cross-validate with known trial databases

- **Accessibility Scoring**:
  - **Risk**: Accessibility score methodology may not reflect real patient access
  - **Mitigation**: Include geographic, linguistic, and inclusion criteria factors

---

## 📝 **Summary**

This task implements a focused clinical trials accessibility analysis pipeline:

1. **🏭 Curator**: Processes clinical trial data and generates Spanish/EU accessibility metrics
2. **🔌 Client**: Provides clean data access following the established prevalence pattern
3. **📊 Statistics**: Delivers comprehensive trial accessibility analysis and outlier detection

The implementation follows the proven metabolic disease pattern while focusing specifically on clinical trial accessibility for Spanish and EU rare disease patients.

**Key Innovation**: Spanish and EU clinical trial accessibility analysis with Phase III focus and active recruitment tracking.

*This task creates clinical trial accessibility analysis capability that complements the existing prevalence infrastructure, enabling evidence-based clinical research participation planning for rare disease patients.* 