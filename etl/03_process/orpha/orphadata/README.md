# Orphadata Processing Pipeline

This directory contains the processing scripts for transforming raw Orphanet XML data into structured, analysis-ready JSON datasets.

## 📁 Directory Contents

### Processing Scripts
- **`process_orpha_genes.py`** - Transform raw gene-disease association XML to structured JSON
- **`process_orpha_prevalence.py`** - Transform raw prevalence XML to structured JSON  
- **`process_orpha_drugs.py`** - Transform raw Orphanet drug api to structured JSON (deprecated, use curate_drugs instead in curate dir)

## 🚀 Gene Processing Pipeline

### Input Data
- **Source:** `data/01_raw/en_product6.xml` (21MB)
- **Content:** Complete Orphanet gene-disease association database
- **Scope:** 4,078 diseases with comprehensive gene association records

### Processing Features
- **XML Parsing:** Comprehensive parsing with error handling
- **Gene Association Extraction:** Extract and standardize gene-disease associations
- **External Reference Integration:** HGNC, OMIM, Ensembl, SwissProt mappings
- **Association Type Classification:** Disease-causing, candidate, modifier classifications
- **Data Quality Assessment:** Validation and quality metrics

### Output Structure
```
data/03_processed/orpha/orphadata/orpha_genes/
├── disease2genes.json                     # Complete disease-gene mapping
├── gene2diseases.json                     # Reverse lookup: gene→diseases
├── gene_instances.json                    # Individual gene records
├── gene_association_instances.json        # Association records
├── orpha_index.json                       # Disease summary index
├── external_references/                   # External database references
├── validation_data/                       # Quality analysis
├── gene_types/                           # Gene type analysis
└── cache/                                # Performance optimization
```

## 🔧 Usage Examples

### Basic Processing
```bash
# Process genes with default settings
python process_orpha_genes.py

# Process with custom paths
python process_orpha_genes.py \
  --xml data/01_raw/en_product6.xml \
  --output data/03_processed/orpha/orphadata/orpha_genes
```

### Advanced Options
```bash
# Enable verbose logging
python process_orpha_genes.py --verbose

# Process with custom configuration
python process_orpha_genes.py \
  --xml custom_data.xml \
  --output custom_output/ \
  --verbose
```

## 📊 Data Quality Metrics

### Processing Statistics
- **Total Diseases:** 4,078 diseases processed
- **Gene Associations:** 15,000+ gene-disease associations
- **Unique Genes:** 3,000+ unique gene symbols
- **External References:** High coverage of major databases

### Quality Assurance
- **XML Validation:** Structural integrity checks
- **Content Validation:** Required field verification
- **Association Classification:** Type-based filtering
- **External Reference Validation:** Database cross-references

## 🔄 Integration with Pipeline

This processing step is part of the larger genes ETL pipeline:

```
Raw XML → [Process] → Structured JSON → [Curate] → Final Dataset
```

**Next Steps:**
1. **Curation:** `etl/04_curate/orpha/orphadata/curate_orpha_genes.py`
2. **Statistics:** `etl/05_stats/orpha/orphadata/orpha_genes_stats.py`
3. **Access:** `core/datastore/orpha/orphadata/processed_gene_client.py`

## 📚 Documentation

- **Complete System Documentation:** `docs/genes_data_system.md`
- **Task Plans:** `task_plan/genes_etl_executive_plan.md`
- **Data Models:** `core/schemas/orpha/orphadata/orpha_genes.py`

## 🛠️ Technical Requirements

- **Python 3.8+** with standard library
- **Dependencies:** xml.etree.ElementTree, json, pathlib
- **Memory:** ~2GB RAM for processing 21MB XML
- **Storage:** ~60MB for complete processed output

## 🔍 Troubleshooting

### Common Issues
1. **Memory Errors:** Increase available RAM or process in chunks
2. **XML Parsing Errors:** Validate XML structure and encoding
3. **File Permission Errors:** Ensure write permissions for output directory
4. **Missing Dependencies:** Install required Python packages

### Performance Tips
- Use SSD storage for faster I/O operations
- Increase system memory for large datasets
- Enable verbose logging for debugging
- Use appropriate output directory structure 


#TODO add the rest of pipes