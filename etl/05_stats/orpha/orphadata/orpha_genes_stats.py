#!/usr/bin/env python3
"""
Orpha Genes Statistical Analysis

This script generates comprehensive statistical analysis and visualizations
for the genes ETL system, analyzing both processed and curated datasets.
"""

import json
import logging
import argparse
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Client imports
from core.datastore.orpha.orphadata.processed_gene_client import ProcessedGeneClient
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class GeneStatisticsAnalyzer:
    """Main class for gene statistics analysis"""
    
    def __init__(self, output_base_dir: str = "results/stats/etl", 
                 dataset_type: str = "metabolic"):
        """
        Initialize the analyzer with configurable paths
        
        Args:
            output_base_dir: Base directory for outputs
            dataset_type: Type of dataset (metabolic, all, etc.)
        """
        self.output_base_dir = Path(output_base_dir)
        self.dataset_type = dataset_type
        
        # Configure output paths dynamically
        self.all_diseases_path = self.output_base_dir / "all_disease_instances" / "orpha" / "orphadata" / "orpha_genes"
        self.subset_path = self.output_base_dir / "subset_of_disease_instances" / dataset_type / "orpha" / "orphadata" / "orpha_genes"
        
        # Initialize clients
        self.processed_client = ProcessedGeneClient()
        self.curated_client = CuratedGeneClient()
        
        # Cache for performance
        self.cache = {}
        
        logger.info(f"Initialized GeneStatisticsAnalyzer")
        logger.info(f"Output base directory: {self.output_base_dir}")
        logger.info(f"Dataset type: {self.dataset_type}")
        logger.info(f"All diseases path: {self.all_diseases_path}")
        logger.info(f"Subset path: {self.subset_path}")

    def ensure_output_directories(self):
        """Create output directories if they don't exist"""
        self.all_diseases_path.mkdir(parents=True, exist_ok=True)
        self.subset_path.mkdir(parents=True, exist_ok=True)
        logger.info("Output directories created")

    def analyze_comprehensive_dataset(self) -> Dict[str, Any]:
        """Analyze complete processed dataset"""
        logger.info("Starting comprehensive dataset analysis...")
        
        # Check if processed client has data
        if not self.processed_client.is_data_available():
            logger.error("Processed gene data not available")
            return {}
        
        # Get basic statistics
        basic_stats = self.processed_client.get_basic_coverage_stats()
        
        # Load internal data structures to get disease lists
        self.processed_client._ensure_disease2genes_loaded()
        self.processed_client._ensure_gene2diseases_loaded()
        
        all_diseases = list(self.processed_client._disease2genes.keys())
        diseases_with_genes = [d for d in all_diseases if self.processed_client._disease2genes[d]]
        
        # Gene distribution from gene2diseases
        gene_distribution = {}
        for gene, diseases in self.processed_client._gene2diseases.items():
            gene_distribution[gene] = len(diseases)
        
        # Association type distribution
        association_type_dist = self.processed_client.get_association_type_distribution()
        
        # External reference coverage
        external_ref_coverage = self.processed_client.get_external_reference_coverage()
        
        # Calculate summary statistics
        total_associations = basic_stats['total_gene_associations']
        unique_genes = basic_stats['unique_genes']
        
        comprehensive_stats = {
            'dataset_overview': {
                'total_diseases': len(all_diseases),
                'diseases_with_genes': len(diseases_with_genes),
                'coverage_percentage': (len(diseases_with_genes) / len(all_diseases)) * 100 if all_diseases else 0,
                'total_associations': total_associations,
                'unique_genes': unique_genes,
                'average_associations_per_disease': total_associations / len(diseases_with_genes) if diseases_with_genes else 0,
                'average_diseases_per_gene': total_associations / unique_genes if unique_genes else 0
            },
            'association_type_distribution': association_type_dist,
            'external_reference_coverage': external_ref_coverage,
            'gene_distribution': dict(sorted(gene_distribution.items(), key=lambda x: x[1], reverse=True)[:50]),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Comprehensive analysis completed:")
        logger.info(f"  - Total diseases: {len(all_diseases)}")
        logger.info(f"  - Diseases with genes: {len(diseases_with_genes)}")
        logger.info(f"  - Coverage: {comprehensive_stats['dataset_overview']['coverage_percentage']:.1f}%")
        logger.info(f"  - Total associations: {total_associations}")
        logger.info(f"  - Unique genes: {unique_genes}")
        
        return comprehensive_stats

    def analyze_curated_subset(self) -> Dict[str, Any]:
        """Analyze curated metabolic diseases subset"""
        logger.info(f"Starting curated subset analysis for {self.dataset_type} diseases...")
        
        # Check if curated client has data
        if not self.curated_client.is_data_available():
            logger.error("Curated gene data not available")
            return {}
        
        # Get coverage statistics
        coverage_stats = self.curated_client.get_coverage_statistics()
        
        # Gene distribution
        gene_distribution = self.curated_client.get_gene_distribution()
        
        # Disease-gene count distribution
        disease_gene_dist = self.curated_client.get_disease_gene_count_distribution()
        
        # Top genes analysis
        top_genes = self.curated_client.get_most_common_genes(50)
        
        # Complex diseases analysis
        complex_diseases = self.curated_client.get_diseases_with_multiple_genes(min_genes=3)
        
        # Single gene diseases
        single_gene_diseases = [d for d in self.curated_client.get_diseases_with_genes() 
                               if len(self.curated_client.get_genes_for_disease(d)) == 1]
        
        # Top diseases by gene count
        diseases_with_genes = self.curated_client.get_diseases_with_genes()
        disease_gene_counts = []
        for disease_code in diseases_with_genes:
            genes = self.curated_client.get_genes_for_disease(disease_code)
            disease_name = self.curated_client.get_disease_name(disease_code)
            disease_gene_counts.append({
                'orpha_code': disease_code,
                'disease_name': disease_name or f"Disease {disease_code}",
                'gene_count': len(genes),
                'genes': genes
            })
        
        # Sort by gene count (descending) and take top 20
        top_diseases_by_gene_count = sorted(disease_gene_counts, key=lambda x: x['gene_count'], reverse=True)[:20]
        
        curated_stats = {
            'subset_overview': {
                'dataset_type': self.dataset_type,
                'total_diseases': coverage_stats['total_diseases'],
                'diseases_with_genes': coverage_stats['diseases_with_genes'],
                'diseases_without_genes': coverage_stats['diseases_without_genes'],
                'coverage_percentage': coverage_stats['coverage_percentage'],
                'total_gene_associations': sum(gene_distribution.values()),
                'unique_genes': len(gene_distribution),
                'average_genes_per_disease': sum(gene_distribution.values()) / coverage_stats['diseases_with_genes'] if coverage_stats['diseases_with_genes'] > 0 else 0
            },
            'disease_gene_distribution': disease_gene_dist,
            'top_genes': top_genes[:20],  # Top 20 for summary
            'complex_diseases': {
                'total_complex_diseases': len(complex_diseases),
                'complex_disease_examples': complex_diseases[:5]  # Top 5 examples
            },
            'top_diseases_by_gene_count': top_diseases_by_gene_count,
            'monogenic_analysis': {
                'single_gene_diseases': len(single_gene_diseases),
                'multi_gene_diseases': coverage_stats['diseases_with_genes'] - len(single_gene_diseases),
                'monogenic_percentage': (len(single_gene_diseases) / coverage_stats['diseases_with_genes']) * 100 if coverage_stats['diseases_with_genes'] > 0 else 0
            },
            'gene_distribution': dict(sorted(gene_distribution.items(), key=lambda x: x[1], reverse=True)[:50]),
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Curated subset analysis completed:")
        logger.info(f"  - Dataset type: {self.dataset_type}")
        logger.info(f"  - Total diseases: {coverage_stats['total_diseases']}")
        logger.info(f"  - Diseases with genes: {coverage_stats['diseases_with_genes']}")
        logger.info(f"  - Coverage: {coverage_stats['coverage_percentage']:.1f}%")
        logger.info(f"  - Unique genes: {len(gene_distribution)}")
        logger.info(f"  - Complex diseases: {len(complex_diseases)}")
        if top_diseases_by_gene_count:
            top_disease = top_diseases_by_gene_count[0]
            logger.info(f"  - Most complex disease: {top_disease['disease_name']} ({top_disease['gene_count']} genes)")
        
        return curated_stats

    def analyze_comparative_metrics(self) -> Dict[str, Any]:
        """Compare processed vs curated datasets"""
        logger.info("Starting comparative analysis...")
        
        # Get curated diseases
        curated_diseases = set(self.curated_client.get_diseases_with_genes())
        
        # Get processed data for the same diseases
        processed_data = {}
        for disease_code in curated_diseases:
            processed_genes = self.processed_client.get_genes_for_disease(disease_code)
            processed_data[disease_code] = len(processed_genes)
        
        # Calculate metrics
        total_processed_associations = sum(processed_data.values())
        total_curated_associations = sum(len(self.curated_client.get_genes_for_disease(code)) for code in curated_diseases)
        
        comparative_stats = {
            'curation_impact': {
                'diseases_analyzed': len(curated_diseases),
                'processed_associations': total_processed_associations,
                'curated_associations': total_curated_associations,
                'association_reduction': 1 - (total_curated_associations / total_processed_associations) if total_processed_associations > 0 else 0,
                'focus_improvement': 'disease-causing associations only',
                'average_reduction_per_disease': (total_processed_associations - total_curated_associations) / len(curated_diseases) if curated_diseases else 0
            },
            'quality_improvement': {
                'curation_method': 'disease-causing gene filtering',
                'excluded_association_types': [
                    'Major susceptibility factor',
                    'Candidate gene',
                    'Biomarker',
                    'Fusion gene'
                ]
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Comparative analysis completed:")
        logger.info(f"  - Diseases analyzed: {len(curated_diseases)}")
        logger.info(f"  - Association reduction: {comparative_stats['curation_impact']['association_reduction']:.1%}")
        
        return comparative_stats

    def create_gene_association_distribution(self, curated_stats: Dict[str, Any]):
        """Create gene association distribution chart"""
        logger.info("Creating gene association distribution chart...")
        
        disease_gene_dist = curated_stats['disease_gene_distribution']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data
        categories = list(disease_gene_dist.keys())
        values = list(disease_gene_dist.values())
        
        # Create bar chart
        colors = sns.color_palette("husl", len(categories))
        bars = ax.bar(categories, values, color=colors, edgecolor='black', alpha=0.8)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + max(values)*0.01,
                   f'{value}\n({value/sum(values)*100:.1f}%)',
                   ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # Styling
        ax.set_title(f'Distribution of Gene Counts per Disease\n({self.dataset_type.title()} Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Gene Count Categories', fontsize=12)
        ax.set_ylabel('Number of Diseases', fontsize=12)
        
        # Add grid and styling
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Add summary statistics
        total_diseases = sum(values)
        ax.text(0.02, 0.98, f'Total Diseases: {total_diseases}\nDataset: {self.dataset_type.title()}',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.subset_path / 'gene_association_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gene association distribution chart saved to: {output_file}")

    def create_top_associated_genes(self, curated_stats: Dict[str, Any]):
        """Create top associated genes chart"""
        logger.info("Creating top associated genes chart...")
        
        top_genes = curated_stats['top_genes'][:15]  # Top 15 for better visibility
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data
        genes = [gene_info['gene'] for gene_info in top_genes]
        counts = [gene_info['disease_count'] for gene_info in top_genes]
        
        # Create horizontal bar chart
        colors = sns.color_palette("viridis", len(genes))
        bars = ax.barh(genes, counts, color=colors, edgecolor='black', alpha=0.8)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2,
                   f'{count}', ha='left', va='center', fontweight='bold')
        
        # Styling
        ax.set_title(f'Top 15 Most Associated Genes\n({self.dataset_type.title()} Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Number of Associated Diseases', fontsize=12)
        ax.set_ylabel('Gene Symbol', fontsize=12)
        
        # Add grid
        ax.grid(True, axis='x', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Invert y-axis to show top genes at top
        ax.invert_yaxis()
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.subset_path / 'top_associated_genes.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Top associated genes chart saved to: {output_file}")

    def create_gene_coverage_analysis(self, curated_stats: Dict[str, Any]):
        """Create gene coverage analysis chart"""
        logger.info("Creating gene coverage analysis chart...")
        
        coverage_data = curated_stats['subset_overview']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Prepare data
        labels = ['With Genes', 'Without Genes']
        sizes = [coverage_data['diseases_with_genes'], coverage_data['diseases_without_genes']]
        colors = ['#4CAF50', '#FFC107']
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 12})
        
        # Styling
        ax.set_title(f'Gene Coverage Analysis\n({self.dataset_type.title()} Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Add summary statistics
        total_diseases = sum(sizes)
        coverage_pct = coverage_data['coverage_percentage']
        
        # Add text box with statistics
        stats_text = f"""Total Diseases: {total_diseases}
Diseases with Genes: {sizes[0]}
Diseases without Genes: {sizes[1]}
Coverage: {coverage_pct:.1f}%"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.subset_path / 'gene_coverage_analysis.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Gene coverage analysis chart saved to: {output_file}")

    def create_association_type_distribution(self, comprehensive_stats: Dict[str, Any]):
        """Create association type distribution chart"""
        logger.info("Creating association type distribution chart...")
        
        association_types = comprehensive_stats['association_type_distribution']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data (top 10 association types)
        sorted_types = sorted(association_types.items(), key=lambda x: x[1], reverse=True)[:10]
        types = [item[0] for item in sorted_types]
        counts = [item[1] for item in sorted_types]
        
        # Truncate long labels
        types = [t[:30] + '...' if len(t) > 30 else t for t in types]
        
        # Create pie chart
        colors = sns.color_palette("Set3", len(types))
        wedges, texts, autotexts = ax.pie(counts, labels=types, colors=colors, autopct='%1.1f%%',
                                         startangle=90, textprops={'fontsize': 9})
        
        # Styling
        ax.set_title('Association Type Distribution\n(All Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Add total count
        total_associations = sum(counts)
        ax.text(0.02, 0.98, f'Total Associations: {total_associations}\n(Top 10 types shown)',
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.all_diseases_path / 'association_type_distribution.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Association type distribution chart saved to: {output_file}")

    def create_monogenic_vs_polygenic(self, curated_stats: Dict[str, Any]):
        """Create monogenic vs polygenic analysis chart"""
        logger.info("Creating monogenic vs polygenic analysis chart...")
        
        monogenic_data = curated_stats['monogenic_analysis']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Prepare data
        categories = ['Single Gene\n(Monogenic)', 'Multiple Genes\n(Polygenic)']
        values = [monogenic_data['single_gene_diseases'], monogenic_data['multi_gene_diseases']]
        colors = ['#FF6B6B', '#4ECDC4']
        
        # Create bar chart
        bars = ax.bar(categories, values, color=colors, edgecolor='black', alpha=0.8)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + max(values)*0.01,
                   f'{value}\n({value/sum(values)*100:.1f}%)',
                   ha='center', va='bottom', fontweight='bold', fontsize=12)
        
        # Styling
        ax.set_title(f'Monogenic vs Polygenic Disease Distribution\n({self.dataset_type.title()} Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('Number of Diseases', fontsize=12)
        
        # Add grid
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Add statistics
        total_diseases = sum(values)
        monogenic_pct = monogenic_data['monogenic_percentage']
        
        stats_text = f"""Total Diseases: {total_diseases}
Monogenic: {monogenic_pct:.1f}%
Polygenic: {100 - monogenic_pct:.1f}%"""
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8))
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.subset_path / 'monogenic_vs_polygenic.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Monogenic vs polygenic analysis chart saved to: {output_file}")

    def create_external_reference_coverage(self, comprehensive_stats: Dict[str, Any]):
        """Create external reference coverage chart"""
        logger.info("Creating external reference coverage chart...")
        
        external_refs = comprehensive_stats['external_reference_coverage']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Prepare data - external_refs contains counts, not percentages
        references = list(external_refs.keys())
        counts = [external_refs[ref] for ref in references]
        
        # Calculate percentages relative to total associations
        total_associations = comprehensive_stats['dataset_overview']['total_associations']
        percentages = [(count / total_associations) * 100 for count in counts]
        
        # Create bar chart
        colors = sns.color_palette("coolwarm", len(references))
        bars = ax.bar(references, percentages, color=colors, edgecolor='black', alpha=0.8)
        
        # Add value labels
        for bar, percentage, count in zip(bars, percentages, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 1,
                   f'{percentage:.1f}%\n({count})', ha='center', va='bottom', fontweight='bold')
        
        # Styling
        ax.set_title('External Reference Coverage\n(All Diseases)', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('Coverage Percentage', fontsize=12)
        ax.set_xlabel('Reference Database', fontsize=12)
        ax.set_ylim(0, max(percentages) + 10)
        
        # Add grid
        ax.grid(True, axis='y', alpha=0.3)
        ax.set_axisbelow(True)
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save chart
        output_file = self.all_diseases_path / 'external_reference_coverage.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"External reference coverage chart saved to: {output_file}")

    def generate_all_visualizations(self, comprehensive_stats: Dict[str, Any], curated_stats: Dict[str, Any]):
        """Generate all visualization charts"""
        logger.info("Generating all visualizations...")
        
        # Set visualization style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Ensure output directories exist
        self.ensure_output_directories()
        
        # Generate comprehensive dataset visualizations
        if comprehensive_stats:
            self.create_association_type_distribution(comprehensive_stats)
            self.create_external_reference_coverage(comprehensive_stats)
        
        # Generate curated subset visualizations
        if curated_stats:
            self.create_gene_association_distribution(curated_stats)
            self.create_top_associated_genes(curated_stats)
            self.create_gene_coverage_analysis(curated_stats)
            self.create_monogenic_vs_polygenic(curated_stats)
        
        logger.info("All visualizations generated successfully")

    def generate_summary_reports(self, comprehensive_stats: Dict[str, Any], 
                                curated_stats: Dict[str, Any], 
                                comparative_stats: Dict[str, Any]):
        """Generate JSON summary reports"""
        logger.info("Generating summary reports...")
        
        # Ensure output directories exist
        self.ensure_output_directories()
        
        # Comprehensive dataset summary
        if comprehensive_stats:
            comprehensive_summary = {
                'analysis_type': 'comprehensive_dataset',
                'dataset_scope': 'all_diseases',
                'statistics': comprehensive_stats,
                'generated_at': datetime.now().isoformat()
            }
            
            comprehensive_file = self.all_diseases_path / 'comprehensive_gene_analysis.json'
            with open(comprehensive_file, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_summary, f, indent=2, ensure_ascii=False)
            
            # Analysis summary for comprehensive
            analysis_summary = {
                'dataset_type': 'all_diseases',
                'total_diseases': comprehensive_stats['dataset_overview']['total_diseases'],
                'diseases_with_genes': comprehensive_stats['dataset_overview']['diseases_with_genes'],
                'coverage_percentage': comprehensive_stats['dataset_overview']['coverage_percentage'],
                'unique_genes': comprehensive_stats['dataset_overview']['unique_genes'],
                'total_associations': comprehensive_stats['dataset_overview']['total_associations']
            }
            
            summary_file = self.all_diseases_path / 'analysis_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_summary, f, indent=2, ensure_ascii=False)
        
        # Curated subset summary
        if curated_stats:
            curated_summary = {
                'analysis_type': 'curated_subset',
                'dataset_scope': self.dataset_type,
                'statistics': curated_stats,
                'comparative_analysis': comparative_stats,
                'generated_at': datetime.now().isoformat()
            }
            
            curated_file = self.subset_path / f'{self.dataset_type}_gene_analysis.json'
            with open(curated_file, 'w', encoding='utf-8') as f:
                json.dump(curated_summary, f, indent=2, ensure_ascii=False)
            
            # Analysis summary for curated
            analysis_summary = {
                'dataset_type': self.dataset_type,
                'total_diseases': curated_stats['subset_overview']['total_diseases'],
                'diseases_with_genes': curated_stats['subset_overview']['diseases_with_genes'],
                'coverage_percentage': curated_stats['subset_overview']['coverage_percentage'],
                'unique_genes': curated_stats['subset_overview']['unique_genes'],
                'total_associations': curated_stats['subset_overview']['total_gene_associations']
            }
            
            summary_file = self.subset_path / 'analysis_summary.json'
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_summary, f, indent=2, ensure_ascii=False)
        
        logger.info("Summary reports generated successfully")

    def run_complete_analysis(self):
        """Run complete statistical analysis"""
        logger.info("Starting complete gene statistics analysis...")
        
        try:
            # 1. Comprehensive dataset analysis
            comprehensive_stats = self.analyze_comprehensive_dataset()
            
            # 2. Curated subset analysis
            curated_stats = self.analyze_curated_subset()
            
            # 3. Comparative analysis
            comparative_stats = self.analyze_comparative_metrics()
            
            # 4. Generate visualizations
            self.generate_all_visualizations(comprehensive_stats, curated_stats)
            
            # 5. Generate summary reports
            self.generate_summary_reports(comprehensive_stats, curated_stats, comparative_stats)
            
            logger.info("Complete gene statistics analysis finished successfully!")
            
            # Print summary
            if curated_stats:
                coverage_pct = curated_stats['subset_overview']['coverage_percentage']
                total_diseases = curated_stats['subset_overview']['total_diseases']
                diseases_with_genes = curated_stats['subset_overview']['diseases_with_genes']
                unique_genes = curated_stats['subset_overview']['unique_genes']
                
                print(f"\n🎯 GENES STATISTICS ANALYSIS COMPLETED")
                print(f"=" * 50)
                print(f"Dataset Type: {self.dataset_type.title()}")
                print(f"Total Diseases: {total_diseases}")
                print(f"Diseases with Genes: {diseases_with_genes}")
                print(f"Coverage: {coverage_pct:.1f}%")
                print(f"Unique Genes: {unique_genes}")
                print(f"Output Directory: {self.output_base_dir}")
                print(f"✅ Analysis completed successfully!")
        
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Generate genes statistical analysis')
    parser.add_argument('--output-dir', 
                       default='results/stats/etl',
                       help='Base output directory for results')
    parser.add_argument('--dataset-type', 
                       default='metabolic',
                       help='Type of dataset (metabolic, all, etc.)')
    parser.add_argument('--comprehensive', action='store_true',
                       help='Generate comprehensive dataset analysis')
    parser.add_argument('--curated', action='store_true',
                       help='Generate curated subset analysis')
    parser.add_argument('--visualizations', action='store_true',
                       help='Generate all visualizations')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = GeneStatisticsAnalyzer(args.output_dir, args.dataset_type)
    
    # Run analysis based on arguments
    if not any([args.comprehensive, args.curated, args.visualizations]):
        # If no specific options, run complete analysis
        analyzer.run_complete_analysis()
    else:
        # Run specific analyses
        comprehensive_stats = {}
        curated_stats = {}
        comparative_stats = {}
        
        if args.comprehensive:
            comprehensive_stats = analyzer.analyze_comprehensive_dataset()
        
        if args.curated:
            curated_stats = analyzer.analyze_curated_subset()
            comparative_stats = analyzer.analyze_comparative_metrics()
        
        if args.visualizations:
            analyzer.generate_all_visualizations(comprehensive_stats, curated_stats)
        
        if comprehensive_stats or curated_stats:
            analyzer.generate_summary_reports(comprehensive_stats, curated_stats, comparative_stats)


if __name__ == "__main__":
    main() 