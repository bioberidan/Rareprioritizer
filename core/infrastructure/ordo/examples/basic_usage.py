#!/usr/bin/env python3
"""
Basic Usage Examples for Orpha Disease Preprocessing System

This file contains working examples demonstrating the main functionality
of the Orpha Disease Preprocessing System.

Requirements:
- Processed data in data/processed/ directory
- Run: python tools/disease_preprocessing.py path/to/xml data/processed/

Usage:
    python utils/orpha/examples/basic_usage.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.orpha import OrphaTaxonomy
from utils.orpha.exceptions import NodeNotFoundError, AmbiguousNameError


def check_data_availability():
    """Check if processed data is available"""
    data_dir = project_root / "data" / "processed"
    if not data_dir.exists():
        print("❌ Processed data not found!")
        print(f"Expected directory: {data_dir}")
        print("\nTo create processed data:")
        print("1. Place your Orphanet XML file in data/input/")
        print("2. Run: python tools/disease_preprocessing.py data/input/your_file.xml data/processed/")
        return False
    
    # Check for required subdirectories
    required_dirs = ["taxonomy", "instances", "cache"]
    for dir_name in required_dirs:
        if not (data_dir / dir_name).exists():
            print(f"❌ Missing directory: {data_dir / dir_name}")
            return False
    
    print(f"✅ Processed data found at: {data_dir}")
    return True


def example_1_initialization():
    """Example 1: Basic initialization and system information"""
    print("\n" + "="*50)
    print("EXAMPLE 1: INITIALIZATION AND SYSTEM INFO")
    print("="*50)
    
    try:
        # Initialize the taxonomy system
        print("Initializing Orpha taxonomy system...")
        taxonomy = OrphaTaxonomy()
        print("✅ Initialization successful!")
        
        # Get system statistics
        stats = taxonomy.get_statistics()
        print(f"\n📊 System Statistics:")
        print(f"  - Total categories: {stats['combined']['total_categories']}")
        print(f"  - Total diseases: {stats['combined']['total_diseases']}")
        print(f"  - Total nodes: {stats['combined']['total_nodes']}")
        print(f"  - Max taxonomy depth: {stats['taxonomy']['max_depth']}")
        
        # Show memory usage
        print(f"\n💾 Memory Usage:")
        print(f"  - Loaded diseases: {stats['diseases']['loaded_count']}")
        print(f"  - Cache hit rate: {stats['diseases'].get('cache_hit_rate', 'N/A')}")
        
        return taxonomy
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return None


def example_2_basic_navigation(taxonomy):
    """Example 2: Basic navigation by ID and name"""
    print("\n" + "="*50)
    print("EXAMPLE 2: BASIC NAVIGATION")
    print("="*50)
    
    # Get node by ID (assuming we have some standard IDs)
    try:
        # Try to get the root or first available category
        all_categories = taxonomy.taxonomy.get_all_categories()
        if all_categories:
            category = all_categories[0]
            print(f"📂 Category by ID: {category.name} (ID: {category.id})")
            
            # Get parent
            parent = taxonomy.get_parent(category.id)
            if parent:
                print(f"  ⬆️  Parent: {parent.name}")
            else:
                print("  ⬆️  No parent (root node)")
            
            # Get children
            children = taxonomy.get_children(category.id)
            print(f"  ⬇️  Children: {len(children)} nodes")
            
            # Show first few children
            for i, child in enumerate(children[:3]):
                node_type = "📂" if hasattr(child, 'children') else "🏥"
                print(f"    {node_type} {child.name}")
            
            if len(children) > 3:
                print(f"    ... and {len(children) - 3} more")
    
    except Exception as e:
        print(f"❌ Navigation by ID failed: {e}")


def example_3_search_operations(taxonomy):
    """Example 3: Search operations"""
    print("\n" + "="*50)
    print("EXAMPLE 3: SEARCH OPERATIONS")
    print("="*50)
    
    # Search for nodes with common terms
    search_terms = ["metabolic", "disease", "disorder"]
    
    for term in search_terms:
        try:
            print(f"\n🔍 Searching for '{term}':")
            results = taxonomy.search_by_name(term)
            
            if results:
                print(f"  Found {len(results)} matches")
                # Show first few results
                for i, (node_id, name) in enumerate(results[:5]):
                    node_type = taxonomy.get_node_type(node_id)
                    icon = "📂" if node_type == "category" else "🏥"
                    print(f"    {icon} {name} (ID: {node_id})")
                
                if len(results) > 5:
                    print(f"    ... and {len(results) - 5} more")
            else:
                print(f"  No matches found for '{term}'")
                
        except Exception as e:
            print(f"❌ Search failed for '{term}': {e}")


def example_4_disease_operations(taxonomy):
    """Example 4: Disease-specific operations"""
    print("\n" + "="*50)
    print("EXAMPLE 4: DISEASE OPERATIONS")
    print("="*50)
    
    # Try to find diseases in different ways
    try:
        # Search for diseases specifically
        disease_results = taxonomy.search_by_name("syndrome", node_type="disease")
        
        if disease_results:
            print(f"🏥 Found {len(disease_results)} diseases with 'syndrome'")
            
            # Get the first disease and explore it
            disease_id, disease_name = disease_results[0]
            disease = taxonomy.get_node(disease_id)
            
            print(f"\n📋 Disease Details:")
            print(f"  Name: {disease.name}")
            print(f"  ID: {disease.id}")
            
            # Get parent category
            parent = taxonomy.get_parent(disease_id)
            if parent:
                print(f"  Category: {parent.name}")
                
                # Get path to root
                path = taxonomy.get_path_to_root(disease_id)
                path_names = [node.name for node in path]
                print(f"  Path: {' -> '.join(path_names)}")
            
            # Show classification info if available
            if hasattr(disease, 'classification'):
                print(f"  Classification: {disease.classification}")
        
        else:
            print("🔍 No diseases found with 'syndrome' in name")
            
            # Try with other terms
            for term in ["disorder", "deficiency", "malformation"]:
                results = taxonomy.search_by_name(term, node_type="disease")
                if results:
                    print(f"  Found {len(results)} diseases with '{term}'")
                    break
    
    except Exception as e:
        print(f"❌ Disease operations failed: {e}")


def example_5_category_analysis(taxonomy):
    """Example 5: Category analysis and statistics"""
    print("\n" + "="*50)
    print("EXAMPLE 5: CATEGORY ANALYSIS")
    print("="*50)
    
    # Get some categories to analyze
    all_categories = taxonomy.taxonomy.get_all_categories()
    
    if all_categories:
        print(f"📊 Analyzing {len(all_categories)} categories:")
        
        # Find categories with diseases
        categories_with_diseases = []
        for category in all_categories[:10]:  # Check first 10
            try:
                disease_count = taxonomy.count_diseases_in_subtree(category.id)
                if disease_count > 0:
                    categories_with_diseases.append((category, disease_count))
            except Exception:
                continue
        
        # Sort by disease count
        categories_with_diseases.sort(key=lambda x: x[1], reverse=True)
        
        print(f"\n🏆 Top categories by disease count:")
        for i, (category, count) in enumerate(categories_with_diseases[:5]):
            print(f"  {i+1}. {category.name}: {count} diseases")
            
            # Get some diseases from this category
            try:
                diseases = taxonomy.diseases.get_diseases_in_category(category.id)
                if diseases:
                    print(f"     Examples: {', '.join([d.name for d in diseases[:3]])}")
                    if len(diseases) > 3:
                        print(f"     ... and {len(diseases) - 3} more")
            except Exception:
                pass
    
    else:
        print("❌ No categories found")


def example_6_error_handling(taxonomy):
    """Example 6: Error handling and validation"""
    print("\n" + "="*50)
    print("EXAMPLE 6: ERROR HANDLING")
    print("="*50)
    
    # Test various error scenarios
    print("🧪 Testing error handling:")
    
    # Test 1: Non-existent node
    try:
        taxonomy.get_node("NONEXISTENT")
        print("❌ Should have raised NodeNotFoundError")
    except NodeNotFoundError:
        print("✅ NodeNotFoundError handled correctly")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    
    # Test 2: Ambiguous name (if any exist)
    try:
        # Try some common names that might be ambiguous
        common_names = ["Disease", "Disorder", "Syndrome"]
        for name in common_names:
            try:
                node = taxonomy.get_node_by_name(name)
                print(f"✅ Found unique match for '{name}': {node.name}")
                break
            except AmbiguousNameError as e:
                print(f"⚠️  Ambiguous name '{name}': {len(e.candidate_ids)} candidates")
                
                # Show how to resolve
                diseases = taxonomy.resolve_name(name, node_type="disease")
                categories = taxonomy.resolve_name(name, node_type="category")
                print(f"    - {len(diseases)} diseases, {len(categories)} categories")
                break
            except NodeNotFoundError:
                continue
    
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    # Test 3: System validation
    try:
        print("\n🔍 Running system validation...")
        validation_result = taxonomy.validate()
        
        if validation_result.is_valid:
            print("✅ System validation passed")
        else:
            print(f"⚠️  System validation found {len(validation_result.issues)} issues")
            for issue in validation_result.issues[:3]:
                print(f"    - {issue}")
        
        if validation_result.warnings:
            print(f"⚠️  {len(validation_result.warnings)} warnings:")
            for warning in validation_result.warnings[:3]:
                print(f"    - {warning}")
    
    except Exception as e:
        print(f"❌ Validation failed: {e}")


def example_7_batch_operations(taxonomy):
    """Example 7: Batch operations and performance"""
    print("\n" + "="*50)
    print("EXAMPLE 7: BATCH OPERATIONS")
    print("="*50)
    
    import time
    
    # Get some categories for batch processing
    all_categories = taxonomy.taxonomy.get_all_categories()
    
    if len(all_categories) > 0:
        # Test batch disease counting
        print("⚡ Testing batch operations:")
        
        # Time multiple individual operations
        start_time = time.time()
        individual_counts = []
        
        for category in all_categories[:5]:
            count = taxonomy.count_diseases_in_subtree(category.id)
            individual_counts.append((category.name, count))
        
        individual_time = time.time() - start_time
        
        print(f"  Individual operations (5 categories): {individual_time:.3f}s")
        for name, count in individual_counts:
            print(f"    - {name}: {count} diseases")
        
        # Show memory usage after operations
        stats = taxonomy.get_statistics()
        print(f"  Loaded diseases after operations: {stats['diseases']['loaded_count']}")
    
    else:
        print("❌ No categories available for batch testing")


def main():
    """Main function to run all examples"""
    print("🚀 Orpha Disease Preprocessing System - Basic Usage Examples")
    print("=" * 70)
    
    # Check data availability
    if not check_data_availability():
        print("\n❌ Cannot run examples without processed data")
        print("Please follow the installation instructions in the README.md")
        return
    
    # Initialize the system
    taxonomy = example_1_initialization()
    if not taxonomy:
        return
    
    # Run examples
    example_2_basic_navigation(taxonomy)
    example_3_search_operations(taxonomy)
    example_4_disease_operations(taxonomy)
    example_5_category_analysis(taxonomy)
    example_6_error_handling(taxonomy)
    example_7_batch_operations(taxonomy)
    
    print("\n" + "="*70)
    print("✅ All examples completed successfully!")
    print("📚 For more advanced examples, see the cookbooks:")
    print("   - cookbooks/orpha/01_getting_started/")
    print("   - cookbooks/orpha/02_navigation/")
    print("   - cookbooks/orpha/03_data_analysis/")
    print("="*70)


if __name__ == "__main__":
    main() 