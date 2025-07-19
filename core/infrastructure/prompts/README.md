# Prompt Architecture System

A modular, extensible prompt architecture for the Carlos III Research Prioritization system that enables clean separation of concerns, automatic registration, and type-safe interactions with LLMs.

## Quick Start

```python
# 1. Initialize the prompt system
import apps.research_prioritization.prompts.prompt_registry

# 2. Use the prompter
from utils.prompts import Prompter

prompter = Prompter()
prompt = prompter.get_prompt("socioeconomic_v1")

# 3. Format and use the template
template = prompt.template.format(disease_name="Wilson disease", orphacode="905")

# 4. Validate response with the model
response_data = prompt.model(**json_response)
```

## Architecture Components

### 1. BasePrompt Abstract Class

All prompts inherit from `BasePrompt` and implement:

```python
@property
def alias(self) -> str:
    """Unique identifier (e.g., 'socioeconomic_v1')"""

@property  
def template(self) -> str:
    """Complete prompt template with placeholders"""

@property
def model(self) -> Type[BaseModel]:
    """Pydantic model for response validation"""

def parser(self, response: str) -> Any:
    """Optional response parser (default: passthrough)"""
```

### 2. Registration System

Use the `@register_prompt` decorator for automatic registration:

```python
from utils.prompts import register_prompt, BasePrompt

@register_prompt
class MyPrompt(BasePrompt):
    @property
    def alias(self) -> str:
        return "my_prompt_v1"
    # ... other methods
```

### 3. Prompter Interface

The `Prompter` class provides access to registered prompts:

```python
prompter = Prompter()

# Get specific prompt
prompt = prompter.get_prompt("socioeconomic_v1")

# List all available prompts
aliases = prompter.list_prompts()

# Get system inventory
inventory = prompter.get_inventory()

# Check if prompt exists
exists = prompter.has_prompt("some_alias")

# Get prompts by domain
socio_prompts = prompter.get_prompts_by_domain("socioeconomic")
```

## Package Structure

```
utils/prompts/
├── README.md                             # This documentation
├── __init__.py                          # Public exports
├── base_prompt.py                       # Abstract base class
├── prompter.py                          # Registry & prompter
└── exceptions.py                        # Custom exceptions
```

## Available Prompts

### Socioeconomic Impact Analysis

**`socioeconomic_v1`** - Original prompt
- Comprehensive cost-of-illness analysis
- Evidence-based scoring (0-10)
- European focus with Spanish prioritization
- Model: `SocioeconomicImpactResponse`

**`socioeconomic_v2`** - Enhanced version
- Improved instruction structure
- Better evidence hierarchy
- Custom markdown parser
- Model: `SocioeconomicImpactResponse`

### CIBERER Groups Analysis

**`groups_v1`** - Original prompt
- Comprehensive CIBERER unit discovery
- Publication mining with strict criteria
- Verifiable source requirements
- Model: `GroupsResponse`

**`groups_v2`** - Advanced version
- Multi-phase discovery strategy
- Enhanced network analysis
- Improved quality requirements
- Model: `GroupsResponse`

## Usage Patterns

### Basic Usage

```python
import apps.research_prioritization.prompts.prompt_registry
from utils.prompts import Prompter

# Initialize
prompter = Prompter()

# Get prompt
prompt = prompter.get_prompt("socioeconomic_v2")

# Format template
template = prompt.template.format(
    disease_name="Wilson disease",
    orphacode="905"
)

# Use with LLM (example with OpenAI)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": template}],
    response_format={"type": "json_object"}
)

# Parse and validate
parsed = prompt.parser(response.choices[0].message.content)
validated = prompt.model(**json.loads(parsed))
```

### Advanced Usage with Error Handling

```python
from utils.prompts import Prompter, PromptNotFoundError
from pydantic import ValidationError
import json

def analyze_disease(disease_name: str, orphacode: str, version: str = "v2"):
    try:
        # Initialize system
        prompter = Prompter()
        
        # Get prompt with error handling
        try:
            prompt = prompter.get_prompt(f"socioeconomic_{version}")
        except PromptNotFoundError as e:
            print(f"Available prompts: {e.available_prompts}")
            raise
        
        # Format template
        template = prompt.template.format(
            disease_name=disease_name,
            orphacode=orphacode
        )
        
        # Call LLM (your implementation)
        llm_response = your_llm_call(template)
        
        # Parse response
        parsed = prompt.parser(llm_response)
        
        # Validate with Pydantic
        try:
            validated = prompt.model(**json.loads(parsed))
            return validated
        except ValidationError as e:
            print(f"Validation failed: {e}")
            raise
            
    except Exception as e:
        print(f"Analysis failed: {e}")
        raise

# Usage
result = analyze_disease("Wilson disease", "905", "v2")
```

### Custom Prompt Development

```python
from utils.prompts import register_prompt, BasePrompt
from typing import Type
from pydantic import BaseModel, Field

# 1. Define your model
class MyResponse(BaseModel):
    result: str = Field(description="Analysis result")
    confidence: float = Field(description="Confidence score 0-1")

# 2. Create prompt class
@register_prompt
class MyCustomPrompt(BasePrompt):
    @property
    def alias(self) -> str:
        return "my_analysis_v1"
    
    @property
    def template(self) -> str:
        return """Analyze {input_data} and return JSON:
        {{
          "result": "your analysis",
          "confidence": 0.95
        }}
        
        Input: {input_data}"""
    
    @property
    def model(self) -> Type[MyResponse]:
        return MyResponse
    
    def parser(self, response: str) -> str:
        # Custom parsing if needed
        if response.startswith('```json'):
            response = response[7:-3]
        return response

# 3. Add to prompt_registry.py
# from .my_module.prompts import *

