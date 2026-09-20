import json
from datetime import datetime, timezone

FEED="data/radar-feed.json"

LOCAL_EXACT=[
    "san patricio del chañar","san patricio del chanar","el chañar","el chanar",
    "hospital dra alicia cruz","cpem 31","epet 26","escuela primaria 273",
    "comisaria 13","municipalidad de san patricio","parque industrial",
    "picada 1","picada 2","picada 3","picada 4","picada 5","picada 6",
    "picada 7","picada 8","picada 9","picada 10","picada 11","picada 19","picada 20",
    "barrio costa verde","128 viviendas","unión y fuerza","union y fuerza",
    "76 viviendas","50 viviendas","plan federalismo","primeros pobladores",
    "barrio suyai","barrio obrero","barrio jardín","barrio jardin",
    "12 de octubre","25 de abril","loteo social","ruta 7","ruta 8"
]

def norm(s):
    return " ".join((s or "").lower().replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ü","u").split())

with open(FEED,encoding="utf-8") as f:
    data=json.load(f)

items=data.get("items",[])
events=data.get("events",[])
accepted_without_evidence=[]
for item in items:
    evidence=norm(" ".join([item.get("title",""),item.get("description","")]))
    if item.get("relevance",0)>=2 and not any(norm(x) in evidence for x in LOCAL_EXACT):
        accepted_without_evidence.append({
            "title":item.get("title",""),
            "source":item.get("source",""),
            "url":item.get("url","")
        })

coverage=sum(int(e.get("coverage") or 1) for e in events)
direct=sum(1 for e in events if e.get("relevanceLabel")=="DIRECTA")
specific=sum(1 for e in events if any((e.get("territory") or {}).get(k) for k in ["sectors","barrios","microzones","institutions","corridors"]))
source_counts=[int(e.get("sourceCount") or 1) for e in events]
source_diversity=round(sum(source_counts)/len(source_counts),2) if source_counts else 0
failed=sum(1 for s in data.get("sourceRegistry",[]) if s.get("success") is False)
active_nodes=int((data.get("territorialGraph") or {}).get("stats",{}).get("activeNodes") or 0)

data["audit"]={
    "version":"1.0",
    "updatedAt":datetime.now(timezone.utc).isoformat(),
    "rule":"fact != coverage; territory requires textual evidence",
    "facts":len(events),
    "coverage":coverage,
    "coveragePerFact":round(coverage/len(events),2) if events else 0,
    "directAnchorFacts":direct,
    "directAnchorPct":round(direct/len(events)*100,1) if events else 0,
    "territorySpecificFacts":specific,
    "territorySpecificPct":round(specific/len(events)*100,1) if events else 0,
    "averageSourcesPerFact":source_diversity,
    "activeTerritorialNodes":active_nodes,
    "failedSources":failed,
    "acceptedWithoutLocalEvidence":len(accepted_without_evidence),
    "examplesAcceptedWithoutLocalEvidence":accepted_without_evidence[:12],
    "interpretation":"auditoria técnica; no mide importancia, calidad periodística ni verdad del hecho"
}

data.setdefault("system",{})["audit"]="fact-vs-coverage + evidence-first + territorial-specificity"
with open(FEED,"w",encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
print("Audit:",data["audit"])
