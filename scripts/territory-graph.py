import json
import re
from datetime import datetime, timezone

FEED = "data/radar-feed.json"

# PULSO CHAÑAR — TERRITORIO v2
# Principio: el territorio no se adivina. Cada nodo de un evento debe aparecer
# como evidencia textual en título/descripcion/anchors. Las relaciones
# estructurales sirven para ordenar el conocimiento, no para fabricar hechos.
#
# Fuentes territoriales de referencia:
# - Municipalidad: ejido, RP7/RP8, mirador, espacios y corredores.
# - CFI / Plan de Ordenamiento Territorial: instituciones y microregión.
# - Vialidad Neuquén: RP7/RP8 y tramo Picada 1–11.
# La taxonomía se amplía solo cuando exista evidencia verificable.

NODES = [
 {"id":"spc","label":"San Patricio del Chañar","type":"LOCALIDAD","level":"localidad","aliases":["san patricio del chañar","san patricio del chanar","el chañar","el chanar"]},
 {"id":"rio-neuquen","label":"Río Neuquén","type":"AMBIENTE","level":"microregion","aliases":["río neuquén","rio neuquen"]},
 {"id":"ruta-7","label":"Ruta 7","type":"CORREDOR","level":"corredor","aliases":["ruta 7","ruta provincial 7"]},
 {"id":"ruta-8","label":"Ruta 8","type":"CORREDOR","level":"corredor","aliases":["ruta 8","ruta provincial 8"]},

 # Microzonas / picadas: solo nombres explícitos, nunca inferidos por cercanía.
 {"id":"picada-1","label":"Picada 1","type":"MICROZONA","level":"microzona","aliases":["picada 1","picada n° 1","picada n.º 1"]},
 {"id":"picada-2","label":"Picada 2","type":"MICROZONA","level":"microzona","aliases":["picada 2","picada n° 2","picada n.º 2"]},
 {"id":"picada-3","label":"Picada 3","type":"MICROZONA","level":"microzona","aliases":["picada 3","picada n° 3","picada n.º 3"]},
 {"id":"picada-4","label":"Picada 4","type":"MICROZONA","level":"microzona","aliases":["picada 4","picada n° 4","picada n.º 4"]},
 {"id":"picada-5","label":"Picada 5","type":"MICROZONA","level":"microzona","aliases":["picada 5","picada n° 5","picada n.º 5"]},
 {"id":"picada-6","label":"Picada 6","type":"MICROZONA","level":"microzona","aliases":["picada 6","picada n° 6","picada n.º 6"]},
 {"id":"picada-7","label":"Picada 7","type":"MICROZONA","level":"microzona","aliases":["picada 7","picada n° 7","picada n.º 7"]},
 {"id":"picada-8","label":"Picada 8","type":"MICROZONA","level":"microzona","aliases":["picada 8","picada n° 8","picada n.º 8"]},
 {"id":"picada-9","label":"Picada 9","type":"MICROZONA","level":"microzona","aliases":["picada 9","picada n° 9","picada n.º 9"]},
 {"id":"picada-10","label":"Picada 10","type":"MICROZONA","level":"microzona","aliases":["picada 10","picada n° 10","picada n.º 10"]},
 {"id":"picada-11","label":"Picada 11","type":"MICROZONA","level":"microzona","aliases":["picada 11","picada n° 11","picada n.º 11"]},
 {"id":"picada-19","label":"Picada 19","type":"MICROZONA","level":"microzona","aliases":["picada 19","picada n° 19","picada n.º 19"]},
 {"id":"picada-20","label":"Picada 20","type":"MICROZONA","level":"microzona","aliases":["picada 20","picada n° 20","picada n.º 20"]},

 # Sectores / barrios: matching only when the complete territorial expression appears.
 {"id":"sector-bodegas","label":"Sector bodegas","type":"SECTOR","level":"sector","aliases":["sector bodegas"]},
 {"id":"parque-industrial","label":"Parque Industrial","type":"SECTOR","level":"sector","aliases":["parque industrial"]},
 {"id":"loteo-social","label":"Loteo Social","type":"SECTOR","level":"sector","aliases":["loteo social"]},
 {"id":"costa-verde","label":"Barrio Costa Verde","type":"BARRIO","level":"barrio","aliases":["barrio costa verde","costa verde"]},
 {"id":"128-viviendas","label":"128 Viviendas","type":"BARRIO","level":"barrio","aliases":["128 viviendas"]},
 {"id":"union-fuerza","label":"Unión y Fuerza","type":"BARRIO","level":"barrio","aliases":["barrio unión y fuerza","barrio union y fuerza","unión y fuerza","union y fuerza"]},
 {"id":"76-viviendas","label":"76 Viviendas","type":"BARRIO","level":"barrio","aliases":["76 viviendas"]},
 {"id":"50-viviendas","label":"50 Viviendas","type":"BARRIO","level":"barrio","aliases":["50 viviendas"]},
 {"id":"plan-federalismo","label":"Plan Federalismo","type":"BARRIO","level":"barrio","aliases":["barrio plan federalismo","plan federalismo"]},
 {"id":"primeros-pobladores","label":"Primeros Pobladores","type":"BARRIO","level":"barrio","aliases":["barrio primeros pobladores","primeros pobladores"]},
 {"id":"suyai","label":"Suyai","type":"BARRIO","level":"barrio","aliases":["barrio suyai","suyai"]},
 {"id":"obrero","label":"Barrio Obrero","type":"BARRIO","level":"barrio","aliases":["barrio obrero"]},
 {"id":"jardin","label":"Barrio Jardín","type":"BARRIO","level":"barrio","aliases":["barrio jardín","barrio jardin"]},
 {"id":"12-octubre","label":"12 de Octubre","type":"BARRIO","level":"barrio","aliases":["barrio 12 de octubre","12 de octubre"]},
 {"id":"25-abril","label":"25 de Abril","type":"BARRIO","level":"barrio","aliases":["barrio 25 de abril","25 de abril"]},

 # Instituciones / servicios.
 {"id":"municipalidad","label":"Municipalidad","type":"INSTITUCIÓN","level":"institucion","aliases":["municipalidad de san patricio del chañar","municipalidad de san patricio"]},
 {"id":"hospital-alicia-cruz","label":"Hospital Dra. Alicia Cruz","type":"INSTITUCIÓN","level":"institucion","aliases":["hospital dra alicia cruz","hospital alicia cruz","hospital local"]},
 {"id":"centro-salud-19","label":"Centro de Salud · Picada 19","type":"INSTITUCIÓN","level":"institucion","aliases":["centro de salud picada 19"]},
 {"id":"comisaria-13","label":"Comisaría 13","type":"INSTITUCIÓN","level":"institucion","aliases":["comisaria 13","comisaría 13"]},
 {"id":"cpem-31","label":"CPEM 31","type":"INSTITUCIÓN","level":"institucion","aliases":["cpem 31","cpem n° 31","cpem n.º 31"]},
 {"id":"epet-26","label":"EPET 26","type":"INSTITUCIÓN","level":"institucion","aliases":["epet 26","epet n° 26","epet n.º 26"]},
 {"id":"escuela-273","label":"Escuela Primaria 273","type":"INSTITUCIÓN","level":"institucion","aliases":["escuela primaria 273","escuela 273"]},
 {"id":"epen","label":"EPEN","type":"SERVICIO","level":"servicio","aliases":["epen","ente provincial de energía"]},
 {"id":"bomberos","label":"Bomberos Voluntarios","type":"INSTITUCIÓN","level":"institucion","aliases":["bomberos voluntarios","bomberos de san patricio"]},
 {"id":"correo","label":"Correo Argentino","type":"SERVICIO","level":"servicio","aliases":["correo argentino"]},

 # Nodos productivos / ambientales.
 {"id":"bodegas","label":"Bodegas y viñedos","type":"PRODUCCIÓN","level":"produccion","aliases":["bodega familia schroeder","bodega del fin del mundo","bodega malma","bodegas","viñedo","viñedos","chacra","chacras"]},
 {"id":"balneario","label":"Balneario Municipal","type":"ESPACIO","level":"espacio","aliases":["balneario municipal"]},
 {"id":"mirador-virgen","label":"Mirador La Virgen","type":"ESPACIO","level":"espacio","aliases":["mirador la virgen","virgen del valle"]},
 {"id":"plaza-infancias","label":"Plaza de las Infancias","type":"ESPACIO","level":"espacio","aliases":["plaza de las infancias"]},
]

