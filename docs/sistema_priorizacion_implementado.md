# Sistema de Priorización de Enfermedades Raras: Documentación de Implementación

## Resumen Ejecutivo

Este documento describe el sistema de priorización de enfermedades raras implementado según el SOW (Statement of Work) inicial, detallando los cambios realizados durante el desarrollo y las decisiones técnicas tomadas. El sistema prioriza 665 enfermedades metabólicas raras utilizando un modelo de análisis de decisión multicriterio (ADMC) con seis criterios ponderados.

### Cambios Principales respecto al SOW Original

1. **Datos de Entrada**: En lugar de procesar las más de 6,000 enfermedades de Orphanet, el sistema se enfoca en 665 enfermedades metabólicas, permitiendo un análisis más profundo y curado.

2. **Métodos de Puntuación**: Se implementaron métodos estadísticos avanzados (winsorización, escalado inverso) en lugar de simples transformaciones lineales.

3. **Fuentes de Datos**: Se desarrolló un sistema completo de ETL con curación manual y automatizada, superando las limitaciones de acceso directo a algunas fuentes.

4. **Arquitectura Modular**: Se creó una arquitectura de microservicios con clientes de datos especializados en lugar de un sistema monolítico.


## 2. Criterios de Priorización Implementados

### 2.1 Criterio 1: Prevalencia y Población de Pacientes (20%)

**Implementación Real vs SOW Original:**

- **SOW**: Calcular número estimado de pacientes usando prevalencia media de orphanet y población española registrada
- **Implementado**: Sistema de puntuación por niveles basado en clases de prevalencia discretas de Orphanet

**Método de Puntuación - sistema de puntuación por niveles**:

| Clase de Prevalencia | Puntuación | Interpretación Médica |
|---------------------|------------|----------------------|
| >1 / 1000 | 10 | Muy alta prevalencia para enfermedad rara |
| 6-9 / 10 000 | 9 | Alta prevalencia |
| 1-5 / 10 000 | 8 | Prevalencia moderada-alta |
| 1-9 / 100 000 | 6 | Prevalencia estándar de enfermedad rara |
| 1-9 / 1 000 000 | 3 | Baja prevalencia |
| <1 / 1 000 000 | 2 | Ultra-rara |
| Sin datos | 0 | Datos no disponibles |

**Justificación del Cambio**: El SOW original proponía calcular el número estimado de pacientes españoles multiplicando una "prevalencia media" por la población española (47 millones), y después aplicar transformaciones logarítmicas o clasificación por percentiles para normalizar estos números a una escala de 0-10 puntos. Sin embargo, los datos de Orphanet se proporcionan como rangos categóricos (ej. "1-5 / 10 000", "6-9 / 10 000"), no como valores numéricos puntuales. No es posible extraer una "prevalencia media" de un rango sin introducir precisión artificial. Las transformaciones logarítmicas requieren valores numéricos continuos, no categorías ordinales. Igualmente, la clasificación por percentiles necesita una distribución continua de valores, que no puede construirse válidamente a partir de datos categóricos discretos. Además, no se pudo acceder al Registro de Pacientes del ISCIII para obtener números reales. Por tanto, se adoptó el "sistema de puntuación por niveles" especificado en el SOW para el criterio socioeconómico, que es apropiado para datos categóricos y preserva la validez de las clasificaciones médicas.

**Fuente de Datos**: 
- Orphadata (archivos XML curados de prevalencia)
- Cobertura: 532 de 665 enfermedades (80.0%)
- Estimación total: 489,818 pacientes españoles agregados

**Tratamiento de Datos**: Orphanet proporciona múltiples tipos de prevalencia para la misma enfermedad:

| Tipo de Prevalencia | Definición |
|---------------------|------------|
| Point prevalence | Número de personas afectadas en un momento específico |
| Birth prevalence | Número de recién nacidos afectados por cada nacimiento |
| Lifetime prevalence | Probabilidad de desarrollar la enfermedad durante toda la vida |
| Annual incidence | Número de nuevos casos que aparecen cada año |
| Cases/families | Número total de casos o familias reportados en la literatura médica |

El sistema implementa un proceso de selección inteligente priorizando la prevalencia puntual como medida epidemiológica estándar. Cuando existen múltiples registros, selecciona automáticamente el de mayor calidad según los metadatos de Orphanet. Sin prevalencia puntual directa, busca registros mundiales o regionales confiables con validación experta.

