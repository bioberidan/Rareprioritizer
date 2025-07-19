from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class SimpleDisease(BaseModel):
    disease_name: str
    orpha_code: str


class ClinicalTrialResult(BaseModel):
    disease_name: str
    orpha_code: str
    trials: List[Dict]
    processing_timestamp: datetime
    run_number: int
    total_trials_found: int


class ProcessingStatus(BaseModel):
    data_type: str
    run_number: int
    total_diseases: int
    processed_diseases: int
    failed_diseases: List[str]
    start_time: datetime
    end_time: Optional[datetime]


class DrugInfo(BaseModel):
    name: str
    substance_id: Optional[str]
    substance_url: Optional[str]
    regulatory_id: Optional[str]
    regulatory_url: Optional[str]
    status: Optional[str]
    manufacturer: Optional[str]
    indication: Optional[str]
    regions: List[str]
    links: List[Dict]
    details: List[str]


class DrugResult(BaseModel):
    disease_name: str
    orpha_code: str
    drugs: List[Dict]
    processing_timestamp: datetime
    run_number: int
    total_drugs_found: int
    search_url: str
    search_params: Dict 