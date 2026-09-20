# RADAR CHAÑAR — CONTRATO DE PRODUCTO

## Misión
**Detectar qué se está moviendo en San Patricio del Chañar y mostrar de dónde surge cada señal.**

La interfaz pública puede ser espectacular y futurista, pero la regla epistemológica no cambia: **evidencia primero**.

## Arquitectura pública
RADAR CHAÑAR funciona como una central multiradar:

1. **Conversación** — qué se está moviendo.
2. **Ruta 7** — señales territoriales asociadas al corredor.
3. **Ruta 8** — señales territoriales asociadas al corredor.
4. **Viento** — dato ambiental directo cuando la fuente está disponible.
5. **Energía** — señales sobre electricidad y cortes.
6. **Agua** — señales sobre abastecimiento, agua y cloacas.
7. **Servicios** — infraestructura y servicios públicos.
8. **Salud**.
9. **Educación**.
10. **Producción**.
11. **Emergencias**.
12. **Territorio** — barrios, sectores, picadas, instituciones y microzonas.

Estos radares no son 12 portales separados. Son **12 lentes sobre un mismo motor territorial**.

## Contrato de fuentes por lectura

Cada radar, sensor, gráfico, reporte o dato operacional debe declarar internamente:

1. **fuente primaria** — la más idónea para ese dato;
2. **fuente secundaria** — corroboración institucional o técnica;
3. **respaldo** — alternativa cuando la primaria no responde;
4. **modo de captura** — API directa, web oficial, fuente institucional, medio local o respaldo comunitario;
5. **frecuencia objetivo** — actualmente 30 minutos para el ciclo del motor;
6. **regla de precedencia** — una fuente de menor jerarquía nunca reemplaza silenciosamente una confirmación directa.

La interfaz pública muestra la **fuente primaria** de cada radar y conserva las demás detrás del dato. Así la página permanece limpia, mientras el motor mantiene trazabilidad completa.

## Regla crítica de datos
Hay tres estados distintos:

- **DATO DIRECTO**: procede de una fuente de datos específica.
- **SEÑAL DETECTADA / SEÑAL RECIENTE**: existe evidencia editorial o territorial.
- **SIN SEÑAL RECIENTE**: el motor no encontró evidencia reciente.

**Nunca interpretar “sin señal” como “no existe el problema”.**

Una noticia sobre un corte de agua no equivale por sí sola a una confirmación operativa del corte. La interfaz debe conservar esa diferencia.

## Infraestructura interna
El motor puede relacionar:

**hecho ↔ institución ↔ picada ↔ barrio ↔ sector ↔ corredor ↔ Ruta 7 ↔ Ruta 8 ↔ producción ↔ educación ↔ servicios ↔ ambiente ↔ microzona ↔ microregión**

Las relaciones territoriales deben estar sustentadas por evidencia textual o por una relación estructural previamente curada.

## Ambiente
Cuando existe fuente directa, el sistema puede incorporar variables ambientales como:

- temperatura;
- viento;
- dirección del viento;
- humedad;
- precipitación.

El dato ambiental debe mostrar su procedencia y momento de observación.

## Memoria
Se conservan:

- identificadores estables;
- primera y última aparición;
- ciclo de vida;
- cobertura;
- diversidad de fuentes;
- nuevas fuentes;
- continuidad de eventos.

## Qué no debe hacer
No convertir RADAR CHAÑAR en:

- portal de noticias;
- red social;
- ranking de importancia;
- sistema de alarma falsa;
- panel administrativo público;
- acumulador de titulares sin deduplicación.

## Actualización continua

El motor se ejecuta automáticamente cada 30 minutos y la interfaz puede volver a consultar el feed sin recargar manualmente la página. La frescura se mide por dato, fuente y radar; si una fuente falla, el sistema conserva memoria y lo declara en lugar de inventar una actualización.

## Principio de diseño
**Más inteligencia detrás. Más claridad delante.**

La espectacularidad visual sirve para hacer visible la infraestructura tecnológica de Ocarina Producciones; no debe reemplazar la trazabilidad de la evidencia.

**Versión de contrato: 2.0 · RADAR CHAÑAR**
