# Scoring Function Modifications Task

## Overview

This document specifies the exact modifications needed to implement the enhanced scoring methods in `core/services/raredisease_prioritization.py` based on the corrected requirements and scientific terminology.

## Critical Corrections Applied

### 1. Prevalence Classes Correction ✅
**Actual classes from curated data:**
```python
PREVALENCE_CLASS_MAPPING = {
    ">1 / 1000": 10,        # 2 diseases
    "6-9 / 10 000": 9,      # 3 diseases  
    "1-5 / 10 000": 8,      # 11 diseases
    "1-9 / 100 000": 6,     # 50 diseases
    "1-9 / 1 000 000": 3,   # 74 diseases
    "<1 / 1 000 000": 2     # 392 diseases
}
```
**Note**: Removed "Unknown" class - missing data handled separately.

### 2. Scientific Terminology Upgrade ✅
- `norm2max` → `winsorized_min_max_scaling`
- `inverse_norm2max` → `reverse_winsorized_min_max_scaling`

### 3. User-Defined Maximum Values ✅
- Maximum values now configurable by user, not auto-calculated from data
- Each scoring method has `max` and `scale_factor` parameters

## Required Function Modifications

### 1. Update `score_orpha_drugs()` Function

**Current Implementation**: Binary scoring (has drugs = 0, no drugs = 10)

**Required Changes**: Implement compound weighted reverse winsorized min-max scaling

```python
def score_orpha_drugs(self, orpha_code: str) -> float:
    """
    Score drug criterion using compound weighted reverse winsorized min-max scaling
    
    Formula: weighted_sum of reverse_winsorized_min_max_scaling per data source
    - EU Tradenames: weight=0.8, max=10, scale_factor=10
    - Medical Products: weight=0.2, max=20, scale_factor=10
    
    Returns:
        Normalized score (0-10) - Higher score for fewer available drugs
    """
    criteria_config = self.config['criteria']['orpha_drugs']
    
    if criteria_config['mock']:
        return criteria_config['mock_value']
    
    # Get compound scoring configuration
    components = criteria_config['scoring']['components']
    total_score = 0.0
    
    for component in components:
        data_source = component['data_source']
        weight = component['weight']
        max_value = component['max']
        scale_factor = component['scale_factor']
        
        # Get drug count for this data source
        if data_source == "eu_tradename_drugs":
            drug_count = len(self.drugs_client.get_eu_tradename_drugs(orpha_code))
        elif data_source == "medical_products_eu":
            drug_count = len(self.drugs_client.get_eu_medical_products(orpha_code))
        else:
            drug_count = 0
            
        # Apply inverse linear scaling: (1 - value/max) * scale_factor
        if drug_count >= max_value:
            component_score = 0.0  # Saturated - no unmet need
        else:
            component_score = (1 - drug_count / max_value) * scale_factor
            
        # Add weighted component
        total_score += component_score * weight
        
    return min(total_score, 10.0)  # Cap at maximum score
```

### 2. Update `score_clinical_trials()` Function

**Current Implementation**: Simple count-based scoring

**Required Changes**: Implement winsorized min-max scaling with user-defined maximum

```python
def score_clinical_trials(self, orpha_code: str) -> float:
    """
    Score clinical trials criterion using winsorized min-max scaling
    
    Formula: (trial_count / user_max) * scale_factor
    - Max: 100 (user-configured)
    - Scale factor: 10
    - Data source: Spanish trials (fallback to EU trials)
    
    Returns:
        Normalized score (0-10) - Higher score for more trials
    """
    criteria_config = self.config['criteria']['clinical_trials']
    
    if criteria_config['mock']:
        return criteria_config['mock_value']
        
    # Get configuration
    max_value = criteria_config['scoring']['max']  # User-defined: 100
    scale_factor = criteria_config['scoring']['scale_factor']  # 10
    data_usage = criteria_config['data_usage']
    
    # Get trial count with fallback
    if data_usage['source_preference'] == 'spanish_trials':
        trial_count = len(self.clinical_trials_client.get_spanish_trials(orpha_code))
        if trial_count == 0 and 'fallback' in data_usage:
            trial_count = len(self.clinical_trials_client.get_eu_trials(orpha_code))
    else:
        trial_count = len(self.clinical_trials_client.get_all_trials(orpha_code))
    
    # Apply linear scaling: (value / max) * scale_factor
    if trial_count >= max_value:
        return scale_factor  # Saturated at maximum score
    else:
        return (trial_count / max_value) * scale_factor
```

### 3. Update `score_prevalence()` Function

**Current Implementation**: Discrete class mapping (mostly correct)

**Required Changes**: Update class mapping with correct spacing

