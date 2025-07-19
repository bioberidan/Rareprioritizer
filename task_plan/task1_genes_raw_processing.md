# Task 1: Genes ETL Raw Processing & Data Extraction

## 📋 Task Overview

**Objective:** Transform raw XML gene data from `en_product6.xml` into structured, analysis-ready JSON format with comprehensive data processing and client access layer.

**Deliverable:** Complete raw gene data processing pipeline with structured output and programmatic access client

**Duration:** Week 1 of Genes ETL project

**Dependencies:** 
- Raw XML file: `data/01_raw/en_product6.xml` (21MB)
- Existing ETL patterns from prevalence system
- Disease subset: `data/04_curated/orpha/ordo/metabolic_disease_instances.json`

## 🎯 Success Criteria

- **Data Processing:** Successfully process all 4,078 diseases from XML
- **Quality Assurance:** Achieve <5% data quality issues
- **Performance:** Complete processing in <10 minutes
- **Client Access:** Provide comprehensive programmatic access via ProcessedGeneClient
- **Data Integrity:** Generate structured JSON with gene associations and validation
- **Error Handling:** Robust error handling for malformed XML or missing data

## 📊 XML Data Structure Analysis

### Input XML Structure (`en_product6.xml`)

**Root Structure:**
```xml
<JDBOR>
  <DisorderList count="4078">
    <Disorder id="17601">
      <OrphaCode>166024</OrphaCode>
      <Name lang="en">Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome</Name>
      <DisorderType><Name lang="en">Disease</Name></DisorderType>
      <DisorderGroup><Name lang="en">Disorder</Name></DisorderGroup>
      <DisorderGeneAssociationList count="1">
        <DisorderGeneAssociation>
          <SourceOfValidation>22587682[PMID]</SourceOfValidation>
          <Gene id="20160">
            <Name lang="en">kinesin family member 7</Name>
            <Symbol>KIF7</Symbol>
            <SynonymList count="1">
              <Synonym lang="en">JBTS12</Synonym>
            </SynonymList>
            <GeneType id="25993">
              <Name lang="en">gene with protein product</Name>
            </GeneType>
            <ExternalReferenceList count="7">
              <ExternalReference id="250592">
                <Source>ClinVar</Source>
                <Reference>KIF7</Reference>
              </ExternalReference>
              <ExternalReference id="57240">
                <Source>Ensembl</Source>
                <Reference>ENSG00000166813</Reference>
              </ExternalReference>
              <ExternalReference id="51758">
                <Source>Genatlas</Source>
                <Reference>KIF7</Reference>
              </ExternalReference>
              <ExternalReference id="51756">
                <Source>HGNC</Source>
                <Reference>30497</Reference>
              </ExternalReference>
              <ExternalReference id="51757">
                <Source>OMIM</Source>
                <Reference>611254</Reference>
              </ExternalReference>
              <ExternalReference id="97306">
                <Source>Reactome</Source>
                <Reference>Q2M1P5</Reference>
              </ExternalReference>
              <ExternalReference id="51759">
                <Source>SwissProt</Source>
                <Reference>Q2M1P5</Reference>
              </ExternalReference>
            </ExternalReferenceList>
            <LocusList count="1">
              <Locus id="95035">
                <GeneLocus>15q26.1</GeneLocus>
                <LocusKey>1</LocusKey>
              </Locus>
            </LocusList>
          </Gene>
          <DisorderGeneAssociationType id="17949">
            <Name lang="en">Disease-causing germline mutation(s) in</Name>
          </DisorderGeneAssociationType>
          <DisorderGeneAssociationStatus id="17991">
            <Name lang="en">Assessed</Name>
          </DisorderGeneAssociationStatus>
        </DisorderGeneAssociation>
      </DisorderGeneAssociationList>
    </Disorder>
  </DisorderList>
</JDBOR>
```

### Key XML Fields to Extract

| XML Element | Target Field | Description |
|-------------|-------------|-------------|
| `Disorder/@id` | `disorder_id` | XML disorder identifier |
| `Disorder/OrphaCode` | `orpha_code` | Disease Orphanet code |
| `Disorder/Name[@lang="en"]` | `disease_name` | English disease name |
| `DisorderGeneAssociation/SourceOfValidation` | `source_validation` | PMID references for validation |
| `Gene/@id` | `gene_id` | Gene identifier |
| `Gene/Name[@lang="en"]` | `gene_name` | Gene full name |
| `Gene/Symbol` | `gene_symbol` | Gene symbol (e.g., KIF7) |
| `Gene/SynonymList/Synonym` | `gene_synonyms` | List of gene synonyms |
| `Gene/GeneType/Name[@lang="en"]` | `gene_type` | Gene type classification |
| `Gene/ExternalReferenceList/ExternalReference` | `external_references` | External database references |
| `Gene/LocusList/Locus/GeneLocus` | `gene_locus` | Chromosomal location |
| `DisorderGeneAssociationType/Name[@lang="en"]` | `association_type` | Type of gene-disease association |
| `DisorderGeneAssociationStatus/Name[@lang="en"]` | `association_status` | Status of association |

