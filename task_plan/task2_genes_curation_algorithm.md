# Task 2: Gene Data Curation & Selection Algorithm

## 📋 Task Overview

**Objective:** Apply a focused selection algorithm to curate disease-causing gene associations for the 665 metabolic diseases subset, creating a simplified JSON mapping format for research applications.

**Deliverable:** Complete gene data curation pipeline with disease-causing gene filtering and CuratedGeneClient

**Duration:** Week 2 of Genes ETL project

**Dependencies:** 
- Processed gene data: `data/03_processed/orpha/orphadata/orpha_genes/`
- Metabolic disease subset: `data/04_curated/orpha/ordo/metabolic_disease_instances.json` (665 diseases)
- Task 1 completion: ProcessedGeneClient and processed data structures

## 🎯 Success Criteria

- **Coverage Target:** 80%+ of the 665 metabolic diseases with disease-causing gene associations
- **Data Quality:** Only validated disease-causing gene associations in curated output
- **Output Format:** Simple JSON mapping `{"orpha_code": ["gene1", "gene2", ...]}`
- **Client Access:** Comprehensive CuratedGeneClient with lazy loading and caching
- **Integration:** Seamless integration with existing CuratedPrevalenceClient patterns
- **Performance:** Fast query performance for research applications

## 📊 Data Analysis Results

### Current Processed Gene Data Statistics
- **Total Disorders:** 4,078 diseases processed
- **Gene Associations:** 8,300 total gene-disease associations
- **Disease-Causing Associations:** 6,899 associations (83.1% of total)
- **Metabolic Disease Subset:** 665 diseases (target subset)

### Association Type Distribution
- **Disease-causing germline mutation(s) in:** 5,235 associations (63.1%)
- **Disease-causing germline mutation(s) (loss of function) in:** 1,223 associations (14.7%)
- **Disease-causing germline mutation(s) (gain of function) in:** 219 associations (2.6%)
- **Disease-causing somatic mutation(s) in:** 222 associations (2.7%)
- **Non-disease-causing associations:** 1,401 associations (16.9%)

### Target Output Format

**Simple JSON Structure (following executive plan):**
```json
{
  "79318": ["PMM2"],
  "272": ["FBN1", "TGFBR2"],
  "93": ["AGA"],
  "166024": ["KIF7"]
}
```

**NOT the complex structure with association details - just disease code to gene symbol list mapping.**

## 🔧 Curation Algorithm Design

### 1. Disease Subset Filtering
**Input:** All 4,078 diseases from processed gene data
**Filter:** Restrict to 665 metabolic diseases from `metabolic_disease_instances.json`

```python
def load_metabolic_disease_subset():
    """Load the 665 metabolic diseases subset"""
    with open('data/04_curated/orpha/ordo/metabolic_disease_instances.json', 'r') as f:
        metabolic_diseases = json.load(f)
    
    # Extract orpha codes from list structure
    metabolic_codes = {disease['orpha_code'] for disease in metabolic_diseases}
    return metabolic_codes
```

### 2. Disease-Causing Gene Association Filter
**Criteria:** Include only associations where `association_type` contains "Disease-causing"

**Disease-Causing Association Types to Include:**
- `Disease-causing germline mutation(s) in`
- `Disease-causing germline mutation(s) (loss of function) in`
- `Disease-causing germline mutation(s) (gain of function) in`
- `Disease-causing somatic mutation(s) in`

**Excluded Association Types:**
- `Major susceptibility factor in` (not disease-causing)
- `Candidate gene tested in` (not confirmed)
- `Role in the phenotype of` (modifier role)
- `Part of a fusion gene in` (special case)
- `Biomarker tested in` (diagnostic, not causative)

### 3. Gene Selection Algorithm
**Approach:** Simple inclusion of all disease-causing genes (no complex prioritization needed)

