import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone

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

def rss_url(q):
  return "https://news.google.com/rss/search?q="+urllib.parse.quote(q+" when:7d")+"&hl=es-419&gl=AR&ceid=AR:es-419"

def fetch(q):
  req=urllib.request.Request(rss_url(q),headers={"User-Agent":"Chañar-Radar/1.0"})
  with urllib.request.urlopen(req,timeout=20) as r:
    return r.read()

def text(x):
  return re.sub(r"\\s+"," ",x or "").strip()

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

queries=LOCAL+REGIONAL+[(q,"Google News · territorio","regional") for q,_,_ in BASE]
items=[]
for q,source,tier in queries:
  try:
    items += parse(fetch(q),source,tier,q)
  except Exception as e:
    print("ERROR",q,e)

# Deduplicar por URL/título. Prioridad: local > regional > base.
rank={"local":0,"regional":1,"base":2}
items.sort(key=lambda x:(rank.get(x["tier"],9), x.get("published","")), reverse=False)
seen=set()
clean=[]
for x in items:
  key=(x["url"] or x["title"]).lower()
  if key in seen: continue
  seen.add(key); clean.append(x)

previous={i.get("url"):i for i in old.get("items",[])}
now=datetime.now(timezone.utc).isoformat()
for x in clean:
  x["firstSeen"]=previous.get(x["url"],{}).get("firstSeen",now)
  x["isNew"]=x["url"] not in previous

# Mantener historial reciente y limitar tamaño.
merged=clean+[i for i in old.get("items",[]) if i.get("url") not in {x["url"] for x in clean}]
merged=merged[:300]
stats={
 "local":sum(i["tier"]=="local" for i in merged),
 "regional":sum(i["tier"]=="regional" for i in merged),
 "new":sum(i.get("isNew",False) for i in clean)
}
out={"updatedAt":now,"window":"7 días","keywords":[q for q,_,_ in BASE],
     "items":merged,"stats":stats}
open(OUT,"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
print("Radar:",len(clean),"nuevos:",stats["new"])
