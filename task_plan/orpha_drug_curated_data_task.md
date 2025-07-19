# Task Plan: Orpha Drug Curated Data Analysis

**Date**: December 2024  
**Priority**: High  
**Estimated Time**: 2-2.5 hours  
**Type**: Curated Data Processing + Client Infrastructure + Statistics

---

## 📋 **Task Overview**

### **Three-Step Process**
1. **🏭 Curator Script**: Process existing drug data → Generate curated drug availability files
2. **🔌 Client Infrastructure**: Create CuratedDrugClient for data access
3. **📊 Statistics Module**: Generate analysis and reports for drug availability

### **Business Context**
- **Input**: Processed drug data in `data/03_processed/orpha/orphadata/orpha_drugs/`
- **Output**: Disease-focused drug availability metrics with regional focus
- **Data Source**: 665 diseases processed, 407 with drugs, 885 unique drugs
- **Regional Coverage**: US, EU, and other regions from drug database
- **Data Flow**: Processed Drug Data → Disease-Centric Aggregation → Regional Analysis → Statistics

---

## 🔍 **Available Input Data Analysis**

### **Actual Data Structure** (No Guessing!)
Based on `data/03_processed/orpha/orphadata/orpha_drugs/`:

#### **processing_summary.json**
- **665 diseases processed** (matches metabolic diseases count)
- **407 diseases with drugs** (61.2% coverage)
- **258 diseases without drugs** (listed in empty_diseases array)
- **885 unique drugs** in database
- **Processing runs**: run1 (402 diseases), run2 (5 diseases)

#### **diseases2drugs.json** (5,962 lines)
Structure per disease:
```json
{
  "100924": {
    "disease_name": "Porphyria due to ALA dehydratase deficiency",
    "orpha_code": "100924",
    "drugs_count": 9,
    "last_processed_run": 1,
    "drugs": ["drug_0", "480914", "drug_2", ...]
  }
}
```

#### **drugs2diseases.json** (23,517 lines) 
Structure per drug:
```json
{
  "480914": {
    "drug_name": "Givosiran",
    "substance_id": "480914",
    "status": "Medicinal product",
    "regions": ["US"],
    "diseases": [
      {"orpha_code": "100924", "disease_name": "..."},
      {"orpha_code": "79273", "disease_name": "..."}
    ]
  }
}
```

#### **drug_index.json** (36,165 lines)
Comprehensive drug database with:
- Drug names, substance IDs, regulatory IDs
- **Regions**: "US", "EU", etc.
- **Status**: "Medicinal product", "Tradename"
- Regulatory URLs, substance URLs
- Disease associations via ORPHA codes

---

## 🏭 **Phase A: Curator Script - Drug Data Processing**

### **OrphaDrugCurator Implementation**
- **File**: `etl/04_curate/orpha/orphadata/curate_orpha_drugs.py`
- **Class**: `OrphaDrugCurator`
- **Input**: Existing processed data in `data/03_processed/orpha/orphadata/orpha_drugs/`
- **Processing**: Aggregate and transform into disease-centric metrics

### **Processing Workflow**
1. **Load Processed Data**: Read existing diseases2drugs.json and drugs2diseases.json
2. **Regional Analysis**: Extract US and EU drug availability from regions data
3. **Drug Classification**: Count drugs by status (Medicinal product vs. Tradename)
4. **Coverage Calculation**: Calculate drug availability metrics per disease
5. **Aggregation**: Generate disease-centric JSON files

### **Key Processing Logic**
```python
# For each disease, analyze:
- Total drug count (from diseases2drugs.json)
- US drugs count (filter drugs by "US" in regions)
- EU drugs count (filter drugs by "EU" in regions) 
- Medicinal products count (status == "Medicinal product")
- Tradenames count (status == "Tradename")
```

---

## 📊 **Generated JSON Files with Examples**

### **File 1: `orpha_diseases2total_drug_count.json`**
**Description**: Total number of drugs per disease (from existing drugs_count)
```json
{
  "100924": 9,
  "101109": 13,
  "101330": 3,
  "104": 9,
  "111": 13
}
```

