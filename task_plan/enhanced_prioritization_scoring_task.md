# Enhanced Rare Disease Prioritization Scoring System - Task Plan

## Task Overview

Enhance the existing rare disease prioritization script (`core/services/raredisease_prioritization.py`) with advanced scoring methods, flexible configuration, and improved data usage options per criterion.

## Current State Analysis

### Existing Implementation
- **Configuration Location**: `conf/raredisease_prioritization.yaml` 
- **Script Location**: `core/services/raredisease_prioritization.py`
- **Basic scoring**: Simple discrete and binary scoring methods
- **Global scoring configuration**: Single normalization method for all criteria

### Available Curated Data Sources
- **Clinical Trials**: All trials, EU trials, Spanish trials per disease
- **Drugs**: All tradename drugs, USA drugs, EU drugs per disease  
- **Prevalence**: Discrete classes (">1/1000" to "<1/1000000", "Unknown")
- **Genes**: Disease-to-genes mapping (monogenic vs polygenic distinction)
- **Disease Lists**: 665 metabolic diseases with orpha_codes

## Required Enhancements

### 1. Configuration Structure Improvements

#### 1.1 Move Configuration Location
- **FROM**: `conf/raredisease_prioritization.yaml`
- **TO**: `core/services/conf/raredisease_prioritization.yaml`
- **Rationale**: Better organization - configuration closer to service implementation

#### 1.2 Per-Criterion Scoring Configuration
**Current (Global)**:
```yaml
scoring:
  normalization_method: "percentile"
  handle_missing_data: "zero_score"
```

**Enhanced (Per-Criterion)**:
```yaml
criteria:
  prevalence:
    scoring:
      method: "discrete_class_mapping"
      handle_missing_data: "zero_score"
      normalization_method: "percentile"  # if needed
  clinical_trials:
    scoring:
      method: "winsorized_min_max_scaling"  # value/user_max * scale_factor
      max: 100  # User-defined maximum (winsorized)
      scale_factor: 10
      handle_missing_data: "zero_score"
  orpha_drugs:
    scoring:
      method: "reverse_winsorized_min_max_scaling"  # (1 - value/user_max) * scale_factor
      max: 10  # User-defined maximum drugs threshold (winsorized)
      scale_factor: 10
      handle_missing_data: "max_score"  # 10 for no drugs = high priority
```

### 2. New Scoring Methods Implementation

#### 2.1 Core Scoring Methods
- **`winsorized_min_max_scaling`**: `value/user_defined_max * scale_factor` 
  - Use case: Clinical trials (more trials = higher score)
  - Formula: `score = (disease_value / user_defined_max) * scale_factor`
  - Config: `max` parameter set by user, values capped at max (winsorized)

- **`reverse_winsorized_min_max_scaling`**: `(1 - value/user_defined_max) * scale_factor`
  - Use case: Drugs (fewer drugs = higher priority)  
  - Formula: `score = (1 - disease_value / user_defined_max) * scale_factor`
  - Config: `max` parameter set by user, values capped at max (winsorized)

- **`discrete_class_mapping`**: Pre-defined class-to-score mapping
  - Use case: Prevalence classes
  - Formula: Direct lookup from predefined mapping

- **`percentile_rank`**: Existing percentile-based normalization
- **`binary`**: Existing binary scoring (0 or 10)

#### 2.2 Compound Scoring Methods
For criteria with multiple data sources (e.g., drugs):
```yaml
orpha_drugs:
  scoring:
    method: "compound_weighted"
    components:
      - data_source: "eu_tradename_drugs"
        weight: 0.8
        scoring_method: "reverse_winsorized_min_max_scaling"
        max: 10
        scale_factor: 10
      - data_source: "usa_medical_products" 
        weight: 0.2
        scoring_method: "reverse_winsorized_min_max_scaling"
        max: 20
        scale_factor: 10
    final_formula: "weighted_sum"  # sum(component_score * weight)
```

### 3. Data Usage Configuration

#### 3.1 Per-Criterion Data Source Selection
Add `data_usage` configuration for each criterion:

```yaml
criteria:
  clinical_trials:
    data_usage:
      source_preference: "spanish_trials"  # spanish_trials, eu_trials, all_trials
      fallback: "eu_trials"
      
  orpha_drugs:
    data_usage:
      use_eu_tradenames: true
      use_usa_tradenames: false  
      use_eu_medical_products: true
      use_usa_medical_products: false
      compound_scoring: true
      
  prevalence:
    data_usage:
      source: "curated_prevalence_classes"
      fallback_unknown: "zero_score"
```

#### 3.2 Available Data Sources Mapping
- **Clinical Trials**: `spanish_trials`, `eu_trials`, `all_trials`
- **Drugs**: `eu_tradenames`, `usa_tradenames`, `all_tradenames`, `eu_medical_products`, `usa_medical_products`
- **Prevalence**: `curated_prevalence_classes`
- **Genes**: `disease_genes` (monogenic/polygenic classification)

### 4. Implementation Requirements

#### 4.1 Core Scoring Engine Enhancement
**Location**: `core/services/raredisease_prioritization.py`

