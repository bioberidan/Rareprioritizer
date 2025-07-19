# Orphadata Curation Pipeline

This directory contains the curation scripts for transforming processed Orphanet data into high-quality, research-ready datasets focused on specific disease subsets and quality criteria.

## 📁 Directory Contents

### Curation Scripts
- **`curate_orpha_genes.py`** - Curate gene-disease associations for metabolic diseases
- **`curate_orpha_prevalence.py`** - Curate prevalence data with advanced fallback algorithms
- **`curate_orpha_drugs.py`** - Curate drug-disease associations for treatment analysis

## 🚀 Gene Curation Pipeline

### Input Data
- **Source:** `data/03_processed/orpha/orphadata/orpha_genes/disease2genes.json`
- **Disease Subset:** 665 metabolic diseases from `data/04_curated/orpha/ordo/metabolic_disease_instances.json`
- **Content:** Complete processed gene-disease association data

### Curation Features
- **Disease Subset Filtering:** Focus on 665 metabolic diseases
- **Disease-Causing Gene Filtering:** Include only validated disease-causing associations
- **Quality Assurance:** Exclude candidate genes and genetic modifiers
- **Consistency Validation:** Ensure data integrity and format consistency

### Disease-Causing Gene Criteria
**Included Association Types:**
- Disease-causing germline mutation(s) in
- Disease-causing germline mutation(s) (loss of function) in
- Disease-causing germline mutation(s) (gain of function) in
- Disease-causing somatic mutation(s) in

**Excluded Association Types:**
- Candidate gene tested in
- Role in the phenotype of
- Major susceptibility factor in
- Modifying germline mutation in

### Output Structure
```
data/04_curated/orpha/orphadata/
├── disease2genes.json                      # 549 diseases with disease-causing genes
└── orpha_gene_curation_summary.json       # Processing metadata and statistics
```

## 🔧 Usage Examples

### Basic Curation
```bash
# Curate genes with default settings
python -m etl.04_curate.orpha.orphadata.curate_orpha_genes

# Curate with custom paths
python -m etl.04_curate.orpha.orphadata.curate_orpha_genes \
  --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json \
  --input data/03_processed/orpha/orphadata/orpha_genes/disease2genes.json \
  --output data/04_curated/orpha/orphadata/
```

### Advanced Options
```bash
# Curate with verbose logging
python -m etl.04_curate.orpha.orphadata.curate_orpha_genes \
  --disease-subset custom_subset.json \
  --input custom_input.json \
  --output custom_output/ \
  --verbose
```

## 📊 Curation Quality Metrics

### Coverage Statistics
- **Input Diseases:** 665 metabolic diseases (metabolic subset)
- **Diseases with Disease-Causing Genes:** 549 diseases
- **Coverage Achievement:** 82.6% of metabolic diseases
- **Total Gene Associations:** 820 disease-causing associations
- **Unique Genes:** 656 distinct gene symbols

### Disease-Gene Distribution
- **Monogenic Diseases:** 479 diseases (87.2%) - Single gene
- **Oligogenic Diseases:** 53 diseases (9.7%) - 2-5 genes
- **Polygenic Diseases:** 17 diseases (3.1%) - 6+ genes
- **Average Genes per Disease:** 1.49 genes

### Quality Assurance Results
- **Association Type Filtering:** 820 disease-causing associations retained
- **Excluded Associations:** 44 candidate/modifier associations excluded
- **Data Validation:** 100% validation passed
- **Quality Issues:** 0 critical issues detected

## 🔄 Integration with Pipeline

This curation step is part of the larger genes ETL pipeline:

```
Raw XML → [Process] → Structured JSON → [Curate] → Final Dataset → [Statistics]
```

**Previous Step:** `etl/03_process/orpha/orphadata/process_orpha_genes.py`
**Next Steps:** 
1. **Statistics:** `etl/05_stats/orpha/orphadata/orpha_genes_stats.py`
2. **Access:** `core/datastore/orpha/orphadata/curated_gene_client.py`

## 📚 Documentation

- **Complete System Documentation:** `docs/genes_data_system.md`
- **Task Plans:** `task_plan/genes_etl_executive_plan.md`
- **Data Models:** `core/schemas/orpha/orphadata/orpha_genes.py`

## 🛠️ Technical Requirements

- **Python 3.8+** with standard library
- **Dependencies:** json, pathlib, typing, datetime
- **Memory:** ~500MB RAM for curation processing
- **Storage:** ~50KB for curated output

## 🔍 Scientific Methodology

### Conservative Curation Approach
1. **Evidence-Based Filtering:** Only include scientifically validated disease-causing genes
2. **Quality Over Quantity:** Exclude uncertain associations to maintain data integrity
3. **Metabolic Disease Focus:** Concentrate on well-defined metabolic disorder subset
4. **Comprehensive Validation:** Multi-level quality checks and consistency validation

### Data Quality Standards
- **Association Type Validation:** Strict filtering based on scientific evidence
- **Gene Symbol Standardization:** Consistent gene nomenclature
- **Duplicate Removal:** Ensure unique gene associations per disease
- **Format Consistency:** Standardized JSON output format

## 🔍 Troubleshooting

### Common Issues
1. **Missing Input Files:** Ensure processed data exists before curation
2. **Subset File Errors:** Validate metabolic disease subset format
3. **Memory Issues:** Increase available RAM for large datasets
4. **Validation Failures:** Check data consistency and format

### Performance Tips
- Use SSD storage for faster I/O operations
- Ensure sufficient memory for data loading
- Enable verbose logging for debugging
- Validate input data before processing

## 📈 Research Applications

### Use Cases
1. **Monogenic Disease Research:** Focus on single-gene disorders
2. **Complex Disease Analysis:** Study multi-gene associations
3. **Drug Target Discovery:** Identify therapeutic targets
4. **Diagnostic Development:** Support genetic testing strategies

### Integration Opportunities
- **Prevalence Analysis:** Combine with prevalence data for prioritization
- **Drug Research:** Cross-reference with treatment options
- **Clinical Applications:** Support precision medicine approaches
- **Research Prioritization:** Identify knowledge gaps and opportunities 