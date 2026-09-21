import json
import re
import hashlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher

OUT="data/radar-feed.json"
DAYS=7
MEMORY_DAYS=45
NOW=datetime.now(timezone.utc)
MIN_DATE=NOW-timedelta(days=DAYS)
UA="Pulso-Chañar/8.0 (+https://eliasmartinezcultural-glitch.github.io/RADAR-CHA-AR/)"

DIRECT_SOURCES=[
 {"name":"Chañar Digital","type":"MEDIO LOCAL","url":"https://chanardigital.com.ar/","rss":["https://chanardigital.com.ar/feed/"]},
 {"name":"Mía Radio 94.7","type":"RADIO LOCAL","url":"https://www.radiomia.com.ar/","rss":[]},
 {"name":"Radio Tuit Vaca Muerta 90.5","type":"RADIO LOCAL / PRODUCTIVA","url":"https://tuitvacamuerta.com/","rss":[]},
 {"name":"Vaca Muerta News","type":"MEDIO REGIONAL / RADIO","url":"https://www.vacamuertanews.com/","rss":["https://www.vacamuertanews.com/feed/"]},
 {"name":"Neuquén Informa","type":"MEDIO OFICIAL PROVINCIAL","url":"https://www.neuqueninforma.gob.ar/","rss":["https://www.neuqueninforma.gob.ar/feed/","https://www.neuqueninforma.gob.ar/rss/"]},
 {"name":"Municipalidad de San Patricio del Chañar","type":"INSTITUCIONAL LOCAL","url":"https://sanpatricio.gob.ar/","rss":[]},
 {"name":"Boletín Oficial de Neuquén","type":"FUENTE NORMATIVA","url":"https://boletinoficial.neuquen.gov.ar/","rss":[]},
 {"name":"LM Neuquén","type":"MEDIO REGIONAL","url":"https://www.lmneuquen.com/","rss":["https://www.lmneuquen.com/rss/pages/section.xml?section=neuquen"]},
 {"name":"Diario Río Negro","type":"MEDIO REGIONAL","url":"https://www.rionegro.com.ar/","rss":["https://www.rionegro.com.ar/feed/"]},
 {"name":"Mejor Informado","type":"MEDIO REGIONAL","url":"https://www.mejorinformado.com/","rss":["https://www.mejorinformado.com/rss/"]},
 {"name":"Diariamente Neuquén","type":"MEDIO REGIONAL","url":"https://www.diariamenteneuquen.com/","rss":["https://www.diariamenteneuquen.com/feed/"]},
]

SOURCE_CATALOG=[
 {"name":"Chañar Digital","group":"LOCAL","role":"medio local","url":"https://chanardigital.com.ar/"},
 {"name":"Radio Municipal FM Chañar 87.9","group":"LOCAL","role":"radio municipal","url":"https://sanpatricio.gob.ar/"},
 {"name":"Radio FM Cadena Oasis","group":"LOCAL","role":"radio local","url":"https://www.facebook.com/"},
 {"name":"Mía Radio 94.7","group":"LOCAL","role":"radio local","url":"https://www.radiomia.com.ar/"},
 {"name":"Radio Tuit Vaca Muerta 90.5","group":"LOCAL-REGIONAL","role":"radio productiva","url":"https://tuitvacamuerta.com/"},
 {"name":"Municipalidad de San Patricio del Chañar","group":"LOCAL","role":"fuente institucional primaria","url":"https://sanpatricio.gob.ar/"},
 {"name":"EPEN","group":"REGIONAL","role":"energía eléctrica","url":"https://www.epen.gov.ar/"},
 {"name":"Dirección Provincial de Vialidad","group":"REGIONAL","role":"estado y obras viales","url":"https://www.dpvneuquen.gov.ar/"},
 {"name":"Vialidad Nacional","group":"REGIONAL-NACIONAL","role":"red vial nacional","url":"https://www.argentina.gob.ar/transporte/vialidad-nacional"},
 {"name":"Neuquén Informa","group":"REGIONAL","role":"comunicación oficial provincial","url":"https://www.neuqueninforma.gob.ar/"},
 {"name":"Servicio Meteorológico Nacional","group":"REGIONAL-NACIONAL","role":"alertas y meteorología","url":"https://www.smn.gob.ar/"},
 {"name":"Defensa Civil Neuquén","group":"REGIONAL","role":"emergencias y alertas","url":"https://www.neuquen.gob.ar/"},
 {"name":"Ministerio de Salud de Neuquén","group":"REGIONAL","role":"salud pública","url":"https://www.saludneuquen.gob.ar/"},
 {"name":"Consejo Provincial de Educación","group":"REGIONAL","role":"educación pública","url":"https://www.neuquen.edu.ar/"},
 {"name":"EPAS Neuquén","group":"REGIONAL","role":"agua y saneamiento","url":"https://www.epas.gov.ar/"},
 {"name":"Policía del Neuquén","group":"REGIONAL","role":"seguridad y emergencias","url":"https://www.policiadelneuquen.gob.ar/"},
 {"name":"Bomberos Voluntarios de San Patricio del Chañar","group":"LOCAL","role":"emergencias locales","url":"https://sanpatricio.gob.ar/"},
 {"name":"Ministerio de Producción e Industria de Neuquén","group":"REGIONAL","role":"producción rural","url":"https://www.neuquen.gob.ar/"},
 {"name":"Boletín Oficial de Neuquén","group":"REGIONAL","role":"normativa y actos oficiales","url":"https://boletinoficial.neuquen.gov.ar/"},
 {"name":"Diario Río Negro","group":"REGIONAL","role":"medio regional","url":"https://www.rionegro.com.ar/"},
 {"name":"LM Neuquén","group":"REGIONAL","role":"medio regional","url":"https://www.lmneuquen.com/"},
 {"name":"Mejor Informado","group":"REGIONAL","role":"medio regional","url":"https://www.mejorinformado.com/"},
 {"name":"Vaca Muerta News","group":"REGIONAL","role":"medio energético/productivo","url":"https://www.vacamuertanews.com/"},
 {"name":"Argentina.gob.ar","group":"EXTERNA","role":"fuente nacional","url":"https://www.argentina.gob.ar/"},
 {"name":"INTA","group":"EXTERNA","role":"producción, clima y territorio","url":"https://www.argentina.gob.ar/inta"}
]

