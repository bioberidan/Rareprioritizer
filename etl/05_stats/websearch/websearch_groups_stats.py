#!/usr/bin/env python3
"""
Websearch Groups Statistics and Analysis

This script generates comprehensive statistics and visualizations for websearch groups data.
IMPORTANT: Uses complete datasets - NO data slicing allowed.

Input: data/04_curated/websearch/groups/
Output: results/etl/subset_of_disease_instances/metabolic/websearch/groups/

Analysis includes:
- Group distribution analysis (full datasets only)
- Top 15 groups by disease coverage
- Group type analysis (U-format vs descriptive vs PI-based)
- Source type analysis
- Disease coverage analysis
- Source validation report
- Summary statistics
"""

import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.datastore.websearch.curated_websearch_groups_client import CuratedWebsearchGroupsClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
plt.style.use('default')
sns.set_palette("husl")


class WebsearchGroupsStatsAnalyzer:
    """
    Comprehensive statistics and analysis for websearch groups data
    
    CRITICAL: All analyses use complete datasets - NO data slicing allowed
    """
    
    def __init__(self, 
                 input_dir: str = "data/04_curated/websearch/groups",
                 output_dir: str = "results/etl/subset_of_disease_instances/metabolic/websearch/groups"):
        """
        Initialize the websearch groups statistics analyzer
        
        Args:
            input_dir: Directory containing curated websearch groups data
            output_dir: Directory for output statistics and visualizations
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize client for data access
        self.client = CuratedWebsearchGroupsClient(str(self.input_dir))
        
        logger.info(f"Initialized WebsearchGroupsStatsAnalyzer")
        logger.info(f"Input: {self.input_dir}")
        logger.info(f"Output: {self.output_dir}")
    
    def _calculate_iqr_outliers(self, values: List[int]) -> Tuple[List[int], float, float]:
        """
        Calculate IQR-based outliers on COMPLETE dataset
        
        Args:
            values: Complete list of values (NO slicing allowed)
            
        Returns:
            Tuple of (outlier_indices, lower_bound, upper_bound)
        """
        if not values:
            return [], 0, 0
        
        # Use COMPLETE dataset - no slicing
        values_array = np.array(values)
        
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Find outliers in COMPLETE dataset
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        logger.info(f"IQR outlier analysis on COMPLETE data: {len(outlier_indices)} outliers found")
        return outlier_indices, lower_bound, upper_bound
    
    def analyze_group_distribution(self) -> Dict[str, Any]:
        """
        Analyze the distribution of groups per disease
        
        Returns:
            Dictionary containing distribution analysis
        """
        logger.info("Analyzing group distribution...")
        
        # Get disease-group mappings
        diseases = self.client.get_diseases_with_groups()
        
        # Calculate groups per disease
        groups_per_disease = []
        for disease in diseases:
            groups = self.client.get_groups_for_disease(disease)
            groups_per_disease.append(len(groups))
        
        # Include diseases without groups
        all_disease_data = self.client._load_disease_group_data()
        diseases_without_groups = len([d for d, g in all_disease_data.items() if not g])
        
        # Add zeros for diseases without groups
        groups_per_disease.extend([0] * diseases_without_groups)
        
        # Calculate statistics
        analysis = {
            'total_diseases': len(all_disease_data),
            'diseases_with_groups': len(diseases),
            'diseases_without_groups': diseases_without_groups,
            'coverage_percentage': (len(diseases) / len(all_disease_data) * 100) if all_disease_data else 0,
            'groups_per_disease_distribution': {
                'values': groups_per_disease,
                'mean': np.mean(groups_per_disease) if groups_per_disease else 0,
                'median': np.median(groups_per_disease) if groups_per_disease else 0,
                'std': np.std(groups_per_disease) if groups_per_disease else 0,
                'min': min(groups_per_disease) if groups_per_disease else 0,
                'max': max(groups_per_disease) if groups_per_disease else 0
            }
        }
        
        # Count distribution
        count_distribution = Counter(groups_per_disease)
        analysis['count_distribution'] = dict(count_distribution)
        
        # IQR outlier analysis on groups per disease
        outlier_indices, lower_bound, upper_bound = self._calculate_iqr_outliers(groups_per_disease)
        
        # Get outlier diseases
        all_disease_codes = list(all_disease_data.keys())
        outlier_diseases = []
        for idx in outlier_indices:
            if idx < len(all_disease_codes):
                orpha_code = all_disease_codes[idx]
                group_count = groups_per_disease[idx]
                groups = all_disease_data[orpha_code] if group_count > 0 else []
                outlier_diseases.append({
                    "orpha_code": orpha_code,
                    "group_count": group_count,
                    "groups": groups
                })
        
        analysis['groups_per_disease_outliers'] = {
            "outlier_count": len(outlier_diseases),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_diseases": outlier_diseases
        }
        
        logger.info(f"Group distribution analysis completed: {analysis['coverage_percentage']:.1f}% coverage")
        return analysis
    
    def get_top_groups_by_activity(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get top groups by number of diseases they work on
        
        Args:
            limit: Number of top groups to return
            
        Returns:
            List of top groups with their statistics
        """
        logger.info(f"Getting top {limit} groups by activity...")
        
        top_groups = self.client.get_most_active_groups(limit)
        
        # Add source information for each group
        for group_info in top_groups:
            group_name = group_info['group_name']
            sources = self.client.get_sources_for_group(group_name)
            group_info['source_count'] = len(sources)
            group_info['sources'] = sources
        
        logger.info(f"Retrieved top {len(top_groups)} groups")
        return top_groups
    
    def analyze_source_types(self) -> Dict[str, Any]:
        """
        Analyze the distribution of source types
        
        Returns:
            Dictionary containing source type analysis
        """
        logger.info("Analyzing source types...")
        
        source_stats = self.client.get_source_statistics()
        
        # Get detailed source analysis
        all_groups = self.client.get_all_groups()
        source_details = []
        
        for group in all_groups:
            sources = self.client.get_sources_for_group(group)
            for source in sources:
                url = source.get('url', '').lower()
                label = source.get('label', '')
                
                if 'pubmed' in url or 'ncbi.nlm.nih.gov' in url:
                    source_type = 'pubmed'
                elif 'ciberer' in url:
                    source_type = 'ciberer_website'
                else:
                    source_type = 'other_websites'
                
                source_details.append({
                    'group': group,
                    'type': source_type,
                    'url': source.get('url'),
                    'label': label
                })
        
        analysis = {
            'source_statistics': source_stats,
            'source_details': source_details,
            'type_distribution': source_stats['source_types']
        }
        
        # IQR outlier analysis on sources per group
        all_groups = self.client.get_all_groups()
        sources_per_group = []
        for group in all_groups:
            sources = self.client.get_sources_for_group(group)
            sources_per_group.append(len(sources))
        
        outlier_indices, lower_bound, upper_bound = self._calculate_iqr_outliers(sources_per_group)
        
        # Get outlier groups
        outlier_groups = []
        for idx in outlier_indices:
            if idx < len(all_groups):
                group_name = all_groups[idx]
                source_count = sources_per_group[idx]
                sources = self.client.get_sources_for_group(group_name)
                outlier_groups.append({
                    "group_name": group_name,
                    "source_count": source_count,
                    "sources": sources
                })
        
        analysis['sources_per_group_outliers'] = {
            "outlier_count": len(outlier_groups),
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "outlier_groups": outlier_groups
        }
        
        logger.info(f"Source type analysis completed: {len(source_details)} total sources")
        return analysis
    
    def analyze_group_types(self) -> Dict[str, Any]:
        """
        Analyze the distribution of group types (U-format, descriptive, PI-based)
        
        Returns:
            Dictionary containing group type analysis
        """
        logger.info("Analyzing group types...")
        
        u_format_groups = self.client.get_groups_by_type('u_format')
        descriptive_groups = self.client.get_groups_by_type('descriptive')
        pi_based_groups = self.client.get_groups_by_type('pi_based')
        
        analysis = {
            'u_format': {
                'count': len(u_format_groups),
                'groups': u_format_groups
            },
            'descriptive': {
                'count': len(descriptive_groups),
                'groups': descriptive_groups
            },
            'pi_based': {
                'count': len(pi_based_groups),
                'groups': pi_based_groups
            },
            'total_groups': len(u_format_groups) + len(descriptive_groups) + len(pi_based_groups)
        }
        
        # Calculate percentages
        total = analysis['total_groups']
        if total > 0:
            analysis['u_format']['percentage'] = (len(u_format_groups) / total) * 100
            analysis['descriptive']['percentage'] = (len(descriptive_groups) / total) * 100
            analysis['pi_based']['percentage'] = (len(pi_based_groups) / total) * 100
        
        logger.info(f"Group type analysis completed: {total} total groups")
        return analysis
    
    def analyze_disease_coverage(self) -> Dict[str, Any]:
        """
        Analyze disease coverage patterns
        
        Returns:
            Dictionary containing coverage analysis
        """
        logger.info("Analyzing disease coverage...")
        
        summary_stats = self.client.get_summary_statistics()
        
        # Additional coverage metrics
        diseases_with_groups = self.client.get_diseases_with_groups()
        all_groups = self.client.get_all_groups()
        
        # Calculate diseases per group distribution
        diseases_per_group = []
        for group in all_groups:
            diseases = self.client.get_diseases_for_group(group)
            diseases_per_group.append(len(diseases))
        
        analysis = {
            'summary_statistics': summary_stats,
            'diseases_per_group_distribution': {
                'values': diseases_per_group,
                'mean': np.mean(diseases_per_group) if diseases_per_group else 0,
                'median': np.median(diseases_per_group) if diseases_per_group else 0,
                'std': np.std(diseases_per_group) if diseases_per_group else 0
            },
            'coverage_metrics': {
                'total_diseases': summary_stats['total_diseases'],
                'diseases_with_groups': summary_stats['diseases_with_groups'],
                'coverage_percentage': summary_stats['coverage_percentage']
            }
        }
        
        logger.info(f"Disease coverage analysis completed")
        return analysis
    
    def validate_source_accessibility(self) -> Dict[str, Any]:
        """
        Validate source accessibility and generate validation report
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Validating source accessibility...")
        
        validation_results = self.client.validate_sources_accessibility()
        
        # Additional validation metrics
        source_stats = self.client.get_source_statistics()
        
        analysis = {
            'validation_results': validation_results,
            'source_statistics': source_stats,
            'quality_score': validation_results['valid_format_percentage']
        }
        
        logger.info(f"Source validation completed: {validation_results['valid_format_percentage']:.1f}% valid format")
        return analysis
    
    def generate_visualizations(self) -> None:
        """Generate all visualizations for the analysis"""
        logger.info("Generating visualizations...")
        
        # 1. Group distribution analysis
        self._plot_group_distribution()
        
        # 2. Top groups by diseases
        self._plot_top_groups_by_diseases()
        
        # 3. Source type analysis
        self._plot_source_type_analysis()
        
        # 4. Group type distribution
        self._plot_group_type_distribution()
        
        # 5. Disease coverage analysis
        self._plot_disease_coverage_analysis()
        
        # 6. Source validation report
        self._plot_source_validation_report()
        
        # 7. Summary dashboard
        self._plot_summary_dashboard()
        
        # 8. IQR outlier analysis
        self._plot_iqr_outlier_analysis()
        
        logger.info("All visualizations generated")
    
    def _plot_group_distribution(self) -> None:
        """Plot group distribution analysis"""
        distribution_data = self.analyze_group_distribution()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Groups per disease histogram
        groups_per_disease = distribution_data['groups_per_disease_distribution']['values']
        ax1.hist(groups_per_disease, bins=range(max(groups_per_disease) + 2), alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Number of Groups per Disease')
        ax1.set_ylabel('Number of Diseases')
        ax1.set_title('Distribution of Groups per Disease')
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        mean_val = distribution_data['groups_per_disease_distribution']['mean']
        ax1.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
        ax1.legend()
        
        # Plot 2: Coverage pie chart
        coverage_data = [
            distribution_data['diseases_with_groups'],
            distribution_data['diseases_without_groups']
        ]
        labels = ['With Groups', 'Without Groups']
        colors = ['#2E8B57', '#CD5C5C']
        
        ax2.pie(coverage_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Disease Coverage by Research Groups')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'group_distribution_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_top_groups_by_diseases(self) -> None:
        """Plot top groups by number of diseases"""
        top_groups = self.get_top_groups_by_activity(15)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        group_names = [g['group_name'] for g in top_groups]
        disease_counts = [g['disease_count'] for g in top_groups]
        
        # Truncate long group names for display
        display_names = [name[:30] + '...' if len(name) > 30 else name for name in group_names]
        
        bars = ax.barh(range(len(display_names)), disease_counts, color='skyblue', edgecolor='navy')
        ax.set_yticks(range(len(display_names)))
        ax.set_yticklabels(display_names)
        ax.set_xlabel('Number of Diseases')
        ax.set_title('Top Research Groups by Disease Coverage')
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'top_groups_by_diseases.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_source_type_analysis(self) -> None:
        """Plot source type distribution"""
        source_analysis = self.analyze_source_types()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Source type pie chart
        type_dist = source_analysis['type_distribution']
        labels = list(type_dist.keys())
        sizes = list(type_dist.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Distribution of Source Types')
        
        # Plot 2: Sources per group histogram
        source_stats = source_analysis['source_statistics']
        sources_per_group = list(source_stats['sources_per_group'].values())
        
        ax2.hist(sources_per_group, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_xlabel('Number of Sources per Group')
        ax2.set_ylabel('Number of Groups')
        ax2.set_title('Distribution of Sources per Group')
        ax2.grid(True, alpha=0.3)
        
        # Add mean line
        mean_sources = np.mean(sources_per_group)
        ax2.axvline(mean_sources, color='red', linestyle='--', label=f'Mean: {mean_sources:.2f}')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'source_type_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_group_type_distribution(self) -> None:
        """Plot group type distribution"""
        group_types = self.analyze_group_types()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Group type pie chart
        type_counts = [
            group_types['u_format']['count'],
            group_types['descriptive']['count'],
            group_types['pi_based']['count']
        ]
        labels = ['U-format', 'Descriptive', 'PI-based']
        colors = ['#FFB6C1', '#98FB98', '#87CEEB']
        
        ax1.pie(type_counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Distribution of Group Types')
        
        # Plot 2: Group type bar chart
        ax2.bar(labels, type_counts, color=colors, edgecolor='black')
        ax2.set_ylabel('Number of Groups')
        ax2.set_title('Group Types Count')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, count in enumerate(type_counts):
            ax2.text(i, count + 0.1, str(count), ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'group_type_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_disease_coverage_analysis(self) -> None:
        """Plot disease coverage analysis"""
        coverage_data = self.analyze_disease_coverage()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Coverage percentage
        coverage_pct = coverage_data['coverage_metrics']['coverage_percentage']
        uncovered_pct = 100 - coverage_pct
        
        labels = ['Covered', 'Not Covered']
        sizes = [coverage_pct, uncovered_pct]
        colors = ['#32CD32', '#FF6347']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Disease Coverage by Research Groups')
        
        # Plot 2: Diseases per group distribution
        diseases_per_group = coverage_data['diseases_per_group_distribution']['values']
        
        ax2.hist(diseases_per_group, bins=20, alpha=0.7, color='orange', edgecolor='black')
        ax2.set_xlabel('Number of Diseases per Group')
        ax2.set_ylabel('Number of Groups')
        ax2.set_title('Distribution of Diseases per Group')
        ax2.grid(True, alpha=0.3)
        
        # Add mean line
        mean_diseases = coverage_data['diseases_per_group_distribution']['mean']
        ax2.axvline(mean_diseases, color='red', linestyle='--', label=f'Mean: {mean_diseases:.2f}')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'disease_coverage_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_source_validation_report(self) -> None:
        """Plot source validation report"""
        validation_data = self.validate_source_accessibility()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Plot 1: Source validation status
        validation = validation_data['validation_results']
        valid_sources = validation['valid_format']
        invalid_sources = validation['invalid_sources']
        
        labels = ['Valid Format', 'Invalid Format']
        sizes = [valid_sources, invalid_sources]
        colors = ['#90EE90', '#F08080']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Source Validation Status')
        
        # Plot 2: Validation metrics bar chart
        metrics = ['Total Sources', 'Valid Format', 'Missing URL', 'Missing Label']
        values = [
            validation['total_sources'],
            validation['valid_format'],
            validation['missing_url'],
            validation['missing_label']
        ]
        
        bars = ax2.bar(metrics, values, color=['skyblue', 'lightgreen', 'lightcoral', 'lightyellow'], 
                      edgecolor='black')
        ax2.set_ylabel('Count')
        ax2.set_title('Source Validation Metrics')
        ax2.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    str(value), ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'source_validation_report.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_summary_dashboard(self) -> None:
        """Plot comprehensive summary dashboard"""
        # Get all analysis data
        distribution_data = self.analyze_group_distribution()
        group_types = self.analyze_group_types()
        source_analysis = self.analyze_source_types()
        coverage_data = self.analyze_disease_coverage()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Top left: Coverage overview
        coverage_pct = coverage_data['coverage_metrics']['coverage_percentage']
        uncovered_pct = 100 - coverage_pct
        ax1.pie([coverage_pct, uncovered_pct], labels=['Covered', 'Not Covered'], 
               colors=['#32CD32', '#FF6347'], autopct='%1.1f%%', startangle=90)
        ax1.set_title('Disease Coverage Overview')
        
        # Top right: Group types
        type_counts = [
            group_types['u_format']['count'],
            group_types['descriptive']['count'],
            group_types['pi_based']['count']
        ]
        labels = ['U-format', 'Descriptive', 'PI-based']
        ax2.pie(type_counts, labels=labels, colors=['#FFB6C1', '#98FB98', '#87CEEB'], 
               autopct='%1.1f%%', startangle=90)
        ax2.set_title('Group Type Distribution')
        
        # Bottom left: Source types
        type_dist = source_analysis['type_distribution']
        ax3.pie(list(type_dist.values()), labels=list(type_dist.keys()), 
               colors=['#FF6B6B', '#4ECDC4', '#45B7D1'], autopct='%1.1f%%', startangle=90)
        ax3.set_title('Source Type Distribution')
        
        # Bottom right: Key metrics
        ax4.axis('off')
        summary_stats = coverage_data['summary_statistics']
        
        metrics_text = f"""
        Key Metrics:
        
        Total Diseases: {summary_stats['total_diseases']}
        Diseases with Groups: {summary_stats['diseases_with_groups']}
        Coverage: {summary_stats['coverage_percentage']:.1f}%
        Total Groups: {summary_stats['total_groups']}
        
        Avg Groups per Disease: {summary_stats['avg_groups_per_disease']:.2f}
        Avg Diseases per Group: {summary_stats['avg_diseases_per_group']:.2f}
        
        Total Sources: {source_analysis['source_statistics']['total_sources']}
        Avg Sources per Group: {source_analysis['source_statistics']['avg_sources_per_group']:.2f}
        """
        
        ax4.text(0.1, 0.9, metrics_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax4.set_title('Summary Statistics')
        
        plt.suptitle('Websearch Groups Analysis Dashboard', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'summary_dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_iqr_outlier_analysis(self) -> None:
        """Plot IQR outlier analysis for groups per disease and sources per group"""
        distribution_data = self.analyze_group_distribution()
        source_analysis = self.analyze_source_types()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot 1: Groups per disease outlier analysis
        groups_per_disease = distribution_data['groups_per_disease_distribution']['values']
        outlier_info = distribution_data.get('groups_per_disease_outliers', {})
        
        if groups_per_disease and outlier_info:
            # Box plot showing outliers
            box_plot = ax1.boxplot(groups_per_disease, vert=True, patch_artist=True)
            box_plot['boxes'][0].set_facecolor('lightblue')
            
            ax1.set_ylabel('Number of Groups per Disease')
            ax1.set_title(f'Groups per Disease\n({outlier_info.get("outlier_count", 0)} outliers)')
            ax1.grid(True, alpha=0.3)
            
            # Add outlier threshold lines
            if 'lower_bound' in outlier_info and 'upper_bound' in outlier_info:
                ax1.axhline(y=outlier_info['upper_bound'], color='red', linestyle='--', 
                           label=f'Upper: {outlier_info["upper_bound"]:.1f}')
                if outlier_info['lower_bound'] > 0:
                    ax1.axhline(y=outlier_info['lower_bound'], color='red', linestyle='--',
                               label=f'Lower: {outlier_info["lower_bound"]:.1f}')
                ax1.legend(fontsize=10)
        else:
            ax1.text(0.5, 0.5, 'No Data', transform=ax1.transAxes, 
                   fontsize=12, ha='center', va='center')
            ax1.set_title('Groups per Disease\n(No data)')
        
        # Plot 2: Sources per group outlier analysis
        all_groups = self.client.get_all_groups()
        sources_per_group = []
        for group in all_groups:
            sources = self.client.get_sources_for_group(group)
            sources_per_group.append(len(sources))
        
        outlier_info_sources = source_analysis.get('sources_per_group_outliers', {})
        
        if sources_per_group and outlier_info_sources:
            # Box plot showing outliers
            box_plot = ax2.boxplot(sources_per_group, vert=True, patch_artist=True)
            box_plot['boxes'][0].set_facecolor('lightgreen')
            
            ax2.set_ylabel('Number of Sources per Group')
            ax2.set_title(f'Sources per Group\n({outlier_info_sources.get("outlier_count", 0)} outliers)')
            ax2.grid(True, alpha=0.3)
            
            # Add outlier threshold lines
            if 'lower_bound' in outlier_info_sources and 'upper_bound' in outlier_info_sources:
                ax2.axhline(y=outlier_info_sources['upper_bound'], color='red', linestyle='--', 
                           label=f'Upper: {outlier_info_sources["upper_bound"]:.1f}')
                if outlier_info_sources['lower_bound'] > 0:
                    ax2.axhline(y=outlier_info_sources['lower_bound'], color='red', linestyle='--',
                               label=f'Lower: {outlier_info_sources["lower_bound"]:.1f}')
                ax2.legend(fontsize=10)
        else:
            ax2.text(0.5, 0.5, 'No Data', transform=ax2.transAxes, 
                   fontsize=12, ha='center', va='center')
            ax2.set_title('Sources per Group\n(No data)')
        
        plt.suptitle('IQR Outlier Analysis - Websearch Groups', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'outlier_analysis_iqr.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_statistics_json(self) -> None:
        """Generate comprehensive statistics JSON file"""
        logger.info("Generating statistics JSON...")
        
        # Collect all analysis data
        distribution_data = self.analyze_group_distribution()
        top_groups = self.get_top_groups_by_activity(15)
        source_analysis = self.analyze_source_types()
        group_types = self.analyze_group_types()
        coverage_data = self.analyze_disease_coverage()
        validation_data = self.validate_source_accessibility()
        
        statistics = {
            'analysis_metadata': {
                'generated_timestamp': datetime.now().isoformat(),
                'analysis_type': 'complete_dataset_analysis',
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir)
            },
            'basic_statistics': {
                'total_diseases_searched': distribution_data['total_diseases'],
                'diseases_with_groups': distribution_data['diseases_with_groups'],
                'diseases_without_groups': distribution_data['diseases_without_groups'],
                'total_unique_groups': group_types['total_groups'],
                'total_sources': source_analysis['source_statistics']['total_sources'],
                'avg_groups_per_disease': coverage_data['summary_statistics']['avg_groups_per_disease'],
                'avg_sources_per_group': source_analysis['source_statistics']['avg_sources_per_group']
            },
            'group_analysis': {
                'most_active_groups': top_groups[:10],
                'group_type_distribution': {
                    'u_format': group_types['u_format']['count'],
                    'descriptive': group_types['descriptive']['count'],
                    'pi_based': group_types['pi_based']['count']
                },
                'group_distribution_stats': distribution_data['groups_per_disease_distribution']
            },
            'source_analysis': {
                'source_type_distribution': source_analysis['type_distribution'],
                'source_validation': validation_data['validation_results'],
                'source_quality_score': validation_data['quality_score']
            },
            'coverage_analysis': {
                'coverage_percentage': coverage_data['coverage_metrics']['coverage_percentage'],
                'diseases_per_group_stats': coverage_data['diseases_per_group_distribution']
            },
            'outlier_analysis': {
                'groups_per_disease_outliers': distribution_data.get('groups_per_disease_outliers', {}),
                'sources_per_group_outliers': source_analysis.get('sources_per_group_outliers', {})
            }
        }
        
        # Save statistics JSON
        output_file = self.output_dir / "websearch_groups_statistics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated statistics JSON: {output_file}")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run complete analysis on FULL datasets (NO slicing)
        
        Returns:
            Complete analysis results
        """
        logger.info("Starting COMPLETE websearch groups analysis...")
        logger.info("CRITICAL: Using full datasets - NO data slicing applied")
        
        # Generate all visualizations
        self.generate_visualizations()
        
        # Generate statistics JSON
        self.generate_statistics_json()
        
        # Collect summary results
        summary_stats = self.client.get_summary_statistics()
        
        logger.info("COMPLETE websearch groups analysis finished successfully!")
        logger.info(f"All outputs saved to: {self.output_dir}")
        logger.info("VERIFICATION: All analyses used complete datasets without slicing")
        
        return summary_stats


