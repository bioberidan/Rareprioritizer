"""
Simple example showing different methods to get structured JSON responses
from OpenAI's API using Pydantic models.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .prompt_models import SocioeconomicImpactResponse, DiseaseQuery

# Load environment variables
load_dotenv()

def method_1_json_mode():
    """
    Method 1: Using JSON mode (recommended)
    Forces the model to respond with valid JSON
    """
    
    client = OpenAI(api_key=os.getenv('OAI_API_KEY'))
    
    # Create disease query
    disease = DiseaseQuery(orphacode="905", disease_name="Wilson disease")
    
    # Get JSON schema from Pydantic model
    schema = SocioeconomicImpactResponse.model_json_schema()
    
    # System prompt with schema
    system_prompt = f"""
    You are a research assistant. Respond with valid JSON matching this schema:
    
    {json.dumps(schema, indent=2)}
    
    Use empty strings ("") for unknown fields, never null.
    """
    
    # User prompt
    user_prompt = f"""
    Analyze the socioeconomic impact of {disease.disease_name} (ORPHA:{disease.orphacode}).
    Find cost studies and assign a score (0, 3, 5, 7, or 10).
    """
    
    # Call API with JSON mode
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
        response_format={"type": "json_object"}  # This forces JSON output
    )
    
    # Parse and validate response
    json_content = response.choices[0].message.content
    data = json.loads(json_content)
    validated_response = SocioeconomicImpactResponse(**data)
    
    return validated_response

def method_2_function_calling():
    """
    Method 2: Using function calling for guaranteed structure
    """
    
    client = OpenAI(api_key=os.getenv('OAI_API_KEY'))
    
    # Create disease query
    disease = DiseaseQuery(orphacode="905", disease_name="Wilson disease")
    
    # Define function schema from Pydantic model
    function_schema = {
        "name": "submit_analysis",
        "description": "Submit socioeconomic impact analysis",
        "parameters": SocioeconomicImpactResponse.model_json_schema()
    }
    
    # User prompt
    user_prompt = f"""
    Analyze the socioeconomic impact of {disease.disease_name} (ORPHA:{disease.orphacode}).
    Find cost studies and assign a score (0, 3, 5, 7, or 10).
    """
    
    # Call API with function calling
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": user_prompt}
        ],
        functions=[function_schema],
        function_call={"name": "submit_analysis"}
    )
    
    # Extract function call arguments
    function_call = response.choices[0].message.function_call
    if function_call and function_call.name == "submit_analysis":
        arguments = json.loads(function_call.arguments)
        validated_response = SocioeconomicImpactResponse(**arguments)
        return validated_response
    else:
        raise Exception("Function call not found in response")

def method_3_structured_outputs():
    """
    Method 3: Using OpenAI's Structured Outputs (newest method)
    Available with newer models like gpt-4o-mini
    """
    
    client = OpenAI(api_key=os.getenv('OAI_API_KEY'))
    
    # Create disease query
    disease = DiseaseQuery(orphacode="905", disease_name="Wilson disease")
    
    # User prompt
    user_prompt = f"""
    Analyze the socioeconomic impact of {disease.disease_name} (ORPHA:{disease.orphacode}).
    Find cost studies and assign a score (0, 3, 5, 7, or 10).
    """
    
    # Get JSON schema from Pydantic model
    schema = SocioeconomicImpactResponse.model_json_schema()
    
    try:
        # Call API with structured outputs
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "socioeconomic_analysis",
                    "schema": schema
                }
            }
        )
        
        # Parse and validate response
        json_content = response.choices[0].message.content
        data = json.loads(json_content)
        validated_response = SocioeconomicImpactResponse(**data)
        
        return validated_response
        
    except Exception as e:
        print(f"Structured outputs not available: {e}")
        # Fallback to JSON mode
        return method_1_json_mode()

def compare_methods():
    """
    Compare different methods for getting structured JSON
    """
    
    methods = [
        ("JSON Mode", method_1_json_mode),
        ("Function Calling", method_2_function_calling),
        ("Structured Outputs", method_3_structured_outputs)
    ]
    
    for method_name, method_func in methods:
        print(f"\n=== {method_name} ===")
        try:
            result = method_func()
            print(f"✅ Success!")
            print(f"Score: {result.score}")
            print(f"Evidence Level: {result.evidence_level}")
            print(f"Studies: {len(result.socioeconomic_impact_studies)}")
            
            # Save result
            filename = f"result_{method_name.lower().replace(' ', '_')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result.model_dump_json(indent=2))
                
        except Exception as e:
            print(f"❌ Error: {e}")

# Quick validation example
def validate_existing_json():
    """
    Example of validating existing JSON with Pydantic models
    """
    
    # Sample JSON response (could come from any source)
    json_response = {
        "orphacode": "905",
        "disease_name": "Wilson disease",
        "socioeconomic_impact_studies": [
            {
                "cost": 25000,
                "measure": "Annual healthcare costs",
                "label": "Economic burden study",
                "source": "https://pubmed.ncbi.nlm.nih.gov/12345",
                "country": "Spain",
                "year": "2023"
            }
        ],
        "score": 7,
        "evidence_level": "Medium-High evidence",
        "justification": "Based on Spanish cost-of-illness study"
    }
    
    try:
        # Validate with Pydantic
        validated = SocioeconomicImpactResponse(**json_response)
        print("✅ JSON validation successful!")
        print(f"Validated score: {validated.score}")
        return validated
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return None

if __name__ == "__main__":
    
    print("=== OpenAI API + Pydantic Integration Examples ===")
    
    # Test validation first
    print("\n1. Testing JSON validation:")
    validate_existing_json()
    
    # Compare API methods
    print("\n2. Comparing API methods:")
    compare_methods()
    
    print("\n=== Summary ===")
    print("✅ JSON Mode: Most reliable, forces JSON output")
    print("✅ Function Calling: Guaranteed structure, works with older models")
    print("✅ Structured Outputs: Newest method, best for complex schemas")
    print("✅ Pydantic validation: Ensures data integrity") 