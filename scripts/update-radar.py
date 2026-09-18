import json, re, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from difflib import SequenceMatcher

OUT = "data/radar-feed.json"
WINDOW = "7d"

# Solo buscamos conversación que pueda atribuirse territorialmente a San Patricio del Chañar.
QUERIES = [
    ("San Patricio del Chañar", "territorio"),
    ("\"San Patricio del Chañar\" salud", "salud"),
    ("\"San Patricio del Chañar\" educación", "educación"),
    ("\"San Patricio del Chañar\" municipio", "instituciones"),
    ("\"San Patricio del Chañar\" producción", "producción"),
    ("\"San Patricio del Chañar\" deporte", "deportes"),
    ("site:chanardigital.com.ar \"San Patricio del Chañar\"", "local"),
    ("site:lmneuquen.com \"San Patricio del Chañar\"", "regional"),
    ("site:rionegro.com.ar \"San Patricio del Chañar\"", "regional"),
    ("site:neuqueninforma.gob.ar \"San Patricio del Chañar\"", "regional"),
]

LOCAL_ENTITIES = [
    "san patricio del chañar", "san patricio del chanar", "san patricio chañar",
    "san patricio chanar", "cpem 31", "hospital dra alicia cruz",
    "hospital alicia cruz", "picada 4", "picada 11", "ruta 7", "ruta 8",
    "municipalidad de san patricio", "concejo deliberante de san patricio",
    "bodega familia schroeder", "balneario municipal", "chasque", "chañar digital"
]
AMBIGUOUS = [
    "el chañar", "puerto el chañar", "chañaral", "chañaral", "chañar viejo",
    "chañaral de caracoles"
]
GENERIC_PAGES = [
    "últimas noticias sobre", "ultimas noticias sobre", "policiales -",
    "amp -", "home -", "inicio -", "últimas noticias", "ultimas noticias"
]
STOP = {
    "san","patricio","del","el","de","la","los","las","una","un","y","en","por",
    "para","con","que","neuquen","neuquén","chanar","chañar","municipio","ciudad",
    "provincia","noticias","últimas","ultimas","sobre"
}

def clean_text(x):
    return re.sub(r"\s+", " ", x or "").strip()

def normalize(x):
    x = (x or "").lower()
    x = x.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ü","u")
    return re.sub(r"[^a-z0-9ñ ]+", " ", x)

def title_key(title):
    words = [w for w in normalize(title).split() if len(w) > 2 and w not in STOP]
    return " ".join(words[:18])

def similarity(a, b):
    aa, bb = set(title_key(a).split()), set(title_key(b).split())
    if not aa or not bb:
        return 0
    jac = len(aa & bb) / len(aa | bb)
    seq = SequenceMatcher(None, title_key(a), title_key(b)).ratio()
    return max(jac, seq)

def rss_url(q):
    return "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:7d") + "&hl=es-419&gl=AR&ceid=AR:es-419"

def fetch(q):
    req = urllib.request.Request(rss_url(q), headers={"User-Agent":"Chañar-Radar/3.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()

def relevance(title, description, source, query):
    text = normalize(" ".join([title, description, source]))
    raw = (title + " " + description).lower()
    score = 0
    reason = "DIRECTA"

    if "san patricio del chañar" in raw or "san patricio del chanar" in raw:
        score += 6
    if any(k in text for k in [normalize(k) for k in LOCAL_ENTITIES]):
        score += 3
    if normalize(source) == normalize("Chañar Digital"):
        score += 2

    # Una consulta amplia no convierte por sí sola a una mención en señal local.
    if "chañar" in text and "san patricio" not in text and not any(normalize(k) in text for k in LOCAL_ENTITIES):
        score -= 4
        reason = "AMBIGUA"

    if any(normalize(k) in text for k in AMBIGUOUS) and "san patricio" not in text:
        score -= 5
        reason = "AMBIGUA"

    if any(normalize(k) in normalize(title) for k in GENERIC_PAGES):
        score -= 5

    if score >= 7:
        return 3, "DIRECTA"
    if score >= 4:
        return 2, "REGIONAL"
    if score >= 2:
        return 1, "INCIDENTAL"
    return 0, reason

def parse(xml, source_hint, query):
    root = ET.fromstring(xml)
    rows = []
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title"))
        link = clean_text(item.findtext("link"))
        pub = clean_text(item.findtext("pubDate"))
        desc = clean_text(item.findtext("description"))
        src = clean_text(item.findtext("{http://search.yahoo.com/mrss/}source")) or source_hint
        if not title or not link:
            continue
        # Google News suele agregar " - Medio" al título.
        title = re.sub(r"\s+-\s+(Chañar Digital|LM Neuquén|Diario Río Negro|Neuquén Informa|Lmneuquen\.com|rionegro\.com\.ar)$", "", title, flags=re.I)
        score, relevance_label = relevance(title, desc, src, query)
        if score <= 0:
            continue
        rows.append({
            "title": title, "url": link, "published": pub, "description": desc,
            "source": src, "query": query, "relevance": score,
            "relevanceLabel": relevance_label
        })
    return rows

try:
    old = json.load(open(OUT, encoding="utf-8"))
except Exception:
    old = {"updatedAt": None, "items": []}

fresh = []
for q, hint in QUERIES:
    try:
        fresh.extend(parse(fetch(q), hint, q))
    except Exception as e:
        print("ERROR", q, e)

# Canonicalización + deduplicación por URL y por historia, conservando la mejor señal.
by_url = {}
for item in fresh:
    key = item["url"].split("#", 1)[0]
    if key not in by_url or item["relevance"] > by_url[key]["relevance"]:
        by_url[key] = item

unique = list(by_url.values())
unique.sort(key=lambda x: (x["relevance"], x.get("published","")), reverse=True)

deduped = []
for item in unique:
    duplicate = False
    for kept in deduped:
        if similarity(item["title"], kept["title"]) >= 0.78:
            # Preferimos la fuente local/directa y, en empate, la fecha más reciente.
            duplicate = True
            if item["relevance"] > kept["relevance"]:
                kept.update(item)
            break
    if not duplicate:
        deduped.append(item)

previous = {i.get("url"): i for i in old.get("items", [])}
now = datetime.now(timezone.utc).isoformat()

for item in deduped:
    prev = previous.get(item["url"], {})
    item["firstSeen"] = prev.get("firstSeen", now)
    item["isNew"] = item["url"] not in previous
    item["titleKey"] = title_key(item["title"])

# No conservamos basura histórica: el feed representa la señal vigente de la ventana actual.
deduped = deduped[:120]

stats = {
    "total": len(deduped),
    "direct": sum(i["relevance"] == 3 for i in deduped),
    "regional": sum(i["relevance"] == 2 for i in deduped),
    "incidental": sum(i["relevance"] == 1 for i in deduped),
    "new": sum(i.get("isNew", False) for i in deduped),
    "sources": len(set(i["source"] for i in deduped)),
}

out = {
    "updatedAt": now,
    "window": "7 días",
    "purpose": "¿De qué se está hablando cuando se habla de San Patricio del Chañar?",
    "items": deduped,
    "stats": stats
}
open(OUT, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=2))
print("Radar:", stats)
