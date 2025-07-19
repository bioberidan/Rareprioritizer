# IQR Outlier Analysis Plan - Hyperparameter Sensitivity Study

**Date**: December 2024  
**Objective**: Comprehensive analysis of IQR outlier detection methods with multiple hyperparameters for prevalence data

## 🎯 **Task Overview**

### **Primary Deliverables**
1. **IQR Sensitivity Grid**: Multi-panel visualization showing different IQR methods and parameters
2. **Hyperparameter Comparison**: Analysis of how different IQR parameters affect outlier detection
3. **Method Evaluation**: Comparison of traditional vs modified IQR approaches
4. **Optimization Recommendations**: Best IQR parameters for prevalence data

### **Data Source**
- **Path**: `data/03_processed/orpha/orphadata/orpha_prevalence/`
- **Output**: `results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only/`

---

## 📊 **IQR Method Variations**

### **1. Classic IQR with Different Multipliers**
```python
def iqr_classic_variants(data):
    """Test different IQR multipliers"""
    multipliers = [1.0, 1.5, 2.0, 2.5, 3.0]
    results = {}
    
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    
    for mult in multipliers:
        lower_bound = Q1 - mult * IQR
        upper_bound = Q3 + mult * IQR
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        
        results[f'IQR_{mult}x'] = {
            'outliers': outliers,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'count': len(outliers),
            'percentage': len(outliers) / len(data) * 100
        }
    
    return results
```

### **2. Different Quartile Calculation Methods**
```python
def iqr_quartile_methods(data):
    """Test different quartile calculation methods"""
    methods = {
        'linear': 'linear',          # Default numpy
        'lower': 'lower',            # Conservative
        'higher': 'higher',          # Aggressive
        'midpoint': 'midpoint',      # Moderate
        'nearest': 'nearest'         # Rounded
    }
    
    results = {}
    
    for name, method in methods.items():
        Q1 = np.percentile(data, 25, method=method)
        Q3 = np.percentile(data, 75, method=method)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        
        results[f'IQR_quartile_{name}'] = {
            'outliers': outliers,
            'Q1': Q1,
            'Q3': Q3,
            'IQR': IQR,
            'count': len(outliers)
        }
    
    return results
```

### **3. Modified IQR with Different Percentiles**
```python
def iqr_percentile_variants(data):
    """Test IQR-like methods with different percentile ranges"""
    percentile_pairs = [
        (10, 90, 'P10-P90'),   # Wider range
        (15, 85, 'P15-P85'),   # Moderate range
        (20, 80, 'P20-P80'),   # Narrower range
        (25, 75, 'P25-P75'),   # Classic IQR
        (5, 95, 'P5-P95'),     # Very wide range
    ]
    
    results = {}
    
    for lower_p, upper_p, name in percentile_pairs:
        P_lower = np.percentile(data, lower_p)
        P_upper = np.percentile(data, upper_p)
        IPR = P_upper - P_lower  # Inter-Percentile Range
        
        lower_bound = P_lower - 1.5 * IPR
        upper_bound = P_upper + 1.5 * IPR
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        
        results[name] = {
            'outliers': outliers,
            'lower_percentile': P_lower,
            'upper_percentile': P_upper,
            'range': IPR,
            'count': len(outliers)
        }
    
    return results
```

### **4. Robust IQR Methods**
```python
def iqr_robust_variants(data):
    """Test robust IQR variants"""
    results = {}
    
    # Trimmed IQR (remove extreme 5% before calculation)
    trimmed_data = np.trim_zeros(np.sort(data)[int(0.05*len(data)):int(0.95*len(data))])
    Q1_trim = np.percentile(trimmed_data, 25)
    Q3_trim = np.percentile(trimmed_data, 75)
    IQR_trim = Q3_trim - Q1_trim
    
    outliers_trimmed = [x for x in data if x < Q1_trim - 1.5 * IQR_trim or x > Q3_trim + 1.5 * IQR_trim]
    
    results['IQR_trimmed'] = {
        'outliers': outliers_trimmed,
        'count': len(outliers_trimmed)
    }
    
    # Winsorized IQR (cap extreme values)
    from scipy.stats import mstats
    winsorized_data = mstats.winsorize(data, limits=[0.05, 0.05])
    Q1_wins = np.percentile(winsorized_data, 25)
    Q3_wins = np.percentile(winsorized_data, 75)
    IQR_wins = Q3_wins - Q1_wins
    
    outliers_winsorized = [x for x in data if x < Q1_wins - 1.5 * IQR_wins or x > Q3_wins + 1.5 * IQR_wins]
    
    results['IQR_winsorized'] = {
        'outliers': outliers_winsorized,
        'count': len(outliers_winsorized)
    }
    
    # Median-based IQR (use median instead of mean for centering)
    median = np.median(data)
    mad = np.median([abs(x - median) for x in data])
    
    # Convert MAD to IQR-like bounds
    iqr_like_bound = 1.5 * mad * 1.4826  # Scale factor to match normal distribution
    outliers_median = [x for x in data if abs(x - median) > iqr_like_bound]
    
    results['IQR_median_based'] = {
        'outliers': outliers_median,
        'count': len(outliers_median)
    }
    
    return results
```

