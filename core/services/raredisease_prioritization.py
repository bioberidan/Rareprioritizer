#!/usr/bin/env python3
"""
Rare Disease Prioritization Service

This script prioritizes rare diseases according to the SOW criteria:
1. Prevalence and Population of Patients (20%)
2. Socioeconomic Impact (20%)  
3. Approved Therapies - Drugs (25%)
4. Clinical Trials in Spain (10%)
5. Gene Therapy Traceability (15%)
6. National Research Capacity - Groups (10%)

The script processes diseases from curated data sources, applies scoring algorithms,
and outputs a prioritized Excel file with the top N diseases and a JSON file.
"""

import sys
import json
import yaml
import logging
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import curated data clients
from core.datastore.orpha.orphadata.curated_prevalence_client import CuratedOrphaPrevalenceClient
from core.datastore.orpha.orphadata.curated_drugs_client import CuratedDrugsClient
from core.datastore.orpha.orphadata.curated_gene_client import CuratedGeneClient
from core.datastore.clinical_trials.curated_clinical_trials_client import CuratedClinicalTrialsClient
from core.datastore.metabolic_prevalence_client import CuratedPrevalenceClient
from core.datastore.websearch.curated_websearch_socioeconomic_client import CuratedWebsearchSocioeconomicClient
from core.datastore.websearch.curated_websearch_groups_client import CuratedWebsearchGroupsClient


@dataclass
class CriteriaScore:
    """Data class for storing criteria scores"""
    prevalence: float = 0.0
    socioeconomic: float = 0.0
    orpha_drugs: float = 0.0
    clinical_trials: float = 0.0
    orpha_gene: float = 0.0
    groups: float = 0.0
    

@dataclass
class DiseaseScore:
    """Data class for storing disease prioritization results"""
    orpha_code: str
    disease_name: str
    criteria_scores: CriteriaScore
    weighted_score: float
    rank: int = 0


