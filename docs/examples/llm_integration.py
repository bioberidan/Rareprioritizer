"""
Integration example showing how to use Pydantic models with OpenAI's API
for structured JSON responses.
"""

import os
import json
from typing import Type, TypeVar, Union
from openai import OpenAI
from dotenv import load_dotenv
from .prompt_models import (
    SocioeconomicImpactResponse, 
    GroupsResponse, 
    DiseaseQuery
)

# Load environment variables
load_dotenv()

# Type variable for generic response handling
T = TypeVar('T', bound=Union[SocioeconomicImpactResponse, GroupsResponse])

class LLMClient:
    """Client for structured LLM interactions using Pydantic models"""
    
    def __init__(self):
        api_key = os.getenv('OAI_API_KEY')
        if not api_key:
            raise ValueError("OAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
    
    def get_structured_response(
        self, 
        prompt: str, 
        response_model: Type[T], 
        disease_query: DiseaseQuery,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1
    ) -> T:
        """
        Get structured JSON response using Pydantic model validation
        
        Args:
            prompt: The formatted prompt string
            response_model: Pydantic model class for response validation
            disease_query: Disease information for prompt formatting
            model: OpenAI model to use
            temperature: Response randomness (lower = more deterministic)
            
        Returns:
            Validated Pydantic model instance
        """
        
        # Format prompt with disease information
        formatted_prompt = prompt.format(
            disease_name=disease_query.disease_name,
            orphacode=disease_query.orphacode
        )
        
        # Get JSON schema from Pydantic model
        schema = response_model.model_json_schema()
        
        # Create system message with JSON schema
        system_message = f"""
        You are a biomedical research assistant. Respond with valid JSON that matches this exact schema:
        
        {json.dumps(schema, indent=2)}
        
        Important:
        - Return ONLY the JSON object, no markdown formatting
        - Use empty strings ("") for unknown fields, never null
        - Follow the schema exactly
        """
        
        try:
            # Method 1: Using JSON mode (recommended for most cases)
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}  # Forces JSON output
            )
            
            # Extract and validate JSON response
            json_content = response.choices[0].message.content
            return self._validate_response(json_content, response_model)
            
        except Exception as e:
            raise Exception(f"Error getting structured response: {e}")
    
    def get_structured_response_with_function_calling(
        self, 
        prompt: str, 
        response_model: Type[T], 
        disease_query: DiseaseQuery,
        model: str = "gpt-4o-mini"
    ) -> T:
        """
        Alternative method using function calling for guaranteed structure
        """
        
        # Format prompt with disease information
        formatted_prompt = prompt.format(
            disease_name=disease_query.disease_name,
            orphacode=disease_query.orphacode
        )
        
        # Create function schema from Pydantic model
        function_schema = {
            "name": "submit_analysis",
            "description": f"Submit the {response_model.__name__} analysis",
            "parameters": response_model.model_json_schema()
        }
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a biomedical research assistant."},
                    {"role": "user", "content": formatted_prompt}
                ],
                functions=[function_schema],
                function_call={"name": "submit_analysis"}
            )
            
            # Extract function call arguments
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "submit_analysis":
                arguments = json.loads(function_call.arguments)
                return response_model(**arguments)
            else:
                raise Exception("Function call not found in response")
                
        except Exception as e:
            raise Exception(f"Error with function calling: {e}")
    
    def _validate_response(self, json_content: str, response_model: Type[T]) -> T:
        """
        Validate JSON response against Pydantic model
        """
        try:
            # Parse JSON
            data = json.loads(json_content)
            
            # Validate with Pydantic model
            validated_response = response_model(**data)
            
            return validated_response
            
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {e}\nContent: {json_content}")
        except Exception as e:
            raise Exception(f"Validation error: {e}\nContent: {json_content}")

