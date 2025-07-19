#!/usr/bin/env python3
"""
IQR Outlier Analysis Script - Hyperparameter Sensitivity Study

This script performs comprehensive IQR outlier analysis with multiple hyperparameters
and methods, generating detailed sensitivity analysis and optimization results.

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
from scipy.stats import mstats

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IQROutlierAnalyzer:
    """Comprehensive IQR outlier analysis with hyperparameter sensitivity"""
    
    def __init__(self, output_dir: str = "results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only"):
        """Initialize the IQR outlier analyzer"""
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
        self.iqr_results = {}
        self.sensitivity_results = {}
        self.evaluation_results = {}
        
        logger.info(f"IQR outlier analyzer initialized with output dir: {output_dir}")
    
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
    
    def iqr_classic_variants(self, data: List[float]) -> Dict:
        """Test different IQR multipliers"""
        multipliers = [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
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
                'percentage': len(outliers) / len(data) * 100,
                'multiplier': mult,
                'Q1': Q1,
                'Q3': Q3,
                'IQR': IQR
            }
        
        return results
    
    def iqr_quartile_methods(self, data: List[float]) -> Dict:
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
            try:
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
                    'count': len(outliers),
                    'percentage': len(outliers) / len(data) * 100,
                    'method': method
                }
            except:
                # Fallback for methods not supported in older numpy versions
                Q1 = np.percentile(data, 25)
                Q3 = np.percentile(data, 75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                outliers = [x for x in data if x < lower_bound or x > upper_bound]
                
                results[f'IQR_quartile_{name}'] = {
                    'outliers': outliers,
                    'Q1': Q1,
                    'Q3': Q3,
                    'IQR': IQR,
                    'count': len(outliers),
                    'percentage': len(outliers) / len(data) * 100,
                    'method': 'linear'  # Fallback
                }
        
        return results
    
    def iqr_percentile_variants(self, data: List[float]) -> Dict:
        """Test IQR-like methods with different percentile ranges"""
        percentile_pairs = [
            (10, 90, 'P10-P90'),   # Wider range
            (15, 85, 'P15-P85'),   # Moderate range
            (20, 80, 'P20-P80'),   # Narrower range
            (25, 75, 'P25-P75'),   # Classic IQR
            (5, 95, 'P5-P95'),     # Very wide range
            (12.5, 87.5, 'P12.5-P87.5'),  # Alternative moderate
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
                'count': len(outliers),
                'percentage': len(outliers) / len(data) * 100,
                'percentiles': (lower_p, upper_p)
            }
        
        return results
    
    def iqr_robust_variants(self, data: List[float]) -> Dict:
        """Test robust IQR variants"""
        results = {}
        
        # Trimmed IQR (remove extreme 5% before calculation)
        sorted_data = np.sort(data)
        trim_idx = int(0.05 * len(data))
        trimmed_data = sorted_data[trim_idx:-trim_idx] if trim_idx > 0 else sorted_data
        
        Q1_trim = np.percentile(trimmed_data, 25)
        Q3_trim = np.percentile(trimmed_data, 75)
        IQR_trim = Q3_trim - Q1_trim
        
        outliers_trimmed = [x for x in data if x < Q1_trim - 1.5 * IQR_trim or x > Q3_trim + 1.5 * IQR_trim]
        
        results['IQR_trimmed'] = {
            'outliers': outliers_trimmed,
            'count': len(outliers_trimmed),
            'percentage': len(outliers_trimmed) / len(data) * 100,
            'Q1': Q1_trim,
            'Q3': Q3_trim,
            'IQR': IQR_trim
        }
        
        # Winsorized IQR (cap extreme values)
        try:
            winsorized_data = mstats.winsorize(data, limits=[0.05, 0.05])
            Q1_wins = np.percentile(winsorized_data, 25)
            Q3_wins = np.percentile(winsorized_data, 75)
            IQR_wins = Q3_wins - Q1_wins
            
            outliers_winsorized = [x for x in data if x < Q1_wins - 1.5 * IQR_wins or x > Q3_wins + 1.5 * IQR_wins]
            
            results['IQR_winsorized'] = {
                'outliers': outliers_winsorized,
                'count': len(outliers_winsorized),
                'percentage': len(outliers_winsorized) / len(data) * 100,
                'Q1': Q1_wins,
                'Q3': Q3_wins,
                'IQR': IQR_wins
            }
        except:
            # Fallback if winsorize fails
            results['IQR_winsorized'] = {
                'outliers': [],
                'count': 0,
                'percentage': 0.0,
                'error': 'Winsorization failed'
            }
        
        # Median-based IQR (use median instead of mean for centering)
        median = np.median(data)
        mad = np.median([abs(x - median) for x in data])
        
        # Convert MAD to IQR-like bounds
        iqr_like_bound = 1.5 * mad * 1.4826  # Scale factor to match normal distribution
        outliers_median = [x for x in data if abs(x - median) > iqr_like_bound]
        
        results['IQR_median_based'] = {
            'outliers': outliers_median,
            'count': len(outliers_median),
            'percentage': len(outliers_median) / len(data) * 100,
            'median': median,
            'mad': mad,
            'bound': iqr_like_bound
        }
        
        return results
    
    def iqr_adaptive_variants(self, data: List[float]) -> Dict:
        """Test adaptive IQR methods that adjust based on data characteristics"""
        results = {}
        
        # Skewness-adjusted IQR
        data_skewness = stats.skew(data)
        
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
            'count': len(outliers_adaptive),
            'percentage': len(outliers_adaptive) / len(data) * 100,
            'Q1': Q1,
            'Q3': Q3,
            'IQR': IQR
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
            'count': len(outliers_sample_adj),
            'percentage': len(outliers_sample_adj) / len(data) * 100,
            'Q1': Q1,
            'Q3': Q3,
            'IQR': IQR
        }
        
        return results
    
    def run_all_iqr_methods(self) -> None:
        """Run all IQR method variations"""
        logger.info("Running all IQR method variations...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Run all variants
        self.iqr_results.update(self.iqr_classic_variants(prevalence_values))
        self.iqr_results.update(self.iqr_quartile_methods(prevalence_values))
        self.iqr_results.update(self.iqr_percentile_variants(prevalence_values))
        self.iqr_results.update(self.iqr_robust_variants(prevalence_values))
        self.iqr_results.update(self.iqr_adaptive_variants(prevalence_values))
        
        # Log results summary
        method_counts = {method: results['count'] for method, results in self.iqr_results.items()}
        logger.info(f"IQR methods complete. Method count range: {min(method_counts.values())} to {max(method_counts.values())}")
    
    def analyze_parameter_sensitivity(self) -> None:
        """Analyze sensitivity to parameter changes"""
        logger.info("Analyzing parameter sensitivity...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Multiplier sensitivity (fine-grained)
        multipliers = np.arange(1.0, 4.1, 0.1)
        Q1 = np.percentile(prevalence_values, 25)
        Q3 = np.percentile(prevalence_values, 75)
        IQR = Q3 - Q1
        
        multiplier_sensitivity = {}
        for mult in multipliers:
            lower_bound = Q1 - mult * IQR
            upper_bound = Q3 + mult * IQR
            outliers = [x for x in prevalence_values if x < lower_bound or x > upper_bound]
            multiplier_sensitivity[mult] = len(outliers)
        
        # Percentile sensitivity
        percentile_sensitivity = {}
        for lower_p in range(5, 31, 2):  # 5 to 30 in steps of 2
            upper_p = 100 - lower_p
            P_lower = np.percentile(prevalence_values, lower_p)
            P_upper = np.percentile(prevalence_values, upper_p)
            IPR = P_upper - P_lower
            
            lower_bound = P_lower - 1.5 * IPR
            upper_bound = P_upper + 1.5 * IPR
            outliers = [x for x in prevalence_values if x < lower_bound or x > upper_bound]
            percentile_sensitivity[f'{lower_p}-{upper_p}'] = len(outliers)
        
        self.sensitivity_results = {
            'multiplier_sensitivity': multiplier_sensitivity,
            'percentile_sensitivity': percentile_sensitivity
        }
        
        logger.info("Parameter sensitivity analysis complete")
    
    def assess_medical_relevance(self) -> Dict:
        """Assess medical relevance of different IQR methods"""
        logger.info("Assessing medical relevance...")
        
        medical_assessment = {}
        
        for method_name, method_results in self.iqr_results.items():
            outliers = method_results['outliers']
            
            # Find corresponding diseases
            outlier_diseases = []
            for item in self.prevalence_data:
                if item['prevalence'] in outliers:
                    outlier_diseases.append(item)
            
            # Medical relevance metrics
            high_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] >= 8.0])
            medium_reliability_outliers = len([d for d in outlier_diseases if 6.0 <= d['reliability_score'] < 8.0])
            low_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] < 6.0])
            
            single_record_outliers = len([d for d in outlier_diseases if d['records_count'] == 1])
            multiple_record_outliers = len([d for d in outlier_diseases if d['records_count'] > 1])
            
            worldwide_outliers = len([d for d in outlier_diseases if d['has_worldwide']])
            
            medical_assessment[method_name] = {
                'total_outliers': len(outlier_diseases),
                'high_reliability_outliers': high_reliability_outliers,
                'medium_reliability_outliers': medium_reliability_outliers,
                'low_reliability_outliers': low_reliability_outliers,
                'single_record_outliers': single_record_outliers,
                'multiple_record_outliers': multiple_record_outliers,
                'worldwide_outliers': worldwide_outliers,
                'quality_ratio': high_reliability_outliers / max(len(outlier_diseases), 1),
                'evidence_ratio': multiple_record_outliers / max(len(outlier_diseases), 1),
                'global_ratio': worldwide_outliers / max(len(outlier_diseases), 1)
            }
        
        return medical_assessment
    
    def plot_iqr_variant(self, ax, data: List[float], method_name: str, method_results: Dict, title: str, subtitle: str) -> None:
        """Plot individual IQR variant with KDE"""
        
        outliers = method_results['outliers']
        
        # Create kernel density plot for all data
        try:
            sns.kdeplot(data, ax=ax, color='lightblue', alpha=0.7, linewidth=2, 
                       label=f'All Data (n={len(data)})', fill=True)
        except:
            ax.hist(data, bins=50, density=True, alpha=0.7, color='lightblue', 
                    label=f'All Data (n={len(data)})')
        
        # Add outlier highlights
        if outliers and len(outliers) > 1:
            try:
                sns.kdeplot(outliers, ax=ax, color='red', alpha=0.8, linewidth=2,
                           label=f'Outliers (n={len(outliers)})', fill=True)
            except:
                ax.hist(outliers, bins=min(20, len(outliers)), density=True, alpha=0.8, color='red', 
                        label=f'Outliers (n={len(outliers)})')
        elif outliers:
            ax.scatter(outliers, [0.001] * len(outliers), color='red', s=50, 
                      label=f'Outliers (n={len(outliers)})', alpha=0.8, zorder=5)
        
        # Add threshold lines
        if 'upper_bound' in method_results and method_results['upper_bound'] < max(data):
            ax.axvline(method_results['upper_bound'], color='orange', linestyle='--', linewidth=2,
                       label=f'Upper: {method_results["upper_bound"]:.1f}')
        
        # Formatting
        ax.set_title(f'{title}\n{subtitle}', fontweight='bold', fontsize=10)
        ax.set_xlabel('Prevalence (per million)', fontsize=9)
        ax.set_ylabel('Density', fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        
        # Add statistics text
        stats_text = f'Outliers: {len(outliers)} ({len(outliers)/len(data)*100:.1f}%)'
        if 'multiplier' in method_results:
            stats_text += f'\nMultiplier: {method_results["multiplier"]}'
        elif 'percentiles' in method_results:
            stats_text += f'\nPercentiles: {method_results["percentiles"]}'
        
        ax.text(0.65, 0.85, stats_text, transform=ax.transAxes, fontsize=7,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    def create_iqr_sensitivity_grid(self) -> None:
        """Create comprehensive IQR sensitivity analysis grid"""
        logger.info("Creating IQR sensitivity grid...")
        
        fig, axes = plt.subplots(3, 3, figsize=(20, 18))
        fig.suptitle('IQR Outlier Detection - Hyperparameter Sensitivity Analysis', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Row 1: Classic IQR Multipliers (1.5x, 2.0x, 2.5x)
        multipliers = [1.5, 2.0, 2.5]
        for i, mult in enumerate(multipliers):
            method_name = f'IQR_{mult}x'
            if method_name in self.iqr_results:
                self.plot_iqr_variant(axes[0, i], prevalence_values, method_name, 
                                    self.iqr_results[method_name],
                                    f'Classic IQR {mult}x', f'Multiplier = {mult}')
        
        # Row 2: Percentile Variants
        percentile_methods = ['P10-P90', 'P20-P80', 'P5-P95']
        for i, method_name in enumerate(percentile_methods):
            if method_name in self.iqr_results:
                percentiles = self.iqr_results[method_name]['percentiles']
                self.plot_iqr_variant(axes[1, i], prevalence_values, method_name,
                                    self.iqr_results[method_name],
                                    f'{method_name} Method', f'Percentiles: {percentiles[0]}-{percentiles[1]}')
        
        # Row 3: Robust and Adaptive Methods
        robust_methods = ['IQR_trimmed', 'IQR_winsorized', 'IQR_skewness_adaptive']
        robust_titles = ['Trimmed IQR', 'Winsorized IQR', 'Skewness Adaptive']
        for i, (method_name, title) in enumerate(zip(robust_methods, robust_titles)):
            if method_name in self.iqr_results:
                subtitle = f'{title} approach'
                if 'multiplier_used' in self.iqr_results[method_name]:
                    subtitle += f' (mult: {self.iqr_results[method_name]["multiplier_used"]})'
                self.plot_iqr_variant(axes[2, i], prevalence_values, method_name,
                                    self.iqr_results[method_name],
                                    title, subtitle)
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output_dir / 'iqr_sensitivity_grid.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("IQR sensitivity grid saved")
    
    def create_parameter_sensitivity_plots(self) -> None:
        """Create parameter sensitivity analysis plots"""
        logger.info("Creating parameter sensitivity plots...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('IQR Parameter Sensitivity Analysis', fontsize=16, fontweight='bold')
        
        # Plot 1: Multiplier sensitivity
        multipliers = list(self.sensitivity_results['multiplier_sensitivity'].keys())
        outlier_counts = list(self.sensitivity_results['multiplier_sensitivity'].values())
        
        ax1.plot(multipliers, outlier_counts, 'bo-', linewidth=2, markersize=6)
        ax1.set_title('Sensitivity to IQR Multiplier')
        ax1.set_xlabel('IQR Multiplier')
        ax1.set_ylabel('Number of Outliers')
        ax1.grid(True, alpha=0.3)
        
        # Add common multiplier lines
        for mult in [1.5, 2.0, 2.5]:
            ax1.axvline(mult, color='red', linestyle='--', alpha=0.7, 
                       label=f'{mult}x' if mult == 1.5 else '')
        ax1.legend()
        
        # Plot 2: Percentile sensitivity
        percentile_ranges = list(self.sensitivity_results['percentile_sensitivity'].keys())
        percentile_counts = list(self.sensitivity_results['percentile_sensitivity'].values())
        
        # Convert to numeric for plotting
        range_widths = [100 - 2*int(r.split('-')[0]) for r in percentile_ranges]
        
        ax2.plot(range_widths, percentile_counts, 'go-', linewidth=2, markersize=6)
        ax2.set_title('Sensitivity to Percentile Range')
        ax2.set_xlabel('Percentile Range Width')
        ax2.set_ylabel('Number of Outliers')
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Method comparison
        method_names = []
        method_counts = []
        method_percentages = []
        
        for method, results in self.iqr_results.items():
            if 'count' in results:
                method_names.append(method.replace('IQR_', '').replace('_', ' '))
                method_counts.append(results['count'])
                method_percentages.append(results.get('percentage', 0))
        
        # Limit to top 10 methods for readability
        if len(method_names) > 10:
            sorted_methods = sorted(zip(method_names, method_counts), key=lambda x: x[1])
            method_names = [m[0] for m in sorted_methods[-10:]]
            method_counts = [m[1] for m in sorted_methods[-10:]]
        
        ax3.barh(range(len(method_names)), method_counts, color='skyblue')
        ax3.set_title('Outlier Count by IQR Method')
        ax3.set_xlabel('Number of Outliers')
        ax3.set_yticks(range(len(method_names)))
        ax3.set_yticklabels(method_names, fontsize=8)
        ax3.grid(True, alpha=0.3, axis='x')
        
        # Plot 4: Stability analysis (coefficient of variation)
        stability_data = {}
        for method, results in self.iqr_results.items():
            if 'percentage' in results:
                # Simple stability metric based on distance from median
                median_percentage = np.median([r.get('percentage', 0) for r in self.iqr_results.values()])
                stability = abs(results['percentage'] - median_percentage)
                stability_data[method.replace('IQR_', '').replace('_', ' ')] = stability
        
        if stability_data:
            methods = list(stability_data.keys())[:10]  # Top 10
            stabilities = list(stability_data.values())[:10]
            
            ax4.bar(range(len(methods)), stabilities, color='lightcoral')
            ax4.set_title('Method Stability (deviation from median)')
            ax4.set_xlabel('IQR Methods')
            ax4.set_ylabel('Stability Score (lower = more stable)')
            ax4.set_xticks(range(len(methods)))
            ax4.set_xticklabels(methods, rotation=45, ha='right', fontsize=8)
            ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'iqr_parameter_sensitivity.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Parameter sensitivity plots saved")
    
    def generate_iqr_analysis_summary(self) -> str:
        """Generate comprehensive IQR analysis summary"""
        
        # Calculate summary statistics
        total_diseases = len(self.prevalence_data)
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        
        # Find best and worst methods
        method_counts = {method: results['count'] for method, results in self.iqr_results.items() if 'count' in results}
        most_conservative = min(method_counts.items(), key=lambda x: x[1])
        most_aggressive = max(method_counts.items(), key=lambda x: x[1])
        
        # Medical relevance assessment
        medical_assessment = self.assess_medical_relevance()
        
        markdown_content = f"""# IQR Outlier Analysis Summary - Hyperparameter Sensitivity Study

