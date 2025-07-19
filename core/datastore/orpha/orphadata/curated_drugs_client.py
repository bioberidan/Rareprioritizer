"""
Curated Drugs Client - Query interface for curated Orpha drugs data

This module provides a high-performance interface for querying curated Orpha drugs data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class CuratedDrugsClient:
    """
    Client for accessing curated Orpha drugs data with lazy loading and caching
    
    This client provides access to the curated drug data files:
    - disease2eu_tradename_drugs.json: EU-accessible tradename drugs per disease
    - disease2all_tradename_drugs.json: All tradename drugs per disease
    - disease2usa_tradename_drugs.json: USA-accessible tradename drugs per disease
    - disease2eu_medical_product_drugs.json: EU-accessible medical products per disease
    - disease2all_medical_product_drugs.json: All medical products per disease  
    - disease2usa_medical_product_drugs.json: USA-accessible medical products per disease
    - drug2name.json: Drug ID to name mapping
    """
    
    def __init__(self, data_dir: str = "data/04_curated/orpha/orphadata"):
        """
        Initialize the curated drugs client
        
        Args:
            data_dir: Directory containing curated drugs data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Curated drugs data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._eu_tradename_drugs: Optional[Dict[str, List[str]]] = None
        self._all_tradename_drugs: Optional[Dict[str, List[str]]] = None
        self._usa_tradename_drugs: Optional[Dict[str, List[str]]] = None
        self._eu_medical_products: Optional[Dict[str, List[str]]] = None
        self._all_medical_products: Optional[Dict[str, List[str]]] = None
        self._usa_medical_products: Optional[Dict[str, List[str]]] = None
        self._drug_names: Optional[Dict[str, str]] = None
        
        logger.info(f"Initialized CuratedDrugsClient with data dir: {data_dir}")
    
    def _load_eu_tradename_drugs_data(self) -> Dict[str, List[str]]:
        """Load EU tradename drugs data with lazy loading"""
        if self._eu_tradename_drugs is None:
            file_path = self.data_dir / "disease2eu_tradename_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._eu_tradename_drugs = json.load(f)
                logger.info(f"Loaded EU tradename drugs data: {len(self._eu_tradename_drugs)} diseases")
            else:
                self._eu_tradename_drugs = {}
                logger.warning("EU tradename drugs file not found")
        return self._eu_tradename_drugs
    
    def _load_all_tradename_drugs_data(self) -> Dict[str, List[str]]:
        """Load all tradename drugs data with lazy loading"""
        if self._all_tradename_drugs is None:
            file_path = self.data_dir / "disease2all_tradename_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._all_tradename_drugs = json.load(f)
                logger.info(f"Loaded all tradename drugs data: {len(self._all_tradename_drugs)} diseases")
            else:
                self._all_tradename_drugs = {}
                logger.warning("All tradename drugs file not found")
        return self._all_tradename_drugs
    
    def _load_usa_tradename_drugs_data(self) -> Dict[str, List[str]]:
        """Load USA tradename drugs data with lazy loading"""
        if self._usa_tradename_drugs is None:
            file_path = self.data_dir / "disease2usa_tradename_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._usa_tradename_drugs = json.load(f)
                logger.info(f"Loaded USA tradename drugs data: {len(self._usa_tradename_drugs)} diseases")
            else:
                self._usa_tradename_drugs = {}
                logger.warning("USA tradename drugs file not found")
        return self._usa_tradename_drugs
    
    def _load_eu_medical_products_data(self) -> Dict[str, List[str]]:
        """Load EU medical products data with lazy loading"""
        if self._eu_medical_products is None:
            file_path = self.data_dir / "disease2eu_medical_product_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._eu_medical_products = json.load(f)
                logger.info(f"Loaded EU medical products data: {len(self._eu_medical_products)} diseases")
            else:
                self._eu_medical_products = {}
                logger.warning("EU medical products file not found")
        return self._eu_medical_products
    
    def _load_all_medical_products_data(self) -> Dict[str, List[str]]:
        """Load all medical products data with lazy loading"""
        if self._all_medical_products is None:
            file_path = self.data_dir / "disease2all_medical_product_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._all_medical_products = json.load(f)
                logger.info(f"Loaded all medical products data: {len(self._all_medical_products)} diseases")
            else:
                self._all_medical_products = {}
                logger.warning("All medical products file not found")
        return self._all_medical_products
    
    def _load_usa_medical_products_data(self) -> Dict[str, List[str]]:
        """Load USA medical products data with lazy loading"""
        if self._usa_medical_products is None:
            file_path = self.data_dir / "disease2usa_medical_product_drugs.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._usa_medical_products = json.load(f)
                logger.info(f"Loaded USA medical products data: {len(self._usa_medical_products)} diseases")
            else:
                self._usa_medical_products = {}
                logger.warning("USA medical products file not found")
        return self._usa_medical_products
    
    def _load_drug_names_data(self) -> Dict[str, str]:
        """Load drug names data with lazy loading"""
        if self._drug_names is None:
            file_path = self.data_dir / "drug2name.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._drug_names = json.load(f)
                logger.info(f"Loaded drug names data: {len(self._drug_names)} drugs")
            else:
                self._drug_names = {}
                logger.warning("Drug names file not found")
        return self._drug_names
    
    # Tradename drugs methods
    @lru_cache(maxsize=1000)
    def get_eu_tradename_drugs_for_disease(self, orpha_code: str) -> List[str]:
        """Get EU-accessible tradename drugs for disease"""
        eu_tradename_drugs = self._load_eu_tradename_drugs_data()
        return eu_tradename_drugs.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_all_tradename_drugs_for_disease(self, orpha_code: str) -> List[str]:
        """Get all tradename drugs for disease"""
        all_tradename_drugs = self._load_all_tradename_drugs_data()
        return all_tradename_drugs.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_usa_tradename_drugs_for_disease(self, orpha_code: str) -> List[str]:
        """Get USA-accessible tradename drugs for disease"""
        usa_tradename_drugs = self._load_usa_tradename_drugs_data()
        return usa_tradename_drugs.get(orpha_code, [])
    
    # Medical products methods
    @lru_cache(maxsize=1000)
    def get_eu_medical_products_for_disease(self, orpha_code: str) -> List[str]:
        """Get EU-accessible medical products for disease"""
        eu_medical_products = self._load_eu_medical_products_data()
        return eu_medical_products.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_all_medical_products_for_disease(self, orpha_code: str) -> List[str]:
        """Get all medical products for disease"""
        all_medical_products = self._load_all_medical_products_data()
        return all_medical_products.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_usa_medical_products_for_disease(self, orpha_code: str) -> List[str]:
        """Get USA-accessible medical products for disease"""
        usa_medical_products = self._load_usa_medical_products_data()
        return usa_medical_products.get(orpha_code, [])
    
    # Combined methods
    def get_all_drugs_for_disease(self, orpha_code: str, region: str = "all", drug_type: str = "all") -> List[str]:
        """
        Get drugs for disease with filtering options
        
        Args:
            orpha_code: Disease Orphanet code
            region: Region filter ("all", "eu", "usa")
            drug_type: Drug type filter ("all", "tradename", "medical_product")
            
        Returns:
            List of drug IDs matching criteria
        """
        drugs = []
        
        if drug_type in ["all", "tradename"]:
            if region == "eu":
                drugs.extend(self.get_eu_tradename_drugs_for_disease(orpha_code))
            elif region == "usa":
                drugs.extend(self.get_usa_tradename_drugs_for_disease(orpha_code))
            else:
                drugs.extend(self.get_all_tradename_drugs_for_disease(orpha_code))
        
        if drug_type in ["all", "medical_product"]:
            if region == "eu":
                drugs.extend(self.get_eu_medical_products_for_disease(orpha_code))
            elif region == "usa":
                drugs.extend(self.get_usa_medical_products_for_disease(orpha_code))
            else:
                drugs.extend(self.get_all_medical_products_for_disease(orpha_code))
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(drugs))
    
    @lru_cache(maxsize=1000)
    def get_drug_name(self, drug_id: str) -> str:
        """
        Get drug name
        
        Args:
            drug_id: Drug identifier
            
        Returns:
            Drug name or default name if not found
        """
        drug_names = self._load_drug_names_data()
        return drug_names.get(drug_id, f"Drug {drug_id}")
    
    def get_drug_names_for_disease(self, orpha_code: str, region: str = "all", drug_type: str = "all") -> Dict[str, str]:
        """
        Get drug IDs and names for disease
        
        Args:
            orpha_code: Disease Orphanet code
            region: Region filter ("all", "eu", "usa")
            drug_type: Drug type filter ("all", "tradename", "medical_product")
            
        Returns:
            Dict mapping drug IDs to drug names
        """
        drug_ids = self.get_all_drugs_for_disease(orpha_code, region, drug_type)
        return {
            drug_id: self.get_drug_name(drug_id)
            for drug_id in drug_ids
        }
    
    # Disease listing methods
    def get_diseases_with_tradename_drugs(self, region: str = "all") -> List[str]:
        """Get diseases that have tradename drugs"""
        if region == "eu":
            data = self._load_eu_tradename_drugs_data()
        elif region == "usa":
            data = self._load_usa_tradename_drugs_data()
        else:
            data = self._load_all_tradename_drugs_data()
        return list(data.keys())
    
    def get_diseases_with_medical_products(self, region: str = "all") -> List[str]:
        """Get diseases that have medical products"""
        if region == "eu":
            data = self._load_eu_medical_products_data()
        elif region == "usa":
            data = self._load_usa_medical_products_data()
        else:
            data = self._load_all_medical_products_data()
        return list(data.keys())
    
    def get_diseases_with_any_drugs(self) -> List[str]:
        """Get all diseases that have any drugs"""
        all_diseases = set()
        all_diseases.update(self.get_diseases_with_tradename_drugs())
        all_diseases.update(self.get_diseases_with_medical_products())
        return list(all_diseases)
    
    # Analysis methods
    def has_drugs(self, orpha_code: str, region: str = "all", drug_type: str = "all") -> bool:
        """Check if disease has drugs matching criteria"""
        return len(self.get_all_drugs_for_disease(orpha_code, region, drug_type)) > 0
    
    def get_diseases_with_multiple_drugs(self, min_drugs: int = 2, region: str = "all", drug_type: str = "all") -> List[Dict[str, any]]:
        """
        Get diseases with multiple drugs
        
        Args:
            min_drugs: Minimum number of drugs
            region: Region filter ("all", "eu", "usa")
            drug_type: Drug type filter ("all", "tradename", "medical_product")
            
        Returns:
            List of dicts with disease info and drug counts
        """
        result = []
        
        # Get relevant diseases
        if drug_type == "tradename":
            diseases = self.get_diseases_with_tradename_drugs(region)
        elif drug_type == "medical_product":
            diseases = self.get_diseases_with_medical_products(region)
        else:
            diseases = self.get_diseases_with_any_drugs()
        
        for orpha_code in diseases:
            drugs = self.get_all_drugs_for_disease(orpha_code, region, drug_type)
            if len(drugs) >= min_drugs:
                result.append({
                    "orpha_code": orpha_code,
                    "drugs": drugs,
                    "drug_count": len(drugs),
                    "region": region,
                    "drug_type": drug_type
                })
        
        # Sort by drug count descending
        result.sort(key=lambda x: x["drug_count"], reverse=True)
        return result
    
    def get_most_common_drugs(self, limit: int = 15, drug_type: str = "all") -> List[Dict[str, any]]:
        """
        Get drugs that appear across multiple diseases
        
        Args:
            limit: Maximum number of drugs to return
            drug_type: Drug type filter ("all", "tradename", "medical_product")
            
        Returns:
            List of dicts with drug info and disease counts
        """
        drug_disease_count = {}
        
        # Count diseases per drug
        if drug_type in ["all", "tradename"]:
            all_tradename_drugs = self._load_all_tradename_drugs_data()
            for orpha_code, drugs in all_tradename_drugs.items():
                for drug_id in drugs:
                    if drug_id not in drug_disease_count:
                        drug_disease_count[drug_id] = []
                    drug_disease_count[drug_id].append(orpha_code)
        
        if drug_type in ["all", "medical_product"]:
            all_medical_products = self._load_all_medical_products_data()
            for orpha_code, drugs in all_medical_products.items():
                for drug_id in drugs:
                    if drug_id not in drug_disease_count:
                        drug_disease_count[drug_id] = []
                    drug_disease_count[drug_id].append(orpha_code)
        
        # Create result list
        result = []
        drug_names = self._load_drug_names_data()
        
        for drug_id, diseases in drug_disease_count.items():
            result.append({
                "drug_id": drug_id,
                "drug_name": drug_names.get(drug_id, f"Drug {drug_id}"),
                "diseases": list(set(diseases)),  # Remove duplicates
                "disease_count": len(set(diseases))
            })
        
        # Sort by disease count descending and limit
        result.sort(key=lambda x: x["disease_count"], reverse=True)
        return result[:limit]
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get comprehensive statistics
        
        Returns:
            Dict with statistics about the curated data
        """
        # Load all data
        eu_tradename_drugs = self._load_eu_tradename_drugs_data()
        all_tradename_drugs = self._load_all_tradename_drugs_data()
        usa_tradename_drugs = self._load_usa_tradename_drugs_data()
        eu_medical_products = self._load_eu_medical_products_data()
        all_medical_products = self._load_all_medical_products_data()
        usa_medical_products = self._load_usa_medical_products_data()
        drug_names = self._load_drug_names_data()
        
        # Calculate statistics
        total_diseases_with_drugs = len(set(
            list(all_tradename_drugs.keys()) + list(all_medical_products.keys())
        ))
        total_unique_drugs = len(drug_names)
        
        return {
            "total_diseases_with_drugs": total_diseases_with_drugs,
            "total_unique_drugs": total_unique_drugs,
            "tradename_drugs": {
                "diseases_with_eu_access": len(eu_tradename_drugs),
                "diseases_with_usa_access": len(usa_tradename_drugs),
                "diseases_with_any_access": len(all_tradename_drugs),
                "total_drug_disease_pairs": sum(len(drugs) for drugs in all_tradename_drugs.values())
            },
            "medical_products": {
                "diseases_with_eu_access": len(eu_medical_products),
                "diseases_with_usa_access": len(usa_medical_products),
                "diseases_with_any_access": len(all_medical_products),
                "total_drug_disease_pairs": sum(len(drugs) for drugs in all_medical_products.values())
            },
            "regional_coverage": {
                "eu_tradename_percentage": (len(eu_tradename_drugs) / total_diseases_with_drugs * 100) if total_diseases_with_drugs > 0 else 0,
                "usa_tradename_percentage": (len(usa_tradename_drugs) / total_diseases_with_drugs * 100) if total_diseases_with_drugs > 0 else 0,
                "eu_medical_product_percentage": (len(eu_medical_products) / total_diseases_with_drugs * 100) if total_diseases_with_drugs > 0 else 0,
                "usa_medical_product_percentage": (len(usa_medical_products) / total_diseases_with_drugs * 100) if total_diseases_with_drugs > 0 else 0
            },
            "data_sources": {
                "eu_tradename_file": str(self.data_dir / "disease2eu_tradename_drugs.json"),
                "all_tradename_file": str(self.data_dir / "disease2all_tradename_drugs.json"),
                "usa_tradename_file": str(self.data_dir / "disease2usa_tradename_drugs.json"),
                "eu_medical_product_file": str(self.data_dir / "disease2eu_medical_product_drugs.json"),
                "all_medical_product_file": str(self.data_dir / "disease2all_medical_product_drugs.json"),
                "usa_medical_product_file": str(self.data_dir / "disease2usa_medical_product_drugs.json"),
                "drug_names_file": str(self.data_dir / "drug2name.json")
            }
        }
    
    def export_to_csv(self, output_file: str, region: str = "all", drug_type: str = "all", include_drug_names: bool = True) -> None:
        """
        Export drug data to CSV format
        
        Args:
            output_file: Output CSV file path
            region: Region filter ("all", "eu", "usa")
            drug_type: Drug type filter ("all", "tradename", "medical_product")
            include_drug_names: Whether to include drug names
        """
        import csv
        
        # Get all relevant diseases
        if drug_type == "tradename":
            diseases = self.get_diseases_with_tradename_drugs(region)
        elif drug_type == "medical_product":
            diseases = self.get_diseases_with_medical_products(region)
        else:
            diseases = self.get_diseases_with_any_drugs()
        
        drug_names = self._load_drug_names_data() if include_drug_names else {}
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if include_drug_names:
                fieldnames = ['orpha_code', 'drug_id', 'drug_name', 'drug_type', 'region']
            else:
                fieldnames = ['orpha_code', 'drug_id', 'drug_type', 'region']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for orpha_code in diseases:
                drugs = self.get_all_drugs_for_disease(orpha_code, region, drug_type)
                for drug_id in drugs:
                    row = {
                        'orpha_code': orpha_code,
                        'drug_id': drug_id,
                        'drug_type': drug_type,
                        'region': region
                    }
                    if include_drug_names:
                        row['drug_name'] = drug_names.get(drug_id, f"Drug {drug_id}")
                    
                    writer.writerow(row)
        
        logger.info(f"Exported {region} {drug_type} drugs data to CSV: {output_file}")


# Convenience function for quick access
def get_curated_drugs_client() -> CuratedDrugsClient:
    """
    Get a configured CuratedDrugsClient instance
    
    Returns:
        Configured client instance
    """
    return CuratedDrugsClient() 