### **File 2: `orpha_diseases2us_drug_count.json`**
**Description**: Number of US-available drugs per disease
```json
{
  "100924": 7,
  "101109": 8,
  "101330": 2,
  "104": 6,
  "111": 9
}
```

### **File 3: `orpha_diseases2eu_drug_count.json`**
**Description**: Number of EU-available drugs per disease
```json
{
  "100924": 2,
  "101109": 4,
  "101330": 1,
  "104": 3,
  "111": 4
}
```

### **File 4: `orpha_diseases2medicinal_product_count.json`**
**Description**: Number of approved medicinal products per disease
```json
{
  "100924": 6,
  "101109": 9,
  "101330": 2,
  "104": 7,
  "111": 8
}
```

### **File 5: `orpha_diseases2tradename_count.json`**
**Description**: Number of tradename drugs per disease
```json
{
  "100924": 3,
  "101109": 4,
  "101330": 1,
  "104": 2,
  "111": 5
}
```

### **File 6: `orpha_diseases2drug_list.json`**
**Description**: Disease ID to list of drug IDs (like user requested: "1987: [drug1, drug2, drug3...]")
```json
{
  "100924": ["drug_0", "480914", "drug_2", "drug_3", "689505", "24990"],
  "101109": ["686840", "635854", "628292", "479413", "531922"],
  "101330": ["66148", "drug_20", "24990"],
  "104": ["drug_21", "628268", "260395", "73656"],
  "111": ["556445", "drug_27", "588874", "689505"]
}
```

### **File 7: `orpha_drugs2drug_names.json`**
**Description**: Drug ID to drug name mapping
```json
{
  "480914": "Givosiran",
  "689505": "Burixafor", 
  "24990": "Hemin",
  "686840": "Befiradol fumarate",
  "635854": "Rovatirelin"
}
```

### **File 8: `orpha_diseases2disease_names.json`**
**Description**: Disease ID to disease name mapping
```json
{
  "100924": "Porphyria due to ALA dehydratase deficiency",
  "101109": "Spinocerebellar ataxia type 28",
  "101330": "Porphyria cutanea tarda",
  "104": "Leber hereditary optic neuropathy",
  "111": "Barth syndrome"
}
```

---

## 🔌 **Phase B: Client Infrastructure - Data Access Layer**

### **CuratedDrugClient Design**

#### **File Location**
```
core/datastore/orpha_drug_client.py
```

#### **Class Structure**
```python
class CuratedDrugClient:
    """Client for accessing curated Orpha drug availability data"""
    
    def __init__(self, 
                 orphadata_dir: str = "data/04_curated/orpha/orphadata"):
        self.orphadata_dir = Path(orphadata_dir)
        self._total_drug_data = None
        self._us_drug_data = None
                 self._eu_drug_data = None
         self._medicinal_product_data = None
         self._tradename_data = None
         self._drug_list_data = None
         self._drug_names_data = None
         self._disease_names_data = None
```

#### **Core Data Loading Methods**
```python
    def load_total_drug_data(self) -> Dict[int, int]:
        """Load total drug count data"""
        
    def load_us_drug_data(self) -> Dict[int, int]:
        """Load US drug count data"""
        
    def load_eu_drug_data(self) -> Dict[int, int]:
        """Load EU drug count data"""
        
    def load_medicinal_product_data(self) -> Dict[int, int]:
        """Load medicinal product counts"""
        
         def load_tradename_data(self) -> Dict[int, int]:
         """Load tradename counts"""
         
     def load_drug_list_data(self) -> Dict[int, List[str]]:
         """Load disease to drug list mappings"""
         
     def load_drug_names_data(self) -> Dict[str, str]:
         """Load drug ID to drug name mappings"""
         
     def load_disease_names_data(self) -> Dict[int, str]:
         """Load disease ID to disease name mappings"""
```