# Example usage functions
def analyze_socioeconomic_impact(disease_query: DiseaseQuery) -> SocioeconomicImpactResponse:
    """
    Analyze socioeconomic impact of a rare disease
    """
    
    # Your existing prompt from openai_tries.py
    prompt = """Generate a single, well-formed JSON object that assigns a socioeconomic-impact score to a specific rare disease identified by its ORPHA code.
Follow every instruction precisely: add no extra keys, keep the indicated order, and output only the JSON object (no Markdown, no comments).

1 · Gather the best available evidence
Bibliographic search
Query PubMed, Europe PMC, Google Scholar and preprint servers, combining the disease name with terms such as "cost of illness", "economic burden", "cost analysis", "carga económica", etc.

European / international studies
Review pan-European projects (e.g. BURQOL-RD) and cost studies from other high-income countries comparable to Spain.

Patient-organisation reports
Consult documents from recognised groups (FEDER, EURORDIS, national foundations such as "ENSERio").

Qualitative literature
Include publications that describe severe impact on quality of life, dependency or productivity even if they provide no cost figures.

2 · Assign the socioeconomic-impact score
Choose the highest score justified by your evidence:

Score 10 – High evidence: peer-reviewed cost-of-illness study specific to Spain.
Score 7 – Medium-High evidence: peer-reviewed cost-of-illness study from another high-income country or a pan-European analysis.
Score 5 – Medium evidence: quantitative data in a high-quality patient-organisation report (e.g. FEDER).
Score 3 – Low evidence: only qualitative descriptions of severe burden.
Score 0 – No evidence: no relevant information found.

The disease name is: {disease_name}
The ORPHA code is: {orphacode}
"""
    
    client = LLMClient()
    return client.get_structured_response(
        prompt=prompt,
        response_model=SocioeconomicImpactResponse,
        disease_query=disease_query
    )

def analyze_ciberer_groups(disease_query: DiseaseQuery) -> GroupsResponse:
    """
    Analyze CIBERER research groups for a rare disease
    """
    
    # Your existing prompt from openai_tries.py
    prompt = """**Improved Prompt for the Biomedical Text-Mining Assistant**

Your goal is to build a single, well-formed JSON object that maps **every CIBERER research unit (Uxxx) with any connection to {disease_name} (ORPHA:{orphacode})**—even if the group has produced **no** relevant publications.
Follow the steps and JSON schema below **exactly**; add **no extra keys**, keep the **key order**, and output **only** the JSON object (no Markdown, no comments).

### 1 · Identify candidate units
* **Scan the entire public domain of CIBERER** (annual reports, news, press releases, group profiles, "Results" pages, etc.).
* Run comprehensive web searches (Google, Bing, DuckDuckGo) combining **"CIBERER" + "{disease_name}"** and synonyms or genes related to the disease.
* Record **every** unit ID you find, **even when no paper is yet linked**.

### 2 · Collect core metadata for each unit
* **host_institution** – university, research institute, or hospital hosting the group.
* **city** – headquarters city of the host institution.
* **principal_investigators** – *all* PIs or co-PIs; capture their role ("Principal Investigator", "Co-PI", etc.).
* Leave any unknown field as an empty string `""`.

The disease name is: {disease_name}
The ORPHA code is: {orphacode}
"""
    
    client = LLMClient()
    return client.get_structured_response(
        prompt=prompt,
        response_model=GroupsResponse,
        disease_query=disease_query
    )

# Example usage
def main():
    """
    Example usage of the LLM integration
    """
    
    # Define disease query
    disease = DiseaseQuery(
        orphacode="905",
        disease_name="Wilson disease"
    )
    
    print("=== Socioeconomic Impact Analysis ===")
    try:
        socio_result = analyze_socioeconomic_impact(disease)
        print(f"Score: {socio_result.score}")
        print(f"Evidence Level: {socio_result.evidence_level}")
        print(f"Studies Found: {len(socio_result.socioeconomic_impact_studies)}")
        print(f"Justification: {socio_result.justification}")
        
        # Save to file
        with open("socio_result.json", "w", encoding="utf-8") as f:
            f.write(socio_result.model_dump_json(indent=2))
            
    except Exception as e:
        print(f"Error in socioeconomic analysis: {e}")
    
    print("\n=== CIBERER Groups Analysis ===")
    try:
        groups_result = analyze_ciberer_groups(disease)
        print(f"Groups Found: {len(groups_result.groups)}")
        for group in groups_result.groups:
            print(f"- {group.unit_id}: {group.official_name}")
            print(f"  Publications: {len(group.disease_related_publications)}")
        
        # Save to file
        with open("groups_result.json", "w", encoding="utf-8") as f:
            f.write(groups_result.model_dump_json(indent=2))
            
    except Exception as e:
        print(f"Error in groups analysis: {e}")

if __name__ == "__main__":
    main() 