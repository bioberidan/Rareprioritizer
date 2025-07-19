# Prevalence Preprocessing Correction

## Overview

This document addresses a critical issue in the prevalence preprocessing system where prevalence estimates are being calculated incorrectly, resulting in unrealistic values that exceed 100% of the population for rare diseases.

## Problem Analysis

### Current Issue
The current implementation in `tools/prevalence_preprocessing.py` incorrectly calculates prevalence estimates by multiplying `val_moy` values by 1,000,000:

```python
# INCORRECT CALCULATION
if record["val_moy"]:
    record["per_million_estimate"] = record["val_moy"] * 1000000
```

This results in prevalence estimates that are completely unrealistic for rare diseases:
- **154,000,000 per million** (15,400% of population)
- **100,000,000 per million** (10,000% of population)  
- **4,000,000 per million** (400% of population)

### Root Cause
The `val_moy` field in the XML data appears to represent a different metric than expected, and multiplying it by 1,000,000 produces inflated values that contradict the fundamental definition of rare diseases.

## Solution: Prevalence Class-Based Estimates

### Approach
**Completely ignore `val_moy` values** and calculate prevalence estimates exclusively from standardized prevalence classes using midpoint calculations.

### Prevalence Class Mappings

The Orphanet XML provides the following prevalence classes:

| Prevalence Class | Fraction | Per Million Range | Midpoint Estimate |
|------------------|----------|-------------------|-------------------|
| `>1 / 1,000` | >0.001 | >1,000 per million | **1,000 per million** |
| `1-5 / 10,000` | 0.0001-0.0005 | 100-500 per million | **300 per million** |
| `6-9 / 10,000` | 0.0006-0.0009 | 600-900 per million | **750 per million** |
| `1-9 / 100,000` | 0.00001-0.00009 | 10-90 per million | **50 per million** |
| `1-9 / 1,000,000` | 0.000001-0.000009 | 1-9 per million | **5 per million** |
| `<1 / 1,000,000` | <0.000001 | <1 per million | **0.5 per million** |
| `Not yet documented` | - | - | **0 per million** |
| `Unknown` | - | - | **0 per million** |

### Calculation Logic

#### Standard Classes (Midpoint Calculation)
```python
def calculate_prevalence_estimate(prevalence_class):
    """Calculate per-million estimate from prevalence class using midpoint"""
    
    class_mappings = {
        ">1 / 1,000": 1000.0,  # Use 1000 as reasonable estimate for ">1"
        "1-5 / 10,000": 300.0,  # Midpoint of 100-500
        "6-9 / 10,000": 750.0,  # Midpoint of 600-900
        "1-9 / 100,000": 50.0,  # Midpoint of 10-90
        "1-9 / 1,000,000": 5.0,  # Midpoint of 1-9
        "<1 / 1,000,000": 0.5,  # Midpoint of 0-1
        "Not yet documented": 0.0,
        "Unknown": 0.0
    }
    
    return class_mappings.get(prevalence_class, 0.0)
```

#### Edge Case Handling

**1. Open-ended ranges:**
- `>1 / 1,000`: Use 1,000 per million as a conservative estimate
- `<1 / 1,000,000`: Use 0.5 per million as midpoint between 0 and 1

**2. Unknown values:**
- `Not yet documented`: Set to 0 (no prevalence data available)
- `Unknown`: Set to 0 (no prevalence data available)
- `null` or empty: Set to 0 (no prevalence data available)

**3. Invalid/unexpected values:**
- Any unrecognized prevalence class should default to 0 and log a warning

## Implementation Changes

