# Genes ETL Executive Task Plan

## 📋 Executive Overview

This executive plan outlines the development of a comprehensive Genes ETL pipeline that will process Orphanet gene-disease association data from `en_product6.xml` to generate curated gene mappings for rare disease research. The system will follow the proven architecture of the prevalence data system, ultimately producing a `disease2genes.json` file mapping Orpha codes to associated genes.

**Target Output Format:**
```json
{
  "79318": ["KIF7", "GENE2", "GENE3"],
  "272": ["FBN1", "TGFBR2"],
  "orphacode": ["gene1", "gene2", ...]
}
```

**Pipeline Architecture:**
```
Raw XML (21MB) → Processed JSON → Curated Selection → Statistical Analysis
en_product6.xml   Gene-Disease     disease2genes.json   Visualizations
4,078 diseases    Associations     665 metabolic        & Reports
```

## 🎯 Success Criteria

- **Coverage Target:** 80%+ of the 665 metabolic diseases with gene associations
- **Data Quality:** Only validated gene-disease associations in curated output: check gene classes, it should be disease caussing
- **Performance:** Efficient processing of 21MB XML with 4,078+ diseases
- **Integration:** Seamless integration with existing prevalence and drug systems
- **Documentation:** Comprehensive system documentation and usage guides

## 📊 Project Scope

**Input Data:**
- **Source:** `data/01_raw/en_product6.xml` (21MB)
- **Content:** Complete Orphanet gene-disease association database
- **Scope:** +4,078 diseases with comprehensive gene association records
- **Target Subset:** 665 metabolic diseases (matching prevalence/drug systems)

**Expected Output Structure:**
```
data/03_processed/orpha/orphadata/orpha_genes/
├── disease2genes.json              # Complete disease-gene mapping
├── gene2diseases.json              # Reverse lookup: gene→diseases
├── gene_instances.json             # Individual gene records
├── validation_data/                # Gene validation analysis
└── cache/                         # Performance optimization

data/04_curated/orpha/orphadata/
├── disease2genes.json              # Curated subset (665 diseases)
└── gene_curation_summary.json     # Processing metadata
```

## 🗂️ Task Breakdown

---

## Task 1: Raw Gene Data Processing & Extraction
**Deliverable:** `task_plan/task1_genes_raw_processing.md`

**Objective:** Transform raw XML gene data into structured, analysis-ready JSON format

**Key Components:**
- **XML Parsing & Validation:** Process 21MB `en_product6.xml` with error handling
- **Gene-Disease Association Extraction:** Parse `DisorderGeneAssociationList` structures
- **Gene Information Standardization:** Extract gene symbols, names, synonyms, types
- **External Reference Integration:** Include HGNC, Ensembl, ClinVar, Genatlas references
- **Validation Score Calculation:** Develop reliability scoring for gene associations
- **Data Quality Assessment:** Analyze source validation, PMID references

**Technical Scope:**
- Create `etl/03_process/orpha/orphadata/process_orpha_genes.py`
- Implement gene association reliability scoring algorithm
- Generate comprehensive gene-disease mapping files
- Create validation reports and quality metrics
- Establish data structures for downstream processing

**Success Metrics:**
- Successfully process all 4,078 diseases from XML
- Generate structured JSON with gene associations
- Achieve <5% data quality issues
- Complete processing in <10 minutes

---

## Task 2: Gene Data Curation & Selection Algorithm
**Deliverable:** `task_plan/task2_genes_curation_algorithm.md`

**Objective:** Apply sophisticated selection algorithms to curate high-quality gene associations for metabolic diseases

**Key Components:**
- **Disease Subset Filtering:** Focus on 665 metabolic diseases from existing subset
- **Multi-Tier Selection Algorithm:** Prioritize gene associations by validation quality
- **Gene Association Validation:** PMID-referenced sources prioritized over expert opinions
- **Redundancy Resolution:** Handle multiple associations for same gene-disease pair
- **Quality Assurance:** Exclude low-confidence or contradictory associations
- **Conservative Estimation:** Apply safety margins for uncertain associations

**Technical Scope:**
- Create `etl/04_curate/orpha/orphadata/curate_orpha_genes.py`
- Implement priority-based gene selection algorithm
- Develop gene association confidence scoring
- Create quality control mechanisms
- Generate curated `disease2genes.json` output

**Algorithm Framework:**
```
Priority 1: PMID-validated associations with high confidence
Priority 2: Expert-validated associations with multiple sources
Priority 3: Single-source validated associations
Priority 4: Predicted associations with experimental support
Priority 5: Exclude: Low-confidence or contradictory associations
```

**Success Metrics:**
- Achieve 80%+ coverage of metabolic diseases with gene associations
- Maintain 100% data quality in curated output (no invalid associations)
- Generate comprehensive curation metadata and processing statistics

---

## Task 3: Statistical Analysis & Visualization Generation
**Deliverable:** `task_plan/task3_genes_statistics_analysis.md`

**Objective:** Generate comprehensive statistical analysis, visualizations, and research insights

