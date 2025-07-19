#!/usr/bin/env python3
"""
Websearch Socioeconomic Statistics and Analysis

This script generates statistics and visualization for websearch socioeconomic data.
Generates only a bar chart showing count of diseases per evidence level, including "No evidence".

Input: data/04_curated/websearch/socioeconomic/
Output: results/etl/subset_of_disease_instances/socioeconomic/websearch/

Analysis includes:
- Evidence level distribution bar chart with "No evidence" category
"""

import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import sys

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.datastore.websearch.curated_websearch_socioeconomic_client import CuratedWebsearchSocioeconomicClient

logger = logging.getLogger(__name__)


class WebsearchSocioeconomicStatsAnalyzer:
    """
    Statistics and analysis for websearch socioeconomic data
    
    Generates bar chart visualization for evidence level distribution with "No evidence" category.
    """
    
    def __init__(self, output_dir: Path, total_diseases: int = 25):
        """
        Initialize the analyzer
        
        Args:
            output_dir: Directory to save analysis results
            total_diseases: Total number of diseases (including failed ones)
        """
        self.output_dir = output_dir
        self.total_diseases = total_diseases
        self.client = CuratedWebsearchSocioeconomicClient()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_evidence_level_barchart(self) -> None:
        """
        Generate bar chart showing count of diseases per evidence level, including "No evidence"
        """
        logger.info("Generating evidence level distribution bar chart")
        
        # Get evidence level distribution from curated data
        distribution = self.client.get_evidence_level_distribution()
        
        if not distribution:
            logger.warning("No evidence level data available for bar chart")
            return
        
        # Calculate diseases with evidence and those without
        diseases_with_evidence = sum(distribution.values())
        diseases_no_evidence = self.total_diseases - diseases_with_evidence
        
        # Add "No evidence" to the distribution
        distribution["No evidence"] = diseases_no_evidence
        
        # Prepare data for bar chart
        evidence_levels = list(distribution.keys())
        counts = list(distribution.values())
        
        logger.info(f"Evidence level distribution: {distribution}")
        logger.info(f"Total diseases: {self.total_diseases}, With evidence: {diseases_with_evidence}, No evidence: {diseases_no_evidence}")
        
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Define colors for different evidence levels
        colors = {
            'High evidence': '#d62728',        # Red
            'Medium-High evidence': '#ff7f0e', # Orange  
            'Medium evidence': '#2ca02c',      # Green
            'Low evidence': '#1f77b4',        # Blue
            'No evidence': '#7f7f7f'          # Gray
        }
        
        # Get colors for each evidence level
        bar_colors = [colors.get(level, '#17becf') for level in evidence_levels]
        
        # Create bar chart
        bars = plt.bar(evidence_levels, counts, color=bar_colors, alpha=0.8, edgecolor='black', linewidth=1)
        
        # Customize the plot
        plt.title('Socioeconomic Evidence Level Distribution', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Evidence Level', fontsize=12, fontweight='bold')
        plt.ylabel('Number of Diseases', fontsize=12, fontweight='bold')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45, ha='right')
        
        # Add value labels on top of bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(count)}', ha='center', va='bottom', fontweight='bold')
        
        # Add grid for better readability
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save plot
        output_file = self.output_dir / 'evidence_level_distribution_barchart.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Evidence level distribution bar chart saved to: {output_file}")
        
        # Log summary statistics
        logger.info(f"Summary statistics:")
        logger.info(f"  Total diseases analyzed: {self.total_diseases}")
        logger.info(f"  Diseases with evidence: {diseases_with_evidence}")
        logger.info(f"  Diseases without evidence: {diseases_no_evidence}")
        for level, count in distribution.items():
            percentage = (count / self.total_diseases) * 100
            logger.info(f"  {level}: {count} ({percentage:.1f}%)")
    
    def run_analysis(self) -> None:
        """
        Run the complete analysis pipeline
        """
        logger.info("Starting socioeconomic evidence analysis")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Total diseases: {self.total_diseases}")
        
        # Generate the bar chart
        self.generate_evidence_level_barchart()
        
        logger.info("Socioeconomic evidence analysis completed successfully")


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main function to run socioeconomic statistics analysis"""
    parser = argparse.ArgumentParser(description='Generate socioeconomic evidence statistics and visualizations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--total-diseases', type=int, default=25, help='Total number of diseases (default: 25)')
    parser.add_argument('--output-dir', type=str, 
                       default='results/etl/subset_of_disease_instances/socioeconomic/websearch',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Convert output directory to Path
    output_dir = Path(args.output_dir)
    
    try:
        # Create analyzer and run analysis
        analyzer = WebsearchSocioeconomicStatsAnalyzer(
            output_dir=output_dir,
            total_diseases=args.total_diseases
        )
        analyzer.run_analysis()
        
        logger.info("Analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 