#!/usr/bin/env python3
"""
Websearch Groups Curation Script

This script processes websearch groups data from the preprocessed directory and generates
curated JSON files for group-disease mappings and source tracking.

Input: data/02_preprocess/websearch/metabolic/
Output: data/04_curated/websearch/groups/

Generated Files:
- disease2group.json: Mapping from disease to groups
- group2source.json: Mapping from groups to sources
- group2disease.json: Reverse mapping from groups to diseases
- websearch_groups_curation_summary.json: Curation metadata
"""

import json
import os
import sys
import logging
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_preprocessed_data(input_dir: str) -> Dict[str, Any]:
    """
    Load all preprocessed websearch data from the input directory.
    
    Args:
        input_dir: Directory containing preprocessed websearch data
        
    Returns:
        Dictionary containing all disease data
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    diseases_data = {}
    processing_stats = {
        'total_diseases_found': 0,
        'diseases_processed': 0,
        'diseases_with_groups': 0,
        'diseases_without_groups': 0,
        'failed_loads': []
    }
    
    logger.info(f"Loading preprocessed data from: {input_path}")
    
    # Iterate through each disease directory
    for disease_dir in input_path.iterdir():
        if not disease_dir.is_dir():
            continue
            
        orpha_code = disease_dir.name
        processing_stats['total_diseases_found'] += 1
        
        # Look for run1.json file
        run_file = disease_dir / "run1.json"
        if not run_file.exists():
            logger.warning(f"No run1.json found for disease {orpha_code}")
            processing_stats['failed_loads'].append(f"{orpha_code}: No run1.json file")
            continue
        
        try:
            with open(run_file, 'r', encoding='utf-8') as f:
                disease_data = json.load(f)
            
            diseases_data[orpha_code] = disease_data
            processing_stats['diseases_processed'] += 1
            
            # Check if disease has groups
            groups = disease_data.get('groups', [])
            if groups:
                processing_stats['diseases_with_groups'] += 1
            else:
                processing_stats['diseases_without_groups'] += 1
                
        except Exception as e:
            logger.warning(f"Failed to load data for disease {orpha_code}: {e}")
            processing_stats['failed_loads'].append(f"{orpha_code}: {str(e)}")
    
    logger.info(f"Loaded {processing_stats['diseases_processed']} diseases")
    logger.info(f"Diseases with groups: {processing_stats['diseases_with_groups']}")
    logger.info(f"Diseases without groups: {processing_stats['diseases_without_groups']}")
    
    return diseases_data, processing_stats


def extract_disease_group_mappings(diseases_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Extract disease to groups mappings from loaded data.
    
    Args:
        diseases_data: Dictionary containing disease data
        
    Returns:
        Dictionary mapping orpha codes to group names
    """
    disease2group = {}
    
    for orpha_code, disease_data in diseases_data.items():
        groups = disease_data.get('groups', [])
        group_names = []
        
        for group in groups:
            unit_name = group.get('unit_name')
            if unit_name:
                group_names.append(unit_name)
        
        disease2group[orpha_code] = group_names
    
    logger.info(f"Generated disease to group mappings for {len(disease2group)} diseases")
    return disease2group


def extract_group_source_mappings(diseases_data: Dict[str, Any]) -> Dict[str, List[Dict[str, str]]]:
    """
    Extract group to sources mappings from loaded data.
    
    Args:
        diseases_data: Dictionary containing disease data
        
    Returns:
        Dictionary mapping group names to source lists
    """
    group2source = defaultdict(list)
    
    for orpha_code, disease_data in diseases_data.items():
        groups = disease_data.get('groups', [])
        
        for group in groups:
            unit_name = group.get('unit_name')
            sources = group.get('sources', [])
            
            if unit_name and sources:
                # Merge sources for the same group
                for source in sources:
                    if source not in group2source[unit_name]:
                        group2source[unit_name].append(source)
    
    # Convert defaultdict to regular dict
    group2source = dict(group2source)
    
    logger.info(f"Generated group to source mappings for {len(group2source)} groups")
    return group2source