QUERIES=[
 ('"San Patricio del Chañar"','territorio'),
 ('"San Patricio del Chañar" salud hospital','salud'),
 ('"San Patricio del Chañar" educación escuela CPEM EPET','educación'),
 ('"San Patricio del Chañar" municipio municipalidad concejo','instituciones'),
 ('"San Patricio del Chañar" producción chacra viñedo bodega productores','producción'),
 ('"San Patricio del Chañar" deporte club polideportivo','deportes'),
 ('"San Patricio del Chañar" cultura turismo fiesta','cultura'),
 ('"San Patricio del Chañar" obra servicio agua gas cloacas','servicios'),
 ('"San Patricio del Chañar" tránsito transporte ruta','movilidad'),
 ('"San Patricio del Chañar" seguridad bomberos policía','emergencias'),
 ('"San Patricio del Chañar" "Ruta 7"','territorio'),
 ('"San Patricio del Chañar" "Ruta 8"','territorio'),
 ('"San Patricio del Chañar" "Vaca Muerta"','regional'),
 ('"San Patricio del Chañar" Añelo','regional'),
 ('"San Patricio del Chañar" Neuquén','regional'),
 ('site:chanardigital.com.ar "San Patricio del Chañar"','Chañar Digital'),
 ('site:radiomia.com.ar "San Patricio del Chañar"','Mía Radio 94.7'),
 ('site:tuitvacamuerta.com "San Patricio del Chañar"','Radio Tuit Vaca Muerta 90.5'),
 ('site:neuqueninforma.gob.ar "San Patricio del Chañar"','Neuquén Informa'),
 ('site:lmneuquen.com "San Patricio del Chañar"','LM Neuquén'),
 ('site:rionegro.com.ar "San Patricio del Chañar"','Diario Río Negro'),
 ('site:mejorinformado.com "San Patricio del Chañar"','Mejor Informado'),
 ('site:diariamenteneuquen.com "San Patricio del Chañar"','Diariamente Neuquén'),
 ('site:vacamuertanews.com "San Patricio del Chañar"','Vaca Muerta News'),
 ('site:epen.gov.ar "San Patricio del Chañar"','EPEN'),
 ('site:dpvneuquen.gov.ar "San Patricio del Chañar"','Dirección Provincial de Vialidad'),
 ('site:argentina.gob.ar "San Patricio del Chañar" ruta','Vialidad Nacional'),
 ('site:smn.gob.ar "San Patricio del Chañar" Neuquén','Servicio Meteorológico Nacional'),
 ('site:saludneuquen.gob.ar "San Patricio del Chañar"','Ministerio de Salud de Neuquén'),
 ('site:neuquen.edu.ar "San Patricio del Chañar"','Consejo Provincial de Educación'),
 ('site:epas.gov.ar "San Patricio del Chañar"','EPAS Neuquén'),
 ('site:policiadelneuquen.gob.ar "San Patricio del Chañar"','Policía del Neuquén'),
 ('site:boletinoficial.neuquen.gov.ar "San Patricio del Chañar"','Boletín Oficial de Neuquén'),
 ('site:inta.gob.ar "San Patricio del Chañar"','INTA'),
]

LOCAL_ENTITIES=[
 'san patricio del chañar','san patricio del chanar','el chañar','el chanar',
 'hospital dra alicia cruz','hospital alicia cruz','hospital local',
 'municipalidad de san patricio','concejo deliberante de san patricio',
 'cpem 31','epet 26','escuela primaria 273','escuela 273','club san patricio',
 'polideportivo municipal','parque industrial','bodega familia schroeder','bodegas',
 'viñedo','viñedos','chacra','picada 1','picada 3','picada 4','picada 5','picada 9',
 'picada 11','picada 19','picada 20','ruta 7','ruta 8','comisaria 13',
 'bomberos voluntarios','correo argentino','centro de salud','128 viviendas',
 'union y fuerza','76 viviendas','50 viviendas','plan federalismo','primeros pobladores',
 'suyai','barrio obrero','barrio jardin','12 de octubre','25 de abril','loteo social'
]
STRONG_LOCAL=set(LOCAL_ENTITIES)-{'ruta 7','ruta 8','epen','viñedo','viñedos','bodegas','chacra'}
AMBIGUOUS=['puerto el chañar','chañaral','chañar viejo','chañaral de caracoles']
def clean(s): return re.sub(r'\\s+',' ',s or '').strip()
def norm(s):
    s=(s or '').lower().translate(str.maketrans('áéíóúü','aeiouu'))
    return re.sub(r'[^a-z0-9ñ ]+',' ',s)

GENERIC_TITLES=[norm('últimas noticias sobre san patricio del chañar'),norm('ultimas noticias sobre san patricio del chañar'),norm('noticias de san patricio del chañar')]