class RareDiseasePrioritizer:
    """
    Main prioritization service for rare diseases
    
    Implements the SOW prioritization algorithm using curated data clients
    and configurable scoring weights.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the prioritizer with configuration
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config = self._load_config(config_path)
        self._setup_logging()
        
        # Initialize data clients
        self._init_data_clients()
        
        # Cache for scoring data
        self._scoring_cache = {}
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("RareDiseasePrioritizer initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required keys (removed global 'scoring' for per-criterion scoring)
        required_keys = ['input', 'output', 'criteria']
        for key in required_keys:
            if key not in config:
                raise KeyError(f"Missing required config key: {key}")
        
        return config
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('log_file')
        
        # Create log directory if needed
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_file) if log_file else logging.NullHandler()
            ]
        )
    
    def _init_data_clients(self):
        """Initialize curated data clients"""
        criteria = self.config['criteria']
        
        # Initialize clients based on paths in config
        self.prevalence_client = CuratedOrphaPrevalenceClient(
            data_dir=criteria['prevalence']['path']
        )
        
        self.drugs_client = CuratedDrugsClient(
            data_dir=criteria['orpha_drugs']['path']
        )
        
        self.genes_client = CuratedGeneClient(
            data_dir=criteria['orpha_gene']['path']
        )
        
        self.trials_client = CuratedClinicalTrialsClient(
            data_dir=criteria['clinical_trials']['path']
        )
        
        # Initialize websearch clients
        self.socioeconomic_client = CuratedWebsearchSocioeconomicClient(
            data_dir=criteria['socioeconomic']['path']
        )
        
        self.groups_client = CuratedWebsearchGroupsClient(
            data_dir=criteria['groups']['path']
        )
        
        # For metabolic diseases, use the specific prevalence client
        self.metabolic_prevalence_client = CuratedPrevalenceClient()
    
    # ===== New Statistical Scoring Utility Methods =====
    
    def winsorized_min_max_scaling(self, value: float, max_value: float, scale_factor: float = 10) -> float:
        """
        Generic winsorized min-max scaling: (value / max_value) * scale_factor
        
        Args:
            value: Input value to scale
            max_value: User-defined maximum value (winsorized)
            scale_factor: Output scaling factor (default: 10)
            
        Returns:
            Scaled value, capped at scale_factor
        """
        if value >= max_value:
            return scale_factor  # Winsorized at maximum
        return (value / max_value) * scale_factor

    def reverse_winsorized_min_max_scaling(self, value: float, max_value: float, scale_factor: float = 10) -> float:
        """
        Generic reverse winsorized min-max scaling: (1 - value / max_value) * scale_factor
        
        Args:
            value: Input value to scale (higher values = lower scores)
            max_value: User-defined maximum value (winsorized)
            scale_factor: Output scaling factor (default: 10)
            
        Returns:
            Reverse scaled value, capped at scale_factor
        """
        if value >= max_value:
            return 0.0  # Winsorized at minimum score
        return (1 - value / max_value) * scale_factor
    
    def load_diseases(self) -> List[Dict[str, str]]:
        """
        Load diseases from input data source
        
        Returns:
            List of disease dictionaries with orpha_code and disease_name
        """
        input_file = self.config['input']['data_source']
        
        with open(input_file, 'r', encoding='utf-8') as f:
            diseases = json.load(f)
        
        self.logger.info(f"Loaded {len(diseases)} diseases from {input_file}")
        return diseases
    
    def score_prevalence(self, orpha_code: str) -> float:
        """
        Score prevalence criterion using discrete class mapping
        
        Uses actual prevalence classes from curated data with proper spacing
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) based on prevalence class
        """
        criteria_config = self.config['criteria']['prevalence']
        
        if criteria_config['mock']:
            return criteria_config['mock_value']
        
        # Get prevalence class from curated data
        prevalence_class = self.prevalence_client.get_prevalence_class(orpha_code)
        
        if not prevalence_class:
            # Handle missing data based on config
            handle_missing = criteria_config['scoring'].get('handle_missing_data', 'zero_score')
            return 0.0 if handle_missing == 'zero_score' else criteria_config['mock_value']
        
        # Use class mapping from configuration with corrected spacing
        class_mapping = criteria_config['scoring']['class_mapping']
        return class_mapping.get(prevalence_class, 0.0)
    
    def score_socioeconomic(self, orpha_code: str) -> float:
        """
        Score socioeconomic impact criterion using evidence level mapping
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) based on evidence level
        """
        criteria_config = self.config['criteria']['socioeconomic']
        
        # Use mock values if mock is enabled
        if criteria_config['mock']:
            return criteria_config['mock_value']
        
        # Get evidence level from curated data
        evidence_level = self.socioeconomic_client.get_evidence_level_for_disease(orpha_code)
        
        if not evidence_level:
            # Handle missing data based on config
            handle_missing = criteria_config['scoring'].get('handle_missing_data', 'zero_score')
            return 0.0 if handle_missing == 'zero_score' else criteria_config['mock_value']
        
        # Use evidence level mapping from configuration
        evidence_mappings = criteria_config['scoring']['evidence_mappings']
        return evidence_mappings.get(evidence_level, 0.0)
    
    def score_orpha_drugs(self, orpha_code: str) -> float:
        """
        Score drug criterion using compound weighted reverse winsorized min-max scaling
        
        Formula: weighted_sum of reverse_winsorized_min_max_scaling per data source
        - EU Tradenames: weight=0.8, max=10, scale_factor=10
        - Medical Products: weight=0.2, max=20, scale_factor=10
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) - Higher score for fewer available drugs
        """
        criteria_config = self.config['criteria']['orpha_drugs']
        
        if criteria_config['mock']:
            return criteria_config['mock_value']
        
        # Get compound scoring configuration
        components = criteria_config['scoring']['components']
        total_score = 0.0
        
        for component in components:
            data_source = component['data_source']
            weight = component['weight']
            max_value = component['max']
            scale_factor = component['scale_factor']
            
            # Get drug count for this data source
            if data_source == "eu_tradename_drugs":
                drug_count = len(self.drugs_client.get_eu_tradename_drugs_for_disease(orpha_code))
            elif data_source == "medical_products_eu":
                drug_count = len(self.drugs_client.get_eu_medical_products_for_disease(orpha_code))
            else:
                drug_count = 0
                
            # Apply reverse winsorized min-max scaling: (1 - value/max) * scale_factor
            component_score = self.reverse_winsorized_min_max_scaling(drug_count, max_value, scale_factor)
            
            # Add weighted component
            total_score += component_score * weight
            
        return min(total_score, 10.0)  # Cap at maximum score
    
    def score_clinical_trials(self, orpha_code: str) -> float:
        """
        Score clinical trials criterion using winsorized min-max scaling
        
        Formula: (trial_count / user_max) * scale_factor
        - Max: 100 (user-configured)
        - Scale factor: 10
        - Data source: Spanish trials (fallback to EU trials)
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) - Higher score for more trials
        """
        criteria_config = self.config['criteria']['clinical_trials']
        
        if criteria_config['mock']:
            return criteria_config['mock_value']
            
        # Get configuration
        max_value = criteria_config['scoring']['max']  # User-defined: 100
        scale_factor = criteria_config['scoring']['scale_factor']  # 10
        data_usage = criteria_config['data_usage']
        
        # Get trial count with fallback
        if data_usage['source_preference'] == 'spanish_trials':
            trial_count = len(self.trials_client.get_spanish_trials_for_disease(orpha_code))
            if trial_count == 0 and 'fallback' in data_usage:
                trial_count = len(self.trials_client.get_eu_trials_for_disease(orpha_code))
        else:
            trial_count = len(self.trials_client.get_all_trials_for_disease(orpha_code))
        
        # Apply winsorized min-max scaling: (value / max) * scale_factor
        return self.winsorized_min_max_scaling(trial_count, max_value, scale_factor)
    
    def score_orpha_gene(self, orpha_code: str) -> float:
        """
        Score gene therapy traceability criterion (monogenic diseases only)
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) - 10 only for monogenic diseases (exactly 1 gene)
        """
        criteria_config = self.config['criteria']['orpha_gene']
        
        if criteria_config['mock']:
            return criteria_config['mock_value']
        
        # Get genes for the disease
        genes = self.genes_client.get_genes_for_disease(orpha_code)
        
        # Correct scoring logic:
        # - Monogenic (exactly 1 gene) = 10 points (suitable for gene therapy)
        # - Polygenic (multiple genes) = 0 points (complex, not suitable for simple gene therapy)
        # - Unknown (no genes) = 0 points (no genetic target)
        if len(genes) == 1:
            return 10.0  # Monogenic - ideal for gene therapy
        else:
            return 0.0   # Either polygenic or no genes - not suitable for gene therapy
    
    def score_groups(self, orpha_code: str) -> float:
        """
        Score research groups criterion using winsorized min-max scaling
        
        Formula: (group_count / user_max) * scale_factor
        - Max: 3 (user-configured, capped at 3 groups) 
        - Scale factor: 10
        - Data source: Curated websearch groups
        
        Args:
            orpha_code: Disease Orphanet code
            
        Returns:
            Normalized score (0-10) - Higher score for more research groups
        """
        criteria_config = self.config['criteria']['groups']
        
        if criteria_config['mock']:
            return criteria_config['mock_value']
            
        # Get configuration
        max_value = criteria_config['scoring']['max']  # User-defined: 3
        scale_factor = criteria_config['scoring']['scale_factor']  # 10
        
        # Get group count from curated data
        groups = self.groups_client.get_groups_for_disease(orpha_code)
        group_count = len(groups)
        
        # Apply winsorized min-max scaling
        return self.winsorized_min_max_scaling(group_count, max_value, scale_factor)
    
    def score_disease(self, disease: Dict[str, str]) -> DiseaseScore:
        """
        Score a single disease across all criteria
        
        Args:
            disease: Disease dictionary with orpha_code and disease_name
            
        Returns:
            DiseaseScore object with all criteria scores and weighted total
        """
        orpha_code = disease['orpha_code']
        disease_name = disease['disease_name']
        
        # Calculate individual criteria scores
        criteria_scores = CriteriaScore(
            prevalence=self.score_prevalence(orpha_code),
            socioeconomic=self.score_socioeconomic(orpha_code),
            orpha_drugs=self.score_orpha_drugs(orpha_code),
            clinical_trials=self.score_clinical_trials(orpha_code),
            orpha_gene=self.score_orpha_gene(orpha_code),
            groups=self.score_groups(orpha_code)
        )
        
        # Calculate weighted score using SOW weights
        criteria_config = self.config['criteria']
        weighted_score = (
            criteria_scores.prevalence * criteria_config['prevalence']['weight'] +
            criteria_scores.socioeconomic * criteria_config['socioeconomic']['weight'] +
            criteria_scores.orpha_drugs * criteria_config['orpha_drugs']['weight'] +
            criteria_scores.clinical_trials * criteria_config['clinical_trials']['weight'] +
            criteria_scores.orpha_gene * criteria_config['orpha_gene']['weight'] +
            criteria_scores.groups * criteria_config['groups']['weight']
        )
        
        return DiseaseScore(
            orpha_code=orpha_code,
            disease_name=disease_name,
            criteria_scores=criteria_scores,
            weighted_score=weighted_score
        )
    
    def prioritize_diseases(self, diseases: List[Dict[str, str]]) -> List[DiseaseScore]:
        """
        Score and prioritize all diseases
        
        Args:
            diseases: List of disease dictionaries
            
        Returns:
            List of DiseaseScore objects sorted by priority (highest first)
        """
        self.logger.info(f"Scoring {len(diseases)} diseases across all criteria")
        
        scored_diseases = []
        for i, disease in enumerate(diseases):
            if i % 100 == 0:
                self.logger.info(f"Processed {i}/{len(diseases)} diseases")
            
            try:
                disease_score = self.score_disease(disease)
                scored_diseases.append(disease_score)
            except Exception as e:
                self.logger.warning(f"Failed to score disease {disease['orpha_code']}: {e}")
                continue
        
        # Sort by weighted score (descending)
        scored_diseases.sort(key=lambda x: x.weighted_score, reverse=True)
        
        # Assign ranks
        for i, disease_score in enumerate(scored_diseases):
            disease_score.rank = i + 1
        
        self.logger.info(f"Prioritization complete. Top disease: {scored_diseases[0].disease_name} "
                        f"(score: {scored_diseases[0].weighted_score:.2f})")
        
        return scored_diseases
    
    # ===== Individual Justification Methods =====
    
    def generate_prevalence_justification(self, orpha_code: str) -> str:
        """Generate justification for prevalence scoring"""
        prevalence_class = self.prevalence_client.get_prevalence_class(orpha_code)
        if prevalence_class:
            if prevalence_class == ">1 / 1000":
                return f"Alta prevalencia ({prevalence_class}) indica impacto significativo en salud pública"
            elif prevalence_class in ["6-9 / 10 000", "1-5 / 10 000"]:
                return f"Prevalencia moderada-alta ({prevalence_class}) afecta población sustancial"
            elif prevalence_class == "1-9 / 100 000":
                return f"Prevalencia estándar de enfermedad rara ({prevalence_class}) dentro definición UE"
            elif prevalence_class == "1-9 / 1 000 000":
                return f"Baja prevalencia ({prevalence_class}) condición ultra-rara"
            elif prevalence_class == "<1 / 1 000 000":
                return f"Muy baja prevalencia ({prevalence_class}) condición extremadamente rara"
        else:
            return "Datos de prevalencia desconocidos"
    
    def generate_socioeconomic_justification(self, orpha_code: str) -> str:
        """Generate justification for socioeconomic scoring"""
        if self.config['criteria']['socioeconomic']['mock']:
            return "Impacto socioeconómico asumido alto (fase mock)"
        else:
            # Get justification from curated data
            justification = self.socioeconomic_client.get_justification_for_disease(orpha_code)
            if justification:
                return justification
            else:
                return "Análisis de impacto socioeconómico no disponible"
    
    def generate_drugs_justification(self, orpha_code: str) -> str:
        """Generate justification for drugs scoring"""
        eu_tradename = self.drugs_client.get_eu_tradename_drugs_for_disease(orpha_code)
        eu_medical = self.drugs_client.get_eu_medical_products_for_disease(orpha_code)
        
        if len(eu_tradename) == 0 and len(eu_medical) == 0:
            return "Sin terapias aprobadas disponibles (alta necesidad médica no cubierta)"
        else:
            therapy_desc = []
            if len(eu_tradename) > 0:
                # Get drug names for tradename drugs
                tradename_names = [self.drugs_client.get_drug_name(drug_id) for drug_id in eu_tradename]
                names_str = ", ".join(tradename_names)
                therapy_desc.append(f"{len(eu_tradename)} medicamento(s) comercial(es) UE: ({names_str})")
            if len(eu_medical) > 0:
                # Get drug names for medical products
                medical_names = [self.drugs_client.get_drug_name(drug_id) for drug_id in eu_medical]
                names_str = ", ".join(medical_names)
                therapy_desc.append(f"{len(eu_medical)} producto(s) médico(s): ({names_str})")
            return f"Opciones terapéuticas limitadas: {'; '.join(therapy_desc)}"
    
    def generate_clinical_trials_justification(self, orpha_code: str) -> str:
        """Generate justification for clinical trials scoring"""
        spanish_trials = self.trials_client.get_spanish_trials_for_disease(orpha_code)
        if spanish_trials:
            trial_count = len(spanish_trials)
            return f"Investigación clínica activa española con {trial_count} ensayo(s)"
        else:
            # Check EU trials as fallback
            eu_trials = self.trials_client.get_eu_trials_for_disease(orpha_code)
            if eu_trials:
                trial_count = len(eu_trials)
                return f"Investigación clínica activa UE con {trial_count} ensayo(s) (sin ensayos españoles)"
            else:
                return "Sin ensayos clínicos en curso en España o UE"
    
    def generate_gene_justification(self, orpha_code: str) -> str:
        """Generate justification for gene therapy scoring"""
        genes = self.genes_client.get_genes_for_disease(orpha_code)
        if len(genes) == 1:
            return f"Enfermedad monogénica causada por gen {genes[0]}, ideal para terapia génica"
        elif len(genes) > 1:
            gene_list = ", ".join(genes[:3])  # Show first 3 genes
            if len(genes) > 3:
                gene_list += f" (y {len(genes)-3} otros)"
            return f"Enfermedad poligénica con genes: {gene_list}, base genética compleja no adecuada para terapia génica simple"
        else:
            return "Sin genes causales conocidos identificados, sin diana genética para terapia génica"
    
    def generate_groups_justification(self, orpha_code: str) -> str:
        """Generate justification for research groups scoring"""
        if self.config['criteria']['groups']['mock']:
            return "Grupos de investigación: asumida participación activa (fase mock)"
        else:
            groups = self.groups_client.get_groups_for_disease(orpha_code)
            if groups:
                group_count = len(groups)
                # Show first 3 groups in parentheses like drug justification
                group_names = ", ".join(groups[:3])
                if len(groups) > 3:
                    group_names += f" (y {len(groups)-3} otros)"
                return f"{group_count} grupos de investigación activos: ({group_names})"
            else:
                return "Sin grupos de investigación españoles identificados"

    def export_to_excel(self, scored_diseases: List[DiseaseScore]) -> str:
        """
        Export prioritized diseases to Excel with Spanish column names and detailed justifications
        
        Args:
            scored_diseases: List of scored diseases
            
        Returns:
            Path to output Excel file
        """
        output_config = self.config['output']
        output_dir = Path(output_config['base_path'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Change extension to .xlsx and add timestamp
        base_filename = output_config['filename'].replace('.csv', '')
        output_filename = f"{base_filename}_{timestamp}.xlsx"
        output_file = output_dir / output_filename
        
        # Export ALL diseases for complete analysis in Excel
        total_diseases = len(scored_diseases)
        
        self.logger.info(f"Generating justifications for all {total_diseases} diseases...")
        
        # Prepare data for Excel with separate justification columns - ALL diseases
        excel_data = []
        for i, disease_score in enumerate(scored_diseases):
            if i % 100 == 0:
                self.logger.info(f"Generated justifications for {i}/{total_diseases} diseases")
            
            orpha_code = disease_score.orpha_code
            
            excel_data.append({
                'Ranking': disease_score.rank,
                'Código ORPHA': disease_score.orpha_code,
                'Nombre Enfermedad': disease_score.disease_name,
                'C1: Prevalencia (Score)': round(disease_score.criteria_scores.prevalence, 2),
                'C1: Prevalencia (Justificación)': self.generate_prevalence_justification(orpha_code),
                'C2: Impacto Socioeconómico (Score)': round(disease_score.criteria_scores.socioeconomic, 2),
                'C2: Impacto Socioeconómico (Justificación)': self.generate_socioeconomic_justification(orpha_code),
                'C3: Terapias Aprobadas (Score)': round(disease_score.criteria_scores.orpha_drugs, 2),
                'C3: Terapias Aprobadas (Justificación)': self.generate_drugs_justification(orpha_code),
                'C4: Ensayos Clínicos (Score)': round(disease_score.criteria_scores.clinical_trials, 2),
                'C4: Ensayos Clínicos (Justificación)': self.generate_clinical_trials_justification(orpha_code),
                'C5: Trazabilidad Genética (Score)': round(disease_score.criteria_scores.orpha_gene, 2),
                'C5: Trazabilidad Genética (Justificación)': self.generate_gene_justification(orpha_code),
                'C6: Capacidad Investigadora (Score)': round(disease_score.criteria_scores.groups, 2),
                'C6: Capacidad Investigadora (Justificación)': self.generate_groups_justification(orpha_code),
                'Índice de Prioridad Final': round(disease_score.weighted_score, 2)
            })
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(excel_data)
        
        # Use openpyxl engine for Excel writing
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Priorización Enfermedades')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Priorización Enfermedades']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.logger.info(f"Exported all {len(excel_data)} diseases with justifications to {output_file}")
        return str(output_file)

    def export_prioritized_diseases_json(self, scored_diseases: List[DiseaseScore]) -> str:
        """
        Export prioritized diseases to JSON in the same format as metabolic disease instances
        
        Args:
            scored_diseases: List of scored diseases
            
        Returns:
            Path to output JSON file
        """
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define output path in data/04_curated/metabolic
        output_dir = Path("data/04_curated/metabolic")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_filename = f"prioritized_diseases_{timestamp}.json"
        output_file = output_dir / output_filename
        
        # Get top_n from config to match Excel output
        top_n = self.config['output'].get('top_n', 50)
        
        # Prepare data in the same format as metabolic disease instances - only top_n diseases
        json_data = []
        for disease_score in scored_diseases[:top_n]:
            json_data.append({
                "disease_name": disease_score.disease_name,
                "orpha_code": disease_score.orpha_code
            })
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Exported {len(json_data)} prioritized diseases to {output_file}")
        return str(output_file)
    
    def export_final_top_n_excel(self, scored_diseases: List[DiseaseScore], final_top_n: int) -> str:
        """
        Export final top N prioritized diseases to Excel with Spanish column names and detailed justifications
        
        Args:
            scored_diseases: List of scored diseases
            final_top_n: Number of top diseases to export
            
        Returns:
            Path to output Excel file
        """
        output_config = self.config['output']
        output_dir = Path(output_config['base_path'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create final top N filename
        base_filename = output_config['filename'].replace('.csv', '')
        output_filename = f"{base_filename}_final_top_{final_top_n}_{timestamp}.xlsx"
        output_file = output_dir / output_filename
        
        # Export only final top N diseases
        top_diseases = scored_diseases[:final_top_n]
        
        self.logger.info(f"Generating justifications for final top {final_top_n} diseases...")
        
        # Prepare data for Excel with separate justification columns
        excel_data = []
        for i, disease_score in enumerate(top_diseases):
            orpha_code = disease_score.orpha_code
            
            excel_data.append({
                'Ranking': disease_score.rank,
                'Código ORPHA': disease_score.orpha_code,
                'Nombre Enfermedad': disease_score.disease_name,
                'C1: Prevalencia (Score)': round(disease_score.criteria_scores.prevalence, 2),
                'C1: Prevalencia (Justificación)': self.generate_prevalence_justification(orpha_code),
                'C2: Impacto Socioeconómico (Score)': round(disease_score.criteria_scores.socioeconomic, 2),
                'C2: Impacto Socioeconómico (Justificación)': self.generate_socioeconomic_justification(orpha_code),
                'C3: Terapias Aprobadas (Score)': round(disease_score.criteria_scores.orpha_drugs, 2),
                'C3: Terapias Aprobadas (Justificación)': self.generate_drugs_justification(orpha_code),
                'C4: Ensayos Clínicos (Score)': round(disease_score.criteria_scores.clinical_trials, 2),
                'C4: Ensayos Clínicos (Justificación)': self.generate_clinical_trials_justification(orpha_code),
                'C5: Trazabilidad Genética (Score)': round(disease_score.criteria_scores.orpha_gene, 2),
                'C5: Trazabilidad Genética (Justificación)': self.generate_gene_justification(orpha_code),
                'C6: Capacidad Investigadora (Score)': round(disease_score.criteria_scores.groups, 2),
                'C6: Capacidad Investigadora (Justificación)': self.generate_groups_justification(orpha_code),
                'Índice de Prioridad Final': round(disease_score.weighted_score, 2)
            })
        
        # Create DataFrame and save to Excel
        df = pd.DataFrame(excel_data)
        
        # Use openpyxl engine for Excel writing
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Top Enfermedades Priorizadas')
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Top Enfermedades Priorizadas']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        self.logger.info(f"Exported final top {final_top_n} diseases with justifications to {output_file}")
        return str(output_file)

    def generate_summary_report(self, scored_diseases: List[DiseaseScore]) -> str:
        """
        Generate a summary report of the prioritization
        
        Args:
            scored_diseases: List of scored diseases
            
        Returns:
            Summary report text
        """
        total_diseases = len(scored_diseases)
        criteria_config = self.config['criteria']
        
        # Calculate statistics
        scores = [d.weighted_score for d in scored_diseases]
        mean_score = sum(scores) / len(scores)
        
        # Count diseases with data in each criterion
        has_prevalence = sum(1 for d in scored_diseases if d.criteria_scores.prevalence > 0)
        has_drugs = sum(1 for d in scored_diseases if d.criteria_scores.orpha_drugs < 10)  # Inverse scoring
        has_trials = sum(1 for d in scored_diseases if d.criteria_scores.clinical_trials > 0)
        has_genes = sum(1 for d in scored_diseases if d.criteria_scores.orpha_gene > 0)
        
        report = f"""
