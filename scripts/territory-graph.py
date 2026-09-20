import json
import re
from datetime import datetime, timezone

FEED = "data/radar-feed.json"

# PULSO CHAÑAR — grafo territorial curado.
# Regla: un vínculo solo nace cuando un evento trae evidencia textual del nodo.
# No se inventan relaciones geográficas por cercanía ni por conocimiento general.
# Las relaciones persistidas sirven al motor; la interfaz pública solo muestra una
# pequeña etiqueta territorial para no convertir RADAR en un mapa interactivo.

NODES = [
 {"id":"spc","label":"San Patricio del Chañar","type":"LOCALIDAD","level":"localidad","aliases":["san patricio del chañar","san patricio del chanar","el chañar","el chanar"]},
 {"id":"rio-neuquen","label":"Río Neuquén","type":"AMBIENTE","level":"microregion","aliases":["río neuquén","rio neuquen"]},
 {"id":"ruta-7","label":"Ruta 7","type":"CORREDOR","level":"corredor","aliases":["ruta 7","ruta provincial 7"]},
 {"id":"ruta-8","label":"Ruta 8","type":"CORREDOR","level":"corredor","aliases":["ruta 8","ruta provincial 8"]},
 {"id":"picada-1","label":"Picada 1","type":"PICADA","level":"microzona","aliases":["picada 1","picada n° 1","picada n.º 1"]},
 {"id":"picada-3","label":"Picada 3","type":"PICADA","level":"microzona","aliases":["picada 3","picada n° 3","picada n.º 3"]},
 {"id":"picada-4","label":"Picada 4","type":"PICADA","level":"microzona","aliases":["picada 4","picada n° 4","picada n.º 4"]},
 {"id":"picada-5","label":"Picada 5","type":"PICADA","level":"microzona","aliases":["picada 5","picada n° 5","picada n.º 5"]},
 {"id":"picada-9","label":"Picada 9","type":"PICADA","level":"microzona","aliases":["picada 9","picada n° 9","picada n.º 9"]},
 {"id":"picada-10","label":"Picada 10","type":"PICADA","level":"microzona","aliases":["picada 10","picada n° 10","picada n.º 10"]},
 {"id":"picada-11","label":"Picada 11","type":"PICADA","level":"microzona","aliases":["picada 11","picada n° 11","picada n.º 11"]},
 {"id":"picada-19","label":"Picada 19","type":"PICADA","level":"microzona","aliases":["picada 19","picada n° 19","picada n.º 19"]},
 {"id":"picada-20","label":"Picada 20","type":"PICADA","level":"microzona","aliases":["picada 20","picada n° 20","picada n.º 20"]},
 {"id":"sector-bodegas","label":"Sector bodegas","type":"SECTOR","level":"sector","aliases":["sector bodegas","bodegas"]},
 {"id":"parque-industrial","label":"Parque Industrial","type":"SECTOR","level":"sector","aliases":["parque industrial"]},
 {"id":"costa-verde","label":"Barrio Costa Verde","type":"BARRIO","level":"barrio","aliases":["costa verde","barrio costa verde"]},
 {"id":"128-viviendas","label":"128 Viviendas","type":"BARRIO","level":"barrio","aliases":["128 viviendas","128 vivienda"]},
 {"id":"union-fuerza","label":"Unión y Fuerza","type":"BARRIO","level":"barrio","aliases":["unión y fuerza","union y fuerza"]},
 {"id":"76-viviendas","label":"76 Viviendas","type":"BARRIO","level":"barrio","aliases":["76 viviendas"]},
 {"id":"50-viviendas","label":"50 Viviendas","type":"BARRIO","level":"barrio","aliases":["50 viviendas"]},
 {"id":"plan-federalismo","label":"Plan Federalismo","type":"BARRIO","level":"barrio","aliases":["plan federalismo"]},
 {"id":"primeros-pobladores","label":"Primeros Pobladores","type":"BARRIO","level":"barrio","aliases":["primeros pobladores"]},
 {"id":"suyai","label":"Suyai","type":"BARRIO","level":"barrio","aliases":["suyai"]},
 {"id":"obrero","label":"Obrero","type":"BARRIO","level":"barrio","aliases":["barrio obrero","obrero"]},
 {"id":"jardin","label":"Jardín","type":"BARRIO","level":"barrio","aliases":["barrio jardín","barrio jardin","jardín","jardin"]},
 {"id":"12-octubre","label":"12 de Octubre","type":"BARRIO","level":"barrio","aliases":["12 de octubre"]},
 {"id":"25-abril","label":"25 de Abril","type":"BARRIO","level":"barrio","aliases":["25 de abril"]},
 {"id":"loteo-social","label":"Loteo Social","type":"SECTOR","level":"sector","aliases":["loteo social"]},
 {"id":"hospital-alicia-cruz","label":"Hospital Dra. Alicia Cruz","type":"INSTITUCIÓN","level":"institucion","aliases":["hospital dra alicia cruz","hospital alicia cruz","hospital san patricio del chañar","hospital local"]},
 {"id":"centro-salud-19","label":"Centro de Salud · Picada 19","type":"INSTITUCIÓN","level":"institucion","aliases":["centro de salud picada 19","centro de salud"]},
 {"id":"cpem-31","label":"CPEM 31","type":"INSTITUCIÓN","level":"institucion","aliases":["cpem 31","cpem n° 31","cpem n.º 31"]},
 {"id":"epet-26","label":"EPET 26","type":"INSTITUCIÓN","level":"institucion","aliases":["epet 26","epet n° 26","epet n.º 26"]},
 {"id":"escuela-273","label":"Escuela Primaria 273","type":"INSTITUCIÓN","level":"institucion","aliases":["escuela primaria 273","escuela 273"]},
 {"id":"comisaria-13","label":"Comisaría 13","type":"INSTITUCIÓN","level":"institucion","aliases":["comisaria 13","comisaría 13"]},
 {"id":"municipalidad","label":"Municipalidad de San Patricio del Chañar","type":"INSTITUCIÓN","level":"institucion","aliases":["municipalidad de san patricio","municipalidad de san patricio del chañar"]},
 {"id":"epen","label":"EPEN","type":"SERVICIO","level":"servicio","aliases":["epen","ente provincial de energía"]},
 {"id":"bodegas","label":"Bodegas y viñedos","type":"PRODUCCIÓN","level":"produccion","aliases":["bodega","bodegas","viñedo","viñedos","chacra","chacras"]},
 {"id":"educacion","label":"Educación","type":"ÁREA","level":"area","aliases":["educación","educacion","escuela","escuelas","docente","clases"]},
 {"id":"salud","label":"Salud","type":"ÁREA","level":"area","aliases":["salud","hospital","enfermería","enfermeria","insumos"]},
 {"id":"servicios","label":"Servicios","type":"ÁREA","level":"area","aliases":["servicio","servicios","electricidad","luz","agua","gas","cloaca"]},
 {"id":"produccion","label":"Producción","type":"ÁREA","level":"area","aliases":["producción","produccion","productores","agro"]},
]

