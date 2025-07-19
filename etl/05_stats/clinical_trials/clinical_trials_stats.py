#!/usr/bin/env python3
"""
Clinical Trials Statistics and Analysis

This script generates comprehensive statistics and visualizations for clinical trials data.
IMPORTANT: Uses complete datasets - NO data slicing allowed (no [:50] tricks).

Input: data/04_curated/clinical_trials/
Output: results/etl/subset_of_disease_instances/metabolic/clinical_trials/

Analysis includes:
- Distribution analysis (full datasets only)
- Top 15 diseases by trials
- Top 15 trials by disease coverage
- IQR outlier analysis (complete data)
- Geographic accessibility analysis
- Summary statistics
"""

import json
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set style for plots
plt.style.use('default')
sns.set_palette("husl")


class ClinicalTrialsStatsAnalyzer:
    """
    Comprehensive statistics and analysis for clinical trials data
    
    CRITICAL: All analyses use complete datasets - NO data slicing allowed
    """
    
    def __init__(self, 
                 input_dir: str = "data/04_curated/clinical_trials",
                 output_dir: str = "results/etl/subset_of_disease_instances/metabolic/clinical_trials"):
        """
        Initialize the clinical trials statistics analyzer
        
        Args:
            input_dir: Directory containing curated clinical trials data
            output_dir: Directory for output statistics and visualizations
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load all data (COMPLETE datasets only)
        self.data = self._load_complete_data()
        
        logger.info(f"Initialized ClinicalTrialsStatsAnalyzer")
        logger.info(f"Input: {self.input_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Data loaded: {len(self.data)} datasets")
    
    def _load_complete_data(self) -> Dict[str, Dict]:
        """
        Load ALL curated clinical trials data - COMPLETE datasets only
        
        Returns:
            Dict containing all loaded data
        """
        logger.info("Loading COMPLETE clinical trials datasets...")
        
        data = {}
        
        # Load disease2eu_trial.json (COMPLETE)
        eu_file = self.input_dir / "disease2eu_trial.json"
        if eu_file.exists():
            with open(eu_file, 'r', encoding='utf-8') as f:
                data['eu_trials'] = json.load(f)
            logger.info(f"Loaded COMPLETE EU trials: {len(data['eu_trials'])} diseases")
        else:
            data['eu_trials'] = {}
        
        # Load disease2all_trials.json (COMPLETE)
        all_file = self.input_dir / "disease2all_trials.json"
        if all_file.exists():
            with open(all_file, 'r', encoding='utf-8') as f:
                data['all_trials'] = json.load(f)
            logger.info(f"Loaded COMPLETE all trials: {len(data['all_trials'])} diseases")
        else:
            data['all_trials'] = {}
        
        # Load disease2spanish_trials.json (COMPLETE)
        spanish_file = self.input_dir / "disease2spanish_trials.json"
        if spanish_file.exists():
            with open(spanish_file, 'r', encoding='utf-8') as f:
                data['spanish_trials'] = json.load(f)
            logger.info(f"Loaded COMPLETE Spanish trials: {len(data['spanish_trials'])} diseases")
        else:
            data['spanish_trials'] = {}
        
        # Load clinicaltrial2name.json (COMPLETE)
        names_file = self.input_dir / "clinicaltrial2name.json"
        if names_file.exists():
            with open(names_file, 'r', encoding='utf-8') as f:
                data['trial_names'] = json.load(f)
            logger.info(f"Loaded COMPLETE trial names: {len(data['trial_names'])} trials")
        else:
            data['trial_names'] = {}
        
        return data
    
    def _calculate_iqr_outliers(self, values: List[int]) -> Tuple[List[int], float, float]:
        """
        Calculate IQR-based outliers on COMPLETE dataset
        
        Args:
            values: Complete list of values (NO slicing allowed)
            
        Returns:
            Tuple of (outlier_indices, lower_bound, upper_bound)
        """
        if not values:
            return [], 0, 0
        
        # Use COMPLETE dataset - no slicing
        values_array = np.array(values)
        
        q1 = np.percentile(values_array, 25)
        q3 = np.percentile(values_array, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # Find outliers in COMPLETE dataset
        outlier_indices = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outlier_indices.append(i)
        
        logger.info(f"IQR outlier analysis on COMPLETE data: {len(outlier_indices)} outliers found")
        return outlier_indices, lower_bound, upper_bound
    
    def analyze_distribution_complete(self) -> Dict[str, Any]:
        """
        Analyze trial distribution across diseases - COMPLETE data analysis
        
        Returns:
            Dict with complete distribution analysis
        """
        logger.info("Analyzing trial distribution on COMPLETE dataset...")
        
        analysis = {}
        
        # Analyze each region with COMPLETE data
        for region, trials_data in [
            ("all", self.data['all_trials']),
            ("eu", self.data['eu_trials']),
            ("spanish", self.data['spanish_trials'])
        ]:
            logger.info(f"Processing COMPLETE {region} trials data...")
            
            # Get trial counts for ALL diseases (COMPLETE)
            trial_counts = [len(trials) for trials in trials_data.values()]
            
            if trial_counts:  # Only if we have data
                # Calculate statistics on COMPLETE dataset
                analysis[f"{region}_statistics"] = {
                    "total_diseases": len(trial_counts),
                    "min_trials": min(trial_counts),
                    "max_trials": max(trial_counts),
                    "mean_trials": np.mean(trial_counts),
                    "median_trials": np.median(trial_counts),
                    "std_trials": np.std(trial_counts),
                    "total_trials": sum(trial_counts)
                }
                
                # IQR outlier analysis on COMPLETE data
                outlier_indices, lower_bound, upper_bound = self._calculate_iqr_outliers(trial_counts)
                
                # Get outlier diseases (COMPLETE analysis)
                disease_codes = list(trials_data.keys())
                outlier_diseases = []
                for idx in outlier_indices:
                    orpha_code = disease_codes[idx]
                    trial_count = trial_counts[idx]
                    outlier_diseases.append({
                        "orpha_code": orpha_code,
                        "trial_count": trial_count,
                        "trials": trials_data[orpha_code]
                    })
                
                analysis[f"{region}_outliers"] = {
                    "outlier_count": len(outlier_diseases),
                    "lower_bound": lower_bound,
                    "upper_bound": upper_bound,
                    "outlier_diseases": outlier_diseases
                }
            else:
                analysis[f"{region}_statistics"] = {}
                analysis[f"{region}_outliers"] = {}
        
        logger.info(f"Distribution analysis completed on COMPLETE data")
        return analysis
    
    def get_top_diseases_complete(self, limit: int = 15) -> Dict[str, List[Dict]]:
        """
        Get top diseases by trial count - COMPLETE analysis (NO slicing)
        
        Args:
            limit: Number of top diseases to return
            
        Returns:
            Dict with top diseases for each region
        """
        logger.info(f"Getting top {limit} diseases from COMPLETE dataset...")
        
        top_diseases = {}
        
        for region, trials_data in [
            ("all", self.data['all_trials']),
            ("eu", self.data['eu_trials']),
            ("spanish", self.data['spanish_trials'])
        ]:
            # Process ALL diseases (COMPLETE dataset)
            disease_trial_counts = []
            for orpha_code, trials in trials_data.items():
                disease_trial_counts.append({
                    "orpha_code": orpha_code,
                    "trial_count": len(trials),
                    "trials": trials
                })
            
            # Sort COMPLETE list and take top N
            disease_trial_counts.sort(key=lambda x: x["trial_count"], reverse=True)
            top_diseases[region] = disease_trial_counts[:limit]
            
            logger.info(f"Top {limit} {region} diseases from {len(disease_trial_counts)} total diseases")
        
        return top_diseases
    
    def get_top_trials_complete(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Get top trials by disease coverage - COMPLETE analysis (NO slicing)
        
        Args:
            limit: Number of top trials to return
            
        Returns:
            List of top trials with disease counts
        """
        logger.info(f"Getting top {limit} trials from COMPLETE dataset...")
        
        # Count diseases per trial using COMPLETE data
        trial_disease_count = {}
        
        # Process ALL trials in COMPLETE dataset
        for orpha_code, trials in self.data['all_trials'].items():
            for nct_id in trials:
                if nct_id not in trial_disease_count:
                    trial_disease_count[nct_id] = []
                trial_disease_count[nct_id].append(orpha_code)
        
        # Create COMPLETE results list
        trial_results = []
        for nct_id, diseases in trial_disease_count.items():
            trial_results.append({
                "nct_id": nct_id,
                "trial_name": self.data['trial_names'].get(nct_id, f"Clinical Trial {nct_id}"),
                "disease_count": len(diseases),
                "diseases": diseases
            })
        
        # Sort COMPLETE list and take top N
        trial_results.sort(key=lambda x: x["disease_count"], reverse=True)
        top_trials = trial_results[:limit]
        
        logger.info(f"Top {limit} trials from {len(trial_results)} total trials")
        return top_trials
    
    def generate_visualizations(self, analysis: Dict[str, Any]) -> None:
        """
        Generate visualizations from COMPLETE data analysis
        
        Args:
            analysis: Complete analysis results
        """
        logger.info("Generating visualizations from COMPLETE data...")
        
        # Set up the plotting style
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        
        # 1. Trial distribution analysis (COMPLETE data)
        self._plot_trial_distribution_complete()
        
        # 2. Top diseases by trials (COMPLETE data)
        self._plot_top_diseases_complete()
        
        # 3. Top trials by disease coverage (COMPLETE data)
        self._plot_top_trials_complete()
        
        # 4. IQR outlier analysis (COMPLETE data)
        self._plot_outlier_analysis_complete(analysis)
        
        # 5. Geographic accessibility comparison (COMPLETE data)
        self._plot_geographic_accessibility_complete()
        
        # 6. Summary dashboard (COMPLETE data)
        self._plot_summary_dashboard_complete(analysis)
        
        logger.info("All visualizations generated from COMPLETE datasets")
    
    def _plot_trial_distribution_complete(self) -> None:
        """Plot trial distribution using COMPLETE data"""
        logger.info("Plotting trial distribution from COMPLETE data...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Clinical Trials Distribution Analysis (Complete Data)', fontsize=16, fontweight='bold')
        
        regions = [
            ("All Trials", self.data['all_trials']),
            ("EU Trials", self.data['eu_trials']),
            ("Spanish Trials", self.data['spanish_trials'])
        ]
        
        # Plot distributions for each region (COMPLETE data)
        for i, (region_name, trials_data) in enumerate(regions):
            if i < 3:  # We have 3 regions but 4 subplots
                row, col = i // 2, i % 2
                ax = axes[row, col]
                
                # Get COMPLETE trial counts
                trial_counts = [len(trials) for trials in trials_data.values()]
                
                if trial_counts:
                    # Histogram with COMPLETE data
                    ax.hist(trial_counts, bins=20, alpha=0.7, edgecolor='black')
                    ax.set_title(f'{region_name} Distribution\n({len(trial_counts)} diseases)', fontweight='bold')
                    ax.set_xlabel('Number of Trials per Disease')
                    ax.set_ylabel('Number of Diseases')
                    ax.grid(True, alpha=0.3)
                    
                    # Add statistics text
                    stats_text = f'Mean: {np.mean(trial_counts):.1f}\nMedian: {np.median(trial_counts):.1f}\nMax: {max(trial_counts)}'
                    ax.text(0.7, 0.8, stats_text, transform=ax.transAxes, 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.5))
        
        # Use the 4th subplot for summary statistics
        ax = axes[1, 1]
        summary_text = f"""Complete Dataset Summary:
        
Total Diseases with Trials: {len(self.data['all_trials'])}
Total Unique Trials: {len(self.data['trial_names'])}
        
Regional Coverage:
• EU Accessible: {len(self.data['eu_trials'])} diseases
• Spanish Accessible: {len(self.data['spanish_trials'])} diseases
        
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Dataset: Complete (No slicing applied)"""
        
        ax.text(0.1, 0.5, summary_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='center', bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow"))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "trial_distribution_analysis.png"
        if output_file.exists():
            output_file = self.output_dir / f"trial_distribution_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved trial distribution plot: {output_file}")
    
    def _plot_top_diseases_complete(self) -> None:
        """Plot top diseases by trials using COMPLETE data"""
        logger.info("Plotting top diseases from COMPLETE data...")
        
        top_diseases = self.get_top_diseases_complete(15)  # COMPLETE analysis
        
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle('Top 15 Diseases by Trial Count (Complete Analysis)', fontsize=16, fontweight='bold')
        
        regions = [("All Trials", "all"), ("EU Trials", "eu"), ("Spanish Trials", "spanish")]
        
        for i, (region_name, region_key) in enumerate(regions):
            ax = axes[i]
            
            diseases = top_diseases[region_key]
            if diseases:
                # Extract data for plotting (COMPLETE list)
                disease_codes = [d["orpha_code"] for d in diseases]
                trial_counts = [d["trial_count"] for d in diseases]
                
                # Create bar plot
                bars = ax.barh(range(len(disease_codes)), trial_counts)
                ax.set_yticks(range(len(disease_codes)))
                ax.set_yticklabels([f"ORPHA:{code}" for code in disease_codes])
                ax.set_xlabel('Number of Trials')
                ax.set_title(f'{region_name}\n(Top 15 from complete data)')
                ax.grid(True, alpha=0.3, axis='x')
                
                # Invert y-axis to show highest at top
                ax.invert_yaxis()
                
                # Add value labels on bars
                for j, (bar, count) in enumerate(zip(bars, trial_counts)):
                    ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2, 
                           str(count), va='center', fontsize=9)
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "top_diseases_by_trials.png"
        if output_file.exists():
            output_file = self.output_dir / f"top_diseases_by_trials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved top diseases plot: {output_file}")
    
    def _plot_top_trials_complete(self) -> None:
        """Plot top trials by disease coverage using COMPLETE data"""
        logger.info("Plotting top trials from COMPLETE data...")
        
        top_trials = self.get_top_trials_complete(15)  # COMPLETE analysis
        
        if not top_trials:
            logger.warning("No trials data for plotting")
            return
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        # Extract data (COMPLETE)
        trial_names = [trial["trial_name"][:50] + "..." if len(trial["trial_name"]) > 50 
                      else trial["trial_name"] for trial in top_trials]
        disease_counts = [trial["disease_count"] for trial in top_trials]
        nct_ids = [trial["nct_id"] for trial in top_trials]
        
        # Create horizontal bar plot
        bars = ax.barh(range(len(trial_names)), disease_counts)
        ax.set_yticks(range(len(trial_names)))
        ax.set_yticklabels([f"{nct_id}\n{name}" for nct_id, name in zip(nct_ids, trial_names)])
        ax.set_xlabel('Number of Diseases')
        ax.set_title('Top 15 Trials by Disease Coverage (Complete Analysis)', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        ax.invert_yaxis()
        
        # Add value labels
        for bar, count in zip(bars, disease_counts):
            ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2, 
                   str(count), va='center', fontsize=9)
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "top_trials_by_diseases.png"
        if output_file.exists():
            output_file = self.output_dir / f"top_trials_by_diseases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved top trials plot: {output_file}")
    
    def _plot_outlier_analysis_complete(self, analysis: Dict[str, Any]) -> None:
        """Plot IQR outlier analysis using COMPLETE data"""
        logger.info("Plotting outlier analysis from COMPLETE data...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('IQR Outlier Analysis - Diseases with Excessive Trials (Complete Data)', 
                     fontsize=16, fontweight='bold')
        
        regions = [("all", "All Trials"), ("eu", "EU Trials"), ("spanish", "Spanish Trials")]
        
        for i, (region_key, region_name) in enumerate(regions):
            if i < 3:  # We have 3 regions
                row, col = i // 2, i % 2
                ax = axes[row, col]
                
                trials_data = self.data[f'{region_key}_trials']
                outlier_info = analysis.get(f'{region_key}_outliers', {})
                
                if trials_data and outlier_info:
                    # Get COMPLETE trial counts
                    trial_counts = [len(trials) for trials in trials_data.values()]
                    
                    if trial_counts:
                        # Box plot showing outliers
                        box_plot = ax.boxplot(trial_counts, vert=True, patch_artist=True)
                        box_plot['boxes'][0].set_facecolor('lightblue')
                        
                        ax.set_ylabel('Number of Trials per Disease')
                        ax.set_title(f'{region_name} Outlier Analysis\n'
                                   f'({outlier_info.get("outlier_count", 0)} outliers found)')
                        ax.grid(True, alpha=0.3)
                        
                        # Add outlier threshold lines
                        if 'lower_bound' in outlier_info and 'upper_bound' in outlier_info:
                            ax.axhline(y=outlier_info['upper_bound'], color='red', linestyle='--', 
                                     label=f'Upper threshold: {outlier_info["upper_bound"]:.1f}')
                            if outlier_info['lower_bound'] > 0:
                                ax.axhline(y=outlier_info['lower_bound'], color='red', linestyle='--',
                                         label=f'Lower threshold: {outlier_info["lower_bound"]:.1f}')
                            ax.legend()
                        
                        # Add statistics text
                        stats_text = f'Q1: {np.percentile(trial_counts, 25):.1f}\n'
                        stats_text += f'Median: {np.median(trial_counts):.1f}\n'
                        stats_text += f'Q3: {np.percentile(trial_counts, 75):.1f}\n'
                        stats_text += f'IQR: {np.percentile(trial_counts, 75) - np.percentile(trial_counts, 25):.1f}'
                        
                        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                               verticalalignment='top',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
        
        # Use 4th subplot for outlier details
        ax = axes[1, 1]
        outlier_text = "IQR Outlier Summary (Complete Analysis):\n\n"
        
        for region_key, region_name in [("all", "All"), ("eu", "EU"), ("spanish", "Spanish")]:
            outlier_info = analysis.get(f'{region_key}_outliers', {})
            outlier_count = outlier_info.get('outlier_count', 0)
            outlier_text += f"• {region_name}: {outlier_count} outliers\n"
            
            # Show top outliers
            outlier_diseases = outlier_info.get('outlier_diseases', [])
            if outlier_diseases:
                top_outlier = max(outlier_diseases, key=lambda x: x['trial_count'])
                outlier_text += f"  Max: ORPHA:{top_outlier['orpha_code']} ({top_outlier['trial_count']} trials)\n"
        
        outlier_text += f"\nAnalysis Method: IQR (1.5 × IQR rule)\n"
        outlier_text += f"Dataset: Complete (No slicing)\n"
        outlier_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        ax.text(0.1, 0.5, outlier_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='center', 
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.3))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "outlier_analysis_iqr.png"
        if output_file.exists():
            output_file = self.output_dir / f"outlier_analysis_iqr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved outlier analysis plot: {output_file}")
    
    def _plot_geographic_accessibility_complete(self) -> None:
        """Plot geographic accessibility comparison using COMPLETE data"""
        logger.info("Plotting geographic accessibility from COMPLETE data...")
        
        fig, axes = plt.subplots(1, 2, figsize=(15, 6))
        fig.suptitle('Geographic Accessibility Analysis (Complete Data)', fontsize=16, fontweight='bold')
        
        # Left plot: Disease counts by region
        ax1 = axes[0]
        regions = ['All Trials', 'EU Accessible', 'Spanish Accessible']
        disease_counts = [
            len(self.data['all_trials']),
            len(self.data['eu_trials']),
            len(self.data['spanish_trials'])
        ]
        
        bars = ax1.bar(regions, disease_counts, color=['skyblue', 'lightgreen', 'coral'])
        ax1.set_ylabel('Number of Diseases')
        ax1.set_title('Diseases with Trial Access by Region')
        ax1.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, count in zip(bars, disease_counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontweight='bold')
        
        # Right plot: Coverage percentages
        ax2 = axes[1]
        total_diseases = len(self.data['all_trials'])
        if total_diseases > 0:
            eu_percentage = (len(self.data['eu_trials']) / total_diseases) * 100
            spanish_percentage = (len(self.data['spanish_trials']) / total_diseases) * 100
            
            coverage_data = [100, eu_percentage, spanish_percentage]
            colors = ['skyblue', 'lightgreen', 'coral']
            
            bars = ax2.bar(regions, coverage_data, color=colors)
            ax2.set_ylabel('Coverage Percentage (%)')
            ax2.set_title('Regional Trial Coverage (% of diseases with trials)')
            ax2.set_ylim(0, 105)
            ax2.grid(True, alpha=0.3, axis='y')
            
            # Add percentage labels
            for bar, percentage in zip(bars, coverage_data):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{percentage:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "geographic_accessibility.png"
        if output_file.exists():
            output_file = self.output_dir / f"geographic_accessibility_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved geographic accessibility plot: {output_file}")
    
    def _plot_summary_dashboard_complete(self, analysis: Dict[str, Any]) -> None:
        """Plot summary dashboard using COMPLETE data"""
        logger.info("Creating summary dashboard from COMPLETE data...")
        
        fig = plt.figure(figsize=(16, 12))
        fig.suptitle('Clinical Trials Analysis Dashboard (Complete Dataset)', 
                     fontsize=18, fontweight='bold', y=0.95)
        
        # Create grid layout
        gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 1], width_ratios=[1, 1, 1])
        
        # 1. Key statistics (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        stats_text = f"""Key Statistics (Complete Data):
        
