#!/usr/bin/env python3
"""
Curated Gene Client

This client provides access to curated gene data with lazy loading
and caching capabilities for efficient data access.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
import csv


class CuratedGeneClient:
    """
    Client for accessing curated gene data with lazy loading and caching.
    
    This client provides efficient access to curated gene data including:
    - Disease to gene mappings (simple format)
    - Processing metadata and statistics
    - Disease name mappings
    - Cached results for performance
    """
    
    def __init__(self, data_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the curated gene client.
        
        Args:
            data_dir: Directory containing curated gene data files
        """
        self.data_dir = Path(data_dir)
        
        # Lazy-loaded data structures
        self._disease2genes: Optional[Dict[str, List[str]]] = None
        self._gene2diseases: Optional[Dict[str, List[str]]] = None
        self._gene_distribution: Optional[Dict[str, int]] = None
        self._processing_summary: Optional[Dict] = None
        self._orphacode2disease_name: Optional[Dict[str, str]] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Validate data directory
        if not self.data_dir.exists():
            raise ValueError(f"Data directory does not exist: {self.data_dir}")

    def _ensure_disease2genes_loaded(self):
        """Load disease to genes mapping if not already loaded"""
        if self._disease2genes is None:
            file_path = self.data_dir / "disease2genes.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2genes = json.load(f)
                self.logger.debug(f"Loaded disease2genes mapping: {len(self._disease2genes)} diseases")
            else:
                self._disease2genes = {}
                self.logger.warning("disease2genes.json not found")

    def _ensure_processing_summary_loaded(self):
        """Load processing summary if not already loaded"""
        if self._processing_summary is None:
            file_path = self.data_dir / "orpha_gene_curation_summary.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._processing_summary = json.load(f)
                self.logger.debug("Loaded processing summary")
            else:
                self._processing_summary = {}
                self.logger.warning("orpha_gene_curation_summary.json not found")

    def _ensure_orphacode2disease_name_loaded(self):
        """Load orpha code to disease name mapping if not already loaded"""
        if self._orphacode2disease_name is None:
            # Try the main disease name file
            file_path = self.data_dir / ".." / "ordo" / "orphacode2disease_name.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._orphacode2disease_name = json.load(f)
                self.logger.debug(f"Loaded disease names: {len(self._orphacode2disease_name)} diseases")
            else:
                # Fallback to empty dict
                self._orphacode2disease_name = {}
                self.logger.warning("orphacode2disease_name.json not found")

    def _calculate_gene2diseases(self) -> Dict[str, List[str]]:
        """Calculate gene to diseases mapping from disease to genes data"""
        if self._gene2diseases is None:
            self._ensure_disease2genes_loaded()
            
            gene2diseases = {}
            for orpha_code, genes in self._disease2genes.items():
                for gene in genes:
                    if gene not in gene2diseases:
                        gene2diseases[gene] = []
                    gene2diseases[gene].append(orpha_code)
            
            self._gene2diseases = gene2diseases
            
        return self._gene2diseases

    def _calculate_gene_distribution(self) -> Dict[str, int]:
        """Calculate gene distribution from loaded data"""
        if self._gene_distribution is None:
            self._ensure_disease2genes_loaded()
            
            distribution = {}
            for genes in self._disease2genes.values():
                for gene in genes:
                    distribution[gene] = distribution.get(gene, 0) + 1
            
            self._gene_distribution = distribution
            
        return self._gene_distribution

    # ========== Core Data Access ==========

    def get_genes_for_disease(self, orpha_code: str) -> List[str]:
        """
        Get disease-causing genes for a specific disease.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            List of gene symbols or empty list if not found
        """
        self._ensure_disease2genes_loaded()
        return self._disease2genes.get(orpha_code, [])

    def get_diseases_for_gene(self, gene_symbol: str) -> List[str]:
        """
        Get diseases associated with a specific gene.
        
        Args:
            gene_symbol: Gene symbol (e.g., PMM2)
            
        Returns:
            List of orpha codes or empty list if not found
        """
        gene2diseases = self._calculate_gene2diseases()
        return gene2diseases.get(gene_symbol, [])

    def has_genes(self, orpha_code: str) -> bool:
        """
        Check if disease has disease-causing genes.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            True if disease has genes in the curated dataset
        """
        return bool(self.get_genes_for_disease(orpha_code))

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

    def get_disease_info(self, orpha_code: str) -> Dict[str, Any]:
        """
        Get comprehensive disease gene information.
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Dictionary with disease information
        """
        return {
            'orpha_code': orpha_code,
            'disease_name': self.get_disease_name(orpha_code),
            'genes': self.get_genes_for_disease(orpha_code),
            'gene_count': len(self.get_genes_for_disease(orpha_code))
        }

    # ========== Search and Filter Methods ==========

    def search_diseases_by_gene(self, gene_symbol: str) -> List[str]:
        """
        Search diseases by exact gene symbol match.
        
        Args:
            gene_symbol: Gene symbol to search for
            
        Returns:
            List of orpha codes with this gene
        """
        return self.get_diseases_for_gene(gene_symbol)

    def search_genes_by_pattern(self, pattern: str, case_sensitive: bool = False) -> List[str]:
        """
        Search genes by name pattern.
        
        Args:
            pattern: Pattern to search for in gene symbols
            case_sensitive: Whether search should be case sensitive
            
        Returns:
            List of gene symbols matching the pattern
        """
        gene_distribution = self._calculate_gene_distribution()
        
        if not case_sensitive:
            pattern = pattern.lower()
        
        matching_genes = []
        for gene in gene_distribution.keys():
            search_gene = gene if case_sensitive else gene.lower()
            if pattern in search_gene:
                matching_genes.append(gene)
        
        return sorted(matching_genes)

    def get_diseases_with_multiple_genes(self, min_genes: int = 2) -> List[Dict]:
        """
        Get diseases with multiple disease-causing genes.
        
        Args:
            min_genes: Minimum number of genes (default: 2)
            
        Returns:
            List of dictionaries with disease information
        """
        self._ensure_disease2genes_loaded()
        
        diseases_with_multiple = []
        for orpha_code, genes in self._disease2genes.items():
            if len(genes) >= min_genes:
                diseases_with_multiple.append({
                    'orpha_code': orpha_code,
                    'disease_name': self.get_disease_name(orpha_code),
                    'genes': genes,
                    'gene_count': len(genes)
                })
        
        # Sort by gene count (descending)
        diseases_with_multiple.sort(key=lambda x: x['gene_count'], reverse=True)
        return diseases_with_multiple

    def get_diseases_with_single_gene(self) -> List[Dict]:
        """
        Get diseases with exactly one disease-causing gene.
        
        Returns:
            List of dictionaries with disease information
        """
        return self.get_diseases_with_multiple_genes(min_genes=1)[:self.get_diseases_with_multiple_genes(min_genes=2)[0]['gene_count'] if self.get_diseases_with_multiple_genes(min_genes=2) else len(self._disease2genes)]

    def get_diseases_with_genes(self) -> List[str]:
        """
        Get all disease codes that have genes in the curated dataset.
        
        Returns:
            List of orpha codes
        """
        self._ensure_disease2genes_loaded()
        return list(self._disease2genes.keys())

    # ========== Statistical Methods ==========

    def get_coverage_statistics(self) -> Dict[str, Any]:
        """
        Get coverage statistics for metabolic diseases.
        
        Returns:
            Dictionary with coverage statistics
        """
        self._ensure_processing_summary_loaded()
        
        if self._processing_summary:
            metadata = self._processing_summary.get('curation_metadata', {})
            return {
                'total_diseases': metadata.get('input_diseases', 0),
                'diseases_with_genes': metadata.get('diseases_with_genes', 0),
                'diseases_without_genes': metadata.get('diseases_without_genes', 0),
                'coverage_percentage': metadata.get('coverage_percentage', 0.0),
                'processing_timestamp': metadata.get('processing_timestamp', '')
            }
        else:
            # Fallback calculation
            self._ensure_disease2genes_loaded()
            diseases_with_genes = len(self._disease2genes)
            return {
                'total_diseases': diseases_with_genes,  # Only curated diseases available
                'diseases_with_genes': diseases_with_genes,
                'diseases_without_genes': 0,
                'coverage_percentage': 100.0,
                'processing_timestamp': ''
            }

    def get_gene_distribution(self) -> Dict[str, int]:
        """
        Get distribution of genes across diseases.
        
        Returns:
            Dictionary mapping gene symbol to count of diseases
        """
        return self._calculate_gene_distribution()

    def get_disease_gene_count_distribution(self) -> Dict[str, int]:
        """
        Get distribution of gene counts per disease.
        
        Returns:
            Dictionary mapping gene count ranges to disease counts
        """
        self._ensure_disease2genes_loaded()
        
        count_distribution = {}
        for genes in self._disease2genes.values():
            gene_count = len(genes)
            
            # Create count ranges
            if gene_count == 1:
                range_key = "1_gene"
            elif gene_count <= 3:
                range_key = "2-3_genes"
            elif gene_count <= 5:
                range_key = "4-5_genes"
            elif gene_count <= 10:
                range_key = "6-10_genes"
            else:
                range_key = "11+_genes"
            
            count_distribution[range_key] = count_distribution.get(range_key, 0) + 1
        
        return count_distribution

    def get_most_common_genes(self, limit: int = 20) -> List[Dict]:
        """
        Get most frequently associated genes.
        
        Args:
            limit: Maximum number of genes to return
            
        Returns:
            List of dictionaries with gene information
        """
        gene_distribution = self._calculate_gene_distribution()
        
        # Sort by frequency
        sorted_genes = sorted(gene_distribution.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'gene': gene,
                'disease_count': count,
                'diseases': self.get_diseases_for_gene(gene)
            }
            for gene, count in sorted_genes[:limit]
        ]

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        coverage_stats = self.get_coverage_statistics()
        gene_dist = self.get_gene_distribution()
        disease_gene_dist = self.get_disease_gene_count_distribution()
        
        return {
            'coverage_statistics': coverage_stats,
            'gene_statistics': {
                'total_unique_genes': len(gene_dist),
                'total_gene_associations': sum(gene_dist.values()),
                'average_diseases_per_gene': round(sum(gene_dist.values()) / len(gene_dist), 2) if gene_dist else 0,
                'most_common_gene': max(gene_dist.items(), key=lambda x: x[1]) if gene_dist else None
            },
            'disease_gene_distribution': disease_gene_dist,
            'processing_metadata': self.get_processing_metadata()
        }

    def get_processing_metadata(self) -> Dict[str, Any]:
        """
        Get processing metadata.
        
        Returns:
            Dictionary with processing metadata
        """
        self._ensure_processing_summary_loaded()
        return self._processing_summary.copy() if self._processing_summary else {}

    # ========== Data Management ==========

    def export_to_csv(self, output_file: str, include_disease_names: bool = True):
        """
        Export to CSV format.
        
        Args:
            output_file: Output CSV file path
            include_disease_names: Whether to include disease names
        """
        self._ensure_disease2genes_loaded()
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if include_disease_names:
                self._ensure_orphacode2disease_name_loaded()
                fieldnames = ['orpha_code', 'disease_name', 'genes', 'gene_count']
            else:
                fieldnames = ['orpha_code', 'genes', 'gene_count']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for orpha_code, genes in self._disease2genes.items():
                row = {
                    'orpha_code': orpha_code,
                    'genes': ';'.join(genes),
                    'gene_count': len(genes)
                }
                
                if include_disease_names:
                    row['disease_name'] = self.get_disease_name(orpha_code) or 'Unknown'
                
                writer.writerow(row)
        
        self.logger.info(f"Exported gene data to CSV: {output_file}")

    def export_to_json(self, output_file: str):
        """
        Export to JSON format.
        
        Args:
            output_file: Output JSON file path
        """
        self._ensure_disease2genes_loaded()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self._disease2genes, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Exported gene data to JSON: {output_file}")

    def validate_data_consistency(self) -> Dict[str, Any]:
        """
        Validate data consistency.
        
        Returns:
            Dictionary with validation results
        """
        self._ensure_disease2genes_loaded()
        
        validation_result = {
            'is_valid': True,
            'issues': [],
            'statistics': {
                'total_diseases': len(self._disease2genes),
                'total_gene_associations': sum(len(genes) for genes in self._disease2genes.values()),
                'unique_genes': len(self._calculate_gene_distribution())
            }
        }
        
        # Check for empty gene lists
        empty_gene_diseases = [orpha_code for orpha_code, genes in self._disease2genes.items() if not genes]
        if empty_gene_diseases:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Found {len(empty_gene_diseases)} diseases with empty gene lists")
        
        # Check for invalid gene symbols (basic validation)
        invalid_genes = []
        for orpha_code, genes in self._disease2genes.items():
            for gene in genes:
                if not gene or not isinstance(gene, str) or len(gene.strip()) == 0:
                    invalid_genes.append((orpha_code, gene))
        
        if invalid_genes:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Found {len(invalid_genes)} invalid gene symbols")
        
        # Check for duplicate genes within same disease
        duplicate_issues = []
        for orpha_code, genes in self._disease2genes.items():
            if len(genes) != len(set(genes)):
                duplicate_issues.append(orpha_code)
        
        if duplicate_issues:
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Found duplicate genes in {len(duplicate_issues)} diseases")
        
        return validation_result

    def clear_cache(self):
        """Clear cached data to free memory"""
        self._disease2genes = None
        self._gene2diseases = None
        self._gene_distribution = None
        self._processing_summary = None
        self._orphacode2disease_name = None
        self._cache.clear()
        self.logger.info("Curated gene client cache cleared")

    def reload_data(self):
        """Reload data from files"""
        self.clear_cache()
        self._ensure_disease2genes_loaded()
        self._ensure_processing_summary_loaded()
        self._ensure_orphacode2disease_name_loaded()
        self.logger.info("Curated gene client data reloaded")

    def is_data_available(self) -> bool:
        """Check if gene data is available"""
        disease2genes_file = self.data_dir / "disease2genes.json"
        return disease2genes_file.exists()