#### **Individual Disease Access Methods**
```python
    def get_total_drug_count(self, orpha_code: int) -> int:
        """Get total drug count for specific disease"""
        
    def get_us_drug_count(self, orpha_code: int) -> int:
        """Get US drug count for specific disease"""
        
    def get_eu_drug_count(self, orpha_code: int) -> int:
        """Get EU drug count for specific disease"""
        
    def get_medicinal_product_count(self, orpha_code: int) -> int:
        """Get medicinal product count for specific disease"""
        
         def get_tradename_count(self, orpha_code: int) -> int:
         """Get tradename count for specific disease"""
         
     def get_drug_list(self, orpha_code: int) -> List[str]:
         """Get list of drug IDs for specific disease"""
         
     def get_drug_name(self, drug_id: str) -> str:
         """Get drug name for specific drug ID"""
         
     def get_disease_name(self, orpha_code: int) -> str:
         """Get disease name for specific disease ID"""
```

#### **Bulk Data Access Methods**
```python
    def get_all_total_drug_counts(self) -> Dict[int, int]:
        """Get all total drug counts"""
        
    def get_all_us_drug_counts(self) -> Dict[int, int]:
        """Get all US drug counts"""
        
    def get_all_eu_drug_counts(self) -> Dict[int, int]:
        """Get all EU drug counts"""
        
    def get_all_medicinal_product_counts(self) -> Dict[int, int]:
        """Get all medicinal product counts"""
        
         def get_all_tradename_counts(self) -> Dict[int, int]:
         """Get all tradename counts"""
         
     def get_all_drug_lists(self) -> Dict[int, List[str]]:
         """Get all disease to drug list mappings"""
         
     def get_all_drug_names(self) -> Dict[str, str]:
         """Get all drug ID to drug name mappings"""
         
     def get_all_disease_names(self) -> Dict[int, str]:
         """Get all disease ID to disease name mappings"""
```

#### **Analysis Methods**
```python
    def get_diseases_with_drugs(self) -> List[int]:
        """Get diseases that have drugs available (407 diseases)"""
        
    def get_diseases_without_drugs(self) -> List[int]:
        """Get diseases with no drugs available (258 diseases)"""
        
    def get_diseases_with_us_drugs(self) -> List[int]:
        """Get diseases with US-available drugs"""
        
    def get_diseases_with_eu_drugs(self) -> List[int]:
        """Get diseases with EU-available drugs"""
        
    def get_diseases_with_medicinal_products(self) -> List[int]:
        """Get diseases with approved medicinal products"""
        
    def get_us_vs_eu_drug_gap(self) -> Dict[int, int]:
        """Calculate drug availability gap between US and EU"""
        
    def get_drug_coverage_summary(self) -> Dict:
        """Get comprehensive coverage statistics"""
```

#### **Enhanced Analysis Methods**
```python
    def get_high_drug_count_diseases(self, min_drugs: int = 5) -> List[int]:
        """Get diseases with high drug availability"""
        
    def get_diseases_by_us_drug_count(self, min_drugs: int = 1) -> List[int]:
        """Get diseases with minimum US drug count"""
        
    def get_diseases_by_drug_range(self, min_drugs: int, max_drugs: int) -> List[int]:
        """Get diseases within drug count range"""
        
    def get_medicinal_vs_tradename_analysis(self) -> Dict:
        """Analyze medicinal products vs tradenames distribution"""
```

---

## 📊 **Phase C: Statistics Module - Analysis & Reporting**

### **OrphaDrugStatsAnalyzer**

#### **File Location**
```
etl/05_stats/orpha_drugs/orpha_drug_stats.py
```

#### **Analysis Categories**

##### **Coverage Analysis**
- **665 total diseases** processed
- **407 diseases with drugs** (61.2% coverage)
- **258 diseases without drugs** (38.8% no coverage)
- **885 unique drugs** in database
- US vs. EU drug availability coverage

##### **Drug Distribution Analysis**
- Descriptive statistics for drug counts per disease
- Total drugs vs. US drugs vs. EU drugs comparison
- Medicinal products vs. tradenames distribution
- High-availability vs. low-availability disease analysis

