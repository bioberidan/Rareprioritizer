#!/usr/bin/env python3
"""
Prevalence Data Outlier Analysis Script

This script performs comprehensive outlier analysis on prevalence data using multiple
detection methods and generates density plots in grid format along with detailed
summary documentation.

Author: RarePrioritizer System
Date: December 2024
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import sys
import warnings
from typing import Dict, List, Tuple, Optional, Any
import logging
from scipy import stats

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PrevalenceOutlierAnalyzer:
    """Comprehensive outlier analysis for prevalence data"""
    
    def __init__(self, output_dir: str = "results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis"):
        """Initialize the outlier analyzer"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize controller
        self.controller = ProcessedPrevalenceClient()
        self.controller.preload_all()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Data containers
        self.prevalence_data = []
        self.analysis_results = {}
        self.outlier_methods = {}
        
        logger.info(f"Outlier analyzer initialized with output dir: {output_dir}")
    
    def extract_prevalence_data(self) -> None:
        """Extract prevalence data with disease context"""
        logger.info("Extracting prevalence data...")
        
        self.controller._ensure_disease2prevalence_loaded()
        
        for orpha_code, disease_data in self.controller._disease2prevalence.items():
            mean_prevalence = disease_data.get('mean_value_per_million', 0.0)
            if mean_prevalence > 0:  # Only include diseases with valid prevalence estimates
                
                # Get reliability score from most reliable prevalence record
                most_reliable = disease_data.get('most_reliable_prevalence', {})
                reliability_score = most_reliable.get('reliability_score', 0.0)
                
                # Get geographic info
                prevalence_records = disease_data.get('prevalence_records', [])
                has_worldwide = any(r.get('geographic_area') == 'Worldwide' for r in prevalence_records)
                
                self.prevalence_data.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name', ''),
                    'prevalence': mean_prevalence,
                    'records_count': len(prevalence_records),
                    'reliability_score': reliability_score,
                    'has_worldwide': has_worldwide,
                    'validated_records': len(disease_data.get('validated_prevalences', [])),
                    'regional_coverage': len(disease_data.get('regional_prevalences', {}))
                })
        
        logger.info(f"Extracted {len(self.prevalence_data)} diseases with valid prevalence estimates")
    
    def detect_iqr_outliers(self, data: List[float]) -> Tuple[List[float], float, float]:
        """Interquartile Range (IQR) outlier detection"""
        Q1 = np.percentile(data, 25)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        return outliers, lower_bound, upper_bound
    
    def detect_zscore_outliers(self, data: List[float], threshold: float = 3.0) -> Tuple[List[float], float, float]:
        """Z-Score outlier detection"""
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        if std_val == 0:
            return [], mean_val, mean_val
        
        z_scores = [(x - mean_val) / std_val for x in data]
        outliers = [data[i] for i, z in enumerate(z_scores) if abs(z) > threshold]
        
        return outliers, mean_val - threshold * std_val, mean_val + threshold * std_val
    
    def detect_modified_zscore_outliers(self, data: List[float], threshold: float = 3.5) -> Tuple[List[float], float, float]:
        """Modified Z-Score (MAD) outlier detection"""
        median_val = np.median(data)
        mad = np.median([abs(x - median_val) for x in data])
        
        if mad == 0:
            return [], median_val, median_val
        
        modified_z_scores = [0.6745 * (x - median_val) / mad for x in data]
        outliers = [data[i] for i, z in enumerate(modified_z_scores) if abs(z) > threshold]
        
        return outliers, median_val - threshold * mad / 0.6745, median_val + threshold * mad / 0.6745
    
    def detect_log_normal_outliers(self, data: List[float], threshold: float = 2.5) -> Tuple[List[float], float, float]:
        """Log-normal distribution outlier detection"""
        log_data = [np.log(x + 1) for x in data if x > 0]  # +1 to handle zeros
        
        if len(log_data) == 0:
            return [], 0, 0
        
        mean_log = np.mean(log_data)
        std_log = np.std(log_data)
        
        if std_log == 0:
            return [], np.exp(mean_log), np.exp(mean_log)
        
        outliers = []
        for x in data:
            if x > 0:
                log_x = np.log(x + 1)
                z_score = abs(log_x - mean_log) / std_log
                if z_score > threshold:
                    outliers.append(x)
        
        return outliers, np.exp(mean_log - threshold * std_log), np.exp(mean_log + threshold * std_log)
    
    def detect_percentile_outliers(self, data: List[float], lower_percentile: float = 5, upper_percentile: float = 95) -> Tuple[List[float], float, float]:
        """Percentile-based outlier detection"""
        lower_bound = np.percentile(data, lower_percentile)
        upper_bound = np.percentile(data, upper_percentile)
        
        outliers = [x for x in data if x < lower_bound or x > upper_bound]
        return outliers, lower_bound, upper_bound
    
    def detect_medical_domain_outliers(self, prevalence_data: List[Dict]) -> List[Dict]:
        """Medical domain-specific outlier detection"""
        outliers = []
        
        for item in prevalence_data:
            prevalence = item['prevalence']
            reliability = item['reliability_score']
            records_count = item['records_count']
            
            # High prevalence + low reliability
            if prevalence > 100 and reliability < 6.0:
                outliers.append({**item, 'reason': 'High prevalence + low reliability'})
            
            # High prevalence + single record
            elif prevalence > 100 and records_count == 1:
                outliers.append({**item, 'reason': 'High prevalence + single record'})
            
            # Exceeds rare disease definition (EU: 500 per million)
            elif prevalence > 500:
                outliers.append({**item, 'reason': 'Exceeds rare disease definition'})
            
            # Extremely high prevalence (>1000 per million = 0.1% of population)
            elif prevalence > 1000:
                outliers.append({**item, 'reason': 'Extremely high prevalence'})
        
        return outliers
    
    def run_outlier_detection(self) -> None:
        """Run all outlier detection methods"""
        logger.info("Running outlier detection methods...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Statistical methods
        iqr_outliers, iqr_lower, iqr_upper = self.detect_iqr_outliers(prevalence_values)
        zscore_outliers, zscore_lower, zscore_upper = self.detect_zscore_outliers(prevalence_values)
        mad_outliers, mad_lower, mad_upper = self.detect_modified_zscore_outliers(prevalence_values)
        log_outliers, log_lower, log_upper = self.detect_log_normal_outliers(prevalence_values)
        percentile_outliers, perc_lower, perc_upper = self.detect_percentile_outliers(prevalence_values)
        
        # Medical domain method
        medical_outliers = self.detect_medical_domain_outliers(self.prevalence_data)
        
        # Store results
        self.outlier_methods = {
            'iqr': {
                'outliers': iqr_outliers,
                'lower_bound': iqr_lower,
                'upper_bound': iqr_upper,
                'count': len(iqr_outliers)
            },
            'zscore': {
                'outliers': zscore_outliers,
                'lower_bound': zscore_lower,
                'upper_bound': zscore_upper,
                'count': len(zscore_outliers)
            },
            'modified_zscore': {
                'outliers': mad_outliers,
                'lower_bound': mad_lower,
                'upper_bound': mad_upper,
                'count': len(mad_outliers)
            },
            'log_normal': {
                'outliers': log_outliers,
                'lower_bound': log_lower,
                'upper_bound': log_upper,
                'count': len(log_outliers)
            },
            'percentile': {
                'outliers': percentile_outliers,
                'lower_bound': perc_lower,
                'upper_bound': perc_upper,
                'count': len(percentile_outliers)
            },
            'medical_domain': {
                'outliers': medical_outliers,
                'count': len(medical_outliers)
            }
        }
        
        logger.info(f"Outlier detection complete. Found: IQR={len(iqr_outliers)}, Z-Score={len(zscore_outliers)}, MAD={len(mad_outliers)}, Log-Normal={len(log_outliers)}, Percentile={len(percentile_outliers)}, Medical={len(medical_outliers)}")
    
    def identify_consensus_outliers(self) -> Dict:
        """Identify diseases flagged by multiple methods"""
        logger.info("Identifying consensus outliers...")
        
        # Create disease-to-outlier mapping
        disease_outlier_count = defaultdict(int)
        disease_methods = defaultdict(list)
        
        prevalence_to_disease = {item['prevalence']: item for item in self.prevalence_data}
        
        # Count how many methods flag each disease
        for method_name, method_data in self.outlier_methods.items():
            if method_name == 'medical_domain':
                # Medical domain outliers are already disease objects
                for outlier in method_data['outliers']:
                    disease_key = outlier['orpha_code']
                    disease_outlier_count[disease_key] += 1
                    disease_methods[disease_key].append(method_name)
            else:
                # Statistical methods return prevalence values
                for outlier_val in method_data['outliers']:
                    if outlier_val in prevalence_to_disease:
                        disease = prevalence_to_disease[outlier_val]
                        disease_key = disease['orpha_code']
                        disease_outlier_count[disease_key] += 1
                        disease_methods[disease_key].append(method_name)
        
        # Categorize by confidence level
        high_confidence = []  # 4+ methods
        medium_confidence = []  # 2-3 methods
        low_confidence = []  # 1 method
        
        for disease_key, count in disease_outlier_count.items():
            disease_data = next(d for d in self.prevalence_data if d['orpha_code'] == disease_key)
            consensus_data = {
                **disease_data,
                'methods_count': count,
                'flagged_by': disease_methods[disease_key]
            }
            
            if count >= 4:
                high_confidence.append(consensus_data)
            elif count >= 2:
                medium_confidence.append(consensus_data)
            else:
                low_confidence.append(consensus_data)
        
        # Sort by prevalence (descending)
        high_confidence.sort(key=lambda x: x['prevalence'], reverse=True)
        medium_confidence.sort(key=lambda x: x['prevalence'], reverse=True)
        low_confidence.sort(key=lambda x: x['prevalence'], reverse=True)
        
        consensus_results = {
            'high_confidence': high_confidence,
            'medium_confidence': medium_confidence,
            'low_confidence': low_confidence
        }
        
        logger.info(f"Consensus outliers: High={len(high_confidence)}, Medium={len(medium_confidence)}, Low={len(low_confidence)}")
        
        return consensus_results
    
    def plot_distribution_with_outliers(self, ax, data: List[float], detection_method, title: str, subtitle: str) -> None:
        """Plot kernel density distribution with outlier highlights"""
        
        # Get outliers using the detection method
        outliers, lower_bound, upper_bound = detection_method(data)
        
        # Create kernel density plot for all data
        try:
            sns.kdeplot(data, ax=ax, color='skyblue', alpha=0.7, linewidth=2, 
                       label=f'All Data (n={len(data)})', fill=True)
        except:
            # Fallback to histogram if KDE fails
            ax.hist(data, bins=50, density=True, alpha=0.7, color='skyblue', 
                    label=f'All Data (n={len(data)})')
        
        # Add outlier highlights with KDE
        if outliers and len(outliers) > 1:
            try:
                sns.kdeplot(outliers, ax=ax, color='red', alpha=0.8, linewidth=2,
                           label=f'Outliers (n={len(outliers)})', fill=True)
            except:
                # Fallback to histogram for outliers if KDE fails
                ax.hist(outliers, bins=min(30, len(outliers)), density=True, alpha=0.8, color='red', 
                        label=f'Outliers (n={len(outliers)})')
        elif outliers:
            # For single outliers, add scatter points
            ax.scatter(outliers, [0.001] * len(outliers), color='red', s=50, 
                      label=f'Outliers (n={len(outliers)})', alpha=0.8, zorder=5)
        
        # Add threshold lines
        if lower_bound is not None and lower_bound > 0:
            ax.axvline(lower_bound, color='orange', linestyle='--', linewidth=2,
                       label=f'Lower: {lower_bound:.1f}')
        if upper_bound is not None and upper_bound < max(data):
            ax.axvline(upper_bound, color='orange', linestyle='--', linewidth=2,
                       label=f'Upper: {upper_bound:.1f}')
        
        # Formatting
        ax.set_title(f'{title}\n{subtitle}', fontweight='bold', fontsize=12)
        ax.set_xlabel('Prevalence (per million)', fontsize=10)
        ax.set_ylabel('Density', fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f'Mean: {np.mean(data):.1f}\nMedian: {np.median(data):.1f}\n'
        stats_text += f'Outliers: {len(outliers)} ({len(outliers)/len(data)*100:.1f}%)'
        ax.text(0.65, 0.85, stats_text, transform=ax.transAxes, fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def plot_medical_domain_analysis(self, ax, prevalence_data: List[Dict]) -> None:
        """Plot medical domain outlier analysis"""
        
        medical_outliers = self.outlier_methods['medical_domain']['outliers']
        
        # Create categories
        categories = ['All Diseases', 'High Prev + Low Rel', 'High Prev + Single Rec', 
                     'Exceeds Rare Def', 'Extremely High']
        
        counts = [
            len(prevalence_data),
            len([o for o in medical_outliers if o['reason'] == 'High prevalence + low reliability']),
            len([o for o in medical_outliers if o['reason'] == 'High prevalence + single record']),
            len([o for o in medical_outliers if o['reason'] == 'Exceeds rare disease definition']),
            len([o for o in medical_outliers if o['reason'] == 'Extremely high prevalence'])
        ]
        
        colors = ['lightblue', 'orange', 'red', 'darkred', 'purple']
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.7)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{count}', ha='center', va='bottom')
        
        ax.set_title('Medical Domain Outliers\nDomain-Specific Rules', fontweight='bold')
        ax.set_ylabel('Number of Diseases')
        ax.tick_params(axis='x', rotation=45)
        
        # Add percentage text
        total = len(prevalence_data)
        medical_total = len(medical_outliers)
        stats_text = f'Total Flagged: {medical_total}\nPercentage: {medical_total/total*100:.1f}%'
        ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def create_outlier_density_grid(self) -> None:
        """Create comprehensive density plot grid"""
        logger.info("Creating density plot grid...")
        
        fig, axes = plt.subplots(3, 2, figsize=(18, 20))
        fig.suptitle('Prevalence Data Outlier Analysis - Kernel Density Distributions', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Panel 1: IQR Method
        ax1 = axes[0, 0]
        self.plot_distribution_with_outliers(ax1, prevalence_values, self.detect_iqr_outliers, 
                                           'IQR Method', 'Interquartile Range')
        
        # Panel 2: Z-Score Method
        ax2 = axes[0, 1]
        self.plot_distribution_with_outliers(ax2, prevalence_values, self.detect_zscore_outliers, 
                                           'Z-Score Method', 'Standard Deviations')
        
        # Panel 3: Modified Z-Score (MAD)
        ax3 = axes[1, 0]
        self.plot_distribution_with_outliers(ax3, prevalence_values, self.detect_modified_zscore_outliers, 
                                           'Modified Z-Score', 'Median Absolute Deviation')
        
        # Panel 4: Log-Normal Distribution
        ax4 = axes[1, 1]
        self.plot_distribution_with_outliers(ax4, prevalence_values, self.detect_log_normal_outliers, 
                                           'Log-Normal Method', 'Log-Space Analysis')
        
        # Panel 5: Percentile-Based
        ax5 = axes[2, 0]
        self.plot_distribution_with_outliers(ax5, prevalence_values, self.detect_percentile_outliers, 
                                           'Percentile Method', '5th-95th Percentile')
        
        # Panel 6: Medical Domain Analysis
        ax6 = axes[2, 1]
        self.plot_medical_domain_analysis(ax6, self.prevalence_data)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output_dir / 'outlier_density_grid.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Density plot grid saved")
    
    def calculate_analysis_results(self) -> None:
        """Calculate comprehensive analysis results"""
        logger.info("Calculating analysis results...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Basic statistics
        self.analysis_results = {
            'total_diseases': len(self.prevalence_data),
            'min_prevalence': min(prevalence_values),
            'max_prevalence': max(prevalence_values),
            'mean': np.mean(prevalence_values),
            'median': np.median(prevalence_values),
            'std': np.std(prevalence_values),
            'skewness': stats.skew(prevalence_values),
            'kurtosis': stats.kurtosis(prevalence_values),
            
            # Outlier counts
            'outlier_counts': {
                'iqr': self.outlier_methods['iqr']['count'],
                'zscore': self.outlier_methods['zscore']['count'],
                'mad': self.outlier_methods['modified_zscore']['count'],
                'lognormal': self.outlier_methods['log_normal']['count'],
                'percentile': self.outlier_methods['percentile']['count'],
                'medical': self.outlier_methods['medical_domain']['count']
            },
            
            # Thresholds
            'iqr_threshold': self.outlier_methods['iqr']['upper_bound'],
            'zscore_threshold': self.outlier_methods['zscore']['upper_bound'],
            'mad_threshold': self.outlier_methods['modified_zscore']['upper_bound'],
            'lognormal_threshold': self.outlier_methods['log_normal']['upper_bound'],
            'percentile_threshold': self.outlier_methods['percentile']['upper_bound'],
            
            # Analysis timestamp
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Identify consensus outliers
        consensus_results = self.identify_consensus_outliers()
        self.analysis_results['consensus_outliers'] = {
            'high': len(consensus_results['high_confidence']),
            'medium': len(consensus_results['medium_confidence']),
            'low': len(consensus_results['low_confidence'])
        }
        
        # Store detailed consensus results
        self.analysis_results['detailed_consensus'] = consensus_results
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary section"""
        total_diseases = self.analysis_results['total_diseases']
        outlier_counts = self.analysis_results['outlier_counts']
        
        summary = f"""
### Key Findings

- **Total Diseases Analyzed**: {total_diseases} with valid prevalence estimates
- **Prevalence Range**: {self.analysis_results['min_prevalence']:.1f} to {self.analysis_results['max_prevalence']:.1f} per million
- **Distribution**: Highly right-skewed (median: {self.analysis_results['median']:.1f}, mean: {self.analysis_results['mean']:.1f})
- **Skewness**: {self.analysis_results['skewness']:.2f} (highly right-skewed)
- **Kurtosis**: {self.analysis_results['kurtosis']:.2f} (heavy-tailed distribution)

### Outlier Detection Results

| Method | Outliers Detected | Percentage | Upper Threshold |
|--------|------------------|------------|----------------|
| IQR Method | {outlier_counts['iqr']} | {outlier_counts['iqr']/total_diseases*100:.1f}% | {self.analysis_results['iqr_threshold']:.1f} |
| Z-Score | {outlier_counts['zscore']} | {outlier_counts['zscore']/total_diseases*100:.1f}% | {self.analysis_results['zscore_threshold']:.1f} |
| Modified Z-Score | {outlier_counts['mad']} | {outlier_counts['mad']/total_diseases*100:.1f}% | {self.analysis_results['mad_threshold']:.1f} |
| Log-Normal | {outlier_counts['lognormal']} | {outlier_counts['lognormal']/total_diseases*100:.1f}% | {self.analysis_results['lognormal_threshold']:.1f} |
| Percentile | {outlier_counts['percentile']} | {outlier_counts['percentile']/total_diseases*100:.1f}% | {self.analysis_results['percentile_threshold']:.1f} |
| Medical Domain | {outlier_counts['medical']} | {outlier_counts['medical']/total_diseases*100:.1f}% | Domain Rules |

### Consensus Outliers
- **High Confidence**: {self.analysis_results['consensus_outliers']['high']} diseases flagged by ≥4 methods
- **Medium Confidence**: {self.analysis_results['consensus_outliers']['medium']} diseases flagged by 2-3 methods
- **Low Confidence**: {self.analysis_results['consensus_outliers']['low']} diseases flagged by 1 method
"""
        return summary
    
    def generate_methods_comparison(self) -> str:
        """Generate methods comparison section"""
        comparison = """
### Method Characteristics

#### Statistical Methods
- **IQR Method**: Traditional box plot approach, good for symmetric distributions
- **Z-Score**: Assumes normal distribution, sensitive to extreme values
- **Modified Z-Score**: More robust to outliers, uses median and MAD
- **Log-Normal**: Appropriate for skewed biological data, transforms to log space
- **Percentile**: Distribution-free, uses empirical percentiles

#### Medical Domain Method
- **High Prevalence + Low Reliability**: Prevalence >100 per million with reliability <6.0
- **High Prevalence + Single Record**: Prevalence >100 per million with only 1 record
- **Exceeds Rare Disease Definition**: Prevalence >500 per million (EU definition)
- **Extremely High Prevalence**: Prevalence >1000 per million (0.1% of population)

### Method Recommendations
- **For Statistical Analysis**: Log-Normal method most appropriate for prevalence data
- **For Data Quality**: Medical Domain method identifies problematic records
- **For Conservative Filtering**: Modified Z-Score provides balanced approach
- **For Aggressive Filtering**: IQR method removes more outliers
"""
        return comparison
    
    def generate_statistical_analysis(self) -> str:
        """Generate statistical analysis section"""
        analysis = f"""
### Distribution Characteristics
- **Mean**: {self.analysis_results['mean']:.2f} per million
- **Median**: {self.analysis_results['median']:.2f} per million
- **Standard Deviation**: {self.analysis_results['std']:.2f}
- **Skewness**: {self.analysis_results['skewness']:.2f} (highly right-skewed)
- **Kurtosis**: {self.analysis_results['kurtosis']:.2f} (heavy-tailed)

### Quartile Analysis
- **Q1 (25th percentile)**: {np.percentile([item['prevalence'] for item in self.prevalence_data], 25):.2f} per million
- **Q3 (75th percentile)**: {np.percentile([item['prevalence'] for item in self.prevalence_data], 75):.2f} per million
- **IQR**: {np.percentile([item['prevalence'] for item in self.prevalence_data], 75) - np.percentile([item['prevalence'] for item in self.prevalence_data], 25):.2f}

### Extreme Values
- **Top 1%**: >{np.percentile([item['prevalence'] for item in self.prevalence_data], 99):.2f} per million
- **Top 5%**: >{np.percentile([item['prevalence'] for item in self.prevalence_data], 95):.2f} per million
- **Bottom 5%**: <{np.percentile([item['prevalence'] for item in self.prevalence_data], 5):.2f} per million
"""
        return analysis
    
    def generate_medical_domain_findings(self) -> str:
        """Generate medical domain findings section"""
        medical_outliers = self.outlier_methods['medical_domain']['outliers']
        
        # Group by reason
        reason_counts = defaultdict(int)
        for outlier in medical_outliers:
            reason_counts[outlier['reason']] += 1
        
        findings = f"""
### Medical Domain Outlier Categories

#### High Prevalence + Low Reliability ({reason_counts['High prevalence + low reliability']} diseases)
Diseases with prevalence >100 per million but reliability score <6.0. These may represent:
- Data quality issues
- Conflicting evidence
- Geographic bias in small studies

#### High Prevalence + Single Record ({reason_counts['High prevalence + single record']} diseases)
Diseases with prevalence >100 per million based on only one record. These may represent:
- Insufficient evidence
- Preliminary findings
- Publication bias

#### Exceeds Rare Disease Definition ({reason_counts['Exceeds rare disease definition']} diseases)
Diseases with prevalence >500 per million (EU rare disease threshold). These may represent:
- Common conditions misclassified as rare
- Geographic variations
- Prevalence class mapping errors

#### Extremely High Prevalence ({reason_counts['Extremely high prevalence']} diseases)
Diseases with prevalence >1000 per million (0.1% of population). These likely represent:
- Data processing errors
- Prevalence type confusion (birth vs population)
- Geographic-specific conditions applied globally

### Top Medical Domain Outliers
"""
        
        # Add top outliers by prevalence
        top_medical_outliers = sorted(medical_outliers, key=lambda x: x['prevalence'], reverse=True)[:10]
        
        for i, outlier in enumerate(top_medical_outliers, 1):
            findings += f"""
{i}. **{outlier['disease_name']}** (Orpha: {outlier['orpha_code']})
   - Prevalence: {outlier['prevalence']:.1f} per million
   - Reliability: {outlier['reliability_score']:.1f}
   - Records: {outlier['records_count']}
   - Reason: {outlier['reason']}
"""
        
        return findings
    
    def generate_recommendations(self) -> str:
        """Generate recommendations section"""
        return """
### Data Quality Recommendations

#### Immediate Actions
1. **Review High-Confidence Outliers**: Manually validate diseases flagged by ≥4 methods
2. **Verify Medical Domain Flags**: Check diseases exceeding rare disease thresholds
3. **Cross-Reference Literature**: Validate extreme prevalence estimates with published data
4. **Geographic Stratification**: Separate population-specific from global estimates

#### Medium-Term Improvements
1. **Enhance Reliability Scoring**: Incorporate geographic representativeness
2. **Implement Consensus Filtering**: Use multi-method agreement for data quality
3. **Add Temporal Validation**: Check for prevalence changes over time
4. **Improve Documentation**: Flag data quality issues transparently

#### Long-Term Strategy
1. **Automated Quality Control**: Implement real-time outlier detection
2. **Expert Review Process**: Establish medical expert validation workflow
3. **Data Source Diversification**: Incorporate multiple prevalence databases
4. **Uncertainty Quantification**: Provide confidence intervals for estimates

### Filtering Recommendations

#### Conservative Approach (Recommended)
- Use **Log-Normal method** for statistical outliers
- Flag but don't remove **Medical Domain outliers**
- Require **≥2 method consensus** for exclusion
- Preserve original data with quality flags

#### Aggressive Approach (Research-Specific)
- Use **IQR method** for broader outlier removal
- Exclude **High-Confidence consensus outliers**
- Apply **Medical Domain filters** strictly
- Focus on highest-quality data only
"""
    
    def generate_data_quality_impact(self) -> str:
        """Generate data quality impact section"""
        total_diseases = self.analysis_results['total_diseases']
        high_confidence = self.analysis_results['consensus_outliers']['high']
        medium_confidence = self.analysis_results['consensus_outliers']['medium']
        
        impact = f"""
### Impact on Dataset Quality

#### Current State
- **Total Diseases**: {total_diseases} with prevalence estimates
- **High-Quality Diseases**: {total_diseases - high_confidence - medium_confidence} ({(total_diseases - high_confidence - medium_confidence)/total_diseases*100:.1f}%)
- **Questionable Quality**: {high_confidence + medium_confidence} ({(high_confidence + medium_confidence)/total_diseases*100:.1f}%)

#### Filtering Impact
- **Conservative Filtering**: Removes {high_confidence} diseases ({high_confidence/total_diseases*100:.1f}%)
- **Moderate Filtering**: Removes {high_confidence + medium_confidence} diseases ({(high_confidence + medium_confidence)/total_diseases*100:.1f}%)
- **Aggressive Filtering**: Could remove up to {self.analysis_results['outlier_counts']['iqr']} diseases ({self.analysis_results['outlier_counts']['iqr']/total_diseases*100:.1f}%)

#### Quality Metrics
- **Reliability Score Distribution**: {len([d for d in self.prevalence_data if d['reliability_score'] >= 6.0])} diseases with reliable scores (≥6.0)
- **Multiple Records**: {len([d for d in self.prevalence_data if d['records_count'] > 1])} diseases with multiple records
- **Worldwide Coverage**: {len([d for d in self.prevalence_data if d['has_worldwide']])} diseases with worldwide data
- **Validated Data**: {sum(d['validated_records'] for d in self.prevalence_data)} total validated records

### Recommended Actions
1. **Flag High-Confidence Outliers**: Mark for manual review
2. **Stratify by Quality**: Separate high/medium/low quality datasets
3. **Transparent Reporting**: Document all filtering decisions
4. **Preserve Raw Data**: Maintain original estimates with quality flags
"""
        return impact
    
    def generate_outlier_markdown_summary(self) -> str:
        """Generate comprehensive outlier analysis summary"""
        
        markdown_content = f"""# Prevalence Data Outlier Analysis Summary

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset**: {self.analysis_results['total_diseases']} diseases with prevalence estimates  
**Data Source**: `data/03_processed/orpha/orphadata/orpha_prevalence/`

## 📊 **Executive Summary**

{self.generate_executive_summary()}

## 🔬 **Outlier Detection Methods Comparison**

{self.generate_methods_comparison()}

## 📈 **Statistical Analysis Results**

{self.generate_statistical_analysis()}

## 🏥 **Medical Domain Findings**

{self.generate_medical_domain_findings()}

## 🎯 **Recommendations**

{self.generate_recommendations()}

## 📁 **Generated Files**

- `outlier_density_grid.png` - Comprehensive kernel density plot grid (3x2 panels)
- `outlier_summary_statistics.json` - Detailed statistical results
- `outlier_flagged_diseases.json` - List of flagged diseases by method
- `consensus_outliers.json` - High-confidence outliers
- `medical_domain_flags.json` - Medical domain violations

## 🔗 **Data Quality Impact**

{self.generate_data_quality_impact()}

---

*Generated by RarePrioritizer Outlier Analysis System*  
*For questions or issues, refer to the project documentation*
"""
        
        return markdown_content
    
    def save_analysis_results(self) -> None:
        """Save all analysis results to files"""
        logger.info("Saving analysis results...")
        
        # Save summary statistics
        with open(self.output_dir / 'outlier_summary_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        # Save detailed consensus outliers
        with open(self.output_dir / 'consensus_outliers.json', 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results['detailed_consensus'], f, indent=2, ensure_ascii=False)
        
        # Save medical domain flags
        with open(self.output_dir / 'medical_domain_flags.json', 'w', encoding='utf-8') as f:
            json.dump(self.outlier_methods['medical_domain']['outliers'], f, indent=2, ensure_ascii=False)
        
        # Save flagged diseases by method
        flagged_diseases = {}
        for method_name, method_data in self.outlier_methods.items():
            if method_name == 'medical_domain':
                flagged_diseases[method_name] = method_data['outliers']
            else:
                # Convert prevalence values to disease info
                prevalence_to_disease = {item['prevalence']: item for item in self.prevalence_data}
                flagged_diseases[method_name] = [
                    prevalence_to_disease[val] for val in method_data['outliers'] 
                    if val in prevalence_to_disease
                ]
        
        with open(self.output_dir / 'outlier_flagged_diseases.json', 'w', encoding='utf-8') as f:
            json.dump(flagged_diseases, f, indent=2, ensure_ascii=False)
        
        # Save markdown summary
        markdown_summary = self.generate_outlier_markdown_summary()
        with open(self.output_dir / 'outlier.md', 'w', encoding='utf-8') as f:
            f.write(markdown_summary)
        
        logger.info("Analysis results saved successfully")
    
    def run_complete_analysis(self) -> None:
        """Run complete outlier analysis workflow"""
        logger.info("Starting complete outlier analysis...")
        
        # Extract data
        self.extract_prevalence_data()
        
        # Run outlier detection
        self.run_outlier_detection()
        
        # Calculate comprehensive results
        self.calculate_analysis_results()
        
        # Create visualizations
        self.create_outlier_density_grid()
        
        # Save all results
        self.save_analysis_results()
        
        logger.info("Complete outlier analysis finished successfully!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        # Print summary
        print(f"\n🎯 OUTLIER ANALYSIS COMPLETE")
        print(f"📊 Analyzed {self.analysis_results['total_diseases']} diseases")
        print(f"🔍 Methods: IQR={self.analysis_results['outlier_counts']['iqr']}, Z-Score={self.analysis_results['outlier_counts']['zscore']}, MAD={self.analysis_results['outlier_counts']['mad']}")
        print(f"🏥 Medical Domain: {self.analysis_results['outlier_counts']['medical']} diseases flagged")
        print(f"🎯 Consensus: {self.analysis_results['consensus_outliers']['high']} high-confidence outliers")
        print(f"📁 Output: {self.output_dir}")


def main():
    """Main function to run outlier analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prevalence Data Outlier Analysis')
    parser.add_argument('--output', '-o', 
                       default='results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = PrevalenceOutlierAnalyzer(output_dir=args.output)
    analyzer.run_complete_analysis()


if __name__ == "__main__":
    main() 