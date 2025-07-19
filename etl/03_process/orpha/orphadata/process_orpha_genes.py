#!/usr/bin/env python3
"""
Process Orpha Gene Data

This script processes the Orphanet gene-disease association XML data from en_product6.xml
and creates structured JSON files for analysis and querying.

Based on the proven patterns from process_orpha_prevalence.py
"""

import json
import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

# Standard logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)



def standardize_external_references(ref_list: List[Dict]) -> Dict[str, str]:
    """
    Standardize external database references
    
    Args:
        ref_list: List of external reference records from XML
        
    Returns:
        Standardized reference dictionary
    """
    standardized = {}
    
    for ref in ref_list:
        source = ref.get('source', '')
        reference = ref.get('reference', '')
        
        if source and reference:
            standardized[source] = reference
    
    return standardized

def process_gene_element(gene_elem: ET.Element) -> Dict:
    """
    Process a Gene XML element and extract all relevant information
    
    Args:
        gene_elem: XML Gene element
        
    Returns:
        Dictionary with gene information
    """
    gene_id = gene_elem.get('id', '')
    
    # Basic gene information
    name_elem = gene_elem.find('Name[@lang="en"]')
    gene_name = name_elem.text if name_elem is not None else f"Unknown_{gene_id}"
    
    symbol_elem = gene_elem.find('Symbol')
    gene_symbol = symbol_elem.text if symbol_elem is not None else f"UNK_{gene_id}"
    
    # Gene type
    gene_type_elem = gene_elem.find('GeneType/Name[@lang="en"]')
    gene_type = gene_type_elem.text if gene_type_elem is not None else "Unknown"
    
    # Gene synonyms
    synonyms = []
    synonym_list = gene_elem.find('SynonymList')
    if synonym_list is not None:
        for synonym in synonym_list.findall('Synonym[@lang="en"]'):
            if synonym.text:
                synonyms.append(synonym.text)
    
    # External references
    external_refs = {}
    ref_list = gene_elem.find('ExternalReferenceList')
    if ref_list is not None:
        ref_data = []
        for ref in ref_list.findall('ExternalReference'):
            source_elem = ref.find('Source')
            reference_elem = ref.find('Reference')
            
            if source_elem is not None and reference_elem is not None:
                ref_data.append({
                    'source': source_elem.text,
                    'reference': reference_elem.text
                })
        
        external_refs = standardize_external_references(ref_data)
    
    # Gene locus
    gene_locus = None
    locus_list = gene_elem.find('LocusList')
    if locus_list is not None:
        locus_elem = locus_list.find('Locus/GeneLocus')
        if locus_elem is not None:
            gene_locus = locus_elem.text
    
    return {
        'gene_id': gene_id,
        'gene_symbol': gene_symbol,
        'gene_name': gene_name,
        'gene_type': gene_type,
        'gene_locus': gene_locus,
        'gene_synonyms': synonyms,
        'external_references': external_refs
    }

