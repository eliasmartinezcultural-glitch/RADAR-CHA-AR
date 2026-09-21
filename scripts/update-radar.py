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
DAYS=14
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
 {"name":"Mía Radio 94.7","group":"LOCAL","role":"radio local","url":"https://www.radiomia.com.ar/"},
 {"name":"Radio Tuit Vaca Muerta 90.5","group":"LOCAL-REGIONAL","role":"radio productiva","url":"https://tuitvacamuerta.com/"},
 {"name":"Municipalidad de San Patricio del Chañar","group":"LOCAL","role":"fuente institucional primaria","url":"https://sanpatricio.gob.ar/"},
 {"name":"EPEN","group":"REGIONAL","role":"energía eléctrica","url":"https://www.epen.gov.ar/"},
 {"name":"Dirección Provincial de Vialidad","group":"REGIONAL","role":"estado y obras viales","url":"https://www.dpvneuquen.gov.ar/"},
 {"name":"Vialidad Nacional","group":"REGIONAL-NACIONAL","role":"red vial nacional","url":"https://www.argentina.gob.ar/transporte/vialidad-nacional"},
 {"name":"Neuquén Informa","group":"REGIONAL","role":"comunicación oficial provincial","url":"https://www.neuqueninforma.gob.ar/"},
 {"name":"Servicio Meteorológico Nacional","group":"REGIONAL-NACIONAL","role":"alertas y meteorología","url":"https://www.smn.gob.ar/"},
 {"name":"AIC","group":"REGIONAL","role":"pronóstico y viento para El Chañar","url":"https://www.aic.gob.ar/sitio/home?a=1015&z=1967225803"},
 {"name":"Diario Neuquino","group":"REGIONAL","role":"medio regional","url":"https://www.diariamenteneuquen.com/"},
 {"name":"Defensa Civil Neuquén","group":"REGIONAL","role":"emergencias y alertas","url":"https://www.neuquen.gob.ar/"},
 {"name":"Ministerio de Salud de Neuquén","group":"REGIONAL","role":"salud pública","url":"https://www.saludneuquen.gob.ar/"},
 {"name":"Consejo Provincial de Educación","group":"REGIONAL","role":"educación pública","url":"https://www.neuquen.edu.ar/"},
 {"name":"EPAS Neuquén","group":"REGIONAL","role":"agua y saneamiento","url":"https://www.epas.gov.ar/"},
 {"name":"Policía del Neuquén","group":"REGIONAL","role":"seguridad y emergencias","url":"https://www.policiadelneuquen.gob.ar/"},
 {"name":"Ministerio de Producción e Industria de Neuquén","group":"REGIONAL","role":"producción rural","url":"https://www.neuquen.gob.ar/"},
 {"name":"Diario Río Negro","group":"REGIONAL","role":"medio regional","url":"https://www.rionegro.com.ar/"},
 {"name":"LM Neuquén","group":"REGIONAL","role":"medio regional","url":"https://www.lmneuquen.com/"},
 {"name":"Mejor Informado","group":"REGIONAL","role":"medio regional","url":"https://www.mejorinformado.com/"},
 {"name":"Vaca Muerta News","group":"REGIONAL","role":"medio energético/productivo","url":"https://www.vacamuertanews.com/"},
 {"name":"Argentina.gob.ar","group":"EXTERNA","role":"fuente nacional","url":"https://www.argentina.gob.ar/"},
 {"name":"INTA","group":"EXTERNA","role":"producción, clima y territorio","url":"https://www.argentina.gob.ar/inta"},
 {"name":"CFI","group":"EXTERNA","role":"información territorial y federal","url":"https://cfi.org.ar/"},
 {"name":"COPADE Neuquén","group":"EXTERNA","role":"planificación territorial","url":"https://www.copade.gob.ar/"},
 {"name":"Universidad Nacional del Comahue","group":"EXTERNA","role":"conocimiento regional","url":"https://www.uncoma.edu.ar/"}
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
 ('site:cfi.org.ar "San Patricio del Chañar"','CFI'),
 ('site:copade.gob.ar "San Patricio del Chañar"','COPADE Neuquén'),
 ('site:uncoma.edu.ar "San Patricio del Chañar"','Universidad Nacional del Comahue'),
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
def clean(s): return ' '.join((s or '').split())
def norm(s):
    s=(s or '').lower().translate(str.maketrans('áéíóúü','aeiouu'))
    return re.sub(r'[^a-z0-9ñ ]+',' ',s)

GENERIC_TITLES=[norm('últimas noticias sobre san patricio del chañar'),norm('ultimas noticias sobre san patricio del chañar'),norm('noticias de san patricio del chañar')]

