# Pipeline Run Management System Documentation

## Overview

The pipeline run management system provides a universal, per-disease run tracking mechanism for all ETL processes in the research system. This system ensures data consistency, prevents data loss, and enables reprocessing of failed cases.

## Core Concepts

### 1. Per-Disease Run Tracking

Each disease maintains its own independent run sequence:
- **Run 1**: First processing attempt
- **Run 2**: Second processing attempt (reprocessing)
- **Run N**: Nth processing attempt

### 2. Data Type Organization

Processing results are organized by data type:
- `clinical_trials`: Clinical trials data from ClinicalTrials.gov
- `drug`: Drug and treatment information (future)
- `prevalence`: Disease prevalence data (future)
- `biomarkers`: Biomarker data (future)

### 3. File Structure

```
data/preprocessing/
├── {data_type}/
│   ├── {orphacode}/
│   │   ├── run1_disease2{data_type}.json
│   │   ├── run2_disease2{data_type}.json
│   │   └── run{n}_disease2{data_type}.json
│   └── processing_log.json
```

## Run Management Functions

### Core Functions (`utils/pipeline/run_management.py`)

#### `get_next_run_number(data_type: str, orphacode: str) -> int`
- **Purpose**: Determines the next run number for a disease
- **Logic**: Scans existing run files and returns highest run number + 1
- **Returns**: Next available run number (starts at 1)

#### `is_disease_processed(orphacode: str, data_type: str, run_number: int) -> bool`
- **Purpose**: Checks if a disease has already been processed in a specific run
- **Logic**: Looks for existing run file with the specified run number
- **Returns**: True if already processed, False otherwise

#### `create_output_path(data_type: str, orphacode: str, run_number: int) -> str`
- **Purpose**: Generates standardized output file path
- **Format**: `data/preprocessing/{data_type}/{orphacode}/run{run_number}_disease2{data_type}.json`
- **Returns**: Full file path string

#### `save_processing_result(data: dict, data_type: str, orphacode: str, run_number: int)`
- **Purpose**: Saves processing results to the correct location
- **Logic**: Creates directory if needed, saves JSON data
- **Error Handling**: Logs errors, doesn't raise exceptions

## File Naming Conventions

### Standard Format
`run{number}_disease2{data_type}.json`

### Examples
- `run1_disease2clinical_trials.json` - First clinical trials processing
- `run2_disease2clinical_trials.json` - Second clinical trials processing
- `run1_disease2drug.json` - First drug data processing
- `run3_disease2prevalence.json` - Third prevalence data processing

## Processing Flow

### 1. Pre-Processing Check
```python
# Check if disease already processed in current run
run_number = get_next_run_number("clinical_trials", orphacode)
if is_disease_processed(orphacode, "clinical_trials", run_number):
    print(f"Disease {orphacode} already processed in run {run_number}")
    return
```

### 2. Processing Execution
```python
# Execute processing logic
results = process_disease_data(orphacode, disease_name)
```

### 3. Result Storage
```python
# Save results with run management
save_processing_result(results, "clinical_trials", orphacode, run_number)
```

## Reprocessing Strategy

### When to Reprocess
1. **API Failures**: Network issues, rate limiting, server errors
2. **Data Quality Issues**: Malformed responses, missing data
3. **Business Logic Updates**: Algorithm improvements, new requirements
4. **Validation Failures**: Data validation errors

### How to Reprocess
1. **Run the same ETL script again** - the system automatically detects existing runs
2. **New run number assigned** - prevents overwriting existing data
3. **Previous runs preserved** - maintains data history and audit trail

### Example Reprocessing
```bash
# First run
python etl/process_clinical_trials.py
# Creates run1_disease2clinical_trials.json files

# Second run (reprocessing)
python etl/process_clinical_trials.py
# Creates run2_disease2clinical_trials.json files
# run1 files are preserved
```

## Error Handling

### File System Errors
- **Missing directories**: Automatically created
- **Permission errors**: Logged and skipped
- **Disk space issues**: Logged and failed gracefully

### Processing Errors
- **Continue on error**: Individual disease failures don't stop processing
- **Error logging**: All errors logged with context
- **Retry capability**: Rerun script for failed diseases

### Data Validation Errors
- **JSON validation**: Malformed JSON logged and skipped
- **Schema validation**: Schema errors logged but processing continues
- **Data quality**: Quality issues logged for manual review

## Performance Considerations

### Sequential Processing
- **No concurrency**: Simple, reliable processing
- **One disease at a time**: Easier debugging and error isolation
- **Predictable resource usage**: Constant memory and CPU usage

### Storage Optimization
- **Efficient JSON**: Compact JSON format with proper encoding
- **Directory structure**: Hierarchical organization for fast access
- **Cleanup utilities**: Optional cleanup of old runs

## Monitoring and Maintenance

### Log Files
- **Processing logs**: Detailed processing information
- **Error logs**: Error details and context
- **Performance logs**: Processing times and statistics

### Maintenance Tasks
- **Old run cleanup**: Remove old runs to save disk space
- **Performance monitoring**: Track processing times and failures
- **Data quality checks**: Regular validation of processed data

## Integration with ETL Scripts

### Standard Integration Pattern
```python
from utils.pipeline.run_management import (
    get_next_run_number, 
    is_disease_processed, 
    save_processing_result
)

def process_diseases(diseases_file, data_type="clinical_trials"):
    for disease in diseases:
        orphacode = disease['orpha_code']
        
        # Get next run number
        run_number = get_next_run_number(data_type, orphacode)
        
        # Check if already processed
        if is_disease_processed(orphacode, data_type, run_number):
            continue
        
        # Process disease
        results = process_disease_logic(disease)
        
        # Save results
        save_processing_result(results, data_type, orphacode, run_number)
```

## Troubleshooting

### Common Issues

#### "No runs found for disease"
- **Cause**: Disease never processed or files deleted
- **Solution**: Run ETL script to generate initial data

#### "Run number skipped"
- **Cause**: Processing interrupted or failed
- **Solution**: Rerun ETL script - system will continue from next run

#### "Disk space errors"
- **Cause**: Insufficient disk space
- **Solution**: Clean up old runs or increase disk space

#### "Permission denied"
- **Cause**: File system permissions
- **Solution**: Check and fix directory permissions

### Debug Commands
```bash
# Check run status for a disease
ls data/preprocessing/clinical_trials/646/

# Check processing logs
cat data/preprocessing/clinical_trials/processing_log.json

# Count total runs
find data/preprocessing/clinical_trials -name "run*" | wc -l
```

## Best Practices

### 1. Regular Monitoring
- Check processing logs regularly
- Monitor disk space usage
- Track processing success rates

### 2. Data Backup
- Regular backups of processed data
- Version control for ETL scripts
- Document processing configurations

### 3. Error Investigation
- Investigate failed diseases promptly
- Keep error logs for analysis
- Document recurring issues and solutions

### 4. Performance Optimization
- Monitor processing times
- Identify bottlenecks
- Optimize based on usage patterns

## Future Enhancements

### 1. Run Metadata
- Processing duration tracking
- Resource usage monitoring
- Data quality metrics

### 2. Automated Cleanup
- Age-based run cleanup
- Disk space management
- Automated archiving

### 3. Enhanced Monitoring
- Real-time processing dashboards
- Alert systems for failures
- Performance trend analysis

---

This run management system provides a robust, scalable foundation for data processing while maintaining simplicity and reliability. The per-disease run tracking ensures data consistency and enables flexible reprocessing strategies. 