Como alternativa, utiliza prevalencia al nacer aplicando un algoritmo de conversión conservador que reduce un escalón la categoría para compensar la mortalidad natural. Por ejemplo, prevalencia al nacer "1-5 por 10,000 nacimientos" se convierte en prevalencia puntual estimada "1-9 por 100,000 habitantes".

Cuando únicamente existen datos de casos o familias reportados, el sistema asigna conservadoramente la categoría más baja ("menos de 1 por 1,000,000 habitantes") debido a que usualmente en enfermedades ultrararas el unico registro posible son los casos reportados en la literatura. Las enfermedades sin información de prevalencia útil reciben puntuación cero.


### 2.2 Criterio 2: Impacto Socioeconómico (20%)

**Implementación Real vs SOW Original**: El SOW proponía un enfoque técnicamente complejo basado en parsers automáticos de XML, APIs de PubMed, scraping de sitios web de organizaciones de pacientes y análisis programático de metadatos bibliográficos para asignar puntuaciones de evidencia. La implementación real simplifica ENORMEMENTE esta arquitectura utilizando un solo agente LLM que realiza búsqueda web inteligente y aplica los mismos criterios de puntuación de forma automatizada, eliminando toda la complejidad de parseo y múltiples conectores de datos.

**Sistema de Puntuación por Niveles**:

| Nivel de Evidencia | Puntuación | Tipo de Estudio | Criterio de Asignación |
|---------------------|------------|-----------------|------------------------|
| High evidence | 10 | Estudio de coste de la enfermedad revisado por pares específico para España | Estudio COI nacional |
| Medium-High evidence | 7 | Estudio de coste de la enfermedad revisado por pares para Europa u otro país de ingresos altos | Estudio COI internacional |
| Medium evidence | 5 | Datos cuantitativos sobre carga financiera en informes de organizaciones de pacientes | Informes cuantitativos |
| Low evidence | 3 | Descripciones cualitativas de impacto severo en literatura científica | Literatura cualitativa |
| No evidence | 0 | Sin información disponible | Ausencia de datos |

**Prompt de Búsqueda Automatizada (socioeconomic_v1)**:

El sistema utiliza el siguiente prompt completo para búsqueda bibliográfica automatizada:

```
Generate a single, well-formed JSON object that assigns a socioeconomic-impact score to a specific rare disease identified by its ORPHA code.
Follow every instruction precisely: add no extra keys, keep the indicated order, and output only the JSON object (no Markdown, no comments).

1 · Gather the best available evidence
Bibliographic search
Query PubMed, Europe PMC, Google Scholar and preprint servers, combining the disease name with terms such as "cost of illness", "economic burden", "cost analysis", "carga económica", etc.

European / international studies
Review pan-European projects (e.g. BURQOL-RD) and cost studies from other high-income countries comparable to Spain.

Patient-organisation reports
Consult documents from recognised groups (FEDER, EURORDIS, national foundations such as "ENSERio").

Qualitative literature
Include publications that describe severe impact on quality of life, dependency or productivity even if they provide no cost figures.

2 · Assign the socioeconomic-impact score
Choose the highest score justified by your evidence:

Score 10 – High evidence: peer-reviewed cost-of-illness study specific to Spain.
Score 7 – Medium-High evidence: peer-reviewed cost-of-illness study from another high-income country or a pan-European analysis.
Score 5 – Medium evidence: quantitative data in a high-quality patient-organisation report (e.g. FEDER).
Score 3 – Low evidence: only qualitative descriptions of severe burden.
Score 0 – No evidence: no relevant information found.

3 · Document all evidence found
socioeconomic_impact_studies (array): list every key reference, even those with lower evidence levels. Each entry must include:

cost: annual mean cost in euros (rounded to an integer) reported by that study / report (enter 0 if not provided).
measure: nature of the cost, e.g. cost of hospitalisation, family out-of-pocket expenses...
label: label of the study, usually the title.
source: verifiable URL (PubMed, DOI, PDF or direct link to the report).
country: country of the study.  
year: year of the study.

4 · Output format
Return only the JSON object below, using double quotes and empty strings ("") for unknown fields (never null).

{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "socioeconomic_impact_studies": [
    {
      "cost": 0,
      "measure": "",
      "label": "",
      "source": "",
      "country": "",
      "year": ""
    }
  ],
  "score": 0,
  "evidence_level": "",
  "justification": ""
}
```

