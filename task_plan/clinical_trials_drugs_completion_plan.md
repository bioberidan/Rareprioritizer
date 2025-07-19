# Executive Plan: Clinical Trials and Drugs Data Systems Completion

**Date**: January 2025  
**Priority**: High  
**Estimated Time**: 8-10 hours total  
**Type**: Data Curation + Client Infrastructure + Statistics Generation

---

## 📋 Executive Summary

This plan completes the clinical trials and drugs data systems by implementing the curation layer (04_curate), client infrastructure, and comprehensive statistics generation. Both systems currently have processed data available and need the final transformation to research-ready curated datasets.

### Current State Analysis

#### Clinical Trials System ✅ (Processed)
- **Processed Data**: `data/03_processed/clinical_trials/`
  - `diseases2clinical_trials.json` (941 lines, 20KB)
  - `clinical_trials2diseases.json` (9,518 lines, 299KB)  
  - `clinical_trials_index.json` (3.6MB)
  - `processing_summary.json` (604 lines)

- **Missing**: Curation layer, curated client, statistics

#### Drugs System ✅ (Processed)
- **Processed Data**: `data/03_processed/orpha/orphadata/orpha_drugs/`
  - `diseases2drugs.json` (5,962 lines, 121KB)
  - `drugs2diseases.json` (23,517 lines, 710KB)
  - `drug_index.json` (1.5MB)
  - `processing_summary.json` (270 lines)

- **Missing**: Curation layer, curated client, statistics

---

## 📊 Required Schemas Implementation

Before proceeding with curation, we need to implement Pydantic schemas for type-safe data validation:

### Clinical Trials Schema
**File**: `core/schemas/clinical_trials/clinical_trials.py`

**Required Models**:
```python
class ClinicalTrialInstance(BaseModel):
    """Model for individual clinical trial records"""
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT identifier")
    brief_title: str = Field(..., description="Brief trial title")
    official_title: str = Field(..., description="Official trial title")
    overall_status: str = Field(..., description="RECRUITING, ACTIVE_NOT_RECRUITING, etc.")
    study_type: str = Field(..., description="Interventional, Observational, etc.")
    phases: List[str] = Field(default_factory=list, description="Phase I, II, III, IV")
    interventions: List[str] = Field(default_factory=list, description="Drug, Device, etc.")
    enrollment: Optional[int] = Field(None, description="Target enrollment")
    locations: List[Dict[str, str]] = Field(default_factory=list, description="Study locations")
    diseases: List[Dict[str, str]] = Field(default_factory=list, description="Associated diseases")
    last_update: str = Field(..., description="Last update date")
    
class TrialMapping(BaseModel):
    """Model for disease-trial mappings"""
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    trials: List[str] = Field(default_factory=list, description="List of NCT IDs")
    eu_accessible_trials: List[str] = Field(default_factory=list, description="EU accessible trials")
    spanish_accessible_trials: List[str] = Field(default_factory=list, description="Spanish trials")
```

### Orpha Drugs Schema
**File**: `core/schemas/orpha/orphadata/orpha_drugs.py`

**Required Models**:
```python
class DrugInstance(BaseModel):
    """Model for individual drug records"""
    drug_id: str = Field(..., description="Drug identifier")
    drug_name: str = Field(..., description="Drug name")
    substance_id: Optional[str] = Field(None, description="Substance identifier")
    status: str = Field(..., description="Medicinal product, Tradename")
    regions: List[str] = Field(default_factory=list, description="US, EU, etc.")
    regulatory_urls: List[str] = Field(default_factory=list, description="Regulatory URLs")
    diseases: List[Dict[str, str]] = Field(default_factory=list, description="Associated diseases")
    
class DrugMapping(BaseModel):
    """Model for disease-drug mappings"""
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    drugs: List[str] = Field(default_factory=list, description="List of drug IDs")
    eu_tradename_drugs: List[str] = Field(default_factory=list, description="EU tradename drugs")
    usa_tradename_drugs: List[str] = Field(default_factory=list, description="USA tradename drugs")
    eu_medical_products: List[str] = Field(default_factory=list, description="EU medical products")
    usa_medical_products: List[str] = Field(default_factory=list, description="USA medical products")
```

