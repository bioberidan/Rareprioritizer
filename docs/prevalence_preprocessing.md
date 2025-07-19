# Prevalence Data Preprocessing System

## Overview

The prevalence preprocessing system processes Orphanet prevalence data from `en_product9_prev.xml` into structured JSON files with reliability scoring and geographic distribution analysis. The system calculates prevalence estimates **exclusively from prevalence classes** using midpoint calculations to ensure realistic estimates for rare diseases.

## Quick Start

```bash
# Process prevalence data with default settings
python tools/prevalence_preprocessing.py

# Process with custom input/output paths
python tools/prevalence_preprocessing.py --xml data/input/raw/en_product9_prev.xml --output data/preprocessing/prevalence

# Validate existing processed files
python tools/prevalence_preprocessing.py --validate-only

# Force overwrite existing files
python tools/prevalence_preprocessing.py --force
```

## Processing Results Summary

### Data Volume
- **Total disorders**: 6,317
- **Disorders with prevalence data**: 6,317 (100%)
- **Total prevalence records**: 16,420
- **Reliable records (≥6.0 score)**: 14,241 (86.7%)
- **Processing time**: ~7.9 seconds
- **Total output size**: 64.55 MB

### Data Quality Distribution
- **Validated records**: 14,520 (88.4%)
- **Not yet validated**: 1,897 (11.6%)
- **Records with prevalence estimates**: 11,059 (67.3%)
- **Records with reliable estimates**: 6,315 (38.5%)

## File Structure

```
data/preprocessing/prevalence/
├── disease2prevalence.json            # 33.21 MB - Main mapping: OrphaCode → prevalence records
├── prevalence2diseases.json           # 0.50 MB  - Reverse mapping: PrevalenceID → diseases
├── prevalence_instances.json          # 8.46 MB  - All individual prevalence records
├── orpha_index.json                   # 1.31 MB  - Optimized OrphaCode lookup
├── regional_data/                     # Geographic breakdown (141 regions)
│   ├── spain_prevalences.json         # 0.11 MB  - 218 Spanish prevalence records
│   ├── europe_prevalences.json        # 0.85 MB  - 1,675 European records
│   ├── worldwide_prevalences.json     # 4.43 MB  - 8,835 worldwide records
│   ├── united_states_prevalences.json # 0.23 MB  - 449 US records
│   ├── united_kingdom_prevalences.json# 0.19 MB  - 361 UK records
│   └── regional_summary.json          # 0.01 MB  - Regional statistics
├── reliability/
│   ├── reliable_prevalences.json      # 7.38 MB  - Only reliable records (≥6.0 score)
│   ├── reliability_scores.json        # 5.16 MB  - Detailed scoring for each record
│   └── validation_report.json         # 0.00 MB  - Data quality assessment
└── cache/
    ├── statistics.json                 # 0.00 MB  - Processing statistics
    ├── prevalence_classes.json        # 0.00 MB  - Standardized class mappings
    └── geographic_index.json          # 0.19 MB  - Geographic area groupings
```

## Data Models

### PrevalenceInstance
Each prevalence record contains:
```json
{
  "prevalence_id": "8322",
  "orpha_code": "166024",
  "disease_name": "Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome",
  "source": "11389160[PMID]_9689990[PMID]_[EXPERT]",
  "prevalence_type": "Point prevalence",
  "prevalence_class": "1-9 / 1 000 000", 
  "qualification": "Value and class",
  "geographic_area": "Europe",
  "validation_status": "Validated",
  "reliability_score": 8.5,
  "is_fiable": true,
  "per_million_estimate": 5.0,
  "confidence_level": "high",
  "estimate_source": "class_midpoint"
}
```

**Note**: The `val_moy` field is no longer included in the processed records. The `per_million_estimate` is calculated exclusively from the `prevalence_class` using midpoint calculations:
- `"1-9 / 1 000 000"` → **5.0 per million** (midpoint of 1-9 range)

### Disease2Prevalence Mapping
```json
{
  "166024": {
    "orpha_code": "166024",
    "disease_name": "Disease Name",
    "prevalence_records": [...],
    "most_reliable_prevalence": {...},
    "validated_prevalences": [...],
    "regional_prevalences": {
      "Europe": [...],
      "Worldwide": [...]
    },
    "statistics": {
      "total_records": 2,
      "reliable_records": 1
    }
  }
}
```

## Reliability Scoring System

### Scoring Criteria (0-10 scale)
1. **Validation Status** (3 points): "Validated" = 3.0
2. **Source Quality** (2 points): [PMID] = 2.0, [EXPERT] = 1.0
3. **Data Qualification** (2 points): "Value and class" = 2.0, "Class only" = 1.0
4. **Prevalence Type** (2 points): 
   - "Point prevalence" = 2.0 (most reliable)
   - "Prevalence at birth" = 1.8
   - "Annual incidence" = 1.5
   - "Cases/families" = 1.0 (least reliable)