##### **Regional Analysis**
- US drug availability per disease
- EU drug availability per disease
- US-EU drug availability gap analysis
- Regional coverage patterns

##### **Drug Type Analysis**
- Medicinal products vs. tradenames by disease
- Approved drugs vs. branded products
- Regional approval patterns
- Drug type distribution insights

#### **Outlier Detection**
Based on real data patterns:
- Diseases with unusually high drug counts (outliers in 885 drugs)
- Diseases with disproportionate US vs. EU availability
- Diseases with unusual medicinal product vs. tradename ratios

---

## 📋 **Implementation Steps**

### **Phase A: Curator Script (60 minutes)**
- [ ] **Load existing processed data** from diseases2drugs.json and drugs2diseases.json
- [ ] **Implement regional filtering** to count US and EU drugs per disease
- [ ] **Add drug type classification** to count medicinal products vs tradenames
- [ ] **Generate 8 structured JSON files** (5 count files + 3 mapping files)
- [ ] **Validate against known totals** (407 diseases with drugs, 258 without)
- [ ] **Add comprehensive logging** for processing results

### **Phase B: Client Infrastructure (45 minutes)**
- [ ] **Create CuratedDrugClient** following prevalence pattern
- [ ] **Implement lazy loading** for all 5 data types
- [ ] **Add individual disease access methods** for each metric
- [ ] **Implement bulk operations** for efficient data retrieval
- [ ] **Add analysis methods** for coverage and gap analysis
- [ ] **Test client** with known data (407 diseases with drugs)

### **Phase C: Statistics Module (30 minutes)**
- [ ] **Create OrphaDrugStatsAnalyzer** 
- [ ] **Implement coverage analysis** (61.2% with drugs, 38.8% without)
- [ ] **Add US vs. EU comparative analysis**
- [ ] **Create outlier detection** for drug availability patterns
- [ ] **Generate JSON reports and visualizations**
- [ ] **Test integration** with CuratedDrugClient

---

## 🎯 **Expected Outcomes**

### **Quantitative Results** (Based on Real Data)
- **Total diseases**: 665 (matching metabolic diseases)
- **Diseases with drugs**: 407 (61.2% coverage)
- **Diseases without drugs**: 258 (38.8% no coverage)
- **Unique drugs**: 885 in database
- **Regional coverage**: US vs. EU availability analysis

### **Data Products Created**
- **8 Curated JSON Files**: 5 count files + 3 mapping files (drug lists, drug names, disease names)
- **Data Access Layer**: CuratedDrugClient for efficient data retrieval
- **Statistical Reports**: Comprehensive drug availability analysis
- **Visualizations**: Coverage analysis and regional comparison charts

### **Healthcare Planning Value**
- **Drug Availability Assessment**: Direct counts of available drugs per disease
- **US vs. EU Comparison**: Understanding of regional drug access differences
- **Therapeutic Gaps**: Identification of 258 diseases without drug options
- **Drug Type Analysis**: Medicinal products vs. tradenames availability
- **Coverage Insights**: Prioritization based on 61.2% current coverage

---

## 📁 **File Structure**

### **Curated Data Output**
```
data/04_curated/orpha/orphadata/
├── orpha_diseases2total_drug_count.json
├── orpha_diseases2us_drug_count.json
├── orpha_diseases2eu_drug_count.json
├── orpha_diseases2medicinal_product_count.json
├── orpha_diseases2tradename_count.json
├── orpha_diseases2drug_list.json
├── orpha_drugs2drug_names.json
└── orpha_diseases2disease_names.json
```

### **Infrastructure Files**
```
# Phase A: Curator Script
etl/04_curate/orpha/orphadata/
└── curate_orpha_drugs.py

# Phase B: Client Infrastructure  
core/datastore/
└── orpha_drug_client.py

# Phase C: Statistics Module
etl/05_stats/orpha_drugs/
├── __init__.py
└── orpha_drug_stats.py
```