# Relaciones estructurales conocidas, usadas solo como contexto de navegación interna.
# Las relaciones evento→nodo siempre exigen evidencia textual.
STRUCTURAL = [
 ("picada-3","costa-verde","UBICA"),
 ("picada-4","ruta-7","CONECTA"),
 ("picada-5","ruta-7","CONECTA"),
 ("picada-9","ruta-7","CONECTA"),
 ("picada-10","ruta-7","CONECTA"),
 ("picada-11","ruta-7","CONECTA"),
 ("picada-19","ruta-7","CONECTA"),
 ("picada-20","ruta-7","CONECTA"),
 ("hospital-alicia-cruz","salud","PERTENECE_A"),
 ("cpem-31","educacion","PERTENECE_A"),
 ("epet-26","educacion","PERTENECE_A"),
 ("escuela-273","educacion","PERTENECE_A"),
 ("bodegas","produccion","PERTENECE_A"),
 ("epen","servicios","PERTENECE_A"),
 ("parque-industrial","produccion","RELACIONA"),
 ("sector-bodegas","bodegas","RELACIONA"),
 ("spc","rio-neuquen","TERRITORIO"),
 ("spc","ruta-7","TERRITORIO"),
 ("spc","ruta-8","TERRITORIO"),
]

def norm(s):
    return re.sub(r"[^a-z0-9ñ ]+"," ",(s or "").lower().translate(str.maketrans("áéíóúü","aeiouu")))

def hits_for_event(event):
    text=norm(" ".join([event.get("title",""),event.get("topic","")," ".join(event.get("territorialAnchors",[]))]))
    hits=[]
    for n in NODES:
        for alias in n["aliases"]:
            if norm(alias) in text:
                hits.append(n)
                break
    # La localidad es el ancla raíz de RADAR cuando el evento ya fue aceptado como local.
    if event.get("relevance",0)>=2 and not any(n["id"]=="spc" for n in hits):
        hits.insert(0,next(n for n in NODES if n["id"]=="spc"))
    unique={n["id"]:n for n in hits}
    return list(unique.values())

