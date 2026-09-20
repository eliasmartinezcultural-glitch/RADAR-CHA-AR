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
UA = "Chañar-Radar/6.0 (+https://eliasmartinezcultural-glitch.github.io/RADAR-CHA-AR/)"

# RADAR CHAÑAR — arquitectura de fuentes
# 1) Fuentes directas: RSS cuando existe + páginas web cuando no existe.
# 2) Buscador de respaldo: Google News RSS para ampliar cobertura.
# 3) Clasificación territorial y deduplicación.
# La misión sigue siendo una sola: detectar conversación pública con anclaje en Chañar.
# Orden operativo: fuente local/institucional directa -> radio local directa -> regional directa -> buscador de respaldo.
# El buscador amplía cobertura; no convierte una fuente secundaria en fuente primaria.

DIRECT_SOURCES = [
    {"name":"Chañar Digital","type":"MEDIO LOCAL","url":"https://www.chanardigital.com.ar/","rss":["https://www.chanardigital.com.ar/rss.xml","https://www.chanardigital.com.ar/feed/","https://www.chanardigital.com.ar/rss.php"]},
    {"name":"Mía Radio 94.7","type":"RADIO LOCAL","url":"https://www.radiomia.com.ar/","rss":[]},
    {"name":"Radio Tuit Vaca Muerta 90.5","type":"RADIO LOCAL / PRODUCTIVA","url":"https://tuitvacamuerta.com/","rss":[]},
    {"name":"Vaca Muerta News","type":"MEDIO REGIONAL / RADIO","url":"https://www.vacamuertanews.com/","rss":["https://www.vacamuertanews.com/feed/"]},
    {"name":"Neuquén Informa","type":"MEDIO OFICIAL PROVINCIAL","url":"https://www.neuqueninforma.gob.ar/","rss":["https://www.neuqueninforma.gob.ar/feed/","https://www.neuqueninforma.gob.ar/rss/"]},
    {"name":"Municipalidad de San Patricio del Chañar","type":"INSTITUCIONAL LOCAL","url":"https://sanpatricio.gob.ar/","rss":["https://sanpatricio.gob.ar/feed/","https://sanpatricio.gob.ar/rss/"]},
    {"name":"Boletín Oficial de Neuquén","type":"FUENTE NORMATIVA","url":"https://boletinoficial.neuquen.gov.ar/","rss":[]},
    {"name":"Infoleg Neuquén","type":"FUENTE NORMATIVA","url":"https://infoleg.neuquen.gob.ar/","rss":[]},
    {"name":"LM Neuquén","type":"MEDIO REGIONAL","url":"https://www.lmneuquen.com/","rss":["https://www.lmneuquen.com/rss/pages/section.xml?section=neuquen"]},
    {"name":"Diario Río Negro","type":"MEDIO REGIONAL","url":"https://www.rionegro.com.ar/","rss":["https://www.rionegro.com.ar/feed/"]},
    {"name":"Mejor Informado","type":"MEDIO REGIONAL","url":"https://www.mejorinformado.com/","rss":["https://www.mejorinformado.com/rss/"]},
    {"name":"Diariamente Neuquén","type":"MEDIO REGIONAL","url":"https://www.diariamenteneuquen.com/","rss":["https://www.diariamenteneuquen.com/feed/"]},
]

QUERIES = [
    ('"San Patricio del Chañar"', 'territorio'),
    ('"San Patricio del Chañar" salud hospital', 'salud'),
    ('"San Patricio del Chañar" educación escuela CPEM EPET', 'educación'),
    ('"San Patricio del Chañar" municipio municipalidad concejo', 'instituciones'),
    ('"San Patricio del Chañar" producción chacra viñedo bodega productores', 'producción'),
    ('"San Patricio del Chañar" deporte club polideportivo', 'deportes'),
    ('"San Patricio del Chañar" cultura turismo fiesta', 'cultura'),
    ('"San Patricio del Chañar" obra servicio agua gas cloacas', 'servicios'),
    ('"San Patricio del Chañar" tránsito transporte ruta', 'movilidad'),
    ('"San Patricio del Chañar" seguridad bomberos policía', 'emergencias'),
    ('"San Patricio del Chañar" "Ruta 7"', 'territorio'),
    ('"San Patricio del Chañar" "Ruta 8"', 'territorio'),
    ('"San Patricio del Chañar" "Vaca Muerta"', 'regional'),
    ('"San Patricio del Chañar" Añelo', 'regional'),
    ('"San Patricio del Chañar" Neuquén', 'regional'),
    ('site:chanardigital.com.ar "San Patricio del Chañar"', 'Chañar Digital'),
    ('site:radiomia.com.ar "San Patricio del Chañar"', 'Mía Radio 94.7'),
    ('site:tuitvacamuerta.com "San Patricio del Chañar"', 'Radio Tuit Vaca Muerta 90.5'),
    ('site:neuqueninforma.gob.ar "San Patricio del Chañar"', 'Neuquén Informa'),
    ('site:lmneuquen.com "San Patricio del Chañar"', 'LM Neuquén'),
    ('site:rionegro.com.ar "San Patricio del Chañar"', 'Diario Río Negro'),
    ('site:mejorinformado.com "San Patricio del Chañar"', 'Mejor Informado'),
    ('site:diariamenteneuquen.com "San Patricio del Chañar"', 'Diariamente Neuquén'),
    ('site:vacamuertanews.com "San Patricio del Chañar"', 'Vaca Muerta News'),
]