TOPIC_RULES=[
 ('SALUD',['hospital','salud','enfermer','medic','vacun','insumo']),
 ('EDUCACIÓN',['cpem','escuela','epet','educacion','clases','docente']),
 ('SERVICIOS',['agua','gas','cloaca','residu','luz','servicio']),
 ('MOVILIDAD',['ruta 7','ruta 8','transito','transporte','camiones','estacionamiento','corredor']),
 ('PRODUCCIÓN',['chacra','viñedo','bodega','productor','produccion','agro']),
 ('DEPORTE',['club','deporte','polideportivo','liga','futbol','basquet','regional amateur','deportivo rincon','deportivo roca']),
 ('CULTURA / TURISMO',['cultura','turismo','fiesta','festival','museo','patrimonio','wine fest','evento','los pericos','los tipitos']),
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
    with urllib.request.urlopen(req,timeout=20) as r:
        return r.read().decode('utf-8','ignore')

def relevance(title,desc):
    evidence=norm(' '.join([title,desc]))
    t=norm(title)
    if any(norm(x) in evidence for x in AMBIGUOUS) and not ('san patricio del chañar' in evidence or 'san patricio del chanar' in evidence): return 0,'AMBIGUA'
    if any(t.startswith(norm(x)) for x in GENERIC_TITLES): return 0,'AGREGADOR'
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
            root=ET.fromstring(fetch('https://news.google.com/rss/search?q='+urllib.parse.quote(query+' when:14d')+'&hl=es-419&gl=AR&ceid=AR:es-419'))
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
  {'name':'AIC','role':'pronóstico de viento para El Chañar','mode':'DIRECTA-WEB','url':'https://www.aic.gob.ar/sitio/home?a=1015&z=1967225803'},
  {'name':'Open-Meteo','role':'respaldo meteorológico','mode':'DIRECTA-API','url':'https://open-meteo.com/'},
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
    # LEY MUNDIAL RADAR: ningún indicador se publica sin una fuente profesional
    # adecuada al fenómeno que pretende describir. Cada adaptador declara
    # procedencia, parser, unidad, temporalidad, semántica y fallback.
    'RUTA 7': {
        'primary': 'Dirección Provincial de Vialidad del Neuquén',
        'secondary': 'WSESTADORUTAS · sistema oficial de estado vial',
        'fallback': 'ninguno para estado operativo',
        'refresh': '30 min',
        'domain': 'estado de transitabilidad, cortes, obras y restricciones',
        'unit': 'estado vial / tramo / horario',
        'language': 'habilitación, precaución, reducción de calzada, corte, obra, desvío',
        'rule': 'fuente vial oficial > sistema oficial > referencia secundaria; nunca inferir transitabilidad desde ausencia de noticias'
    },
    'RUTA 8': {
        'primary': 'Dirección Provincial de Vialidad del Neuquén',
        'secondary': 'WSESTADORUTAS · sistema oficial de estado vial',
        'fallback': 'Ruta0 · referencia secundaria',
        'refresh': '30 min',
        'domain': 'estado de transitabilidad, cortes, obras y restricciones',
        'unit': 'estado vial / tramo / horario',
        'language': 'habilitación, precaución, reducción de calzada, corte, obra, desvío',
        'rule': 'fuente vial oficial > sistema oficial > referencia secundaria; nunca inferir transitabilidad desde ausencia de noticias'
    },
    'VIENTO': {
        'primary': 'Autoridad Interjurisdiccional de las Cuencas (AIC) · Pronóstico El Chañar',
        'secondary': 'Servicio Meteorológico Nacional',
        'fallback': 'Open-Meteo / MET Norway · solo transporte meteorológico secundario',
        'refresh': '30 min',
        'domain': 'viento meteorológico para El Chañar',
        'unit': 'km/h; ráfagas km/h; dirección; temperatura °C; presión hPa',
        'language': 'viento, ráfagas, dirección, temperatura, presión, pronóstico, observación',
        'rule': 'AIC es la autoridad primaria para el pronóstico local; si no entrega un valor válido, identificar expresamente la fuente secundaria utilizada'
    },
    'CAUDAL': {
        'primary': 'Autoridad Interjurisdiccional de las Cuencas (AIC) · Caudales Programados',
        'secondary': 'AIC · mediciones hidrológicas',
        'fallback': 'ninguno para dato actual; histórico solo fuera del indicador operativo',
        'refresh': '30 min',
        'domain': 'caudal programado/medido del sistema hídrico asociado a El Chañar',
        'unit': 'm³/s',
        'language': 'caudal mínimo, caudal máximo, erogado, programado, medido, fecha',
        'rule': 'no presentar un valor histórico como actual; observedAt corresponde al dato y fetchedAt a la consulta'
    },
    'ENERGÍA': {
        'primary': 'Ente Provincial de Energía del Neuquén (EPEN)',
        'secondary': 'EPEN · cortes programados / comunicados',
        'fallback': 'Municipalidad de San Patricio del Chañar · solo comunicación local',
        'refresh': '30 min',
        'domain': 'cortes programados y afectación del suministro eléctrico',
        'unit': 'sector / fecha / horario',
        'language': 'corte programado, mantenimiento, sectores afectados, horario, restitución',
        'rule': 'no convertir ausencia de publicación en normalidad del servicio'
    },
    'AGUA': {
        'primary': 'Ente Provincial de Agua y Saneamiento (EPAS)',
        'secondary': 'Municipalidad de San Patricio del Chañar',
        'fallback': 'Neuquén Informa',
        'refresh': '30 min',
        'domain': 'abastecimiento y saneamiento de agua',
        'unit': 'servicio / sector / fecha / horario',
        'language': 'interrupción, baja presión, abastecimiento, reparación, restablecimiento',
        'rule': 'EPAS es la referencia técnica primaria; nunca inferir servicio normal por ausencia de aviso'
    },
    'SERVICIOS': {
        'primary': 'Municipalidad de San Patricio del Chañar',
        'secondary': 'organismo provincial competente según servicio',
        'fallback': 'Neuquén Informa',
        'refresh': '30 min',
        'domain': 'avisos y prestación de servicios municipales',
        'unit': 'servicio / sector / fecha / horario',
        'language': 'aviso, atención, interrupción, mantenimiento, habilitación, horario',
        'rule': 'cada evento debe conservar el organismo responsable del servicio'
    },
    'SALUD': {
        'primary': 'Ministerio de Salud de la Provincia del Neuquén',
        'secondary': 'Hospital San Patricio del Chañar Dra. Alicia Cruz',
        'fallback': 'organismo sanitario provincial',
        'refresh': '30 min',
        'domain': 'atención sanitaria, servicios y avisos de salud',
        'unit': 'establecimiento / servicio / fecha / horario',
        'language': 'atención, guardia, turno, servicio, campaña, aviso sanitario',
        'rule': 'no inferir disponibilidad clínica desde silencio editorial'
    },
    'EDUCACIÓN': {
        'primary': 'Consejo Provincial de Educación del Neuquén',
        'secondary': 'Ministerio de Educación del Neuquén',
        'fallback': 'Neuquén Informa',
        'refresh': '30 min',
        'domain': 'actividad educativa oficial',
        'unit': 'establecimiento / nivel / fecha / horario',
        'language': 'suspensión, clases, jornada, calendario, inscripción, establecimiento',
        'rule': 'la condición educativa debe provenir de autoridad educativa competente'
    },
    'PRODUCCIÓN': {
        'primary': 'Ministerio de Producción e Industria del Neuquén',
        'secondary': 'organismo provincial productivo competente',
        'fallback': 'Municipalidad de San Patricio del Chañar',
        'refresh': '30 min',
        'domain': 'actividad productiva, agrícola y agroindustrial',
        'unit': 'programa / establecimiento / sector / fecha',
        'language': 'producción, cosecha, sanidad, riego, asistencia, programa, actividad',
        'rule': 'distinguir dato productivo de noticia general'
    },
    'EMERGENCIAS': {
        'primary': 'Secretaría de Emergencias y Gestión de Riesgos de la Provincia del Neuquén',
        'secondary': 'Bomberos Voluntarios de San Patricio del Chañar',
        'fallback': 'Municipalidad de San Patricio del Chañar',
        'refresh': '15 min',
        'domain': 'alertas, emergencias y respuesta operativa',
        'unit': 'evento / zona / fecha / horario',
        'language': 'alerta, emergencia, intervención, evacuación, prevención, incidente',
        'rule': 'solo publicar como emergencia lo que tenga fuente operativa o institucional identificable'
    },
    'TERRITORIO': {
        'primary': 'Municipalidad de San Patricio del Chañar',
        'secondary': 'organismo provincial competente según fenómeno',
        'fallback': 'Neuquén Informa',
        'refresh': '30 min',
        'domain': 'hechos territoriales con anclaje explícito en San Patricio del Chañar',
        'unit': 'lugar / sector / evento / fecha',
        'language': 'localización, sector, obra, servicio, actividad, intervención',
        'rule': 'todo hecho territorial debe conservar su anclaje geográfico verificable'
    },
    'CONVERSACIÓN': {
        'primary': 'medios locales identificables',
        'secondary': 'fuentes institucionales competentes',
        'fallback': 'medios regionales',
        'refresh': '30 min',
        'domain': 'agenda editorial local, no estado operativo',
        'unit': 'hecho / fecha / fuente',
        'language': 'tema, hecho, cobertura, fuente, fecha',
        'rule': 'este radar describe conversación editorial; nunca sustituye un indicador técnico u operativo'
    }
}