---

## 🎯 Completion Objectives

### Phase 1: Clinical Trials Curation & Client
- **Curated JSON Files** (4 files)
- **CuratedClinicalTrialsClient** 
- **Statistics Module**

### Phase 2: Drugs Curation & Client  
- **Curated JSON Files** (7 files)
- **CuratedDrugsClient**
- **Statistics Module**

### Phase 3: Cross-System Analytics
- **Comparative Analysis**
- **Integration Statistics**
- **Research Gap Identification**

---

## 🏗️ Phase 1: Clinical Trials System Completion

### 1.1 Curation Script Implementation

#### **File**: `etl/04_curate/clinical_trials/curate_clinical_trials.py`

**Input Data Analysis** (from `data/03_processed/clinical_trials/`):
```json
// diseases2clinical_trials.json structure
{
  "79318": [
    {
      "nct_id": "NCT04324983",
      "brief_title": "PMM2-CDG Natural History Study",
      "overall_status": "RECRUITING",
      "study_type": "Observational",
      "phases": ["N/A"],
      "locations_spain": true,
      "enrollment": 50
    }
  ]
}

// clinical_trials_index.json structure  
{
  "NCT04324983": {
    "nct_id": "NCT04324983",
    "brief_title": "PMM2-CDG Natural History Study", 
    "official_title": "Natural History Study of PMM2-CDG",
    "overall_status": "RECRUITING",
    "locations": [
      {
        "facility": "Hospital Madrid",
        "city": "Madrid", 
        "country": "Spain"
      }
    ],
    "diseases": [{"orpha_code": "79318", "disease_name": "PMM2-CDG"}]
  }
}
```

**Curation Logic**:
```python
class ClinicalTrialsCurator:
    def __init__(self, input_dir="data/03_processed/clinical_trials", 
                 output_dir="data/04_curated/clinical_trials"):
        
    def curate_trials(self):
        # Load processed data
        diseases2trials = self.load_diseases2trials()
        trials_index = self.load_trials_index()
        
        # Process geographic filtering
        eu_countries = ["Spain", "France", "Germany", "Italy", ...]
        
        # Generate curated files
        return {
            "disease2eu_trial.json": self.filter_eu_trials(diseases2trials, trials_index),
            "disease2all_trials.json": self.format_all_trials(diseases2trials),
            "disease2spanish_trials.json": self.filter_spanish_trials(diseases2trials, trials_index),
            "clinicaltrial2name.json": self.extract_trial_names(trials_index)
        }
    
    def filter_eu_trials(self, diseases2trials, trials_index):
        """Filter trials accessible from EU countries"""
        eu_countries = ["Spain", "France", "Germany", "Italy", "Netherlands", 
                       "Belgium", "Austria", "Portugal", "Sweden", "Denmark"]
        
        eu_trials = {}
        for orpha_code, trials in diseases2trials.items():
            eu_trial_ids = []
            for trial in trials:
                nct_id = trial["nct_id"]
                trial_detail = trials_index.get(nct_id, {})
                locations = trial_detail.get("locations", [])
                
                # Check if trial has EU locations
                if any(loc.get("country") in eu_countries for loc in locations):
                    eu_trial_ids.append(nct_id)
            
            if eu_trial_ids:
                eu_trials[orpha_code] = eu_trial_ids
                
        return eu_trials
```

**Output Files**:

1. **`disease2eu_trial.json`** - EU-accessible trials per disease
```json
{
  "79318": ["NCT04324983", "NCT05123456"],
  "272": ["NCT03789012"],
  "646": ["NCT04567890", "NCT05234567", "NCT04890123"]
}
```