**Fuente de Datos**: El sistema procesa un subconjunto prefiltrado de 25 enfermedades metabólicas prioritarias, ya que cada análisis mediante agente LLM requiere aproximadamente 3 minutos por enfermedad. El proceso incluye mecanismo de reintentos automático (máximo 3 intentos) para manejar fallos de API o respuestas vacías, utilizando el agente WebSearcher con configuración de timeout de 150 segundos y modelo o4-mini con capacidad de razonamiento medio.

### 2.3 Criterio 3: Terapias Aprobadas (25%)

**Implementación Real vs SOW Original**: El SOW proponía un enfoque binario simple donde las enfermedades sin terapias aprobadas recibían puntuación máxima (10) y las que tenían al menos una terapia recibían puntuación mínima (0). La implementación real utiliza un sistema mucho más sofisticado con puntuación compuesta ponderada inversa y min-max scaling winsorizado que considera gradualmente la disponibilidad de opciones terapéuticas.

**Tratamiento de Datos**: Orphanet proporciona información de medicamentos clasificados en dos categorías principales con diferentes relevances clínicas:

| Tipo de Medicamento | Definición | Relevancia Clínica |
|---------------------|------------|-------------------|
| Tradename drugs | Medicamentos comerciales con nombre de marca específico y autorización de comercialización | Alta - tratamientos específicos y validados |
| Medical products | Productos médicos generales incluyendo suplementos nutricionales y dispositivos médicos | Media - soporte terapéutico complementario |


**Sistema de Puntuación Compuesta**:
El sistema funciona con una lógica simple: las enfermedades que tienen menos medicamentos disponibles reciben puntuaciones más altas porque tienen mayor necesidad de nuevos tratamientos. Para calcular la puntuación se establecen límites máximos (4 medicamentos comerciales, 6 productos médicos) para evitar que enfermedades con muchísimos medicamentos desequilibren la puntuación del resto. Si una enfermedad no tiene medicamentos recibe 10 puntos, si tiene algunos medicamentos recibe puntuación media, y si tiene muchos medicamentos recibe puntuación baja. La puntuación final se calcula sumando dos componentes: medicamentos comerciales (cuenta 80% del total) y productos médicos (cuenta 20% del total). Los límites se establecieron en 4 medicamentos comerciales y 6 productos médicos basándose en la distribución empírica de los datos, representando aproximadamente el percentil 95 para cada categoría.

**Nota técnica**: Este sistema se denomina min-max scaling winsorizado inverso (MMSWI) con score compuessto, donde "min-max" se refiere al uso de límites máximos para crear la escala de puntuación, "winsorizado" indica que se truncan los valores extremos para evitar desequilibrios, e "inverso" significa que la relación se invierte para que menos medicamentos genere mayor puntuación. El criterio de truncado a sido deteccion de outliers por el metodo 1.5*IQR.

 El score compuesto se obtiene calculando el MMSWI para cada tipo de medicamento y haceindo la suma ponderada.

| Componente | Peso | Límite Winsorizado | Fórmula |
|------------|------|-------------------|---------|
| EU Tradename Drugs | 0.8 | 4 medicamentos | (1 - count/4) × 10 × 0.8 |
| Medical Products EU | 0.2 | 6 productos | (1 - count/6) × 10 × 0.2 |


### 2.4 Criterio 4: Ensayos Clínicos en España (10%)

**Implementación Real vs SOW Original**: La implementación es prácticamente idéntica al SOW en concepto y método de puntuación. El SOW proponía consultar tanto ClinicalTrials.gov como EU Clinical Trials Information System (CTIS), pero la implementación real utiliza únicamente ClinicalTrials.gov.

**Método de Puntuación**: Se implementa min-max scaling winsorizado donde mayor número de ensayos clínicos genera mayor puntuación. Los outliers se detectaron mediante el método 1.5×IQR estableciendo el límite de winsorización en 3.5 ensayos clínicos, truncando 11 enfermedades con actividad investigadora excepcionalmente alta para evitar desequilibrios en la puntuación del resto.

**Fuente de Datos**:
- ClinicalTrials.gov mediante API v2.0
- Filtros aplicados: país España, estados activos (reclutando, activo sin reclutar)
- Cobertura: 73 de 665 enfermedades con ensayos clínicos (11.0%)

### 2.5 Criterio 5: Trazabilidad para Terapia Génica (15%)

**Implementación Real vs SOW Original**: El SOW proponía consultar la base de datos OMIM para determinar la base genética monogénica de las enfermedades. El sistema implementado utiliza directamente las asociaciones gen-enfermedad curadas de Orphadata, simplificando el proceso y manteniendo la coherencia con las demás fuentes de datos del proyecto.

