# Orphadata Statistics Pipeline

This directory contains the statistical analysis and visualization scripts for generating comprehensive insights from curated Orphanet data.

## 📁 Directory Contents

### Statistics Scripts
- **`orpha_genes_stats.py`** - Comprehensive gene-disease association analysis and visualization
- **`orpha_prevalence_stats.py`** - Prevalence distribution analysis and visualization
- **`orpha_drugs_stats.py`** - Drug-disease association analysis and visualization

## 🚀 Gene Statistics Pipeline

### Input Data
- **Processed Data:** `data/03_processed/orpha/orphadata/orpha_genes/`
- **Curated Data:** `data/04_curated/orpha/orphadata/disease2genes.json`
- **Content:** Complete gene-disease association dataset and curated subset

### Analysis Features
- **Comprehensive Coverage Analysis:** Gene association coverage across disease categories
- **Gene Distribution Analysis:** Most frequently associated genes across diseases
- **Association Type Analysis:** Distribution of disease-causing vs. other associations
- **Comparative Analysis:** Processed vs. curated dataset comparison
- **Disease Complexity Analysis:** Monogenic vs. polygenic disease patterns

### Generated Visualizations
1. **`gene_association_distribution.png`** - Distribution of gene counts per disease
2. **`top_associated_genes.png`** - Most frequently associated genes across diseases
3. **`gene_coverage_analysis.png`** - Coverage analysis of genes vs diseases
4. **`monogenic_vs_polygenic.png`** - Comparison of single-gene vs multi-gene diseases
5. **`association_type_distribution.png`** - Distribution of gene association types

### Output Structure
```
results/stats/etl/subset_of_disease_instances/metabolic/orpha/orphadata/orpha_genes/
├── gene_association_distribution.png          # Gene count distribution visualization
├── top_associated_genes.png                   # Most common genes visualization
├── gene_coverage_analysis.png                 # Coverage analysis visualization
├── monogenic_vs_polygenic.png                 # Disease complexity analysis
├── metabolic_gene_analysis.json               # Detailed statistical analysis
└── analysis_summary.json                      # Summary statistics
```

## 🔧 Usage Examples

### Basic Analysis
```bash
# Generate all statistics and visualizations
python -m etl.05_stats.orpha.orphadata.orpha_genes_stats

# Generate with custom configuration
python -m etl.05_stats.orpha.orphadata.orpha_genes_stats \
  --output-base results/stats/etl \
  --dataset-type metabolic
```

### Advanced Options
```bash
# Custom output directory and dataset
python -m etl.05_stats.orpha.orphadata.orpha_genes_stats \
  --output-base custom_results/ \
  --dataset-type all_diseases \
  --verbose
```

## 📊 Statistical Analysis Results

### Coverage Statistics
- **Total Diseases Analyzed:** 549 diseases with disease-causing genes
- **Coverage Achievement:** 82.6% of metabolic diseases
- **Total Gene Associations:** 820 disease-causing associations
- **Unique Genes:** 656 distinct gene symbols

### Disease-Gene Distribution
- **Monogenic Diseases:** 479 diseases (87.2%) - Single gene
- **Oligogenic Diseases:** 53 diseases (9.7%) - 2-5 genes
- **Polygenic Diseases:** 17 diseases (3.1%) - 6+ genes
- **Average Genes per Disease:** 1.49 genes

### Association Type Analysis
- **Disease-causing germline mutations:** 660 associations (80.5%)
- **Loss of function mutations:** 154 associations (18.8%)
- **Gain of function mutations:** 5 associations (0.6%)
- **Somatic mutations:** 1 association (0.1%)

### Most Associated Genes
Top genes by disease association frequency:
1. **FBN1** - Associated with 8 diseases
2. **COL2A1** - Associated with 6 diseases
3. **TGFBR2** - Associated with 4 diseases
4. **COL1A1** - Associated with 4 diseases
5. **ACADVL** - Associated with 3 diseases

## 🔄 Integration with Pipeline

This statistics step is the final stage of the genes ETL pipeline:

```
Raw XML → [Process] → Structured JSON → [Curate] → Final Dataset → [Statistics]
```

**Previous Steps:**
1. **Processing:** `etl/03_process/orpha/orphadata/process_orpha_genes.py`
2. **Curation:** `etl/04_curate/orpha/orphadata/curate_orpha_genes.py`

**Data Access:** `core/datastore/orpha/orphadata/curated_gene_client.py`

## 📚 Documentation

- **Complete System Documentation:** `docs/genes_data_system.md`
- **Task Plans:** `task_plan/genes_etl_executive_plan.md`
- **Data Models:** `core/schemas/orpha/orphadata/orpha_genes.py`

## 🛠️ Technical Requirements

- **Python 3.8+** with scientific computing libraries
- **Dependencies:** matplotlib, seaborn, pandas, numpy
- **Memory:** ~1GB RAM for visualization generation
- **Storage:** ~2MB for all visualizations and analysis files

## 🔍 Analysis Methodology

### Statistical Approach
1. **Descriptive Statistics:** Basic coverage and distribution metrics
2. **Comparative Analysis:** Processed vs. curated dataset comparison
3. **Distribution Analysis:** Gene frequency and disease complexity patterns
4. **Quality Assessment:** Association type and coverage evaluation

### Visualization Standards
- **High-Quality Graphics:** 300 DPI publication-ready visualizations
- **Consistent Styling:** Standardized color schemes and formatting
- **Clear Labels:** Descriptive titles and axis labels
- **Data Annotations:** Key statistics and insights highlighted

## 🔍 Troubleshooting

### Common Issues
1. **Import Errors:** Ensure matplotlib, seaborn, pandas installed
2. **Memory Issues:** Increase available RAM for large datasets
3. **File Access Errors:** Verify input data files exist
4. **Visualization Errors:** Check display backend configuration

### Performance Tips
- Use sufficient memory for data loading
- Enable batch processing for large datasets
- Use appropriate figure sizes for memory efficiency
- Save visualizations in optimal formats

## 📈 Research Applications

### Use Cases
1. **Research Prioritization:** Identify understudied diseases and genes
2. **Drug Discovery:** Target identification and validation
3. **Clinical Research:** Understand disease complexity patterns
4. **Diagnostic Development:** Support genetic testing strategies

### Key Insights
- **Monogenic Dominance:** Most metabolic diseases are monogenic
- **Complex Disorders:** Small subset with multiple gene associations
- **Gene Frequency:** Few genes associated with many diseases
- **Coverage Gaps:** Opportunities for further research

## 📊 Integration with Other Systems

### Cross-System Analysis
- **Prevalence Integration:** Combine with prevalence data for priority scoring
- **Drug Integration:** Cross-reference with treatment availability
- **Clinical Integration:** Support precision medicine approaches

### Export Formats
- **JSON:** Machine-readable statistical data
- **PNG:** High-quality visualizations
- **CSV:** Tabular data for external analysis
- **PDF:** Publication-ready reports

## 🎯 Quality Assurance

### Data Validation
- **Input Validation:** Verify data integrity and format
- **Statistical Validation:** Ensure mathematical accuracy
- **Visualization Validation:** Check chart accuracy and clarity
- **Output Validation:** Verify file generation and accessibility

### Performance Monitoring
- **Processing Time:** Monitor analysis execution time
- **Memory Usage:** Track resource consumption
- **Output Quality:** Validate visualization and data quality
- **Error Handling:** Comprehensive error reporting and recovery 