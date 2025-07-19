# Orpha Disease Preprocessing System - Cookbooks

Welcome to the Orpha Disease Preprocessing System cookbooks! This collection of Jupyter notebooks provides hands-on tutorials and examples for working with the Orpha disease taxonomy system.

## 📚 Learning Path

These cookbooks are designed to take you from beginner to expert in using the Orpha system. Follow the numbered sequence for the best learning experience.

### 🚀 Getting Started (Essential)
Start here if you're new to the Orpha system.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_installation.ipynb](01_getting_started/01_installation.ipynb)** | Setup and installation guide | 15 min | Python 3.8+ |
| **[02_basic_concepts.ipynb](01_getting_started/02_basic_concepts.ipynb)** | Core concepts and architecture | 20 min | Notebook 01 |
| **[03_first_queries.ipynb](01_getting_started/03_first_queries.ipynb)** | Your first taxonomy queries | 25 min | Notebook 02 |

### 🧭 Navigation (Core Skills)
Learn to navigate the taxonomy structure effectively.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_category_navigation.ipynb](02_navigation/01_category_navigation.ipynb)** | Category tree exploration | 30 min | Getting Started |
| **[02_disease_exploration.ipynb](02_navigation/02_disease_exploration.ipynb)** | Disease instance navigation | 35 min | Category Navigation |
| **[03_search_techniques.ipynb](02_navigation/03_search_techniques.ipynb)** | Search and filtering methods | 25 min | Disease Exploration |

### 📊 Data Analysis (Advanced)
Analyze taxonomy data and extract insights.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_statistics_overview.ipynb](03_data_analysis/01_statistics_overview.ipynb)** | System statistics and metrics | 30 min | Navigation Skills |
| **[02_category_analysis.ipynb](03_data_analysis/02_category_analysis.ipynb)** | Category-based analysis | 40 min | Statistics Overview |
| **[03_disease_patterns.ipynb](03_data_analysis/03_disease_patterns.ipynb)** | Disease pattern analysis | 45 min | Category Analysis |

### ⚡ Advanced Usage (Expert)
Master advanced features and optimization techniques.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_batch_processing.ipynb](04_advanced_usage/01_batch_processing.ipynb)** | Batch operations and parallel processing | 35 min | Data Analysis |
| **[02_performance_tuning.ipynb](04_advanced_usage/02_performance_tuning.ipynb)** | Memory and performance optimization | 40 min | Batch Processing |
| **[03_custom_workflows.ipynb](04_advanced_usage/03_custom_workflows.ipynb)** | Custom processing pipelines | 45 min | Performance Tuning |

### 🔗 Integration (Applications)
Integrate the system with other tools and platforms.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_web_applications.ipynb](05_integration/01_web_applications.ipynb)** | Web app integration patterns | 40 min | Advanced Usage |
| **[02_research_workflows.ipynb](05_integration/02_research_workflows.ipynb)** | Research pipeline integration | 45 min | Web Applications |
| **[03_data_export.ipynb](05_integration/03_data_export.ipynb)** | Export and visualization | 35 min | Research Workflows |

### 🏥 Real-World Examples (Applied)
Apply your knowledge to real clinical and research scenarios.

| Notebook | Description | Duration | Prerequisites |
|----------|-------------|----------|---------------|
| **[01_metabolic_analysis.ipynb](06_real_world_examples/01_metabolic_analysis.ipynb)** | Metabolic disease analysis | 50 min | Integration Skills |
| **[02_rare_disease_research.ipynb](06_real_world_examples/02_rare_disease_research.ipynb)** | Rare disease research applications | 55 min | Metabolic Analysis |
| **[03_clinical_applications.ipynb](06_real_world_examples/03_clinical_applications.ipynb)** | Clinical decision support | 60 min | All Previous |

## 🎯 Quick Start Guide

### New to the System?
1. Start with **[01_installation.ipynb](01_getting_started/01_installation.ipynb)** to set up your environment
2. Read **[02_basic_concepts.ipynb](01_getting_started/02_basic_concepts.ipynb)** to understand the architecture
3. Try **[03_first_queries.ipynb](01_getting_started/03_first_queries.ipynb)** for hands-on practice

### Need Specific Skills?
- **Navigation**: Jump to the Navigation series (02_navigation/)
- **Analysis**: Go to Data Analysis series (03_data_analysis/)
- **Performance**: Check Advanced Usage series (04_advanced_usage/)
- **Integration**: See Integration series (05_integration/)

### Looking for Examples?
- **Clinical Use**: See Real-World Examples (06_real_world_examples/)
- **Research Applications**: Check Research Workflows notebook
- **Code Examples**: Look at the basic_usage.py in utils/orpha/examples/

## 🛠️ Prerequisites

### System Requirements
- Python 3.8 or higher
- Jupyter Notebook or JupyterLab
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space

### Required Packages
```bash
pip install pydantic lxml jupyter matplotlib seaborn pandas numpy
```

### Data Requirements
- Processed Orphanet XML data (see installation notebook)
- Data directory structure: `data/processed/`

## 📁 Directory Structure