## 🏗️ Output Data Structure

### Target Directory Structure

```
data/03_processed/orpha/orphadata/orpha_genes/
├── disease2genes.json                     # Complete disease-gene mapping (15MB)
├── gene2diseases.json                     # Reverse lookup: gene→diseases (8MB)
├── gene_instances.json                    # Individual gene records (25MB)
├── gene_association_instances.json        # Individual association records (12MB)
├── orpha_index.json                       # Disease summary index (2MB)
├── external_references/                   # External database references
│   ├── hgnc_references.json              # HGNC mappings
│   ├── ensembl_references.json           # Ensembl mappings
│   ├── omim_references.json              # OMIM mappings
│   ├── clinvar_references.json           # ClinVar mappings
│   └── external_references_summary.json  # Reference statistics
├── validation_data/                       # Gene validation analysis
│   ├── validated_associations.json       # PMID-validated associations
│   ├── reliability_scores.json           # Association reliability scores
│   └── validation_summary.json           # Validation statistics
├── gene_types/                           # Gene type analysis
│   ├── gene_type_distribution.json       # Gene type classifications
│   └── gene_type_mapping.json            # Type standardization
└── cache/                                # Performance optimization
    ├── statistics.json                   # Processing statistics
    ├── gene_symbols_index.json           # Symbol lookups
    ├── locus_index.json                  # Chromosomal location index
    └── association_type_index.json       # Association type mappings
```

### Main Output Files

#### 1. `disease2genes.json` - Complete Disease-Gene Mapping
```json
{
  "166024": {
    "orpha_code": "166024",
    "disease_name": "Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome",
    "gene_associations": [
      {
        "gene_association_id": "assoc_166024_KIF7",
        "gene_id": "20160",
        "gene_symbol": "KIF7",
        "gene_name": "kinesin family member 7",
        "association_type": "Disease-causing germline mutation(s) in",
        "association_status": "Assessed",
        "source_validation": "22587682[PMID]",
        "reliability_score": 8.5,
        "is_validated": true,
        "gene_locus": "15q26.1",
        "gene_type": "gene with protein product",
        "external_references": {
          "HGNC": "30497",
          "OMIM": "611254",
          "Ensembl": "ENSG00000166813",
          "ClinVar": "KIF7",
          "Genatlas": "KIF7",
          "SwissProt": "Q2M1P5",
          "Reactome": "Q2M1P5"
        }
      }
    ],
    "primary_gene": "KIF7",
    "total_gene_associations": 1,
    "validated_associations": 1,
    "statistics": {
      "total_associations": 1,
      "validated_associations": 1,
      "mean_reliability_score": 8.5
    }
  }
}
```

#### 2. `gene2diseases.json` - Reverse Lookup
```json
{
  "KIF7": {
    "gene_id": "20160",
    "gene_symbol": "KIF7",
    "gene_name": "kinesin family member 7",
    "gene_type": "gene with protein product",
    "gene_locus": "15q26.1",
    "gene_synonyms": ["JBTS12"],
    "associated_diseases": [
      {
        "orpha_code": "166024",
        "disease_name": "Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome",
        "association_type": "Disease-causing germline mutation(s) in",
        "association_status": "Assessed",
        "reliability_score": 8.5,
        "source_validation": "22587682[PMID]"
      }
    ],
    "external_references": {
      "HGNC": "30497",
      "OMIM": "611254",
      "Ensembl": "ENSG00000166813",
      "ClinVar": "KIF7",
      "Genatlas": "KIF7",
      "SwissProt": "Q2M1P5",
      "Reactome": "Q2M1P5"
    },
    "total_disease_associations": 1,
    "validated_associations": 1,
    "statistics": {
      "association_types": {
        "Disease-causing germline mutation(s) in": 1
      },
      "mean_reliability_score": 8.5
    }
  }
}
```

