
#### **Step 1.1: Extract Pure XML Parser (45 min)**
```python
# prevalence_processor_core/xml_parser.py
class XMLPrevalenceParser:
    """Extract pure XML data without any calculations"""
    
    def parse_prevalence_xml(self, xml_path: str) -> Dict[str, Any]:
        """
        Extract only fields present in XML:
        - prevalence_id, orpha_code, disease_name
        - source, prevalence_type, prevalence_class
        - qualification, geographic_area, validation_status
        """
        # Implementation extracts pure XML data
        pass
```

->

#### **Step 1.1: Reuse Existing Functions from v1 Processor (30 min)**
**IMPORTANT**: Forbidden to change existing code. Must reuse existing functions from `process_orpha_prevalence.py`:

**Functions to Reuse:**
- `calculate_reliability_score()` - Already implemented reliability scoring
- `standardize_prevalence_class()` - Already implemented class-to-estimate conversion  
- `calculate_weighted_mean_prevalence()` - Already implemented weighted means
- XML parsing logic from `process_prevalence_xml()` - Already implemented

**New Function to Add:**
```python
def standardize_per_million_prevalence(prevalence_class: str) -> Dict[str, Any]:
    """
    Transform prevalence classes to standardized per million ranges
    Conserves original ranges, adds standardized format
    
    Args:
        prevalence_class: Original prevalence class from XML
        
    Returns:
        {
            "original_class": "1-9 / 1 000 000",
            "standard_per_million_prevalence": {
                "min_per_million": 1.0,
                "max_per_million": 9.0,
                "midpoint_per_million": 5.0,
                "range_type": "closed_range"
            },
            "standardized_format": "1-9 per million"
        }
    """
    pass
```



#### **Step 1.3: Create v2 Processor (60 min)**
```python
# process_orpha_prevalence_v2.py
class PrevalenceProcessorV2:
    def __init__(self, mode: ProcessingMode = ProcessingMode.ENHANCED):
        self.mode = mode
        self.xml_parser = XMLPrevalenceParser()
        self.reliability_calc = ReliabilityCalculator()
        self.estimator = PrevalenceEstimator()
    
    def process(self, xml_path: str, output_dir: str):
        # 1. Parse pure XML data
        # 2. Apply calculations based on mode
        # 3. Save to appropriate directories
        pass
```

->

#### **Step 1.2: Add Prevalence Voting Logic to Processor (90 min)**
**Key Requirement**: Voted prevalence is a processor task, not curator task.

```python
# Add to process_orpha_prevalence_v2.py
def vote_best_prevalence_per_type(prevalence_records: List[Dict]) -> Dict[str, Dict]:
    """
    Perform intra-prevalence-type voting for each type
    
    Voting Rules:
    1. Group records by prevalence_type
    2. Within each type: majority voting by prevalence_class
    3. Tie-breaker: Worldwide > Europe > specific countries
    4. Final tie-breaker: highest reliability_score
    
    Returns:
        {
            "Point prevalence": {
                "prevalence_classes": ["1-9 / 1 000 000", "<1 / 1 000 000"],
                "votes": {"1-9 / 1 000 000": 3, "<1 / 1 000 000": 1},
                "best_prevalence": "1-9 / 1 000 000",
                "has_spanish_record": false,
                "winning_record": {...}
            }
        }
    """
    pass

def vote_final_best_prevalence(type_winners: Dict, has_spanish_record: bool) -> str:
    """
    Perform inter-prevalence-type voting
    
    Priority Rules:
    - If Spain Record: Prevalence at birth > Point prevalence
    - No Spain Record: Point prevalence > Prevalence at birth > Annual incidence > Lifetime prevalence > Cases/families
    
    Returns:
        final_best_prevalence_class (str)
    """
    pass
```

#### **Step 1.3: Create v2 Processor with Runtime Paths (60 min)**
```python
# process_orpha_prevalence_v2.py
import argparse
from pathlib import Path
from process_orpha_prevalence import (
    calculate_reliability_score,
    standardize_prevalence_class, 
    calculate_weighted_mean_prevalence
)

class PrevalenceProcessorV2:
    def __init__(self, mode: ProcessingMode = ProcessingMode.ENHANCED):
        self.mode = mode
        
    def process(self, xml_path: str, output_dir: str):
        # 1. Reuse existing XML parsing from v1
        # 2. Add standard_per_million_prevalence field
        # 3. Add voting logic per disease
        # 4. Save to configurable output directories
        pass

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--xml', default="data/01_raw/en_product9_prev.xml")
    parser.add_argument('--output', default="data/03_processed/orpha/orphadata/orpha_prevalence_v2")
    parser.add_argument('--mode', choices=['original', 'enhanced', 'separate'], default='enhanced')
    args = parser.parse_args()
    
    processor = PrevalenceProcessorV2(mode=args.mode)
    processor.process(args.xml, args.output)
```















### **Task 2**  
- [ ] Enhanced curator processes all diseases (not just metabolic)
- [ ] Correct prevalence voting logic implementation
- [ ] Both JSON outputs match specified format
- [ ] Cases/families constraint properly applied
- [ ] Spanish patient calculations accurate
- [ ] Comprehensive prevalence classes documentation

->

### **Task 2**  
- [ ] Enhanced curator processes metabolic instances from curated data
- [ ] Reads voted prevalence results from processor v2 correctly
- [ ] Both JSON outputs match specified format exactly
- [ ] Spanish patient calculations accurate (prevalence × 47 million)
- [ ] Measured vs inferred patient counts distinguished
- [ ] Complete output files generated in curated data directory










### **Dependencies**
- `ProcessedPrevalenceClient` (existing, working)
- `core.schemas.orpha.orphadata.orpha_prevalence` (existing schemas)
- Spanish population constant: 47 million

This comprehensive task plan provides detailed guidance for both prevalence processor refactoring and curator enhancement while maintaining backward compatibility and improving system architecture.

->

### **Dependencies**

**Task 1: Processor v2**
- `process_orpha_prevalence.py` (existing, forbidden to modify)
- Reuse existing functions: `calculate_reliability_score`, `standardize_prevalence_class`, `calculate_weighted_mean_prevalence`
- Runtime configurable paths for XML input and output directories

**Task 2: Curator v2**
- `data/04_curated/orpha/ordo/metabolic_disease_instances.json` (665 metabolic diseases)
- Processor v2 voted prevalence results
- Spanish population constant: 47 million inhabitants
- No dependency on `ProcessedPrevalenceClient` (reads files directly)

### **Key Clarifications**

1. **Voting Logic**: Implemented in processor v2, NOT in curator
2. **Curator Scope**: ONLY metabolic diseases from curated data (665 diseases)
3. **Code Reuse**: Forbidden to modify existing processor, must reuse functions
4. **Output Format**: Prevalence classes as strings, not numerical values
5. **Spanish Calculations**: Inferred (always) vs measured (if Spanish record exists)

This comprehensive task plan provides detailed guidance for both prevalence processor refactoring and curator enhancement while maintaining backward compatibility and improving system architecture.