def process_genes_xml(xml_path: str, output_dir: str) -> Dict:
    """
    Main processing function to transform XML to structured JSON
    
    Args:
        xml_path: Path to en_product6.xml
        output_dir: Output directory for processed data
        
    Returns:
        Processing statistics and metadata
    """
    logger.info(f"Starting gene processing: {xml_path}")
    
    # Initialize statistics
    stats = {
        "total_disorders": 0,
        "disorders_with_genes": 0,
        "total_gene_associations": 0,
        "unique_genes": 0,
        "association_types": {},
        "gene_types": {},
        "external_reference_coverage": {},
        "processing_timestamp": datetime.now().isoformat()
    }
    
    # Output data structures
    disease2genes = {}
    gene2diseases = {}
    gene_instances = {}
    gene_association_instances = {}
    orpha_index = {}
    
    # Parse XML
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        logger.info("XML parsed successfully")
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        raise
    
    # Process each disorder
    for disorder in root.findall('.//Disorder'):
        stats["total_disorders"] += 1
        
        # Get disorder information
        disorder_id = disorder.get('id', '')
        orpha_code_elem = disorder.find('OrphaCode')
        orpha_code = orpha_code_elem.text if orpha_code_elem is not None else disorder_id
        
        name_elem = disorder.find('Name[@lang="en"]')
        disease_name = name_elem.text if name_elem is not None else f"Unknown_{orpha_code}"
        
        # Process gene associations
        gene_assoc_list = disorder.find('DisorderGeneAssociationList')
        if gene_assoc_list is None:
            continue
            
        stats["disorders_with_genes"] += 1
        gene_associations = []
        
        for gene_assoc in gene_assoc_list.findall('DisorderGeneAssociation'):
            stats["total_gene_associations"] += 1
            
            # Source validation
            source_validation_elem = gene_assoc.find('SourceOfValidation')
            source_validation = source_validation_elem.text if source_validation_elem is not None else ""
            
            # Process gene element
            gene_elem = gene_assoc.find('Gene')
            if gene_elem is not None:
                gene_data = process_gene_element(gene_elem)
                
                # Association type
                assoc_type_elem = gene_assoc.find('DisorderGeneAssociationType/Name[@lang="en"]')
                association_type = assoc_type_elem.text if assoc_type_elem is not None else ""
                
                # Association status
                assoc_status_elem = gene_assoc.find('DisorderGeneAssociationStatus/Name[@lang="en"]')
                association_status = assoc_status_elem.text if assoc_status_elem is not None else ""
                
                # Create association record
                association_record = {
                    'gene_association_id': f"assoc_{orpha_code}_{gene_data['gene_symbol']}",
                    'orpha_code': orpha_code,
                    'disease_name': disease_name,
                    'association_type': association_type,
                    'association_status': association_status,
                    'source_validation': source_validation,
                    **gene_data
                }
                
                # Update statistics
                stats["association_types"][association_type] = stats["association_types"].get(association_type, 0) + 1
                stats["gene_types"][gene_data['gene_type']] = stats["gene_types"].get(gene_data['gene_type'], 0) + 1
                
                # Track external reference coverage
                for ref_source in gene_data['external_references'].keys():
                    stats["external_reference_coverage"][ref_source] = stats["external_reference_coverage"].get(ref_source, 0) + 1
                
                # Add to data structures
                gene_associations.append(association_record)
                
                # Add to gene_association_instances
                gene_association_instances[association_record['gene_association_id']] = {
                    **association_record,
                    'processing_metadata': {
                        'xml_disorder_id': disorder_id,
                        'xml_gene_id': gene_data['gene_id'],
                        'processed_timestamp': datetime.now().isoformat()
                    }
                }
                
                # Add to gene_instances
                gene_symbol = gene_data['gene_symbol']
                if gene_symbol not in gene_instances:
                    gene_instances[gene_symbol] = {
                        **gene_data,
                        'associated_diseases_count': 0,
                        'processing_metadata': {
                            'first_seen': datetime.now().isoformat(),
                            'data_quality_score': 0.0,
                            'validation_status': 'complete'
                        }
                    }
                    stats["unique_genes"] += 1
                
                gene_instances[gene_symbol]['associated_diseases_count'] += 1
                
                # Add to gene2diseases
                if gene_symbol not in gene2diseases:
                    gene2diseases[gene_symbol] = {
                        **gene_data,
                        'associated_diseases': [],
                        'total_disease_associations': 0,
                        'statistics': {
                            'association_types': {}
                        }
                    }
                
                disease_assoc = {
                    'orpha_code': orpha_code,
                    'disease_name': disease_name,
                    'association_type': association_type,
                    'association_status': association_status,
                    'source_validation': source_validation
                }
                
                gene2diseases[gene_symbol]['associated_diseases'].append(disease_assoc)
                gene2diseases[gene_symbol]['total_disease_associations'] += 1
                
                # Update association types stats
                assoc_types = gene2diseases[gene_symbol]['statistics']['association_types']
                assoc_types[association_type] = assoc_types.get(association_type, 0) + 1
        
        # Add to disease2genes
        if gene_associations:
            # Determine primary gene (first one for simplicity)
            primary_gene = gene_associations[0]['gene_symbol']
            
            disease2genes[orpha_code] = {
                'orpha_code': orpha_code,
                'disease_name': disease_name,
                'gene_associations': gene_associations,
                'primary_gene': primary_gene,
                'total_gene_associations': len(gene_associations),
                'statistics': {
                    'total_associations': len(gene_associations)
                }
            }
            
            # Add to orpha_index
            orpha_index[orpha_code] = {
                'orpha_code': orpha_code,
                'disease_name': disease_name,
                'gene_count': len(gene_associations),
                'primary_gene': primary_gene
            }
    

    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (output_path / 'external_references').mkdir(exist_ok=True)
    (output_path / 'validation_data').mkdir(exist_ok=True)
    (output_path / 'gene_types').mkdir(exist_ok=True)
    (output_path / 'cache').mkdir(exist_ok=True)
    
    # Write main output files
    logger.info("Writing main output files...")
    
    with open(output_path / 'disease2genes.json', 'w', encoding='utf-8') as f:
        json.dump(disease2genes, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'gene2diseases.json', 'w', encoding='utf-8') as f:
        json.dump(gene2diseases, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'gene_instances.json', 'w', encoding='utf-8') as f:
        json.dump(gene_instances, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'gene_association_instances.json', 'w', encoding='utf-8') as f:
        json.dump(gene_association_instances, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'orpha_index.json', 'w', encoding='utf-8') as f:
        json.dump(orpha_index, f, ensure_ascii=False, indent=2)
    
    # Write external references
    logger.info("Writing external reference files...")
    
    external_refs_by_source = {}
    for gene_data in gene_instances.values():
        for source, reference in gene_data['external_references'].items():
            if source not in external_refs_by_source:
                external_refs_by_source[source] = {}
            external_refs_by_source[source][gene_data['gene_symbol']] = reference
    
    for source, refs in external_refs_by_source.items():
        filename = f"{source.lower()}_references.json"
        with open(output_path / 'external_references' / filename, 'w', encoding='utf-8') as f:
            json.dump(refs, f, ensure_ascii=False, indent=2)
    
    # Write validation data
    logger.info("Writing validation data...")
    
    with open(output_path / 'validation_data' / 'validation_summary.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_associations': len(gene_association_instances),
            'source_validation_stats': {
                'pmid_validated': len([a for a in gene_association_instances.values() if '[PMID]' in (a.get('source_validation') or '')]),
                'expert_validated': len([a for a in gene_association_instances.values() if 'EXPERT' in (a.get('source_validation') or '')]),
                'no_validation': len([a for a in gene_association_instances.values() if not (a.get('source_validation') or '')])
            }
        }, f, ensure_ascii=False, indent=2)
    
    # Write gene types
    logger.info("Writing gene type files...")
    
    gene_type_mapping = {}
    for gene_data in gene_instances.values():
        gene_type = gene_data['gene_type']
        if gene_type not in gene_type_mapping:
            gene_type_mapping[gene_type] = []
        gene_type_mapping[gene_type].append(gene_data['gene_symbol'])
    
    with open(output_path / 'gene_types' / 'gene_type_distribution.json', 'w', encoding='utf-8') as f:
        json.dump(stats['gene_types'], f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'gene_types' / 'gene_type_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(gene_type_mapping, f, ensure_ascii=False, indent=2)
    
    # Write cache files
    logger.info("Writing cache files...")
    
    gene_symbols_index = {gene['gene_symbol']: gene['gene_id'] for gene in gene_instances.values()}
    
    locus_index = {}
    for gene_data in gene_instances.values():
        if gene_data['gene_locus']:
            locus = gene_data['gene_locus']
            if locus not in locus_index:
                locus_index[locus] = []
            locus_index[locus].append(gene_data['gene_symbol'])
    
    association_type_index = {}
    for assoc in gene_association_instances.values():
        assoc_type = assoc['association_type']
        if assoc_type not in association_type_index:
            association_type_index[assoc_type] = []
        association_type_index[assoc_type].append(assoc['gene_association_id'])
    
    with open(output_path / 'cache' / 'statistics.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'cache' / 'gene_symbols_index.json', 'w', encoding='utf-8') as f:
        json.dump(gene_symbols_index, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'cache' / 'locus_index.json', 'w', encoding='utf-8') as f:
        json.dump(locus_index, f, ensure_ascii=False, indent=2)
    
    with open(output_path / 'cache' / 'association_type_index.json', 'w', encoding='utf-8') as f:
        json.dump(association_type_index, f, ensure_ascii=False, indent=2)
    
    # Write external references summary
    with open(output_path / 'external_references' / 'external_references_summary.json', 'w', encoding='utf-8') as f:
        json.dump({
            'coverage_by_source': stats['external_reference_coverage'],
            'total_genes_with_references': len([g for g in gene_instances.values() if g['external_references']]),
            'reference_completeness': {
                source: (count / stats['unique_genes']) * 100 
                for source, count in stats['external_reference_coverage'].items()
            }
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Gene processing completed successfully")
    logger.info(f"Total disorders: {stats['total_disorders']}")
    logger.info(f"Disorders with genes: {stats['disorders_with_genes']}")
    logger.info(f"Total gene associations: {stats['total_gene_associations']}")
    logger.info(f"Unique genes: {stats['unique_genes']}")
    
    return stats

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Process Orpha gene data')
    parser.add_argument('--xml', default='data/01_raw/en_product6.xml', help='Path to XML file')
    parser.add_argument('--output', default='data/03_processed/orpha/orphadata/orpha_genes', help='Output directory')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Validate input file
    if not Path(args.xml).exists():
        logger.error(f"XML file not found: {args.xml}")
        sys.exit(1)
    
    try:
        stats = process_genes_xml(args.xml, args.output)
        logger.info("Processing completed successfully")
        
        if args.verbose:
            logger.info("Final statistics:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    logger.info(f"  {key}:")
                    for sub_key, sub_value in value.items():
                        logger.info(f"    {sub_key}: {sub_value}")
                else:
                    logger.info(f"  {key}: {value}")
                    
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 