# Task Plan: Curate Orpha Prevalence

## Overview
Create a curation process `curate_orpha_prevalence` that selects optimal prevalence data for a subset of diseases and generates a simplified mapping from orphacode to prevalence class.

## Input and Output Paths

### Input Paths
- **Main input**: `data/03_processed/orpha/orphadata/orpha_prevalence/disease2prevalence.json`
- **Disease subset**: `data/04_curated/orpha/ordo/metabolic_disease_instances.json` (665 diseases - largest subset)
- **Additional reference**: `data/03_processed/orpha/orphadata/orpha_prevalence/orpha_index.json`
- **Disease names mapping**: `data/04_curated/orpha/ordo/orphacode2disease_name.json` (to be created if missing)

### Output Paths
- **Main output**: `data/04_curated/orpha/orphadata/disease2prevalence.json`
- **Processing summary**: `data/04_curated/orpha/orphadata/orpha_prevalence_curation_summary.json`
- **Disease names mapping**: `data/04_curated/orpha/ordo/orphacode2disease_name.json` (if created)

### Implementation Paths
- **Main script**: `etl/04_curate/orpha/orphadata/curate_orpha_prevalence.py`
- **Statistics script**: `etl/05_stats/orpha/orphadata/orpha_prevalence_stats.py`
- **Client interface**: `core/datastore/orpha/orphadata/curated_prevalence_client.py`
- **Disease names script**: `etl/04_curate/orpha/ordo/curate_disease_names.py` (if needed)

## Technical Requirements

### 1. Data Selection Logic
Implement the prevalence class selection algorithm with the following priority:

1. **First Priority**: Check `most_reliable_prevalence` field
   - If `most_reliable_prevalence.prevalence_type == "Point prevalence"`, use its `prevalence_class`
   - The `most_reliable_prevalence` is already pre-calculated as the record with highest reliability score

2. **Second Priority**: If most reliable is not point prevalence, apply choice-based method
   - Filter records with `geographic_area == "Worldwide"`
   - Select record with highest `reliability_score`
   - Return the `prevalence_class` from this record

3. **Third Priority**: If no worldwide available
   - Filter records with `geographic_area != "Worldwide"` (regional records)
   - Select record with highest `reliability_score`
   - Return the `prevalence_class` from this record

4. **Fallback**: If no records available, return `null` or `"Unknown"`

### 2. Output Format
```json
{
  "orphacode": "prevalence_class",
  "166024": "1-9 / 1 000 000",
  "58": "<1 / 1 000 000",
  "61": "1-9 / 100 000"
}
```

### 3. Input Disease Subset
Use the metabolic disease instances dataset (665 diseases):
- **File**: `data/04_curated/orpha/ordo/metabolic_disease_instances.json`
- **Format**: `[{"orpha_code": "79318", "disease_name": "PMM2-CDG"}]`
- **Size**: 665 diseases (largest available subset)
- **Coverage**: 92.18% prevalence data coverage based on existing metabolic data

## Implementation Steps

### Step 1: Create Base Structure
Create the curation script following the pattern of `curate_metabolic_prevalence.py`:

```python
class OrphaPrevalenceCurator:
    def __init__(self, 
                 disease_subset_path: str,
                 processed_prevalence_path: str,
                 output_dir: str):
        """
        Initialize the orpha prevalence curator
        
        Args:
            disease_subset_path: Path to disease subset JSON file
            processed_prevalence_path: Path to processed prevalence data JSON
            output_dir: Directory for output files (all paths configurable via CLI)
        """
        self.disease_subset_path = Path(disease_subset_path)
        self.processed_prevalence_path = Path(processed_prevalence_path)
        self.output_dir = Path(output_dir)
        
        # Initialize ProcessedPrevalenceClient
        self.prevalence_client = ProcessedPrevalenceClient()
        
        # Processing statistics (basic tracking only)
        self.stats = {
            'total_diseases': 0,
            'diseases_with_prevalence': 0,
            'diseases_without_prevalence': 0,
            'prevalence_class_distribution': {},
            'coverage_percentage': 0.0,
            'processing_timestamp': None
        }
```

