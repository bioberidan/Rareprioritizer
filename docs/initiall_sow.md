2. Definiendo las Dimensiones de Prioridad: Los Criterios Fundamentales

El núcleo del modelo ADMC se basa en la definición de un conjunto de criterios que capturan las múltiples facetas de la "prioridad". Se han seleccionado siete criterios, agrupados en dos dimensiones principales: "Carga de la Enfermedad y Necesidad No Cubierta" y "Panorama de Investigación y Desarrollo". A continuación, se detalla la justificación y las fuentes de datos para cada uno.

2.1. Carga de la Enfermedad y Necesidad No Cubierta


2.1.1. Criterio 1: Prevalencia y Población de Pacientes

Justificación: Esta es la métrica fundamental de la escala del problema. Cuantifica el número de individuos afectados por una enfermedad, proporcionando una medida basal de su magnitud como desafío de salud pública. Un mayor número de pacientes, si bien cada enfermedad es "rara" por definición (prevalencia <5 por 10.000 habitantes en Europa), indica una carga agregada mayor para el sistema sanitario y la sociedad.1
Fuentes de Datos e Integración:
Prevalencia Global/Europea: La principal fuente de datos epidemiológicos estandarizados es Orphadata, la plataforma de descarga de Orphanet. Sus archivos, como en_product9_prev.xml, proporcionan datos de prevalencia puntual, prevalencia al nacer, incidencia o número de casos publicados, basados en una curación experta de la literatura científica.7 Estos datos ofrecen un contexto global y una estimación estandarizada para cada enfermedad.
Número de Pacientes en España: El dato de mayor valor y especificidad nacional proviene del Registro de Pacientes de Enfermedades Raras, gestionado por el Instituto de Investigación de Enfermedades Raras (IIER) del Instituto de Salud Carlos III (ISCIII).2 Este registro es la fuente autorizada para conocer el número de casos diagnosticados en España.
Abordaje de la Brecha de Datos en España:
La implementación de este criterio revela una realidad operativa crítica. El acceso público y programático a los datos agregados del registro del ISCIII no está garantizado; la información disponible sugiere que la obtención de datos específicos puede requerir una solicitud formal por correo electrónico (registro.raras@isciii.es).10 Un sistema completamente automatizado no puede depender de un proceso manual y potencialmente lento.
Para superar este obstáculo, el sistema debe diseñarse con un enfoque híbrido de dos niveles:
Nivel 1 (Estimación Automatizada): El sistema calculará de forma automática un número estimado de pacientes en España. Para ello, tomará la clase de prevalencia media proporcionada por Orphadata (p. ej., 5 por 1.000.000) y la aplicará a la población actual de España (aproximadamente 47 millones). Esto proporciona un valor inicial y comparable para todas las enfermedades de la lista.
Nivel 2 (Enriquecimiento Manual con Datos Oficiales): La arquitectura del sistema debe incluir una interfaz que permita a un operador introducir manualmente los datos oficiales de número de pacientes obtenidos del ISCIII. Este dato, de mayor calidad, sobrescribirá la estimación inicial. Este diseño pragmático reconoce las limitaciones de acceso a los datos, proporcionando una solución funcional desde el primer momento, a la vez que permite una mejora progresiva de la precisión del modelo a medida que se establecen flujos de datos con las autoridades nacionales.

2.1.2. Criterio 2: Impacto Socioeconómico

