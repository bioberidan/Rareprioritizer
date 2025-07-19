"""
Curated Clinical Trials Client - Query interface for curated clinical trials data

This module provides a high-performance interface for querying curated clinical trials data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class CuratedClinicalTrialsClient:
    """
    Client for accessing curated clinical trials data with lazy loading and caching
    
    This client provides access to the curated trial data files:
    - disease2eu_trial.json: EU-accessible trials per disease
    - disease2all_trials.json: All trials per disease
    - disease2spanish_trials.json: Spanish-accessible trials per disease
    - clinicaltrial2name.json: Trial ID to name mapping
    """
    
    def __init__(self, data_dir: str = "data/04_curated/clinical_trials"):
        """
        Initialize the curated clinical trials client
        
        Args:
            data_dir: Directory containing curated clinical trials data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Curated trials data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._eu_trials: Optional[Dict[str, List[str]]] = None
        self._all_trials: Optional[Dict[str, List[str]]] = None
        self._spanish_trials: Optional[Dict[str, List[str]]] = None
        self._trial_names: Optional[Dict[str, str]] = None
        
        logger.info(f"Initialized CuratedClinicalTrialsClient with data dir: {data_dir}")
    
    def _load_eu_trials_data(self) -> Dict[str, List[str]]:
        """Load EU trials data with lazy loading"""
        if self._eu_trials is None:
            file_path = self.data_dir / "disease2eu_trial.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._eu_trials = json.load(f)
                logger.info(f"Loaded EU trials data: {len(self._eu_trials)} diseases")
            else:
                self._eu_trials = {}
                logger.warning("EU trials file not found")
        return self._eu_trials
    
    def _load_all_trials_data(self) -> Dict[str, List[str]]:
        """Load all trials data with lazy loading"""
        if self._all_trials is None:
            file_path = self.data_dir / "disease2all_trials.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._all_trials = json.load(f)
                logger.info(f"Loaded all trials data: {len(self._all_trials)} diseases")
            else:
                self._all_trials = {}
                logger.warning("All trials file not found")
        return self._all_trials
    
    def _load_spanish_trials_data(self) -> Dict[str, List[str]]:
        """Load Spanish trials data with lazy loading"""
        if self._spanish_trials is None:
            file_path = self.data_dir / "disease2spanish_trials.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._spanish_trials = json.load(f)
                logger.info(f"Loaded Spanish trials data: {len(self._spanish_trials)} diseases")
            else:
                self._spanish_trials = {}
                logger.warning("Spanish trials file not found")
        return self._spanish_trials
    
    def _load_trial_names_data(self) -> Dict[str, str]:
        """Load trial names data with lazy loading"""
        if self._trial_names is None:
            file_path = self.data_dir / "clinicaltrial2name.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._trial_names = json.load(f)
                logger.info(f"Loaded trial names data: {len(self._trial_names)} trials")
            else:
                self._trial_names = {}
                logger.warning("Trial names file not found")
        return self._trial_names
    
    @lru_cache(maxsize=1000)
    def get_eu_trials_for_disease(self, orpha_code: str) -> List[str]:
        """
        Get EU-accessible trials for disease
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            List of NCT IDs for EU-accessible trials
        """
        eu_trials = self._load_eu_trials_data()
        return eu_trials.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_all_trials_for_disease(self, orpha_code: str) -> List[str]:
        """
        Get all trials for disease
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            List of all NCT IDs for the disease
        """
        all_trials = self._load_all_trials_data()
        return all_trials.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_spanish_trials_for_disease(self, orpha_code: str) -> List[str]:
        """
        Get Spanish-accessible trials for disease
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            List of NCT IDs for Spanish-accessible trials
        """
        spanish_trials = self._load_spanish_trials_data()
        return spanish_trials.get(orpha_code, [])
    
    @lru_cache(maxsize=1000)
    def get_trial_name(self, nct_id: str) -> str:
        """
        Get trial title/name
        
        Args:
            nct_id: Trial NCT identifier
            
        Returns:
            Trial title or default name if not found
        """
        trial_names = self._load_trial_names_data()
        return trial_names.get(nct_id, f"Clinical Trial {nct_id}")
    
    def get_diseases_with_eu_trials(self) -> List[str]:
        """
        Get diseases that have EU-accessible trials
        
        Returns:
            List of disease Orpha codes
        """
        eu_trials = self._load_eu_trials_data()
        return list(eu_trials.keys())
    
    def get_diseases_with_all_trials(self) -> List[str]:
        """
        Get diseases that have any trials
        
        Returns:
            List of disease Orpha codes
        """
        all_trials = self._load_all_trials_data()
        return list(all_trials.keys())
    
    def get_diseases_with_spanish_trials(self) -> List[str]:
        """
        Get diseases that have Spanish-accessible trials
        
        Returns:
            List of disease Orpha codes
        """
        spanish_trials = self._load_spanish_trials_data()
        return list(spanish_trials.keys())
    
    def has_trials(self, orpha_code: str) -> bool:
        """
        Check if disease has any trials
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            True if disease has trials
        """
        return len(self.get_all_trials_for_disease(orpha_code)) > 0
    
    def has_eu_trials(self, orpha_code: str) -> bool:
        """
        Check if disease has EU-accessible trials
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            True if disease has EU trials
        """
        return len(self.get_eu_trials_for_disease(orpha_code)) > 0
    
    def has_spanish_trials(self, orpha_code: str) -> bool:
        """
        Check if disease has Spanish-accessible trials
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            True if disease has Spanish trials
        """
        return len(self.get_spanish_trials_for_disease(orpha_code)) > 0
    
    def get_trial_names_for_disease(self, orpha_code: str, region: str = "all") -> Dict[str, str]:
        """
        Get trial NCT IDs and names for disease
        
        Args:
            orpha_code: Disease Orphanet code
            region: Region filter ("all", "eu", "spanish")
            
        Returns:
            Dict mapping NCT IDs to trial names
        """
        if region.lower() == "eu":
            trial_ids = self.get_eu_trials_for_disease(orpha_code)
        elif region.lower() == "spanish":
            trial_ids = self.get_spanish_trials_for_disease(orpha_code)
        else:
            trial_ids = self.get_all_trials_for_disease(orpha_code)
        
        return {
            nct_id: self.get_trial_name(nct_id)
            for nct_id in trial_ids
        }
    
    def get_diseases_with_multiple_trials(self, min_trials: int = 2, region: str = "all") -> List[Dict[str, any]]:
        """
        Get diseases with multiple trials
        
        Args:
            min_trials: Minimum number of trials
            region: Region filter ("all", "eu", "spanish")
            
        Returns:
            List of dicts with disease info and trial counts
        """
        if region.lower() == "eu":
            trials_data = self._load_eu_trials_data()
        elif region.lower() == "spanish":
            trials_data = self._load_spanish_trials_data()
        else:
            trials_data = self._load_all_trials_data()
        
        result = []
        for orpha_code, trials in trials_data.items():
            if len(trials) >= min_trials:
                result.append({
                    "orpha_code": orpha_code,
                    "trials": trials,
                    "trial_count": len(trials),
                    "region": region
                })
        
        # Sort by trial count descending
        result.sort(key=lambda x: x["trial_count"], reverse=True)
        return result
    
    def get_most_common_trials(self, limit: int = 15) -> List[Dict[str, any]]:
        """
        Get trials that appear across multiple diseases
        
        Args:
            limit: Maximum number of trials to return
            
        Returns:
            List of dicts with trial info and disease counts
        """
        all_trials = self._load_all_trials_data()
        trial_names = self._load_trial_names_data()
        
        # Count diseases per trial
        trial_disease_count = {}
        for orpha_code, trials in all_trials.items():
            for nct_id in trials:
                if nct_id not in trial_disease_count:
                    trial_disease_count[nct_id] = []
                trial_disease_count[nct_id].append(orpha_code)
        
        # Create result list
        result = []
        for nct_id, diseases in trial_disease_count.items():
            result.append({
                "nct_id": nct_id,
                "trial_name": trial_names.get(nct_id, f"Clinical Trial {nct_id}"),
                "diseases": diseases,
                "disease_count": len(diseases)
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
        all_trials = self._load_all_trials_data()
        eu_trials = self._load_eu_trials_data()
        spanish_trials = self._load_spanish_trials_data()
        trial_names = self._load_trial_names_data()
        
        # Calculate statistics
        total_diseases_with_trials = len(all_trials)
        total_unique_trials = len(trial_names)
        total_trial_disease_pairs = sum(len(trials) for trials in all_trials.values())
        
        diseases_with_eu_trials = len(eu_trials)
        diseases_with_spanish_trials = len(spanish_trials)
        
        eu_trial_disease_pairs = sum(len(trials) for trials in eu_trials.values())
        spanish_trial_disease_pairs = sum(len(trials) for trials in spanish_trials.values())
        
        return {
            "total_diseases_with_trials": total_diseases_with_trials,
            "diseases_with_eu_trials": diseases_with_eu_trials,
            "diseases_with_spanish_trials": diseases_with_spanish_trials,
            "total_unique_trials": total_unique_trials,
            "total_trial_disease_pairs": total_trial_disease_pairs,
            "eu_trial_disease_pairs": eu_trial_disease_pairs,
            "spanish_trial_disease_pairs": spanish_trial_disease_pairs,
            "average_trials_per_disease": total_trial_disease_pairs / total_diseases_with_trials if total_diseases_with_trials > 0 else 0,
            "eu_coverage_percentage": (diseases_with_eu_trials / total_diseases_with_trials * 100) if total_diseases_with_trials > 0 else 0,
            "spanish_coverage_percentage": (diseases_with_spanish_trials / total_diseases_with_trials * 100) if total_diseases_with_trials > 0 else 0,
            "data_sources": {
                "eu_trials_file": str(self.data_dir / "disease2eu_trial.json"),
                "all_trials_file": str(self.data_dir / "disease2all_trials.json"),
                "spanish_trials_file": str(self.data_dir / "disease2spanish_trials.json"),
                "trial_names_file": str(self.data_dir / "clinicaltrial2name.json")
            }
        }
    
    def export_to_csv(self, output_file: str, region: str = "all", include_trial_names: bool = True) -> None:
        """
        Export trial data to CSV format
        
        Args:
            output_file: Output CSV file path
            region: Region filter ("all", "eu", "spanish")
            include_trial_names: Whether to include trial names
        """
        import csv
        
        if region.lower() == "eu":
            trials_data = self._load_eu_trials_data()
        elif region.lower() == "spanish":
            trials_data = self._load_spanish_trials_data()
        else:
            trials_data = self._load_all_trials_data()
        
        trial_names = self._load_trial_names_data() if include_trial_names else {}
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            if include_trial_names:
                fieldnames = ['orpha_code', 'nct_id', 'trial_name']
            else:
                fieldnames = ['orpha_code', 'nct_id']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for orpha_code, trials in trials_data.items():
                for nct_id in trials:
                    row = {
                        'orpha_code': orpha_code,
                        'nct_id': nct_id
                    }
                    if include_trial_names:
                        row['trial_name'] = trial_names.get(nct_id, f"Clinical Trial {nct_id}")
                    
                    writer.writerow(row)
        
        logger.info(f"Exported {region} trials data to CSV: {output_file}")


# Convenience function for quick access
def get_curated_clinical_trials_client() -> CuratedClinicalTrialsClient:
    """
    Get a configured CuratedClinicalTrialsClient instance
    
    Returns:
        Configured client instance
    """
    return CuratedClinicalTrialsClient() 