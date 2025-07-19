#!/usr/bin/env python3
"""
Curate Disease Names

This script creates a mapping from orphacode to disease name using available data sources.

Usage:
    python curate_disease_names.py --input path/to/input/data --output path/to/output.json
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import existing clients
from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient


class DiseaseNamesCurator:
    """
    Creates orphacode to disease name mappings from available data sources.
    """
    
    def __init__(self, input_path: str, output_path: str):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        
        # Initialize ProcessedPrevalenceClient
        self.prevalence_client = ProcessedPrevalenceClient()
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def extract_names_from_disease_instances(self) -> Dict[str, str]:
        """Extract disease names from disease instances file"""
        orphacode2name = {}
        
        if not self.input_path.exists():
            self.logger.warning(f"Input file not found: {self.input_path}")
            return orphacode2name
        
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                disease_instances = json.load(f)
            
            for disease_info in disease_instances:
                if isinstance(disease_info, dict):
                    orpha_code = disease_info.get('orpha_code')
                    disease_name = disease_info.get('disease_name')
                    
                    if orpha_code and disease_name:
                        orphacode2name[orpha_code] = disease_name
            
            self.logger.info(f"Extracted {len(orphacode2name)} disease names from instances file")
            
        except Exception as e:
            self.logger.error(f"Error processing disease instances file: {e}")
        
        return orphacode2name

    def extract_names_from_orpha_index(self) -> Dict[str, str]:
        """Extract disease names from orpha index if available"""
        orphacode2name = {}
        
        try:
            orpha_index = self.prevalence_client.get_orpha_index()
            
            if orpha_index:
                for orpha_code, disease_info in orpha_index.items():
                    disease_name = disease_info.get('disease_name')
                    if disease_name:
                        orphacode2name[orpha_code] = disease_name
                
                self.logger.info(f"Extracted {len(orphacode2name)} disease names from orpha index")
            
        except Exception as e:
            self.logger.warning(f"Could not extract names from orpha index: {e}")
        
        return orphacode2name

    def merge_name_sources(self, *sources: Dict[str, str]) -> Dict[str, str]:
        """Merge multiple name sources, prioritizing first sources"""
        merged_names = {}
        
        for source in sources:
            for orpha_code, disease_name in source.items():
                if orpha_code not in merged_names:
                    merged_names[orpha_code] = disease_name
        
        return merged_names

    def create_orphacode2disease_name_mapping(self) -> Dict[str, str]:
        """Create comprehensive orphacode to disease name mapping"""
        self.logger.info("Creating orphacode to disease name mapping")
        
        # Extract names from different sources
        names_from_instances = self.extract_names_from_disease_instances()
        names_from_index = self.extract_names_from_orpha_index()
        
        # Merge sources (instances file takes priority)
        orphacode2name = self.merge_name_sources(
            names_from_instances,
            names_from_index
        )
        
        self.logger.info(f"Created mapping for {len(orphacode2name)} diseases")
        
        return orphacode2name

    def generate_creation_summary(self, orphacode2name: Dict[str, str]) -> Dict[str, Any]:
        """Generate summary of the creation process"""
        summary = {
            'creation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'input_path': str(self.input_path),
                'output_path': str(self.output_path),
                'script_version': '1.0.0'
            },
            'mapping_statistics': {
                'total_diseases': len(orphacode2name),
                'unique_names': len(set(orphacode2name.values())),
                'sample_mappings': dict(list(orphacode2name.items())[:5])
            },
            'data_quality': {
                'empty_names': len([name for name in orphacode2name.values() if not name or name.strip() == ""]),
                'average_name_length': sum(len(name) for name in orphacode2name.values()) / len(orphacode2name) if orphacode2name else 0,
                'shortest_name': min(orphacode2name.values(), key=len) if orphacode2name else None,
                'longest_name': max(orphacode2name.values(), key=len) if orphacode2name else None
            }
        }
        
        return summary

    def save_outputs(self, orphacode2name: Dict[str, str], summary: Dict[str, Any]) -> None:
        """Save outputs to files"""
        # Save main mapping
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(orphacode2name, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved orphacode2disease_name mapping to {self.output_path}")
        
        # Save summary
        summary_path = self.output_path.parent / f"{self.output_path.stem}_creation_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved creation summary to {summary_path}")

    def run(self) -> None:
        """Run the complete disease names curation process"""
        try:
            self.logger.info("Starting disease names curation process")
            
            # Create mapping
            orphacode2name = self.create_orphacode2disease_name_mapping()
            
            if not orphacode2name:
                self.logger.error("No disease names could be extracted from any source")
                return
            
            # Generate summary
            summary = self.generate_creation_summary(orphacode2name)
            
            # Save outputs
            self.save_outputs(orphacode2name, summary)
            
            self.logger.info("Disease names curation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error during disease names curation: {e}")
            raise


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Create orphacode to disease name mapping")
    
    parser.add_argument(
        '--input',
        required=True,
        help="Path to disease instances JSON file"
    )
    
    parser.add_argument(
        '--output',
        required=True,
        help="Path to output orphacode2disease_name.json file"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Create and run curator
    curator = DiseaseNamesCurator(
        input_path=args.input,
        output_path=args.output
    )
    
    curator.run()


if __name__ == "__main__":
    main() 