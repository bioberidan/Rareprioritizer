# Prevalence Data Outlier Removal Strategies

**Date**: December 2024  
**Context**: Rare disease prevalence data analysis  
**Objective**: Identify appropriate methods for detecting and handling outliers in epidemiological data

## 📊 **Current Data Characteristics**

### **Prevalence Distribution Profile**
- **Range**: 0.5 to 500.0 per million (artificially capped)
- **Mean**: 29.17 per million, **Median**: 0.50 per million
- **Distribution**: Highly right-skewed (median << mean)
- **Standard deviation**: 84.62 (high variability)
- **Sample size**: 4,924 diseases with prevalence estimates

### **Known Artifacts**
- **67 diseases capped at 500 per million** (artificial ceiling)
- **Geographic bias**: Population-specific prevalences applied globally
- **Birth vs population prevalence** confusion in some records
- **Reliability variation**: 0-10 score with 86.7% considered reliable (≥6.0)

## 🔬 **Statistical Outlier Detection Methods**

### **1. Interquartile Range (IQR) Method**
**Approach**: Traditional box plot method using quartiles
- **Formula**: Outliers if value < Q1 - 1.5×IQR or value > Q3 + 1.5×IQR
- **Results**: 21.3% outliers (1,047 diseases) above 11.75 per million
- **Pros**: Simple, well-understood, identifies extreme values
- **Cons**: Too aggressive for skewed distributions, many false positives
- **Recommendation**: ❌ **Not suitable** for highly skewed prevalence data

### **2. Z-Score Method**
**Approach**: Standard deviations from mean
- **Formula**: |z| = |x - μ| / σ, threshold typically 3.0
- **Results**: 5.1% outliers (252 diseases) above 284.3 per million
- **Pros**: Based on normal distribution theory
- **Cons**: Assumes normal distribution, sensitive to extreme values
- **Recommendation**: ⚠️ **Limited use** - prevalence data is not normally distributed

### **3. Modified Z-Score (Median-based)**
**Approach**: Uses median and MAD (Median Absolute Deviation)
- **Formula**: Modified z = 0.6745 × (x - median) / MAD
- **Results**: 30.3% outliers (1,490 diseases) - too aggressive
- **Pros**: More robust to outliers than standard z-score
- **Cons**: High false positive rate for skewed data
- **Recommendation**: ❌ **Not suitable** for prevalence data

### **4. Percentile-Based Thresholds**
**Approach**: Use empirical distribution percentiles
- **95th percentile**: 293.2 per million (247 diseases above)
- **99th percentile**: 500.0 per million (0 diseases above due to cap)
- **Pros**: Data-driven, no distributional assumptions
- **Cons**: Arbitrary cutoff choice
- **Recommendation**: ✅ **Useful** for defining high-prevalence categories

### **5. Log-Scale Analysis**
**Approach**: Transform to log space before outlier detection
- **Rationale**: Prevalence data often log-normally distributed
- **Results**: 6.9% outliers (341 diseases) above 125.1 per million
- **Pros**: More appropriate for skewed biological data
- **Cons**: Still requires arbitrary threshold choice
- **Recommendation**: ✅ **Recommended** for statistical outlier detection

## 🏥 **Medical Domain-Based Approaches**

### **1. Artificial Ceiling Detection**
**Target**: Identify system-imposed caps
- **Method**: Flag diseases at exact threshold values (e.g., 500.0 per million)
- **Results**: 67 diseases identified as artificially capped
- **Action**: Keep data but flag as "capped" rather than remove
- **Recommendation**: ✅ **Essential** - preserve but annotate

### **2. Data Quality Outliers**
**Target**: High prevalence with poor data quality
- **Criteria**: Prevalence >100 per million AND reliability <6.0
- **Results**: 31 diseases identified
- **Rationale**: Suspicious combination of high impact + low confidence
- **Action**: Flag for manual review or exclude from analysis
- **Recommendation**: ✅ **High priority** for review

### **3. Single-Record High Prevalence**
**Target**: High estimates based on single studies
- **Criteria**: Prevalence >100 per million AND only 1 record
- **Results**: 88 diseases identified
- **Rationale**: Insufficient evidence for high-impact claim
- **Action**: Flag as "insufficient evidence" or exclude
- **Recommendation**: ✅ **Important** quality filter

### **4. Geographic Outliers**
**Target**: Population-specific prevalences misapplied globally
- **Criteria**: High prevalence without worldwide data
- **Results**: 206 diseases with prevalence >100 and no worldwide records
- **Examples**: Trehalase deficiency (Greenland-specific), Welander myopathy (Sweden-specific)
- **Action**: Stratify by geography or flag as population-specific
- **Recommendation**: ✅ **Critical** for epidemiological accuracy

### **5. Birth vs Population Prevalence Confusion**
**Target**: Birth defects with population-wide prevalence claims
- **Identification**: Prevalence type = "Prevalence at birth" but high population estimate
- **Examples**: Hydrops fetalis, hemolytic disease of newborn
- **Action**: Separate birth prevalence from population prevalence
- **Recommendation**: ✅ **Essential** medical distinction