### Step 2: Implement Selection Algorithm
```python
def select_best_prevalence_class(self, disease_data: Dict) -> Optional[str]:
    """
    Select the best prevalence class based on priority rules:
    1. If most_reliable_prevalence is point prevalence, use it
    2. Otherwise, apply choice-based method (worldwide > regional)
    """
    # Get the most reliable prevalence record
    most_reliable = disease_data.get('most_reliable_prevalence')
    
    if not most_reliable:
        return None
    
    # Priority 1: If most reliable is point prevalence, use it directly
    if most_reliable.get('prevalence_type') == 'Point prevalence':
        return most_reliable.get('prevalence_class')
    
    # Priority 2: Apply choice-based method
    # Get all prevalence records for examination
    prevalence_records = disease_data.get('prevalence_records', [])
    
    # Filter reliable records (reliability_score >= 6.0)
    reliable_records = [r for r in prevalence_records if r.get('reliability_score', 0) >= 6.0]
    
    if not reliable_records:
        reliable_records = prevalence_records  # Use all if none are reliable
    
    # Priority 2a: Worldwide records with best reliability
    worldwide_records = [r for r in reliable_records if r.get('geographic_area') == 'Worldwide']
    if worldwide_records:
        best_record = max(worldwide_records, key=lambda x: x.get('reliability_score', 0))
        return best_record.get('prevalence_class')
    
    # Priority 2b: Regional records with best reliability
    regional_records = [r for r in reliable_records if r.get('geographic_area') != 'Worldwide']
    if regional_records:
        best_record = max(regional_records, key=lambda x: x.get('reliability_score', 0))
        return best_record.get('prevalence_class')
    
    return None
```

### Step 3: Create Main Processing Function
```python
def process_disease_subset(self) -> Dict[str, str]:
    """
    Process the disease subset and generate orphacode -> prevalence_class mapping
    """
    # Load disease subset
    disease_subset = self.load_disease_subset()
    
    # Load processed prevalence data
    prevalence_data = self.load_processed_prevalence()
    
    # Generate mapping
    disease2prevalence = {}
    
    for disease_code in disease_subset:
        if disease_code in prevalence_data:
            disease_data = prevalence_data[disease_code]
            best_class = self.select_best_prevalence_class(disease_data)
            
            if best_class:
                disease2prevalence[disease_code] = best_class
            else:
                disease2prevalence[disease_code] = "Unknown"
    
    return disease2prevalence
```

### Step 4: Add CLI Interface (All paths required)
```python
def main():
    """Main function with CLI interface - all paths configurable"""
    parser = argparse.ArgumentParser(description="Curate orpha prevalence data for disease subset")
    
    # All arguments are required - no hardcoded defaults
    parser.add_argument(
        '--disease-subset',
        required=True,
        help="Path to disease subset JSON file"
    )
    
    parser.add_argument(
        '--input',
        required=True, 
        help="Path to processed prevalence data JSON file"
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help="Output directory for curated files"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and run curator with provided paths
    curator = OrphaPrevalenceCurator(
        disease_subset_path=args.disease_subset,
        processed_prevalence_path=args.input,
        output_dir=args.output
    )
    
    curator.run_curation()
```

### Step 5: Add Basic Processing Summary
```python
def generate_curation_stats(self, disease2prevalence: Dict[str, str]) -> Dict:
    """
    Generate processing statistics and validation metrics
    """
    stats = {
        'total_diseases_in_subset': len(self.disease_subset),
        'diseases_with_prevalence': len([v for v in disease2prevalence.values() if v != "Unknown"]),
        'diseases_without_prevalence': len([v for v in disease2prevalence.values() if v == "Unknown"]),
        'prevalence_class_distribution': {},
        'coverage_percentage': 0.0,
        'processing_timestamp': datetime.now().isoformat()
    }
    
    # Calculate prevalence class distribution
    for prevalence_class in disease2prevalence.values():
        stats['prevalence_class_distribution'][prevalence_class] = \
            stats['prevalence_class_distribution'].get(prevalence_class, 0) + 1
    
    # Calculate coverage
    if stats['total_diseases_in_subset'] > 0:
        stats['coverage_percentage'] = \
            (stats['diseases_with_prevalence'] / stats['total_diseases_in_subset']) * 100
    
    return stats
```

## CuratedPrevalenceClient Implementation

### Step 6: Create CuratedPrevalenceClient
Following the pattern of existing clients (`ProcessedPrevalenceClient`, `CuratedPrevalenceClient`):

