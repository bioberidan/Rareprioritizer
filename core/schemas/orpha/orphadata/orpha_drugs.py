"""
Pydantic models for Orphanet drug data processing

These models represent the data structures used in Orpha drug processing,
based on the actual output from Orpha.net drug database API and aggregation pipeline.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DrugInstance(BaseModel):
    """
    Model for individual drug records from Orpha.net
    
    This represents a single drug with all API data and processing metadata.
    """
    drug_id: str = Field(..., description="Drug identifier")
    substance_id: Optional[str] = Field(None, description="Substance identifier")
    drug_name: str = Field(..., description="Drug/substance name")
    
    # Classification and status
    status: str = Field(..., description="Medicinal product, Tradename, etc.")
    drug_type: Optional[str] = Field(None, description="Drug type classification")
    
    # Regional availability
    regions: List[str] = Field(default_factory=list, description="US, EU, Spain, etc.")
    
    # External references and URLs
    substance_url: Optional[str] = Field(None, description="Substance URL")
    regulatory_id: Optional[str] = Field(None, description="Regulatory identifier")
    regulatory_url: Optional[str] = Field(None, description="Regulatory URL")
    
    # Manufacturer and indication
    manufacturer: Optional[str] = Field(None, description="Manufacturer name")
    indication: Optional[str] = Field(None, description="Drug indication")
    
    # Disease associations
    diseases: List[Dict[str, str]] = Field(default_factory=list, description="Associated diseases")
    
    # Additional metadata
    links: List[Dict[str, str]] = Field(default_factory=list, description="Additional links")
    details: List[str] = Field(default_factory=list, description="Additional details")
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['Medicinal product', 'Tradename', 'Substance', 'Unknown']
        if v not in valid_statuses:
            # Allow any status but normalize known ones
            return v
        return v
    
    @validator('regions')
    def validate_regions(cls, v):
        # Normalize region names
        normalized_regions = []
        for region in v:
            if region.upper() in ['US', 'USA', 'UNITED STATES']:
                normalized_regions.append('US')
            elif region.upper() in ['EU', 'EUROPE', 'EUROPEAN UNION']:
                normalized_regions.append('EU')
            else:
                normalized_regions.append(region)
        return normalized_regions


class DrugMapping(BaseModel):
    """
    Model for disease-drug mappings (diseases2drugs.json)
    
    Main mapping structure following codebase conventions
    """
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name for reference")
    
    # Drug associations
    drugs: List[str] = Field(default_factory=list, description="List of drug IDs")
    drugs_count: int = Field(0, description="Total number of drugs")
    
    # Regional drug classification
    eu_tradename_drugs: List[str] = Field(default_factory=list, description="EU tradename drugs")
    usa_tradename_drugs: List[str] = Field(default_factory=list, description="USA tradename drugs")
    all_tradename_drugs: List[str] = Field(default_factory=list, description="All tradename drugs")
    
    eu_medical_products: List[str] = Field(default_factory=list, description="EU medical products")
    usa_medical_products: List[str] = Field(default_factory=list, description="USA medical products")
    all_medical_products: List[str] = Field(default_factory=list, description="All medical products")
    
    # Drug details
    drug_details: List[DrugInstance] = Field(default_factory=list, description="Full drug records")
    
    # Processing metadata
    last_processed_run: Optional[int] = Field(None, description="Last processing run number")
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('drugs_count')
    def validate_drugs_count(cls, v, values):
        # Ensure drugs_count matches length of drugs list
        drugs = values.get('drugs', [])
        return len(drugs)


class DrugStatistics(BaseModel):
    """
    Model for drug processing statistics
    """
    total_diseases_processed: int = Field(0, description="Total diseases processed")
    diseases_with_drugs: int = Field(0, description="Diseases with drugs")
    total_unique_drugs: int = Field(0, description="Total unique drugs")
    
    # Regional statistics
    drugs_available_us: int = Field(0, description="Drugs available in US")
    drugs_available_eu: int = Field(0, description="Drugs available in EU")
    
    # Status distribution
    medicinal_products: int = Field(0, description="Medicinal products")
    tradename_drugs: int = Field(0, description="Tradename drugs")
    substance_entries: int = Field(0, description="Substance entries")
    
    # Coverage metrics
    coverage_percentage: float = Field(0.0, description="Percentage of diseases with drugs")
    mean_drugs_per_disease: float = Field(0.0, description="Average drugs per disease")
    
    # Availability analysis
    us_coverage_percentage: float = Field(0.0, description="Percentage with US drugs")
    eu_coverage_percentage: float = Field(0.0, description="Percentage with EU drugs")
    
    # Processing information
    processing_timestamp: str = Field(..., description="Processing timestamp")
    processing_runs: Dict[str, int] = Field(default_factory=dict, description="Processing runs by run number")
    empty_diseases: List[str] = Field(default_factory=list, description="Diseases without drugs")


class CuratedDrugMapping(BaseModel):
    """
    Model for curated drug data output (final JSON files)
    """
    # Disease information
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: Optional[str] = Field(None, description="Disease name")
    
    # Regional drug lists by type
    eu_tradename_drugs: List[str] = Field(default_factory=list, description="EU tradename drug IDs")
    all_tradename_drugs: List[str] = Field(default_factory=list, description="All tradename drug IDs")
    usa_tradename_drugs: List[str] = Field(default_factory=list, description="USA tradename drug IDs")
    
    eu_medical_product_drugs: List[str] = Field(default_factory=list, description="EU medical product IDs")
    all_medical_product_drugs: List[str] = Field(default_factory=list, description="All medical product IDs")
    usa_medical_product_drugs: List[str] = Field(default_factory=list, description="USA medical product IDs")
    
    # Drug metadata
    drug_names: Dict[str, str] = Field(default_factory=dict, description="Drug ID to name mapping")


class DrugProcessingResult(BaseModel):
    """
    Model for complete drug processing results
    """
    # Core mappings
    diseases2drugs: Dict[str, DrugMapping] = Field(default_factory=dict, description="Disease to drugs mapping")
    drugs2diseases: Dict[str, DrugInstance] = Field(default_factory=dict, description="Drug to diseases mapping")
    drug_index: Dict[str, DrugInstance] = Field(default_factory=dict, description="Drug instances")
    
    # Curated outputs
    curated_mappings: Dict[str, CuratedDrugMapping] = Field(default_factory=dict, description="Curated drug mappings")
    
    # Statistics and metadata
    statistics: DrugStatistics = Field(..., description="Processing statistics")
    processing_summary: Dict[str, Any] = Field(default_factory=dict, description="Processing summary")
    
    # Quality metrics
    data_quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Data quality assessment")


# Type aliases for complex structures
DrugInstances = Dict[str, DrugInstance]
Disease2DrugsMapping = Dict[str, DrugMapping]
Drugs2DiseasesMapping = Dict[str, DrugInstance]
CuratedDrugMappings = Dict[str, CuratedDrugMapping]


# Data validation functions
def validate_drug_data(data: Dict[str, Any], model_type: str) -> bool:
    """
    Validate drug data against appropriate Pydantic model
    
    Args:
        data: Dictionary data to validate
        model_type: Type of model to validate against
        
    Returns:
        bool: True if data is valid
    """
    model_map = {
        'drug_instance': DrugInstance,
        'drug_mapping': DrugMapping,
        'curated_drug_mapping': CuratedDrugMapping,
        'drug_statistics': DrugStatistics,
        'drug_processing_result': DrugProcessingResult
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


# Processing helper functions
def is_tradename_drug(drug: DrugInstance) -> bool:
    """
    Determine if drug is a tradename
    
    Args:
        drug: Drug instance
        
    Returns:
        bool: True if drug is a tradename
    """
    return drug.status == "Tradename"


def is_medical_product(drug: DrugInstance) -> bool:
    """
    Determine if drug is a medicinal product
    
    Args:
        drug: Drug instance
        
    Returns:
        bool: True if drug is a medicinal product
    """
    return drug.status == "Medicinal product"


def is_available_in_region(drug: DrugInstance, region: str) -> bool:
    """
    Determine if drug is available in specified region
    
    Args:
        drug: Drug instance
        region: Region code (US, EU, etc.)
        
    Returns:
        bool: True if drug is available in region
    """
    if region.upper() == "ALL":
        return True
    
    normalized_region = region.upper()
    if normalized_region == "USA":
        normalized_region = "US"
    elif normalized_region in ["EUROPE", "EUROPEAN UNION"]:
        normalized_region = "EU"
    
    return normalized_region in [r.upper() for r in drug.regions]


def filter_drugs_by_criteria(drugs: List[DrugInstance], 
                           status: Optional[str] = None,
                           region: Optional[str] = None) -> List[DrugInstance]:
    """
    Filter drugs by status and region criteria
    
    Args:
        drugs: List of drug instances
        status: Drug status filter (Tradename, Medicinal product, etc.)
        region: Region filter (US, EU, ALL, etc.)
        
    Returns:
        List of filtered drug instances
    """
    filtered_drugs = drugs
    
    if status:
        filtered_drugs = [drug for drug in filtered_drugs if drug.status == status]
    
    if region and region.upper() != "ALL":
        filtered_drugs = [drug for drug in filtered_drugs if is_available_in_region(drug, region)]
    
    return filtered_drugs


def extract_drug_names(drugs2diseases: Dict[str, DrugInstance]) -> Dict[str, str]:
    """
    Extract drug ID to name mapping
    
    Args:
        drugs2diseases: Drugs to diseases mapping
        
    Returns:
        Dict mapping drug IDs to names
    """
    return {
        drug_id: drug_data.drug_name
        for drug_id, drug_data in drugs2diseases.items()
    }


def calculate_regional_coverage(disease_mappings: Dict[str, DrugMapping], region: str) -> float:
    """
    Calculate percentage of diseases with drugs in specified region
    
    Args:
        disease_mappings: Disease to drug mappings
        region: Region to analyze (US, EU, etc.)
        
    Returns:
        float: Coverage percentage
    """
    if not disease_mappings:
        return 0.0
    
    diseases_with_regional_drugs = 0
    
    for disease_mapping in disease_mappings.values():
        has_regional_drugs = False
        
        if region.upper() == "US":
            has_regional_drugs = (len(disease_mapping.usa_tradename_drugs) > 0 or 
                                len(disease_mapping.usa_medical_products) > 0)
        elif region.upper() == "EU":
            has_regional_drugs = (len(disease_mapping.eu_tradename_drugs) > 0 or 
                                len(disease_mapping.eu_medical_products) > 0)
        
        if has_regional_drugs:
            diseases_with_regional_drugs += 1
    
    return (diseases_with_regional_drugs / len(disease_mappings)) * 100.0 