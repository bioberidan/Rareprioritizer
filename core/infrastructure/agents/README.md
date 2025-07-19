# Carlos III Agents Package

Intelligent agents for automating research prioritization tasks in the Carlos III rare disease system.

## Overview

The `agents` package provides high-level, stateful interfaces for complex research workflows. These agents encapsulate common patterns and provide reusable, configurable components for LLM-powered analysis.

## Available Agents

### WebSearcher

A stateful prompt-based LLM search interface that maintains prompt and client configuration for efficient repeated searches.

## WebSearcher Agent

### Purpose

WebSearcher eliminates the repetitive boilerplate of:
1. Loading prompts from registry
2. Configuring LLM clients  
3. Formatting templates
4. Making API calls
5. Handling structured responses

Instead, you configure once and search many times.

### Quick Start

```python
from agents import WebSearcher

# Initialize with prompt and client configuration
searcher = WebSearcher(
    prompt_alias="socioeconomic_v1",
    client_kwargs={"reasoning": {"effort": "low"}, "max_output_tokens": 5000}
)

# Use repeatedly with different data
wilson_result = searcher.search({
    "disease_name": "Wilson disease", 
    "orphacode": "905"
})

huntington_result = searcher.search({
    "disease_name": "Huntington disease", 
    "orphacode": "399"
})
```

### Key Features

- **🔄 Stateful Design**: Configure once, use many times
- **⚡ Performance**: No repeated configuration overhead
- **🎯 Consistency**: Same prompt/client across searches
- **🛠️ Maintainability**: Clean, simple interface
- **📊 Observability**: Built-in monitoring and debugging

### Architecture

```mermaid
graph TD
    A[WebSearcher.__init__] --> B[Load Prompt from Registry]
    A --> C[Configure WebResponses Client]
    B --> D[Store Template & Model]
    C --> E[Store Client Configuration]
    
    F[searcher.search()] --> G[Format Template with Data]
    G --> H[Use Stored Client]
    H --> I[Return Parsed Response]
    
    D --> G
    E --> H
```

### API Reference

#### `WebSearcher(prompt_alias, client_kwargs=None)`

Initialize a new WebSearcher instance.

**Parameters:**
- `prompt_alias` (str): Registered prompt identifier from the prompt registry
- `client_kwargs` (dict, optional): Configuration for the WebResponses client

**Example:**
```python
searcher = WebSearcher(
    prompt_alias="groups_v1",
    client_kwargs={
        "reasoning": {"effort": "medium"},
        "max_output_tokens": 8000
    }
)
```

#### `search(template_kwargs)`

Execute search using stored configuration and new template data.

**Parameters:**
- `template_kwargs` (dict): Data for template formatting

