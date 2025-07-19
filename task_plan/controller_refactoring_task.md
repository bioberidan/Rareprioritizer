# Task Plan: Controller → ProcessedClient Refactoring

**Date**: December 2024  
**Priority**: Medium  
**Estimated Time**: 30-45 minutes  
**Type**: Architecture Refactoring  

---

## 📋 **Task Overview**

### **Objective**
Rename all Controller classes to follow `Processed{datatype}Client` naming convention for consistency with medallion architecture and to distinguish between processed vs. curated data clients.

### **Rationale**
- **Consistency**: Align with medallion architecture naming patterns
- **Clarity**: Distinguish between processed vs. curated data clients  
- **Future-Proofing**: Enable clean separation of data processing stages
- **Architecture**: Prepare for CuratedClient classes

---

## 🔧 **Classes to Rename**

| Current Class | New Class | File Location |
|---------------|-----------|---------------|
| `PrevalenceController` | `ProcessedPrevalenceClient` | `core/datastore/orpha/orphadata/prevalence_client.py` |
| `DrugController` | `ProcessedDrugClient` | `core/datastore/orpha/orphadata/drug_client.py` |
| `ClinicalTrialsController` | `ProcessedClinicalTrialsClient` | `core/datastore/clinical_trials/clinical_trials_client.py` |

---

## 📁 **Files with Import References**

### **Prevalence Controller References (6 files)**
- `etl/05_stats/orpha/orphadata/prevalence_stats.py`
- `etl/05_stats/orpha/orphadata/p90_trimming_analysis.py`
- `etl/05_stats/orpha/orphadata/log_iqr_asymmetric_analysis.py`
- `etl/05_stats/orpha/orphadata/outlier_analysis.py`
- `etl/05_stats/orpha/orphadata/iqr_outlier_analysis.py`
- `etl/05_stats/orpha/orphadata/iqr_asymmetric_analysis.py`

### **Drug Controller References (1 file)**
- `etl/05_stats/orpha/orphadata/drug_stats.py`

### **Clinical Trials Controller References (1 file)**
- `etl/05_stats/clinical_trials/clinical_trials_stats.py`

---

## 🔄 **Changes Required per File**

### **Import Statement Updates**
```python
# OLD IMPORT
from core.datastore.orpha.orphadata.prevalence_client import PrevalenceController
from core.datastore.orpha.orphadata.drug_client import DrugController  
from core.datastore.clinical_trials.clinical_trials_client import ClinicalTrialsController

# NEW IMPORT  
from core.datastore.orpha.orphadata.prevalence_client import ProcessedPrevalenceClient
from core.datastore.orpha.orphadata.drug_client import ProcessedDrugClient
from core.datastore.clinical_trials.clinical_trials_client import ProcessedClinicalTrialsClient
```

### **Instance Creation Updates**
```python
# OLD INSTANTIATION
self.controller = PrevalenceController()
self.controller = DrugController()
self.controller = ClinicalTrialsController()

# NEW INSTANTIATION
self.controller = ProcessedPrevalenceClient()
self.controller = ProcessedDrugClient()
self.controller = ProcessedClinicalTrialsClient()
```

### **Documentation Updates**
- Update class docstrings mentioning Controller classes
- Update inline comments referencing controllers
- Update any README files or architecture documentation

---

## 📋 **Implementation Steps**

### **Step 1: Update Class Definitions (10 minutes)**
- [ ] Rename `PrevalenceController` → `ProcessedPrevalenceClient` in `prevalence_client.py`
- [ ] Rename `DrugController` → `ProcessedDrugClient` in `drug_client.py`  
- [ ] Rename `ClinicalTrialsController` → `ProcessedClinicalTrialsClient` in `clinical_trials_client.py`
- [ ] Update class docstrings and comments

### **Step 2: Update Import References (15 minutes)**
- [ ] Update import in `prevalence_stats.py`
- [ ] Update import in `p90_trimming_analysis.py`
- [ ] Update import in `log_iqr_asymmetric_analysis.py`
- [ ] Update import in `outlier_analysis.py`
- [ ] Update import in `iqr_outlier_analysis.py`
- [ ] Update import in `iqr_asymmetric_analysis.py`
- [ ] Update import in `drug_stats.py`
- [ ] Update import in `clinical_trials_stats.py`