Justificación: Este criterio busca capturar la carga real de una enfermedad más allá del mero recuento de pacientes. Las enfermedades raras a menudo imponen una carga económica y social desproporcionada a los pacientes, sus familias y la sociedad. Esto incluye costes médicos directos (hospitalizaciones, fármacos), costes no médicos (cuidados informales, adaptación de la vivienda, transporte) y costes indirectos (pérdida de productividad laboral del paciente y los cuidadores).11 Una enfermedad con un alto impacto socioeconómico representa una necesidad social urgente.
Fuentes de Datos e Integración:
Estudios de "coste de la enfermedad" (cost-of-illness) publicados en revistas científicas, idealmente específicos para España, como los existentes para la esclerosis sistémica o la epidermólisis bullosa.11
Estudios a nivel europeo, como el proyecto BURQOL-RD, que proporcionan datos de referencia.12
Informes y encuestas de organizaciones de pacientes, como la Federación Española de Enfermedades Raras (FEDER), que documentan la carga financiera y social a través de estudios como el "Estudio ENSERio".15
Literatura cualitativa que describe el impacto en la calidad de vida, el retraso diagnóstico y la necesidad de apoyo psicosocial.19
Cuantificación mediante un Sistema de Puntuación por Niveles:
La disponibilidad de datos robustos sobre el coste de la enfermedad es muy escasa y heterogénea; existen estudios detallados para muy pocas de las más de 6.000 enfermedades raras.22 Basar este criterio únicamente en un valor monetario sería imposible y excluiría a la gran mayoría de las patologías.
Por lo tanto, se debe implementar un sistema de puntuación por niveles basado en la calidad de la evidencia, que permita incorporar la mejor información disponible para cada caso:
Puntuación 10 (Evidencia Alta): Existe un estudio de coste de la enfermedad revisado por pares y específico para España.11
Puntuación 7 (Evidencia Media-Alta): Existe un estudio de coste de la enfermedad revisado por pares para Europa u otro país de ingresos altos comparable.
Puntuación 5 (Evidencia Media): Existen datos cuantitativos sobre la carga financiera en informes de alta calidad de organizaciones de pacientes de referencia (p. ej., FEDER).15
Puntuación 3 (Evidencia Baja): Solo se dispone de descripciones cualitativas de un impacto severo (alta dependencia, gran afectación de la calidad de vida, necesidad de cuidados constantes) en la literatura científica o informes de pacientes.19
Puntuación 0 (Sin Evidencia): No se encuentra información disponible.
Este enfoque pragmático permite que el modelo valore diferencialmente la carga de cada enfermedad, recompensando con una puntuación más alta a aquellas con un impacto documentado, sin penalizar injustamente a las que sufren de escasez de datos.

2.1.3. Criterio 3: Terapias Aprobadas Existentes

Justificación: Este es el indicador más directo de necesidad médica no cubierta. La ausencia total de una terapia aprobada para una enfermedad representa un "vacío terapéutico" y eleva intrínsecamente su prioridad. Por el contrario, la existencia de uno o más tratamientos, aunque no sean curativos, indica que ya se ha recorrido una parte del camino del desarrollo.23
Fuentes de Datos e Integración:
Agencia Europea de Medicamentos (EMA): El Registro Comunitario de medicamentos huérfanos es la fuente principal para identificar los fármacos con designación huérfana y autorización de comercialización en la Unión Europea.24 Listados curados por organizaciones como EURORDIS y Orphanet complementan esta información.25
Agencia Española de Medicamentos y Productos Sanitarios (AEMPS): El Centro de Información online de Medicamentos (CIMA) es la base de datos autorizada para todos los medicamentos autorizados y comercializados en España.28
Restricción en la Estrategia de Búsqueda y Flujo de Trabajo:
Una limitación técnica clave es que el buscador avanzado de CIMA no permite realizar búsquedas por indicación terapéutica o nombre de la enfermedad; las búsquedas se limitan a criterios como el nombre del medicamento, el principio activo o el código nacional.30 Esto impide una consulta directa del tipo "¿qué medicamentos están aprobados en España para la Enfermedad X?".
Para solventar esto, el proceso de adquisición de datos debe ser secuencial:
Paso 1 (Identificación en Europa): Consultar las fuentes de la EMA y Orphanet para obtener una lista de los nombres comerciales de los medicamentos que han sido aprobados a nivel europeo para una enfermedad rara específica.25
Paso 2 (Confirmación en España): Utilizar los nombres comerciales identificados en el paso anterior para realizar búsquedas específicas en la base de datos CIMA de la AEMPS. Esto permitirá confirmar si dicho medicamento está efectivamente autorizado y en qué estado de comercialización se encuentra en España.28
El resultado de este proceso será una puntuación binaria: 1 si no existe ninguna terapia aprobada y comercializada en España para esa enfermedad, y 0 si existe al menos una.

