# Task 3: Genes Statistical Analysis & Visualization Generation

## 📋 Executive Overview

Task 3 focuses on generating comprehensive statistical analysis and publication-ready visualizations for the genes ETL system. This task will leverage both the ProcessedGeneClient and CuratedGeneClient to analyze the complete genetic landscape of rare diseases, from the full 4,078 disease dataset to the curated 549 metabolic diseases subset.

**Key Deliverables:**
- Comprehensive statistical analysis script
- Multiple publication-ready visualizations
- Both comprehensive (all diseases) and subset-specific analysis
- Detailed analytical reports and metadata
- Performance-optimized analysis pipeline

## 🎯 Success Criteria

- **Comprehensive Analysis:** Generate statistics for both processed (4,078 diseases) and curated (549 diseases) datasets
- **Publication-Ready Visualizations:** Create 8+ professional charts and graphs
- **Research Insights:** Identify key patterns, gaps, and research opportunities
- **Performance Excellence:** Complete analysis in <30 seconds with efficient data processing
- **Dual Output Structure:** Results for both all disease instances and metabolic subset

## 📊 Data Sources and Clients

### Primary Data Sources
```
Processed Data (Complete Dataset):
├── data/03_processed/orpha/orphadata/orpha_genes/
│   ├── disease2genes.json              # 4,078 diseases, 8.5MB
│   ├── gene_instances.json             # 3.2MB gene records
│   ├── gene_association_instances.json # 8.0MB association records
│   ├── gene2diseases.json              # 5.5MB reverse mapping
│   ├── orpha_index.json                # 664KB disease index
│   ├── external_references/            # HGNC, Ensembl, etc.
│   ├── gene_types/                     # Gene type classifications
│   └── validation_data/                # Reliability and validation info

Curated Data (Metabolic Subset):
├── data/04_curated/orpha/orphadata/
│   ├── disease2genes.json              # 549 diseases, 21KB
│   └── orpha_gene_curation_summary.json # Processing metadata
```

### Client Integration
```python
# Dual-client analysis approach
from core.datastore.orpha.orphadata.processed_gene_client import ProcessedGeneClient
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

processed_client = ProcessedGeneClient()     # Full dataset analysis
curated_client = CuratedGeneClient()         # Subset analysis
```

## 📈 Statistical Analysis Framework

### 1. Comprehensive Dataset Analysis
**Scope:** Full 4,078 disease dataset using ProcessedGeneClient

**Key Metrics:**
- **Disease Coverage:** Diseases with gene associations by disease type
- **Gene Distribution:** Most frequently associated genes across all diseases
- **Association Types:** Distribution of association types (disease-causing, susceptibility, etc.)
- **Gene-Disease Network:** Complex network analysis of gene-disease relationships
- **External References:** Coverage of HGNC, Ensembl, ClinVar, SwissProt references
- **Validation Analysis:** Distribution of validation sources and reliability scores

**Statistical Calculations:**
```python
# Comprehensive dataset metrics
total_diseases = len(processed_client.get_all_diseases())
diseases_with_genes = len(processed_client.get_diseases_with_genes())
total_associations = processed_client.get_total_association_count()
unique_genes = len(processed_client.get_all_genes())
association_types = processed_client.get_association_type_distribution()
external_ref_coverage = processed_client.get_external_reference_coverage()
```

### 2. Curated Subset Analysis
**Scope:** 549 metabolic diseases using CuratedGeneClient

**Key Metrics:**
- **Metabolic Coverage:** Gene association coverage within metabolic diseases
- **Gene Count Distribution:** Distribution of gene counts per disease
- **Disease-Causing Focus:** Analysis of disease-causing gene associations only
- **Monogenic vs. Polygenic:** Single-gene vs. multi-gene disease patterns
- **Curation Quality:** Analysis of curation process effectiveness

**Statistical Calculations:**
```python
# Curated subset metrics
curated_diseases = len(curated_client.get_diseases_with_genes())
coverage_stats = curated_client.get_coverage_statistics()
gene_distribution = curated_client.get_gene_distribution()
disease_gene_dist = curated_client.get_disease_gene_count_distribution()
top_genes = curated_client.get_most_common_genes(50)
```

