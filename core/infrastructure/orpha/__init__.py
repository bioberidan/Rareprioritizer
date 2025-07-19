"""
Orpha Disease Preprocessing System

A high-performance system for processing Orphanet XML data into structured JSON outputs
with separated taxonomy structure and disease instances for optimal performance and scalability.

Main components:
- OrphaTaxonomy: Main interface for disease taxonomy navigation
- TaxonomyGraph: Lightweight taxonomy structure navigation  
- DiseaseInstances: Lazy-loaded disease instance management
- OrphaXMLConverter: XML to JSON conversion utilities
"""

__version__ = "2.0.0"

from .taxonomy import OrphaTaxonomy
from .taxonomy_graph import TaxonomyGraph
from .disease_instances import DiseaseInstances
from .xml_converter import OrphaXMLConverter, convert_orpha_xml

__all__ = [
    "__version__",
    "OrphaTaxonomy",
    "TaxonomyGraph", 
    "DiseaseInstances",
    "OrphaXMLConverter",
    "convert_orpha_xml"
] 