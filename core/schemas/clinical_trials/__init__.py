"""
Clinical Trials Data Models

This package contains Pydantic data models for clinical trials data processing,
providing type-safe, validated data structures for clinical trials information.
"""

from .clinical_trials import (
    ClinicalTrialInstance,
    TrialMapping,
    TrialLocationInfo,
    TrialProcessingResult,
    TrialStatistics,
    CuratedTrialMapping
)

__all__ = [
    "ClinicalTrialInstance",
    "TrialMapping", 
    "TrialLocationInfo",
    "TrialProcessingResult",
    "TrialStatistics",
    "CuratedTrialMapping"
] 