#!/usr/bin/env python3
"""
Asymmetric 1.5 IQR Analysis Script

This script analyzes the asymmetric 1.5 IQR method for outlier detection,
showing original data, outliers highlighted, and clean data in a 3x1 plot.
Only removes upper outliers (Q3 + 1.5*IQR), not lower outliers.

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


class AsymmetricIQRAnalyzer:
    """Asymmetric 1.5 IQR method analysis for prevalence data (upper outliers only)"""
    
    def __init__(self, output_dir: str = "results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only"):
        """Initialize the asymmetric IQR analyzer"""
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
        
        logger.info(f"Asymmetric IQR analyzer initialized with output dir: {output_dir}")
    
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
    
    def apply_asymmetric_iqr(self, data: List[float]) -> Dict:
        """Apply asymmetric 1.5 IQR method (remove upper outliers only)"""
        
        # Calculate quartiles
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        # Calculate upper threshold only (asymmetric approach)
        upper_threshold = q3 + 1.5 * iqr
        
        # Identify outliers (only upper outliers)
        outliers = [x for x in data if x > upper_threshold]
        
        # Clean data (remove upper outliers only)
        clean_data = [x for x in data if x <= upper_threshold]
        
        # Calculate statistics
        results = {
            'original_data': data,
            'outliers': outliers,
            'clean_data': clean_data,
            'q1': q1,
            'q3': q3,
            'iqr': iqr,
            'upper_threshold': upper_threshold,
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
            if item['prevalence'] in self.iqr_results['outliers']:
                outlier_diseases.append(item)
        
        # Sort by prevalence descending
        outlier_diseases.sort(key=lambda x: x['prevalence'], reverse=True)
        
        return outlier_diseases
    
    def create_iqr_analysis_plot(self) -> None:
        """Create 3x1 plot showing original, outliers highlighted, and clean data"""
        logger.info("Creating asymmetric IQR analysis plot...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        self.iqr_results = self.apply_asymmetric_iqr(prevalence_values)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
        fig.suptitle('Asymmetric 1.5 IQR Method Analysis\nPrevalence Data Outlier Detection (Upper Outliers Only)', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Panel 1: Original Data
        ax1.hist(self.iqr_results['original_data'], bins=50, density=True, alpha=0.7, 
                color='steelblue', label=f'Original Data (n={len(self.iqr_results["original_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        # Add IQR threshold lines
        ax1.axvline(self.iqr_results['q1'], color='green', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q1: {self.iqr_results["q1"]:.1f}')
        ax1.axvline(self.iqr_results['q3'], color='orange', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q3: {self.iqr_results["q3"]:.1f}')
        ax1.axvline(self.iqr_results['upper_threshold'], color='red', linestyle='--', linewidth=2,
                   label=f'Upper Threshold: {self.iqr_results["upper_threshold"]:.1f}')
        
        ax1.set_title('Panel 1: Original Prevalence Data Distribution', fontweight='bold', fontsize=14)
        ax1.set_xlabel('Prevalence (per million)', fontsize=12)
        ax1.set_ylabel('Density', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        orig_stats = self.iqr_results['original_stats']
        stats_text = f'Mean: {orig_stats["mean"]:.1f}\nMedian: {orig_stats["median"]:.1f}\n'
        stats_text += f'Std: {orig_stats["std"]:.1f}\nSkewness: {orig_stats["skewness"]:.2f}\n'
        stats_text += f'IQR: {self.iqr_results["iqr"]:.1f}'
        ax1.text(0.7, 0.8, stats_text, transform=ax1.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Panel 2: Data with Outliers Highlighted
        # Create histogram for all data
        ax2.hist(self.iqr_results['original_data'], bins=50, density=True, alpha=0.6, 
                color='steelblue', label=f'All Data (n={len(self.iqr_results["original_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        # Highlight outliers with different histogram
        if self.iqr_results['outliers']:
            ax2.hist(self.iqr_results['outliers'], bins=min(20, len(self.iqr_results['outliers'])), 
                    density=True, alpha=0.8, color='red', 
                    label=f'Outliers (n={len(self.iqr_results["outliers"])})', 
                    edgecolor='darkred', linewidth=1.0)
        
        # Add threshold lines
        ax2.axvline(self.iqr_results['q3'], color='orange', linestyle=':', linewidth=2, alpha=0.7,
                   label=f'Q3: {self.iqr_results["q3"]:.1f}')
        ax2.axvline(self.iqr_results['upper_threshold'], color='red', linestyle='--', linewidth=2,
                   label=f'Upper Threshold: {self.iqr_results["upper_threshold"]:.1f}')
        
        ax2.set_title('Panel 2: Outliers Highlighted (Above Q3 + 1.5×IQR)', fontweight='bold', fontsize=14)
        ax2.set_xlabel('Prevalence (per million)', fontsize=12)
        ax2.set_ylabel('Density', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Add outlier statistics
        outlier_text = f'Outliers: {len(self.iqr_results["outliers"])} ({self.iqr_results["outlier_percentage"]:.1f}%)\n'
        outlier_text += f'Upper Threshold: {self.iqr_results["upper_threshold"]:.1f}\n'
        outlier_text += f'Max Outlier: {max(self.iqr_results["outliers"]) if self.iqr_results["outliers"] else "None":.1f}\n'
        outlier_text += f'IQR: {self.iqr_results["iqr"]:.1f}'
        ax2.text(0.7, 0.8, outlier_text, transform=ax2.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        # Panel 3: Clean Data (Outliers Removed)
        ax3.hist(self.iqr_results['clean_data'], bins=50, density=True, alpha=0.7, 
                color='green', label=f'Clean Data (n={len(self.iqr_results["clean_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        ax3.set_title('Panel 3: Clean Data Distribution (After Asymmetric IQR)', fontweight='bold', fontsize=14)
        ax3.set_xlabel('Prevalence (per million)', fontsize=12)
        ax3.set_ylabel('Density', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        # Add clean statistics
        clean_stats = self.iqr_results['clean_stats']
        clean_text = f'Mean: {clean_stats["mean"]:.1f}\nMedian: {clean_stats["median"]:.1f}\n'
        clean_text += f'Std: {clean_stats["std"]:.1f}\nSkewness: {clean_stats["skewness"]:.2f}'
        ax3.text(0.7, 0.8, clean_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
        
        # Add comparison text
        improvement_text = f'Skewness Reduction: {orig_stats["skewness"]:.2f} → {clean_stats["skewness"]:.2f}\n'
        improvement_text += f'Std Reduction: {orig_stats["std"]:.1f} → {clean_stats["std"]:.1f}\n'
        improvement_text += f'Data Retained: {self.iqr_results["clean_percentage"]:.1f}%'
        ax3.text(0.05, 0.8, improvement_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output_dir / 'iqr_asymmetric_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("Asymmetric IQR analysis plot saved")
    
    def generate_iqr_summary_stats(self) -> Dict:
        """Generate comprehensive asymmetric IQR method statistics"""
        
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
                'method_name': 'Asymmetric 1.5 IQR',
                'description': 'Remove values above Q3 + 1.5×IQR (upper outliers only)',
                'threshold_type': 'Upper threshold only (asymmetric)',
                'multiplier': 1.5
            },
            'dataset_info': {
                'total_diseases': len(self.prevalence_data),
                'outliers_detected': len(outlier_diseases),
                'outlier_percentage': len(outlier_diseases) / len(self.prevalence_data) * 100,
                'clean_diseases': len(self.prevalence_data) - len(outlier_diseases),
                'clean_percentage': (len(self.prevalence_data) - len(outlier_diseases)) / len(self.prevalence_data) * 100
            },
            'threshold_info': {
                'q1': self.iqr_results['q1'],
                'q3': self.iqr_results['q3'],
                'iqr': self.iqr_results['iqr'],
                'upper_threshold': self.iqr_results['upper_threshold'],
                'min_outlier': min(self.iqr_results['outliers']) if self.iqr_results['outliers'] else None,
                'max_outlier': max(self.iqr_results['outliers']) if self.iqr_results['outliers'] else None
            },
            'statistical_improvement': {
                'original_skewness': self.iqr_results['original_stats']['skewness'],
                'clean_skewness': self.iqr_results['clean_stats']['skewness'],
                'skewness_reduction': self.iqr_results['original_stats']['skewness'] - self.iqr_results['clean_stats']['skewness'],
                'original_std': self.iqr_results['original_stats']['std'],
                'clean_std': self.iqr_results['clean_stats']['std'],
                'std_reduction': self.iqr_results['original_stats']['std'] - self.iqr_results['clean_stats']['std'],
                'original_mean': self.iqr_results['original_stats']['mean'],
                'clean_mean': self.iqr_results['clean_stats']['mean']
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
    
    def save_iqr_results(self) -> None:
        """Save asymmetric IQR analysis results"""
        logger.info("Saving asymmetric IQR analysis results...")
        
        # Generate comprehensive statistics
        summary_stats = self.generate_iqr_summary_stats()
        
        # Save detailed results
        with open(self.output_dir / 'iqr_asymmetric_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'iqr_results': self.iqr_results,
                'summary_stats': summary_stats
            }, f, indent=2, ensure_ascii=False)
        
        logger.info("Asymmetric IQR analysis results saved successfully")
    
    def run_iqr_analysis(self) -> Dict:
        """Run complete asymmetric IQR analysis"""
        logger.info("Starting asymmetric IQR analysis...")
        
        # Extract data
        self.extract_prevalence_data()
        
        # Create visualization
        self.create_iqr_analysis_plot()
        
        # Save results
        self.save_iqr_results()
        
        # Generate summary statistics
        summary_stats = self.generate_iqr_summary_stats()
        
        logger.info("Asymmetric IQR analysis complete!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        # Print summary
        print(f"\n🎯 ASYMMETRIC 1.5 IQR ANALYSIS COMPLETE")
        print(f"📊 Analyzed {len(self.prevalence_data)} diseases")
        print(f"🔍 IQR: {self.iqr_results['iqr']:.1f}")
        print(f"🔍 Upper Threshold: {self.iqr_results['upper_threshold']:.1f} per million")
        print(f"🚫 Outliers Detected: {len(self.iqr_results['outliers'])} ({self.iqr_results['outlier_percentage']:.1f}%)")
        print(f"✅ Clean Data: {len(self.iqr_results['clean_data'])} ({self.iqr_results['clean_percentage']:.1f}%)")
        print(f"📈 Skewness Improvement: {self.iqr_results['original_stats']['skewness']:.2f} → {self.iqr_results['clean_stats']['skewness']:.2f}")
        print(f"📁 Output: {self.output_dir}")
        
        return summary_stats


def main():
    """Main function to run asymmetric IQR analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Asymmetric 1.5 IQR Analysis for Prevalence Data')
    parser.add_argument('--output', '-o', 
                       default='results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = AsymmetricIQRAnalyzer(output_dir=args.output)
    analyzer.run_iqr_analysis()


if __name__ == "__main__":
    main() 