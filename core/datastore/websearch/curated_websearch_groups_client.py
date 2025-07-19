"""
Curated Websearch Groups Client - Query interface for curated websearch groups data

This module provides a high-performance interface for querying curated websearch groups data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from functools import lru_cache
import csv

logger = logging.getLogger(__name__)


class CuratedWebsearchGroupsClient:
    """
    Client for accessing curated websearch groups data with lazy loading and caching
    
    This client provides access to the curated websearch groups data files:
    - disease2group.json: Groups per disease mapping
    - group2source.json: Sources per group mapping
    - group2disease.json: Diseases per group mapping (reverse mapping)
    - websearch_groups_curation_summary.json: Summary and metadata
    """
    
    def __init__(self, data_dir: str = "data/04_curated/websearch/groups"):
        """
        Initialize the curated websearch groups client
        
        Args:
            data_dir: Directory containing curated websearch groups data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Curated websearch groups data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._disease2group: Optional[Dict[str, List[str]]] = None
        self._group2source: Optional[Dict[str, List[Dict[str, str]]]] = None
        self._group2disease: Optional[Dict[str, List[str]]] = None
        self._curation_summary: Optional[Dict[str, Any]] = None
        
        logger.info(f"Initialized CuratedWebsearchGroupsClient with data dir: {data_dir}")
    
    def _load_disease_group_data(self) -> Dict[str, List[str]]:
        """Load disease to group data with lazy loading"""
        if self._disease2group is None:
            file_path = self.data_dir / "disease2group.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2group = json.load(f)
                logger.info(f"Loaded disease to group data: {len(self._disease2group)} diseases")
            else:
                self._disease2group = {}
                logger.warning("disease2group.json not found")
        return self._disease2group
    
    def _load_group_source_data(self) -> Dict[str, List[Dict[str, str]]]:
        """Load group to source data with lazy loading"""
        if self._group2source is None:
            file_path = self.data_dir / "group2source.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._group2source = json.load(f)
                logger.info(f"Loaded group to source data: {len(self._group2source)} groups")
            else:
                self._group2source = {}
                logger.warning("group2source.json not found")
        return self._group2source
    
    def _load_group_disease_data(self) -> Dict[str, List[str]]:
        """Load group to disease data with lazy loading"""
        if self._group2disease is None:
            file_path = self.data_dir / "group2disease.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._group2disease = json.load(f)
                logger.info(f"Loaded group to disease data: {len(self._group2disease)} groups")
            else:
                self._group2disease = {}
                logger.warning("group2disease.json not found")
        return self._group2disease
    
    def _load_curation_summary(self) -> Dict[str, Any]:
        """Load curation summary with lazy loading"""
        if self._curation_summary is None:
            file_path = self.data_dir / "websearch_groups_curation_summary.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._curation_summary = json.load(f)
                logger.info("Loaded curation summary")
            else:
                self._curation_summary = {}
                logger.warning("websearch_groups_curation_summary.json not found")
        return self._curation_summary
    
    def get_groups_for_disease(self, orpha_code: str) -> List[str]:
        """
        Get research groups associated with a disease
        
        Args:
            orpha_code: Orpha code as string
            
        Returns:
            List of group names, empty list if none found
        """
        disease_data = self._load_disease_group_data()
        return disease_data.get(orpha_code, [])
    
    def get_diseases_for_group(self, group_name: str) -> List[str]:
        """
        Get diseases associated with a research group
        
        Args:
            group_name: Name of the research group
            
        Returns:
            List of orpha codes, empty list if none found
        """
        group_data = self._load_group_disease_data()
        return group_data.get(group_name, [])
    
    def get_sources_for_group(self, group_name: str) -> List[Dict[str, str]]:
        """
        Get sources/publications for a research group
        
        Args:
            group_name: Name of the research group
            
        Returns:
            List of source dictionaries with 'label' and 'url' keys
        """
        source_data = self._load_group_source_data()
        return source_data.get(group_name, [])
    
    def has_research_groups(self, orpha_code: str) -> bool:
        """
        Check if a disease has associated research groups
        
        Args:
            orpha_code: Orpha code as string
            
        Returns:
            True if disease has groups, False otherwise
        """
        groups = self.get_groups_for_disease(orpha_code)
        return len(groups) > 0
    
    def get_diseases_with_groups(self) -> List[str]:
        """
        Get list of all diseases that have associated research groups
        
        Returns:
            List of orpha codes
        """
        disease_data = self._load_disease_group_data()
        return [orpha_code for orpha_code, groups in disease_data.items() if groups]
    
    def get_all_groups(self) -> List[str]:
        """
        Get list of all research groups
        
        Returns:
            List of group names
        """
        group_data = self._load_group_disease_data()
        return list(group_data.keys())
    
    def get_groups_by_type(self, group_type: str) -> List[str]:
        """
        Get groups filtered by type (u_format, descriptive, pi_based)
        
        Args:
            group_type: Type of group ('u_format', 'descriptive', 'pi_based')
            
        Returns:
            List of group names of the specified type
        """
        summary = self._load_curation_summary()
        quality_data = summary.get('quality_metrics', {})
        
        # If detailed type data is not available, use simple heuristics
        all_groups = self.get_all_groups()
        
        if group_type == 'u_format':
            return [g for g in all_groups if g.startswith('U') and g[1:].replace(' ', '').replace('CIBERER', '').strip().isdigit()]
        elif group_type == 'pi_based':
            return [g for g in all_groups if 'grupo del' in g.lower() or ('dr.' in g.lower() and 'grupo' in g.lower())]
        elif group_type == 'descriptive':
            u_groups = set(self.get_groups_by_type('u_format'))
            pi_groups = set(self.get_groups_by_type('pi_based'))
            return [g for g in all_groups if g not in u_groups and g not in pi_groups]
        else:
            return []
    
    def get_most_active_groups(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most active research groups by number of diseases
        
        Args:
            limit: Maximum number of groups to return
            
        Returns:
            List of dictionaries with group info sorted by activity
        """
        group_data = self._load_group_disease_data()
        
        # Calculate activity for each group
        group_activity = []
        for group_name, diseases in group_data.items():
            group_activity.append({
                'group_name': group_name,
                'disease_count': len(diseases),
                'diseases': diseases
            })
        
        # Sort by disease count (descending) and return top results
        group_activity.sort(key=lambda x: x['disease_count'], reverse=True)
        return group_activity[:limit]
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about sources and validation
        
        Returns:
            Dictionary containing source statistics
        """
        source_data = self._load_group_source_data()
        
        stats = {
            'total_groups_with_sources': len(source_data),
            'total_sources': 0,
            'sources_per_group': {},
            'source_types': {
                'pubmed': 0,
                'ciberer_website': 0,
                'other_websites': 0
            }
        }
        
        for group_name, sources in source_data.items():
            stats['sources_per_group'][group_name] = len(sources)
            stats['total_sources'] += len(sources)
            
            # Categorize sources
            for source in sources:
                url = source.get('url', '').lower()
                if 'pubmed' in url or 'ncbi.nlm.nih.gov' in url:
                    stats['source_types']['pubmed'] += 1
                elif 'ciberer' in url:
                    stats['source_types']['ciberer_website'] += 1
                else:
                    stats['source_types']['other_websites'] += 1
        
        # Calculate averages
        if stats['total_groups_with_sources'] > 0:
            stats['avg_sources_per_group'] = stats['total_sources'] / stats['total_groups_with_sources']
        else:
            stats['avg_sources_per_group'] = 0
        
        return stats
    
    def validate_sources_accessibility(self) -> Dict[str, Any]:
        """
        Validate source accessibility and format
        
        Returns:
            Dictionary containing validation results
        """
        source_data = self._load_group_source_data()
        
        validation = {
            'total_sources': 0,
            'valid_format': 0,
            'missing_url': 0,
            'missing_label': 0,
            'groups_validated': len(source_data)
        }
        
        for group_name, sources in source_data.items():
            for source in sources:
                validation['total_sources'] += 1
                
                has_url = 'url' in source and source['url']
                has_label = 'label' in source and source['label']
                
                if not has_url:
                    validation['missing_url'] += 1
                if not has_label:
                    validation['missing_label'] += 1
                    
                if has_url and has_label:
                    validation['valid_format'] += 1
        
        # Calculate percentages and invalid sources
        if validation['total_sources'] > 0:
            validation['valid_format_percentage'] = (validation['valid_format'] / validation['total_sources']) * 100
            validation['invalid_sources'] = validation['total_sources'] - validation['valid_format']
        else:
            validation['valid_format_percentage'] = 0
            validation['invalid_sources'] = 0
            
        return validation
    
    def export_to_csv(self, output_file: str) -> None:
        """
        Export disease-group mappings to CSV format
        
        Args:
            output_file: Path to output CSV file
        """
        disease_data = self._load_disease_group_data()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['orpha_code', 'group_name', 'group_count'])
            
            # Write data
            for orpha_code, groups in disease_data.items():
                if groups:
                    for group in groups:
                        writer.writerow([orpha_code, group, len(groups)])
                else:
                    writer.writerow([orpha_code, '', 0])
        
        logger.info(f"Exported disease-group mappings to: {output_file}")
    
    def get_curation_metadata(self) -> Dict[str, Any]:
        """
        Get curation process metadata and statistics
        
        Returns:
            Dictionary containing curation metadata
        """
        summary = self._load_curation_summary()
        return summary.get('curation_metadata', {})
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics
        
        Returns:
            Dictionary containing all summary statistics
        """
        disease_data = self._load_disease_group_data()
        group_data = self._load_group_disease_data()
        
        # Basic counts
        total_diseases = len(disease_data)
        diseases_with_groups = len([d for d, g in disease_data.items() if g])
        total_groups = len(group_data)
        
        # Coverage analysis
        coverage_percentage = (diseases_with_groups / total_diseases * 100) if total_diseases > 0 else 0
        
        # Group analysis
        group_sizes = [len(diseases) for diseases in group_data.values()]
        avg_diseases_per_group = sum(group_sizes) / len(group_sizes) if group_sizes else 0
        
        # Disease analysis
        disease_group_counts = [len(groups) for groups in disease_data.values()]
        avg_groups_per_disease = sum(disease_group_counts) / len(disease_group_counts) if disease_group_counts else 0
        
        return {
            'total_diseases': total_diseases,
            'diseases_with_groups': diseases_with_groups,
            'coverage_percentage': coverage_percentage,
            'total_groups': total_groups,
            'avg_diseases_per_group': avg_diseases_per_group,
            'avg_groups_per_disease': avg_groups_per_disease,
            'source_statistics': self.get_source_statistics(),
            'validation_results': self.validate_sources_accessibility()
        }


# Convenience function for quick access
def get_curated_websearch_groups_client() -> CuratedWebsearchGroupsClient:
    """
    Get a configured CuratedWebsearchGroupsClient instance
    
    Returns:
        Configured client instance
    """
    return CuratedWebsearchGroupsClient() 