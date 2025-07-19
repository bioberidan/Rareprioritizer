"""
Curated Prevalence Client - Data access layer for curated metabolic disease prevalence

This module provides a client interface for accessing curated metabolic disease 
prevalence data and Spanish patient estimates. It combines disease instances 
from ORDO data with processed prevalence data to deliver structured access 
to metabolic disease information.

Spanish population: 47 million inhabitants
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from functools import lru_cache

from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient

logger = logging.getLogger(__name__)


class CuratedPrevalenceClient:
    """Client for accessing curated metabolic disease data and prevalence"""
    
    def __init__(self, 
                 ordo_data_dir: str = "data/04_curated/orpha/ordo",
                 orphadata_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the curated prevalence client
        
        Args:
            ordo_data_dir: Directory containing curated ORDO data
            orphadata_dir: Directory containing curated orphadata (prevalence files)
        """
        self.ordo_data_dir = Path(ordo_data_dir)
        self.orphadata_dir = Path(orphadata_dir)
        
        # Validate directories exist
        if not self.ordo_data_dir.exists():
            raise FileNotFoundError(f"ORDO data directory not found: {ordo_data_dir}")
        if not self.orphadata_dir.exists():
            raise FileNotFoundError(f"Orphadata directory not found: {orphadata_dir}")
        
        # Initialize ProcessedPrevalenceClient for disease name lookups
        self.processed_prevalence_client = ProcessedPrevalenceClient()
        
        # Lazy-loaded data structures
        self._metabolic_diseases: Optional[List[Dict]] = None
        self._prevalence_data: Optional[Dict[int, float]] = None
        self._spanish_patients_data: Optional[Dict[int, int]] = None
        self._orpha_codes_set: Optional[Set[int]] = None
        self._disease_name_cache: Dict[int, str] = {}
        
        logger.info(f"Curated prevalence client initialized")
        logger.info(f"ORDO data dir: {self.ordo_data_dir}")
        logger.info(f"Orphadata dir: {self.orphadata_dir}")
    
    # ========== Data Loading Methods ==========
    
    def _ensure_metabolic_diseases_loaded(self) -> None:
        """Load metabolic disease instances if not already loaded"""
        if self._metabolic_diseases is None:
            metabolic_file = self.ordo_data_dir / "metabolic_disease_instances.json"
            
            if not metabolic_file.exists():
                raise FileNotFoundError(f"Metabolic diseases file not found: {metabolic_file}")
            
            with open(metabolic_file, 'r', encoding='utf-8') as f:
                self._metabolic_diseases = json.load(f)
            
            logger.info(f"Loaded {len(self._metabolic_diseases)} metabolic diseases")
    
    def _ensure_prevalence_data_loaded(self) -> None:
        """Load prevalence per million data if not already loaded"""
        if self._prevalence_data is None:
            prevalence_file = self.orphadata_dir / "metabolic_diseases2prevalence_per_million.json"
            
            if not prevalence_file.exists():
                raise FileNotFoundError(f"Prevalence data file not found: {prevalence_file}")
            
            with open(prevalence_file, 'r', encoding='utf-8') as f:
                # Convert string keys to integers
                data = json.load(f)
                self._prevalence_data = {int(k): v for k, v in data.items()}
            
            logger.info(f"Loaded prevalence data for {len(self._prevalence_data)} diseases")
    
    def _ensure_spanish_patients_data_loaded(self) -> None:
        """Load Spanish patients data if not already loaded"""
        if self._spanish_patients_data is None:
            spanish_file = self.orphadata_dir / "metabolic_diseases2spanish_patient_number.json"
            
            if not spanish_file.exists():
                raise FileNotFoundError(f"Spanish patients data file not found: {spanish_file}")
            
            with open(spanish_file, 'r', encoding='utf-8') as f:
                # Convert string keys to integers
                data = json.load(f)
                self._spanish_patients_data = {int(k): v for k, v in data.items()}
            
            logger.info(f"Loaded Spanish patients data for {len(self._spanish_patients_data)} diseases")
    
    def _ensure_orpha_codes_loaded(self) -> None:
        """Ensure orpha codes set is loaded for fast membership testing"""
        if self._orpha_codes_set is None:
            self._ensure_metabolic_diseases_loaded()
            self._orpha_codes_set = {int(disease['orpha_code']) for disease in self._metabolic_diseases}
    
    # ========== Disease Data Access Methods ==========
    
    def load_metabolic_diseases(self) -> List[Dict]:
        """
        Load metabolic disease instances from JSON
        
        Returns:
            List of disease dictionaries with disease_name and orpha_code
        """
        self._ensure_metabolic_diseases_loaded()
        return self._metabolic_diseases.copy()
    
    def get_metabolic_orpha_codes(self) -> List[int]:
        """
        Get list of integer orpha codes for all metabolic diseases
        
        Returns:
            List of orpha codes as integers
        """
        self._ensure_metabolic_diseases_loaded()
        return [int(disease['orpha_code']) for disease in self._metabolic_diseases]
    
    def get_disease_name_by_orpha_code(self, orpha_code: Union[int, str]) -> Optional[str]:
        """
        Get disease name for a specific orpha code (with lazy loading from other sources)
        
        Args:
            orpha_code: Orpha code as integer or string
            
        Returns:
            Disease name or None if not found
        """
        orpha_code_int = int(orpha_code)
        
        # Check cache first
        if orpha_code_int in self._disease_name_cache:
            return self._disease_name_cache[orpha_code_int]
        
        # Check in metabolic diseases first
        self._ensure_metabolic_diseases_loaded()
        for disease in self._metabolic_diseases:
            if int(disease['orpha_code']) == orpha_code_int:
                name = disease['disease_name']
                self._disease_name_cache[orpha_code_int] = name
                return name
        
        # Lazy loading from ProcessedPrevalenceClient if not found in metabolic diseases
        try:
            prevalence_summary = self.processed_prevalence_client.get_disease_prevalence_summary(str(orpha_code))
            if prevalence_summary and 'disease_name' in prevalence_summary:
                name = prevalence_summary['disease_name']
                self._disease_name_cache[orpha_code_int] = name
                return name
        except Exception as e:
            logger.debug(f"Could not get disease name from processed prevalence for {orpha_code}: {e}")
        
        return None
    
    def is_metabolic_disease(self, orpha_code: Union[int, str]) -> bool:
        """
        Check if an orpha code corresponds to a metabolic disease
        
        Args:
            orpha_code: Orpha code as integer or string
            
        Returns:
            True if it's a metabolic disease, False otherwise
        """
        self._ensure_orpha_codes_loaded()
        return int(orpha_code) in self._orpha_codes_set
    
    # ========== Prevalence Data Access Methods ==========
    
    def load_prevalence_data(self) -> Dict[int, float]:
        """
        Load prevalence per million mapping
        
        Returns:
            Dictionary mapping orpha codes to prevalence per million
        """
        self._ensure_prevalence_data_loaded()
        return self._prevalence_data.copy()
    
    def get_disease_prevalence_per_million(self, orpha_code: Union[int, str]) -> Optional[float]:
        """
        Get prevalence per million for a specific disease
        
        Args:
            orpha_code: Orpha code as integer or string
            
        Returns:
            Prevalence per million or None if not available
        """
        self._ensure_prevalence_data_loaded()
        return self._prevalence_data.get(int(orpha_code))
    
    def get_spanish_patients_number(self, orpha_code: Union[int, str]) -> Optional[int]:
        """
        Get Spanish patient count for a specific disease
        
        Args:
            orpha_code: Orpha code as integer or string
            
        Returns:
            Number of Spanish patients or None if not available
        """
        self._ensure_spanish_patients_data_loaded()
        return self._spanish_patients_data.get(int(orpha_code))
    
    # ========== Bulk Operations ==========
    
    def get_all_metabolic_prevalences(self) -> Dict[int, float]:
        """
        Get dictionary of all metabolic disease prevalences
        
        Returns:
            Dictionary mapping orpha codes to prevalence per million
        """
        return self.load_prevalence_data()
    
    def get_all_spanish_patients(self) -> Dict[int, int]:
        """
        Get dictionary of all Spanish patient counts
        
        Returns:
            Dictionary mapping orpha codes to Spanish patient counts
        """
        self._ensure_spanish_patients_data_loaded()
        return self._spanish_patients_data.copy()
    
    def get_diseases_with_prevalence(self) -> List[Dict]:
        """
        Get only diseases that have prevalence data
        
        Returns:
            List of disease dictionaries that have prevalence data
        """
        self._ensure_metabolic_diseases_loaded()
        self._ensure_prevalence_data_loaded()
        
        diseases_with_prevalence = []
        for disease in self._metabolic_diseases:
            orpha_code = int(disease['orpha_code'])
            if orpha_code in self._prevalence_data:
                disease_info = disease.copy()
                disease_info['prevalence_per_million'] = self._prevalence_data[orpha_code]
                disease_info['spanish_patients'] = self.get_spanish_patients_number(orpha_code)
                diseases_with_prevalence.append(disease_info)
        
        return diseases_with_prevalence
    
    def get_diseases_without_prevalence(self) -> List[Dict]:
        """
        Get diseases that are missing prevalence data
        
        Returns:
            List of disease dictionaries without prevalence data
        """
        self._ensure_metabolic_diseases_loaded()
        self._ensure_prevalence_data_loaded()
        
        diseases_without_prevalence = []
        for disease in self._metabolic_diseases:
            orpha_code = int(disease['orpha_code'])
            if orpha_code not in self._prevalence_data:
                diseases_without_prevalence.append(disease.copy())
        
        return diseases_without_prevalence
    
    # ========== Analysis Methods ==========
    
    def get_top_diseases_by_spanish_patients(self, limit: int = 10) -> List[Dict]:
        """
        Get top diseases by Spanish patient count
        
        Args:
            limit: Maximum number of diseases to return
            
        Returns:
            List of disease dictionaries sorted by Spanish patient count (descending)
        """
        diseases_with_prevalence = self.get_diseases_with_prevalence()
        
        # Sort by Spanish patients (descending)
        sorted_diseases = sorted(
            diseases_with_prevalence,
            key=lambda x: x.get('spanish_patients', 0),
            reverse=True
        )
        
        return sorted_diseases[:limit]
    
    def get_diseases_by_prevalence_range(self, 
                                       min_prevalence: float = 0.0, 
                                       max_prevalence: float = float('inf')) -> List[Dict]:
        """
        Get diseases within a specific prevalence range
        
        Args:
            min_prevalence: Minimum prevalence per million (inclusive)
            max_prevalence: Maximum prevalence per million (inclusive)
            
        Returns:
            List of diseases within the prevalence range
        """
        diseases_with_prevalence = self.get_diseases_with_prevalence()
        
        filtered_diseases = [
            disease for disease in diseases_with_prevalence
            if min_prevalence <= disease['prevalence_per_million'] <= max_prevalence
        ]
        
        return filtered_diseases
    
    def get_ultra_rare_diseases(self) -> List[Dict]:
        """
        Get ultra-rare diseases (prevalence < 1 per million)
        
        Returns:
            List of ultra-rare disease dictionaries
        """
        return self.get_diseases_by_prevalence_range(max_prevalence=1.0)
    
    def get_common_rare_diseases(self) -> List[Dict]:
        """
        Get more common rare diseases (prevalence >= 50 per million)
        
        Returns:
            List of common rare disease dictionaries
        """
        return self.get_diseases_by_prevalence_range(min_prevalence=50.0)
    
    # ========== Statistics Methods ==========
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about metabolic diseases and prevalence
        
        Returns:
            Dictionary with coverage, prevalence, and patient statistics
        """
        self._ensure_metabolic_diseases_loaded()
        self._ensure_prevalence_data_loaded()
        self._ensure_spanish_patients_data_loaded()
        
        total_diseases = len(self._metabolic_diseases)
        diseases_with_prevalence = len(self._prevalence_data)
        diseases_without_prevalence = total_diseases - diseases_with_prevalence
        
        # Prevalence statistics
        prevalences = list(self._prevalence_data.values())
        spanish_patients = list(self._spanish_patients_data.values())
        
        # Calculate statistics
        if prevalences:
            prevalence_stats = {
                'mean': sum(prevalences) / len(prevalences),
                'min': min(prevalences),
                'max': max(prevalences),
                'median': sorted(prevalences)[len(prevalences) // 2],
                'zero_prevalence_count': sum(1 for p in prevalences if p == 0.0)
            }
        else:
            prevalence_stats = {'mean': 0, 'min': 0, 'max': 0, 'median': 0, 'zero_prevalence_count': 0}
        
        if spanish_patients:
            spanish_stats = {
                'total_patients': sum(spanish_patients),
                'mean_per_disease': sum(spanish_patients) / len(spanish_patients),
                'min': min(spanish_patients),
                'max': max(spanish_patients),
                'median': sorted(spanish_patients)[len(spanish_patients) // 2]
            }
        else:
            spanish_stats = {'total_patients': 0, 'mean_per_disease': 0, 'min': 0, 'max': 0, 'median': 0}
        
        return {
            'coverage': {
                'total_metabolic_diseases': total_diseases,
                'diseases_with_prevalence': diseases_with_prevalence,
                'diseases_without_prevalence': diseases_without_prevalence,
                'coverage_percentage': round(diseases_with_prevalence / total_diseases * 100, 2) if total_diseases > 0 else 0
            },
            'prevalence_statistics': prevalence_stats,
            'spanish_patients_statistics': spanish_stats,
            'ultra_rare_count': len(self.get_ultra_rare_diseases()),
            'common_rare_count': len(self.get_common_rare_diseases())
        }
    
    def get_data_summary(self) -> Dict:
        """
        Get summary of available data sources
        
        Returns:
            Dictionary summarizing data availability
        """
        stats = self.get_statistics()
        
        return {
            'data_sources': {
                'metabolic_diseases_file': str(self.ordo_data_dir / "metabolic_disease_instances.json"),
                'prevalence_file': str(self.orphadata_dir / "metabolic_diseases2prevalence_per_million.json"),
                'spanish_patients_file': str(self.orphadata_dir / "metabolic_diseases2spanish_patient_number.json")
            },
            'coverage_summary': stats['coverage'],
            'top_diseases_by_patients': [
                {
                    'disease_name': disease['disease_name'],
                    'orpha_code': disease['orpha_code'],
                    'spanish_patients': disease['spanish_patients']
                }
                for disease in self.get_top_diseases_by_spanish_patients(5)
            ]
        }
    
    # ========== Utility Methods ==========
    
    def clear_cache(self) -> None:
        """Clear all cached data to free memory"""
        self._metabolic_diseases = None
        self._prevalence_data = None
        self._spanish_patients_data = None
        self._orpha_codes_set = None
        self._disease_name_cache.clear()
        
        # Also clear ProcessedPrevalenceClient cache
        self.processed_prevalence_client.clear_cache()
        
        logger.info("Curated prevalence client cache cleared")
    
    def is_data_available(self) -> bool:
        """
        Check if all required data files are available
        
        Returns:
            True if all data files exist, False otherwise
        """
        required_files = [
            self.ordo_data_dir / "metabolic_disease_instances.json",
            self.orphadata_dir / "metabolic_diseases2prevalence_per_million.json",
            self.orphadata_dir / "metabolic_diseases2spanish_patient_number.json"
        ]
        
        return all(file.exists() for file in required_files)
    
    def get_file_info(self) -> Dict:
        """
        Get information about data files
        
        Returns:
            Dictionary with file paths and existence status
        """
        files_info = {}
        
        required_files = {
            'metabolic_diseases': self.ordo_data_dir / "metabolic_disease_instances.json",
            'prevalence_per_million': self.orphadata_dir / "metabolic_diseases2prevalence_per_million.json",
            'spanish_patients': self.orphadata_dir / "metabolic_diseases2spanish_patient_number.json"
        }
        
        for name, path in required_files.items():
            files_info[name] = {
                'path': str(path),
                'exists': path.exists(),
                'size_mb': round(path.stat().st_size / (1024 * 1024), 2) if path.exists() else 0
            }
        
        return files_info 