TOPIC_RULES=[
 ('SALUD',['hospital','salud','enfermer','medic','vacun','insumo']),
 ('EDUCACIÓN',['cpem','escuela','epet','educacion','clases','docente']),
 ('SERVICIOS',['agua','gas','cloaca','residu','luz','servicio']),
 ('MOVILIDAD',['ruta 7','ruta 8','transito','transporte','camiones','estacionamiento']),
 ('PRODUCCIÓN',['chacra','viñedo','bodega','productor','produccion','agro']),
 ('DEPORTE',['club','deporte','polideportivo','liga','futbol','basquet']),
 ('CULTURA / TURISMO',['cultura','turismo','fiesta','festival','museo','patrimonio']),
 ('INSTITUCIONES',['municipalidad','concejo','ordenanza','obra','licitacion']),
 ('SEGURIDAD / EMERGENCIAS',['bombero','policia','comisaria','emergencia']),
]

def parse_date(raw):
    if not raw: return None
    try:
        dt=parsedate_to_datetime(raw)
        return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    except Exception: pass
    try: return datetime.fromisoformat(raw.replace('Z','+00:00')).astimezone(timezone.utc)
    except Exception: return None
def title_key(s):
    stop={'san','patricio','del','el','de','la','los','las','una','un','y','en','por','para','con','que','neuquen','chanar','chañar','municipio','ciudad','provincia','noticias','ultimas','últimas','sobre'}
    return ' '.join(w for w in norm(s).split() if len(w)>2 and w not in stop)[:240]