Rare Disease Prioritization Summary Report
==========================================

Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Diseases Analyzed: {total_diseases}
Mean Weighted Score: {mean_score:.2f}

Criteria Weights (SOW Configuration):
- Prevalence: {criteria_config['prevalence']['weight']:.0%}
- Socioeconomic: {criteria_config['socioeconomic']['weight']:.0%}
- Drugs (Therapies): {criteria_config['orpha_drugs']['weight']:.0%}
- Clinical Trials: {criteria_config['clinical_trials']['weight']:.0%}
- Gene Therapy: {criteria_config['orpha_gene']['weight']:.0%}
- Groups: {criteria_config['groups']['weight']:.0%}

Data Coverage:
- Diseases with prevalence data: {has_prevalence} ({has_prevalence/total_diseases:.1%})
- Diseases with approved therapies: {has_drugs} ({has_drugs/total_diseases:.1%})
- Diseases with clinical trials: {has_trials} ({has_trials/total_diseases:.1%})
- Diseases with gene data: {has_genes} ({has_genes/total_diseases:.1%})

Top 10 Prioritized Diseases:
"""
        
        for i, disease in enumerate(scored_diseases[:10]):
            report += f"{i+1:2d}. {disease.disease_name} (ORPHA:{disease.orpha_code}) - Score: {disease.weighted_score:.2f}\n"
        
        return report


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Rare Disease Prioritization Service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config conf/raredisease_prioritization.yaml
  %(prog)s --config conf/raredisease_prioritization.yaml --output results/custom_prioritization.xlsx
  %(prog)s --config conf/raredisease_prioritization.yaml --top-n 100 --verbose
        """
    )
    
    parser.add_argument(
        '--config',
        default='conf/raredisease_prioritization.yaml',
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--output',
        help='Override output Excel file path'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        help='Override number of top diseases to export'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show configuration and exit without processing'
    )
    
    return parser


