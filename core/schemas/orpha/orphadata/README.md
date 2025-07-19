# Orphadata Data Models

This directory contains the Pydantic data models for Orphanet data processing, providing type-safe, validated data structures for genes, prevalence, and drug information.

## 📁 Directory Contents

### Data Model Files
- **`orpha_genes.py`** - Gene-disease association data models
- **`orpha_prevalence.py`** - Prevalence data models  
- **`orpha_drugs.py`** - Drug-disease association data models

## 🚀 Gene Data Models

### Core Data Models

#### GeneInstance
**Purpose:** Represents individual gene records with complete information
```python
class GeneInstance(BaseModel):
    gene_id: str                           # XML Gene/@id
    gene_symbol: str                       # Official gene symbol (e.g., KIF7)
    gene_name: str                         # Full gene name
    gene_type: str                         # Gene type classification
    gene_locus: Optional[str]              # Chromosomal location (e.g., 15q26.1)
    gene_synonyms: List[str]               # List of gene synonyms
    external_references: Dict[str, str]    # External database references
    
    # Calculated metrics
    associated_diseases_count: int         # Number of associated diseases
    validated_associations_count: int      # Number of validated associations
    
    # Processing metadata
    processing_metadata: Dict[str, Any]    # Processing metadata
```

#### GeneAssociationInstance
**Purpose:** Represents individual gene-disease association records
```python
class GeneAssociationInstance(BaseModel):
    gene_association_id: str               # Unique association identifier
    orpha_code: str                        # Disease Orphanet code
    disease_name: str                      # Disease name
    
    # Gene information
    gene_id: str                           # Gene identifier
    gene_symbol: str                       # Gene symbol
    gene_name: str                         # Gene full name
    gene_type: str                         # Gene type classification
    gene_locus: Optional[str]              # Chromosomal location
    gene_synonyms: List[str]               # Gene synonyms
    
    # Association details
    association_type: str                  # Type of gene-disease association
    association_status: str                # Status of association assessment
    source_validation: str                 # Source validation (PMID references)
    
    # Calculated metrics
    reliability_score: float               # Calculated reliability score 0-10
    is_validated: bool                     # Meets validation criteria (≥6.0 score)
    
    # External references
    external_references: Dict[str, str]    # External database references
    
    # Processing metadata
    processing_metadata: Dict[str, Any]    # Processing metadata
```

#### Disease2GenesMapping
**Purpose:** Maps diseases to their associated genes
```python
class Disease2GenesMapping(BaseModel):
    orpha_code: str                        # Disease Orphanet code
    disease_name: str                      # Disease name
    gene_associations: List[GeneAssociationInstance]  # Gene association records
    primary_gene: Optional[str]            # Primary gene (first in list)
    total_gene_associations: int           # Total number of associations
    validated_associations: int            # Number of validated associations
    statistics: Dict[str, Any]             # Processing statistics
```

#### Gene2DiseasesMapping
**Purpose:** Maps genes to their associated diseases
```python
class Gene2DiseasesMapping(BaseModel):
    gene_symbol: str                       # Gene symbol
    gene_name: str                         # Gene full name
    associated_diseases: List[str]         # List of associated disease codes
    disease_associations: List[GeneAssociationInstance]  # Full association records
    total_diseases: int                    # Total number of diseases
    validated_diseases: int                # Number of validated diseases
    statistics: Dict[str, Any]             # Processing statistics
```

### Supporting Data Models

#### ProcessingStatistics
**Purpose:** Tracks processing metrics and quality indicators
```python
class ProcessingStatistics(BaseModel):
    total_disorders: int                   # Total diseases processed
    disorders_with_genes: int              # Diseases with gene associations
    total_gene_associations: int           # Total gene associations
    unique_genes: int                      # Unique gene count
    association_types: Dict[str, int]      # Association type distribution
    gene_types: Dict[str, int]             # Gene type distribution
    external_reference_coverage: Dict[str, int]  # External reference coverage
    processing_timestamp: str              # Processing timestamp
```

