# Task Plan: Birth-to-Point Prevalence Fallback Implementation

## 📋 **Overview**

This task implements a conservative birth-to-point prevalence estimation fallback for diseases where no point prevalence data is available after all existing fallback methods have been exhausted.

## 🎯 **Objective**

Add a final fallback mechanism that estimates point prevalence from birth prevalence data using a conservative one-step mapping, reducing the number of diseases marked as "Unknown" in the curated dataset.

## 📊 **Current Fallback System Analysis**

### **Existing Algorithm in `select_best_prevalence_class()`**

The current system follows this priority hierarchy:

```python
def select_best_prevalence_class(self, disease_data: Dict) -> Optional[str]:
    """
    Current fallback priorities:
    1. Point prevalence from most_reliable_prevalence
    2. Worldwide records with best reliability  
    3. Regional records with best reliability
    4. Return None → "Unknown"
    """
    
    # Priority 1: Point prevalence
    most_reliable = disease_data.get('most_reliable_prevalence')
    if most_reliable and most_reliable.get('prevalence_type') == 'Point prevalence':
        self.stats['selection_method_counts']['point_prevalence'] += 1
        return most_reliable.get('prevalence_class')
    
    # Priority 2: Worldwide fallback
    prevalence_records = disease_data.get('prevalence_records', [])
    reliable_records = [r for r in prevalence_records if r.get('reliability_score', 0) >= 6.0]
    
    worldwide_records = [r for r in reliable_records if r.get('geographic_area') == 'Worldwide']
    if worldwide_records:
        best_record = max(worldwide_records, key=lambda x: x.get('reliability_score', 0))
        self.stats['selection_method_counts']['worldwide_fallback'] += 1
        return best_record.get('prevalence_class')
    
    # Priority 3: Regional fallback  
    regional_records = [r for r in reliable_records if r.get('geographic_area') != 'Worldwide']
    if regional_records:
        best_record = max(regional_records, key=lambda x: x.get('reliability_score', 0))
        self.stats['selection_method_counts']['regional_fallback'] += 1
        return best_record.get('prevalence_class')
    
    # Current: No fallback → "Unknown"
    self.stats['selection_method_counts']['no_data'] += 1
    return None
```

### **Gap Analysis**

**Problem**: After all fallbacks, diseases are marked as "Unknown" even when birth prevalence data might be available.

**Solution**: Add a birth-to-point prevalence estimation as a final fallback before marking as "Unknown".

## 🔄 **Birth-to-Point Prevalence Conversion**

### **Scientific Rationale**

**Key Concepts**:
- **Birth Prevalence**: Cases per live births at birth
- **Point Prevalence**: Cases per total living population at a point in time
- **Conservation Principle**: Point prevalence ≤ Birth prevalence due to mortality

**Conservative Mapping**: Estimate point prevalence as one category lower than birth prevalence to account for disease-related mortality.

### **Prevalence Categories (Ordered by Frequency)**

| Category              | Description           |
|-----------------------|----------------------|
| `<1 / 1 000 000`      | Extremely rare       |
| `1-9 / 1 000 000`     | Very rare           |
| `1-9 / 100 000`       | Rare                |
| `1-5 / 10 000`        | Uncommon            |
| `6-9 / 10 000`        | Moderately uncommon |
| `>1 / 1000`           | Relatively frequent |

### **Birth-to-Point Mapping Table**

| Birth Prevalence       | → | Estimated Point Prevalence |
|------------------------|---|----------------------------|
| `>1 / 1000`            | → | `6-9 / 10 000`             |
| `6-9 / 10 000`         | → | `1-5 / 10 000`             |
| `1-5 / 10 000`         | → | `1-9 / 100 000`            |
| `1-9 / 100 000`        | → | `1-9 / 1 000 000`          |
| `1-9 / 1 000 000`      | → | `<1 / 1 000 000`           |
| `<1 / 1 000 000`       | → | `<1 / 1 000 000`           |
| `Unknown`              | → | `Unknown`                  |
| `Not yet documented`   | → | `Unknown`                  |

## 🛠 **Implementation Plan**

### **Minimal Code Changes Required**

**Principle**: Touch code minimally - only modify the selection function to add birth prevalence fallback.

### **Step 1: Add Birth-to-Point Conversion Function**

```python
def birth2point(self, birth_category: str) -> str:
    """
    Convert birth prevalence category to estimated point prevalence category.
    
    Uses conservative one-step down mapping to account for disease mortality.
    """
    mapping = {
        ">1 / 1000":           "6-9 / 10 000",
        "6-9 / 10 000":        "1-5 / 10 000", 
        "1-5 / 10 000":        "1-9 / 100 000",
        "1-9 / 100 000":       "1-9 / 1 000 000",
        "1-9 / 1 000 000":     "<1 / 1 000 000",
        "<1 / 1 000 000":      "<1 / 1 000 000",
        "Unknown":             "Unknown",
        "Not yet documented":  "Unknown"
    }
    return mapping.get(birth_category, "Unknown")
```

### **Step 2: Modify Selection Algorithm**

Add birth prevalence fallback as **Priority 4** before returning "Unknown":