def relationship_label(a,b):
    if a["type"]=="PICADA" and b["type"]=="CORREDOR": return "CONECTA"
    if a["type"]=="BARRIO" and b["type"]=="PICADA": return "SECTOR"
    if a["type"]=="INSTITUCIÓN" and b["type"]=="BARRIO": return "SECTOR"
    if a["type"]=="INSTITUCIÓN" and b["type"]=="ÁREA": return "ÁREA"
    if a["type"]=="PRODUCCIÓN" and b["type"]=="ÁREA": return "ÁREA"
    return "RELACIONA"

def build():
    with open(FEED,encoding="utf-8") as f:
        data=json.load(f)
    events=data.get("events",[])
    event_nodes={}
    edge_counts={}
    node_counts={n["id"]:0 for n in NODES}
    node_map={n["id"]:n for n in NODES}

    for e in events:
        nodes=hits_for_event(e)
        ids=[n["id"] for n in nodes]
        event_nodes[e.get("eventId","")]=ids
        for nid in ids: node_counts[nid]+=1
        graph_nodes=[n for n in nodes if n["id"]!="spc"]
        for i,a in enumerate(graph_nodes):
            for b in graph_nodes[i+1:]:
                key=tuple(sorted((a["id"],b["id"])))
                edge_counts[key]=edge_counts.get(key,0)+1

    edges=[]
    for a,b in STRUCTURAL:
        if a in node_map and b in node_map:
            edges.append({"from":a,"to":b,"relation":"ESTRUCTURAL","evidence":"registro territorial curado"})
    for (a,b),count in sorted(edge_counts.items(),key=lambda x:x[1],reverse=True):
        if count<1: continue
        na,nb=node_map[a],node_map[b]
        edges.append({"from":a,"to":b,"relation":relationship_label(na,nb),"eventCount":count,"evidence":"coocurrencia textual en eventos"})

    for e in events:
        ids=event_nodes.get(e.get("eventId",""),[])
        labels=[node_map[x]["label"] for x in ids if x in node_map]
        micro=[node_map[x]["label"] for x in ids if node_map[x]["level"]=="microzona"]
        sectors=[node_map[x]["label"] for x in ids if node_map[x]["level"] in {"sector","barrio"}]
        corridors=[node_map[x]["label"] for x in ids if node_map[x]["level"]=="corredor"]
        institutions=[node_map[x]["label"] for x in ids if node_map[x]["level"]=="institucion"]
        areas=[node_map[x]["label"] for x in ids if node_map[x]["level"]=="area"]
        e["territory"]={
            "primary":"San Patricio del Chañar",
            "nodes":labels[:10],
            "microzones":micro[:6],
            "sectors":sectors[:8],
            "corridors":corridors[:4],
            "institutions":institutions[:6],
            "areas":areas[:4],
            "path":" → ".join((["San Patricio del Chañar"]+micro[:2]+corridors[:1]+areas[:1]))[:220]
        }
        e["territorialAnchors"]=list(dict.fromkeys((e.get("territorialAnchors") or [])+[x.lower() for x in labels]))[:10]

    active_nodes=[]
    for n in NODES:
        active_nodes.append({**n,"eventCount":node_counts[n["id"]]})
    data["territorialGraph"]={
        "version":"1.1",
        "generatedAt":datetime.now(timezone.utc).isoformat(),
        "root":"spc",
        "rule":"evidence-first",
        "levels":["microzona","barrio","sector","corredor","institucion","servicio","produccion","area","microregion"],
        "nodes":active_nodes,
        "edges":edges[:500],
        "eventNodes":event_nodes,
        "stats":{
            "nodes":len(active_nodes),
            "activeNodes":sum(1 for x in active_nodes if x["eventCount"]),
            "edges":len(edges),
            "eventsLinked":sum(bool(v) for v in event_nodes.values())
        }
    }
    data["system"]["territorialGraph"]="evidence-first v1.1"
    data["system"]["territorialLevels"]="microzona > barrio/sector > corredor > institución/servicio/producción > microregión"
    with open(FEED,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)
    print("Territorial graph:",data["territorialGraph"]["stats"])

if __name__=="__main__":
    build()