### **5. Adaptive IQR Methods**
```python
def iqr_adaptive_variants(data):
    """Test adaptive IQR methods that adjust based on data characteristics"""
    results = {}
    
    # Skewness-adjusted IQR
    from scipy.stats import skew
    data_skewness = skew(data)
    
    # Adjust multiplier based on skewness
    if data_skewness > 2:  # Highly skewed
        multiplier = 2.5
    elif data_skewness > 1:  # Moderately skewed
        multiplier = 2.0
    else:  # Low skew
        multiplier = 1.5
    
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    
    outliers_adaptive = [x for x in data if x < Q1 - multiplier * IQR or x > Q3 + multiplier * IQR]
    
    results['IQR_skewness_adaptive'] = {
        'outliers': outliers_adaptive,
        'skewness': data_skewness,
        'multiplier_used': multiplier,
        'count': len(outliers_adaptive)
    }
    
    # Sample size adjusted IQR
    n = len(data)
    if n < 100:
        sample_multiplier = 1.0  # Conservative for small samples
    elif n < 1000:
        sample_multiplier = 1.5  # Standard
    else:
        sample_multiplier = 2.0  # Liberal for large samples
    
    outliers_sample_adj = [x for x in data if x < Q1 - sample_multiplier * IQR or x > Q3 + sample_multiplier * IQR]
    
    results['IQR_sample_size_adaptive'] = {
        'outliers': outliers_sample_adj,
        'sample_size': n,
        'multiplier_used': sample_multiplier,
        'count': len(outliers_sample_adj)
    }
    
    return results
```

---

## 🎨 **Visualization Design**

### **Grid Layout: 3x3 Panel Structure**
```python
def create_iqr_analysis_grid(prevalence_data):
    """Create comprehensive IQR analysis grid"""
    
    fig, axes = plt.subplots(3, 3, figsize=(20, 18))
    fig.suptitle('IQR Outlier Detection - Hyperparameter Sensitivity Analysis', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    prevalence_values = [item['prevalence'] for item in prevalence_data]
    
    # Row 1: Classic IQR Multipliers
    multipliers = [1.5, 2.0, 2.5]
    for i, mult in enumerate(multipliers):
        plot_iqr_variant(axes[0, i], prevalence_values, 'classic', mult,
                        f'Classic IQR {mult}x', f'Multiplier = {mult}')
    
    # Row 2: Percentile Variants
    percentile_methods = [('P10-P90', 10, 90), ('P20-P80', 20, 80), ('P5-P95', 5, 95)]
    for i, (name, lower, upper) in enumerate(percentile_methods):
        plot_percentile_variant(axes[1, i], prevalence_values, lower, upper,
                               f'{name} Method', f'Percentiles: {lower}-{upper}')
    
    # Row 3: Robust Methods
    robust_methods = ['trimmed', 'winsorized', 'adaptive']
    for i, method in enumerate(robust_methods):
        plot_robust_variant(axes[2, i], prevalence_values, method,
                           f'Robust IQR: {method.title()}', f'{method.title()} approach')
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig
```

### **Comparison Summary Plot**
```python
def create_iqr_comparison_summary():
    """Create summary comparison of all IQR methods"""
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('IQR Methods Comparison Summary', fontsize=16, fontweight='bold')
    
    # Panel 1: Outlier count by method
    plot_outlier_counts_comparison(ax1)
    
    # Panel 2: Sensitivity analysis (parameter vs outlier count)
    plot_parameter_sensitivity(ax2)
    
    # Panel 3: Method performance matrix
    plot_method_performance_matrix(ax3)
    
    # Panel 4: Recommendations heatmap
    plot_recommendations_heatmap(ax4)
    
    return fig
```

