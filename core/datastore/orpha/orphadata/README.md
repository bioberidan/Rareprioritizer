# Orphadata Data Access Clients

This directory contains the data access clients for efficient querying and retrieval of Orphanet data with lazy loading, caching, and comprehensive query capabilities.

## 📁 Directory Contents

### Data Access Clients
- **`processed_gene_client.py`** - Access to complete processed gene-disease association data
- **`curated_gene_client.py`** - Access to curated disease-causing gene associations
- **`prevalence_client.py`** - Access to processed prevalence data
- **`curated_prevalence_client.py`** - Access to curated prevalence data

## 🚀 Gene Data Access Clients

### Processed Gene Client
**Purpose:** Access to complete gene-disease association dataset from processing stage
**Data Source:** `data/03_processed/orpha/orphadata/orpha_genes/`
**Coverage:** 4,078 diseases with complete gene association data

**Key Features:**
- Complete gene-disease association access
- External database reference queries
- Association type filtering and analysis
- Gene locus and type information
- Comprehensive statistics and metrics

### Curated Gene Client
**Purpose:** Access to curated disease-causing gene associations
**Data Source:** `data/04_curated/orpha/orphadata/disease2genes.json`
**Coverage:** 549 diseases with disease-causing genes (82.6% of metabolic diseases)

**Key Features:**
- Disease-causing gene associations only
- High-performance lazy loading
- Comprehensive query methods
- Export capabilities (CSV, JSON)
- Statistical analysis functions

## 🔧 Usage Examples

### Curated Gene Client Usage
```python
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

# Initialize client
client = CuratedGeneClient()

# Basic gene queries
genes = client.get_genes_for_disease("79318")
# Returns: ["PMM2"]

diseases = client.get_diseases_for_gene("FBN1")
# Returns: ["272", "1490", "558"]

# Check if disease has genes
has_genes = client.has_genes("79318")
# Returns: True

# Get disease information
disease_info = client.get_disease_info("79318")
# Returns: {"orpha_code": "79318", "disease_name": "PMM2-CDG", "genes": ["PMM2"], "gene_count": 1}
```

### Advanced Query Examples
```python
# Complex queries
multi_gene_diseases = client.get_diseases_with_multiple_genes(min_genes=3)
# Returns: [{"orpha_code": "272", "genes": ["FBN1", "TGFBR2", "TGFB2"], "gene_count": 3}, ...]

monogenic_diseases = client.get_diseases_with_single_gene()
# Returns: [{"orpha_code": "79318", "genes": ["PMM2"], "gene_count": 1}, ...]

# Gene frequency analysis
common_genes = client.get_most_common_genes(limit=10)
# Returns: [{"gene": "FBN1", "disease_count": 8}, {"gene": "COL2A1", "disease_count": 6}, ...]

# Search and filtering
pattern_genes = client.search_genes_by_pattern("COL", case_sensitive=False)
# Returns: ["COL1A1", "COL2A1", "COL3A1", ...]

fbn1_diseases = client.search_diseases_by_gene("FBN1")
# Returns: ["272", "1490", "558", ...]
```

### Statistical Analysis
```python
# Coverage statistics
stats = client.get_coverage_statistics()
# Returns: {
#   "total_diseases": 549,
#   "coverage_percentage": 82.6,
#   "total_genes": 656,
#   "total_associations": 820,
#   "average_genes_per_disease": 1.49
# }

# Gene distribution
gene_dist = client.get_gene_distribution()
# Returns: {"FBN1": 8, "COL2A1": 6, "TGFBR2": 4, ...}

# Disease-gene count distribution
count_dist = client.get_disease_gene_count_distribution()
# Returns: {"1": 479, "2": 36, "3": 4, "4": 9, "5": 4, "6+": 17}

# Summary statistics
summary = client.get_summary_statistics()
# Returns comprehensive statistical summary
```

### Data Export
```python
# Export to CSV
client.export_to_csv("gene_data.csv", include_disease_names=True)

# Export to JSON
client.export_to_json("gene_data.json")

# Custom export with specific diseases
diseases_of_interest = ["79318", "272", "61"]
subset_data = {code: client.get_genes_for_disease(code) for code in diseases_of_interest}
```

### Processed Gene Client Usage
```python
from core.datastore.orpha.orphadata.processed_gene_client import ProcessedGeneClient

# Initialize client
client = ProcessedGeneClient()

# Complete gene association data
associations = client.get_gene_associations_for_disease("79318")
# Returns: [{"gene_symbol": "PMM2", "association_type": "Disease-causing...", ...}]

# External references
external_refs = client.get_external_references_for_gene("PMM2")
# Returns: {"HGNC": "9115", "OMIM": "601785", "Ensembl": "ENSG00000140650"}

# Association type analysis
assoc_types = client.get_association_type_distribution()
# Returns: {"Disease-causing germline mutation(s) in": 1245, ...}

# Chromosomal location queries
genes_on_locus = client.get_genes_by_locus("16p13.2")
# Returns: ["PMM2", "GENE2", ...]
```

