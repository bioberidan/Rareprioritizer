#!/usr/bin/env python3
"""
Processed Gene Client - Query interface for gene data

This module provides a sophisticated interface for querying gene data
with lazy loading, caching, and advanced filtering capabilities for gene-disease
associations, external references, and gene types.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union, Any
from functools import lru_cache
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class ProcessedGeneClient:
    """Client for processed gene data with lazy loading and advanced query capabilities"""
    
    def __init__(self, data_dir: str = "data/03_processed/orpha/orphadata/orpha_genes"):
        """
        Initialize the processed gene client
        
        Args:
            data_dir: Directory containing processed gene data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Gene data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._disease2genes: Optional[Dict] = None
        self._gene2diseases: Optional[Dict] = None
        self._gene_instances: Optional[Dict] = None
        self._gene_association_instances: Optional[Dict] = None
        self._orpha_index: Optional[Dict] = None
        self._processing_statistics: Optional[Dict] = None
        
        # External references
        self._external_references: Optional[Dict] = None
        
        # Cache files
        self._gene_symbols_index: Optional[Dict] = None
        self._locus_index: Optional[Dict] = None
        self._association_type_index: Optional[Dict] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        logger.info(f"Processed gene client initialized with data dir: {data_dir}")
    
    # ========== Data Loading Methods ==========
    
    def _ensure_disease2genes_loaded(self):
        """Load disease to genes mapping if not already loaded"""
        if self._disease2genes is None:
            file_path = self.data_dir / "disease2genes.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2genes = json.load(f)
                logger.info(f"Loaded disease2genes mapping: {len(self._disease2genes)} diseases")
            else:
                self._disease2genes = {}
                logger.warning("disease2genes.json not found")
    
    def _ensure_gene2diseases_loaded(self):
        """Load gene to diseases mapping if not already loaded"""
        if self._gene2diseases is None:
            file_path = self.data_dir / "gene2diseases.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._gene2diseases = json.load(f)
                logger.info(f"Loaded gene2diseases mapping: {len(self._gene2diseases)} genes")
            else:
                self._gene2diseases = {}
                logger.warning("gene2diseases.json not found")
    
    def _ensure_gene_instances_loaded(self):
        """Load gene instances if not already loaded"""
        if self._gene_instances is None:
            file_path = self.data_dir / "gene_instances.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._gene_instances = json.load(f)
                logger.info(f"Loaded gene instances: {len(self._gene_instances)} genes")
            else:
                self._gene_instances = {}
                logger.warning("gene_instances.json not found")
    
    def _ensure_gene_association_instances_loaded(self):
        """Load gene association instances if not already loaded"""
        if self._gene_association_instances is None:
            file_path = self.data_dir / "gene_association_instances.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._gene_association_instances = json.load(f)
                logger.info(f"Loaded gene association instances: {len(self._gene_association_instances)} associations")
            else:
                self._gene_association_instances = {}
                logger.warning("gene_association_instances.json not found")
    
    def _ensure_orpha_index_loaded(self):
        """Load orpha index if not already loaded"""
        if self._orpha_index is None:
            file_path = self.data_dir / "orpha_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._orpha_index = json.load(f)
                logger.info(f"Loaded orpha index: {len(self._orpha_index)} diseases")
            else:
                self._orpha_index = {}
                logger.warning("orpha_index.json not found")
    
    def _ensure_processing_statistics_loaded(self):
        """Load processing statistics if not already loaded"""
        if self._processing_statistics is None:
            file_path = self.data_dir / "cache" / "statistics.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._processing_statistics = json.load(f)
                logger.info("Loaded processing statistics")
            else:
                self._processing_statistics = {}
                logger.warning("cache/statistics.json not found")
    
    def _ensure_gene_symbols_index_loaded(self):
        """Load gene symbols index if not already loaded"""
        if self._gene_symbols_index is None:
            file_path = self.data_dir / "cache" / "gene_symbols_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._gene_symbols_index = json.load(f)
                logger.info(f"Loaded gene symbols index: {len(self._gene_symbols_index)} symbols")
            else:
                self._gene_symbols_index = {}
                logger.warning("cache/gene_symbols_index.json not found")
    
    def _ensure_locus_index_loaded(self):
        """Load locus index if not already loaded"""
        if self._locus_index is None:
            file_path = self.data_dir / "cache" / "locus_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._locus_index = json.load(f)
                logger.info(f"Loaded locus index: {len(self._locus_index)} loci")
            else:
                self._locus_index = {}
                logger.warning("cache/locus_index.json not found")
    
    def _ensure_association_type_index_loaded(self):
        """Load association type index if not already loaded"""
        if self._association_type_index is None:
            file_path = self.data_dir / "cache" / "association_type_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._association_type_index = json.load(f)
                logger.info(f"Loaded association type index: {len(self._association_type_index)} types")
            else:
                self._association_type_index = {}
                logger.warning("cache/association_type_index.json not found")
    
    # ========== Core Query Methods ==========
    
    def get_genes_for_disease(self, orpha_code: str,
                            association_type: Optional[str] = None,
                            gene_type: Optional[str] = None) -> List[Dict]:
        """
        Get gene associations for a specific disease with optional filtering
        
        Args:
            orpha_code: Orpha code of the disease
            association_type: Filter by association type (Disease-causing, Risk factor, etc.)
            gene_type: Filter by gene type (gene with protein product, etc.)
            
        Returns:
            List of gene association dictionaries
        """
        self._ensure_disease2genes_loaded()
        
        disease_data = self._disease2genes.get(orpha_code)
        if not disease_data:
            return []
        
        associations = disease_data.get('gene_associations', [])
        
        # Apply filters
        if association_type:
            associations = [a for a in associations if a.get('association_type') == association_type]
        
        if gene_type:
            associations = [a for a in associations if a.get('gene_type') == gene_type]
        
        return associations
    
    def get_diseases_for_gene(self, gene_symbol: str,
                            association_type: Optional[str] = None) -> List[Dict]:
        """
        Get disease associations for a specific gene
        
        Args:
            gene_symbol: Gene symbol (e.g., KIF7)
            association_type: Filter by association type
            
        Returns:
            List of disease association dictionaries
        """
        self._ensure_gene2diseases_loaded()
        
        gene_data = self._gene2diseases.get(gene_symbol)
        if not gene_data:
            return []
        
        diseases = gene_data.get('associated_diseases', [])
        
        # Apply filters
        if association_type:
            diseases = [d for d in diseases if d.get('association_type') == association_type]
        
        return diseases
    
    def get_gene_details(self, gene_symbol: str) -> Optional[Dict]:
        """
        Get comprehensive gene information
        
        Args:
            gene_symbol: Gene symbol
            
        Returns:
            Gene instance dictionary or None if not found
        """
        self._ensure_gene_instances_loaded()
        return self._gene_instances.get(gene_symbol)
    
    def get_disease_gene_summary(self, orpha_code: str) -> Optional[Dict]:
        """
        Get complete gene summary for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Complete disease gene mapping or None if not found
        """
        self._ensure_disease2genes_loaded()
        return self._disease2genes.get(orpha_code)
    
    def get_gene_association_details(self, association_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific gene association
        
        Args:
            association_id: Gene association ID
            
        Returns:
            Gene association dictionary or None if not found
        """
        self._ensure_gene_association_instances_loaded()
        return self._gene_association_instances.get(association_id)
    
    # ========== Search Methods ==========
    
    def search_genes_by_locus(self, locus: str) -> List[Dict]:
        """
        Search genes by chromosomal location
        
        Args:
            locus: Chromosomal location (e.g., 15q26.1)
            
        Returns:
            List of gene dictionaries
        """
        self._ensure_locus_index_loaded()
        self._ensure_gene_instances_loaded()
        
        gene_symbols = self._locus_index.get(locus, [])
        return [self._gene_instances[symbol] for symbol in gene_symbols if symbol in self._gene_instances]
    
    def search_genes_by_name(self, name_pattern: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search genes by name pattern
        
        Args:
            name_pattern: Pattern to search for in gene names
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of gene dictionaries
        """
        self._ensure_gene_instances_loaded()
        
        if not case_sensitive:
            name_pattern = name_pattern.lower()
        
        matching_genes = []
        for gene_symbol, gene_data in self._gene_instances.items():
            gene_name = gene_data.get('gene_name', '')
            search_name = gene_name if case_sensitive else gene_name.lower()
            
            if name_pattern in search_name:
                matching_genes.append(gene_data)
        
        return matching_genes
    
    def search_genes_by_symbol(self, symbol_pattern: str, case_sensitive: bool = False) -> List[Dict]:
        """
        Search genes by symbol pattern
        
        Args:
            symbol_pattern: Pattern to search for in gene symbols
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of gene dictionaries
        """
        self._ensure_gene_instances_loaded()
        
        if not case_sensitive:
            symbol_pattern = symbol_pattern.lower()
        
        matching_genes = []
        for gene_symbol, gene_data in self._gene_instances.items():
            search_symbol = gene_symbol if case_sensitive else gene_symbol.lower()
            
            if symbol_pattern in search_symbol:
                matching_genes.append(gene_data)
        
        return matching_genes
    
    def get_genes_by_type(self, gene_type: str) -> List[Dict]:
        """
        Get genes by type classification
        
        Args:
            gene_type: Gene type (e.g., "gene with protein product")
            
        Returns:
            List of gene dictionaries
        """
        self._ensure_gene_instances_loaded()
        
        matching_genes = []
        for gene_data in self._gene_instances.values():
            if gene_data.get('gene_type') == gene_type:
                matching_genes.append(gene_data)
        
        return matching_genes
    
    def get_associations_by_type(self, association_type: str) -> List[Dict]:
        """
        Get associations by type
        
        Args:
            association_type: Association type (e.g., "Disease-causing germline mutation(s) in")
            
        Returns:
            List of association dictionaries
        """
        self._ensure_association_type_index_loaded()
        self._ensure_gene_association_instances_loaded()
        
        association_ids = self._association_type_index.get(association_type, [])
        return [self._gene_association_instances[aid] for aid in association_ids 
                if aid in self._gene_association_instances]
    
    def search_by_external_reference(self, database: str, reference: str) -> List[Dict]:
        """
        Search by external database reference
        
        Args:
            database: Database name (e.g., HGNC, OMIM, Ensembl)
            reference: Reference identifier
            
        Returns:
            List of gene dictionaries
        """
        self._ensure_gene_instances_loaded()
        
        matching_genes = []
        for gene_data in self._gene_instances.values():
            external_refs = gene_data.get('external_references', {})
            if external_refs.get(database) == reference:
                matching_genes.append(gene_data)
        
        return matching_genes
    
    # ========== Statistical Methods ==========
    
    def get_statistics(self) -> Dict:
        """Get comprehensive gene statistics"""
        self._ensure_processing_statistics_loaded()
        return self._processing_statistics.copy() if self._processing_statistics else {}
    
    def get_basic_coverage_stats(self) -> Dict:
        """Get basic coverage statistics"""
        stats = self.get_statistics()
        
        return {
            "total_disorders": stats.get("total_disorders", 0),
            "disorders_with_genes": stats.get("disorders_with_genes", 0),
            "total_gene_associations": stats.get("total_gene_associations", 0),
            "unique_genes": stats.get("unique_genes", 0),
            "coverage_percentage": round((stats.get("disorders_with_genes", 0) / 
                                        max(stats.get("total_disorders", 1), 1)) * 100, 2)
        }
    
    def get_association_type_distribution(self) -> Dict[str, int]:
        """Get distribution of association types"""
        stats = self.get_statistics()
        return stats.get('association_types', {})
    
    def get_gene_type_distribution(self) -> Dict[str, int]:
        """Get distribution of gene types"""
        stats = self.get_statistics()
        return stats.get('gene_types', {})
    
    def get_external_reference_coverage(self) -> Dict[str, int]:
        """Get coverage statistics for external references"""
        stats = self.get_statistics()
        return stats.get('external_reference_coverage', {})
    
    def get_genes_with_most_diseases(self, limit: int = 20) -> List[Dict]:
        """Get genes with the most disease associations"""
        self._ensure_gene2diseases_loaded()
        
        genes_list = []
        for gene_symbol, gene_data in self._gene2diseases.items():
            genes_list.append({
                'gene_symbol': gene_symbol,
                'gene_name': gene_data.get('gene_name'),
                'gene_type': gene_data.get('gene_type'),
                'total_disease_associations': gene_data.get('total_disease_associations', 0),
                'association_types': gene_data.get('statistics', {}).get('association_types', {})
            })
        
        genes_list.sort(key=lambda g: g['total_disease_associations'], reverse=True)
        return genes_list[:limit]
    
    def get_diseases_with_most_genes(self, limit: int = 20) -> List[Dict]:
        """Get diseases with the most gene associations"""
        self._ensure_disease2genes_loaded()
        
        diseases_list = []
        for orpha_code, disease_data in self._disease2genes.items():
            diseases_list.append({
                'orpha_code': orpha_code,
                'disease_name': disease_data.get('disease_name'),
                'total_gene_associations': disease_data.get('total_gene_associations', 0),
                'primary_gene': disease_data.get('primary_gene'),
                'gene_list': [assoc['gene_symbol'] for assoc in disease_data.get('gene_associations', [])]
            })
        
        diseases_list.sort(key=lambda d: d['total_gene_associations'], reverse=True)
        return diseases_list[:limit]
    
    def get_locus_distribution(self) -> Dict[str, int]:
        """Get distribution of genes by chromosomal location"""
        self._ensure_locus_index_loaded()
        
        locus_dist = {}
        for locus, genes in self._locus_index.items():
            locus_dist[locus] = len(genes)
        
        return locus_dist
    
    def get_source_validation_stats(self) -> Dict[str, int]:
        """Get statistics on source validation"""
        self._ensure_gene_association_instances_loaded()
        
        validation_stats = {
            'pmid_validated': 0,
            'expert_validated': 0,
            'no_validation': 0,
            'other_validation': 0
        }
        
        for assoc in self._gene_association_instances.values():
            source_validation = assoc.get('source_validation', '')
            if '[PMID]' in source_validation:
                validation_stats['pmid_validated'] += 1
            elif 'EXPERT' in source_validation:
                validation_stats['expert_validated'] += 1
            elif not source_validation:
                validation_stats['no_validation'] += 1
            else:
                validation_stats['other_validation'] += 1
        
        return validation_stats
    
    def get_external_reference_completeness(self) -> Dict[str, Dict[str, float]]:
        """Get external reference completeness statistics"""
        self._ensure_gene_instances_loaded()
        
        total_genes = len(self._gene_instances)
        if total_genes == 0:
            return {}
        
        reference_sources = set()
        for gene_data in self._gene_instances.values():
            reference_sources.update(gene_data.get('external_references', {}).keys())
        
        completeness = {}
        for source in reference_sources:
            genes_with_ref = sum(1 for gene_data in self._gene_instances.values() 
                               if source in gene_data.get('external_references', {}))
            completeness[source] = {
                'count': genes_with_ref,
                'percentage': round((genes_with_ref / total_genes) * 100, 2)
            }
        
        return completeness
    
    # ========== Utility Methods ==========
    
    def clear_cache(self):
        """Clear all cached data to free memory"""
        self._disease2genes = None
        self._gene2diseases = None
        self._gene_instances = None
        self._gene_association_instances = None
        self._orpha_index = None
        self._processing_statistics = None
        self._external_references = None
        self._gene_symbols_index = None
        self._locus_index = None
        self._association_type_index = None
        self._cache.clear()
        logger.info("Processed gene client cache cleared")
    
    def preload_all(self):
        """Preload all data for better performance"""
        self._ensure_disease2genes_loaded()
        self._ensure_gene2diseases_loaded()
        self._ensure_gene_instances_loaded()
        self._ensure_gene_association_instances_loaded()
        self._ensure_orpha_index_loaded()
        self._ensure_processing_statistics_loaded()
        self._ensure_gene_symbols_index_loaded()
        self._ensure_locus_index_loaded()
        self._ensure_association_type_index_loaded()
        logger.info("All gene data preloaded")
    
    def is_data_available(self) -> bool:
        """Check if gene data is available"""
        required_files = [
            "disease2genes.json",
            "gene2diseases.json",
            "gene_instances.json",
            "gene_association_instances.json",
            "orpha_index.json"
        ]
        
        for filename in required_files:
            if not (self.data_dir / filename).exists():
                return False
        
        return True
    
    def export_gene_associations(self, output_file: str, format: str = 'json'):
        """
        Export gene associations to file
        
        Args:
            output_file: Output file path
            format: Export format (json, csv)
        """
        self._ensure_gene_association_instances_loaded()
        
        if format.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self._gene_association_instances, f, ensure_ascii=False, indent=2)
        elif format.lower() == 'csv':
            import csv
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if not self._gene_association_instances:
                    return
                
                # Get field names from first record
                first_record = next(iter(self._gene_association_instances.values()))
                fieldnames = [k for k in first_record.keys() if k != 'external_references']
                fieldnames.extend(['external_references'])
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for assoc in self._gene_association_instances.values():
                    row = {k: v for k, v in assoc.items() if k != 'external_references'}
                    row['external_references'] = str(assoc.get('external_references', {}))
                    writer.writerow(row)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @lru_cache(maxsize=1000)
    def _get_disease_cached(self, orpha_code: str) -> Optional[Dict]:
        """Cached version of disease lookup"""
        return self.get_disease_gene_summary(orpha_code)
    
    @lru_cache(maxsize=1000)
    def _get_gene_cached(self, gene_symbol: str) -> Optional[Dict]:
        """Cached version of gene lookup"""
        return self.get_gene_details(gene_symbol)