2. **`disease2all_trials.json`** - All trials per disease  
```json
{
  "79318": ["NCT04324983", "NCT05123456", "NCT06789012"],
  "272": ["NCT03789012", "NCT04456789"],
  "646": ["NCT04567890", "NCT05234567", "NCT04890123", "NCT05456789"]
}
```

3. **`disease2spanish_trials.json`** - Spanish-accessible trials
```json  
{
  "79318": ["NCT04324983"],
  "272": [],
  "646": ["NCT04567890"]
}
```

4. **`clinicaltrial2name.json`** - Trial ID to title mapping
```json
{
  "NCT04324983": "Natural History Study of PMM2-CDG",
  "NCT05123456": "Gene Therapy for PMM2-CDG",
  "NCT03789012": "Marfan Syndrome Clinical Trial",
  "NCT04567890": "Niemann-Pick Disease Treatment Study"
}
```

### 1.2 CuratedClinicalTrialsClient Implementation

#### **File**: `core/datastore/clinical_trials/curated_clinical_trials_client.py`

```python
class CuratedClinicalTrialsClient:
    """Client for accessing curated clinical trials data with lazy loading"""
    
    def __init__(self, data_dir="data/04_curated/clinical_trials"):
        self.data_dir = Path(data_dir)
        self._eu_trials = None
        self._all_trials = None
        self._spanish_trials = None
        self._trial_names = None
    
    @lru_cache(maxsize=1000)
    def get_eu_trials_for_disease(self, orpha_code: str) -> List[str]:
        """Get EU-accessible trials for disease"""
        
    @lru_cache(maxsize=1000) 
    def get_all_trials_for_disease(self, orpha_code: str) -> List[str]:
        """Get all trials for disease"""
        
    @lru_cache(maxsize=1000)
    def get_spanish_trials_for_disease(self, orpha_code: str) -> List[str]:
        """Get Spanish-accessible trials for disease"""
        
    def get_trial_name(self, nct_id: str) -> str:
        """Get trial title/name"""
        
    def get_diseases_with_eu_trials(self) -> List[str]:
        """Get diseases that have EU-accessible trials"""
        
    def get_diseases_with_spanish_trials(self) -> List[str]:
        """Get diseases that have Spanish-accessible trials"""
        
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics"""
        return {
            "total_diseases_with_trials": len(self.load_all_trials_data()),
            "diseases_with_eu_trials": len(self.get_diseases_with_eu_trials()),
            "diseases_with_spanish_trials": len(self.get_diseases_with_spanish_trials()),
            "total_trials": sum(len(trials) for trials in self.load_all_trials_data().values()),
            "total_eu_trials": sum(len(trials) for trials in self.load_eu_trials_data().values()),
            "total_spanish_trials": sum(len(trials) for trials in self.load_spanish_trials_data().values())
        }
```

### 1.3 Clinical Trials Statistics Module

#### **File**: `etl/05_stats/clinical_trials/clinical_trials_stats.py`

**Generated Analysis**:
1. **Distribution Analysis**: Trials per disease distribution per json file (NO data slicing allowed - use complete datasets)
2. **Top 15 Diseases**: By total trials, EU trials, Spanish trials (full analysis, no [:50] shortcuts)
3. **Top 15 Trials**: By disease coverage (multi-disease trials)
4. **Outlier Analysis**: IQR method for identifying outlier diseases with excessive trials
5. **Geographic Analysis**: EU vs Spanish accessibility 
6. **Summary Statistics**: Mean, median, mode for trial distributions

**IMPORTANT**: All statistics must use complete data - NO data slicing tricks like [:50] allowed.

**Visualizations** (saved to `results/etl/subset_of_disease_instances/metabolic/clinical_trials/`):
- `trial_distribution_analysis.png`
- `top_diseases_by_trials.png`
- `top_trials_by_diseases.png`
- `outlier_analysis_iqr.png`
- `geographic_accessibility.png`
- `summary_dashboard.png`

