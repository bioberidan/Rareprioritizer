#!/usr/bin/env python3
"""
Orpha Prevalence Statistics

This script generates comprehensive statistics and visualizations for curated orpha prevalence data.

Usage:
    python orpha_prevalence_stats.py --input-dir path/to/curated/data 
                                    --output path/to/output/dir
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Import existing clients
from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient


class OrphaPrevalenceStatsGenerator:
    """
    Generates comprehensive statistics and visualizations for curated orpha prevalence data.
    """
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Initialize ProcessedPrevalenceClient for additional data
        self.prevalence_client = ProcessedPrevalenceClient()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Configure matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

    def load_curated_data(self) -> Dict[str, Any]:
        """Load curated prevalence data and processing summary"""
        data = {}
        
        # Load disease2prevalence mapping
        prevalence_file = self.input_dir / "disease2prevalence.json"
        if prevalence_file.exists():
            with open(prevalence_file, 'r', encoding='utf-8') as f:
                data['disease2prevalence'] = json.load(f)
            self.logger.info(f"Loaded {len(data['disease2prevalence'])} disease-prevalence mappings")
        
        # Load processing summary
        summary_file = self.input_dir / "orpha_prevalence_curation_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                data['processing_summary'] = json.load(f)
            self.logger.info("Loaded processing summary")
        
        return data

    def generate_basic_statistics(self, curated_data: Dict) -> Dict:
        """Generate basic statistics about the curated data"""
        disease2prevalence = curated_data.get('disease2prevalence', {})
        processing_summary = curated_data.get('processing_summary', {})
        
        stats = {
            'data_overview': {
                'total_diseases': len(disease2prevalence),
                'diseases_with_known_prevalence': len([v for v in disease2prevalence.values() if v != "Unknown"]),
                'diseases_with_unknown_prevalence': len([v for v in disease2prevalence.values() if v == "Unknown"]),
                'coverage_percentage': (len([v for v in disease2prevalence.values() if v != "Unknown"]) / len(disease2prevalence)) * 100 if disease2prevalence else 0
            },
            'prevalence_class_distribution': {},
            'selection_method_analysis': processing_summary.get('selection_method_distribution', {}),
            'processing_metadata': processing_summary.get('processing_metadata', {}),
            'generation_timestamp': datetime.now().isoformat()
        }
        
        # Calculate prevalence class distribution
        for prevalence_class in disease2prevalence.values():
            if prevalence_class != "Unknown":
                stats['prevalence_class_distribution'][prevalence_class] = \
                    stats['prevalence_class_distribution'].get(prevalence_class, 0) + 1
        
        return stats

    def generate_advanced_statistics(self, curated_data: Dict) -> Dict:
        """Generate advanced statistics using processed prevalence client"""
        disease2prevalence = curated_data.get('disease2prevalence', {})
        advanced_stats = {}
        
        try:
            # Get processed prevalence data for subset
            processed_data = {}
            for orpha_code in disease2prevalence.keys():
                if orpha_code != "Unknown":
                    disease_data = self.prevalence_client.get_disease_prevalence(orpha_code)
                    if disease_data:
                        processed_data[orpha_code] = disease_data
            
            # Analyze reliability scores
            reliability_scores = []
            geographic_distribution = {}
            prevalence_types = {}
            
            for orpha_code, disease_data in processed_data.items():
                most_reliable = disease_data.get('most_reliable_prevalence')
                if most_reliable:
                    reliability_score = most_reliable.get('reliability_score', 0)
                    reliability_scores.append(reliability_score)
                    
                    geographic_area = most_reliable.get('geographic_area', 'Unknown')
                    geographic_distribution[geographic_area] = geographic_distribution.get(geographic_area, 0) + 1
                    
                    prevalence_type = most_reliable.get('prevalence_type', 'Unknown')
                    prevalence_types[prevalence_type] = prevalence_types.get(prevalence_type, 0) + 1
            
            advanced_stats = {
                'reliability_analysis': {
                    'mean_reliability_score': np.mean(reliability_scores) if reliability_scores else 0,
                    'median_reliability_score': np.median(reliability_scores) if reliability_scores else 0,
                    'std_reliability_score': np.std(reliability_scores) if reliability_scores else 0,
                    'min_reliability_score': min(reliability_scores) if reliability_scores else 0,
                    'max_reliability_score': max(reliability_scores) if reliability_scores else 0
                },
                'geographic_distribution': geographic_distribution,
                'prevalence_type_distribution': prevalence_types,
                'data_quality_metrics': {
                    'diseases_with_processed_data': len(processed_data),
                    'diseases_without_processed_data': len(disease2prevalence) - len(processed_data),
                    'processed_data_coverage': (len(processed_data) / len(disease2prevalence)) * 100 if disease2prevalence else 0
                }
            }
            
        except Exception as e:
            self.logger.warning(f"Error generating advanced statistics: {e}")
            advanced_stats = {'error': str(e)}
        
        return advanced_stats

    def create_visualizations(self, basic_stats: Dict, advanced_stats: Dict) -> List[str]:
        """Create comprehensive visualizations"""
        created_plots = []
        
        try:
            # 1. Prevalence Class Distribution
            if basic_stats.get('prevalence_class_distribution'):
                fig, ax = plt.subplots(figsize=(12, 8))
                
                classes = list(basic_stats['prevalence_class_distribution'].keys())
                counts = list(basic_stats['prevalence_class_distribution'].values())
                
                bars = ax.bar(classes, counts, color=sns.color_palette("husl", len(classes)))
                ax.set_title('Prevalence Class Distribution', fontsize=16, fontweight='bold')
                ax.set_xlabel('Prevalence Class', fontsize=12)
                ax.set_ylabel('Number of Diseases', fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels on bars
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{count}', ha='center', va='bottom')
                
                plt.tight_layout()
                plot_path = self.output_dir / "prevalence_class_distribution.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                created_plots.append(str(plot_path))
            
            # 2. Coverage Analysis
            coverage_data = basic_stats.get('data_overview', {})
            if coverage_data:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                # Coverage pie chart
                labels = ['With Prevalence', 'Unknown']
                sizes = [coverage_data.get('diseases_with_known_prevalence', 0),
                        coverage_data.get('diseases_with_unknown_prevalence', 0)]
                colors = ['#2ecc71', '#e74c3c']
                
                ax1.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
                ax1.set_title('Prevalence Data Coverage', fontsize=14, fontweight='bold')
                
                # Selection method analysis
                selection_methods = basic_stats.get('selection_method_analysis', {})
                if selection_methods:
                    methods = list(selection_methods.keys())
                    counts = list(selection_methods.values())
                    
                    bars = ax2.bar(methods, counts, color=sns.color_palette("Set2", len(methods)))
                    ax2.set_title('Selection Method Distribution', fontsize=14, fontweight='bold')
                    ax2.set_xlabel('Selection Method', fontsize=12)
                    ax2.set_ylabel('Number of Diseases', fontsize=12)
                    ax2.tick_params(axis='x', rotation=45)
                    
                    # Add value labels
                    for bar, count in zip(bars, counts):
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height,
                               f'{count}', ha='center', va='bottom')
                
                plt.tight_layout()
                plot_path = self.output_dir / "coverage_analysis.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                created_plots.append(str(plot_path))
            
            # 3. Geographic Distribution (if available)
            geographic_dist = advanced_stats.get('geographic_distribution', {})
            if geographic_dist:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                areas = list(geographic_dist.keys())
                counts = list(geographic_dist.values())
                
                bars = ax.bar(areas, counts, color=sns.color_palette("viridis", len(areas)))
                ax.set_title('Geographic Distribution of Prevalence Data', fontsize=14, fontweight='bold')
                ax.set_xlabel('Geographic Area', fontsize=12)
                ax.set_ylabel('Number of Diseases', fontsize=12)
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for bar, count in zip(bars, counts):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{count}', ha='center', va='bottom')
                
                plt.tight_layout()
                plot_path = self.output_dir / "geographic_distribution.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                created_plots.append(str(plot_path))
            
            # 4. Reliability Score Analysis
            reliability_analysis = advanced_stats.get('reliability_analysis', {})
            if reliability_analysis and reliability_analysis.get('mean_reliability_score', 0) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                metrics = ['Mean', 'Median', 'Min', 'Max']
                values = [
                    reliability_analysis.get('mean_reliability_score', 0),
                    reliability_analysis.get('median_reliability_score', 0),
                    reliability_analysis.get('min_reliability_score', 0),
                    reliability_analysis.get('max_reliability_score', 0)
                ]
                
                bars = ax.bar(metrics, values, color=sns.color_palette("plasma", len(metrics)))
                ax.set_title('Reliability Score Statistics', fontsize=14, fontweight='bold')
                ax.set_xlabel('Metric', fontsize=12)
                ax.set_ylabel('Reliability Score', fontsize=12)
                ax.set_ylim(0, 10)
                
                # Add value labels
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{value:.2f}', ha='center', va='bottom')
                
                plt.tight_layout()
                plot_path = self.output_dir / "reliability_analysis.png"
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                created_plots.append(str(plot_path))
            
            self.logger.info(f"Created {len(created_plots)} visualizations")
            
        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")
        
        return created_plots

    def generate_comprehensive_report(self, basic_stats: Dict, advanced_stats: Dict, 
                                    created_plots: List[str]) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            'report_metadata': {
                'generation_timestamp': datetime.now().isoformat(),
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'created_visualizations': created_plots
            },
            'basic_statistics': basic_stats,
            'advanced_statistics': advanced_stats,
            'key_insights': self._generate_key_insights(basic_stats, advanced_stats),
            'recommendations': self._generate_recommendations(basic_stats, advanced_stats)
        }
        
        return report

    def _generate_key_insights(self, basic_stats: Dict, advanced_stats: Dict) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []
        
        # Coverage insights
        coverage = basic_stats.get('data_overview', {}).get('coverage_percentage', 0)
        insights.append(f"Data coverage: {coverage:.1f}% of diseases have known prevalence classes")
        
        # Most common prevalence class
        prevalence_dist = basic_stats.get('prevalence_class_distribution', {})
        if prevalence_dist:
            most_common = max(prevalence_dist.items(), key=lambda x: x[1])
            insights.append(f"Most common prevalence class: '{most_common[0]}' ({most_common[1]} diseases)")
        
        # Selection method insights
        selection_methods = basic_stats.get('selection_method_analysis', {})
        if selection_methods:
            point_prevalence = selection_methods.get('point_prevalence', 0)
            total_with_data = sum(v for k, v in selection_methods.items() if k != 'no_data')
            if total_with_data > 0:
                point_prevalence_pct = (point_prevalence / total_with_data) * 100
                insights.append(f"Point prevalence data available for {point_prevalence_pct:.1f}% of diseases with data")
        
        # Reliability insights
        reliability = advanced_stats.get('reliability_analysis', {})
        if reliability and reliability.get('mean_reliability_score', 0) > 0:
            mean_score = reliability.get('mean_reliability_score', 0)
            insights.append(f"Average reliability score: {mean_score:.2f} out of 10")
        
        return insights

    def _generate_recommendations(self, basic_stats: Dict, advanced_stats: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        coverage = basic_stats.get('data_overview', {}).get('coverage_percentage', 0)
        if coverage < 80:
            recommendations.append("Consider expanding data collection to improve coverage below 80%")
        
        selection_methods = basic_stats.get('selection_method_analysis', {})
        fallback_count = selection_methods.get('worldwide_fallback', 0) + selection_methods.get('regional_fallback', 0)
        if fallback_count > 0:
            recommendations.append(f"Review {fallback_count} diseases using fallback methods for potential point prevalence data")
        
        reliability = advanced_stats.get('reliability_analysis', {})
        if reliability and reliability.get('mean_reliability_score', 0) < 7:
            recommendations.append("Consider reviewing data quality - average reliability score is below 7")
        
        return recommendations

    def save_outputs(self, comprehensive_report: Dict) -> None:
        """Save all outputs to files"""
        # Save comprehensive statistics
        stats_file = self.output_dir / "orpha_prevalence_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved comprehensive statistics to {stats_file}")
        
        # Save analysis summary
        summary = {
            'generation_timestamp': comprehensive_report['report_metadata']['generation_timestamp'],
            'data_overview': comprehensive_report['basic_statistics']['data_overview'],
            'key_insights': comprehensive_report['key_insights'],
            'recommendations': comprehensive_report['recommendations']
        }
        
        summary_file = self.output_dir / "analysis_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved analysis summary to {summary_file}")

    def run(self) -> None:
        """Run the complete statistics generation process"""
        try:
            self.logger.info("Starting orpha prevalence statistics generation")
            
            # Load curated data
            curated_data = self.load_curated_data()
            
            # Generate basic statistics
            basic_stats = self.generate_basic_statistics(curated_data)
            
            # Generate advanced statistics
            advanced_stats = self.generate_advanced_statistics(curated_data)
            
            # Create visualizations
            created_plots = self.create_visualizations(basic_stats, advanced_stats)
            
            # Generate comprehensive report
            comprehensive_report = self.generate_comprehensive_report(basic_stats, advanced_stats, created_plots)
            
            # Save outputs
            self.save_outputs(comprehensive_report)
            
            self.logger.info("Statistics generation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during statistics generation: {e}")
            raise


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Generate statistics for curated orpha prevalence data")
    
    parser.add_argument(
        '--input-dir',
        required=True,
        help="Directory containing curated prevalence data files"
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help="Output directory for statistics and visualizations"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Create and run statistics generator
    stats_generator = OrphaPrevalenceStatsGenerator(
        input_dir=args.input_dir,
        output_dir=args.output
    )
    
    stats_generator.run()


if __name__ == "__main__":
    main() 