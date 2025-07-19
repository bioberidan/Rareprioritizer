#!/usr/bin/env python3
"""
Main script for processing Orphanet prevalence data (en_product9_prev.xml)

Usage:
    python prevalence_preprocessing.py
    python prevalence_preprocessing.py --xml path/to/en_product9_prev.xml --output path/to/output
    python prevalence_preprocessing.py --force --validate-only
"""
import argparse
import json
import logging
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('prevalence_preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)


def calculate_reliability_score(prevalence_record):
    """Calculate reliability score (0-10) based on data quality criteria"""
    score = 0.0
    
    # Validation status (3 points)
    if prevalence_record.get('validation_status') == "Validated":
        score += 3.0
    
    # Source quality (2 points)
    source = prevalence_record.get('source', '') or ''
    if "[PMID]" in source:
        score += 2.0
    elif "[EXPERT]" in source:
        score += 1.0
    
    # Data qualification (2 points)
    qualification = prevalence_record.get('qualification', '')
    if qualification == "Value and class":
        score += 2.0
    elif qualification == "Class only":
        score += 1.0
    
    # Prevalence type reliability (2 points)
    prev_type = prevalence_record.get('prevalence_type', '')
    if prev_type == "Point prevalence":
        score += 2.0
    elif prev_type == "Prevalence at birth":
        score += 1.8
    elif prev_type == "Annual incidence":
        score += 1.5
    elif prev_type == "Cases/families":
        score += 1.0
    
    # Geographic specificity (1 point)
    geographic_area = prevalence_record.get('geographic_area') or ''
    if geographic_area and geographic_area != "Worldwide":
        score += 1.0
    
    return min(score, 10.0)


def calculate_weighted_mean_prevalence(prevalence_records):
    """Calculate reliability-weighted mean prevalence per million
    
    Note: Mean prevalence is capped at 500 per million for epidemiological coherence.
    Individual records can have higher values, but global mean estimates are capped.
    """
    # Filter valid records for calculation
    valid_records = []
    excluded_counts = {
        "cases_families": 0,
        "unknown_class": 0,
        "zero_estimate": 0
    }
    
    for record in prevalence_records:
        # Exclude qualitative data
        if record.get("prevalence_type") == "Cases/families":
            excluded_counts["cases_families"] += 1
            continue
        # Exclude unknown/undocumented  
        if record.get("prevalence_class") in ["Unknown", "Not yet documented", None]:
            excluded_counts["unknown_class"] += 1
            continue
        # Exclude zero estimates
        if record.get("per_million_estimate", 0) <= 0:
            excluded_counts["zero_estimate"] += 1
            continue
        valid_records.append(record)
    
    if not valid_records:
        return {
            "mean_value_per_million": 0.0,
            "uncapped_mean_per_million": 0.0,
            "is_capped": False,
            "valid_records_count": 0,
            "calculation_method": "no_valid_data",
            "total_records_count": len(prevalence_records),
            "weight_sum": 0.0,
            "excluded_records": excluded_counts,
            "weight_distribution": {
                "min_weight": 0.0,
                "max_weight": 0.0,
                "mean_weight": 0.0
            }
        }
    
    # Calculate weighted mean
    weighted_sum = 0.0
    weight_sum = 0.0
    weights = []
    
    for record in valid_records:
        prevalence = record["per_million_estimate"]
        weight = record["reliability_score"]
        weighted_sum += prevalence * weight
        weight_sum += weight
        weights.append(weight)
    
    if weight_sum == 0:
        # Fallback to simple mean if all weights are zero
        mean_value = sum(r["per_million_estimate"] for r in valid_records) / len(valid_records)
        calculation_method = "simple_mean_fallback"
    else:
        mean_value = weighted_sum / weight_sum
        calculation_method = "reliability_weighted_mean"
    
    # Cap mean prevalence at 500 per million (global epidemiological ceiling)
    if mean_value > 500.0:
        uncapped_mean = mean_value
        mean_value = 500.0
        calculation_method += "_capped_at_500"
    else:
        uncapped_mean = mean_value
    
    return {
        "mean_value_per_million": round(mean_value, 2),
        "uncapped_mean_per_million": round(uncapped_mean, 2),
        "is_capped": mean_value != uncapped_mean,
        "valid_records_count": len(valid_records),
        "calculation_method": calculation_method,
        "total_records_count": len(prevalence_records),
        "weight_sum": round(weight_sum, 2),
        "excluded_records": excluded_counts,
        "weight_distribution": {
            "min_weight": min(weights) if weights else 0.0,
            "max_weight": max(weights) if weights else 0.0,
            "mean_weight": round(sum(weights) / len(weights), 2) if weights else 0.0
        }
    }


def standardize_prevalence_class(prevalence_class):
    """Convert prevalence class to per-million estimates using midpoint calculation
    
    Note: ">1 / 1000" interpreted as range "1-9/1000" with midpoint "5/1000" = 5000 per million
    """
    
    if not prevalence_class or prevalence_class in ["Unknown", "Not yet documented", ""]:
        return {
            "per_million_estimate": 0.0,
            "confidence": "none",
            "source": "no_data"
        }
    
    class_mappings = {
        # Standard comma-separated formats
        ">1 / 1,000": {
            "per_million_estimate": 5000.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 1000, "max": 9000}
        },
        "1-5 / 10,000": {
            "per_million_estimate": 300.0,
            "confidence": "high", 
            "source": "class_midpoint",
            "range": {"min": 100, "max": 500}
        },
        "6-9 / 10,000": {
            "per_million_estimate": 750.0,
            "confidence": "high",
            "source": "class_midpoint", 
            "range": {"min": 600, "max": 900}
        },
        "1-9 / 100,000": {
            "per_million_estimate": 50.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 10, "max": 90}
        },
        "1-9 / 1,000,000": {
            "per_million_estimate": 5.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 1, "max": 9}
        },
        "<1 / 1,000,000": {
            "per_million_estimate": 0.5,
            "confidence": "medium",
            "source": "class_estimate",
            "range": {"min": 0, "max": 1}
        },
        # Space-separated formats (actual XML format)
        ">1 / 1000": {
            "per_million_estimate": 5000.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 1000, "max": 9000}
        },
        "1-5 / 10 000": {
            "per_million_estimate": 300.0,
            "confidence": "high", 
            "source": "class_midpoint",
            "range": {"min": 100, "max": 500}
        },
        "6-9 / 10 000": {
            "per_million_estimate": 750.0,
            "confidence": "high",
            "source": "class_midpoint", 
            "range": {"min": 600, "max": 900}
        },
        "1-9 / 100 000": {
            "per_million_estimate": 50.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 10, "max": 90}
        },
        "1-9 / 1 000 000": {
            "per_million_estimate": 5.0,
            "confidence": "high",
            "source": "class_midpoint",
            "range": {"min": 1, "max": 9}
        },
        "<1 / 1 000 000": {
            "per_million_estimate": 0.5,
            "confidence": "medium",
            "source": "class_estimate",
            "range": {"min": 0, "max": 1}
        }
    }
    
    if prevalence_class in class_mappings:
        return class_mappings[prevalence_class]
    else:
        logger.warning(f"Unknown prevalence class: {prevalence_class}")
        return {
            "per_million_estimate": 0.0,
            "confidence": "none",
            "source": "unknown_class"
        }