LOCAL_ENTITIES = [
    'san patricio del chañar','san patricio del chanar','el chañar','el chanar',
    'hospital dra alicia cruz','hospital alicia cruz','hospital local',
    'municipalidad de san patricio','concejo deliberante de san patricio',
    'cpem 31','epet 26','escuela primaria 273','escuela 273',
    'club san patricio','polideportivo municipal','parque industrial',
    'bodega familia schroeder','bodegas','viñedo','viñedos','chacra',
    'picada 1','picada 4','picada 9','picada 11','picada 20',
    'ruta 7','ruta 8','comisaria 13','bomberos voluntarios',
    'correo argentino','centro de salud','plaza','rincón de los sauces'
]
AMBIGUOUS = ['puerto el chañar','chañaral','chañar viejo','chañaral de caracoles']
STOP = {'san','patricio','del','el','de','la','los','las','una','un','y','en','por','para','con','que','neuquen','neuquén','chanar','chañar','municipio','ciudad','provincia','noticias','últimas','ultimas','sobre'}

def clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()

def norm(text):
    text = (text or '').lower().translate(str.maketrans('áéíóúü','aeiouu'))
    return re.sub(r'[^a-z0-9ñ ]+', ' ', text)

def title_key(title):
    return ' '.join(w for w in norm(title).split() if len(w)>2 and w not in STOP)[:240]

def similarity(a,b):
    aa=set(title_key(a).split()); bb=set(title_key(b).split())
    if not aa or not bb: return 0
    return max(len(aa&bb)/len(aa|bb), SequenceMatcher(None,title_key(a),title_key(b)).ratio())

def parse_date(raw):
    if not raw: return None
    for parser in (parsedate_to_datetime,):
        try:
            dt=parser(raw)
            if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception: pass
    try:
        dt=datetime.fromisoformat(raw.replace('Z','+00:00'))
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def fetch_url(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=20) as response:
        return response.read(), response.headers.get('Content-Type','')

def relevance(title,description,source):
    # La fuente/query NO pueden convertir por sí solas una nota en "DIRECTA".
    # La evidencia territorial debe aparecer en el título o descripción.
    evidence=norm(' '.join([title,description]))
    exact='san patricio del chañar' in evidence or 'san patricio del chanar' in evidence
    if any(norm(x) in evidence for x in AMBIGUOUS) and not exact: return 0,'AMBIGUA'
    hits=[x for x in LOCAL_ENTITIES if norm(x) in evidence]
    title_hits=[x for x in LOCAL_ENTITIES if norm(x) in norm(title)]
    if exact: return 3,'DIRECTA'
    if len(title_hits)>=1: return 3,'DIRECTA'
    if len(hits)>=2: return 3,'DIRECTA'
    if len(hits)==1: return 2,'CON ANCLA LOCAL'
    return 0,'SIN ANCLA'

def parse_rss(xml_bytes,source,source_type,source_url,query='direct-rss'):
    root=ET.fromstring(xml_bytes)
    rows=[]
    for item in root.findall('.//item'):
        title=clean(item.findtext('title')); link=clean(item.findtext('link'))
        raw=clean(item.findtext('pubDate') or item.findtext('published') or item.findtext('{http://purl.org/dc/elements/1.1/}date'))
        dt=parse_date(raw)
        desc=clean(item.findtext('description'))
        if not title or not link or not dt or dt<MIN_DATE: continue
        score,label=relevance(title,desc,source)
        if score<2: continue
        rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':raw,'description':desc,'source':source,'sourceType':source_type,'sourceUrl':source_url,'collection':'DIRECTA','query':query,'relevance':score,'relevanceLabel':label})
    return rows