# ================================================================
# RADAR-DATA-CONTRACT-2.0
# Ley: indicador -> organismo competente -> adaptador -> validación ->
# unidad -> temporalidad -> semántica -> procedencia.
# ================================================================
CONTRACT_VERSION="RADAR-DATA-CONTRACT-2.0"

INDICATOR_TECHNICAL_CONTRACTS={
    "RUTA 7":{"dataType":"road_operational_state","geography":"RP7 · tramo identificado","temporalField":"validFrom/validTo","parser":"DPV road-state parser","validation":"estado vial explícito + tramo + vigencia + fuente competente"},
    "RUTA 8":{"dataType":"road_operational_state","geography":"RP8 · tramo identificado","temporalField":"validFrom/validTo","parser":"DPV road-state parser","validation":"estado vial explícito + tramo + vigencia + fuente competente"},
    "VIENTO":{"dataType":"meteorological_forecast","geography":"El Chañar","temporalField":"forecastPeriod","parser":"AIC El Chañar forecast parser","validation":"km/h + ráfagas + dirección + clasificación de pronóstico"},
    "CAUDAL":{"dataType":"hydrological_program","geography":"Compensador/embalse El Chañar","temporalField":"programDate","parser":"AIC programmed-flow parser","validation":"m³/s + fecha + sitio + semántica programada"},
    "ENERGÍA":{"dataType":"electricity_service_event","geography":"San Patricio del Chañar / sector","temporalField":"eventStart/eventEnd","parser":"EPEN outage parser","validation":"sector + evento + fecha/hora + EPEN"},
    "AGUA":{"dataType":"water_service_event","geography":"San Patricio del Chañar / sector","temporalField":"eventDate/time","parser":"EPAS notice parser","validation":"sector + evento hídrico + fecha/hora + EPAS"},
    "SERVICIOS":{"dataType":"public_service_event","geography":"área del servicio","temporalField":"eventDate/time","parser":"competent-service parser","validation":"servicio + organismo responsable + evento + fecha"},
    "SALUD":{"dataType":"health_service_notice","geography":"establecimiento/cobertura","temporalField":"eventDate/time","parser":"health-authority parser","validation":"establecimiento + servicio + fecha + autoridad sanitaria"},
    "EDUCACIÓN":{"dataType":"education_notice","geography":"establecimiento/nivel","temporalField":"eventDate/time","parser":"CPE notice parser","validation":"establecimiento + evento educativo + fecha + CPE"},
    "PRODUCCIÓN":{"dataType":"productive_notice","geography":"cadena/establecimiento/sector","temporalField":"eventDate","parser":"productive-authority parser","validation":"actividad productiva + anclaje local + fecha + fuente competente"},
    "EMERGENCIAS":{"dataType":"emergency_operational_event","geography":"zona del evento","temporalField":"alertTime/eventTime","parser":"emergency-authority parser","validation":"evento + zona + timestamp + fuente operativa"},
    "TERRITORIO":{"dataType":"territorial_event","geography":"lugar/sector local","temporalField":"eventDate","parser":"municipal/competent-authority parser","validation":"anclaje geográfico + organismo + evento + fecha"},
    "CONVERSACIÓN":{"dataType":"editorial_event","geography":"San Patricio del Chañar","temporalField":"publishedAt","parser":"RSS/web parser","validation":"relevancia local + fecha + URL + identidad de fuente"}
}

