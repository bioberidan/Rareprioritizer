"""
XML to JSON converter for Orphanet disease data

Converts hierarchical XML structure to separated taxonomy and disease instance JSON files
"""
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .models import (
    TaxonomyNode, DiseaseInstance, Classification, DiseaseMetadata,
    TaxonomyStructure, TaxonomyRelationship, TaxonomyMetadata
)
from .exceptions import XMLParsingError, DataIntegrityError, ValidationError

logger = logging.getLogger(__name__)


class OrphaXMLConverter:
    """Converts Orphanet XML to optimized JSON structure with separated taxonomy and instances"""
    
    def __init__(self, xml_path: str, output_dir: str):
        """
        Initialize the converter
        
        Args:
            xml_path: Path to the Orphanet XML file
            output_dir: Directory to save the converted JSON files
        """
        self.xml_path = Path(xml_path)
        self.output_dir = Path(output_dir)
        
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML file not found: {xml_path}")
        
        # Create output directories
        self.taxonomy_dir = self.output_dir / "taxonomy"
        self.instances_dir = self.output_dir / "instances"
        self.cache_dir = self.output_dir / "cache"
        
        for dir_path in [self.taxonomy_dir, self.instances_dir, self.cache_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize data structures
        self.categories: Dict[str, TaxonomyNode] = {}
        self.diseases: Dict[str, DiseaseInstance] = {}
        self.relationships: Dict[str, TaxonomyRelationship] = {}
        self.classification_index: Dict[str, List[str]] = {}
        self.name_index: Dict[str, List[str]] = {}
        
        # Metadata
        self.xml_metadata: Dict[str, str] = {}
        self.statistics = {
            "total_categories": 0,
            "total_diseases": 0,
            "max_depth": 0,
            "diseases_by_level": {},
            "categories_by_level": {}
        }
    
    def convert_xml_to_json(self) -> None:
        """Main conversion method - orchestrates the entire conversion process"""
        logger.info(f"Starting XML conversion from {self.xml_path}")
        
        try:
            # Parse XML
            tree = ET.parse(self.xml_path)
            root = tree.getroot()
            
            # Extract metadata
            self._extract_metadata(root)
            
            # Find classification root
            classification = self._find_classification(root)
            if classification is None:
                raise XMLParsingError("No classification found in XML")
            
            # Process the classification tree
            root_nodes = classification.findall(".//ClassificationNodeRootList/ClassificationNode")
            for node in root_nodes:
                self._process_classification_node(node, parent_id=None, level=0)
            
            # Generate all output files
            self._generate_taxonomy_files()
            self._generate_instance_files()
            self._generate_cache_files()
            
            # Validate the output
            self._validate_output()
            
            logger.info("XML conversion completed successfully")
            logger.info(f"Processed {self.statistics['total_categories']} categories and {self.statistics['total_diseases']} diseases")
            
        except ET.ParseError as e:
            raise XMLParsingError(f"Failed to parse XML: {e}")
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise
    
    def _extract_metadata(self, root: ET.Element) -> None:
        """Extract metadata from XML root"""
        self.xml_metadata = {
            "date": root.get("date", ""),
            "version": root.get("version", ""),
            "copyright": root.get("copyright", ""),
            "dbserver": root.get("dbserver", "")
        }
    
    def _find_classification(self, root: ET.Element) -> Optional[ET.Element]:
        """Find the classification element in XML"""
        classifications = root.findall(".//ClassificationList/Classification")
        
        # Look for metabolic disease classification
        for classification in classifications:
            name_elem = classification.find(".//Name[@lang='en']")
            if name_elem is not None and "metabolism" in name_elem.text.lower():
                return classification
        
        # Return first classification if specific one not found
        return classifications[0] if classifications else None
    
    def _process_classification_node(self, node: ET.Element, parent_id: Optional[str], level: int) -> None:
        """Recursively process classification nodes"""
        disorder = node.find("Disorder")
        if disorder is None:
            return
        
        disorder_id = disorder.get("id")
        orpha_code_elem = disorder.find("OrphaCode")
        orpha_code = orpha_code_elem.text if orpha_code_elem is not None else disorder_id
        
        name_elem = disorder.find("Name[@lang='en']")
        name = name_elem.text if name_elem is not None else f"Unknown_{orpha_code}"
        
        disorder_type_elem = disorder.find("DisorderType/Name[@lang='en']")
        disorder_type = disorder_type_elem.text if disorder_type_elem is not None else "Unknown"
        
        expert_link_elem = disorder.find("ExpertLink[@lang='en']")
        expert_link = expert_link_elem.text if expert_link_elem is not None else None
        
        # Update max depth
        self.statistics["max_depth"] = max(self.statistics["max_depth"], level)
        
        # Process based on type
        if disorder_type == "Category" or level < 3:  # Treat upper levels as categories
            self._process_category(orpha_code, name, parent_id, level)
            
            # Process children
            child_list = node.find("ClassificationNodeChildList")
            if child_list is not None:
                for child in child_list.findall("ClassificationNode"):
                    self._process_classification_node(child, orpha_code, level + 1)
        else:
            # It's a disease
            self._process_disease(orpha_code, name, disorder_type, expert_link, parent_id, level)
            
            # Diseases can still have children (subtypes)
            child_list = node.find("ClassificationNodeChildList")
            if child_list is not None:
                for child in child_list.findall("ClassificationNode"):
                    self._process_classification_node(child, parent_id, level + 1)
    
    def _process_category(self, category_id: str, name: str, parent_id: Optional[str], level: int) -> None:
        """Process a category node"""
        node_type = "root_category" if level == 0 else "category"
        
        category = TaxonomyNode(
            id=category_id,
            name=name,
            type=node_type,
            level=level,
            parent_id=parent_id,
            children=[]
        )
        
        self.categories[category_id] = category
        
        # Update relationships
        if category_id not in self.relationships:
            self.relationships[category_id] = TaxonomyRelationship(parent=parent_id, children=[])
        else:
            self.relationships[category_id].parent = parent_id
        
        if parent_id:
            if parent_id not in self.relationships:
                self.relationships[parent_id] = TaxonomyRelationship(children=[])
            if category_id not in self.relationships[parent_id].children:
                self.relationships[parent_id].children.append(category_id)
            
            # Update parent's children list
            if parent_id in self.categories:
                if category_id not in self.categories[parent_id].children:
                    self.categories[parent_id].children.append(category_id)
        
        # Update name index
        if name not in self.name_index:
            self.name_index[name] = []
        self.name_index[name].append(category_id)
        
        # Update statistics
        self.statistics["total_categories"] += 1
        if level not in self.statistics["categories_by_level"]:
            self.statistics["categories_by_level"][level] = 0
        self.statistics["categories_by_level"][level] += 1
    
    def _process_disease(self, disease_id: str, name: str, disorder_type: str, 
                        expert_link: Optional[str], parent_id: Optional[str], level: int) -> None:
        """Process a disease instance"""
        if not parent_id:
            logger.warning(f"Disease {disease_id} ({name}) has no parent category")
            return
        
        # Build path to root
        path = self._build_path_to_root(parent_id)
        path.append(disease_id)
        
        # Create disease instance
        disease = DiseaseInstance(
            id=disease_id,
            name=name,
            type="disease",
            classification=Classification(
                category_id=parent_id,
                path=path[:-1],  # Exclude the disease itself from path
                level=level
            ),
            metadata=DiseaseMetadata(
                expert_link=expert_link,
                disorder_type=disorder_type,
                orpha_code=disease_id,
                last_updated=datetime.now().isoformat()
            )
        )
        
        self.diseases[disease_id] = disease
        
        # Update classification index
        if parent_id not in self.classification_index:
            self.classification_index[parent_id] = []
        self.classification_index[parent_id].append(disease_id)
        
        # Update name index
        if name not in self.name_index:
            self.name_index[name] = []
        self.name_index[name].append(disease_id)
        
        # Also index common abbreviations
        if "-" in name:
            abbrev = name.split("-")[-1]
            if abbrev not in self.name_index:
                self.name_index[abbrev] = []
            self.name_index[abbrev].append(disease_id)
        
        # Update statistics
        self.statistics["total_diseases"] += 1
        if level not in self.statistics["diseases_by_level"]:
            self.statistics["diseases_by_level"][level] = 0
        self.statistics["diseases_by_level"][level] += 1
    
    def _build_path_to_root(self, node_id: str) -> List[str]:
        """Build path from root to given node"""
        path = []
        current_id = node_id
        
        while current_id:
            if current_id in path:  # Circular reference detection
                logger.error(f"Circular reference detected at node {current_id}")
                break
                
            path.append(current_id)
            
            if current_id in self.relationships and self.relationships[current_id].parent:
                current_id = self.relationships[current_id].parent
            else:
                break
        
        return list(reversed(path))
    
    def _generate_taxonomy_files(self) -> None:
        """Generate taxonomy-related JSON files"""
        logger.info("Generating taxonomy files...")
        
        # Structure file
        structure = {
            "nodes": {cat_id: cat.model_dump() for cat_id, cat in self.categories.items()},
            "relationships": {rel_id: rel.model_dump() for rel_id, rel in self.relationships.items() 
                            if rel_id in self.categories}  # Only category relationships
        }
        
        structure_path = self.taxonomy_dir / "structure.json"
        with open(structure_path, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        
        # Categories file (detailed info)
        categories_path = self.taxonomy_dir / "categories.json"
        with open(categories_path, 'w', encoding='utf-8') as f:
            json.dump({cat_id: cat.model_dump() for cat_id, cat in self.categories.items()}, 
                     f, indent=2, ensure_ascii=False)
        
        # Relationships file
        relationships_path = self.taxonomy_dir / "relationships.json"
        with open(relationships_path, 'w', encoding='utf-8') as f:
            json.dump({rel_id: rel.model_dump() for rel_id, rel in self.relationships.items()
                      if rel_id in self.categories}, 
                     f, indent=2, ensure_ascii=False)
        
        # Metadata file
        metadata = TaxonomyMetadata(
            version="2.0.0",
            source_file=self.xml_path.name,
            generation_date=datetime.now().isoformat(),
            xml_date=self.xml_metadata.get("date"),
            xml_version=self.xml_metadata.get("version"),
            total_categories=self.statistics["total_categories"],
            total_diseases=self.statistics["total_diseases"],
            max_depth=self.statistics["max_depth"]
        )
        
        metadata_path = self.taxonomy_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata.model_dump(), f, indent=2, ensure_ascii=False)
    
    def _generate_instance_files(self) -> None:
        """Generate disease instance JSON files"""
        logger.info("Generating instance files...")
        
        # Diseases file
        diseases_path = self.instances_dir / "diseases.json"
        with open(diseases_path, 'w', encoding='utf-8') as f:
            json.dump({dis_id: dis.model_dump() for dis_id, dis in self.diseases.items()}, 
                     f, indent=2, ensure_ascii=False)
        
        # Classification index
        classification_index_path = self.instances_dir / "classification_index.json"
        with open(classification_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.classification_index, f, indent=2, ensure_ascii=False)
        
        # Name index
        name_index_path = self.instances_dir / "name_index.json"
        with open(name_index_path, 'w', encoding='utf-8') as f:
            json.dump(self.name_index, f, indent=2, ensure_ascii=False)
        
        # Disease metadata (extended info, currently same as in diseases.json)
        disease_metadata_path = self.instances_dir / "disease_metadata.json"
        with open(disease_metadata_path, 'w', encoding='utf-8') as f:
            metadata_dict = {
                dis_id: dis.metadata.model_dump() 
                for dis_id, dis in self.diseases.items()
            }
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
    
    def _generate_cache_files(self) -> None:
        """Generate cache files for performance optimization"""
        logger.info("Generating cache files...")
        
        # Paths cache
        paths = {}
        for disease_id, disease in self.diseases.items():
            path = disease.classification.path + [disease_id]
            path_names = []
            
            for node_id in path[:-1]:  # Exclude disease itself
                if node_id in self.categories:
                    path_names.append(self.categories[node_id].name)
            path_names.append(disease.name)
            
            paths[disease_id] = {
                "path_to_root": path,
                "path_names": path_names
            }
        
        paths_path = self.cache_dir / "paths.json"
        with open(paths_path, 'w', encoding='utf-8') as f:
            json.dump(paths, f, indent=2, ensure_ascii=False)
        
        # Statistics cache
        total_nodes = self.statistics["total_categories"] + self.statistics["total_diseases"]
        avg_diseases = (self.statistics["total_diseases"] / self.statistics["total_categories"] 
                       if self.statistics["total_categories"] > 0 else 0)
        
        statistics = {
            "total_nodes": total_nodes,
            "total_diseases": self.statistics["total_diseases"],
            "total_categories": self.statistics["total_categories"],
            "max_depth": self.statistics["max_depth"],
            "avg_diseases_per_category": round(avg_diseases, 2),
            "diseases_by_level": self.statistics["diseases_by_level"],
            "categories_by_level": self.statistics["categories_by_level"]
        }
        
        statistics_path = self.cache_dir / "statistics.json"
        with open(statistics_path, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        # Combined views (empty for now, will be populated on demand)
        combined_views_path = self.cache_dir / "combined_views.json"
        with open(combined_views_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    
    def _validate_output(self) -> None:
        """Validate the generated output files"""
        issues = []
        warnings = []
        
        # Check all required files exist
        required_files = [
            self.taxonomy_dir / "structure.json",
            self.taxonomy_dir / "categories.json",
            self.taxonomy_dir / "relationships.json",
            self.taxonomy_dir / "metadata.json",
            self.instances_dir / "diseases.json",
            self.instances_dir / "classification_index.json",
            self.instances_dir / "name_index.json",
            self.cache_dir / "paths.json",
            self.cache_dir / "statistics.json"
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                issues.append(f"Required file missing: {file_path}")
        
        # Validate data integrity
        orphan_diseases = 0
        for disease_id, disease in self.diseases.items():
            if disease.classification.category_id not in self.categories:
                orphan_diseases += 1
                warnings.append(f"Disease {disease_id} references non-existent category {disease.classification.category_id}")
        
        if orphan_diseases > 0:
            warnings.append(f"Found {orphan_diseases} orphaned diseases")
        
        # Check for circular references
        for cat_id in self.categories:
            path = self._build_path_to_root(cat_id)
            if len(path) != len(set(path)):
                issues.append(f"Circular reference detected for category {cat_id}")
        
        if issues:
            raise ValidationError("Output validation failed", issues)
        
        if warnings:
            logger.warning(f"Validation completed with {len(warnings)} warnings")
            for warning in warnings[:10]:  # Show first 10 warnings
                logger.warning(warning)
            if len(warnings) > 10:
                logger.warning(f"... and {len(warnings) - 10} more warnings")


def convert_orpha_xml(xml_path: str, output_dir: str) -> None:
    """
    Convenience function to convert Orphanet XML to JSON
    
    Args:
        xml_path: Path to the Orphanet XML file
        output_dir: Directory to save the converted JSON files
    """
    converter = OrphaXMLConverter(xml_path, output_dir)
    converter.convert_xml_to_json() 