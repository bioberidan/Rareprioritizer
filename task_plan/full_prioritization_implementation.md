# Full Prioritization Implementation Plan

## Objective
Implement actual scoring for socioeconomic and groups criteria while maintaining backward compatibility with mock functionality.

## Implementation Steps

### 1. Update Configuration
- Add `output_final_top_n` parameter to output section
- Update socioeconomic scoring config with evidence level mappings
- Update groups scoring config with winsorized scaling parameters
- Set paths to curated websearch data directories

### 2. Update RareDiseasePrioritizer Class
- Import curated websearch clients
- Initialize websearch clients in `_init_data_clients()`
- Implement `score_socioeconomic()` with evidence level mapping
- Implement `score_groups()` with winsorized scaling (max=3)
- Update justification methods for socioeconomic and groups

### 3. Update Export Methods
- Add `export_final_top_n_excel()` method
- Modify `main()` to generate additional Excel if `output_final_top_n` is set

### 4. Evidence Level Mappings
```python
evidence_mappings = {
    "High evidence": 10,
    "Medium-High evidence": 7, 
    "Medium evidence": 5,
    "Low evidence": 3,
    "No evidence": 0
}
```

### 5. Groups Winsorized Scaling
- Use `winsorized_min_max_scaling()` with max=3 groups
- Formula: `(group_count / 3) * 10`, capped at 10

### 6. Justification Updates
- Socioeconomic: Use `get_justification_for_disease()`
- Groups: Format as "X grupos de investigación: (group1, group2, group3)"

## Files to Modify
1. `core/services/conf/raredisease_prioritization.yaml` - Update config
2. `core/services/raredisease_prioritization.py` - Implement scoring logic

## Backward Compatibility
- Keep mock flags functional
- All existing mock behavior preserved
- New scoring only active when mock=false 