AUXILIARY_INDICATOR_CONTRACTS={
    "TEMPERATURA":{
        "primary":"AIC · Pronóstico El Chañar",
        "secondary":"Servicio Meteorológico Nacional",
        "domain":"temperatura meteorológica local",
        "unit":"°C",
        "language":"temperatura mínima, temperatura máxima, período de pronóstico",
        "rule":"distinguir pronóstico de observación"
    },
    "NIVEL_RIO":{
        "primary":"AIC · estación COMPENSADOR EL CHANAR",
        "secondary":"AIC · mediciones hidrológicas",
        "domain":"altura de río/lago",
        "unit":"m",
        "language":"altura de río/lago, fecha de actualización",
        "rule":"no publicar sin sitio de estación y timestamp"
    },
    "CAUDAL_OBSERVADO":{
        "primary":"AIC · estación COMPENSADOR EL CHANAR",
        "secondary":"AIC · mediciones hidrológicas",
        "domain":"caudal medio diario medido",
        "unit":"m³/s",
        "language":"caudal medio diario medido, fecha",
        "rule":"no mezclar con caudal saliente programado"
    },
    "CALIDAD_AIRE":{
        "primary":"Ministerio de Salud de Neuquén · red de monitoreo de calidad del aire",
        "secondary":"Sustentabilidad Sin Fronteras / estación cuando esté operativa",
        "domain":"calidad del aire local",
        "unit":"PM2.5 y parámetros publicados",
        "language":"PM2.5, contaminante, concentración, fecha/hora",
        "rule":"no publicar Chañar hasta verificar estación local operativa y lectura accesible"
    },
    "RIESGO_INCENDIO":{
        "primary":"Servicio Meteorológico Nacional · Índice de Peligro de Incendios FWI",
        "secondary":"autoridad provincial de manejo del fuego",
        "domain":"peligro meteorológico de incendios",
        "unit":"índice/clase",
        "language":"peligro bajo, moderado, alto, muy alto, extremo, FWI y vigencia",
        "rule":"no inferir peligro de incendio solo a partir de viento o temperatura"
    },
    "ESTADO_TRANSITO":{
        "primary":"autoridad vial competente según corredor",
        "secondary":"autoridad de tránsito competente según jurisdicción",
        "domain":"estado de tránsito de un corredor/tramo",
        "unit":"tramo / evento / vigencia",
        "language":"restricción, incidente, desvío, demora, corte, circulación",
        "rule":"no mezclar RP, RN y tránsito urbano bajo una sola fuente"
    }
}

def audit_contract_registry():
    required=("primary","domain","unit","language","rule")
    technical=("dataType","geography","temporalField","parser","validation")
    audit={}
    for name,contract in SOURCE_CONTRACTS.items():
        missing=[k for k in required if not contract.get(k)]
        tech=INDICATOR_TECHNICAL_CONTRACTS.get(name,{})
        missing += ["technical."+k for k in technical if not tech.get(k)]
        audit[name]={"valid":not missing,"missing":missing,"primary":contract.get("primary"),"domain":contract.get("domain"),"unit":contract.get("unit"),"language":contract.get("language"),"technical":tech}
    failures=[k for k,v in audit.items() if not v["valid"]]
    if failures:
        raise RuntimeError("CONTRATO DE DATOS INCOMPLETO: "+", ".join(failures))
    return audit

CONTRACT_AUDIT=audit_contract_registry()

