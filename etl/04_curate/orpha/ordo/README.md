# Orpha ORDO Curation

## Purpose

This directory contains curation scripts for Orpha ORDO (Orphanet Rare Disease Ontology) data, focusing on creating clean, curated datasets of disease instances and their associated metadata.

## Main Scripts

### `curate_disease_names.py`

**Purpose**: Creates a comprehensive mapping from orphacode to disease name using available data sources.

**Key Features**:
- Extracts disease names from multiple sources
- Prioritizes disease instances data over other sources
- Merges data from different sources intelligently
- Generates comprehensive creation statistics

**Usage**:
```bash
python curate_disease_names.py \
    --input data/04_curated/orpha/ordo/metabolic_disease_instances.json \
    --output data/04_curated/orpha/ordo/orphacode2disease_name.json
```

**Outputs**:
- `orphacode2disease_name.json`: Main mapping from orphacode to disease name
- `orphacode2disease_name_creation_summary.json`: Creation statistics and metadata

### `curate_disease_instances.py`

**Purpose**: Existing script for curating disease instances (reference implementation).

### `sample_disease_instances.py`

**Purpose**: Utility script for creating sample datasets from larger disease instances.

## Data Sources

### Primary Sources
- `metabolic_disease_instances.json`: Main disease instances dataset (665 diseases)
- `metabolic_disease_instances_sample_10.json`: Small sample dataset (10 diseases)

### Secondary Sources
- Orpha index from processed prevalence data
- Additional disease metadata from ORDO ontology

## Data Flow

```
Input: Disease Instances + Orpha Index
  ↓
Name Extraction & Merging
  ↓
Output: Orphacode → Disease Name Mapping
```

## Name Extraction Logic

1. **Primary Source**: Extract names from disease instances file
2. **Secondary Source**: Extract names from orpha index
3. **Merging**: Combine sources with priority to instances file
4. **Validation**: Check for empty/invalid names

## Quality Metrics

- **Total Diseases**: Number of diseases with name mappings
- **Unique Names**: Number of unique disease names
- **Data Quality**: Empty names, name length statistics
- **Coverage**: Percentage of requested diseases with names

## Integration

This module integrates with:
- `etl/04_curate/orpha/orphadata/` for prevalence data curation
- `core/datastore/orpha/orphadata/curated_prevalence_client.py` for data access
- Disease instance management workflows

## Output Structure

```
data/04_curated/orpha/ordo/
├── orphacode2disease_name.json                    # Main name mapping
├── orphacode2disease_name_creation_summary.json  # Creation statistics
├── metabolic_disease_instances.json               # Disease instances (665)
└── metabolic_disease_instances_sample_10.json     # Sample dataset (10)
```

## Usage in Downstream Processes

The orphacode2disease_name mapping is used by:
- Curated prevalence client for disease name resolution
- Statistics generation for human-readable reports
- Visualization tools for disease labeling
- API endpoints for disease information retrieval 