def html_text(html):
    return clean(re.sub(r'<[^>]+>',' ',html,flags=re.S))

def first_date(html):
    patterns=[
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'"dateCreated"\s*:\s*"([^"]+)"'
    ]
    for p in patterns:
        m=re.search(p,html,re.I)
        if m:
            dt=parse_date(m.group(1))
            if dt: return dt
    return None

def parse_homepage(html_bytes,source,source_type,source_url):
    raw=html_bytes.decode('utf-8','ignore')
    rows=[]
    # We only accept links whose visible title carries a Chañar/local signal.
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',raw,re.I|re.S):
        href,inside=m.group(1),m.group(2)
        title=clean(html_text(inside))
        if len(title)<18 or len(title)>240: continue
        body=norm(title)
        if not any(norm(k) in body for k in LOCAL_ENTITIES): continue
        link=urllib.parse.urljoin(source_url,href)
        if link.startswith(('javascript:','mailto:','#')): continue
        dt=first_date(raw[max(0,m.start()-3000):min(len(raw),m.end()+3000)])
        if not dt or dt<MIN_DATE: continue
        score,label=relevance(title,'',source)
        if score<2: continue
        rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':dt.isoformat(),'description':'','source':source,'sourceType':source_type,'sourceUrl':source_url,'collection':'DIRECTA-WEB','query':'homepage','relevance':score,'relevanceLabel':label})
    return rows

def direct_collect():
    rows=[]
    source_status=[]
    for src in DIRECT_SOURCES:
        found=0; mode='sin respuesta'
        for rss in src['rss']:
            try:
                data,ctype=fetch_url(rss)
                got=parse_rss(data,src['name'],src['type'],src['url'],rss)
                rows.extend(got); found+=len(got)
                if got: mode='RSS directo'
            except Exception: pass
        try:
            data,ctype=fetch_url(src['url'])
            got=parse_homepage(data,src['name'],src['type'],src['url'])
            rows.extend(got); found+=len(got)
            if got and mode=='sin respuesta': mode='WEB directa'
        except Exception: pass
        source_status.append({'name':src['name'],'type':src['type'],'mode':mode,'signals':found,'url':src['url']})
    return rows,source_status

def google_url(query):
    q=query+' when:7d'
    return 'https://news.google.com/rss/search?q='+urllib.parse.quote(q)+'&hl=es-419&gl=AR&ceid=AR:es-419'

def search_collect():
    rows=[]
    for query,hint in QUERIES:
        try:
            data,_=fetch_url(google_url(query))
            root=ET.fromstring(data)
            for item in root.findall('.//item'):
                title=clean(item.findtext('title')); link=clean(item.findtext('link'))
                raw=clean(item.findtext('pubDate')); dt=parse_date(raw)
                desc=clean(item.findtext('description'))
                sn=item.find('source'); source=clean(sn.text if sn is not None else '') or hint
                if not title or not link or not dt or dt<MIN_DATE: continue
                score,label=relevance(title,desc,source)
                if score<2: continue
                rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':raw,'description':desc,'source':source,'sourceType':'BUSCADOR / RESPALDO','sourceUrl':'','collection':'BUSCADOR','query':query,'relevance':score,'relevanceLabel':label})
        except Exception as exc:
            print('SEARCH ERROR',query,exc)
    return rows

try:
    with open(OUT,encoding='utf-8') as handle: old=json.load(handle)
except Exception:
    old={'items':[]}

direct_rows,status=direct_collect()
search_rows=search_collect()
fresh=direct_rows+search_rows

by_url={}
for item in fresh:
    key=item['url'].split('#',1)[0]
    if key not in by_url or (item['collection']=='DIRECTA' and by_url[key]['collection']!='DIRECTA'):
        by_url[key]=item

ordered=sorted(by_url.values(),key=lambda x:(x['publishedAt'],x['relevance']),reverse=True)
deduped=[]
for item in ordered:
    match=None
    for kept in deduped:
        if similarity(item['title'],kept['title'])>=0.84:
            match=kept; break
    if match is None:
        deduped.append(item)
    elif item['collection'].startswith('DIRECTA') and not kept['collection'].startswith('DIRECTA'):
        deduped[deduped.index(match)]=item