**Returns:**
- Parsed response object (type depends on prompt's Pydantic model)

**Example:**
```python
response = searcher.search({
    "disease_name": "Wilson disease",
    "orphacode": "905"
})
```

#### `get_info()`

Get information about the searcher's current configuration.

**Returns:**
- `dict`: Configuration details including prompt info and client settings

**Example:**
```python
info = searcher.get_info()
print(f"Using prompt: {info['prompt_alias']}")
print(f"Template length: {info['prompt_template_length']} chars")
print(f"Model: {info['prompt_model']}")
```

#### `refresh_prompt()`

Refresh prompt configuration from the registry.

**Use case:** When prompts have been updated in the registry after initialization.

**Example:**
```python
# Prompts updated in registry...
searcher.refresh_prompt()  # Reload latest version
```

### Advanced Usage

#### Multiple Disease Analysis

```python
# Analyze multiple diseases efficiently
searcher = WebSearcher("socioeconomic_v1", {"max_output_tokens": 5000})

diseases = [
    {"disease_name": "Wilson disease", "orphacode": "905"},
    {"disease_name": "Huntington disease", "orphacode": "399"},
    {"disease_name": "Fabry disease", "orphacode": "324"}
]

results = []
for disease_data in diseases:
    result = searcher.search(disease_data)
    results.append({
        "disease": disease_data["disease_name"],
        "score": result.score,
        "evidence": result.evidence_level
    })
```

#### Error Handling

```python
from utils.prompts.exceptions import PromptNotFoundError

try:
    searcher = WebSearcher("invalid_prompt", client_kwargs)
except PromptNotFoundError as e:
    print(f"Prompt not found: {e}")
    print(f"Available prompts: {e.available_prompts}")

try:
    result = searcher.search({"missing_field": "value"})
except KeyError as e:
    print(f"Missing template field: {e}")
```

#### Configuration Validation

```python
# Check searcher configuration
info = searcher.get_info()
print(f"Prompt: {info['prompt_alias']}")
print(f"Template size: {info['prompt_template_length']} chars")
print(f"Has client config: {info['has_configured_client']}")
```

### Performance Considerations

#### Memory Usage
Each WebSearcher instance stores:
- Prompt template (typically 1-5KB)
- Pydantic model metadata 
- Configured WebResponses client
- Prompter instance

**Recommendation:** Create searchers for frequently-used prompts, not one-off searches.

#### Client Reuse
WebSearcher reuses the configured client across searches:
- ✅ **Benefit**: No repeated configuration overhead
- ⚠️ **Consideration**: Shared state between searches
- 🔒 **Thread Safety**: Not guaranteed - use separate instances per thread

### Integration Examples

#### With Existing Code

**Before (Manual Pattern):**
```python
# 15+ lines of boilerplate
prompter = Prompter()
prompt = prompter.get_prompt("socioeconomic_v1")
template = prompt.template
model = prompt.model
client = WebResponses()
client.configure(**client_kwargs)
formatted = template.format(**template_kwargs)
response = client.chat(formatted, text_format=model)
```

**After (WebSearcher):**
```python
# 3 lines
searcher = WebSearcher("socioeconomic_v1", client_kwargs)
response = searcher.search(template_kwargs)
```

#### Batch Processing

```python
def analyze_disease_list(diseases, prompt_alias="socioeconomic_v1"):
    """Analyze multiple diseases with the same prompt."""
    searcher = WebSearcher(prompt_alias, {"max_output_tokens": 5000})
    
    results = []
    for disease in diseases:
        try:
            result = searcher.search(disease)
            results.append(result)
        except Exception as e:
            print(f"Error analyzing {disease['disease_name']}: {e}")
            
    return results
```

### Best Practices

1. **Initialization Strategy**
   - Create searchers for frequently-used prompts
   - Use appropriate client configuration for your use case
   - Consider memory usage with many searcher instances

2. **Error Handling**
   - Validate prompt aliases exist before creating searchers
   - Handle template formatting errors gracefully
   - Implement retry logic for API failures

3. **Monitoring**
   - Use `get_info()` for debugging and logging
   - Monitor memory usage with many instances
   - Track API usage and response times

4. **Thread Safety**
   - Use separate searcher instances per thread
   - Don't share searchers across concurrent operations
   - Consider client state consistency

### Troubleshooting

#### Common Issues

**ImportError: No module named 'agents'**
```python
# Solution: Add parent directory to Python path
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**PromptNotFoundError**
```python
# Check available prompts
from utils.prompts import Prompter
prompter = Prompter()
print("Available prompts:", prompter.list_prompts())
```

**KeyError in template formatting**
```python
# Check template placeholders
searcher = WebSearcher("socioeconomic_v1")
info = searcher.get_info()
print(f"Template: {searcher.prompt_template}")
# Ensure your template_kwargs match the placeholders
```

**BadRequestError from OpenAI**
```python
# Check client configuration compatibility
# Remove unsupported parameters like 'temperature' for o4-mini
client_kwargs = {
    "reasoning": {"effort": "low"},
    "max_output_tokens": 5000
    # Remove: "temperature": 0.3  # Not supported by o4-mini
}
```

### Changelog

#### v1.0.0 (Current)
- Initial WebSearcher implementation
- Stateful prompt and client configuration
- Built-in debugging and monitoring
- Integration with Carlos III prompt system
- Support for all registered prompts

### Contributing

When extending WebSearcher:

1. **Maintain State Management**: Preserve the stateful design pattern
2. **Template Compatibility**: Use original `template.format()` approach
3. **Error Handling**: Provide clear error messages and context
4. **Documentation**: Update this README with new features
5. **Testing**: Verify with multiple prompt types and data sets

### License

Part of the Carlos III research prioritization system. 