#### 3. `gene_instances.json` - Individual Gene Records
```json
{
  "20160": {
    "gene_id": "20160",
    "gene_symbol": "KIF7",
    "gene_name": "kinesin family member 7",
    "gene_type": "gene with protein product",
    "gene_locus": "15q26.1",
    "gene_synonyms": ["JBTS12"],
    "external_references": {
      "HGNC": "30497",
      "OMIM": "611254",
      "Ensembl": "ENSG00000166813",
      "ClinVar": "KIF7",
      "Genatlas": "KIF7",
      "SwissProt": "Q2M1P5",
      "Reactome": "Q2M1P5"
    },
    "associated_diseases_count": 1,
    "validated_associations_count": 1,
    "processing_metadata": {
      "first_seen": "2024-01-15T10:30:00Z",
      "data_quality_score": 9.2,
      "validation_status": "complete"
    }
  }
}
```

#### 4. `gene_association_instances.json` - Individual Association Records
```json
{
  "assoc_166024_KIF7": {
    "gene_association_id": "assoc_166024_KIF7",
    "orpha_code": "166024",
    "disease_name": "Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome",
    "gene_id": "20160",
    "gene_symbol": "KIF7",
    "gene_name": "kinesin family member 7",
    "association_type": "Disease-causing germline mutation(s) in",
    "association_status": "Assessed",
    "source_validation": "22587682[PMID]",
    "reliability_score": 8.5,
    "is_validated": true,
    "gene_locus": "15q26.1",
    "gene_type": "gene with protein product",
    "external_references": {
      "HGNC": "30497",
      "OMIM": "611254",
      "Ensembl": "ENSG00000166813",
      "ClinVar": "KIF7",
      "Genatlas": "KIF7",
      "SwissProt": "Q2M1P5",
      "Reactome": "Q2M1P5"
    },
    "processing_metadata": {
      "xml_disorder_id": "17601",
      "xml_gene_id": "20160",
      "processed_timestamp": "2024-01-15T10:30:00Z"
    }
  }
}
```

## 🔧 Technical Implementation

### 1. Core Processing Script: `etl/03_process/orpha/orphadata/process_orpha_genes.py`

**Key Features:**
- XML parsing with comprehensive error handling
- Gene association reliability scoring algorithm
- External reference standardization
- Data quality assessment and validation
- Performance optimization with streaming processing

**Core Functions:**
```python
def process_genes_xml(xml_path: str, output_dir: str) -> Dict:
    """
    Main processing function to transform XML to structured JSON
    
    Args:
        xml_path: Path to en_product6.xml
        output_dir: Output directory for processed data
        
    Returns:
        Processing statistics and metadata
    """

def calculate_gene_reliability_score(association_record: Dict) -> float:
    """
    Calculate reliability score for gene-disease associations (0-10 scale)
    
    Scoring criteria:
    - Source validation (4 points): PMID references
    - Association status (2 points): Assessed > Not assessed
    - Association type (2 points): Disease-causing > Risk factor > Modifier
    - Gene type (1 point): protein product > other
    - External references (1 point): Multiple databases
    
    Args:
        association_record: Gene association record
        
    Returns:
        Reliability score (0-10)
    """

def standardize_external_references(ref_list: List[Dict]) -> Dict:
    """
    Standardize external database references
    
    Args:
        ref_list: List of external reference records
        
    Returns:
        Standardized reference dictionary
    """

def validate_gene_data_quality(gene_record: Dict) -> Dict:
    """
    Assess data quality for gene records
    
    Args:
        gene_record: Gene record dictionary
        
    Returns:
        Quality assessment results
    """
```

### 2. Gene Association Reliability Scoring Algorithm

**Scoring Framework (10-point scale):**
```python
def calculate_gene_reliability_score(association_record):
    """
    Gene association reliability scoring algorithm
    
    Total possible score: 10.0 points
    """
    score = 0.0
    
    # Source validation (4 points)
    source_validation = association_record.get('source_validation', '')
    if '[PMID]' in source_validation:
        pmid_count = source_validation.count('[PMID]')
        if pmid_count >= 3:
            score += 4.0  # Multiple PMID references
        elif pmid_count == 2:
            score += 3.5  # Two PMID references
        elif pmid_count == 1:
            score += 3.0  # Single PMID reference
    elif 'EXPERT' in source_validation:
        score += 1.5  # Expert validation
    
    # Association status (2 points)
    association_status = association_record.get('association_status', '')
    if association_status == 'Assessed':
        score += 2.0  # Fully assessed
    elif association_status == 'Not assessed':
        score += 0.5  # Preliminary assessment
    
    # Association type (2 points)
    association_type = association_record.get('association_type', '')
    if 'Disease-causing' in association_type:
        score += 2.0  # Disease-causing mutations
    elif 'Risk factor' in association_type:
        score += 1.5  # Risk factor associations
    elif 'Modifier' in association_type:
        score += 1.0  # Modifier associations
    elif 'Susceptibility' in association_type:
        score += 0.8  # Susceptibility associations
    
    # Gene type (1 point)
    gene_type = association_record.get('gene_type', '')
    if 'gene with protein product' in gene_type:
        score += 1.0  # Protein-coding genes
    elif 'pseudogene' in gene_type:
        score += 0.3  # Pseudogenes
    
    # External references (1 point)
    external_refs = association_record.get('external_references', {})
    ref_count = len([ref for ref in external_refs.values() if ref])
    if ref_count >= 5:
        score += 1.0  # Multiple database references
    elif ref_count >= 3:
        score += 0.7  # Several references
    elif ref_count >= 1:
        score += 0.4  # Some references
    
    return min(score, 10.0)
```

