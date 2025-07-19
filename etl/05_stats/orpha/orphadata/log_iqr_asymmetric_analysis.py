#!/usr/bin/env python3
"""
Log + Asymmetric 1.5 IQR Analysis Script

This script applies log transformation followed by asymmetric 1.5 IQR method for outlier detection.
The log transformation reduces skewness, making IQR method more effective.
Shows original data, outliers highlighted, and clean data in a 3x1 plot.

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
from collections import defaultdict
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


class LogIQRAsymmetricAnalyzer:
    """Log transformation + Asymmetric 1.5 IQR method analysis for prevalence data"""
    
    def __init__(self, output_dir: str = "results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only"):
        """Initialize the log + asymmetric IQR analyzer"""
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
        self.log_iqr_results = {}
        
        logger.info(f"Log + Asymmetric IQR analyzer initialized with output dir: {output_dir}")
    
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
    
    def apply_log_iqr_asymmetric(self, data: List[float]) -> Dict:
        """Apply log transformation followed by asymmetric 1.5 IQR method"""
        
        # Apply log transformation (log10 for interpretability)
        # Add small constant to handle potential zeros
        log_data = [np.log10(x + 0.01) for x in data]
        
        # Calculate quartiles on log-transformed data
        q1_log = np.percentile(log_data, 25)
        q3_log = np.percentile(log_data, 75)
        iqr_log = q3_log - q1_log
        
        # Calculate upper threshold on log scale
        upper_threshold_log = q3_log + 1.5 * iqr_log
        
        # Transform thresholds back to original scale
        q1_original = 10**(q1_log) - 0.01
        q3_original = 10**(q3_log) - 0.01
        upper_threshold_original = 10**(upper_threshold_log) - 0.01
        
        # Identify outliers on original scale
        outliers = [x for x in data if x > upper_threshold_original]
        
        # Clean data (remove upper outliers only)
        clean_data = [x for x in data if x <= upper_threshold_original]
        
        # Calculate statistics
        results = {
            'original_data': data,
            'log_data': log_data,
            'outliers': outliers,
            'clean_data': clean_data,
            'q1_log': q1_log,
            'q3_log': q3_log,
            'iqr_log': iqr_log,
            'upper_threshold_log': upper_threshold_log,
            'q1_original': q1_original,
            'q3_original': q3_original,
            'upper_threshold_original': upper_threshold_original,
            'outlier_count': len(outliers),
            'outlier_percentage': len(outliers) / len(data) * 100,
            'clean_count': len(clean_data),
            'clean_percentage': len(clean_data) / len(data) * 100,
            'original_stats': {
                'mean': np.mean(data),
                'median': np.median(data),
                'std': np.std(data),
                'min': np.min(data),
                'max': np.max(data),
                'skewness': stats.skew(data),
                'kurtosis': stats.kurtosis(data)
            },
            'log_stats': {
                'mean': np.mean(log_data),
                'median': np.median(log_data),
                'std': np.std(log_data),
                'min': np.min(log_data),
                'max': np.max(log_data),
                'skewness': stats.skew(log_data),
                'kurtosis': stats.kurtosis(log_data)
            },
            'clean_stats': {
                'mean': np.mean(clean_data),
                'median': np.median(clean_data),
                'std': np.std(clean_data),
                'min': np.min(clean_data),
                'max': np.max(clean_data),
                'skewness': stats.skew(clean_data),
                'kurtosis': stats.kurtosis(clean_data)
            }
        }
        
        return results
    
    def get_outlier_diseases(self) -> List[Dict]:
        """Get disease details for outliers"""
        outlier_diseases = []
        
        for item in self.prevalence_data:
            if item['prevalence'] in self.log_iqr_results['outliers']:
                outlier_diseases.append(item)
        
        # Sort by prevalence descending
        outlier_diseases.sort(key=lambda x: x['prevalence'], reverse=True)
        
        return outlier_diseases
    
    def create_log_iqr_analysis_plot(self) -> None:
        """Create 3x1 plot showing log-transformed data, outliers highlighted, and clean data"""
        logger.info("Creating log + asymmetric IQR analysis plot...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        self.log_iqr_results = self.apply_log_iqr_asymmetric(prevalence_values)
        
        # Create log-transformed outlier and clean data for plotting
        log_outliers = [np.log10(x + 0.01) for x in self.log_iqr_results['outliers']]
        log_clean = [np.log10(x + 0.01) for x in self.log_iqr_results['clean_data']]
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
        fig.suptitle('Log + Asymmetric 1.5 IQR Method Analysis\nPrevalence Data Outlier Detection (Log-Transformed Space)', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Panel 1: Log-transformed Data
        ax1.hist(self.log_iqr_results['log_data'], bins=200, density=False, alpha=0.7, 
                color='steelblue', label=f'Log Data (n={len(self.log_iqr_results["log_data"])})', 
                edgecolor='black', linewidth=0.3)
        
        # Add threshold lines (on log scale)
        ax1.axvline(self.log_iqr_results['q1_log'], color='green', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q1 (log): {self.log_iqr_results["q1_log"]:.2f}')
        ax1.axvline(self.log_iqr_results['q3_log'], color='orange', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q3 (log): {self.log_iqr_results["q3_log"]:.2f}')
        ax1.axvline(self.log_iqr_results['upper_threshold_log'], color='red', linestyle='--', linewidth=2,
                   label=f'Upper Threshold: {self.log_iqr_results["upper_threshold_log"]:.2f}')
        
        ax1.set_title('Panel 1: Log-Transformed Prevalence Data Distribution', fontweight='bold', fontsize=14)
        ax1.set_xlabel('Log10(Prevalence + 0.01)', fontsize=12)
        ax1.set_ylabel('Number of Cases', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        orig_stats = self.log_iqr_results['original_stats']
        log_stats = self.log_iqr_results['log_stats']
        stats_text = f'Original Skewness: {orig_stats["skewness"]:.2f}\nLog Skewness: {log_stats["skewness"]:.2f}\n'
        stats_text += f'Log Mean: {log_stats["mean"]:.2f}\nLog Median: {log_stats["median"]:.2f}\n'
        stats_text += f'IQR (log): {self.log_iqr_results["iqr_log"]:.2f}'
        ax1.text(0.7, 0.8, stats_text, transform=ax1.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Panel 2: Log Data with Outliers Highlighted
        # Create histogram for all log data
        ax2.hist(self.log_iqr_results['log_data'], bins=200, density=False, alpha=0.6, 
                color='steelblue', label=f'All Log Data (n={len(self.log_iqr_results["log_data"])})', 
                edgecolor='black', linewidth=0.3)
        
        # Highlight outliers with different histogram
        if log_outliers:
            ax2.hist(log_outliers, bins=min(50, len(log_outliers)), 
                    density=False, alpha=0.8, color='red', 
                    label=f'Outliers (n={len(log_outliers)})', 
                    edgecolor='darkred', linewidth=0.5)
        
        # Add threshold lines
        ax2.axvline(self.log_iqr_results['q3_log'], color='orange', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q3 (log): {self.log_iqr_results["q3_log"]:.2f}')
        ax2.axvline(self.log_iqr_results['upper_threshold_log'], color='red', linestyle='--', linewidth=2,
                   label=f'Upper Threshold: {self.log_iqr_results["upper_threshold_log"]:.2f}')
        
        ax2.set_title('Panel 2: Outliers Highlighted (Log-Based IQR Threshold)', fontweight='bold', fontsize=14)
        ax2.set_xlabel('Log10(Prevalence + 0.01)', fontsize=12)
        ax2.set_ylabel('Number of Cases', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Add outlier statistics
        outlier_text = f'Outliers: {len(self.log_iqr_results["outliers"])} ({self.log_iqr_results["outlier_percentage"]:.1f}%)\n'
        outlier_text += f'Log threshold: {self.log_iqr_results["upper_threshold_log"]:.2f}\n'
        outlier_text += f'Original threshold: {self.log_iqr_results["upper_threshold_original"]:.1f}\n'
        outlier_text += f'Log IQR: {self.log_iqr_results["iqr_log"]:.2f}'
        ax2.text(0.7, 0.8, outlier_text, transform=ax2.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        # Panel 3: Clean Log Data (Outliers Removed)
        ax3.hist(log_clean, bins=200, density=False, alpha=0.7, 
                color='green', label=f'Clean Log Data (n={len(log_clean)})', 
                edgecolor='black', linewidth=0.3)
        
        # Set x-axis limits to show truncation clearly
        ax3.set_xlim(min(self.log_iqr_results['log_data']) - 0.1, 
                     self.log_iqr_results['upper_threshold_log'] + 0.1)
        
        # Add vertical line to show where data was cut off
        ax3.axvline(self.log_iqr_results['upper_threshold_log'], color='red', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'Cut-off Threshold: {self.log_iqr_results["upper_threshold_log"]:.2f}')
        
        ax3.set_title('Panel 3: Clean Log Data Distribution (Truncated at Threshold)', fontweight='bold', fontsize=14)
        ax3.set_xlabel('Log10(Prevalence + 0.01)', fontsize=12)
        ax3.set_ylabel('Number of Cases', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        # Add clean statistics (log scale)
        log_clean_stats = {
            'mean': np.mean(log_clean),
            'median': np.median(log_clean),
            'std': np.std(log_clean),
            'skewness': stats.skew(log_clean)
        }
        clean_text = f'Log Mean: {log_clean_stats["mean"]:.2f}\nLog Median: {log_clean_stats["median"]:.2f}\n'
        clean_text += f'Log Std: {log_clean_stats["std"]:.2f}\nLog Skewness: {log_clean_stats["skewness"]:.2f}'
        ax3.text(0.7, 0.8, clean_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
        
        # Add comparison text showing truncation info
        improvement_text = f'Data Retained: {self.log_iqr_results["clean_percentage"]:.1f}%\n'
        improvement_text += f'Outliers Removed: {len(self.log_iqr_results["outliers"])} cases\n'
        improvement_text += f'Max Value: {max(log_clean):.2f}\n'
        improvement_text += f'Truncated at: {self.log_iqr_results["upper_threshold_log"]:.2f}'
        ax3.text(0.05, 0.8, improvement_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output_dir / 'log_iqr_asymmetric_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Log + asymmetric IQR analysis plot saved")
    
    def generate_log_iqr_summary_stats(self) -> Dict:
        """Generate comprehensive log + IQR method statistics"""
        
        outlier_diseases = self.get_outlier_diseases()
        
        # Medical relevance assessment
        high_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] >= 8.0])
        medium_reliability_outliers = len([d for d in outlier_diseases if 6.0 <= d['reliability_score'] < 8.0])
        low_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] < 6.0])
        
        single_record_outliers = len([d for d in outlier_diseases if d['records_count'] == 1])
        multiple_record_outliers = len([d for d in outlier_diseases if d['records_count'] > 1])
        
        worldwide_outliers = len([d for d in outlier_diseases if d['has_worldwide']])
        
        # Top outliers by prevalence
        top_outliers = outlier_diseases[:10]  # Top 10
        
        summary_stats = {
            'method_info': {
                'method_name': 'Log + Asymmetric 1.5 IQR',
                'description': 'Apply log10 transformation then asymmetric 1.5 IQR on log scale',
                'threshold_type': 'Log-transformed upper threshold only',
                'multiplier': 1.5,
                'transformation': 'log10'
            },
            'dataset_info': {
                'total_diseases': len(self.prevalence_data),
                'outliers_detected': len(outlier_diseases),
                'outlier_percentage': len(outlier_diseases) / len(self.prevalence_data) * 100,
                'clean_diseases': len(self.prevalence_data) - len(outlier_diseases),
                'clean_percentage': (len(self.prevalence_data) - len(outlier_diseases)) / len(self.prevalence_data) * 100
            },
            'threshold_info': {
                'q1_log': self.log_iqr_results['q1_log'],
                'q3_log': self.log_iqr_results['q3_log'],
                'iqr_log': self.log_iqr_results['iqr_log'],
                'upper_threshold_log': self.log_iqr_results['upper_threshold_log'],
                'q1_original': self.log_iqr_results['q1_original'],
                'q3_original': self.log_iqr_results['q3_original'],
                'upper_threshold_original': self.log_iqr_results['upper_threshold_original'],
                'min_outlier': min(self.log_iqr_results['outliers']) if self.log_iqr_results['outliers'] else None,
                'max_outlier': max(self.log_iqr_results['outliers']) if self.log_iqr_results['outliers'] else None
            },
            'statistical_improvement': {
                'original_skewness': self.log_iqr_results['original_stats']['skewness'],
                'log_skewness': self.log_iqr_results['log_stats']['skewness'],
                'clean_skewness': self.log_iqr_results['clean_stats']['skewness'],
                'skewness_reduction': self.log_iqr_results['original_stats']['skewness'] - self.log_iqr_results['clean_stats']['skewness'],
                'log_transformation_benefit': self.log_iqr_results['original_stats']['skewness'] - self.log_iqr_results['log_stats']['skewness'],
                'original_std': self.log_iqr_results['original_stats']['std'],
                'clean_std': self.log_iqr_results['clean_stats']['std'],
                'std_reduction': self.log_iqr_results['original_stats']['std'] - self.log_iqr_results['clean_stats']['std'],
                'original_mean': self.log_iqr_results['original_stats']['mean'],
                'clean_mean': self.log_iqr_results['clean_stats']['mean']
            },
            'medical_assessment': {
                'high_reliability_outliers': high_reliability_outliers,
                'medium_reliability_outliers': medium_reliability_outliers,
                'low_reliability_outliers': low_reliability_outliers,
                'single_record_outliers': single_record_outliers,
                'multiple_record_outliers': multiple_record_outliers,
                'worldwide_outliers': worldwide_outliers,
                'quality_ratio': high_reliability_outliers / max(len(outlier_diseases), 1),
                'evidence_ratio': multiple_record_outliers / max(len(outlier_diseases), 1),
                'global_ratio': worldwide_outliers / max(len(outlier_diseases), 1)
            },
            'top_outliers': top_outliers,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        return summary_stats
    
    def save_log_iqr_results(self) -> None:
        """Save log + IQR analysis results"""
        logger.info("Saving log + asymmetric IQR analysis results...")
        
        # Generate comprehensive statistics
        summary_stats = self.generate_log_iqr_summary_stats()
        
        # Save detailed results
        with open(self.output_dir / 'log_iqr_asymmetric_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'log_iqr_results': self.log_iqr_results,
                'summary_stats': summary_stats
            }, f, indent=2, ensure_ascii=False)
        
        logger.info("Log + asymmetric IQR analysis results saved successfully")
    
    def run_log_iqr_analysis(self) -> Dict:
        """Run complete log + asymmetric IQR analysis"""
        logger.info("Starting log + asymmetric IQR analysis...")
        
        # Extract data
        self.extract_prevalence_data()
        
        # Create visualization
        self.create_log_iqr_analysis_plot()
        
        # Save results
        self.save_log_iqr_results()
        
        # Generate summary statistics
        summary_stats = self.generate_log_iqr_summary_stats()
        
        logger.info("Log + asymmetric IQR analysis complete!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        # Print summary
        print(f"\n🎯 LOG + ASYMMETRIC 1.5 IQR ANALYSIS COMPLETE")
        print(f"📊 Analyzed {len(self.prevalence_data)} diseases")
        print(f"🔍 Log IQR: {self.log_iqr_results['iqr_log']:.2f}")
        print(f"🔍 Upper Threshold: {self.log_iqr_results['upper_threshold_original']:.1f} per million")
        print(f"🚫 Outliers Detected: {len(self.log_iqr_results['outliers'])} ({self.log_iqr_results['outlier_percentage']:.1f}%)")
        print(f"✅ Clean Data: {len(self.log_iqr_results['clean_data'])} ({self.log_iqr_results['clean_percentage']:.1f}%)")
        print(f"📈 Original Skewness: {self.log_iqr_results['original_stats']['skewness']:.2f}")
        print(f"📈 Log Skewness: {self.log_iqr_results['log_stats']['skewness']:.2f}")
        print(f"📈 Clean Skewness: {self.log_iqr_results['clean_stats']['skewness']:.2f}")
        print(f"📁 Output: {self.output_dir}")
        
        return summary_stats


def main():
    """Main function to run log + asymmetric IQR analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Log + Asymmetric 1.5 IQR Analysis for Prevalence Data')
    parser.add_argument('--output', '-o', 
                       default='results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = LogIQRAsymmetricAnalyzer(output_dir=args.output)
    analyzer.run_log_iqr_analysis()


if __name__ == "__main__":
    main() 