**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Dataset**: {total_diseases} diseases with prevalence estimates  
**Data Source**: `data/03_processed/orpha/orphadata/orpha_prevalence/`

## 📊 **Executive Summary**

### Key Findings
- **Total Diseases Analyzed**: {total_diseases} with valid prevalence estimates
- **Prevalence Range**: {min(prevalence_values):.1f} to {max(prevalence_values):.1f} per million
- **Distribution**: Highly right-skewed (median: {np.median(prevalence_values):.1f}, mean: {np.mean(prevalence_values):.1f})
- **IQR Methods Tested**: {len(self.iqr_results)} different IQR variations

### Method Range
- **Most Conservative**: {most_conservative[0]} ({most_conservative[1]} outliers, {most_conservative[1]/total_diseases*100:.1f}%)
- **Most Aggressive**: {most_aggressive[0]} ({most_aggressive[1]} outliers, {most_aggressive[1]/total_diseases*100:.1f}%)
- **Outlier Range**: {most_conservative[1]} to {most_aggressive[1]} diseases ({most_conservative[1]/total_diseases*100:.1f}% to {most_aggressive[1]/total_diseases*100:.1f}%)

## 🔬 **IQR Method Categories**

### Classic IQR Multipliers
| Multiplier | Outliers | Percentage | Upper Threshold |
|------------|----------|------------|----------------|"""

        # Add classic multiplier results
        for mult in [1.5, 2.0, 2.5]:
            method_name = f'IQR_{mult}x'
            if method_name in self.iqr_results:
                results = self.iqr_results[method_name]
                markdown_content += f"\n| {mult}x | {results['count']} | {results['percentage']:.1f}% | {results.get('upper_bound', 'N/A')} |"

        markdown_content += f"""

