"""
Curated Websearch Socioeconomic Client - Query interface for curated websearch socioeconomic data

This module provides a simple interface for querying curated websearch socioeconomic data
with lazy loading and caching capabilities.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class CuratedWebsearchSocioeconomicClient:
    """
    Client for accessing curated websearch socioeconomic data with lazy loading and caching
    
    This client provides access to the curated websearch socioeconomic data files:
    - disease2socioeconomic_evidence_level.json: Evidence levels per disease mapping
    - disease2socioeconomic_justification.json: Justifications per disease mapping
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the client
        
        Args:
            data_dir: Directory containing curated socioeconomic data files
                     Defaults to data/04_curated/websearch/socioeconomic/
        """
        if data_dir is None:
            # Default to the standard curated data directory
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / "data" / "04_curated" / "websearch" / "socioeconomic"
        else:
            self.data_dir = Path(data_dir)
        
        self._evidence_level_data = None
        self._justification_data = None
        
        logger.debug(f"Initialized CuratedWebsearchSocioeconomicClient with data_dir: {self.data_dir}")
    
    @property
    def evidence_level_data(self) -> Dict[str, str]:
        """Lazy load evidence level data with caching"""
        if self._evidence_level_data is None:
            evidence_file = self.data_dir / "disease2socioeconomic_evidence_level.json"
            try:
                with open(evidence_file, 'r', encoding='utf-8') as f:
                    self._evidence_level_data = json.load(f)
                logger.debug(f"Loaded evidence level data for {len(self._evidence_level_data)} diseases")
            except FileNotFoundError:
                logger.error(f"Evidence level file not found: {evidence_file}")
                self._evidence_level_data = {}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing evidence level file: {e}")
                self._evidence_level_data = {}
        return self._evidence_level_data
    
    @property 
    def justification_data(self) -> Dict[str, str]:
        """Lazy load justification data with caching"""
        if self._justification_data is None:
            justification_file = self.data_dir / "disease2socioeconomic_justification.json"
            try:
                with open(justification_file, 'r', encoding='utf-8') as f:
                    self._justification_data = json.load(f)
                logger.debug(f"Loaded justification data for {len(self._justification_data)} diseases")
            except FileNotFoundError:
                logger.error(f"Justification file not found: {justification_file}")
                self._justification_data = {}
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing justification file: {e}")
                self._justification_data = {}
        return self._justification_data
    
    def get_evidence_level_for_disease(self, orpha_code: str) -> Optional[str]:
        """
        Get evidence level for a specific disease
        
        Args:
            orpha_code: ORPHA code of the disease
            
        Returns:
            Evidence level string or None if not found
        """
        return self.evidence_level_data.get(orpha_code)
    
    def get_justification_for_disease(self, orpha_code: str) -> Optional[str]:
        """
        Get justification for a specific disease
        
        Args:
            orpha_code: ORPHA code of the disease
            
        Returns:
            Justification string or None if not found
        """
        return self.justification_data.get(orpha_code)
    
    def get_evidence_level_distribution(self) -> Dict[str, int]:
        """
        Get distribution of evidence levels across all diseases
        
        Returns:
            Dictionary mapping evidence levels to counts
        """
        distribution = {}
        for evidence_level in self.evidence_level_data.values():
            distribution[evidence_level] = distribution.get(evidence_level, 0) + 1
        
        logger.debug(f"Evidence level distribution: {distribution}")
        return distribution
    
    def get_total_diseases(self) -> int:
        """
        Get total number of diseases with evidence data
        
        Returns:
            Total count of diseases
        """
        return len(self.evidence_level_data)
    
    def get_diseases_with_evidence(self) -> List[str]:
        """
        Get list of all disease ORPHA codes with evidence data
        
        Returns:
            List of ORPHA codes
        """
        return list(self.evidence_level_data.keys())
    
    def has_evidence_data(self, orpha_code: str) -> bool:
        """
        Check if a disease has evidence data
        
        Args:
            orpha_code: ORPHA code of the disease
            
        Returns:
            True if evidence data exists, False otherwise
        """
        return orpha_code in self.evidence_level_data 