2.2. Panorama de Investigación y Desarrollo


2.2.1. Criterio 4: Investigación Clínica en Curso (en España)

Justificación: El número de ensayos clínicos activos es un indicador potente del impulso de la I+D, el interés científico y la probabilidad de que una nueva terapia emerja en un futuro próximo. Centrarse específicamente en los ensayos con participación de centros españoles mide directamente la implicación del país en la vanguardia de la investigación para esa enfermedad y el acceso potencial de los pacientes españoles a tratamientos innovadores.
Fuentes de Datos e Integración:
ClinicalTrials.gov: Es el mayor registro de ensayos clínicos del mundo, gestionado por la Biblioteca Nacional de Medicina de EE. UU. Su nueva API (v2.0) es una herramienta robusta que permite realizar consultas complejas y estructuradas.31
Clinical Trials Information System (CTIS) de la UE: Es el portal único y obligatorio para la presentación y autorización de todos los ensayos clínicos en la UE/EEE desde el 31 de enero de 2022.33 Sustituye al antiguo registro EudraCT y ofrece un portal público con capacidades de búsqueda avanzada.34
Fiabilidad y Automatización gracias a las API:
Afortunadamente, tanto ClinicalTrials.gov como el CTIS de la UE ofrecen interfaces de programación de aplicaciones (API) modernas o portales de búsqueda muy bien estructurados que facilitan enormemente la extracción de datos.32 Estas plataformas permiten filtrar las búsquedas por múltiples campos de manera precisa.
Esto convierte la recopilación de datos para este criterio en una de las partes más fiables y automatizables de todo el proyecto. El protocolo técnico especificará llamadas a las API o consultas web estructuradas para cada enfermedad de la lista de Orphanet (incluyendo sus sinónimos), con los siguientes filtros aplicados:
Condition (Enfermedad): Nombre de la enfermedad y sinónimos.
Country (País): "Spain".
Status (Estado): "Recruiting" (Reclutando), "Enrolling by invitation" (Reclutando por invitación), "Active, not recruiting" (Activo, no reclutando).
La puntuación para este criterio será un recuento directo del número de ensayos únicos que cumplan estas condiciones, reflejando la actividad investigadora clínica actual en España para cada patología.

2.2.2. Criterio 5: Trazabilidad para Terapias Avanzadas

Justificación: Este criterio evalúa la viabilidad científica de aplicar modalidades terapéuticas de vanguardia, con un enfoque particular en las terapias génicas y celulares. Las enfermedades con una causa monogénica conocida (causadas por la mutación de un único gen) son candidatas ideales para estrategias de reemplazo génico, edición génica (como CRISPR-Cas9) o terapias basadas en ARN, que tienen el potencial de ser curativas o transformadoras. Priorizar estas enfermedades supone una apuesta estratégica por la medicina de precisión y la innovación de alto impacto.
Fuentes de Datos e Integración:
Online Mendelian Inheritance in Man (OMIM): Esta base de datos, mantenida por la Universidad Johns Hopkins, es el compendio autoritativo y universalmente reconocido de los genes humanos y los fenotipos genéticos.36 Es el estándar de oro para identificar la base genética de las enfermedades.
Orphanet: De forma crucial para la automatización, la base de datos de Orphanet incluye referencias cruzadas desde cada ORPHAcode a su correspondiente número de entrada en OMIM, cuando existe una correlación establecida.37
OMIM como Indicador Cuantificable de Idoneidad para Terapia Génica:
Evaluar directamente la "idoneidad" para la terapia génica de más de 6.000 enfermedades es una tarea de revisión científica monumental, inviable para un sistema automatizado. Sin embargo, se puede utilizar un indicador indirecto (proxy) muy potente y fácilmente cuantificable: la existencia de una etiología monogénica confirmada.
El proceso algorítmico para determinar esto es el siguiente:
Paso 1 (Obtener Referencia): Para un ORPHAcode dado, consultar la base de datos de Orphanet (a través de la API o los archivos descargables) para obtener su referencia cruzada a OMIM.37
Paso 2 (Consultar OMIM): Utilizar el ID de OMIM obtenido para realizar una consulta a la API de OMIM.36
Paso 3 (Analizar Entrada): Analizar la respuesta de la API para determinar el tipo de entrada. OMIM clasifica sus entradas, y aquellas que describen un gen con una mutación causante de enfermedad conocida son las de interés.
Se asignará una puntuación binaria de alta ponderación: una puntuación elevada (p. ej., 10) si la enfermedad tiene una base monogénica claramente documentada en OMIM, y una puntuación de 0 si no la tiene (por ser poligénica, de causa ambiental, desconocida, etc.).