---

## 📊 **Analysis Components**

### **1. Sensitivity Analysis**
```python
def analyze_parameter_sensitivity(prevalence_data):
    """Analyze how sensitive IQR is to parameter changes"""
    
    sensitivity_results = {
        'multiplier_sensitivity': {},
        'percentile_sensitivity': {},
        'method_stability': {}
    }
    
    prevalence_values = [item['prevalence'] for item in prevalence_data]
    
    # Test multiplier sensitivity
    multipliers = np.arange(1.0, 4.1, 0.25)  # 1.0 to 4.0 in 0.25 steps
    for mult in multipliers:
        outliers = detect_iqr_outliers_with_multiplier(prevalence_values, mult)
        sensitivity_results['multiplier_sensitivity'][mult] = len(outliers)
    
    # Test percentile sensitivity
    for lower_p in range(5, 26, 5):  # 5, 10, 15, 20, 25
        upper_p = 100 - lower_p
        outliers = detect_percentile_outliers(prevalence_values, lower_p, upper_p)
        sensitivity_results['percentile_sensitivity'][f'{lower_p}-{upper_p}'] = len(outliers)
    
    return sensitivity_results
```

### **2. Stability Analysis**
```python
def analyze_method_stability(prevalence_data):
    """Analyze stability of different IQR methods"""
    
    # Bootstrap analysis
    n_bootstrap = 1000
    stability_results = {}
    
    prevalence_values = [item['prevalence'] for item in prevalence_data]
    
    methods = ['classic_1.5', 'classic_2.0', 'percentile_10_90', 'trimmed', 'adaptive']
    
    for method in methods:
        outlier_counts = []
        
        for _ in range(n_bootstrap):
            # Bootstrap sample
            bootstrap_sample = np.random.choice(prevalence_values, 
                                              size=len(prevalence_values), 
                                              replace=True)
            
            # Apply method
            outliers = apply_iqr_method(bootstrap_sample, method)
            outlier_counts.append(len(outliers))
        
        stability_results[method] = {
            'mean_outliers': np.mean(outlier_counts),
            'std_outliers': np.std(outlier_counts),
            'cv': np.std(outlier_counts) / np.mean(outlier_counts),  # Coefficient of variation
            'min_outliers': np.min(outlier_counts),
            'max_outliers': np.max(outlier_counts)
        }
    
    return stability_results
```

### **3. Medical Relevance Assessment**
```python
def assess_medical_relevance(prevalence_data, iqr_results):
    """Assess medical relevance of different IQR methods"""
    
    medical_assessment = {}
    
    for method_name, method_results in iqr_results.items():
        outliers = method_results['outliers']
        
        # Find corresponding diseases
        outlier_diseases = []
        for item in prevalence_data:
            if item['prevalence'] in outliers:
                outlier_diseases.append(item)
        
        # Medical relevance metrics
        high_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] >= 8.0])
        low_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] < 6.0])
        single_record_outliers = len([d for d in outlier_diseases if d['records_count'] == 1])
        multiple_record_outliers = len([d for d in outlier_diseases if d['records_count'] > 1])
        
        medical_assessment[method_name] = {
            'total_outliers': len(outlier_diseases),
            'high_reliability_outliers': high_reliability_outliers,
            'low_reliability_outliers': low_reliability_outliers,
            'single_record_outliers': single_record_outliers,
            'multiple_record_outliers': multiple_record_outliers,
            'quality_ratio': high_reliability_outliers / max(len(outlier_diseases), 1),
            'evidence_ratio': multiple_record_outliers / max(len(outlier_diseases), 1)
        }
    
    return medical_assessment
```

---

## 📋 **Optimization Framework**