def collect_operational():
    # Solo la fuente profesional puede crear un estado operativo.
    op={'updatedAt':NOW.isoformat(),'route7':None,'route8':None,'energy':None,'water':None,'sources':[]}

    def attempt(name,url,kind,tier):
        try:
            raw=fetch(url)
            op['sources'].append({'name':name,'tier':tier,'mode':'reachable','kind':kind,'url':url})
            return raw
        except Exception as e:
            op['sources'].append({'name':name,'tier':tier,'mode':'connection_error','kind':kind,'url':url,'error':type(e).__name__})
            return ''

    dpv='https://www.dpvneuquen.gov.ar/'
    raw=attempt('Dirección Provincial de Vialidad',dpv,'road_official','primary')
    road_evidence={}
    if raw:
        plain=clean(re.sub(r'\\s+',' ',re.sub(r'<[^>]+>',' ',raw)))
        road_evidence={'route7Mention':bool(re.search(r'Ruta[ ]*7|RP[ ]*7',plain,re.I)),'route8Mention':bool(re.search(r'Ruta[ ]*8|RP[ ]*8',plain,re.I))}
    for key in ('route7','route8'):
        op[key]={'source':'Dirección Provincial de Vialidad','sourceTier':'primary','sourceUrl':dpv,'semanticState':None,'publicationState':'source_reachable_no_current_machine_readable_state' if raw else 'source_unreachable','retrievedAt':NOW.isoformat(),'evidence':road_evidence}

    eurl='https://www.epen.gov.ar/index.php/cortes-programados/'
    eraw=attempt('EPEN',eurl,'electricity_official','primary')
    hits=[]
    if eraw:
        et=clean(re.sub(r'\\s+',' ',re.sub(r'<[^>]+>',' ',eraw)))
        hits=[m.group(0) for m in re.finditer(r'.{0,180}(?:San Patricio del Chañar|El Chañar).{0,420}',et,re.I)]
    op['energy']={'source':'EPEN','sourceTier':'primary','sourceUrl':eurl,'semanticState':'corte_programado' if hits else None,'eventType':'scheduled_outage' if hits else None,'detail':' '.join(hits[:3])[:1000] if hits else None,'publicationState':'specific_local_notice_found' if hits else ('source_reachable_no_specific_local_notice' if eraw else 'source_unreachable'),'retrievedAt':NOW.isoformat()}

    aurl='https://www.epas.gov.ar/'
    araw=attempt('EPAS',aurl,'water_official','primary')
    whits=[]
    if araw:
        at=clean(re.sub(r'\\s+',' ',re.sub(r'<[^>]+>',' ',araw)))
        whits=[m.group(0) for m in re.finditer(r'.{0,180}(?:San Patricio del Chañar|El Chañar|corte de agua|abastecimiento|baja presión|interrupción|restablecimiento).{0,420}',at,re.I)]
    op['water']={'source':'EPAS','sourceTier':'primary','sourceUrl':aurl,'semanticState':'evento_hidrico_publicado' if whits else None,'eventType':'water_service_event' if whits else None,'detail':' '.join(whits[:2])[:900] if whits else None,'publicationState':'specific_local_notice_found' if whits else ('source_reachable_no_specific_local_notice' if araw else 'source_unreachable'),'retrievedAt':NOW.isoformat()}
    return op