2.2.3. Criterio 6: Capacidad de Investigación Nacional

Justificación: Invertir recursos en la investigación de una enfermedad para la cual España ya posee una masa crítica de experiencia científica genera un efecto sinérgico. Aprovecha el conocimiento, la infraestructura, las cohortes de pacientes y el talento ya existentes, aumentando la probabilidad de éxito y la eficiencia de la inversión. Este criterio mide la fortaleza del ecosistema de investigación español para una enfermedad concreta.
Fuentes de Datos e Integración:
CIBERER (Centro de Investigación Biomédica en Red de Enfermedades Raras): Es la estructura central que aglutina a los principales grupos de investigación en EERR de España. Su sitio web, sus programas de investigación y, sobre todo, sus memorias anuales son las fuentes primarias de información.4
PubMed y otras bases de datos académicas: Son esenciales para vincular de manera objetiva a los grupos de investigación con las enfermedades específicas que estudian, a través de su producción científica.
El Desafío de Mapear Grupos de Investigación a Enfermedades Específicas:
El CIBERER no proporciona una base de datos estructurada y fácilmente consultable que asocie cada uno de sus aproximadamente 60 grupos de investigación 40 con los ORPHAcodes específicos de las enfermedades que investigan. La información está dispersa en descripciones de programas, noticias y, fundamentalmente, en memorias anuales, que a menudo se publican en formato PDF, lo que dificulta la extracción automática.41
Para resolver este problema, se requiere un proceso semi-automatizado en varias etapas:
Paso 1 (Extracción de Grupos y PIs): Realizar una extracción de datos (scraping) del sitio web del CIBERER y un análisis de texto (parsing) de las memorias anuales más recientes para compilar una base de datos maestra de todos los grupos de investigación del CIBERER, sus investigadores principales (IPs) y sus instituciones de adscripción.4
Paso 2 (Consulta de Publicaciones): Para cada IP o grupo identificado, ejecutar una consulta automatizada a la API de PubMed para recuperar su historial de publicaciones de los últimos 5-10 años.
Paso 3 (Análisis de Menciones de Enfermedades): Aplicar técnicas de minería de texto para analizar los títulos y resúmenes (abstracts) de las publicaciones recuperadas. El sistema buscará menciones de los nombres de enfermedades raras y sus sinónimos, obtenidos de la lista maestra de Orphanet.
Paso 4 (Puntuación): La puntuación para este criterio será un recuento del número de grupos de investigación distintos del CIBERER que han publicado sobre una enfermedad específica en el período de tiempo definido. Esto crea una medida cuantificable y objetiva de la capacidad de investigación activa y relevante en España.

3. El Algoritmo de Priorización: De Datos Brutos a Lista Clasificada


3.1. Transformación y Normalización de Datos

