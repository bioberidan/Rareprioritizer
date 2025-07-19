# Refactor: Prevalence Preprocessing - Weighted Mean Calculation

## Overview

This document outlines the architecture plan for adding a `mean_prevalence_per_million` field to the prevalence preprocessing system. This field will provide a single, reliability-weighted prevalence estimate for each disease by combining all valid prevalence records.

## Business Requirements

### Purpose
- **Single Disease Estimate**: Provide one consolidated prevalence estimate per disease
- **Quality-Weighted**: Give more weight to higher reliability scores
- **Exclude Invalid Data**: Remove qualitative records and unknown values
- **Research Prioritization**: Enable consistent comparison across diseases

### Calculation Rules
1. **Include Only**: Records with `per_million_estimate > 0`
2. **Exclude**: 
   - `prevalence_type = "Cases/families"` (qualitative data)
   - `prevalence_class = "Unknown"` or `"Not yet documented"`
   - `per_million_estimate = 0`
3. **Weighting**: Use `reliability_score` as weights (0-10 scale)
4. **Fallback**: If no valid data exists, `mean_prevalence_per_million = 0`

## Architecture Design

### 1. Data Flow Architecture

```
XML Input → Individual Records → Reliability Scoring → Disease Grouping → Weighted Mean Calculation → Final Output
```

**Current Flow:**
1. Parse XML → prevalence records
2. Calculate reliability scores
3. Group by disease (OrphaCode)
4. Store in disease2prevalence mapping

**New Flow Addition:**
1. Parse XML → prevalence records
2. Calculate reliability scores
3. Group by disease (OrphaCode)
4. **[NEW]** Calculate weighted mean for each disease
5. Store in disease2prevalence mapping with mean_prevalence_per_million

### 2. Implementation Location

**Target Function**: `process_prevalence_xml()` in `tools/prevalence_preprocessing.py`

**Integration Point**: After building `disease2prevalence` mapping, before saving to files

```python
# Current code location (around line 400):
disease2prevalence[orpha_code] = {
    "orpha_code": orpha_code,
    "disease_name": name,
    "prevalence_records": prevalence_records,
    "most_reliable_prevalence": most_reliable,
    "validated_prevalences": validated_records,
    "regional_prevalences": dict(regional_prevalences),
    "statistics": {
        "total_records": len(prevalence_records),
        "reliable_records": len([r for r in prevalence_records if r["is_fiable"]])
    }
}

# NEW: Add weighted mean calculation here
```

### 3. Algorithm Design

#### Weighted Mean Formula
```
mean_prevalence_per_million = Σ(prevalence_i × reliability_score_i) / Σ(reliability_score_i)
```

#### Filtering Logic
```python
def get_valid_prevalence_records(prevalence_records):
    """Filter records valid for weighted mean calculation"""
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
    
    return valid_records
```

#### Weighted Mean Calculation
```python
def calculate_weighted_mean_prevalence(valid_records):
    """Calculate reliability-weighted mean prevalence"""
    if not valid_records:
        return 0.0
        
    weighted_sum = 0.0
    weight_sum = 0.0
    
    for record in valid_records:
        prevalence = record["per_million_estimate"]
        weight = record["reliability_score"]
        
        weighted_sum += prevalence * weight
        weight_sum += weight
    
    if weight_sum == 0:
        return 0.0
        
    return weighted_sum / weight_sum
```

### 4. Data Structure Changes

#### Enhanced Disease2Prevalence Schema
```json
{
  "166024": {
    "orpha_code": "166024",
    "disease_name": "Disease Name",
    "prevalence_records": [...],
    "most_reliable_prevalence": {...},
    "validated_prevalences": [...],
    "regional_prevalences": {...},
    "mean_prevalence_per_million": 25.7,
    "mean_prevalence_metadata": {
      "calculation_method": "reliability_weighted_mean",
      "valid_records_count": 3,
      "total_records_count": 5,
      "excluded_records": {
        "cases_families": 1,
        "unknown_class": 1,
        "zero_estimate": 0
      },
      "weight_distribution": {
        "min_weight": 6.0,
        "max_weight": 9.5,
        "mean_weight": 7.8
      }
    },
    "statistics": {
      "total_records": 5,
      "reliable_records": 3,
      "valid_for_mean": 3
    }
  }
}
```