previous={i.get('url'):i for i in old.get('items',[])}
now=datetime.now(timezone.utc).isoformat()
for item in deduped:
    old_item=previous.get(item['url'],{})
    item['firstSeen']=old_item.get('firstSeen',now)
    item['isNew']=item['url'] not in previous
    item['titleKey']=title_key(item['title'])
    item['evidenceUrl']=item['url']
    item['sourcePriority'] = (
        1 if item.get('collection','').startswith('DIRECTA') and item.get('sourceType','') in {'MEDIO LOCAL','INSTITUCIONAL LOCAL','RADIO LOCAL'}
        else 2 if item.get('collection','').startswith('DIRECTA')
        else 3
    )

def event_similarity(a,b):
    # Agrupa coberturas del mismo hecho sin exigir títulos idénticos.
    da=parse_date(a.get('publishedAt')) or MIN_DATE
    db=parse_date(b.get('publishedAt')) or MIN_DATE
    if abs((da-db).total_seconds()) > 4*86400:
        return 0
    sa=set(w for w in title_key(a.get('title','')).split() if len(w)>=4)
    sb=set(w for w in title_key(b.get('title','')).split() if len(w)>=4)
    common=len(sa & sb)
    sim=similarity(a.get('title',''),b.get('title',''))
    if sim>=0.78: return sim
    if common>=2 and sim>=0.58: return sim
    return 0

def build_events(items):
    clusters=[]
    for item in sorted(items,key=lambda x:x.get('publishedAt',''),reverse=True):
        best=None; best_score=0
        for idx,event in enumerate(clusters):
            score=max((event_similarity(item,member) for member in event['items']),default=0)
            if score>best_score:
                best_score=score; best=idx
        if best is None or best_score==0:
            clusters.append({'items':[item]})
        else:
            clusters[best]['items'].append(item)

    events=[]
    for n,cluster in enumerate(clusters,1):
        members=cluster['items']
        canonical=sorted(members,key=lambda x:(x.get('sourcePriority',3),-len(x.get('title','')),x.get('publishedAt','')),reverse=False)[0]
        # Prioriza una fuente directa para nombrar el hecho cuando existe.
        direct=[x for x in members if x.get('sourcePriority',3)<3]
        if direct:
            canonical=sorted(direct,key=lambda x:(x.get('sourcePriority',3),x.get('publishedAt','')),key=None) if False else sorted(direct,key=lambda x:(x.get('sourcePriority',3),-len(x.get('title',''))))[0]
        members=sorted(members,key=lambda x:x.get('publishedAt',''),reverse=True)
        sources=[]
        for m in members:
            if m.get('source') and m['source'] not in sources: sources.append(m['source'])
        events.append({
            'eventId':f'CHA-{n:03d}',
            'title':canonical.get('title',''),
            'publishedAt':members[0].get('publishedAt'),
            'relevance':max(m.get('relevance',0) for m in members),
            'relevanceLabel':'DIRECTA' if any(m.get('relevance')==3 for m in members) else 'CON ANCLA LOCAL',
            'coverage':len(members),
            'sources':sources[:8],
            'evidenceUrl':canonical.get('evidenceUrl') or canonical.get('url'),
            'items':members[:8]
        })
    events.sort(key=lambda x:(x.get('publishedAt') or '',x.get('coverage',0)),reverse=True)
    return events[:80]

deduped.sort(key=lambda x:x['publishedAt'],reverse=True)
deduped=deduped[:240]
events=build_events(deduped)
direct_count=sum(x['collection'].startswith('DIRECTA') for x in deduped)
stats={'total':len(deduped),'direct':sum(x['relevance']==3 for x in deduped),'regional':sum(x['relevance']==2 for x in deduped),'new':sum(bool(x.get('isNew')) for x in deduped),'sources':len({x['source'] for x in deduped}),'directSignals':direct_count,'localDirectSignals':sum(x.get('sourcePriority')==1 for x in deduped),'radioDirectSignals':sum(x.get('sourceType')=='RADIO LOCAL' for x in deduped)}
output={'updatedAt':now,'window':f'{DAYS} días','purpose':'¿De qué se está hablando cuando se habla de San Patricio del Chañar?','architecture':'fuentes directas + web directa + buscador de respaldo + eventos agrupados','keywords':[q for q,_ in QUERIES],'sourceRegistry':status,'stats':stats,'events':events,'items':deduped}
with open(OUT,'w',encoding='utf-8') as handle: json.dump(output,handle,ensure_ascii=False,indent=2)
print('Radar:',stats)
for s in status: print('SOURCE',s)