### 3. Comparative Analysis
**Scope:** Comparison between processed and curated datasets

**Key Metrics:**
- **Curation Impact:** Effect of curation on data quality and focus
- **Coverage Comparison:** Disease coverage before and after curation
- **Gene Focus:** Shift from all associations to disease-causing only
- **Quality Improvement:** Validation and reliability improvements
- **Research Prioritization:** Most impactful genes for metabolic diseases

**Statistical Calculations:**
```python
# Comparative metrics
processed_metabolic = processed_client.get_diseases_in_subset(metabolic_codes)
curation_efficiency = len(curated_diseases) / len(processed_metabolic)
association_reduction = processed_associations / curated_associations
quality_improvement = curated_validation_score / processed_validation_score
```

## 📊 Visualization Framework

### 1. Gene Association Visualizations

#### 1.1 Gene Association Distribution (Bar Chart)
**File:** `gene_association_distribution.png`
**Purpose:** Show distribution of diseases across gene count categories
**Data Source:** CuratedGeneClient
```python
# Categories: 1 gene, 2-3 genes, 4-5 genes, 6-10 genes, 11+ genes
disease_gene_dist = curated_client.get_disease_gene_count_distribution()
```

#### 1.2 Top Associated Genes (Horizontal Bar Chart)
**File:** `top_associated_genes.png`
**Purpose:** Show top 20 most frequently disease-associated genes
**Data Source:** CuratedGeneClient
```python
top_genes = curated_client.get_most_common_genes(20)
```

#### 1.3 Association Type Distribution (Pie Chart)
**File:** `association_type_distribution.png`
**Purpose:** Show distribution of association types in processed data
**Data Source:** ProcessedGeneClient
```python
association_types = processed_client.get_association_type_distribution()
```

### 2. Coverage Analysis Visualizations

#### 2.1 Gene Coverage Analysis (Pie Chart)
**File:** `gene_coverage_analysis.png`
**Purpose:** Show coverage of metabolic diseases with gene data
**Data Source:** CuratedGeneClient
```python
coverage_stats = curated_client.get_coverage_statistics()
# Sections: With genes, Without genes
```

#### 2.2 Data Processing Pipeline (Flow Chart)
**File:** `data_processing_pipeline.png`
**Purpose:** Show data flow from raw to curated with statistics
**Data Source:** Processing summaries
```python
# Raw → Processed → Curated with numbers at each stage
```

### 3. Quality and Validation Visualizations

#### 3.1 External Reference Coverage (Stacked Bar Chart)
**File:** `external_reference_coverage.png`
**Purpose:** Show coverage of external references (HGNC, Ensembl, etc.)
**Data Source:** ProcessedGeneClient
```python
ref_coverage = processed_client.get_external_reference_coverage()
```

#### 3.2 Validation Source Distribution (Donut Chart)
**File:** `validation_source_distribution.png`
**Purpose:** Show distribution of validation sources
**Data Source:** ProcessedGeneClient
```python
validation_sources = processed_client.get_validation_source_distribution()
```

### 4. Research Insight Visualizations

#### 4.1 Gene-Disease Network (Network Graph)
**File:** `gene_disease_network.png`
**Purpose:** Show complex relationships between top genes and diseases
**Data Source:** CuratedGeneClient
```python
# Top 50 genes and their disease associations
```

#### 4.2 Monogenic vs Polygenic Analysis (Violin Plot)
**File:** `monogenic_vs_polygenic.png`
**Purpose:** Show distribution of gene counts per disease
**Data Source:** CuratedGeneClient
```python
# Distribution of gene counts with statistical analysis
```

## 🔧 Implementation Architecture

### Core Statistics Script
**File:** `etl/05_stats/orpha/orphadata/orpha_genes_stats.py`

**Key Features:**
- Dual-client integration for comprehensive analysis
- Efficient data processing with lazy loading
- Multiple output formats (JSON, CSV, visualizations)
- Comprehensive error handling and logging
- Modular design for easy extension