def validate_sources(group2source: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """
    Validate source URLs and format consistency.
    
    Args:
        group2source: Dictionary mapping groups to sources
        
    Returns:
        Dictionary containing validation results
    """
    validation_results = {
        'total_groups': len(group2source),
        'total_sources': 0,
        'sources_with_urls': 0,
        'sources_with_labels': 0,
        'valid_sources': 0,
        'invalid_sources': 0
    }
    
    for group_name, sources in group2source.items():
        for source in sources:
            validation_results['total_sources'] += 1
            
            has_url = 'url' in source and source['url']
            has_label = 'label' in source and source['label']
            
            if has_url:
                validation_results['sources_with_urls'] += 1
            if has_label:
                validation_results['sources_with_labels'] += 1
            
            if has_url and has_label:
                validation_results['valid_sources'] += 1
            else:
                validation_results['invalid_sources'] += 1
    
    logger.info(f"Source validation completed: {validation_results['valid_sources']} valid sources")
    return validation_results


def normalize_group_names(disease2group: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Normalize and categorize group names by format.
    
    Args:
        disease2group: Dictionary mapping diseases to groups
        
    Returns:
        Dictionary containing group name analysis
    """
    all_groups = set()
    for groups in disease2group.values():
        all_groups.update(groups)
    
    group_types = {
        'u_format': [],
        'descriptive': [],
        'pi_based': []
    }
    
    for group in all_groups:
        if group.startswith('U') and group[1:].replace(' ', '').isdigit():
            group_types['u_format'].append(group)
        elif 'grupo del' in group.lower() or 'grupo de' in group.lower() and ('dr.' in group.lower() or 'dra.' in group.lower()):
            group_types['pi_based'].append(group)
        else:
            group_types['descriptive'].append(group)
    
    group_analysis = {
        'total_unique_groups': len(all_groups),
        'group_type_distribution': {
            'u_format': len(group_types['u_format']),
            'descriptive': len(group_types['descriptive']),
            'pi_based': len(group_types['pi_based'])
        },
        'group_types': group_types
    }
    
    logger.info(f"Group name analysis: {group_analysis['group_type_distribution']}")
    return group_analysis


def handle_failed_searches(diseases_data: Dict[str, Any]) -> List[str]:
    """
    Identify and process diseases with empty groups arrays.
    
    Args:
        diseases_data: Dictionary containing disease data
        
    Returns:
        List of orpha codes with failed searches
    """
    failed_diseases = []
    
    for orpha_code, disease_data in diseases_data.items():
        groups = disease_data.get('groups', [])
        if not groups:
            failed_diseases.append(orpha_code)
    
    logger.info(f"Found {len(failed_diseases)} diseases with failed searches")
    return failed_diseases


def generate_summary_statistics(disease2group: Dict[str, List[str]], 
                               group2source: Dict[str, List[Dict[str, str]]],
                               group_analysis: Dict[str, Any],
                               validation_results: Dict[str, Any],
                               processing_stats: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive summary statistics.
    
    Args:
        disease2group: Disease to group mappings
        group2source: Group to source mappings
        group_analysis: Group name analysis results
        validation_results: Source validation results
        processing_stats: Processing statistics
        
    Returns:
        Dictionary containing summary statistics
    """
    # Calculate disease coverage
    diseases_with_groups = sum(1 for groups in disease2group.values() if groups)
    
    # Calculate group statistics
    group_disease_count = defaultdict(int)
    for orpha_code, groups in disease2group.items():
        for group in groups:
            group_disease_count[group] += 1
    
    summary = {
        'curation_metadata': {
            'total_diseases_searched': processing_stats['total_diseases_found'],
            'diseases_with_groups': diseases_with_groups,
            'total_unique_groups': group_analysis['total_unique_groups'],
            'total_sources': validation_results['total_sources'],
            'group_type_distribution': group_analysis['group_type_distribution'],
            'processing_timestamp': datetime.now().isoformat()
        },
        'quality_metrics': validation_results,
        'most_active_groups': sorted(
            [{'group': group, 'disease_count': count} 
             for group, count in group_disease_count.items()],
            key=lambda x: x['disease_count'], 
            reverse=True
        )[:10]
    }
    
    return summary


def save_curated_file(data: Any, filename: str, output_dir: Path) -> None:
    """
    Save data to JSON file in the output directory.
    
    Args:
        data: Data to save
        filename: Output filename
        output_dir: Output directory path
    """
    output_file = output_dir / filename
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved {filename}")


def curate_websearch_groups(input_dir: str = "data/02_preprocess/websearch/metabolic",
                           output_dir: str = "data/04_curated/websearch/groups") -> Dict[str, Any]:
    """
    Main curation function - aggregate websearch groups data and generate curated files.
    
    Args:
        input_dir: Input directory with preprocessed websearch data
        output_dir: Output directory for curated data
        
    Returns:
        Dictionary containing curation results
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting websearch groups curation...")
    logger.info(f"Input: {input_dir}")
    logger.info(f"Output: {output_path}")
    
    # Load preprocessed data
    diseases_data, processing_stats = load_preprocessed_data(input_dir)
    
    # Extract mappings
    disease2group = extract_disease_group_mappings(diseases_data)
    group2source = extract_group_source_mappings(diseases_data)
    
    # Generate reverse mapping
    group2disease = defaultdict(list)
    for orpha_code, groups in disease2group.items():
        for group in groups:
            group2disease[group].append(orpha_code)
    group2disease = dict(group2disease)
    
    # Validate and analyze
    validation_results = validate_sources(group2source)
    group_analysis = normalize_group_names(disease2group)
    failed_diseases = handle_failed_searches(diseases_data)
    
    # Generate summary
    summary = generate_summary_statistics(
        disease2group, group2source, group_analysis, 
        validation_results, processing_stats
    )
    
    # Save all output files
    save_curated_file(disease2group, "disease2group.json", output_path)
    save_curated_file(group2source, "group2source.json", output_path)
    save_curated_file(group2disease, "group2disease.json", output_path)
    save_curated_file(summary, "websearch_groups_curation_summary.json", output_path)
    
    logger.info("Websearch groups curation completed successfully!")
    logger.info(f"Generated files in: {output_path}")
    
    return {
        "disease2group": disease2group,
        "group2source": group2source,
        "group2disease": group2disease,
        "summary": summary
    }


def main():
    """
    Main entry point for websearch groups curation
    """
    parser = argparse.ArgumentParser(description="Curate websearch groups data")
    parser.add_argument("--input-dir", default="data/02_preprocess/websearch/metabolic",
                       help="Input directory with preprocessed websearch data")
    parser.add_argument("--output-dir", default="data/04_curated/websearch/groups",
                       help="Output directory for curated data")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Run curation
        results = curate_websearch_groups(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Print summary
        print("\n" + "="*60)
        print("WEBSEARCH GROUPS CURATION SUMMARY")
        print("="*60)
        
        metadata = results["summary"]["curation_metadata"]
        print(f"Total diseases searched: {metadata['total_diseases_searched']}")
        print(f"Diseases with groups: {metadata['diseases_with_groups']}")
        print(f"Total unique groups: {metadata['total_unique_groups']}")
        print(f"Total sources: {metadata['total_sources']}")
        
        print(f"\nGroup Type Distribution:")
        type_dist = metadata['group_type_distribution']
        print(f"  U-format: {type_dist['u_format']} groups")
        print(f"  Descriptive: {type_dist['descriptive']} groups")
        print(f"  PI-based: {type_dist['pi_based']} groups")
        
        print(f"\nFiles generated in: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Curation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 