# Architecture Documentation

## Intro

RarePrioritizer is a data-driven application designed to prioritize rare diseases and analyze clinical data. The system follows a clean architecture pattern with clear separation of concerns, featuring a data pipeline for processing clinical information, a core business logic layer, and modern web interfaces. The architecture emphasizes modularity, testability, and scalability while maintaining clear data flow from raw sources through processing stages to final curated datasets.

## Structure

```
project-root/
├── .gitattributes          # Git LFS patterns and file handling
├── README.md               # Project overview and quick start
├── pyproject.toml          # Python dependencies and tooling config
├── architecture.md         # This file - architecture documentation
│
├── apps/                   # 🚀 Application entry points (executables)
│   └── api/                # FastAPI REST API service
│       ├── main.py         # API application setup
│       └── asgi.py         # ASGI server configuration
│
├── core/                   # 🏗️ Core business logic and infrastructure
│   ├── __init__.py         # Package initialization
│   ├── infrastructure/     # External system adapters
│   │   ├── connectors/     # Database and external API connectors
│   │   ├── llm/           # Large Language Model integrations
│   │   ├── prompts/       # LLM prompt templates
│   │   └── examples/      # Usage examples and demos
│   ├── schemas/           # Pydantic data models and validation
│   ├── datastore/         # Data access layer and repositories
│   ├── services/          # Application services and use cases
│   └── settings/          # Configuration management
│
├── etl/                   # 📊 Extract, Transform, Load pipeline
│   ├── cli.py             # Command-line interface for ETL tasks
│   ├── 01_raw/            # Raw data extraction scripts
│   ├── 02_preprocess/     # Data cleaning and preprocessing
│   ├── 03_process/        # Data transformation and enrichment
│   ├── 04_curate/         # Data curation and finalization
│   └── utils/             # ETL utility functions and helpers
│
├── data/                  # 💾 Versioned data storage zones
│   ├── 01_raw/            # Raw, unprocessed source data
│   ├── 02_preprocess/     # Cleaned and standardized data
│   ├── 03_processed/      # Transformed and enriched data
│   ├── 04_curated/        # Final, analysis-ready datasets
│   └── results/           # Analysis outputs and reports
│
├── frontend/              # 🌐 React web application
│   ├── package.json       # Node.js dependencies
│   └── src/
│       ├── App.tsx        # Main React application component
│       └── generated/     # Auto-generated TypeScript SDK from API
│
├── docs/                  # 📚 Documentation and guides
│   ├── architecture_design.md  # Detailed architecture design
│   ├── README.md          # Documentation index
│   ├── usage/             # User guides and tutorials
│   ├── cookbook/          # Code examples and recipes
│   └── [data_system_docs] # Specialized data system documentation
│
├── tests/                 # 🧪 Test suites
│   ├── unit/              # Unit tests for individual components
│   ├── integration/       # Integration tests for component interaction
│   └── e2e/               # End-to-end tests for full workflows
│
└── infra/                 # ⚙️ Infrastructure as Code
    ├── docker-compose.yaml # Local development environment
    └── terraform/         # Cloud infrastructure provisioning
```

## Modules

### `/apps` - Application Entry Points
Contains executable applications that serve as entry points to the system. These are never imported by other modules but consume the core business logic.

- **`api/`**: FastAPI-based REST API service providing HTTP endpoints for data access and manipulation. Includes ASGI configuration for production deployment.

### `/core` - Business Logic and Infrastructure
The heart of the application containing all business logic, domain models, and infrastructure adapters.

- **`infrastructure/`**: Adapters for external systems including database connectors, LLM integrations, and prompt management. Follows the ports and adapters pattern.
- **`schemas/`**: Pydantic models defining data structures, validation rules, and API contracts. Ensures type safety across the application.
- **`datastore/`**: Data access layer implementing repository patterns for database operations and data persistence.
- **`services/`**: Application services orchestrating business workflows and use cases. Contains the main business logic.
- **`settings/`**: Configuration management including environment variables, secrets, and application settings.

### `/etl` - Data Pipeline
Comprehensive Extract, Transform, Load pipeline for processing clinical and rare disease data through multiple stages.

- **`01_raw/`**: Scripts for extracting data from various sources (APIs, databases, files) in their original format.
- **`02_preprocess/`**: Data cleaning, standardization, and initial quality checks to prepare raw data for processing.
- **`03_process/`**: Data transformation, enrichment, and feature engineering to create analytical datasets.
- **`04_curate/`**: Final data curation, validation, and preparation of analysis-ready datasets.
- **`utils/`**: Shared utilities, helper functions, and common ETL operations.
- **`cli.py`**: Command-line interface providing unified access to all ETL operations.

### `/data` - Data Storage Zones
Organized data storage following a medallion architecture pattern with clear data lineage and quality progression.

- **`01_raw/`**: Unprocessed source data in original formats, preserved for audit and reprocessing.
- **`02_preprocess/`**: Cleaned and standardized data with consistent schemas and quality checks applied.
- **`03_processed/`**: Transformed data with applied business rules, enrichments, and feature engineering.
- **`04_curated/`**: Production-ready datasets optimized for analysis and reporting.
- **`results/`**: Analysis outputs, reports, and derived insights from the curated data.

### `/frontend` - Web Application
Modern React-based web interface providing user access to the system's capabilities.

- **`src/`**: React components, hooks, and application logic with TypeScript for type safety.
- **`generated/`**: Auto-generated TypeScript SDK from the FastAPI backend ensuring API contract synchronization.

### `/docs` - Documentation
Comprehensive documentation covering architecture, usage, and implementation details.

- **Architecture documentation**: System design, patterns, and technical decisions.
- **`usage/`**: User guides, tutorials, and how-to documentation.
- **`cookbook/`**: Practical examples, code snippets, and common patterns.
- **Data system docs**: Specialized documentation for data flows and processing pipelines.

### `/tests` - Quality Assurance
Multi-level testing strategy ensuring system reliability and correctness.

- **`unit/`**: Fast, isolated tests for individual components and functions.
- **`integration/`**: Tests verifying correct interaction between system components.
- **`e2e/`**: End-to-end tests validating complete user workflows and system behavior.

### `/infra` - Infrastructure
Infrastructure as Code for deployment, orchestration, and environment management.

- **`docker-compose.yaml`**: Local development environment with all required services.
- **`terraform/`**: Cloud infrastructure provisioning for production deployments.

