# RADAR CHAÑAR — CONTRATO DE PRODUCTO

## Misión bloqueada
RADAR tiene una sola función pública:

**¿De qué se está hablando cuando se habla de San Patricio del Chañar?**

## Interfaz bloqueada
La experiencia pública se mantiene en tres apartados:

1. **Pulso territorial** — estado general de la conversación detectada.
2. **Qué se está moviendo** — eventos territoriales agrupados, no una lista plana de noticias.
3. **De dónde viene** — fuentes y evidencia original.

## Inteligencia territorial interna
El motor puede crecer sin multiplicar la interfaz. El grafo interno trabaja con:

**hecho ↔ institución ↔ picada ↔ barrio ↔ sector ↔ corredor ↔ Ruta 7/Ruta 8 ↔ producción ↔ educación ↔ servicios ↔ río ↔ microregión**

Capas internas:

- **LOCALIDAD**: San Patricio del Chañar como raíz.
- **MICROZONA**: picadas y sectores rurales.
- **BARRIO**: unidades barriales identificables.
- **SECTOR**: Parque Industrial, sector bodegas, Loteo Social y otros sectores curados.
- **CORREDOR**: Ruta 7 y Ruta 8.
- **INSTITUCIÓN**: escuelas, hospital, policía, municipio, etc.
- **SERVICIO**: infraestructura/servicios públicos.
- **PRODUCCIÓN**: chacras, viñedos, bodegas.
- **ÁREA**: salud, educación, servicios, producción.
- **MICROREGIÓN**: relaciones territoriales de escala superior.

### Regla de oro del grafo
**Evidencia primero.**

Un evento se vincula a un nodo cuando el texto del evento contiene una evidencia territorial identificable. No se inventan relaciones por proximidad, intuición ni por conocimiento general.

Las relaciones estructurales conocidas se mantienen separadas de las relaciones obtenidas por coocurrencia textual.

## Memoria
Se conservan identificadores estables, primera/última aparición, ciclo de vida, variación de movimiento y nuevas fuentes.

## Compartibilidad
RADAR debe poder circular como una pieza editorial simple:

- título social claro;
- imagen de presentación;
- descripción corta;
- URL canónica;
- botón de compartir nativo cuando exista;
- fallback de copia para WhatsApp/redes;
- ninguna cuenta ni instalación para observar el radar.

La compartibilidad es una capa de distribución, no una nueva función pública del radar.

## No agregar
No agregar:

- buscador público;
- filtros múltiples;
- rankings;
- comentarios;
- perfiles;
- red social interna;
- panel administrativo público;
- mapa interactivo obligatorio;
- funciones que conviertan RADAR en portal de noticias.

**Regla central: más inteligencia detrás, menos cosas delante.**

**Versión de contrato: 0.7**
