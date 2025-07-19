# Carlos III Research Prioritization - Data Systems Documentation

## Overview

This documentation describes the comprehensive data systems implemented for rare disease research prioritization at Carlos III. The system consists of two primary data collection and analysis pipelines designed to support evidence-based decision making in rare disease research.

## Architecture Overview

The Carlos III Research Prioritization System is built around two core data systems:

### 1. Clinical Trials Data System
- **Purpose**: Collect and analyze clinical trial data from ClinicalTrials.gov
- **Coverage**: 665 rare diseases from Orpha taxonomy
- **Results**: 317 unique clinical trials across 73 diseases (10.98% coverage)
- **Geographic Focus**: Spain-based trials with recruiting/active status

### 2. Drug Data System  
- **Purpose**: Collect and analyze drug/treatment data from Orpha.net
- **Coverage**: Same 665 rare diseases from Orpha taxonomy
- **Results**: 885 unique drugs across 407 diseases (61.2% coverage)
- **Scope**: Comprehensive drug information including regulatory status, manufacturers, and regional availability

## System Integration

Both systems share a common foundation:
- **Data Source**: Orpha taxonomy (665 diseases extracted from 999 total)
- **Architecture**: Identical ETL pipeline structure for consistency
- **Run Management**: Per-disease run numbering with empty run detection
- **Processing**: Sequential processing with rate limiting
- **Output**: Structured JSON data with comprehensive metadata

## Directory Structure

```
carlos_III/
├── docs/                                    # Documentation (this directory)
│   ├── README.md                           # This overview
│   ├── clinical_trial_data_system.md       # Clinical trials system docs
│   └── drug_data_system.md                 # Drug data system docs
├── data/
│   ├── input/etl/init_diseases/            # Source disease data
│   ├── preprocessing/                      # Raw ETL outputs
│   │   ├── clinical_trials/                # Per-disease trial data
│   │   └── drug/                          # Per-disease drug data
│   └── processed/                         # Aggregated datasets
│       ├── clinical_trials/               # Consolidated trial data
│       └── drug/                          # Consolidated drug data
├── etl/                                   # ETL pipeline scripts
├── utils/                                 # Utility modules
│   ├── clinical_trials/                   # Clinical trials API client
│   ├── orpha_drug/                        # Drug data scraper
│   └── pipeline/                          # Universal run management
└── apps/research_prioritization/stats/    # Statistical analysis
```

## Key Features

### Universal Run Management
- **Per-disease tracking**: Each disease maintains independent run history
- **Empty run detection**: Automatic reprocessing of failed/empty runs
- **Error isolation**: Failed diseases don't stop overall processing
- **Extensible design**: Easy to add new data types

### Data Quality Assurance
- **Pydantic models**: Structured data validation
- **Comprehensive logging**: Full audit trail of processing
- **Error handling**: Graceful failure handling with detailed reporting
- **Rate limiting**: Respectful API usage patterns

### Advanced Analytics
- **Statistical analysis**: Comprehensive metrics and visualizations
- **Query interfaces**: Powerful search and filtering capabilities
- **Cross-referencing**: Bidirectional disease-data mappings
- **Dashboard generation**: Executive-level reporting

## Quick Start

### 1. Environment Setup
```bash
# Activate virtual environment
activate_env.bat

# Install dependencies (if needed)
pip install -r requirements.txt
```

### 2. Data Processing
```bash
# Process clinical trials data
python etl/process_clinical_trials.py

# Process drug data
python etl/process_drug_data.py

# Aggregate results
python etl/aggregate_clinical_trials.py
python etl/aggregate_drug_data.py
```

### 3. Analysis and Reporting
```bash
# Generate statistics
python apps/research_prioritization/stats/clinical_trials_stats.py
python apps/research_prioritization/stats/drug_stats.py

# Query interface usage
python etl/clinical_trials_cont.py
python etl/drug_controller.py
```

## Research Applications

### Priority Setting
- **Gap Analysis**: Identify diseases with limited research activity
- **Opportunity Assessment**: Find diseases with drug availability but no trials
- **Resource Allocation**: Data-driven funding decisions

### Collaboration Opportunities
- **Active Research Areas**: Identify diseases with ongoing trials
- **Drug Development**: Connect with pharmaceutical companies
- **International Partnerships**: Geographic distribution analysis

### Strategic Planning
- **Trend Analysis**: Temporal patterns in research activity
- **Portfolio Balance**: Assess diversity of research approaches
- **Impact Measurement**: Track research outcomes over time

## Performance Metrics

### Clinical Trials System
- **Processing Success**: 100% (665/665 diseases)
- **Data Coverage**: 10.98% of diseases have trials
- **Geographic Reach**: 100% Spain-based trials
- **Participant Enrollment**: 330,690 total participants

### Drug Data System
- **Processing Success**: 100% (665/665 diseases)
- **Data Coverage**: 61.2% of diseases have drugs
- **Regulatory Status**: 52.7% approved drugs
- **Geographic Coverage**: 100% US, 12.2% EU

## Technical Specifications

### Rate Limiting
- **Clinical Trials**: Standard API rate limits
- **Drug Data**: 0.5 second delays between requests
- **Respectful Usage**: User-agent headers and session management

### Data Formats
- **Input**: JSON (Orpha taxonomy)
- **Processing**: Per-disease JSON files
- **Output**: Aggregated JSON + CSV exports
- **Visualizations**: PNG plots and dashboards

### Scalability
- **Current Capacity**: 665 diseases processed successfully
- **Extension Ready**: New data types easily added
- **Performance**: Optimized for large-scale processing

## Quality Assurance

### Data Validation
- **Schema Validation**: Pydantic models ensure data integrity
- **Completeness Checking**: Empty run detection and reprocessing
- **Cross-validation**: Consistency checks across data sources

### Error Handling
- **Graceful Degradation**: Continue processing despite individual failures
- **Detailed Logging**: Comprehensive audit trails
- **Manual Review**: Failed case identification and resolution

### Reproducibility
- **Deterministic Processing**: Consistent results across runs
- **Version Control**: All code and configurations tracked
- **Documentation**: Complete methodology documentation

## Future Enhancements

### Data Source Expansion
- **Prevalence Data**: Population-level disease statistics
- **Biomarker Information**: Diagnostic and prognostic markers
- **Genetic Data**: Molecular characterization
- **Health Economics**: Cost-effectiveness analysis

### Advanced Analytics
- **Machine Learning**: Predictive modeling for research success
- **Network Analysis**: Disease-drug-trial relationship mapping
- **Temporal Modeling**: Time-series analysis of research trends
- **Comparative Analysis**: Cross-disease prioritization algorithms

### Integration Capabilities
- **API Development**: RESTful interfaces for external systems
- **Dashboard Development**: Interactive web-based analytics
- **Export Formats**: Integration with external analysis tools
- **Real-time Updates**: Automated data refresh mechanisms

## Support and Maintenance

### Documentation Updates
- **System Changes**: Documentation updated with code changes
- **Best Practices**: Evolved based on operational experience
- **User Guides**: Expanded based on user feedback

### Performance Monitoring
- **System Health**: Regular performance assessments
- **Data Quality**: Ongoing validation and improvement
- **User Experience**: Continuous interface refinement

## Contact Information

For questions about the data systems, please refer to:
- **Clinical Trials System**: See `clinical_trial_data_system.md`
- **Drug Data System**: See `drug_data_system.md`
- **Technical Implementation**: Code comments and inline documentation

---

*This documentation reflects the current implementation as of the latest system deployment. Both systems are production-ready and actively used for research prioritization activities.* 