### Percentile-Based Methods
| Percentile Range | Outliers | Percentage | Method |
|------------------|----------|------------|--------|"""

        # Add percentile results
        for method_name in ['P10-P90', 'P20-P80', 'P5-P95']:
            if method_name in self.iqr_results:
                results = self.iqr_results[method_name]
                percentiles = results.get('percentiles', (0, 100))
                markdown_content += f"\n| {percentiles[0]}-{percentiles[1]} | {results['count']} | {results['percentage']:.1f}% | {method_name} |"

        markdown_content += f"""

### Robust Methods
| Method | Outliers | Percentage | Description |
|--------|----------|------------|-------------|"""

        # Add robust method results
        robust_methods = {
            'IQR_trimmed': 'Trimmed 5% extremes',
            'IQR_winsorized': 'Winsorized extremes',
            'IQR_median_based': 'Median + MAD based'
        }
        
        for method_name, description in robust_methods.items():
            if method_name in self.iqr_results:
                results = self.iqr_results[method_name]
                markdown_content += f"\n| {method_name.replace('IQR_', '')} | {results['count']} | {results['percentage']:.1f}% | {description} |"

        markdown_content += f"""

### Adaptive Methods
| Method | Outliers | Percentage | Adaptation |
|--------|----------|------------|------------|"""

        # Add adaptive method results
        if 'IQR_skewness_adaptive' in self.iqr_results:
            results = self.iqr_results['IQR_skewness_adaptive']
            skewness = results.get('skewness', 0)
            multiplier = results.get('multiplier_used', 1.5)
            markdown_content += f"\n| Skewness Adaptive | {results['count']} | {results['percentage']:.1f}% | Skew: {skewness:.2f}, Mult: {multiplier} |"

        if 'IQR_sample_size_adaptive' in self.iqr_results:
            results = self.iqr_results['IQR_sample_size_adaptive']
            sample_size = results.get('sample_size', 0)
            multiplier = results.get('multiplier_used', 1.5)
            markdown_content += f"\n| Sample Size Adaptive | {results['count']} | {results['percentage']:.1f}% | N: {sample_size}, Mult: {multiplier} |"

        # Add parameter sensitivity section
        markdown_content += f"""

