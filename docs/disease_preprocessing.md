# Disease Taxonomy Processing System

## Overview

The disease preprocessing system processes Orphanet XML taxonomy data into structured JSON files with hierarchical disease classification, category relationships, and comprehensive metadata. This system creates the foundation for disease analysis and research prioritization in the Carlos III platform.

## Quick Start

```bash
# Process disease taxonomy with default settings
python tools/disease_preprocessing.py

# Process with custom input/output paths
python tools/disease_preprocessing.py --xml data/input/raw/Metabolicas.xml --output data/processed/orpha/ordo

# Validate existing processed files
python tools/disease_preprocessing.py --validate-only --output data/processed/orpha/ordo

# Force overwrite existing files
python tools/disease_preprocessing.py --force
```

## Processing Results Summary

### Data Volume
- **Total nodes**: 1,166 (diseases + categories)
- **Total diseases**: 999 rare metabolic diseases
- **Total categories**: 167 taxonomic categories
- **Max taxonomy depth**: 8 levels
- **Average diseases per category**: 5.98
- **Processing time**: ~0.65 seconds
- **Total output size**: ~1.22 MB

### Taxonomy Distribution
- **Root categories (Level 0)**: 1 category
- **Primary categories (Level 1)**: 13 categories  
- **Secondary categories (Level 2)**: 85 categories
- **Disease distribution**: Most diseases at levels 3-5 (839/999 = 84%)

## File Structure

```
data/processed/orpha/ordo/
├── taxonomy/                           # Hierarchical classification structure
│   ├── structure.json          # 0.05 MB - Complete taxonomy tree structure
│   ├── categories.json         # 0.03 MB - All category definitions and relationships
│   ├── relationships.json      # 0.01 MB - Parent-child relationships mapping
│   └── metadata.json           # 0.00 MB - Taxonomy metadata and versioning
├── instances/                          # Individual disease records
│   ├── diseases.json           # 0.47 MB - Complete disease instances with metadata
│   ├── classification_index.json # 0.02 MB - Disease classification mappings
│   ├── name_index.json         # 0.09 MB - Disease name-to-ID lookups
│   └── disease_metadata.json   # 0.20 MB - Extended disease metadata
├── cache/                              # Performance optimization files
│   ├── paths.json              # 0.35 MB - Hierarchical path calculations
│   ├── statistics.json         # 0.00 MB - Processing statistics
│   └── combined_views.json     # 0.00 MB - Aggregated view definitions
└── processing_report.json             # Processing summary and metrics
```

## Data Models

### Disease Instance
Each disease record contains:
```json
{
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
    "last_updated": "2025-07-05T13:15:19.983468",
    "disorder_type": "Disease",
    "orpha_code": "79318"
  }
}
```

### Category Structure
```json
{
  "id": "68367",
  "name": "Rare inborn errors of metabolism",
  "type": "root_category",
  "level": 0,
  "parent_id": null,
  "children": [
    "137", "68366", "68373", "79062", "79161", 
    "79200", "79214", "79224", "91088", "309005"
  ]
}
```

### Classification Mapping
```json
{
  "disease_id": {
    "category_id": "309347",
    "category_name": "Congenital disorders of glycosylation",
    "full_path": ["68367", "137", "309347"],
    "level": 3,
    "path_names": [
      "Rare inborn errors of metabolism",
      "Congenital disorders of deglycosylation and glycosylation",
      "Congenital disorders of glycosylation"
    ]
  }
}
```

## Taxonomy Structure Analysis

### Disease Distribution by Level
- **Level 3**: 260 diseases (26.0%) - Specific disease groups
- **Level 4**: 386 diseases (38.6%) - Main disease level
- **Level 5**: 193 diseases (19.3%) - Detailed classifications  
- **Level 6**: 122 diseases (12.2%) - Subspecific variants
- **Level 7**: 26 diseases (2.6%) - Rare variants
- **Level 8**: 12 diseases (1.2%) - Ultra-specific classifications

### Category Hierarchy
- **Level 0**: 1 root category ("Rare inborn errors of metabolism")
- **Level 1**: 13 primary categories (major metabolic pathways)
- **Level 2**: 85 secondary categories (pathway subdivisions)
- **Level 3**: 51 specific categories (disease groups)
- **Level 4**: 9 detailed categories (rare classifications)
- **Level 5**: 6 subspecific categories
- **Level 6**: 2 ultra-specific categories

