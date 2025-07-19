# Prevalence Processing Artifact Analysis

**Investigation Date**: December 2024  
**Issue**: Understanding where 1000.0 per million prevalence values originate and how means are calculated

## 🔍 **Root Cause Discovery**

### **Source of 1000.0 Artifact**

The 1000.0 per million values are **NOT missing data placeholders** but come from the `standardize_prevalence_class()` function in `etl/03_process/orpha/orphadata/process_orpha_prevalence.py`:

```python
def standardize_prevalence_class(prevalence_class):
    class_mappings = {
        # Standard comma-separated formats
        ">1 / 1,000": {
            "per_million_estimate": 1000.0,  # ← HERE!
            "confidence": "high",
            "source": "class_estimate",
            "range": {"min": 1000, "max": "unlimited"}
        },
        # Space-separated formats (actual XML format)
        ">1 / 1000": {
            "per_million_estimate": 1000.0,  # ← AND HERE!
            "confidence": "high",
            "source": "class_estimate", 
            "range": {"min": 1000, "max": "unlimited"}
        }
    }
```

### **The "N/A per million" Red Herring**

The "N/A per million" in our earlier analysis was from **accessing the wrong field**:
- ❌ **Non-existent**: `record.get('prevalence_value_per_million', 'N/A')` 
- ✅ **Actual field**: `record['per_million_estimate']` (contains 1000.0)

The XML data contains **prevalence classes only**, no numerical values. The processing pipeline converts classes like ">1 / 1000" to 1000.0 per million.

## 📊 **Data Processing Flow**

### **Step 1: XML Extraction**
```python
# From XML: <PrevalenceClass><Name lang="en">>1 / 1000</Name></PrevalenceClass>
record["prevalence_class"] = ">1 / 1000"  # Raw class from XML
```

### **Step 2: Class Standardization** 
```python
# Convert class to numerical estimate
class_data = standardize_prevalence_class(record["prevalence_class"])
record["per_million_estimate"] = class_data["per_million_estimate"]  # 1000.0
```

### **Step 3: Mean Calculation**
```python
def calculate_weighted_mean_prevalence(prevalence_records):
    for record in valid_records:
        prevalence = record["per_million_estimate"]  # Uses 1000.0 values
        weight = record["reliability_score"]
        weighted_sum += prevalence * weight
        weight_sum += weight
    
    mean_value = weighted_sum / weight_sum  # Results in 1000.0 for ">1/1000" diseases
```

## 🧬 **Medical Interpretation Problem**

### **Prevalence Class Mapping Issues**

| **XML Class** | **Mapped Value** | **Medical Reality** | **Issue** |
|---------------|------------------|---------------------|-----------|
| `>1 / 1000` | 1000.0 per million | ≥0.1% of population | **Overly precise for open-ended range** |
| `1-5 / 10000` | 300.0 per million | 0.01-0.05% | ✅ Reasonable midpoint |
| `6-9 / 10000` | 750.0 per million | 0.06-0.09% | ✅ Reasonable midpoint |

### **The ">1 / 1000" Problem**

**Class Definition**: Greater than 1 in 1,000 (>1000 per million)  
**Current Mapping**: Exactly 1000.0 per million  
**Medical Reality**: Could be 1001, 5000, 50000, or even 100000 per million

**Examples of Medical Incoherence:**
- **Hydrops fetalis**: Birth defect affecting pregnancies, not general population
- **Anterior uveitis**: Could legitimately be ~1000 per million (✅ coherent)
- **Trehalase deficiency**: 50,000+ per million in Greenland, 0 elsewhere
- **Distal myopathy Welander**: 1000+ per million in Sweden, 0 globally

## 🔧 **Technical Issues Identified**

### **1. Open Range Handling**
```python
# CURRENT (problematic)
">1 / 1000": {"per_million_estimate": 1000.0}  # Treats as ceiling, not floor

# BETTER (suggested)
">1 / 1000": {"per_million_estimate": None, "min_estimate": 1000.0}  # Open range
```