```python
class CuratedOrphaPrevalenceClient:
    """Client for accessing curated orpha prevalence data with lazy loading"""
    
    def __init__(self, 
                 data_dir: str = "data/04_curated/orpha/orphadata",
                 disease_names_path: str = "data/04_curated/orpha/ordo/orphacode2disease_name.json"):
        """
        Initialize the curated orpha prevalence client
        
        Args:
            data_dir: Directory containing curated prevalence data
            disease_names_path: Path to disease names mapping file
        """
        self.data_dir = Path(data_dir)
        self.disease_names_path = Path(disease_names_path)
        
        # Lazy-loaded data structures
        self._disease2prevalence: Optional[Dict[str, str]] = None
        self._prevalence_class_distribution: Optional[Dict[str, int]] = None
        self._processing_summary: Optional[Dict] = None
        self._orphacode2disease_name: Optional[Dict[str, str]] = None
        
        # Cache for frequently accessed data
        self._cache = {}
    
    def _ensure_disease2prevalence_loaded(self):
        """Load disease to prevalence mapping if not already loaded"""
        if self._disease2prevalence is None:
            file_path = self.data_dir / "disease2prevalence.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2prevalence = json.load(f)
    
    def get_prevalence_class(self, orpha_code: str) -> Optional[str]:
        """Get prevalence class for a disease"""
        self._ensure_disease2prevalence_loaded()
        return self._disease2prevalence.get(orpha_code)
    
    def get_diseases_by_prevalence_class(self, prevalence_class: str) -> List[str]:
        """Get all diseases with specific prevalence class"""
        self._ensure_disease2prevalence_loaded()
        return [code for code, pclass in self._disease2prevalence.items() 
                if pclass == prevalence_class]
    
    def get_prevalence_class_distribution(self) -> Dict[str, int]:
        """Get distribution of prevalence classes"""
        if self._prevalence_class_distribution is None:
            self._ensure_disease2prevalence_loaded()
            distribution = {}
            for prevalence_class in self._disease2prevalence.values():
                distribution[prevalence_class] = distribution.get(prevalence_class, 0) + 1
            self._prevalence_class_distribution = distribution
        return self._prevalence_class_distribution.copy()
    
    def get_processing_summary(self) -> Dict:
        """Get processing statistics"""
        if self._processing_summary is None:
            summary_path = self.data_dir / "orpha_prevalence_curation_summary.json"
            if summary_path.exists():
                with open(summary_path, 'r', encoding='utf-8') as f:
                    self._processing_summary = json.load(f)
        return self._processing_summary
    
    @lru_cache(maxsize=1000)
    def get_disease_name(self, orpha_code: str) -> Optional[str]:
        """Get disease name for orpha code (cached)"""
        if self._orphacode2disease_name is None:
            if self.disease_names_path.exists():
                with open(self.disease_names_path, 'r', encoding='utf-8') as f:
                    self._orphacode2disease_name = json.load(f)
        return self._orphacode2disease_name.get(orpha_code) if self._orphacode2disease_name else None
    
    def clear_cache(self):
        """Clear all cached data"""
        self._disease2prevalence = None
        self._prevalence_class_distribution = None
        self._processing_summary = None
        self._orphacode2disease_name = None
        self._cache.clear()
```

### Step 7: Create Disease Names Script (if needed)
```python
# etl/04_curate/orpha/ordo/curate_disease_names.py
def create_orphacode2disease_name_mapping(input_path: str, output_path: str):
    """Create mapping from orphacode to disease name"""
    # Load from processed prevalence data
    prevalence_client = ProcessedPrevalenceClient()
    
    # Get disease index
    orpha_index = prevalence_client.get_orpha_index()
    
    # Create mapping
    orphacode2name = {}
    for orpha_code, disease_info in orpha_index.items():
        orphacode2name[orpha_code] = disease_info['disease_name']
    
    # Save to file (path provided via CLI)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(orphacode2name, f, indent=2, ensure_ascii=False)
    
    return orphacode2name

# CLI with required arguments
def main():
    parser = argparse.ArgumentParser(description="Create orphacode to disease name mapping")
    
    parser.add_argument(
        '--input',
        required=True,
        help="Path to orpha index JSON file"
    )
    
    parser.add_argument(
        '--output', 
        required=True,
        help="Path for output disease names JSON file"
    )
    
    args = parser.parse_args()
    
    # Create mapping with configurable paths
    mapping = create_orphacode2disease_name_mapping(args.input, args.output)
    print(f"Created disease names mapping with {len(mapping)} entries")
```

