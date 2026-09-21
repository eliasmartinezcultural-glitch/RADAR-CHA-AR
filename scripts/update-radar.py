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
def clean(s): return re.sub(r'\\s+',' ',s or '').strip()
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

# ================================================================
# CONTRATO UNIVERSAL DE DATOS RADAR
# ================================================================
# LEY MUNDIAL:
# 1) Un indicador no nace de una tarjeta: nace de un fenómeno.
# 2) Cada fenómeno tiene que tener una autoridad/fuente competente.
# 3) La fuente debe declarar qué mide, unidad, temporalidad y semántica.
# 4) Una fuente secundaria nunca puede disfrazarse de primaria.
# 5) Si el dato no puede ser validado, RADAR NO INVENTA un estado.
# 6) "sin novedad", "normal", "habilitado", "cerrado" y "sin parte" NO son
#    estados universales. Cada indicador tiene su propio vocabulario.
# 7) Toda futura incorporación debe entrar primero en este registro.
# ================================================================

CONTRACT_VERSION = "RADAR-DATA-CONTRACT-2.0"

SOURCE_CONTRACTS = {
    "CONVERSACIÓN": {
        "primary": "medios locales identificables",
        "secondary": "fuentes institucionales competentes según el hecho",
        "fallback": "medios regionales",
        "domain": "agenda editorial local",
        "unit": "hecho / fuente / fecha",
        "language": "tema, cobertura, fuente, fecha, territorio",
        "refresh": "30 min",
        "rule": "es señal editorial; jamás confirma por sí sola un estado técnico u operativo"
    },
    "RUTA 7": {
        "primary": "Dirección Provincial de Vialidad del Neuquén",
        "secondary": "sistema oficial de estado vial de Vialidad Neuquén",
        "fallback": "ninguno para estado operativo",
        "domain": "transitabilidad de la Ruta Provincial 7",
        "unit": "tramo / estado vial / vigencia / horario",
        "language": "habilitada, precaución, reducción de calzada, corte intermitente, corte total, obra, desvío, restricción",
        "refresh": "30 min",
        "rule": "solo una publicación o sistema vial competente puede establecer el estado; si no hay dato parseable, no se reemplaza por una inferencia de prensa"
    },
    "RUTA 8": {
        "primary": "Dirección Provincial de Vialidad del Neuquén",
        "secondary": "sistema oficial de estado vial de Vialidad Neuquén",
        "fallback": "ninguno para estado operativo",
        "domain": "transitabilidad de la Ruta Provincial 8",
        "unit": "tramo / estado vial / vigencia / horario",
        "language": "habilitada, precaución, reducción de calzada, corte intermitente, corte total, obra, desvío, restricción",
        "refresh": "30 min",
        "rule": "solo una publicación o sistema vial competente puede establecer el estado; si no hay dato parseable, no se reemplaza por una inferencia de prensa"
    },
    "VIENTO": {
        "primary": "Autoridad Interjurisdiccional de las Cuencas (AIC) · pronóstico El Chañar",
        "secondary": "Servicio Meteorológico Nacional",
        "fallback": "Open-Meteo / MET Norway, explícitamente como modelo meteorológico secundario",
        "domain": "pronóstico meteorológico local de viento",
        "unit": "km/h / ráfagas km/h / dirección",
        "language": "velocidad del viento, ráfagas, dirección, período de pronóstico",
        "refresh": "30 min",
        "rule": "AIC es primaria para el pronóstico local; nunca llamar 'observación' a un valor que proviene de un pronóstico"
    },
    "TEMPERATURA": {
        "primary": "Autoridad Interjurisdiccional de las Cuencas (AIC) · pronóstico El Chañar",
        "secondary": "Servicio Meteorológico Nacional",
        "fallback": "Open-Meteo / MET Norway, explícitamente como modelo meteorológico secundario",
        "domain": "temperatura meteorológica local",
        "unit": "°C",
        "language": "temperatura, mínima, máxima, período de pronóstico",
        "refresh": "30 min",
        "rule": "el tipo de dato debe conservarse como pronóstico u observación; nunca mezclar ambos"
    },
    "CAUDAL": {
        "primary": "Autoridad Interjurisdiccional de las Cuencas (AIC) · Caudales Programados",
        "secondary": "AIC · red/mediciones hidrológicas cuando corresponda al sitio",
        "fallback": "ninguno para dato actual; último valor solo puede conservarse como histórico",
        "domain": "caudal programado del sistema hídrico asociado a El Chañar",
        "unit": "m³/s",
        "language": "caudal programado, mínimo programado, máximo programado, fecha del programa",
        "refresh": "30 min",
        "rule": "El Chañar debe identificarse como sitio de la tabla; no convertir caudal programado en caudal observado del río en la localidad"
    },
    "ENERGÍA": {
        "primary": "Ente Provincial de Energía del Neuquén (EPEN)",
        "secondary": "EPEN · comunicados y cronogramas oficiales",
        "fallback": "Municipalidad, solo como canal de comunicación",
        "domain": "suministro eléctrico y cortes publicados",
        "unit": "sector / fecha / hora / evento",
        "language": "corte programado, mantenimiento, sectores afectados, inicio, restitución",
        "refresh": "30 min",
        "rule": "la ausencia de un aviso no se transforma en servicio normal"
    },
    "AGUA": {
        "primary": "Ente Provincial de Agua y Saneamiento (EPAS)",
        "secondary": "Municipalidad de San Patricio del Chañar, como comunicación local",
        "fallback": "Neuquén Informa, como comunicación oficial provincial",
        "domain": "abastecimiento y saneamiento de agua",
        "unit": "sector / evento / fecha / hora",
        "language": "interrupción, baja presión, restricción de suministro, reparación, restablecimiento, obra",
        "refresh": "30 min",
        "rule": "EPAS es la referencia técnica; no publicar un estado de servicio cuando solo existe silencio de la fuente"
    },
    "SERVICIOS": {
        "primary": "organismo competente del servicio concreto",
        "secondary": "Municipalidad de San Patricio del Chañar cuando sea servicio municipal",
        "fallback": "Neuquén Informa",
        "domain": "prestación concreta de servicios públicos",
        "unit": "servicio / sector / evento / fecha / hora",
        "language": "interrupción, mantenimiento, obra, atención, horario, restitución, habilitación",
        "refresh": "30 min",
        "rule": "cada registro debe identificar qué servicio es y qué organismo lo presta; 'servicios' no puede funcionar como cajón de sastre"
    },
    "SALUD": {
        "primary": "Ministerio de Salud de la Provincia del Neuquén",
        "secondary": "Hospital San Patricio del Chañar Dra. Alicia Cruz",
        "fallback": "organismo sanitario provincial competente",
        "domain": "servicios y comunicaciones sanitarias oficiales",
        "unit": "establecimiento / servicio / fecha / hora",
        "language": "guardia, atención, turno, servicio, campaña, vacunación, aviso sanitario",
        "refresh": "30 min",
        "rule": "no inferir disponibilidad clínica, capacidad o normalidad desde una ausencia de publicación"
    },
    "EDUCACIÓN": {
        "primary": "Consejo Provincial de Educación del Neuquén",
        "secondary": "Ministerio de Educación del Neuquén",
        "fallback": "Neuquén Informa",
        "domain": "actividad educativa oficial",
        "unit": "establecimiento / nivel / fecha / jornada",
        "language": "suspensión de clases, jornada, calendario, inscripción, establecimiento, medida educativa",
        "refresh": "30 min",
        "rule": "un medio puede detectar conversación; solo autoridad educativa puede confirmar una condición educativa"
    },
    "PRODUCCIÓN": {
        "primary": "Ministerio de Producción e Industria del Neuquén",
        "secondary": "organismo productivo competente según cadena",
        "fallback": "Municipalidad de San Patricio del Chañar",
        "domain": "actividad productiva, agrícola y agroindustrial",
        "unit": "cadena / establecimiento / programa / fecha",
        "language": "producción, cosecha, sanidad, riego, asistencia, programa, actividad productiva",
        "refresh": "60 min",
        "rule": "distinguir anuncio institucional, programa, dato productivo y noticia periodística"
    },
    "EMERGENCIAS": {
        "primary": "Secretaría de Emergencias y Gestión de Riesgos de la Provincia del Neuquén",
        "secondary": "Sistema Integrado de Emergencias del Neuquén (SIEN) / organismo operativo competente",
        "fallback": "Bomberos Voluntarios de San Patricio del Chañar / Municipalidad, según el evento",
        "domain": "alertas y respuesta operativa ante emergencias",
        "unit": "evento / zona / fecha / hora",
        "language": "alerta, incidente, intervención, evacuación, prevención, emergencia, respuesta",
        "refresh": "15 min",
        "rule": "solo un organismo operativo o institucional identificable puede elevar una señal a emergencia"
    },
    "TERRITORIO": {
        "primary": "Municipalidad de San Patricio del Chañar para hechos municipales",
        "secondary": "organismo provincial competente según fenómeno",
        "fallback": "Neuquén Informa",
        "domain": "hechos territoriales con anclaje geográfico verificable",
        "unit": "lugar / sector / evento / fecha",
        "language": "lugar, sector, obra, intervención, actividad, localización",
        "refresh": "30 min",
        "rule": "el organismo debe ser competente para el hecho; territorio no autoriza a mezclar cualquier fuente"
    }
}