**Script Structure:**
```python
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
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Client imports
from core.datastore.orpha.orphadata.processed_gene_client import ProcessedGeneClient
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

class GeneStatisticsAnalyzer:
    """Main class for gene statistics analysis"""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.processed_client = ProcessedGeneClient()
        self.curated_client = CuratedGeneClient()
        
    def generate_comprehensive_analysis(self):
        """Generate complete statistical analysis"""
        
        # 1. Comprehensive dataset analysis
        comprehensive_stats = self.analyze_comprehensive_dataset()
        
        # 2. Curated subset analysis  
        curated_stats = self.analyze_curated_subset()
        
        # 3. Comparative analysis
        comparative_stats = self.analyze_comparative_metrics()
        
        # 4. Generate visualizations
        self.generate_all_visualizations()
        
        # 5. Create summary report
        self.generate_summary_report()
```

### Output Directory Structure
```
results/stats/etl/
├── all_disease_instances/orpha/orphadata/orpha_genes/
│   ├── comprehensive_gene_analysis.json
│   ├── gene_association_network.json
│   ├── association_type_distribution.png
│   ├── comprehensive_coverage_analysis.png
│   ├── external_reference_coverage.png
│   ├── validation_source_distribution.png
│   ├── gene_disease_network.png
│   └── analysis_summary.json
│
└── subset_of_disease_instances/orpha/orphadata/orpha_genes/metabolic/
    ├── metabolic_gene_analysis.json
    ├── gene_association_distribution.png
    ├── top_associated_genes.png
    ├── gene_coverage_analysis.png
    ├── monogenic_vs_polygenic.png
    ├── data_processing_pipeline.png
    └── analysis_summary.json
```

## 📈 Statistical Analysis Components

### 1. Comprehensive Dataset Analysis
**Output:** `results/stats/etl/all_disease_instances/orpha/orphadata/orpha_genes/`

**Key Functions:**
```python
def analyze_comprehensive_dataset(self) -> Dict[str, Any]:
    """Analyze complete processed dataset"""
    
    # Basic statistics
    total_diseases = len(self.processed_client.get_all_diseases())
    diseases_with_genes = len(self.processed_client.get_diseases_with_genes())
    
    # Gene statistics
    total_associations = self.processed_client.get_total_association_count()
    unique_genes = len(self.processed_client.get_all_genes())
    
    # Association type analysis
    association_types = self.processed_client.get_association_type_distribution()
    
    # External reference coverage
    external_refs = self.processed_client.get_external_reference_coverage()
    
    # Validation analysis
    validation_stats = self.processed_client.get_validation_statistics()
    
    return {
        'dataset_overview': {
            'total_diseases': total_diseases,
            'diseases_with_genes': diseases_with_genes,
            'coverage_percentage': (diseases_with_genes / total_diseases) * 100,
            'total_associations': total_associations,
            'unique_genes': unique_genes,
            'average_associations_per_disease': total_associations / diseases_with_genes
        },
        'association_type_distribution': association_types,
        'external_reference_coverage': external_refs,
        'validation_statistics': validation_stats,
        'gene_distribution': self.processed_client.get_gene_distribution()
    }
```

### 2. Curated Subset Analysis
**Output:** `results/stats/etl/subset_of_disease_instances/metabolic/orpha/orphadata/orpha_genes/`