## Statistics Script (Separate)

### Statistics Location
Statistics are generated by a separate script following the repository pattern:
- **Location**: `etl/05_stats/orpha/orphadata/orpha_prevalence_stats.py`
- **Pattern**: Follows existing stats scripts like `metabolic_prevalence_stats.py`

### Statistics Script Structure
```python
class OrphaPrevalenceStatsAnalyzer:
    """Statistical analysis for curated orpha prevalence data"""
    
    def __init__(self, 
                 client: Optional[CuratedOrphaPrevalenceClient] = None,
                 output_dir: str = None):  # No default path - must be provided via CLI
        """
        Initialize the orpha prevalence stats analyzer
        
        Args:
            client: CuratedOrphaPrevalenceClient instance 
            output_dir: Directory for output files (provided via CLI)
        """
        self.client = client if client else CuratedOrphaPrevalenceClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis results storage
        self.analysis_results = {}
    
    def analyze_coverage(self) -> Dict:
        """Analyze coverage of diseases with prevalence data"""
        # Coverage analysis implementation
        pass
    
    def analyze_prevalence_class_distribution(self) -> Dict:
        """Analyze the distribution of prevalence classes"""
        # Distribution analysis implementation
        pass
    
    def analyze_data_quality_metrics(self) -> Dict:
        """Analyze data quality and selection method usage"""
        # Quality metrics: point prevalence vs worldwide vs regional usage
        pass
    
    def generate_json_report(self, filename: str = None) -> Path:
        """Generate comprehensive JSON statistics report"""
        # No hardcoded filename - provided via parameter or CLI
        pass
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate complete analysis with all components"""
        # Main analysis runner
        pass

# CLI Interface with configurable paths
def main():
    parser = argparse.ArgumentParser(description="Generate statistics for curated orpha prevalence data")
    
    parser.add_argument(
        '--input-dir',
        required=True,
        help="Input directory containing curated data files"
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help="Output directory for statistics files"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Create analyzer with configurable paths
    analyzer = OrphaPrevalenceStatsAnalyzer(output_dir=args.output)
    summary = analyzer.generate_comprehensive_report()
```

## File Structure

```
etl/04_curate/orpha/orphadata/
├── curate_orpha_prevalence.py          # Main curation script (no hardcoded paths)
├── curate_metabolic_prevalence.py      # Existing reference
└── __init__.py

etl/04_curate/orpha/ordo/
├── curate_disease_names.py             # Disease names mapping script (configurable paths)
├── curate_disease_instances.py         # Existing reference
└── __init__.py

etl/05_stats/orpha/orphadata/
├── orpha_prevalence_stats.py           # Statistics script (separate from curation)
├── prevalence_stats.py                 # Existing reference
└── __init__.py

core/datastore/orpha/orphadata/
├── curated_prevalence_client.py        # New client interface (configurable paths)
├── prevalence_client.py                # Existing processed client
└── __init__.py

data/04_curated/orpha/orphadata/
├── disease2prevalence.json             # Output: {orphacode: prevalence_class}
├── orpha_prevalence_curation_summary.json  # Basic processing summary
├── metabolic_diseases2prevalence_per_million.json  # Existing
└── metabolic_diseases2spanish_patient_number.json  # Existing

data/04_curated/orpha/ordo/
├── orphacode2disease_name.json         # Disease names mapping (optional)
├── metabolic_disease_instances.json    # Input subset (665 diseases)
└── metabolic_disease_instances_sample_10.json  # Small sample

results/stats/\etl\subset_of_disease_instances\orpha\orphadata\orpha_prevalence\metabolic
├── orpha_prevalence_statistics.json    # Comprehensive statistics
├── orpha_prevalence_visualization.png   # Charts and plots Here you should create several plots, but only on curated data. mainly distribution but be imaginative, maybe you can use also the proccessed client to get some more stats on this subset dataset
└── analysis_summary.json               # Detailed analysis results
```

## Command Line Interface