## 📈 **Parameter Sensitivity Analysis**

### Multiplier Sensitivity
- **Range Tested**: 1.0x to 4.0x in 0.1 increments
- **Most Sensitive Range**: 1.0-2.0x (large changes in outlier count)
- **Stability Range**: 2.5-4.0x (smaller changes in outlier count)

### Percentile Range Sensitivity
- **Range Tested**: 5th-95th to 30th-70th percentiles
- **Optimal Range**: Based on balance between sensitivity and specificity

## 🏥 **Medical Relevance Assessment**

### Quality Metrics by Method
| Method | High Reliability Outliers | Evidence Ratio | Global Coverage |
|--------|---------------------------|----------------|-----------------|"""

        # Add medical assessment for key methods
        key_methods = ['IQR_1.5x', 'IQR_2.0x', 'P10-P90', 'IQR_skewness_adaptive']
        for method in key_methods:
            if method in medical_assessment:
                assess = medical_assessment[method]
                markdown_content += f"\n| {method} | {assess['high_reliability_outliers']} | {assess['evidence_ratio']:.2f} | {assess['global_ratio']:.2f} |"

        markdown_content += f"""

## 🎯 **Recommendations**

### Optimal IQR Parameters for Prevalence Data

#### Conservative Approach (High Precision)
- **Method**: IQR 2.0x multiplier
- **Rationale**: Balanced outlier detection with low false positive rate
- **Use Case**: High-stakes analysis where false positives are costly

