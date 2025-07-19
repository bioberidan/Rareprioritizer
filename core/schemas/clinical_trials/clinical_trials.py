"""
Pydantic models for Clinical Trials data processing

These models represent the data structures used in clinical trials processing,
based on the actual output from ClinicalTrials.gov API and aggregation pipeline.
"""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TrialLocationInfo(BaseModel):
    """
    Model for clinical trial location information
    """
    facility: Optional[str] = Field(None, description="Facility name")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State/Province")
    country: Optional[str] = Field(None, description="Country name")
    zip_code: Optional[str] = Field(None, description="ZIP/Postal code")
    status: Optional[str] = Field(None, description="Location recruitment status")
    
    @validator('country')
    def validate_country(cls, v):
        if v:
            return v.strip()
        return v


class ClinicalTrialInstance(BaseModel):
    """
    Model for individual clinical trial records from ClinicalTrials.gov
    
    This represents a single clinical trial with all API data and processing metadata.
    """
    nct_id: str = Field(..., description="ClinicalTrials.gov NCT identifier")
    brief_title: str = Field(..., description="Brief trial title")
    official_title: Optional[str] = Field(None, description="Official trial title")
    overall_status: str = Field(..., description="RECRUITING, ACTIVE_NOT_RECRUITING, etc.")
    study_type: Optional[str] = Field(None, description="Interventional, Observational, etc.")
    
    # Study design information
    phases: List[str] = Field(default_factory=list, description="Phase I, II, III, IV, N/A")
    interventions: List[str] = Field(default_factory=list, description="Drug, Device, Behavioral, etc.")
    primary_purpose: Optional[str] = Field(None, description="Treatment, Prevention, Diagnostic, etc.")
    
    # Enrollment and timeline
    enrollment: Optional[int] = Field(None, description="Target enrollment number")
    start_date: Optional[str] = Field(None, description="Study start date")
    completion_date: Optional[str] = Field(None, description="Primary completion date")
    
    # Location and accessibility
    locations: List[TrialLocationInfo] = Field(default_factory=list, description="Study locations")
    locations_spain: bool = Field(False, description="Has locations in Spain")
    locations_eu: bool = Field(False, description="Has locations in EU countries")
    
    # Disease associations
    diseases: List[Dict[str, str]] = Field(default_factory=list, description="Associated diseases")
    
    # Study description
    brief_summary: Optional[str] = Field(None, description="Brief study summary")
    detailed_description: Optional[str] = Field(None, description="Detailed study description")
    
    # Contact and administrative
    last_update: Optional[str] = Field(None, description="Last update date")
    study_first_posted: Optional[str] = Field(None, description="First posted date")
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('nct_id')
    def validate_nct_id(cls, v):
        if not v.startswith('NCT'):
            raise ValueError('NCT ID must start with "NCT"')
        return v.upper()
    
    @validator('phases')
    def validate_phases(cls, v):
        valid_phases = ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'N/A', 'Early Phase 1']
        return [phase for phase in v if phase in valid_phases]
    
    @validator('enrollment')
    def validate_enrollment(cls, v):
        if v is not None and v < 0:
            raise ValueError('Enrollment must be non-negative')
        return v


class TrialMapping(BaseModel):
    """
    Model for disease-trial mappings (diseases2clinical_trials.json)
    
    Main mapping structure following codebase conventions
    """
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: str = Field(..., description="Disease name for reference")
    
    # Trial associations
    trials: List[str] = Field(default_factory=list, description="List of NCT IDs")
    trial_details: List[ClinicalTrialInstance] = Field(default_factory=list, description="Full trial records")
    
    # Regional accessibility
    eu_accessible_trials: List[str] = Field(default_factory=list, description="EU accessible trials")
    spanish_accessible_trials: List[str] = Field(default_factory=list, description="Spanish trials")
    
    # Trial classification
    recruiting_trials: List[str] = Field(default_factory=list, description="Currently recruiting trials")
    phase3_trials: List[str] = Field(default_factory=list, description="Phase III trials")
    interventional_trials: List[str] = Field(default_factory=list, description="Interventional trials")
    
    # Statistics
    total_trials: int = Field(0, description="Total number of trials")
    accessibility_score: float = Field(0.0, description="Trial accessibility score 0-100")
    
    # Processing metadata
    processing_metadata: Dict[str, Any] = Field(default_factory=dict, description="Processing metadata")
    
    @validator('accessibility_score')
    def validate_accessibility_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Accessibility score must be between 0 and 100')
        return v


class TrialStatistics(BaseModel):
    """
    Model for trial processing statistics
    """
    total_diseases_processed: int = Field(0, description="Total diseases processed")
    diseases_with_trials: int = Field(0, description="Diseases with trials")
    total_unique_trials: int = Field(0, description="Total unique trials")
    
    # Regional statistics
    trials_with_spain_locations: int = Field(0, description="Trials with Spain locations")
    trials_with_eu_locations: int = Field(0, description="Trials with EU locations")
    
    # Status distribution
    recruiting_trials: int = Field(0, description="Currently recruiting trials")
    active_trials: int = Field(0, description="Active not recruiting trials")
    completed_trials: int = Field(0, description="Completed trials")
    
    # Phase distribution
    phase1_trials: int = Field(0, description="Phase I trials")
    phase2_trials: int = Field(0, description="Phase II trials")
    phase3_trials: int = Field(0, description="Phase III trials")
    phase4_trials: int = Field(0, description="Phase IV trials")
    
    # Coverage metrics
    coverage_percentage: float = Field(0.0, description="Percentage of diseases with trials")
    mean_trials_per_disease: float = Field(0.0, description="Average trials per disease")
    
    # Processing information
    processing_timestamp: str = Field(..., description="Processing timestamp")
    processing_runs: Dict[str, int] = Field(default_factory=dict, description="Processing runs by run number")