### Main Curation Script (All paths required)
```bash
# Basic usage - all parameters required (no defaults)
python etl/04_curate/orpha/orphadata/curate_orpha_prevalence.py \
    --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json \
    --input data/03_processed/orpha/orphadata/orpha_prevalence/disease2prevalence.json \
    --output data/04_curated/orpha/orphadata/

# With verbose logging
python etl/04_curate/orpha/orphadata/curate_orpha_prevalence.py \
    --disease-subset data/04_curated/orpha/ordo/metabolic_disease_instances.json \
    --input data/03_processed/orpha/orphadata/orpha_prevalence/disease2prevalence.json \
    --output data/04_curated/orpha/orphadata/ \
    --verbose

# CLI Arguments (all required):
# --disease-subset: Path to disease subset JSON file
# --input: Path to processed prevalence data JSON
# --output: Directory for output files
# --verbose: Enable verbose logging (optional)
```

### Statistics Script (Separate)
```bash
# Generate statistics from curated data
python etl/05_stats/orpha/orphadata/orpha_prevalence_stats.py \
    --input-dir data/04_curated/orpha/orphadata/ \
    --output results/stats/orpha/orphadata/prevalence_curation/

# With verbose output
python etl/05_stats/orpha/orphadata/orpha_prevalence_stats.py \
    --input-dir data/04_curated/orpha/orphadata/ \
    --output results/stats/orpha/orphadata/prevalence_curation/ \
    --verbose
```

### Disease Names Script (if needed)
```bash
# Create disease names mapping if missing
python etl/04_curate/orpha/ordo/curate_disease_names.py \
    --input data/03_processed/orpha/orphadata/orpha_prevalence/orpha_index.json \
    --output data/04_curated/orpha/ordo/orphacode2disease_name.json
```

## Validation Requirements

### 1. Input Validation
- Verify disease subset file exists and is valid JSON
- Verify processed prevalence data exists and is valid JSON
- Validate that disease codes in subset exist in prevalence data

### 2. Output Validation
- Ensure all disease codes from subset are processed
- Verify output JSON format is correct
- Check that no orphacode appears multiple times

### 3. Logic Validation
- Verify selection algorithm follows priority rules
- Check that reliability scores are correctly considered
- Ensure geographic area filtering works properly

## Error Handling

### 1. Missing Data
- Log warnings for diseases without prevalence data
- Continue processing remaining diseases
- Report missing diseases in summary

### 2. Invalid Data
- Handle malformed prevalence records gracefully
- Skip invalid records and log warnings
- Use fallback values when appropriate

### 3. File I/O Errors
- Provide clear error messages for file access issues
- Validate file permissions before processing
- Create output directories if they don't exist


## Success Criteria

1. **Functionality**: Script processes disease subset and generates correct prevalence class mapping
2. **Reliability**: Implements selection algorithm exactly as specified
3. **Usability**: Command line interface is intuitive and well-documented

5. **Maintainability**: Code follows existing patterns and is well-documented
6. **Validation**: Comprehensive error handling and validation
7. DOCS: Mandatory: put README in the folders, explaining the folder motivo de ser.
## Client Usage Examples

### Basic Usage
```python
from core.datastore.orpha.orphadata.curated_prevalence_client import CuratedOrphaPrevalenceClient

# Initialize client
client = CuratedOrphaPrevalenceClient()

# Get prevalence class for a disease
prevalence_class = client.get_prevalence_class("79318")  # PMM2-CDG
print(f"Prevalence class: {prevalence_class}")

# Get disease name
disease_name = client.get_disease_name("79318")
print(f"Disease name: {disease_name}")

# Get all diseases with specific prevalence class
rare_diseases = client.get_diseases_by_prevalence_class("<1 / 1 000 000")
print(f"Very rare diseases: {len(rare_diseases)}")

# Get prevalence class distribution
distribution = client.get_prevalence_class_distribution()
print(f"Distribution: {distribution}")

# Get processing summary
summary = client.get_processing_summary()
print(f"Coverage: {summary['dataset_statistics']['coverage_percentage']:.1f}%")
```

### Advanced Usage
```python
# Batch processing
disease_codes = ["79318", "79319", "79320"]
prevalence_data = {}

for code in disease_codes:
    prevalence_data[code] = {
        'prevalence_class': client.get_prevalence_class(code),
        'disease_name': client.get_disease_name(code)
    }

# Generate report
for code, data in prevalence_data.items():
    print(f"{data['disease_name']} ({code}): {data['prevalence_class']}")

# Memory management
client.clear_cache()  # Clear cache when done
```