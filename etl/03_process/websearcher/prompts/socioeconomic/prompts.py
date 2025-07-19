"""
Socioeconomic impact analysis prompts.

This module contains prompt implementations for analyzing the socioeconomic
impact of rare diseases, including cost-of-illness studies and economic burden analysis.
"""

from typing import Type
from utils.prompts import BasePrompt, register_prompt
from .models import SocioeconomicImpactResponse


@register_prompt
class SocioeconomicPromptV1(BasePrompt):
    """
    Version 1 of the socioeconomic impact analysis prompt.
    
    This prompt analyzes the economic burden of rare diseases by:
    - Searching for cost-of-illness studies
    - Evaluating evidence quality 
    - Assigning standardized impact scores (0-10)
    - Documenting supporting literature
    """
    
    @property
    def alias(self) -> str:
        return "socioeconomic_v1"
    
    @property
    def template(self) -> str:
        return """Generate a single, well-formed JSON object that assigns a socioeconomic-impact score to a specific rare disease identified by its ORPHA code.
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

3 · Document all evidence found
socioeconomic_impact_studies (array): list every key reference, even those with lower evidence levels. Each entry must include:

cost: annual mean cost in euros (rounded to an integer) reported by that study / report (enter 0 if not provided).
measure: nature of the cost, e.g. cost of hospitalisation, family out-of-pocket expenses...
label: label of the study, usually the title.
source: verifiable URL (PubMed, DOI, PDF or direct link to the report).
country: country of the study.  
year: year of the study.

score: the single score chosen (10, 7, 5, 3 or 0).

evidence_level: the evidence label ("High evidence", "Medium-High", etc.) corresponding to the chosen score.

justification: 1-3 sentences explaining why this score was assigned (type of study, country, year, population, cost category, etc.).

If no evidence exists, set score = 0, leave evidence_level and justification as empty strings, and let socioeconomic_impact_studies contain exactly one empty object (all fields blank, including measure):

{{
  "cost": 0,
  "measure": "",
  "label": "",
  "source": "",
  "country": "",
  "year": ""
}}

4 · Output format
Return only the JSON object below, using double quotes and empty strings ("") for unknown fields (never null).
If multiple diseases are requested later, return an array of objects with this same structure (only if explicitly asked).

{{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "socioeconomic_impact_studies": [
    {{
      "cost": 0,
      "measure": "",
      "label": "",
      "source": "",
      "country": "",
      "year": ""
    }}
  ],
  "score": 0,
  "evidence_level": "",
  "justification": ""
}}

The disease name is: {disease_name}
The ORPHA code is: {orphacode}"""
    
    @property
    def model(self) -> Type[SocioeconomicImpactResponse]:
        return SocioeconomicImpactResponse


@register_prompt 
class SocioeconomicPromptV2(BasePrompt):
    """
    Version 2 of the socioeconomic impact analysis prompt.
    
    Enhanced version with:
    - Improved European focus
    - Better structured instructions
    - Enhanced evidence evaluation criteria
    """
    
    @property
    def alias(self) -> str:
        return "socioeconomic_v2"
    
    @property
    def template(self) -> str:
        return """**Enhanced Socioeconomic Impact Analysis for Rare Diseases**

Analyze the socioeconomic impact of {disease_name} (ORPHA:{orphacode}) and generate a structured JSON response.

**SEARCH STRATEGY:**
1. **Primary Sources**: PubMed, Europe PMC, Google Scholar
2. **Keywords**: "{disease_name}" + ["cost of illness", "economic burden", "healthcare costs", "carga económica"]
3. **Regional Focus**: Prioritize Spain > Europe > High-income countries
4. **Study Types**: Cost-of-illness studies, economic evaluations, patient registries

**EVIDENCE HIERARCHY:**
- **Score 10**: Spanish peer-reviewed cost-of-illness study
- **Score 7**: European/high-income country peer-reviewed study  
- **Score 5**: Quality patient organization quantitative data
- **Score 3**: Qualitative burden descriptions only
- **Score 0**: No relevant evidence found

**OUTPUT REQUIREMENTS:**
- JSON format only (no markdown)
- Document ALL studies found (even low-quality)
- Include cost data in euros when available
- Provide verifiable source URLs
- Justify score assignment clearly

**JSON Schema:**
{{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "socioeconomic_impact_studies": [
    {{
      "cost": 0,
      "measure": "description of cost type",
      "label": "study title",
      "source": "verifiable URL",
      "country": "study location", 
      "year": "publication year"
    }}
  ],
  "score": 0,
  "evidence_level": "evidence quality description",
  "justification": "1-3 sentences explaining score rationale"
}}

**Target Disease**: {disease_name} (ORPHA:{orphacode})
**Required**: Return only the JSON object above with actual data."""
    
    @property
    def model(self) -> Type[SocioeconomicImpactResponse]:
        return SocioeconomicImpactResponse
    
    def parser(self, response: str) -> str:
        """
        Custom parser for v2 that handles markdown-wrapped JSON responses.
        """
        response = response.strip()
        
        # Remove markdown code block formatting if present
        if response.startswith('```json'):
            response = response[7:]  # Remove ```json
        if response.startswith('```'):
            response = response[3:]   # Remove ```
        if response.endswith('```'):
            response = response[:-3]  # Remove closing ```
            
        return response.strip() 