El primer paso del algoritmo es convertir los datos brutos recopilados para cada criterio en una escala normalizada común, por ejemplo, de 0 a 10. Esto es esencial para poder comparar y ponderar criterios que se miden en unidades completamente diferentes (p. ej., número de pacientes vs. una puntuación binaria).
Datos Binarios (Criterios 3 y 5): La transformación es una simple asignación.
Existencia de Terapias (Criterio 3): No hay terapia aprobada = 10; Hay al menos una terapia = 0.
Trazabilidad para Terapias Avanzadas (Criterio 5): Causa monogénica confirmada = 10; No monogénica o desconocida = 0.
Datos de Recuento (Criterios 1, 4, 6): Estos datos (número de pacientes, de ensayos clínicos, de grupos de investigación) suelen tener una distribución muy sesgada, donde unas pocas enfermedades acumulan la mayoría de los recuentos y la gran mayoría tiene cero o muy pocos. Para manejar esto y evitar que los valores atípicos dominen la puntuación, se puede utilizar una transformación logarítmica o, preferiblemente, una clasificación por percentiles. Por ejemplo, una enfermedad en el percentil 95 para el número de ensayos clínicos recibiría una puntuación de 9.5.
Datos Ordinales por Niveles (Criterio 2): El sistema de puntuación para el impacto socioeconómico ya está definido en una escala ordinal. La transformación consiste en una asignación directa de esos niveles a la escala final (p. ej., Evidencia Alta = 10, Media-Alta = 7, Media = 5, Baja = 3, Sin Evidencia = 0).

3.2. Un Sistema de Ponderación Flexible

Una vez que todos los criterios están en la misma escala normalizada, se les debe asignar un peso que refleje su importancia relativa en la decisión final. Se propondrá un esquema de ponderación de referencia equilibrado (p. ej., todos los criterios con el mismo peso).
Sin embargo, la característica más potente del sistema debe ser su flexibilidad. La interfaz de usuario debe permitir a los responsables de la toma de decisiones ajustar estos pesos de forma dinámica. Esto transforma la herramienta de un informe estático a un modelo de simulación estratégica. Los usuarios pueden explorar diferentes escenarios de priorización según sus objetivos:
Escenario de "Salud Pública": Se asignaría un mayor peso al Criterio 1 (Prevalencia y Pacientes) y al Criterio 2 (Impacto Socioeconómico).
Escenario de "Innovación en I+D": Se daría más importancia al Criterio 5 (Trazabilidad para Terapias Avanzadas) y al Criterio 6 (Capacidad de Investigación Nacional).
Escenario de "Necesidad Médica Urgente": Se otorgaría el peso predominante al Criterio 3 (Existencia de Terapias Aprobadas).

3.3. Cálculo de la Puntuación Final de Prioridad

La puntuación final para cada enfermedad se calcula mediante una fórmula de suma ponderada estándar. Para cada enfermedad, la puntuación final (Sf​) es la suma de los productos de la puntuación normalizada de cada criterio (Pi​) por su peso correspondiente (Wi​):
Sf​=i=1∑n​(Pi​×Wi​)
Donde n es el número de criterios utilizados. Este cálculo produce una puntuación continua para cada una de las más de 6.000 enfermedades, lo que permite una clasificación completa y sin ambigüedades desde la más prioritaria hasta la menos prioritaria, según la configuración de pesos seleccionada.
A continuación, se presenta una tabla de ejemplo para ilustrar el funcionamiento del algoritmo con un conjunto de enfermedades hipotéticas y datos simulados, utilizando una ponderación de referencia equilibrada.
Tabla 1: Ejemplo de Cálculo de Puntuación y Ponderación

Enfermedad (ORPHAcode)
Criterio 1: Pacientes (España)
Criterio 2: Impacto Socioeconómico
Criterio 3: Terapias Aprobadas
Criterio 4: Ensayos Clínicos (España)
Criterio 5: Trazabilidad Génica
Criterio 6: Grupos CIBERER
Puntuación Final
Rango Final
Ponderación de Referencia
20%
20%
25%
10%
15%
10%




Enfermedad A (177)
P. Norm: 8.5
P. Pond: 1.70
P. Norm: 7.0
P. Pond: 1.40
P. Norm: 0.0
P. Pond: 0.00
P. Norm: 9.0
P. Pond: 0.90
P. Norm: 0.0
P. Pond: 0.00
P. Norm: 8.0
P. Pond: 0.80
4.80
2
Perfil: Alta prevalencia, con terapia existente
(~2.000 pac.)
(Estudio europeo)
(Sí, 3)
(5 ensayos)
(No monogénica)
(4 grupos)




