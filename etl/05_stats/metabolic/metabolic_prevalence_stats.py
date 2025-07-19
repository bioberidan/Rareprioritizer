"""
Metabolic Disease Prevalence Statistics Analyzer

This module provides comprehensive statistical analysis for metabolic disease 
prevalence and Spanish patient estimates using the CuratedPrevalenceClient.

Generates analysis reports, visualizations, and statistical summaries for
metabolic diseases in the Spanish healthcare context.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
from datetime import datetime
import statistics

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    logging.warning("Visualization libraries not available. Install matplotlib, seaborn, pandas for full functionality.")

from core.datastore.metabolic_prevalence_client import CuratedPrevalenceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MetabolicPrevalenceStatsAnalyzer:
    """Statistical analysis for metabolic disease prevalence and Spanish patients"""
    
    def __init__(self, 
                 client: Optional[CuratedPrevalenceClient] = None,
                 output_dir: str = "results/etl/metabolic"):
        """
        Initialize the metabolic prevalence stats analyzer
        
        Args:
            client: CuratedPrevalenceClient instance (creates new if None)
            output_dir: Directory for output files
        """
        self.client = client if client else CuratedPrevalenceClient()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Analysis results storage
        self.analysis_results = {}
        
        logger.info(f"Metabolic prevalence stats analyzer initialized")
        logger.info(f"Output directory: {self.output_dir}")
    
    # ========== Coverage Analysis ==========
    
    def analyze_coverage(self) -> Dict:
        """
        Analyze coverage of metabolic diseases with prevalence data
        
        Returns:
            Dictionary with coverage statistics
        """
        logger.info("Analyzing prevalence data coverage...")
        
        # Get basic statistics
        stats = self.client.get_statistics()
        coverage = stats['coverage']
        
        # Get diseases with and without prevalence
        diseases_with_prevalence = self.client.get_diseases_with_prevalence()
        diseases_without_prevalence = self.client.get_diseases_without_prevalence()
        
        # Analyze missing diseases
        missing_analysis = {
            'count': len(diseases_without_prevalence),
            'percentage': round(len(diseases_without_prevalence) / coverage['total_metabolic_diseases'] * 100, 2),
            'sample_diseases': [disease['disease_name'] for disease in diseases_without_prevalence[:10]]
        }
        
        coverage_analysis = {
            'total_metabolic_diseases': coverage['total_metabolic_diseases'],
            'diseases_with_prevalence': coverage['diseases_with_prevalence'],
            'coverage_percentage': coverage['coverage_percentage'],
            'missing_prevalence_data': missing_analysis,
            'data_completeness': {
                'excellent': coverage['coverage_percentage'] >= 95,
                'good': 85 <= coverage['coverage_percentage'] < 95,
                'fair': 70 <= coverage['coverage_percentage'] < 85,
                'poor': coverage['coverage_percentage'] < 70,
                'assessment': self._assess_coverage(coverage['coverage_percentage'])
            }
        }
        
        self.analysis_results['coverage_analysis'] = coverage_analysis
        logger.info(f"Coverage analysis completed: {coverage['coverage_percentage']}% coverage")
        
        return coverage_analysis
    
    def _assess_coverage(self, percentage: float) -> str:
        """Assess coverage quality"""
        if percentage >= 95:
            return "Excellent coverage - suitable for comprehensive analysis"
        elif percentage >= 85:
            return "Good coverage - reliable for most analyses"
        elif percentage >= 70:
            return "Fair coverage - adequate for general trends"
        else:
            return "Poor coverage - limited analytical reliability"
    
    # ========== Prevalence Distribution Analysis ==========
    
    def analyze_prevalence_distribution(self) -> Dict:
        """
        Analyze the distribution of prevalence values across metabolic diseases
        
        Returns:
            Dictionary with prevalence distribution statistics
        """
        logger.info("Analyzing prevalence distribution...")
        
        # Get prevalence data
        prevalence_data = self.client.get_all_metabolic_prevalences()
        prevalences = list(prevalence_data.values())
        
        if not prevalences:
            return {'error': 'No prevalence data available'}
        
        # Basic statistics
        basic_stats = {
            'count': len(prevalences),
            'mean': round(statistics.mean(prevalences), 2),
            'median': round(statistics.median(prevalences), 2),
            'mode': statistics.mode(prevalences) if len(set(prevalences)) < len(prevalences) else None,
            'std_dev': round(statistics.stdev(prevalences) if len(prevalences) > 1 else 0, 2),
            'min': min(prevalences),
            'max': max(prevalences)
        }
        
        # Percentiles
        sorted_prevalences = sorted(prevalences)
        percentiles = {
            'p25': sorted_prevalences[int(0.25 * len(sorted_prevalences))],
            'p50': basic_stats['median'],
            'p75': sorted_prevalences[int(0.75 * len(sorted_prevalences))],
            'p90': sorted_prevalences[int(0.90 * len(sorted_prevalences))],
            'p95': sorted_prevalences[int(0.95 * len(sorted_prevalences))],
            'p99': sorted_prevalences[int(0.99 * len(sorted_prevalences))]
        }
        
        # Prevalence categories
        categories = {
            'ultra_rare': sum(1 for p in prevalences if p < 1.0),  # < 1 per million
            'very_rare': sum(1 for p in prevalences if 1.0 <= p < 10.0),  # 1-9 per million
            'rare': sum(1 for p in prevalences if 10.0 <= p < 50.0),  # 10-49 per million
            'common_rare': sum(1 for p in prevalences if p >= 50.0),  # ≥ 50 per million
            'zero_prevalence': sum(1 for p in prevalences if p == 0.0)
        }
        
        # Calculate category percentages
        total_count = len(prevalences)
        category_percentages = {
            cat: round(count / total_count * 100, 1) for cat, count in categories.items()
        }
        
        distribution_analysis = {
            'basic_statistics': basic_stats,
            'percentiles': percentiles,
            'prevalence_categories': {
                'counts': categories,
                'percentages': category_percentages
            },
            'distribution_shape': {
                'highly_skewed': basic_stats['mean'] > 2 * basic_stats['median'],
                'skewness_direction': 'right' if basic_stats['mean'] > basic_stats['median'] else 'left'
            }
        }
        
        self.analysis_results['prevalence_distribution'] = distribution_analysis
        logger.info(f"Prevalence distribution analysis completed for {len(prevalences)} diseases")
        
        return distribution_analysis
    
    # ========== Spanish Patient Analysis ==========
    
    def analyze_spanish_patients(self) -> Dict:
        """
        Analyze Spanish patient estimates across metabolic diseases
        
        Returns:
            Dictionary with Spanish patient analysis
        """
        logger.info("Analyzing Spanish patient estimates...")
        
        # Get Spanish patient data
        spanish_data = self.client.get_all_spanish_patients()
        patient_counts = list(spanish_data.values())
        
        if not patient_counts:
            return {'error': 'No Spanish patient data available'}
        
        # Basic statistics
        basic_stats = {
            'total_patients': sum(patient_counts),
            'diseases_count': len(patient_counts),
            'mean_per_disease': round(statistics.mean(patient_counts), 1),
            'median_per_disease': round(statistics.median(patient_counts), 1),
            'std_dev': round(statistics.stdev(patient_counts) if len(patient_counts) > 1 else 0, 1),
            'min_patients': min(patient_counts),
            'max_patients': max(patient_counts)
        }
        
        # Patient burden categories
        burden_categories = {
            'no_patients': sum(1 for p in patient_counts if p == 0),
            'very_low': sum(1 for p in patient_counts if 1 <= p < 50),  # 1-49 patients
            'low': sum(1 for p in patient_counts if 50 <= p < 500),  # 50-499 patients
            'moderate': sum(1 for p in patient_counts if 500 <= p < 2000),  # 500-1999 patients
            'high': sum(1 for p in patient_counts if p >= 2000)  # ≥ 2000 patients
        }
        
        # Calculate burden percentages
        total_diseases = len(patient_counts)
        burden_percentages = {
            cat: round(count / total_diseases * 100, 1) for cat, count in burden_categories.items()
        }
        
        # Top diseases by Spanish patients
        diseases_with_prevalence = self.client.get_diseases_with_prevalence()
        top_diseases = sorted(
            diseases_with_prevalence,
            key=lambda x: x.get('spanish_patients', 0),
            reverse=True
        )[:15]
        
        top_diseases_info = [
            {
                'disease_name': disease['disease_name'],
                'orpha_code': disease['orpha_code'],
                'spanish_patients': disease['spanish_patients'],
                'prevalence_per_million': disease['prevalence_per_million']
            }
            for disease in top_diseases
        ]
        
        spanish_analysis = {
            'basic_statistics': basic_stats,
            'burden_categories': {
                'counts': burden_categories,
                'percentages': burden_percentages
            },
            'top_diseases_by_patients': top_diseases_info,
            'healthcare_planning': {
                'total_metabolic_patients_spain': basic_stats['total_patients'],
                'high_burden_diseases': burden_categories['high'],
                'resource_concentration': f"{sum(d['spanish_patients'] for d in top_diseases_info[:5])} patients in top 5 diseases"
            }
        }
        
        self.analysis_results['spanish_patients_analysis'] = spanish_analysis
        logger.info(f"Spanish patient analysis completed: {basic_stats['total_patients']} total patients")
        
        return spanish_analysis
    
    # ========== Comparative Analysis ==========
    
    def analyze_comparative_insights(self) -> Dict:
        """
        Perform comparative analysis across different dimensions
        
        Returns:
            Dictionary with comparative insights
        """
        logger.info("Performing comparative analysis...")
        
        diseases_with_prevalence = self.client.get_diseases_with_prevalence()
        
        if not diseases_with_prevalence:
            return {'error': 'No diseases with prevalence data for comparison'}
        
        # Ultra-rare vs common rare comparison
        ultra_rare = [d for d in diseases_with_prevalence if d['prevalence_per_million'] < 1.0]
        common_rare = [d for d in diseases_with_prevalence if d['prevalence_per_million'] >= 50.0]
        
        ultra_rare_patients = sum(d['spanish_patients'] for d in ultra_rare)
        common_rare_patients = sum(d['spanish_patients'] for d in common_rare)
        
        # Zero prevalence diseases
        zero_prevalence = [d for d in diseases_with_prevalence if d['prevalence_per_million'] == 0.0]
        
        # High-impact diseases (≥ 1000 Spanish patients)
        high_impact = [d for d in diseases_with_prevalence if d['spanish_patients'] >= 1000]
        
        comparative_analysis = {
            'ultra_rare_vs_common_rare': {
                'ultra_rare_diseases': len(ultra_rare),
                'ultra_rare_total_patients': ultra_rare_patients,
                'common_rare_diseases': len(common_rare),
                'common_rare_total_patients': common_rare_patients,
                'patient_distribution': f"{common_rare_patients}/{ultra_rare_patients + common_rare_patients} patients in common rare diseases"
            },
            'zero_prevalence_analysis': {
                'count': len(zero_prevalence),
                'percentage': round(len(zero_prevalence) / len(diseases_with_prevalence) * 100, 1),
                'interpretation': "Diseases with zero prevalence may indicate data limitations or extremely rare conditions"
            },
            'high_impact_diseases': {
                'count': len(high_impact),
                'total_patients': sum(d['spanish_patients'] for d in high_impact),
                'diseases': [
                    {
                        'name': d['disease_name'],
                        'orpha_code': d['orpha_code'],
                        'spanish_patients': d['spanish_patients']
                    }
                    for d in sorted(high_impact, key=lambda x: x['spanish_patients'], reverse=True)[:10]
                ]
            },
            'prevalence_patient_correlation': {
                'interpretation': "Higher prevalence diseases generally have more Spanish patients",
                'exceptions': [
                    d['disease_name'] for d in diseases_with_prevalence 
                    if d['prevalence_per_million'] > 100 and d['spanish_patients'] < 1000
                ][:5]
            }
        }
        
        self.analysis_results['comparative_analysis'] = comparative_analysis
        logger.info("Comparative analysis completed")
        
        return comparative_analysis
    
    # ========== Output Generation ==========
    
    def generate_json_report(self, filename: str = "metabolic_prevalence_statistics.json") -> Path:
        """
        Generate comprehensive JSON statistics report
        
        Args:
            filename: Name of output JSON file
            
        Returns:
            Path to generated JSON file
        """
        logger.info("Generating JSON statistics report...")
        
        # Ensure all analyses are completed
        if 'coverage_analysis' not in self.analysis_results:
            self.analyze_coverage()
        if 'prevalence_distribution' not in self.analysis_results:
            self.analyze_prevalence_distribution()
        if 'spanish_patients_analysis' not in self.analysis_results:
            self.analyze_spanish_patients()
        if 'comparative_analysis' not in self.analysis_results:
            self.analyze_comparative_insights()
        
        # Compile comprehensive report
        report = {
            'report_metadata': {
                'generated_at': datetime.now().isoformat(),
                'analyzer_version': '1.0.0',
                'data_sources': self.client.get_data_summary()['data_sources'],
                'analysis_scope': 'Metabolic diseases prevalence and Spanish patient estimates'
            },
            'executive_summary': self._generate_executive_summary(),
            'coverage_analysis': self.analysis_results['coverage_analysis'],
            'prevalence_distribution': self.analysis_results['prevalence_distribution'],
            'spanish_patients_analysis': self.analysis_results['spanish_patients_analysis'],
            'comparative_analysis': self.analysis_results['comparative_analysis']
        }
        
        # Save JSON report
        json_file = self.output_dir / filename
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report saved: {json_file}")
        return json_file
    
    def _generate_executive_summary(self) -> Dict:
        """Generate executive summary from analysis results"""
        coverage = self.analysis_results.get('coverage_analysis', {})
        spanish = self.analysis_results.get('spanish_patients_analysis', {})
        prevalence = self.analysis_results.get('prevalence_distribution', {})
        
        return {
            'key_findings': [
                f"Coverage: {coverage.get('coverage_percentage', 0)}% of metabolic diseases have prevalence data",
                f"Total Spanish patients: {spanish.get('basic_statistics', {}).get('total_patients', 0)} across all metabolic diseases",
                f"Disease distribution: {prevalence.get('prevalence_categories', {}).get('percentages', {}).get('ultra_rare', 0)}% ultra-rare, {prevalence.get('prevalence_categories', {}).get('percentages', {}).get('common_rare', 0)}% common rare",
                f"High-impact diseases: {len(self.analysis_results.get('comparative_analysis', {}).get('high_impact_diseases', {}).get('diseases', []))} diseases with ≥1000 Spanish patients"
            ],
            'data_quality': coverage.get('data_completeness', {}).get('assessment', 'Unknown'),
            'healthcare_impact': {
                'total_patient_burden': spanish.get('basic_statistics', {}).get('total_patients', 0),
                'coverage_adequacy': coverage.get('coverage_percentage', 0) >= 90,
                'analysis_reliability': 'High' if coverage.get('coverage_percentage', 0) >= 85 else 'Moderate'
            }
        }
    
    def generate_comprehensive_report(self) -> Dict:
        """
        Generate complete analysis with all components
        
        Returns:
            Dictionary with file paths of generated outputs
        """
        logger.info("="*60)
        logger.info("METABOLIC DISEASE PREVALENCE ANALYSIS")
        logger.info("="*60)
        
        # Run all analyses
        coverage = self.analyze_coverage()
        distribution = self.analyze_prevalence_distribution()
        spanish = self.analyze_spanish_patients()
        comparative = self.analyze_comparative_insights()
        outliers = self.analyze_outliers()
        
        # Generate outputs
        json_report = self.generate_json_report()
        
        # Generate visualizations if available
        visualization_files = []
        if VISUALIZATION_AVAILABLE:
            try:
                visualization_files = self.generate_visualizations()
            except Exception as e:
                logger.warning(f"Visualization generation failed: {e}")
        
        # Summary report
        output_summary = {
            'json_report': str(json_report),
            'visualizations': visualization_files,
            'output_directory': str(self.output_dir),
            'analysis_summary': {
                'total_diseases': coverage['total_metabolic_diseases'],
                'coverage_percentage': coverage['coverage_percentage'],
                'total_spanish_patients': spanish['basic_statistics']['total_patients'],
                'high_burden_diseases': len(comparative['high_impact_diseases']['diseases']),
                'outliers_detected': outliers.get('iqr_methods', {}).get('moderate', {}).get('outlier_count', 0),
                'outlier_percentage': outliers.get('iqr_methods', {}).get('moderate', {}).get('outlier_percentage', 0)
            }
        }
        
        logger.info("="*60)
        logger.info("ANALYSIS COMPLETED SUCCESSFULLY")
        logger.info("="*60)
        
        # Print key results
        print(f"\n📊 METABOLIC DISEASE ANALYSIS SUMMARY")
        print(f"Total diseases analyzed: {coverage['total_metabolic_diseases']}")
        print(f"Prevalence coverage: {coverage['coverage_percentage']}%")
        print(f"Total Spanish patients: {spanish['basic_statistics']['total_patients']:,}")
        print(f"High-impact diseases (≥1000 patients): {len(comparative['high_impact_diseases']['diseases'])}")
        print(f"Outliers detected (IQR 2.0x): {outliers.get('iqr_methods', {}).get('moderate', {}).get('outlier_count', 0)} ({outliers.get('iqr_methods', {}).get('moderate', {}).get('outlier_percentage', 0):.1f}%)")
        print(f"Reports saved to: {self.output_dir}")
        
        return output_summary
    
    def analyze_outliers(self) -> Dict:
        """
        Perform comprehensive outlier analysis on CURATED metabolic disease prevalence data
        Following the patterns from existing repo outlier analysis modules
        
        This analyzes the curated metabolic prevalence data and Spanish patient estimates,
        not the original raw prevalence data from ProcessedPrevalenceClient.
        
        Returns:
            Dictionary with comprehensive outlier analysis results
        """
        logger.info("Performing comprehensive outlier analysis on CURATED metabolic disease data...")
        
        # Get CURATED metabolic disease data (not raw prevalence data)
        diseases_with_prevalence = self.client.get_diseases_with_prevalence()
        
        if not diseases_with_prevalence:
            return {'error': 'No curated metabolic prevalence data available for outlier analysis'}
        
        logger.info(f"Analyzing outliers in {len(diseases_with_prevalence)} curated metabolic diseases")
        
        # Extract CURATED metabolic prevalence data with enhanced context
        prevalence_data = []
        prevalence_values = []
        spanish_patient_values = []
        
        for disease in diseases_with_prevalence:
            prev = disease['prevalence_per_million']
            patients = disease['spanish_patients']
            prevalence_values.append(prev)
            spanish_patient_values.append(patients)
            
            # Enhanced disease context for METABOLIC diseases specifically
            # Focus on metabolic disease characteristics
            prevalence_data.append({
                'orpha_code': disease['orpha_code'],
                'disease_name': disease['disease_name'],
                'prevalence': prev,
                'spanish_patients': patients,
                'records_count': 1,  # Curated data has processed records
                'reliability_score': 8.0 if prev > 0 else 0.0,  # High reliability for curated data
                'has_worldwide': prev > 5.0,  # Metabolic diseases with higher prevalence likely have worldwide data
                'validated_records': 1 if prev > 0 else 0,
                'regional_coverage': 3 if prev > 50.0 else 2 if prev > 10.0 else 1,
                'metabolic_category': self._categorize_metabolic_disease(prev),
                'is_high_impact': patients >= 1000  # Spanish patients >= 1000
            })
        
        # IQR-based outlier detection with multiple methods on CURATED data
        Q1_prev = statistics.quantiles(prevalence_values, n=4)[0] if len(prevalence_values) > 1 else 0
        Q3_prev = statistics.quantiles(prevalence_values, n=4)[2] if len(prevalence_values) > 1 else max(prevalence_values)
        IQR_prev = Q3_prev - Q1_prev
        
        # Also analyze Spanish patient outliers
        Q1_patients = statistics.quantiles(spanish_patient_values, n=4)[0] if len(spanish_patient_values) > 1 else 0
        Q3_patients = statistics.quantiles(spanish_patient_values, n=4)[2] if len(spanish_patient_values) > 1 else max(spanish_patient_values)
        IQR_patients = Q3_patients - Q1_patients
        
        # Multiple IQR methods for metabolic disease outlier detection
        iqr_methods = {
            'conservative': 1.5,
            'moderate': 2.0,
            'liberal': 2.5,
            'very_liberal': 3.0
        }
        
        iqr_results = {}
        
        for method_name, multiplier in iqr_methods.items():
            # Prevalence-based outliers (primary analysis)
            lower_bound_prev = Q1_prev - multiplier * IQR_prev
            upper_bound_prev = Q3_prev + multiplier * IQR_prev
            
            # Spanish patients-based outliers (secondary analysis)
            lower_bound_patients = Q1_patients - multiplier * IQR_patients
            upper_bound_patients = Q3_patients + multiplier * IQR_patients
            
            outlier_diseases = []
            for disease_data in prevalence_data:
                prev = disease_data['prevalence']
                patients = disease_data['spanish_patients']
                
                # Check if outlier by prevalence OR by Spanish patients
                is_prevalence_outlier = prev < lower_bound_prev or prev > upper_bound_prev
                is_patients_outlier = patients < lower_bound_patients or patients > upper_bound_patients
                
                if is_prevalence_outlier or is_patients_outlier:
                    outlier_copy = disease_data.copy()
                    outlier_copy['outlier_type'] = 'high' if (prev > upper_bound_prev or patients > upper_bound_patients) else 'low'
                    outlier_copy['prevalence_deviation'] = abs(prev - Q3_prev) if prev > upper_bound_prev else abs(prev - Q1_prev)
                    outlier_copy['patients_deviation'] = abs(patients - Q3_patients) if patients > upper_bound_patients else abs(patients - Q1_patients)
                    outlier_copy['outlier_reason'] = []
                    
                    if is_prevalence_outlier:
                        outlier_copy['outlier_reason'].append('prevalence')
                    if is_patients_outlier:
                        outlier_copy['outlier_reason'].append('spanish_patients')
                    
                    outlier_diseases.append(outlier_copy)
            
            # Sort by prevalence (descending for high outliers, ascending for low)
            outlier_diseases.sort(key=lambda x: x['prevalence'], reverse=True)
            
            # Metabolic disease-specific medical relevance assessment
            high_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] >= 8.0])
            medium_reliability_outliers = len([d for d in outlier_diseases if 6.0 <= d['reliability_score'] < 8.0])
            low_reliability_outliers = len([d for d in outlier_diseases if d['reliability_score'] < 6.0])
            
            single_record_outliers = len([d for d in outlier_diseases if d['records_count'] == 1])
            multiple_record_outliers = len([d for d in outlier_diseases if d['records_count'] > 1])
            
            worldwide_outliers = len([d for d in outlier_diseases if d['has_worldwide']])
            high_impact_outliers = len([d for d in outlier_diseases if d['is_high_impact']])
            
            # Metabolic category distribution of outliers
            category_distribution = {}
            for disease in outlier_diseases:
                cat = disease['metabolic_category']
                category_distribution[cat] = category_distribution.get(cat, 0) + 1
            
            # Statistical analysis of outlier prevalences and patients
            outlier_prevalences = [d['prevalence'] for d in outlier_diseases]
            outlier_patients = [d['spanish_patients'] for d in outlier_diseases]
            
            iqr_results[method_name] = {
                'method_info': {
                    'multiplier': multiplier,
                    'method_name': f'IQR {multiplier}x (Metabolic Curated)',
                    'description': f'IQR method with {multiplier}x multiplier applied to curated metabolic disease data'
                },
                'thresholds': {
                    'prevalence_lower_bound': lower_bound_prev,
                    'prevalence_upper_bound': upper_bound_prev,
                    'patients_lower_bound': lower_bound_patients,
                    'patients_upper_bound': upper_bound_patients,
                    'Q1_prevalence': Q1_prev,
                    'Q3_prevalence': Q3_prev,
                    'IQR_prevalence': IQR_prev,
                    'Q1_patients': Q1_patients,
                    'Q3_patients': Q3_patients,
                    'IQR_patients': IQR_patients
                },
                'outlier_detection': {
                    'outlier_count': len(outlier_diseases),
                    'outlier_percentage': round(len(outlier_diseases) / len(prevalence_data) * 100, 2),
                    'high_outliers': len([d for d in outlier_diseases if d['outlier_type'] == 'high']),
                    'low_outliers': len([d for d in outlier_diseases if d['outlier_type'] == 'low']),
                    'prevalence_outliers': len([d for d in outlier_diseases if 'prevalence' in d['outlier_reason']]),
                    'patients_outliers': len([d for d in outlier_diseases if 'spanish_patients' in d['outlier_reason']])
                },
                'outlier_statistics': {
                    'min_outlier_prevalence': min(outlier_prevalences) if outlier_prevalences else None,
                    'max_outlier_prevalence': max(outlier_prevalences) if outlier_prevalences else None,
                    'mean_outlier_prevalence': statistics.mean(outlier_prevalences) if outlier_prevalences else None,
                    'median_outlier_prevalence': statistics.median(outlier_prevalences) if outlier_prevalences else None,
                    'min_outlier_patients': min(outlier_patients) if outlier_patients else None,
                    'max_outlier_patients': max(outlier_patients) if outlier_patients else None,
                    'mean_outlier_patients': statistics.mean(outlier_patients) if outlier_patients else None,
                    'median_outlier_patients': statistics.median(outlier_patients) if outlier_patients else None
                },
                'metabolic_assessment': {
                    'high_reliability_outliers': high_reliability_outliers,
                    'medium_reliability_outliers': medium_reliability_outliers,
                    'low_reliability_outliers': low_reliability_outliers,
                    'single_record_outliers': single_record_outliers,
                    'multiple_record_outliers': multiple_record_outliers,
                    'worldwide_outliers': worldwide_outliers,
                    'high_impact_outliers': high_impact_outliers,
                    'quality_ratio': high_reliability_outliers / max(len(outlier_diseases), 1),
                    'evidence_ratio': multiple_record_outliers / max(len(outlier_diseases), 1),
                    'global_ratio': worldwide_outliers / max(len(outlier_diseases), 1),
                    'high_impact_ratio': high_impact_outliers / max(len(outlier_diseases), 1),
                    'category_distribution': category_distribution
                },
                'top_outliers': outlier_diseases[:15],  # Top 15 outliers
                'outliers': outlier_diseases[:20]  # Keep this for backward compatibility
            }
        
        # Percentile-based detection on CURATED metabolic data (P90, P95, P99)
        sorted_prevalences = sorted(prevalence_values)
        sorted_patients = sorted(spanish_patient_values)
        
        p90_prev = sorted_prevalences[int(0.9 * len(sorted_prevalences))] if len(sorted_prevalences) > 10 else max(sorted_prevalences)
        p95_prev = sorted_prevalences[int(0.95 * len(sorted_prevalences))] if len(sorted_prevalences) > 20 else max(sorted_prevalences)
        p99_prev = sorted_prevalences[int(0.99 * len(sorted_prevalences))] if len(sorted_prevalences) > 100 else max(sorted_prevalences)
        
        p90_patients = sorted_patients[int(0.9 * len(sorted_patients))] if len(sorted_patients) > 10 else max(sorted_patients)
        p95_patients = sorted_patients[int(0.95 * len(sorted_patients))] if len(sorted_patients) > 20 else max(sorted_patients)
        p99_patients = sorted_patients[int(0.99 * len(sorted_patients))] if len(sorted_patients) > 100 else max(sorted_patients)
        
        # P90 trimming analysis on metabolic data
        p90_outliers = [d for d in prevalence_data if d['prevalence'] > p90_prev or d['spanish_patients'] > p90_patients]
        
        # Calculate statistical improvements from outlier removal (using moderate method)
        original_stats = {
            'prevalence_mean': statistics.mean(prevalence_values),
            'prevalence_median': statistics.median(prevalence_values),
            'prevalence_std_dev': statistics.stdev(prevalence_values) if len(prevalence_values) > 1 else 0,
            'prevalence_min': min(prevalence_values),
            'prevalence_max': max(prevalence_values),
            'patients_mean': statistics.mean(spanish_patient_values),
            'patients_median': statistics.median(spanish_patient_values),
            'patients_std_dev': statistics.stdev(spanish_patient_values) if len(spanish_patient_values) > 1 else 0,
            'patients_min': min(spanish_patient_values),
            'patients_max': max(spanish_patient_values)
        }
        
        # Clean data (using moderate IQR method)
        moderate_outliers = iqr_results['moderate']['top_outliers']
        moderate_outlier_prevalences = [d['prevalence'] for d in moderate_outliers]
        moderate_outlier_patients = [d['spanish_patients'] for d in moderate_outliers]
        
        clean_prevalences = [p for p in prevalence_values if p not in moderate_outlier_prevalences]
        clean_patients = [p for p in spanish_patient_values if p not in moderate_outlier_patients]
        
        clean_stats = {
            'prevalence_mean': statistics.mean(clean_prevalences) if clean_prevalences else 0,
            'prevalence_median': statistics.median(clean_prevalences) if clean_prevalences else 0,
            'prevalence_std_dev': statistics.stdev(clean_prevalences) if len(clean_prevalences) > 1 else 0,
            'prevalence_min': min(clean_prevalences) if clean_prevalences else 0,
            'prevalence_max': max(clean_prevalences) if clean_prevalences else 0,
            'patients_mean': statistics.mean(clean_patients) if clean_patients else 0,
            'patients_median': statistics.median(clean_patients) if clean_patients else 0,
            'patients_std_dev': statistics.stdev(clean_patients) if len(clean_patients) > 1 else 0,
            'patients_min': min(clean_patients) if clean_patients else 0,
            'patients_max': max(clean_patients) if clean_patients else 0
        }
        
        # Comprehensive outlier analysis results focused on CURATED METABOLIC data
        outlier_analysis = {
            'analysis_metadata': {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_diseases': len(prevalence_data),
                'method_count': len(iqr_methods) + 1,  # IQR methods + percentile
                'recommended_method': 'moderate',
                'data_source': 'curated_metabolic_prevalence',
                'description': 'Outlier analysis on curated metabolic disease prevalence and Spanish patient estimates'
            },
            'dataset_statistics': {
                'original_stats': original_stats,
                'clean_stats': clean_stats,
                'statistical_improvement': {
                    'prevalence_mean_change': clean_stats['prevalence_mean'] - original_stats['prevalence_mean'],
                    'prevalence_std_reduction': original_stats['prevalence_std_dev'] - clean_stats['prevalence_std_dev'],
                    'prevalence_max_reduction': original_stats['prevalence_max'] - clean_stats['prevalence_max'],
                    'patients_mean_change': clean_stats['patients_mean'] - original_stats['patients_mean'],
                    'patients_std_reduction': original_stats['patients_std_dev'] - clean_stats['patients_std_dev'],
                    'patients_max_reduction': original_stats['patients_max'] - clean_stats['patients_max']
                }
            },
            'iqr_methods': iqr_results,
            'percentile_analysis': {
                'thresholds': {
                    'p90_prevalence': p90_prev,
                    'p95_prevalence': p95_prev,
                    'p99_prevalence': p99_prev,
                    'p90_patients': p90_patients,
                    'p95_patients': p95_patients,
                    'p99_patients': p99_patients
                },
                'p90_outliers': {
                    'count': len(p90_outliers),
                    'percentage': round(len(p90_outliers) / len(prevalence_data) * 100, 2),
                    'diseases': p90_outliers[:10]  # Top 10
                },
                'high_prevalence_categories': {
                    'p90_plus_prevalence': len([d for d in prevalence_data if d['prevalence'] >= p90_prev]),
                    'p95_plus_prevalence': len([d for d in prevalence_data if d['prevalence'] >= p95_prev]),
                    'p99_plus_prevalence': len([d for d in prevalence_data if d['prevalence'] >= p99_prev]),
                    'p90_plus_patients': len([d for d in prevalence_data if d['spanish_patients'] >= p90_patients]),
                    'p95_plus_patients': len([d for d in prevalence_data if d['spanish_patients'] >= p95_patients]),
                    'p99_plus_patients': len([d for d in prevalence_data if d['spanish_patients'] >= p99_patients])
                }
            },
            'summary': {
                'total_diseases': len(prevalence_data),
                'prevalence_range': f"{min(prevalence_values):.2f} - {max(prevalence_values):.2f}",
                'patients_range': f"{min(spanish_patient_values)} - {max(spanish_patient_values)}",
                'IQR_prevalence': round(IQR_prev, 2),
                'IQR_patients': round(IQR_patients, 2),
                'recommended_method': 'moderate',
                'primary_outlier_count': iqr_results['moderate']['outlier_detection']['outlier_count'],
                'primary_outlier_percentage': iqr_results['moderate']['outlier_detection']['outlier_percentage']
            }
        }
        
        # Save outlier analysis to analysis_results for use in reports
        self.analysis_results['outlier_analysis'] = outlier_analysis
        
        # Save detailed outlier analysis to JSON file
        self.save_outlier_analysis_json(outlier_analysis)
        
        logger.info("Comprehensive outlier analysis on CURATED metabolic data completed")
        logger.info(f"Primary method (IQR 2.0x): {outlier_analysis['summary']['primary_outlier_count']} outliers ({outlier_analysis['summary']['primary_outlier_percentage']:.1f}%)")
        
        return outlier_analysis
    
    def _categorize_metabolic_disease(self, prevalence: float) -> str:
        """Categorize metabolic disease by prevalence level"""
        if prevalence == 0:
            return "zero_prevalence"
        elif prevalence < 1.0:
            return "ultra_rare"
        elif prevalence < 10.0:
            return "very_rare"
        elif prevalence < 50.0:
            return "rare"
        else:
            return "common_rare"
    
    def save_outlier_analysis_json(self, outlier_analysis: Dict) -> None:
        """Save comprehensive outlier analysis to JSON file"""
        try:
            outlier_file = self.output_dir / f"metabolic_outlier_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(outlier_file, 'w', encoding='utf-8') as f:
                json.dump(outlier_analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Comprehensive outlier analysis saved: {outlier_file}")
            
            # Also save a simplified summary for quick reference
            summary_file = self.output_dir / "metabolic_outlier_summary.json"
            summary_data = {
                'analysis_date': outlier_analysis['analysis_metadata']['analysis_timestamp'],
                'total_diseases': outlier_analysis['summary']['total_diseases'],
                'recommended_method': outlier_analysis['summary']['recommended_method'],
                'primary_outliers': {
                    'count': outlier_analysis['summary']['primary_outlier_count'],
                    'percentage': outlier_analysis['summary']['primary_outlier_percentage']
                },
                'top_outliers': outlier_analysis['iqr_methods']['moderate']['top_outliers'][:10],
                'statistical_improvement': outlier_analysis['dataset_statistics']['statistical_improvement']
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Outlier summary saved: {summary_file}")
            
        except Exception as e:
            logger.error(f"Error saving outlier analysis: {e}")
    
    def create_comprehensive_outlier_analysis_plot(self) -> str:
        """
        Create comprehensive outlier analysis visualization for CURATED metabolic data
        Following repo patterns but focused on curated metabolic prevalence and Spanish patients
        
        Returns:
            Path to the generated plot file
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualization libraries not available")
            return ""
        
        logger.info("Creating comprehensive outlier analysis plot for CURATED metabolic data...")
        
        try:
            # Ensure outlier analysis has been run
            if 'outlier_analysis' not in self.analysis_results:
                self.analyze_outliers()
            
            outlier_data = self.analysis_results.get('outlier_analysis', {})
            if not outlier_data or 'iqr_methods' not in outlier_data:
                logger.error("No outlier analysis data available")
                return ""
            
            # Get CURATED metabolic data for visualization
            diseases_with_prevalence = self.client.get_diseases_with_prevalence()
            prevalence_values = [d['prevalence_per_million'] for d in diseases_with_prevalence]
            spanish_patient_values = [d['spanish_patients'] for d in diseases_with_prevalence]
            
            # Get moderate method results (recommended)
            moderate_results = outlier_data['iqr_methods']['moderate']
            outlier_diseases = moderate_results['top_outliers']
            outlier_prevalences = [d['prevalence'] for d in outlier_diseases]
            outlier_patients = [d['spanish_patients'] for d in outlier_diseases]
            
            # Calculate clean data
            clean_prevalences = [p for p in prevalence_values if p not in outlier_prevalences]
            clean_patients = [p for p in spanish_patient_values if p not in outlier_patients]
            
            # Create 3x2 plot grid
            fig, axes = plt.subplots(3, 2, figsize=(20, 18))
            fig.suptitle('Comprehensive Metabolic Disease Outlier Analysis\nCurated Prevalence Data & Spanish Patient Estimates (IQR 2.0x)', 
                        fontsize=18, fontweight='bold', y=0.98)
            
            # Panel 1: Original Curated Prevalence Distribution
            axes[0, 0].hist(prevalence_values, bins=50, density=True, alpha=0.7, 
                           color='steelblue', edgecolor='black', linewidth=0.5)
            axes[0, 0].axvline(moderate_results['thresholds']['prevalence_upper_bound'], color='red', 
                              linestyle='--', linewidth=2, 
                              label=f'Upper Bound: {moderate_results["thresholds"]["prevalence_upper_bound"]:.1f}')
            axes[0, 0].set_title('Panel 1: Curated Metabolic Prevalence Distribution', fontweight='bold', fontsize=12)
            axes[0, 0].set_xlabel('Prevalence (per million)', fontsize=10)
            axes[0, 0].set_ylabel('Density', fontsize=10)
            axes[0, 0].legend(fontsize=9)
            axes[0, 0].grid(True, alpha=0.3)
            
            # Add original statistics
            orig_stats = outlier_data['dataset_statistics']['original_stats']
            stats_text = f'Count: {len(prevalence_values)}\nMean: {orig_stats["prevalence_mean"]:.1f}\n'
            stats_text += f'Median: {orig_stats["prevalence_median"]:.1f}\nStd: {orig_stats["prevalence_std_dev"]:.1f}'
            axes[0, 0].text(0.7, 0.8, stats_text, transform=axes[0, 0].transAxes, fontsize=9,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8))
            
            # Panel 2: Original Spanish Patients Distribution
            axes[0, 1].hist(spanish_patient_values, bins=50, density=True, alpha=0.7, 
                           color='orange', edgecolor='black', linewidth=0.5)
            axes[0, 1].axvline(moderate_results['thresholds']['patients_upper_bound'], color='red', 
                              linestyle='--', linewidth=2, 
                              label=f'Upper Bound: {moderate_results["thresholds"]["patients_upper_bound"]:.0f}')
            axes[0, 1].set_title('Panel 2: Spanish Patient Estimates Distribution', fontweight='bold', fontsize=12)
            axes[0, 1].set_xlabel('Spanish Patients', fontsize=10)
            axes[0, 1].set_ylabel('Density', fontsize=10)
            axes[0, 1].legend(fontsize=9)
            axes[0, 1].grid(True, alpha=0.3)
            
            # Add patients statistics
            patients_text = f'Count: {len(spanish_patient_values)}\nMean: {orig_stats["patients_mean"]:.0f}\n'
            patients_text += f'Median: {orig_stats["patients_median"]:.0f}\nMax: {orig_stats["patients_max"]:.0f}'
            axes[0, 1].text(0.7, 0.8, patients_text, transform=axes[0, 1].transAxes, fontsize=9,
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
            
            # Panel 3: Outliers Highlighted (Prevalence)
            axes[1, 0].hist(prevalence_values, bins=50, density=True, alpha=0.6, 
                           color='steelblue', edgecolor='black', linewidth=0.5,
                           label=f'All Diseases (n={len(prevalence_values)})')
            
            if outlier_prevalences:
                axes[1, 0].hist(outlier_prevalences, bins=min(20, len(outlier_prevalences)), 
                               density=True, alpha=0.8, color='red', edgecolor='darkred', linewidth=1.0,
                               label=f'Outliers (n={len(outlier_prevalences)})')
            
            axes[1, 0].axvline(moderate_results['thresholds']['prevalence_upper_bound'], color='orange', 
                              linestyle='--', linewidth=2, label=f'IQR 2.0x Threshold')
            axes[1, 0].set_title('Panel 3: Prevalence Outliers Highlighted', fontweight='bold', fontsize=12)
            axes[1, 0].set_xlabel('Prevalence (per million)', fontsize=10)
            axes[1, 0].set_ylabel('Density', fontsize=10)
            axes[1, 0].legend(fontsize=9)
            axes[1, 0].grid(True, alpha=0.3)
            
            # Add outlier statistics
            outlier_text = f'Prevalence Outliers: {moderate_results["outlier_detection"]["prevalence_outliers"]}\n'
            outlier_text += f'Total Outliers: {moderate_results["outlier_detection"]["outlier_count"]} '
            outlier_text += f'({moderate_results["outlier_detection"]["outlier_percentage"]:.1f}%)\n'
            outlier_text += f'Max Outlier: {max(outlier_prevalences) if outlier_prevalences else 0:.1f}'
            axes[1, 0].text(0.7, 0.8, outlier_text, transform=axes[1, 0].transAxes, fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcoral", alpha=0.8))
            
            # Panel 4: Outliers Highlighted (Spanish Patients)
            axes[1, 1].hist(spanish_patient_values, bins=50, density=True, alpha=0.6, 
                           color='orange', edgecolor='black', linewidth=0.5,
                           label=f'All Diseases (n={len(spanish_patient_values)})')
            
            if outlier_patients:
                axes[1, 1].hist(outlier_patients, bins=min(20, len(outlier_patients)), 
                               density=True, alpha=0.8, color='red', edgecolor='darkred', linewidth=1.0,
                               label=f'Outliers (n={len(outlier_patients)})')
            
            axes[1, 1].axvline(moderate_results['thresholds']['patients_upper_bound'], color='purple', 
                              linestyle='--', linewidth=2, label=f'IQR 2.0x Threshold')
            axes[1, 1].set_title('Panel 4: Spanish Patients Outliers Highlighted', fontweight='bold', fontsize=12)
            axes[1, 1].set_xlabel('Spanish Patients', fontsize=10)
            axes[1, 1].set_ylabel('Density', fontsize=10)
            axes[1, 1].legend(fontsize=9)
            axes[1, 1].grid(True, alpha=0.3)
            
            # Add patients outlier statistics
            patients_outlier_text = f'Patient Outliers: {moderate_results["outlier_detection"]["patients_outliers"]}\n'
            patients_outlier_text += f'High Impact: {moderate_results["metabolic_assessment"]["high_impact_outliers"]}\n'
            patients_outlier_text += f'Max: {max(outlier_patients) if outlier_patients else 0:.0f} patients'
            axes[1, 1].text(0.7, 0.8, patients_outlier_text, transform=axes[1, 1].transAxes, fontsize=9,
                            bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgreen", alpha=0.8))
            
            # Panel 5: Top Outliers by Spanish Patients
            top_outliers = moderate_results['top_outliers'][:10]
            if top_outliers:
                outlier_names = [d['disease_name'][:25] + '...' if len(d['disease_name']) > 25 
                                else d['disease_name'] for d in top_outliers]
                outlier_patients_list = [d['spanish_patients'] for d in top_outliers]
                
                y_pos = range(len(outlier_names))
                axes[2, 0].barh(y_pos, outlier_patients_list, alpha=0.7, color='red')
                axes[2, 0].set_yticks(y_pos)
                axes[2, 0].set_yticklabels(outlier_names, fontsize=8)
                axes[2, 0].set_title('Panel 5: Top 10 Metabolic Disease Outliers\n(by Spanish Patients)', fontweight='bold', fontsize=12)
                axes[2, 0].set_xlabel('Spanish Patients', fontsize=10)
                axes[2, 0].invert_yaxis()
                axes[2, 0].grid(True, alpha=0.3)
                
                # Add outlier reasons as text
                reasons_text = "Outlier Reasons:\n"
                for i, outlier in enumerate(top_outliers[:5]):
                    reasons = ", ".join(outlier.get('outlier_reason', ['unknown']))
                    reasons_text += f"{outlier['disease_name'][:15]}...: {reasons}\n"
                
                axes[2, 0].text(1.02, 0.5, reasons_text, transform=axes[2, 0].transAxes, fontsize=8,
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8))
            else:
                axes[2, 0].text(0.5, 0.5, 'No Outliers\nDetected', ha='center', va='center', 
                               transform=axes[2, 0].transAxes, fontsize=12)
                axes[2, 0].set_title('Panel 5: Top Outliers', fontweight='bold', fontsize=12)
            
            # Panel 6: Metabolic Category Assessment
            if outlier_diseases:
                met_assessment = moderate_results['metabolic_assessment']
                
                # Create pie chart of metabolic category distribution
                category_dist = met_assessment.get('category_distribution', {})
                
                if category_dist:
                    labels = []
                    sizes = []
                    colors = ['brown', 'purple', 'blue', 'orange', 'gray']
                    
                    category_names = {
                        'ultra_rare': 'Ultra-rare\n(<1ppm)',
                        'very_rare': 'Very Rare\n(1-9ppm)',
                        'rare': 'Rare\n(10-49ppm)',
                        'common_rare': 'Common Rare\n(≥50ppm)',
                        'zero_prevalence': 'Zero\nPrevalence'
                    }
                    
                    for cat, count in category_dist.items():
                        if count > 0:
                            labels.append(category_names.get(cat, cat))
                            sizes.append(count)
                    
                    if sizes:
                        axes[2, 1].pie(sizes, labels=labels, colors=colors[:len(sizes)], 
                                      autopct='%1.1f%%', startangle=90)
                    else:
                        axes[2, 1].text(0.5, 0.5, 'No Category\nData Available', ha='center', va='center',
                                        transform=axes[2, 1].transAxes, fontsize=12)
                else:
                    axes[2, 1].text(0.5, 0.5, 'No Category\nDistribution Available', ha='center', va='center',
                                    transform=axes[2, 1].transAxes, fontsize=12)
                
                axes[2, 1].set_title('Panel 6: Outlier Metabolic Categories', fontweight='bold', fontsize=12)
                
                # Add assessment text
                assessment_text = f'Quality Ratio: {met_assessment["quality_ratio"]:.2f}\n'
                assessment_text += f'High Impact: {met_assessment["high_impact_outliers"]}\n'
                assessment_text += f'Global Coverage: {met_assessment["global_ratio"]:.2f}'
                
                axes[2, 1].text(1.1, 0.5, assessment_text, transform=axes[2, 1].transAxes, fontsize=9,
                                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightcyan", alpha=0.8))
            else:
                axes[2, 1].text(0.5, 0.5, 'No Outliers\nfor Assessment', ha='center', va='center',
                               transform=axes[2, 1].transAxes, fontsize=12)
                axes[2, 1].set_title('Panel 6: Metabolic Assessment', fontweight='bold', fontsize=12)
            
            plt.tight_layout(rect=[0, 0.02, 1, 0.96])
            
            # Save the comprehensive outlier plot
            outlier_plot_file = self.output_dir / "metabolic_curated_outlier_analysis.png"
            plt.savefig(outlier_plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Comprehensive CURATED metabolic outlier analysis plot saved: {outlier_plot_file}")
            return str(outlier_plot_file)
        
        except Exception as e:
            logger.error(f"Error creating comprehensive outlier analysis plot: {e}")
            return ""
    
    def _format_disease_label(self, disease: Dict) -> str:
        """Format disease label with name and prevalence in parentheses"""
        name = disease['disease_name']
        prevalence = disease['prevalence_per_million']
        
        # Truncate long names
        if len(name) > 35:
            name = name[:32] + "..."
        
        return f"{name}({prevalence:.1f}ppm)"
    
    def create_comprehensive_plot_grid(self) -> str:
        """
        Create comprehensive plot grid with all requested analyses
        
        Returns:
            Path to the generated plot file
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualization libraries not available")
            return ""
        
        logger.info("Creating comprehensive plot grid...")
        
        try:
            # Get data
            diseases_with_prevalence = self.client.get_diseases_with_prevalence()
            
            # Sort by prevalence for top/bottom analysis
            diseases_sorted = sorted(diseases_with_prevalence, key=lambda x: x['prevalence_per_million'], reverse=True)
            
            # Categorize diseases
            ultra_rare = [d for d in diseases_sorted if d['prevalence_per_million'] < 1.0 and d['prevalence_per_million'] > 0]
            very_rare = [d for d in diseases_sorted if 1.0 <= d['prevalence_per_million'] < 10.0]
            rare = [d for d in diseases_sorted if 10.0 <= d['prevalence_per_million'] < 50.0]
            common_rare = [d for d in diseases_sorted if d['prevalence_per_million'] >= 50.0]
            zero_prevalence = [d for d in diseases_sorted if d['prevalence_per_million'] == 0.0]
            
            # Create the plot grid
            fig, axes = plt.subplots(4, 3, figsize=(24, 32))
            fig.suptitle('Comprehensive Metabolic Disease Prevalence Analysis\nSpanish Patient Estimates (47M Population)', 
                        fontsize=20, fontweight='bold', y=0.98)
            
            # Row 1: Overall Top and Bottom
            # Top 25 diseases overall
            top_25 = diseases_sorted[:25]
            labels = [self._format_disease_label(d) for d in top_25]
            patients = [d['spanish_patients'] for d in top_25]
            
            axes[0, 0].barh(range(len(labels)), patients, color='darkgreen', alpha=0.7)
            axes[0, 0].set_yticks(range(len(labels)))
            axes[0, 0].set_yticklabels(labels, fontsize=8)
            axes[0, 0].set_xlabel('Spanish Patients', fontsize=10)
            axes[0, 0].set_title('Top 25 Metabolic Diseases\n(Highest Spanish Patient Count)', fontweight='bold', fontsize=12)
            axes[0, 0].invert_yaxis()
            axes[0, 0].grid(True, alpha=0.3)
            
            # Bottom 25 diseases overall (non-zero prevalence)
            non_zero = [d for d in diseases_sorted if d['prevalence_per_million'] > 0]
            bottom_25 = non_zero[-25:]
            labels_bottom = [self._format_disease_label(d) for d in bottom_25]
            patients_bottom = [d['spanish_patients'] for d in bottom_25]
            
            axes[0, 1].barh(range(len(labels_bottom)), patients_bottom, color='darkred', alpha=0.7)
            axes[0, 1].set_yticks(range(len(labels_bottom)))
            axes[0, 1].set_yticklabels(labels_bottom, fontsize=8)
            axes[0, 1].set_xlabel('Spanish Patients', fontsize=10)
            axes[0, 1].set_title('Bottom 25 Metabolic Diseases\n(Lowest Spanish Patient Count)', fontweight='bold', fontsize=12)
            axes[0, 1].invert_yaxis()
            axes[0, 1].grid(True, alpha=0.3)
            
            # Zero prevalence diseases (15 random)
            import random
            if len(zero_prevalence) >= 15:
                zero_sample = random.sample(zero_prevalence, 15)
            else:
                zero_sample = zero_prevalence
            
            zero_labels = [d['disease_name'][:40] + "..." if len(d['disease_name']) > 40 else d['disease_name'] for d in zero_sample]
            
            axes[0, 2].barh(range(len(zero_labels)), [0] * len(zero_labels), color='gray', alpha=0.7)
            axes[0, 2].set_yticks(range(len(zero_labels)))
            axes[0, 2].set_yticklabels(zero_labels, fontsize=8)
            axes[0, 2].set_xlabel('Spanish Patients', fontsize=10)
            axes[0, 2].set_title(f'Zero Prevalence Diseases\n({len(zero_sample)} Random Sample)', fontweight='bold', fontsize=12)
            axes[0, 2].invert_yaxis()
            axes[0, 2].grid(True, alpha=0.3)
            
            # Row 2: Common Rare and Rare diseases
            # Bottom 10 common rare
            if len(common_rare) >= 10:
                bottom_common_rare = sorted(common_rare, key=lambda x: x['prevalence_per_million'])[:10]
                labels_cr = [self._format_disease_label(d) for d in bottom_common_rare]
                patients_cr = [d['spanish_patients'] for d in bottom_common_rare]
                
                axes[1, 0].barh(range(len(labels_cr)), patients_cr, color='orange', alpha=0.7)
                axes[1, 0].set_yticks(range(len(labels_cr)))
                axes[1, 0].set_yticklabels(labels_cr, fontsize=8)
                axes[1, 0].set_xlabel('Spanish Patients', fontsize=10)
                axes[1, 0].set_title('Bottom 10 Common Rare Diseases\n(≥50ppm, Lowest)', fontweight='bold', fontsize=12)
                axes[1, 0].invert_yaxis()
                axes[1, 0].grid(True, alpha=0.3)
            else:
                axes[1, 0].text(0.5, 0.5, f'Only {len(common_rare)} Common Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[1, 0].transAxes, fontsize=12)
                axes[1, 0].set_title('Bottom 10 Common Rare Diseases', fontweight='bold', fontsize=12)
            
            # Top 10 rare diseases
            if len(rare) >= 10:
                top_rare = sorted(rare, key=lambda x: x['prevalence_per_million'], reverse=True)[:10]
                labels_r_top = [self._format_disease_label(d) for d in top_rare]
                patients_r_top = [d['spanish_patients'] for d in top_rare]
                
                axes[1, 1].barh(range(len(labels_r_top)), patients_r_top, color='blue', alpha=0.7)
                axes[1, 1].set_yticks(range(len(labels_r_top)))
                axes[1, 1].set_yticklabels(labels_r_top, fontsize=8)
                axes[1, 1].set_xlabel('Spanish Patients', fontsize=10)
                axes[1, 1].set_title('Top 10 Rare Diseases\n(10-49ppm, Highest)', fontweight='bold', fontsize=12)
                axes[1, 1].invert_yaxis()
                axes[1, 1].grid(True, alpha=0.3)
            else:
                axes[1, 1].text(0.5, 0.5, f'Only {len(rare)} Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[1, 1].transAxes, fontsize=12)
                axes[1, 1].set_title('Top 10 Rare Diseases', fontweight='bold', fontsize=12)
            
            # Bottom 10 rare diseases  
            if len(rare) >= 10:
                bottom_rare = sorted(rare, key=lambda x: x['prevalence_per_million'])[:10]
                labels_r_bottom = [self._format_disease_label(d) for d in bottom_rare]
                patients_r_bottom = [d['spanish_patients'] for d in bottom_rare]
                
                axes[1, 2].barh(range(len(labels_r_bottom)), patients_r_bottom, color='lightblue', alpha=0.7)
                axes[1, 2].set_yticks(range(len(labels_r_bottom)))
                axes[1, 2].set_yticklabels(labels_r_bottom, fontsize=8)
                axes[1, 2].set_xlabel('Spanish Patients', fontsize=10)
                axes[1, 2].set_title('Bottom 10 Rare Diseases\n(10-49ppm, Lowest)', fontweight='bold', fontsize=12)
                axes[1, 2].invert_yaxis()
                axes[1, 2].grid(True, alpha=0.3)
            else:
                axes[1, 2].text(0.5, 0.5, f'Only {len(rare)} Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[1, 2].transAxes, fontsize=12)
                axes[1, 2].set_title('Bottom 10 Rare Diseases', fontweight='bold', fontsize=12)
            
            # Row 3: Very Rare diseases
            # Top 10 very rare diseases
            if len(very_rare) >= 10:
                top_very_rare = sorted(very_rare, key=lambda x: x['prevalence_per_million'], reverse=True)[:10]
                labels_vr_top = [self._format_disease_label(d) for d in top_very_rare]
                patients_vr_top = [d['spanish_patients'] for d in top_very_rare]
                
                axes[2, 0].barh(range(len(labels_vr_top)), patients_vr_top, color='purple', alpha=0.7)
                axes[2, 0].set_yticks(range(len(labels_vr_top)))
                axes[2, 0].set_yticklabels(labels_vr_top, fontsize=8)
                axes[2, 0].set_xlabel('Spanish Patients', fontsize=10)
                axes[2, 0].set_title('Top 10 Very Rare Diseases\n(1-9ppm, Highest)', fontweight='bold', fontsize=12)
                axes[2, 0].invert_yaxis()
                axes[2, 0].grid(True, alpha=0.3)
            else:
                axes[2, 0].text(0.5, 0.5, f'Only {len(very_rare)} Very Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[2, 0].transAxes, fontsize=12)
                axes[2, 0].set_title('Top 10 Very Rare Diseases', fontweight='bold', fontsize=12)
            
            # Bottom 10 very rare diseases
            if len(very_rare) >= 10:
                bottom_very_rare = sorted(very_rare, key=lambda x: x['prevalence_per_million'])[:10]
                labels_vr_bottom = [self._format_disease_label(d) for d in bottom_very_rare]
                patients_vr_bottom = [d['spanish_patients'] for d in bottom_very_rare]
                
                axes[2, 1].barh(range(len(labels_vr_bottom)), patients_vr_bottom, color='pink', alpha=0.7)
                axes[2, 1].set_yticks(range(len(labels_vr_bottom)))
                axes[2, 1].set_yticklabels(labels_vr_bottom, fontsize=8)
                axes[2, 1].set_xlabel('Spanish Patients', fontsize=10)
                axes[2, 1].set_title('Bottom 10 Very Rare Diseases\n(1-9ppm, Lowest)', fontweight='bold', fontsize=12)
                axes[2, 1].invert_yaxis()
                axes[2, 1].grid(True, alpha=0.3)
            else:
                axes[2, 1].text(0.5, 0.5, f'Only {len(very_rare)} Very Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[2, 1].transAxes, fontsize=12)
                axes[2, 1].set_title('Bottom 10 Very Rare Diseases', fontweight='bold', fontsize=12)
            
            # Top 25 ultra rare diseases
            if len(ultra_rare) >= 25:
                top_ultra_rare = sorted(ultra_rare, key=lambda x: x['prevalence_per_million'], reverse=True)[:25]
                labels_ur_top = [self._format_disease_label(d) for d in top_ultra_rare]
                patients_ur_top = [d['spanish_patients'] for d in top_ultra_rare]
                
                axes[2, 2].barh(range(len(labels_ur_top)), patients_ur_top, color='brown', alpha=0.7)
                axes[2, 2].set_yticks(range(len(labels_ur_top)))
                axes[2, 2].set_yticklabels(labels_ur_top, fontsize=7)
                axes[2, 2].set_xlabel('Spanish Patients', fontsize=10)
                axes[2, 2].set_title('Top 25 Ultra-Rare Diseases\n(<1ppm, Highest)', fontweight='bold', fontsize=12)
                axes[2, 2].invert_yaxis()
                axes[2, 2].grid(True, alpha=0.3)
            else:
                axes[2, 2].text(0.5, 0.5, f'Only {len(ultra_rare)} Ultra-Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[2, 2].transAxes, fontsize=12)
                axes[2, 2].set_title('Top 25 Ultra-Rare Diseases', fontweight='bold', fontsize=12)
            
            # Row 4: Ultra-rare bottom and outlier analysis
            # Bottom 25 ultra rare diseases
            if len(ultra_rare) >= 25:
                bottom_ultra_rare = sorted(ultra_rare, key=lambda x: x['prevalence_per_million'])[:25]
                labels_ur_bottom = [self._format_disease_label(d) for d in bottom_ultra_rare]
                patients_ur_bottom = [d['spanish_patients'] for d in bottom_ultra_rare]
                
                axes[3, 0].barh(range(len(labels_ur_bottom)), patients_ur_bottom, color='lightcoral', alpha=0.7)
                axes[3, 0].set_yticks(range(len(labels_ur_bottom)))
                axes[3, 0].set_yticklabels(labels_ur_bottom, fontsize=7)
                axes[3, 0].set_xlabel('Spanish Patients', fontsize=10)
                axes[3, 0].set_title('Bottom 25 Ultra-Rare Diseases\n(<1ppm, Lowest)', fontweight='bold', fontsize=12)
                axes[3, 0].invert_yaxis()
                axes[3, 0].grid(True, alpha=0.3)
            else:
                axes[3, 0].text(0.5, 0.5, f'Only {len(ultra_rare)} Ultra-Rare\nDiseases Available', 
                              ha='center', va='center', transform=axes[3, 0].transAxes, fontsize=12)
                axes[3, 0].set_title('Bottom 25 Ultra-Rare Diseases', fontweight='bold', fontsize=12)
            
            # Outlier analysis visualization
            if 'outlier_analysis' not in self.analysis_results:
                self.analyze_outliers()
            
            outlier_data = self.analysis_results.get('outlier_analysis', {})
            if outlier_data and 'iqr_methods' in outlier_data:
                moderate_outliers = outlier_data['iqr_methods']['moderate']['top_outliers'][:15]
                if moderate_outliers:
                    outlier_labels = [f"{d['disease_name'][:35]}...({d['prevalence']:.1f}ppm)" 
                                    if len(d['disease_name']) > 35 else f"{d['disease_name']}({d['prevalence']:.1f}ppm)"
                                    for d in moderate_outliers]
                    outlier_patients = [d['spanish_patients'] for d in moderate_outliers]
                    
                    axes[3, 1].barh(range(len(outlier_labels)), outlier_patients, color='red', alpha=0.7)
                    axes[3, 1].set_yticks(range(len(outlier_labels)))
                    axes[3, 1].set_yticklabels(outlier_labels, fontsize=8)
                    axes[3, 1].set_xlabel('Spanish Patients', fontsize=10)
                    axes[3, 1].set_title('IQR Outliers (2.0x Method)\nHigh Prevalence Anomalies', fontweight='bold', fontsize=12)
                    axes[3, 1].invert_yaxis()
                    axes[3, 1].grid(True, alpha=0.3)
                else:
                    axes[3, 1].text(0.5, 0.5, 'No Outliers Detected\n(IQR 2.0x Method)', 
                                  ha='center', va='center', transform=axes[3, 1].transAxes, fontsize=12)
                    axes[3, 1].set_title('IQR Outliers (2.0x Method)', fontweight='bold', fontsize=12)
            
            # Distribution summary
            category_counts = {
                'Ultra-rare (<1ppm)': len(ultra_rare),
                'Very Rare (1-9ppm)': len(very_rare), 
                'Rare (10-49ppm)': len(rare),
                'Common Rare (≥50ppm)': len(common_rare),
                'Zero Prevalence': len(zero_prevalence)
            }
            
            labels_dist = list(category_counts.keys())
            sizes_dist = list(category_counts.values())
            colors_dist = ['brown', 'purple', 'blue', 'orange', 'gray']
            
            axes[3, 2].pie(sizes_dist, labels=labels_dist, colors=colors_dist, autopct='%1.1f%%', startangle=90)
            axes[3, 2].set_title('Metabolic Disease Distribution\nby Prevalence Category', fontweight='bold', fontsize=12)
            
            plt.tight_layout()
            
            # Save the comprehensive plot
            plot_file = self.output_dir / "metabolic_comprehensive_analysis_grid.png"
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Comprehensive plot grid saved: {plot_file}")
            return str(plot_file)
        
        except Exception as e:
            logger.error(f"Error creating comprehensive plot grid: {e}")
            return ""
    
    def generate_visualizations(self) -> List[str]:
        """
        Generate all visualizations for metabolic disease data
        
        Returns:
            List of generated visualization file paths
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualization libraries not available")
            return []
        
        logger.info("Generating all visualizations...")
        
        visualization_files = []
        
        try:
            # Generate comprehensive plot grid
            comprehensive_plot = self.create_comprehensive_plot_grid()
            if comprehensive_plot:
                visualization_files.append(comprehensive_plot)
            
            # Generate comprehensive outlier analysis plot
            outlier_plot = self.create_comprehensive_outlier_analysis_plot()
            if outlier_plot:
                visualization_files.append(outlier_plot)
            
            # Generate original summary plots
            plt.style.use('seaborn-v0_8')
            
            # 1. Prevalence distribution histogram
            prevalence_data = self.client.get_all_metabolic_prevalences()
            prevalences = list(prevalence_data.values())
            
            if prevalences:
                fig, axes = plt.subplots(2, 2, figsize=(15, 12))
                fig.suptitle('Metabolic Disease Prevalence Summary Analysis', fontsize=16, fontweight='bold')
                
                # 1. Prevalence distribution histogram
                axes[0, 0].hist(prevalences, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
                axes[0, 0].set_xlabel('Prevalence per Million')
                axes[0, 0].set_ylabel('Number of Diseases')
                axes[0, 0].set_title('Distribution of Metabolic Disease Prevalence')
                axes[0, 0].set_yscale('log')
                axes[0, 0].grid(True, alpha=0.3)
                
                # 2. Spanish patients distribution
                spanish_data = self.client.get_all_spanish_patients()
                patients = list(spanish_data.values())
                
                axes[0, 1].hist(patients, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
                axes[0, 1].set_xlabel('Spanish Patients')
                axes[0, 1].set_ylabel('Number of Diseases')
                axes[0, 1].set_title('Distribution of Spanish Patient Counts')
                axes[0, 1].set_yscale('log')
                axes[0, 1].grid(True, alpha=0.3)
                
                # 3. Top diseases by Spanish patients
                top_diseases = self.client.get_top_diseases_by_spanish_patients(15)
                disease_names = [d['disease_name'][:30] + '...' if len(d['disease_name']) > 30 else d['disease_name'] for d in top_diseases]
                patient_counts = [d['spanish_patients'] for d in top_diseases]
                
                axes[1, 0].barh(range(len(disease_names)), patient_counts, color='lightgreen')
                axes[1, 0].set_yticks(range(len(disease_names)))
                axes[1, 0].set_yticklabels(disease_names, fontsize=9)
                axes[1, 0].set_xlabel('Spanish Patients')
                axes[1, 0].set_title('Top 15 Diseases by Spanish Patient Count')
                axes[1, 0].invert_yaxis()
                axes[1, 0].grid(True, alpha=0.3)
                
                # 4. Prevalence categories pie chart
                distribution_data = self.analysis_results.get('prevalence_distribution', {})
                categories = distribution_data.get('prevalence_categories', {}).get('counts', {})
                
                if categories:
                    labels = list(categories.keys())
                    sizes = list(categories.values())
                    colors = ['gold', 'lightcoral', 'lightskyblue', 'lightgreen', 'pink']
                    
                    axes[1, 1].pie(sizes, labels=labels, colors=colors[:len(labels)], autopct='%1.1f%%', startangle=90)
                    axes[1, 1].set_title('Metabolic Diseases by Prevalence Category')
                
                plt.tight_layout()
                
                # Save the summary plot
                summary_file = self.output_dir / "metabolic_prevalence_summary.png"
                plt.savefig(summary_file, dpi=300, bbox_inches='tight')
                plt.close()
                
                visualization_files.append(str(summary_file))
                logger.info(f"Summary visualizations saved: {summary_file}")
        
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
        
        return visualization_files


def main():
    """Main function with CLI interface"""
    parser = argparse.ArgumentParser(description="Generate comprehensive statistics for metabolic disease prevalence")
    
    parser.add_argument(
        '--output',
        default="results/etl/metabolic",
        help="Output directory for statistics files"
    )
    
    parser.add_argument(
        '--json-only',
        action='store_true',
        help="Generate only JSON report (skip visualizations)"
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create analyzer and generate comprehensive report
    analyzer = MetabolicPrevalenceStatsAnalyzer(output_dir=args.output)
    
    if args.json_only:
        json_file = analyzer.generate_json_report()
        print(f"JSON report generated: {json_file}")
    else:
        summary = analyzer.generate_comprehensive_report()
        print(f"Comprehensive analysis completed. Files saved to: {summary['output_directory']}")


if __name__ == "__main__":
    main() 