**Tratamiento de Datos**: Orphanet clasifica las asociaciones gen-enfermedad en diferentes categorías según su relación causal y evidencia científica. La ETL implementa un filtro de selección estricto que incluye únicamente asociaciones gen-enfermedad con evidencia causal confirmada.

| Tipo de Asociación Gen-Enfermedad | Definición | Seleccionado |
|-----------------------------------|------------|--------------|
| Disease-causing germline mutation(s) in | Mutaciones germinales que causan directamente la enfermedad | Sí |
| Disease-causing germline mutation(s) (loss of function) in | Mutaciones germinales con pérdida de función que causan la enfermedad | Sí |
| Disease-causing germline mutation(s) (gain of function) in | Mutaciones germinales con ganancia de función que causan la enfermedad | Sí |
| Disease-causing somatic mutation(s) in | Mutaciones somáticas que causan directamente la enfermedad | Sí |
| Candidate gene tested in | Genes candidatos bajo investigación sin confirmación causal | No |
| Role in the phenotype of | Genes que influyen en el fenotipo sin ser causales directos | No |
| Major susceptibility factor in | Genes que aumentan susceptibilidad sin ser causales directos | No |
| Modifying germline mutation in | Mutaciones que modifican la presentación de la enfermedad | No |

**Método de Puntuación**
Idem al SoW

**Fuente de Datos**: Orphadata gene-disease associations curadas, que integran información genética validada por expertos de múltiples bases de datos internacionales.
- Cobertura: 479 de 665 enfermedades (72.0%)

### 2.6 Criterio 6: Capacidad de Investigación Nacional (10%)

**Implementación Real vs SOW Original**: Idem al criterio socioeconómico - el SOW proponía un enfoque técnicamente complejo con parsing de memorias anuales del CIBERER, análisis de PDFs, scraping web estructurado y consultas programáticas a APIs de PubMed para mapear grupos de investigación. La implementación real simplifica esta arquitectura utilizando un solo agente.

**Sistema de Puntuación por Winsorización**:

| Número de Grupos | Puntuación | Interpretación |
|------------------|------------|----------------|
| 3 o más grupos | 10 | Capacidad investigadora alta |
| 2 grupos | 6.7 | Capacidad investigadora media |
| 1 grupo | 3.3 | Capacidad investigadora limitada |
| 0 grupos | 0 | Sin capacidad investigadora identificada |

**Prompt de Búsqueda Automatizada (groups_v3)**:

El sistema utiliza el siguiente prompt para identificación automatizada de grupos CIBERER:

```
Objective: Identify ALL CIBERER research units or CIBERER-related spanish research units connected to {disease_name} (ORPHA:{orphacode}).

DISCOVERY STRATEGY:

Phase 1: Web Intelligence
- Search CIBERER official website, annual reports, news archives
- Query Google: "CIBERER" + "{disease_name}" + [synonyms, gene names, metabolite names]
- Check ResearchGate, LinkedIn for CIBERER + {disease_name} connections
- Scan clinical trial registries for CIBERER involvement
- if you don't find any results, Try again in spanish instead of english.

Phase 2: Publication Mining
- example of PubMed search: ("{disease_name}"[Title/Abstract] AND "CIBERER"[Affiliation])
- Europe PMC: Advanced search with CIBERER institutional affiliations
- Google Scholar: CIBERER + {disease_name} + specific gene symbols
- Include: Articles, reviews, conference abstracts, preprints

OUTPUT SCHEMA:
{
  "orphacode": "{orphacode}",
  "disease_name": "{disease_name}",
  "groups": [
    {
      "unit_name": "U123",
      "sources": [
        {"label": "source description", "url": "verifiable URL"}
      ]
    }
  ]
}

QUALITY REQUIREMENTS:
✓ Confirm the exact spelling of the group name appears verbatim in at least one source
✓ Minimum 1 verifiable source per unit
✓ Unit name formats: Prefer unit names beginning with U xxx; otherwise keep full descriptive 
  or PI-based label exactly as written
✓ Return pure JSON (no markdown formatting)
```

**Fuente de Datos**: Idem al criterio socioeconómico - el sistema procesa un subconjunto prefiltrado de 25 enfermedades metabólicas prioritarias, ya que cada análisis mediante agente LLM requiere aproximadamente 3 minutos por enfermedad. El proceso incluye mecanismo de reintentos automático (máximo 3 intentos) utilizando el agente WebSearcher con modelo o4-mini y capacidad de razonamiento medio.