```python
def curate_disease_genes(processed_gene_data, metabolic_codes):
    """
    Curate genes for metabolic diseases with disease-causing associations
    
    Args:
        processed_gene_data: Output from ProcessedGeneClient
        metabolic_codes: Set of metabolic disease orpha codes
        
    Returns:
        Simple mapping of orpha_code -> list of gene symbols
    """
    curated_genes = {}
    
    for orpha_code, disease_data in processed_gene_data.items():
        # Filter to metabolic diseases only
        if orpha_code not in metabolic_codes:
            continue
        
        # Extract disease-causing genes
        disease_causing_genes = []
        for association in disease_data.get('gene_associations', []):
            association_type = association.get('association_type', '')
            
            # Include only disease-causing associations
            if 'Disease-causing' in association_type:
                gene_symbol = association.get('gene_symbol')
                if gene_symbol and gene_symbol not in disease_causing_genes:
                    disease_causing_genes.append(gene_symbol)
        
        # Only include diseases with disease-causing genes
        if disease_causing_genes:
            curated_genes[orpha_code] = sorted(disease_causing_genes)
    
    return curated_genes
```

### 4. Quality Assurance
**Validation Checks:**
- Ensure all gene symbols are valid (non-empty strings)
- Remove duplicate genes within same disease
- Verify orpha codes exist in metabolic subset
- Check for reasonable gene counts per disease (1-10 typical range)

```python
def validate_curated_genes(curated_genes):
    """Quality assurance for curated gene mappings"""
    validation_report = {
        'total_diseases': len(curated_genes),
        'diseases_with_single_gene': 0,
        'diseases_with_multiple_genes': 0,
        'total_gene_associations': 0,
        'unique_genes': set(),
        'quality_issues': []
    }
    
    for orpha_code, genes in curated_genes.items():
        # Count associations
        validation_report['total_gene_associations'] += len(genes)
        validation_report['unique_genes'].update(genes)
        
        # Count distribution
        if len(genes) == 1:
            validation_report['diseases_with_single_gene'] += 1
        else:
            validation_report['diseases_with_multiple_genes'] += 1
        
        # Quality checks
        if len(genes) > 10:
            validation_report['quality_issues'].append(f"Disease {orpha_code} has {len(genes)} genes (unusual)")
        
        for gene in genes:
            if not gene or not isinstance(gene, str):
                validation_report['quality_issues'].append(f"Invalid gene symbol in {orpha_code}: {gene}")
    
    validation_report['unique_genes'] = len(validation_report['unique_genes'])
    return validation_report
```

## 🏗️ Implementation Architecture

### Target Directory Structure

```
data/04_curated/orpha/orphadata/
├── disease2genes.json                    # Main curated mapping (simple format)
└── orpha_gene_curation_summary.json     # Processing metadata and statistics
```

### 1. Core Curation Script: `etl/04_curate/orpha/orphadata/curate_orpha_genes.py`

**Key Features:**
- Load metabolic disease subset (665 diseases)
- Filter processed gene data to metabolic diseases only
- Extract disease-causing gene associations
- Create simple JSON mapping format
- Generate curation statistics and quality reports

**Command Line Interface:**
```bash
# Basic curation
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py

# Custom paths
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py \
  --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json \
  --input data/03_processed/orpha/orphadata/orpha_genes/disease2genes.json \
  --output data/04_curated/orpha/orphadata/

# Verbose output
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py --verbose
```

### 2. CuratedGeneClient: `core/datastore/orpha/orphadata/curated_gene_client.py`

**Following CuratedPrevalenceClient patterns:**
- Lazy loading and caching
- Simple API for gene lookups
- Statistical analysis methods
- Export capabilities
- Data validation

