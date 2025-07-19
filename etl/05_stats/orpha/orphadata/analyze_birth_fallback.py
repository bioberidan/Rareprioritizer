#!/usr/bin/env python3
"""
Analyze Birth Prevalence Fallback

This script analyzes why the birth prevalence fallback didn't work for diseases
without prevalence data, providing detailed debugging information.

Usage:
    python analyze_birth_fallback.py --disease-subset path/to/subset.json 
                                    --processed-data path/to/processed.json
                                    --curated-data path/to/curated.json
                                    --output-dir path/to/output
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from collections import defaultdict, Counter


class BirthFallbackAnalyzer:
    """
    Analyzes birth prevalence fallback performance and identifies why it failed
    for diseases without prevalence data.
    """
    
    def __init__(self, disease_subset_path: str, processed_data_path: str, 
                 curated_data_path: str, output_dir: str):
        self.disease_subset_path = Path(disease_subset_path)
        self.processed_data_path = Path(processed_data_path)
        self.curated_data_path = Path(curated_data_path)
        self.output_dir = Path(output_dir)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Analysis results
        self.analysis_results = {
            'summary': {},
            'selection_method_breakdown': {},
            'diseases_without_prevalence': [],
            'birth_prevalence_candidates': [],
            'birth_fallback_failure_reasons': {},
            'recommendations': []
        }
        
    def load_data(self) -> tuple:
        """Load all required data files"""
        self.logger.info("Loading data files...")
        
        # Load disease subset
        with open(self.disease_subset_path, 'r', encoding='utf-8') as f:
            disease_subset = json.load(f)
        
        # Load processed prevalence data
        with open(self.processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        
        # Load curated results
        with open(self.curated_data_path, 'r', encoding='utf-8') as f:
            curated_data = json.load(f)
        
        self.logger.info(f"Loaded {len(disease_subset)} diseases from subset")
        self.logger.info(f"Loaded {len(processed_data)} diseases from processed data")
        self.logger.info(f"Loaded {len(curated_data)} diseases from curated data")
        
        return disease_subset, processed_data, curated_data
    
    def simulate_selection_algorithm(self, disease_data: Dict) -> Dict:
        """
        Simulate the selection algorithm to understand which priority was used
        """
        selection_trace = {
            'disease_code': disease_data.get('orpha_code'),
            'priority_used': None,
            'selected_prevalence_class': None,
            'priority_1_available': False,
            'priority_2_available': False,
            'priority_3_available': False,
            'priority_4_available': False,
            'failure_reason': None,
            'birth_prevalence_records': []
        }
        
        try:
            # Priority 1: Point prevalence from most_reliable_prevalence
            most_reliable = disease_data.get('most_reliable_prevalence')
            if most_reliable and most_reliable.get('prevalence_type') == 'Point prevalence':
                selection_trace['priority_1_available'] = True
                selection_trace['priority_used'] = 1
                selection_trace['selected_prevalence_class'] = most_reliable.get('prevalence_class')
                return selection_trace
            
            # Get prevalence records for fallback analysis
            prevalence_records = disease_data.get('prevalence_records', [])
            if not prevalence_records:
                selection_trace['failure_reason'] = 'No prevalence records available'
                return selection_trace
            
            # Filter reliable records (reliability_score >= 6.0)
            reliable_records = [r for r in prevalence_records if r.get('reliability_score', 0) >= 6.0]
            if not reliable_records:
                reliable_records = prevalence_records  # Use all if none are reliable
            
            # Priority 2: Worldwide records
            worldwide_records = [r for r in reliable_records if r.get('geographic_area') == 'Worldwide']
            if worldwide_records:
                selection_trace['priority_2_available'] = True
                selection_trace['priority_used'] = 2
                best_record = max(worldwide_records, key=lambda x: x.get('reliability_score', 0))
                selection_trace['selected_prevalence_class'] = best_record.get('prevalence_class')
                return selection_trace
            
            # Priority 3: Regional records
            regional_records = [r for r in reliable_records if r.get('geographic_area') != 'Worldwide']
            if regional_records:
                selection_trace['priority_3_available'] = True
                selection_trace['priority_used'] = 3
                best_record = max(regional_records, key=lambda x: x.get('reliability_score', 0))
                selection_trace['selected_prevalence_class'] = best_record.get('prevalence_class')
                return selection_trace
            
            # Priority 4: Birth prevalence fallback
            birth_prevalence_records = [r for r in prevalence_records 
                                       if r.get('prevalence_type') == 'Prevalence at birth']
            
            selection_trace['birth_prevalence_records'] = birth_prevalence_records
            
            if birth_prevalence_records:
                selection_trace['priority_4_available'] = True
                # Use most reliable birth prevalence record
                best_birth_record = max(birth_prevalence_records, 
                                       key=lambda x: x.get('reliability_score', 0))
                birth_class = best_birth_record.get('prevalence_class')
                
                if birth_class:
                    estimated_point_class = self.birth2point(birth_class)
                    if estimated_point_class != "Unknown":
                        selection_trace['priority_used'] = 4
                        selection_trace['selected_prevalence_class'] = estimated_point_class
                        return selection_trace
                    else:
                        selection_trace['failure_reason'] = 'Birth prevalence mapped to Unknown'
                else:
                    selection_trace['failure_reason'] = 'Birth prevalence record has no prevalence_class'
            else:
                selection_trace['failure_reason'] = 'No birth prevalence records available'
            
            # No suitable records found
            selection_trace['failure_reason'] = selection_trace.get('failure_reason', 'No suitable records after all priorities')
            return selection_trace
            
        except Exception as e:
            selection_trace['failure_reason'] = f'Error during selection: {e}'
            return selection_trace
    
    def birth2point(self, birth_category: str) -> str:
        """
        Convert birth prevalence category to estimated point prevalence category.
        """
        mapping = {
            ">1 / 1000":           "6-9 / 10 000",
            "6-9 / 10 000":        "1-5 / 10 000", 
            "1-5 / 10 000":        "1-9 / 100 000",
            "1-9 / 100 000":       "1-9 / 1 000 000",
            "1-9 / 1 000 000":     "<1 / 1 000 000",
            "<1 / 1 000 000":      "<1 / 1 000 000",
            "Unknown":             "Unknown",
            "Not yet documented":  "Unknown"
        }
        return mapping.get(birth_category, "Unknown")
    
    def analyze_diseases_without_prevalence(self, disease_subset: List[Dict], 
                                          processed_data: Dict, curated_data: Dict) -> List[Dict]:
        """
        Analyze diseases that ended up without prevalence data
        """
        self.logger.info("Analyzing diseases without prevalence...")
        
        diseases_without_prevalence = []
        
        for disease_info in disease_subset:
            disease_code = disease_info['orpha_code']
            
            # Check if disease has "Unknown" prevalence in curated data
            curated_prevalence = curated_data.get(disease_code, "Unknown")
            
            if curated_prevalence == "Unknown":
                analysis = {
                    'disease_code': disease_code,
                    'disease_name': disease_info['disease_name'],
                    'curated_prevalence': curated_prevalence,
                    'has_raw_data': disease_code in processed_data,
                    'selection_trace': None,
                    'birth_prevalence_analysis': None
                }
                
                # If disease has raw data, analyze why it failed
                if disease_code in processed_data:
                    disease_data = processed_data[disease_code]
                    analysis['selection_trace'] = self.simulate_selection_algorithm(disease_data)
                    
                    # Detailed birth prevalence analysis
                    birth_records = [r for r in disease_data.get('prevalence_records', []) 
                                   if r.get('prevalence_type') == 'Prevalence at birth']
                    
                    if birth_records:
                        analysis['birth_prevalence_analysis'] = {
                            'birth_records_count': len(birth_records),
                            'birth_records': birth_records,
                            'best_birth_record': max(birth_records, key=lambda x: x.get('reliability_score', 0)),
                            'birth_to_point_mappings': []
                        }
                        
                        # Show birth-to-point mappings
                        for record in birth_records:
                            birth_class = record.get('prevalence_class')
                            if birth_class:
                                estimated_point = self.birth2point(birth_class)
                                analysis['birth_prevalence_analysis']['birth_to_point_mappings'].append({
                                    'birth_class': birth_class,
                                    'estimated_point_class': estimated_point,
                                    'reliability_score': record.get('reliability_score', 0)
                                })
                
                diseases_without_prevalence.append(analysis)
        
        self.logger.info(f"Found {len(diseases_without_prevalence)} diseases without prevalence")
        return diseases_without_prevalence
    
    def categorize_failure_reasons(self, diseases_without_prevalence: List[Dict]) -> Dict:
        """
        Categorize why diseases failed to get prevalence data
        """
        failure_categories = defaultdict(list)
        
        for disease in diseases_without_prevalence:
            if not disease['has_raw_data']:
                failure_categories['No raw data available'].append(disease)
            elif disease['selection_trace']:
                reason = disease['selection_trace']['failure_reason']
                if reason:
                    failure_categories[reason].append(disease)
                else:
                    failure_categories['Unknown failure'].append(disease)
            else:
                failure_categories['Selection trace failed'].append(disease)
        
        return dict(failure_categories)
    
    def generate_recommendations(self, failure_categories: Dict) -> List[str]:
        """
        Generate recommendations based on failure analysis
        """
        recommendations = []
        
        if 'No raw data available' in failure_categories:
            count = len(failure_categories['No raw data available'])
            recommendations.append(
                f"Data Gap: {count} diseases have no prevalence data in the processed dataset. "
                f"Consider expanding data collection or using alternative prevalence estimation methods."
            )
        
        if 'No prevalence records available' in failure_categories:
            count = len(failure_categories['No prevalence records available'])
            recommendations.append(
                f"Processing Issue: {count} diseases have empty prevalence_records. "
                f"Check the preprocessing pipeline for these diseases."
            )
        
        if 'Birth prevalence mapped to Unknown' in failure_categories:
            count = len(failure_categories['Birth prevalence mapped to Unknown'])
            recommendations.append(
                f"Mapping Issue: {count} diseases have birth prevalence that maps to 'Unknown'. "
                f"Consider improving the birth2point mapping function or handling these cases specially."
            )
        
        if 'No birth prevalence records available' in failure_categories:
            count = len(failure_categories['No birth prevalence records available'])
            recommendations.append(
                f"Birth Fallback Gap: {count} diseases have no birth prevalence records. "
                f"The birth fallback cannot help these diseases - they need other types of prevalence data."
            )
        
        return recommendations
    
    def save_analysis_results(self, analysis_results: Dict) -> None:
        """Save analysis results to JSON files"""
        
        # Save main analysis results
        main_output = self.output_dir / "birth_fallback_analysis.json"
        with open(main_output, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved main analysis to {main_output}")
        
        # Save detailed disease analysis
        diseases_output = self.output_dir / "diseases_without_prevalence_detailed.json"
        with open(diseases_output, 'w', encoding='utf-8') as f:
            json.dump(analysis_results['diseases_without_prevalence'], f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved detailed disease analysis to {diseases_output}")
        
        # Save failure categories
        failure_output = self.output_dir / "failure_categories.json"
        with open(failure_output, 'w', encoding='utf-8') as f:
            json.dump(analysis_results['birth_fallback_failure_reasons'], f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved failure categories to {failure_output}")
        
        # Create human-readable summary
        summary_output = self.output_dir / "analysis_summary.txt"
        with open(summary_output, 'w', encoding='utf-8') as f:
            f.write("=== BIRTH PREVALENCE FALLBACK ANALYSIS SUMMARY ===\n\n")
            
            f.write("OVERVIEW:\n")
            f.write(f"- Total diseases analyzed: {analysis_results['summary']['total_diseases']}\n")
            f.write(f"- Diseases without prevalence: {analysis_results['summary']['diseases_without_prevalence']}\n")
            f.write(f"- Diseases with birth prevalence records: {analysis_results['summary']['diseases_with_birth_records']}\n\n")
            
            f.write("FAILURE REASONS:\n")
            for reason, diseases in analysis_results['birth_fallback_failure_reasons'].items():
                f.write(f"- {reason}: {len(diseases)} diseases\n")
            
            f.write("\nRECOMMENDATIONS:\n")
            for i, rec in enumerate(analysis_results['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
        
        self.logger.info(f"Saved human-readable summary to {summary_output}")
    
    def run_analysis(self) -> None:
        """Run the complete birth fallback analysis"""
        try:
            self.logger.info("Starting birth prevalence fallback analysis")
            
            # Load data
            disease_subset, processed_data, curated_data = self.load_data()
            
            # Analyze diseases without prevalence
            diseases_without_prevalence = self.analyze_diseases_without_prevalence(
                disease_subset, processed_data, curated_data
            )
            
            # Categorize failure reasons
            failure_categories = self.categorize_failure_reasons(diseases_without_prevalence)
            
            # Generate recommendations
            recommendations = self.generate_recommendations(failure_categories)
            
            # Count diseases with birth prevalence records
            diseases_with_birth_records = sum(1 for d in diseases_without_prevalence 
                                            if d.get('birth_prevalence_analysis') is not None)
            
            # Compile analysis results
            self.analysis_results = {
                'processing_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'disease_subset_path': str(self.disease_subset_path),
                    'processed_data_path': str(self.processed_data_path),
                    'curated_data_path': str(self.curated_data_path),
                    'output_dir': str(self.output_dir)
                },
                'summary': {
                    'total_diseases': len(disease_subset),
                    'diseases_without_prevalence': len(diseases_without_prevalence),
                    'diseases_with_birth_records': diseases_with_birth_records,
                    'failure_categories_count': len(failure_categories)
                },
                'diseases_without_prevalence': diseases_without_prevalence,
                'birth_fallback_failure_reasons': failure_categories,
                'recommendations': recommendations
            }
            
            # Save results
            self.save_analysis_results(self.analysis_results)
            
            # Print summary
            self.logger.info("=== ANALYSIS COMPLETE ===")
            self.logger.info(f"Total diseases: {len(disease_subset)}")
            self.logger.info(f"Diseases without prevalence: {len(diseases_without_prevalence)}")
            self.logger.info(f"Diseases with birth records: {diseases_with_birth_records}")
            self.logger.info(f"Failure categories: {len(failure_categories)}")
            
            for reason, diseases in failure_categories.items():
                self.logger.info(f"  - {reason}: {len(diseases)} diseases")
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {e}")
            raise


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Analyze birth prevalence fallback performance")
    
    parser.add_argument(
        '--disease-subset',
        required=True,
        help="Path to disease subset JSON file"
    )
    
    parser.add_argument(
        '--processed-data',
        required=True,
        help="Path to processed prevalence data JSON file"
    )
    
    parser.add_argument(
        '--curated-data',
        required=True,
        help="Path to curated prevalence data JSON file"
    )
    
    parser.add_argument(
        '--output-dir',
        required=True,
        help="Output directory for analysis results"
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
    
    # Create and run analyzer
    analyzer = BirthFallbackAnalyzer(
        disease_subset_path=args.disease_subset,
        processed_data_path=args.processed_data,
        curated_data_path=args.curated_data,
        output_dir=args.output_dir
    )
    
    analyzer.run_analysis()


if __name__ == "__main__":
    main() 