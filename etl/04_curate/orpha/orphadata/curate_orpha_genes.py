#!/usr/bin/env python3
"""
Curate Orpha Gene Data

This script curates the processed gene data to focus on the 665 metabolic diseases
subset and extracts only disease-causing gene associations into a simple JSON format.

Based on the proven patterns from curate_orpha_prevalence.py
"""

import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def load_metabolic_disease_subset(subset_file: str) -> Set[str]:
    """
    Load the 665 metabolic diseases subset
    
    Args:
        subset_file: Path to metabolic_disease_instances.json
        
    Returns:
        Set of orpha codes for metabolic diseases
    """
    logger.info(f"Loading metabolic disease subset from: {subset_file}")
    
    try:
        with open(subset_file, 'r', encoding='utf-8') as f:
            metabolic_diseases = json.load(f)
        
        # Extract orpha codes from list structure
        if isinstance(metabolic_diseases, list):
            metabolic_codes = {disease['orpha_code'] for disease in metabolic_diseases if 'orpha_code' in disease}
        elif isinstance(metabolic_diseases, dict):
            metabolic_codes = set(metabolic_diseases.keys())
        else:
            raise ValueError(f"Unexpected data structure: {type(metabolic_diseases)}")
        
        logger.info(f"Loaded {len(metabolic_codes)} metabolic disease codes")
        return metabolic_codes
        
    except Exception as e:
        logger.error(f"Error loading metabolic disease subset: {e}")
        raise

def is_disease_causing_association(association_type: str) -> bool:
    """
    Check if an association type is disease-causing
    
    Args:
        association_type: The association type string
        
    Returns:
        True if the association is disease-causing
    """
    disease_causing_types = [
        "Disease-causing germline mutation(s) in",
        "Disease-causing germline mutation(s) (loss of function) in",
        "Disease-causing germline mutation(s) (gain of function) in",
        "Disease-causing somatic mutation(s) in"
    ]
    
    # Check if association type contains "Disease-causing"
    return "Disease-causing" in association_type

def curate_genes(processed_gene_file: str, metabolic_codes: Set[str]) -> Dict[str, List[str]]:
    """
    Curate genes for metabolic diseases with disease-causing associations
    
    Args:
        processed_gene_file: Path to processed disease2genes.json
        metabolic_codes: Set of metabolic disease orpha codes
        
    Returns:
        Simple mapping of orpha_code -> list of gene symbols
    """
    logger.info(f"Loading processed gene data from: {processed_gene_file}")
    
    try:
        with open(processed_gene_file, 'r', encoding='utf-8') as f:
            processed_gene_data = json.load(f)
        
        logger.info(f"Loaded gene data for {len(processed_gene_data)} diseases")
        
    except Exception as e:
        logger.error(f"Error loading processed gene data: {e}")
        raise
    
    curated_genes = {}
    
    # Statistics tracking
    stats = {
        'total_processed_diseases': len(processed_gene_data),
        'metabolic_diseases_found': 0,
        'diseases_with_disease_causing_genes': 0,
        'total_disease_causing_associations': 0,
        'association_type_counts': {},
        'excluded_association_types': {},
        'diseases_without_genes': 0
    }
    
    logger.info("Processing gene associations...")
    
    for orpha_code, disease_data in processed_gene_data.items():
        # Filter to metabolic diseases only
        if orpha_code not in metabolic_codes:
            continue
        
        stats['metabolic_diseases_found'] += 1
        
        # Extract disease-causing genes
        disease_causing_genes = []
        
        for association in disease_data.get('gene_associations', []):
            association_type = association.get('association_type', '')
            gene_symbol = association.get('gene_symbol')
            
            # Track association types
            stats['association_type_counts'][association_type] = stats['association_type_counts'].get(association_type, 0) + 1
            
            # Include only disease-causing associations
            if is_disease_causing_association(association_type):
                if gene_symbol and gene_symbol not in disease_causing_genes:
                    disease_causing_genes.append(gene_symbol)
                    stats['total_disease_causing_associations'] += 1
            else:
                # Track excluded types
                stats['excluded_association_types'][association_type] = stats['excluded_association_types'].get(association_type, 0) + 1
        
        # Only include diseases with disease-causing genes
        if disease_causing_genes:
            curated_genes[orpha_code] = sorted(disease_causing_genes)
            stats['diseases_with_disease_causing_genes'] += 1
        else:
            stats['diseases_without_genes'] += 1
    
    logger.info(f"Curation completed:")
    logger.info(f"  - Metabolic diseases found: {stats['metabolic_diseases_found']}")
    logger.info(f"  - Diseases with disease-causing genes: {stats['diseases_with_disease_causing_genes']}")
    logger.info(f"  - Diseases without disease-causing genes: {stats['diseases_without_genes']}")
    logger.info(f"  - Total disease-causing associations: {stats['total_disease_causing_associations']}")
    logger.info(f"  - Coverage: {(stats['diseases_with_disease_causing_genes'] / stats['metabolic_diseases_found']) * 100:.1f}%")
    
    return curated_genes, stats

