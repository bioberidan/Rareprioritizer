"""
Pydantic models for Orphanet prevalence data processing

These models represent the data structures used in prevalence preprocessing,
based on the actual output from tools/prevalence_preprocessing.py
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class PrevalenceInstance(BaseModel):
    """
    Model for individual prevalence records from en_product9_prev.xml
    
    This represents a single prevalence record with all XML data and calculated metrics.
    """
    prevalence_id: str = Field(..., description="XML Prevalence/@id")
    orpha_code: str = Field(..., description="Disease OrphaCode")
    disease_name: str = Field(..., description="Disease name for reference")
    
    # Core prevalence data from XML
    source: str = Field(..., description="Source element (contains PMID references)")
    prevalence_type: str = Field(..., description="Point prevalence, Prevalence at birth, Annual incidence, Cases/families")
    prevalence_class: Optional[str] = Field(None, description="1-9 / 1 000 000, <1 / 1 000 000, Unknown, etc.")
    qualification: str = Field(..., description="Value and class, Class only, Case(s)")
    val_moy: Optional[float] = Field(None, description="Numeric prevalence value from XML, value moyen in french")
    geographic_area: str = Field(..., description="Europe, Spain, Worldwide, Japan, etc.")
    validation_status: str = Field(..., description="Validated, Not yet validated")
    
    # Calculated reliability metrics
    reliability_score: float = Field(..., description="Calculated reliability score 0-10")
    is_fiable: bool = Field(..., description="Meets reliability criteria (≥6.0 score)")
    
    # Processed data
    per_million_estimate: Optional[float] = Field(None, description="Standardized per-million estimate")
    
    @validator('reliability_score')
    def validate_reliability_score(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Reliability score must be between 0 and 10')
        return v
    
    @validator('prevalence_type')
    def validate_prevalence_type(cls, v):
        valid_types = ["Point prevalence", "Prevalence at birth", "Annual incidence", "Cases/families"]
        if v not in valid_types:
            raise ValueError(f'Prevalence type must be one of: {valid_types}')
        return v
    
    @validator('validation_status')
    def validate_validation_status(cls, v):
        valid_statuses = ["Validated", "Not yet validated", ""]
        if v not in valid_statuses:
            raise ValueError(f'Validation status must be one of: {valid_statuses}')
        return v


class ReliabilityScore(BaseModel):
    """
    Model for detailed reliability scoring breakdown
    
    Used in reliability/reliability_scores.json
    """
    prevalence_id: str = Field(..., description="Reference to prevalence record")
    reliability_score: float = Field(..., description="Overall reliability score 0-10")
    is_fiable: bool = Field(..., description="Meets fiable threshold (≥6.0)")
    
    score_breakdown: Dict[str, Union[str, bool]] = Field(..., description="Detailed scoring criteria")
    
    @validator('score_breakdown')
    def validate_score_breakdown(cls, v):
        required_keys = ["validation_status", "has_pmid", "qualification", "prevalence_type", "geographic_specificity"]
        for key in required_keys:
            if key not in v:
                raise ValueError(f'Score breakdown must include: {required_keys}')
        return v


class MeanCalculationMetadata(BaseModel):
    """Metadata for weighted mean calculation"""
    mean_value_per_million: float = Field(..., description="Calculated weighted mean")
    valid_records_count: int = Field(..., description="Records used in calculation")
    calculation_method: str = Field(..., description="Method used for calculation")
    total_records_count: int = Field(..., description="Total records for this disease")
    weight_sum: float = Field(..., description="Sum of reliability weights")
    excluded_records: Dict[str, int] = Field(default_factory=dict, description="Count of excluded records by reason")
    weight_distribution: Dict[str, float] = Field(default_factory=dict, description="Min/max/mean weight statistics")


class DiseaseStatistics(BaseModel):
    """Statistics for a disease's prevalence records"""
    total_records: int = Field(..., description="Total number of prevalence records")
    reliable_records: int = Field(..., description="Number of reliable records (≥6.0 score)")
    valid_for_mean: int = Field(0, description="Number of records valid for mean calculation")