**New Methods to Implement**:
```python
def winsorized_min_max_scaling(self, values: List[float], max_value: float, scale_factor: float = 10) -> List[float]:
    """Winsorized min-max scaling using value/user_max * scale_factor formula"""
    
def reverse_winsorized_min_max_scaling(self, values: List[float], max_value: float, scale_factor: float = 10) -> List[float]:
    """Reverse winsorized min-max scaling using (1 - value/user_max) * scale_factor formula"""
    
def compound_weighted_scoring(self, criterion_config: Dict, orpha_code: str) -> float:
    """Calculate weighted compound score from multiple data sources"""
    
def get_data_source_value(self, data_source: str, orpha_code: str) -> Union[int, float]:
    """Retrieve value from specified data source"""
```

#### 4.2 Conditional Scoring Logic
Implement scoring method selection using conditional logic:
```python
def score_criterion(self, criterion_name: str, orpha_code: str) -> float:
    config = self.config['criteria'][criterion_name]
    method = config['scoring']['method']
    
    if method == "winsorized_min_max_scaling":
        return self.winsorized_min_max_scaling(...)
    elif method == "reverse_winsorized_min_max_scaling":
        return self.reverse_winsorized_min_max_scaling(...)
    elif method == "compound_weighted":
        return self.compound_weighted_scoring(...)
    elif method == "discrete_class_mapping":
        return self.discrete_class_scoring(...)
    else:
        raise ValueError(f"Unknown scoring method: {method}")
```

#### 4.3 Data Source Client Integration
**Required Clients**:
- `CuratedClinicalTrialsClient` - Access to spanish/eu/all trials
- `CuratedDrugsClient` - Access to tradename/medical product data
- `CuratedPrevalenceClient` - Access to prevalence classes
- `CuratedGeneClient` - Access to gene data

### 5. Configuration Schema Validation

#### 5.1 Enhanced YAML Schema
```yaml
# New enhanced configuration structure
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
      max: 100  # User-defined maximum trials
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
        - data_source: "usa_medical_products"
          weight: 0.2
          scoring_method: "reverse_winsorized_min_max_scaling"
          max: 20
          scale_factor: 10
      handle_missing_data: "max_score"
    data_usage:
      use_eu_tradenames: true
      use_usa_tradenames: false
      use_medical_products: true
      compound_scoring: true
```

### 6. Testing Strategy

#### 6.1 Unit Tests
- Test each scoring method with known inputs/outputs
- Test compound scoring calculations
- Test data source selection logic

#### 6.2 Integration Tests  
- Test full scoring pipeline with enhanced configuration
- Test fallback mechanisms for missing data
- Validate output consistency with legacy scoring

#### 6.3 Validation Tests
- Compare top 10 diseases with current implementation
- Verify scoring explanations/justifications remain accurate
- Test edge cases (no data, maximum values, zero values)

### 7. Deliverables

#### 7.1 Enhanced Configuration
- **File**: `core/services/conf/raredisease_prioritization.yaml`
- **Features**: Per-criterion scoring, data usage options, compound scoring

#### 7.2 Enhanced Script
- **File**: `core/services/raredisease_prioritization.py`  
- **Features**: Multiple scoring methods, conditional logic, compound scoring

#### 7.3 Documentation
- **File**: `task_plan/scoring_methods_analysis.md`
- **Content**: Analysis of available scoring methods per criterion

### 8. Implementation Priority

#### Phase 1: Core Infrastructure
1. Move configuration to `core/services/conf/`
2. Implement per-criterion scoring configuration parsing
3. Add conditional scoring method selection

#### Phase 2: Scoring Methods
1. Implement `norm2max` and `inverse_norm2max` methods
2. Implement compound weighted scoring
3. Add data source selection logic

#### Phase 3: Integration & Testing
1. Integrate new scoring methods with existing pipeline
2. Update justification generation for new methods
3. Comprehensive testing and validation

#### Phase 4: Documentation & Validation
1. Create scoring methods analysis document
2. Validate results against current implementation
3. Performance testing and optimization

## Success Criteria

1. **Flexibility**: Each criterion can use different scoring methods
2. **Accuracy**: Drug scoring correctly prioritizes diseases with fewer therapies
3. **Transparency**: Justifications clearly explain scoring rationale
4. **Maintainability**: Configuration-driven approach allows easy adjustments
5. **Performance**: No significant performance degradation vs current implementation

## Open Questions for Clarification

1. **Medical Products vs Tradenames**: Should medical products have different scoring weight than tradenames?
2. **Fallback Strategy**: How should the system handle diseases missing from preferred data sources?
3. **Validation Threshold**: What percentage difference from current results is acceptable?
4. **Configuration Validation**: Should we implement schema validation for the enhanced YAML?

## Timeline Estimate

- **Phase 1**: 2-3 days (configuration restructuring)
- **Phase 2**: 3-4 days (scoring methods implementation)  
- **Phase 3**: 2-3 days (integration & testing)
- **Phase 4**: 1-2 days (documentation & validation)
- **Total**: 8-12 days 