def main():
    """Main function"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        # Initialize prioritizer
        prioritizer = RareDiseasePrioritizer(args.config)
        
        # Override config with command line arguments
        if args.output:
            prioritizer.config['output']['filename'] = Path(args.output).name
            prioritizer.config['output']['base_path'] = str(Path(args.output).parent)
        
        if args.top_n:
            prioritizer.config['output']['top_n'] = args.top_n
        
        if args.verbose:
            prioritizer.config['logging']['level'] = 'DEBUG'
            prioritizer._setup_logging()
        
        logger = logging.getLogger(__name__)
        logger.info("Starting rare disease prioritization")
        
        if args.dry_run:
            logger.info("DRY RUN - Configuration loaded successfully")
            logger.info(f"Input: {prioritizer.config['input']['data_source']}")
            logger.info(f"Output: {prioritizer.config['output']['base_path']}/{prioritizer.config['output']['filename']}")
            logger.info(f"Top N: {prioritizer.config['output']['top_n']}")
            return 0
        
        # Load diseases
        diseases = prioritizer.load_diseases()
        
        # Prioritize diseases
        scored_diseases = prioritizer.prioritize_diseases(diseases)
        
        # Export results to Excel
        excel_output_file = prioritizer.export_to_excel(scored_diseases)
        
        # Export results to JSON
        json_output_file = prioritizer.export_prioritized_diseases_json(scored_diseases)
        
        # Export final top N Excel if configured
        final_excel_output_file = None
        output_final_top_n = prioritizer.config['output'].get('output_final_top_n')
        if output_final_top_n is not None:
            final_excel_output_file = prioritizer.export_final_top_n_excel(scored_diseases, output_final_top_n)
        
        # Generate and print summary
        summary = prioritizer.generate_summary_report(scored_diseases)
        print(summary)
        
        logger.info(f"Prioritization complete.")
        logger.info(f"Excel results saved to: {excel_output_file}")
        logger.info(f"JSON results saved to: {json_output_file}")
        if final_excel_output_file:
            logger.info(f"Final top {output_final_top_n} Excel results saved to: {final_excel_output_file}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 