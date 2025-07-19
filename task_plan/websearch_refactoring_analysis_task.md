# WebSearch Refactoring Analysis Task Plan

## Overview
Analyze the simplified websearch metabolic processing script to understand the prompt system, WebSearcher configuration, and overall functionality. This is preparatory analysis before implementing fixes.

## Task 1: Understand Prompt System Architecture

### 1.1 Analyze Prompter Class
- **Objective**: Understand how the Prompter class works
- **Actions**:
  - [ ] Search for and examine the `core.infrastructure.prompts` module
  - [ ] Understand the Prompter class interface and methods
  - [ ] Identify how prompts are loaded and managed
  - [ ] Document the relationship between Prompter and prompt aliases

### 1.2 Analyze Prompt Registry System
- **Objective**: Understand how prompt registration and aliasing works
- **Actions**:
  - [ ] Examine `etl.02_preprocess.websearch.prompts.prompt_registry` module
  - [ ] Understand the `@register_prompt` decorator mechanism
  - [ ] Map how prompt aliases are registered and resolved
  - [ ] Identify all available prompt aliases (especially "groups_v2")
  - [ ] Document the prompt registration workflow

### 1.3 Analyze Prompt Alias Mechanism
- **Objective**: Understand how prompt aliases map to actual prompts
- **Actions**:
  - [ ] Trace how `prompt_alias` parameter flows through the system
  - [ ] Understand how WebSearcher uses prompt aliases
  - [ ] Verify that "groups_v2" alias exists and is properly registered
  - [ ] Document the prompt resolution process

## Task 2: Understand WebSearcher Configuration

### 2.1 Analyze WebSearcher Class
- **Objective**: Understand WebSearcher initialization and configuration
- **Actions**:
  - [ ] Examine the `core.infrastructure.agents.WebSearcher` class
  - [ ] Understand the constructor parameters (prompt_alias, client_kwargs)
  - [ ] Map how client configuration is passed and used
  - [ ] Document the search() method interface and expected inputs

### 2.2 Analyze Client Configuration Structure
- **Objective**: Understand how LLM client configuration works
- **Actions**:
  - [ ] Examine the current client config structure in YAML
  - [ ] Understand what parameters are supported (model, temperature, max_tokens, timeout)
  - [ ] Research where "reasoning_effort" parameter should be added
  - [ ] Document the complete client configuration schema

### 2.3 Research Reasoning Effort Configuration
- **Objective**: Understand how to add reasoning effort to configuration
- **Actions**:
  - [ ] Search for existing reasoning effort implementations in codebase
  - [ ] Understand what LLM models support reasoning effort
  - [ ] Identify the correct parameter name and format
  - [ ] Plan YAML configuration changes needed

## Task 3: Analyze Script Functionality

### 3.1 Review Import Structure
- **Objective**: Verify all imports are correct and available
- **Actions**:
  - [ ] Check all imports in the corrected sections
  - [ ] Verify relative vs absolute import paths
  - [ ] Ensure all required modules exist in the codebase
  - [ ] Document any missing dependencies

### 3.2 Analyze Configuration Loading
- **Objective**: Verify configuration loading works correctly
- **Actions**:
  - [ ] Review `load_simplified_config()` function
  - [ ] Verify it can handle the simplified YAML structure
  - [ ] Check validation of required keys
  - [ ] Test configuration override mechanism

### 3.3 Analyze Disease Processing Flow
- **Objective**: Understand the complete processing workflow
- **Actions**:
  - [ ] Trace the disease processing pipeline
  - [ ] Verify retry wrapper integration
  - [ ] Check error handling mechanisms
  - [ ] Validate file saving and run management logic

### 3.4 Analyze WebSearcher Integration
- **Objective**: Verify WebSearcher is properly integrated
- **Actions**:
  - [ ] Check WebSearcher initialization with config
  - [ ] Verify disease data format expected by searcher
  - [ ] Validate result processing and serialization
  - [ ] Check error handling for search failures

## Task 4: Identify Potential Issues

### 4.1 Configuration Issues
- **Objective**: Identify configuration-related problems
- **Actions**:
  - [ ] Check if config paths are correct for different execution contexts
  - [ ] Verify default configuration file locations
  - [ ] Validate configuration merging logic
  - [ ] Check for missing configuration validation

### 4.2 Import and Dependency Issues
- **Objective**: Identify import and dependency problems
- **Actions**:
  - [ ] Check for circular imports
  - [ ] Verify all utility modules exist
  - [ ] Check if sys.path manipulation is sufficient
  - [ ] Validate module loading sequence

### 4.3 Data Flow Issues
- **Objective**: Identify data processing problems
- **Actions**:
  - [ ] Verify disease data structure compatibility
  - [ ] Check result serialization compatibility
  - [ ] Validate file path handling across platforms
  - [ ] Check for encoding issues

### 4.4 Error Handling Issues
- **Objective**: Identify error handling gaps
- **Actions**:
  - [ ] Review exception handling in main processing loop
  - [ ] Check retry mechanism integration
  - [ ] Validate error reporting and summary generation
  - [ ] Check for graceful failure handling

## Task 5: Create Implementation Plan

### 5.1 Priority Issues
- **Objective**: Rank issues by severity and impact
- **Actions**:
  - [ ] Categorize issues as critical, major, or minor
  - [ ] Identify blocking issues that prevent script execution
  - [ ] Plan fix sequence based on dependencies
  - [ ] Document estimated effort for each fix

### 5.2 Configuration Enhancements
- **Objective**: Plan configuration improvements
- **Actions**:
  - [ ] Design reasoning effort parameter addition
  - [ ] Plan configuration validation enhancements
  - [ ] Design better error messages for config issues
  - [ ] Plan backward compatibility considerations

### 5.3 Testing Strategy
- **Objective**: Plan testing approach for fixes
- **Actions**:
  - [ ] Design unit tests for utility functions
  - [ ] Plan integration tests for WebSearcher
  - [ ] Design end-to-end test with sample data
  - [ ] Plan error condition testing

## Deliverables

1. **Prompt System Analysis Report**
   - Documentation of how Prompter, registry, and aliases work
   - Verification of "groups_v2" prompt availability
   - Flow diagram of prompt resolution

2. **WebSearcher Configuration Analysis**
   - Current configuration schema documentation
   - Reasoning effort integration plan
   - Updated YAML configuration template

3. **Script Functionality Assessment**
   - List of identified issues with severity ratings
   - Compatibility analysis with existing codebase
   - Data flow validation results

4. **Implementation Roadmap**
   - Prioritized list of fixes needed
   - Step-by-step implementation plan
   - Testing strategy for each component

## Success Criteria

- [ ] Complete understanding of prompt system architecture
- [ ] Clear plan for adding reasoning effort to configuration
- [ ] Comprehensive list of script issues identified
- [ ] Actionable implementation plan created
- [ ] All potential blocking issues documented
- [ ] Testing strategy defined for validation

## Notes

- Focus on understanding before implementing
- Document all findings for future reference
- Consider backward compatibility in all changes
- Plan for robust error handling and user feedback
- Ensure configuration changes are well-documented 