```python
def score_prevalence(self, orpha_code: str) -> float:
    """
    Score prevalence criterion using discrete class mapping
    
    Uses actual prevalence classes from curated data with proper spacing
    
    Returns:
        Normalized score (0-10) based on prevalence class
    """
    criteria_config = self.config['criteria']['prevalence']
    
    if criteria_config['mock']:
        return criteria_config['mock_value']
    
    # Get prevalence class
    prevalence_class = self.prevalence_client.get_prevalence_class(orpha_code)
    
    # Updated class mapping with correct spacing
    class_mapping = {
        ">1 / 1000": 10,        # Most prevalent rare diseases
        "6-9 / 10 000": 9,      
        "1-5 / 10 000": 8,      
        "1-9 / 100 000": 6,     
        "1-9 / 1 000 000": 3,   
        "<1 / 1 000 000": 2     # Ultra-rare diseases
    }
    
    return class_mapping.get(prevalence_class, 0)  # 0 for missing data
```

### 4. Update `score_groups()` Function

**Current Implementation**: Mock scoring (10.0)

**Required Changes**: Implement winsorized min-max scaling for CIBERER groups (future)

```python
def score_groups(self, orpha_code: str) -> float:
    """
    Score research groups criterion using winsorized min-max scaling
    
    Formula: (group_count / user_max) * scale_factor
    - Max: 20 (user-configured) 
    - Scale factor: 10
    - Data source: CIBERER groups (when available)
    
    Returns:
        Normalized score (0-10) - Higher score for more research groups
    """
    criteria_config = self.config['criteria']['groups']
    
    if criteria_config['mock']:
        return criteria_config['mock_value']
        
    # Future implementation when CIBERER data available
    max_value = criteria_config['scoring']['max']  # User-defined: 20
    scale_factor = criteria_config['scoring']['scale_factor']  # 10
    
    # Get group count (placeholder for future implementation)
    group_count = self.groups_client.get_ciberer_groups_count(orpha_code)
    
    # Apply winsorized min-max scaling
    if group_count >= max_value:
        return scale_factor
    else:
        return (group_count / max_value) * scale_factor
```

### 5. Add New Utility Methods

**Required**: Generic scaling methods for reusability

```python
def winsorized_min_max_scaling(self, value: float, max_value: float, scale_factor: float = 10) -> float:
    """
    Generic winsorized min-max scaling: (value / max_value) * scale_factor
    
    Args:
        value: Input value to scale
        max_value: User-defined maximum value (winsorized)
        scale_factor: Output scaling factor (default: 10)
        
    Returns:
        Scaled value, capped at scale_factor
    """
    if value >= max_value:
        return scale_factor  # Winsorized at maximum
    return (value / max_value) * scale_factor

def reverse_winsorized_min_max_scaling(self, value: float, max_value: float, scale_factor: float = 10) -> float:
    """
    Generic reverse winsorized min-max scaling: (1 - value / max_value) * scale_factor
    
    Args:
        value: Input value to scale (higher values = lower scores)
        max_value: User-defined maximum value (winsorized)
        scale_factor: Output scaling factor (default: 10)
        
    Returns:
        Reverse scaled value, capped at scale_factor
    """
    if value >= max_value:
        return 0.0  # Winsorized at minimum score
    return (1 - value / max_value) * scale_factor
```

## Configuration File Updates

### Move Configuration Location
- **FROM**: `conf/raredisease_prioritization.yaml`
- **TO**: `core/services/conf/raredisease_prioritization.yaml`

### Enhanced Configuration Structure

```yaml
# Enhanced configuration with per-criterion scoring
criteria:
  prevalence:
    path: "data/04_curated/orpha/orphadata"
    mock: false
    mock_value: 10.0
    weight: 0.20
    scoring:
      method: "discrete_class_mapping"
      class_mapping:
        ">1 / 1000": 10
        "6-9 / 10 000": 9
        "1-5 / 10 000": 8
        "1-9 / 100 000": 6
        "1-9 / 1 000 000": 3
        "<1 / 1 000 000": 2
      handle_missing_data: "zero_score"
    data_usage:
      source: "curated_prevalence_classes"

  clinical_trials:
    path: "data/04_curated/clinical_trials"
    mock: false
    mock_value: 0.0
    weight: 0.10
    scoring:
      method: "winsorized_min_max_scaling"
      max: 100  # User-defined maximum trials (winsorized)
      scale_factor: 10
      handle_missing_data: "zero_score"
    data_usage:
      source_preference: "spanish_trials"
      fallback: "eu_trials"

  orpha_drugs:
    path: "data/04_curated/orpha/orphadata"
    mock: false
    mock_value: 10.0
    weight: 0.25
    scoring:
      method: "compound_weighted"
      components:
        - data_source: "eu_tradename_drugs"
          weight: 0.8
          scoring_method: "reverse_winsorized_min_max_scaling"
          max: 10
          scale_factor: 10
        - data_source: "medical_products_eu"
          weight: 0.2
          scoring_method: "reverse_winsorized_min_max_scaling"
          max: 20
          scale_factor: 10
      handle_missing_data: "max_score"
    data_usage:
      use_eu_tradenames: true
      use_medical_products: true

  groups:
    path: "data/02_preprocess/websearch"
    mock: true  # Until CIBERER data available
    mock_value: 10.0
    weight: 0.10
    scoring:
      method: "winsorized_min_max_scaling"
      max: 20  # User-defined maximum groups (winsorized)
      scale_factor: 10
      handle_missing_data: "zero_score"
    data_usage:
      source: "ciberer_groups"
```

