"""
CIBERER research groups analysis prompts.

This module contains prompt implementations for identifying and analyzing
CIBERER research units that work on specific rare diseases.
"""

from typing import Type
from utils.prompts import BasePrompt, register_prompt
from .models import GroupsResponse


@register_prompt
class GroupsPromptV1(BasePrompt):
    """
    Version 1 of the CIBERER groups analysis prompt.
    
    This prompt identifies CIBERER research units working on specific diseases by:
    - Scanning CIBERER public domain
    - Collecting unit metadata (PIs, institutions, locations)
    - Finding disease-related publications
    - Documenting source evidence
    """
    
    @property
    def alias(self) -> str:
        return "groups_v1"
    
    @property
    def template(self) -> str:
        return """**Improved Prompt for the Biomedical Text-Mining Assistant**

Your goal is to build a single, well-formed JSON object that maps **every CIBERER research unit (Uxxx) with any connection to {disease_name} (ORPHA:{orphacode})**—even if the group has produced **no** relevant publications.
Follow the steps and JSON schema below **exactly**; add **no extra keys**, keep the **key order**, and output **only** the JSON object (no Markdown, no comments).

---

### 1 · Identify candidate units

* **Scan the entire public domain of CIBERER** (annual reports, news, press releases, group profiles, "Results" pages, etc.).
* Run comprehensive web searches (Google, Bing, DuckDuckGo) combining **"CIBERER" + "{disease_name}"** and synonyms or genes related to the disease.
* Record **every** unit ID you find, **even when no paper is yet linked**.

---

### 2 · Collect core metadata for each unit

* **host_institution** – university, research institute, or hospital hosting the group.
* **city** – headquarters city of the host institution.
* **principal_investigators** – *all* PIs or co-PIs; capture their role ("Principal Investigator", "Co-PI", etc.).
* Leave any unknown field as an empty string `""`.

---

### 3 · Justify inclusion

For **every** unit, add a concise **justification** explaining why it is considered linked to {disease_name}. Typical reasons:

* the unit *publishes* {disease_name}-related work;
* the unit appears in CIBERER news about {disease_name};
* the unit participated in a {disease_name} clinical project;
* a PI sits on a {disease_name} consortium board; etc.

---

### 4 · Provide verifiable sources

Create a **sources** array with **direct URLs** that support the justification:

* CIBERER web pages (news article, annual-report section, group profile);
* PubMed, Europe PMC, or journal-site links (for publications);
* project websites or clinical-trial registries.
  Include at least **one** source for every unit. Use more if needed.

---

### 5 · Harvest disease-related publications

Search **PubMed, Europe PMC, Google Scholar, pre-print servers**. A paper qualifies **only if BOTH** conditions hold:

1. **Relevance** – the **title *or* abstract** contains

   * "{disease_name}" (any language) **OR**
   * an Orphanet synonym **OR**
   * a major {disease_name} gene/protein symbol .
2. **Affiliation** – **at least one author address** contains the substring **"CIBERER"**.

Be **exhaustive**: include articles, reviews, letters, pre-prints.
For each qualifying paper record:

* **pmid** (string) – leave `""` for pre-prints without PMID.
* **title** – exact PubMed title.
* **year** – official publication year (integer).
* **journal** – MEDLINE abbreviation if available.
* **url** – direct PubMed (or pre-print) link.

Verify that every PMID resolves on PubMed.

---

### 6 · Produce the JSON

Return **one** JSON object conforming to this schema **and nothing else**:

```json
{{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "groups": [
    {{
      "unit_id": "",
      "official_name": "",
      "host_institution": "",
      "city": "",
      "principal_investigators": [
        {{ "name": "", "role": "" }}
      ],
      "justification": "",
      "sources": [
        {{ "label": "", "url": "" }}
      ],
      "disease_related_publications": [
        {{ "pmid": "", "title": "", "year": 0, "journal": "", "url": "" }}
      ]
    }}
  ]
}}
```

**Rules & checks**

* Include **every** CIBERER unit you discovered—even if `disease_related_publications` is empty.
* Do **not** fabricate data.
* Use `""` for unknown strings (never `null`).
* If absolutely no units exist, set `"groups": []`.
* if no results are found, return the empty json object.
* Output **only** the JSON object **and nothing else** — do **not** wrap it in Markdown or add explanations.

* REMEMBER: The disease name is: {disease_name}"""
    
    @property
    def model(self) -> Type[GroupsResponse]:
        return GroupsResponse


@register_prompt
class GroupsPromptV2(BasePrompt):
    """
    Version 2 of the CIBERER groups analysis prompt.
    
    Enhanced version with:
    - Improved search strategies
    - Better structured instructions  
    - Enhanced publication criteria
    - More comprehensive source requirements
    """
    
    @property
    def alias(self) -> str:
        return "groups_v2"
    
    @property
    def template(self) -> str:
        return """**Advanced CIBERER Research Units Discovery for {disease_name}**

Objective: Identify ALL CIBERER research units (Uxxx) connected to {disease_name} (ORPHA:{orphacode}).

**DISCOVERY STRATEGY:**

**Phase 1: Web Intelligence**
- Search CIBERER official website, annual reports, news archives
- Query Google: "CIBERER" + "{disease_name}" + [synonyms, gene names]
- Check ResearchGate, LinkedIn for CIBERER + {disease_name} connections
- Scan clinical trial registries for CIBERER involvement

**Phase 2: Publication Mining**
- PubMed: ("{disease_name}"[Title/Abstract] AND "CIBERER"[Affiliation])
- Europe PMC: Advanced search with CIBERER institutional affiliations
- Google Scholar: CIBERER + {disease_name} + specific gene symbols
- Include: Articles, reviews, conference abstracts, preprints

**Phase 3: Network Analysis**
- Map PI connections through consortium memberships
- Check European rare disease networks (EURORDIS, ERN)
- Identify collaborative projects and funding connections

**OUTPUT SCHEMA:**
{{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "groups": [
    {{
      "unit_id": "U123",
      "official_name": "Full unit name",
      "host_institution": "Host institution",
      "city": "Location city",
      "principal_investigators": [
        {{"name": "PI Name", "role": "Principal Investigator"}}
      ],
      "justification": "Clear reason for inclusion",
      "sources": [
        {{"label": "Source description", "url": "verifiable URL"}}
      ],
      "disease_related_publications": [
        {{"pmid": "12345678", "title": "Publication title", "year": 2023, "journal": "J Med Genet", "url": "https://pubmed.ncbi.nlm.nih.gov/12345678"}}
      ]
    }}
  ]
}}

**QUALITY REQUIREMENTS:**
✓ Include units even without publications
✓ Minimum 1 verifiable source per unit
✓ Verify all PMIDs resolve correctly
✓ Use empty arrays [] if no data found
✓ Return pure JSON (no markdown formatting)

**Target**: {disease_name} (ORPHA:{orphacode})
**Instructions**: Return the JSON object with comprehensive CIBERER unit data."""
    
    @property
    def model(self) -> Type[GroupsResponse]:
        return GroupsResponse
    
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