5. **Geographic Specificity** (1 point): Specific region = 1.0, "Worldwide" = 0.0

### Reliability Threshold
- **Fiable (reliable)**: score ≥ 6.0
- **86.7% of records** meet this threshold

## Prevalence Calculation Method

### Approach
The system calculates prevalence estimates **exclusively from prevalence classes** using midpoint calculations. The `val_moy` field from the XML is **completely ignored** to ensure realistic estimates for rare diseases.

### Prevalence Class Mappings
Each prevalence class is converted to a per-million estimate using the midpoint of the range:

| Prevalence Class | Fraction Range | Per Million Range | **Midpoint Estimate** |
|------------------|----------------|-------------------|-----------------------|
| `>1 / 1,000` | >0.001 | >1,000 per million | **1,000 per million** |
| `1-5 / 10,000` | 0.0001-0.0005 | 100-500 per million | **300 per million** |
| `6-9 / 10,000` | 0.0006-0.0009 | 600-900 per million | **750 per million** |
| `1-9 / 100,000` | 0.00001-0.00009 | 10-90 per million | **50 per million** |
| `1-9 / 1,000,000` | 0.000001-0.000009 | 1-9 per million | **5 per million** |
| `<1 / 1,000,000` | <0.000001 | <1 per million | **0.5 per million** |

### Special Cases
- `"Unknown"` → **0 per million** (no prevalence data)
- `"Not yet documented"` → **0 per million** (no prevalence data)
- `null` or empty → **0 per million** (no prevalence data)

### Implementation Code

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

### Processing Logic
```python
def calculate_prevalence_estimate(record):
    """Calculate prevalence estimate ONLY from prevalence class"""
    
    # Get class-based estimate
    class_result = standardize_prevalence_class(record["prevalence_class"])
    
    # Set the per-million estimate from class calculation
    record["per_million_estimate"] = class_result["per_million_estimate"]
    record["confidence_level"] = class_result["confidence"]
    record["estimate_source"] = class_result["source"]
    
    # val_moy is completely ignored
    return record
```

### Why This Approach?
1. **Consistency**: All estimates use the same calculation method
2. **Accuracy**: Prevents impossible prevalence values (>100% of population)
3. **Reliability**: Based on standardized Orphanet classification system
4. **Transparency**: Clear traceability from class to estimate

### Validation and Quality Assurance

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

### Expected Prevalence Ranges
All prevalence estimates are now within realistic ranges for rare diseases:
- **Maximum estimate**: 1,000 per million (0.1% of population)
- **Most common rare diseases**: 300-750 per million (0.03%-0.075% of population)
- **Typical rare diseases**: 5-50 per million (0.0005%-0.005% of population)
- **Ultra-rare diseases**: 0.5 per million (0.00005% of population)
- **Unknown/undocumented**: 0 per million

## Geographic Distribution

### Top Regions by Record Count
1. **Worldwide**: 8,835 records (53.8%)
2. **Europe**: 1,675 records (10.2%)
3. **United States**: 449 records (2.7%)
4. **United Kingdom**: 361 records (2.2%)
5. **Italy**: 260 records (1.6%)
6. **France**: 274 records (1.7%)
7. **Spain**: 218 records (1.3%)

### Coverage
- **141 different geographic regions** represented
- **European countries well represented**: 25+ EU countries with data
- **Global coverage**: All continents represented

## Data Quality Analysis

### Prevalence Types Distribution
- **Point prevalence**: 39.3% (most reliable)
- **Prevalence at birth**: 44.8%
- **Annual incidence**: 5.5%
- **Cases/families**: 10.4% (least reliable)

### Prevalence Class Distribution
- **`<1 / 1 000 000`**: 4,647 records (28.3%) → 0.5 per million
- **`1-9 / 100 000`**: 2,805 records (17.1%) → 50.0 per million
- **`1-9 / 1 000 000`**: 2,205 records (13.4%) → 5.0 per million
- **`Unknown`**: 1,997 records (12.2%) → 0 per million
- **`1-5 / 10 000`**: 1,193 records (7.3%) → 300.0 per million
- **`6-9 / 10 000`**: 112 records (0.7%) → 750.0 per million
- **`>1 / 1000`**: 97 records (0.6%) → 1000.0 per million
- **`null`**: 3,358 records (20.5%) → 0 per million

### Validation Status
- **Validated**: 14,520 records (88.4%)
- **Not yet validated**: 1,897 records (11.6%)
- **Empty**: 3 records (<0.1%)

## Key Features

### Reliability-Based Analysis
- Automatic reliability scoring for all prevalence records
- Identification of most reliable prevalence per disease
- Filtering of reliable vs unreliable data
- Quality metrics and validation reports

### Geographic Intelligence
- Regional breakdown of prevalence data
- Country-specific prevalence files
- Geographic conflict resolution
- Regional statistics and comparisons