class DiseasePrevalenceMapping(BaseModel):
    """
    Model for OrphaCode-to-prevalence relationships (disease2prevalence.json)
    
    Main mapping structure following codebase conventions
    """
    orpha_code: str = Field(..., description="OrphaCode as primary identifier")
    disease_name: str = Field(..., description="Disease name for reference")
    
    # All prevalence records for this disease
    prevalence_records: List[PrevalenceInstance] = Field(default_factory=list, description="All prevalence records")
    
    # Reliability-based selection
    most_reliable_prevalence: Optional[PrevalenceInstance] = Field(None, description="Highest reliability score record")
    validated_prevalences: List[PrevalenceInstance] = Field(default_factory=list, description="Only validated records")
    
    # Geographic breakdown
    regional_prevalences: Dict[str, List[PrevalenceInstance]] = Field(default_factory=dict, description="Records by geographic area")
    
    # Weighted mean calculation (NEW)
    mean_value_per_million: float = Field(0.0, description="Reliability-weighted mean prevalence estimate")
    mean_calculation_metadata: MeanCalculationMetadata = Field(default_factory=dict, description="Calculation details and metadata")
    
    # Statistics
    statistics: DiseaseStatistics = Field(..., description="Statistics for this disease")
    
    @validator('statistics', pre=True)
    def create_statistics(cls, v, values):
        if isinstance(v, dict):
            return DiseaseStatistics(**v)
        return v


class OrphaIndex(BaseModel):
    """
    Model for optimized OrphaCode lookup (orpha_index.json)
    
    Lightweight index for fast lookups
    """
    disease_name: str = Field(..., description="Disease name")
    total_prevalence_records: int = Field(..., description="Total number of prevalence records")
    reliable_records: int = Field(..., description="Number of reliable records")
    geographic_areas: List[str] = Field(default_factory=list, description="List of geographic areas")


class RegionalSummary(BaseModel):
    """
    Model for regional summary statistics (regional_data/regional_summary.json)
    """
    total_records: int = Field(..., description="Total prevalence records in this region")
    reliable_records: int = Field(..., description="Reliable records in this region")
    diseases: int = Field(..., description="Number of diseases with prevalence data in this region")


class PrevalenceClassMapping(BaseModel):
    """
    Model for prevalence class standardization (cache/prevalence_classes.json)
    """
    per_million_min: float = Field(..., description="Minimum per-million estimate")
    per_million_max: float = Field(..., description="Maximum per-million estimate")
    
    @validator('per_million_min', 'per_million_max')
    def validate_per_million(cls, v):
        if v < 0:
            raise ValueError('Per-million values must be non-negative')
        return v


class GeographicIndex(BaseModel):
    """
    Model for geographic area groupings (cache/geographic_index.json)
    """
    diseases: List[str] = Field(default_factory=list, description="List of OrphaCodes in this region")
    total_records: int = Field(..., description="Total records in this region")


class DataQualityMetrics(BaseModel):
    """Data quality metrics for validation report"""
    total_records: int = Field(..., description="Total prevalence records processed")
    reliable_records: int = Field(..., description="Records meeting reliability threshold")
    reliability_percentage: float = Field(..., description="Percentage of reliable records")
    validated_records: int = Field(..., description="Records with 'Validated' status")


class ValidationReport(BaseModel):
    """
    Model for data quality assessment (reliability/validation_report.json)
    """
    processing_timestamp: str = Field(..., description="ISO timestamp of processing")
    
    data_quality_metrics: DataQualityMetrics = Field(..., description="Quality metrics")
    geographic_distribution: Dict[str, int] = Field(default_factory=dict, description="Records by region")
    validation_status_distribution: Dict[str, int] = Field(default_factory=dict, description="Records by validation status")
    prevalence_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Records by prevalence type")
    
    @validator('data_quality_metrics', pre=True)
    def create_data_quality_metrics(cls, v):
        if isinstance(v, dict):
            return DataQualityMetrics(**v)
        return v


