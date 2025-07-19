# RarePrioritizer: Rare Metabolic Disease Prioritization System

A comprehensive data-driven system for prioritizing rare metabolic diseases using multi-criteria decision analysis (MCDA) with automated data processing and machine learning components.

## 🎯 Overview

RarePrioritizer is a sophisticated system designed to prioritize 665 rare metabolic diseases using a **3-phase workflow**:

1. **Initial Mock Prioritization** - Rank diseases using 4 real criteria + 2 mock criteria
2. **Targeted Web Search ETL** - Gather detailed data for top-priority diseases  
3. **Final Complete Prioritization** - Re-rank using all 6 real criteria

### Six Weighted Criteria

1. **Prevalence and Population** (20%) - Disease frequency and patient impact
2. **Socioeconomic Impact** (20%) - Economic burden and social cost  
3. **Approved Therapies** (25%) - Available treatment options
4. **Clinical Trials** (10%) - Active research in Spain
5. **Gene Therapy Potential** (15%) - Genetic tractability
6. **Research Capacity** (10%) - National research groups

The system processes data from multiple sources including Orphanet, ClinicalTrials.gov, and scientific literature. The 3-phase approach efficiently focuses expensive LLM-based web search on the most promising diseases identified in the initial ranking.

## 🏗️ Architecture

The system follows a clean architecture pattern with modular components:

```
RarePrioritizer/
├── 🚀 apps/              # Application entry points
│   └── api/              # FastAPI REST API
├── 🏗️ core/             # Core business logic
│   ├── datastore/        # Data access clients
│   ├── infrastructure/   # External system adapters
│   ├── services/         # Business logic services
│   └── schemas/          # Data models
├── 📊 etl/              # Extract, Transform, Load pipeline
├── 💾 data/             # Versioned data storage
├── 🌐 frontend/         # React web interface
├── 📚 docs/             # Comprehensive documentation
└── 🧪 tests/            # Test suites
```

### Data Flow

```
Phase 1: External Sources → ETL Pipeline → Curated Data → Mock Prioritization → Priority List JSON
Phase 2: Priority List JSON → Web Search ETL → Socioeconomic & Groups Data → Curated Web Data  
Phase 3: All Curated Data → Final Prioritization Service → Complete Results
```

## 📊 ETL Pipeline

The ETL system processes data through five stages:

1. **01_raw**: Data extraction from external sources
2. **02_preprocess**: Cleaning and per-disease processing  
3. **03_process**: Data aggregation and unification
4. **04_curate**: Quality assurance and optimization
5. **05_stats**: Statistics and analysis generation

### Key Data Sources

- **Orphanet**: Disease prevalence, drugs, genetic associations
- **ClinicalTrials.gov**: Active clinical trials in Spain
- **Scientific Literature**: Socioeconomic impact studies
- **CIBERER**: National research group information

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API keys for external services (see configuration)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd rareprioritizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and settings
```

### Basic Usage

#### 1. Run Initial Mock Prioritization (4 Criteria)

Start with a mock prioritization using 4 real criteria (prevalence, drugs, clinical trials, genes) and mock values for the remaining 2 criteria (socioeconomic, groups). This produces a prioritized list of diseases that will be used for targeted web search:

```bash
# Run initial prioritization with mock values for socioeconomic and groups
python core/services/raredisease_prioritization.py \
    --config conf/raredisease_prioritization.yaml \
    --verbose
```

This generates:
- Excel results with all diseases ranked
- **JSON file** in `data/04_curated/metabolic/prioritized_diseases_{timestamp}.json` containing the top-ranked diseases

#### 2. Execute Web Search ETL for Top-Priority Diseases

Use the JSON file from step 1 to run targeted web search for socioeconomic impact and research groups on the prioritized diseases:

```bash
# Update the config file to point to your generated JSON file
# Edit etl/02_preprocess/websearch/conf/config_socioeconomic.yaml
# Set: data_source: "data/04_curated/metabolic/prioritized_diseases_{your_timestamp}.json"

# Run socioeconomic impact web search
python etl/02_preprocess/websearch/preprocess_metabolic.py \
    --config etl/02_preprocess/websearch/conf/config_socioeconomic.yaml

# Run research groups web search (change analysis_type in config to "groups")
python etl/02_preprocess/websearch/preprocess_metabolic.py \
    --config etl/02_preprocess/websearch/conf/config_metabolic.yaml

# Curate the web search results
python etl/04_curate/websearch/curate_websearch.py
```

#### 3. Run Final Complete Prioritization

Execute the final prioritization with all 6 criteria using real web search data:

```bash
# Run complete prioritization with all real data
python core/services/raredisease_prioritization.py \
    --config core/services/conf/raredisease_prioritization.yaml \
    --verbose
```

### Configuration

The system uses two main YAML configuration files for the different phases:

#### Phase 1: Initial Mock Prioritization
`conf/raredisease_prioritization.yaml` - Used for initial ranking with partial mock data:

```yaml
criteria:
  prevalence:
    mock: false      # Use real Orphanet data
  socioeconomic:
    mock: true       # Use mock values (web search not done yet)
  orpha_drugs:
    mock: false      # Use real Orphanet drug data
  clinical_trials:
    mock: false      # Use real ClinicalTrials.gov data
  orpha_gene:
    mock: false      # Use real Orphanet gene data
  groups:
    mock: true       # Use mock values (web search not done yet)
```

#### Phase 3: Final Complete Prioritization
`core/services/conf/raredisease_prioritization.yaml` - Used for final ranking with all real data:

```yaml
criteria:
  socioeconomic:
    mock: false      # Use real web search data from ETL
    path: "data/04_curated/websearch/socioeconomic"
  groups:
    mock: false      # Use real web search data from ETL
    path: "data/04_curated/websearch/groups"
```

## 📈 Results

The system generates:

- **Prioritized disease rankings** with justifications
- **Detailed scoring breakdown** by criteria  
- **Statistical analysis** and visualizations
- **Export formats**: CSV, Excel, JSON

### Top 10 Prioritized Diseases (Example)

1. **Fenilcetonuria materna** (ORPHA:2209) - Score: 8.60
2. **Deficiencia de trehalasa** (ORPHA:103909) - Score: 7.40
3. **Miopatía GNE** (ORPHA:602) - Score: 7.23
4. **Deficiencia de acil-CoA deshidrogenasa** (ORPHA:42) - Score: 7.14
5. **Albinismo oculocutáneo tipo 2** (ORPHA:79432) - Score: 7.07

## 🧪 Development

### Running Tests

```bash
# Run unit tests
python -m pytest tests/unit/

# Run integration tests
python -m pytest tests/integration/

# Run end-to-end tests
python -m pytest tests/e2e/
```

### API Development

```bash
# Start the API server
python apps/api/main.py

# API will be available at http://localhost:8000
# Interactive documentation at http://localhost:8000/docs
```

### Frontend Development

```bash
cd frontend
npm install
npm start

# Frontend will be available at http://localhost:3000
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` folder:

- **[System Implementation](docs/sistema_priorizacion_implementado.md)**: Complete technical documentation
- **[Architecture Design](docs/architecture_design.md)**: System architecture details
- **[Clinical Trial Data System](docs/clinical_trial_data_system.md)**: Clinical trials processing
- **[ETL Pipeline](etl/README.md)**: Data processing documentation
- **[Cookbook Examples](docs/cookbook/)**: Practical usage examples

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Orphanet** for rare disease data
- **ClinicalTrials.gov** for clinical trial information
- **CIBERER** for Spanish research group data
- **FEDER** and patient organizations for socioeconomic insights