**Core Methods:**
```python
class CuratedGeneClient:
    """Client for curated gene data with lazy loading and caching"""
    
    def __init__(self, data_dir: str = "data/04_curated/orpha/orphadata"):
        """Initialize the curated gene client"""
        
    # ========== Core Data Access ==========
    
    def get_genes_for_disease(self, orpha_code: str) -> List[str]:
        """Get disease-causing genes for a specific disease"""
        
    def get_diseases_for_gene(self, gene_symbol: str) -> List[str]:
        """Get diseases associated with a specific gene"""
        
    def has_genes(self, orpha_code: str) -> bool:
        """Check if disease has disease-causing genes"""
        
    def get_disease_info(self, orpha_code: str) -> Dict[str, Any]:
        """Get comprehensive disease gene information"""
        
    # ========== Search and Filter Methods ==========
    
    def search_diseases_by_gene(self, gene_symbol: str) -> List[str]:
        """Search diseases by exact gene symbol match"""
        
    def search_genes_by_pattern(self, pattern: str) -> List[str]:
        """Search genes by name pattern"""
        
    def get_diseases_with_multiple_genes(self, min_genes: int = 2) -> List[Dict]:
        """Get diseases with multiple disease-causing genes"""
        
    def get_diseases_with_single_gene(self) -> List[Dict]:
        """Get diseases with exactly one disease-causing gene"""
        
    # ========== Statistical Methods ==========
    
    def get_coverage_statistics(self) -> Dict[str, Any]:
        """Get coverage statistics for metabolic diseases"""
        
    def get_gene_distribution(self) -> Dict[str, int]:
        """Get distribution of genes across diseases"""
        
    def get_disease_gene_count_distribution(self) -> Dict[str, int]:
        """Get distribution of gene counts per disease"""
        
    def get_most_common_genes(self, limit: int = 20) -> List[Dict]:
        """Get most frequently associated genes"""
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics"""
        
    # ========== Data Management ==========
    
    def export_to_csv(self, output_file: str, include_disease_names: bool = True):
        """Export to CSV format"""
        
    def export_to_json(self, output_file: str):
        """Export to JSON format"""
        
    def validate_data_consistency(self) -> Dict[str, Any]:
        """Validate data consistency"""
        
    def clear_cache(self):
        """Clear cached data"""
```

### 3. Expected Output Files

#### `disease2genes.json` - Main Curated Mapping
```json
{
  "79318": ["PMM2"],
  "272": ["FBN1", "TGFBR2"],
  "93": ["AGA"],
  "166024": ["KIF7"],
  "534": ["OCRL"],
  "214": ["SLC3A1", "SLC7A9"]
}
```

#### `orpha_gene_curation_summary.json` - Processing Metadata
```json
{
  "curation_metadata": {
    "input_diseases": 665,
    "diseases_with_genes": 532,
    "diseases_without_genes": 133,
    "coverage_percentage": 80.0,
    "total_gene_associations": 847,
    "unique_genes": 623,
    "processing_timestamp": "2024-01-15T10:30:00Z"
  },
  "disease_gene_distribution": {
    "diseases_with_1_gene": 445,
    "diseases_with_2_genes": 62,
    "diseases_with_3_genes": 18,
    "diseases_with_4_genes": 5,
    "diseases_with_5+_genes": 2
  },
  "quality_statistics": {
    "association_type_counts": {
      "Disease-causing germline mutation(s) in": 678,
      "Disease-causing germline mutation(s) (loss of function) in": 123,
      "Disease-causing germline mutation(s) (gain of function) in": 28,
      "Disease-causing somatic mutation(s) in": 18
    },
    "data_quality_score": 9.8,
    "validation_passed": true
  },
  "selection_criteria": {
    "metabolic_disease_filter": true,
    "disease_causing_only": true,
    "excluded_association_types": [
      "Major susceptibility factor in",
      "Candidate gene tested in",
      "Role in the phenotype of",
      "Part of a fusion gene in",
      "Biomarker tested in"
    ]
  }
}
```

## 🚀 Implementation Steps

### Phase 1: Curation Algorithm Development (Days 1-2)

1. **Create curation script**
   - Load metabolic disease subset
   - Filter processed gene data
   - Extract disease-causing associations
   - Generate simple JSON mapping

2. **Quality assurance implementation**
   - Data validation checks
   - Statistical analysis
   - Error handling and reporting

### Phase 2: CuratedGeneClient Development (Days 3-4)