class ProcessingStatistics(BaseModel):
    """
    Model for processing statistics (cache/statistics.json)
    """
    total_disorders: int = Field(..., description="Total disorders processed")
    disorders_with_prevalence: int = Field(..., description="Disorders with prevalence data")
    total_prevalence_records: int = Field(..., description="Total prevalence records")
    reliable_records: int = Field(..., description="Reliable records count")
    
    geographic_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by region")
    validation_status_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by validation")
    prevalence_type_distribution: Dict[str, int] = Field(default_factory=dict, description="Distribution by type")
    
    processing_timestamp: str = Field(..., description="Processing timestamp")
    file_sizes: Optional[Dict[str, str]] = Field(None, description="Generated file sizes")
    total_size_mb: Optional[str] = Field(None, description="Total output size")


# Type aliases for complex structures
PrevalenceInstances = Dict[str, PrevalenceInstance]
Disease2PrevalenceMapping = Dict[str, DiseasePrevalenceMapping]
Prevalence2DiseasesMapping = Dict[str, List[str]]
OrphaIndexMapping = Dict[str, OrphaIndex]
RegionalSummaryMapping = Dict[str, RegionalSummary]
PrevalenceClassMappings = Dict[str, PrevalenceClassMapping]
GeographicIndexMapping = Dict[str, GeographicIndex]
ReliabilityScores = Dict[str, ReliabilityScore]


# Data validation functions
def validate_prevalence_data(data: Dict[str, Any], model_type: str) -> bool:
    """
    Validate prevalence data against appropriate Pydantic model
    
    Args:
        data: Dictionary data to validate
        model_type: Type of model to validate against
        
    Returns:
        bool: True if data is valid
    """
    model_map = {
        'prevalence_instance': PrevalenceInstance,
        'disease_prevalence_mapping': DiseasePrevalenceMapping,
        'orpha_index': OrphaIndex,
        'regional_summary': RegionalSummary,
        'reliability_score': ReliabilityScore,
        'validation_report': ValidationReport
    }
    
    if model_type not in model_map:
        raise ValueError(f"Unknown model type: {model_type}")
    
    try:
        model_class = model_map[model_type]
        if isinstance(data, dict):
            model_class(**data)
        elif isinstance(data, list):
            for item in data:
                model_class(**item)
        return True
    except Exception as e:
        print(f"Validation error for {model_type}: {e}")
        return False


# Utility functions for model creation
def create_prevalence_instance(xml_data: Dict[str, Any], orpha_code: str, disease_name: str) -> PrevalenceInstance:
    """Create PrevalenceInstance from XML data"""
    return PrevalenceInstance(
        prevalence_id=xml_data.get('id', ''),
        orpha_code=orpha_code,
        disease_name=disease_name,
        source=xml_data.get('source', ''),
        prevalence_type=xml_data.get('prevalence_type', ''),
        prevalence_class=xml_data.get('prevalence_class'),
        qualification=xml_data.get('qualification', ''),
        val_moy=xml_data.get('val_moy'),
        geographic_area=xml_data.get('geographic_area', ''),
        validation_status=xml_data.get('validation_status', ''),
        reliability_score=xml_data.get('reliability_score', 0.0),
        is_fiable=xml_data.get('is_fiable', False),
        per_million_estimate=xml_data.get('per_million_estimate')
    )


def create_disease_prevalence_mapping(orpha_code: str, disease_name: str, 
                                    prevalence_records: List[PrevalenceInstance]) -> DiseasePrevalenceMapping:
    """Create DiseasePrevalenceMapping from prevalence records"""
    # Find most reliable
    most_reliable = max(prevalence_records, key=lambda x: x.reliability_score) if prevalence_records else None
    
    # Filter validated
    validated = [r for r in prevalence_records if r.validation_status == "Validated"]
    
    # Group by region
    regional = {}
    for record in prevalence_records:
        region = record.geographic_area or "Unknown"
        if region not in regional:
            regional[region] = []
        regional[region].append(record)
    
    # Statistics
    stats = DiseaseStatistics(
        total_records=len(prevalence_records),
        reliable_records=len([r for r in prevalence_records if r.is_fiable])
    )
    
    return DiseasePrevalenceMapping(
        orpha_code=orpha_code,
        disease_name=disease_name,
        prevalence_records=prevalence_records,
        most_reliable_prevalence=most_reliable,
        validated_prevalences=validated,
        regional_prevalences=regional,
        statistics=stats
    ) 