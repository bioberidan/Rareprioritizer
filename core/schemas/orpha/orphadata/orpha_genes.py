"""
Pydantic models for Orphanet gene data processing

These models represent the data structures used in gene preprocessing,
following the patterns established in the prevalence system.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class GeneInstance(BaseModel):
    """
    Model for individual gene records from en_product6.xml
    
    This represents a single gene with all XML data and calculated metrics.
    """
    gene_id: str = Field(..., description="XML Gene/@id")
    gene_symbol: str = Field(..., description="Official gene symbol (e.g., KIF7)")
    gene_name: str = Field(..., description="Full gene name")
    gene_type: str = Field(..., description="Gene type classification")
    gene_locus: Optional[str] = Field(None, description="Chromosomal location (e.g., 15q26.1)")
    gene_synonyms: List[str] = Field(default_factory=list, description="List of gene synonyms")
    external_references: Dict[str, str] = Field(default_factory=dict, description="External database references")
    
    # Calculated metrics
    associated_diseases_count: int = Field(0, description="Number of associated diseases")
    validated_associations_count: int = Field(0, description="Number of validated associations")
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
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
                    "ClinVar": "KIF7"
                },
                "associated_diseases_count": 3,
                "validated_associations_count": 2,
                "processing_metadata": {
                    "first_seen": "2024-01-15T10:30:00Z",
                    "data_quality_score": 9.2,
                    "validation_status": "complete"
                }
            }
        }


class GeneAssociationInstance(BaseModel):
    """
    Model for individual gene-disease association records
    
    This represents a single gene-disease association with all validation data.
    """
    gene_association_id: str = Field(..., description="Unique association identifier")
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    
    # Gene information
    gene_id: str = Field(..., description="Gene identifier")
    gene_symbol: str = Field(..., description="Gene symbol")
    gene_name: str = Field(..., description="Gene full name")
    gene_type: str = Field(..., description="Gene type classification")
    gene_locus: Optional[str] = Field(None, description="Chromosomal location")
    gene_synonyms: List[str] = Field(default_factory=list, description="Gene synonyms")
    
    # Association details
    association_type: str = Field(..., description="Type of gene-disease association")
    association_status: str = Field(..., description="Status of association assessment")
    source_validation: str = Field(..., description="Source validation (PMID references)")
    
    # Calculated metrics
    reliability_score: float = Field(..., description="Calculated reliability score 0-10")
    is_validated: bool = Field(..., description="Meets validation criteria (≥6.0 score)")
    
    # External references
    external_references: Dict[str, str] = Field(default_factory=dict, description="External database references")
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('reliability_score')
    def validate_reliability_score(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Reliability score must be between 0 and 10')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "gene_association_id": "assoc_166024_KIF7",
                "orpha_code": "166024",
                "disease_name": "Multiple epiphyseal dysplasia-macrocephaly-facial dysmorphism syndrome",
                "gene_id": "20160",
                "gene_symbol": "KIF7",
                "gene_name": "kinesin family member 7",
                "gene_type": "gene with protein product",
                "gene_locus": "15q26.1",
                "gene_synonyms": ["JBTS12"],
                "association_type": "Disease-causing germline mutation(s) in",
                "association_status": "Assessed",
                "source_validation": "22587682[PMID]",
                "reliability_score": 8.5,
                "is_validated": True,
                "external_references": {
                    "HGNC": "30497",
                    "OMIM": "611254",
                    "Ensembl": "ENSG00000166813"
                },
                "processing_metadata": {
                    "xml_disorder_id": "17601",
                    "xml_gene_id": "20160",
                    "processed_timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }


class DiseaseAssociation(BaseModel):
    """
    Model for disease association within gene records
    """
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    association_type: str = Field(..., description="Type of association")
    association_status: str = Field(..., description="Association status")
    reliability_score: float = Field(..., description="Reliability score")
    source_validation: str = Field(..., description="Source validation")
    
    @validator('reliability_score')
    def validate_reliability_score(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Reliability score must be between 0 and 10')
        return v


class GeneAssociationStatistics(BaseModel):
    """
    Model for gene association statistics
    """
    association_types: Dict[str, int] = Field(default_factory=dict, description="Association type counts")
    mean_reliability_score: float = Field(0.0, description="Mean reliability score")
    total_associations: int = Field(0, description="Total number of associations")
    validated_associations: int = Field(0, description="Number of validated associations")


class Gene2DiseasesMapping(BaseModel):
    """
    Model for gene-to-diseases mappings
    """
    gene_id: str = Field(..., description="Gene identifier")
    gene_symbol: str = Field(..., description="Gene symbol")
    gene_name: str = Field(..., description="Gene full name")
    gene_type: str = Field(..., description="Gene type")
    gene_locus: Optional[str] = Field(None, description="Chromosomal location")
    gene_synonyms: List[str] = Field(default_factory=list, description="Gene synonyms")
    
    # Disease associations
    associated_diseases: List[DiseaseAssociation] = Field(default_factory=list, description="Associated diseases")
    total_disease_associations: int = Field(0, description="Total disease associations")
    validated_associations: int = Field(0, description="Validated associations")
    
    # External references
    external_references: Dict[str, str] = Field(default_factory=dict, description="External database references")
    
    # Statistics
    statistics: GeneAssociationStatistics = Field(default_factory=GeneAssociationStatistics, description="Association statistics")


class GeneAssociationSummary(BaseModel):
    """
    Model for gene association summary within disease records
    """
    gene_association_id: str = Field(..., description="Association identifier")
    gene_id: str = Field(..., description="Gene identifier")
    gene_symbol: str = Field(..., description="Gene symbol")
    gene_name: str = Field(..., description="Gene name")
    association_type: str = Field(..., description="Association type")
    association_status: str = Field(..., description="Association status")
    source_validation: str = Field(..., description="Source validation")
    reliability_score: float = Field(..., description="Reliability score")
    is_validated: bool = Field(..., description="Is validated")
    gene_locus: Optional[str] = Field(None, description="Gene locus")
    gene_type: str = Field(..., description="Gene type")
    external_references: Dict[str, str] = Field(default_factory=dict, description="External references")


class DiseaseStatistics(BaseModel):
    """
    Model for disease-level statistics
    """
    total_associations: int = Field(0, description="Total gene associations")
    validated_associations: int = Field(0, description="Validated associations")
    mean_reliability_score: float = Field(0.0, description="Mean reliability score")


class Disease2GenesMapping(BaseModel):
    """
    Model for disease-to-genes mappings
    """
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    gene_associations: List[GeneAssociationSummary] = Field(default_factory=list, description="Gene associations")
    primary_gene: Optional[str] = Field(None, description="Primary gene (highest reliability)")
    total_gene_associations: int = Field(0, description="Total gene associations")
    validated_associations: int = Field(0, description="Validated associations")
    statistics: DiseaseStatistics = Field(default_factory=DiseaseStatistics, description="Disease statistics")


class OrphaIndexEntry(BaseModel):
    """
    Model for Orpha index entries
    """
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name")
    gene_count: int = Field(0, description="Number of associated genes")
    primary_gene: Optional[str] = Field(None, description="Primary gene")
    validated_genes: int = Field(0, description="Number of validated gene associations")
    mean_reliability: float = Field(0.0, description="Mean reliability score")


class ExternalReferenceEntry(BaseModel):
    """
    Model for external reference entries
    """
    gene_symbol: str = Field(..., description="Gene symbol")
    reference: str = Field(..., description="External reference identifier")
    source: str = Field(..., description="Reference source database")


class ValidationSummary(BaseModel):
    """
    Model for validation summary statistics
    """
    total_associations: int = Field(0, description="Total associations")
    validated_associations: int = Field(0, description="Validated associations")
    validation_percentage: float = Field(0.0, description="Validation percentage")
    reliability_distribution: Dict[str, int] = Field(default_factory=dict, description="Reliability score distribution")
    source_validation_stats: Dict[str, int] = Field(default_factory=dict, description="Source validation statistics")


class GeneTypeDistribution(BaseModel):
    """
    Model for gene type distribution
    """
    gene_type: str = Field(..., description="Gene type")
    count: int = Field(0, description="Count of genes")
    percentage: float = Field(0.0, description="Percentage of total")


class ProcessingStatistics(BaseModel):
    """
    Model for processing statistics
    """
    total_disorders: int = Field(0, description="Total disorders processed")
    disorders_with_genes: int = Field(0, description="Disorders with gene associations")
    total_gene_associations: int = Field(0, description="Total gene associations")
    unique_genes: int = Field(0, description="Number of unique genes")
    validated_associations: int = Field(0, description="Validated associations")
    
    # Distributions
    association_types: Dict[str, int] = Field(default_factory=dict, description="Association type distribution")
    gene_types: Dict[str, int] = Field(default_factory=dict, description="Gene type distribution")
    external_reference_coverage: Dict[str, int] = Field(default_factory=dict, description="External reference coverage")
    reliability_distribution: Dict[str, int] = Field(default_factory=dict, description="Reliability distribution")
    
    # Metadata
    processing_timestamp: str = Field(..., description="Processing timestamp")
    
    @validator('processing_timestamp')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('Invalid timestamp format')
        return v


class GeneProcessingResult(BaseModel):
    """
    Model for complete gene processing results
    """
    statistics: ProcessingStatistics = Field(..., description="Processing statistics")
    disease2genes: Dict[str, Disease2GenesMapping] = Field(default_factory=dict, description="Disease to genes mapping")
    gene2diseases: Dict[str, Gene2DiseasesMapping] = Field(default_factory=dict, description="Gene to diseases mapping")
    gene_instances: Dict[str, GeneInstance] = Field(default_factory=dict, description="Gene instances")
    gene_association_instances: Dict[str, GeneAssociationInstance] = Field(default_factory=dict, description="Association instances")
    orpha_index: Dict[str, OrphaIndexEntry] = Field(default_factory=dict, description="Orpha index")


# Type aliases for convenience
GeneSymbol = str
OrphaCode = str
GeneId = str
AssociationId = str

# Common validation patterns
ORPHA_CODE_PATTERN = r'^\d+$'
GENE_SYMBOL_PATTERN = r'^[A-Z0-9-]+$'
PMID_PATTERN = r'\d+\[PMID\]' 