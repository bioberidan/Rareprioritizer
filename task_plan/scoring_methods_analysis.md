# Scoring Methods Analysis for Rare Disease Prioritization

## Executive Summary

This document analyzes the available scoring methods for each criterion in the rare disease prioritization system, based on the curated data structures found in the repository. The analysis considers data availability, distribution patterns, and optimal scoring strategies to achieve the SOW objectives.

## Data Landscape Analysis

### Available Curated Data Assets

#### Clinical Trials (`data/04_curated/clinical_trials/`)
- **Spanish Trials**: 73 diseases with trials, 317 total unique trials
- **EU Trials**: Same coverage as Spanish (100% overlap observed)
- **All Trials**: Global trial coverage
- **Data Structure**: Disease → List of NCT IDs
- **Coverage**: High (100% for metabolic diseases with trials)

#### Drug Therapies (`data/04_curated/orpha/orphadata/`)
- **EU Tradename Drugs**: 29 diseases, limited coverage
- **USA Tradename Drugs**: 133 diseases, broader coverage
- **Medical Products**: 401 diseases (USA), 49 diseases (EU)
- **Data Structure**: Disease → List of drug IDs
- **Coverage**: Variable by region and product type

#### Prevalence (`data/04_curated/orpha/orphadata/`)
- **Coverage**: 532/665 diseases (80.0%)
- **Classes**: 6 discrete categories from ">1/1000" to "<1/1000000" plus "Unknown"
- **Distribution**: Heavily skewed toward rare classes (<1/1000000: 392 diseases)
- **Data Quality**: Curated with fallback mechanisms (birth prevalence, cases/families)

#### Genes (`data/04_curated/orpha/orphadata/`)
- **Coverage**: 549/665 diseases (82.6%)
- **Monogenic Diseases**: 479 diseases (1 gene)
- **Polygenic Diseases**: 70 diseases (multiple genes)
- **Gene Associations**: 820 total, 656 unique genes
- **Quality**: Filtered for disease-causing associations only

## Criterion-Specific Scoring Method Analysis

### 1. Prevalence and Population of Patients

#### Current Implementation: Discrete Class Mapping ✅
```yaml
scoring:
  method: "discrete_class_mapping"
  class_mapping:
    ">1 / 1000": 10      # 2 diseases
    "6-9 / 10 000": 9    # 3 diseases  
    "1-5 / 10 000": 8    # 11 diseases
    "1-9 / 100 000": 6   # 50 diseases
    "1-9 / 1 000 000": 3 # 74 diseases
    "<1 / 1 000 000": 2  # 392 diseases
```

#### Alternative Methods Considered:

**A) Population-Based Scoring**
- Formula: `estimated_patients_spain / spanish_population * adjustment_factor`
- **Pros**: Directly quantifies patient burden
- **Cons**: Requires population calculation, estimation errors
- **Recommendation**: Keep as future enhancement

**B) Prevalence Rank Scoring**
- Formula: `percentile_rank(prevalence_class) * 10`
- **Pros**: Continuous scoring, relative ranking
- **Cons**: Less interpretable than discrete classes
- **Recommendation**: Not recommended - loses clinical meaning

**✅ Recommended**: Keep **discrete class mapping** - aligns with SOW requirement for EU rare disease definition, clinically meaningful thresholds.

### 2. Socioeconomic Impact

#### Current Implementation: Mock Scoring (10.0)
```yaml
scoring:
  method: "mock_maximum"
  mock_value: 10.0
```

#### Proposed Scoring Methods:

**A) Evidence-Based Tiered Scoring** ⭐ (Recommended)
```yaml
scoring:
  method: "evidence_tiered"
  evidence_levels:
    "spanish_cost_study": 10      # Peer-reviewed Spanish study
    "european_cost_study": 7      # EU/comparable country study  
    "patient_organization_data": 5 # FEDER quantitative reports
    "qualitative_description": 3  # Literature qualitative impact
    "no_evidence": 0              # No data available
```

**B) Web Search Score Aggregation**
- Formula: `sum(study_quality_scores) / max_possible_score * 10`
- **Pros**: Uses available web search data
- **Cons**: Requires quality assessment automation
- **Data Source**: `data/02_preprocess/websearch/` directories