LEVEL_ORDER=["localidad","microregion","sector","barrio","microzona","institucion","servicio","corredor","espacio","produccion"]

def norm(s):
    return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9ñ ]+"," ",(s or "").lower().translate(str.maketrans("áéíóúü","aeiouu")))).strip()

def event_text(event):
    return norm(" ".join([
        event.get("title",""),
        event.get("description",""),
        event.get("topic",""),
        " ".join(event.get("territorialAnchors",[]))
    ]))

def hits_for_event(event):
    text=event_text(event)
    hits=[]
    for node in NODES:
        if any(norm(alias) in text for alias in node["aliases"]):
            hits.append(node)
    # Un evento aceptado por el filtro local pertenece al root aunque el nombre
    # de la localidad no se repita en el título.
    if event.get("relevance",0)>=2 and not any(n["id"]=="spc" for n in hits):
        hits.insert(0,NODES[0])
    return list({n["id"]:n for n in hits}.values())

def evidence_level(node,event):
    text=event_text(event)
    exact=sum(1 for a in node["aliases"] if norm(a) in text)
    if node["level"]=="localidad" and event.get("relevance",0)>=3: return "DIRECTA"
    if exact>=2: return "FUERTE"
    if exact==1: return "TEXTUAL"
    return "RAÍZ"