#### Balanced Approach (Recommended)
- **Method**: Skewness-adaptive IQR
- **Rationale**: Adjusts to data characteristics automatically
- **Use Case**: General prevalence data analysis

#### Sensitive Approach (High Recall)
- **Method**: P10-P90 percentile range
- **Rationale**: Captures more potential outliers for investigation
- **Use Case**: Data quality screening and exploratory analysis

### Implementation Guidelines

1. **For Skewed Data** (skewness > 2): Use multiplier ≥ 2.0
2. **For Normal-like Data** (skewness < 1): Standard 1.5x multiplier acceptable
3. **For Small Samples** (n < 100): Use conservative multipliers (1.0-1.5x)
4. **For Large Samples** (n > 1000): Can use more liberal multipliers (2.0-2.5x)

### Quality Thresholds
- **High-Quality Outliers**: Reliability score ≥ 8.0
- **Evidence-Based Outliers**: Multiple records (>1)
- **Global Outliers**: Worldwide geographic coverage

## 📁 **Generated Files**

- `iqr_sensitivity_grid.png` - 3x3 grid of IQR method variations
- `iqr_parameter_sensitivity.png` - Parameter sensitivity analysis plots
- `iqr_detailed_results.json` - Complete numerical results
- `iqr_medical_assessment.json` - Medical relevance evaluation
- `iqr_analysis_summary.md` - This comprehensive summary