### **1. Multi-Criteria Evaluation**
```python
def evaluate_iqr_methods(prevalence_data):
    """Multi-criteria evaluation of IQR methods"""
    
    criteria = {
        'statistical_soundness': 0.3,    # Weight for statistical rigor
        'medical_relevance': 0.4,        # Weight for medical validity
        'stability': 0.2,                # Weight for method stability
        'interpretability': 0.1          # Weight for ease of interpretation
    }
    
    evaluation_results = {}
    
    # Run all IQR variants
    all_methods = {
        **iqr_classic_variants(prevalence_data),
        **iqr_percentile_variants(prevalence_data),
        **iqr_robust_variants(prevalence_data),
        **iqr_adaptive_variants(prevalence_data)
    }
    
    for method_name, method_results in all_methods.items():
        scores = calculate_method_scores(method_name, method_results, prevalence_data)
        
        # Weighted composite score
        composite_score = sum(scores[criterion] * weight for criterion, weight in criteria.items())
        
        evaluation_results[method_name] = {
            'scores': scores,
            'composite_score': composite_score,
            'rank': 0  # Will be filled after ranking
        }
    
    # Rank methods
    ranked_methods = sorted(evaluation_results.items(), 
                           key=lambda x: x[1]['composite_score'], 
                           reverse=True)
    
    for i, (method_name, results) in enumerate(ranked_methods):
        evaluation_results[method_name]['rank'] = i + 1
    
    return evaluation_results
```

### **2. Optimal Parameter Selection**
```python
def find_optimal_iqr_parameters(prevalence_data):
    """Find optimal IQR parameters for prevalence data"""
    
    optimization_results = {}
    
    # Grid search for optimal multiplier
    multipliers = np.arange(1.0, 4.1, 0.1)
    best_multiplier = None
    best_score = -np.inf
    
    for mult in multipliers:
        outliers = detect_iqr_outliers_with_multiplier(prevalence_data, mult)
        score = evaluate_outlier_quality(outliers, prevalence_data)
        
        if score > best_score:
            best_score = score
            best_multiplier = mult
    
    optimization_results['optimal_multiplier'] = {
        'value': best_multiplier,
        'score': best_score,
        'outlier_count': len(detect_iqr_outliers_with_multiplier(prevalence_data, best_multiplier))
    }
    
    # Find optimal percentile range
    best_percentile_range = None
    best_percentile_score = -np.inf
    
    for lower_p in range(5, 26, 5):
        upper_p = 100 - lower_p
        outliers = detect_percentile_outliers(prevalence_data, lower_p, upper_p)
        score = evaluate_outlier_quality(outliers, prevalence_data)
        
        if score > best_percentile_score:
            best_percentile_score = score
            best_percentile_range = (lower_p, upper_p)
    
    optimization_results['optimal_percentile_range'] = {
        'range': best_percentile_range,
        'score': best_percentile_score,
        'outlier_count': len(detect_percentile_outliers(prevalence_data, *best_percentile_range))
    }
    
    return optimization_results
```

---

## 📁 **Output Structure**

```
results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only/
├── iqr_sensitivity_grid.png           # 3x3 grid of IQR variants
├── iqr_comparison_summary.png         # 2x2 summary comparison
├── iqr_parameter_sensitivity.png      # Sensitivity analysis plots
├── iqr_method_evaluation.png          # Multi-criteria evaluation
├── iqr_analysis_summary.md            # Comprehensive summary
├── iqr_detailed_results.json          # All numerical results
├── iqr_optimal_parameters.json        # Optimization results
├── iqr_stability_analysis.json        # Bootstrap stability results
├── iqr_medical_assessment.json        # Medical relevance assessment
└── iqr_recommendations.json           # Final recommendations
```

---

## 🎯 **Expected Insights**

### **Key Research Questions**
1. **Parameter Sensitivity**: How does IQR outlier detection change with different multipliers?
2. **Method Robustness**: Which IQR variant is most stable across different data characteristics?
3. **Medical Validity**: Which IQR method best identifies medically meaningful outliers?
4. **Optimal Configuration**: What are the best IQR parameters for prevalence data?

### **Expected Findings**
- **Classical IQR (1.5x)**: Likely too aggressive for skewed prevalence data
- **Moderate IQR (2.0-2.5x)**: Better balance for biological data
- **Percentile methods**: May be more robust for non-normal distributions
- **Adaptive methods**: Could provide best performance by adjusting to data characteristics

### **Practical Recommendations**
- Recommended IQR multiplier for prevalence data
- Best percentile range for robust outlier detection
- Guidelines for method selection based on data characteristics
- Quality thresholds for medical relevance filtering

This comprehensive IQR analysis will provide definitive guidance on optimal outlier detection parameters for rare disease prevalence data. 