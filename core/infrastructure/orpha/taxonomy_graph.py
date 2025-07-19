"""
TaxonomyGraph - Lightweight taxonomy structure navigation

This module provides fast navigation through the taxonomy structure without loading disease instances.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

from .models import TaxonomyNode, TaxonomyRelationship, ValidationResult
from .exceptions import NodeNotFoundError, FileNotFoundError, InvalidDataFormatError

logger = logging.getLogger(__name__)


class TaxonomyGraph:
    """Navigate taxonomy structure only (lightweight, categories only)"""
    
    def __init__(self, taxonomy_dir: str):
        """
        Initialize the taxonomy graph
        
        Args:
            taxonomy_dir: Directory containing taxonomy JSON files
        """
        self.taxonomy_dir = Path(taxonomy_dir)
        
        if not self.taxonomy_dir.exists():
            raise FileNotFoundError(f"Taxonomy directory not found: {taxonomy_dir}")
        
        # Load taxonomy structure
        self._structure: Dict[str, Dict] = {}
        self._relationships: Dict[str, Dict] = {}
        self._nodes: Dict[str, TaxonomyNode] = {}
        
        self._load_taxonomy_structure()
    
    def _load_taxonomy_structure(self) -> None:
        """Load taxonomy structure from JSON files"""
        try:
            # Load structure file
            structure_path = self.taxonomy_dir / "structure.json"
            if not structure_path.exists():
                raise FileNotFoundError(f"Structure file not found: {structure_path}")
            
            with open(structure_path, 'r', encoding='utf-8') as f:
                structure_data = json.load(f)
            
            # Parse nodes
            if 'nodes' in structure_data:
                for node_id, node_data in structure_data['nodes'].items():
                    self._nodes[node_id] = TaxonomyNode(**node_data)
            
            # Parse relationships
            if 'relationships' in structure_data:
                self._relationships = structure_data['relationships']
            
            self._structure = structure_data
            
            logger.info(f"Loaded taxonomy with {len(self._nodes)} categories")
            
        except json.JSONDecodeError as e:
            raise InvalidDataFormatError(f"Invalid JSON in taxonomy files: {e}")
        except Exception as e:
            logger.error(f"Failed to load taxonomy structure: {e}")
            raise
    
    def get_category(self, category_id: str) -> Optional[TaxonomyNode]:
        """
        Get a category node by ID
        
        Args:
            category_id: ID of the category
            
        Returns:
            TaxonomyNode or None if not found
        """
        return self._nodes.get(category_id)
    
    def get_category_parent(self, category_id: str) -> Optional[TaxonomyNode]:
        """
        Get the parent category of a given category
        
        Args:
            category_id: ID of the category
            
        Returns:
            Parent TaxonomyNode or None if no parent
        """
        if category_id not in self._relationships:
            raise NodeNotFoundError(category_id, "category")
        
        parent_id = self._relationships[category_id].get('parent')
        if parent_id:
            return self.get_category(parent_id)
        return None
    
    def get_category_children(self, category_id: str) -> List[TaxonomyNode]:
        """
        Get child categories of a given category
        
        Args:
            category_id: ID of the parent category
            
        Returns:
            List of child TaxonomyNodes
        """
        if category_id not in self._relationships:
            raise NodeNotFoundError(category_id, "category")
        
        children_ids = self._relationships[category_id].get('children', [])
        children = []
        for child_id in children_ids:
            child = self.get_category(child_id)
            if child:
                children.append(child)
        
        return children
    
    def get_category_path(self, category_id: str) -> List[TaxonomyNode]:
        """
        Get path from root to the given category
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of TaxonomyNodes from root to target category
        """
        if category_id not in self._nodes:
            raise NodeNotFoundError(category_id, "category")
        
        path = []
        current_id = category_id
        visited = set()  # Circular reference protection
        
        while current_id:
            if current_id in visited:
                logger.warning(f"Circular reference detected at category {current_id}")
                break
            
            visited.add(current_id)
            node = self.get_category(current_id)
            if node:
                path.append(node)
            
            # Get parent
            if current_id in self._relationships:
                current_id = self._relationships[current_id].get('parent')
            else:
                break
        
        return list(reversed(path))
    
    def get_all_categories(self) -> List[TaxonomyNode]:
        """
        Get all categories in the taxonomy
        
        Returns:
            List of all TaxonomyNodes
        """
        return list(self._nodes.values())
    
    def get_root_categories(self) -> List[TaxonomyNode]:
        """
        Get all root categories (categories with no parent)
        
        Returns:
            List of root TaxonomyNodes
        """
        roots = []
        for node_id, node in self._nodes.items():
            if node_id not in self._relationships or not self._relationships[node_id].get('parent'):
                roots.append(node)
        return roots
    
    def get_category_ancestors(self, category_id: str) -> List[TaxonomyNode]:
        """
        Get all ancestors of a category (from parent to root)
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of ancestor TaxonomyNodes
        """
        path = self.get_category_path(category_id)
        # Remove the category itself from path
        return path[:-1] if path else []
    
    def get_category_descendants(self, category_id: str, max_depth: Optional[int] = None) -> List[TaxonomyNode]:
        """
        Get all descendants of a category (recursive)
        
        Args:
            category_id: ID of the category
            max_depth: Maximum depth to traverse (None for unlimited)
            
        Returns:
            List of descendant TaxonomyNodes
        """
        if category_id not in self._nodes:
            raise NodeNotFoundError(category_id, "category")
        
        descendants = []
        
        def traverse(cat_id: str, current_depth: int = 0):
            if max_depth is not None and current_depth >= max_depth:
                return
            
            children = self.get_category_children(cat_id)
            for child in children:
                descendants.append(child)
                traverse(child.id, current_depth + 1)
        
        traverse(category_id)
        return descendants
    
    def get_category_siblings(self, category_id: str) -> List[TaxonomyNode]:
        """
        Get sibling categories (same parent)
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of sibling TaxonomyNodes
        """
        parent = self.get_category_parent(category_id)
        if not parent:
            # Root nodes' siblings are other root nodes
            siblings = self.get_root_categories()
            return [s for s in siblings if s.id != category_id]
        
        siblings = self.get_category_children(parent.id)
        return [s for s in siblings if s.id != category_id]
    
    def get_categories_by_level(self, level: int) -> List[TaxonomyNode]:
        """
        Get all categories at a specific level
        
        Args:
            level: Hierarchical level (0 = root)
            
        Returns:
            List of TaxonomyNodes at the specified level
        """
        return [node for node in self._nodes.values() if node.level == level]
    
    def is_ancestor_of(self, ancestor_id: str, descendant_id: str) -> bool:
        """
        Check if one category is an ancestor of another
        
        Args:
            ancestor_id: ID of potential ancestor
            descendant_id: ID of potential descendant
            
        Returns:
            True if ancestor_id is an ancestor of descendant_id
        """
        try:
            path = self.get_category_path(descendant_id)
            return any(node.id == ancestor_id for node in path[:-1])
        except NodeNotFoundError:
            return False
    
    def get_common_ancestor(self, category_id1: str, category_id2: str) -> Optional[TaxonomyNode]:
        """
        Find the lowest common ancestor of two categories
        
        Args:
            category_id1: ID of first category
            category_id2: ID of second category
            
        Returns:
            Common ancestor TaxonomyNode or None
        """
        try:
            path1 = self.get_category_path(category_id1)
            path2 = self.get_category_path(category_id2)
            
            # Find common prefix
            common_ancestor = None
            for node1, node2 in zip(path1, path2):
                if node1.id == node2.id:
                    common_ancestor = node1
                else:
                    break
            
            return common_ancestor
            
        except NodeNotFoundError:
            return None
    
    def validate_taxonomy_structure(self) -> ValidationResult:
        """
        Validate the integrity of the taxonomy structure
        
        Returns:
            ValidationResult with any issues found
        """
        issues = []
        warnings = []
        
        # Check for orphaned nodes in relationships
        for rel_id in self._relationships:
            if rel_id not in self._nodes:
                issues.append(f"Relationship references non-existent node: {rel_id}")
        
        # Check for circular references
        for node_id in self._nodes:
            try:
                path = self.get_category_path(node_id)
                if len(path) > len(set(node.id for node in path)):
                    issues.append(f"Circular reference detected for category {node_id}")
            except Exception as e:
                issues.append(f"Error validating category {node_id}: {e}")
        
        # Check parent-child consistency
        for node_id, rel in self._relationships.items():
            parent_id = rel.get('parent')
            if parent_id and parent_id in self._relationships:
                parent_children = self._relationships[parent_id].get('children', [])
                if node_id not in parent_children:
                    warnings.append(f"Inconsistent parent-child relationship: {node_id} not in parent {parent_id}'s children")
        
        # Check for disconnected subtrees
        roots = self.get_root_categories()
        if len(roots) > 1:
            warnings.append(f"Multiple root categories found: {[r.id for r in roots]}")
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            warnings=warnings
        )
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the taxonomy structure
        
        Returns:
            Dictionary with taxonomy statistics
        """
        total_categories = len(self._nodes)
        
        # Count by level
        categories_by_level = {}
        max_depth = 0
        
        for node in self._nodes.values():
            level = node.level
            categories_by_level[level] = categories_by_level.get(level, 0) + 1
            max_depth = max(max_depth, level)
        
        # Count children
        children_counts = []
        for node_id, rel in self._relationships.items():
            children_count = len(rel.get('children', []))
            children_counts.append(children_count)
        
        avg_children = sum(children_counts) / len(children_counts) if children_counts else 0
        
        return {
            "total_categories": total_categories,
            "max_depth": max_depth,
            "categories_by_level": categories_by_level,
            "avg_children_per_category": round(avg_children, 2),
            "root_categories": len(self.get_root_categories()),
            "leaf_categories": len([c for c in children_counts if c == 0])
        } 