## 3. Algoritmo de Priorización

### 3.1 Fórmula de Puntuación Final

La puntuación final para cada enfermedad se calcula mediante suma ponderada:

```
Sf = Σ(Pi × Wi)

Donde:
- Sf = Puntuación final
- Pi = Puntuación normalizada del criterio i (0-10)
- Wi = Peso del criterio i
```

### 3.2 Pesos de los Criterios

| Criterio | Peso | Justificación |
|----------|------|---------------|
| Prevalencia | 20% | Impacto en salud pública |
| Socioeconómico | 20% | Carga social y económica |
| Terapias | 25% | Necesidad médica no cubierta (máxima prioridad) |
| Ensayos Clínicos | 10% | Actividad investigadora |
| Terapia Génica | 15% | Potencial innovador |
| Grupos | 10% | Capacidad nacional |

## 8. Justificaciones Generadas

El sistema genera justificaciones automáticas en español para cada criterio:

### Ejemplos de Justificaciones

**Prevalencia:**
- "Alta prevalencia (>1 / 1000) indica impacto significativo en salud pública"
- "Prevalencia estándar de enfermedad rara (1-9 / 100 000) dentro definición UE"

**Terapias:**
- "Sin terapias aprobadas disponibles (alta necesidad médica no cubierta)"
- "Opciones terapéuticas limitadas: 2 medicamento(s) comercial(es) UE: (Nitisinone, Orfadin)"

**Ensayos Clínicos:**
- "Investigación clínica activa española con 3 ensayo(s)"
- "Sin ensayos clínicos en curso en España o UE"

**Genes:**
- "Enfermedad monogénica causada por gen FAH, ideal para terapia génica"
- "Enfermedad poligénica con genes: COL4A3, COL4A4, COL4A5, base genética compleja"

**Grupos:**
- "2 grupos de investigación activos: (U729 CIBERER, Grupo del Dr. Pérez)"
- "Sin grupos de investigación españoles identificados"

## 4. Top 10 Enfermedades Priorizadas

1. **Fenilcetonuria materna** (ORPHA:2209) - Score: 8.60
2. **Deficiencia de trehalasa** (ORPHA:103909) - Score: 7.40
3. **Miopatía GNE** (ORPHA:602) - Score: 7.23
4. **Deficiencia de acil-CoA deshidrogenasa de cadena media** (ORPHA:42) - Score: 7.14
5. **Albinismo oculocutáneo tipo 2** (ORPHA:79432) - Score: 7.07
6. **PMM2-CDG** (ORPHA:79318) - Score: 6.95
7. **Albinismo oculocutáneo tipo 3** (ORPHA:79433) - Score: 6.87
8. **Intolerancia hereditaria a la fructosa** (ORPHA:469) - Score: 6.80
9. **Deficiencia sistémica primaria de carnitina** (ORPHA:158) - Score: 6.40
10. **Síndrome de Sjögren-Larsson** (ORPHA:816) - Score: 6.20


## 5. Arquitectura del Sistema

### 5.1 Componentes Principales

```
rareprioritizer/
├── core/                          # Núcleo del sistema
│   ├── services/                  # Servicio de priorización
│   │   └── raredisease_prioritization.py
│   ├── datastore/                 # Clientes de acceso a datos
│   │   ├── orpha/                # Datos de Orphanet
│   │   ├── clinical_trials/       # Ensayos clínicos
│   │   └── websearch/            # Datos socioeconómicos y grupos
│   └── schemas/                   # Modelos de datos
├── etl/                          # Pipeline de procesamiento
│   ├── 02_preprocess/            # Preprocesamiento
│   ├── 03_process/               # Procesamiento
│   ├── 04_curate/                # Curación
│   └── 05_stats/                 # Análisis estadístico
└── data/                         # Almacenamiento de datos
    └── 04_curated/               # Datos curados finales
```

### 5.2 Flujo de Datos

```
Fuentes Externas → ETL Pipeline → Datos Curados → Clientes de Datos → Servicio de Priorización → Resultados stadisticos
```

## 6. Pipeline ETL y Procesamiento de Datos

### 6.1 Arquitectura del Pipeline

El sistema implementa un pipeline ETL completo con las siguientes etapas:

1. **Extracción (Raw)**: Descarga de fuentes originales
2. **Preprocesamiento**: Limpieza y estructuración inicial
3. **Procesamiento**: Transformación y enriquecimiento
4. **Curación**: Validación manual y automática
5. **Estadísticas**: Análisis y visualización