# Example usage and testing
def main():
    """Example usage of the CuratedGeneClient"""
    
    client = CuratedGeneClient()
    
    if not client.is_data_available():
        print("Gene data not available. Run curate_orpha_genes.py first.")
        return
    
    # Get basic statistics
    stats = client.get_summary_statistics()
    coverage = stats['coverage_statistics']
    gene_stats = stats['gene_statistics']
    
    print(f"Gene Statistics:")
    print(f"- Total diseases with genes: {coverage['diseases_with_genes']}")
    print(f"- Coverage: {coverage['coverage_percentage']:.1f}%")
    print(f"- Unique genes: {gene_stats['total_unique_genes']}")
    print(f"- Total gene associations: {gene_stats['total_gene_associations']}")
    print(f"- Average diseases per gene: {gene_stats['average_diseases_per_gene']}")
    
    # Get disease gene distribution
    disease_dist = client.get_disease_gene_count_distribution()
    print(f"\nDisease gene count distribution:")
    for range_key, count in sorted(disease_dist.items()):
        print(f"- {range_key}: {count} diseases")
    
    # Get top genes
    top_genes = client.get_most_common_genes(5)
    print(f"\nTop 5 most common genes:")
    for gene_info in top_genes:
        print(f"- {gene_info['gene']}: {gene_info['disease_count']} diseases")
    
    # Example queries
    print(f"\nExample queries:")
    genes_for_disease = client.get_genes_for_disease("79318")  # PMM2-CDG
    print(f"- Genes for disease 79318: {genes_for_disease}")
    
    if genes_for_disease:
        diseases_for_gene = client.get_diseases_for_gene(genes_for_disease[0])
        print(f"- Diseases for gene {genes_for_disease[0]}: {len(diseases_for_gene)} diseases")
    
    # Search functionality
    multiple_gene_diseases = client.get_diseases_with_multiple_genes(min_genes=5)
    print(f"- Diseases with 5+ genes: {len(multiple_gene_diseases)}")
    if multiple_gene_diseases:
        top_disease = multiple_gene_diseases[0]
        print(f"  Top: {top_disease['orpha_code']} with {top_disease['gene_count']} genes")


if __name__ == "__main__":
    main() 