**Key Components:**
- **Coverage Analysis:** Gene association coverage across disease categories
- **Gene Distribution Analysis:** Most frequently associated genes across diseases
- **Validation Quality Metrics:** Source reliability and validation status analysis
- **Cross-System Integration:** Compare gene coverage with prevalence/drug data
- **Research Prioritization Insights:** Identify research gaps and opportunities
- **Publication-Ready Visualizations:** Charts and graphs for research reports

**Technical Scope:**
- Create `etl/05_stats/orpha/orphadata/orpha_genes_stats.py`
- Develop comprehensive statistical analysis framework
- Generate multiple visualization types (distributions, coverage, correlations)
- Create cross-system comparison analytics
- Produce detailed analytical reports

**Visualization Outputs:**
- `gene_association_distribution.png`: Disease-gene association frequency
- `coverage_analysis.png`: Data coverage across metabolic diseases
- `validation_quality_analysis.png`: Source validation and reliability metrics
- `top_genes_analysis.png`: Most frequently associated genes
- `cross_system_comparison.png`: Integration with prevalence/drug data

**Success Metrics:**
- Generate 5+ publication-ready visualizations
- Produce comprehensive statistical analysis report
- Identify key research insights and recommendations
- Complete integration with existing system analytics

---

## Task 4: System Integration & Documentation
**Deliverable:** `task_plan/task4_genes_system_integration.md`

**Objective:** Complete system integration, create data access clients, and produce comprehensive documentation

**Key Components:**
- **Data Access Client Development:** Create `CuratedGenesClient` for programmatic access
- **System Integration:** Integrate with existing prevalence and drug data systems
- **Cross-Reference Capabilities:** Enable multi-system queries across genes/prevalence/drugs
- **Performance Optimization:** Implement lazy loading, caching, and efficient data structures
- **API Integration:** Prepare for FastAPI endpoint integration
- **Comprehensive Documentation:** Complete system documentation following established patterns

**Technical Scope:**
- Create `core/datastore/orpha/orphadata/curated_genes_client.py`
- Implement lazy loading and LRU caching for performance
- Develop comprehensive query methods and search capabilities
- Create export functionality (CSV, JSON formats)
- Generate complete system documentation
- Create usage examples and integration guides

**Documentation Deliverables:**
- `docs/genes_data_system.md`: Complete system documentation
- Client usage examples and API documentation
- Integration guides for cross-system research workflows
- Performance optimization guidelines

**Success Metrics:**
- Achieve <100ms query response times for cached data
- Complete integration with existing system architecture
- Generate comprehensive documentation following established patterns
- Provide seamless API for research applications

---

## 🚀 Implementation Timeline

**Phase 1 (Task 1):** Raw Processing Development - **Week 1**
- XML parsing and data extraction implementation
- Gene association reliability scoring development
- Initial data quality assessment and validation

**Phase 2 (Task 2):** Curation Algorithm Development - **Week 2** 
- Multi-tier selection algorithm implementation
- Quality assurance and validation mechanisms
- Curated dataset generation and testing

**Phase 3 (Task 3):** Analytics & Visualization - **Week 3**
- Statistical analysis framework development
- Visualization generation and testing
- Cross-system integration analytics

**Phase 4 (Task 4):** Integration & Documentation - **Week 4**
- Data access client development
- System integration and performance optimization
- Documentation completion and final testing

## 📈 Expected Outcomes

**Data Products:**
- **Processed Genes Database:** Complete gene-disease association dataset
- **Curated Genes Mapping:** High-quality `disease2genes.json` for 665 diseases
- **Statistical Analysis:** Comprehensive research insights and visualizations
- **Data Access Infrastructure:** Production-ready client and API integration

**Research Impact:**
- **Enhanced Disease Understanding:** Genetic basis for 80%+ of metabolic diseases
- **Research Prioritization:** Identify diseases with genetic basis vs. those needing more research
- **Cross-System Analysis:** Integrated view of prevalence, treatments, and genetic factors
- **Publication Support:** Research-ready data and visualizations

**Technical Excellence:**
- **Scalable Architecture:** Modular pipeline supporting future expansion
- **Performance Optimization:** Efficient processing of large XML datasets
- **Quality Assurance:** Rigorous validation and error handling
- **Integration Standards:** Seamless integration with existing data systems

## 🎯 Risk Assessment & Mitigation

**Data Quality Risks:**
- **Mitigation:** Implement multi-level validation with PMID source prioritization
- **Contingency:** Conservative selection algorithms with safety margins

**Performance Risks:**
- **Mitigation:** Implement streaming XML processing and efficient data structures
- **Contingency:** Parallel processing capabilities for large datasets

**Integration Risks:**
- **Mitigation:** Follow established patterns from prevalence system
- **Contingency:** Comprehensive testing with existing system components

## 📋 Deliverable Summary

1. **Task 1 Plan:** `task_plan/task1_genes_raw_processing.md`
2. **Task 2 Plan:** `task_plan/task2_genes_curation_algorithm.md`  
3. **Task 3 Plan:** `task_plan/task3_genes_statistics_analysis.md`
4. **Task 4 Plan:** `task_plan/task4_genes_system_integration.md`

Each task plan will provide detailed technical specifications, implementation guidance, and success criteria for the respective development phase.

---

**Executive Approval Required:** This plan establishes the foundation for a comprehensive genes data system that will significantly enhance the rare disease research capabilities of the RarePrioritizer platform. 