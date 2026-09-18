import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher

OUT = "data/radar-feed.json"
DAYS = 7
MIN_DATE = datetime.now(timezone.utc) - timedelta(days=DAYS)

# El motor busca conversación pública reciente. Las consultas son deliberadamente
# territoriales: una fuente local no convierte por sí sola una noticia en local.
QUERIES = [
    ('"San Patricio del Chañar"', 'territorio'),
    ('"San Patricio del Chañar" salud', 'salud'),
    ('"San Patricio del Chañar" educación', 'educación'),
    ('"San Patricio del Chañar" municipio', 'instituciones'),
    ('"San Patricio del Chañar" producción', 'producción'),
    ('"San Patricio del Chañar" deporte', 'deportes'),
    ('"San Patricio del Chañar" "Ruta 7"', 'territorio'),
    ('"San Patricio del Chañar" hospital', 'salud'),
    ('"San Patricio del Chañar" escuela', 'educación'),
    ('site:chanardigital.com.ar "San Patricio del Chañar"', 'local'),
    ('site:neuqueninforma.gob.ar "San Patricio del Chañar"', 'oficial'),
    ('site:lmneuquen.com "San Patricio del Chañar"', 'regional'),
    ('site:rionegro.com.ar "San Patricio del Chañar"', 'regional'),
]

# Entidades que permiten reconocer Chañar incluso cuando el nombre completo
# no aparece. No se asigna puntaje por ser una fuente local.
LOCAL_ENTITIES = [
    'cpem 31',
    'hospital dra alicia cruz',
    'hospital alicia cruz',
    'municipalidad de san patricio',
    'concejo deliberante de san patricio',
    'club san patricio',
    'san patricio',
    'picada 1', 'picada 4', 'picada 9', 'picada 11', 'picada 20',
    'ruta 7', 'ruta 8',
    'polideportivo municipal',
    'parque industrial',
    'bodega familia schroeder',
]

# Expresiones que suelen llevar a falsos positivos.
AMBIGUOUS = [
    'el chañar', 'puerto el chañar', 'chañaral', 'chañar viejo',
    'chañaral de caracoles'
]
GENERIC_PAGES = [
    'últimas noticias sobre', 'ultimas noticias sobre',
    'últimas noticias', 'ultimas noticias',
    'home -', 'inicio -', 'amp -'
]

STOP = {
    'san','patricio','del','el','de','la','los','las','una','un','y','en','por',
    'para','con','que','neuquen','neuquén','chanar','chañar','municipio',
    'ciudad','provincia','noticias','últimas','ultimas','sobre'
}

def clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()

def norm(text):
    text = (text or '').lower()
    text = text.translate(str.maketrans('áéíóúü', 'aeiouu'))
    return re.sub(r'[^a-z0-9ñ ]+', ' ', text)

def title_key(title):
    return ' '.join(
        w for w in norm(title).split()
        if len(w) > 2 and w not in STOP
    )[:240]

def similarity(a, b):
    aa = set(title_key(a).split())
    bb = set(title_key(b).split())
    if not aa or not bb:
        return 0
    jac = len(aa & bb) / len(aa | bb)
    seq = SequenceMatcher(None, title_key(a), title_key(b)).ratio()
    return max(jac, seq)

def rss_url(query):
    q = query + ' when:7d'
    return (
        'https://news.google.com/rss/search?q=' +
        urllib.parse.quote(q) +
        '&hl=es-419&gl=AR&ceid=AR:es-419'
    )

