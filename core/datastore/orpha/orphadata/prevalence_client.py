"""
Processed Prevalence Client - Query interface for prevalence data

This module provides a sophisticated interface for querying prevalence data
with lazy loading, caching, and advanced filtering capabilities for geographic,
reliability, and prevalence type dimensions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
from functools import lru_cache
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class ProcessedPrevalenceClient:
    """Client for processed prevalence data with lazy loading and advanced query capabilities"""
    
    def __init__(self, data_dir: str = "data/03_processed/orpha/orphadata/orpha_prevalence"):
        """
        Initialize the processed prevalence client
        
        Args:
            data_dir: Directory containing processed prevalence data
        """
        self.data_dir = Path(data_dir)
        
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Prevalence data directory not found: {data_dir}")
        
        # Lazy-loaded data structures
        self._disease2prevalence: Optional[Dict] = None
        self._prevalence2diseases: Optional[Dict] = None  
        self._prevalence_instances: Optional[Dict] = None
        self._orpha_index: Optional[Dict] = None
        self._processing_statistics: Optional[Dict] = None
        self._reliability_scores: Optional[Dict] = None
        self._prevalence_classes: Optional[Dict] = None
        self._geographic_index: Optional[Dict] = None
        
        # Cache for frequently accessed data
        self._cache = {}
        
        logger.info(f"Processed prevalence client initialized with data dir: {data_dir}")
    
    # ========== Data Loading Methods ==========
    
    def _ensure_disease2prevalence_loaded(self):
        """Load diseases to prevalence mapping if not already loaded"""
        if self._disease2prevalence is None:
            file_path = self.data_dir / "disease2prevalence.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._disease2prevalence = json.load(f)
                logger.info(f"Loaded disease2prevalence mapping: {len(self._disease2prevalence)} diseases")
            else:
                self._disease2prevalence = {}
                logger.warning("disease2prevalence.json not found")
    
    def _ensure_prevalence2diseases_loaded(self):
        """Load prevalence to diseases mapping if not already loaded"""
        if self._prevalence2diseases is None:
            file_path = self.data_dir / "prevalence2diseases.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prevalence2diseases = json.load(f)
                logger.info(f"Loaded prevalence2diseases mapping: {len(self._prevalence2diseases)} prevalence records")
            else:
                self._prevalence2diseases = {}
                logger.warning("prevalence2diseases.json not found")
    
    def _ensure_prevalence_instances_loaded(self):
        """Load prevalence instances if not already loaded"""
        if self._prevalence_instances is None:
            file_path = self.data_dir / "prevalence_instances.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prevalence_instances = json.load(f)
                logger.info(f"Loaded prevalence instances: {len(self._prevalence_instances)} records")
            else:
                self._prevalence_instances = {}
                logger.warning("prevalence_instances.json not found")
    
    def _ensure_orpha_index_loaded(self):
        """Load orpha index if not already loaded"""
        if self._orpha_index is None:
            file_path = self.data_dir / "orpha_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._orpha_index = json.load(f)
                logger.info(f"Loaded orpha index: {len(self._orpha_index)} diseases")
            else:
                self._orpha_index = {}
                logger.warning("orpha_index.json not found")
    
    def _ensure_processing_statistics_loaded(self):
        """Load processing statistics if not already loaded"""
        if self._processing_statistics is None:
            file_path = self.data_dir / "cache" / "statistics.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._processing_statistics = json.load(f)
                logger.info("Loaded processing statistics")
            else:
                self._processing_statistics = {}
                logger.warning("cache/statistics.json not found")
    
    def _ensure_reliability_scores_loaded(self):
        """Load reliability scores if not already loaded"""
        if self._reliability_scores is None:
            file_path = self.data_dir / "reliability" / "reliability_scores.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._reliability_scores = json.load(f)
                logger.info(f"Loaded reliability scores: {len(self._reliability_scores)} records")
            else:
                self._reliability_scores = {}
                logger.warning("reliability/reliability_scores.json not found")
    
    def _ensure_prevalence_classes_loaded(self):
        """Load prevalence classes mapping if not already loaded"""
        if self._prevalence_classes is None:
            file_path = self.data_dir / "cache" / "prevalence_classes.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._prevalence_classes = json.load(f)
                logger.info(f"Loaded prevalence classes: {len(self._prevalence_classes)} classes")
            else:
                self._prevalence_classes = {}
                logger.warning("cache/prevalence_classes.json not found")
    
    def _ensure_geographic_index_loaded(self):
        """Load geographic index if not already loaded"""
        if self._geographic_index is None:
            file_path = self.data_dir / "cache" / "geographic_index.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    self._geographic_index = json.load(f)
                logger.info(f"Loaded geographic index: {len(self._geographic_index)} regions")
            else:
                self._geographic_index = {}
                logger.warning("cache/geographic_index.json not found")
    
    # ========== Core Query Methods ==========
    
    def get_prevalence_for_disease(self, orpha_code: str, 
                                 prevalence_type: Optional[str] = None,
                                 geographic_area: Optional[str] = None,
                                 min_reliability: float = 0.0) -> List[Dict]:
        """
        Get prevalence records for a specific disease with optional filtering
        
        Args:
            orpha_code: Orpha code of the disease
            prevalence_type: Filter by type (Point prevalence, Prevalence at birth, etc.)
            geographic_area: Filter by geographic area
            min_reliability: Minimum reliability score (0-10)
            
        Returns:
            List of prevalence record dictionaries
        """
        self._ensure_disease2prevalence_loaded()
        
        disease_data = self._disease2prevalence.get(orpha_code)
        if not disease_data:
            return []
        
        records = disease_data.get('prevalence_records', [])
        
        # Apply filters
        if prevalence_type:
            records = [r for r in records if r.get('prevalence_type') == prevalence_type]
        
        if geographic_area:
            records = [r for r in records if r.get('geographic_area') == geographic_area]
        
        if min_reliability > 0:
            records = [r for r in records if r.get('reliability_score', 0) >= min_reliability]
        
        return records
    
    def get_disease_prevalence_summary(self, orpha_code: str) -> Optional[Dict]:
        """
        Get complete prevalence summary for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Complete disease prevalence mapping or None if not found
        """
        self._ensure_disease2prevalence_loaded()
        return self._disease2prevalence.get(orpha_code)
    
    def get_mean_prevalence_estimate(self, orpha_code: str) -> Optional[Dict]:
        """
        Get the weighted mean prevalence estimate for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            Dictionary with mean estimate and metadata or None if not found
        """
        disease_data = self.get_disease_prevalence_summary(orpha_code)
        if not disease_data:
            return None
        
        return {
            "orpha_code": orpha_code,
            "disease_name": disease_data.get("disease_name"),
            "mean_value_per_million": disease_data.get("mean_value_per_million", 0.0),
            "metadata": disease_data.get("mean_calculation_metadata", {})
        }
    
    def get_prevalence_details(self, prevalence_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific prevalence record
        
        Args:
            prevalence_id: Prevalence record ID
            
        Returns:
            Prevalence record dictionary or None if not found
        """
        self._ensure_prevalence_instances_loaded()
        return self._prevalence_instances.get(prevalence_id)
    
    # ========== Reliability-Based Queries ==========
    
    def get_most_reliable_prevalence(self, orpha_code: str, 
                                   prevalence_type: str = "Point prevalence") -> Optional[Dict]:
        """
        Get the most reliable prevalence record for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            prevalence_type: Preferred prevalence type
            
        Returns:
            Most reliable prevalence record or None if not found
        """
        disease_data = self.get_disease_prevalence_summary(orpha_code)
        if not disease_data:
            return None
        
        # Try to get most reliable of preferred type first
        records = self.get_prevalence_for_disease(orpha_code, prevalence_type=prevalence_type)
        if records:
            return max(records, key=lambda x: x.get('reliability_score', 0))
        
        # Fallback to overall most reliable
        return disease_data.get('most_reliable_prevalence')
    
    def get_reliable_prevalence_for_disease(self, orpha_code: str, 
                                          min_score: float = 6.0) -> List[Dict]:
        """
        Get all reliable prevalence records for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            min_score: Minimum reliability score (default: 6.0 for "fiable")
            
        Returns:
            List of reliable prevalence records
        """
        return self.get_prevalence_for_disease(orpha_code, min_reliability=min_score)
    
    def get_validated_prevalence_for_disease(self, orpha_code: str) -> List[Dict]:
        """
        Get validated prevalence records for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            
        Returns:
            List of validated prevalence records
        """
        disease_data = self.get_disease_prevalence_summary(orpha_code)
        if not disease_data:
            return []
        
        return disease_data.get('validated_prevalences', [])
    
    def get_best_prevalence_estimate(self, orpha_code: str, 
                                   prefer_worldwide: bool = True) -> Optional[Dict]:
        """
        Get the best available prevalence estimate for a disease
        
        Args:
            orpha_code: Orpha code of the disease
            prefer_worldwide: Prefer worldwide data over regional
            
        Returns:
            Best prevalence estimate or None if not found
        """
        # First try weighted mean if available
        mean_data = self.get_mean_prevalence_estimate(orpha_code)
        if mean_data and mean_data["mean_value_per_million"] > 0:
            return {
                "source": "weighted_mean",
                "prevalence_type": "Consolidated estimate",
                "per_million_estimate": mean_data["mean_value_per_million"],
                "reliability_score": 10.0,  # Max score for consolidated data
                "geographic_area": "Multiple regions",
                "metadata": mean_data["metadata"]
            }
        
        # Fallback to most reliable individual record
        if prefer_worldwide:
            worldwide_records = self.get_prevalence_for_disease(orpha_code, geographic_area="Worldwide")
            if worldwide_records:
                return max(worldwide_records, key=lambda x: x.get('reliability_score', 0))
        
        return self.get_most_reliable_prevalence(orpha_code)
    
    # ========== Geographic-Aware Queries ==========
    
    def get_worldwide_prevalence(self, orpha_code: str) -> List[Dict]:
        """Get worldwide prevalence data for a disease"""
        return self.get_prevalence_for_disease(orpha_code, geographic_area="Worldwide")
    
    def get_regional_prevalence(self, orpha_code: str, region: str) -> List[Dict]:
        """Get regional prevalence data for a disease"""
        return self.get_prevalence_for_disease(orpha_code, geographic_area=region)
    
    def get_prevalence_geographic_variants(self, orpha_code: str) -> Dict[str, List[Dict]]:
        """
        Get prevalence data grouped by geographic area
        
        Args:
            orpha_code: Orpha code of the disease
        
        Returns:
            Dictionary mapping regions to prevalence records
        """
        disease_data = self.get_disease_prevalence_summary(orpha_code)
        if not disease_data:
            return {}
        
        return disease_data.get('regional_prevalences', {})
    
    def get_available_regions(self) -> List[str]:
        """Get list of all available geographic regions"""
        self._ensure_geographic_index_loaded()
        return list(self._geographic_index.keys())
    
    def get_top_regions_by_data_volume(self, limit: int = 20) -> List[Dict]:
        """
        Get regions with the most prevalence data
        
        Args:
            limit: Maximum number of regions to return
        
        Returns:
            List of region entries sorted by data volume
        """
        self._ensure_geographic_index_loaded()
        
        regions_list = []
        for region, data in self._geographic_index.items():
            regions_list.append({
                'region': region,
                'total_records': data.get('total_records', 0),
                'diseases': len(data.get('diseases', []))
            })
        
        regions_list.sort(key=lambda r: r['total_records'], reverse=True)
        return regions_list[:limit]
    
    # ========== Statistics Methods ==========
    
    def get_statistics(self) -> Dict:
        """Get comprehensive prevalence statistics"""
        self._ensure_processing_statistics_loaded()
        return self._processing_statistics.copy() if self._processing_statistics else {}
    
    def get_basic_coverage_stats(self) -> Dict:
        """Get basic coverage statistics"""
        stats = self.get_statistics()
        
        return {
            "total_disorders": stats.get("total_disorders", 0),
            "disorders_with_prevalence": stats.get("disorders_with_prevalence", 0),
            "total_prevalence_records": stats.get("total_prevalence_records", 0),
            "reliable_records": stats.get("reliable_records", 0),
            "reliability_percentage": round((stats.get("reliable_records", 0) / max(stats.get("total_prevalence_records", 1), 1)) * 100, 2)
        }
    
    def get_data_quality_metrics(self) -> Dict:
        """Get data quality metrics"""
        self._ensure_disease2prevalence_loaded()
        self._ensure_prevalence_instances_loaded()
        
        total_diseases = len(self._disease2prevalence)
        diseases_with_mean = len([d for d in self._disease2prevalence.values() if d.get('mean_value_per_million', 0) > 0])
        
        validation_counts = {}
        for record in self._prevalence_instances.values():
            status = record.get('validation_status', 'Unknown')
            validation_counts[status] = validation_counts.get(status, 0) + 1
        
        return {
            "total_diseases": total_diseases,
            "diseases_with_mean_estimates": diseases_with_mean,
            "mean_estimate_coverage": round((diseases_with_mean / max(total_diseases, 1)) * 100, 2),
            "validation_status_distribution": validation_counts
        }
    
    def get_reliability_distribution(self) -> Dict[str, int]:
        """Get distribution of reliability scores in ranges"""
        self._ensure_prevalence_instances_loaded()
        
        score_ranges = {
            "0-2": 0, "2-4": 0, "4-6": 0, 
            "6-8": 0, "8-10": 0
        }
        
        for record in self._prevalence_instances.values():
            score = record.get('reliability_score', 0)
            if score < 2:
                score_ranges["0-2"] += 1
            elif score < 4:
                score_ranges["2-4"] += 1
            elif score < 6:
                score_ranges["4-6"] += 1
            elif score < 8:
                score_ranges["6-8"] += 1
            else:
                score_ranges["8-10"] += 1
        
        return score_ranges
    
    def get_validation_status_distribution(self) -> Dict[str, int]:
        """Get distribution by validation status"""
        stats = self.get_statistics()
        return stats.get('validation_status_distribution', {})
    
    def get_source_quality_breakdown(self) -> Dict[str, int]:
        """Get breakdown of source types"""
        self._ensure_prevalence_instances_loaded()
        
        source_types = {
            "PMID_referenced": 0,
            "Registry_based": 0,
            "Expert_opinion": 0,
            "Other": 0
        }
        
        for record in self._prevalence_instances.values():
            source = record.get('source', '') or ''
            if '[PMID]' in source:
                source_types["PMID_referenced"] += 1
            elif '[REG]' in source or 'surveillance' in source.lower():
                source_types["Registry_based"] += 1
            elif '[EXPERT]' in source:
                source_types["Expert_opinion"] += 1
            else:
                source_types["Other"] += 1
        
        return source_types
    
    def get_geographic_distribution(self) -> Dict[str, int]:
        """Get distribution of records by geographic area"""
        stats = self.get_statistics()
        return stats.get('geographic_distribution', {})
    
    def get_prevalence_type_distribution(self) -> Dict[str, int]:
        """Get distribution by prevalence type"""
        stats = self.get_statistics()
        return stats.get('prevalence_type_distribution', {})
    
    def get_estimate_confidence_breakdown(self) -> Dict[str, int]:
        """Get breakdown of estimate confidence levels"""
        stats = self.get_statistics()
        return stats.get('estimate_source_distribution', {})
    
    def get_fiable_vs_non_fiable_stats(self) -> Dict[str, int]:
        """Get reliable vs non-reliable record counts"""
        self._ensure_prevalence_instances_loaded()
        
        fiable_count = 0
        non_fiable_count = 0
        
        for record in self._prevalence_instances.values():
            if record.get('is_fiable', False):
                fiable_count += 1
            else:
                non_fiable_count += 1
        
        return {
            "fiable_records": fiable_count,
            "non_fiable_records": non_fiable_count,
            "fiable_percentage": round((fiable_count / max(fiable_count + non_fiable_count, 1)) * 100, 2)
        }
    
    def get_diseases_with_most_prevalence_records(self, limit: int = 20) -> List[Dict]:
        """Get diseases with the most prevalence records"""
        self._ensure_disease2prevalence_loaded()
        
        diseases_list = []
        for orpha_code, disease_data in self._disease2prevalence.items():
            diseases_list.append({
                'orpha_code': orpha_code,
                'disease_name': disease_data.get('disease_name'),
                'total_records': len(disease_data.get('prevalence_records', [])),
                'reliable_records': disease_data.get('statistics', {}).get('reliable_records', 0),
                'mean_value_per_million': disease_data.get('mean_value_per_million', 0.0)
            })
        
        diseases_list.sort(key=lambda d: d['total_records'], reverse=True)
        return diseases_list[:limit]
    
    def get_diseases_by_reliability_score(self, limit: int = 20) -> List[Dict]:
        """Get diseases with highest average reliability scores"""
        self._ensure_disease2prevalence_loaded()
        
        diseases_list = []
        for orpha_code, disease_data in self._disease2prevalence.items():
            records = disease_data.get('prevalence_records', [])
            if records:
                avg_reliability = statistics.mean(r.get('reliability_score', 0) for r in records)
                diseases_list.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name'),
                    'avg_reliability': round(avg_reliability, 2),
                    'total_records': len(records),
                    'mean_value_per_million': disease_data.get('mean_value_per_million', 0.0)
                })
        
        diseases_list.sort(key=lambda d: d['avg_reliability'], reverse=True)
        return diseases_list[:limit]
    
    def get_diseases_with_global_coverage(self) -> List[Dict]:
        """Get diseases with worldwide prevalence data"""
        self._ensure_disease2prevalence_loaded()
        
        global_diseases = []
        for orpha_code, disease_data in self._disease2prevalence.items():
            regional_data = disease_data.get('regional_prevalences', {})
            if 'Worldwide' in regional_data:
                global_diseases.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name'),
                    'worldwide_records': len(regional_data.get('Worldwide', [])),
                    'total_regions': len(regional_data),
                    'mean_value_per_million': disease_data.get('mean_value_per_million', 0.0)
                })
        
        return global_diseases
    
    def get_diseases_with_regional_variations(self) -> List[Dict]:
        """Get diseases with prevalence data in multiple regions"""
        self._ensure_disease2prevalence_loaded()
        
        multi_region_diseases = []
        for orpha_code, disease_data in self._disease2prevalence.items():
            regional_data = disease_data.get('regional_prevalences', {})
            if len(regional_data) > 1:
                multi_region_diseases.append({
                    'orpha_code': orpha_code,
                    'disease_name': disease_data.get('disease_name'),
                    'region_count': len(regional_data),
                    'regions': list(regional_data.keys()),
                    'mean_value_per_million': disease_data.get('mean_value_per_million', 0.0)
                })
        
        # Sort by number of regions
        multi_region_diseases.sort(key=lambda d: d['region_count'], reverse=True)
        return multi_region_diseases
    
    def get_regional_data_quality(self) -> Dict[str, float]:
        """Get average reliability scores by region"""
        self._ensure_prevalence_instances_loaded()
        
        region_scores = {}
        region_counts = {}
        
        for record in self._prevalence_instances.values():
            region = record.get('geographic_area', 'Unknown')
            score = record.get('reliability_score', 0)
            
            if region not in region_scores:
                region_scores[region] = 0
                region_counts[region] = 0
            
            region_scores[region] += score
            region_counts[region] += 1
        
        regional_quality = {}
        for region in region_scores:
            if region_counts[region] > 0:
                regional_quality[region] = round(region_scores[region] / region_counts[region], 2)
        
        return regional_quality
    
    def get_regional_coverage_completeness(self) -> Dict[str, int]:
        """Get number of diseases per region"""
        self._ensure_geographic_index_loaded()
        
        region_completeness = {}
        for region, data in self._geographic_index.items():
            region_completeness[region] = len(data.get('diseases', []))
        
        return region_completeness
    
    def get_reliability_by_prevalence_type(self) -> Dict[str, float]:
        """Get average reliability scores by prevalence type"""
        self._ensure_prevalence_instances_loaded()
        
        type_scores = {}
        type_counts = {}
        
        for record in self._prevalence_instances.values():
            prev_type = record.get('prevalence_type', 'Unknown')
            score = record.get('reliability_score', 0)
            
            if prev_type not in type_scores:
                type_scores[prev_type] = 0
                type_counts[prev_type] = 0
            
            type_scores[prev_type] += score
            type_counts[prev_type] += 1
        
        type_reliability = {}
        for prev_type in type_scores:
            if type_counts[prev_type] > 0:
                type_reliability[prev_type] = round(type_scores[prev_type] / type_counts[prev_type], 2)
        
        return type_reliability
    
    def get_prevalence_class_distribution(self) -> Dict[str, int]:
        """Get distribution by prevalence class"""
        self._ensure_prevalence_instances_loaded()
        
        class_dist = {}
        for record in self._prevalence_instances.values():
            prev_class = record.get('prevalence_class') or 'Unknown'
            class_dist[prev_class] = class_dist.get(prev_class, 0) + 1
        
        return class_dist
    
    def get_rarity_spectrum_analysis(self) -> Dict[str, int]:
        """Get analysis of rarity spectrum"""
        class_dist = self.get_prevalence_class_distribution()
        
        rarity_spectrum = {
            "ultra_rare": 0,      # <1 / 1,000,000
            "very_rare": 0,       # 1-9 / 1,000,000
            "rare": 0,            # 1-9 / 100,000
            "uncommon": 0,        # 1-5 / 10,000+
            "common": 0,          # >1 / 1,000
            "unknown": 0          # Unknown/Not documented
        }
        
        for prev_class, count in class_dist.items():
            if prev_class and "< 1" in prev_class and "1 000 000" in prev_class:
                rarity_spectrum["ultra_rare"] += count
            elif prev_class and "1-9" in prev_class and "1 000 000" in prev_class:
                rarity_spectrum["very_rare"] += count
            elif prev_class and "1-9" in prev_class and "100 000" in prev_class:
                rarity_spectrum["rare"] += count
            elif prev_class and ("1-5" in prev_class or "6-9" in prev_class) and "10 000" in prev_class:
                rarity_spectrum["uncommon"] += count
            elif prev_class and "> 1" in prev_class:
                rarity_spectrum["common"] += count
            else:
                rarity_spectrum["unknown"] += count
        
        return rarity_spectrum
    
    def get_data_density_analysis(self) -> Dict:
        """Analyze distribution of records per disease"""
        self._ensure_disease2prevalence_loaded()
        
        record_counts = []
        for disease_data in self._disease2prevalence.values():
            record_counts.append(len(disease_data.get('prevalence_records', [])))
        
        if not record_counts:
            return {}
        
        return {
            "min_records": min(record_counts),
            "max_records": max(record_counts),
            "mean_records": round(statistics.mean(record_counts), 2),
            "median_records": statistics.median(record_counts),
            "total_diseases": len(record_counts)
        }
    
    def get_multi_region_diseases(self) -> List[Dict]:
        """Get diseases with prevalence data in multiple regions (>5 regions)"""
        multi_region = self.get_diseases_with_regional_variations()
        return [d for d in multi_region if d['region_count'] >= 5]
    
    def get_consensus_analysis(self) -> Dict:
        """Analyze where multiple sources agree"""
        self._ensure_disease2prevalence_loaded()
        
        consensus_diseases = 0
        total_multi_record_diseases = 0
        
        for disease_data in self._disease2prevalence.values():
            records = disease_data.get('prevalence_records', [])
            if len(records) > 1:
                total_multi_record_diseases += 1
                
                # Check if estimates are within reasonable range of each other
                estimates = [r.get('per_million_estimate', 0) for r in records if r.get('per_million_estimate', 0) > 0]
                if len(estimates) > 1:
                    est_min, est_max = min(estimates), max(estimates)
                    if est_max <= est_min * 10:  # Within order of magnitude
                        consensus_diseases += 1
        
        return {
            "diseases_with_multiple_records": total_multi_record_diseases,
            "diseases_with_consensus": consensus_diseases,
            "consensus_percentage": round((consensus_diseases / max(total_multi_record_diseases, 1)) * 100, 2)
        }
    
    def get_data_gaps_analysis(self) -> Dict:
        """Analyze missing data patterns"""
        self._ensure_disease2prevalence_loaded()
        
        gaps_analysis = {
            "diseases_without_worldwide_data": 0,
            "diseases_without_reliable_data": 0,
            "diseases_without_mean_estimate": 0,
            "total_diseases": len(self._disease2prevalence)
        }
        
        for disease_data in self._disease2prevalence.values():
            regional_data = disease_data.get('regional_prevalences', {})
            if 'Worldwide' not in regional_data:
                gaps_analysis["diseases_without_worldwide_data"] += 1
            
            reliable_records = disease_data.get('statistics', {}).get('reliable_records', 0)
            if reliable_records == 0:
                gaps_analysis["diseases_without_reliable_data"] += 1
            
            if disease_data.get('mean_value_per_million', 0) == 0:
                gaps_analysis["diseases_without_mean_estimate"] += 1
        
        return gaps_analysis
    
    def search_reliable_prevalence(self, min_score: float = 6.0) -> List[Dict]:
        """Search reliable prevalence records (≥6.0 score)"""
        self._ensure_prevalence_instances_loaded()
        
        reliable_records = []
        for record in self._prevalence_instances.values():
            if record.get('reliability_score', 0) >= min_score:
                reliable_records.append(record)
        
        return reliable_records
    
    def search_validated_prevalence(self) -> List[Dict]:
        """Get all validated prevalence records"""
        self._ensure_prevalence_instances_loaded()
        
        validated_records = []
        for record in self._prevalence_instances.values():
            if record.get('validation_status') == "Validated":
                validated_records.append(record)
        
        return validated_records
    
    # ========== Utility Methods ==========
    
    def clear_cache(self):
        """Clear all cached data to free memory"""
        self._disease2prevalence = None
        self._prevalence2diseases = None
        self._prevalence_instances = None
        self._orpha_index = None
        self._processing_statistics = None
        self._reliability_scores = None
        self._prevalence_classes = None
        self._geographic_index = None
        self._cache.clear()
        logger.info("Processed prevalence client cache cleared")
    
    def preload_all(self):
        """Preload all data for better performance"""
        self._ensure_disease2prevalence_loaded()
        self._ensure_prevalence2diseases_loaded()
        self._ensure_prevalence_instances_loaded()
        self._ensure_orpha_index_loaded()
        self._ensure_processing_statistics_loaded()
        self._ensure_reliability_scores_loaded()
        self._ensure_prevalence_classes_loaded()
        self._ensure_geographic_index_loaded()
        logger.info("All prevalence data preloaded")
    
    def is_data_available(self) -> bool:
        """Check if prevalence data is available"""
        required_files = [
            "disease2prevalence.json",
            "prevalence_instances.json",
            "orpha_index.json"
        ]
        
        for filename in required_files:
            if not (self.data_dir / filename).exists():
                return False
        
        return True
    
    @lru_cache(maxsize=1000)
    def _get_disease_cached(self, orpha_code: str) -> Optional[Dict]:
        """Cached version of disease lookup"""
        return self.get_disease_prevalence_summary(orpha_code)


# Example usage and testing
def main():
    """Example usage of the ProcessedPrevalenceClient"""
    
    controller = ProcessedPrevalenceClient()
    
    if not controller.is_data_available():
        print("Prevalence data not available. Run process_orpha_prevalence.py first.")
        return
    
    # Get basic statistics
    stats = controller.get_basic_coverage_stats()
    print(f"Prevalence Statistics:")
    print(f"- Total disorders: {stats.get('total_disorders', 'N/A')}")
    print(f"- Disorders with prevalence: {stats.get('disorders_with_prevalence', 'N/A')}")
    print(f"- Total prevalence records: {stats.get('total_prevalence_records', 'N/A')}")
    print(f"- Reliable records: {stats.get('reliable_records', 'N/A')} ({stats.get('reliability_percentage', 'N/A')}%)")
    
    # Get available regions
    regions = controller.get_available_regions()
    print(f"\nGeographic coverage: {len(regions)} regions")
    
    # Get top regions
    top_regions = controller.get_top_regions_by_data_volume(5)
    print(f"\nTop 5 regions by data volume:")
    for region in top_regions:
        print(f"- {region['region']}: {region['total_records']} records ({region['diseases']} diseases)")


if __name__ == "__main__":
    main() 