def build():
    with open(FEED,encoding="utf-8") as f:
        data=json.load(f)
    events=data.get("events",[])
    node_map={n["id"]:n for n in NODES}
    node_counts={n["id"]:0 for n in NODES}
    edge_counts={}
    event_nodes={}

    for event in events:
        nodes=hits_for_event(event)
        ids=[n["id"] for n in nodes]
        event_nodes[event.get("eventId","")]=ids
        for nid in ids: node_counts[nid]+=1

        # Co-ocurrencia solo dentro del mismo evento. No significa proximidad física.
        for i,a in enumerate(nodes):
            for b in nodes[i+1:]:
                key=tuple(sorted((a["id"],b["id"])))
                edge_counts[key]=edge_counts.get(key,0)+1

        micro=[n["label"] for n in nodes if n["level"]=="microzona"]
        barrios=[n["label"] for n in nodes if n["level"]=="barrio"]
        sectors=[n["label"] for n in nodes if n["level"]=="sector"]
        corridors=[n["label"] for n in nodes if n["level"]=="corredor"]
        institutions=[n["label"] for n in nodes if n["level"]=="institucion"]
        services=[n["label"] for n in nodes if n["level"]=="servicio"]
        spaces=[n["label"] for n in nodes if n["level"]=="espacio"]
        production=[n["label"] for n in nodes if n["level"]=="produccion"]

        # Ruta de lectura, no ruta geográfica.
        path=["San Patricio del Chañar"]
        path += sectors[:1] + barrios[:1] + micro[:1] + corridors[:1] + institutions[:1] + spaces[:1] + production[:1]
        path=list(dict.fromkeys(path))
        event["territory"]={
            "version":"2.0",
            "primary":"San Patricio del Chañar",
            "nodes":[n["label"] for n in nodes][:12],
            "sectors":sectors[:6],
            "barrios":barrios[:6],
            "microzones":micro[:8],
            "corridors":corridors[:4],
            "institutions":institutions[:8],
            "services":services[:5],
            "spaces":spaces[:5],
            "production":production[:5],
            "path":" → ".join(path)[:260],
            "evidence":[
                {"node":n["label"],"level":n["level"],"evidence":evidence_level(n,event)}
                for n in nodes[:12]
            ]
        }

    edges=[]
    for (a,b),count in sorted(edge_counts.items(),key=lambda x:(-x[1],x[0])):
        if count<1: continue
        edges.append({
            "from":a,"to":b,
            "relation":"COOCURRENCIA_TEXTUAL",
            "eventCount":count,
            "evidence":"menciones de ambos nodos dentro del mismo hecho"
        })

    active_nodes=[{**n,"eventCount":node_counts[n["id"]]} for n in NODES]
    level_stats={}
    for n in active_nodes:
        level_stats[n["level"]]=level_stats.get(n["level"],0)+(1 if n["eventCount"] else 0)

    events_with_micro=sum(bool(e.get("territory",{}).get("microzones")) for e in events)
    events_with_barrio=sum(bool(e.get("territory",{}).get("barrios")) for e in events)
    events_with_sector=sum(bool(e.get("territory",{}).get("sectors")) for e in events)

    data["territorialGraph"]={
        "version":"2.0",
        "generatedAt":datetime.now(timezone.utc).isoformat(),
        "root":"spc",
        "rule":"evidence-first",
        "levels":LEVEL_ORDER,
        "nodes":active_nodes,
        "edges":edges[:700],
        "eventNodes":event_nodes,
        "taxonomy":{
            "localidad":"San Patricio del Chañar",
            "sector":"zona territorial amplia con evidencia explícita",
            "barrio":"barrio nombrado explícitamente",
            "institucion":"institución/servicio identificable",
            "corredor":"ruta o eje vial explícito",
            "microzona":"picada o microespacio nombrado",
            "espacio":"espacio público identificable",
            "produccion":"nodo productivo nombrado",
            "microregion":"relación territorial mayor; no implica que el hecho sea local"
        },
        "stats":{
            "nodes":len(active_nodes),
            "activeNodes":sum(1 for n in active_nodes if n["eventCount"]),
            "edges":len(edges),
            "eventsLinked":sum(bool(v) for v in event_nodes.values()),
            "eventsWithMicrozones":events_with_micro,
            "eventsWithBarrios":events_with_barrio,
            "eventsWithSectors":events_with_sector,
            "levelActivity":level_stats
        }
    }
    data["system"]["territorialGraph"]="evidence-first v2.0"
    data["system"]["territorialTaxonomy"]="localidad > sector > barrio > institucion/servicio > corredor > microzona > espacio/produccion"
    data["system"]["territorialRule"]="no inferir proximidad; solo evidencia textual"
    with open(FEED,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    print("Territorial graph v2:",data["territorialGraph"]["stats"])

if __name__=="__main__":
    build()