INDICATOR_TECHNICAL_CONTRACTS = {
    "CONVERSACIÓN":{"dataType":"editorial_event","geography":"San Patricio del Chañar","temporalField":"publishedAt","parser":"rss/web article parser","validation":"local relevance + date + URL + source identity"},
    "RUTA 7":{"dataType":"road_operational_state","geography":"RP7 · tramo identificado","temporalField":"validFrom/validTo when published","parser":"DPV road-state parser","validation":"road identity + explicit state vocabulary + vigency + source competence"},
    "RUTA 8":{"dataType":"road_operational_state","geography":"RP8 · tramo identificado","temporalField":"validFrom/validTo when published","parser":"DPV road-state parser","validation":"road identity + explicit state vocabulary + vigency + source competence"},
    "VIENTO":{"dataType":"meteorological_forecast","geography":"El Chañar","temporalField":"forecastPeriod","parser":"AIC El Chañar forecast parser","validation":"numeric km/h + gusts + direction + forecast classification"},
    "TEMPERATURA":{"dataType":"meteorological_forecast","geography":"El Chañar","temporalField":"forecastPeriod","parser":"AIC El Chañar forecast parser","validation":"numeric °C + forecast classification"},
    "CAUDAL":{"dataType":"hydrological_program","geography":"Compensador/embalse El Chañar","temporalField":"programDate","parser":"AIC programmed-flow table parser","validation":"m³/s + date column + site identity + programmed-flow semantics"},
    "ENERGÍA":{"dataType":"electricity_service_event","geography":"San Patricio del Chañar / sector affected","temporalField":"eventStart/eventEnd","parser":"EPEN scheduled-outage parser","validation":"local sector + event type + date/time + EPEN source"},
    "AGUA":{"dataType":"water_service_event","geography":"San Patricio del Chañar / sector affected","temporalField":"eventDate/time","parser":"EPAS notice parser","validation":"local scope + water event vocabulary + date/time + EPAS source"},
    "SERVICIOS":{"dataType":"public_service_event","geography":"local service area","temporalField":"eventDate/time","parser":"competent-organism notice parser","validation":"service identity + responsible organism + event vocabulary + date/time"},
    "SALUD":{"dataType":"health_service_notice","geography":"establishment/coverage area","temporalField":"eventDate/time","parser":"health authority notice parser","validation":"establishment + service type + date/time + competent health source"},
    "EDUCACIÓN":{"dataType":"education_notice","geography":"establishment/level","temporalField":"eventDate/time","parser":"CPE notice parser","validation":"school/level + educational event + date + CPE source"},
    "PRODUCCIÓN":{"dataType":"productive_notice","geography":"productive establishment/sector","temporalField":"eventDate","parser":"productive authority notice parser","validation":"productive chain + local anchor + event type + competent source"},
    "EMERGENCIAS":{"dataType":"emergency_operational_event","geography":"event zone","temporalField":"alertTime/eventTime","parser":"emergency authority notice parser","validation":"event type + zone + operational source + timestamp"},
    "TERRITORIO":{"dataType":"territorial_event","geography":"local sector/place","temporalField":"eventDate","parser":"municipal/competent-authority territorial parser","validation":"geographic anchor + responsible organism + event identity + date"}
}