### 3. Data Access Client: `core/datastore/orpha/orphadata/processed_gene_client.py`

**Key Features:**
- Lazy loading and caching for performance
- Comprehensive query methods
- Gene-disease association filtering
- External reference lookup
- Statistical analysis capabilities

**Core Methods:**
```python
class ProcessedGeneClient:
    """
    Client for processed gene data with lazy loading and advanced query capabilities
    """
    
    def __init__(self, data_dir: str = "data/03_processed/orpha/orphadata/orpha_genes"):
        """Initialize the processed gene client"""
        
    # ========== Core Query Methods ==========
    
    def get_genes_for_disease(self, orpha_code: str, 
                            min_reliability: float = 0.0,
                            association_type: Optional[str] = None,
                            validated_only: bool = False) -> List[Dict]:
        """Get gene associations for a specific disease"""
        
    def get_diseases_for_gene(self, gene_symbol: str,
                            min_reliability: float = 0.0,
                            association_type: Optional[str] = None) -> List[Dict]:
        """Get disease associations for a specific gene"""
        
    def get_gene_details(self, gene_symbol: str) -> Optional[Dict]:
        """Get comprehensive gene information"""
        
    def get_disease_gene_summary(self, orpha_code: str) -> Optional[Dict]:
        """Get complete gene summary for a disease"""
        
    # ========== Advanced Query Methods ==========
    
    def search_genes_by_locus(self, locus: str) -> List[Dict]:
        """Search genes by chromosomal location"""
        
    def get_genes_by_type(self, gene_type: str) -> List[Dict]:
        """Get genes by type classification"""
        
    def get_validated_associations(self, min_score: float = 6.0) -> List[Dict]:
        """Get validated gene-disease associations"""
        
    def search_by_external_reference(self, database: str, reference: str) -> List[Dict]:
        """Search by external database reference"""
        
    # ========== Statistical Methods ==========
    
    def get_gene_statistics(self) -> Dict:
        """Get comprehensive gene statistics"""
        
    def get_association_type_distribution(self) -> Dict[str, int]:
        """Get distribution of association types"""
        
    def get_reliability_distribution(self) -> Dict[str, int]:
        """Get distribution of reliability scores"""
        
    def get_gene_type_distribution(self) -> Dict[str, int]:
        """Get distribution of gene types"""
        
    def get_external_reference_coverage(self) -> Dict[str, int]:
        """Get coverage statistics for external references"""
        
    # ========== Utility Methods ==========
    
    def clear_cache(self):
        """Clear all cached data"""
        
    def preload_all(self):
        """Preload all data for better performance"""
        
    def is_data_available(self) -> bool:
        """Check if gene data is available"""
        
    def export_gene_associations(self, output_file: str, format: str = 'json'):
        """Export gene associations to file"""
```

### 4. Data Models: `core/schemas/orpha/orphadata/orpha_genes.py`

**Pydantic Models:**
```python
class GeneInstance(BaseModel):
    """Model for individual gene records"""
    gene_id: str
    gene_symbol: str
    gene_name: str
    gene_type: str
    gene_locus: Optional[str]
    gene_synonyms: List[str]
    external_references: Dict[str, str]
    associated_diseases_count: int
    validated_associations_count: int
    processing_metadata: Dict

class GeneAssociationInstance(BaseModel):
    """Model for gene-disease association records"""
    gene_association_id: str
    orpha_code: str
    disease_name: str
    gene_id: str
    gene_symbol: str
    gene_name: str
    association_type: str
    association_status: str
    source_validation: str
    reliability_score: float
    is_validated: bool
    gene_locus: Optional[str]
    gene_type: str
    external_references: Dict[str, str]
    processing_metadata: Dict

class DiseaseGeneMapping(BaseModel):
    """Model for disease-gene mappings"""
    orpha_code: str
    disease_name: str
    gene_associations: List[GeneAssociationInstance]
    primary_gene: Optional[str]
    total_gene_associations: int
    validated_associations: int
    statistics: Dict
```