### **Step 3: Update Instance Creation (10 minutes)**
- [ ] Update all `self.controller = ControllerClass()` instantiations
- [ ] Search for any additional references with grep
- [ ] Update variable names if needed for consistency

### **Step 4: Validation Testing (10 minutes)**
- [ ] Run existing prevalence analysis scripts (skip if files not found)
- [ ] Run outlier analysis scripts (6 files) (skip if files not found)
- [ ] Run drug and clinical trials stats (skip if files not found)
- [ ] Verify no import errors or runtime failures (ignore missing file errors)

---

## 🔍 **Validation Checklist**

### **No Breaking Changes**
- [ ] All existing analysis scripts run successfully (if accessible)
- [ ] No import errors in any file (except missing files due to refactoring)
- [ ] All controller functionality works as before (where testable)

### **Complete Coverage**
- [ ] All Controller class references updated
- [ ] All import statements corrected
- [ ] All instantiation statements updated

### **Naming Consistency**
- [ ] ProcessedClient pattern followed consistently
- [ ] Class names match file organization
- [ ] Docstrings updated appropriately

---

## 🚨 **Risk Mitigation**

### **Directory Refactoring Notice**
- **⚠️ IMPORTANT**: The directory structure has been refactored and files may have been moved to other locations
- **File Location**: Do not attempt to correct file paths or sources during this refactoring
- **Missing Files**: If scripts fail with "file not found" or "missing path" errors, ignore these errors
- **Focus**: Only rename Controller classes to ProcessedClient classes, regardless of file accessibility

### **Missed References**
- **Risk**: Some Controller references might be missed
- **Mitigation**: Use comprehensive grep search before and after changes
- **Command**: `grep -r "Controller" --include="*.py" .`

### **Breaking Existing Functionality**
- **Risk**: Analysis scripts fail after refactoring
- **Mitigation**: Test each script individually, fix issues immediately
- **Note**: File not found errors due to directory refactoring should be ignored
- **Rollback**: Keep backup of original class names if needed

### **Import Errors**
- **Risk**: Incorrect import paths after renaming
- **Mitigation**: Run Python import tests on each file
- **Validation**: Use `python -c "import module"` to test imports
- **Exception**: Skip validation for files that cannot be found due to directory changes

---

## 📊 **Expected Outcomes**

### **Improved Architecture**
- Clear distinction between processed and curated data clients
- Consistent naming across medallion architecture stages
- Ready for future CuratedClient implementations

### **Maintained Functionality**
- All existing analysis scripts continue to work
- No change in data access patterns or performance
- Same API interface with updated class names

### **Future Benefits**
- Clean separation for curated data clients
- Scalable pattern for additional data types
- Improved code maintainability and organization

---

## ⏱️ **Implementation Timeline**

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Class Renaming** | 10 min | Update 3 class definitions |
| **Import Updates** | 15 min | Update 8 import statements |
| **Instance Updates** | 10 min | Update instantiation code |
| **Validation** | 10 min | Test all affected scripts |
| **Total** | **45 min** | Complete refactoring |

---

## 📁 **Complete File List**

### **Class Definition Files (3 files)**
```
core/datastore/orpha/orphadata/prevalence_client.py
core/datastore/orpha/orphadata/drug_client.py
core/datastore/clinical_trials/clinical_trials_client.py
```

### **Import Reference Files (8 files)**
```
etl/05_stats/orpha/orphadata/prevalence_stats.py
etl/05_stats/orpha/orphadata/p90_trimming_analysis.py
etl/05_stats/orpha/orphadata/log_iqr_asymmetric_analysis.py
etl/05_stats/orpha/orphadata/outlier_analysis.py
etl/05_stats/orpha/orphadata/iqr_outlier_analysis.py
etl/05_stats/orpha/orphadata/iqr_asymmetric_analysis.py
etl/05_stats/orpha/orphadata/drug_stats.py
etl/05_stats/clinical_trials/clinical_trials_stats.py
```

---

*This refactoring task improves architectural consistency and prepares the system for clean separation between processed and curated data access patterns.* 