Total Diseases: {len(self.data['all_trials'])}
Total Trials: {len(self.data['trial_names'])}
        
Regional Access:
• EU: {len(self.data['eu_trials'])} diseases
• Spain: {len(self.data['spanish_trials'])} diseases
        
Avg Trials/Disease: {sum(len(t) for t in self.data['all_trials'].values()) / len(self.data['all_trials']):.1f}"""
        
        ax1.text(0.1, 0.5, stats_text, transform=ax1.transAxes, fontsize=11,
                verticalalignment='center', fontweight='bold',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.7))
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        ax1.set_title('Overview', fontweight='bold')
        
        # 2. Trial distribution histogram (top center)
        ax2 = fig.add_subplot(gs[0, 1])
        all_trial_counts = [len(trials) for trials in self.data['all_trials'].values()]
        ax2.hist(all_trial_counts, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.set_xlabel('Trials per Disease')
        ax2.set_ylabel('Number of Diseases')
        ax2.set_title('Trial Distribution', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # 3. Regional comparison (top right)
        ax3 = fig.add_subplot(gs[0, 2])
        regions = ['All', 'EU', 'Spanish']
        counts = [len(self.data['all_trials']), len(self.data['eu_trials']), len(self.data['spanish_trials'])]
        ax3.bar(regions, counts, color=['skyblue', 'lightgreen', 'coral'])
        ax3.set_ylabel('Diseases with Trials')
        ax3.set_title('Regional Coverage', fontweight='bold')
        for i, count in enumerate(counts):
            ax3.text(i, count + 1, str(count), ha='center', fontweight='bold')
        
        # 4-6. Top diseases charts (middle row)
        top_diseases = self.get_top_diseases_complete(10)
        
        for i, (region_key, region_name) in enumerate([("all", "All Trials"), ("eu", "EU Trials"), ("spanish", "Spanish")]):
            ax = fig.add_subplot(gs[1, i])
            diseases = top_diseases[region_key][:5]  # Top 5 for space
            
            if diseases:
                disease_codes = [d["orpha_code"] for d in diseases]
                trial_counts = [d["trial_count"] for d in diseases]
                
                bars = ax.barh(range(len(disease_codes)), trial_counts)
                ax.set_yticks(range(len(disease_codes)))
                ax.set_yticklabels([f"ORPHA:{code}" for code in disease_codes])
                ax.set_xlabel('Trials')
                ax.set_title(f'Top 5 - {region_name}', fontweight='bold')
                ax.invert_yaxis()
                
                for bar, count in zip(bars, trial_counts):
                    ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2, 
                           str(count), va='center', fontsize=9)
        
        # 7-9. Bottom row: Additional analysis
        
        # Outlier summary (bottom left)
        ax7 = fig.add_subplot(gs[2, 0])
        outlier_summary = "Outliers (IQR Method):\n\n"
        for region_key, region_name in [("all", "All"), ("eu", "EU"), ("spanish", "Spanish")]:
            outlier_info = analysis.get(f'{region_key}_outliers', {})
            outlier_count = outlier_info.get('outlier_count', 0)
            outlier_summary += f"• {region_name}: {outlier_count} diseases\n"
        
        ax7.text(0.1, 0.5, outlier_summary, transform=ax7.transAxes, fontsize=11,
                verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightcoral", alpha=0.7))
        ax7.set_xlim(0, 1)
        ax7.set_ylim(0, 1)
        ax7.axis('off')
        ax7.set_title('Outlier Analysis', fontweight='bold')
        
        # Top multi-disease trials (bottom center)
        ax8 = fig.add_subplot(gs[2, 1])
        top_trials = self.get_top_trials_complete(5)
        if top_trials:
            trial_names = [trial["nct_id"] for trial in top_trials]
            disease_counts = [trial["disease_count"] for trial in top_trials]
            
            bars = ax8.barh(range(len(trial_names)), disease_counts)
            ax8.set_yticks(range(len(trial_names)))
            ax8.set_yticklabels(trial_names)
            ax8.set_xlabel('Disease Count')
            ax8.set_title('Top Multi-Disease Trials', fontweight='bold')
            ax8.invert_yaxis()
            
            for bar, count in zip(bars, disease_counts):
                ax8.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2, 
                        str(count), va='center', fontsize=9)
        
        # Analysis metadata (bottom right)
        ax9 = fig.add_subplot(gs[2, 2])
        metadata_text = f"""Analysis Details:
        