def similarity(a,b):
    aa=set(title_key(a).split()); bb=set(title_key(b).split())
    if not aa or not bb: return 0
    return max(len(aa&bb)/len(aa|bb),SequenceMatcher(None,title_key(a),title_key(b)).ratio())
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/rss+xml,application/xml;q=0.9,*/*;q=0.8'})
    with urllib.request.urlopen(req,timeout=20) as r: return r.read()

def relevance(title,desc):
    evidence=norm(' '.join([title,desc]))
    t=norm(title)
    if any(norm(x) in evidence for x in AMBIGUOUS) and not ('san patricio del chañar' in evidence or 'san patricio del chanar' in evidence): return 0,'AMBIGUA'
    if any(norm(x)==t for x in GENERIC_TITLES): return 0,'AGREGADOR'
    exact=('san patricio del chañar' in evidence or 'san patricio del chanar' in evidence)
    title_hits=[x for x in STRONG_LOCAL if norm(x) in t]
    body_hits=[x for x in STRONG_LOCAL if norm(x) in evidence]
    if exact or title_hits or len(body_hits)>=2: return 3,'DIRECTA'
    if len(body_hits)==1: return 2,'CON ANCLA LOCAL'
    return 0,'SIN ANCLA'

def parse_rss(data,src,query):
    root=ET.fromstring(data); rows=[]
    for item in root.findall('.//item'):
        title=clean(item.findtext('title')); link=clean(item.findtext('link'))
        dt=parse_date(clean(item.findtext('pubDate') or item.findtext('published') or item.findtext('{http://purl.org/dc/elements/1.1/}date')))
        desc=clean(item.findtext('description'))
        if not title or not link or not dt or dt<MIN_DATE: continue
        score,label=relevance(title,desc)
        if score<2: continue
        rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':dt.isoformat(),'description':desc,'source':src['name'],'sourceType':src['type'],'sourceUrl':src['url'],'collection':'DIRECTA','query':query,'relevance':score,'relevanceLabel':label})
    return rows

def first_date(fragment):
    patterns=[r'article:published_time["\']\s*content=["\']([^"\']+)',r'<time[^>]+datetime=["\']([^"\']+)',r'"datePublished"\s*:\s*"([^"]+)"']
    for p in patterns:
        m=re.search(p,fragment,re.I)
        if m:
            dt=parse_date(m.group(1))
            if dt: return dt
    return None

def parse_homepage(data,src):
    raw=data.decode('utf-8','ignore'); rows=[]
    for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',raw,re.I|re.S):
        title=clean(re.sub(r'<[^>]+>',' ',m.group(2)))
        if not 18<=len(title)<=240: continue
        score,label=relevance(title,'')
        if score<2: continue
        dt=first_date(raw[max(0,m.start()-3000):min(len(raw),m.end()+3000)])
        if not dt or dt<MIN_DATE: continue
        link=urllib.parse.urljoin(src['url'],m.group(1))
        if link.startswith(('javascript:','mailto:','#')): continue
        rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':dt.isoformat(),'description':'','source':src['name'],'sourceType':src['type'],'sourceUrl':src['url'],'collection':'DIRECTA-WEB','query':'homepage','relevance':score,'relevanceLabel':label})
    return rows

def collect_direct():
    rows=[]; status=[]
    for src in DIRECT_SOURCES:
        attempted=0; failures=[]; found=0; mode='SIN RESPUESTA'
        for rss in src['rss']:
            attempted+=1
            try:
                got=parse_rss(fetch(rss),src,rss); rows.extend(got); found+=len(got)
                if got: mode='RSS DIRECTO'
            except Exception as e: failures.append('RSS:'+type(e).__name__)
        attempted+=1
        try:
            got=parse_homepage(fetch(src['url']),src); rows.extend(got); found+=len(got)
            if got and mode=='SIN RESPUESTA': mode='WEB DIRECTA'
        except Exception as e: failures.append('WEB:'+type(e).__name__)
        dates=[parse_date(x['publishedAt']) for x in rows if x['source']==src['name']]
        dates=[d for d in dates if d]
        status.append({'name':src['name'],'type':src['type'],'mode':mode,'signals':found,'url':src['url'],'lastFetch':datetime.now(timezone.utc).isoformat(),'success':attempted>len(failures),'attempted':attempted,'failures':failures[:4],'directAvailability':'available' if attempted>len(failures) else 'failed','freshnessHours':round((datetime.now(timezone.utc)-max(dates)).total_seconds()/3600,1) if dates else None})
    return rows,status

def search_collect():
    rows=[]
    for query,hint in QUERIES:
        try:
            root=ET.fromstring(fetch('https://news.google.com/rss/search?q='+urllib.parse.quote(query+' when:7d')+'&hl=es-419&gl=AR&ceid=AR:es-419'))
            for item in root.findall('.//item'):
                title=clean(item.findtext('title')); link=clean(item.findtext('link'))
                dt=parse_date(clean(item.findtext('pubDate'))); desc=clean(item.findtext('description'))
                source_node=item.find('source'); source=clean(source_node.text if source_node is not None else '') or hint
                if not title or not link or not dt or dt<MIN_DATE: continue
                score,label=relevance(title,desc)
                if score<2: continue
                rows.append({'title':title,'url':link,'publishedAt':dt.isoformat(),'published':dt.isoformat(),'description':desc,'source':source,'sourceType':'BUSCADOR / RESPALDO','sourceUrl':'','collection':'BUSCADOR','query':query,'relevance':score,'relevanceLabel':label})
        except Exception as e: print('SEARCH ERROR',query,type(e).__name__)
    return rows


RADAR_SOURCE_MAP={
 'CONVERSACIÓN':[
  {'name':'Chañar Digital','role':'medio local','mode':'DIRECTA','url':'https://www.chanardigital.com.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'fuente institucional local','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/'},
  {'name':'Neuquén Informa','role':'fuente oficial provincial','mode':'RESPALDO','url':'https://www.neuqueninforma.gob.ar/'}
 ],
 'RUTA 7':[
  {'name':'Dirección Provincial de Vialidad','role':'estado vial oficial / API','mode':'DIRECTA','url':'https://www.dpvneuquen.gov.ar/'},
  {'name':'Catálogo de servicios Neuquén','role':'endpoint WSESTADORUTAS','mode':'DIRECTA-API','url':'https://ww4.neuquen.gov.ar/Pecas/Optic/xroad/monitoreo/auditoria/Default.aspx'},
  {'name':'Ruta0','role':'respaldo comunitario de transitabilidad','mode':'RESPALDO','url':'https://www.ruta0.com/estado-de-rutas/'}
 ],
 'RUTA 8':[
  {'name':'Dirección Provincial de Vialidad','role':'estado vial oficial / API','mode':'DIRECTA','url':'https://www.dpvneuquen.gov.ar/'},
  {'name':'Catálogo de servicios Neuquén','role':'endpoint WSESTADORUTAS','mode':'DIRECTA-API','url':'https://ww4.neuquen.gov.ar/Pecas/Optic/xroad/monitoreo/auditoria/Default.aspx'},
  {'name':'Ruta0','role':'respaldo comunitario de transitabilidad','mode':'RESPALDO','url':'https://www.ruta0.com/estado-de-rutas/'}
 ],
 'VIENTO':[
  {'name':'Open-Meteo','role':'viento observado/modelado actual','mode':'DIRECTA-API','url':'https://open-meteo.com/'},
  {'name':'Servicio Meteorológico Nacional','role':'alertas oficiales','mode':'OFICIAL-ALERTAS','url':'https://www.smn.gob.ar/'},
  {'name':'Neuquén Informa','role':'comunicación oficial provincial','mode':'RESPALDO','url':'https://www.neuqueninforma.gob.ar/'}
 ],
 'ENERGÍA':[
  {'name':'EPEN','role':'cortes programados','mode':'DIRECTA-WEB','url':'https://www.epen.gov.ar/index.php/cortes-programados/'},
  {'name':'Neuquén Informa','role':'comunicados EPEN','mode':'OFICIAL','url':'https://www.neuqueninforma.gob.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'canal institucional local','mode':'RESPALDO','url':'https://sanpatricio.gob.ar/'}
 ],
 'AGUA':[
  {'name':'Municipalidad de San Patricio del Chañar','role':'canal institucional local','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/'},
  {'name':'EPAS Neuquén','role':'organismo provincial de agua y saneamiento','mode':'OFICIAL','url':'https://www.epas.gov.ar/'},
  {'name':'Neuquén Informa','role':'comunicados oficiales','mode':'RESPALDO','url':'https://www.neuqueninforma.gob.ar/'}
 ],
 'SERVICIOS':[
  {'name':'Municipalidad de San Patricio del Chañar','role':'servicios y avisos locales','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/'},
  {'name':'Neuquén Informa','role':'infraestructura provincial','mode':'OFICIAL','url':'https://www.neuqueninforma.gob.ar/'},
  {'name':'Chañar Digital','role':'seguimiento local','mode':'RESPALDO','url':'https://www.chanardigital.com.ar/'}
 ],
 'SALUD':[
  {'name':'Hospital Dra. Alicia Cruz','role':'referencia sanitaria local','mode':'INSTITUCIONAL','url':'https://www.saludneuquen.gob.ar/'},
  {'name':'Ministerio de Salud de Neuquén','role':'fuente sanitaria provincial','mode':'OFICIAL','url':'https://www.saludneuquen.gob.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'avisos locales','mode':'RESPALDO','url':'https://sanpatricio.gob.ar/'}
 ],
 'EDUCACIÓN':[
  {'name':'Consejo Provincial de Educación','role':'fuente educativa oficial','mode':'OFICIAL','url':'https://www.neuquen.edu.ar/'},
  {'name':'Neuquén Informa','role':'comunicados provinciales','mode':'RESPALDO','url':'https://www.neuqueninforma.gob.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'agenda local','mode':'RESPALDO','url':'https://sanpatricio.gob.ar/'}
 ],
 'PRODUCCIÓN':[
  {'name':'Ministerio de Producción e Industria de Neuquén','role':'fuente productiva oficial','mode':'OFICIAL','url':'https://www.neuqueninforma.gob.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'agenda productiva local','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/'},
  {'name':'Chañar Digital','role':'seguimiento local','mode':'RESPALDO','url':'https://www.chanardigital.com.ar/'}
 ],
 'EMERGENCIAS':[
  {'name':'Defensa Civil Neuquén','role':'emergencias provinciales','mode':'OFICIAL','url':'https://www.neuqueninforma.gob.ar/'},
  {'name':'Bomberos Voluntarios de San Patricio del Chañar','role':'referencia local','mode':'INSTITUCIONAL','url':'https://sanpatricio.gob.ar/'},
  {'name':'Municipalidad de San Patricio del Chañar','role':'seguridad y emergencias','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/sec-ciudadana'}
 ],
 'TERRITORIO':[
  {'name':'Municipalidad de San Patricio del Chañar','role':'territorio y agenda local','mode':'DIRECTA-WEB','url':'https://sanpatricio.gob.ar/'},
  {'name':'Dirección Provincial de Vialidad','role':'corredores y rutas','mode':'OFICIAL','url':'https://www.dpvneuquen.gov.ar/'},
  {'name':'Neuquén Informa','role':'infraestructura regional','mode':'RESPALDO','url':'https://www.neuqueninforma.gob.ar/'}
 ]
}

SOURCE_CONTRACTS = {
    'CONVERSACIÓN': {'primary':'Chañar Digital','secondary':'Municipalidad de San Patricio del Chañar','fallback':'Neuquén Informa','refresh':'30 min','rule':'evidencia editorial local'},
    'RUTA 7': {'primary':'Dirección Provincial de Vialidad','secondary':'WSESTADORUTAS · API oficial','fallback':'Ruta0','refresh':'30 min','rule':'parte oficial > fuente comunitaria'},
    'RUTA 8': {'primary':'Dirección Provincial de Vialidad','secondary':'WSESTADORUTAS · API oficial','fallback':'Ruta0','refresh':'30 min','rule':'parte oficial > fuente comunitaria'},
    'VIENTO': {'primary':'Open-Meteo','secondary':'Servicio Meteorológico Nacional','fallback':'Neuquén Informa','refresh':'30 min','rule':'dato meteorológico directo'},
    'ENERGÍA': {'primary':'EPEN','secondary':'Neuquén Informa','fallback':'Municipalidad de San Patricio del Chañar','refresh':'30 min','rule':'parte EPEN > comunicado'},
    'AGUA': {'primary':'EPAS','secondary':'Municipalidad de San Patricio del Chañar','fallback':'Neuquén Informa','refresh':'30 min','rule':'no inferir normalidad sin parte'},
    'SERVICIOS': {'primary':'Municipalidad de San Patricio del Chañar','secondary':'Neuquén Informa','fallback':'Chañar Digital','refresh':'30 min','rule':'fuente institucional local'},
    'SALUD': {'primary':'Salud Neuquén','secondary':'Hospital local / Salud Neuquén','fallback':'Municipalidad de San Patricio del Chañar','refresh':'30 min','rule':'fuente sanitaria oficial'},
    'EDUCACIÓN': {'primary':'Consejo Provincial de Educación','secondary':'Neuquén Informa','fallback':'Municipalidad de San Patricio del Chañar','refresh':'30 min','rule':'fuente educativa oficial'},
    'PRODUCCIÓN': {'primary':'Ministerio de Producción de Neuquén','secondary':'Neuquén Informa','fallback':'Municipalidad de San Patricio del Chañar','refresh':'30 min','rule':'fuente productiva oficial'},
    'EMERGENCIAS': {'primary':'Defensa Civil Neuquén','secondary':'Bomberos Voluntarios de San Patricio del Chañar','fallback':'Municipalidad de San Patricio del Chañar','refresh':'30 min','rule':'emergencia oficial > referencia institucional'},
    'TERRITORIO': {'primary':'Municipalidad de San Patricio del Chañar','secondary':'Dirección Provincial de Vialidad','fallback':'Neuquén Informa','refresh':'30 min','rule':'anclaje territorial explícito'}
}

def collect_operational():
    op={'updatedAt':datetime.now(timezone.utc).isoformat(),'route7':None,'route8':None,'energy':None,'water':None,'sources':[]}
    def attempt(name,url,kind):
        try:
            raw=fetch(url).decode('utf-8','ignore')
            return raw
        except Exception as e:
            op['sources'].append({'name':name,'mode':'FALLA','kind':kind,'url':url,'error':type(e).__name__})
            return ''
    route_raw=attempt('Ruta0','https://www.ruta0.com/estado-de-rutas/?pag=4','rutas')
    if route_raw:
        txt=re.sub(r'<[^>]+>',' ',route_raw); txt=clean(re.sub(r'\\s+',' ',txt))
        for key in ['route7','route8']:
            route='RP 7' if key=='route7' else 'RP 8'
            pos=txt.lower().find(route.lower())
            if pos>=0:
                frag=txt[max(0,pos-250):pos+900]
                if 'san patricio del chañar' in frag.lower() or key=='route8':
                    op[key]={'status':'SEÑAL DE TRANSITABILIDAD','detail':frag[:650],'source':'Ruta0','mode':'RESPALDO COMUNITARIO','url':'https://www.ruta0.com/estado-de-rutas/?pag=4'}
        op['sources'].append({'name':'Ruta0','mode':'OK','kind':'rutas','url':'https://www.ruta0.com/estado-de-rutas/?pag=4'})
    eurl='https://www.epen.gov.ar/index.php/cortes-programados/'
    eraw=attempt('EPEN','https://www.epen.gov.ar/index.php/cortes-programados/','energia')
    if eraw:
        et=re.sub(r'<[^>]+>',' ',eraw); et=clean(re.sub(r'\\s+',' ',et))
        hits=[m.group(0) for m in re.finditer(r'.{0,180}(?:Chañar|chañar).{0,360}',et,re.I)]
        op['energy']={'status':'PARTE EPEN DISPONIBLE','detail':' '.join(hits[:3])[:900] if hits else 'No se encontró una coincidencia reciente explícita para San Patricio del Chañar.','source':'EPEN','mode':'DIRECTA-WEB','url':eurl}
        op['sources'].append({'name':'EPEN','mode':'OK','kind':'energia','url':eurl})
    murl='https://sanpatricio.gob.ar/'
    mraw=attempt('Municipalidad de San Patricio del Chañar',murl,'agua')
    if mraw:
        mt=re.sub(r'<[^>]+>',' ',mraw); mt=clean(re.sub(r'\\s+',' ',mt))
        hits=[m.group(0) for m in re.finditer(r'.{0,160}(?:agua|abastecimiento|servicio).{0,300}',mt,re.I)]
        op['water']={'status':'MONITOREO INSTITUCIONAL','detail':' '.join(hits[:2])[:700] if hits else 'Sin parte operativo de agua visible en la portada municipal.','source':'Municipalidad de San Patricio del Chañar','mode':'DIRECTA-WEB','url':murl}
        op['sources'].append({'name':'Municipalidad de San Patricio del Chañar','mode':'OK','kind':'agua','url':murl})
    return op

def collect_environment():
    """Datos ambientales reales y señales de infraestructura derivadas de evidencia.
    No convierte ausencia de datos en ausencia de problema."""
    env={'updatedAt':datetime.now(timezone.utc).isoformat(),'weather':None,'sources':[]}
    try:
        url='https://api.open-meteo.com/v1/forecast?latitude=-39.061&longitude=-68.353&current=temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation&wind_speed_unit=kmh&timezone=America%2FArgentina%2FNeuquen'
        raw=json.loads(fetch(url).decode('utf-8'))
        c=raw.get('current',{})
        env['weather']={'temperatureC':c.get('temperature_2m'),'humidityPct':c.get('relative_humidity_2m'),'windKmh':c.get('wind_speed_10m'),'windDirection':c.get('wind_direction_10m'),'precipitationMm':c.get('precipitation'),'observedAt':c.get('time'),'source':'Open-Meteo','mode':'DATO DIRECTO'}
        env['sources'].append({'name':'Open-Meteo','mode':'OK','url':url})
    except Exception as e:
        env['sources'].append({'name':'Open-Meteo','mode':'FALLA','error':type(e).__name__})

    return env

def build_system_radars(events, environment):
    now=datetime.now(timezone.utc)
    specs=[
      ('CONVERSACIÓN','Conversación general',[''], 'evidencia editorial'),
      ('RUTA 7','Corredor Ruta 7',['ruta 7','transito','transporte','corte','desvio','camiones'], 'evidencia territorial'),
      ('RUTA 8','Corredor Ruta 8',['ruta 8','transito','transporte','corte','desvio'], 'evidencia territorial'),
      ('VIENTO','Condición de viento',['viento','rafaga','ráfaga','alerta meteorologica'], 'dato ambiental directo + evidencia'),
      ('ENERGÍA','Electricidad / cortes de luz',['luz','energia','eléctr','electric','corte de luz','epen'], 'evidencia editorial'),
      ('AGUA','Agua / abastecimiento',['agua','abastecimiento','corte de agua','potable','cloaca'], 'evidencia editorial'),
      ('SERVICIOS','Servicios e infraestructura',['servicio','obra','cloaca','residu','gas','luz','agua'], 'evidencia editorial'),
      ('SALUD','Salud',['hospital','salud','medic','vacun','guardia'], 'evidencia editorial'),
      ('EDUCACIÓN','Educación',['escuela','cpem','epet','clases','docente'], 'evidencia editorial'),
      ('PRODUCCIÓN','Producción rural',['chacra','viñedo','bodega','productor','agro'], 'evidencia editorial'),
      ('EMERGENCIAS','Seguridad / emergencias',['bombero','policia','emergencia','rescate','accidente'], 'evidencia editorial'),
      ('TERRITORIO','Territorio / microzonas',['picada','barrio','sector','parque industrial','loteo'], 'evidencia territorial')
    ]
    out=[]
    for code,label,terms,mode in specs:
        if code=='CONVERSACIÓN':
            matches=len(events)
        elif code=='VIENTO':
            matches=sum(1 for e in events if any(norm(t) in norm(e.get('title','')+' '+str(e.get('description',''))) for t in terms))
        else:
            matches=sum(1 for e in events if any(t in norm(e.get('title','')+' '+str(e.get('description',''))) for t in terms))
        last=max([parse_date(e.get('publishedAt')) for e in events if any(t in norm(e.get('title','')+' '+str(e.get('description',''))) for t in terms) and parse_date(e.get('publishedAt'))] or [None])
        age=None if not last else round((now-last).total_seconds()/3600,1)
        status='SIN SEÑAL RECIENTE'
        if matches:
            status='SEÑAL DETECTADA'
            if age is not None and age<=24: status='SEÑAL RECIENTE'
        if code=='VIENTO' and environment.get('weather'):
            status='DATO DIRECTO'
            matches=environment['weather'].get('windKmh') if environment['weather'].get('windKmh') is not None else matches
        out.append({'id':code,'label':label,'signal':matches,'status':status,'freshnessHours':age,'mode':('DATO DIRECTO' if code=='VIENTO' and environment.get('weather') else mode),'evidenceCount':sum(1 for e in events if any(t in norm(e.get('title','')+' '+str(e.get('description',''))) for t in terms))})
    return out

try:
    old=json.load(open(OUT,encoding='utf-8'))
except Exception: old={'items':[],'events':[]}

fresh,status=collect_direct()
fresh+=search_collect()

by_url={}
for x in fresh:
    key=x['url'].split('#',1)[0]
    if key not in by_url or (x['collection'].startswith('DIRECTA') and not by_url[key]['collection'].startswith('DIRECTA')): by_url[key]=x
ordered=sorted(by_url.values(),key=lambda x:x['publishedAt'],reverse=True)

dedup=[]
for x in ordered:
    merged=False
    for y in dedup:
        days=abs((parse_date(x['publishedAt'])-parse_date(y['publishedAt'])).total_seconds())/86400
        if days>2: continue
        sim=similarity(x['title'],y['title'])
        xt=set(norm(' '.join([x['title'],x['description']])).split())
        yt=set(norm(' '.join([y['title'],y['description']])).split())
        anchor_overlap=bool(xt & yt & {norm(a) for a in LOCAL_ENTITIES})
        topic_overlap=any(norm(term) in norm(x['title']+' '+x['description']) and norm(term) in norm(y['title']+' '+y['description']) for _,terms in TOPIC_RULES for term in terms)
        if sim>=0.84 or (sim>=0.48 and anchor_overlap and topic_overlap):
            # Prefer direct collection; otherwise preserve the richer title.
            if x['collection'].startswith('DIRECTA') and not y['collection'].startswith('DIRECTA'): dedup[dedup.index(y)]=x
            merged=True; break
    if not merged: dedup.append(x)

previous={x.get('url'):x for x in old.get('items',[])}
now=datetime.now(timezone.utc).isoformat()
for x in dedup:
    oldx=previous.get(x['url'],{})
    x['firstSeen']=oldx.get('firstSeen',now)
    x['isNew']=x['url'] not in previous
    x['titleKey']=title_key(x['title'])
    x['evidenceUrl']=x['url']
    x['sourcePriority']=1 if x['collection'].startswith('DIRECTA') and x['sourceType'] in {'MEDIO LOCAL','INSTITUCIONAL LOCAL','RADIO LOCAL'} else 2 if x['collection'].startswith('DIRECTA') else 3

def classify(x):
    text=norm(x.get('title','')+' '+x.get('description',''))
    scores=[(sum(norm(t) in text for t in terms),topic) for topic,terms in TOPIC_RULES]
    scores=[v for v in scores if v[0]]
    return max(scores)[1] if scores else 'OTROS'

def anchors(x):
    text=norm(x.get('title','')+' '+x.get('description',''))
    return [a for a in LOCAL_ENTITIES if norm(a) in text][:8]

def event_similarity(a,b):
    da=parse_date(a['publishedAt']); db=parse_date(b['publishedAt'])
    if not da or not db or abs((da-db).total_seconds())>2*86400: return 0
    sim=similarity(a['title'],b['title'])
    aa=set(anchors(a)); bb=set(anchors(b))
    topic=classify(a)==classify(b)
    overlap=len(aa&bb)/max(1,len(aa|bb))
    if sim>=0.80: return sim
    if sim>=0.62 and (overlap>0 or topic): return sim
    return 0

def metrics(members):
    dates=[parse_date(x['publishedAt']) for x in members if parse_date(x['publishedAt'])]
    latest=max(dates) if dates else NOW
    age=max(0,(NOW-latest).total_seconds()/3600)
    recency=max(0,1-age/168)
    sources=list(dict.fromkeys(x['source'] for x in members if x.get('source')))
    direct=sum(1 for s in sources if any(x.get('source')==s and x.get('sourcePriority',3)<=2 for x in members))
    topic=max(((sum(classify(x)==t for x in members),t) for t,_ in TOPIC_RULES),default=(0,'OTROS'))[1]
    movement=round(100*(0.45*recency+0.30*min(1,len(members)/4)+0.25*min(1,len(sources)/3)))
    return movement,topic,sources,direct

def build_events(items,old_events):
    clusters=[]
    for x in sorted(items,key=lambda z:z['publishedAt'],reverse=True):
        best=max(((event_similarity(x,y),i) for i,c in enumerate(clusters) for y in c),default=(0,None))
        if best[0]: clusters[best[1]].append(x)
        else: clusters.append([x])
    events=[]; used=set()
    for members in clusters:
        direct=[x for x in members if x.get('sourcePriority',3)<=2]
        canonical=sorted(direct or members,key=lambda x:(x.get('sourcePriority',3),-len(x['title'])))[0]
        movement,topic,sources,direct_count=metrics(members)
        ats=[]
        for x in members:
            for a in anchors(x):
                if a not in ats: ats.append(a)
        provisional={'title':canonical['title'],'publishedAt':max(x['publishedAt'] for x in members),'topic':topic,'territorialAnchors':ats,'sources':sources}
        best_old=None; best_score=0
        for olde in old_events:
            if olde.get('eventId') in used: continue
            d=similarity(provisional['title'],olde.get('title',''))
            oa=set(olde.get('territorialAnchors',[])); ca=set(ats)
            score=.55*d+.25*(len(ca&oa)/max(1,len(ca|oa)))+.20*(topic==olde.get('topic'))
            if score>best_score: best_score=score; best_old=olde
        seed=norm(canonical['title'])+'|'+'|'.join(sorted(ats[:4]))
        eid=(best_old.get('eventId') if best_old and best_score>=.62 else None) or 'CHA-'+hashlib.sha256(seed.encode()).hexdigest()[:12]
        if best_old: used.add(best_old.get('eventId'))
        first=min(x.get('firstSeen',x['publishedAt']) for x in members)
        prev_cov=best_old.get('coverage',0) if best_old else 0
        prev_sources=set(best_old.get('sources',[])) if best_old else set()
        new_sources=[s for s in sources if s not in prev_sources]
        age_days=(NOW-(parse_date(first) or NOW)).total_seconds()/86400
        if age_days<1 and movement>=45: life='EMERGENTE'
        elif movement>=65 or len(members)>prev_cov: life='ACTIVO'
        elif movement>=35: life='SOSTENIDO'
        elif age_days>4: life='EN DESCENSO'
        else: life='RECIENTE'
        incidence='DIRECTA EN CHANAR' if (canonical.get('relevance',0)==3 and len(ats)>0) else ('ANCLA TERRITORIAL' if len(ats)>0 else 'CONTEXTO REGIONAL')
        events.append({'eventId':eid,'title':canonical['title'],'publishedAt':max(x['publishedAt'] for x in members),'firstSeen':first,'lastSeen':max(x['publishedAt'] for x in members),'relevance':max(x['relevance'] for x in members),'relevanceLabel':'DIRECTA' if any(x['relevance']==3 for x in members) else 'CON ANCLA LOCAL','incidenceLabel':incidence,'topic':topic,'movement':movement,'coverage':len(members),'sourceCount':len(sources),'directSourceCount':direct_count,'territorialAnchors':ats[:8],'sources':sources[:8],'evidenceUrl':canonical['url'],'items':members[:8],'lifecycle':life,'movementDelta':movement-(best_old.get('movement',movement) if best_old else movement),'previousCoverage':prev_cov,'newSources':new_sources[:8],'sourceDiversity':len(sources),'memoryMatched':bool(best_old),'isNew':not bool(best_old)})
    current={e['eventId'] for e in events}
    failed={s['name'] for s in status if not s.get('success')}
    for e in old_events:
        if e.get('eventId') in current: continue
        if set(e.get('sources',[])) & failed:
            last=parse_date(e.get('lastSeen') or e.get('publishedAt'))
            if last and (NOW-last).days<=MEMORY_DAYS:
                carry=dict(e); carry['lifecycle']='SIN NUEVA COBERTURA'; carry['sourceContinuity']='fuente conocida sin respuesta; no se infiere desaparición'; carry['movementDelta']=0; carry['memoryMatched']=True; carry['isNew']=False
                events.append(carry)
    return sorted(events,key=lambda e:(e.get('movement',0),e.get('publishedAt','')),reverse=True)[:80]

dedup=dedup[:240]
events=build_events(dedup,old.get('events',[]))
environment=collect_environment()
operational=collect_operational()
system_radars=build_system_radars(events,environment)
for radar in system_radars:
    radar['sources']=RADAR_SOURCE_MAP.get(radar['id'],[])
    radar['sourceContract']=SOURCE_CONTRACTS.get(radar['id'])
    if radar['id']=='RUTA 7' and operational.get('route7'): radar['operational']=operational['route7']
    if radar['id']=='RUTA 8' and operational.get('route8'): radar['operational']=operational['route8']
    if radar['id']=='ENERGÍA' and operational.get('energy'): radar['operational']=operational['energy']
    if radar['id']=='AGUA' and operational.get('water'): radar['operational']=operational['water']
stats={'total':len(dedup),'direct':sum(x['relevance']==3 for x in dedup),'regional':sum(x['relevance']==2 for x in dedup),'new':sum(x.get('isNew',False) for x in dedup),'sources':len({x['source'] for x in dedup}),'directSignals':sum(x['collection'].startswith('DIRECTA') for x in dedup),'localDirectSignals':sum(x.get('sourcePriority')==1 for x in dedup),'radioDirectSignals':sum(x.get('sourceType')=='RADIO LOCAL' for x in dedup),'precisionRule':'evidence-first','searchNoiseRejected':sum(1 for x in fresh if relevance(x.get('title',''),x.get('description',''))[1] in {'AGREGADOR','SIN ANCLA','AMBIGUA'})}
output={'updatedAt':now,'window':f'{DAYS} días','purpose':'Detectar qué se está moviendo en San Patricio del Chañar y mostrar de dónde surge cada señal.','architecture':'25 fuentes profesionales + búsquedas dirigidas + fuentes directas + web directa + respaldo + memoria de eventos + ciclo de vida + incidencia territorial + evidencia + salud de fuentes + radares de infraestructura + ambiente','keywords':[q for q,_ in QUERIES],'sourceRegistry':status,'sourceCatalog':SOURCE_CATALOG,'stats':stats,'environment':environment,'operational':operational,'sourceContracts':SOURCE_CONTRACTS,'systemRadars':system_radars,'system':{'memoryDays':MEMORY_DAYS,'eventIdentity':'estable entre actualizaciones','evidenceRule':'evidence-first','movementRule':'descriptivo: recencia + cobertura + diversidad de fuentes; no es ranking de importancia','sourceFailureRule':'no inferir desaparición cuando las fuentes conocidas no responden','infrastructureRule':'una señal editorial no equivale a confirmación operativa; los datos directos se etiquetan por separado','lifecycle':['EMERGENTE','ACTIVO','SOSTENIDO','EN DESCENSO','RECIENTE'],'sourceHealth':status},'events':events,'items':dedup}
with open(OUT,'w',encoding='utf-8') as f: json.dump(output,f,ensure_ascii=False,indent=2)
print('PULSO:',stats,'RADARES:',len(system_radars))
