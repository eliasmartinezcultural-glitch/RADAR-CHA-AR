/* RADAR WORKBENCH · provenance-first newsroom layer */
(()=> {
const WBKEY='chanarRadarWorkbenchV1';
const state=JSON.parse(localStorage.getItem(WBKEY)||'{}');
state.selectedSignal=state.selectedSignal||null;
function save(){localStorage.setItem(WBKEY,JSON.stringify(state))}
const css=`
.signal-workbench{margin-top:10px;border:1px solid rgba(232,196,109,.18);border-radius:15px;background:#080e13;overflow:hidden}
.sw-head{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:11px 12px;border-bottom:1px solid rgba(102,240,255,.1)}
.sw-head b{font:900 .68rem ui-monospace,monospace;letter-spacing:.08em}.sw-head span{font-size:.58rem;color:#7e929c}
.sw-body{padding:10px}.sw-empty{padding:14px;border:1px dashed rgba(99,150,166,.2);border-radius:10px;color:#7e929c;font-size:.7rem}
.sw-signal{display:grid;grid-template-columns:1fr auto;gap:8px;padding:10px;border:1px solid rgba(99,150,166,.14);border-radius:10px;background:#071016;margin-bottom:7px}
.sw-signal b{font-size:.76rem;line-height:1.3}.sw-signal small{display:block;color:#7e929c;font-size:.58rem;margin-top:4px}.sw-actions{display:flex;gap:5px;flex-wrap:wrap}.sw-actions button{font-size:.59rem;padding:7px 8px;min-height:32px}
.sw-panel{margin-top:9px;padding:11px;border:1px solid rgba(102,240,255,.14);border-radius:11px;background:#061017}
.sw-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}.sw-field{width:100%;background:#070d12;color:#edf7fa;border:1px solid rgba(99,150,166,.2);border-radius:8px;padding:8px;font-size:.67rem}.sw-field:focus{outline:none;border-color:#66f0ff}.sw-full{grid-column:1/-1}.sw-label{font-size:.55rem;color:#7e929c;text-transform:uppercase;letter-spacing:.08em}.sw-value{font-size:.68rem;margin-top:3px}.sw-status{display:inline-flex;padding:4px 7px;border-radius:99px;border:1px solid rgba(232,196,109,.2);color:#e8c46d;font-size:.57rem}.sw-note{font-size:.61rem;color:#7e929c;margin-top:8px}
@media(max-width:560px){.sw-signal{grid-template-columns:1fr}.sw-grid{grid-template-columns:1fr}.sw-full{grid-column:auto}}
`;
const st=document.createElement('style');st.textContent=css;document.head.appendChild(st);

function esc2(s){return String(s??'').replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]))}
function date(v){try{return new Date(v).toLocaleString('es-AR',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'})}catch{return v||'—'}}
function active(){return typeof currentCase==='function'?currentCase():null}
function ensureCaseFields(){
 const sel=document.getElementById('caseStatus');
 if(sel && !sel.dataset.wb){
   sel.innerHTML=['Por revisar','En búsqueda','En verificación','Confirmada','Descartada','Archivada'].map(x=>'<option>'+x+'</option>').join('');
   sel.dataset.wb='1';
 }
 const form=document.getElementById('caseForm');
 if(!form || document.getElementById('wbProvenance')) return;
 const box=document.createElement('div');box.id='wbProvenance';box.className='sw-panel';
 box.innerHTML='<b style="font-size:.76rem">🔎 TRAZABILIDAD DE LA SEÑAL</b><div class="sw-grid" style="margin-top:8px">'+
 '<div><div class="sw-label">Fuente</div><input id="wbSource" class="sw-field" placeholder="Medio, organismo, documento…"></div>'+
 '<div><div class="sw-label">Fecha de la señal</div><input id="wbDate" class="sw-field" type="datetime-local"></div>'+
 '<div class="sw-full"><div class="sw-label">Evidencia principal</div><input id="wbEvidence" class="sw-field" placeholder="Enlace al documento, nota o publicación original"></div>'+
 '<div class="sw-full"><div class="sw-label">Seguimiento</div><textarea id="wbFollow" class="sw-field" rows="3" placeholder="Qué falta comprobar, a quién consultar, qué documento buscar…"></textarea></div>'+
 '</div><div class="sw-actions" style="margin-top:8px"><button class="primary" id="wbSave">GUARDAR TRAZABILIDAD</button><button id="wbCopy">COPIAR FICHA</button></div>'+
 '<div class="sw-note">La trazabilidad es interna y local al navegador. RADAR no publica ni atribuye automáticamente.</div>';
 form.appendChild(box);
 document.getElementById('wbSave').onclick=saveTrace;
 document.getElementById('wbCopy').onclick=copyTrace;
}
function loadTrace(){
 ensureCaseFields();const c=active();if(!c)return;
 const t=c.trace||{};['wbSource','wbEvidence','wbFollow'].forEach(id=>{const e=document.getElementById(id);if(e)e.value=t[id.slice(2).toLowerCase()]||''});
 const d=document.getElementById('wbDate');if(d)d.value=t.date||'';
}
function saveTrace(){
 const c=active();if(!c)return alert('Abrí un expediente.');
 c.trace={source:document.getElementById('wbSource').value.trim(),date:document.getElementById('wbDate').value,evidence:document.getElementById('wbEvidence').value.trim(),follow:document.getElementById('wbFollow').value.trim()};
 if(c.trace.evidence && !c.evidence.some(x=>x.url===c.trace.evidence))c.evidence.unshift({url:c.trace.evidence,date:new Date().toLocaleString('es-AR'),kind:'evidencia principal'});
 c.updatedAt=new Date().toLocaleString('es-AR');persist();renderCaseForm();loadTrace();alert('Trazabilidad guardada localmente.');
}
function copyTrace(){
 const c=active();if(!c)return;
 const t=c.trace||{};const s='📡 CHÁÑAR RADAR · FICHA\nSeñal: '+(c.title||'—')+'\nFuente: '+(t.source||'—')+'\nFecha: '+(t.date||'—')+'\nEstado: '+(c.status||'Por revisar')+'\nEvidencia: '+(t.evidence||'—')+'\nSeguimiento: '+(t.follow||'—')+'\nNo verificado automáticamente.';
 navigator.clipboard?.writeText(s).then(()=>alert('Ficha copiada.'));
}
function openSignal(i){
 const x=window.radarFeed?.[i];if(!x)return;
 state.selectedSignal=x;save();
 const c=active();
 const html='<div class="kicker">MESA DE SEÑAL</div><h2>'+esc2(x.title)+'</h2>'+
 '<p class="muted">'+esc2(x.source||'Fuente no identificada')+' · '+esc2(x.tier==='local'?'LOCAL':'REGIONAL')+' · '+date(x.published)+'</p>'+
 '<div class="sw-panel"><div class="sw-label">PROCEDENCIA</div><div class="sw-value">'+esc2(x.url)+'</div>'+
 '<div class="sw-note">Detectada por el monitor. Esto es una señal documental, no una confirmación.</div></div>'+
 '<div class="sw-actions" style="margin-top:10px"><button class="primary" id="wbCreate">＋ CREAR EXPEDIENTE</button><button id="wbOpen">ABRIR FUENTE ↗</button></div>';
 const m=document.getElementById('modalContent');if(m){m.innerHTML=html;document.getElementById('modal').classList.add('open');}
 document.getElementById('wbCreate')?.addEventListener('click',()=>createFromSignal(x));
 document.getElementById('wbOpen')?.addEventListener('click',()=>window.open(x.url,'_blank','noopener'));
}
function createFromSignal(x){
 const c=newCase(x.title);
 c.title=x.title;c.area='San Patricio del Chañar';c.status='Por revisar';
 c.trace={source:x.source||'',date:x.published||'',evidence:x.url||'',follow:'Confirmar la información con la fuente original y, si corresponde, una segunda fuente.'};
 c.signal={tier:x.tier||'',url:x.url||'',query:x.query||'',detectedAt:new Date().toISOString()};
 c.evidence=[{url:x.url,date:new Date().toLocaleString('es-AR'),kind:'señal detectada'}];
 c.updatedAt=new Date().toLocaleString('es-AR');persist();renderCaseForm();loadTrace();closeModal();focusSec('investigacion');
}
function injectWorkbench(){
 const monitor=document.querySelector('.radar-monitor');if(!monitor||document.getElementById('signalWorkbench'))return;
 const box=document.createElement('div');box.id='signalWorkbench';box.className='signal-workbench';
 box.innerHTML='<div class="sw-head"><b>▣ MESA DE SEÑALES</b><span>fuente → fecha → estado → evidencia → seguimiento</span></div><div class="sw-body"><div id="swList" class="sw-empty">Seleccioná una señal del monitor.</div></div>';
 monitor.appendChild(box);
}
function renderWorkbench(){
 injectWorkbench();const list=document.getElementById('swList');if(!list)return;
 const feed=(window.radarFeed||[]).slice(0,8);
 if(!feed.length){list.className='sw-empty';list.textContent='Sin señales disponibles.';return}
 list.className='';list.innerHTML=feed.map((x,i)=>'<article class="sw-signal"><div><b>'+esc2(x.title)+'</b><small>'+esc2(x.source||'Fuente')+' · '+esc2(x.tier||'señal')+' · '+date(x.published)+'</small></div><div class="sw-actions"><button onclick="window.radarWorkbenchOpen('+i+')">FICHA</button><button class="primary" onclick="window.radarWorkbenchCase('+i+')">EXPEDIENTE</button></div></article>').join('');
}
window.radarWorkbenchOpen=openSignal;
window.radarWorkbenchCase=i=>{const x=window.radarFeed?.[i];if(x)createFromSignal(x)};
const oldRender=window.renderRadarFeed;
window.renderRadarFeed=function(){oldRender?.();renderWorkbench()};
const oldLoad=window.loadRadarFeed;
window.loadRadarFeed=async function(){await oldLoad?.();renderWorkbench()};
const oldRenderCaseForm=window.renderCaseForm;
window.renderCaseForm=function(){oldRenderCaseForm?.();ensureCaseFields();loadTrace()};
setTimeout(()=>{ensureCaseFields();renderWorkbench();loadTrace()},80);
})();