def validate_curated_genes(curated_genes: Dict[str, List[str]]) -> Dict[str, Any]:
    """
    Quality assurance for curated gene mappings
    
    Args:
        curated_genes: Curated gene mappings
        
    Returns:
        Validation report
    """
    logger.info("Validating curated gene data...")
    
    validation_report = {
        'total_diseases': len(curated_genes),
        'diseases_with_single_gene': 0,
        'diseases_with_multiple_genes': 0,
        'total_gene_associations': 0,
        'unique_genes': set(),
        'quality_issues': [],
        'gene_count_distribution': {}
    }
    
    for orpha_code, genes in curated_genes.items():
        # Count associations
        gene_count = len(genes)
        validation_report['total_gene_associations'] += gene_count
        validation_report['unique_genes'].update(genes)
        
        # Count distribution
        if gene_count == 1:
            validation_report['diseases_with_single_gene'] += 1
        else:
            validation_report['diseases_with_multiple_genes'] += 1
        
        # Gene count distribution
        count_key = f"{gene_count}_genes" if gene_count <= 5 else "6+_genes"
        validation_report['gene_count_distribution'][count_key] = validation_report['gene_count_distribution'].get(count_key, 0) + 1
        
        # Quality checks
        if gene_count > 10:
            validation_report['quality_issues'].append(f"Disease {orpha_code} has {gene_count} genes (unusual)")
        
        for gene in genes:
            if not gene or not isinstance(gene, str):
                validation_report['quality_issues'].append(f"Invalid gene symbol in {orpha_code}: {gene}")
            elif len(gene) > 20:  # Unusually long gene symbol
                validation_report['quality_issues'].append(f"Unusually long gene symbol in {orpha_code}: {gene}")
    
    validation_report['unique_genes'] = len(validation_report['unique_genes'])
    
    logger.info(f"Validation completed:")
    logger.info(f"  - Total diseases: {validation_report['total_diseases']}")
    logger.info(f"  - Diseases with single gene: {validation_report['diseases_with_single_gene']}")
    logger.info(f"  - Diseases with multiple genes: {validation_report['diseases_with_multiple_genes']}")
    logger.info(f"  - Total gene associations: {validation_report['total_gene_associations']}")
    logger.info(f"  - Unique genes: {validation_report['unique_genes']}")
    logger.info(f"  - Quality issues: {len(validation_report['quality_issues'])}")
    
    if validation_report['quality_issues']:
        logger.warning("Quality issues found:")
        for issue in validation_report['quality_issues'][:5]:  # Show first 5 issues
            logger.warning(f"  - {issue}")
    
    return validation_report

