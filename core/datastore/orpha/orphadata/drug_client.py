"""
Processed Drug Client - Query interface for drug data

This module provides a OrphaTaxonomy-style interface for querying drug data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)


class ProcessedDrugClient:
    """Client for processed drug data with lazy loading and query capabilities"""
    
    def __init__(self, data_dir: str = "data/processed/drug"):
        """
        Initialize the processed drug client
        
        Args:
            data_dir: Directory containing processed drug data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Drug data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._diseases2drugs: Optional[Dict] = None
        self._drugs2diseases: Optional[Dict] = None
        self._drug_index: Optional[Dict] = None
        self._processing_summary: Optional[Dict] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        logger.info(f"Processed drug client initialized with data dir: {data_dir}")
    
    def _ensure_diseases2drugs_loaded(self):
        """Load diseases to drugs mapping if not already loaded"""
        if self._diseases2drugs is None:
            file_path = self.data_dir / "diseases2drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._diseases2drugs = json.load(f)
                logger.info(f"Loaded diseases2drugs mapping: {len(self._diseases2drugs)} diseases")
            else:
                self._diseases2drugs = {}
                logger.warning("diseases2drugs.json not found")
    
    def _ensure_drugs2diseases_loaded(self):
        """Load drugs to diseases mapping if not already loaded"""
        if self._drugs2diseases is None:
            file_path = self.data_dir / "drugs2diseases.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._drugs2diseases = json.load(f)
                logger.info(f"Loaded drugs2diseases mapping: {len(self._drugs2diseases)} drugs")
            else:
                self._drugs2diseases = {}
                logger.warning("drugs2diseases.json not found")
    
    def _ensure_drug_index_loaded(self):
        """Load drug index if not already loaded"""
        if self._drug_index is None:
            file_path = self.data_dir / "drug_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._drug_index = json.load(f)
                logger.info(f"Loaded drug index: {len(self._drug_index)} drugs")
            else:
                self._drug_index = {}
                logger.warning("drug_index.json not found")
    
    def _ensure_processing_summary_loaded(self):
        """Load processing summary if not already loaded"""
        if self._processing_summary is None:
            file_path = self.data_dir / "processing_summary.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._processing_summary = json.load(f)
                logger.info("Loaded processing summary")
            else:
                self._processing_summary = {}
                logger.warning("processing_summary.json not found")
    
    # ========== Basic Query Methods ==========
    
    def get_drugs_for_disease(self, orpha_code: str) -> List[Dict]:
        """
        Get all drugs for a specific disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            List of drug dictionaries
        """
        self._ensure_diseases2drugs_loaded()
        self._ensure_drug_index_loaded()
        
        disease_data = self._diseases2drugs.get(orpha_code)
        if not disease_data:
            return []
        
        drugs = []
        for drug_id in disease_data.get('drugs', []):
            drug_details = self._drug_index.get(drug_id)
            if drug_details:
                drugs.append(drug_details)
        
        return drugs
    
    def get_diseases_for_drug(self, drug_id: str) -> List[Dict]:
        """
        Get all diseases associated with a drug
        
        Args:
            drug_id: Drug ID (substance_id or generated ID)
            
        Returns:
            List of disease dictionaries
        """
        self._ensure_drugs2diseases_loaded()
        
        drug_data = self._drugs2diseases.get(drug_id)
        if not drug_data:
            return []
        
        return drug_data.get('diseases', [])
    
    def get_drug_details(self, drug_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific drug
        
        Args:
            drug_id: Drug ID (substance_id or generated ID)
            
        Returns:
            Drug dictionary or None if not found
        """
        self._ensure_drug_index_loaded()
        return self._drug_index.get(drug_id)
    
    def get_disease_drug_summary(self, orpha_code: str) -> Optional[Dict]:
        """
        Get summary information about drugs for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Summary dictionary or None if not found
        """
        self._ensure_diseases2drugs_loaded()
        return self._diseases2drugs.get(orpha_code)
    
    # ========== Search and Filter Methods ==========
    
    def search_drugs_by_status(self, status: str) -> List[Dict]:
        """
        Search drugs by regulatory status
        
        Args:
            status: Drug status (e.g., 'Medicinal product', 'Investigational')
            
        Returns:
            List of matching drug dictionaries
        """
        self._ensure_drugs2diseases_loaded()
        
        matching_drugs = []
        for drug_id, drug_data in self._drugs2diseases.items():
            if drug_data.get('status') == status:
                matching_drugs.append(drug_data)
        
        return matching_drugs
    
    def search_drugs_by_manufacturer(self, manufacturer: str) -> List[Dict]:
        """
        Search drugs by manufacturer name
        
        Args:
            manufacturer: Manufacturer name to search for
            
        Returns:
            List of matching drug dictionaries
        """
        self._ensure_drugs2diseases_loaded()
        
        manufacturer_lower = manufacturer.lower()
        matching_drugs = []
        
        for drug_id, drug_data in self._drugs2diseases.items():
            drug_manufacturer = str(drug_data.get('manufacturer', '')).lower()
            if manufacturer_lower in drug_manufacturer:
                matching_drugs.append(drug_data)
        
        return matching_drugs
    
    def search_drugs_by_name(self, query: str) -> List[Dict]:
        """
        Search drugs by name (case-insensitive partial match)
        
        Args:
            query: Search query
            
        Returns:
            List of matching drug entries
        """
        self._ensure_drugs2diseases_loaded()
        
        query_lower = query.lower()
        matching_drugs = []
        
        for drug_id, drug_data in self._drugs2diseases.items():
            drug_name = drug_data.get('drug_name', '').lower()
            if query_lower in drug_name:
                matching_drugs.append(drug_data)
        
        return matching_drugs
    
    def search_drugs_by_region(self, region: str) -> List[Dict]:
        """
        Search drugs by region/country
        
        Args:
            region: Region code to search for (e.g., 'EU', 'US')
            
        Returns:
            List of matching drug dictionaries
        """
        self._ensure_drugs2diseases_loaded()
        
        matching_drugs = []
        for drug_id, drug_data in self._drugs2diseases.items():
            regions = drug_data.get('regions', [])
            if region in regions:
                matching_drugs.append(drug_data)
        
        return matching_drugs
    
    def search_diseases_by_name(self, query: str) -> List[Dict]:
        """
        Search diseases by name (case-insensitive partial match)
        
        Args:
            query: Search query
            
        Returns:
            List of matching disease entries
        """
        self._ensure_diseases2drugs_loaded()
        
        query_lower = query.lower()
        matching_diseases = []
        
        for orpha_code, disease_data in self._diseases2drugs.items():
            disease_name = disease_data.get('disease_name', '').lower()
            if query_lower in disease_name:
                matching_diseases.append(disease_data)
        
        return matching_diseases
    
    def search_approved_drugs(self) -> List[Dict]:
        """
        Get all approved drugs (medicinal products)
        
        Returns:
            List of approved drug dictionaries
        """
        return self.search_drugs_by_status('Medicinal product')
    
    def search_investigational_drugs(self) -> List[Dict]:
        """
        Get all investigational drugs
        
        Returns:
            List of investigational drug dictionaries
        """
        return self.search_drugs_by_status('Investigational')
    
    # ========== Statistics and Analysis ==========
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about drug data
        
        Returns:
            Dictionary with statistics
        """
        self._ensure_processing_summary_loaded()
        self._ensure_diseases2drugs_loaded()
        self._ensure_drugs2diseases_loaded()
        
        stats = self._processing_summary.copy() if self._processing_summary else {}
        
        # Add runtime statistics
        if self._drugs2diseases:
            status_counts = {}
            manufacturer_counts = {}
            region_counts = {}
            
            for drug_data in self._drugs2diseases.values():
                # Count by status
                status = drug_data.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by manufacturer
                manufacturer = drug_data.get('manufacturer', 'Unknown')
                if manufacturer and manufacturer != 'Unknown':
                    manufacturer_counts[manufacturer] = manufacturer_counts.get(manufacturer, 0) + 1
                
                # Count by regions
                regions = drug_data.get('regions', [])
                for region in regions:
                    region_counts[region] = region_counts.get(region, 0) + 1
            
            stats.update({
                "runtime_stats": {
                    "drugs_by_status": status_counts,
                    "drugs_by_manufacturer": manufacturer_counts,
                    "drugs_by_region": region_counts,
                    "data_loaded_at": datetime.now().isoformat()
                }
            })
        
        return stats
    
    def get_diseases_with_most_drugs(self, limit: int = 10) -> List[Dict]:
        """
        Get diseases with the most drugs
        
        Args:
            limit: Maximum number of diseases to return
            
        Returns:
            List of disease entries sorted by drug count
        """
        self._ensure_diseases2drugs_loaded()
        
        diseases_list = list(self._diseases2drugs.values())
        diseases_list.sort(key=lambda d: d.get('drugs_count', 0), reverse=True)
        
        return diseases_list[:limit]
    
    def get_manufacturers_with_most_drugs(self, limit: int = 10) -> List[Dict]:
        """
        Get manufacturers with the most drugs
        
        Args:
            limit: Maximum number of manufacturers to return
            
        Returns:
            List of manufacturer entries with drug counts
        """
        self._ensure_drugs2diseases_loaded()
        
        manufacturer_counts = {}
        for drug_data in self._drugs2diseases.values():
            manufacturer = drug_data.get('manufacturer', 'Unknown')
            if manufacturer and manufacturer != 'Unknown':
                if manufacturer not in manufacturer_counts:
                    manufacturer_counts[manufacturer] = {
                        'manufacturer': manufacturer,
                        'drug_count': 0,
                        'drugs': []
                    }
                manufacturer_counts[manufacturer]['drug_count'] += 1
                manufacturer_counts[manufacturer]['drugs'].append(drug_data.get('drug_name', 'Unknown'))
        
        manufacturers_list = list(manufacturer_counts.values())
        manufacturers_list.sort(key=lambda m: m['drug_count'], reverse=True)
        
        return manufacturers_list[:limit]
    
    # ========== Utility Methods ==========
    
    def clear_cache(self):
        """Clear all cached data to free memory"""
        self._diseases2drugs = None
        self._drugs2diseases = None
        self._drug_index = None
        self._processing_summary = None
        self._cache.clear()
        logger.info("Processed drug client cache cleared")
    
    def preload_all(self):
        """Preload all data for better performance"""
        self._ensure_diseases2drugs_loaded()
        self._ensure_drugs2diseases_loaded()
        self._ensure_drug_index_loaded()
        self._ensure_processing_summary_loaded()
        logger.info("All drug data preloaded")
    
    def is_data_available(self) -> bool:
        """Check if drug data is available"""
        required_files = [
            "diseases2drugs.json",
            "drugs2diseases.json",
            "drug_index.json"
        ]
        
        for filename in required_files:
            if not (self.data_dir / filename).exists():
                return False
        
        return True
    
    @lru_cache(maxsize=100)
    def _get_disease_cached(self, orpha_code: str) -> Optional[Dict]:
        """Cached version of disease lookup"""
        return self.get_disease_drug_summary(orpha_code)


# Example usage and testing
def main():
    """Example usage of the ProcessedDrugClient"""
    
    controller = ProcessedDrugClient()
    
    if not controller.is_data_available():
        print("Drug data not available. Run aggregate_drug_data.py first.")
        return
    
    # Get statistics
    stats = controller.get_statistics()
    print(f"Drug Statistics:")
    print(f"- Total diseases processed: {stats.get('total_diseases_processed', 'N/A')}")
    print(f"- Diseases with drugs: {stats.get('diseases_with_drugs', 'N/A')}")
    print(f"- Total unique drugs: {stats.get('total_unique_drugs', 'N/A')}")
    
    # Get diseases with most drugs
    top_diseases = controller.get_diseases_with_most_drugs(5)
    print(f"\nTop 5 diseases by drug count:")
    for disease in top_diseases:
        print(f"- {disease['disease_name']}: {disease['drugs_count']} drugs")
    
    # Get manufacturers with most drugs
    top_manufacturers = controller.get_manufacturers_with_most_drugs(5)
    print(f"\nTop 5 manufacturers by drug count:")
    for manufacturer in top_manufacturers:
        print(f"- {manufacturer['manufacturer']}: {manufacturer['drug_count']} drugs")
    
    # Search approved drugs
    approved_drugs = controller.search_approved_drugs()
    print(f"\nApproved drugs: {len(approved_drugs)}")
    
    # Example disease lookup
    if top_diseases:
        example_code = top_diseases[0]['orpha_code']
        drugs = controller.get_drugs_for_disease(example_code)
        print(f"\nDrugs for {top_diseases[0]['disease_name']} ({example_code}): {len(drugs)}")


if __name__ == "__main__":
    main() 