def collect_environment():
    env={'weather':None,'hydrology':None,'sources':[],'updatedAt':NOW.isoformat()}
    aic_url='https://www.aic.gob.ar/sitio/home?a=1015&z=1967225803'
    try:
        html=fetch(aic_url)
        plain=clean(re.sub(r'<[^>]+>',' ',html))
        idx=plain.lower().find('pronóstico para el chañar')
        block=plain[idx:idx+5000] if idx>=0 else plain[:5000]
        vm=re.search(r'Viento[ ]+([0-9]{1,3})[ ]*km/h',block,re.I)
        gm=re.search(r'Ráfagas[ ]+([0-9]{1,3})[ ]*km/h',block,re.I)
        dm=re.search(r'Dirección[ ]+([A-ZÁÉÍÓÚÑ/]{1,6})',block,re.I)
        tm=re.search(r'Temperatura[ ]+(-?[0-9]{1,3})[ ]*ºC',block,re.I)
        if vm:
            env['weather']={'dataType':'forecast','forecastWindKmh':float(vm.group(1)),'forecastGustKmh':float(gm.group(1)) if gm else None,'forecastWindDirection':dm.group(1) if dm else None,'forecastTemperatureC':float(tm.group(1)) if tm else None,'retrievedAt':NOW.isoformat(),'source':'AIC','sourceTier':'primary','sourceUrl':aic_url,'semanticState':'pronostico_local'}
            env['sources'].append({'name':'AIC · Pronóstico El Chañar','tier':'primary','mode':'parsed','url':aic_url})
        else:
            env['sources'].append({'name':'AIC · Pronóstico El Chañar','tier':'primary','mode':'reachable_but_unparsed','url':aic_url})
    except Exception as e:
        env['sources'].append({'name':'AIC · Pronóstico El Chañar','tier':'primary','mode':'connection_error','error':type(e).__name__,'url':aic_url})

    hurl='https://www.aic.gob.ar/sitio/caudales'
    try:
        ht=fetch(hurl)
        plain=clean(re.sub(r'<[^>]+>',' ',ht))
        row=re.search(r'El Chañar[ ]*[|][ ]*([0-9]+)[ ]*[|][ ]*((?:[0-9]+[ ]*[|][ ]*){5}[0-9]+)[ ]*([0-9]+(?:[ ]*[|][ ]*[0-9]+){5})',plain,re.I)
        if row:
            max_vals=[int(x) for x in re.findall(r'[0-9]+',row.group(2))]
            min_vals=[int(x) for x in re.findall(r'[0-9]+',row.group(3))]
            env['hydrology']={'site':'El Chañar','flowType':'programmed_outflow','erogatedM3s':int(row.group(1)),'programmedMaxM3s':max_vals,'programmedMinM3s':min_vals,'currentProgrammedMaxM3s':max_vals[0] if max_vals else None,'currentProgrammedMinM3s':min_vals[0] if min_vals else None,'programDate':(NOW+timedelta(days=1)).strftime('%Y-%m-%d'),'tableDate':NOW.strftime('%Y-%m-%d'),'retrievedAt':NOW.isoformat(),'source':'AIC','sourceTier':'primary','sourceUrl':hurl,'semanticState':'caudal_programado'}
            env['sources'].append({'name':'AIC · Caudales Programados','tier':'primary','mode':'parsed','url':hurl})
        else:
            env['sources'].append({'name':'AIC · Caudales Programados','tier':'primary','mode':'reachable_but_unparsed','url':hurl})
    except Exception as e:
        env['sources'].append({'name':'AIC · Caudales Programados','tier':'primary','mode':'connection_error','error':type(e).__name__,'url':hurl})
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
        semantic_labels={
            'CONVERSACIÓN':'cobertura editorial',
            'SERVICIOS':'evidencia de servicio',
            'SALUD':'evidencia sanitaria',
            'EDUCACIÓN':'evidencia educativa',
            'PRODUCCIÓN':'evidencia productiva',
            'EMERGENCIAS':'cobertura de emergencia',
            'TERRITORIO':'hecho territorial',
            'RUTA 7':'estado vial',
            'RUTA 8':'estado vial',
            'ENERGÍA':'evento eléctrico',
            'AGUA':'evento hídrico',
            'VIENTO':'pronóstico meteorológico'
        }
        status=semantic_labels.get(code,'señal editorial')
        if code=='VIENTO' and environment.get('weather'):
            status='pronóstico local'
            matches=environment['weather'].get('forecastWindKmh') if environment['weather'].get('forecastWindKmh') is not None else matches
        out.append({'id':code,'label':label,'signal':matches,'status':status,'freshnessHours':age,'mode':('DATO DIRECTO' if code=='VIENTO' and environment.get('weather') else mode),'evidenceCount':sum(1 for e in events if any(t in norm(e.get('title','')+' '+str(e.get('description',''))) for t in terms))})
    for radar in out:
        radar['sourceContract']=SOURCE_CONTRACTS.get(radar['id'])
        radar['contractVersion']=CONTRACT_VERSION
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
    priority=['DEPORTE','CULTURA / TURISMO','SALUD','EDUCACIÓN','MOVILIDAD','PRODUCCIÓN','SEGURIDAD / EMERGENCIAS','INSTITUCIONES','SERVICIOS']
    scores={topic:sum(norm(t) in text for t in terms) for topic,terms in TOPIC_RULES}
    active=[(scores.get(topic,0),-priority.index(topic),topic) for topic in priority if scores.get(topic,0)]
    return max(active)[2] if active else 'OTROS'

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
    if sim>=0.35 and topic and overlap>=0.50: return sim
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

def consolidate_related_events(events):
    out=[]
    for e in events:
        merged=False
        for base in out:
            if e.get('topic')!=base.get('topic'): continue
            ea=set(e.get('territorialAnchors',[])); ba=set(base.get('territorialAnchors',[]))
            if not (ea & ba): continue
            da=parse_date(e.get('publishedAt')); db=parse_date(base.get('publishedAt'))
            if not da or not db or abs((da-db).total_seconds())>2*86400: continue
            # Same territorial node + same topic within 48h = one underlying local fact.
            base['sources']=list(dict.fromkeys((base.get('sources',[])+e.get('sources',[]))))[:8]
            base['sourceCount']=len(base['sources'])
            base['coverage']=max(base.get('coverage',1),0)+e.get('coverage',1)
            base['directSourceCount']=max(base.get('directSourceCount',0),e.get('directSourceCount',0))
            base['items']=(base.get('items',[])+e.get('items',[]))[:8]
            base['territorialAnchors']=list(dict.fromkeys(base.get('territorialAnchors',[])+e.get('territorialAnchors',[])))[:8]
            base['publishedAt']=max(base.get('publishedAt',''),e.get('publishedAt',''))
            base['lastSeen']=max(base.get('lastSeen',''),e.get('lastSeen',''))
            base['movement']=max(base.get('movement',0),e.get('movement',0))
            base['newSources']=list(dict.fromkeys(base.get('newSources',[])+e.get('newSources',[])))[:8]
            base['sourceDiversity']=len(base['sources'])
            merged=True
            break
        if not merged: out.append(e)
    return out

events=consolidate_related_events(events)

# INCIDENCIA no es una segunda lista de noticias.
# Es una capa de hechos con capacidad de afectar/explicar algo local y con anclaje
# territorial verificable. Señales queda reservada al movimiento informativo que no
# entra en esa capa, evitando repetir el mismo hecho en dos lugares.
INCIDENCE_TOPICS={'SALUD','EDUCACIÓN','MOVILIDAD','SERVICIOS','SEGURIDAD / EMERGENCIAS','INSTITUCIONES','PRODUCCIÓN'}
def incidence_eligible(e):
    anchors_set=set(e.get('territorialAnchors',[]))
    strong_anchor=bool(anchors_set)
    operational_topic=e.get('topic') in INCIDENCE_TOPICS
    direct=e.get('relevance',0)>=3
    # Deportes/cultura pueden ser señales, pero no se convierten automáticamente
    # en "incidencia" sin un contrato operativo específico.
    return bool(strong_anchor and direct and operational_topic)

