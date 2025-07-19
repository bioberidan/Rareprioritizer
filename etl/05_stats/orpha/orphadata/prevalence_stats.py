import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import sys
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient


class PrevalenceStatistics:
    """Generate comprehensive statistics and visualizations for prevalence data"""
    
    def __init__(self, output_dir="results/etl/orpha/orphadata/prevalence"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize controller
        self.controller = ProcessedPrevalenceClient()
        self.controller.preload_all()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Initialize data containers
        self.stats = {}
        self.plots_created = []
        
    def generate_all_statistics(self):
        """Generate all prevalence statistics and visualizations"""
        
        print("🔍 Generating Prevalence Statistics...")
        
        # Basic statistics
        self.generate_basic_stats()
        
        # Data quality analysis
        self.analyze_data_quality()
        
        # Disease analysis  
        self.analyze_diseases()
        
        # Geographic analysis
        self.analyze_geographic_patterns()
        
        # Prevalence type analysis
        self.analyze_prevalence_types()
        
        # Reliability analysis
        self.analyze_reliability_patterns()
        
        # Rarity spectrum analysis
        self.analyze_rarity_spectrum()
        
        # Advanced analytics
        self.analyze_advanced_patterns()
        
        # Generate summary report
        self.generate_summary_report()
        
        # Create all plots
        self.create_all_plots()
        
        print(f"✅ Statistics generation complete!")
        print(f"📊 Generated {len(self.plots_created)} plots")
        print(f"📁 Output directory: {self.output_dir}")
        
    def generate_basic_stats(self):
        """Generate basic coverage statistics"""
        
        basic_stats = self.controller.get_basic_coverage_stats()
        data_quality = self.controller.get_data_quality_metrics()
        
        self.stats['basic'] = {
            'total_disorders_in_system': basic_stats.get('total_disorders', 0),
            'disorders_with_prevalence': basic_stats.get('disorders_with_prevalence', 0),
            'disorders_without_prevalence': basic_stats.get('total_disorders', 0) - basic_stats.get('disorders_with_prevalence', 0),
            'prevalence_coverage_percentage': round((basic_stats.get('disorders_with_prevalence', 0) / max(basic_stats.get('total_disorders', 1), 1)) * 100, 2),
            'total_prevalence_records': basic_stats.get('total_prevalence_records', 0),
            'reliable_records': basic_stats.get('reliable_records', 0),
            'reliability_percentage': basic_stats.get('reliability_percentage', 0),
            'diseases_with_mean_estimates': data_quality.get('diseases_with_mean_estimates', 0),
            'mean_estimate_coverage': data_quality.get('mean_estimate_coverage', 0),
            'average_records_per_disease': 0
        }
        
        if self.stats['basic']['disorders_with_prevalence'] > 0:
            self.stats['basic']['average_records_per_disease'] = round(
                self.stats['basic']['total_prevalence_records'] / self.stats['basic']['disorders_with_prevalence'], 2
            )
        
        print(f"📊 Basic Stats: {self.stats['basic']['disorders_with_prevalence']} diseases have prevalence data ({self.stats['basic']['prevalence_coverage_percentage']}%)")
        
    def analyze_data_quality(self):
        """Analyze data quality patterns"""
        
        # Get reliability and validation distributions
        reliability_dist = self.controller.get_reliability_distribution()
        validation_dist = self.controller.get_validation_status_distribution()
        source_quality = self.controller.get_source_quality_breakdown()
        fiable_stats = self.controller.get_fiable_vs_non_fiable_stats()
        
        self.stats['data_quality'] = {
            'reliability_distribution': reliability_dist,
            'validation_status_distribution': validation_dist,
            'source_quality_breakdown': source_quality,
            'fiable_vs_non_fiable': fiable_stats,
            'estimate_confidence': self.controller.get_estimate_confidence_breakdown()
        }
        
        print(f"📊 Data Quality: {fiable_stats.get('fiable_percentage', 0)}% of records are reliable (≥6.0 score)")
        
    def analyze_diseases(self):
        """Analyze disease patterns and distributions using COMPLETE dataset"""
        
        # Get diseases with most records - GET ALL, NOT LIMITED TO 50
        all_diseases = self.controller.get_diseases_with_most_prevalence_records(10000)  # Get ALL diseases
        top_diseases = all_diseases[:50]  # Top 50 for detailed analysis
        reliable_diseases = self.controller.get_diseases_by_reliability_score(20)
        global_diseases = self.controller.get_diseases_with_global_coverage()
        multi_region_diseases = self.controller.get_diseases_with_regional_variations()
        
        # Disease distribution analysis - USE COMPLETE DATASET
        record_counts = [d['total_records'] for d in all_diseases]  # ALL diseases, not just top 50
        mean_estimates = [d['mean_value_per_million'] for d in all_diseases if d['mean_value_per_million'] > 0]  # ALL mean estimates
        
        self.stats['diseases'] = {
            'top_diseases': top_diseases[:20],  # Top 20 for detailed analysis
            'reliable_diseases': reliable_diseases[:15],  # Top 15 most reliable
            'global_coverage_diseases': len(global_diseases),
            'multi_region_diseases': len(multi_region_diseases),
            'record_distribution': {
                'mean': np.mean(record_counts) if record_counts else 0,
                'median': np.median(record_counts) if record_counts else 0,
                'std': np.std(record_counts) if record_counts else 0,
                'max': max(record_counts) if record_counts else 0,
                'min': min(record_counts) if record_counts else 0
            },
            'mean_estimate_distribution': {
                'mean': np.mean(mean_estimates) if mean_estimates else 0,
                'median': np.median(mean_estimates) if mean_estimates else 0,
                'std': np.std(mean_estimates) if mean_estimates else 0,
                'max': max(mean_estimates) if mean_estimates else 0,
                'min': min(mean_estimates) if mean_estimates else 0
            },
            'diseases_by_record_count': dict(Counter(record_counts))
        }
        
        print(f"🧬 Disease Analysis: {len(record_counts)} diseases analyzed, top disease has {self.stats['diseases']['record_distribution']['max']} prevalence records")
        
    def analyze_geographic_patterns(self):
        """Analyze geographic distribution and patterns"""
        
        # Get geographic data
        geographic_dist = self.controller.get_geographic_distribution()
        top_regions = self.controller.get_top_regions_by_data_volume(30)
        regional_quality = self.controller.get_regional_data_quality()
        regional_completeness = self.controller.get_regional_coverage_completeness()
        
        # Analysis
        total_regions = len(geographic_dist)
        top_10_regions = dict(sorted(geographic_dist.items(), key=lambda x: x[1], reverse=True)[:10])
        
        self.stats['geographic'] = {
            'total_regions': total_regions,
            'top_regions': top_regions[:20],  # Top 20 regions
            'geographic_distribution': top_10_regions,
            'regional_data_quality': dict(sorted(regional_quality.items(), key=lambda x: x[1], reverse=True)[:10]),
            'regional_completeness': dict(sorted(regional_completeness.items(), key=lambda x: x[1], reverse=True)[:10]),
            'worldwide_records': geographic_dist.get('Worldwide', 0),
            'worldwide_percentage': round((geographic_dist.get('Worldwide', 0) / sum(geographic_dist.values())) * 100, 2) if geographic_dist else 0
        }
        
        print(f"🌍 Geographic Analysis: {total_regions} regions, {geographic_dist.get('Worldwide', 0)} worldwide records")
        
    def analyze_prevalence_types(self):
        """Analyze prevalence type patterns"""
        
        # Get prevalence type data
        type_dist = self.controller.get_prevalence_type_distribution()
        type_reliability = self.controller.get_reliability_by_prevalence_type()
        
        # Analysis of type usage
        total_records = sum(type_dist.values())
        type_percentages = {t: round((count / total_records) * 100, 2) for t, count in type_dist.items()}
        
        self.stats['prevalence_types'] = {
            'type_distribution': type_dist,
            'type_percentages': type_percentages,
            'type_reliability': type_reliability,
            'most_common_type': max(type_dist.items(), key=lambda x: x[1]) if type_dist else ('None', 0),
            'total_types': len(type_dist)
        }
        
        most_common = self.stats['prevalence_types']['most_common_type']
        print(f"📊 Prevalence Types: {most_common[0]} is most common ({most_common[1]} records)")
        
    def analyze_reliability_patterns(self):
        """Analyze reliability and validation patterns"""
        
        # Get reliability data
        reliability_dist = self.controller.get_reliability_distribution()
        validation_dist = self.controller.get_validation_status_distribution()
        source_quality = self.controller.get_source_quality_breakdown()
        
        # Calculate reliability metrics
        total_records = sum(reliability_dist.values())
        high_quality_records = reliability_dist.get('8-10', 0)
        medium_quality_records = reliability_dist.get('6-8', 0)
        low_quality_records = sum([reliability_dist.get(k, 0) for k in ['0-2', '2-4', '4-6']])
        
        self.stats['reliability'] = {
            'reliability_distribution': reliability_dist,
            'validation_distribution': validation_dist,
            'source_quality': source_quality,
            'quality_levels': {
                'high_quality': high_quality_records,
                'medium_quality': medium_quality_records,
                'low_quality': low_quality_records
            },
            'high_quality_percentage': round((high_quality_records / total_records) * 100, 2) if total_records else 0,
            'validated_percentage': round((validation_dist.get('Validated', 0) / total_records) * 100, 2) if total_records else 0,
            'pmid_percentage': round((source_quality.get('PMID_referenced', 0) / total_records) * 100, 2) if total_records else 0
        }
        
        print(f"📊 Reliability: {self.stats['reliability']['high_quality_percentage']}% high quality (8-10 score)")
        
    def analyze_rarity_spectrum(self):
        """Analyze prevalence class and rarity patterns"""
        
        # Get rarity data
        class_dist = self.controller.get_prevalence_class_distribution()
        rarity_spectrum = self.controller.get_rarity_spectrum_analysis()
        
        # Analysis
        total_classified = sum(rarity_spectrum.values())
        rarity_percentages = {level: round((count / total_classified) * 100, 2) 
                             for level, count in rarity_spectrum.items()}
        
        self.stats['rarity'] = {
            'prevalence_class_distribution': dict(sorted(class_dist.items(), key=lambda x: x[1], reverse=True)[:10]),
            'rarity_spectrum': rarity_spectrum,
            'rarity_percentages': rarity_percentages,
            'ultra_rare_percentage': rarity_percentages.get('ultra_rare', 0),
            'very_rare_percentage': rarity_percentages.get('very_rare', 0),
            'rare_percentage': rarity_percentages.get('rare', 0),
            'total_classified': total_classified
        }
        
        print(f"📊 Rarity: {rarity_percentages.get('ultra_rare', 0)}% ultra-rare, {rarity_percentages.get('very_rare', 0)}% very rare")
        
    def analyze_advanced_patterns(self):
        """Analyze advanced patterns and relationships"""
        
        # Get advanced analytics
        data_density = self.controller.get_data_density_analysis()
        multi_region_diseases = self.controller.get_multi_region_diseases()
        consensus_analysis = self.controller.get_consensus_analysis()
        gaps_analysis = self.controller.get_data_gaps_analysis()
        
        self.stats['advanced'] = {
            'data_density': data_density,
            'multi_region_diseases_count': len(multi_region_diseases),
            'multi_region_diseases': multi_region_diseases[:10],  # Top 10
            'consensus_analysis': consensus_analysis,
            'data_gaps': gaps_analysis,
            'coverage_completeness': {
                'worldwide_gap_percentage': round((gaps_analysis.get('diseases_without_worldwide_data', 0) / 
                                                 max(gaps_analysis.get('total_diseases', 1), 1)) * 100, 2),
                'reliability_gap_percentage': round((gaps_analysis.get('diseases_without_reliable_data', 0) / 
                                                   max(gaps_analysis.get('total_diseases', 1), 1)) * 100, 2),
                'mean_estimate_gap_percentage': round((gaps_analysis.get('diseases_without_mean_estimate', 0) / 
                                                     max(gaps_analysis.get('total_diseases', 1), 1)) * 100, 2)
            }
        }
        
        print(f"📊 Advanced: {len(multi_region_diseases)} diseases in 5+ regions, {consensus_analysis.get('consensus_percentage', 0)}% consensus")
        
    def create_all_plots(self):
        """Create all visualization plots"""
        
        try:
            # 1. Basic overview dashboard
            self.plot_basic_overview()
            print("✅ Basic overview plot created")
        except Exception as e:
            print(f"❌ Error creating basic overview: {e}")
        
        try:
            # 2. Data quality analysis
            self.plot_data_quality_analysis()
            print("✅ Data quality analysis plot created")
        except Exception as e:
            print(f"❌ Error creating data quality analysis: {e}")
        
        try:
            # 3. Disease analysis
            self.plot_disease_analysis()
            print("✅ Disease analysis plot created")
        except Exception as e:
            print(f"❌ Error creating disease analysis: {e}")
        
        try:
            # 4. Geographic analysis
            self.plot_geographic_analysis()
            print("✅ Geographic analysis plot created")
        except Exception as e:
            print(f"❌ Error creating geographic analysis: {e}")
        
        try:
            # 5. Prevalence type analysis
            self.plot_prevalence_type_analysis()
            print("✅ Prevalence type analysis plot created")
        except Exception as e:
            print(f"❌ Error creating prevalence type analysis: {e}")
        
        try:
            # 6. Reliability analysis
            self.plot_reliability_analysis()
            print("✅ Reliability analysis plot created")
        except Exception as e:
            print(f"❌ Error creating reliability analysis: {e}")
        
        try:
            # 7. Rarity spectrum
            self.plot_rarity_spectrum()
            print("✅ Rarity spectrum plot created")
        except Exception as e:
            print(f"❌ Error creating rarity spectrum: {e}")
        
        try:
            # 8. PREVALENCE VALUE DISTRIBUTION (THE MOST IMPORTANT!)
            self.plot_prevalence_distribution()
            print("✅ Prevalence distribution plot created")
        except Exception as e:
            print(f"❌ Error creating prevalence distribution: {e}")
        
        try:
            # 9. Comprehensive dashboard
            self.create_dashboard()
            print("✅ Dashboard created")
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
        
    def plot_basic_overview(self):
        """Create basic statistics overview plot"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Prevalence Data - Basic Statistics Overview', fontsize=16, fontweight='bold')
        
        # 1. Disease coverage pie chart
        coverage_data = [
            self.stats['basic']['disorders_with_prevalence'],
            self.stats['basic']['disorders_without_prevalence']
        ]
        coverage_labels = ['Diseases with Prevalence', 'Diseases without Prevalence']
        colors = ['#2E86AB', '#A23B72']
        
        ax1.pie(coverage_data, labels=coverage_labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Disease Coverage')
        
        # 2. Key metrics bar chart
        metrics = ['Total Diseases', 'With Prevalence', 'Total Records', 'Reliable Records']
        values = [
            self.stats['basic']['total_disorders_in_system'],
            self.stats['basic']['disorders_with_prevalence'],
            self.stats['basic']['total_prevalence_records'],
            self.stats['basic']['reliable_records']
        ]
        
        bars = ax2.bar(metrics, values, color=['#F18F01', '#C73E1D', '#2E86AB', '#A23B72'])
        ax2.set_title('Key Metrics')
        ax2.set_ylabel('Count')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        # 3. Reliability distribution
        reliability_data = list(self.stats['data_quality']['reliability_distribution'].values())
        reliability_labels = list(self.stats['data_quality']['reliability_distribution'].keys())
        
        ax3.pie(reliability_data, labels=reliability_labels, autopct='%1.1f%%', startangle=90)
        ax3.set_title('Reliability Score Distribution')
        
        # 4. Mean estimate coverage
        mean_metrics = ['With Mean Estimates', 'Without Mean Estimates']
        mean_values = [
            self.stats['basic']['diseases_with_mean_estimates'],
            self.stats['basic']['disorders_with_prevalence'] - self.stats['basic']['diseases_with_mean_estimates']
        ]
        
        ax4.bar(mean_metrics, mean_values, color=['#2E86AB', '#F18F01'])
        ax4.set_title('Mean Estimate Coverage')
        ax4.set_ylabel('Number of Diseases')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'basic_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('basic_overview.png')
        
    def plot_data_quality_analysis(self):
        """Create data quality focused visualizations"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Data Quality Analysis', fontsize=16, fontweight='bold')
        
        # 1. Reliability score histogram
        reliability_dist = self.stats['data_quality']['reliability_distribution']
        score_ranges = list(reliability_dist.keys())
        score_counts = list(reliability_dist.values())
        
        ax1.bar(score_ranges, score_counts, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.set_title('Reliability Score Distribution')
        ax1.set_xlabel('Score Range')
        ax1.set_ylabel('Number of Records')
        
        # 2. Validation status pie chart
        validation_dist = self.stats['data_quality']['validation_status_distribution']
        valid_statuses = list(validation_dist.keys())
        valid_counts = list(validation_dist.values())
        
        ax2.pie(valid_counts, labels=valid_statuses, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Validation Status Distribution')
        
        # 3. Source quality breakdown
        source_quality = self.stats['data_quality']['source_quality_breakdown']
        sources = list(source_quality.keys())
        source_counts = list(source_quality.values())
        
        ax3.barh(sources, source_counts, color='#F18F01')
        ax3.set_title('Source Quality Breakdown')
        ax3.set_xlabel('Number of Records')
        
        # 4. Estimate confidence
        confidence_data = self.stats['data_quality']['estimate_confidence']
        conf_types = list(confidence_data.keys())
        conf_counts = list(confidence_data.values())
        
        ax4.pie(conf_counts, labels=conf_types, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Estimate Confidence Breakdown')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'data_quality_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('data_quality_analysis.png') 
        
    def plot_disease_analysis(self):
        """Create disease-focused analysis plots using COMPLETE dataset"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
        fig.suptitle('Disease Analysis - Complete Dataset (Record Count vs Prevalence Value)', fontsize=16, fontweight='bold')
        
        # GET TOP DISEASES BY PREVALENCE VALUE (THE MISSING ANALYSIS!)
        self.controller._ensure_disease2prevalence_loaded()
        diseases_by_prevalence = []
        
        for orpha_code, disease_data in self.controller._disease2prevalence.items():
            mean_prevalence = disease_data.get('mean_value_per_million', 0.0)
            if mean_prevalence > 0:
                diseases_by_prevalence.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name', ''),
                    'prevalence': mean_prevalence,
                    'total_records': len(disease_data.get('prevalence_records', [])),
                    'is_capped': disease_data.get('mean_calculation_metadata', {}).get('is_capped', False)
                })
        
        diseases_by_prevalence.sort(key=lambda x: x['prevalence'], reverse=True)
        top_by_prevalence = diseases_by_prevalence[:20]
        
        # 1. TOP DISEASES BY PREVALENCE VALUE (FIXED!)
        prev_names = [d['disease_name'][:30] + '...' if len(d['disease_name']) > 30 else d['disease_name'] 
                     for d in top_by_prevalence]
        prev_values = [d['prevalence'] for d in top_by_prevalence]
        prev_colors = ['#C73E1D' if d['is_capped'] else '#2E86AB' for d in top_by_prevalence]
        
        bars1 = ax1.barh(prev_names, prev_values, color=prev_colors)
        ax1.set_title('Top 20 Diseases by PREVALENCE VALUE\n(Red = Capped at 500)')
        ax1.set_xlabel('Prevalence (per million)')
        
        # Add value labels
        for i, bar in enumerate(bars1):
            width = bar.get_width()
            capped_text = " (CAPPED)" if top_by_prevalence[i]['is_capped'] else ""
            ax1.text(width + 2, bar.get_y() + bar.get_height()/2,
                    f'{width:.1f}{capped_text}', ha='left', va='center', fontsize=6)
        
        # 2. TOP DISEASES BY RECORD COUNT (ORIGINAL)
        top_diseases = self.stats['diseases']['top_diseases'][:20]  # Show top 20
        disease_names = [d['disease_name'][:30] + '...' if len(d['disease_name']) > 30 else d['disease_name'] 
                        for d in top_diseases]
        record_counts = [d['total_records'] for d in top_diseases]
        
        bars2 = ax2.barh(disease_names, record_counts, color='#F18F01')
        ax2.set_title('Top 20 Diseases by RECORD COUNT\n(Most Studied)')
        ax2.set_xlabel('Number of Records')
        
        # Add value labels
        for i, bar in enumerate(bars2):
            width = bar.get_width()
            ax2.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                    f'{int(width)}', ha='left', va='center', fontsize=7)
        
        # 3. PREVALENCE VALUE DISTRIBUTION
        all_prevalence_values = [d['prevalence'] for d in diseases_by_prevalence]
        ax3.hist(all_prevalence_values, bins=50, color='#A23B72', alpha=0.7, edgecolor='black')
        ax3.set_title(f'Prevalence Value Distribution\n({len(all_prevalence_values)} diseases)')
        ax3.set_xlabel('Prevalence (per million)')
        ax3.set_ylabel('Number of Diseases')
        ax3.axvline(np.mean(all_prevalence_values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(all_prevalence_values):.1f}')
        ax3.axvline(500.0, color='orange', linestyle='--', 
                   label=f'Cap: 500.0 ({len([d for d in diseases_by_prevalence if d["prevalence"] == 500.0])} diseases)')
        ax3.legend()
        
        # 4. RECORD COUNT DISTRIBUTION  
        all_diseases = self.controller.get_diseases_with_most_prevalence_records(10000)  # Get ALL
        all_record_counts = [d['total_records'] for d in all_diseases]
        
        ax4.hist(all_record_counts, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax4.set_title(f'Record Count Distribution\n({len(all_record_counts)} diseases)')
        ax4.set_xlabel('Number of Records')
        ax4.set_ylabel('Number of Diseases')
        ax4.axvline(np.mean(all_record_counts), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(all_record_counts):.1f}')
        ax4.axvline(np.median(all_record_counts), color='green', linestyle='--', 
                   label=f'Median: {np.median(all_record_counts):.1f}')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'disease_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('disease_analysis.png')
        
    def plot_geographic_analysis(self):
        """Create geographic distribution and coverage plots"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Geographic Analysis', fontsize=16, fontweight='bold')
        
        # 1. Top regions by record count
        top_regions = self.stats['geographic']['top_regions'][:15]
        region_names = [r['region'][:20] + '...' if len(r['region']) > 20 else r['region'] for r in top_regions]
        region_counts = [r['total_records'] for r in top_regions]
        
        ax1.barh(region_names, region_counts, color='#F18F01')
        ax1.set_title('Top 15 Regions by Record Count')
        ax1.set_xlabel('Number of Records')
        
        # 2. Regional data quality (top 10)
        regional_quality = self.stats['geographic']['regional_data_quality']
        if regional_quality:
            quality_regions = list(regional_quality.keys())[:10]
            quality_scores = list(regional_quality.values())[:10]
            
            ax2.bar(quality_regions, quality_scores, color='#2E86AB')
            ax2.set_title('Top 10 Regions by Data Quality')
            ax2.set_ylabel('Average Reliability Score')
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.text(0.5, 0.5, 'No regional quality data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Regional Data Quality')
        
        # 3. Worldwide vs Regional distribution
        worldwide_records = self.stats['geographic']['worldwide_records']
        total_records = sum(self.stats['geographic']['geographic_distribution'].values())
        regional_records = total_records - worldwide_records
        
        coverage_data = [worldwide_records, regional_records]
        coverage_labels = ['Worldwide', 'Regional/Country-specific']
        
        ax3.pie(coverage_data, labels=coverage_labels, autopct='%1.1f%%', 
                colors=['#2E86AB', '#F18F01'], startangle=90)
        ax3.set_title('Worldwide vs Regional Coverage')
        
        # 4. Regional completeness (diseases per region)
        regional_completeness = self.stats['geographic']['regional_completeness']
        if regional_completeness:
            comp_regions = list(regional_completeness.keys())[:10]
            comp_counts = list(regional_completeness.values())[:10]
            
            ax4.bar(comp_regions, comp_counts, color='#A23B72')
            ax4.set_title('Top 10 Regions by Disease Count')
            ax4.set_ylabel('Number of Diseases')
            ax4.tick_params(axis='x', rotation=45)
        else:
            ax4.text(0.5, 0.5, 'No completeness data', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Regional Completeness')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'geographic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('geographic_analysis.png')
        
    def plot_prevalence_type_analysis(self):
        """Create prevalence type pattern analysis"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Prevalence Type Analysis', fontsize=16, fontweight='bold')
        
        # 1. Type distribution pie chart
        type_dist = self.stats['prevalence_types']['type_distribution']
        type_names = list(type_dist.keys())
        type_counts = list(type_dist.values())
        
        ax1.pie(type_counts, labels=type_names, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Prevalence Type Distribution')
        
        # 2. Type percentages bar chart
        type_percentages = self.stats['prevalence_types']['type_percentages']
        types = list(type_percentages.keys())
        percentages = list(type_percentages.values())
        
        ax2.bar(types, percentages, color='#2E86AB')
        ax2.set_title('Prevalence Type Percentages')
        ax2.set_ylabel('Percentage of Records')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Reliability by prevalence type
        type_reliability = self.stats['prevalence_types']['type_reliability']
        if type_reliability:
            rel_types = list(type_reliability.keys())
            rel_scores = list(type_reliability.values())
            
            ax3.bar(rel_types, rel_scores, color='#F18F01')
            ax3.set_title('Average Reliability by Prevalence Type')
            ax3.set_ylabel('Average Reliability Score')
            ax3.tick_params(axis='x', rotation=45)
        else:
            ax3.text(0.5, 0.5, 'No reliability data', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Type Reliability')
        
        # 4. Type usage comparison
        ax4.bar(types, type_counts, color='#A23B72')
        ax4.set_title('Record Count by Prevalence Type')
        ax4.set_ylabel('Number of Records')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'prevalence_type_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('prevalence_type_analysis.png')
        
    def plot_reliability_analysis(self):
        """Create reliability and validation analysis"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Reliability and Validation Analysis', fontsize=16, fontweight='bold')
        
        # 1. Detailed reliability score distribution
        reliability_dist = self.stats['data_quality']['reliability_distribution']
        score_ranges = list(reliability_dist.keys())
        score_counts = list(reliability_dist.values())
        
        ax1.bar(score_ranges, score_counts, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.set_title('Detailed Reliability Score Distribution')
        ax1.set_xlabel('Score Range')
        ax1.set_ylabel('Number of Records')
        
        # Add reliability threshold line
        ax1.axvline(x=2.5, color='red', linestyle='--', label='Fiable Threshold (≥6.0)')
        ax1.legend()
        
        # 2. Quality levels pie chart
        quality_levels = self.stats['reliability']['quality_levels']
        quality_names = ['High Quality (8-10)', 'Medium Quality (6-8)', 'Low Quality (0-6)']
        quality_counts = [quality_levels['high_quality'], quality_levels['medium_quality'], quality_levels['low_quality']]
        
        ax2.pie(quality_counts, labels=quality_names, autopct='%1.1f%%', 
                colors=['#2E86AB', '#F18F01', '#A23B72'], startangle=90)
        ax2.set_title('Data Quality Levels')
        
        # 3. Validation status analysis
        validation_dist = self.stats['data_quality']['validation_status_distribution']
        val_statuses = list(validation_dist.keys())
        val_counts = list(validation_dist.values())
        
        ax3.bar(val_statuses, val_counts, color='#F18F01')
        ax3.set_title('Validation Status Distribution')
        ax3.set_ylabel('Number of Records')
        
        # 4. Source quality comparison
        source_quality = self.stats['data_quality']['source_quality_breakdown']
        source_types = list(source_quality.keys())
        source_counts = list(source_quality.values())
        
        ax4.barh(source_types, source_counts, color='#A23B72')
        ax4.set_title('Source Quality Breakdown')
        ax4.set_xlabel('Number of Records')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'reliability_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('reliability_analysis.png')
        
    def plot_rarity_spectrum(self):
        """Create rarity spectrum and prevalence class analysis"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Rarity Spectrum Analysis', fontsize=16, fontweight='bold')
        
        # 1. Rarity spectrum pie chart
        rarity_spectrum = self.stats['rarity']['rarity_spectrum']
        rarity_levels = list(rarity_spectrum.keys())
        rarity_counts = list(rarity_spectrum.values())
        
        ax1.pie(rarity_counts, labels=rarity_levels, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Disease Rarity Spectrum')
        
        # 2. Rarity percentages bar chart
        rarity_percentages = self.stats['rarity']['rarity_percentages']
        rarity_names = list(rarity_percentages.keys())
        rarity_pcts = list(rarity_percentages.values())
        
        ax2.bar(rarity_names, rarity_pcts, color='#2E86AB')
        ax2.set_title('Rarity Level Percentages')
        ax2.set_ylabel('Percentage of Records')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Top prevalence classes
        class_dist = self.stats['rarity']['prevalence_class_distribution']
        class_names = list(class_dist.keys())[:8]  # Top 8 classes
        class_counts = list(class_dist.values())[:8]
        
        ax3.barh(class_names, class_counts, color='#F18F01')
        ax3.set_title('Top Prevalence Classes by Record Count')
        ax3.set_xlabel('Number of Records')
        
        # 4. Ultra-rare vs rare comparison
        comparison_data = [
            rarity_spectrum.get('ultra_rare', 0),
            rarity_spectrum.get('very_rare', 0),
            rarity_spectrum.get('rare', 0),
            rarity_spectrum.get('uncommon', 0)
        ]
        comparison_labels = ['Ultra-rare\n(<1/1M)', 'Very rare\n(1-9/1M)', 'Rare\n(1-9/100K)', 'Uncommon\n(>1-9/10K)']
        
        ax4.bar(comparison_labels, comparison_data, color=['#C73E1D', '#F18F01', '#2E86AB', '#A23B72'])
        ax4.set_title('Rarity Level Comparison')
        ax4.set_ylabel('Number of Records')
        ax4.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'rarity_spectrum.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('rarity_spectrum.png')
    
    def plot_prevalence_distribution(self):
        """Create THE MOST IMPORTANT prevalence value distribution analysis"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Prevalence Value Distribution Analysis - Complete Dataset', fontsize=16, fontweight='bold')
        
        # GET ALL PREVALENCE VALUES FROM COMPLETE DATASET
        print("📊 Extracting all prevalence values from complete dataset...")
        self.controller._ensure_disease2prevalence_loaded()
        
        all_prevalence_values = []
        disease_prevalence_data = []
        
        for orpha_code, disease_data in self.controller._disease2prevalence.items():
            mean_prevalence = disease_data.get('mean_value_per_million', 0.0)
            if mean_prevalence > 0:  # Only include diseases with valid prevalence estimates
                all_prevalence_values.append(mean_prevalence)
                disease_prevalence_data.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name', ''),
                    'prevalence': mean_prevalence,
                    'total_records': len(disease_data.get('prevalence_records', []))
                })
        
        print(f"📊 Analyzing {len(all_prevalence_values)} diseases with valid prevalence estimates")
        
        if not all_prevalence_values:
            print("❌ No prevalence values found!")
            return
        
        # 1. LINEAR SCALE PREVALENCE DISTRIBUTION
        ax1.hist(all_prevalence_values, bins=100, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.set_title(f'Prevalence Distribution - Linear Scale\n({len(all_prevalence_values)} diseases)')
        ax1.set_xlabel('Prevalence (per million)')
        ax1.set_ylabel('Number of Diseases')
        ax1.axvline(np.mean(all_prevalence_values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(all_prevalence_values):.1f}')
        ax1.axvline(np.median(all_prevalence_values), color='green', linestyle='--', 
                   label=f'Median: {np.median(all_prevalence_values):.1f}')
        ax1.legend()
        
        # Add key statistics
        ax1.text(0.6, 0.9, f'Min: {min(all_prevalence_values):.2f}\nMax: {max(all_prevalence_values):.1f}\nStd: {np.std(all_prevalence_values):.1f}', 
                transform=ax1.transAxes, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        # 2. LOG SCALE PREVALENCE DISTRIBUTION
        log_values = [val for val in all_prevalence_values if val > 0]  # Ensure positive for log
        ax2.hist(log_values, bins=100, color='#F18F01', alpha=0.7, edgecolor='black')
        ax2.set_xscale('log')
        ax2.set_title(f'Prevalence Distribution - Log Scale\n({len(log_values)} diseases)')
        ax2.set_xlabel('Prevalence (per million) - Log Scale')
        ax2.set_ylabel('Number of Diseases')
        ax2.axvline(np.mean(log_values), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(log_values):.1f}')
        ax2.axvline(np.median(log_values), color='green', linestyle='--', 
                   label=f'Median: {np.median(log_values):.1f}')
        ax2.legend()
        
        # 3. CUMULATIVE DISTRIBUTION
        sorted_values = np.sort(all_prevalence_values)
        y_cumulative = np.arange(1, len(sorted_values) + 1) / len(sorted_values) * 100
        
        ax3.plot(sorted_values, y_cumulative, color='#A23B72', linewidth=2)
        ax3.set_title('Cumulative Distribution of Prevalence')
        ax3.set_xlabel('Prevalence (per million)')
        ax3.set_ylabel('Percentage of Diseases (%)')
        ax3.grid(True, alpha=0.3)
        
        # Add percentile markers
        percentiles = [10, 25, 50, 75, 90]
        for p in percentiles:
            val = np.percentile(all_prevalence_values, p)
            ax3.axhline(p, color='gray', linestyle=':', alpha=0.5)
            ax3.axvline(val, color='gray', linestyle=':', alpha=0.5)
            ax3.text(val * 1.1, p + 2, f'P{p}: {val:.1f}', fontsize=8)
        
        # 4. PREVALENCE RANGES ANALYSIS
        # Define epidemiologically meaningful ranges
        ranges = {
            'Ultra-rare (<0.1)': (0, 0.1),
            'Very rare (0.1-1)': (0.1, 1),
            'Rare (1-10)': (1, 10),
            'Uncommon (10-100)': (10, 100),
            'Common (100-1000)': (100, 1000),
            'Very common (>1000)': (1000, float('inf'))
        }
        
        range_counts = {}
        for range_name, (min_val, max_val) in ranges.items():
            count = len([v for v in all_prevalence_values if min_val <= v < max_val])
            range_counts[range_name] = count
        
        range_names = list(range_counts.keys())
        range_values = list(range_counts.values())
        
        bars = ax4.bar(range_names, range_values, color=['#C73E1D', '#F18F01', '#2E86AB', '#A23B72', '#4CAF50', '#FF9800'])
        ax4.set_title('Disease Count by Prevalence Range')
        ax4.set_ylabel('Number of Diseases')
        ax4.tick_params(axis='x', rotation=45)
        
        # Add count labels on bars
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'prevalence_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('prevalence_distribution.png')
        
        # Print insights
        print(f"📈 PREVALENCE DISTRIBUTION INSIGHTS:")
        print(f"  • Total diseases analyzed: {len(all_prevalence_values)}")
        print(f"  • Prevalence range: {min(all_prevalence_values):.3f} to {max(all_prevalence_values):.1f} per million")
        print(f"  • Mean prevalence: {np.mean(all_prevalence_values):.2f} per million")
        print(f"  • Median prevalence: {np.median(all_prevalence_values):.2f} per million")
        print(f"  • Most common range: {max(range_counts, key=range_counts.get)} ({max(range_counts.values())} diseases)")
        
        # Save distribution data for further analysis
        distribution_analysis = {
            'total_diseases_analyzed': len(all_prevalence_values),
            'prevalence_statistics': {
                'min': float(min(all_prevalence_values)),
                'max': float(max(all_prevalence_values)),
                'mean': float(np.mean(all_prevalence_values)),
                'median': float(np.median(all_prevalence_values)),
                'std': float(np.std(all_prevalence_values)),
                'percentiles': {
                    'p10': float(np.percentile(all_prevalence_values, 10)),
                    'p25': float(np.percentile(all_prevalence_values, 25)),
                    'p75': float(np.percentile(all_prevalence_values, 75)),
                    'p90': float(np.percentile(all_prevalence_values, 90))
                }
            },
            'prevalence_ranges': range_counts,
            'disease_distribution': disease_prevalence_data[:100]  # Top 100 for reference
        }
        
        with open(self.output_dir / 'prevalence_distribution_analysis.json', 'w') as f:
            json.dump(distribution_analysis, f, indent=2)
        
        print(f"📊 Detailed distribution analysis saved to: prevalence_distribution_analysis.json")
        
    def create_dashboard(self):
        """Create comprehensive dashboard"""
        
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle('Prevalence Data - Comprehensive Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Key metrics (top left)
        ax1 = fig.add_subplot(gs[0, :2])
        metrics = ['Total Diseases', 'With Prevalence', 'Total Records', 'Reliable Records']
        values = [
            self.stats['basic']['total_disorders_in_system'],
            self.stats['basic']['disorders_with_prevalence'],
            self.stats['basic']['total_prevalence_records'],
            self.stats['basic']['reliable_records']
        ]
        
        bars = ax1.bar(metrics, values, color=['#2E86AB', '#F18F01', '#C73E1D', '#A23B72'])
        ax1.set_title('Key Metrics', fontweight='bold')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
        
        # 2. Disease coverage (top right)
        ax2 = fig.add_subplot(gs[0, 2:])
        coverage_data = [
            self.stats['basic']['disorders_with_prevalence'],
            self.stats['basic']['disorders_without_prevalence']
        ]
        coverage_labels = ['With Prevalence', 'Without Prevalence']
        
        ax2.pie(coverage_data, labels=coverage_labels, autopct='%1.1f%%', 
                colors=['#2E86AB', '#A23B72'], startangle=90)
        ax2.set_title('Disease Coverage', fontweight='bold')
        
        # 3. Top diseases (middle left)
        ax3 = fig.add_subplot(gs[1, :2])
        top_diseases = self.stats['diseases']['top_diseases'][:8]
        disease_names = [d['disease_name'][:25] + '...' if len(d['disease_name']) > 25 else d['disease_name'] 
                        for d in top_diseases]
        record_counts = [d['total_records'] for d in top_diseases]
        
        ax3.barh(disease_names, record_counts, color='#2E86AB')
        ax3.set_title('Top Diseases by Record Count', fontweight='bold')
        ax3.set_xlabel('Number of Records')
        
        # 4. Prevalence type distribution (middle right)
        ax4 = fig.add_subplot(gs[1, 2:])
        type_dist = self.stats['prevalence_types']['type_distribution']
        type_names = list(type_dist.keys())
        type_counts = list(type_dist.values())
        
        ax4.pie(type_counts, labels=type_names, autopct='%1.1f%%', startangle=90)
        ax4.set_title('Prevalence Type Distribution', fontweight='bold')
        
        # 5. Top regions (bottom left)
        ax5 = fig.add_subplot(gs[2, :2])
        top_regions = self.stats['geographic']['top_regions'][:8]
        region_names = [r['region'][:15] + '...' if len(r['region']) > 15 else r['region'] for r in top_regions]
        region_counts = [r['total_records'] for r in top_regions]
        
        ax5.barh(region_names, region_counts, color='#F18F01')
        ax5.set_title('Top Regions by Data Volume', fontweight='bold')
        ax5.set_xlabel('Number of Records')
        
        # 6. Reliability distribution (bottom right)
        ax6 = fig.add_subplot(gs[2, 2:])
        reliability_dist = self.stats['data_quality']['reliability_distribution']
        rel_ranges = list(reliability_dist.keys())
        rel_counts = list(reliability_dist.values())
        
        ax6.pie(rel_counts, labels=rel_ranges, autopct='%1.1f%%', startangle=90)
        ax6.set_title('Reliability Distribution', fontweight='bold')
        
        # 7. Summary statistics (bottom)
        ax7 = fig.add_subplot(gs[3, :])
        summary_text = f"""
        SUMMARY STATISTICS
        • Total Diseases: {self.stats['basic']['total_disorders_in_system']} | With Prevalence: {self.stats['basic']['disorders_with_prevalence']} ({self.stats['basic']['prevalence_coverage_percentage']}%)
        • Total Records: {self.stats['basic']['total_prevalence_records']} | Reliable: {self.stats['basic']['reliable_records']} ({self.stats['basic']['reliability_percentage']}%)
        • Mean Estimates: {self.stats['basic']['diseases_with_mean_estimates']} diseases ({self.stats['basic']['mean_estimate_coverage']}%)
        • Geographic Coverage: {self.stats['geographic']['total_regions']} regions | Worldwide: {self.stats['geographic']['worldwide_percentage']}%
        • Data Quality: {self.stats['reliability']['high_quality_percentage']}% high quality | {self.stats['reliability']['validated_percentage']}% validated
        """
        
        ax7.text(0.02, 0.5, summary_text, transform=ax7.transAxes, fontsize=12,
                verticalalignment='center', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        ax7.set_xlim(0, 1)
        ax7.set_ylim(0, 1)
        ax7.axis('off')
        
        plt.savefig(self.output_dir / 'dashboard.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('dashboard.png')
        
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        
        report = {
            'generation_date': datetime.now().isoformat(),
            'basic_statistics': self.stats['basic'],
            'data_quality_analysis': self.stats['data_quality'],
            'disease_analysis': self.stats['diseases'],
            'geographic_analysis': self.stats['geographic'],
            'prevalence_type_analysis': self.stats['prevalence_types'],
            'reliability_analysis': self.stats['reliability'],
            'rarity_analysis': self.stats['rarity'],
            'advanced_analysis': self.stats['advanced'],
            'plots_generated': self.plots_created
        }
        
        # Save JSON report
        with open(self.output_dir / 'prevalence_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate markdown summary
        self.generate_markdown_summary(report)
        
        print(f"📄 Summary report saved to: {self.output_dir}/prevalence_statistics.json")
        print(f"📄 Markdown summary saved to: {self.output_dir}/prevalence_summary.md")
        
    def generate_markdown_summary(self, report):
        """Generate markdown summary report"""
        
        markdown_content = f"""# Prevalence Data Analysis Summary

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Key Findings

### Disease Coverage
- **Total Diseases in System**: {report['basic_statistics']['total_disorders_in_system']:,}
- **Diseases with Prevalence Data**: {report['basic_statistics']['disorders_with_prevalence']:,} ({report['basic_statistics']['prevalence_coverage_percentage']}%)
- **Diseases with Mean Estimates**: {report['basic_statistics']['diseases_with_mean_estimates']:,} ({report['basic_statistics']['mean_estimate_coverage']}%)

### Data Volume and Quality
- **Total Prevalence Records**: {report['basic_statistics']['total_prevalence_records']:,}
- **Reliable Records (≥6.0 score)**: {report['basic_statistics']['reliable_records']:,} ({report['basic_statistics']['reliability_percentage']}%)
- **High Quality Records (8-10 score)**: {report['reliability_analysis']['high_quality_percentage']}%
- **Validated Records**: {report['reliability_analysis']['validated_percentage']}%
- **PMID-Referenced Records**: {report['reliability_analysis']['pmid_percentage']}%

### Geographic Coverage
- **Total Geographic Regions**: {report['geographic_analysis']['total_regions']}
- **Worldwide Records**: {report['geographic_analysis']['worldwide_records']:,} ({report['geographic_analysis']['worldwide_percentage']}%)
- **Diseases with Multi-Regional Data**: {report['advanced_analysis']['multi_region_diseases_count']:,}

### Prevalence Types
- **Most Common Type**: {report['prevalence_type_analysis']['most_common_type'][0]} ({report['prevalence_type_analysis']['most_common_type'][1]:,} records)
- **Total Type Categories**: {report['prevalence_type_analysis']['total_types']}

### Rarity Spectrum
- **Ultra-rare Diseases**: {report['rarity_analysis']['ultra_rare_percentage']}% (<1 per million)
- **Very Rare Diseases**: {report['rarity_analysis']['very_rare_percentage']}% (1-9 per million)
- **Rare Diseases**: {report['rarity_analysis']['rare_percentage']}% (1-9 per 100,000)

### Top Diseases by Prevalence Data Volume
"""
        
        for i, disease in enumerate(report['disease_analysis']['top_diseases'][:10], 1):
            markdown_content += f"{i}. **{disease['disease_name']}** - {disease['total_records']} records"
            if disease['mean_value_per_million'] > 0:
                markdown_content += f" (Mean: {disease['mean_value_per_million']:.1f} per million)"
            markdown_content += "\n"
        
        markdown_content += f"""
### Top Geographic Regions by Data Volume
"""
        
        for i, region in enumerate(report['geographic_analysis']['top_regions'][:10], 1):
            markdown_content += f"{i}. **{region['region']}** - {region['total_records']:,} records ({region['diseases']} diseases)\n"
        
        markdown_content += f"""
### Data Quality Insights
- **High Quality Data**: {report['reliability_analysis']['high_quality_percentage']}% of records have reliability scores ≥8.0
- **Source Distribution**: {report['data_quality_analysis']['source_quality_breakdown']}
- **Consensus Analysis**: {report['advanced_analysis']['consensus_analysis']['consensus_percentage']}% of multi-record diseases show consensus

### Data Gaps Analysis
- **Diseases without Worldwide Data**: {report['advanced_analysis']['coverage_completeness']['worldwide_gap_percentage']}%
- **Diseases without Reliable Data**: {report['advanced_analysis']['coverage_completeness']['reliability_gap_percentage']}%
- **Diseases without Mean Estimates**: {report['advanced_analysis']['coverage_completeness']['mean_estimate_gap_percentage']}%

### Data Density
- **Average Records per Disease**: {report['basic_statistics']['average_records_per_disease']}
- **Max Records for Single Disease**: {report['disease_analysis']['record_distribution']['max']}
- **Median Records per Disease**: {report['disease_analysis']['record_distribution']['median']}

### Generated Visualizations
"""
        
        for plot in report['plots_generated']:
            markdown_content += f"- {plot}\n"
        
        markdown_content += f"""
## Analysis Notes
- Prevalence coverage reaches {report['basic_statistics']['prevalence_coverage_percentage']}% of diseases in the system
- {report['basic_statistics']['reliability_percentage']}% of prevalence records meet reliability threshold (≥6.0 score)
- Data spans {report['geographic_analysis']['total_regions']} geographic regions with strong worldwide representation
- {report['prevalence_type_analysis']['total_types']} different prevalence types provide comprehensive epidemiological coverage
- Mean estimate calculation provides consolidated prevalence values for {report['basic_statistics']['mean_estimate_coverage']}% of diseases

---
*This report was generated automatically by the Prevalence Statistics system.*
"""
        
        with open(self.output_dir / 'prevalence_summary.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)


def main():
    """Run prevalence statistics generation"""
    
    # Check if data is available
    controller = ProcessedPrevalenceClient()
    if not controller.is_data_available():
        print("❌ Prevalence data not available. Please run the following first:")
        print("1. python etl/03_process/orpha/orphadata/process_orpha_prevalence.py")
        return
    
    # Generate statistics
    stats = PrevalenceStatistics()
    stats.generate_all_statistics()
    
    print("🎉 Prevalence statistics generation complete!")


if __name__ == "__main__":
    main() 