### **Results Output**
```
results/etl/orpha_drugs/
├── orpha_drug_statistics.json
├── orpha_drug_coverage_analysis.png
├── us_vs_eu_drug_comparison.png
└── orpha_drug_outlier_analysis.png
```

---

## 🔍 **Quality Assurance & Validation**

### **Curator Script Validation**
- [ ] **Data Completeness**: All 665 diseases processed correctly
- [ ] **Coverage Accuracy**: 407 diseases with drugs, 258 without drugs
- [ ] **Regional Filtering**: Correct US and EU drug counts per disease
- [ ] **Drug Type Classification**: Accurate medicinal product vs. tradename counts
- [ ] **JSON Format**: Correct orphacode:value structure with integer keys
- [ ] **Total Validation**: Sum validation against 885 unique drugs

### **Client Infrastructure Validation**
- [ ] **Data Consistency**: Matches processed data exactly
- [ ] **Coverage Verification**: 61.2% coverage (407/665 diseases)
- [ ] **Regional Analysis**: Accurate US vs. EU comparisons
- [ ] **Bulk Operations**: Efficient retrieval of all data
- [ ] **Error Handling**: Graceful handling of missing data
- [ ] **Performance**: Fast lookup operations

### **Statistics Module Validation**
- [ ] **Coverage Analysis**: Accurate 61.2% vs 38.8% reporting
- [ ] **Distribution Analysis**: Correct statistical calculations
- [ ] **Regional Comparison**: Valid US vs. EU drug analysis
- [ ] **Outlier Detection**: Meaningful drug availability outliers
- [ ] **Integration**: Seamless work with CuratedDrugClient

---

## ⏱️ **Implementation Timeline**

### **Phase A: Curator Script (75 minutes)**
- Data loading and validation: 15 minutes
- Regional and type filtering: 25 minutes
- Mapping files generation (drug lists, names): 20 minutes
- Output generation & testing: 15 minutes

### **Phase B: Client Infrastructure (45 minutes)**
- CuratedDrugClient creation: 30 minutes
- Testing and validation: 15 minutes

### **Phase C: Statistics Module (30 minutes)**
- OrphaDrugStatsAnalyzer implementation: 20 minutes
- Output generation & testing: 10 minutes

**Total Estimated Time**: 2.5 hours

---

## 🚨 **Implementation Considerations**

### **Data Validation**
- **Source Accuracy**: Processed data from existing pipeline is reliable
- **Coverage Verification**: 407 diseases with drugs vs. 258 without
- **Regional Data Quality**: US and EU regions clearly identified in source
- **Drug Classification**: Medicinal product vs. tradename status available

### **Performance Optimization**
- **Large Dataset**: 885 drugs across 665 diseases requires efficient processing
- **Memory Management**: 23,517 lines in drugs2diseases.json needs careful handling
- **Caching Strategy**: Lazy loading for 5 different metric types

### **Success Criteria**
- **100% Data Consistency**: Perfect match with source processed data
- **Accurate Coverage**: Exact 61.2% coverage (407/665 diseases)
- **Regional Accuracy**: Correct US vs. EU drug availability metrics
- **Type Classification**: Accurate medicinal product vs. tradename counts

---

## 📝 **Summary**

This task implements a focused drug availability analysis pipeline based on **real processed data**:

1. **🏭 Curator**: Transforms existing processed drug data into disease-centric metrics
2. **🔌 Client**: Provides clean data access following the established prevalence pattern
3. **📊 Statistics**: Delivers comprehensive drug availability analysis with regional focus

The implementation leverages **actual data structure** (665 diseases, 407 with drugs, 885 unique drugs) rather than assumptions, ensuring accuracy and reliability.

**Key Innovation**: Disease-centric drug availability analysis with US vs. EU regional focus and medicinal product vs. tradename classification.

*This task creates drug availability analysis capability based on real Orphanet data, enabling evidence-based therapeutic access planning for rare disease patients.* 