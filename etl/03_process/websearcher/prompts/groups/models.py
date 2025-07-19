"""
Pydantic models for CIBERER research groups analysis prompts.

This module contains all the data models used for validating
and parsing responses from research groups analysis prompts.
"""

from pydantic import BaseModel, Field
from typing import List


class PrincipalInvestigator(BaseModel):
    """Model for principal investigators."""
    name: str = Field(default="", description="Name of the principal investigator")
    role: str = Field(default="", description="Role (e.g., Principal Investigator, Co-PI)")


class Source(BaseModel):
    """Model for source references."""
    label: str = Field(default="", description="Label or description of the source")
    url: str = Field(default="", description="Direct URL to the source")


class Publication(BaseModel):
    """Model for disease-related publications."""
    pmid: str = Field(default="", description="PubMed ID (empty string for preprints)")
    title: str = Field(default="", description="Exact PubMed title")
    year: int = Field(default=0, description="Official publication year")
    journal: str = Field(default="", description="MEDLINE abbreviation if available")
    url: str = Field(default="", description="Direct PubMed or preprint link")


class ResearchGroup(BaseModel):
    """Model for CIBERER research units."""
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
    """Model for the complete CIBERER groups analysis response."""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")
    groups: List[ResearchGroup] = Field(
        default_factory=list,
        description="List of CIBERER research units connected to the disease"
    )
    
    def is_empty_search(self) -> bool:
        """Check if response represents an empty search result."""
        return len(self.groups) == 0


# Models for GroupsPromptV3 - Simplified structure
class ResearchGroupV3(BaseModel):
    """Simplified model for CIBERER research units in V3."""
    unit_name: str = Field(default="", description="CIBERER unit name (e.g., U123, 'Grupo de enfermedades raras', 'grupo del Dr. Perez')")
    sources: List[Source] = Field(
        default_factory=list,
        description="Direct URLs supporting the unit identification"
    )


class GroupsResponseV3(BaseModel):
    """Model for the complete CIBERER groups analysis response V3."""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")
    groups: List[ResearchGroupV3] = Field(
        default_factory=list,
        description="List of CIBERER research units connected to the disease"
    )
    
    def is_empty_search(self) -> bool:
        """Check if response represents an empty search result."""
        return len(self.groups) == 0


# Input validation models
class DiseaseQuery(BaseModel):
    """Model for disease query input."""
    orphacode: str = Field(description="ORPHA code of the disease")
    disease_name: str = Field(description="Name of the disease")


class GroupsAnalysisRequest(DiseaseQuery):
    """Request model for CIBERER groups analysis."""
    pass 