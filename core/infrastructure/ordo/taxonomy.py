"""
OrphaTaxonomy - Main interface for disease taxonomy navigation

This module provides the main combined interface for navigating both taxonomy structure and disease instances.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from .taxonomy_graph import TaxonomyGraph
from .disease_instances import DiseaseInstances  
from .models import TaxonomyNode, DiseaseInstance, ValidationResult
from .exceptions import NodeNotFoundError, AmbiguousNameError, FileNotFoundError

logger = logging.getLogger(__name__)


class OrphaTaxonomy:
    """Main interface combining taxonomy structure and disease instance management"""
    
    def __init__(self, data_dir: str = "data/processed", preload_diseases: bool = False):
        """
        Initialize the Orpha taxonomy system
        
        Args:
            data_dir: Directory containing processed taxonomy and instance data
            preload_diseases: If True, preload all disease data (uses more memory)
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        
        # Initialize components
        taxonomy_dir = self.data_dir / "taxonomy"
        instances_dir = self.data_dir / "instances"
        cache_dir = self.data_dir / "cache"
        
        self.taxonomy = TaxonomyGraph(str(taxonomy_dir))
        self.diseases = DiseaseInstances(str(instances_dir))
        self.cache_dir = cache_dir
        
        # Name resolution cache
        self._name_cache: Dict[str, List[str]] = {}
        self._load_name_cache()
        
        # Optionally preload diseases
        if preload_diseases:
            logger.info("Preloading all disease data...")
            self.diseases.preload_all()
    
    def _load_name_cache(self) -> None:
        """Load combined name index for fast resolution"""
        # Combine category and disease names
        for category in self.taxonomy.get_all_categories():
            if category.name not in self._name_cache:
                self._name_cache[category.name] = []
            self._name_cache[category.name].append(category.id)
        
        # Add disease names (already in disease name index)
        for name, ids in self.diseases._name_index.items():
            if name not in self._name_cache:
                self._name_cache[name] = []
            self._name_cache[name].extend(ids)
    
    # ========== Basic Navigation Methods ==========
    
    def get_node(self, node_id: str) -> Union[TaxonomyNode, DiseaseInstance, None]:
        """
        Get any node (category or disease) by ID
        
        Args:
            node_id: ID of the node
            
        Returns:
            TaxonomyNode, DiseaseInstance, or None
        """
        # Try category first (faster)
        category = self.taxonomy.get_category(node_id)
        if category:
            return category
        
        # Then try disease
        return self.diseases.get_disease(node_id)
    
    def get_parent(self, node_id: str) -> Optional[TaxonomyNode]:
        """
        Get parent of any node (category or disease)
        
        Args:
            node_id: ID of the node
            
        Returns:
            Parent TaxonomyNode or None
        """
        # Check if it's a category
        category = self.taxonomy.get_category(node_id)
        if category:
            return self.taxonomy.get_category_parent(node_id)
        
        # Check if it's a disease
        disease = self.diseases.get_disease(node_id)
        if disease:
            parent_id = disease.classification.category_id
            return self.taxonomy.get_category(parent_id)
        
        raise NodeNotFoundError(node_id)
    
    def get_children(self, node_id: str) -> List[Union[TaxonomyNode, DiseaseInstance]]:
        """
        Get children of a node (categories and diseases)
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of child nodes (mixed categories and diseases)
        """
        # Only categories can have children
        if node_id not in self.taxonomy._nodes:
            return []
        
        children = []
        
        # Get child categories
        child_categories = self.taxonomy.get_category_children(node_id)
        children.extend(child_categories)
        
        # Get diseases in this category
        diseases = self.diseases.get_diseases_in_category(node_id)
        children.extend(diseases)
        
        return children
    
    def get_path_to_root(self, node_id: str) -> List[Union[TaxonomyNode, DiseaseInstance]]:
        """
        Get path from root to any node
        
        Args:
            node_id: ID of the node
            
        Returns:
            List of nodes from root to target
        """
        # Check if it's a category
        category = self.taxonomy.get_category(node_id)
        if category:
            return self.taxonomy.get_category_path(node_id)
        
        # Check if it's a disease
        disease = self.diseases.get_disease(node_id)
        if disease:
            # Get path to parent category, then add disease
            path = []
            for cat_id in disease.classification.path:
                cat = self.taxonomy.get_category(cat_id)
                if cat:
                    path.append(cat)
            path.append(disease)
            return path
        
        raise NodeNotFoundError(node_id)
    
    # ========== Name-Based Methods ==========
    
    def get_node_by_name(self, name: str, node_type: Optional[str] = None) -> Union[TaxonomyNode, DiseaseInstance]:
        """
        Get a node by name (raises error if ambiguous)
        
        Args:
            name: Name of the node
            node_type: Optional filter - "category" or "disease"
            
        Returns:
            TaxonomyNode or DiseaseInstance
            
        Raises:
            AmbiguousNameError: If name maps to multiple nodes
            NodeNotFoundError: If name not found
        """
        ids = self.resolve_name(name, node_type)
        
        if not ids:
            raise NodeNotFoundError(name, "name")
        
        if len(ids) > 1:
            raise AmbiguousNameError(name, ids)
        
        return self.get_node(ids[0])
    
    def resolve_name(self, name: str, node_type: Optional[str] = None) -> List[str]:
        """
        Resolve a name to one or more node IDs
        
        Args:
            name: Name to resolve
            node_type: Optional filter - "category" or "disease"
            
        Returns:
            List of matching node IDs
        """
        all_ids = self._name_cache.get(name, [])
        
        if not node_type:
            return all_ids
        
        # Filter by type
        filtered_ids = []
        for node_id in all_ids:
            node = self.get_node(node_id)
            if node_type == "category" and isinstance(node, TaxonomyNode):
                filtered_ids.append(node_id)
            elif node_type == "disease" and isinstance(node, DiseaseInstance):
                filtered_ids.append(node_id)
        
        return filtered_ids
    
    def search_by_name(self, query: str, node_type: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Search for nodes by partial name match
        
        Args:
            query: Search query (case-insensitive)
            node_type: Optional filter - "category" or "disease"
            
        Returns:
            List of (id, name) tuples
        """
        query_lower = query.lower()
        results = []
        
        # Search categories
        if node_type != "disease":
            for category in self.taxonomy.get_all_categories():
                if query_lower in category.name.lower():
                    results.append((category.id, category.name))
        
        # Search diseases (requires loading)
        if node_type != "category":
            diseases = self.diseases.search_diseases_by_name(query, exact=False)
            for disease in diseases:
                results.append((disease.id, disease.name))
        
        return results
    
    # ========== Convenience Methods with Name Support ==========
    
    def get_parent_from_name(self, name: str) -> Optional[TaxonomyNode]:
        """Get parent of a node by name"""
        node = self.get_node_by_name(name)
        return self.get_parent(node.id)
    
    def get_children_from_name(self, name: str) -> List[Union[TaxonomyNode, DiseaseInstance]]:
        """Get children of a node by name"""
        node = self.get_node_by_name(name)
        return self.get_children(node.id)
    
    def get_path_from_name(self, name: str) -> List[Union[TaxonomyNode, DiseaseInstance]]:
        """Get path to root from a node name"""
        node = self.get_node_by_name(name)
        return self.get_path_to_root(node.id)
    
    def get_diseases_in_category_by_name(self, category_name: str) -> List[DiseaseInstance]:
        """Get all diseases in a category by category name"""
        category = self.get_node_by_name(category_name, node_type="category")
        return self.diseases.get_diseases_in_category(category.id)
    
    # ========== Statistics and Analysis ==========
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about the taxonomy
        
        Returns:
            Dictionary with combined statistics
        """
        taxonomy_stats = self.taxonomy.get_statistics()
        disease_stats = self.diseases.get_statistics()
        
        # Combine statistics
        return {
            "taxonomy": taxonomy_stats,
            "diseases": disease_stats,
            "combined": {
                "total_nodes": taxonomy_stats["total_categories"] + disease_stats["total_diseases"],
                "total_categories": taxonomy_stats["total_categories"],
                "total_diseases": disease_stats["total_diseases"],
                "max_depth": taxonomy_stats["max_depth"],
                "avg_diseases_per_category": disease_stats["avg_diseases_per_category"]
            }
        }
    
    def validate(self) -> ValidationResult:
        """
        Validate the entire taxonomy system
        
        Returns:
            ValidationResult with any issues found
        """
        # Validate taxonomy structure
        taxonomy_result = self.taxonomy.validate_taxonomy_structure()
        
        issues = taxonomy_result.issues.copy()
        warnings = taxonomy_result.warnings.copy()
        
        # Additional cross-validation
        # Check that all diseases reference valid categories
        for disease_ids in self.diseases._classification_index.values():
            for disease_id in disease_ids:
                disease = self.diseases.get_disease(disease_id)
                if disease:
                    cat_id = disease.classification.category_id
                    if not self.taxonomy.get_category(cat_id):
                        issues.append(f"Disease {disease_id} references non-existent category {cat_id}")
        
        # Check name conflicts
        for name, ids in self._name_cache.items():
            if len(ids) > 1:
                # Check if they're different types
                types = set()
                for node_id in ids:
                    node = self.get_node(node_id)
                    if isinstance(node, TaxonomyNode):
                        types.add("category")
                    elif isinstance(node, DiseaseInstance):
                        types.add("disease")
                
                if len(types) > 1:
                    warnings.append(f"Name '{name}' is used by both categories and diseases: {ids}")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings
        )
    
    # ========== Batch Operations ==========
    
    def get_all_diseases_in_subtree(self, category_id: str) -> List[DiseaseInstance]:
        """
        Get all diseases in a category and its descendants
        
        Args:
            category_id: Root category ID
            
        Returns:
            List of all diseases in the subtree
        """
        diseases = []
        
        # Get diseases in this category
        diseases.extend(self.diseases.get_diseases_in_category(category_id))
        
        # Get diseases in descendant categories
        descendants = self.taxonomy.get_category_descendants(category_id)
        for desc_cat in descendants:
            diseases.extend(self.diseases.get_diseases_in_category(desc_cat.id))
        
        return diseases
    
    def count_diseases_in_subtree(self, category_id: str) -> int:
        """
        Count all diseases in a category and its descendants
        
        Args:
            category_id: Root category ID
            
        Returns:
            Total disease count in subtree
        """
        count = self.diseases.count_diseases_in_category(category_id)
        
        # Add counts from descendants
        descendants = self.taxonomy.get_category_descendants(category_id)
        for desc_cat in descendants:
            count += self.diseases.count_diseases_in_category(desc_cat.id)
        
        return count
    
    # ========== Export Methods ==========
    
    def export_subtree(self, root_id: str, output_file: str) -> None:
        """
        Export a subtree to JSON file
        
        Args:
            root_id: Root node ID
            output_file: Output JSON file path
        """
        node = self.get_node(root_id)
        if not node:
            raise NodeNotFoundError(root_id)
        
        # Build subtree data
        subtree_data = {
            "root": node.model_dump() if hasattr(node, 'model_dump') else node.dict(),
            "categories": {},
            "diseases": {}
        }
        
        if isinstance(node, TaxonomyNode):
            # Get all descendant categories
            descendants = self.taxonomy.get_category_descendants(root_id)
            for cat in descendants:
                subtree_data["categories"][cat.id] = cat.model_dump()
            
            # Get all diseases in subtree
            diseases = self.get_all_diseases_in_subtree(root_id)
            for disease in diseases:
                subtree_data["diseases"][disease.id] = disease.model_dump()
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(subtree_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported subtree to {output_file}")
    
    def get_node_type(self, node_id: str) -> Optional[str]:
        """
        Get the type of a node
        
        Args:
            node_id: Node ID
            
        Returns:
            "category", "disease", or None
        """
        if self.taxonomy.get_category(node_id):
            return "category"
        elif self.diseases.get_disease(node_id):
            return "disease"
        return None 