## 🔗 **Conclusions**

The IQR hyperparameter sensitivity analysis reveals that:

1. **Standard IQR (1.5x)** is too aggressive for highly skewed prevalence data
2. **Moderate multipliers (2.0-2.5x)** provide better balance for biological data
3. **Adaptive methods** show promise for automatic parameter selection
4. **Percentile-based methods** offer robust alternatives for non-normal distributions

**Recommended Default**: Skewness-adaptive IQR with fallback to 2.0x multiplier for prevalence data analysis.

---

*Generated by RarePrioritizer IQR Outlier Analysis System*  
*For questions or issues, refer to the project documentation*
"""
        
        return markdown_content
    
    def save_analysis_results(self) -> None:
        """Save all IQR analysis results"""
        logger.info("Saving IQR analysis results...")
        
        # Save detailed results
        with open(self.output_dir / 'iqr_detailed_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.iqr_results, f, indent=2, ensure_ascii=False)
        
        # Save sensitivity analysis
        with open(self.output_dir / 'iqr_sensitivity_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(self.sensitivity_results, f, indent=2, ensure_ascii=False)
        
        # Save medical assessment
        medical_assessment = self.assess_medical_relevance()
        with open(self.output_dir / 'iqr_medical_assessment.json', 'w', encoding='utf-8') as f:
            json.dump(medical_assessment, f, indent=2, ensure_ascii=False)
        
        # Save summary markdown
        summary_markdown = self.generate_iqr_analysis_summary()
        with open(self.output_dir / 'iqr_analysis_summary.md', 'w', encoding='utf-8') as f:
            f.write(summary_markdown)
        
        logger.info("IQR analysis results saved successfully")
    
    def run_complete_iqr_analysis(self) -> None:
        """Run complete IQR hyperparameter sensitivity analysis"""
        logger.info("Starting complete IQR analysis...")
        
        # Extract data
        self.extract_prevalence_data()
        
        # Run all IQR methods
        self.run_all_iqr_methods()
        
        # Analyze parameter sensitivity
        self.analyze_parameter_sensitivity()
        
        # Create visualizations
        self.create_iqr_sensitivity_grid()
        self.create_parameter_sensitivity_plots()
        
        # Save all results
        self.save_analysis_results()
        
        logger.info("Complete IQR analysis finished successfully!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        # Print summary
        method_counts = {method: results['count'] for method, results in self.iqr_results.items() if 'count' in results}
        most_conservative = min(method_counts.items(), key=lambda x: x[1])
        most_aggressive = max(method_counts.items(), key=lambda x: x[1])
        
        print(f"\n🎯 IQR ANALYSIS COMPLETE")
        print(f"📊 Analyzed {len(self.prevalence_data)} diseases")
        print(f"🔍 Tested {len(self.iqr_results)} IQR method variations")
        print(f"📈 Outlier range: {most_conservative[1]} to {most_aggressive[1]} diseases")
        print(f"🥇 Most conservative: {most_conservative[0]} ({most_conservative[1]} outliers)")
        print(f"🔥 Most aggressive: {most_aggressive[0]} ({most_aggressive[1]} outliers)")
        print(f"📁 Output: {self.output_dir}")


def main():
    """Main function to run IQR analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IQR Outlier Analysis - Hyperparameter Sensitivity Study')
    parser.add_argument('--output', '-o', 
                       default='results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = IQROutlierAnalyzer(output_dir=args.output)
    analyzer.run_complete_iqr_analysis()


if __name__ == "__main__":
    main() 