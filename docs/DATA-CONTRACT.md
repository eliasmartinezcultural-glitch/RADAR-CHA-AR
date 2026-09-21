# RADAR — Contrato Universal de Datos

## Ley de procedencia profesional

RADAR no incorpora indicadores porque una tarjeta visual los necesite.

Un indicador solo puede existir cuando se puede responder, antes de programarlo:

1. Qué fenómeno mide.
2. Qué organismo o fuente profesional es competente para producir ese dato.
3. Qué unidad utiliza.
4. Qué territorio representa.
5. Qué reloj representa: observado, medido, programado, pronosticado o publicado.
6. Qué parser/adaptador lo transforma.
7. Qué validaciones impiden publicar datos mal interpretados.
8. Qué vocabulario semántico propio utiliza.
9. Qué fuente secundaria puede complementar y qué fuente NO puede sustituir a la primaria.
10. Qué ocurre si la fuente no responde o no publica un valor: se conserva la ausencia del dato, nunca se fabrica un estado.

## Prohibiciones

No usar como estado universal:
- normal
- sin novedad
- habilitado
- cerrado
- sin parte
- activo
- inactivo

Esas palabras solo pueden aparecer si forman parte del vocabulario propio y explícito del fenómeno.

Ejemplos:
- Viento: km/h, ráfagas, dirección, período de pronóstico.
- Ruta: reducción de calzada, corte intermitente, corte total, obra, desvío, restricción, etc., solo si la autoridad vial lo publica.
- Agua: interrupción, baja presión, reparación, restablecimiento, etc.
- Electricidad: corte programado, mantenimiento, sectores afectados, inicio, restitución.
- Caudal: m³/s y fecha; diferenciar programado de medido.
- Temperatura: °C y período; diferenciar pronóstico de observación.
- Riesgo de incendio: índice/clase oficial y vigencia; no inferirlo solo por viento o temperatura.

## Cadena obligatoria

Fuente profesional → adaptador/parser específico → validación → normalización → timestamp/periodo → semántica propia → procedencia → RADAR

Nunca:

noticia → tarjeta → estado

## Jerarquía

Primaria: organismo competente que produce o publica el dato.

Secundaria: organismo técnico complementario o sistema oficial relacionado.

Respaldo: solo si está expresamente permitido por el contrato y se etiqueta como tal.

Una fuente secundaria no puede rellenar silenciosamente un dato que la primaria no publicó.

## Fuentes actualmente contratadas

- Rutas Provinciales 7 y 8 → Dirección Provincial de Vialidad del Neuquén.
- Viento y temperatura de pronóstico local → AIC, pronóstico de El Chañar.
- Caudales programados → AIC, Caudales Programados.
- Energía → EPEN.
- Agua → EPAS.
- Salud → Ministerio de Salud de Neuquén / Hospital Dra. Alicia Cruz.
- Educación → CPE Neuquén.
- Producción → Ministerio de Producción e Industria.
- Emergencias → Secretaría de Emergencias y Gestión de Riesgos / organismo operativo competente.
- Territorio municipal → Municipalidad, solo para hechos bajo competencia municipal.
- Conversación → medios locales identificables; no es fuente técnica.

## Indicadores reservados

Pueden investigarse sin publicarse automáticamente:

- Calidad del aire: existe una red provincial en desarrollo; antes de publicar Chañar debe verificarse que la estación local esté operativa y que exista lectura accesible con timestamp.
- Nivel de río: AIC dispone de estación COMPENSADOR EL CHANAR; requiere adaptador específico.
- Caudal observado: AIC dispone de medición de caudal medio diario en la estación; debe separarse del caudal programado.
- Estado del tránsito: la fuente depende del corredor y jurisdicción.
- Riesgo de incendio: SMN publica el Índice de Peligro de Incendios FWI; requiere adaptador territorial específico antes de mostrarlo.

## Regla de incorporación futura

Si mañana alguien propone: "Agreguemos calidad del aire."

La primera tarea NO es programar la tarjeta.

La primera tarea es completar el contrato:

organismo → estación → endpoint → unidad → cobertura → timestamp → parser → validación → vocabulario → fallback → auditoría.

Si uno de esos eslabones críticos falta, el indicador queda RESERVADO, no publicado.

## Control automático

update-radar.py ejecuta una auditoría obligatoria de los contratos antes de escribir data/radar-feed.json.

El build falla si falta alguno de los campos críticos del contrato o de la especificación técnica del adaptador.

Versión contractual actual: RADAR-DATA-CONTRACT-2.0.