**CRITICAL**: Existing files in this directory must NOT be deleted or overwritten.

**Statistics JSON** (`clinical_trials_statistics.json`):
```json
{
  "basic_statistics": {
    "total_diseases": 665,
    "diseases_with_trials": 73,
    "coverage_percentage": 10.98,
    "total_unique_trials": 317,
    "average_trials_per_disease": 4.34
  },
  "geographic_analysis": {
    "diseases_with_eu_trials": 45,
    "diseases_with_spanish_trials": 23,
    "eu_coverage_percentage": 6.77,
    "spanish_coverage_percentage": 3.46
  },
  "distribution_analysis": {
    "mean_trials": 4.34,
    "median_trials": 2.0,
    "std_trials": 6.12,
    "min_trials": 1,
    "max_trials": 45
  },
  "outlier_analysis": {
    "iqr_outliers": ["272", "646", "324"],
    "outlier_threshold": 12.5,
    "total_outliers": 3
  },
  "top_diseases": {
    "by_total_trials": [
      {"orpha_code": "272", "disease_name": "Marfan syndrome", "trial_count": 45},
      {"orpha_code": "646", "disease_name": "Niemann-Pick disease", "trial_count": 23}
    ],
    "by_eu_trials": [...],
    "by_spanish_trials": [...]
  }
}
```

---

## 🏗️ Phase 2: Drugs System Completion

### 2.1 Curation Script Implementation

#### **File**: `etl/04_curate/orpha/orphadata/curate_orpha_drugs.py`

**Input Data Analysis** (from `data/03_processed/orpha/orphadata/orpha_drugs/`):
```json
// diseases2drugs.json structure
{
  "100924": {
    "disease_name": "Porphyria due to ALA dehydratase deficiency",
    "orpha_code": "100924", 
    "drugs_count": 9,
    "drugs": ["drug_0", "480914", "drug_2", "689505"]
  }
}

// drugs2diseases.json structure
{
  "480914": {
    "drug_name": "Givosiran",
    "substance_id": "480914",
    "status": "Medicinal product", 
    "regions": ["US"],
    "diseases": [
      {"orpha_code": "100924", "disease_name": "Porphyria due to ALA dehydratase deficiency"}
    ]
  }
}
```

**Curation Logic**:
```python
class OrphaDrugsCurator:
    def __init__(self, input_dir="data/03_processed/orpha/orphadata/orpha_drugs",
                 output_dir="data/04_curated/orpha/orphadata"):
                 
    def curate_drugs(self):
        diseases2drugs = self.load_diseases2drugs()
        drugs2diseases = self.load_drugs2diseases()
        
        return {
            "disease2eu_tradename_drugs.json": self.filter_tradename_drugs(diseases2drugs, drugs2diseases, "EU"),
            "disease2all_tradename_drugs.json": self.filter_tradename_drugs(diseases2drugs, drugs2diseases, "ALL"),
            "disease2usa_tradename_drugs.json": self.filter_tradename_drugs(diseases2drugs, drugs2diseases, "US"),
            "disease2eu_medical_product_drugs.json": self.filter_medical_products(diseases2drugs, drugs2diseases, "EU"),
            "disease2all_medical_product_drugs.json": self.filter_medical_products(diseases2drugs, drugs2diseases, "ALL"),
            "disease2usa_medical_product_drugs.json": self.filter_medical_products(diseases2drugs, drugs2diseases, "US"),
            "drug2name.json": self.extract_drug_names(drugs2diseases)
        }
    
    def filter_tradename_drugs(self, diseases2drugs, drugs2diseases, region):
        """Filter drugs by tradename status and region"""
        result = {}
        
        for orpha_code, disease_data in diseases2drugs.items():
            drug_ids = []
            
            for drug_id in disease_data["drugs"]:
                drug_info = drugs2diseases.get(drug_id, {})
                
                # Check if it's a tradename
                if drug_info.get("status") == "Tradename":
                    # Check region compatibility
                    drug_regions = drug_info.get("regions", [])
                    
                    if region == "ALL" or region in drug_regions:
                        drug_ids.append(drug_id)
            
            if drug_ids:
                result[orpha_code] = drug_ids
                
        return result
    
    def filter_medical_products(self, diseases2drugs, drugs2diseases, region):
        """Filter drugs by medicinal product status and region"""
        # Similar logic but filter by status == "Medicinal product"
        
    def extract_drug_names(self, drugs2diseases):
        """Extract drug ID to name mapping"""
        return {
            drug_id: drug_data.get("drug_name", f"Unknown_{drug_id}")
            for drug_id, drug_data in drugs2diseases.items()
        }
```

