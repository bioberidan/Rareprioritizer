"""
Pydantic models for Orphanet drug data processing (Version 2)

These models represent the updated data structures used in Orpha drug processing,
based on the new boolean-based schema from preprocessed data.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class DrugInstanceV2(BaseModel):
    """
    Model for individual drug records from Orpha.net (Version 2)
    
    Uses boolean flags instead of status strings and region arrays.
    """
    name: str = Field(..., description="Drug/substance name")
    substance_url: Optional[str] = Field(None, description="Substance URL path")
    substance_id: Optional[str] = Field(None, description="Substance identifier")
    regulatory_url: Optional[str] = Field(None, description="Regulatory URL path")
    regulatory_id: Optional[str] = Field(None, description="Regulatory identifier")
    
    # Boolean classification flags
    is_tradename: bool = Field(..., description="True if drug is a tradename")
    is_medical_product: bool = Field(..., description="True if drug is a medical product")
    is_available_in_us: bool = Field(..., description="True if available in US")
    is_available_in_eu: bool = Field(..., description="True if available in EU")
    is_specific: bool = Field(..., description="True if drug is specific to disease")
    
    @validator('substance_id')
    def validate_substance_id(cls, v):
        # Use substance_id or regulatory_id as drug identifier
        return v
    
    def get_drug_id(self) -> str:
        """Get unique drug identifier, preferring substance_id"""
        return self.substance_id or self.regulatory_id or f"drug_{hash(self.name)}"


class DiseaseDataV2(BaseModel):
    """
    Model for disease data with drugs using new schema (Version 2)
    """
    disease_name: str = Field(..., description="Disease name")
    orpha_code: str = Field(..., description="Orphanet disease code")
    drugs: List[DrugInstanceV2] = Field(default_factory=list, description="List of drugs")
    processing_timestamp: str = Field(..., description="Processing timestamp")
    run_number: int = Field(..., description="Processing run number")
    total_drugs_found: int = Field(..., description="Total number of drugs found")
    
    @validator('total_drugs_found')
    def validate_total_drugs_found(cls, v, values):
        # Ensure total_drugs_found matches length of drugs list
        drugs = values.get('drugs', [])
        return len(drugs)


class CurationSummaryV2(BaseModel):
    """
    Model for curation summary statistics (Version 2)
    """
    total_diseases_processed: int = Field(0, description="Total diseases processed")
    diseases_with_drugs: int = Field(0, description="Diseases with drugs")
    total_unique_drugs: int = Field(0, description="Total unique drugs")
    
    # Coverage by drug type and region
    tradename_coverage: Dict[str, int] = Field(default_factory=dict, description="Tradename drug coverage")
    medical_product_coverage: Dict[str, int] = Field(default_factory=dict, description="Medical product coverage")
    
    # Processing metadata
    processing_timestamp: str = Field(..., description="Processing timestamp")
    empty_diseases: List[str] = Field(default_factory=list, description="Diseases without drugs")


# Helper functions for drug filtering
def is_tradename_drug_v2(drug: DrugInstanceV2) -> bool:
    """
    Determine if drug is a tradename
    
    Args:
        drug: Drug instance
        
    Returns:
        bool: True if drug is a tradename
    """
    return drug.is_tradename


def is_medical_product_v2(drug: DrugInstanceV2) -> bool:
    """
    Determine if drug is a medical product
    
    Args:
        drug: Drug instance
        
    Returns:
        bool: True if drug is a medical product
    """
    return drug.is_medical_product


def is_available_in_region_v2(drug: DrugInstanceV2, region: str) -> bool:
    """
    Determine if drug is available in specified region
    
    Args:
        drug: Drug instance
        region: Region code (US, EU, ALL)
        
    Returns:
        bool: True if drug is available in region
    """
    region_upper = region.upper()
    
    if region_upper == "ALL":
        return True
    elif region_upper in ["US", "USA"]:
        return drug.is_available_in_us
    elif region_upper in ["EU", "EUROPE"]:
        return drug.is_available_in_eu
    else:
        return False


def filter_drugs_by_criteria_v2(drugs: List[DrugInstanceV2], 
                               drug_type: str, 
                               region: str) -> List[DrugInstanceV2]:
    """
    Filter drugs by type and region criteria, only including specific drugs
    
    Args:
        drugs: List of drug instances
        drug_type: Drug type filter (tradename, medical_product)
        region: Region filter (US, EU, ALL)
        
    Returns:
        List of filtered drug instances (only specific drugs)
    """
    filtered_drugs = []
    
    for drug in drugs:
        # Only include drugs that are specific
        if not drug.is_specific:
            continue
            
        # Check drug type
        type_match = False
        if drug_type.lower() == "tradename" and is_tradename_drug_v2(drug):
            type_match = True
        elif drug_type.lower() == "medical_product" and is_medical_product_v2(drug):
            type_match = True
        
        # Check region availability
        region_match = is_available_in_region_v2(drug, region)
        
        if type_match and region_match:
            filtered_drugs.append(drug)
    
    return filtered_drugs


def extract_drug_ids_v2(drugs: List[DrugInstanceV2]) -> List[str]:
    """
    Extract drug IDs from list of drug instances
    
    Args:
        drugs: List of drug instances
        
    Returns:
        List of drug IDs
    """
    return [drug.get_drug_id() for drug in drugs]


def create_drug_name_mapping_v2(diseases_data: Dict[str, DiseaseDataV2]) -> Dict[str, str]:
    """
    Create drug ID to name mapping from diseases data, only including specific drugs
    
    Args:
        diseases_data: Dictionary of disease data
        
    Returns:
        Dict mapping drug IDs to names (only specific drugs)
    """
    drug_names = {}
    
    for disease_data in diseases_data.values():
        for drug in disease_data.drugs:
            # Only include drugs that are specific
            if not drug.is_specific:
                continue
                
            drug_id = drug.get_drug_id()
            if drug_id not in drug_names:
                drug_names[drug_id] = drug.name
    
    return drug_names


def validate_disease_data_v2(data: Dict[str, Any]) -> DiseaseDataV2:
    """
    Validate and parse disease data using V2 schema
    
    Args:
        data: Raw disease data dictionary
        
    Returns:
        Validated DiseaseDataV2 instance
        
    Raises:
        ValidationError: If data doesn't match schema
    """
    return DiseaseDataV2(**data) 