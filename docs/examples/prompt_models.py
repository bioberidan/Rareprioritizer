from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum

class EvidenceLevel(str, Enum):
    HIGH = "High evidence"
    MEDIUM_HIGH = "Medium-High evidence"
    MEDIUM = "Medium evidence"
    LOW = "Low evidence"
    NONE = ""

class SocioeconomicScore(int, Enum):
    HIGH = 10
    MEDIUM_HIGH = 7
    MEDIUM = 5
    LOW = 3
    NONE = 0

class SocioeconomicStudy(BaseModel):
    """Model for individual socioeconomic impact studies"""
    cost: int = Field(default=0, description="Annual mean cost in euros (rounded to integer)")
    measure: str = Field(default="", description="Nature of the cost (e.g., hospitalization, out-of-pocket expenses)")
    label: str = Field(default="", description="Study title or label")
    source: str = Field(default="", description="Verifiable URL (PubMed, DOI, PDF or direct link)")
    country: str = Field(default="", description="Country of the study")
    year: str = Field(default="", description="Year of the study")

class SocioeconomicImpactResponse(BaseModel):
    """Model for the complete socioeconomic impact analysis response"""
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

class PrincipalInvestigator(BaseModel):
    """Model for principal investigators"""
    name: str = Field(default="", description="Name of the principal investigator")
    role: str = Field(default="", description="Role (e.g., Principal Investigator, Co-PI)")

class Source(BaseModel):
    """Model for source references"""
    label: str = Field(default="", description="Label or description of the source")
    url: str = Field(default="", description="Direct URL to the source")

class Publication(BaseModel):
    """Model for disease-related publications"""
    pmid: str = Field(default="", description="PubMed ID (empty string for preprints)")
    title: str = Field(default="", description="Exact PubMed title")
    year: int = Field(default=0, description="Official publication year")
    journal: str = Field(default="", description="MEDLINE abbreviation if available")
    url: str = Field(default="", description="Direct PubMed or preprint link")

class ResearchGroup(BaseModel):
    """Model for CIBERER research units"""
    unit_id: str = Field(default="", description="CIBERER unit identifier (e.g., Uxxx)")
    official_name: str = Field(default="", description="Official name of the research unit")
    host_institution: str = Field(default="", description="University, research institute, or hospital")
    city: str = Field(default="", description="Headquarters city of the host institution")
    principal_investigators: List[PrincipalInvestigator] = Field(
        default_factory=list,
        description="All PIs or co-PIs"
    )
    justification: str = Field(default="", description="Why this unit is linked to the disease")
    sources: List[Source] = Field(
        default_factory=list,
        description="Direct URLs supporting the justification"
    )
    disease_related_publications: List[Publication] = Field(
        default_factory=list,
        description="Publications related to the disease"
    )

class GroupsResponse(BaseModel):
    """Model for the complete CIBERER groups analysis response"""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")
    groups: List[ResearchGroup] = Field(
        default_factory=list,
        description="List of CIBERER research units connected to the disease"
    )

# Additional utility models for request/input validation
class DiseaseQuery(BaseModel):
    """Model for disease query input"""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")
    
class SocioeconomicAnalysisRequest(DiseaseQuery):
    """Request model for socioeconomic impact analysis"""
    pass

class GroupsAnalysisRequest(DiseaseQuery):
    """Request model for CIBERER groups analysis"""
    pass 