**Output Files**:

1. **`disease2eu_tradename_drugs.json`** - EU tradename drugs per disease
```json
{
  "100924": ["480914", "689505"],
  "101109": ["686840", "635854"],
  "111": ["556445", "588874"]
}
```

2. **`disease2all_tradename_drugs.json`** - All tradename drugs per disease
```json
{
  "100924": ["480914", "689505", "24990"],
  "101109": ["686840", "635854", "628292"],
  "111": ["556445", "588874", "689505"]
}
```

3. **`disease2usa_tradename_drugs.json`** - USA tradename drugs per disease
```json
{
  "100924": ["480914"],
  "101109": ["628292"],
  "111": ["689505"]
}
```

4. **`disease2eu_medical_product_drugs.json`** - EU medical products per disease
```json
{
  "100924": ["drug_0", "drug_2"],
  "101109": ["479413", "531922"],
  "111": ["drug_27"]
}
```

5. **`disease2all_medical_product_drugs.json`** - All medical products per disease
```json
{
  "100924": ["drug_0", "drug_2", "drug_3"],
  "101109": ["479413", "531922", "686840"],
  "111": ["drug_27", "556445"]
}
```

6. **`disease2usa_medical_product_drugs.json`** - USA medical products per disease
```json
{
  "100924": ["drug_3"],
  "101109": ["686840"],
  "111": ["556445"]
}
```

7. **`drug2name.json`** - Drug ID to name mapping
```json
{
  "480914": "Givosiran",
  "689505": "Burixafor",
  "24990": "Hemin",
  "686840": "Befiradol fumarate",
  "635854": "Rovatirelin"
}
```

### 2.2 CuratedDrugsClient Implementation

#### **File**: `core/datastore/orpha/orphadata/curated_drugs_client.py`

```python
class CuratedDrugsClient:
    """Client for accessing curated drugs data with lazy loading"""
    
    def __init__(self, data_dir="data/04_curated/orpha/orphadata"):
        self.data_dir = Path(data_dir)
        self._eu_tradename_drugs = None
        self._all_tradename_drugs = None
        self._usa_tradename_drugs = None
        self._eu_medical_products = None
        self._all_medical_products = None
        self._usa_medical_products = None
        self._drug_names = None
    
    @lru_cache(maxsize=1000)
    def get_eu_tradename_drugs_for_disease(self, orpha_code: str) -> List[str]:
        """Get EU tradename drugs for disease"""
        
    @lru_cache(maxsize=1000)
    def get_usa_medical_products_for_disease(self, orpha_code: str) -> List[str]:
        """Get USA medical products for disease"""
        
    def get_drug_name(self, drug_id: str) -> str:
        """Get drug name from drug ID"""
        
    def get_diseases_with_eu_drugs(self) -> List[str]:
        """Get diseases that have EU-accessible drugs"""
        
    def get_diseases_with_usa_drugs(self) -> List[str]:
        """Get diseases that have USA-accessible drugs"""
        
    def get_statistics(self) -> Dict:
        """Get comprehensive drug statistics"""
        return {
            "total_diseases_with_drugs": len(self.load_all_tradename_drugs()),
            "diseases_with_eu_tradenames": len(self.get_diseases_with_eu_drugs()),
            "diseases_with_usa_tradenames": len(self.get_diseases_with_usa_drugs()),
            "total_tradename_drugs": len(self.load_drug_names()),
            "total_medical_products": len([d for d in self.load_drug_names() if "product" in d.lower()])
        }
```