def generate_curation_summary(curated_genes: Dict[str, List[str]], 
                            validation_report: Dict[str, Any],
                            curation_stats: Dict[str, Any],
                            metabolic_disease_count: int) -> Dict[str, Any]:
    """
    Generate comprehensive curation summary
    
    Args:
        curated_genes: Curated gene mappings
        validation_report: Validation results
        curation_stats: Curation statistics
        metabolic_disease_count: Total metabolic diseases in subset
        
    Returns:
        Comprehensive curation summary
    """
    # Calculate coverage
    diseases_with_genes = len(curated_genes)
    coverage_percentage = (diseases_with_genes / metabolic_disease_count) * 100
    
    # Most common genes
    gene_counts = {}
    for genes in curated_genes.values():
        for gene in genes:
            gene_counts[gene] = gene_counts.get(gene, 0) + 1
    
    most_common_genes = sorted(gene_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    summary = {
        "curation_metadata": {
            "input_diseases": metabolic_disease_count,
            "diseases_with_genes": diseases_with_genes,
            "diseases_without_genes": metabolic_disease_count - diseases_with_genes,
            "coverage_percentage": round(coverage_percentage, 1),
            "total_gene_associations": validation_report['total_gene_associations'],
            "unique_genes": validation_report['unique_genes'],
            "processing_timestamp": datetime.now().isoformat()
        },
        "disease_gene_distribution": {
            "diseases_with_single_gene": validation_report['diseases_with_single_gene'],
            "diseases_with_multiple_genes": validation_report['diseases_with_multiple_genes'],
            "gene_count_distribution": validation_report['gene_count_distribution']
        },
        "quality_statistics": {
            "association_type_counts": curation_stats['association_type_counts'],
            "excluded_association_types": curation_stats['excluded_association_types'],
            "quality_issues": len(validation_report['quality_issues']),
            "validation_passed": len(validation_report['quality_issues']) == 0,
            "average_genes_per_disease": round(validation_report['total_gene_associations'] / diseases_with_genes, 2) if diseases_with_genes > 0 else 0
        },
        "selection_criteria": {
            "metabolic_disease_filter": True,
            "disease_causing_only": True,
            "included_association_types": [
                "Disease-causing germline mutation(s) in",
                "Disease-causing germline mutation(s) (loss of function) in",
                "Disease-causing germline mutation(s) (gain of function) in",
                "Disease-causing somatic mutation(s) in"
            ],
            "excluded_association_types": list(curation_stats['excluded_association_types'].keys())
        },
        "top_genes": [
            {"gene": gene, "disease_count": count} 
            for gene, count in most_common_genes
        ]
    }
    
    return summary

def curate_orpha_genes(disease_subset_file: str, processed_gene_file: str, output_dir: str):
    """
    Main curation function
    
    Args:
        disease_subset_file: Path to metabolic disease subset file
        processed_gene_file: Path to processed gene data file
        output_dir: Output directory for curated data
    """
    logger.info("Starting gene curation process...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load metabolic disease subset
    metabolic_codes = load_metabolic_disease_subset(disease_subset_file)
    
    # Curate genes
    curated_genes, curation_stats = curate_genes(processed_gene_file, metabolic_codes)
    
    # Validate curated data
    validation_report = validate_curated_genes(curated_genes)
    
    # Generate summary
    summary = generate_curation_summary(curated_genes, validation_report, curation_stats, len(metabolic_codes))
    
    # Write output files
    logger.info("Writing output files...")
    
    # Main curated mapping
    output_file = output_path / "disease2genes.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(curated_genes, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote curated gene mapping to: {output_file}")
    
    # Curation summary
    summary_file = output_path / "orpha_gene_curation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote curation summary to: {summary_file}")
    
    logger.info("Gene curation completed successfully!")
    
    # Print final statistics
    logger.info("Final Results:")
    logger.info(f"  - Curated {len(curated_genes)} diseases with disease-causing genes")
    logger.info(f"  - Coverage: {summary['curation_metadata']['coverage_percentage']:.1f}% of metabolic diseases")
    logger.info(f"  - Total gene associations: {summary['curation_metadata']['total_gene_associations']}")
    logger.info(f"  - Unique genes: {summary['curation_metadata']['unique_genes']}")
    logger.info(f"  - Average genes per disease: {summary['quality_statistics']['average_genes_per_disease']}")
    
    return summary

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Curate Orpha gene data for metabolic diseases')
    parser.add_argument('--disease-subset', 
                       default='data/04_curated/orpha/ordo/metabolic_disease_instances.json',
                       help='Path to metabolic disease subset file')
    parser.add_argument('--input', 
                       default='data/03_processed/orpha/orphadata/orpha_genes/disease2genes.json',
                       help='Path to processed gene data file')
    parser.add_argument('--output', 
                       default='data/04_curated/orpha/orphadata',
                       help='Output directory for curated data')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input files
    if not Path(args.disease_subset).exists():
        logger.error(f"Disease subset file not found: {args.disease_subset}")
        sys.exit(1)
    
    if not Path(args.input).exists():
        logger.error(f"Processed gene data file not found: {args.input}")
        sys.exit(1)
    
    try:
        summary = curate_orpha_genes(args.disease_subset, args.input, args.output)
        
        if args.verbose:
            logger.info("Detailed statistics:")
            logger.info(f"  Association type counts:")
            for assoc_type, count in summary['quality_statistics']['association_type_counts'].items():
                logger.info(f"    {assoc_type}: {count}")
            
            logger.info(f"  Top 5 genes:")
            for gene_info in summary['top_genes'][:5]:
                logger.info(f"    {gene_info['gene']}: {gene_info['disease_count']} diseases")
                
    except Exception as e:
        logger.error(f"Curation failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 