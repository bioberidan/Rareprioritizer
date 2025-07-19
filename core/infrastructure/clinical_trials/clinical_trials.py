#!/usr/bin/env python3
"""
ClinicalTrials.gov API v2 Client for Disease Code Searches

This script allows searching for clinical trials using various disease identifiers:
- OrphaCode (Orphanet codes for rare diseases)
- MeSH terms (Medical Subject Headings)
- ICD-10 codes
- OMIM codes (Online Mendelian Inheritance in Man)
- GARD codes (Genetic and Rare Diseases)
- Disease names

Available Query Parameters in the API:
- query.term: Searches across multiple fields (broadest search)
- query.cond: Searches specifically in conditions/diseases field
- query.intr: Searches in interventions field
- query.titles: Searches in brief and official titles
- query.outc: Searches in outcome measures
- query.spons: Searches in all sponsors
- query.lead: Searches in lead sponsor only
- query.id: Searches in study IDs (NCT number, other IDs)
- query.patient: Searches in patient/volunteer information
- query.locn: Searches in locations (facility, city, state, country)

Available Filter Parameters:
- filter.overallStatus: Filter by study status (comma-separated values)
  Available values: NOT_YET_RECRUITING, RECRUITING, ENROLLING_BY_INVITATION,
  ACTIVE_NOT_RECRUITING, SUSPENDED, TERMINATED, COMPLETED, WITHDRAWN, UNKNOWN
- filter.ids: Filter by specific NCT IDs (comma-separated)

Example API URLs:
- All active trials in Spain:
  https://clinicaltrials.gov/api/v2/studies?query.locn=Spain&filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING
  
- Rare disease trials in Spain:
  https://clinicaltrials.gov/api/v2/studies?query.term=ORPHA:513&query.locn=Spain&filter.overallStatus=RECRUITING

Note: query.term is particularly useful for disease codes as it searches
across multiple fields and can find codes mentioned anywhere in the study record.

Author: Assistant
Date: 2025
"""