## 📊 Client Features

### Performance Optimization
- **Lazy Loading:** Data loaded only when accessed
- **LRU Caching:** Frequently accessed data cached in memory
- **Efficient Queries:** Optimized data structures for fast retrieval
- **Memory Management:** Automatic cache clearing and data reloading

### Data Validation
- **Input Validation:** Comprehensive parameter validation
- **Data Consistency:** Internal consistency checks
- **Error Handling:** Graceful error handling and recovery
- **Type Safety:** Full type hints and validation

### Query Capabilities
- **Basic Queries:** Simple get/set operations
- **Advanced Filtering:** Complex query conditions
- **Pattern Matching:** Flexible search capabilities
- **Statistical Analysis:** Built-in statistical functions

## 🔄 Integration with Pipeline

The data access clients serve as the final interface layer:

```
Raw XML → [Process] → [Curate] → [Statistics] → [Data Access Clients]
```

**Data Flow:**
1. **Processing:** Creates processed data files
2. **Curation:** Creates curated data files
3. **Statistics:** Analyzes curated data
4. **Clients:** Provide programmatic access to all data

## 📚 Documentation

- **Complete System Documentation:** `docs/genes_data_system.md`
- **Task Plans:** `task_plan/genes_etl_executive_plan.md`
- **Data Models:** `core/schemas/orpha/orphadata/orpha_genes.py`

## 🛠️ Technical Requirements

- **Python 3.8+** with standard library
- **Dependencies:** json, pathlib, typing, functools, csv
- **Memory:** ~100MB RAM for typical usage
- **Storage:** Direct access to processed/curated data files

## 🔍 Client Architecture

### Base Architecture
```python
class DataClient:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self._lazy_data_structures = {}
        self._cache = {}
    
    def _ensure_data_loaded(self):
        """Lazy loading implementation"""
        pass
    
    @lru_cache(maxsize=128)
    def cached_query(self, query_params):
        """Cached query implementation"""
        pass
```

### Error Handling
```python
try:
    client = CuratedGeneClient()
    genes = client.get_genes_for_disease("79318")
except FileNotFoundError:
    print("Data files not found - run ETL pipeline first")
except ValueError as e:
    print(f"Invalid query parameters: {e}")
```

## 🔍 Troubleshooting

### Common Issues
1. **FileNotFoundError:** Run ETL pipeline to generate data files
2. **Memory Issues:** Clear cache or increase available memory
3. **Query Errors:** Validate input parameters and data types
4. **Performance Issues:** Use caching and optimize query patterns

### Performance Tips
- Use cached queries for repeated operations
- Clear cache periodically for memory management
- Batch similar queries for efficiency
- Use appropriate data structures for specific use cases

## 📈 Research Applications

### Use Cases
1. **Exploratory Data Analysis:** Interactive data exploration
2. **Batch Processing:** Large-scale data analysis
3. **API Integration:** Backend services for web applications
4. **Research Workflows:** Systematic data retrieval and analysis

### Integration Examples
```python
# Multi-system integration
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient
from core.datastore.orpha.orphadata.curated_prevalence_client import CuratedOrphaPrevalenceClient

gene_client = CuratedGeneClient()
prevalence_client = CuratedOrphaPrevalenceClient()

# Cross-system analysis
diseases_with_genes = set(gene_client.get_diseases_with_genes())
diseases_with_prevalence = set(prevalence_client.get_diseases_with_prevalence())
complete_data = diseases_with_genes.intersection(diseases_with_prevalence)

# Comprehensive disease analysis
for disease_code in complete_data:
    genes = gene_client.get_genes_for_disease(disease_code)
    prevalence = prevalence_client.get_prevalence_class(disease_code)
    disease_name = gene_client.get_disease_name(disease_code)
    print(f"{disease_name}: {genes} | {prevalence}")
```

## 🎯 Quality Assurance

### Data Validation
- **Parameter Validation:** Comprehensive input validation
- **Data Integrity:** Consistency checks and validation
- **Error Recovery:** Graceful error handling and fallback
- **Performance Monitoring:** Query performance tracking

### Testing
- **Unit Tests:** Individual method testing
- **Integration Tests:** Cross-client functionality testing
- **Performance Tests:** Load and stress testing
- **Data Quality Tests:** Validation of data accuracy 