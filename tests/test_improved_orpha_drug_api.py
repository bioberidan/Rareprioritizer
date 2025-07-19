#!/usr/bin/env python3
"""
Test script for the improved OrphaDrugAPIClient

This script tests the updated parsing logic with the simplified schema
and verifies it can distinguish between specific and non-specific drugs,
as well as correctly detect regional availability (EU/US).

Tests diseases:
- ORPHA:584 (Mucopolysaccharidosis type 7) - Expected: 3 specific + 10 non-specific = 13 total
- ORPHA:1168 (Ataxia-oculomotor apraxia type 1) - Expected: 1 specific + 1 non-specific = 2 total
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.infrastructure.orpha_drug.orpha_drug import OrphaDrugAPIClient

def test_orpha_drug_api():
    """Test the improved OrphaDrugAPIClient with both test cases"""
    
    print("="*80)
    print("TESTING IMPROVED ORPHA DRUG API CLIENT")
    print("="*80)
    
    client = OrphaDrugAPIClient(delay=1.0)
    
    # Test cases with expected results
    test_cases = [
        {
            'disease_name': 'Mucopolysaccharidosis type 7',
            'orpha_code': '584',
            'expected_total': 11,
            'expected_specific': 2,
            'expected_non_specific': 9,
            'description': 'Should have 2 specific drugs and 9 non-specific drugs (after deduplication of regional duplicates)'
        },
        {
            'disease_name': 'Ataxia-oculomotor apraxia type 1', 
            'orpha_code': '1168',
            'expected_total': 2,
            'expected_specific': 1,
            'expected_non_specific': 1,
            'description': 'Should have 1 specific drug and 1 non-specific drug'
        }
    ]
    
    results_summary = {
        'test_timestamp': datetime.now().isoformat(),
        'test_results': [],
        'all_tests_passed': True
    }
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'-'*60}")
        print(f"TEST {i}: {test_case['disease_name']} (ORPHA:{test_case['orpha_code']})")
        print(f"Description: {test_case['description']}")
        print(f"{'-'*60}")
        
        try:
            # Execute the search
            print(f"Searching for drugs for {test_case['disease_name']}...")
            result = client.search(
                disease_name=test_case['disease_name'],
                orphacode=test_case['orpha_code']
            )
            
            # Check for errors
            if 'error' in result:
                print(f"❌ ERROR: {result['error']}")
                test_result = {
                    'orpha_code': test_case['orpha_code'],
                    'disease_name': test_case['disease_name'],
                    'status': 'FAILED',
                    'error': result['error']
                }
                results_summary['test_results'].append(test_result)
                results_summary['all_tests_passed'] = False
                continue
            
            # Extract drugs
            drugs = result.get('drugs', [])
            total_drugs = len(drugs)
            
            # Count specific vs non-specific drugs
            specific_drugs = [d for d in drugs if d.get('is_specific', False)]
            non_specific_drugs = [d for d in drugs if not d.get('is_specific', False)]
            
            # Count regional availability
            eu_drugs = [d for d in drugs if d.get('is_available_in_eu', False)]
            us_drugs = [d for d in drugs if d.get('is_available_in_us', False)]
            
            # Count drug types
            tradename_drugs = [d for d in drugs if d.get('is_tradename', False)]
            medical_product_drugs = [d for d in drugs if d.get('is_medical_product', False)]
            
            # Print results
            print(f"✅ Search completed successfully!")
            print(f"📊 RESULTS SUMMARY:")
            print(f"   Total drugs found: {total_drugs}")
            print(f"   Specific drugs: {len(specific_drugs)}")
            print(f"   Non-specific drugs: {len(non_specific_drugs)}")
            print(f"   EU available: {len(eu_drugs)}")
            print(f"   US available: {len(us_drugs)}")
            print(f"   Trade names: {len(tradename_drugs)}")
            print(f"   Medical products: {len(medical_product_drugs)}")
            
            # Validate expectations
            validation_passed = True
            validation_errors = []
            
            if total_drugs != test_case['expected_total']:
                validation_errors.append(f"Expected {test_case['expected_total']} total drugs, got {total_drugs}")
                validation_passed = False
                
            if len(specific_drugs) != test_case['expected_specific']:
                validation_errors.append(f"Expected {test_case['expected_specific']} specific drugs, got {len(specific_drugs)}")
                validation_passed = False
                
            if len(non_specific_drugs) != test_case['expected_non_specific']:
                validation_errors.append(f"Expected {test_case['expected_non_specific']} non-specific drugs, got {len(non_specific_drugs)}")
                validation_passed = False
            
            if validation_passed:
                print("✅ VALIDATION PASSED: All counts match expectations!")
            else:
                print("❌ VALIDATION FAILED:")
                for error in validation_errors:
                    print(f"   - {error}")
                results_summary['all_tests_passed'] = False
            
            # Show sample drugs
            print(f"\n📋 SAMPLE DRUGS (showing first 3):")
            for j, drug in enumerate(drugs[:3], 1):
                print(f"   {j}. {drug.get('name', 'Unknown')}")
                print(f"      - Specific: {drug.get('is_specific', False)}")
                print(f"      - EU: {drug.get('is_available_in_eu', False)}")
                print(f"      - US: {drug.get('is_available_in_us', False)}")
                print(f"      - Trade name: {drug.get('is_tradename', False)}")
                print(f"      - Medical product: {drug.get('is_medical_product', False)}")
                if drug.get('substance_url'):
                    print(f"      - Substance URL: {drug.get('substance_url')}")
                if drug.get('regulatory_url'):
                    print(f"      - Regulatory URL: {drug.get('regulatory_url')}")
                print()
            
            # Save detailed results to JSON file
            output_filename = f"tests/orpha_{test_case['orpha_code']}_improved_results.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Detailed results saved to: {output_filename}")
            
            # Create test result summary
            test_result = {
                'orpha_code': test_case['orpha_code'],
                'disease_name': test_case['disease_name'],
                'status': 'PASSED' if validation_passed else 'FAILED',
                'total_drugs': total_drugs,
                'specific_drugs': len(specific_drugs),
                'non_specific_drugs': len(non_specific_drugs),
                'eu_drugs': len(eu_drugs),
                'us_drugs': len(us_drugs),
                'tradename_drugs': len(tradename_drugs),
                'medical_product_drugs': len(medical_product_drugs),
                'validation_errors': validation_errors if not validation_passed else [],
                'output_file': output_filename
            }
            results_summary['test_results'].append(test_result)
            
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            test_result = {
                'orpha_code': test_case['orpha_code'],
                'disease_name': test_case['disease_name'],
                'status': 'ERROR',
                'exception': str(e)
            }
            results_summary['test_results'].append(test_result)
            results_summary['all_tests_passed'] = False
    
    # Save overall test summary
    summary_filename = "tests/orpha_drug_api_test_summary.json"
    with open(summary_filename, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print(f"\n{'='*80}")
    print("FINAL TEST SUMMARY")
    print(f"{'='*80}")
    
    total_tests = len(test_cases)
    passed_tests = sum(1 for t in results_summary['test_results'] if t['status'] == 'PASSED')
    failed_tests = sum(1 for t in results_summary['test_results'] if t['status'] in ['FAILED', 'ERROR'])
    
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    if results_summary['all_tests_passed']:
        print("🎉 ALL TESTS PASSED! The improved API is working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED. Check the detailed results above.")
    
    print(f"\n📁 Files generated:")
    for test_result in results_summary['test_results']:
        if 'output_file' in test_result:
            print(f"   - {test_result['output_file']}")
    print(f"   - {summary_filename}")
    
    return results_summary

def analyze_schema_differences():
    """Analyze differences between old and new schemas"""
    print(f"\n{'='*80}")
    print("SCHEMA COMPARISON ANALYSIS")
    print(f"{'='*80}")
    
    # Load the example schemas for comparison
    try:
        # Load old wrong schema
        with open('data/02_preprocess/orpha/orphadata/orpha_drugs/example_wrong_json_drug.json', 'r') as f:
            old_schema = json.load(f)
        
        # Load good schema
        with open('data/02_preprocess/orpha/orphadata/orpha_drugs/example_good_json_drug.json', 'r') as f:
            good_schema = json.load(f)
        
        print("📋 OLD SCHEMA FIELDS (from example_wrong_json_drug.json):")
        if old_schema.get('drugs'):
            old_drug = old_schema['drugs'][0]
            for key, value in old_drug.items():
                print(f"   - {key}: {type(value).__name__}")
        
        print("\n📋 NEW IMPROVED SCHEMA FIELDS (from example_good_json_drug.json):")
        if good_schema.get('drugs'):
            good_drug = good_schema['drugs'][0]
            for key, value in good_drug.items():
                print(f"   - {key}: {type(value).__name__}")
        
        print("\n🔄 KEY IMPROVEMENTS:")
        print("   ✅ Simplified boolean flags instead of complex nested structures")
        print("   ✅ Clear is_specific field to distinguish drug types")
        print("   ✅ Regional availability detection (is_available_in_eu/us)")
        print("   ✅ Proper handling of trade_name vs substance URLs")
        print("   ✅ Removed unnecessary fields like 'details', 'links', 'orpha_substance_code'")
        
    except Exception as e:
        print(f"⚠️  Could not load schema files for comparison: {e}")

if __name__ == "__main__":
    print("Starting Orpha Drug API Test Suite...")
    
    # Run the main tests
    results = test_orpha_drug_api()
    
    # Analyze schema differences
    analyze_schema_differences()
    
    # Exit with appropriate code
    if results['all_tests_passed']:
        print(f"\n🎉 SUCCESS: All tests passed! The improved API is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ FAILURE: Some tests failed. Please check the output above.")
        sys.exit(1) 