## 📈 **Epidemiological Reasonableness Criteria**

### **1. Rare Disease Definition Compliance**
**EU Definition**: <5 per 10,000 (500 per million)
**US Definition**: <1 per 200,000 (~5 per million)
- **Action**: Flag diseases >500 per million as "not rare"
- **Consideration**: May be legitimate high-prevalence conditions
- **Recommendation**: ✅ **Flag** but don't automatically exclude

### **2. Public Health Impact Thresholds**
**Ultra-high impact**: >300 per million (>0.03% population)
**High impact**: 100-300 per million (0.01-0.03% population)
**Moderate impact**: 10-100 per million (0.001-0.01% population)
- **Results**: 85 ultra-high, 286 high, 4,553 moderate/low
- **Action**: Separate analysis categories by impact level
- **Recommendation**: ✅ **Useful** for prioritization

### **3. Literature Consistency Check**
**Method**: Compare prevalence estimates with published literature
- **High-prevalence diseases to verify**: Scleroderma, MELAS, Down syndrome
- **Database sources**: PubMed, clinical guidelines, health registries
- **Action**: Manual validation of extreme values
- **Recommendation**: ✅ **Gold standard** for validation

## 🎯 **Recommended Outlier Removal Strategy**

### **Phase 1: Automatic Flagging**
1. **Artificial caps**: Flag exact values at processing thresholds (500.0)
2. **Data quality**: Flag high prevalence (>100) + low reliability (<6.0)
3. **Insufficient evidence**: Flag high prevalence (>100) + single record
4. **Geographic bias**: Flag high prevalence without worldwide data

### **Phase 2: Domain Expert Review**
1. **Medical validation**: Expert review of prevalences >300 per million
2. **Literature verification**: Cross-check against published estimates
3. **Geographic stratification**: Separate population-specific from global estimates
4. **Prevalence type correction**: Distinguish birth from population prevalence

### **Phase 3: Statistical Filtering**
1. **Log-scale outliers**: Remove statistical outliers in log space (>2.5 SD)
2. **Percentile-based**: Consider 99th+ percentile for extreme outlier removal
3. **Conservative approach**: Err on side of inclusion with clear flagging

### **Phase 4: Stratified Analysis**
1. **Clean dataset**: Conservative prevalence estimates for primary analysis
2. **High-prevalence subset**: Separate analysis of diseases >100 per million
3. **Flagged dataset**: Transparent reporting of all exclusions and flags
4. **Sensitivity analysis**: Compare results with/without outlier removal

## ⚖️ **Removal vs Flagging Decision Framework**

### **Remove From Analysis:**
- **Demonstrably wrong**: Obvious data entry errors
- **Artificial values**: System-generated caps or defaults
- **Insufficient evidence**: Single low-quality record with extreme claim
- **Wrong population**: Birth prevalence misapplied as population prevalence

### **Flag But Keep:**
- **High but plausible**: Medically possible high prevalences
- **Geographic-specific**: Population-specific high prevalences  
- **Lower confidence**: High prevalence with moderate data quality
- **Borderline rare**: Diseases approaching rare disease definition limits

### **Manual Review Required:**
- **Literature discrepancy**: Prevalence differs significantly from literature
- **Medical implausibility**: Prevalence seems medically unreasonable
- **Data quality concerns**: Mixed signals on reliability
- **Novel findings**: Previously unknown high-prevalence diseases

## 📋 **Implementation Considerations**

### **Transparency Requirements**
- **Document all decisions**: Clear rationale for each exclusion
- **Provide excluded data**: Make filtered data available separately
- **Sensitivity analysis**: Show impact of different outlier thresholds
- **Audit trail**: Track all automated and manual filtering steps

### **Validation Approach**
- **Cross-validation**: Compare with external prevalence databases
- **Expert consultation**: Involve epidemiologists and clinicians
- **Iterative refinement**: Update criteria based on validation results
- **Performance metrics**: Track false positive/negative rates

### **Clinical Context**
- **Preserve medical relevance**: Don't remove clinically important diseases
- **Consider comorbidities**: Some conditions may have legitimately high prevalence
- **Account for population changes**: Prevalence may change over time
- **Respect geographic variation**: Acknowledge genuine population differences

## 🏁 **Final Recommendations**

### **Primary Strategy: Multi-layered Approach**
1. **Conservative statistical filtering**: Remove only clear statistical impossibilities
2. **Strong domain-knowledge filtering**: Apply medical and epidemiological criteria
3. **Transparent flagging system**: Mark questionable but plausible estimates
4. **Stratified reporting**: Separate analysis for different confidence levels

### **Quality Over Quantity**
- **Prioritize reliability**: Better to have fewer, high-quality estimates
- **Preserve uncertainty**: Don't artificially reduce apparent precision
- **Enable user choice**: Provide multiple dataset versions with different filtering
- **Support research needs**: Balance statistical rigor with clinical utility

**Result**: A robust, medically-informed approach to outlier handling that maintains scientific integrity while preserving epidemiologically important information. 