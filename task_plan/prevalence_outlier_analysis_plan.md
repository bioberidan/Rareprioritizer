# Prevalence Data Outlier Analysis Plan

**Date**: December 2024  
**Objective**: Create comprehensive outlier analysis for prevalence data with density plots and summary documentation

## 🎯 **Task Overview**

### **Primary Deliverables**
1. **Density Plot Grid**: Multi-panel visualization showing prevalence distributions with different outlier detection methods
2. **Outlier Summary**: Comprehensive `outlier.md` file documenting findings, methods, and recommendations
3. **Statistical Analysis**: Detailed analysis of outlier patterns and their impact on prevalence data

### **Data Source**
- **Path**: `data/03_processed/orpha/orphadata/orpha_prevalence/`
- **Main Data**: `disease2prevalence.json` (37MB) with `mean_value_per_million` estimates
- **Controller**: `PrevalenceController` for data access and filtering

---

## 📊 **Implementation Architecture**

### **1. Script Location**
Following the recommended architecture pattern:
- **Main Script**: `etl/05_stats/orpha/orphadata/outlier_analysis.py`
- **Output Directory**: `results/etl/orpha/orphadata/prevalence/outlier_analysis/`

### **2. Data Access Pattern**
```python
from core.datastore.orpha.orphadata.prevalence_client import PrevalenceController

controller = PrevalenceController()
controller.preload_all()

# Extract prevalence values with disease context
prevalence_data = []
for orpha_code, disease_data in controller._disease2prevalence.items():
    mean_prevalence = disease_data.get('mean_value_per_million', 0.0)
    if mean_prevalence > 0:
        prevalence_data.append({
            'orpha_code': orpha_code,
            'disease_name': disease_data.get('disease_name', ''),
            'prevalence': mean_prevalence,
            'records_count': len(disease_data.get('prevalence_records', [])),
            'reliability_score': disease_data.get('most_reliable_prevalence', {}).get('reliability_score', 0)
        })
```

---

## 🔬 **Outlier Detection Methods**

### **Method 1: Interquartile Range (IQR)**
```python
def detect_iqr_outliers(data):
    """Traditional box plot method"""
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = [x for x in data if x < lower_bound or x > upper_bound]
    return outliers, lower_bound, upper_bound
```

### **Method 2: Z-Score Method**
```python
def detect_zscore_outliers(data, threshold=3.0):
    """Standard deviations from mean"""
    mean = np.mean(data)
    std = np.std(data)
    z_scores = [(x - mean) / std for x in data]
    
    outliers = [data[i] for i, z in enumerate(z_scores) if abs(z) > threshold]
    return outliers, mean - threshold * std, mean + threshold * std
```

### **Method 3: Modified Z-Score (MAD)**
```python
def detect_modified_zscore_outliers(data, threshold=3.5):
    """Median Absolute Deviation based"""
    median = np.median(data)
    mad = np.median([abs(x - median) for x in data])
    modified_z_scores = [0.6745 * (x - median) / mad for x in data]
    
    outliers = [data[i] for i, z in enumerate(modified_z_scores) if abs(z) > threshold]
    return outliers, median - threshold * mad / 0.6745, median + threshold * mad / 0.6745
```

### **Method 4: Log-Normal Distribution**
```python
def detect_log_normal_outliers(data, threshold=2.5):
    """Log-space outlier detection"""
    log_data = [np.log(x + 1) for x in data if x > 0]  # +1 to handle zeros
    mean_log = np.mean(log_data)
    std_log = np.std(log_data)
    
    outliers = []
    for x in data:
        if x > 0:
            log_x = np.log(x + 1)
            z_score = abs(log_x - mean_log) / std_log
            if z_score > threshold:
                outliers.append(x)
    
    return outliers, np.exp(mean_log - threshold * std_log), np.exp(mean_log + threshold * std_log)
```

### **Method 5: Percentile-Based Thresholds**
```python
def detect_percentile_outliers(data, lower_percentile=5, upper_percentile=95):
    """Empirical distribution percentiles"""
    lower_bound = np.percentile(data, lower_percentile)
    upper_bound = np.percentile(data, upper_percentile)
    
    outliers = [x for x in data if x < lower_bound or x > upper_bound]
    return outliers, lower_bound, upper_bound
```

### **Method 6: Medical Domain Outliers**
```python
def detect_medical_domain_outliers(prevalence_data):
    """Domain-specific outlier detection"""
    outliers = []
    
    for item in prevalence_data:
        prevalence = item['prevalence']
        reliability = item['reliability_score']
        records_count = item['records_count']
        
        # High prevalence + low reliability
        if prevalence > 100 and reliability < 6.0:
            outliers.append(item)
        
        # High prevalence + single record
        elif prevalence > 100 and records_count == 1:
            outliers.append(item)
        
        # Exceeds rare disease definition
        elif prevalence > 500:  # EU definition
            outliers.append(item)
    
    return outliers
```