import requests
import json
import time
from typing import List, Dict, Optional, Union
import pandas as pd
from datetime import datetime
import logging
from urllib.parse import urlencode

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClinicalTrialsAPIClient:
    """Client for interacting with ClinicalTrials.gov API v2"""
    
    def __init__(self):
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.headers = {
            'User-Agent': 'Python ClinicalTrials API Client/1.0'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def search_by_orphacode(self, orphacode: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by OrphaCode (Orphanet code for rare diseases)
        
        Args:
            orphacode: OrphaCode (e.g., "ORPHA:513" for Marfan syndrome)
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        # OrphaCodes can be searched in multiple ways
        # Format variations to try
        orphacode_clean = orphacode.replace('ORPHA:', '').strip()
        
        # Search strategies:
        # 1. Search in conditions field (most specific)
        # 2. Search as general term (broader search)
        
        all_results = []
        
        # Try different formats in conditions
        cond_terms = [
            f"ORPHA:{orphacode_clean}",
            f"Orphanet:{orphacode_clean}",
            f"ORPHA {orphacode_clean}"
        ]
        
        for term in cond_terms:
            results = self._search_trials(query_cond=term, max_results=max_results//4)
            all_results.extend(results)
        
        # Also try as general term search (searches multiple fields)
        results = self._search_trials(query_term=f"ORPHA:{orphacode_clean}", max_results=max_results//4)
        all_results.extend(results)
        
        # Remove duplicates based on NCT ID
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for OrphaCode: {orphacode}")
        return df
    
    def search_by_mesh(self, mesh_term: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by MeSH (Medical Subject Headings) term
        
        Args:
            mesh_term: MeSH term (e.g., "Diabetes Mellitus, Type 2")
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        # MeSH terms are standard medical terminology and often appear in conditions
        # But they might also appear in other fields, so we search both ways
        
        all_results = []
        
        # Primary search: in conditions field (most likely location)
        results = self._search_trials(query_cond=mesh_term, max_results=max_results*2//3)
        all_results.extend(results)
        
        # Secondary search: general term search for broader coverage
        results = self._search_trials(query_term=mesh_term, max_results=max_results//3)
        all_results.extend(results)
        
        # Remove duplicates
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for MeSH term: {mesh_term}")
        return df
    
    def search_by_icd10(self, icd10_code: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by ICD-10 code
        
        Args:
            icd10_code: ICD-10 code (e.g., "E11" for Type 2 diabetes)
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        # ICD-10 codes might appear in various fields
        # Using query.term is most effective as it searches across multiple fields
        
        all_results = []
        
        # Primary search: use query.term for broad coverage
        results = self._search_trials(query_term=icd10_code, max_results=max_results*2//3)
        all_results.extend(results)
        
        # Secondary search: also try in conditions field specifically
        results = self._search_trials(query_cond=icd10_code, max_results=max_results//3)
        all_results.extend(results)
        
        # Remove duplicates
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for ICD-10 code: {icd10_code}")
        return df
    
    def search_by_omim(self, omim_code: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by OMIM (Online Mendelian Inheritance in Man) code
        
        Args:
            omim_code: OMIM code (e.g., "154700" for Marfan syndrome)
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        # OMIM codes often appear in various fields, not just conditions
        # query.term is most effective for finding these codes
        
        omim_clean = omim_code.replace('OMIM:', '').replace('MIM:', '').strip()
        search_terms = [
            f"OMIM:{omim_clean}",
            f"MIM:{omim_clean}",
            f"OMIM {omim_clean}",
            omim_clean  # Sometimes just the number is used
        ]
        
        all_results = []
        for term in search_terms:
            # Use query.term for broad search across all fields
            results = self._search_trials(query_term=term, max_results=max_results//len(search_terms))
            all_results.extend(results)
        
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for OMIM code: {omim_code}")
        return df
    
    def search_by_gard(self, gard_code: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by GARD (Genetic and Rare Diseases) code
        
        Args:
            gard_code: GARD code (e.g., "GARD:0006975" or "6975")
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        # GARD codes are less common but might appear in various fields
        # Using query.term for comprehensive search
        
        gard_clean = gard_code.replace('GARD:', '').strip()
        search_terms = [
            f"GARD:{gard_clean}",
            f"GARD {gard_clean}",
            gard_clean
        ]
        
        all_results = []
        for term in search_terms:
            # Use query.term for broad search
            results = self._search_trials(query_term=term, max_results=max_results//len(search_terms))
            all_results.extend(results)
        
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for GARD code: {gard_code}")
        return df
    
    def search_by_disease_name(self, disease_name: str, max_results: int = 100) -> pd.DataFrame:
        """
        Search clinical trials by disease name
        
        Args:
            disease_name: Disease name (e.g., "Marfan syndrome", "Type 2 Diabetes")
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        all_results = []
        
        # Primary search: in conditions field (most specific)
        results = self._search_trials(query_cond=disease_name, max_results=max_results*2//3)
        all_results.extend(results)
        
        # Secondary search: general term search (catches mentions in other fields)
        results = self._search_trials(query_term=disease_name, max_results=max_results//3)
        all_results.extend(results)
        
        # Remove duplicates
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Found {len(df)} unique trials for disease: {disease_name}")
        return df
    
    def search_multi_code(self, codes: Dict[str, str], max_results: int = 200) -> pd.DataFrame:
        """
        Search using multiple disease codes simultaneously
        
        Args:
            codes: Dictionary with code types as keys (e.g., {'orphacode': '513', 'mesh': 'Marfan Syndrome'})
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        all_results = []
        
        for code_type, code_value in codes.items():
            if code_type.lower() == 'orphacode':
                df = self.search_by_orphacode(code_value, max_results//len(codes))
            elif code_type.lower() == 'mesh':
                df = self.search_by_mesh(code_value, max_results//len(codes))
            elif code_type.lower() == 'icd10':
                df = self.search_by_icd10(code_value, max_results//len(codes))
            elif code_type.lower() == 'omim':
                df = self.search_by_omim(code_value, max_results//len(codes))
            elif code_type.lower() == 'gard':
                df = self.search_by_gard(code_value, max_results//len(codes))
            elif code_type.lower() == 'disease_name':
                df = self.search_by_disease_name(code_value, max_results//len(codes))
            else:
                logger.warning(f"Unknown code type: {code_type}")
                continue
            
            if not df.empty:
                all_results.append(df)
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['nctId'])
            logger.info(f"Found {len(combined_df)} unique trials across all code types")
            return combined_df
        else:
            return pd.DataFrame()
    
    def _search_trials(self, query_cond: str = None, query_term: str = None, 
                      query_intr: str = None, query_titles: str = None,
                      query_outc: str = None, query_spons: str = None,
                      query_lead: str = None, query_id: str = None,
                      query_patient: str = None, query_locn: str = None,
                      filter_overall_status: List[str] = None,
                      filter_ids: List[str] = None,
                      max_results: int = 100) -> List[Dict]:
        """
        Internal method to search trials with various query parameters
        
        Args:
            query_cond: Condition/disease query (searches in conditions field)
            query_term: General search term (searches across multiple fields)
            query_intr: Intervention query (searches in interventions)
            query_titles: Title query (searches in brief and official titles)
            query_outc: Outcome measures query
            query_spons: Sponsor query (searches all sponsors)
            query_lead: Lead sponsor query
            query_id: Study ID query (NCT number and other IDs)
            query_patient: Patient/volunteer query
            query_locn: Location query (facility, city, state, country)
            filter_overall_status: List of status values to filter (e.g., ['RECRUITING', 'ACTIVE_NOT_RECRUITING'])
            filter_ids: List of NCT IDs to filter
            max_results: Maximum number of results to retrieve
            
        Returns:
            List of trial dictionaries
        """
        params = {
            'pageSize': min(1000, max_results),  # API max is 1000 per page
            'format': 'json'
        }
        
        # Add query parameters if provided
        # Note: query.term searches across multiple fields including conditions,
        # interventions, outcomes, and other text fields
        if query_cond:
            params['query.cond'] = query_cond
        if query_term:
            params['query.term'] = query_term
        if query_intr:
            params['query.intr'] = query_intr
        if query_titles:
            params['query.titles'] = query_titles
        if query_outc:
            params['query.outc'] = query_outc
        if query_spons:
            params['query.spons'] = query_spons
        if query_lead:
            params['query.lead'] = query_lead
        if query_id:
            params['query.id'] = query_id
        if query_patient:
            params['query.patient'] = query_patient
        if query_locn:
            params['query.locn'] = query_locn
        
        # Add filter parameters if provided
        if filter_overall_status:
            params['filter.overallStatus'] = ','.join(filter_overall_status)
        if filter_ids:
            params['filter.ids'] = ','.join(filter_ids)
        
        all_studies = []
        next_page_token = None
        
        while len(all_studies) < max_results:
            if next_page_token:
                params['pageToken'] = next_page_token
            
            try:
                response = self.session.get(self.base_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                studies = data.get('studies', [])
                
                if not studies:
                    break
                
                # Extract relevant information from each study
                for study in studies:
                    study_info = self._extract_study_info(study)
                    all_studies.append(study_info)
                
                # Check for next page
                next_page_token = data.get('nextPageToken')
                if not next_page_token:
                    break
                
                # Rate limiting
                time.sleep(0.1)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                break
        
        return all_studies[:max_results]
    
    def _extract_study_info(self, study: Dict) -> Dict:
        """
        Extract relevant information from a study record
        
        Args:
            study: Raw study data from API
            
        Returns:
            Dictionary with extracted study information
        """
        protocol_section = study.get('protocolSection', {})
        
        # Extract basic identification
        identification = protocol_section.get('identificationModule', {})
        nct_id = identification.get('nctId', 'Unknown')
        
        # Extract status
        status_module = protocol_section.get('statusModule', {})
        overall_status = status_module.get('overallStatus', 'Unknown')
        
        # Extract conditions
        conditions_module = protocol_section.get('conditionsModule', {})
        conditions = conditions_module.get('conditions', [])
        
        # Extract interventions
        arms_interventions = protocol_section.get('armsInterventionsModule', {})
        interventions = []
        for intervention in arms_interventions.get('interventions', []):
            interventions.append({
                'type': intervention.get('type', 'Unknown'),
                'name': intervention.get('name', 'Unknown')
            })
        
        # Extract design info
        design_module = protocol_section.get('designModule', {})
        study_type = design_module.get('studyType', 'Unknown')
        phases = design_module.get('phases', [])
        
        # Extract enrollment
        enrollment_info = design_module.get('enrollmentInfo', {})
        enrollment = enrollment_info.get('count', 0)
        
        # Extract locations
        contacts_locations = protocol_section.get('contactsLocationsModule', {})
        locations = []
        for location in contacts_locations.get('locations', []):
            locations.append({
                'facility': location.get('facility', 'Unknown'),
                'city': location.get('city', 'Unknown'),
                'country': location.get('country', 'Unknown')
            })
        
        return {
            'nctId': nct_id,
            'briefTitle': identification.get('briefTitle', 'Unknown'),
            'officialTitle': identification.get('officialTitle', 'Unknown'),
            'overallStatus': overall_status,
            'studyType': study_type,
            'phases': phases,
            'conditions': conditions,
            'interventions': interventions,
            'enrollment': enrollment,
            'locations': locations,
            'lastUpdateDate': status_module.get('lastUpdatePostDateStruct', {}).get('date', 'Unknown')
        }
    
    def advanced_search(self, **kwargs) -> pd.DataFrame:
        """
        Advanced search using all available query parameters
        
        Available query parameters:
        - term: General search across multiple fields
        - cond: Conditions/diseases
        - intr: Interventions
        - titles: Brief and official titles
        - outc: Outcome measures
        - spons: All sponsors
        - lead: Lead sponsor
        - id: Study IDs (NCT number, other IDs)
        - patient: Patient/volunteer information
        - locn: Locations (facility, city, state, country)
        
        Available filter parameters:
        - overall_status: List of status values (e.g., ['RECRUITING', 'ACTIVE_NOT_RECRUITING'])
        - ids: List of NCT IDs
        
        - max_results: Maximum number of results (default 100)
        
        Example:
            df = client.advanced_search(
                term="ORPHA:513",
                cond="Marfan syndrome",
                locn="Spain",
                overall_status=['RECRUITING', 'ACTIVE_NOT_RECRUITING'],
                max_results=200
            )
        
        Returns:
            DataFrame with clinical trial results
        """
        max_results = kwargs.pop('max_results', 100)
        
        # Map user-friendly parameter names to API parameter names
        query_param_mapping = {
            'term': 'query_term',
            'cond': 'query_cond',
            'intr': 'query_intr',
            'titles': 'query_titles',
            'outc': 'query_outc',
            'spons': 'query_spons',
            'lead': 'query_lead',
            'id': 'query_id',
            'patient': 'query_patient',
            'locn': 'query_locn'
        }
        
        filter_param_mapping = {
            'overall_status': 'filter_overall_status',
            'ids': 'filter_ids'
        }
        
        # Build search parameters
        search_params = {}
        
        # Process query parameters
        for user_param, api_param in query_param_mapping.items():
            if user_param in kwargs:
                search_params[api_param] = kwargs[user_param]
        
        # Process filter parameters
        for user_param, api_param in filter_param_mapping.items():
            if user_param in kwargs:
                search_params[api_param] = kwargs[user_param]
        
        # Perform search
        results = self._search_trials(max_results=max_results, **search_params)
        df = pd.DataFrame(results)
        
        # Log search summary
        logger.info(f"Advanced search found {len(df)} trials")
        logger.info(f"Search parameters used: {kwargs}")
        
        return df
    
    def search_comprehensive(self, disease_term: str, include_related: bool = True, 
                           max_results: int = 200) -> pd.DataFrame:
        """
        Comprehensive search strategy using multiple query approaches
        
        This method searches using both specific (query.cond) and broad (query.term) 
        approaches to maximize recall of relevant trials.
        
        Args:
            disease_term: Disease name or code to search for
            include_related: Whether to search in related fields (interventions, outcomes)
            max_results: Maximum number of results to retrieve
            
        Returns:
            DataFrame with clinical trial results
        """
        all_results = []
        
        # Strategy 1: Search in conditions (most relevant)
        results = self._search_trials(query_cond=disease_term, max_results=max_results//3)
        all_results.extend(results)
        
        # Strategy 2: General term search (catches mentions in any field)
        results = self._search_trials(query_term=disease_term, max_results=max_results//3)
        all_results.extend(results)
        
        # Strategy 3: Search in titles (for trials specifically named after the disease)
        results = self._search_trials(query_titles=disease_term, max_results=max_results//3)
        all_results.extend(results)
        
        if include_related:
            # Also search in outcome measures (some trials mention disease codes there)
            results = self._search_trials(query_outc=disease_term, max_results=max_results//6)
            all_results.extend(results)
        
        # Combine and deduplicate
        df = pd.DataFrame(all_results)
        if not df.empty:
            df = df.drop_duplicates(subset=['nctId'])
        
        logger.info(f"Comprehensive search found {len(df)} unique trials for: {disease_term}")
        return df
        """
        Export search results to file
        
        Args:
            df: DataFrame with search results
            filename: Output filename (auto-generated if None)
            format: Output format ('csv', 'json', 'excel')
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'clinical_trials_results_{timestamp}'
        
        if format == 'csv':
            df.to_csv(f'{filename}.csv', index=False)
            logger.info(f"Results exported to {filename}.csv")
        elif format == 'json':
            df.to_json(f'{filename}.json', orient='records', indent=2)
            logger.info(f"Results exported to {filename}.json")
        elif format == 'excel':
            df.to_excel(f'{filename}.xlsx', index=False)
            logger.info(f"Results exported to {filename}.xlsx")
        else:
            logger.error(f"Unsupported format: {format}")


    def export_results(self, df: pd.DataFrame, filename: str = None, format: str = 'csv'):
        """
        Export search results to file
        
        Args:
            df: DataFrame with search results
            filename: Output filename (auto-generated if None)
            format: Output format ('csv', 'json', 'excel')
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'clinical_trials_results_{timestamp}'
        
        if format == 'csv':
            df.to_csv(f'{filename}.csv', index=False)
            logger.info(f"Results exported to {filename}.csv")
        elif format == 'json':
            df.to_json(f'{filename}.json', orient='records', indent=2)
            logger.info(f"Results exported to {filename}.json")
        elif format == 'excel':
            df.to_excel(f'{filename}.xlsx', index=False)
            logger.info(f"Results exported to {filename}.xlsx")
        else:
            logger.error(f"Unsupported format: {format}")


def main():
    """Example usage of the ClinicalTrialsAPIClient"""
    
    # Initialize client
    client = ClinicalTrialsAPIClient()
    
    # Show available query parameters
    print("\n=== Available Query Parameters ===")
    params_info = client.get_query_parameter_info()
    for category, params in params_info.items():
        print(f"\n{category}:")
        if isinstance(params, dict):
            for param, description in params.items():
                print(f"  {param}: {description}")
        else:
            print(f"  {params}")
    
    # Example 1: Search active trials in Spain (as in your example)
    print("\n=== Active Trials in Spain ===")
    df_spain = client.search_active_trials_by_location(
        disease_term="",  # Empty for all diseases
        location="Spain",
        max_results=50
    )
    if not df_spain.empty:
        print(f"Found {len(df_spain)} active trials in Spain")
        print(df_spain[['nctId', 'briefTitle', 'overallStatus']].head(3))
    
    # Example 2: Search with disease code and filters
    print("\n=== Search with OrphaCode and Status Filter ===")
    df_filtered = client.advanced_search(
        term="ORPHA:513",
        locn="Spain",
        overall_status=['RECRUITING', 'ACTIVE_NOT_RECRUITING'],
        max_results=50
    )
    if not df_filtered.empty:
        print(f"Found {len(df_filtered)} trials")
        print(df_filtered[['nctId', 'briefTitle', 'overallStatus']].head(3))
    
    # Example 3: Direct API call with all parameters (exactly as your URL)
    print("\n=== Direct API Call Example ===")
    results = client._search_trials(
        query_term="ORPHA:513",  # Or any disease code
        query_locn="Spain",
        filter_overall_status=['RECRUITING', 'ACTIVE_NOT_RECRUITING'],
        max_results=100
    )
    print(f"Found {len(results)} trials matching criteria")
    
    # Example 4: Search rare disease trials in Europe
    print("\n=== Rare Disease Trials in Multiple Countries ===")
    countries = ["Spain", "France", "Germany", "Italy"]
    all_results = []
    
    for country in countries:
        df_country = client.advanced_search(
            term="rare disease",
            locn=country,
            overall_status=['RECRUITING'],
            max_results=20
        )
        if not df_country.empty:
            df_country['search_country'] = country
            all_results.append(df_country)
            print(f"  {country}: {len(df_country)} recruiting trials")
    
    if all_results:
        df_combined = pd.concat(all_results, ignore_index=True)
        print(f"\nTotal: {len(df_combined)} recruiting rare disease trials across Europe")
    
    # Example 5: Search by OrphaCode with comprehensive filters
    print("\n=== Comprehensive OrphaCode Search ===")
    df_orpha = client.search_by_orphacode("513", max_results=50)
    if not df_orpha.empty:
        # Apply post-search filtering for active trials in specific locations
        active_statuses = ['RECRUITING', 'ACTIVE_NOT_RECRUITING']
        df_active = df_orpha[df_orpha['overallStatus'].isin(active_statuses)]
        
        # Check which trials have locations in Spain
        def has_spain_location(locations):
            return any('Spain' in str(loc.get('country', '')) for loc in locations)
        
        df_spain_trials = df_active[df_active['locations'].apply(has_spain_location)]
        
        print(f"Total OrphaCode 513 trials: {len(df_orpha)}")
        print(f"Active trials: {len(df_active)}")
        print(f"Active trials with locations in Spain: {len(df_spain_trials)}")
    
    # Example 6: Build the exact URL from your example
    print("\n=== Building API URL ===")
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        'query.term': 'ORPHA:513',  # You can fill this with any disease code
        'query.locn': 'Spain',
        'filter.overallStatus': 'RECRUITING,ACTIVE_NOT_RECRUITING',
        'pageSize': 100,
        'format': 'json'
    }
    
    # Build URL
    from urllib.parse import urlencode
    full_url = f"{base_url}?{urlencode(params)}"
    print(f"Full API URL: {full_url}")
    
    # You can use requests directly with this URL
    import requests
    response = requests.get(full_url)
    if response.status_code == 200:
        data = response.json()
        print(f"Direct API call returned {len(data.get('studies', []))} studies")


if __name__ == "__main__":
    main()
