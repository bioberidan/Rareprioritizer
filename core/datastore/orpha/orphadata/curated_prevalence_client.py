#!/usr/bin/env python3
"""
Curated Orpha Prevalence Client

This client provides access to curated orpha prevalence data with lazy loading
and caching capabilities for efficient data access.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime


class CuratedOrphaPrevalenceClient:
    """
    Client for accessing curated orpha prevalence data with lazy loading and caching.
    
    This client provides efficient access to curated prevalence data including:
    - Disease to prevalence class mappings
    - Processing metadata and statistics
    - Disease name mappings
    - Cached results for performance
    """
    
    def __init__(self, data_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the curated prevalence client.
        
        Args:
            data_dir: Directory containing curated prevalence data files
        """
        self.data_dir = Path(data_dir)
        
        # Lazy-loaded data structures
        self._disease2prevalence: Optional[Dict[str, str]] = None
        self._prevalence_class_distribution: Optional[Dict[str, int]] = None
        self._processing_summary: Optional[Dict] = None
        self._orphacode2disease_name: Optional[Dict[str, str]] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate data directory
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")

    def _ensure_disease2prevalence_loaded(self) -> None:
        """Load disease to prevalence mapping if not already loaded"""
        if self._disease2prevalence is None:
            file_path = self.data_dir / "disease2prevalence.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2prevalence = json.load(f)
                self.logger.info(f"Loaded {len(self._disease2prevalence)} disease-prevalence mappings")
            else:
                self.logger.warning(f"Disease prevalence file not found: {file_path}")
                self._disease2prevalence = {}

    def _ensure_processing_summary_loaded(self) -> None:
        """Load processing summary if not already loaded"""
        if self._processing_summary is None:
            file_path = self.data_dir / "orpha_prevalence_curation_summary.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._processing_summary = json.load(f)
                self.logger.info("Loaded processing summary")
            else:
                self.logger.warning(f"Processing summary file not found: {file_path}")
                self._processing_summary = {}

    def _ensure_orphacode2disease_name_loaded(self) -> None:
        """Load orphacode to disease name mapping if not already loaded"""
        if self._orphacode2disease_name is None:
            file_path = self.data_dir.parent / "ordo" / "orphacode2disease_name.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._orphacode2disease_name = json.load(f)
                self.logger.info(f"Loaded {len(self._orphacode2disease_name)} disease name mappings")
            else:
                self.logger.warning(f"Disease name mapping file not found: {file_path}")
                self._orphacode2disease_name = {}

    def _calculate_prevalence_class_distribution(self) -> Dict[str, int]:
        """Calculate prevalence class distribution from loaded data"""
        if self._prevalence_class_distribution is None:
            self._ensure_disease2prevalence_loaded()
            
            distribution = {}
            for prevalence_class in self._disease2prevalence.values():
                if prevalence_class != "Unknown":
                    distribution[prevalence_class] = distribution.get(prevalence_class, 0) + 1
            
            self._prevalence_class_distribution = distribution
            
        return self._prevalence_class_distribution

    def get_prevalence_class(self, orpha_code: str) -> Optional[str]:
        """
        Get prevalence class for a specific disease.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Prevalence class string or None if not found
        """
        self._ensure_disease2prevalence_loaded()
        return self._disease2prevalence.get(orpha_code)

    def get_disease_name(self, orpha_code: str) -> Optional[str]:
        """
        Get disease name for a specific orpha code.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Disease name string or None if not found
        """
        self._ensure_orphacode2disease_name_loaded()
        return self._orphacode2disease_name.get(orpha_code)

    def get_diseases_by_prevalence_class(self, prevalence_class: str) -> List[str]:
        """
        Get all diseases with a specific prevalence class.
        
        Args:
            prevalence_class: Prevalence class to filter by
            
        Returns:
            List of orpha codes with the specified prevalence class
        """
        cache_key = f"diseases_by_class_{prevalence_class}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        self._ensure_disease2prevalence_loaded()
        
        diseases = [
            orpha_code for orpha_code, pclass in self._disease2prevalence.items()
            if pclass == prevalence_class
        ]
        
        self._cache[cache_key] = diseases
        return diseases

    def get_all_prevalence_classes(self) -> Set[str]:
        """
        Get all unique prevalence classes in the dataset.
        
        Returns:
            Set of all prevalence classes (excluding "Unknown")
        """
        if 'all_prevalence_classes' in self._cache:
            return self._cache['all_prevalence_classes']
        
        self._ensure_disease2prevalence_loaded()
        
        classes = set(self._disease2prevalence.values())
        classes.discard("Unknown")  # Remove Unknown class
        
        self._cache['all_prevalence_classes'] = classes
        return classes

    def get_prevalence_class_distribution(self) -> Dict[str, int]:
        """
        Get distribution of prevalence classes.
        
        Returns:
            Dictionary mapping prevalence class to count
        """
        return self._calculate_prevalence_class_distribution()

    def get_coverage_statistics(self) -> Dict[str, Any]:
        """
        Get data coverage statistics.
        
        Returns:
            Dictionary with coverage statistics
        """
        if 'coverage_stats' in self._cache:
            return self._cache['coverage_stats']
        
        self._ensure_disease2prevalence_loaded()
        
        total_diseases = len(self._disease2prevalence)
        diseases_with_prevalence = len([v for v in self._disease2prevalence.values() if v != "Unknown"])
        diseases_without_prevalence = total_diseases - diseases_with_prevalence
        
        coverage_stats = {
            'total_diseases': total_diseases,
            'diseases_with_prevalence': diseases_with_prevalence,
            'diseases_without_prevalence': diseases_without_prevalence,
            'coverage_percentage': (diseases_with_prevalence / total_diseases) * 100 if total_diseases > 0 else 0
        }
        
        self._cache['coverage_stats'] = coverage_stats
        return coverage_stats

    def get_processing_metadata(self) -> Dict[str, Any]:
        """
        Get processing metadata and statistics.
        
        Returns:
            Dictionary with processing metadata
        """
        self._ensure_processing_summary_loaded()
        return self._processing_summary.get('processing_metadata', {})

    def get_selection_method_statistics(self) -> Dict[str, int]:
        """
        Get statistics about selection methods used.
        
        Returns:
            Dictionary with selection method counts
        """
        self._ensure_processing_summary_loaded()
        return self._processing_summary.get('selection_method_distribution', {})

    def search_diseases_by_name(self, name_pattern: str, case_sensitive: bool = False) -> List[Dict[str, str]]:
        """
        Search diseases by name pattern.
        
        Args:
            name_pattern: Pattern to search for in disease names
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of dictionaries with orpha_code and disease_name
        """
        self._ensure_orphacode2disease_name_loaded()
        self._ensure_disease2prevalence_loaded()
        
        if not case_sensitive:
            name_pattern = name_pattern.lower()
        
        matching_diseases = []
        for orpha_code, disease_name in self._orphacode2disease_name.items():
            search_name = disease_name if case_sensitive else disease_name.lower()
            
            if name_pattern in search_name:
                prevalence_class = self.get_prevalence_class(orpha_code)
                matching_diseases.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_name,
                    'prevalence_class': prevalence_class
                })
        
        return matching_diseases

    def get_disease_info(self, orpha_code: str) -> Dict[str, Optional[str]]:
        """
        Get comprehensive information about a disease.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Dictionary with disease information
        """
        return {
            'orpha_code': orpha_code,
            'disease_name': self.get_disease_name(orpha_code),
            'prevalence_class': self.get_prevalence_class(orpha_code)
        }

    def get_diseases_with_unknown_prevalence(self) -> List[Dict[str, str]]:
        """
        Get all diseases with unknown prevalence class.
        
        Returns:
            List of dictionaries with orpha_code and disease_name
        """
        if 'unknown_prevalence_diseases' in self._cache:
            return self._cache['unknown_prevalence_diseases']
        
        unknown_diseases = []
        for orpha_code in self.get_diseases_by_prevalence_class("Unknown"):
            disease_name = self.get_disease_name(orpha_code)
            unknown_diseases.append({
                'orpha_code': orpha_code,
                'disease_name': disease_name
            })
        
        self._cache['unknown_prevalence_diseases'] = unknown_diseases
        return unknown_diseases

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'coverage_statistics': self.get_coverage_statistics(),
            'prevalence_class_distribution': self.get_prevalence_class_distribution(),
            'selection_method_statistics': self.get_selection_method_statistics(),
            'total_prevalence_classes': len(self.get_all_prevalence_classes()),
            'most_common_prevalence_class': self._get_most_common_prevalence_class(),
            'processing_metadata': self.get_processing_metadata()
        }

    def _get_most_common_prevalence_class(self) -> Optional[str]:
        """Get the most common prevalence class"""
        distribution = self.get_prevalence_class_distribution()
        if not distribution:
            return None
        
        return max(distribution.items(), key=lambda x: x[1])[0]

    def export_to_csv(self, output_file: str, include_disease_names: bool = True) -> None:
        """
        Export data to CSV file.
        
        Args:
            output_file: Path to output CSV file
            include_disease_names: Whether to include disease names in export
        """
        import csv
        
        self._ensure_disease2prevalence_loaded()
        if include_disease_names:
            self._ensure_orphacode2disease_name_loaded()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if include_disease_names:
                fieldnames = ['orpha_code', 'disease_name', 'prevalence_class']
            else:
                fieldnames = ['orpha_code', 'prevalence_class']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for orpha_code, prevalence_class in self._disease2prevalence.items():
                row = {
                    'orpha_code': orpha_code,
                    'prevalence_class': prevalence_class
                }
                
                if include_disease_names:
                    row['disease_name'] = self.get_disease_name(orpha_code) or "Unknown"
                
                writer.writerow(row)
        
        self.logger.info(f"Exported data to {output_file}")

    def validate_data_consistency(self) -> Dict[str, Any]:
        """
        Validate data consistency across files.
        
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Load all data
            self._ensure_disease2prevalence_loaded()
            self._ensure_orphacode2disease_name_loaded()
            self._ensure_processing_summary_loaded()
            
            # Check for orphacodes in prevalence data but not in disease names
            prevalence_codes = set(self._disease2prevalence.keys())
            name_codes = set(self._orphacode2disease_name.keys())
            
            missing_names = prevalence_codes - name_codes
            if missing_names:
                validation_results['warnings'].append(
                    f"{len(missing_names)} orphacodes in prevalence data but not in disease names"
                )
            
            # Check for empty or invalid prevalence classes
            invalid_classes = [code for code, pclass in self._disease2prevalence.items() 
                             if not pclass or pclass.strip() == ""]
            if invalid_classes:
                validation_results['errors'].append(
                    f"{len(invalid_classes)} orphacodes have empty prevalence classes"
                )
                validation_results['is_valid'] = False
            
            # Check processing summary consistency
            summary_stats = self._processing_summary.get('dataset_statistics', {})
            actual_total = len(self._disease2prevalence)
            summary_total = summary_stats.get('total_diseases_in_subset', 0)
            
            if actual_total != summary_total:
                validation_results['warnings'].append(
                    f"Total diseases mismatch: actual={actual_total}, summary={summary_total}"
                )
            
        except Exception as e:
            validation_results['errors'].append(f"Validation error: {str(e)}")
            validation_results['is_valid'] = False
        
        return validation_results

    def clear_cache(self) -> None:
        """Clear all cached data to free memory"""
        self._cache.clear()
        self.logger.info("Cache cleared")

    def reload_data(self) -> None:
        """Reload all data from files"""
        self._disease2prevalence = None
        self._prevalence_class_distribution = None
        self._processing_summary = None
        self._orphacode2disease_name = None
        self.clear_cache()
        self.logger.info("Data reloaded from files")

    def get_data_info(self) -> Dict[str, Any]:
        """
        Get information about loaded data files.
        
        Returns:
            Dictionary with data file information
        """
        data_info = {
            'data_directory': str(self.data_dir),
            'files_status': {},
            'last_check': datetime.now().isoformat()
        }
        
        # Check each expected file
        files_to_check = [
            ('disease2prevalence.json', 'disease2prevalence'),
            ('orpha_prevalence_curation_summary.json', 'processing_summary'),
            ('../ordo/orphacode2disease_name.json', 'orphacode2disease_name')
        ]
        
        for filename, data_type in files_to_check:
            file_path = self.data_dir / filename
            data_info['files_status'][data_type] = {
                'exists': file_path.exists(),
                'path': str(file_path),
                'loaded': getattr(self, f'_{data_type}') is not None
            }
            
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    data_info['files_status'][data_type].update({
                        'size_bytes': stat.st_size,
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    data_info['files_status'][data_type]['error'] = str(e)
        
        return data_info 