# WebSearch Metabolic Disease Preprocessing

This script processes metabolic diseases through websearch analysis using WebSearcher agents with retry logic, run management, and configuration-driven analysis type selection.

## Overview

The `process_metabolic_v2.py` script is designed to:
- Process metabolic disease data through web search analysis
- Support multiple analysis types (groups, socioeconomic, clinical)
- Manage multiple runs with automatic incrementing
- Provide comprehensive retry logic and error handling
- Generate detailed processing reports

## Requirements

- Python 3.8+
- Project dependencies (see `pyproject.toml`)
- Configuration file: `conf/config_metabolic.yaml`

## Usage

### Method 1: Module Execution (Recommended)

Run from the project root directory:

```bash
# From rareprioritizer/ directory
python -m etl.02_preprocess.websearch.process_metabolic_v2 [OPTIONS]
```

### Method 2: Direct Execution

Run from the websearch directory:

```bash
# From etl/02_preprocess/websearch/ directory
cd etl/02_preprocess/websearch
python process_metabolic_v2.py [OPTIONS]
```

## Command Line Arguments

### Required Arguments

| Argument | Choices | Description |
|----------|---------|-------------|
| `--analysis` | `groups`, `socioeconomic`, `clinical` | Analysis type to run (required unless using `--status`) |

### Configuration Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--config` | Auto-detected | Path to YAML configuration file |
| `--input` | From config | Path to input JSON file (overrides config) |
| `--output` | From config | Base output directory (overrides config) |

### Run Management Arguments

| Argument | Description |
|----------|-------------|
| `--run` | Specific run number to use (overwrites if exists) |
| `--force-reprocess` | Reprocess even if results exist (increments run number) |

### Processing Arguments

| Argument | Description |
|----------|-------------|
| `--max-retries` | Override retry attempts from config |
| `--dry-run` | Show what would be processed without execution |

### Utility Arguments

| Argument | Description |
|----------|-------------|
| `--status` | Show status of existing disease runs and exit |
| `--verbose` | Enable verbose logging |
| `--help` | Show help message and exit |

## Examples

### Basic Usage

```bash
# Run socioeconomic analysis
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis socioeconomic

# Run groups analysis with verbose logging
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis groups --verbose

# Run clinical analysis as dry run
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis clinical --dry-run
```

### Advanced Usage

```bash
# Force reprocess existing results
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis groups --force-reprocess

# Use specific run number
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis socioeconomic --run 2

# Override configuration
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis clinical \
  --input custom_input.json \
  --output custom_output_dir \
  --max-retries 5

# Custom config file
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis groups \
  --config path/to/custom_config.yaml
```

### Status and Monitoring

```bash
# Check status of existing runs
python -m etl.02_preprocess.websearch.process_metabolic_v2 --status

# Dry run with verbose output
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis socioeconomic --dry-run --verbose
```

## Configuration

The script uses a YAML configuration file (`conf/config_metabolic.yaml`) that defines:

- Input data sources
- Output paths
- Retry logic settings
- Analysis-specific parameters
- Logging configuration

### Configuration Override Priority

1. Command line arguments (highest priority)
2. Configuration file values
3. Default values (lowest priority)

## Output

### File Structure

```
data/02_preprocess/websearch/
├── reports/
│   └── metabolic_[analysis_type]_summary_[timestamp].txt
└── [orphacode]/
    ├── run1_[analysis_type]_[timestamp].json
    ├── run2_[analysis_type]_[timestamp].json
    └── ...
```

### Processing Reports

Each run generates:
- Console output with progress and summary
- Detailed log files (if configured)
- Summary report file with processing statistics
- Individual result files per disease

### Summary Report Contents

- Analysis type and configuration
- Total diseases processed/skipped/failed
- Processing duration and timestamps
- Detailed status per disease
- Error messages and retry information

## Run Management

### Automatic Run Numbering

- The script automatically detects existing runs for each disease
- New runs increment the run number (run1, run2, etc.)
- Use `--force-reprocess` to create a new run even if results exist
- Use `--run N` to specify a particular run number (overwrites if exists)

### Skip Logic

Diseases are skipped if:
- Valid results already exist for the current analysis type
- `--force-reprocess` is not specified
- The disease has been marked as failed in previous runs (configurable)

## Error Handling

- Automatic retry logic with exponential backoff
- Comprehensive error logging
- Graceful handling of network failures
- Resume capability for interrupted processing

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the correct directory or using module execution
2. **Config Not Found**: Check that `conf/config_metabolic.yaml` exists or specify `--config` path
3. **Permission Errors**: Ensure write permissions for output directories
4. **Network Issues**: Use `--max-retries` to increase retry attempts

### Debug Mode

Use `--verbose` and `--dry-run` together for detailed debugging:

```bash
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis socioeconomic --dry-run --verbose
```

## Development

### Adding New Analysis Types

1. Add the new type to the `choices` in `create_argument_parser()`
2. Update the analysis selection logic in the utils modules
3. Add corresponding configuration sections
4. Update this README

### Testing

```bash
# Test help output
python -m etl.02_preprocess.websearch.process_metabolic_v2 --help

# Test status
python -m etl.02_preprocess.websearch.process_metabolic_v2 --status

# Test dry run
python -m etl.02_preprocess.websearch.process_metabolic_v2 --analysis groups --dry-run --verbose
``` 