**✅ Recommended**: **Evidence-based tiered scoring** when data becomes available, mock scoring for initial implementation.

### 3. Approved Therapies (Drugs)

#### Current Implementation: Binary (Has Drugs = 0, No Drugs = 10)

#### Enhanced Methods Analysis:

**A) Reverse Winsorized Min-Max Scaling (Compound)** ⭐ (Recommended)
```yaml
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
  formula: "weighted_sum"
```

**Data Distribution Analysis**:
- **EU Tradenames**: 29 diseases, max 5 drugs (disease 79330)
- **USA Tradenames**: 133 diseases, max 7 drugs (disease 213)
- **EU Medical Products**: 49 diseases, varying coverage
- **USA Medical Products**: 401 diseases, broader coverage

**Scoring Examples**:
```python
# Disease with 0 drugs: score = (1 - 0/7) * 10 = 10.0
# Disease with 3 drugs: score = (1 - 3/7) * 10 = 5.7  
# Disease with 7 drugs: score = (1 - 7/7) * 10 = 0.0
```

**B) Therapy Gap Scoring**
- Formula: `(max_drugs_in_class - disease_drugs) / max_drugs_in_class * 10`
- **Pros**: Class-relative comparison
- **Cons**: Complex class definition required

**C) Availability Score** 
- Formula: `(eu_availability + usa_availability) / 2 * availability_weight`
- **Pros**: Considers geographic access
- **Cons**: Complex availability determination

**✅ Recommended**: **Compound weighted inverse norm2max** - prioritizes diseases with fewer therapies while considering both tradenames and medical products.

### 4. Clinical Trials in Spain

#### Current Implementation: Count-Based Scoring

#### Enhanced Methods Analysis:

**A) Winsorized Min-Max Scaling** ⭐ (Recommended)
```yaml
scoring:
  method: "winsorized_min_max_scaling"
  data_source: "spanish_trials"
  fallback: "eu_trials"
  max: 100  # User-defined maximum (winsorized)
  scale_factor: 10
  formula: "value/user_max * scale_factor"
```

**Data Distribution Analysis**:
- **Spanish Trials**: 317 total trials across 73 diseases
- **Max Trials per Disease**: 82 trials (disease 139 - Down syndrome)
- **Distribution**: Heavily skewed (few diseases with many trials)

**Scoring Examples**:
```python
# Disease with 82 trials: score = (82/82) * 10 = 10.0
# Disease with 10 trials: score = (10/82) * 10 = 1.2
# Disease with 0 trials: score = (0/82) * 10 = 0.0
```

**B) Log-Normalized Scoring**
- Formula: `log(trials + 1) / log(max_trials + 1) * 10`
- **Pros**: Reduces skewness impact
- **Cons**: Less intuitive interpretation

**C) Tiered Trial Scoring**
- Formula: Discrete ranges (0, 1-5, 6-15, 16+ trials)
- **Pros**: Simple interpretation
- **Cons**: Loses granularity

**✅ Recommended**: **Winsorized min-max scaling** with Spanish trials preference, EU trials fallback - directly rewards research activity intensity.

### 5. Gene Therapy Traceability

#### Current Implementation: Binary Monogenic vs Polygenic ✅

```yaml
scoring:
  method: "binary_monogenic"
  monogenic_score: 10    # Exactly 1 gene
  polygenic_score: 0     # Multiple genes  
  unknown_score: 0       # No genes identified
```

#### Alternative Methods Considered:

**A) Gene Druggability Scoring**
- Formula: `gene_druggability_score * monogenic_bonus`
- **Pros**: More sophisticated therapy prediction
- **Cons**: Requires external druggability database
- **Data Required**: Gene druggability annotations

**B) Gene Function Scoring**
- Formula: `function_category_score * expression_level`
- **Pros**: Biological relevance
- **Cons**: Complex annotation requirements

**C) Therapeutic Modality Scoring**
```yaml
scoring:
  method: "therapeutic_modality"
  modality_scores:
    "monogenic_membrane": 10    # Easy gene therapy target
    "monogenic_enzyme": 8       # Enzyme replacement possible
    "monogenic_nuclear": 6      # Complex gene therapy
    "polygenic": 0              # Not suitable
```