incidence_ids={e.get('eventId') for e in events if incidence_eligible(e)}
for e in events:
    e['view']='INCIDENCIA' if e.get('eventId') in incidence_ids else 'SEÑAL'
    e['incidenceEligible']=e.get('eventId') in incidence_ids
    e['signalReason']='movimiento informativo / cobertura / diversidad de fuentes' if not e['incidenceEligible'] else 'reservado a incidencia territorial'
    e['incidenceReason']='anclaje directo + tema operativo/local' if e['incidenceEligible'] else None

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
precision_rules = {
    'DIRECTA': 'requiere localidad explícita o anclaje territorial fuerte; no alcanza una mención regional genérica',
    'CON ANCLA LOCAL': 'requiere al menos un nodo territorial local identificable; se conserva como señal secundaria',
    'FALSO POSITIVO': 'rechazar agregadores, títulos genéricos, ambigüedades geográficas, contexto regional sin anclaje o términos aislados débiles',
    'OPERATIVO': 'un dato operativo solo puede declararse confirmado por fuente directa/oficial; medios y buscadores no lo convierten en estado operativo',
    'TEMPORAL': 'la antigüedad afecta frescura, pero una fuente caída no se interpreta como ausencia del hecho',
}

def build_precision_audit(dedup_items, fresh_items):
    rejected=[]
    for x in fresh_items:
        score,label=relevance(x.get('title',''),x.get('description',''))
        if score < 2:
            rejected.append({'source':x.get('source',''),'reason':label,'title':x.get('title','')[:180],'query':x.get('query','')})
    matrix={}
    for x in dedup_items:
        key=(x.get('source','DESCONOCIDA'),classify(x))
        m=matrix.setdefault(key,{'source':key[0],'topic':key[1],'accepted':0,'direct':0,'anchored':0,'falsePositives':0,'territorialTerms':[]})
        m['accepted']+=1
        m['direct']+=1 if x.get('relevance')==3 else 0
        m['anchored']+=1 if x.get('relevance')==2 else 0
        for term in anchors(x):
            if term not in m['territorialTerms']: m['territorialTerms'].append(term)
    for r in rejected:
        key=(r['source'] or 'DESCONOCIDA','RECHAZADO · '+r['reason'])
        m=matrix.setdefault(key,{'source':key[0],'topic':key[1],'accepted':0,'direct':0,'anchored':0,'falsePositives':0,'territorialTerms':[]})
        m['falsePositives']+=1
    source_summary=[]
    for s in SOURCE_CATALOG:
        name=s['name']; accepted=[x for x in dedup_items if x.get('source')==name]; rej=[r for r in rejected if r.get('source')==name]
        source_summary.append({'source':name,'group':s['group'],'role':s['role'],'accepted':len(accepted),'direct':sum(x.get('relevance')==3 for x in accepted),'anchored':sum(x.get('relevance')==2 for x in accepted),'falsePositives':len(rej),'falsePositiveTypes':sorted(set(r['reason'] for r in rej)),'topics':sorted(set(classify(x) for x in accepted))})
    language_precision=[]
    for term in LOCAL_ENTITIES:
        n=norm(term); acc=[x for x in dedup_items if n in norm(x.get('title','')+' '+x.get('description',''))]; rej=[r for r in rejected if n in norm(r.get('title',''))]
        language_precision.append({'term':term,'acceptedHits':len(acc),'directHits':sum(x.get('relevance')==3 for x in acc),'rejectedTitleHits':len(rej),'territorialStrength':'FUERTE' if term in STRONG_LOCAL else ('CORREDOR' if term in {'ruta 7','ruta 8'} else 'DÉBIL')})
    fp={}
    for r in rejected: fp[r['reason']]=fp.get(r['reason'],0)+1
    return {'version':'1.0','rule':'source × signal × local language × false positive','sourceSummary':source_summary,'matrix':sorted(matrix.values(),key=lambda r:(-r['falsePositives'],-r['accepted'],r['source'],r['topic'])),'languagePrecision':language_precision,'falsePositiveSummary':fp,'rejectedSamples':rejected[:80],'rules':precision_rules,'interpretation':'auditoría de precisión del colector; no mide verdad periodística ni importancia del hecho'}

source_audit=[]
all_sources=list(dict.fromkeys([x.get('source') for x in dedup if x.get('source')]))
for catalog in SOURCE_CATALOG:
    name=catalog['name']
    hits=[x for x in dedup if x.get('source')==name]
    source_audit.append({
        'name':name,'group':catalog['group'],'role':catalog['role'],'url':catalog['url'],
        'signals':len(hits),'directSignals':sum(x.get('relevance')==3 for x in hits),
        'anchoredSignals':sum(x.get('relevance')==2 for x in hits),
        'lastSeen':max((x.get('publishedAt') for x in hits),default=None),
        'status':'CON SEÑALES' if hits else 'SIN SEÑALES EN VENTANA',
        'note':'ausencia de señales no equivale a ausencia del hecho'
    })
language_audit=[]
for term in LOCAL_ENTITIES:
    n=norm(term)
    hits=[x for x in dedup if n in norm(x.get('title','')+' '+x.get('description',''))]
    language_audit.append({'term':term,'hits':len(hits),'direct':sum(x.get('relevance')==3 for x in hits)})