## 🚀 Implementation Steps

### Phase 1: Core Processing Development (Days 1-3)

1. **Create processing script** (`etl/03_process/orpha/orphadata/process_orpha_genes.py`)
   - XML parsing with ElementTree
   - Data extraction and standardization
   - Error handling and validation
   - Output file generation

2. **Implement reliability scoring**
   - Gene association reliability algorithm
   - Source validation analysis
   - Association type classification
   - Data quality assessment

3. **Create data models**
   - Pydantic models for gene data
   - Input validation and type checking
   - Data serialization/deserialization

### Phase 2: Client Development (Days 4-5)

1. **Create ProcessedGeneClient**
   - Lazy loading implementation
   - Core query methods
   - Caching mechanisms
   - Performance optimization

2. **Implement advanced queries**
   - Gene-disease association filtering
   - External reference lookup
   - Statistical analysis methods
   - Search capabilities

### Phase 3: Testing & Optimization (Days 6-7)

1. **Performance testing**
   - Processing speed optimization
   - Memory usage analysis
   - Cache efficiency testing
   - Large dataset handling

2. **Data quality validation**
   - Output verification
   - Statistical analysis
   - Error handling testing
   - Integration testing

## 📈 Expected Outcomes

**Data Processing Results:**
- **Total Diseases:** 4,078 diseases processed
- **Gene Associations:** ~8,000+ gene-disease associations
- **Unique Genes:** ~3,000+ unique gene symbols
- **Validated Associations:** ~80% with PMID references
- **Processing Time:** <10 minutes for complete pipeline

**Data Quality Metrics:**
- **Reliability Score Distribution:** 70% > 6.0 (validated)
- **External Reference Coverage:** 90%+ with HGNC/OMIM references
- **Association Type Distribution:** 85% disease-causing mutations
- **Gene Type Distribution:** 95% protein-coding genes
- **Data Completeness:** 95%+ complete gene records

**Performance Metrics:**
- **File Sizes:** 15MB disease2genes, 8MB gene2diseases, 25MB gene_instances
- **Query Performance:** <100ms for cached queries
- **Memory Usage:** <2GB peak during processing
- **Cache Hit Rate:** 90%+ for frequent queries

## 🔧 Usage Examples

### Basic Processing
```bash
# Run complete gene processing pipeline
python etl/03_process/orpha/orphadata/process_orpha_genes.py

# Custom XML path
python etl/03_process/orpha/orphadata/process_orpha_genes.py \
  --xml data/01_raw/en_product6.xml \
  --output data/03_processed/orpha/orphadata/orpha_genes

# Verbose output with statistics
python etl/03_process/orpha/orphadata/process_orpha_genes.py --verbose
```

### Programmatic Access
```python
from core.datastore.orpha.orphadata.processed_gene_client import ProcessedGeneClient

# Initialize client
client = ProcessedGeneClient()

# Get genes for a disease
genes = client.get_genes_for_disease("79318", min_reliability=6.0)
print(f"Found {len(genes)} validated genes for disease 79318")

# Get diseases for a gene
diseases = client.get_diseases_for_gene("KIF7", validated_only=True)
print(f"KIF7 is associated with {len(diseases)} diseases")

# Get gene details
gene_info = client.get_gene_details("KIF7")
print(f"Gene: {gene_info['gene_name']} ({gene_info['gene_symbol']})")
print(f"Location: {gene_info['gene_locus']}")
print(f"Type: {gene_info['gene_type']}")

# Statistical analysis
stats = client.get_gene_statistics()
print(f"Total genes: {stats['total_genes']}")
print(f"Total associations: {stats['total_associations']}")
print(f"Validated associations: {stats['validated_associations']}")
```

## 🎯 Integration with Existing Systems

**Data Flow Integration:**
```
Raw XML → ProcessedGeneClient → CuratedGeneClient → Research Applications
```

**Cross-System Compatibility:**
- Disease codes compatible with prevalence and drug systems
- Same metabolic disease subset (665 diseases)
- Consistent data access patterns
- Unified error handling and logging

**Performance Considerations:**
- Lazy loading for memory efficiency
- LRU caching for frequently accessed data
- Parallel processing for large datasets
- Streaming XML processing for large files

This comprehensive task plan establishes the foundation for a robust gene data processing system that follows established patterns while providing the specific functionality needed for gene-disease association analysis. 