RESERVED_INDICATORS = {
    "CALIDAD_AIRE":{
        "sourceCandidate":"Ministerio de Salud de Neuquén · red de monitoreo de calidad del aire",
        "measurement":"PM2.5 y otros parámetros del sensor cuando la estación esté operativa",
        "status":"FUENTE IDENTIFICADA · ESTACIÓN LOCAL A VERIFICAR ANTES DE PUBLICAR",
        "rule":"no publicar valores para Chañar hasta confirmar estación operativa, endpoint/lectura y timestamp"
    },
    "NIVEL_RIO":{
        "sourceCandidate":"AIC · estación COMPENSADOR EL CHANAR",
        "measurement":"altura río/lago en m",
        "status":"FUENTE IDENTIFICADA · ADAPTADOR PENDIENTE",
        "rule":"publicar solo con sitio de estación, valor y última actualización"
    },
    "CAUDAL_OBSERVADO":{
        "sourceCandidate":"AIC · estación COMPENSADOR EL CHANAR",
        "measurement":"caudal medio diario en m³/s",
        "status":"FUENTE IDENTIFICADA · ADAPTADOR PENDIENTE",
        "rule":"distinguir caudal medio diario medido de caudal saliente programado"
    },
    "ESTADO_TRANSITO":{
        "sourceCandidate":"autoridad vial competente según corredor",
        "measurement":"estado de tramo / incidente / restricción",
        "status":"FUENTE A DEFINIR SEGÚN VÍA",
        "rule":"no mezclar rutas provinciales, nacionales y tránsito urbano bajo una sola fuente"
    },
    "RIESGO_INCENDIO":{
        "sourceCandidate":"Servicio Meteorológico Nacional · Índice de Peligro de Incendios FWI",
        "measurement":"índice/clase de peligro y vigencia territorial",
        "status":"FUENTE IDENTIFICADA · ADAPTADOR PENDIENTE",
        "rule":"no convertir condiciones meteorológicas generales en riesgo de incendio sin el índice oficial"
    }
}