# 4. Use immediately
prompter = Prompter()
my_prompt = prompter.get_prompt("my_analysis_v1")
```

## Best Practices

### 1. Prompt Design
- Use clear, structured instructions
- Include concrete examples
- Specify output format explicitly
- Handle edge cases (no data found)

### 2. Versioning Strategy
- Use semantic versioning: `domain_v1`, `domain_v2`
- Keep backward compatibility when possible
- Document changes between versions
- Archive old versions rather than deleting

### 3. Model Design
- Use descriptive field names
- Include helpful descriptions
- Set appropriate defaults
- Use Enums for constrained values

### 4. Error Handling
- Check prompt existence before use
- Validate LLM responses with Pydantic
- Handle parsing errors gracefully
- Log errors with available alternatives

### 5. Testing
- Test all prompt variants
- Validate model schemas
- Test with edge case inputs
- Performance test with large datasets

## Integration with LLMs

### OpenAI Integration

```python
import json
from openai import OpenAI

def call_openai_with_prompt(prompt, **format_kwargs):
    client = OpenAI(api_key="your-key")
    
    # Format template
    template = prompt.template.format(**format_kwargs)
    
    # Call API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": template}],
        response_format={"type": "json_object"}
    )
    
    # Parse and validate
    raw_response = response.choices[0].message.content
    parsed = prompt.parser(raw_response)
    validated = prompt.model(**json.loads(parsed))
    
    return validated
```

### Anthropic Integration

```python
from anthropic import Anthropic

def call_anthropic_with_prompt(prompt, **format_kwargs):
    client = Anthropic(api_key="your-key")
    
    template = prompt.template.format(**format_kwargs)
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=4000,
        messages=[{"role": "user", "content": template}]
    )
    
    parsed = prompt.parser(response.content[0].text)
    validated = prompt.model(**json.loads(parsed))
    
    return validated
```

## Monitoring & Debugging

### System Inventory

```python
prompter = Prompter()
inventory = prompter.get_inventory()

print(f"Total prompts: {inventory['total_prompts']}")
print(f"Domains: {inventory['registry_stats']['domains']}")
print(f"Memory usage: {inventory['registry_stats']['memory_usage_kb']} KB")

# Detailed prompt information
for alias, details in inventory['prompt_details'].items():
    print(f"{alias}: {details['model_name']} ({details['template_length']} chars)")
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# The system will log:
# - Prompt registrations
# - Failed lookups with suggestions
# - Registry operations
```

## Migration Guide

### From Legacy System

1. **Move prompt strings** to new prompt classes
2. **Create Pydantic models** for responses
3. **Update imports** to use `prompt_registry`
4. **Replace string templates** with prompt objects
5. **Add validation** with Pydantic models

### Example Migration

**Before:**
```python
# Old way
template = prompt_socioeconomic_impact.format(disease_name="...", orphacode="...")
response = llm_call(template)
# Manual JSON parsing
```

**After:**
```python
# New way
import apps.research_prioritization.prompts.prompt_registry
from utils.prompts import Prompter

prompter = Prompter()
prompt = prompter.get_prompt("socioeconomic_v1")
template = prompt.template.format(disease_name="...", orphacode="...")
response = llm_call(template)
validated = prompt.model(**json.loads(prompt.parser(response)))
```

## Troubleshooting

### Common Issues

**Q: "Prompt not found" error**
```python
# Check available prompts
prompter = Prompter()
print("Available:", prompter.list_prompts())
```

**Q: Import errors**
```python
# Ensure prompt_registry is imported first
import apps.research_prioritization.prompts.prompt_registry
```

**Q: Validation errors**
```python
# Check model schema
prompt = prompter.get_prompt("alias")
print(prompt.model.model_json_schema())
```

**Q: Template formatting errors**
```python
# Check required placeholders
template = prompt.template
required_vars = re.findall(r'{(\w+)}', template)
print("Required variables:", required_vars)
```

## Performance Considerations

- **Registry caching**: Prompts are instantiated once and cached
- **Memory usage**: ~2KB per prompt on average
- **Import time**: ~100ms for full system initialization
- **Lookup time**: O(1) hash table access

## Examples & Tutorials

See the comprehensive examples in:
- **`../../cookbooks/prompts/`** - Interactive Jupyter notebooks
- **`01_basic_usage.ipynb`** - Getting started tutorial
- **`04_llm_integration.ipynb`** - Production integration patterns

## API Reference

### Classes

#### `BasePrompt`
Abstract base class for all prompts.

**Abstract Properties:**
- `alias: str` - Unique prompt identifier
- `template: str` - Prompt template with placeholders
- `model: Type[BaseModel]` - Pydantic response model

**Methods:**
- `parser(response: str) -> Any` - Parse LLM response (default: passthrough)

#### `Prompter`
Main interface for prompt management.

**Methods:**
- `get_prompt(alias: str) -> BasePrompt` - Get prompt by alias
- `list_prompts() -> List[str]` - List all prompt aliases
- `get_inventory() -> Dict[str, Any]` - System inventory
- `has_prompt(alias: str) -> bool` - Check prompt existence
- `get_prompts_by_domain(domain: str) -> Dict[str, BasePrompt]` - Domain prompts

### Functions

#### `register_prompt(cls: Type[BasePrompt]) -> Type[BasePrompt]`
Decorator for automatic prompt registration.

### Exceptions

- `PromptError` - Base exception
- `PromptNotFoundError` - Prompt not found in registry
- `PromptValidationError` - Prompt validation failed
- `PromptFormattingError` - Template formatting failed
- `PromptRegistrationError` - Registration failed

---

**Architecture Status**: ✅ **PRODUCTION READY**

This system provides a solid foundation for prompt management that scales with project needs while maintaining maximum developer productivity and minimum maintenance overhead.