**✅ Recommended**: Keep **binary monogenic scoring** - aligns with SOW requirement, simple and clinically relevant for gene therapy feasibility.

### 6. National Research Capacity (Groups)

#### Current Implementation: Mock Scoring (10.0)

#### Proposed Scoring Methods:

**A) CIBERER Group Count** ⭐ (Recommended)
```yaml
scoring:
  method: "winsorized_min_max_scaling"
  data_source: "ciberer_groups"
  max: 20  # User-defined maximum groups (winsorized)
  scale_factor: 10
  formula: "active_groups/user_max * scale_factor"
```

**B) Publication-Based Scoring**
- Formula: `(recent_publications * impact_factor) / max_score * 10`
- **Data Source**: PubMed API integration
- **Pros**: Objective research output measure
- **Cons**: Complex implementation, impact factor bias

**C) Grant Funding Scoring**
- Formula: `total_funding / max_funding * 10`
- **Pros**: Direct research capacity measure  
- **Cons**: Funding data availability challenges

**✅ Recommended**: **CIBERER group count with norm2max** when data becomes available, mock scoring for initial implementation.

## Recommended Scoring Configuration

### Enhanced YAML Configuration
```yaml
# Recommended enhanced configuration
criteria:
  prevalence:
    scoring:
      method: "discrete_class_mapping"
      class_mapping:
        ">1/1000": 10
        "6-9/10000": 9  
        "1-5/10000": 8
        "1-9/100000": 6
        "1-9/1000000": 3
        "<1/1000000": 2
        "Unknown": 0
      handle_missing_data: "zero_score"

  clinical_trials:
    scoring:
      method: "winsorized_min_max_scaling"
      max: 100  # User-defined maximum trials (winsorized)
      scale_factor: 10
      handle_missing_data: "zero_score"
    data_usage:
      source_preference: "spanish_trials"
      fallback: "eu_trials"

  orpha_drugs:
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
      handle_missing_data: "max_score"  # No drugs = high priority

  orpha_gene:
    scoring:
      method: "binary_monogenic" 
      monogenic_score: 10
      polygenic_score: 0
      unknown_score: 0
      handle_missing_data: "zero_score"

  socioeconomic:
    scoring:
      method: "mock_maximum"
      mock_value: 10.0  # Until evidence data available
      
  groups:
    scoring:
      method: "mock_maximum" 
      mock_value: 10.0  # Until CIBERER data available
```

## Implementation Priority Scoring

### High Priority (Immediate Implementation)
1. **Prevalence**: ✅ Already implemented correctly
2. **Clinical Trials**: Norm2max with Spanish preference
3. **Drugs**: Compound weighted inverse norm2max
4. **Genes**: ✅ Already implemented correctly

### Medium Priority (Next Phase)
1. **Socioeconomic**: Evidence-based tiered scoring
2. **Groups**: CIBERER group count scoring

### Low Priority (Future Enhancement)
1. **Prevalence**: Population-based calculations
2. **Drugs**: Therapy mechanism-specific scoring
3. **Genes**: Druggability-enhanced scoring

## Quality Assurance Metrics

### Data Quality Indicators
- **Coverage**: % diseases with data per criterion
- **Completeness**: Missing data handling effectiveness
- **Consistency**: Score distribution analysis
- **Validity**: Clinical expert review of top-ranked diseases

### Validation Approach
1. **Cross-validation**: Compare rankings with clinical expert judgment
2. **Sensitivity analysis**: Test weight variations impact
3. **Robustness testing**: Handle edge cases and missing data
4. **Performance monitoring**: Track scoring time and memory usage

## Conclusion

The proposed enhanced scoring system provides:

1. **Flexibility**: Multiple scoring methods per criterion
2. **Accuracy**: Data-driven scoring aligned with SOW objectives  
3. **Transparency**: Clear justification for each scoring decision
4. **Scalability**: Configuration-driven approach for easy modifications
5. **Robustness**: Proper handling of missing data and edge cases

The compound weighted approach for drugs and winsorized min-max scaling for clinical trials directly address the user's requirements while maintaining the proven discrete mapping for prevalence and binary scoring for genes. 