def fetch(query):
    req = urllib.request.Request(
        rss_url(query),
        headers={'User-Agent': 'Chañar-Radar/4.0'}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()

def parse_date(raw):
    if not raw:
        return None
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def is_ambiguous(text):
    n = norm(text)
    if 'san patricio del chañar' in n or 'san patricio del chanar' in n:
        return False
    return any(norm(x) in n for x in AMBIGUOUS)

def relevance(title, description, source):
    # La decisión territorial se toma sobre título + descripción, no sobre
    # el nombre del medio ni sobre la consulta que produjo el resultado.
    body = norm(' '.join([title, description]))
    exact = 'san patricio del chañar' in body or 'san patricio del chanar' in body
    local_hits = [x for x in LOCAL_ENTITIES if norm(x) in body]

    if is_ambiguous(body) and not exact:
        return 0, 'AMBIGUA'

    if any(norm(x) in norm(title) for x in GENERIC_PAGES):
        return 0, 'GENERICA'

    # DIRECTA: Chañar aparece explícitamente o una entidad inequívocamente local
    # es el sujeto de la noticia.
    if exact:
        return 3, 'DIRECTA'

    # Una entidad local en el cuerpo permite conservar una señal, pero no
    # convierte cualquier coincidencia aislada en noticia local.
    if local_hits:
        if len(local_hits) >= 2 or any(norm(x) in norm(title) for x in LOCAL_ENTITIES):
            return 3, 'DIRECTA'
        return 2, 'REGIONAL'

    return 0, 'SIN_ANCLA'

def parse_feed(xml_bytes, source_hint, query):
    root = ET.fromstring(xml_bytes)
    rows = []

    for item in root.findall('.//item'):
        title = clean(item.findtext('title'))
        link = clean(item.findtext('link'))
        raw_date = clean(item.findtext('pubDate'))
        published_at = parse_date(raw_date)
        description = clean(item.findtext('description'))

        source_node = item.find('{http://search.yahoo.com/mrss/}source')
        source = clean(source_node.text if source_node is not None else '') or source_hint
        source_url = (
            clean(source_node.attrib.get('url', ''))
            if source_node is not None else ''
        )

        if not title or not link or not published_at:
            continue
        if published_at < MIN_DATE:
            continue

        title = re.sub(
            r'\s+-\s+(Chañar Digital|LM Neuquén|Diario Río Negro|'
            r'Neuquén Informa|Lmneuquen\.com|rionegro\.com\.ar)$',
            '',
            title,
            flags=re.I
        ).strip()

        score, label = relevance(title, description, source)
        if score < 2:
            continue

        rows.append({
            'title': title,
            'url': link,
            'published': raw_date,
            'publishedAt': published_at.isoformat(),
            'description': description,
            'source': source,
            'sourceUrl': source_url,
            'query': query,
            'relevance': score,
            'relevanceLabel': label,
        })

    return rows

try:
    with open(OUT, encoding='utf-8') as handle:
        old = json.load(handle)
except Exception:
    old = {'items': []}

fresh = []
for query, hint in QUERIES:
    try:
        fresh.extend(parse_feed(fetch(query), hint, query))
    except Exception as exc:
        print('ERROR', query, exc)

# 1) URL exacta.
by_url = {}
for item in fresh:
    key = item['url'].split('#', 1)[0]
    if key not in by_url or (
        item['relevance'], item['publishedAt']
    ) > (
        by_url[key]['relevance'], by_url[key]['publishedAt']
    ):
        by_url[key] = item

# 2) Misma noticia con titulares casi iguales.
ordered = sorted(
    by_url.values(),
    key=lambda x: (x['publishedAt'], x['relevance']),
    reverse=True
)

deduped = []
for item in ordered:
    match = None
    for kept in deduped:
        if similarity(item['title'], kept['title']) >= 0.84:
            match = kept
            break

    if match is None:
        deduped.append(item)
    elif item['relevance'] > match['relevance']:
        match.update(item)

# Mantener únicamente la ventana vigente. Nada de rescatar pruebas viejas.
previous = {i.get('url'): i for i in old.get('items', [])}
now = datetime.now(timezone.utc).isoformat()

for item in deduped:
    old_item = previous.get(item['url'], {})
    item['firstSeen'] = old_item.get('firstSeen', now)
    item['isNew'] = item['url'] not in previous
    item['titleKey'] = title_key(item['title'])
    item['evidenceUrl'] = item['url']

deduped.sort(key=lambda x: x['publishedAt'], reverse=True)
deduped = deduped[:120]

stats = {
    'total': len(deduped),
    'direct': sum(x['relevance'] == 3 for x in deduped),
    'regional': sum(x['relevance'] == 2 for x in deduped),
    'new': sum(bool(x.get('isNew')) for x in deduped),
    'sources': len({x['source'] for x in deduped}),
}

output = {
    'updatedAt': now,
    'window': f'{DAYS} días',
    'purpose': '¿De qué se está hablando cuando se habla de San Patricio del Chañar?',
    'items': deduped,
    'stats': stats,
}

with open(OUT, 'w', encoding='utf-8') as handle:
    json.dump(output, handle, ensure_ascii=False, indent=2)

print('Radar:', stats)