1. **Core client implementation**
   - Lazy loading and caching
   - Basic data access methods
   - Search and filter capabilities

2. **Statistical analysis methods**
   - Coverage statistics
   - Gene distribution analysis
   - Summary reporting

### Phase 3: Testing & Integration (Days 5-7)

1. **Comprehensive testing**
   - Data consistency validation
   - Performance optimization
   - Integration with existing systems

2. **Documentation and examples**
   - Usage documentation
   - Research workflow examples
   - API documentation

## 📈 Expected Outcomes

### Data Processing Results
- **Target Coverage:** 80%+ of 665 metabolic diseases with disease-causing genes
- **Expected Output:** ~530 diseases with gene associations
- **Gene Count:** ~620 unique disease-causing genes
- **Average Genes per Disease:** 1.6 genes

### Quality Metrics
- **Data Purity:** 100% disease-causing associations only
- **Gene Validation:** All genes have valid symbols
- **Consistency:** No duplicate genes within diseases
- **Integration:** Compatible with prevalence and drug systems

### Performance Metrics
- **File Size:** <50KB for curated JSON (simple format)
- **Query Performance:** <10ms for cached lookups
- **Memory Usage:** <100MB for full dataset
- **Load Time:** <1 second for client initialization

## 🔧 Usage Examples

### Basic Curation
```bash
# Run complete curation pipeline
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py

# With custom subset
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py \
  --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json

# Verbose processing
python etl/04_curate/orpha/orphadata/curate_orpha_genes.py --verbose
```

### Programmatic Access
```python
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

# Initialize client
client = CuratedGeneClient()

# Get genes for a disease
genes = client.get_genes_for_disease("79318")
print(f"PMM2-CDG genes: {genes}")  # Output: ["PMM2"]

# Get diseases for a gene
diseases = client.get_diseases_for_gene("FBN1")
print(f"FBN1 diseases: {diseases}")  # Output: ["272", ...]

# Coverage statistics
stats = client.get_coverage_statistics()
print(f"Coverage: {stats['coverage_percentage']:.1f}%")

# Gene distribution
top_genes = client.get_most_common_genes(5)
for gene_info in top_genes:
    print(f"{gene_info['gene']}: {gene_info['disease_count']} diseases")
```

### Research Workflow Integration
```python
# Combined with prevalence data
from core.datastore.orpha.orphadata.curated_prevalence_client import CuratedOrphaPrevalenceClient
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient

prev_client = CuratedOrphaPrevalenceClient()
gene_client = CuratedGeneClient()

# Find well-characterized diseases (have both prevalence and genes)
diseases_with_prev = set(prev_client.get_diseases_by_prevalence_class("1-9 / 1 000 000"))
diseases_with_genes = set(gene_client.get_diseases_with_genes())

well_characterized = diseases_with_prev & diseases_with_genes
print(f"Well-characterized rare diseases: {len(well_characterized)}")

# Research prioritization
for orpha_code in well_characterized:
    genes = gene_client.get_genes_for_disease(orpha_code)
    prevalence = prev_client.get_prevalence_class(orpha_code)
    print(f"{orpha_code}: {len(genes)} genes, prevalence {prevalence}")
```

## 🎯 Integration with Existing Systems

**Data Flow Integration:**
```
Processed Gene Data → CuratedGeneClient → Research Applications
                           ↓
              CuratedPrevalenceClient → Cross-System Analysis
```

**Consistency with Established Patterns:**
- Same disease subset (665 metabolic diseases)
- Compatible lazy loading and caching patterns  
- Unified error handling and logging
- Consistent API design with prevalence client
- Same data validation approaches

**Cross-System Compatibility:**
- Disease codes match prevalence and drug systems
- Simple JSON format for easy integration
- Performance optimizations for combined queries
- Unified statistical reporting patterns

This task plan provides a focused, realistic approach to gene data curation that delivers the simple JSON format specified in the executive plan while maintaining high data quality and system integration. 