#### OrphaIndexEntry
**Purpose:** Provides summary information for diseases
```python
class OrphaIndexEntry(BaseModel):
    orpha_code: str                        # Disease Orphanet code
    disease_name: str                      # Disease name
    gene_count: int                        # Number of associated genes
    primary_gene: Optional[str]            # Primary gene
    has_validated_genes: bool              # Has validated associations
    processing_metadata: Dict[str, Any]    # Processing metadata
```

## 🔧 Usage Examples

### Basic Model Usage
```python
from core.schemas.orpha.orphadata.orpha_genes import GeneInstance, GeneAssociationInstance

# Create gene instance
gene = GeneInstance(
    gene_id="20160",
    gene_symbol="KIF7",
    gene_name="kinesin family member 7",
    gene_type="gene with protein product",
    gene_locus="15q26.1",
    gene_synonyms=["JBTS12", "ACLS"],
    external_references={"HGNC": "30497", "OMIM": "611254"},
    associated_diseases_count=5,
    validated_associations_count=5,
    processing_metadata={"processed_timestamp": "2024-01-15T10:30:00Z"}
)

# Create association instance
association = GeneAssociationInstance(
    gene_association_id="assoc_79318_KIF7",
    orpha_code="79318",
    disease_name="PMM2-CDG",
    gene_id="20160",
    gene_symbol="KIF7",
    gene_name="kinesin family member 7",
    gene_type="gene with protein product",
    gene_locus="15q26.1",
    gene_synonyms=["JBTS12", "ACLS"],
    association_type="Disease-causing germline mutation(s) in",
    association_status="Assessed",
    source_validation="11389160[PMID]_9689990[PMID]",
    reliability_score=8.5,
    is_validated=True,
    external_references={"HGNC": "30497", "OMIM": "611254"},
    processing_metadata={"processed_timestamp": "2024-01-15T10:30:00Z"}
)
```

### Data Validation Examples
```python
# Automatic validation
try:
    gene = GeneInstance(
        gene_id="20160",
        gene_symbol="KIF7",
        gene_name="kinesin family member 7",
        gene_type="gene with protein product",
        reliability_score=15.0  # Invalid: > 10.0
    )
except ValidationError as e:
    print(f"Validation error: {e}")

# Custom validation
@validator('reliability_score')
def validate_reliability_score(cls, v):
    if not 0 <= v <= 10:
        raise ValueError('Reliability score must be between 0 and 10')
    return v
```

### JSON Serialization/Deserialization
```python
# Serialize to JSON
gene_dict = gene.dict()
gene_json = gene.json()

# Deserialize from JSON
gene_from_dict = GeneInstance(**gene_dict)
gene_from_json = GeneInstance.parse_raw(gene_json)
```

## 📊 Data Model Features

### Type Safety
- **Strict Type Checking:** All fields have explicit types
- **Optional Fields:** Nullable fields clearly marked
- **Custom Validation:** Domain-specific validation rules
- **Runtime Validation:** Automatic data validation on creation

### Data Integrity
- **Required Fields:** Critical fields marked as required
- **Field Validation:** Custom validators for complex fields
- **Consistent Naming:** Standardized field naming conventions
- **Documentation:** Complete docstrings for all fields

### Serialization Support
- **JSON Serialization:** Native JSON support
- **Dictionary Conversion:** Easy conversion to/from dictionaries
- **Custom Serializers:** Support for custom serialization formats
- **Schema Export:** Generate JSON schemas for external use

## 🔄 Integration with Pipeline

The data models are used throughout the ETL pipeline:

```
Raw XML → [Process] → Validated Models → [Curate] → Final Models → [Statistics]
```

**Usage in Pipeline:**
1. **Processing:** XML data parsed into model instances
2. **Validation:** Models ensure data integrity
3. **Curation:** Models provide consistent data structures
4. **Statistics:** Models enable type-safe analysis

## 📚 Documentation