### 5. Implementation Strategy

#### Phase 1: Core Calculation Function
1. **Create helper function**: `calculate_weighted_mean_prevalence()`
2. **Create filter function**: `get_valid_prevalence_records()`
3. **Add metadata tracking**: Record calculation details

#### Phase 2: Integration
1. **Modify disease loop**: Add weighted mean calculation
2. **Update data structure**: Add new fields to disease2prevalence
3. **Update statistics**: Track valid records for mean calculation

#### Phase 3: Validation & Testing
1. **Unit tests**: Test calculation logic with known data
2. **Integration tests**: Verify end-to-end processing
3. **Data validation**: Check results against manual calculations

## Technical Considerations

### 1. Performance Impact
- **Minimal**: Simple mathematical operations
- **Memory**: ~50MB additional for metadata (estimated)
- **Processing time**: +1-2 seconds for 16K records

### 2. Edge Cases Handling

#### No Valid Records
```python
# All records are "Cases/families" or "Unknown"
mean_prevalence_per_million = 0.0
valid_records_count = 0
```

#### Single Valid Record
```python
# Only one record with per_million_estimate > 0
mean_prevalence_per_million = single_record_prevalence
valid_records_count = 1
```

#### Zero Reliability Scores
```python
# If all reliability scores are 0, use simple mean
if weight_sum == 0:
    return sum(prevalences) / len(prevalences)
```

### 3. Data Quality Implications

#### High Confidence Cases
- Multiple records with high reliability scores
- Consistent prevalence estimates across records
- Mean provides robust estimate

#### Low Confidence Cases
- Few records with low reliability scores
- Highly variable prevalence estimates
- Mean may not be representative

### 4. Backwards Compatibility
- **Existing files**: All current functionality preserved
- **New field**: Optional field, doesn't break existing consumers
- **API compatibility**: Existing field names unchanged

## Testing Strategy

### 1. Unit Tests
```python
def test_weighted_mean_calculation():
    # Test with known data
    records = [
        {"per_million_estimate": 100, "reliability_score": 8.0},
        {"per_million_estimate": 200, "reliability_score": 6.0},
        {"per_million_estimate": 300, "reliability_score": 4.0}
    ]
    # Expected: (100*8 + 200*6 + 300*4) / (8+6+4) = 2800/18 = 155.56
    assert calculate_weighted_mean_prevalence(records) == 155.56
```

### 2. Integration Tests
```python
def test_disease_level_calculation():
    # Test with real disease data
    disease_data = load_disease_prevalence("166024")
    assert "mean_prevalence_per_million" in disease_data
    assert disease_data["mean_prevalence_metadata"]["valid_records_count"] >= 0
```

### 3. Data Validation
```python
def test_mean_prevalence_ranges():
    # Verify all means are within expected ranges
    for disease in all_diseases:
        mean_prev = disease["mean_prevalence_per_million"]
        assert 0 <= mean_prev <= 1000  # Max for rare diseases
```

## Documentation Updates Required

### 1. Main Documentation
- **Update**: `docs/prevalence_preprocessing.md`
- **Add**: Weighted mean calculation section
- **Update**: Data structure examples
- **Add**: New statistics and metrics

### 2. API Documentation
- **Update**: Disease2Prevalence schema
- **Add**: New field descriptions
- **Update**: Usage examples

### 3. Research Integration
- **Update**: Research prioritization examples
- **Add**: Weighted mean usage in scoring
- **Document**: Comparison with most_reliable_prevalence

## Migration & Rollout Plan

### Phase 1: Development (Week 1)
- Implement core calculation functions
- Add unit tests
- Update data structures

