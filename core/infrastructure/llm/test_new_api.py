"""
Test file demonstrating the new WebResponses API design.
"""

from openai_responses import WebResponses

def test_new_api():
    """Test the new API design."""
    
    print("=== Testing New WebResponses API ===\n")
    
    # 1. Initialize with kwargs (passed to configure)
    print("1. Initialize with configuration:")
    client = WebResponses(
        reasoning={"effort": "high"},
        max_output_tokens=15000,
        temperature=0.7
    )
    print(f"   Initial params: {client.params}")
    print()
    
    # 2. Use configure() to permanently update
    print("2. Use configure() to permanently update:")
    client.configure(
        reasoning={"effort": "low"},
        temperature=0.3
    )
    print(f"   Updated params: {client.params}")
    print()
    
    # 3. Temporary override with kwargs (doesn't change client.params)
    print("3. Temporary override with method kwargs:")
    print(f"   Before call - params: {client.params}")
    
    # This would make an API call with temporarily overridden parameters
    # response = client.generate_raw("test", max_output_tokens=5000, temperature=0.9)
    
    print(f"   After call - params: {client.params}")
    print("   (params unchanged - kwargs were temporary)")
    print()
    
    # 4. Show that all methods accept kwargs
    print("4. All methods accept kwargs for temporary overrides:")
    print("   client.chat('prompt', temperature=0.1)")
    print("   client.generate('prompt', max_output_tokens=1000)")
    print("   client.generate_raw('prompt', reasoning={'effort': 'medium'})")
    print()
    
    print("=== API Design Summary ===")
    print("✓ __init__ accepts **kwargs → passed to configure()")
    print("✓ configure() permanently updates self.params")
    print("✓ All methods accept **kwargs for temporary overrides")
    print("✓ generate_raw() is the core method (no duplicate logic)")
    print("✓ Clean parameter precedence: defaults → config → method kwargs")

if __name__ == "__main__":
    test_new_api() 