---

## 🎨 **Density Plot Grid Design**

### **Grid Layout: 3x2 Panel Structure**
```python
def create_outlier_density_grid(prevalence_data):
    """Create comprehensive density plot grid"""
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle('Prevalence Data Outlier Analysis - Density Distributions', 
                 fontsize=16, fontweight='bold')
    
    prevalence_values = [item['prevalence'] for item in prevalence_data]
    
    # Panel 1: Raw Distribution + IQR Outliers
    ax1 = axes[0, 0]
    plot_distribution_with_outliers(ax1, prevalence_values, detect_iqr_outliers, 
                                   'IQR Method', 'Interquartile Range')
    
    # Panel 2: Z-Score Outliers
    ax2 = axes[0, 1]
    plot_distribution_with_outliers(ax2, prevalence_values, detect_zscore_outliers, 
                                   'Z-Score Method', 'Standard Deviations')
    
    # Panel 3: Modified Z-Score (MAD)
    ax3 = axes[1, 0]
    plot_distribution_with_outliers(ax3, prevalence_values, detect_modified_zscore_outliers, 
                                   'Modified Z-Score', 'Median Absolute Deviation')
    
    # Panel 4: Log-Normal Distribution
    ax4 = axes[1, 1]
    plot_distribution_with_outliers(ax4, prevalence_values, detect_log_normal_outliers, 
                                   'Log-Normal Method', 'Log-Space Analysis')
    
    # Panel 5: Percentile-Based
    ax5 = axes[2, 0]
    plot_distribution_with_outliers(ax5, prevalence_values, detect_percentile_outliers, 
                                   'Percentile Method', '5th-95th Percentile')
    
    # Panel 6: Medical Domain Analysis
    ax6 = axes[2, 1]
    plot_medical_domain_analysis(ax6, prevalence_data)
    
    plt.tight_layout()
    plt.savefig('results/etl/orpha/orphadata/prevalence/outlier_analysis/outlier_density_grid.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
```

### **Individual Panel Plotting Function**
```python
def plot_distribution_with_outliers(ax, data, detection_method, title, subtitle):
    """Plot density distribution with outlier highlights"""
    
    # Get outliers using the detection method
    outliers, lower_bound, upper_bound = detection_method(data)
    
    # Create density plot
    ax.hist(data, bins=50, density=True, alpha=0.7, color='skyblue', 
            label=f'All Data (n={len(data)})')
    
    # Add outlier highlights
    if outliers:
        ax.hist(outliers, bins=30, density=True, alpha=0.8, color='red', 
                label=f'Outliers (n={len(outliers)})')
    
    # Add threshold lines
    if lower_bound is not None and lower_bound > 0:
        ax.axvline(lower_bound, color='orange', linestyle='--', 
                   label=f'Lower: {lower_bound:.1f}')
    if upper_bound is not None and upper_bound < max(data):
        ax.axvline(upper_bound, color='orange', linestyle='--', 
                   label=f'Upper: {upper_bound:.1f}')
    
    # Formatting
    ax.set_title(f'{title}\n{subtitle}', fontweight='bold')
    ax.set_xlabel('Prevalence (per million)')
    ax.set_ylabel('Density')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Add statistics text
    stats_text = f'Mean: {np.mean(data):.1f}\nMedian: {np.median(data):.1f}\n'
    stats_text += f'Outliers: {len(outliers)} ({len(outliers)/len(data)*100:.1f}%)'
    ax.text(0.7, 0.9, stats_text, transform=ax.transAxes, 
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
```

---

## 📋 **Summary Report Generation**

### **Outlier.md Structure**
```python
def generate_outlier_markdown_summary(analysis_results):
    """Generate comprehensive outlier analysis summary"""
    
    markdown_content = f"""# Prevalence Data Outlier Analysis Summary

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset**: {analysis_results['total_diseases']} diseases with prevalence estimates  
**Data Source**: `data/03_processed/orpha/orphadata/orpha_prevalence/`

## 📊 **Executive Summary**

{generate_executive_summary(analysis_results)}

## 🔬 **Outlier Detection Methods Comparison**

{generate_methods_comparison(analysis_results)}

## 📈 **Statistical Analysis Results**

{generate_statistical_analysis(analysis_results)}

## 🏥 **Medical Domain Findings**

{generate_medical_domain_findings(analysis_results)}

## 🎯 **Recommendations**

{generate_recommendations(analysis_results)}

## 📁 **Generated Files**

- `outlier_density_grid.png` - Comprehensive density plot grid
- `outlier_summary_statistics.json` - Detailed statistical results
- `outlier_flagged_diseases.json` - List of flagged diseases by method
- `outlier_analysis_report.pdf` - Full analysis report

## 🔗 **Data Quality Impact**

{generate_data_quality_impact(analysis_results)}

---

*Generated by RarePrioritizer Outlier Analysis System*
*For questions or issues, refer to the project documentation*
"""
    
    return markdown_content
```