# Example usage and testing
def main():
    """Example usage of the ProcessedGeneClient"""
    
    client = ProcessedGeneClient()
    
    if not client.is_data_available():
        print("Gene data not available. Run process_orpha_genes.py first.")
        return
    
    # Get basic statistics
    stats = client.get_basic_coverage_stats()
    print(f"Gene Statistics:")
    print(f"- Total disorders: {stats.get('total_disorders', 'N/A')}")
    print(f"- Disorders with genes: {stats.get('disorders_with_genes', 'N/A')}")
    print(f"- Total gene associations: {stats.get('total_gene_associations', 'N/A')}")
    print(f"- Unique genes: {stats.get('unique_genes', 'N/A')}")
    print(f"- Coverage percentage: {stats.get('coverage_percentage', 'N/A')}%")
    
    # Get association type distribution
    assoc_types = client.get_association_type_distribution()
    print(f"\nTop 5 association types:")
    for assoc_type, count in sorted(assoc_types.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"- {assoc_type}: {count}")
    
    # Get gene type distribution
    gene_types = client.get_gene_type_distribution()
    print(f"\nGene type distribution:")
    for gene_type, count in sorted(gene_types.items(), key=lambda x: x[1], reverse=True):
        print(f"- {gene_type}: {count}")


if __name__ == "__main__":
    main() 