### **2. Geographic Context Missing**
```python
# CURRENT (ignores geography)
record["per_million_estimate"] = 1000.0  # Applied globally

# BETTER (geography-aware)
if record["geographic_area"] == "Sweden" and disease == "Welander":
    record["per_million_estimate"] = 1000.0  # Valid for Sweden
else:
    record["per_million_estimate"] = 0.0      # Invalid elsewhere
```

### **3. Birth vs Population Prevalence**
```python
# CURRENT (treats all equally)
record["per_million_estimate"] = 1000.0  # Population prevalence

# BETTER (context-aware)
if record["prevalence_type"] == "Prevalence at birth":
    record["birth_prevalence_per_million"] = 1000.0
    record["population_prevalence_per_million"] = much_lower_value
```

## 📈 **Impact on Statistical Analysis**

### **False Ceiling Effect**
- **8 diseases** artificially capped at 1000.0 per million
- **Creates artificial peak** in prevalence distribution
- **Distorts "Very common (>1000)" category** with class artifacts

### **Mean Calculation Bias**
```python
# Example: Disease with mixed records
records = [
    {"per_million_estimate": 1000.0, "reliability_score": 8.0},  # ">1/1000" class
    {"per_million_estimate": 50.0,   "reliability_score": 9.0},  # "1-9/100000" class  
    {"per_million_estimate": 5.0,    "reliability_score": 7.0}   # "1-9/1000000" class
]
# Result: weighted_mean = (1000*8 + 50*9 + 5*7) / (8+9+7) = 367.9 per million
# But the ">1/1000" could actually be 5000+ per million!
```

## 🎯 **Recommended Fixes**

### **1. Open Range Handling**
```python
def standardize_prevalence_class(prevalence_class):
    if prevalence_class.startswith(">"):
        return {
            "per_million_estimate": None,           # Don't assume ceiling
            "min_estimate": extracted_threshold,    # Store minimum only
            "is_open_range": True,
            "range_type": "greater_than"
        }
```

### **2. Geographic Stratification**
```python
def calculate_geographic_adjusted_prevalence(record):
    base_estimate = standardize_prevalence_class(record["prevalence_class"])
    geographic_area = record["geographic_area"]
    
    # Apply geographic modifiers for population-specific diseases
    if is_population_specific_disease(record["orpha_code"], geographic_area):
        return apply_geographic_adjustment(base_estimate, geographic_area)
    return base_estimate
```

### **3. Prevalence Type Handling**
```python
def calculate_context_aware_prevalence(record):
    if record["prevalence_type"] == "Prevalence at birth":
        return calculate_birth_prevalence(record)
    elif record["prevalence_type"] == "Point prevalence":
        return calculate_population_prevalence(record)
    # etc.
```

### **4. Mean Calculation Enhancement**
```python
def calculate_weighted_mean_prevalence(prevalence_records):
    # Exclude open ranges from mean calculation
    finite_records = [r for r in prevalence_records 
                     if not r.get("is_open_range", False)]
    
    if finite_records:
        return calculate_finite_range_mean(finite_records)
    else:
        return {"mean_value_per_million": None, "reason": "only_open_ranges"}
```

## 🏁 **Final Verdict**

**The 1000.0 per million artifact is NOT a data processing error but a medical interpretation problem:**

1. **Class ">1 / 1000"** legitimately maps to "greater than 1000 per million"
2. **Setting it to exactly 1000.0** treats an open range as a closed value
3. **Geographic and context ignorance** applies population-specific prevalences globally
4. **Mean calculations** inappropriately average open ranges with finite values

**Result**: Medically coherent data processing produces epidemiologically incoherent results due to oversimplified prevalence class interpretation.

## 🚀 **Implementation Priority**

1. **High**: Flag open ranges (">1/1000") as non-finite for mean calculations
2. **Medium**: Implement geographic stratification for population-specific diseases  
3. **Low**: Add prevalence type context (birth vs population)
4. **Documentation**: Update data dictionary to explain prevalence class limitations

This analysis explains why diseases like **Trehalase deficiency** (Greenland-specific) and **Hydrops fetalis** (birth-specific) appear to have the same prevalence as truly common conditions - the system treats ">1/1000" as exactly 1000.0 regardless of medical context. 