```
cookbooks/orpha/
├── README.md                           # This file
├── 01_getting_started/
│   ├── 01_installation.ipynb           # Setup and installation
│   ├── 02_basic_concepts.ipynb         # Core concepts
│   └── 03_first_queries.ipynb          # First queries
├── 02_navigation/
│   ├── 01_category_navigation.ipynb    # Category exploration
│   ├── 02_disease_exploration.ipynb    # Disease navigation
│   └── 03_search_techniques.ipynb      # Search methods
├── 03_data_analysis/
│   ├── 01_statistics_overview.ipynb    # System statistics
│   ├── 02_category_analysis.ipynb      # Category analysis
│   └── 03_disease_patterns.ipynb       # Disease patterns
├── 04_advanced_usage/
│   ├── 01_batch_processing.ipynb       # Batch operations
│   ├── 02_performance_tuning.ipynb     # Performance optimization
│   └── 03_custom_workflows.ipynb       # Custom workflows
├── 05_integration/
│   ├── 01_web_applications.ipynb       # Web integration
│   ├── 02_research_workflows.ipynb     # Research pipelines
│   └── 03_data_export.ipynb            # Data export
├── 06_real_world_examples/
│   ├── 01_metabolic_analysis.ipynb     # Metabolic diseases
│   ├── 02_rare_disease_research.ipynb  # Rare diseases
│   └── 03_clinical_applications.ipynb  # Clinical applications
└── utils/
    ├── visualization_helpers.py        # Visualization utilities
    ├── analysis_tools.py              # Analysis helpers
    └── export_utilities.py            # Export utilities
```

## 🎓 Learning Objectives

By completing these cookbooks, you will be able to:

### Basic Level
- ✅ Install and configure the Orpha system
- ✅ Navigate the disease taxonomy structure
- ✅ Search for diseases and categories
- ✅ Understand the separation of taxonomy and instances

### Intermediate Level
- ✅ Perform statistical analysis of the taxonomy
- ✅ Extract disease patterns and relationships
- ✅ Handle errors and edge cases gracefully
- ✅ Optimize queries for performance

### Advanced Level
- ✅ Implement batch processing workflows
- ✅ Integrate with web applications
- ✅ Create custom analysis pipelines
- ✅ Export data for external tools

### Expert Level
- ✅ Apply to real clinical scenarios
- ✅ Conduct rare disease research
- ✅ Build clinical decision support tools
- ✅ Contribute to the system development

## 🔧 Usage Instructions

### Running the Notebooks

1. **Start Jupyter**:
   ```bash
   jupyter notebook
   # or
   jupyter lab
   ```

2. **Navigate to cookbooks**:
   ```
   cookbooks/orpha/
   ```

3. **Open a notebook**:
   - Start with `01_getting_started/01_installation.ipynb`
   - Follow the sequence for best results

### Working with the Code

- **Copy and modify**: All code is designed to be copied and adapted
- **Experiment**: Try modifying parameters and queries
- **Extend**: Build on the examples for your specific use cases

### Data Files

The notebooks expect processed data in `data/processed/`. If you don't have this:
1. Follow the installation notebook
2. Run the data preprocessing script
3. Verify the data structure

## 🆘 Troubleshooting

### Common Issues

**"Data not found" errors**:
- Check that `data/processed/` exists
- Verify all subdirectories are present
- Re-run the data preprocessing if needed

**Import errors**:
- Ensure all packages are installed
- Check Python path configuration
- Verify the project structure

**Performance issues**:
- Monitor memory usage
- Use lazy loading (don't preload all diseases)
- Consider batch processing for large operations

**Unicode errors on Windows**:
- Ensure console encoding is set to UTF-8
- Use the provided environment setup scripts

### Getting Help

1. **Check the troubleshooting guide**: `utils/orpha/docs/TROUBLESHOOTING.md`
2. **Review the API reference**: `utils/orpha/docs/API_REFERENCE.md`
3. **Run the basic examples**: `utils/orpha/examples/basic_usage.py`
4. **Check the system validation**: Use `taxonomy.validate()` method

## 📈 Progress Tracking

Track your progress through the cookbooks:

- [ ] **Getting Started**: Basic installation and concepts
- [ ] **Navigation**: Category and disease exploration
- [ ] **Data Analysis**: Statistics and pattern analysis
- [ ] **Advanced Usage**: Performance and batch processing
- [ ] **Integration**: Web apps and research workflows
- [ ] **Real-World Examples**: Clinical applications

## 🤝 Contributing

We welcome contributions to the cookbooks!

### How to Contribute
1. **Report Issues**: Found a bug or unclear explanation?
2. **Suggest Improvements**: Ideas for better examples or explanations?
3. **Add Examples**: Real-world use cases or advanced techniques?
4. **Improve Documentation**: Clearer instructions or additional context?

### Guidelines
- Follow the existing notebook structure
- Include clear explanations and comments
- Test all code examples
- Provide learning objectives and prerequisites

## 📝 License and Usage

These cookbooks are part of the Orpha Disease Preprocessing System and are provided for educational and research purposes. Please cite appropriately when using in publications or derivative works.

## 🔄 Updates

The cookbooks are regularly updated to reflect system improvements and user feedback. Check the changelog for recent updates:

- **Latest Version**: Check notebook headers for version info
- **Last Updated**: See individual notebook modification dates
- **Changelog**: Available in the main documentation

---

**Happy Learning!** 🎉

Start your journey with the Orpha Disease Preprocessing System and discover the power of structured disease taxonomy navigation. Whether you're a researcher, clinician, or developer, these cookbooks will guide you to mastery of the system.

For questions or support, please refer to the documentation or reach out to the development team. 