### 2.3 Drugs Statistics Module

#### **File**: `etl/05_stats/orpha/orphadata/orpha_drugs_stats.py`

**Generated Analysis**:
1. **Distribution Analysis**: Drugs per disease distribution (by type and region) (NO data slicing allowed - use complete datasets)
2. **Top 15 Diseases**: By total drugs, EU drugs, USA drugs, medical products, tradenames (full analysis, no [:50] shortcuts)
3. **Top 15 Drugs**: By disease coverage (multi-disease drugs)
4. **Outlier Analysis**: IQR method for identifying outlier diseases with excessive drugs
5. **Regional Analysis**: EU vs USA drug availability
6. **Drug Type Analysis**: Medical products vs tradenames
7. **Summary Statistics**: Mean, median, mode for drug distributions

**IMPORTANT**: All statistics must use complete data - NO data slicing tricks like [:50] allowed.

**Visualizations** (saved to `results/etl/subset_of_disease_instances/metabolic/orpha/orphadata/orpha_drugs/`):
- `drug_distribution_analysis.png`
- `top_diseases_by_drugs.png`
- `top_drugs_by_diseases.png`
- `outlier_analysis_iqr.png`
- `regional_availability.png`
- `drug_type_analysis.png`
- `summary_dashboard.png`

**CRITICAL**: Existing files in this directory must NOT be deleted or overwritten.

---


## 📁 Complete File Structure

### Curation Layer (04_curate)
```
data/04_curated/
├── clinical_trials/
│   ├── disease2eu_trial.json
│   ├── disease2all_trials.json
│   ├── disease2spanish_trials.json
│   └── clinicaltrial2name.json
└── orpha/orphadata/
    ├── disease2eu_tradename_drugs.json
    ├── disease2all_tradename_drugs.json
    ├── disease2usa_tradename_drugs.json
    ├── disease2eu_medical_product_drugs.json
    ├── disease2all_medical_product_drugs.json
    ├── disease2usa_medical_product_drugs.json
    └── drug2name.json
```

### Schemas Infrastructure
```
core/schemas/
├── clinical_trials/
│   └── clinical_trials.py                 # Clinical trials data models
└── orpha/orphadata/
    └── orpha_drugs.py                     # Drugs data models (update existing)
```

### Client Infrastructure
```
core/datastore/
├── clinical_trials/
│   └── curated_clinical_trials_client.py
└── orpha/orphadata/
    └── curated_drugs_client.py
```

### Statistics Modules
```
etl/05_stats/
├── clinical_trials/
│   └── clinical_trials_stats.py
├── orpha/orphadata/
│   └── orpha_drugs_stats.py

```

### Results Output
```
results/etl/subset_of_disease_instances/metabolic/
├── clinical_trials/
│   ├── clinical_trials_statistics.json
│   ├── trial_distribution_analysis.png
│   ├── top_diseases_by_trials.png
│   ├── outlier_analysis_iqr.png
│   └── geographic_accessibility.png
└── orpha/orphadata/orpha_drugs/
    ├── orpha_drugs_statistics.json
    ├── drug_distribution_analysis.png
    ├── top_diseases_by_drugs.png
    ├── outlier_analysis_iqr.png
    └── regional_availability.png
```

**IMPORTANT**: These directories contain existing data that must be preserved. New files should be added carefully without overwriting existing analysis.

---

## 🚀 Implementation Timeline

