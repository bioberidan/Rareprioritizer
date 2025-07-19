"""
Pydantic models for socioeconomic impact analysis prompts.

This module contains all the data models used for validating
and parsing responses from socioeconomic impact analysis prompts.
"""

from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class EvidenceLevel(str, Enum):
    """Evidence quality levels for socioeconomic impact studies."""
    HIGH = "High evidence"
    MEDIUM_HIGH = "Medium-High evidence"
    MEDIUM = "Medium evidence"
    LOW = "Low evidence"
    NONE = ""


class SocioeconomicScore(int, Enum):
    """Standardized scoring system for socioeconomic impact."""
    HIGH = 10
    MEDIUM_HIGH = 7
    MEDIUM = 5
    LOW = 3
    NONE = 0


class SocioeconomicStudy(BaseModel):
    """Model for individual socioeconomic impact studies."""
    cost: int = Field(default=0, description="Annual mean cost in euros (rounded to integer)")
    measure: str = Field(default="", description="Nature of the cost (e.g., hospitalization, out-of-pocket expenses)")
    label: str = Field(default="", description="Study title or label")
    source: str = Field(default="", description="Verifiable URL (PubMed, DOI, PDF or direct link)")
    country: str = Field(default="", description="Country of the study")
    year: str = Field(default="", description="Year of the study")


class SocioeconomicImpactResponse(BaseModel):
    """Model for the complete socioeconomic impact analysis response."""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")
    socioeconomic_impact_studies: List[SocioeconomicStudy] = Field(
        default_factory=list,
        description="List of relevant studies and reports"
    )
    score: SocioeconomicScore = Field(description="Overall socioeconomic impact score")
    evidence_level: EvidenceLevel = Field(description="Level of evidence supporting the score")
    justification: str = Field(
        default="",
        description="1-3 sentences explaining why this score was assigned"
    )
    
    def is_empty_search(self) -> bool:
        """Check if response represents an empty search result."""
        # Handle both prompt versions:
        # v1: Returns array with one empty object
        # v2: Returns empty array
        
        if self.score != 0 or self.evidence_level != "":
            return False
            
        # Case 1: Empty array (socioeconomic_v2)
        if len(self.socioeconomic_impact_studies) == 0:
            return True
            
        # Case 2: Single empty object (socioeconomic_v1)
        if len(self.socioeconomic_impact_studies) == 1:
            study = self.socioeconomic_impact_studies[0]
            # Check if all fields are empty/zero (indicating empty object)
            return (study.cost == 0 and 
                    study.measure == "" and 
                    study.label == "" and 
                    study.source == "" and 
                    study.country == "" and 
                    study.year == "")
        
        # More than one study means not empty
        return False


# Input validation models
class DiseaseQuery(BaseModel):
    """Model for disease query input."""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")


class SocioeconomicAnalysisRequest(DiseaseQuery):
    """Request model for socioeconomic impact analysis."""
    pass 