class CuratedTrialMapping(BaseModel):
    """
    Model for curated trial data output (final JSON files)
    """
    # Disease information
    orpha_code: str = Field(..., description="Disease Orphanet code")
    disease_name: Optional[str] = Field(None, description="Disease name")
    
    # Regional trial lists
    eu_trials: List[str] = Field(default_factory=list, description="EU accessible trial NCT IDs")
    all_trials: List[str] = Field(default_factory=list, description="All trial NCT IDs")
    spanish_trials: List[str] = Field(default_factory=list, description="Spanish accessible trial NCT IDs")
    
    # Trial metadata
    trial_names: Dict[str, str] = Field(default_factory=dict, description="Trial ID to name mapping")
    
    # Validation
    @validator('eu_trials', 'all_trials', 'spanish_trials')
    def validate_trial_lists(cls, v):
        # Ensure all NCT IDs are valid format
        for nct_id in v:
            if not nct_id.startswith('NCT'):
                raise ValueError(f'Invalid NCT ID format: {nct_id}')
        return v


class TrialProcessingResult(BaseModel):
    """
    Model for complete trial processing results
    """
    # Core mappings
    diseases2trials: Dict[str, TrialMapping] = Field(default_factory=dict, description="Disease to trials mapping")
    trials2diseases: Dict[str, List[str]] = Field(default_factory=dict, description="Trial to diseases mapping")
    trial_index: Dict[str, ClinicalTrialInstance] = Field(default_factory=dict, description="Trial instances")
    
    # Curated outputs
    curated_mappings: Dict[str, CuratedTrialMapping] = Field(default_factory=dict, description="Curated trial mappings")
    
    # Statistics and metadata
    statistics: TrialStatistics = Field(..., description="Processing statistics")
    processing_summary: Dict[str, Any] = Field(default_factory=dict, description="Processing summary")
    
    # Quality metrics
    data_quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Data quality assessment")


# Type aliases for complex structures
TrialInstances = Dict[str, ClinicalTrialInstance]
Disease2TrialsMapping = Dict[str, TrialMapping]
Trials2DiseasesMapping = Dict[str, List[str]]
CuratedTrialMappings = Dict[str, CuratedTrialMapping]


# Data validation functions
def validate_trial_data(data: Dict[str, Any], model_type: str) -> bool:
    """
    Validate trial data against appropriate Pydantic model
    
    Args:
        data: Dictionary data to validate
        model_type: Type of model to validate against
        
    Returns:
        bool: True if data is valid
    """
    model_map = {
        'trial_instance': ClinicalTrialInstance,
        'trial_mapping': TrialMapping,
        'curated_trial_mapping': CuratedTrialMapping,
        'trial_statistics': TrialStatistics,
        'trial_processing_result': TrialProcessingResult
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


def create_eu_countries_list() -> List[str]:
    """
    Get list of EU countries for geographic filtering
    
    Returns:
        List of EU country names
    """
    return [
        "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece",
        "Hungary", "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg",
        "Malta", "Netherlands", "Poland", "Portugal", "Romania", "Slovakia",
        "Slovenia", "Spain", "Sweden"
    ]


# Processing helper functions
def is_eu_accessible_trial(trial: ClinicalTrialInstance) -> bool:
    """
    Determine if trial is accessible from EU countries
    
    Args:
        trial: Clinical trial instance
        
    Returns:
        bool: True if trial has EU locations
    """
    eu_countries = create_eu_countries_list()
    
    for location in trial.locations:
        if location.country in eu_countries:
            return True
    return False


def is_spanish_accessible_trial(trial: ClinicalTrialInstance) -> bool:
    """
    Determine if trial is accessible from Spain
    
    Args:
        trial: Clinical trial instance
        
    Returns:
        bool: True if trial has Spanish locations
    """
    for location in trial.locations:
        if location.country == "Spain":
            return True
    return False


def calculate_accessibility_score(trial_mapping: TrialMapping) -> float:
    """
    Calculate trial accessibility score for a disease
    
    Args:
        trial_mapping: Disease trial mapping
        
    Returns:
        float: Accessibility score 0-100
    """
    if trial_mapping.total_trials == 0:
        return 0.0
    
    # Weight different factors
    spanish_weight = 0.4
    eu_weight = 0.3
    recruiting_weight = 0.2
    phase3_weight = 0.1
    
    spanish_score = len(trial_mapping.spanish_accessible_trials) / trial_mapping.total_trials * 100
    eu_score = len(trial_mapping.eu_accessible_trials) / trial_mapping.total_trials * 100
    recruiting_score = len(trial_mapping.recruiting_trials) / trial_mapping.total_trials * 100
    phase3_score = len(trial_mapping.phase3_trials) / trial_mapping.total_trials * 100
    
    accessibility_score = (
        spanish_score * spanish_weight +
        eu_score * eu_weight +
        recruiting_score * recruiting_weight +
        phase3_score * phase3_weight
    )
    
    return min(accessibility_score, 100.0) 