def process_prevalence_xml(xml_path, output_dir):
    """Process en_product9_prev.xml and generate all preprocessing files"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Data structures
    disease2prevalence = {}
    prevalence2diseases = defaultdict(list)
    prevalence_instances = {}
    orpha_index = {}
    
    # Regional and reliability data
    regional_data = defaultdict(list)
    reliable_prevalences = {}
    reliability_scores = {}
    
    # Statistics
    stats = {
        "total_disorders": 0,
        "disorders_with_prevalence": 0,
        "total_prevalence_records": 0,
        "reliable_records": 0,
        "geographic_distribution": defaultdict(int),
        "validation_status_distribution": defaultdict(int),
        "prevalence_type_distribution": defaultdict(int),
        "prevalence_class_distribution": defaultdict(int),
        "estimate_source_distribution": defaultdict(int),
        "processing_timestamp": datetime.now().isoformat()
    }
    
    logger.info(f"Processing disorders from {xml_path}")
    
    for disorder in root.findall('.//Disorder'):
        stats["total_disorders"] += 1
        
        orpha_code = disorder.find('OrphaCode').text
        name_elem = disorder.find('Name[@lang="en"]')
        name = name_elem.text if name_elem is not None else f"Unknown_{orpha_code}"
        
        prevalence_list = disorder.find('PrevalenceList')
        if prevalence_list is None:
            continue
            
        stats["disorders_with_prevalence"] += 1
        prevalence_records = []
        
        for prevalence in prevalence_list.findall('Prevalence'):
            stats["total_prevalence_records"] += 1
            
            prev_id = prevalence.get('id')
            source_elem = prevalence.find('Source')
            
            # Extract prevalence data
            prev_type_elem = prevalence.find('PrevalenceType/Name[@lang="en"]')
            prev_class_elem = prevalence.find('PrevalenceClass/Name[@lang="en"]')
            prev_qual_elem = prevalence.find('PrevalenceQualification/Name[@lang="en"]')
            prev_valid_elem = prevalence.find('PrevalenceValidationStatus/Name[@lang="en"]')
            prev_geo_elem = prevalence.find('PrevalenceGeographic/Name[@lang="en"]')
            
            record = {
                "prevalence_id": prev_id,
                "orpha_code": orpha_code,
                "disease_name": name,
                "source": source_elem.text if source_elem is not None else "",
                "prevalence_type": prev_type_elem.text if prev_type_elem is not None else "",
                "prevalence_class": prev_class_elem.text if prev_class_elem is not None else None,
                "qualification": prev_qual_elem.text if prev_qual_elem is not None else "",
                "geographic_area": prev_geo_elem.text if prev_geo_elem is not None else "",
                "validation_status": prev_valid_elem.text if prev_valid_elem is not None else ""
            }
            
            # Calculate reliability score
            reliability = calculate_reliability_score(record)
            record["reliability_score"] = reliability
            record["is_fiable"] = reliability >= 6.0
            
            # Calculate per-million estimate ONLY from prevalence class
            class_data = standardize_prevalence_class(record["prevalence_class"])
            record["per_million_estimate"] = class_data["per_million_estimate"]
            record["confidence_level"] = class_data["confidence"]
            record["estimate_source"] = class_data["source"]
            
            prevalence_records.append(record)
            prevalence_instances[prev_id] = record
            prevalence2diseases[prev_id].append(orpha_code)
            
            # Update statistics
            stats["geographic_distribution"][record["geographic_area"]] += 1
            stats["validation_status_distribution"][record["validation_status"]] += 1
            stats["prevalence_type_distribution"][record["prevalence_type"]] += 1
            stats["prevalence_class_distribution"][record["prevalence_class"]] += 1
            stats["estimate_source_distribution"][record["estimate_source"]] += 1
            
            if record["is_fiable"]:
                stats["reliable_records"] += 1
                reliable_prevalences[prev_id] = record
            
            # Regional data
            geo_area = record["geographic_area"] or "Unknown"
            regional_data[geo_area].append(record)
            
            # Reliability scores
            reliability_scores[prev_id] = {
                "prevalence_id": prev_id,
                "reliability_score": reliability,
                "is_fiable": record["is_fiable"],
                "score_breakdown": {
                    "validation_status": record["validation_status"],
                    "has_pmid": "[PMID]" in (record["source"] or ""),
                    "qualification": record["qualification"],
                    "prevalence_type": record["prevalence_type"],
                    "geographic_specificity": (record["geographic_area"] or "") != "Worldwide"
                }
            }
        
        if prevalence_records:
            # Find most reliable prevalence
            most_reliable = max(prevalence_records, key=lambda x: x["reliability_score"])
            validated_records = [r for r in prevalence_records if r["validation_status"] == "Validated"]
            
            # Group by geographic area
            regional_prevalences = defaultdict(list)
            for record in prevalence_records:
                geo_area = record["geographic_area"] or "Unknown"
                regional_prevalences[geo_area].append(record)
            
            # Calculate weighted mean prevalence
            mean_data = calculate_weighted_mean_prevalence(prevalence_records)
            
            disease2prevalence[orpha_code] = {
                "orpha_code": orpha_code,
                "disease_name": name,
                "prevalence_records": prevalence_records,
                "most_reliable_prevalence": most_reliable,
                "validated_prevalences": validated_records,
                "regional_prevalences": dict(regional_prevalences),
                "mean_value_per_million": mean_data["mean_value_per_million"],
                "mean_calculation_metadata": mean_data,
                "statistics": {
                    "total_records": len(prevalence_records),
                    "reliable_records": len([r for r in prevalence_records if r["is_fiable"]]),
                    "valid_for_mean": mean_data["valid_records_count"]
                }
            }
            
            orpha_index[orpha_code] = {
                "disease_name": name,
                "total_prevalence_records": len(prevalence_records),
                "reliable_records": len([r for r in prevalence_records if r["is_fiable"]]),
                "geographic_areas": list(set(r["geographic_area"] or "Unknown" for r in prevalence_records))
            }
    
    logger.info(f"Processed {stats['disorders_with_prevalence']} disorders with prevalence data")
    
    # Create output directories
    output_path = Path(output_dir)
    regional_dir = output_path / "regional_data"
    reliability_dir = output_path / "reliability"
    cache_dir = output_path / "cache"
    
    for dir_path in [output_path, regional_dir, reliability_dir, cache_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Save main files
    with open(output_path / "disease2prevalence.json", 'w', encoding='utf-8') as f:
        json.dump(disease2prevalence, f, indent=2, ensure_ascii=False)
    
    with open(output_path / "prevalence2diseases.json", 'w', encoding='utf-8') as f:
        json.dump(dict(prevalence2diseases), f, indent=2, ensure_ascii=False)
    
    with open(output_path / "prevalence_instances.json", 'w', encoding='utf-8') as f:
        json.dump(prevalence_instances, f, indent=2, ensure_ascii=False)
    
    with open(output_path / "orpha_index.json", 'w', encoding='utf-8') as f:
        json.dump(orpha_index, f, indent=2, ensure_ascii=False)
    
    # Save regional data
    for region, records in regional_data.items():
        safe_region = region.replace("/", "_").replace(" ", "_")
        with open(regional_dir / f"{safe_region.lower()}_prevalences.json", 'w', encoding='utf-8') as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
    
    # Regional summary
    regional_summary = {
        region: {
            "total_records": len(records),
            "reliable_records": len([r for r in records if r["is_fiable"]]),
            "diseases": len(set(r["orpha_code"] for r in records))
        }
        for region, records in regional_data.items()
    }
    
    with open(regional_dir / "regional_summary.json", 'w', encoding='utf-8') as f:
        json.dump(regional_summary, f, indent=2, ensure_ascii=False)
    
    # Save reliability data
    with open(reliability_dir / "reliable_prevalences.json", 'w', encoding='utf-8') as f:
        json.dump(reliable_prevalences, f, indent=2, ensure_ascii=False)
    
    with open(reliability_dir / "reliability_scores.json", 'w', encoding='utf-8') as f:
        json.dump(reliability_scores, f, indent=2, ensure_ascii=False)
    
    # Validation report
    validation_report = {
        "processing_timestamp": stats["processing_timestamp"],
        "data_quality_metrics": {
            "total_records": stats["total_prevalence_records"],
            "reliable_records": stats["reliable_records"],
            "reliability_percentage": (stats["reliable_records"] / stats["total_prevalence_records"] * 100) if stats["total_prevalence_records"] > 0 else 0,
            "validated_records": stats["validation_status_distribution"].get("Validated", 0)
        },
        "geographic_distribution": dict(stats["geographic_distribution"]),
        "validation_status_distribution": dict(stats["validation_status_distribution"]),
        "prevalence_type_distribution": dict(stats["prevalence_type_distribution"]),
        "prevalence_class_distribution": dict(stats["prevalence_class_distribution"]),
        "estimate_source_distribution": dict(stats["estimate_source_distribution"])
    }
    
    with open(reliability_dir / "validation_report.json", 'w', encoding='utf-8') as f:
        json.dump(validation_report, f, indent=2, ensure_ascii=False)
    
    # Save cache files
    with open(cache_dir / "statistics.json", 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    # Prevalence classes mapping
    prevalence_classes = {}
    for record in prevalence_instances.values():
        if record["prevalence_class"]:
            prevalence_classes[record["prevalence_class"]] = standardize_prevalence_class(record["prevalence_class"])
    
    with open(cache_dir / "prevalence_classes.json", 'w', encoding='utf-8') as f:
        json.dump(prevalence_classes, f, indent=2, ensure_ascii=False)
    
    # Geographic index
    geographic_index = {
        region: {
            "diseases": list(set(r["orpha_code"] for r in records)),
            "total_records": len(records)
        }
        for region, records in regional_data.items()
    }
    
    with open(cache_dir / "geographic_index.json", 'w', encoding='utf-8') as f:
        json.dump(geographic_index, f, indent=2, ensure_ascii=False)
    
    return stats


def validate_outputs(output_dir):
    """Validate that all required prevalence output files were generated"""
    output_path = Path(output_dir)
    
    required_files = [
        output_path / "disease2prevalence.json",
        output_path / "prevalence2diseases.json",
        output_path / "prevalence_instances.json",
        output_path / "orpha_index.json",
        output_path / "regional_data" / "regional_summary.json",
        output_path / "reliability" / "reliable_prevalences.json",
        output_path / "reliability" / "reliability_scores.json",
        output_path / "reliability" / "validation_report.json",
        output_path / "cache" / "statistics.json",
        output_path / "cache" / "prevalence_classes.json",
        output_path / "cache" / "geographic_index.json"
    ]
    
    all_valid = True
    for file_path in required_files:
        if not file_path.exists():
            logger.error(f"Required file missing: {file_path}")
            all_valid = False
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                logger.info(f"✓ Valid: {file_path.relative_to(output_path)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in {file_path}: {e}")
                all_valid = False
    
    return all_valid


def generate_statistics(output_dir):
    """Generate comprehensive statistics about prevalence processing"""
    output_path = Path(output_dir)
    
    # Load statistics from cache
    stats_path = output_path / "cache" / "statistics.json"
    if stats_path.exists():
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
    else:
        stats = {}
    
    # Add file sizes
    file_sizes = {}
    for file_path in output_path.rglob("*.json"):
        size_mb = file_path.stat().st_size / (1024 * 1024)
        file_sizes[str(file_path.relative_to(output_path))] = f"{size_mb:.2f} MB"
    
    stats["file_sizes"] = file_sizes
    
    # Calculate total size
    total_size_mb = sum(
        file_path.stat().st_size / (1024 * 1024)
        for file_path in output_path.rglob("*.json")
    )
    stats["total_size_mb"] = f"{total_size_mb:.2f} MB"
    
    return stats


def print_summary(stats):
    """Print human-readable summary of prevalence processing"""
    print("\n" + "="*60)
    print("PREVALENCE PROCESSING SUMMARY")
    print("="*60)
    
    print(f"\nTotal disorders: {stats.get('total_disorders', 'N/A')}")
    print(f"Disorders with prevalence: {stats.get('disorders_with_prevalence', 'N/A')}")
    print(f"Total prevalence records: {stats.get('total_prevalence_records', 'N/A')}")
    print(f"Reliable records (≥6.0 score): {stats.get('reliable_records', 'N/A')}")
    
    if stats.get('total_prevalence_records', 0) > 0:
        reliability_pct = (stats.get('reliable_records', 0) / stats.get('total_prevalence_records', 1)) * 100
        print(f"Reliability percentage: {reliability_pct:.1f}%")
    
    if 'geographic_distribution' in stats:
        print("\nGeographic distribution:")
        for region, count in sorted(stats['geographic_distribution'].items()):
            print(f"  {region}: {count} records")
    
    if 'validation_status_distribution' in stats:
        print("\nValidation status:")
        for status, count in sorted(stats['validation_status_distribution'].items()):
            print(f"  {status}: {count} records")
    
    if 'file_sizes' in stats:
        print("\nGenerated files:")
        for file_path, size in sorted(stats['file_sizes'].items()):
            print(f"  {file_path}: {size}")
    
    print(f"\nTotal size: {stats.get('total_size_mb', 'N/A')}")
    print("="*60)


def main():
    """Main function to orchestrate prevalence preprocessing"""
    parser = argparse.ArgumentParser(
        description="Process Orphanet prevalence data (en_product9_prev.xml)"
    )
    parser.add_argument(
        "--xml",
        default="data/01_raw/en_product9_prev.xml",
        help="Path to the input XML file (default: data/01_raw/en_product9_prev.xml)"
    )
    parser.add_argument(
        "--output",
        default="data/03_processed/orpha/orphadata/orpha_prevalence",
        help="Output directory for processed files (default: data/03_processed/orpha/orphadata/orpha_prevalence)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing output files"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing output files without processing"
    )
    
    args = parser.parse_args()
    
    xml_path = Path(args.xml)
    output_dir = Path(args.output)
    
    # Validate only mode
    if args.validate_only:
        logger.info("Running in validation-only mode")
        if validate_outputs(str(output_dir)):
            logger.info("✓ All output files are valid")
            stats = generate_statistics(str(output_dir))
            print_summary(stats)
            return 0
        else:
            logger.error("✗ Validation failed")
            return 1
    
    # Check if XML file exists
    if not xml_path.exists():
        logger.error(f"XML file not found: {xml_path}")
        return 1
    
    # Check if output already exists
    if output_dir.exists() and any(output_dir.iterdir()) and not args.force:
        logger.warning(f"Output directory {output_dir} already contains files")
        response = input("Do you want to overwrite? (y/N): ")
        if response.lower() != 'y':
            logger.info("Aborted by user")
            return 0
    
    try:
        start_time = datetime.now()
        logger.info(f"Starting prevalence preprocessing")
        logger.info(f"Input XML: {xml_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Process XML
        stats = process_prevalence_xml(str(xml_path), str(output_dir))
        
        # Validate outputs
        if not validate_outputs(str(output_dir)):
            logger.error("Output validation failed")
            return 1
        
        # Generate and display statistics
        stats = generate_statistics(str(output_dir))
        print_summary(stats)
        
        # Calculate processing time
        duration = datetime.now() - start_time
        logger.info(f"✓ Processing completed successfully in {duration.total_seconds():.1f} seconds")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 