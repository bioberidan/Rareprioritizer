"""
Example usage of the Pydantic models for prompt validation and serialization.
"""

import json
from .prompt_models import (
    SocioeconomicImpactResponse, 
    GroupsResponse, 
    SocioeconomicStudy, 
    ResearchGroup, 
    PrincipalInvestigator, 
    Source, 
    Publication,
    SocioeconomicScore,
    EvidenceLevel
)

def create_sample_socioeconomic_response():
    """Create a sample socioeconomic impact response"""
    
    # Create some sample studies
    studies = [
        SocioeconomicStudy(
            cost=25000,
            measure="Annual healthcare costs",
            label="Economic burden of Wilson disease in Spain",
            source="https://pubmed.ncbi.nlm.nih.gov/12345678",
            country="Spain",
            year="2023"
        ),
        SocioeconomicStudy(
            cost=18000,
            measure="Out-of-pocket expenses",
            label="Patient costs in Wilson disease management",
            source="https://doi.org/10.1016/example.2023.01.001",
            country="Germany",
            year="2022"
        )
    ]
    
    # Create the full response
    response = SocioeconomicImpactResponse(
        orphacode="905",
        disease_name="Wilson disease",
        socioeconomic_impact_studies=studies,
        score=SocioeconomicScore.MEDIUM_HIGH,
        evidence_level=EvidenceLevel.MEDIUM_HIGH,
        justification="Medium-High evidence based on peer-reviewed cost-of-illness studies from high-income European countries with comparable healthcare systems."
    )
    
    return response

def create_sample_groups_response():
    """Create a sample CIBERER groups response"""
    
    # Create sample principal investigators
    pis = [
        PrincipalInvestigator(name="Dr. María González", role="Principal Investigator"),
        PrincipalInvestigator(name="Dr. Juan Pérez", role="Co-PI")
    ]
    
    # Create sample sources
    sources = [
        Source(label="CIBERER Annual Report 2023", url="https://www.ciberer.es/annual-report-2023"),
        Source(label="PubMed Publication", url="https://pubmed.ncbi.nlm.nih.gov/87654321")
    ]
    
    # Create sample publications
    publications = [
        Publication(
            pmid="87654321",
            title="Novel therapeutic approaches for Wilson disease",
            year=2023,
            journal="J Med Genet",
            url="https://pubmed.ncbi.nlm.nih.gov/87654321"
        ),
        Publication(
            pmid="11223344",
            title="Genetic screening in Wilson disease patients",
            year=2022,
            journal="Eur J Hum Genet",
            url="https://pubmed.ncbi.nlm.nih.gov/11223344"
        )
    ]
    
    # Create sample research group
    group = ResearchGroup(
        unit_id="U707",
        official_name="Rare Disease Genetics Unit",
        host_institution="Hospital Universitario La Paz",
        city="Madrid",
        principal_investigators=pis,
        justification="This unit has published extensively on Wilson disease genetics and participates in the European Wilson Disease Registry.",
        sources=sources,
        disease_related_publications=publications
    )
    
    # Create the full response
    response = GroupsResponse(
        orphacode="905",
        disease_name="Wilson disease",
        groups=[group]
    )
    
    return response

def validate_json_string():
    """Example of validating JSON string responses"""
    
    # Sample JSON string that might come from LLM
    json_response = '''
    {
        "orphacode": "905",
        "disease_name": "Wilson disease",
        "socioeconomic_impact_studies": [
            {
                "cost": 30000,
                "measure": "Total annual costs",
                "label": "Comprehensive cost analysis of Wilson disease",
                "source": "https://pubmed.ncbi.nlm.nih.gov/example",
                "country": "Spain",
                "year": "2023"
            }
        ],
        "score": 7,
        "evidence_level": "Medium-High evidence",
        "justification": "Based on recent European cost-of-illness studies."
    }
    '''
    
    try:
        # Parse JSON and validate with Pydantic
        data = json.loads(json_response)
        validated_response = SocioeconomicImpactResponse(**data)
        print("✅ JSON validation successful!")
        print(f"Score: {validated_response.score}")
        print(f"Evidence Level: {validated_response.evidence_level}")
        return validated_response
    except Exception as e:
        print(f"❌ JSON validation failed: {e}")
        return None

def main():
    """Main function to demonstrate the models"""
    
    print("=== Socioeconomic Impact Response Example ===")
    socio_response = create_sample_socioeconomic_response()
    print(socio_response.model_dump_json(indent=2))
    
    print("\n=== Groups Response Example ===")
    groups_response = create_sample_groups_response()
    print(groups_response.model_dump_json(indent=2))
    
    print("\n=== JSON Validation Example ===")
    validated = validate_json_string()
    
    # Example of accessing enum values
    print(f"\n=== Enum Values ===")
    print(f"Available scores: {[score.value for score in SocioeconomicScore]}")
    print(f"Available evidence levels: {[level.value for level in EvidenceLevel]}")
    
    # Example of model validation
    print(f"\n=== Model Validation ===")
    try:
        # This should fail validation
        invalid_response = SocioeconomicImpactResponse(
            orphacode="905",
            disease_name="Wilson disease",
            score=999,  # Invalid score
            evidence_level="Invalid level",  # Invalid evidence level
            justification="Test"
        )
    except Exception as e:
        print(f"✅ Validation correctly caught invalid data: {e}")

if __name__ == "__main__":
    main() 