### 1. Modified Calculation Function
```python
def standardize_prevalence_class(prevalence_class):
    """Convert prevalence class to per-million estimates using midpoint calculation"""
    
    if not prevalence_class or prevalence_class in ["Unknown", "Not yet documented", ""]:
        return {
            "per_million_estimate": 0.0,
            "confidence": "none",
            "source": "no_data"
        }
    
    class_mappings = {
        ">1 / 1,000": {
            "per_million_estimate": 1000.0,
            "confidence": "high",
            "source": "class_estimate",
            "range": {"min": 1000, "max": "unlimited"}
        },
        "1-5 / 10,000": {
            "per_million_estimate": 300.0,
            "confidence": "high", 
            "source": "class_midpoint",
            "range": {"min": 100, "max": 500}
        },
        "6-9 / 10,000": {
            "per_million_estimate": 750.0,
            "confidence": "high",
            "source": "class_midpoint", 
            "range": {"min": 600, "max": 900}
        },
        "1-9 / 100,000": {
            "per_million_estimate": 50.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 10, "max": 90}
        },
        "1-9 / 1,000,000": {
            "per_million_estimate": 5.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 1, "max": 9}
        },
        "<1 / 1,000,000": {
            "per_million_estimate": 0.5,
            "confidence": "medium",
            "source": "class_estimate",
            "range": {"min": 0, "max": 1}
        }
    }
    
    if prevalence_class in class_mappings:
        return class_mappings[prevalence_class]
    else:
        logger.warning(f"Unknown prevalence class: {prevalence_class}")
        return {
            "per_million_estimate": 0.0,
            "confidence": "none",
            "source": "unknown_class"
        }
```

### 2. Updated Processing Logic
```python
# CORRECTED CALCULATION - Remove val_moy usage entirely
def process_prevalence_record(prevalence_data):
    """Process a single prevalence record using class-based estimates only"""
    
    record = {
        "prevalence_id": prevalence_data["id"],
        "orpha_code": prevalence_data["orpha_code"],
        "disease_name": prevalence_data["disease_name"],
        "source": prevalence_data["source"],
        "prevalence_type": prevalence_data["prevalence_type"],
        "prevalence_class": prevalence_data["prevalence_class"],
        "qualification": prevalence_data["qualification"],
        "geographic_area": prevalence_data["geographic_area"],
        "validation_status": prevalence_data["validation_status"]
    }
    
    # Calculate prevalence estimate ONLY from prevalence class
    class_result = standardize_prevalence_class(record["prevalence_class"])
    record["per_million_estimate"] = class_result["per_million_estimate"]
    record["confidence_level"] = class_result["confidence"]
    record["estimate_source"] = class_result["source"]
    
    # Remove val_moy from the record entirely
    # record["val_moy"] = None  # Don't include this field
    
    return record
```

## Quality Assurance

### 1. Validation Rules
```python
def validate_prevalence_estimate(estimate, prevalence_class):
    """Validate that prevalence estimates are reasonable for rare diseases"""
    
    # Maximum reasonable prevalence for rare diseases
    MAX_RARE_DISEASE_PREVALENCE = 5000  # 0.5% of population
    
    if estimate > MAX_RARE_DISEASE_PREVALENCE:
        logger.error(f"Prevalence estimate {estimate} exceeds maximum for rare diseases")
        return False
    
    # Specific class validations
    class_limits = {
        ">1 / 1,000": {"max": 1000000},  # No upper limit, but flag if extreme
        "1-5 / 10,000": {"min": 100, "max": 500},
        "6-9 / 10,000": {"min": 600, "max": 900},
        "1-9 / 100,000": {"min": 10, "max": 90},
        "1-9 / 1,000,000": {"min": 1, "max": 9},
        "<1 / 1,000,000": {"min": 0, "max": 1}
    }
    
    if prevalence_class in class_limits:
        limits = class_limits[prevalence_class]
        if "min" in limits and estimate < limits["min"]:
            logger.warning(f"Estimate {estimate} below expected range for {prevalence_class}")
        if "max" in limits and estimate > limits["max"]:
            logger.warning(f"Estimate {estimate} above expected range for {prevalence_class}")
    
    return True
```