## Key Features

### Hierarchical Classification
- Complete parent-child relationship mapping
- Multi-level disease categorization (8 levels deep)
- Taxonomic path calculation for every disease
- Category inheritance and classification validation

### Search and Index Optimization
- **Name index**: Fast disease name-to-ID lookups
- **Classification index**: Category-based disease grouping
- **Path calculation**: Pre-computed hierarchical paths
- **Metadata indexing**: Expert links and external references

### Data Validation and Quality
- JSON structure validation for all output files
- Disease-category relationship verification  
- Orphanet ID consistency checking
- Metadata completeness validation

### Cross-Reference Support
- **OrphaCode integration**: Compatible with prevalence and drug data
- **Expert link preservation**: Direct links to Orphanet expert pages
- **Classification compatibility**: Ready for research prioritization
- **Metadata standardization**: Consistent timestamp and versioning

## Usage Examples

### Finding Diseases by Category
```bash
# Get all diseases in a specific category
python -c "
import json
with open('data/processed/orpha/ordo/instances/classification_index.json') as f:
    data = json.load(f)
    # Find diseases in 'Congenital disorders of glycosylation'
    for disease_id, info in data.items():
        if info['category_name'] == 'Congenital disorders of glycosylation':
            print(f'{disease_id}: {info}')
"
```

### Disease Hierarchy Navigation
```bash
# View complete taxonomy structure
cat data/processed/orpha/ordo/taxonomy/structure.json

# Check category relationships
cat data/processed/orpha/ordo/taxonomy/relationships.json

# Search diseases by name
python -c "
import json
with open('data/processed/orpha/ordo/instances/name_index.json') as f:
    name_index = json.load(f)
    # Search for CDG diseases
    cdg_diseases = {k:v for k,v in name_index.items() if 'CDG' in k}
    print(json.dumps(cdg_diseases, indent=2))
"
```

### Processing Statistics
```bash
# View processing statistics
cat data/processed/orpha/ordo/cache/statistics.json

# Check processing report
cat data/processed/orpha/ordo/processing_report.json

# Validate data integrity
python tools/disease_preprocessing.py --validate-only --output data/processed/orpha/ordo
```

## Technical Implementation

### Processing Performance
- **XML parsing**: 1,166 nodes in ~0.1 seconds
- **Taxonomy tree building**: Hierarchical relationships in ~0.2 seconds
- **Index generation**: Name and classification indices in ~0.2 seconds
- **File generation**: 1.22 MB output in ~0.15 seconds
- **Memory usage**: <1GB during processing

### Data Validation
- **JSON structure validation**: 100% valid output files
- **Taxonomy consistency**: All parent-child relationships verified
- **OrphaCode validation**: All disease IDs conform to Orphanet standards
- **Completeness checking**: Required metadata present for all diseases

## Input Data Requirements

### XML Structure Expected
- **Input file**: `data/input/raw/Metabolicas.xml` (Orphanet XML format)
- **Root element**: Contains hierarchical disease taxonomy
- **Disease elements**: Include OrphaCode, name, classification path
- **Category elements**: Include parent-child relationships and metadata

### Data Quality Standards
- **Valid XML structure**: Well-formed XML with proper encoding
- **Complete OrphaCodes**: All diseases must have valid Orphanet identifiers
- **Hierarchy integrity**: Parent-child relationships must be consistent
- **Name completeness**: All diseases and categories must have names

## Integration Points

### Prevalence Data Integration
- **OrphaCode compatibility**: Direct linking with prevalence records
- **Disease validation**: Ensures prevalence data references valid diseases
- **Hierarchical analysis**: Supports category-level prevalence aggregation
- **Research prioritization**: Provides disease classification for scoring

### Clinical Trials Integration
- **Disease matching**: Links clinical trials to classified diseases
- **Category analysis**: Groups trials by disease taxonomy
- **Research gap identification**: Identifies under-researched disease areas
- **Prioritization support**: Provides classification context for trial selection

### Drug Data Integration
- **Disease-drug relationships**: Links drugs to classified diseases
- **Therapeutic area mapping**: Groups drugs by disease categories
- **Pipeline analysis**: Analyzes drug development by disease taxonomy
- **Treatment gap analysis**: Identifies therapeutic needs by classification