## Justification Updates

### Enhanced Justification Generation

```python
def generate_justification(self, disease_score: DiseaseScore) -> str:
    """Updated justification with correct terminology and data sources"""
    
    justifications = []
    orpha_code = disease_score.orpha_code
    
    # Prevalence justification (updated classes)
    prevalence_class = self.prevalence_client.get_prevalence_class(orpha_code)
    if prevalence_class:
        justifications.append(f"Prevalence class: {prevalence_class}")
    
    # Clinical trials justification (winsorized min-max scaling)
    spanish_trials = len(self.clinical_trials_client.get_spanish_trials(orpha_code))
    if spanish_trials > 0:
        justifications.append(f"Active Spanish clinical research with {spanish_trials} trial(s)")
        
    # Drug justification (compound reverse winsorized min-max scaling)
    eu_drugs = len(self.drugs_client.get_eu_tradename_drugs(orpha_code))
    medical_products = len(self.drugs_client.get_eu_medical_products(orpha_code))
    
    if eu_drugs == 0 and medical_products == 0:
        justifications.append("No approved therapies available (high unmet medical need)")
    else:
        therapy_desc = []
        if eu_drugs > 0:
            therapy_desc.append(f"{eu_drugs} EU tradename drug(s)")
        if medical_products > 0:
            therapy_desc.append(f"{medical_products} medical product(s)")
        justifications.append(f"Limited therapeutic options: {', '.join(therapy_desc)}")
    
    return "; ".join(justifications)
```

## Testing Requirements

### Unit Tests for New Scoring Methods

```python
def test_winsorized_min_max_scaling():
    """Test winsorized min-max scaling with edge cases"""
    prioritizer = RareDiseasePrioritizer(config)
    
    # Normal case
    assert prioritizer.winsorized_min_max_scaling(50, 100, 10) == 5.0
    
    # Winsorized case (capped at max)
    assert prioritizer.winsorized_min_max_scaling(120, 100, 10) == 10.0
    
    # Zero case
    assert prioritizer.winsorized_min_max_scaling(0, 100, 10) == 0.0

def test_reverse_winsorized_min_max_scaling():
    """Test reverse winsorized min-max scaling with edge cases"""
    prioritizer = RareDiseasePrioritizer(config)
    
    # No drugs = maximum score
    assert prioritizer.reverse_winsorized_min_max_scaling(0, 10, 10) == 10.0
    
    # Max drugs = minimum score (winsorized)
    assert prioritizer.reverse_winsorized_min_max_scaling(10, 10, 10) == 0.0
    
    # Partial drugs
    assert prioritizer.reverse_winsorized_min_max_scaling(3, 10, 10) == 7.0
```

## Implementation Priority

### Phase 1: Core Methods (2-3 days)
1. ✅ Update prevalence class mapping
2. ✅ Implement `winsorized_min_max_scaling()` and `reverse_winsorized_min_max_scaling()` utilities
3. ✅ Update `score_clinical_trials()` with winsorized min-max scaling
4. ✅ Update `score_orpha_drugs()` with compound weighted scoring

### Phase 2: Configuration (1-2 days)
1. ✅ Move configuration file to `core/services/conf/`
2. ✅ Update YAML structure with per-criterion scoring
3. ✅ Add user-defined `max` and `scale_factor` parameters

### Phase 3: Integration & Testing (2-3 days)
1. ✅ Update justification generation
2. ✅ Implement comprehensive unit tests
3. ✅ Validate against current implementation results

## Success Metrics

1. **Drugs Scoring**: Diseases with 0 drugs score ~10, diseases with max drugs score ~0 (reverse winsorized)
2. **Clinical Trials Scoring**: Linear relationship between trial count and score up to user max (winsorized)
3. **Prevalence Scoring**: Correct mapping with actual prevalence classes
4. **Configuration Flexibility**: User can easily adjust max values without code changes
5. **Scientific Accuracy**: Terminology aligns with statistical normalization best practices

## Risk Mitigation

1. **Backward Compatibility**: Keep old configuration format supported during transition
2. **Data Validation**: Validate user-defined max values are reasonable
3. **Performance**: Ensure compound scoring doesn't significantly slow execution
4. **Testing**: Comprehensive edge case testing for all scoring methods 