language_audit=sorted(language_audit,key=lambda x:(x['hits'],x['term']),reverse=True)
precision_audit=build_precision_audit(dedup,fresh)
# Reemplazaremos la auditoría de precisión por una versión basada en los eventos finales más abajo.
stats={'total':len(dedup),'direct':sum(x['relevance']==3 for x in dedup),'regional':sum(x['relevance']==2 for x in dedup),'new':sum(x.get('isNew',False) for x in dedup),'sources':len({x['source'] for x in dedup}),'directSignals':sum(x['collection'].startswith('DIRECTA') for x in dedup),'localDirectSignals':sum(x.get('sourcePriority')==1 for x in dedup),'radioDirectSignals':sum(x.get('sourceType')=='RADIO LOCAL' for x in dedup),'precisionRule':'evidence-first','searchNoiseRejected':sum(1 for x in fresh if relevance(x.get('title',''),x.get('description',''))[1] in {'AGREGADOR','SIN ANCLA','AMBIGUA'})}
def build_precision_audit_from_events(events):
    rows=[]
    for e in events:
        topic=e.get('topic','OTROS')
        for item in e.get('items',[]):
            rows.append({
                'source':item.get('source','DESCONOCIDA'),
                'topic':topic,
                'accepted':1,
                'direct':1 if item.get('relevance')==3 else 0,
                'anchored':1 if item.get('relevance')==2 else 0,
                'territorialTerms':e.get('territorialAnchors',[])[:8],
                'falsePositive':0
            })
    matrix={}
    for r in rows:
        key=(r['source'],r['topic'])
        m=matrix.setdefault(key,{'source':key[0],'topic':key[1],'accepted':0,'direct':0,'anchored':0,'falsePositives':0,'territorialTerms':[]})
        m['accepted']+=1; m['direct']+=r['direct']; m['anchored']+=r['anchored']
        for t in r['territorialTerms']:
            if t not in m['territorialTerms']: m['territorialTerms'].append(t)
    source_summary=[]
    known={s['name']:s for s in SOURCE_CATALOG}
    observed=sorted({r['source'] for r in rows})
    for name in sorted(set(known)|set(observed)):
        accepted=[r for r in rows if r['source']==name]
        meta=known.get(name,{})
        source_summary.append({'source':name,'group':meta.get('group','OBSERVADA'),'role':meta.get('role','fuente detectada fuera del catálogo'),'accepted':len(accepted),'direct':sum(r['direct'] for r in accepted),'anchored':sum(r['anchored'] for r in accepted),'falsePositives':0,'falsePositiveTypes':[],'topics':sorted(set(r['topic'] for r in accepted))})
    language_precision=[]
    for term in LOCAL_ENTITIES:
        n=norm(term)
        hits=[x for e in events for x in e.get('items',[]) if n in norm(x.get('title','')+' '+x.get('description',''))]
        language_precision.append({'term':term,'acceptedHits':len(hits),'directHits':sum(x.get('relevance')==3 for x in hits),'rejectedTitleHits':0,'territorialStrength':'FUERTE' if term in STRONG_LOCAL else ('CORREDOR' if term in {'ruta 7','ruta 8'} else 'DÉBIL')})
    return {'version':'1.1','rule':'source × signal × local language × false positive','sourceSummary':source_summary,'matrix':sorted(matrix.values(),key=lambda r:(-r['accepted'],-r['direct'],r['source'],r['topic'])),'languagePrecision':language_precision,'falsePositiveSummary':{},'rejectedSamples':[],'rules':precision_rules,'interpretation':'auditoría sobre eventos aceptados; la próxima capa debe instrumentar rechazos antes del clustering'}

precision_audit=build_precision_audit_from_events(events)
output={'updatedAt':now,'window':f'{DAYS} días','purpose':'Detectar qué se está moviendo en San Patricio del Chañar y mostrar de dónde surge cada señal.','architecture':'contrato universal de procedencia + fuentes profesionales + adaptadores específicos + validación semántica + temporalidad + evidencia editorial separada','keywords':[q for q,_ in QUERIES],'sourceRegistry':status,'sourceCatalog':SOURCE_CATALOG,'sourceAudit':source_audit,'languageAudit':language_audit,'precisionAudit':precision_audit,'stats':stats,'environment':environment,'operational':operational,'sourceContracts':SOURCE_CONTRACTS,'contractAudit':CONTRACT_AUDIT,'auxiliaryIndicatorContracts':AUXILIARY_INDICATOR_CONTRACTS,'contractVersion':CONTRACT_VERSION,'systemRadars':system_radars,'system':{'memoryDays':MEMORY_DAYS,'eventIdentity':'estable entre actualizaciones','evidenceRule':'evidence-first','movementRule':'descriptivo: recencia + cobertura + diversidad de fuentes; no es ranking de importancia','sourceFailureRule':'no inferir desaparición cuando las fuentes conocidas no responden','infrastructureRule':'una señal editorial no equivale a confirmación operativa; los datos directos se etiquetan por separado','lifecycle':['EMERGENTE','ACTIVO','SOSTENIDO','EN DESCENSO','RECIENTE'],'sourceHealth':status},'events':events,'items':dedup}
with open(OUT,'w',encoding='utf-8') as f: json.dump(output,f,ensure_ascii=False,indent=2)
print('PULSO:',stats,'RADARES:',len(system_radars))