### 2. Data Quality Checks
```python
def generate_quality_report(processed_data):
    """Generate quality report for corrected prevalence data"""
    
    stats = {
        "total_records": len(processed_data),
        "records_with_estimates": 0,
        "records_without_estimates": 0,
        "estimate_distribution": {},
        "class_distribution": {},
        "validation_errors": []
    }
    
    for record in processed_data:
        estimate = record["per_million_estimate"]
        prevalence_class = record["prevalence_class"]
        
        # Count records with/without estimates
        if estimate > 0:
            stats["records_with_estimates"] += 1
        else:
            stats["records_without_estimates"] += 1
        
        # Distribution analysis
        if estimate > 0:
            range_key = get_estimate_range(estimate)
            stats["estimate_distribution"][range_key] = stats["estimate_distribution"].get(range_key, 0) + 1
        
        stats["class_distribution"][prevalence_class] = stats["class_distribution"].get(prevalence_class, 0) + 1
        
        # Validation
        if not validate_prevalence_estimate(estimate, prevalence_class):
            stats["validation_errors"].append({
                "prevalence_id": record["prevalence_id"],
                "estimate": estimate,
                "class": prevalence_class
            })
    
    return stats

def get_estimate_range(estimate):
    """Categorize estimates into ranges for analysis"""
    if estimate == 0:
        return "0 (no data)"
    elif estimate <= 1:
        return "0-1 per million"
    elif estimate <= 10:
        return "1-10 per million"
    elif estimate <= 100:
        return "10-100 per million"
    elif estimate <= 1000:
        return "100-1,000 per million"
    else:
        return ">1,000 per million"
```

## Expected Results After Correction

### 1. Realistic Prevalence Estimates
- Maximum estimate: 1,000 per million (0.1% of population)
- Typical rare disease range: 0.5-50 per million
- Ultra-rare diseases: 0.5-5 per million

### 2. Improved Data Quality
- No impossible prevalence values (>100% of population)
- Consistent methodology across all records
- Clear traceability from prevalence class to estimate

### 3. Better Research Prioritization
- Meaningful prevalence comparisons between diseases
- Accurate population impact assessments
- Reliable data for funding allocation decisions

## Implementation Steps

### 1. Backup Current Data
```bash
# Create backup of current processed data
cp -r data/preprocessing/prevalence data/preprocessing/prevalence_backup_$(date +%Y%m%d)
```

### 2. Update Processing Script
- Modify `tools/prevalence_preprocessing.py` with corrected logic
- Remove all references to `val_moy` in calculations
- Implement class-based estimation only

### 3. Reprocess Data
```bash
# Reprocess with corrected logic
python tools/prevalence_preprocessing.py --force
```

### 4. Validate Results
```bash
# Validate corrected data
python tools/prevalence_preprocessing.py --validate-only
```

### 5. Generate Quality Report
```bash
# Generate comprehensive quality report
python tools/prevalence_quality_analysis.py
```

## Monitoring and Maintenance

### 1. Regular Validation
- Monitor for new prevalence classes in XML updates
- Validate that no estimates exceed reasonable limits
- Track the distribution of estimates across classes

### 2. Performance Metrics
- Percentage of records with valid estimates
- Distribution of estimates across ranges
- Consistency with known epidemiological data

### 3. Data Quality Alerts
- Alert if any estimate exceeds 5,000 per million
- Flag unknown prevalence classes
- Monitor for processing errors

## Conclusion

This correction addresses the fundamental issue of unrealistic prevalence estimates by:

1. **Eliminating `val_moy` usage** completely from calculations
2. **Using only prevalence classes** for estimates
3. **Implementing midpoint calculations** for consistent results
4. **Adding validation rules** to prevent future issues
5. **Providing comprehensive quality assurance**

The corrected system will produce realistic, meaningful prevalence estimates that accurately reflect the rarity of diseases and support effective research prioritization decisions. 