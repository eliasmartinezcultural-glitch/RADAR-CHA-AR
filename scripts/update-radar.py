import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from difflib import SequenceMatcher

OUT="data/radar-feed.json"
BASE=[
  ("San Patricio del Chañar","base","territorio"),
  ("El Chañar Neuquén","base","territorio"),
  ("San Patricio Chañar Ruta 7","base","circulación"),
  ("San Patricio Chañar Hospital","base","salud"),
  ("San Patricio Chañar Municipio","base","instituciones"),
  ("San Patricio Chañar producción","base","producción"),
  ("San Patricio Chañar educación","base","educación"),
]
LOCAL=[
  ("site:chanardigital.com.ar San Patricio del Chañar","Chañar Digital","local"),
]
REGIONAL=[
  ("site:lmneuquen.com San Patricio del Chañar","LM Neuquén","regional"),
  ("site:rionegro.com.ar San Patricio del Chañar","Diario Río Negro","regional"),
  ("site:neuqueninforma.gob.ar San Patricio del Chañar","Neuquén Informa","regional"),
]
STOP={"san","patricio","del","el","de","la","los","las","una","un","y","en","por","para","con","que","neuquen","neuquén","chanar","chañar","municipio","ciudad","provincia","nueva","nuevo"}

def rss_url(q):
    return "https://news.google.com/rss/search?q="+urllib.parse.quote(q+" when:7d")+"&hl=es-419&gl=AR&ceid=AR:es-419"

def fetch(q):
    req=urllib.request.Request(rss_url(q),headers={"User-Agent":"Chañar-Radar/2.0"})
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.read()

def text(x):
    return re.sub(r"\s+"," ",x or "").strip()

def norm_title(title):
    s=(title or "").lower()
    s=re.sub(r"[^a-záéíóúüñ0-9 ]+"," ",s)
    words=[w for w in s.split() if len(w)>2 and w not in STOP]
    return " ".join(words[:14])

def similarity(a,b):
    wa=set(norm_title(a).split()); wb=set(norm_title(b).split())
    if not wa or not wb: return 0
    jac=len(wa&wb)/len(wa|wb)
    seq=SequenceMatcher(None,norm_title(a),norm_title(b)).ratio()
    return max(jac,seq)

def parse(xml, source, tier, query):
    root=ET.fromstring(xml)
    rows=[]
    for item in root.findall(".//item"):
        title=text(item.findtext("title"))
        link=text(item.findtext("link"))
        pub=text(item.findtext("pubDate"))
        source_name=text(item.findtext("{http://search.yahoo.com/mrss/}source")) or source
        if not title or not link: continue
        rows.append({"title":title,"url":link,"published":pub,"source":source_name or source,
                     "tier":tier,"query":query})
    return rows

try:
    old=json.load(open(OUT,encoding="utf-8"))
except Exception:
    old={"updatedAt":None,"items":[],"stats":{}}

queries=LOCAL+REGIONAL+[(q,"Google News · territorio","base") for q,_,_ in BASE]
fresh=[]
for q,source,tier in queries:
    try:
        fresh += parse(fetch(q),source,tier,q)
    except Exception as e:
        print("ERROR",q,e)

rank={"local":0,"regional":1,"base":2}
fresh.sort(key=lambda x:(rank.get(x["tier"],9), x.get("published","")), reverse=False)
seen=set(); clean=[]
for x in fresh:
    key=(x["url"] or x["title"]).lower()
    if key in seen: continue
    seen.add(key); clean.append(x)

previous={i.get("url"):i for i in old.get("items",[])}
now=datetime.now(timezone.utc).isoformat()
for x in clean:
    p=previous.get(x["url"],{})
    x["firstSeen"]=p.get("firstSeen",now)
    x["isNew"]=x["url"] not in previous
    x["titleKey"]=norm_title(x["title"])

# El historial conserva señales anteriores. Los clusters permiten seguir una misma noticia
# cuando reaparece con títulos parecidos en el medio local o salta a medios regionales.
merged=clean+[i for i in old.get("items",[]) if i.get("url") not in {x["url"] for x in clean}]
merged=merged[:300]

clusters=[]
for item in merged:
    best=None; best_score=0
    for c in clusters:
        score=max(similarity(item["title"],c["representative"]), similarity(item["title"],c["representative2"]))
        if score>best_score:
            best_score=score; best=c
    if best is None or best_score<0.52:
        c={"id":"topic-"+str(len(clusters)+1).zfill(4),"representative":item["title"],"representative2":item["title"],"items":[]}
        clusters.append(c)
        best=c
    else:
        if len(item["title"])>len(best["representative2"]): best["representative2"]=item["title"]
    best["items"].append(item)

cluster_by_url={}
topics=[]
for c in clusters:
    its=c["items"]
    local=[i for i in its if i.get("tier")=="local"]
    regional=[i for i in its if i.get("tier")=="regional"]
    base=[i for i in its if i.get("tier")=="base"]
    all_dates=[i.get("firstSeen") for i in its if i.get("firstSeen")]
    local_dates=[i.get("firstSeen") for i in local if i.get("firstSeen")]
    regional_dates=[i.get("firstSeen") for i in regional if i.get("firstSeen")]
    first_local=min(local_dates) if local_dates else None
    first_regional=min(regional_dates) if regional_dates else None
    if local and regional and len(regional)>=2:
        stage="SEGUIMIENTO"
    elif local and regional:
        stage="SALTO REGIONAL"
    elif len(local)>=2:
        stage="REPETICIÓN LOCAL"
    elif local:
        stage="PRIMERA DETECCIÓN LOCAL"
    elif regional:
        stage="REGIONAL SIN DETECCIÓN LOCAL"
    else:
        stage="SEÑAL DE CONTEXTO"
    topic={
        "id":c["id"],"title":c["representative"],
        "stage":stage,"localCount":len(local),"regionalCount":len(regional),
        "totalCount":len(its),"firstSeen":min(all_dates) if all_dates else now,
        "firstLocalSeen":first_local,"firstRegionalSeen":first_regional,
        "lastSeen":max(all_dates) if all_dates else now
    }
    topics.append(topic)
    for i in its:
        cluster_by_url[i["url"]]=topic

for i in merged:
    t=cluster_by_url.get(i["url"])
    if t:
        i["topicId"]=t["id"]
        i["stage"]=t["stage"]
        i["localCount"]=t["localCount"]
        i["regionalCount"]=t["regionalCount"]
        i["firstLocalSeen"]=t["firstLocalSeen"]
        i["firstRegionalSeen"]=t["firstRegionalSeen"]

topics.sort(key=lambda x:x.get("lastSeen",""),reverse=True)
stats={
    "local":sum(i.get("tier")=="local" for i in merged),
    "regional":sum(i.get("tier")=="regional" for i in merged),
    "new":sum(i.get("isNew",False) for i in clean),
    "topics":len(topics),
    "localFirst":sum(t["stage"]=="PRIMERA DETECCIÓN LOCAL" for t in topics),
    "repeatedLocal":sum(t["stage"]=="REPETICIÓN LOCAL" for t in topics),
    "regionalJump":sum(t["stage"]=="SALTO REGIONAL" for t in topics),
    "followUp":sum(t["stage"]=="SEGUIMIENTO" for t in topics),
}
out={"updatedAt":now,"window":"7 días","keywords":[q for q,_,_ in BASE],
     "items":merged,"topics":topics[:100],"stats":stats}
open(OUT,"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
print("Radar:",len(clean),"señales nuevas; temas:",len(topics),"saltos regionales:",stats["regionalJump"])
