"""
DiseaseInstances - Lazy-loaded disease instance management

This module provides efficient access to disease instances with on-demand loading.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache

from .models import DiseaseInstance, Classification
from .exceptions import NodeNotFoundError, FileNotFoundError, InvalidDataFormatError

logger = logging.getLogger(__name__)


class DiseaseInstances:
    """Manage disease instances with lazy loading for memory efficiency"""
    
    def __init__(self, instances_dir: str):
        """
        Initialize the disease instances manager
        
        Args:
            instances_dir: Directory containing instance JSON files
        """
        self.instances_dir = Path(instances_dir)
        
        if not self.instances_dir.exists():
            raise FileNotFoundError(f"Instances directory not found: {instances_dir}")
        
        # Lazy-loaded data
        self._diseases: Optional[Dict[str, DiseaseInstance]] = None
        self._classification_index: Dict[str, List[str]] = {}
        self._name_index: Dict[str, List[str]] = {}
        self._disease_metadata: Optional[Dict[str, Dict]] = None
        
        # Always load indices for fast lookups
        self._load_indices()
    
    def _load_indices(self) -> None:
        """Load classification and name indices (lightweight)"""
        try:
            # Load classification index
            class_index_path = self.instances_dir / "classification_index.json"
            if class_index_path.exists():
                with open(class_index_path, 'r', encoding='utf-8') as f:
                    self._classification_index = json.load(f)
                logger.info(f"Loaded classification index with {len(self._classification_index)} categories")
            
            # Load name index
            name_index_path = self.instances_dir / "name_index.json"
            if name_index_path.exists():
                with open(name_index_path, 'r', encoding='utf-8') as f:
                    self._name_index = json.load(f)
                logger.info(f"Loaded name index with {len(self._name_index)} entries")
                
        except json.JSONDecodeError as e:
            raise InvalidDataFormatError(f"Invalid JSON in index files: {e}")
        except Exception as e:
            logger.error(f"Failed to load indices: {e}")
            raise
    
    def _ensure_diseases_loaded(self) -> None:
        """Load diseases data if not already loaded"""
        if self._diseases is None:
            self._load_diseases()
    
    def _load_diseases(self) -> None:
        """Load all diseases from JSON file"""
        try:
            diseases_path = self.instances_dir / "diseases.json"
            if not diseases_path.exists():
                raise FileNotFoundError(f"Diseases file not found: {diseases_path}")
            
            with open(diseases_path, 'r', encoding='utf-8') as f:
                diseases_data = json.load(f)
            
            self._diseases = {}
            for disease_id, disease_data in diseases_data.items():
                self._diseases[disease_id] = DiseaseInstance(**disease_data)
            
            logger.info(f"Loaded {len(self._diseases)} diseases")
            
        except json.JSONDecodeError as e:
            raise InvalidDataFormatError(f"Invalid JSON in diseases file: {e}")
        except Exception as e:
            logger.error(f"Failed to load diseases: {e}")
            raise
    
    def get_disease(self, disease_id: str) -> Optional[DiseaseInstance]:
        """
        Get a specific disease instance
        
        Args:
            disease_id: ID of the disease
            
        Returns:
            DiseaseInstance or None if not found
        """
        self._ensure_diseases_loaded()
        return self._diseases.get(disease_id)
    
    def get_diseases_in_category(self, category_id: str) -> List[DiseaseInstance]:
        """
        Get all diseases in a specific category
        
        Args:
            category_id: ID of the category
            
        Returns:
            List of DiseaseInstances in the category
        """
        disease_ids = self._classification_index.get(category_id, [])
        
        if not disease_ids:
            return []
        
        self._ensure_diseases_loaded()
        diseases = []
        for disease_id in disease_ids:
            disease = self._diseases.get(disease_id)
            if disease:
                diseases.append(disease)
        
        return diseases
    
    def load_diseases_batch(self, disease_ids: List[str]) -> Dict[str, DiseaseInstance]:
        """
        Load multiple diseases efficiently
        
        Args:
            disease_ids: List of disease IDs to load
            
        Returns:
            Dictionary mapping disease IDs to DiseaseInstances
        """
        self._ensure_diseases_loaded()
        
        result = {}
        for disease_id in disease_ids:
            disease = self._diseases.get(disease_id)
            if disease:
                result[disease_id] = disease
        
        return result
    
    def search_diseases_by_name(self, name: str, exact: bool = True) -> List[DiseaseInstance]:
        """
        Search for diseases by name
        
        Args:
            name: Name to search for
            exact: If True, exact match; if False, partial match
            
        Returns:
            List of matching DiseaseInstances
        """
        if exact:
            # Use name index for exact matches
            disease_ids = self._name_index.get(name, [])
            if not disease_ids:
                return []
            
            self._ensure_diseases_loaded()
            diseases = []
            for disease_id in disease_ids:
                disease = self._diseases.get(disease_id)
                if disease:
                    diseases.append(disease)
            return diseases
        else:
            # Partial match requires loading all diseases
            self._ensure_diseases_loaded()
            name_lower = name.lower()
            return [
                disease for disease in self._diseases.values()
                if name_lower in disease.name.lower()
            ]
    
    def get_disease_ids_by_name(self, name: str) -> List[str]:
        """
        Get disease IDs for a given name (fast, no loading)
        
        Args:
            name: Disease name
            
        Returns:
            List of disease IDs
        """
        return self._name_index.get(name, [])
    
    def get_disease_ids_in_category(self, category_id: str) -> List[str]:
        """
        Get disease IDs in a category (fast, no loading)
        
        Args:
            category_id: Category ID
            
        Returns:
            List of disease IDs
        """
        return self._classification_index.get(category_id, [])
    
    def get_all_disease_ids(self) -> Set[str]:
        """
        Get all disease IDs (fast, no loading)
        
        Returns:
            Set of all disease IDs
        """
        disease_ids = set()
        for ids in self._classification_index.values():
            disease_ids.update(ids)
        return disease_ids
    
    def get_diseases_by_level(self, level: int) -> List[DiseaseInstance]:
        """
        Get all diseases at a specific hierarchical level
        
        Args:
            level: Hierarchical level
            
        Returns:
            List of DiseaseInstances at the specified level
        """
        self._ensure_diseases_loaded()
        return [
            disease for disease in self._diseases.values()
            if disease.classification.level == level
        ]
    
    def count_diseases(self) -> int:
        """
        Get total number of diseases (fast, no loading)
        
        Returns:
            Total disease count
        """
        return len(self.get_all_disease_ids())
    
    def count_diseases_in_category(self, category_id: str) -> int:
        """
        Count diseases in a category (fast, no loading)
        
        Args:
            category_id: Category ID
            
        Returns:
            Number of diseases in the category
        """
        return len(self._classification_index.get(category_id, []))
    
    def get_disease_metadata(self, disease_id: str) -> Optional[Dict]:
        """
        Get extended metadata for a disease
        
        Args:
            disease_id: Disease ID
            
        Returns:
            Metadata dictionary or None
        """
        if self._disease_metadata is None:
            self._load_disease_metadata()
        
        return self._disease_metadata.get(disease_id)
    
    def _load_disease_metadata(self) -> None:
        """Load disease metadata file"""
        try:
            metadata_path = self.instances_dir / "disease_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self._disease_metadata = json.load(f)
            else:
                self._disease_metadata = {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in disease metadata: {e}")
            self._disease_metadata = {}
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about disease instances
        
        Returns:
            Dictionary with disease statistics
        """
        total_diseases = self.count_diseases()
        
        # Count diseases by category
        diseases_per_category = {}
        for cat_id, disease_ids in self._classification_index.items():
            diseases_per_category[cat_id] = len(disease_ids)
        
        # Calculate averages
        category_counts = list(diseases_per_category.values())
        avg_per_category = sum(category_counts) / len(category_counts) if category_counts else 0
        
        # Count ambiguous names
        ambiguous_names = sum(1 for ids in self._name_index.values() if len(ids) > 1)
        
        return {
            "total_diseases": total_diseases,
            "total_categories_with_diseases": len(self._classification_index),
            "avg_diseases_per_category": round(avg_per_category, 2),
            "max_diseases_in_category": max(category_counts) if category_counts else 0,
            "min_diseases_in_category": min(category_counts) if category_counts else 0,
            "total_unique_names": len(self._name_index),
            "ambiguous_names": ambiguous_names
        }
    
    def clear_cache(self) -> None:
        """Clear loaded disease data to free memory"""
        self._diseases = None
        self._disease_metadata = None
        logger.info("Disease cache cleared")
    
    def preload_all(self) -> None:
        """Preload all disease data for performance"""
        self._ensure_diseases_loaded()
        self._load_disease_metadata()
        logger.info("All disease data preloaded")
    
    @lru_cache(maxsize=1000)
    def _get_disease_cached(self, disease_id: str) -> Optional[DiseaseInstance]:
        """
        Cached version of get_disease for frequently accessed diseases
        
        Args:
            disease_id: Disease ID
            
        Returns:
            DiseaseInstance or None
        """
        return self.get_disease(disease_id) 