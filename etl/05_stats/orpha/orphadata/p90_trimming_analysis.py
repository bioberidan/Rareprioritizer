#!/usr/bin/env python3
"""
P90 Trimming Analysis Script

This script analyzes the P90 trimming method for outlier detection,
showing original data, outliers highlighted, and clean data in a 3x1 plot.

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


class P90TrimmingAnalyzer:
    """P90 trimming method analysis for prevalence data"""
    
    def __init__(self, output_dir: str = "results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only"):
        """Initialize the P90 trimming analyzer"""
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
        self.p90_results = {}
        
        logger.info(f"P90 trimming analyzer initialized with output dir: {output_dir}")
    
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
    
    def apply_p90_trimming(self, data: List[float]) -> Dict:
        """Apply P90 trimming method (remove top 10% only)"""
        
        # Calculate P90 threshold
        p90_threshold = np.percentile(data, 90)
        
        # Identify outliers (top 10%)
        outliers = [x for x in data if x > p90_threshold]
        
        # Clean data (remove outliers)
        clean_data = [x for x in data if x <= p90_threshold]
        
        # Calculate statistics
        results = {
            'original_data': data,
            'outliers': outliers,
            'clean_data': clean_data,
            'p90_threshold': p90_threshold,
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
            if item['prevalence'] in self.p90_results['outliers']:
                outlier_diseases.append(item)
        
        # Sort by prevalence descending
        outlier_diseases.sort(key=lambda x: x['prevalence'], reverse=True)
        
        return outlier_diseases
    
    def create_p90_analysis_plot(self) -> None:
        """Create 3x1 plot showing original, outliers highlighted, and clean data"""
        logger.info("Creating P90 analysis plot...")
        
        prevalence_values = [item['prevalence'] for item in self.prevalence_data]
        self.p90_results = self.apply_p90_trimming(prevalence_values)
        
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16))
        fig.suptitle('P90 Trimming Method Analysis\nPrevalence Data Outlier Detection', 
                     fontsize=18, fontweight='bold', y=0.98)
        
        # Panel 1: Original Data
        ax1.hist(self.p90_results['original_data'], bins=50, density=True, alpha=0.7, 
                color='steelblue', label=f'Original Data (n={len(self.p90_results["original_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        # Add P90 threshold line
        ax1.axvline(self.p90_results['p90_threshold'], color='red', linestyle='--', linewidth=2,
                   label=f'P90 Threshold: {self.p90_results["p90_threshold"]:.1f}')
        
        ax1.set_title('Panel 1: Original Prevalence Data Distribution', fontweight='bold', fontsize=14)
        ax1.set_xlabel('Prevalence (per million)', fontsize=12)
        ax1.set_ylabel('Density', fontsize=12)
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        orig_stats = self.p90_results['original_stats']
        stats_text = f'Mean: {orig_stats["mean"]:.1f}\nMedian: {orig_stats["median"]:.1f}\n'
        stats_text += f'Std: {orig_stats["std"]:.1f}\nSkewness: {orig_stats["skewness"]:.2f}'
        ax1.text(0.7, 0.8, stats_text, transform=ax1.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # Panel 2: Data with Outliers Highlighted
        # Create histogram for all data
        ax2.hist(self.p90_results['original_data'], bins=50, density=True, alpha=0.6, 
                color='steelblue', label=f'All Data (n={len(self.p90_results["original_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        # Highlight outliers with different histogram
        if self.p90_results['outliers']:
            ax2.hist(self.p90_results['outliers'], bins=min(20, len(self.p90_results['outliers'])), 
                    density=True, alpha=0.8, color='red', 
                    label=f'Outliers (n={len(self.p90_results["outliers"])})', 
                    edgecolor='darkred', linewidth=1.0)
        
        # Add threshold line
        ax2.axvline(self.p90_results['p90_threshold'], color='orange', linestyle='--', linewidth=2,
                   label=f'P90 Threshold: {self.p90_results["p90_threshold"]:.1f}')
        
        ax2.set_title('Panel 2: Outliers Highlighted (Top 10% Above P90)', fontweight='bold', fontsize=14)
        ax2.set_xlabel('Prevalence (per million)', fontsize=12)
        ax2.set_ylabel('Density', fontsize=12)
        ax2.legend(fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        # Add outlier statistics
        outlier_text = f'Outliers: {len(self.p90_results["outliers"])} ({self.p90_results["outlier_percentage"]:.1f}%)\n'
        outlier_text += f'P90 Threshold: {self.p90_results["p90_threshold"]:.1f}\n'
        outlier_text += f'Max Outlier: {max(self.p90_results["outliers"]) if self.p90_results["outliers"] else "None":.1f}'
        ax2.text(0.7, 0.8, outlier_text, transform=ax2.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        # Panel 3: Clean Data (Outliers Removed)
        ax3.hist(self.p90_results['clean_data'], bins=50, density=True, alpha=0.7, 
                color='green', label=f'Clean Data (n={len(self.p90_results["clean_data"])})', 
                edgecolor='black', linewidth=0.5)
        
        ax3.set_title('Panel 3: Clean Data Distribution (After P90 Trimming)', fontweight='bold', fontsize=14)
        ax3.set_xlabel('Prevalence (per million)', fontsize=12)
        ax3.set_ylabel('Density', fontsize=12)
        ax3.legend(fontsize=10)
        ax3.grid(True, alpha=0.3)
        
        # Add clean statistics
        clean_stats = self.p90_results['clean_stats']
        clean_text = f'Mean: {clean_stats["mean"]:.1f}\nMedian: {clean_stats["median"]:.1f}\n'
        clean_text += f'Std: {clean_stats["std"]:.1f}\nSkewness: {clean_stats["skewness"]:.2f}'
        ax3.text(0.7, 0.8, clean_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
        
        # Add comparison text
        improvement_text = f'Skewness Reduction: {orig_stats["skewness"]:.2f} → {clean_stats["skewness"]:.2f}\n'
        improvement_text += f'Std Reduction: {orig_stats["std"]:.1f} → {clean_stats["std"]:.1f}\n'
        improvement_text += f'Data Retained: {self.p90_results["clean_percentage"]:.1f}%'
        ax3.text(0.05, 0.8, improvement_text, transform=ax3.transAxes, fontsize=10,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(self.output_dir / 'p90_trimming_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("P90 analysis plot saved")
    
    def generate_p90_summary_stats(self) -> Dict:
        """Generate comprehensive P90 method statistics"""
        
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
                'method_name': 'P90 Trimming',
                'description': 'Remove top 10% of prevalence values as outliers',
                'threshold_type': 'Upper percentile only',
                'percentile_used': 90
            },
            'dataset_info': {
                'total_diseases': len(self.prevalence_data),
                'outliers_detected': len(outlier_diseases),
                'outlier_percentage': len(outlier_diseases) / len(self.prevalence_data) * 100,
                'clean_diseases': len(self.prevalence_data) - len(outlier_diseases),
                'clean_percentage': (len(self.prevalence_data) - len(outlier_diseases)) / len(self.prevalence_data) * 100
            },
            'threshold_info': {
                'p90_threshold': self.p90_results['p90_threshold'],
                'min_outlier': min(self.p90_results['outliers']) if self.p90_results['outliers'] else None,
                'max_outlier': max(self.p90_results['outliers']) if self.p90_results['outliers'] else None
            },
            'statistical_improvement': {
                'original_skewness': self.p90_results['original_stats']['skewness'],
                'clean_skewness': self.p90_results['clean_stats']['skewness'],
                'skewness_reduction': self.p90_results['original_stats']['skewness'] - self.p90_results['clean_stats']['skewness'],
                'original_std': self.p90_results['original_stats']['std'],
                'clean_std': self.p90_results['clean_stats']['std'],
                'std_reduction': self.p90_results['original_stats']['std'] - self.p90_results['clean_stats']['std'],
                'original_mean': self.p90_results['original_stats']['mean'],
                'clean_mean': self.p90_results['clean_stats']['mean']
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
    
    def save_p90_results(self) -> None:
        """Save P90 analysis results"""
        logger.info("Saving P90 analysis results...")
        
        # Generate comprehensive statistics
        summary_stats = self.generate_p90_summary_stats()
        
        # Save detailed results
        with open(self.output_dir / 'p90_trimming_results.json', 'w', encoding='utf-8') as f:
            json.dump({
                'p90_results': self.p90_results,
                'summary_stats': summary_stats
            }, f, indent=2, ensure_ascii=False)
        
        logger.info("P90 analysis results saved successfully")
    
    def run_p90_analysis(self) -> Dict:
        """Run complete P90 trimming analysis"""
        logger.info("Starting P90 trimming analysis...")
        
        # Extract data
        self.extract_prevalence_data()
        
        # Create visualization
        self.create_p90_analysis_plot()
        
        # Save results
        self.save_p90_results()
        
        # Generate summary statistics
        summary_stats = self.generate_p90_summary_stats()
        
        logger.info("P90 trimming analysis complete!")
        logger.info(f"Results saved to: {self.output_dir}")
        
        # Print summary
        print(f"\n🎯 P90 TRIMMING ANALYSIS COMPLETE")
        print(f"📊 Analyzed {len(self.prevalence_data)} diseases")
        print(f"🔍 P90 Threshold: {self.p90_results['p90_threshold']:.1f} per million")
        print(f"🚫 Outliers Detected: {len(self.p90_results['outliers'])} ({self.p90_results['outlier_percentage']:.1f}%)")
        print(f"✅ Clean Data: {len(self.p90_results['clean_data'])} ({self.p90_results['clean_percentage']:.1f}%)")
        print(f"📈 Skewness Improvement: {self.p90_results['original_stats']['skewness']:.2f} → {self.p90_results['clean_stats']['skewness']:.2f}")
        print(f"📁 Output: {self.output_dir}")
        
        return summary_stats


def main():
    """Main function to run P90 analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description='P90 Trimming Analysis for Prevalence Data')
    parser.add_argument('--output', '-o', 
                       default='results/etl/all_disease_instances/orpha/orphadata/prevalence/outlier_analysis_iqr_only',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Run analysis
    analyzer = P90TrimmingAnalyzer(output_dir=args.output)
    analyzer.run_p90_analysis()


if __name__ == "__main__":
    main() 