- **Complete System Documentation:** `docs/genes_data_system.md`
- **Task Plans:** `task_plan/genes_etl_executive_plan.md`
- **Processing Scripts:** `etl/03_process/orpha/orphadata/process_orpha_genes.py`

## 🛠️ Technical Requirements

- **Python 3.8+** with type hints support
- **Pydantic v1.8+** for data validation
- **Dependencies:** typing, datetime, json
- **Memory:** Minimal overhead for model validation
- **Performance:** Efficient validation and serialization

## 🔍 Model Architecture

### Base Model Structure
```python
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

class BaseOrphaModel(BaseModel):
    """Base class for all Orphanet data models"""
    
    class Config:
        validate_assignment = True
        use_enum_values = True
        allow_population_by_field_name = True
        
    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None"""
        if v == '':
            return None
        return v
```

### Validation Patterns
```python
# String field validation
@validator('gene_symbol')
def validate_gene_symbol(cls, v):
    if not v or not v.strip():
        raise ValueError('Gene symbol cannot be empty')
    return v.strip().upper()

# Numeric field validation
@validator('reliability_score')
def validate_reliability_score(cls, v):
    if not 0 <= v <= 10:
        raise ValueError('Reliability score must be between 0 and 10')
    return v

# List field validation
@validator('gene_synonyms')
def validate_gene_synonyms(cls, v):
    return [synonym.strip() for synonym in v if synonym.strip()]
```

## 🔍 Troubleshooting

### Common Issues
1. **ValidationError:** Check field types and constraints
2. **Missing Fields:** Ensure required fields are provided
3. **Type Errors:** Verify correct data types for fields
4. **JSON Errors:** Validate JSON structure and format

### Performance Tips
- Use model validation sparingly in tight loops
- Cache model instances for repeated use
- Use `parse_obj` for better performance with dictionaries
- Consider using `construct` for trusted data

## 📈 Research Applications

### Use Cases
1. **Data Quality Assurance:** Ensure consistent data structures
2. **API Development:** Type-safe API endpoints
3. **Data Analysis:** Structured data for research workflows
4. **Documentation:** Self-documenting data structures

### Integration Examples
```python
# Processing pipeline integration
from core.schemas.orpha.orphadata.orpha_genes import GeneProcessingResult

def process_genes_xml(xml_path: str) -> GeneProcessingResult:
    """Process XML and return validated results"""
    
    # Process XML data
    disease2genes = {}
    gene_instances = {}
    statistics = ProcessingStatistics(...)
    
    # Create validated result
    result = GeneProcessingResult(
        statistics=statistics,
        disease2genes=disease2genes,
        gene_instances=gene_instances
    )
    
    return result
```

## 🎯 Quality Assurance

### Data Validation
- **Field Validation:** Comprehensive field-level validation
- **Cross-Field Validation:** Consistency checks across fields
- **Format Validation:** Standardized data formats
- **Business Logic Validation:** Domain-specific validation rules

### Testing
- **Unit Tests:** Individual model testing
- **Integration Tests:** Model integration testing
- **Performance Tests:** Validation performance testing
- **Data Quality Tests:** Real-world data validation

## 🔬 Advanced Features

### Custom Validators
```python
@validator('external_references')
def validate_external_references(cls, v):
    """Validate external reference format"""
    valid_sources = ['HGNC', 'OMIM', 'Ensembl', 'SwissProt']
    
    for source, reference in v.items():
        if source not in valid_sources:
            raise ValueError(f'Invalid reference source: {source}')
        if not reference:
            raise ValueError(f'Empty reference for {source}')
    
    return v
```

### Custom Serializers
```python
class GeneInstance(BaseModel):
    @property
    def display_name(self) -> str:
        """Human-readable display name"""
        return f"{self.gene_symbol} ({self.gene_name})"
    
    def to_research_format(self) -> Dict[str, Any]:
        """Convert to research-friendly format"""
        return {
            'gene': self.gene_symbol,
            'name': self.gene_name,
            'location': self.gene_locus,
            'diseases': self.associated_diseases_count,
            'validated': self.validated_associations_count > 0
        }
``` 