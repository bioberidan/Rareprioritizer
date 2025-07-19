# Continuacion de clinical trials, to be cleaned and merged
"""
Processed Clinical Trials Client - Query interface for clinical trials data

This module provides a OrphaTaxonomy-style interface for querying clinical trials data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)


class ProcessedClinicalTrialsClient:
    """Client for processed clinical trials data with lazy loading and query capabilities"""
    
    def __init__(self, data_dir: str = "data/processed/clinical_trials"):
        """
        Initialize the processed clinical trials client
        
        Args:
            data_dir: Directory containing processed clinical trials data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Clinical trials data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._diseases2trials: Optional[Dict] = None
        self._trials2diseases: Optional[Dict] = None
        self._trials_index: Optional[Dict] = None
        self._processing_summary: Optional[Dict] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        logger.info(f"Processed clinical trials client initialized with data dir: {data_dir}")
    
    def _ensure_diseases2trials_loaded(self):
        """Load diseases to trials mapping if not already loaded"""
        if self._diseases2trials is None:
            file_path = self.data_dir / "diseases2clinical_trials.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._diseases2trials = json.load(f)
                logger.info(f"Loaded diseases2trials mapping: {len(self._diseases2trials)} diseases")
            else:
                self._diseases2trials = {}
                logger.warning("diseases2clinical_trials.json not found")
    
    def _ensure_trials2diseases_loaded(self):
        """Load trials to diseases mapping if not already loaded"""
        if self._trials2diseases is None:
            file_path = self.data_dir / "clinical_trials2diseases.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._trials2diseases = json.load(f)
                logger.info(f"Loaded trials2diseases mapping: {len(self._trials2diseases)} trials")
            else:
                self._trials2diseases = {}
                logger.warning("clinical_trials2diseases.json not found")
    
    def _ensure_trials_index_loaded(self):
        """Load clinical trials index if not already loaded"""
        if self._trials_index is None:
            file_path = self.data_dir / "clinical_trials_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._trials_index = json.load(f)
                logger.info(f"Loaded trials index: {len(self._trials_index)} trials")
            else:
                self._trials_index = {}
                logger.warning("clinical_trials_index.json not found")
    
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
    
    def get_trials_for_disease(self, orpha_code: str) -> List[Dict]:
        """
        Get all clinical trials for a specific disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            List of trial dictionaries
        """
        self._ensure_diseases2trials_loaded()
        self._ensure_trials_index_loaded()
        
        disease_data = self._diseases2trials.get(orpha_code)
        if not disease_data:
            return []
        
        trials = []
        for nct_id in disease_data.get('trials', []):
            trial_details = self._trials_index.get(nct_id)
            if trial_details:
                trials.append(trial_details)
        
        return trials
    
    def get_diseases_for_trial(self, nct_id: str) -> List[Dict]:
        """
        Get all diseases associated with a clinical trial
        
        Args:
            nct_id: NCT ID of the clinical trial
            
        Returns:
            List of disease dictionaries
        """
        self._ensure_trials2diseases_loaded()
        
        trial_data = self._trials2diseases.get(nct_id)
        if not trial_data:
            return []
        
        return trial_data.get('diseases', [])
    
    def get_trial_details(self, nct_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific trial
        
        Args:
            nct_id: NCT ID of the clinical trial
            
        Returns:
            Trial dictionary or None if not found
        """
        self._ensure_trials_index_loaded()
        return self._trials_index.get(nct_id)
    
    def get_disease_trial_summary(self, orpha_code: str) -> Optional[Dict]:
        """
        Get summary information about trials for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Summary dictionary or None if not found
        """
        self._ensure_diseases2trials_loaded()
        return self._diseases2trials.get(orpha_code)
    
    # ========== Search and Filter Methods ==========
    
    def search_trials_by_status(self, status: str) -> List[Dict]:
        """
        Search trials by overall status
        
        Args:
            status: Trial status (e.g., 'RECRUITING', 'ACTIVE_NOT_RECRUITING')
            
        Returns:
            List of matching trial dictionaries
        """
        self._ensure_trials2diseases_loaded()
        
        matching_trials = []
        for nct_id, trial_data in self._trials2diseases.items():
            if trial_data.get('overall_status') == status:
                matching_trials.append(trial_data)
        
        return matching_trials
    
    def search_trials_by_location(self, country: str) -> List[Dict]:
        """
        Search trials by location/country
        
        Args:
            country: Country name to search for
            
        Returns:
            List of matching trial dictionaries
        """
        self._ensure_trials_index_loaded()
        
        matching_trials = []
        country_lower = country.lower()
        
        for nct_id, trial_details in self._trials_index.items():
            locations = trial_details.get('locations', [])
            for location in locations:
                if country_lower in str(location.get('country', '')).lower():
                    matching_trials.append(trial_details)
                    break
        
        return matching_trials
    
    def search_trials_in_spain(self) -> List[Dict]:
        """
        Get all trials with locations in Spain
        
        Returns:
            List of trials with Spanish locations
        """
        self._ensure_trials2diseases_loaded()
        
        spanish_trials = []
        for nct_id, trial_data in self._trials2diseases.items():
            if trial_data.get('locations_spain', False):
                spanish_trials.append(trial_data)
        
        return spanish_trials
    
    def search_diseases_by_name(self, query: str) -> List[Dict]:
        """
        Search diseases by name (case-insensitive partial match)
        
        Args:
            query: Search query
            
        Returns:
            List of matching disease entries
        """
        self._ensure_diseases2trials_loaded()
        
        query_lower = query.lower()
        matching_diseases = []
        
        for orpha_code, disease_data in self._diseases2trials.items():
            disease_name = disease_data.get('disease_name', '').lower()
            if query_lower in disease_name:
                matching_diseases.append(disease_data)
        
        return matching_diseases
    
    def search_trials_by_intervention(self, intervention_name: str) -> List[Dict]:
        """
        Search trials by intervention/drug name
        
        Args:
            intervention_name: Name of intervention to search for
            
        Returns:
            List of matching trial dictionaries
        """
        self._ensure_trials_index_loaded()
        
        intervention_lower = intervention_name.lower()
        matching_trials = []
        
        for nct_id, trial_details in self._trials_index.items():
            interventions = trial_details.get('interventions', [])
            for intervention in interventions:
                intervention_name_field = str(intervention.get('name', '')).lower()
                if intervention_lower in intervention_name_field:
                    matching_trials.append(trial_details)
                    break
        
        return matching_trials
    
    # ========== Statistics and Analysis ==========
    
    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about clinical trials data
        
        Returns:
            Dictionary with statistics
        """
        self._ensure_processing_summary_loaded()
        self._ensure_diseases2trials_loaded()
        self._ensure_trials2diseases_loaded()
        
        stats = self._processing_summary.copy() if self._processing_summary else {}
        
        # Add runtime statistics
        if self._trials2diseases:
            status_counts = {}
            phase_counts = {}
            spain_trials = 0
            
            for trial_data in self._trials2diseases.values():
                # Count by status
                status = trial_data.get('overall_status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count trials in Spain
                if trial_data.get('locations_spain', False):
                    spain_trials += 1
            
            stats.update({
                "runtime_stats": {
                    "trials_by_status": status_counts,
                    "trials_in_spain": spain_trials,
                    "data_loaded_at": datetime.now().isoformat()
                }
            })
        
        return stats
    
    def get_diseases_with_most_trials(self, limit: int = 10) -> List[Dict]:
        """
        Get diseases with the most clinical trials
        
        Args:
            limit: Maximum number of diseases to return
            
        Returns:
            List of disease entries sorted by trial count
        """
        self._ensure_diseases2trials_loaded()
        
        diseases_list = list(self._diseases2trials.values())
        diseases_list.sort(key=lambda d: d.get('trials_count', 0), reverse=True)
        
        return diseases_list[:limit]
    
    def get_trials_by_phase(self, phase: str) -> List[Dict]:
        """
        Get trials by study phase
        
        Args:
            phase: Study phase (e.g., 'PHASE1', 'PHASE2', 'PHASE3')
            
        Returns:
            List of matching trial dictionaries
        """
        self._ensure_trials_index_loaded()
        
        matching_trials = []
        for nct_id, trial_details in self._trials_index.items():
            phases = trial_details.get('phases', [])
            if phase in phases:
                matching_trials.append(trial_details)
        
        return matching_trials
    
    # ========== Utility Methods ==========
    
    def clear_cache(self):
        """Clear all cached data to free memory"""
        self._diseases2trials = None
        self._trials2diseases = None
        self._trials_index = None
        self._processing_summary = None
        self._cache.clear()
        logger.info("Processed clinical trials client cache cleared")
    
    def preload_all(self):
        """Preload all data for better performance"""
        self._ensure_diseases2trials_loaded()
        self._ensure_trials2diseases_loaded()
        self._ensure_trials_index_loaded()
        self._ensure_processing_summary_loaded()
        logger.info("All clinical trials data preloaded")
    
    def is_data_available(self) -> bool:
        """Check if clinical trials data is available"""
        required_files = [
            "diseases2clinical_trials.json",
            "clinical_trials2diseases.json",
            "clinical_trials_index.json"
        ]
        
        for filename in required_files:
            if not (self.data_dir / filename).exists():
                return False
        
        return True
    
    @lru_cache(maxsize=100)
    def _get_disease_cached(self, orpha_code: str) -> Optional[Dict]:
        """Cached version of disease lookup"""
        return self.get_disease_trial_summary(orpha_code)


# Example usage and testing
def main():
    """Example usage of the ProcessedClinicalTrialsClient"""
    
    controller = ProcessedClinicalTrialsClient()
    
    if not controller.is_data_available():
        print("Clinical trials data not available. Run aggregate_clinical_trials.py first.")
        return
    
    # Get statistics
    stats = controller.get_statistics()
    print(f"Clinical Trials Statistics:")
    print(f"- Total diseases processed: {stats.get('total_diseases_processed', 'N/A')}")
    print(f"- Diseases with trials: {stats.get('diseases_with_trials', 'N/A')}")
    print(f"- Total unique trials: {stats.get('total_unique_trials', 'N/A')}")
    
    # Get diseases with most trials
    top_diseases = controller.get_diseases_with_most_trials(5)
    print(f"\nTop 5 diseases by trial count:")
    for disease in top_diseases:
        print(f"- {disease['disease_name']}: {disease['trials_count']} trials")
    
    # Search trials in Spain
    spanish_trials = controller.search_trials_in_spain()
    print(f"\nTrials in Spain: {len(spanish_trials)}")
    
    # Example disease lookup
    if top_diseases:
        example_code = top_diseases[0]['orpha_code']
        trials = controller.get_trials_for_disease(example_code)
        print(f"\nTrials for {top_diseases[0]['disease_name']} ({example_code}): {len(trials)}")


if __name__ == "__main__":
    main() 