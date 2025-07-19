"""
Orpha Drug Module

This module provides functionality to scrape and process drug data from Orpha.net
for rare diseases. It includes web scraping capabilities and data parsing.
"""

from .orpha_drug import OrphaDrugAPIClient, DrugParser

__all__ = ['OrphaDrugAPIClient', 'DrugParser'] 