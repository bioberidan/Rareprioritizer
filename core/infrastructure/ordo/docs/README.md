# Orpha Disease Preprocessing System

A high-performance system for processing Orphanet XML data into structured JSON outputs with separated taxonomy structure and disease instances for optimal performance and scalability.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [Basic Usage](#basic-usage)
- [Performance Features](#performance-features)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Documentation](#documentation)

## Overview

The Orpha Disease Preprocessing System provides a modern, efficient approach to working with Orphanet disease taxonomy data. It separates taxonomy structure from disease instances, enabling fast navigation and memory-efficient operations.

### Key Features

- **Separated Architecture**: Taxonomy structure (~50KB) separated from disease instances (~1.2MB)
- **Lazy Loading**: Memory-efficient design loading only essential data initially
- **Fast Performance**: Initialization in ~10-50ms vs traditional XML loading (~2-5 seconds)
- **Flexible API**: Multiple ways to access data (by ID, name, search)
- **Comprehensive Navigation**: Parent-child relationships, path finding, subtree operations
- **Batch Operations**: Efficient processing of multiple diseases/categories

## Installation

### Prerequisites

- Python 3.8+
- Required packages: `pydantic`, `lxml` (for XML processing)

### Install Dependencies

```bash
pip install pydantic lxml
```

### Data Preparation

1. **Process XML Data**: Convert Orphanet XML to optimized JSON format
   ```bash
   python tools/disease_preprocessing.py path/to/your/orphanet.xml data/processed/
   ```

2. **Verify Installation**: Check that processed data is available
   ```bash
   ls data/processed/
   # Should show: taxonomy/ instances/ cache/
   ```

## Quick Start

```python
from utils.orpha import OrphaTaxonomy

# Initialize the taxonomy system
taxonomy = OrphaTaxonomy(data_dir="data/processed")

# Get basic statistics
stats = taxonomy.get_statistics()
print(f"Total categories: {stats['combined']['total_categories']}")
print(f"Total diseases: {stats['combined']['total_diseases']}")

# Find a disease by name
disease = taxonomy.get_node_by_name("Glycogen storage disease")
print(f"Disease: {disease.name} (ID: {disease.id})")

# Navigate to parent category
parent = taxonomy.get_parent(disease.id)
print(f"Parent category: {parent.name}")

# Get all diseases in a category
diseases = taxonomy.get_diseases_in_category_by_name("Inborn errors of metabolism")
print(f"Found {len(diseases)} diseases in category")
```

## Core Concepts

### 1. Separated Architecture

The system separates data into two main components:

- **Taxonomy Structure**: Hierarchical category tree (lightweight, ~50KB)
- **Disease Instances**: Individual disease records (larger, ~1.2MB)

This separation enables:
- Fast taxonomy navigation without loading all diseases
- Memory-efficient operations
- Independent scaling of components

### 2. Lazy Loading

- **Taxonomy**: Always loaded (lightweight)
- **Disease Instances**: Loaded on-demand with intelligent caching
- **Performance**: Only load what you need, when you need it

### 3. Unified API

Access data through multiple methods:
- **By ID**: `get_node(node_id)`
- **By Name**: `get_node_by_name(name)`
- **By Search**: `search_by_name(query)`
- **By Relationship**: `get_parent()`, `get_children()`, `get_path_to_root()`

## Basic Usage

### Initialize the System

```python
from utils.orpha import OrphaTaxonomy

# Basic initialization
taxonomy = OrphaTaxonomy()

# Custom data directory
taxonomy = OrphaTaxonomy(data_dir="path/to/your/data")

# Preload all diseases (uses more memory but faster access)
taxonomy = OrphaTaxonomy(preload_diseases=True)
```

### Navigate Categories

```python
# Get a category by ID
category = taxonomy.get_node("C01")

# Get category by name
category = taxonomy.get_node_by_name("Inborn errors of metabolism")

# Get parent category
parent = taxonomy.get_parent(category.id)

# Get child categories and diseases
children = taxonomy.get_children(category.id)

# Get path from root
path = taxonomy.get_path_to_root(category.id)
print(" -> ".join([node.name for node in path]))
```

### Work with Diseases

```python
# Get a disease by name
disease = taxonomy.get_node_by_name("Glycogen storage disease")

# Get all diseases in a category
diseases = taxonomy.get_diseases_in_category_by_name("Metabolic disorders")

# Count diseases in a subtree
count = taxonomy.count_diseases_in_subtree("C01")
print(f"Total diseases in subtree: {count}")
```

### Search Operations

```python
# Search for nodes by partial name
results = taxonomy.search_by_name("glycogen")
for node_id, name in results:
    print(f"{node_id}: {name}")

# Search only diseases
disease_results = taxonomy.search_by_name("storage", node_type="disease")

# Search only categories
category_results = taxonomy.search_by_name("metabolic", node_type="category")
```

### Handle Name Conflicts

```python
# Some names might be ambiguous
try:
    node = taxonomy.get_node_by_name("Diabetes")
except AmbiguousNameError as e:
    print(f"Ambiguous name: {e.name}")
    print(f"Possible IDs: {e.candidate_ids}")
    
    # Resolve by type
    diseases = taxonomy.resolve_name("Diabetes", node_type="disease")
    categories = taxonomy.resolve_name("Diabetes", node_type="category")
```

## Performance Features

### Memory Optimization

```python
# Lightweight initialization (recommended)
taxonomy = OrphaTaxonomy()  # ~10-50ms, minimal memory

# Memory usage info
stats = taxonomy.get_statistics()
print(f"Loaded diseases: {stats['diseases']['loaded_count']}")
print(f"Total diseases: {stats['diseases']['total_diseases']}")
```

### Batch Operations

```python
# Get all diseases in a subtree (efficient)
all_diseases = taxonomy.get_all_diseases_in_subtree("C01")

# Process multiple categories
categories = ["C01", "C02", "C03"]
for cat_id in categories:
    count = taxonomy.count_diseases_in_subtree(cat_id)
    print(f"Category {cat_id}: {count} diseases")
```

### Caching

```python
# The system automatically caches accessed data
# Subsequent access to the same disease is instant
disease1 = taxonomy.get_node("D001")  # Loads from disk
disease2 = taxonomy.get_node("D001")  # Returns from cache
```

## API Reference

### Main Classes

- **`OrphaTaxonomy`**: Main interface for disease taxonomy navigation
- **`TaxonomyGraph`**: Lightweight taxonomy structure navigation
- **`DiseaseInstances`**: Lazy-loaded disease instance management
- **`OrphaXMLConverter`**: XML to JSON conversion utilities

### Key Methods

| Method | Description |
|--------|-------------|
| `get_node(node_id)` | Get any node by ID |
| `get_node_by_name(name)` | Get node by name (raises error if ambiguous) |
| `get_parent(node_id)` | Get parent of any node |
| `get_children(node_id)` | Get children of a node |
| `get_path_to_root(node_id)` | Get path from root to node |
| `search_by_name(query)` | Search nodes by partial name |
| `get_statistics()` | Get comprehensive system statistics |
| `validate()` | Validate taxonomy integrity |

For complete API documentation, see [API_REFERENCE.md](API_REFERENCE.md).

## Examples

### Example 1: Basic Navigation

```python
from utils.orpha import OrphaTaxonomy

# Initialize
taxonomy = OrphaTaxonomy()

# Navigate the taxonomy
category = taxonomy.get_node_by_name("Inborn errors of metabolism")
print(f"Category: {category.name}")
print(f"Description: {category.description}")

# Get diseases in this category
diseases = taxonomy.get_diseases_in_category_by_name(category.name)
print(f"Found {len(diseases)} diseases")

# Show first few diseases
for disease in diseases[:5]:
    print(f"  - {disease.name} (ID: {disease.id})")
```

### Example 2: Search and Analysis

```python
# Search for metabolic disorders
results = taxonomy.search_by_name("metabolic", node_type="disease")
print(f"Found {len(results)} metabolic diseases")

# Analyze a category subtree
stats = taxonomy.get_statistics()
print(f"Total taxonomy depth: {stats['taxonomy']['max_depth']}")

# Get diseases in a subtree
metabolic_diseases = taxonomy.get_all_diseases_in_subtree("C01")
print(f"Total diseases in metabolic subtree: {len(metabolic_diseases)}")
```

### Example 3: Batch Processing

```python
# Process multiple categories
categories_of_interest = [
    "Inborn errors of metabolism",
    "Neurological disorders", 
    "Cardiovascular disorders"
]

for cat_name in categories_of_interest:
    try:
        category = taxonomy.get_node_by_name(cat_name)
        count = taxonomy.count_diseases_in_subtree(category.id)
        print(f"{cat_name}: {count} diseases")
    except NodeNotFoundError:
        print(f"Category not found: {cat_name}")
```

## Documentation

- **[API Reference](API_REFERENCE.md)**: Complete method documentation
- **[Architecture Guide](ARCHITECTURE.md)**: System design and components
- **[Performance Guide](PERFORMANCE_GUIDE.md)**: Optimization tips and benchmarks
- **[Troubleshooting](TROUBLESHOOTING.md)**: Common issues and solutions
- **[Cookbooks](../../cookbooks/orpha/)**: Jupyter notebook tutorials

## Error Handling

The system provides specific exceptions for different error conditions:

```python
from utils.orpha.exceptions import (
    NodeNotFoundError,
    AmbiguousNameError,
    FileNotFoundError,
    DataIntegrityError
)

try:
    disease = taxonomy.get_node_by_name("Unknown Disease")
except NodeNotFoundError as e:
    print(f"Disease not found: {e.node_id}")
except AmbiguousNameError as e:
    print(f"Multiple diseases found for: {e.name}")
```

## Performance Benchmarks

- **Initialization**: ~10-50ms (vs ~2-5 seconds for XML loading)
- **Memory Usage**: ~50KB taxonomy + on-demand disease loading
- **Query Speed**: <1ms for cached nodes, <10ms for disk loading
- **Batch Operations**: Efficient processing of thousands of nodes

## Support

For questions, issues, or contributions:
1. Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Review the [API Reference](API_REFERENCE.md)
3. Explore the [Cookbooks](../../cookbooks/orpha/)
4. Check existing issues or create a new one

## Version

Current version: 2.0.0

See [CHANGELOG.md](CHANGELOG.md) for version history and updates. 