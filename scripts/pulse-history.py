import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

FEED=Path("data/radar-feed.json")
OUT=Path("data/pulse-history.json")
MAX_DAYS=45
BUCKET_HOURS=2

def parse_dt(v):
    try:
        return datetime.fromisoformat((v or "").replace("Z","+00:00")).astimezone(timezone.utc)
    except Exception:
        return None

def snapshot(data):
    events=data.get("events",[])
    graph=data.get("territorialGraph",{})
    topics={}
    sources={}
    lifecycle={}
    nodes={}
    direct=0
    for e in events:
        t=e.get("topic") or "OTROS"
        topics[t]=topics.get(t,0)+1
        lifecycle[e.get("lifecycle") or "RECIENTE"]=lifecycle.get(e.get("lifecycle") or "RECIENTE",0)+1
        direct += int(e.get("directSourceCount") or 0)
        for s in e.get("sources",[])[:8]:
            sources[s]=sources.get(s,0)+1
        for n in (e.get("territory") or {}).get("nodes",[])[:10]:
            nodes[n]=nodes.get(n,0)+1
    now=datetime.now(timezone.utc)
    bucket=now.replace(minute=(now.minute//(BUCKET_HOURS*1))*BUCKET_HOURS,second=0,microsecond=0)
    return {
        "at":now.isoformat(),
        "bucket":bucket.isoformat(),
        "events":len(events),
        "topics":topics,
        "sources":sources,
        "lifecycle":lifecycle,
        "nodes":nodes,
        "activeNodes":int(graph.get("stats",{}).get("activeNodes") or 0),
        "directSignals":direct,
        "newSignals":sum(1 for e in events if e.get("isNew")),\n        "sourceHealth":{s.get("name"):{"success":bool(s.get("success")),"signals":int(s.get("signals") or 0),"freshnessHours":s.get("freshnessHours")} for s in data.get("sourceRegistry",[]) if s.get("name")},
    }

try:
    history=json.loads(OUT.read_text(encoding="utf-8"))
except Exception:
    history={"version":"1.0","windowDays":MAX_DAYS,"bucketHours":BUCKET_HOURS,"snapshots":[]}

data=json.loads(FEED.read_text(encoding="utf-8"))
snap=snapshot(data)
rows=history.get("snapshots",[])
rows=[r for r in rows if r.get("bucket")!=snap["bucket"]]
rows.append(snap)
cutoff=datetime.now(timezone.utc)-timedelta(days=MAX_DAYS)
rows=[r for r in rows if (parse_dt(r.get("at")) or datetime.now(timezone.utc))>=cutoff]
rows.sort(key=lambda r:r.get("at",""))
history={"version":"1.0","windowDays":MAX_DAYS,"bucketHours":BUCKET_HOURS,"generatedAt":datetime.now(timezone.utc).isoformat(),"snapshots":rows}
OUT.write_text(json.dumps(history,ensure_ascii=False,indent=2),encoding="utf-8")
print("History:",len(rows),"snapshots")