Enfermedad B (308)
P. Norm: 2.0
P. Pond: 0.40
P. Norm: 10.0
P. Pond: 2.00
P. Norm: 10.0
P. Pond: 2.50
P. Norm: 1.0
P. Pond: 0.10
P. Norm: 10.0
P. Pond: 1.50
P. Norm: 3.0
P. Pond: 0.30
6.80
1
Perfil: Ultra-rara, sin terapia, monogénica
(~50 pac.)
(Estudio español)
(No)
(0 ensayos)
(Sí)
(1 grupo)




Enfermedad C (558)
P. Norm: 5.0
P. Pond: 1.00
P. Norm: 3.0
P. Pond: 0.60
P. Norm: 10.0
P. Pond: 2.50
P. Norm: 1.0
P. Pond: 0.10
P. Norm: 0.0
P. Pond: 0.00
P. Norm: 0.0
P. Pond: 0.00
4.20
3
Perfil: Prevalencia media, sin terapia, sin datos de investigación
(~500 pac.)
(Info cualitativa)
(No)
(0 ensayos)
(No monogénica)
(0 grupos)





Nota: Los datos y puntuaciones son ilustrativos para demostrar el mecanismo de cálculo.

Parte II: Protocolo Técnico para la Implementación Automatizada

Esta sección constituye el manual de instrucciones técnicas para el equipo de desarrollo de cursor.com. Proporciona una guía detallada y explícita para la adquisición de datos, el procesamiento y la arquitectura del sistema.
La siguiente matriz de datos es el elemento central de este protocolo. Funciona como el plano maestro para el desarrollo, centralizando toda la lógica de adquisición de datos y traduciendo los criterios estratégicos de la Parte I en requisitos técnicos concretos.
Tabla 2: Matriz de Fuentes y Adquisición de Datos
Criterio Estratégico
Punto de Dato Específico
Fuente Primaria
Método de Acceso
Endpoint / URL / Consulta Específica
Campos Clave a Extraer
Notas / Desafíos
Fundacional
Lista maestra de EERR en español
Orphadata
REST API
GET https://api.orphacode.org/es/ClinicalEntity 44
ORPHAcode, Name.label, SynonymList
Requiere registro de usuario gratuito para la API.
1. Pacientes
Prevalencia Europea
Orphadata
Descarga XML
https://www.orphadata.com/epidemiology/ (fichero es_product9_prev.xml) 8
Disorder/OrphaNumber, Prevalence/PrevalenceClass
El fichero se actualiza periódicamente. El script debe manejar la descarga y el parseo de XML.
1. Pacientes
N.º Pacientes Oficial en España
ISCIII
Petición Formal
Correo electrónico a registro.raras@isciii.es 10
N/A (entrada manual)
Proceso no automatizable. Requiere interfaz para entrada manual de datos.
2. Impacto
Estudios de coste de la enfermedad
PubMed
REST API
Búsqueda: (DiseaseName OR Synonyms) AND ("cost of illness" OR "economic burden") AND Spain
PMID, Title, Abstract
Requiere API key de NCBI. Los resultados necesitan revisión manual para confirmar relevancia.
2. Impacto
Informes de carga socioeconómica
FEDER
Web Scraping
Búsqueda del nombre de la enfermedad en https://www.enfermedades-raras.org/ 15
Presencia/ausencia de informes relevantes
La estructura del sitio web puede cambiar. El scraper debe ser robusto.
3. Terapias
Fármacos aprobados en UE
Orphanet / EURORDIS
Web Scraping
Scrapear tablas en 25 y 26
Medicinal Product, Indication
Las tablas HTML son relativamente estables pero pueden cambiar.
3. Terapias
Confirmación autorización en España
AEMPS CIMA
Web Scraping
Búsqueda por nombre de fármaco en https://cima.aemps.gob.es/ 28
Estado de comercialización
No hay API. La búsqueda por indicación no es posible.30 Requiere un scraper que simule la búsqueda por nombre.
4. Ensayos
Ensayos clínicos en España
ClinicalTrials.gov
REST API
GET /api/v2/studies?query.term=&query.locn=Spain&filter.overallStatus=... 32
NCTId, officialTitle, overallStatus
API v2.0 es moderna y bien documentada.
4. Ensayos
Ensayos clínicos en España
EU CTIS
Web Scraping
Búsqueda avanzada en https://euclinicaltrials.eu/ 33
EU CT Number, Trial status, Medical condition
No hay API pública documentada. Requiere scraper para el portal de búsqueda avanzada.
5. Trazabilidad
Mapeo ORPHAcode a OMIM
Orphadata
REST API / XML
GET /{lang}/ClinicalEntity/orphacode/{orphacode} 44 o
product1.xml 46
ExternalReference donde Source="OMIM"
Método fiable y bien estructurado.
5. Trazabilidad
Determinación de causa monogénica
OMIM
REST API
GET api.omim.org/api/entry?mimNumber= 36
mimNumber, entryType, geneMap
Requiere API key de OMIM.39 Parsear la respuesta JSON para identificar la etiología.
6. Capacidad
Lista de grupos y PIs del CIBERER
CIBERER
Web Scraping / PDF Parsing
Scrapear https://www.ciberer.es/ y memorias anuales en PDF 4
Nombre del Grupo, Nombre del IP
Tarea compleja. Los PDFs requieren OCR y parsing de texto. Se recomienda una actualización anual.
6. Capacidad
Vínculo Grupo-Enfermedad
PubMed
REST API
Búsqueda: (DiseaseName) AND (PI_Name1[Author] OR PI_Name2[Author]...)
PMID
Contar el número de PIs únicos con publicaciones sobre la enfermedad.