### Data Integration
- OrphaCode-based disease mapping
- Cross-references with disease taxonomy
- Standardized prevalence class conversion using midpoint calculations
- Per-million estimate calculations based exclusively on prevalence classes
- Confidence levels and estimate source tracking

## Usage Examples

### Finding High-Quality Prevalence Data
```bash
# Get reliable prevalences only
cat data/preprocessing/prevalence/reliability/reliable_prevalences.json

# Check Spanish-specific data
cat data/preprocessing/prevalence/regional_data/spain_prevalences.json

# View disease-specific prevalences
python -c "
import json
with open('data/preprocessing/prevalence/disease2prevalence.json') as f:
    data = json.load(f)
    print(data['166024'])  # Specific disease prevalence
"
```

### Quality Assessment
```bash
# View validation report
cat data/preprocessing/prevalence/reliability/validation_report.json

# Check processing statistics
cat data/preprocessing/prevalence/cache/statistics.json

# Analyze EDA
python tools/prevalence_eda.py --reliability-analysis
```

## Data Sources Analysis

### Source Quality Distribution
- **PMID (PubMed) sources**: 9,575 records (58.3%) - Peer-reviewed literature
- **EXPERT sources**: 897 records (5.5%) - Expert opinion  
- **Both PMID and EXPERT**: 297 records (1.8%) - Highest quality combination
- **Other/Orphanet sources**: 6,242 records (38.0%) - Orphanet internal data
- **Empty sources**: 3 records (0.0%) - Missing source information

### Prevalence Estimate Sources
- **Class-based midpoint calculations**: 6,315 records (38.5%) - High confidence estimates
- **Class-based estimates**: 4,744 records (28.9%) - Reliable estimates for open ranges
- **No prevalence data**: 5,361 records (32.7%) - Unknown, null, or undocumented classes

### Geographic Coverage
- **Worldwide estimates**: 8,835 records (53.8%)
- **European data**: 1,675 records (10.2%)
- **United States data**: 449 records (2.7%)
- **Specific regions**: 5,461 records (33.3%) - 138 different countries/regions

## Technical Implementation

### Processing Performance
- **XML parsing**: 6,317 disorders in ~1.0 second
- **Prevalence calculation**: 16,420 records in ~0.7 seconds
- **File generation**: 64.55 MB output in ~6.2 seconds
- **Total processing time**: ~7.9 seconds
- **Memory usage**: <2GB during processing

### Data Validation
- **JSON structure validation**: 100% valid output files
- **Reliability score validation**: All records scored 0-10
- **Geographic normalization**: 141 regions standardized
- **Missing data handling**: Null values properly processed
- **Prevalence estimate validation**: All estimates ≤ 1,000 per million (realistic for rare diseases)
- **Class-based calculation**: Consistent methodology using prevalence class midpoints only

## Maintenance and Updates

### Regular Updates
1. **New XML data**: Rerun preprocessing with `--force` flag
2. **Validation**: Run `--validate-only` to check data integrity
3. **EDA analysis**: Use `tools/prevalence_eda.py` for data exploration

### Monitoring
- **File sizes**: Monitor for significant changes in output size
- **Reliability scores**: Track percentage of reliable records
- **Geographic coverage**: Monitor new regions added
- **Processing time**: Alert if processing takes >30 seconds

## Integration with Research Prioritization

### Prevalence Scoring
The processed prevalence data integrates with the research prioritization system by providing:
- **Reliability-weighted prevalence scores**
- **Geographic-specific prevalence estimates**
- **Confidence levels for prevalence data**
- **Multiple prevalence records per disease for comparison**

### Usage in Prioritization
```python
# Example integration
prevalence_data = load_disease_prevalence("166024")
most_reliable = prevalence_data["most_reliable_prevalence"]
prevalence_score = calculate_prevalence_score(
    most_reliable["per_million_estimate"],
    most_reliable["reliability_score"]
)
```

## Troubleshooting

### Common Issues
1. **Unicode logging errors**: Cosmetic only, doesn't affect processing
2. **Memory usage**: Large XML files may require >4GB RAM
3. **File permissions**: Ensure write access to output directory
4. **Historical data**: Previous versions incorrectly used `val_moy` calculations resulting in unrealistic prevalence estimates (>100% of population). Current version uses class-based calculations only.

### Error Recovery
- **Validation failures**: Run with `--validate-only` to identify issues
- **Partial processing**: Delete output directory and rerun with `--force`
- **XML parsing errors**: Verify XML file integrity and encoding

## Future Enhancements

### Planned Features
1. **Trend analysis**: Track prevalence changes over time
2. **Conflict resolution**: Better handling of conflicting prevalences
3. **API integration**: Real-time updates from Orphanet
4. **Machine learning**: Automated quality assessment improvements

### Performance Optimizations
1. **Streaming processing**: Handle larger XML files efficiently
2. **Incremental updates**: Process only changed records
3. **Parallel processing**: Utilize multiple CPU cores
4. **Database integration**: Optional database backend for large datasets 