def main():
    """
    Main entry point for websearch groups statistics
    """
    parser = argparse.ArgumentParser(description="Generate websearch groups statistics and analysis")
    parser.add_argument("--input-dir", default="data/04_curated/websearch/groups",
                       help="Input directory with curated websearch groups data")
    parser.add_argument("--output-dir", default="results/etl/subset_of_disease_instances/metabolic/websearch/groups",
                       help="Output directory for statistics and visualizations")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = WebsearchGroupsStatsAnalyzer(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Run complete analysis (NO data slicing)
        results = analyzer.run_complete_analysis()
        
        # Print summary
        print("\n" + "="*80)
        print("WEBSEARCH GROUPS STATISTICS SUMMARY")
        print("="*80)
        print(f"Analysis Type: COMPLETE DATASET (No slicing applied)")
        print(f"Output Directory: {args.output_dir}")
        print(f"Total Diseases: {results['total_diseases']}")
        print(f"Diseases with Groups: {results['diseases_with_groups']}")
        print(f"Coverage: {results['coverage_percentage']:.1f}%")
        print(f"Total Groups: {results['total_groups']}")
        print(f"Avg Groups per Disease: {results['avg_groups_per_disease']:.2f}")
        print(f"Avg Diseases per Group: {results['avg_diseases_per_group']:.2f}")
        
        source_stats = results['source_statistics']
        print(f"\nSource Statistics:")
        print(f"Total Sources: {source_stats['total_sources']}")
        print(f"Avg Sources per Group: {source_stats['avg_sources_per_group']:.2f}")
        
        validation_results = results['validation_results']
        print(f"\nValidation Results:")
        print(f"Valid Format: {validation_results['valid_format_percentage']:.1f}%")
        
        print(f"\nGenerated Files:")
        print(f"  - websearch_groups_statistics.json")
        print(f"  - group_distribution_analysis.png")
        print(f"  - top_groups_by_diseases.png")
        print(f"  - source_type_analysis.png")
        print(f"  - group_type_distribution.png")
        print(f"  - disease_coverage_analysis.png")
        print(f"  - source_validation_report.png")
        print(f"  - summary_dashboard.png")
        print(f"\nCRITICAL: All analyses used COMPLETE datasets - no data slicing applied")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 