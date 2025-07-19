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
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from etl.drug_controller import ProcessedDrugClient


class DrugStatistics:
    """Generate comprehensive statistics and visualizations for drug data"""
    
    def __init__(self, output_dir="results/stats/drug"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize controller
        self.controller = ProcessedDrugClient()
        self.controller.preload_all()
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Initialize data containers
        self.stats = {}
        self.plots_created = []
        
    def generate_all_statistics(self):
        """Generate all drug statistics and visualizations"""
        
        print("🔍 Generating Drug Statistics...")
        
        # Basic statistics
        self.generate_basic_stats()
        
        # Disease analysis
        self.analyze_diseases()
        
        # Drug analysis  
        self.analyze_drugs()
        
        # Manufacturer analysis
        self.analyze_manufacturers()
        
        # Regulatory status analysis
        self.analyze_regulatory_status()
        
        # Regional analysis
        self.analyze_regions()
        
        # Generate summary report
        self.generate_summary_report()
        
        # Create plots
        self.create_all_plots()
        
        print(f"✅ Statistics generation complete!")
        print(f"📊 Generated {len(self.plots_created)} plots")
        print(f"📁 Output directory: {self.output_dir}")
        
    def generate_basic_stats(self):
        """Generate basic statistics"""
        
        stats = self.controller.get_statistics()
        
        self.stats['basic'] = {
            'total_diseases_in_system': stats.get('total_diseases_processed', 0),
            'diseases_with_drugs': stats.get('diseases_with_drugs', 0),
            'diseases_without_drugs': stats.get('total_diseases_processed', 0) - stats.get('diseases_with_drugs', 0),
            'drug_coverage_percentage': round((stats.get('diseases_with_drugs', 0) / stats.get('total_diseases_processed', 1)) * 100, 2),
            'total_unique_drugs': stats.get('total_unique_drugs', 0),
            'average_drugs_per_disease': 0
        }
        
        if self.stats['basic']['diseases_with_drugs'] > 0:
            self.stats['basic']['average_drugs_per_disease'] = round(
                self.stats['basic']['total_unique_drugs'] / self.stats['basic']['diseases_with_drugs'], 2
            )
        
        print(f"📊 Basic Stats: {self.stats['basic']['diseases_with_drugs']} diseases have drugs ({self.stats['basic']['drug_coverage_percentage']}%)")
        
    def analyze_diseases(self):
        """Analyze disease patterns and distributions"""
        
        # Get diseases with most drugs
        top_diseases = self.controller.get_diseases_with_most_drugs(50)
        
        # Disease drug distribution
        drug_counts = [d['drugs_count'] for d in top_diseases]
        
        self.stats['diseases'] = {
            'top_diseases': top_diseases[:20],  # Top 20 for detailed analysis
            'drug_distribution': {
                'mean': np.mean(drug_counts) if drug_counts else 0,
                'median': np.median(drug_counts) if drug_counts else 0,
                'std': np.std(drug_counts) if drug_counts else 0,
                'max': max(drug_counts) if drug_counts else 0,
                'min': min(drug_counts) if drug_counts else 0
            },
            'diseases_by_drug_count': dict(Counter(drug_counts))
        }
        
        print(f"🧬 Disease Analysis: Top disease has {self.stats['diseases']['drug_distribution']['max']} drugs")
        
    def analyze_drugs(self):
        """Analyze drug patterns"""
        
        # Get approved vs investigational drugs
        approved_drugs = self.controller.search_approved_drugs()
        investigational_drugs = self.controller.search_investigational_drugs()
        
        # Drug status analysis
        status_counts = {
            'Medicinal product': len(approved_drugs),
            'Investigational': len(investigational_drugs)
        }
        
        # Get all drugs for detailed analysis
        self.controller._ensure_drugs2diseases_loaded()
        all_drugs = list(self.controller._drugs2diseases.values())
        
        # Status distribution
        status_distribution = defaultdict(int)
        substance_count = 0
        regulatory_count = 0
        
        for drug in all_drugs:
            status = drug.get('status', 'Unknown')
            status_distribution[status] += 1
            
            if drug.get('substance_id'):
                substance_count += 1
            if drug.get('regulatory_id'):
                regulatory_count += 1
        
        self.stats['drugs'] = {
            'status_distribution': dict(status_distribution),
            'approved_drugs': len(approved_drugs),
            'investigational_drugs': len(investigational_drugs),
            'drugs_with_substance_id': substance_count,
            'drugs_with_regulatory_id': regulatory_count,
            'substance_id_percentage': round((substance_count / len(all_drugs)) * 100, 2) if all_drugs else 0,
            'regulatory_id_percentage': round((regulatory_count / len(all_drugs)) * 100, 2) if all_drugs else 0
        }
        
        print(f"💊 Drug Analysis: {len(approved_drugs)} approved, {len(investigational_drugs)} investigational")
        
    def analyze_manufacturers(self):
        """Analyze manufacturer patterns"""
        
        # Get manufacturers with most drugs
        top_manufacturers = self.controller.get_manufacturers_with_most_drugs(20)
        
        # Manufacturer distribution
        manufacturer_counts = [m['drug_count'] for m in top_manufacturers]
        
        self.stats['manufacturers'] = {
            'top_manufacturers': top_manufacturers[:15],  # Top 15 for detailed analysis
            'total_manufacturers': len(top_manufacturers),
            'manufacturer_distribution': {
                'mean': np.mean(manufacturer_counts) if manufacturer_counts else 0,
                'median': np.median(manufacturer_counts) if manufacturer_counts else 0,
                'max': max(manufacturer_counts) if manufacturer_counts else 0,
                'min': min(manufacturer_counts) if manufacturer_counts else 0
            }
        }
        
        print(f"🏭 Manufacturer Analysis: {len(top_manufacturers)} manufacturers identified")
        
    def analyze_regulatory_status(self):
        """Analyze regulatory status patterns"""
        
        # Get status distribution
        self.controller._ensure_drugs2diseases_loaded()
        all_drugs = list(self.controller._drugs2diseases.values())
        
        status_counts = defaultdict(int)
        region_counts = defaultdict(int)
        
        for drug in all_drugs:
            status = drug.get('status', 'Unknown')
            status_counts[status] += 1
            
            # Count regions
            regions = drug.get('regions', [])
            for region in regions:
                region_counts[region] += 1
        
        self.stats['regulatory'] = {
            'status_distribution': dict(sorted(status_counts.items(), key=lambda x: x[1], reverse=True)),
            'region_distribution': dict(sorted(region_counts.items(), key=lambda x: x[1], reverse=True)),
            'total_status_types': len(status_counts),
            'total_regions': len(region_counts)
        }
        
        print(f"📋 Regulatory Analysis: {len(status_counts)} status types, {len(region_counts)} regions")
        
    def analyze_regions(self):
        """Analyze regional distribution of drugs"""
        
        # Get regional distribution
        eu_drugs = self.controller.search_drugs_by_region('EU')
        us_drugs = self.controller.search_drugs_by_region('US')
        
        regional_stats = {
            'EU': len(eu_drugs),
            'US': len(us_drugs),
            'total_drugs': len(self.controller._drugs2diseases) if self.controller._drugs2diseases else 0
        }
        
        self.stats['regions'] = {
            'regional_distribution': regional_stats,
            'eu_percentage': round((regional_stats['EU'] / regional_stats['total_drugs']) * 100, 2) if regional_stats['total_drugs'] > 0 else 0,
            'us_percentage': round((regional_stats['US'] / regional_stats['total_drugs']) * 100, 2) if regional_stats['total_drugs'] > 0 else 0
        }
        
        print(f"🌍 Regional Analysis: {regional_stats['EU']} EU drugs, {regional_stats['US']} US drugs")
        
    def create_all_plots(self):
        """Create all visualization plots"""
        
        try:
            # 1. Basic statistics overview
            self.plot_basic_overview()
            print("✅ Basic overview plot created")
        except Exception as e:
            print(f"❌ Error creating basic overview: {e}")
        
        try:
            # 2. Disease distribution plots
            self.plot_disease_distribution()
            print("✅ Disease distribution plot created")
        except Exception as e:
            print(f"❌ Error creating disease distribution: {e}")
        
        try:
            # 3. Drug characteristics plots
            self.plot_drug_characteristics()
            print("✅ Drug characteristics plot created")
        except Exception as e:
            print(f"❌ Error creating drug characteristics: {e}")
        
        try:
            # 4. Manufacturer analysis
            if self.stats['manufacturers']['total_manufacturers'] > 0:
                self.plot_manufacturer_analysis()
                print("✅ Manufacturer analysis plot created")
            else:
                print("⏭️ Skipping manufacturer analysis (no manufacturer data)")
        except Exception as e:
            print(f"❌ Error creating manufacturer analysis: {e}")
        
        try:
            # 5. Regulatory status plots
            self.plot_regulatory_status()
            print("✅ Regulatory status plot created")
        except Exception as e:
            print(f"❌ Error creating regulatory status: {e}")
        
        try:
            # 6. Top diseases analysis
            self.plot_top_diseases()
            print("✅ Top diseases plot created")
        except Exception as e:
            print(f"❌ Error creating top diseases: {e}")
        
        try:
            # 7. Regional distribution
            self.plot_regional_distribution()
            print("✅ Regional distribution plot created")
        except Exception as e:
            print(f"❌ Error creating regional distribution: {e}")
        
        try:
            # 8. Comprehensive dashboard
            self.create_dashboard()
            print("✅ Dashboard created")
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")
        
    def plot_basic_overview(self):
        """Create basic statistics overview plot"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Drug Data - Basic Statistics Overview', fontsize=16, fontweight='bold')
        
        # 1. Disease coverage pie chart
        coverage_data = [
            self.stats['basic']['diseases_with_drugs'],
            self.stats['basic']['diseases_without_drugs']
        ]
        coverage_labels = ['Diseases with Drugs', 'Diseases without Drugs']
        colors = ['#2E86AB', '#A23B72']
        
        ax1.pie(coverage_data, labels=coverage_labels, autopct='%1.1f%%', colors=colors, startangle=90)
        ax1.set_title('Disease Coverage')
        
        # 2. Basic metrics bar chart
        metrics = ['Total Diseases', 'Diseases with Drugs', 'Total Unique Drugs']
        values = [
            self.stats['basic']['total_diseases_in_system'],
            self.stats['basic']['diseases_with_drugs'],
            self.stats['basic']['total_unique_drugs']
        ]
        
        bars = ax2.bar(metrics, values, color=['#F18F01', '#C73E1D', '#2E86AB'])
        ax2.set_title('Key Metrics')
        ax2.set_ylabel('Count')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 3. Drug status distribution
        if self.stats['drugs']['status_distribution']:
            # Filter out None/empty keys and values
            valid_status_items = [(k, v) for k, v in self.stats['drugs']['status_distribution'].items() 
                                if k is not None and k != '' and v > 0]
            
            if valid_status_items:
                status_data = [item[1] for item in valid_status_items]
                status_labels = [item[0] for item in valid_status_items]
                
                ax3.pie(status_data, labels=status_labels, autopct='%1.1f%%', startangle=90)
                ax3.set_title('Drug Status Distribution')
            else:
                ax3.text(0.5, 0.5, 'No status data available', ha='center', va='center', transform=ax3.transAxes)
                ax3.set_title('Drug Status Distribution')
        else:
            ax3.text(0.5, 0.5, 'No status data available', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Drug Status Distribution')
        
        # 4. ID coverage
        id_metrics = ['Substance ID', 'Regulatory ID']
        id_values = [
            self.stats['drugs']['substance_id_percentage'],
            self.stats['drugs']['regulatory_id_percentage']
        ]
        
        ax4.bar(id_metrics, id_values, color=['#A23B72', '#F18F01'])
        ax4.set_title('Drug ID Coverage (%)')
        ax4.set_ylabel('Percentage')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'basic_overview.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('basic_overview.png')
        
    def plot_disease_distribution(self):
        """Create disease distribution plots"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Disease Analysis - Drug Distribution', fontsize=16, fontweight='bold')
        
        # 1. Histogram of drugs per disease
        top_diseases = self.stats['diseases']['top_diseases']
        drug_counts = [d['drugs_count'] for d in top_diseases]
        
        ax1.hist(drug_counts, bins=20, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax1.set_title('Distribution of Drugs per Disease')
        ax1.set_xlabel('Number of Drugs')
        ax1.set_ylabel('Number of Diseases')
        ax1.axvline(np.mean(drug_counts), color='red', linestyle='--', label=f'Mean: {np.mean(drug_counts):.1f}')
        ax1.legend()
        
        # 2. Cumulative distribution
        sorted_counts = sorted(drug_counts, reverse=True)
        cumulative_pct = np.cumsum(sorted_counts) / np.sum(sorted_counts) * 100
        
        ax2.plot(range(1, len(sorted_counts) + 1), cumulative_pct, marker='o', color='#C73E1D')
        ax2.set_title('Cumulative Drug Distribution')
        ax2.set_xlabel('Disease Rank')
        ax2.set_ylabel('Cumulative % of Drugs')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'disease_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('disease_distribution.png')
        
    def plot_drug_characteristics(self):
        """Create drug characteristics plots"""
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Drug Characteristics', fontsize=16, fontweight='bold')
        
        # 1. Status distribution
        status_data = self.stats['drugs']['status_distribution']
        # Filter out None keys and take top 8 statuses
        valid_statuses = [(k, v) for k, v in status_data.items() if k is not None and k != '']
        valid_statuses = sorted(valid_statuses, key=lambda x: x[1], reverse=True)[:8]
        status_names = [s[0] for s in valid_statuses]
        status_counts = [s[1] for s in valid_statuses]
        
        if status_names and status_counts:
            ax1.bar(status_names, status_counts, color=['#2E86AB', '#F18F01', '#C73E1D', '#A23B72'])
        ax1.set_title('Drug Status Distribution')
        ax1.set_ylabel('Number of Drugs')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Approved vs Investigational
        approved_vs_investigational = [
            self.stats['drugs']['approved_drugs'],
            self.stats['drugs']['investigational_drugs']
        ]
        labels = ['Approved', 'Investigational']
        
        ax2.pie(approved_vs_investigational, labels=labels, autopct='%1.1f%%', 
                colors=['#2E86AB', '#F18F01'], startangle=90)
        ax2.set_title('Approved vs Investigational Drugs')
        
        # 3. ID coverage
        id_metrics = ['With Substance ID', 'With Regulatory ID']
        id_counts = [
            self.stats['drugs']['drugs_with_substance_id'],
            self.stats['drugs']['drugs_with_regulatory_id']
        ]
        
        ax3.bar(id_metrics, id_counts, color=['#A23B72', '#C73E1D'])
        ax3.set_title('Drug ID Coverage')
        ax3.set_ylabel('Number of Drugs')
        
        # 4. Regional distribution
        region_data = self.stats['regulatory']['region_distribution']
        # Filter out None keys and take top 8 regions
        valid_regions = [(k, v) for k, v in region_data.items() if k is not None and k != '']
        valid_regions = sorted(valid_regions, key=lambda x: x[1], reverse=True)[:8]
        top_regions = [r[0] for r in valid_regions]
        region_counts = [r[1] for r in valid_regions]
        
        if top_regions and region_counts:
            ax4.barh(top_regions, region_counts, color='#F18F01')
        ax4.set_title('Regional Distribution')
        ax4.set_xlabel('Number of Drugs')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'drug_characteristics.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('drug_characteristics.png')
        
    def plot_manufacturer_analysis(self):
        """Create manufacturer analysis plots"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Manufacturer Analysis', fontsize=16, fontweight='bold')
        
        # 1. Top manufacturers by drug count
        top_manufacturers = self.stats['manufacturers']['top_manufacturers'][:10]
        manufacturer_names = [m['manufacturer'] for m in top_manufacturers]
        drug_counts = [m['drug_count'] for m in top_manufacturers]
        
        # Truncate long names
        manufacturer_names = [name[:30] + '...' if len(name) > 30 else name for name in manufacturer_names]
        
        ax1.barh(manufacturer_names, drug_counts, color='#2E86AB')
        ax1.set_title('Top 10 Manufacturers by Drug Count')
        ax1.set_xlabel('Number of Drugs')
        
        # 2. Manufacturer drug distribution
        all_counts = [m['drug_count'] for m in self.stats['manufacturers']['top_manufacturers']]
        
        ax2.hist(all_counts, bins=15, color='#A23B72', alpha=0.7, edgecolor='black')
        ax2.set_title('Distribution of Drugs per Manufacturer')
        ax2.set_xlabel('Number of Drugs')
        ax2.set_ylabel('Number of Manufacturers')
        ax2.axvline(np.mean(all_counts), color='red', linestyle='--', label=f'Mean: {np.mean(all_counts):.1f}')
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'manufacturer_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('manufacturer_analysis.png')
        
    def plot_regulatory_status(self):
        """Create regulatory status plots"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Regulatory Status Analysis', fontsize=16, fontweight='bold')
        
        # 1. Status distribution
        status_data = self.stats['regulatory']['status_distribution']
        # Filter out None keys and take top 10 statuses
        valid_statuses = [(k, v) for k, v in status_data.items() if k is not None and k != '']
        valid_statuses = sorted(valid_statuses, key=lambda x: x[1], reverse=True)[:10]
        top_statuses = [s[0] for s in valid_statuses]
        status_counts = [s[1] for s in valid_statuses]
        
        if top_statuses and status_counts:
            ax1.bar(top_statuses, status_counts, color='#C73E1D')
        ax1.set_title('Drug Status Distribution')
        ax1.set_ylabel('Number of Drugs')
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Regional coverage
        region_data = self.stats['regions']['regional_distribution']
        regions = ['EU', 'US', 'Other']
        region_counts = [
            region_data['EU'],
            region_data['US'],
            max(0, region_data['total_drugs'] - region_data['EU'] - region_data['US'])
        ]
        
        # Only create pie chart if we have valid data
        if sum(region_counts) > 0 and all(count >= 0 for count in region_counts):
            ax2.pie(region_counts, labels=regions, autopct='%1.1f%%', 
                    colors=['#2E86AB', '#F18F01', '#A23B72'], startangle=90)
            ax2.set_title('Regional Coverage')
        else:
            ax2.text(0.5, 0.5, 'No regional data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Regional Coverage')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'regulatory_status.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('regulatory_status.png')
        
    def plot_top_diseases(self):
        """Create top diseases analysis plots"""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        fig.suptitle('Top Diseases by Drug Activity', fontsize=16, fontweight='bold')
        
        # 1. Top 15 diseases by drug count
        top_diseases = self.stats['diseases']['top_diseases'][:15]
        disease_names = [d['disease_name'] for d in top_diseases]
        drug_counts = [d['drugs_count'] for d in top_diseases]
        
        # Truncate long names
        disease_names = [name[:40] + '...' if len(name) > 40 else name for name in disease_names]
        
        bars = ax1.barh(disease_names, drug_counts, color='#2E86AB')
        ax1.set_title('Top 15 Diseases by Number of Drugs')
        ax1.set_xlabel('Number of Drugs')
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax1.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                    f'{int(width)}', ha='left', va='center')
        
        # 2. Drug count distribution ranges
        drug_ranges = {
            '1 drug': len([d for d in top_diseases if d['drugs_count'] == 1]),
            '2-5 drugs': len([d for d in top_diseases if 2 <= d['drugs_count'] <= 5]),
            '6-10 drugs': len([d for d in top_diseases if 6 <= d['drugs_count'] <= 10]),
            '11-20 drugs': len([d for d in top_diseases if 11 <= d['drugs_count'] <= 20]),
            '21+ drugs': len([d for d in top_diseases if d['drugs_count'] > 20])
        }
        
        ax2.bar(drug_ranges.keys(), drug_ranges.values(), color='#A23B72')
        ax2.set_title('Distribution of Diseases by Drug Count Ranges')
        ax2.set_ylabel('Number of Diseases')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'top_diseases.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('top_diseases.png')
        
    def plot_regional_distribution(self):
        """Create regional distribution plots"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Regional Distribution of Drugs', fontsize=16, fontweight='bold')
        
        # 1. EU vs US vs Other
        region_data = self.stats['regions']['regional_distribution']
        regions = ['EU', 'US', 'Other']
        region_counts = [
            region_data['EU'],
            region_data['US'],
            max(0, region_data['total_drugs'] - region_data['EU'] - region_data['US'])
        ]
        
        # Only create pie chart if we have valid data
        if sum(region_counts) > 0 and all(count >= 0 for count in region_counts):
            ax1.pie(region_counts, labels=regions, autopct='%1.1f%%', 
                    colors=['#2E86AB', '#F18F01', '#A23B72'], startangle=90)
            ax1.set_title('Drug Distribution by Region')
        else:
            ax1.text(0.5, 0.5, 'No regional data available', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Drug Distribution by Region')
        
        # 2. Regional coverage percentages
        coverage_data = [
            self.stats['regions']['eu_percentage'],
            self.stats['regions']['us_percentage']
        ]
        coverage_labels = ['EU Coverage', 'US Coverage']
        
        ax2.bar(coverage_labels, coverage_data, color=['#2E86AB', '#F18F01'])
        ax2.set_title('Regional Coverage Percentages')
        ax2.set_ylabel('Percentage of Drugs')
        
        # Add value labels
        for i, v in enumerate(coverage_data):
            ax2.text(i, v + 0.5, f'{v:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'regional_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        self.plots_created.append('regional_distribution.png')
        
    def create_dashboard(self):
        """Create comprehensive dashboard"""
        
        fig = plt.figure(figsize=(20, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle('Drug Data - Comprehensive Dashboard', fontsize=20, fontweight='bold', y=0.98)
        
        # 1. Basic metrics (top left)
        ax1 = fig.add_subplot(gs[0, :2])
        metrics = ['Total Diseases', 'With Drugs', 'Total Drugs', 'Manufacturers']
        values = [
            self.stats['basic']['total_diseases_in_system'],
            self.stats['basic']['diseases_with_drugs'],
            self.stats['basic']['total_unique_drugs'],
            self.stats['manufacturers']['total_manufacturers']
        ]
        
        bars = ax1.bar(metrics, values, color=['#2E86AB', '#F18F01', '#C73E1D', '#A23B72'])
        ax1.set_title('Key Metrics', fontweight='bold')
        ax1.set_ylabel('Count')
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        # 2. Disease coverage (top right)
        ax2 = fig.add_subplot(gs[0, 2:])
        coverage_data = [
            self.stats['basic']['diseases_with_drugs'],
            self.stats['basic']['diseases_without_drugs']
        ]
        coverage_labels = ['With Drugs', 'Without Drugs']
        
        ax2.pie(coverage_data, labels=coverage_labels, autopct='%1.1f%%', 
                colors=['#2E86AB', '#A23B72'], startangle=90)
        ax2.set_title('Disease Coverage', fontweight='bold')
        
        # 3. Top diseases (middle left)
        ax3 = fig.add_subplot(gs[1, :2])
        top_diseases = self.stats['diseases']['top_diseases'][:8]
        disease_names = [d['disease_name'][:25] + '...' if len(d['disease_name']) > 25 else d['disease_name'] for d in top_diseases]
        drug_counts = [d['drugs_count'] for d in top_diseases]
        
        ax3.barh(disease_names, drug_counts, color='#2E86AB')
        ax3.set_title('Top Diseases by Drug Count', fontweight='bold')
        ax3.set_xlabel('Number of Drugs')
        
        # 4. Drug status (middle right)
        ax4 = fig.add_subplot(gs[1, 2:])
        status_data = self.stats['drugs']['status_distribution']
        
        # Filter out None/empty keys and values
        valid_status_items = [(k, v) for k, v in status_data.items() 
                            if k is not None and k != '' and v > 0][:6]
        
        if valid_status_items:
            status_counts = [item[1] for item in valid_status_items]
            top_statuses = [item[0] for item in valid_status_items]
            ax4.pie(status_counts, labels=top_statuses, autopct='%1.1f%%', startangle=90)
        else:
            ax4.text(0.5, 0.5, 'No status data', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Drug Status Distribution', fontweight='bold')
        
        # 5. Top manufacturers (bottom left)
        ax5 = fig.add_subplot(gs[2, :2])
        top_manufacturers = self.stats['manufacturers']['top_manufacturers'][:8]
        manufacturer_names = [m['manufacturer'][:20] + '...' if len(m['manufacturer']) > 20 else m['manufacturer'] for m in top_manufacturers]
        manufacturer_counts = [m['drug_count'] for m in top_manufacturers]
        
        ax5.barh(manufacturer_names, manufacturer_counts, color='#F18F01')
        ax5.set_title('Top Manufacturers', fontweight='bold')
        ax5.set_xlabel('Number of Drugs')
        
        # 6. Regional distribution (bottom right)
        ax6 = fig.add_subplot(gs[2, 2:])
        region_data = self.stats['regions']['regional_distribution']
        regions = ['EU', 'US', 'Other']
        region_counts = [
            region_data['EU'],
            region_data['US'],
            max(0, region_data['total_drugs'] - region_data['EU'] - region_data['US'])
        ]
        
        # Only create pie chart if we have valid data
        if sum(region_counts) > 0 and all(count >= 0 for count in region_counts):
            ax6.pie(region_counts, labels=regions, autopct='%1.1f%%', 
                    colors=['#2E86AB', '#F18F01', '#A23B72'], startangle=90)
        else:
            ax6.text(0.5, 0.5, 'No regional data', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Regional Distribution', fontweight='bold')
        
        # 7. Summary statistics (bottom)
        ax7 = fig.add_subplot(gs[3, :])
        summary_text = f"""
        SUMMARY STATISTICS
        • Total Diseases: {self.stats['basic']['total_diseases_in_system']} | With Drugs: {self.stats['basic']['diseases_with_drugs']} ({self.stats['basic']['drug_coverage_percentage']}%)
        • Total Unique Drugs: {self.stats['basic']['total_unique_drugs']} | Average per Disease: {self.stats['basic']['average_drugs_per_disease']}
        • Approved Drugs: {self.stats['drugs']['approved_drugs']} | Investigational: {self.stats['drugs']['investigational_drugs']}
        • Manufacturers: {self.stats['manufacturers']['total_manufacturers']} | Status Types: {self.stats['regulatory']['total_status_types']}
        • EU Coverage: {self.stats['regions']['eu_percentage']}% | US Coverage: {self.stats['regions']['us_percentage']}%
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
            'disease_analysis': self.stats['diseases'],
            'drug_analysis': self.stats['drugs'],
            'manufacturer_analysis': self.stats['manufacturers'],
            'regulatory_analysis': self.stats['regulatory'],
            'regional_analysis': self.stats['regions'],
            'plots_generated': self.plots_created
        }
        
        # Save JSON report
        with open(self.output_dir / 'drug_statistics.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Generate markdown summary
        self.generate_markdown_summary(report)
        
        print(f"📄 Summary report saved to: {self.output_dir}/drug_statistics.json")
        print(f"📄 Markdown summary saved to: {self.output_dir}/drug_summary.md")
        
    def generate_markdown_summary(self, report):
        """Generate markdown summary report"""
        
        markdown_content = f"""# Drug Data Analysis Summary

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Key Findings

### Disease Coverage
- **Total Diseases**: {report['basic_statistics']['total_diseases_in_system']}
- **Diseases with Drugs**: {report['basic_statistics']['diseases_with_drugs']} ({report['basic_statistics']['drug_coverage_percentage']}%)
- **Diseases without Drugs**: {report['basic_statistics']['diseases_without_drugs']}

### Drug Portfolio
- **Total Unique Drugs**: {report['basic_statistics']['total_unique_drugs']}
- **Average Drugs per Disease**: {report['basic_statistics']['average_drugs_per_disease']}
- **Approved Drugs**: {report['drug_analysis']['approved_drugs']}
- **Investigational Drugs**: {report['drug_analysis']['investigational_drugs']}

### Top Diseases by Drug Count
"""
        
        for i, disease in enumerate(report['disease_analysis']['top_diseases'][:10], 1):
            markdown_content += f"{i}. **{disease['disease_name']}** - {disease['drugs_count']} drugs\n"
        
        markdown_content += f"""
### Manufacturer Insights
- **Total Manufacturers**: {report['manufacturer_analysis']['total_manufacturers']}"""
        
        if report['manufacturer_analysis']['top_manufacturers']:
            markdown_content += f"- **Top Manufacturer**: {report['manufacturer_analysis']['top_manufacturers'][0]['manufacturer']} ({report['manufacturer_analysis']['top_manufacturers'][0]['drug_count']} drugs)\n"
        else:
            markdown_content += f"- **Top Manufacturer**: No manufacturer data available\n"
        
        markdown_content += f"""

### Regional Distribution
- **EU Coverage**: {report['regional_analysis']['eu_percentage']}%
- **US Coverage**: {report['regional_analysis']['us_percentage']}%

### Data Quality
- **Drugs with Substance ID**: {report['drug_analysis']['substance_id_percentage']}%
- **Drugs with Regulatory ID**: {report['drug_analysis']['regulatory_id_percentage']}%

### Generated Visualizations
"""
        
        for plot in report['plots_generated']:
            markdown_content += f"- {plot}\n"
        
        markdown_content += f"""
## Analysis Notes
- Drug coverage is {report['basic_statistics']['drug_coverage_percentage']}% across rare diseases
- Top disease has {report['disease_analysis']['drug_distribution']['max']} drugs
- {report['regulatory_analysis']['total_status_types']} different regulatory status types identified
- Analysis includes {report['regional_analysis']['regional_distribution']['total_drugs']} total drug records

---
*This report was generated automatically by the Drug Statistics system.*
"""
        
        with open(self.output_dir / 'drug_summary.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)


def main():
    """Run drug statistics generation"""
    
    # Check if data is available
    controller = ProcessedDrugClient()
    if not controller.is_data_available():
        print("❌ Drug data not available. Please run the following first:")
        print("1. python etl/process_drug_data.py")
        print("2. python etl/aggregate_drug_data.py")
        return
    
    # Generate statistics
    stats = DrugStatistics()
    stats.generate_all_statistics()
    
    print("🎉 Drug statistics generation complete!")


if __name__ == "__main__":
    main() 