```python
def select_best_prevalence_class(self, disease_data: Dict) -> Optional[str]:
    """
    Enhanced fallback priorities:
    1. Point prevalence from most_reliable_prevalence
    2. Worldwide records with best reliability
    3. Regional records with best reliability  
    4. Birth prevalence estimation (NEW)
    5. Return None → "Unknown"
    """
    
    # Priorities 1-3: Existing logic (unchanged)
    # ... existing code ...
    
    # NEW Priority 4: Birth prevalence fallback
    birth_prevalence_records = [r for r in prevalence_records 
                               if r.get('prevalence_type') == 'Birth prevalence']
    
    if birth_prevalence_records:
        # Use most reliable birth prevalence record
        best_birth_record = max(birth_prevalence_records, 
                               key=lambda x: x.get('reliability_score', 0))
        birth_class = best_birth_record.get('prevalence_class')
        
        if birth_class:
            estimated_point_class = self.birth2point(birth_class)
            if estimated_point_class != "Unknown":
                self.stats['selection_method_counts']['birth_prevalence_fallback'] += 1
                return estimated_point_class
    
    # Priority 5: No data available
    self.stats['selection_method_counts']['no_data'] += 1
    return None
```

### **Step 3: Update Statistics Tracking**

Add new counter for birth prevalence fallback:

```python
# In __init__ method, update selection_method_counts:
'selection_method_counts': {
    'point_prevalence': 0,
    'worldwide_fallback': 0, 
    'regional_fallback': 0,
    'birth_prevalence_fallback': 0,  # NEW
    'no_data': 0
}
```

## 🧪 **Testing Strategy**

### **Complete Dataset Testing**

**Requirement**: Test on the full dataset of **665 metabolic diseases** and override existing results.

### **Execution Steps**

#### **1. Create Disease Names Mapping (if needed)**
```bash
python etl/04_curate/orpha/ordo/curate_disease_names.py \
    --input data/04_curated/orpha/ordo/metabolic_disease_instances.json \
    --output data/04_curated/orpha/ordo/orphacode2disease_name.json \
    --verbose
```

#### **2. Run Prevalence Curation (Enhanced with Birth Fallback)**
```bash
python etl/04_curate/orpha/orphadata/curate_orpha_prevalence.py \
    --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json \
    --input data/03_processed/orpha/orphadata/orpha_prevalence/disease2prevalence.json \
    --output data/04_curated/orpha/orphadata/ \
    --verbose
```

#### **3. Generate Statistics**
```bash
python etl/05_stats/orpha/orphadata/orpha_prevalence_stats.py \
    --input-dir data/04_curated/orpha/orphadata/ \
    --output results/stats/etl/subset_of_disease_instances/orpha/orphadata/orpha_prevalence/metabolic/ \
    --verbose
```

### **Success Metrics**

#### **Primary Metrics**
- **Coverage Improvement**: Reduction in "Unknown" diseases
- **Birth Fallback Usage**: Number of diseases using birth prevalence estimation
- **Data Quality**: No degradation in existing high-quality assignments

#### **Expected Outcomes**
- **Baseline Coverage**: ~92% (based on existing metabolic data)
- **Enhanced Coverage**: Target >95% with birth prevalence fallback
- **Birth Fallback Usage**: Estimate 20-50 diseases will benefit from this fallback

## 📁 **File Changes Required**

### **Modified Files**
- `etl/04_curate/orpha/orphadata/curate_orpha_prevalence.py`
  - Add `birth2point()` method
  - Modify `select_best_prevalence_class()` method  
  - Update statistics tracking

### **New Files**
- `task_plan/birth_to_point_fallback_task.md` (this document)

### **Output Files**
- `data/04_curated/orpha/orphadata/disease2prevalence.json` (curated results)
- `data/04_curated/orpha/orphadata/orpha_prevalence_curation_summary.json` (processing summary)
- `data/04_curated/orpha/ordo/orphacode2disease_name.json` (disease names mapping)
- `results/stats/etl/subset_of_disease_instances/orpha/orphadata/orpha_prevalence/metabolic/` (statistics)

## 🎯 **Implementation Steps**

### **Phase 1: Code Implementation** 
1. Add `birth2point()` method to `OrphaPrevalenceCurator` class
2. Modify `select_best_prevalence_class()` to include birth prevalence fallback
3. Update statistics tracking to include new fallback counter

### **Phase 2: Testing**
1. Create disease names mapping for 665 diseases
2. Run enhanced prevalence curation on 665 diseases (overwrites existing results)
3. Generate comprehensive statistics


### **Phase 4: Documentation**
1. Update `README.md` files to document new fallback method
2. Update client documentation to explain birth prevalence estimation
3. Document methodology and validation results

## ✅ **Success Criteria**

1. **Functionality**: All scripts execute successfully on 665 diseases

5. **Statistics**: Birth fallback usage clearly tracked and reported
6. **Documentation**: Clear documentation of methodology and limitations

## 📝 **Conclusion**

This implementation adds a scientifically-justified fallback mechanism that can improve data coverage while maintaining data quality. The minimal code changes and comprehensive testing strategy ensure low risk and high confidence in the enhancement. 