### Phase 2: Integration (Week 2)
- Integrate with main processing pipeline
- Add integration tests
- Verify data quality

### Phase 3: Validation (Week 3)
- Run on full dataset
- Validate results against manual calculations
- Performance testing

### Phase 4: Documentation (Week 4)
- Update all documentation
- Create usage examples
- Update research integration guides

## Real-World Examples

### Analysis Results
From the current dataset of 6,317 diseases:
- **926 diseases** have multiple valid prevalence records (14.7%)
- **5,391 diseases** have single or no valid records (85.3%)

### Example 1: Alpha-mannosidosis (OrphaCode: 61)
**Current Data**: 7 valid prevalence records  
**Weighted Mean**: 2.93 per million  

| Record | Prevalence | Reliability | Weight Contribution |
|--------|------------|-------------|-------------------|
| 1 | 5.0 per million | 8.0 | 40.0 |
| 2 | 0.5 per million | 9.8 | 4.9 |
| 3 | 5.0 per million | 6.8 | 34.0 |
| 4 | 0.5 per million | 9.8 | 4.9 |
| 5 | 5.0 per million | 9.8 | 49.0 |
| 6 | 5.0 per million | 9.8 | 49.0 |
| 7 | 0.5 per million | 9.8 | 4.9 |

**Calculation**: (5.0×8.0 + 0.5×9.8 + 5.0×6.8 + 0.5×9.8 + 5.0×9.8 + 5.0×9.8 + 0.5×9.8) / (8.0+9.8+6.8+9.8+9.8+9.8+9.8) = 186.70 / 63.80 = **2.93 per million**

### Example 2: Aspartylglucosaminuria (OrphaCode: 93)
**Current Data**: 3 valid prevalence records  
**Weighted Mean**: 20.00 per million  

| Record | Prevalence | Reliability | Weight Contribution |
|--------|------------|-------------|-------------------|
| 1 | 5.0 per million | 9.8 | 49.0 |
| 2 | 5.0 per million | 9.8 | 49.0 |
| 3 | 50.0 per million | 9.8 | 490.0 |

**Calculation**: (5.0×9.8 + 5.0×9.8 + 50.0×9.8) / (9.8+9.8+9.8) = 588.0 / 29.4 = **20.00 per million**

### Example 3: Beta-mannosidosis (OrphaCode: 118)
**Current Data**: 4 valid prevalence records  
**Weighted Mean**: 5.00 per million  

All 4 records have identical values: 5.0 per million with reliability 9.8  
**Calculation**: (5.0×9.8×4) / (9.8×4) = 196.0 / 39.2 = **5.00 per million**

### Business Value Demonstrated
1. **Consolidation**: Instead of 7 different prevalence estimates, Alpha-mannosidosis gets one representative value (2.93 per million)
2. **Quality Weighting**: Higher reliability scores (9.8) have more influence than lower ones (6.8)
3. **Consistency**: Identical records produce expected results (Beta-mannosidosis)
4. **Outlier Handling**: High values (50.0) are weighted by reliability, not ignored

## Success Metrics

### Technical Metrics
- **Processing time**: <10% increase
- **Memory usage**: <20% increase
- **Data quality**: 100% of diseases have valid mean_prevalence_per_million

### Business Metrics
- **Research utility**: Single prevalence estimate per disease
- **Data consistency**: Reduced variance in prevalence estimates
- **Quality weighting**: Higher reliability scores influence results appropriately

## Risk Assessment

### Low Risk
- **Backwards compatibility**: No breaking changes
- **Algorithm complexity**: Simple weighted mean
- **Performance impact**: Minimal additional processing

### Medium Risk
- **Data interpretation**: Users may misunderstand weighted vs. most reliable
- **Quality assumptions**: Reliability scores may not perfectly reflect data quality

### Mitigation Strategies
- **Clear documentation**: Explain calculation method and limitations
- **Metadata inclusion**: Provide transparency on calculation details
- **Validation**: Cross-check results with domain experts 