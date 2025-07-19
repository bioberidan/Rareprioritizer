"""
Pydantic data models for Orpha Disease Preprocessing System
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, RootModel, ConfigDict


class TaxonomyNode(BaseModel):
    """Model for a taxonomy category node"""
    id: str
    name: str
    type: str = Field(..., pattern="^(root_category|category)$")
    level: int = Field(..., ge=0)
    parent_id: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "137",
                "name": "Congenital disorder of glycosylation",
                "type": "category",
                "level": 1,
                "parent_id": "68367",
                "children": ["309347", "309447", "309458"]
            }
        }
    )


class Classification(BaseModel):
    """Model for disease classification information"""
    category_id: str
    path: List[str] = Field(..., min_length=1)
    level: int = Field(..., ge=0)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "category_id": "309347",
                "path": ["68367", "137", "309347"],
                "level": 3
            }
        }
    )


class DiseaseMetadata(BaseModel):
    """Model for disease metadata"""
    expert_link: Optional[str] = None
    last_updated: Optional[str] = None
    disorder_type: Optional[str] = None
    orpha_code: Optional[str] = None
    
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "expert_link": "http://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=en&Expert=79318",
                "last_updated": "2024-12-03",
                "disorder_type": "Disease"
            }
        }
    )


class DiseaseInstance(BaseModel):
    """Model for a disease instance"""
    id: str
    name: str
    type: str = Field(default="disease")
    classification: Classification
    metadata: DiseaseMetadata = Field(default_factory=DiseaseMetadata)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "79318",
                "name": "PMM2-CDG",
                "type": "disease",
                "classification": {
                    "category_id": "309347",
                    "path": ["68367", "137", "309347"],
                    "level": 3
                },
                "metadata": {
                    "expert_link": "http://www.orpha.net/consor/cgi-bin/OC_Exp.php?lng=en&Expert=79318",
                    "last_updated": "2024-12-03",
                    "disorder_type": "Disease"
                }
            }
        }
    )


class TaxonomyRelationship(BaseModel):
    """Model for parent-child relationships in taxonomy"""
    parent: Optional[str] = None
    children: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent": "68367",
                "children": ["309347", "309447"]
            }
        }
    )


class TaxonomyStructure(BaseModel):
    """Model for the complete taxonomy structure"""
    nodes: Dict[str, TaxonomyNode]
    relationships: Dict[str, TaxonomyRelationship]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nodes": {
                    "68367": {
                        "id": "68367",
                        "name": "Rare inborn errors of metabolism",
                        "type": "root_category",
                        "level": 0,
                        "children": ["137"]
                    }
                },
                "relationships": {
                    "137": {
                        "parent": "68367",
                        "children": ["309347"]
                    }
                }
            }
        }
    )


class ClassificationIndex(RootModel[Dict[str, List[str]]]):
    """Model for category to diseases mapping"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "309347": ["79318", "79319", "79320"],
                "309447": ["79321", "79322"]
            }
        }
    )


class NameIndex(RootModel[Dict[str, List[str]]]):
    """Model for name to ID mapping"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "PMM2-CDG": ["79318"],
                "Congenital disorder of glycosylation": ["137"],
                "CDG": ["79318", "79319", "79320"]  # Ambiguous name
            }
        }
    )


class TaxonomyMetadata(BaseModel):
    """Model for taxonomy metadata"""
    version: str
    source_file: str
    generation_date: str
    xml_date: Optional[str] = None
    xml_version: Optional[str] = None
    total_categories: int
    total_diseases: int
    max_depth: int
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "2.0.0",
                "source_file": "Metabolicas.xml",
                "generation_date": "2024-12-05T10:30:00",
                "xml_date": "2024-12-03 07:05:16",
                "xml_version": "1.3.29 / 4.1.7",
                "total_categories": 150,
                "total_diseases": 1200,
                "max_depth": 5
            }
        }
    )


class ValidationResult(BaseModel):
    """Model for validation results"""
    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "issues": [],
                "warnings": ["Disease '12345' has no parent category"]
            }
        }
    )


class Statistics(BaseModel):
    """Model for taxonomy statistics"""
    total_nodes: int
    total_diseases: int
    total_categories: int
    max_depth: int
    avg_diseases_per_category: float
    diseases_by_level: Dict[int, int]
    categories_by_level: Dict[int, int]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_nodes": 1350,
                "total_diseases": 1200,
                "total_categories": 150,
                "max_depth": 5,
                "avg_diseases_per_category": 8.0,
                "diseases_by_level": {
                    "3": 800,
                    "4": 350,
                    "5": 50
                },
                "categories_by_level": {
                    "0": 1,
                    "1": 15,
                    "2": 134
                }
            }
        }
    ) 