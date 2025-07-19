"""
Example usage of the configurable WebResponses class.
"""

from openai_responses import WebResponses

# Example 1: Using default configuration
def example_default_usage():
    """Example using default configuration."""
    client = WebResponses()
    
    # Simple chat
    response_text = client.chat("Hello, how are you?")
    print(f"Chat response: {response_text}")
    
    # Get structured response
    response = client.generate("What is machine learning?")
    print(f"Total tokens: {response.total_tokens}")
    print(f"Output: {response.output}")


# Example 2: Custom configuration during initialization
def example_custom_config():
    """Example with custom configuration."""
    client = WebResponses(
        model="o4-mini",
        reasoning={"effort": "high"},
        tools=[{"type": "web_search_preview"}],
        max_output_tokens=10000,
        temperature=0.7,  # Additional parameter
        top_p=0.9        # Additional parameter
    )
    
    response = client.generate("Explain quantum computing")
    print(f"Custom config response: {response.output}")


# Example 3: Updating configuration after initialization
def example_dynamic_config():
    """Example showing dynamic configuration updates."""
    client = WebResponses()
    
    # Update default configuration permanently
    client.configure(
        reasoning={"effort": "low"},
        max_output_tokens=5000,
        temperature=0.3
    )
    
    response = client.generate("What is AI?")
    print(f"Dynamic config response: {response.output}")


# Example 4: Override parameters per request
def example_per_request_override():
    """Example showing per-request parameter overrides."""
    client = WebResponses()
    
    # Override specific parameters for this request only
    response = client.generate(
        "Explain neural networks",
        reasoning={"effort": "high"},
        max_output_tokens=15000,
        tools=[]  # No tools for this request
    )
    print(f"Override response: {response.output}")


if __name__ == "__main__":
    # Uncomment to test (requires valid API key)
    # example_default_usage()
    # example_custom_config()
    # example_dynamic_config()
    # example_per_request_override()
    
    print("Example usage file created. Uncomment function calls to test with valid API key.") 