## Maintenance and Updates

### Regular Updates
1. **New XML data**: Rerun preprocessing with `--force` flag when Orphanet updates
2. **Validation**: Run `--validate-only` to check data integrity after updates
3. **Statistics**: Monitor changes in disease counts and taxonomy structure
4. **Integration**: Update linked prevalence and drug data after taxonomy changes

### Quality Monitoring
- **Disease count tracking**: Monitor for significant changes in disease numbers
- **Taxonomy depth**: Alert if hierarchy structure changes significantly
- **Processing time**: Monitor for performance degradation
- **File sizes**: Track output size changes indicating data structure changes

## Error Handling and Troubleshooting

### Common Issues
1. **Unicode logging errors**: Cosmetic only, doesn't affect processing
2. **Memory usage**: Large XML files may require adjustment of memory settings
3. **File permissions**: Ensure write access to output directory
4. **XML parsing errors**: Verify XML file integrity and proper encoding

### Error Recovery
- **Validation failures**: Run with `--validate-only` to identify specific issues
- **Partial processing**: Delete output directory and rerun with `--force`
- **Taxonomy inconsistencies**: Check input XML for relationship errors
- **Missing OrphaCodes**: Verify XML contains complete Orphanet identifiers

### Debugging Tools
```bash
# Check processing logs
cat disease_preprocessing.log

# Validate specific output files
python -c "import json; json.load(open('data/processed/orpha/ordo/instances/diseases.json'))"

# Check taxonomy consistency
python -c "
import json
cats = json.load(open('data/processed/orpha/ordo/taxonomy/categories.json'))
rels = json.load(open('data/processed/orpha/ordo/taxonomy/relationships.json'))
print(f'Categories: {len(cats)}, Relationships: {len(rels)}')
"
```

## Integration with Research Prioritization

### Disease Classification Scoring
The processed disease data provides classification context for research prioritization:
- **Taxonomy level weighting**: Diseases at different levels may have different research priorities
- **Category-based scoring**: Some disease categories may be prioritized over others
- **Hierarchy analysis**: Parent-category diseases may influence child-disease scores
- **Classification completeness**: Well-classified diseases may score higher

### Usage in Prioritization
```python
# Example integration
from utils.orpha.disease_instances import DiseaseInstance

disease_data = load_disease_classification("79318")
classification_score = calculate_classification_score(
    disease_data["classification"]["level"],
    disease_data["classification"]["category_id"],
    disease_data["classification"]["path"]
)
```

## Future Enhancements

### Planned Features
1. **Temporal analysis**: Track taxonomy changes over time
2. **Relationship enrichment**: Add synonym and related disease mappings
3. **External integration**: Link with additional disease databases (MONDO, DO)
4. **Semantic search**: Enable natural language disease discovery
5. **API endpoint**: Provide REST API for disease taxonomy queries

### Performance Optimizations
1. **Incremental processing**: Update only changed taxonomy branches
2. **Database backend**: Optional database storage for large taxonomies
3. **Caching strategies**: Improve lookup performance for frequent queries
4. **Parallel processing**: Utilize multiple cores for large XML files
5. **Memory optimization**: Reduce memory footprint for massive taxonomies

## Data Security and Privacy

### Data Handling
- **Public data**: All disease taxonomy data is publicly available from Orphanet
- **No personal data**: System processes only disease classification information
- **Anonymized identifiers**: Uses OrphaCodes, not patient-identifiable information
- **Open access**: Supports open science and research collaboration

### Compliance
- **Open data standards**: Follows Orphanet's open data principles
- **Attribution**: Maintains references to original Orphanet sources
- **Version tracking**: Preserves data provenance and processing history
- **Reproducibility**: Ensures processing can be reproduced with same inputs

## Conclusion

The disease preprocessing system provides a robust foundation for rare disease research by converting complex XML taxonomy data into optimized JSON structures. With processing of 999 diseases across 167 categories in under a second, it enables efficient disease classification, search, and analysis for the Carlos III research prioritization platform.

The system's hierarchical approach, comprehensive indexing, and integration capabilities make it essential for linking disease taxonomy with prevalence data, clinical trials, and drug information, supporting evidence-based research prioritization in rare metabolic diseases. 