**Key Functions:**
```python
def analyze_curated_subset(self) -> Dict[str, Any]:
    """Analyze curated metabolic diseases subset"""
    
    # Coverage statistics
    coverage_stats = self.curated_client.get_coverage_statistics()
    
    # Gene distribution
    gene_distribution = self.curated_client.get_gene_distribution()
    
    # Disease-gene count distribution
    disease_gene_dist = self.curated_client.get_disease_gene_count_distribution()
    
    # Top genes analysis
    top_genes = self.curated_client.get_most_common_genes(50)
    
    # Complex diseases analysis
    complex_diseases = self.curated_client.get_diseases_with_multiple_genes(min_genes=3)
    
    return {
        'subset_overview': {
            'total_diseases': coverage_stats['total_diseases'],
            'diseases_with_genes': coverage_stats['diseases_with_genes'],
            'coverage_percentage': coverage_stats['coverage_percentage'],
            'total_gene_associations': sum(gene_distribution.values()),
            'unique_genes': len(gene_distribution),
            'average_genes_per_disease': sum(gene_distribution.values()) / coverage_stats['diseases_with_genes']
        },
        'disease_gene_distribution': disease_gene_dist,
        'top_genes': top_genes,
        'complex_diseases': len(complex_diseases),
        'gene_distribution': gene_distribution
    }
```

### 3. Comparative Analysis
**Output:** Both directories with comparative metrics

**Key Functions:**
```python
def analyze_comparative_metrics(self) -> Dict[str, Any]:
    """Compare processed vs curated datasets"""
    
    # Get metabolic diseases from processed data
    metabolic_codes = set(self.curated_client.get_diseases_with_genes())
    processed_metabolic = self.processed_client.get_diseases_in_subset(metabolic_codes)
    
    # Calculate curation impact
    curation_efficiency = len(self.curated_client.get_diseases_with_genes()) / len(processed_metabolic)
    
    # Association reduction analysis
    processed_associations = sum(len(self.processed_client.get_genes_for_disease(code)) for code in metabolic_codes)
    curated_associations = sum(len(self.curated_client.get_genes_for_disease(code)) for code in metabolic_codes)
    
    return {
        'curation_impact': {
            'processed_diseases': len(processed_metabolic),
            'curated_diseases': len(self.curated_client.get_diseases_with_genes()),
            'curation_efficiency': curation_efficiency,
            'processed_associations': processed_associations,
            'curated_associations': curated_associations,
            'association_reduction': 1 - (curated_associations / processed_associations),
            'focus_improvement': 'disease-causing only'
        }
    }
```

## 🎨 Visualization Implementation

### Visualization Functions
```python
def generate_all_visualizations(self):
    """Generate all visualization charts"""
    
    # Set visualization style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")
    
    # Comprehensive dataset visualizations
    self.create_association_type_distribution()
    self.create_external_reference_coverage()
    self.create_validation_source_distribution()
    self.create_gene_disease_network()
    
    # Curated subset visualizations
    self.create_gene_association_distribution()
    self.create_top_associated_genes()
    self.create_gene_coverage_analysis()
    self.create_monogenic_vs_polygenic()
    self.create_data_processing_pipeline()

def create_gene_association_distribution(self):
    """Create gene association distribution chart"""
    
    disease_gene_dist = self.curated_client.get_disease_gene_count_distribution()
    
    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    categories = list(disease_gene_dist.keys())
    values = list(disease_gene_dist.values())
    
    bars = ax.bar(categories, values, color='skyblue', edgecolor='navy', alpha=0.7)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                str(value), ha='center', va='bottom', fontweight='bold')
    
    ax.set_title('Distribution of Gene Counts per Disease\n(Metabolic Diseases)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Gene Count Categories', fontsize=12)
    ax.set_ylabel('Number of Diseases', fontsize=12)
    
    # Add grid and styling
    ax.grid(True, axis='y', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # Save to both output directories
    all_diseases_path = self.output_dir / 'all_disease_instances/orpha/orphadata/orpha_genes'
    subset_path = self.output_dir / 'subset_of_disease_instances/metabolic/orpha/orphadata/orpha_genes/'
    
    all_diseases_path.mkdir(parents=True, exist_ok=True)
    subset_path.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(subset_path / 'gene_association_distribution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
```

## 📊 Performance Optimization