4. El Flujo de Trabajo de Adquisición y Procesamiento de Datos

A continuación se detalla el flujo de trabajo paso a paso para poblar la base de datos del sistema.

4.1. Paso 1: Establecer la Lista Maestra de Enfermedades (Orphanet)

El primer paso es construir la tabla fundamental que contendrá todas las enfermedades raras. Esta será la espina dorsal del sistema.
Acción: Realizar una llamada a la API de Orphadata.
Endpoint: GET https://api.orphacode.org/es/ClinicalEntity.44
Datos a extraer: Para cada entidad, obtener el ORPHAcode (identificador único), el Name.label (término preferente en español) y la lista de sinónimos (SynonymList).
Resultado: Crear y poblar una tabla en la base de datos, por ejemplo Diseases, con los campos ORPHAcode (clave primaria), Name, y Synonyms.

4.2. Paso 2: Recopilar Datos Epidemiológicos (Orphanet e ISCIII)

Este paso se divide en una acción automatizada y un proceso que requiere intervención manual.
Acción A (Automatizada): Desarrollar un script que descargue y analice (parse) el archivo XML de datos epidemiológicos (es_product9_prev.xml) desde el portal de Orphadata.8 Para cada
OrphaNumber en el archivo, extraer el valor de PrevalenceClass (p. ej., "1-9 / 1 000 000"). Utilizar este rango para calcular una estimación de pacientes en España.
Acción B (Manual/Semi-automatizada): El sistema debe contar con una interfaz de administración donde un usuario autorizado pueda introducir el número oficial de pacientes para una enfermedad específica, una vez que esta información haya sido obtenida del ISCIII mediante una solicitud formal.2
Resultado: Añadir a la tabla Diseases las columnas PrevalenceRange_Orphanet, PatientCount_Estimated y PatientCount_Official_ISCIII. La lógica del sistema debe priorizar el uso del dato oficial si está disponible.

4.3. Paso 3: Evaluar el Impacto Socioeconómico (PubMed y FEDER)