### Phase 0: Schemas Implementation (Day 1)
- **Day 1 Morning**: Implement `core/schemas/clinical_trials/clinical_trials.py` 
- **Day 1 Afternoon**: Update `core/schemas/orpha/orphadata/orpha_drugs.py` with additional models

### Week 1: Clinical Trials Completion (Days 2-6)
- **Day 2-3**: Implement `curate_clinical_trials.py` and generate JSON files
- **Day 4**: Implement `CuratedClinicalTrialsClient` with schema validation
- **Day 5-6**: Implement `clinical_trials_stats.py` and generate visualizations (NO data slicing, preserve existing files)

### Week 2: Drugs Completion (Days 7-11)
- **Day 7-8**: Implement `curate_orpha_drugs.py` and generate JSON files
- **Day 9**: Implement `CuratedDrugsClient` with schema validation
- **Day 10-11**: Implement `orpha_drugs_stats.py` and generate visualizations (NO data slicing, preserve existing files)


---

## 🔍 Input/Output Examples

### Clinical Trials Input Example
**From**: `data/03_processed/clinical_trials/diseases2clinical_trials.json`
```json
{
  "79318": [
    {
      "nct_id": "NCT04324983",
      "brief_title": "PMM2-CDG Natural History Study",
      "overall_status": "RECRUITING", 
      "locations_spain": true
    }
  ]
}
```

### Clinical Trials Output Example
**To**: `data/04_curated/clinical_trials/disease2spanish_trials.json`
```json
{
  "79318": ["NCT04324983"]
}
```

### Drugs Input Example
**From**: `data/03_processed/orpha/orphadata/orpha_drugs/drugs2diseases.json`
```json
{
  "480914": {
    "drug_name": "Givosiran",
    "status": "Medicinal product",
    "regions": ["US"],
    "diseases": [{"orpha_code": "100924"}]
  }
}
```

### Drugs Output Example
**To**: `data/04_curated/orpha/orphadata/disease2usa_medical_product_drugs.json`
```json
{
  "100924": ["480914"]
}
```

---






---

## ⚠️ CRITICAL IMPLEMENTATION REQUIREMENTS

### Data Integrity Requirements
1. **NO Data Slicing**: Statistics and analysis must use complete datasets
   - ❌ FORBIDDEN: `data[:50]`, `data.head(100)`, `data.sample(n=200)`
   - ✅ REQUIRED: Full dataset analysis for all statistics

2. **Preserve Existing Files**: 
   - ❌ DO NOT delete or overwrite existing files in results directories
   - ✅ Add new files with descriptive names to avoid conflicts
   - ✅ Check for existing files before writing

3. **Complete Analysis**: 
   - ✅ Top 15 analyses must examine ALL data, not just a subset
   - ✅ Distribution analyses must include ALL diseases with data
   - ✅ Outlier detection must process the complete dataset

4. **Schema Compliance**:
   - ✅ All data must validate against Pydantic schemas
   - ✅ No raw dictionary usage without validation
   - ✅ Type safety enforced throughout the pipeline

### Output Directory Preservation
- **Clinical Trials**: `results/etl/subset_of_disease_instances/metabolic/clinical_trials/` - contains existing data
- **Drugs**: `results/etl/subset_of_disease_instances/metabolic/orpha/orphadata/orpha_drugs/` - contains existing data

### Quality Assurance Checklist
- [ ] Schemas implemented and tested
- [ ] All curation scripts use complete datasets 
- [ ] Clients validate data with schemas
- [ ] Statistics use full data (no slicing)
- [ ] Existing files preserved
- [ ] All 4 clinical trials JSON files generated
- [ ] All 7 drugs JSON files generated
- [ ] IQR outlier analysis on complete data
- [ ] Top 15 analyses on complete data

---

This comprehensive plan provides the complete roadmap for finishing both data systems with high-quality curated data, efficient client infrastructure, and comprehensive analytics suitable for research prioritization decisions. 