### Efficient Data Processing
```python
def optimize_data_loading(self):
    """Optimize data loading for performance"""
    
    # Use lazy loading for large datasets
    self.processed_client._ensure_disease2genes_loaded()
    self.curated_client._ensure_disease2genes_loaded()
    
    # Cache frequently accessed data
    self.processed_cache = {
        'total_diseases': len(self.processed_client.get_all_diseases()),
        'gene_distribution': self.processed_client.get_gene_distribution(),
        'association_types': self.processed_client.get_association_type_distribution()
    }
    
    self.curated_cache = {
        'coverage_stats': self.curated_client.get_coverage_statistics(),
        'gene_distribution': self.curated_client.get_gene_distribution(),
        'disease_gene_dist': self.curated_client.get_disease_gene_count_distribution()
    }
```

### Memory Management
```python
def manage_memory_usage(self):
    """Optimize memory usage during analysis"""
    
    # Process data in chunks for large datasets
    chunk_size = 1000
    
    # Clear caches after major operations
    self.processed_client.clear_cache()
    self.curated_client.clear_cache()
    
    # Use generators for large data iterations
    def process_diseases_generator():
        for disease_code in self.processed_client.get_all_diseases():
            yield self.processed_client.get_disease_info(disease_code)
```

## 🚀 Command Line Interface

### Script Arguments
```python
def main():
    """Main function with command line arguments"""
    
    parser = argparse.ArgumentParser(description='Generate genes statistical analysis')
    parser.add_argument('--output', 
                       default='results/stats/etl',
                       help='Output directory for results')
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
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize analyzer
    analyzer = GeneStatisticsAnalyzer(args.output)
    
    # Run analysis based on arguments
    if args.comprehensive or not any([args.comprehensive, args.curated, args.visualizations]):
        analyzer.generate_comprehensive_analysis()
    
    if args.curated:
        analyzer.generate_curated_analysis()
    
    if args.visualizations:
        analyzer.generate_all_visualizations()
    
    print("✅ Gene statistics analysis completed successfully!")
```

## 📋 Expected Outputs

### 1. JSON Statistical Reports
- `comprehensive_gene_analysis.json`: Complete dataset statistics
- `metabolic_gene_analysis.json`: Curated subset statistics
- `analysis_summary.json`: Executive summary for each dataset

### 2. Visualization Files
- `gene_association_distribution.png`: Gene count distribution
- `top_associated_genes.png`: Most common genes
- `association_type_distribution.png`: Association type breakdown
- `gene_coverage_analysis.png`: Coverage analysis
- `external_reference_coverage.png`: External reference statistics
- `validation_source_distribution.png`: Validation source analysis
- `gene_disease_network.png`: Network visualization
- `monogenic_vs_polygenic.png`: Gene count analysis
- `data_processing_pipeline.png`: Processing pipeline visualization

### 3. Research Insights
- Gene association patterns across rare diseases
- Identification of most clinically relevant genes
- Analysis of data quality and validation coverage
- Comparative analysis of processing pipeline effectiveness

## 🎯 Success Metrics

### Performance Targets
- **Processing Time:** < 30 seconds for complete analysis
- **Memory Usage:** < 2GB peak memory consumption
- **File Sizes:** JSON reports < 10MB, visualizations < 500KB each
- **Data Quality:** 100% validation of statistical calculations

### Research Impact
- **Comprehensive Coverage:** Analysis of 4,078 diseases and 8,300+ associations
- **Focused Analysis:** 549 metabolic diseases with disease-causing genes
- **Visual Insights:** 8+ publication-ready visualizations
- **Research Prioritization:** Clear identification of well-characterized vs. under-researched diseases

## 🎉 Deliverable Summary

**Task 3 will deliver:**
1. **Statistical Analysis Script:** `etl/05_stats/orpha/orphadata/orpha_genes_stats.py`
2. **Comprehensive Results:** Analysis of complete processed dataset
3. **Curated Results:** Analysis of metabolic diseases subset
4. **Visualization Suite:** 8+ professional charts and graphs
5. **Research Insights:** Data-driven recommendations for research priorities

This comprehensive analysis will provide researchers with deep insights into the genetic landscape of rare diseases, enabling data-driven research prioritization and highlighting areas requiring further investigation.

---

**🎯 Task 3 Objective:** Transform raw genetic data into actionable research insights through comprehensive statistical analysis and compelling visualizations. 