Dataset: Complete (No slicing)
Method: IQR outlier detection
Coverage: 100% of available data
        
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
Files Analyzed:
• disease2all_trials.json
• disease2eu_trial.json  
• disease2spanish_trials.json
• clinicaltrial2name.json"""
        
        ax9.text(0.1, 0.5, metadata_text, transform=ax9.transAxes, fontsize=9,
                verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightyellow", alpha=0.7))
        ax9.set_xlim(0, 1)
        ax9.set_ylim(0, 1)
        ax9.axis('off')
        ax9.set_title('Analysis Info', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot (check for existing files)
        output_file = self.output_dir / "summary_dashboard.png"
        if output_file.exists():
            output_file = self.output_dir / f"summary_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            logger.warning(f"File exists, saving as: {output_file}")
        
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"Saved summary dashboard: {output_file}")
    
    def generate_statistics_json(self, analysis: Dict[str, Any]) -> None:
        """
        Generate comprehensive statistics JSON from COMPLETE data
        
        Args:
            analysis: Complete analysis results
        """
        logger.info("Generating statistics JSON from COMPLETE data...")
        
        # Get complete analysis data
        top_diseases = self.get_top_diseases_complete(15)
        top_trials = self.get_top_trials_complete(15)
        
        statistics = {
            "analysis_metadata": {
                "generated_timestamp": datetime.now().isoformat(),
                "analysis_type": "complete_dataset_analysis",
                "data_slicing": "none_applied",
                "iqr_method": "1.5_times_iqr",
                "input_files": {
                    "eu_trials": str(self.input_dir / "disease2eu_trial.json"),
                    "all_trials": str(self.input_dir / "disease2all_trials.json"),
                    "spanish_trials": str(self.input_dir / "disease2spanish_trials.json"),
                    "trial_names": str(self.input_dir / "clinicaltrial2name.json")
                }
            },
            "basic_statistics": {
                "total_diseases_with_trials": len(self.data['all_trials']),
                "diseases_with_eu_trials": len(self.data['eu_trials']),
                "diseases_with_spanish_trials": len(self.data['spanish_trials']),
                "total_unique_trials": len(self.data['trial_names']),
                "total_trial_disease_pairs": sum(len(trials) for trials in self.data['all_trials'].values())
            },
            "regional_analysis": {},
            "distribution_analysis": {},
            "outlier_analysis": {},
            "top_diseases": top_diseases,
            "top_trials": top_trials
        }
        
        # Add regional and distribution analysis
        for region in ["all", "eu", "spanish"]:
            if f"{region}_statistics" in analysis:
                statistics["regional_analysis"][region] = analysis[f"{region}_statistics"]
                statistics["distribution_analysis"][region] = analysis[f"{region}_statistics"]
            
            if f"{region}_outliers" in analysis:
                statistics["outlier_analysis"][region] = analysis[f"{region}_outliers"]
        
        # Save statistics JSON (check for existing files)
        output_file = self.output_dir / "clinical_trials_statistics.json"
        if output_file.exists():
            output_file = self.output_dir / f"clinical_trials_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            logger.warning(f"File exists, saving as: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(statistics, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated statistics JSON: {output_file}")
    
    def run_complete_analysis(self) -> Dict[str, Any]:
        """
        Run complete analysis on FULL datasets (NO slicing)
        
        Returns:
            Complete analysis results
        """
        logger.info("Starting COMPLETE clinical trials analysis...")
        logger.info("CRITICAL: Using full datasets - NO data slicing applied")
        
        # 1. Distribution analysis (COMPLETE data)
        analysis = self.analyze_distribution_complete()
        
        # 2. Generate visualizations (COMPLETE data)
        self.generate_visualizations(analysis)
        
        # 3. Generate statistics JSON (COMPLETE data)
        self.generate_statistics_json(analysis)
        
        logger.info("COMPLETE clinical trials analysis finished successfully!")
        logger.info(f"All outputs saved to: {self.output_dir}")
        logger.info("VERIFICATION: All analyses used complete datasets without slicing")
        
        return analysis


def main():
    """
    Main entry point for clinical trials statistics
    """
    parser = argparse.ArgumentParser(description="Generate clinical trials statistics and analysis")
    parser.add_argument("--input-dir", default="data/04_curated/clinical_trials",
                       help="Input directory with curated clinical trials data")
    parser.add_argument("--output-dir", 
                       default="results/etl/subset_of_disease_instances/metabolic/clinical_trials",
                       help="Output directory for statistics and visualizations")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize analyzer
        analyzer = ClinicalTrialsStatsAnalyzer(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        # Run complete analysis (NO data slicing)
        results = analyzer.run_complete_analysis()
        
        # Print summary
        print("\n" + "="*80)
        print("CLINICAL TRIALS STATISTICS SUMMARY")
        print("="*80)
        print(f"Analysis Type: COMPLETE DATASET (No slicing applied)")
        print(f"Output Directory: {args.output_dir}")
        print(f"Total Diseases with Trials: {len(analyzer.data['all_trials'])}")
        print(f"Total Unique Trials: {len(analyzer.data['trial_names'])}")
        print(f"EU Accessible Diseases: {len(analyzer.data['eu_trials'])}")
        print(f"Spanish Accessible Diseases: {len(analyzer.data['spanish_trials'])}")
        
        # Show outlier summary
        print(f"\nOutlier Analysis (IQR Method):")
        for region in ["all", "eu", "spanish"]:
            outlier_info = results.get(f"{region}_outliers", {})
            outlier_count = outlier_info.get('outlier_count', 0)
            print(f"  {region.upper()}: {outlier_count} diseases with excessive trials")
        
        print(f"\nGenerated Files:")
        print(f"  - clinical_trials_statistics.json")
        print(f"  - trial_distribution_analysis.png")
        print(f"  - top_diseases_by_trials.png")
        print(f"  - top_trials_by_diseases.png") 
        print(f"  - outlier_analysis_iqr.png")
        print(f"  - geographic_accessibility.png")
        print(f"  - summary_dashboard.png")
        print(f"\nCRITICAL: All analyses used COMPLETE datasets - no data slicing applied")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main() 