### **Key Summary Sections**

#### **Executive Summary Generation**
```python
def generate_executive_summary(results):
    total_diseases = results['total_diseases']
    outlier_counts = results['outlier_counts']
    
    summary = f"""
### Key Findings

- **Total Diseases Analyzed**: {total_diseases} with valid prevalence estimates
- **Prevalence Range**: {results['min_prevalence']:.1f} to {results['max_prevalence']:.1f} per million
- **Distribution**: Highly right-skewed (median: {results['median']:.1f}, mean: {results['mean']:.1f})

### Outlier Detection Results

| Method | Outliers Detected | Percentage | Threshold |
|--------|------------------|------------|-----------|
| IQR Method | {outlier_counts['iqr']} | {outlier_counts['iqr']/total_diseases*100:.1f}% | {results['iqr_threshold']:.1f} |
| Z-Score | {outlier_counts['zscore']} | {outlier_counts['zscore']/total_diseases*100:.1f}% | {results['zscore_threshold']:.1f} |
| Modified Z-Score | {outlier_counts['mad']} | {outlier_counts['mad']/total_diseases*100:.1f}% | {results['mad_threshold']:.1f} |
| Log-Normal | {outlier_counts['lognormal']} | {outlier_counts['lognormal']/total_diseases*100:.1f}% | {results['lognormal_threshold']:.1f} |
| Percentile | {outlier_counts['percentile']} | {outlier_counts['percentile']/total_diseases*100:.1f}% | {results['percentile_threshold']:.1f} |
| Medical Domain | {outlier_counts['medical']} | {outlier_counts['medical']/total_diseases*100:.1f}% | Domain Rules |

### Consensus Outliers
- **High Confidence**: {results['consensus_outliers']['high']} diseases flagged by ≥4 methods
- **Medium Confidence**: {results['consensus_outliers']['medium']} diseases flagged by 2-3 methods
"""
    return summary
```

---

## 🚀 **Implementation Steps**

### **Phase 1: Data Extraction and Preparation**
1. Initialize `PrevalenceController` and load all data
2. Extract prevalence values with disease context
3. Filter for valid estimates (> 0 per million)
4. Prepare data structures for analysis

### **Phase 2: Outlier Detection**
1. Implement all 6 detection methods
2. Apply each method to the dataset
3. Collect outlier classifications and thresholds
4. Identify consensus outliers (flagged by multiple methods)

### **Phase 3: Visualization Generation**
1. Create density plot grid (3x2 panels)
2. Generate individual method visualizations
3. Add statistical annotations and thresholds
4. Save high-resolution plots

### **Phase 4: Analysis and Reporting**
1. Generate comprehensive statistical analysis
2. Create detailed markdown summary
3. Export flagged diseases lists
4. Generate data quality impact assessment

### **Phase 5: Validation and Review**
1. Cross-reference with medical literature
2. Validate extreme outliers manually
3. Document findings and recommendations
4. Create final report package

---

## 📁 **Output File Structure**

```
results/etl/orpha/orphadata/prevalence/outlier_analysis/
├── outlier_density_grid.png           # Main density plot grid
├── outlier.md                         # Comprehensive summary
├── outlier_summary_statistics.json    # Statistical results
├── outlier_flagged_diseases.json      # Flagged diseases by method
├── method_comparison.png              # Method comparison chart
├── consensus_outliers.json            # High-confidence outliers
├── medical_domain_flags.json          # Medical domain violations
└── data_quality_impact.json           # Quality assessment
```

---

## 🔧 **Technical Requirements**

### **Dependencies**
- `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`
- `PrevalenceController` from `core.datastore.orpha.orphadata.prevalence_client`
- Standard Python libraries: `json`, `datetime`, `pathlib`

### **Performance Considerations**
- Dataset size: ~5,000 diseases with prevalence estimates
- Memory usage: <1GB for full analysis
- Processing time: ~2-3 minutes for complete analysis
- Output file size: ~50MB total

### **Error Handling**
- Graceful handling of missing data
- Validation of outlier detection results
- Logging of all processing steps
- Fallback mechanisms for failed visualizations

---

## 📊 **Expected Results**

### **Quantitative Outputs**
- Outlier counts and percentages by method
- Statistical thresholds and confidence intervals
- Consensus analysis of multi-method flagged diseases
- Data quality impact assessment

### **Qualitative Insights**
- Medical coherence of outlier classifications
- Geographic bias patterns in high-prevalence diseases
- Reliability score correlation with outlier status
- Recommendations for data quality improvement

This comprehensive plan provides a robust framework for prevalence data outlier analysis with both statistical rigor and medical domain expertise, generating actionable insights for the rare disease prioritization system. 