Este paso utiliza minería de texto y web scraping para asignar una puntuación de impacto.
Acción: Para cada enfermedad en la tabla Diseases, el sistema debe:
Construir y ejecutar una consulta a la API de PubMed: (NombreEnfermedad OR Sinónimos) AND ("cost of illness" OR "economic burden" OR "carga económica") AND Spain.
Si se obtienen resultados, se marcan para una revisión manual rápida que confirme su relevancia y asigne la puntuación correspondiente (10 o 7).
Si no hay resultados, se realiza una búsqueda más amplia sin el término "Spain".
Paralelamente, un scraper buscará el nombre de la enfermedad en la sección de publicaciones e informes del sitio web de FEDER.15 La presencia de un informe relevante asignará una puntuación de nivel medio o bajo (5 o 3).
Resultado: Poblar la columna SocioEconomicImpact_Score en la tabla Diseases.

4.4. Paso 4: Mapear el Panorama Terapéutico (EMA, AEMPS, Orphanet)

Este proceso de dos fases determina la existencia de tratamientos aprobados.
Acción A: Desarrollar un scraper que extraiga de las listas de medicamentos huérfanos de Orphanet y EURORDIS la relación entre el nombre de la enfermedad y los nombres comerciales de los medicamentos aprobados en la UE.25
Acción B: Por cada nombre comercial de medicamento encontrado, el sistema debe realizar una búsqueda en el sitio web de CIMA de la AEMPS para verificar su estado de autorización y comercialización en España.28
Resultado: Actualizar la columna binaria HasApprovedTherapy_Spain en la tabla Diseases.

4.5. Paso 5: Consultar el Pipeline de Desarrollo Clínico (ClinicalTrials.gov y EU CTIS)

Se consultarán los dos registros de ensayos clínicos más importantes.
Acción: Para cada enfermedad, construir y ejecutar las siguientes consultas:
ClinicalTrials.gov API: https://clinicaltrials.gov/api/v2/studies?query.term=&query.locn=Spain&filter.overallStatus=RECRUITING,ACTIVE_NOT_RECRUITING.32
EU CTIS: Dado que no hay una API pública bien definida, se debe desarrollar un scraper que utilice el portal de búsqueda avanzada para filtrar por Condition=[NombreEnfermedad], Country=Spain y Status=Ongoing.33
Resultado: Sumar los resultados de ambas fuentes y poblar la columna ClinicalTrials_Spain_Count en la tabla Diseases.

4.6. Paso 6: Determinar el Potencial para Terapias Avanzadas (Orphanet y OMIM)

Este flujo de trabajo vincula Orphanet con OMIM para evaluar la base genética.
Acción A: Para cada ORPHAcode, consultar la API de Orphadata para obtener la referencia externa (ExternalReference) correspondiente a OMIM.37
Acción B: Utilizar el ID de OMIM recuperado para realizar una llamada a la API de OMIM.36
Acción C: Analizar (parsear) la respuesta JSON de la API de OMIM para verificar si la entrada corresponde a un gen con una relación fenotípica conocida, lo que indica una causa monogénica.
Resultado: Actualizar la columna binaria IsMonogenic en la tabla Diseases.

4.7. Paso 7: Cuantificar la Capacidad de Investigación Nacional (CIBERER y PubMed)

Este es el paso más complejo y combina scraping, parsing de PDF y consultas a API.
Acción A (Extracción de Grupos): Es una tarea que se ejecutará con menor frecuencia (p. ej., anualmente). Consiste en scrapear el sitio web del CIBERER y analizar sus memorias anuales en PDF para crear una base de datos de los grupos de investigación y sus IPs.4
Acción B (Vinculación Automatizada): Para cada enfermedad de la lista, el sistema construirá una consulta a la API de PubMed que combine el nombre de la enfermedad con los nombres de todos los IPs del CIBERER en el campo de autor. Por ejemplo: (NombreEnfermedad) AND (Lapunzina P[Author] OR Perez-Jurado L[Author]... ).
Resultado: Contar el número de IPs únicos que aparecen en los resultados de la búsqueda y poblar la columna CIBERER_Groups_Count en la tabla Diseases.

