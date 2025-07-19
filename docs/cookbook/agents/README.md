# Agents Cookbook

Interactive Jupyter notebooks and tutorials for using Carlos III intelligent agents.

## 📚 Learning Path

### Beginner
1. **[01_websearcher_basics.ipynb](01_websearcher_basics.ipynb)** - WebSearcher fundamentals
2. **[02_single_disease_analysis.ipynb](02_single_disease_analysis.ipynb)** - Comprehensive disease analysis
3. **[03_batch_processing.ipynb](03_batch_processing.ipynb)** - Multiple disease analysis

### Intermediate  
4. **[04_error_handling.ipynb](04_error_handling.ipynb)** - Robust error management
5. **[05_performance_optimization.ipynb](05_performance_optimization.ipynb)** - Efficiency patterns

### Advanced
6. **[06_custom_workflows.ipynb](06_custom_workflows.ipynb)** - Building complex workflows
7. **[07_monitoring_and_debugging.ipynb](07_monitoring_and_debugging.ipynb)** - Production monitoring

## 🎯 Quick Reference

### WebSearcher Agent

```python
from agents import WebSearcher

# Basic usage
searcher = WebSearcher("socioeconomic_v1", {"max_output_tokens": 5000})
result = searcher.search({"disease_name": "Wilson disease", "orphacode": "905"})
```

### Available Prompts

- `socioeconomic_v1` - Spanish socioeconomic impact analysis
- `socioeconomic_v2` - Streamlined socioeconomic analysis  
- `groups_v1` - CIBERER research groups analysis
- `groups_v2` - Simplified groups analysis

### Common Client Configurations

```python
# Fast analysis
{"reasoning": {"effort": "low"}, "max_output_tokens": 2000}

# Balanced analysis  
{"reasoning": {"effort": "medium"}, "max_output_tokens": 5000}

# Thorough analysis
{"reasoning": {"effort": "high"}, "max_output_tokens": 10000}
```

## 🚀 Getting Started

### Option 1: Jupyter Notebook (Recommended)
1. **Start Jupyter in the Carlos III project root**:
   ```bash
   jupyter notebook
   ```

2. **Navigate to cookbooks/agents/**

3. **Open `01_websearcher_basics.ipynb`**

4. **Run cells sequentially** to learn interactively

### Option 2: Run Individual Cells
1. **Copy code from notebooks**
2. **Run in your Python environment**

## 📖 What You'll Learn

- How to initialize and configure WebSearcher agents
- Template data formatting best practices
- Error handling and debugging techniques
- Performance optimization strategies
- Building complex multi-step workflows
- Production monitoring and observability

## 🛠️ Prerequisites

- Carlos III prompt system installed and configured
- Access to OpenAI API (with o4-mini model)
- Python environment with required dependencies
- Jupyter Notebook installed (`pip install jupyter`)

## 💡 Tips for Interactive Learning

- **Run cells sequentially** - each builds on the previous
- **Modify parameters** - experiment with different diseases, configs
- **Check outputs** - understand what each step produces
- **Handle errors gracefully** - notebooks show error handling patterns
- **Save your experiments** - notebooks preserve your learning session

## 📊 Notebook Features

Each notebook includes:
- **📝 Clear explanations** in markdown cells
- **💻 Executable code** in code cells
- **📈 Visual outputs** showing results
- **🔍 Debugging examples** with real error scenarios
- **💡 Best practices** and optimization tips

## 🔗 Related Documentation

- [Agents Package README](../../agents/README.md) - Comprehensive API documentation
- [Prompt System Documentation](../prompts/README.md) - Prompt architecture
- [WebSearcher Design Document](../../websearcher.md) - Architecture decisions

## 🤝 Contributing

Found a useful pattern or want to add a notebook?

1. **Create a new numbered notebook** (e.g., `08_your_topic.ipynb`)
2. **Include comprehensive markdown explanations**
3. **Add executable code with error handling**
4. **Test with multiple scenarios**
5. **Add it to the learning path above**

### Notebook Guidelines

- Use descriptive markdown headers
- Include learning objectives at the start
- Provide code comments and explanations
- Show both successful and error scenarios
- End with summary and next steps

Happy coding! 🎉 