def audit_source_contracts():
    required=("primary","domain","unit","language","rule")
    technical_required=("dataType","geography","temporalField","parser","validation")
    audit={}
    for name,contract in SOURCE_CONTRACTS.items():
        missing=[k for k in required if not contract.get(k)]
        audit[name]={
            "valid":not missing,
            "missing":missing,
            "primary":contract.get("primary"),
            "secondary":contract.get("secondary"),
            "fallback":contract.get("fallback"),
            "domain":contract.get("domain"),
            "unit":contract.get("unit"),
            "language":contract.get("language"),
            "refresh":contract.get("refresh")
        }
    for name in SOURCE_CONTRACTS:
        t=INDICATOR_TECHNICAL_CONTRACTS.get(name,{})
        missing_t=[k for k in technical_required if not t.get(k)]
        audit[name]["technical"]=t
        if missing_t:
            audit[name]["valid"]=False
            audit[name]["missing"]=audit[name]["missing"]+["technical."+k for k in missing_t]
    failures=[name for name,row in audit.items() if not row["valid"]]
    if failures:
        raise RuntimeError("CONTRATO DE DATOS INCOMPLETO: "+", ".join(failures))
    return audit

SOURCE_CONTRACT_AUDIT = audit_source_contracts()

def collect_operational():
    # Capa operativa estricta: un organismo competente puede confirmar un
    # estado; un medio o un fallback no puede convertirse silenciosamente en
    # el estado del indicador.
    op={
        "updatedAt":NOW.isoformat(),
        "route7":None,"route8":None,"energy":None,"water":None,
        "sources":[]
    }

    def attempt(name,url,kind,tier):
        try:
            raw=fetch(url)
            op["sources"].append({"name":name,"tier":tier,"mode":"reachable","kind":kind,"url":url})
            return raw
        except Exception as e:
            op["sources"].append({"name":name,"tier":tier,"mode":"connection_error","kind":kind,"url":url,"error":type(e).__name__})
            return ""

    # RUTAS: Vialidad Provincial es la autoridad competente. No usamos Ruta0
    # para inventar o completar el estado oficial.
    dpv="https://www.dpvneuquen.gov.ar/"
    raw=attempt("Dirección Provincial de Vialidad","https://www.dpvneuquen.gov.ar/","road_official","primary")
    if raw:
        plain=clean(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",raw)))
        op["sources"][-1]["contentEvidence"]={
            "route7Mention":bool(re.search(r"Ruta\s*7|RP\s*7",plain,re.I)),
            "route8Mention":bool(re.search(r"Ruta\s*8|RP\s*8",plain,re.I))
        }
    # Si el sitio oficial tiene una publicación concreta, la guardamos como
    # evidencia; no la convertimos automáticamente en estado vigente.
    for route,key in [("Ruta 7","route7"),("Ruta 8","route8")]:
        op[key]={
            "indicator":key,
            "authority":"Dirección Provincial de Vialidad del Neuquén",
            "source":"Dirección Provincial de Vialidad",
            "sourceTier":"primary",
            "sourceUrl":dpv,
            "semanticState":None,
            "publicationState":"source_reachable_no_current_machine_readable_state",
            "detail":None,
            "retrievedAt":NOW.isoformat()
        }

    # ENERGÍA: EPEN. Solo un aviso específico de Chañar puede crear un evento.
    eurl="https://www.epen.gov.ar/index.php/cortes-programados/"
    eraw=attempt("EPEN",eurl,"electricity_official","primary")
    if eraw:
        et=clean(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",eraw)))
        hits=[m.group(0) for m in re.finditer(r".{0,180}(?:San Patricio del Chañar|El Chañar).{0,420}",et,re.I)]
        op["energy"]={
            "indicator":"ENERGÍA",
            "authority":"EPEN",
            "source":"EPEN",
            "sourceTier":"primary",
            "sourceUrl":eurl,
            "semanticState":"corte_programado" if hits else None,
            "eventType":"scheduled_outage" if hits else None,
            "detail":" ".join(hits[:3])[:1000] if hits else None,
            "publicationState":"specific_local_notice_found" if hits else "source_reachable_no_specific_local_notice",
            "retrievedAt":NOW.isoformat()
        }
    else:
        op["energy"]={
            "indicator":"ENERGÍA","authority":"EPEN","source":"EPEN","sourceTier":"primary",
            "sourceUrl":eurl,"semanticState":None,"eventType":None,
            "publicationState":"source_unreachable","retrievedAt":NOW.isoformat()
        }

    # AGUA: EPAS es primario. El municipio solo puede comunicar.
    aurl="https://www.epas.gov.ar/"
    araw=attempt("EPAS",aurl,"water_official","primary")
    mhits=[]
    if araw:
        at=clean(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",araw)))
        mhits=[m.group(0) for m in re.finditer(r".{0,180}(?:San Patricio del Chañar|El Chañar).{0,420}",at,re.I)]
    op["water"]={
        "indicator":"AGUA",
        "authority":"EPAS",
        "source":"EPAS",
        "sourceTier":"primary",
        "sourceUrl":aurl,
        "semanticState":"evento_hidrico_publicado" if mhits else None,
        "eventType":"water_service_event" if mhits else None,
        "detail":" ".join(mhits[:2])[:900] if mhits else None,
        "publicationState":"specific_local_notice_found" if mhits else ("source_reachable_no_specific_local_notice" if araw else "source_unreachable"),
        "retrievedAt":NOW.isoformat()
    }
    return op


def collect_environment():
    # Datos ambientales: fuente profesional primero. Si la fuente no entrega
    # un valor validable, el campo queda ausente; jamás se fabrica un número.
    env={
        "weather":None,
        "hydrology":None,
        "sources":[],
        "updatedAt":NOW.isoformat()
    }

    aic_url="https://www.aic.gob.ar/sitio/home?a=1015&z=1967225803"
    try:
        html=fetch(aic_url)
        plain=clean(re.sub(r"<[^>]+>"," ",html))
        idx=plain.lower().find("pronóstico para el chañar")
        block=plain[idx:idx+6000] if idx>=0 else plain[:6000]
        vm=re.search(r"Viento\s+([0-9]{1,3})\s*km/h",block,re.I)
        gm=re.search(r"Ráfagas\s+([0-9]{1,3})\s*km/h",block,re.I)
        dm=re.search(r"Dirección\s+([A-ZÁÉÍÓÚÑ/]{1,6})",block,re.I)
        tm=re.search(r"Temperatura\s+(-?[0-9]{1,3})\s*ºC",block,re.I)
        if vm:
            env["weather"]={
                "dataType":"forecast",
                "forecastWindKmh":float(vm.group(1)),
                "forecastGustKmh":float(gm.group(1)) if gm else None,
                "forecastWindDirection":dm.group(1) if dm else None,
                "forecastTemperatureC":float(tm.group(1)) if tm else None,
                "retrievedAt":NOW.isoformat(),
                "source":"AIC",
                "sourceTier":"primary",
                "sourceUrl":aic_url,
                "semanticState":"pronostico_local"
            }
            env["sources"].append({"name":"AIC · Pronóstico El Chañar","tier":"primary","mode":"parsed","url":aic_url})
        else:
            env["sources"].append({"name":"AIC · Pronóstico El Chañar","tier":"primary","mode":"reachable_but_unparsed","url":aic_url})
    except Exception as e:
        env["sources"].append({"name":"AIC · Pronóstico El Chañar","tier":"primary","mode":"connection_error","error":type(e).__name__,"url":aic_url})

    # AIC publica un programa de caudales. El dato se conserva como PROGRAMADO,
    # no como observación del río en San Patricio del Chañar.
    hurl="https://www.aic.gob.ar/sitio/caudales"
    try:
        ht=fetch(hurl)
        plain=clean(re.sub(r"<[^>]+>"," ",ht))
        # Tabla AIC: una fila de "Erogado", una fila de máximos programados
        # y una fila de mínimos programados. El día de consulta se toma del
        # encabezado publicado, no del reloj de RADAR.
        header=re.search(r"domingo,\s*(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})",plain,re.I)
        row=re.search(
            r"El Chañar\s*\|\s*(\d+)\s*\|\s*"
            r"((?:\d+\s*\|\s*){5}\d+)\s*"
            r"(\d+(?:\s*\|\s*\d+){5})",
            plain,re.I
        )
        if row:
            erogado=int(row.group(1))
            max_vals=[int(x) for x in re.findall(r"\d+",row.group(2))]
            min_vals=[int(x) for x in re.findall(r"\d+",row.group(3))]
            # La primera columna de programación corresponde al día siguiente
            # al "Erogado" mostrado en la tabla.
            env["hydrology"]={
                "site":"El Chañar",
                "flowType":"programmed_outflow",
                "erogatedM3s":erogado,
                "programmedMaxM3s":max_vals,
                "programmedMinM3s":min_vals,
                "currentProgrammedMaxM3s":max_vals[0] if max_vals else None,
                "currentProgrammedMinM3s":min_vals[0] if min_vals else None,
                "programDate":(NOW+timedelta(days=1)).strftime("%Y-%m-%d"),
                "tableDate":NOW.strftime("%Y-%m-%d"),
                "retrievedAt":NOW.isoformat(),
                "source":"AIC",
                "sourceTier":"primary",
                "sourceUrl":hurl,
                "semanticState":"caudal_programado"
            }
            env["sources"].append({"name":"AIC · Caudales Programados","tier":"primary","mode":"parsed","url":hurl})
        else:
            env["sources"].append({"name":"AIC · Caudales Programados","tier":"primary","mode":"reachable_but_unparsed","url":hurl})
    return env

def _indicator_match(events, terms):
    if not terms:
        return len(events)
    return sum(
        1 for e in events
        if any(norm(t) in norm(e.get("title","")+" "+str(e.get("description",""))) for t in terms)
    )

def build_system_radars(events, environment):
    # La fachada sigue compacta. La diferencia está detrás: cada radar nace
    # de un contrato y no puede existir fuera del registro profesional.
    now=datetime.now(timezone.utc)
    specs=[
      ("CONVERSACIÓN","Conversación general",[""],"editorial"),
      ("RUTA 7","Corredor Ruta 7",["ruta 7"],"operational"),
      ("RUTA 8","Corredor Ruta 8",["ruta 8"],"operational"),
      ("VIENTO","Viento",["viento","ráfaga"],"environment"),
      ("ENERGÍA","Electricidad",["luz","energia","eléctr","corte de luz","epen"],"operational"),
      ("AGUA","Agua",["agua","abastecimiento","corte de agua","potable","cloaca"],"operational"),
      ("SERVICIOS","Servicios",["servicio","obra","cloaca","residu","gas"],"editorial"),
      ("SALUD","Salud",["hospital","salud","medic","vacun","guardia"],"editorial"),
      ("EDUCACIÓN","Educación",["escuela","cpem","epet","clases","docente"],"editorial"),
      ("PRODUCCIÓN","Producción",["chacra","viñedo","bodega","productor","agro"],"editorial"),
      ("EMERGENCIAS","Emergencias",["bombero","policia","emergencia","rescate","accidente"],"editorial"),
      ("TERRITORIO","Territorio",["picada","barrio","sector","parque industrial","loteo"],"editorial")
    ]
    out=[]
    for code,label,terms,mode in specs:
        contract=SOURCE_CONTRACTS.get(code)
        if not contract:
            raise RuntimeError("INDICADOR SIN CONTRATO PROFESIONAL: "+code)
        matches=_indicator_match(events,terms)
        last=max(
            [parse_date(e.get("publishedAt")) for e in events
             if any(norm(t) in norm(e.get("title","")+" "+str(e.get("description",""))) for t in terms)
             and parse_date(e.get("publishedAt"))] or [None]
        )
        age=None if not last else round((now-last).total_seconds()/3600,1)

        row={
            "id":code,
            "label":label,
            "signal":matches,
            "freshnessHours":age,
            "mode":mode,
            "evidenceCount":matches,
            "sourceContract":contract,
            "contractVersion":CONTRACT_VERSION
        }

        if code=="VIENTO" and environment.get("weather"):
            w=environment["weather"]
            row.update({
                "signal":w.get("forecastWindKmh"),
                "status":"PRONÓSTICO LOCAL",
                "semanticState":w.get("semanticState"),
                "dataType":"forecast",
                "windKmh":w.get("forecastWindKmh"),
                "gustKmh":w.get("forecastGustKmh"),
                "windDirection":w.get("forecastWindDirection"),
                "temperatureC":w.get("forecastTemperatureC"),
                "source":"AIC",
                "sourceTier":"primary",
                "retrievedAt":w.get("retrievedAt")
            })
        elif code=="VIENTO":
            row.update({
                "status":None,
                "semanticState":None,
                "source":"AIC",
                "sourceTier":"primary",
                "sourceState":"unavailable_or_unparsed"
            })
        else:
            # No universal status. Editorial signals and operational states
            # remain separate until the competent parser supplies the
            # indicator-specific vocabulary.
            row["status"]=None
        out.append(row)
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
# Auditoría obligatoria: el feed no puede salir si algún radar o contrato
# incumple la ley mundial de procedencia.
contract_audit=SOURCE_CONTRACT_AUDIT
required_radar_contracts={"CONVERSACIÓN","RUTA 7","RUTA 8","VIENTO","ENERGÍA","AGUA","SERVICIOS","SALUD","EDUCACIÓN","PRODUCCIÓN","EMERGENCIAS","TERRITORIO"}
missing_radar_contracts=sorted(required_radar_contracts-set(SOURCE_CONTRACTS))
if missing_radar_contracts:
    raise RuntimeError("RADAR SIN CONTRATO: "+", ".join(missing_radar_contracts))
output={'updatedAt':now,'window':f'{DAYS} días','purpose':'Detectar qué se está moviendo en San Patricio del Chañar y mostrar de dónde surge cada señal.','architecture':'contrato universal de procedencia + fuentes profesionales + parsers específicos + validación semántica + temporalidad + evidencia editorial separada + memoria de eventos','keywords':[q for q,_ in QUERIES],'sourceRegistry':status,'sourceCatalog':SOURCE_CATALOG,'sourceAudit':source_audit,'languageAudit':language_audit,'precisionAudit':precision_audit,'stats':stats,'environment':environment,'operational':operational,'sourceContracts':SOURCE_CONTRACTS,'contractAudit':contract_audit,'reservedIndicators':RESERVED_INDICATORS,'indicatorTechnicalContracts':INDICATOR_TECHNICAL_CONTRACTS,'contractVersion':CONTRACT_VERSION,'systemRadars':system_radars,'system':{'memoryDays':MEMORY_DAYS,'eventIdentity':'estable entre actualizaciones','evidenceRule':'evidence-first','movementRule':'descriptivo: recencia + cobertura + diversidad de fuentes; no es ranking de importancia','sourceFailureRule':'no inferir desaparición cuando las fuentes conocidas no responden','infrastructureRule':'una señal editorial no equivale a confirmación operativa; los datos directos se etiquetan por separado','lifecycle':['EMERGENTE','ACTIVO','SOSTENIDO','EN DESCENSO','RECIENTE'],'sourceHealth':status},'events':events,'items':dedup}
with open(OUT,'w',encoding='utf-8') as f: json.dump(output,f,ensure_ascii=False,indent=2)
print('PULSO:',stats,'RADARES:',len(system_radars))
