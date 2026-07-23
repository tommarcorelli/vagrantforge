/* VagrantForge — contrôleur de l'interface.
   État en mémoire + persistance localStorage + rendu formulaire/aperçu. */

const CLE='vagrantforge.v3';
let vms=[], openStates={};
const $=s=>document.querySelector(s);

function makeVM(i){
  const id='vm'+Date.now()+Math.floor(Math.random()*1000);
  const nom=i===0?'web':'vm'+(i+1);
  return {id, name:nom, box:'debian/bookworm64', boxVersion:'', guestOs:'', locale:'', keymap:'',
    sshUsername:'', sshPassword:'', winrmUsername:'', winrmPassword:'', rootPassword:'', memory:2048, cpus:1, ip:'',
    provider:'', gui:false, publicNetwork:false, syncedFolder:'./'+nom,
    disableSyncedFolder:false, provisionType:'shell', provisionScript:'apt-get update -y\n', ports:[], extraDisks:[]};
}
function sousReseau(){ return $('#g-subnet').value.trim()||'192.168.56'; }
function nextIP(){ const sr=sousReseau(); const u=vms.map(v=>v.ip).filter(Boolean); let n=10; while(u.includes(sr+'.'+n)) n++; return sr+'.'+n; }

function addVM(){ const v=makeVM(vms.length); v.ip=nextIP(); vms.push(v); openStates[v.id]=true; rendre(); }
function removeVM(id){ vms=vms.filter(v=>v.id!==id); rendre(); }
function dupVM(id){ const s=vms.find(v=>v.id===id); if(!s) return; const c=JSON.parse(JSON.stringify(s)); c.id='vm'+Date.now()+Math.floor(Math.random()*1000); c.name=s.name+'-copie'; c.ip=nextIP(); c.syncedFolder='./'+c.name; vms.splice(vms.findIndex(v=>v.id===id)+1,0,c); openStates[c.id]=true; rendre(); }
function addPort(id){ const v=vms.find(v=>v.id===id); v.ports.push({guest:80,host:8080+v.ports.length}); rendre(); }
function rmPort(id,i){ const v=vms.find(v=>v.id===id); v.ports.splice(i,1); rendre(); }
function addDisk(id){ const v=vms.find(v=>v.id===id); v.extraDisks.push({name:'data'+(v.extraDisks.length+1), sizeGb:10}); rendre(); }
function rmDisk(id,i){ const v=vms.find(v=>v.id===id); v.extraDisks.splice(i,1); rendre(); }

function configCourante(){
  return { provider:$('#g-provider').value, box_check_update:$('#g-boxcheck').checked,
    vms: vms.map(v=>({ name:v.name, box:v.box, box_version:v.boxVersion, guest_os:v.guestOs||undefined, memory:parseInt(v.memory)||0,
      cpus:parseInt(v.cpus)||0, ip:v.ip, provider:v.provider, gui:v.gui, public_network:v.publicNetwork,
      locale:v.locale, keymap:v.keymap, synced_folder:v.syncedFolder, disable_synced_folder:v.disableSyncedFolder,
      ssh_username:v.sshUsername, ssh_password:v.sshPassword,
      winrm_username:v.winrmUsername, winrm_password:v.winrmPassword, root_password:v.rootPassword,
      ports:v.ports, extra_disks:(v.extraDisks||[]).map(d=>({name:d.name, size_gb:parseInt(d.sizeGb)||0})),
      provision:{type:v.provisionType, script:v.provisionScript} })) };
}

function optionsBox(v){
  let html='', connu=false;
  CATALOGUE.forEach(g=>{
    html+=`<optgroup label="${g.famille}">`;
    g.boxes.forEach(b=>{ const sel=b.id===v.box; if(sel) connu=true; html+=`<option value="${b.id}" ${sel?'selected':''}>${b.nom}</option>`; });
    html+=`</optgroup>`;
  });
  html+=`<optgroup label="Avancé"><option value="__autre__" ${!connu?'selected':''}>Autre box (saisie manuelle)…</option></optgroup>`;
  return html;
}
function optionsSimple(niveaux, cur){ return niveaux.map(([val,lib])=>`<option value="${val}" ${val==cur?'selected':''}>${lib}</option>`).join(''); }
function optionsLocale(v){ return LOCALES.map(([loc,km,lib])=>{ const sel=(loc===(v.locale||'')); return `<option value="${loc}|${km}" ${sel?'selected':''}>${lib}</option>`; }).join(''); }
function optionsSnippets(){ let h='<option value="">＋ insérer une commande…</option>'; SNIPPETS.forEach(([cat,items])=>{ h+=`<optgroup label="${cat}">`; items.forEach(([lib,code])=>{ h+=`<option value="${btoa(unescape(encodeURIComponent(code)))}">${lib}</option>`; }); h+='</optgroup>'; }); return h; }

function warnBox(v){
  const pe=v.provider||$('#g-provider').value;
  if(boxSupportsProvider(v.box,pe)===false){
    const alt=Object.keys(BOX_PROVIDERS).find(b=>BOX_PROVIDERS[b].includes(pe)&&v.box.includes('/')&&b.split('/').pop()===v.box.split('/').pop());
    return `<div class="box-warning">⚠ Cet OS n'a pas d'image <b>${pe}</b>.${alt?` Essaie <code>${NOM_BOX[alt]||alt}</code>.`:''}</div>`;
  }
  return '';
}

function renderForm(nomsErr){
  nomsErr=nomsErr||{};
  const list=$('#vm-list');
  if(vms.length===0){ list.innerHTML='<div class="hint">Aucune VM. Clique sur « + ajouter une VM » ou choisis un démarrage rapide.</div>'; return; }
  const ramCustom = v => !RAM_NIVEAUX.some(([val])=>val==v.memory);

  list.innerHTML = vms.map(v=>{
    const boxAutre = !NOM_BOX[v.box];
    const ports=v.ports.map((p,i)=>`
      <div class="port-row">
        <input type="number" data-vm="${v.id}" data-field="port-guest" data-idx="${i}" value="${p.guest}" placeholder="VM (guest)">
        <span style="color:var(--text-dim);font-family:var(--mono);font-size:11px;">→</span>
        <input type="number" data-vm="${v.id}" data-field="port-host" data-idx="${i}" value="${p.host}" placeholder="PC (host)">
        <span class="rm" data-vm="${v.id}" data-idx="${i}" data-action="rmport">✕</span>
      </div>`).join('');
    const disques=(v.extraDisks||[]).map((d,i)=>`
      <div class="port-row">
        <input type="text" data-vm="${v.id}" data-field="disk-name" data-idx="${i}" value="${d.name||''}" placeholder="nom (ex: data)">
        <input type="number" data-vm="${v.id}" data-field="disk-size" data-idx="${i}" value="${d.sizeGb||10}" min="1" placeholder="Go">
        <span class="rm" data-vm="${v.id}" data-idx="${i}" data-action="rmdisk">✕</span>
      </div>`).join('');

    return `
    <div class="vm-card${openStates[v.id]?' open':''}">
      <div class="vm-card-head" data-toggle="${v.id}">
        <span class="dot${nomsErr[v.id]?' err':''}"></span>
        <span class="name">${v.name||'(sans nom)'}</span>
        <span class="badge">${(NOM_BOX[v.box]||v.box).split(' — ')[0]} · ${v.memory}Mo</span>
        <span class="toggle">▸</span>
      </div>
      <div class="vm-card-body">
        <label>${t('vm.nom')}</label>
        <input type="text" data-vm="${v.id}" data-field="name" value="${v.name}">

        <label>${t('vm.os')}
          <span class="info" title="${t('vm.os.tip')}">i</span>
        </label>
        <select data-vm="${v.id}" data-field="box">${optionsBox(v)}</select>
        ${boxAutre?`<input type="text" data-vm="${v.id}" data-field="boxManuel" value="${v.box}" placeholder="ex: monorg/ma-box" style="margin-top:6px;">`:''}
        ${warnBox(v)}

        <label>${t('vm.version')}
          <span class="info" title="${t('vm.version.tip')}">i</span>
        </label>
        <div class="row2">
          <input type="text" data-vm="${v.id}" data-field="boxVersion" value="${v.boxVersion||''}" placeholder="dernière (laisser vide)" list="dl-${v.id}">
          <button type="button" class="btn-secondaire" data-versions="${v.id}">🔎 Versions dispo</button>
        </div>
        <datalist id="dl-${v.id}"></datalist>
        <div class="versions-statut" data-versions-statut="${v.id}">
          <a href="https://vagrantcloud.com/${v.box}" target="_blank" rel="noopener">Voir les versions sur Vagrant Cloud ↗</a>
        </div>

        <div class="row2">
          <div><label>${t('vm.ram')}</label>
            <select data-vm="${v.id}" data-field="memory">
              ${optionsSimple(RAM_NIVEAUX, v.memory)}
              <option value="__custom__" ${ramCustom(v)?'selected':''}>Personnalisé…</option>
            </select>
            ${ramCustom(v)?`<input type="number" data-vm="${v.id}" data-field="memoryCustom" value="${v.memory}" style="margin-top:6px;" placeholder="Mo">`:''}
          </div>
          <div><label>${t('vm.cpu')}</label>
            <select data-vm="${v.id}" data-field="cpus">${optionsSimple(CPU_NIVEAUX, v.cpus)}</select>
          </div>
        </div>

        ${estBoxWindows(v) ? `
        <div class="notice-windows" style="margin:8px 0;padding:10px 12px;border-radius:13px;font-size:.85em;">
          🪟 Box Windows détectée — pilotage en <b>WinRM</b> (pas de SSH), provisioning en <b>PowerShell</b>.
        </div>` : `
        <label>${t('vm.langue')}
          <span class="info" title="${t('vm.langue.tip')}">i</span>
        </label>
        <select data-vm="${v.id}" data-field="locale">${optionsLocale(v)}</select>`}

        <label>${t('vm.ip')}
          <span class="info" title="${t('vm.ip.tip')}">i</span>
        </label>
        <input type="text" data-vm="${v.id}" data-field="ip" value="${v.ip}" placeholder="vide = IP automatique">

        <label>${t('vm.provider')}
          <span class="info" title="${t('vm.provider.tip')}">i</span>
        </label>
        <select data-vm="${v.id}" data-field="provider">
          <option value="" ${v.provider===''?'selected':''}>— hérite du global —</option>
          <option value="virtualbox" ${v.provider==='virtualbox'?'selected':''}>VirtualBox</option>
          <option value="vmware_desktop" ${v.provider==='vmware_desktop'?'selected':''}>VMware Desktop</option>
          <option value="libvirt" ${v.provider==='libvirt'?'selected':''}>libvirt</option>
        </select>

        <div class="checkbox-row"><input type="checkbox" data-vm="${v.id}" data-field="gui" ${v.gui?'checked':''}>
          <label>${t('vm.gui')} <span class="info" title="${t('vm.gui.tip')}">i</span></label></div>
        <div class="checkbox-row"><input type="checkbox" data-vm="${v.id}" data-field="publicNetwork" ${v.publicNetwork?'checked':''}>
          <label>${t('vm.pont')} <span class="info" title="${t('vm.pont.tip')}">i</span></label></div>

        <label>${t('vm.dossier')}
          <span class="info" title="${t('vm.dossier.tip')}">i</span>
        </label>
        <input type="text" data-vm="${v.id}" data-field="syncedFolder" value="${v.syncedFolder}" ${v.disableSyncedFolder?'disabled':''}>
        <div class="checkbox-row"><input type="checkbox" data-vm="${v.id}" data-field="disableSyncedFolder" ${v.disableSyncedFolder?'checked':''}>
          <label>${t('vm.dossier_off')}</label></div>

        ${estBoxWindows(v) ? `
        <label style="margin-bottom:-4px;">${LANGUE_COURANTE==='en'?'Windows credentials':'Identifiants Windows'}
          <span class="info" title="${t('vm.winrm.tip')}">i</span>
        </label>
        <div class="row2">
          <div><label>${t('vm.winrm_user')}</label>
            <input type="text" data-vm="${v.id}" data-field="winrmUsername" value="${v.winrmUsername||''}" placeholder="vagrant"></div>
          <div><label>${t('vm.winrm_pass')}</label>
            <input type="text" data-vm="${v.id}" data-field="winrmPassword" value="${v.winrmPassword||''}" placeholder="vagrant"></div>
        </div>
        <label>${t('vm.admin_pass')}
          <span class="info" title="${t('vm.admin_pass.tip')}">i</span>
        </label>
        <input type="text" data-vm="${v.id}" data-field="rootPassword" value="${v.rootPassword||''}" placeholder="vide = inchangé">` : `
        <label style="margin-bottom:-4px;">${LANGUE_COURANTE==='en'?'SSH credentials':'Identifiants SSH'}
          <span class="info" title="${t('vm.ssh.tip')}">i</span>
        </label>
        <div class="row2">
          <div><label>${t('vm.ssh_user')}</label>
            <input type="text" data-vm="${v.id}" data-field="sshUsername" value="${v.sshUsername||''}" placeholder="vagrant"></div>
          <div><label>${t('vm.ssh_pass')}</label>
            <input type="text" data-vm="${v.id}" data-field="sshPassword" value="${v.sshPassword||''}" placeholder="clé par défaut"></div>
        </div>
        <label>${t('vm.root_pass')}
          <span class="info" title="${t('vm.root_pass.tip')}">i</span>
        </label>
        <input type="text" data-vm="${v.id}" data-field="rootPassword" value="${v.rootPassword||''}" placeholder="vide = inchangé">`}

        <label>${t('vm.ports')}
          <span class="info" title="${t('vm.ports.tip')}">i</span>
        </label>
        <div class="ports-list">${ports}</div>
        <div class="btn-row"><button class="btn small" data-action="addport" data-vm="${v.id}">+ ${LANGUE_COURANTE==='en'?'port':'port'}</button></div>

        <label>${t('vm.disques')}
          <span class="info" title="${t('vm.disques.tip')}">i</span>
        </label>
        <div class="ports-list">${disques}</div>
        <div class="btn-row"><button class="btn small" data-action="adddisk" data-vm="${v.id}">+ ${LANGUE_COURANTE==='en'?'disk':'disque'}</button></div>

        <label>${t('vm.provision')}
          <span class="info" title="${t('vm.provision.tip')}">i</span>
        </label>
        <select data-vm="${v.id}" data-field="provisionType">
          <option value="shell" ${v.provisionType==='shell'?'selected':''}>${LANGUE_COURANTE==='en'?'shell script':'script shell'}</option>
          <option value="ansible" ${v.provisionType==='ansible'?'selected':''}>${LANGUE_COURANTE==='en'?'Ansible playbook':'playbook Ansible'}</option>
          <option value="none" ${v.provisionType==='none'?'selected':''}>${LANGUE_COURANTE==='en'?'nothing':'rien'}</option>
        </select>
        ${v.provisionType==='shell'?`
          <label>${t('vm.aide_cmd')}
            <span class="info" title="${t('vm.aide_cmd.tip')}">i</span>
          </label>
          <select data-vm="${v.id}" data-field="snippet">${optionsSnippets()}</select>
          <label>${t('vm.script')}</label>
          <textarea data-vm="${v.id}" data-field="provisionScript" rows="5">${v.provisionScript}</textarea>`:''}
        ${v.provisionType==='ansible'?`
          <label>${t('vm.playbook')}
            <span class="info" title="${t('vm.playbook.tip')}">i</span>
          </label>
          <input type="text" data-vm="${v.id}" data-field="provisionScript" value="${(v.provisionScript||'').includes('.yml')?v.provisionScript:'provisioning/playbook.yml'}">`:''}

        <div class="btn-row">
          <button class="btn small" data-action="dup" data-vm="${v.id}">${LANGUE_COURANTE==='en'?'duplicate':'dupliquer'}</button>
          <button class="btn danger small" data-action="remove" data-vm="${v.id}">${LANGUE_COURANTE==='en'?'remove':'supprimer'}</button>
        </div>
      </div>
    </div>`;
  }).join('');

  cabler(list);
}

function cabler(list){
  list.querySelectorAll('[data-toggle]').forEach(el=>el.addEventListener('click',()=>{ const id=el.getAttribute('data-toggle'); openStates[id]=!openStates[id]; renderForm(); }));
  list.querySelectorAll('input[data-vm], select[data-vm], textarea[data-vm]').forEach(el=>{ el.addEventListener('input',onField); el.addEventListener('change',onField); });
  list.querySelectorAll('[data-action="remove"]').forEach(el=>el.addEventListener('click',()=>removeVM(el.getAttribute('data-vm'))));
  list.querySelectorAll('[data-action="dup"]').forEach(el=>el.addEventListener('click',()=>dupVM(el.getAttribute('data-vm'))));
  list.querySelectorAll('[data-action="addport"]').forEach(el=>el.addEventListener('click',()=>addPort(el.getAttribute('data-vm'))));
  list.querySelectorAll('[data-action="rmport"]').forEach(el=>el.addEventListener('click',()=>rmPort(el.getAttribute('data-vm'),parseInt(el.getAttribute('data-idx')))));
  list.querySelectorAll('[data-action="adddisk"]').forEach(el=>el.addEventListener('click',()=>addDisk(el.getAttribute('data-vm'))));
  list.querySelectorAll('[data-action="rmdisk"]').forEach(el=>el.addEventListener('click',()=>rmDisk(el.getAttribute('data-vm'),parseInt(el.getAttribute('data-idx')))));
  list.querySelectorAll('[data-versions]').forEach(el=>el.addEventListener('click',()=>chargerVersions(el.getAttribute('data-versions'))));
}

async function chargerVersions(id){
  const v=vms.find(v=>v.id===id); if(!v||!v.box) return;
  const statutEl=document.querySelector(`[data-versions-statut="${id}"]`);
  const dlEl=document.querySelector(`#dl-${id}`);
  const box=v.box;
  const urlCloud=`https://vagrantcloud.com/${box}`;
  if(statutEl) statutEl.textContent='Recherche sur Vagrant Cloud…';

  const appliquer=(versions)=>{
    if(dlEl) dlEl.innerHTML=versions.map(ver=>`<option value="${ver}">`).join('');
    if(statutEl) statutEl.innerHTML=`${versions.length} version(s) trouvée(s) — ouvre le champ pour les voir. <a href="${urlCloud}" target="_blank" rel="noopener">Voir sur Vagrant Cloud ↗</a>`;
  };

  // 1) Tentative directe navigateur → Vagrant Cloud (aucun serveur requis).
  try{
    const r=await fetch(`https://app.vagrantup.com/api/v1/box/${encodeURIComponent(box)}`);
    if(r.ok){
      const data=await r.json();
      const versions=(data.versions||[]).map(x=>x.version).filter(Boolean).slice(0,15);
      if(versions.length){ appliquer(versions); return; }
    }
  }catch(e){ /* CORS, hors-ligne, ou autre — on retente via l'API locale si dispo */ }

  // 2) Si un serveur local tourne (python web/api/main.py), il peut relayer
  //    la requête côté serveur (pas soumis au CORS du navigateur).
  try{
    const r2=await fetch(`/api/box-versions?box=${encodeURIComponent(box)}`);
    const data2=await r2.json();
    if(data2.versions && data2.versions.length){ appliquer(data2.versions); return; }
  }catch(e){ /* pas de serveur local — normal en mode autonome */ }

  // 3) Repli garanti : le lien direct vers la page Vagrant Cloud (marche toujours).
  if(statutEl) statutEl.innerHTML=`Recherche directe indisponible (hors-ligne ou CORS). <a href="${urlCloud}" target="_blank" rel="noopener">Voir les versions sur Vagrant Cloud ↗</a>`;
}

function onField(e){
  const el=e.target, v=vms.find(v=>v.id===el.getAttribute('data-vm')); if(!v) return;
  const f=el.getAttribute('data-field');
  let restructure=false;

  if(f==='port-guest'||f==='port-host'){ v.ports[parseInt(el.getAttribute('data-idx'))][f==='port-guest'?'guest':'host']=parseInt(el.value)||0; }
  else if(f==='disk-name'){ v.extraDisks[parseInt(el.getAttribute('data-idx'))].name=el.value; }
  else if(f==='disk-size'){ v.extraDisks[parseInt(el.getAttribute('data-idx'))].sizeGb=parseInt(el.value)||1; }
  else if(f==='cpus'){ v.cpus=parseInt(el.value)||1; }
  else if(f==='memory'){ if(el.value==='__custom__'){ restructure=true; } else { v.memory=parseInt(el.value)||1024; restructure=true; } }
  else if(f==='memoryCustom'){ v.memory=parseInt(el.value)||1024; }
  else if(f==='box'){ if(el.value==='__autre__'){ v.box=v.box&&!NOM_BOX[v.box]?v.box:''; } else { v.box=el.value; } restructure=true; }
  else if(f==='boxManuel'){ v.box=el.value; }
  else if(f==='locale'){ const [loc,km]=el.value.split('|'); v.locale=loc||''; v.keymap=km||''; }
  else if(f==='snippet'){ if(el.value){ const code=decodeURIComponent(escape(atob(el.value))); v.provisionScript=(v.provisionScript||'')+code; restructure=true; el.value=''; } }
  else if(f==='gui'||f==='disableSyncedFolder'||f==='publicNetwork'){ v[f]=el.checked; if(f==='disableSyncedFolder') restructure=true; }
  else { v[f]=el.value; }

  const struct=['name','provider','provisionType'].includes(f);
  if((e.type==='change'&&struct)||restructure){ renderForm(); }
  renderOutput(); sauver();
}

function renderOutput(){
  const code=buildVagrantfile(configCourante());
  $('#output').innerHTML=highlightRuby(code);
  window.__vf=code;
  const {erreurs,avert,nomsErr}=valider($('#g-provider').value,vms);
  document.querySelectorAll('.vm-card').forEach((card,i)=>{ const v=vms[i]; if(!v) return; const dot=card.querySelector('.dot'); if(dot) dot.classList.toggle('err',!!nomsErr[v.id]); });
  const box=$('#diagnostics');
  if(!erreurs.length&&!avert.length){ box.innerHTML='<div class="diag-item ok"><span class="ico">✓</span> Aucun souci détecté. Prêt pour vagrant up.</div>'; }
  else { box.innerHTML = erreurs.map(e=>`<div class="diag-item err"><span class="ico">✗</span> ${e}</div>`).join('') + avert.map(a=>`<div class="diag-item warn"><span class="ico">⚠</span> ${a}</div>`).join(''); }
  const ram=vms.reduce((s,v)=>s+(parseInt(v.memory)||0),0), cpu=vms.reduce((s,v)=>s+(parseInt(v.cpus)||0),0);
  const etat=erreurs.length?`<span class="bad">●</span> ${erreurs.length} erreur(s)`:`<span class="ok">●</span> config valide`;
  $('#status-bar').innerHTML=`<span class="stat"><b>${vms.length}</b> VM(s)</span><span class="stat"><b>${ram}</b> Mo RAM</span><span class="stat"><b>${cpu}</b> vCPU</span><span class="stat push-right">${etat}</span>`;
}

function loadPreset(kind){
  if(kind==='clear'){ vms=[]; openStates={}; rendre(); return; }
  const p=PRESETS[kind]; if(!p) return;
  vms=p.build(sousReseau()).map((m,i)=>{ const v=makeVM(i); Object.assign(v,m); v.syncedFolder=m.syncedFolder||('./'+m.name); openStates[v.id]=i===0; return v; });
  rendre();
}

function sauver(){ try{ localStorage.setItem(CLE,JSON.stringify({provider:$('#g-provider').value,boxCheck:$('#g-boxcheck').checked,subnet:$('#g-subnet').value,vms,openStates})); }catch(e){} }
function restaurer(){ try{ const d=JSON.parse(localStorage.getItem(CLE)); if(!d||!Array.isArray(d.vms)||!d.vms.length) return false; $('#g-provider').value=d.provider||'virtualbox'; $('#g-boxcheck').checked=!!d.boxCheck; $('#g-subnet').value=d.subnet||'192.168.56'; vms=d.vms; openStates=d.openStates||{}; return true; }catch(e){ return false; } }

function telecharger(blob,nom){ const u=URL.createObjectURL(blob); const a=document.createElement('a'); a.href=u; a.download=nom; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(u); }
function exporter(){ telecharger(new Blob([JSON.stringify(configCourante(),null,2)],{type:'application/json'}),'vagrantforge.config.json'); }
function telechargerInventaire(evt){
  const yaml = !!(evt && evt.shiftKey);
  const contenu = yaml ? buildAnsibleInventoryYaml(configCourante()) : buildAnsibleInventory(configCourante());
  telecharger(new Blob([contenu],{type:'text/plain'}), yaml ? 'inventaire-ansible.yml' : 'inventaire-ansible.ini');
}

/* ── Thème clair / sombre ─────────────────────────────────── */
const CLE_THEME='vagrantforge.theme';
function appliquerTheme(theme){
  document.documentElement.setAttribute('data-theme', theme==='dark'?'dark':'light');
  const btn=$('#theme-btn'); if(btn) btn.innerHTML = theme==='dark' ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
}
function basculerTheme(){
  const actuel=document.documentElement.getAttribute('data-theme')==='dark'?'dark':'light';
  const suivant=actuel==='dark'?'light':'dark';
  try{ localStorage.setItem(CLE_THEME, suivant); }catch(e){}
  appliquerTheme(suivant);
}
function themeInitial(){
  try{ const s=localStorage.getItem(CLE_THEME); if(s) return s; }catch(e){}
  return (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) ? 'dark' : 'light';
}

/* ── Lien de partage (config encodée en base64 dans l'URL) ─── */
function configVersBase64(cfg){ return btoa(unescape(encodeURIComponent(JSON.stringify(cfg)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,''); }
function base64VersConfig(b64){
  const norm = b64.replace(/-/g,'+').replace(/_/g,'/');
  const pad = norm.length%4 ? '='.repeat(4-(norm.length%4)) : '';
  return JSON.parse(decodeURIComponent(escape(atob(norm+pad))));
}
async function partagerLien(){
  const b64=configVersBase64(configCourante());
  const url=location.origin+location.pathname+'#cfg='+b64;
  try{ await navigator.clipboard.writeText(url); const f=$('#flash'); if(f){ f.textContent='lien copié ✓'; f.classList.add('show'); setTimeout(()=>{ f.classList.remove('show'); f.textContent='copié ✓'; },1600); } }
  catch(e){ prompt('Copie ce lien :', url); }
}
function chargerDepuisHash(){
  const m=location.hash.match(/#cfg=([^&]+)/);
  if(!m) return false;
  try{
    const c=base64VersConfig(m[1]);
    $('#g-provider').value=c.provider||'virtualbox';
    $('#g-boxcheck').checked=!!c.box_check_update;
    vms=(c.vms||[]).map((x,i)=>{
      const v=makeVM(i);
      Object.assign(v,{name:x.name??v.name,box:x.box??v.box,boxVersion:x.box_version??'',guestOs:x.guest_os??'',
        memory:x.memory??2048,cpus:x.cpus??1,ip:x.ip??'',provider:x.provider??'',gui:!!x.gui,publicNetwork:!!x.public_network,
        locale:x.locale??'',keymap:x.keymap??'',syncedFolder:x.synced_folder??('./'+(x.name||'vm')),
        disableSyncedFolder:!!x.disable_synced_folder,sshUsername:x.ssh_username??'',sshPassword:x.ssh_password??'',
        winrmUsername:x.winrm_username??'',winrmPassword:x.winrm_password??'',rootPassword:x.root_password??'',
        ports:x.ports??[],extraDisks:(x.extra_disks||[]).map(d=>({name:d.name||'',sizeGb:d.size_gb||10})),
        provisionType:(x.provision&&x.provision.type)||'none',provisionScript:(x.provision&&x.provision.script)||''});
      openStates[v.id]=i===0; return v;
    });
    history.replaceState(null,'',location.pathname);
    return vms.length>0;
  }catch(e){ console.warn('Lien de partage invalide', e); return false; }
}

function importer(f){ const r=new FileReader(); r.onload=()=>{ try{ const c=JSON.parse(r.result); $('#g-provider').value=c.provider||'virtualbox'; $('#g-boxcheck').checked=!!c.box_check_update; vms=(c.vms||[]).map((x,i)=>{ const v=makeVM(i); Object.assign(v,{name:x.name??v.name,box:x.box??v.box,boxVersion:x.box_version??'',guestOs:x.guest_os??'',memory:x.memory??2048,cpus:x.cpus??1,ip:x.ip??'',provider:x.provider??'',gui:!!x.gui,publicNetwork:!!x.public_network,locale:x.locale??'',keymap:x.keymap??'',syncedFolder:x.synced_folder??('./'+(x.name||'vm')),disableSyncedFolder:!!x.disable_synced_folder,sshUsername:x.ssh_username??'',sshPassword:x.ssh_password??'',winrmUsername:x.winrm_username??'',winrmPassword:x.winrm_password??'',rootPassword:x.root_password??'',ports:x.ports??[],extraDisks:(x.extra_disks||[]).map(d=>({name:d.name||'',sizeGb:d.size_gb||10})),provisionType:(x.provision&&x.provision.type)||'none',provisionScript:(x.provision&&x.provision.script)||''}); openStates[v.id]=i===0; return v; }); rendre(); }catch(e){ alert('JSON invalide : '+e.message); } }; r.readAsText(f); }

function rendre(){ renderForm(); renderOutput(); sauver(); }

/* ── Topologie réseau (Mermaid) ─────────────────────────────── */
let mermaidPret=false;
async function ouvrirTopologie(){
  $('#overlay-topo').classList.add('open');
  const code = buildTopologyMermaid(configCourante());
  window.__topoMermaid = code;
  const cible = $('#topo-diagram');
  if(typeof mermaid==='undefined'){
    cible.innerHTML = `<pre class="topo-fallback">${code.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</pre><div class="hint">Mermaid.js n'a pas pu se charger (hors-ligne ?) — voici le code brut, à coller sur <a href="https://mermaid.live" target="_blank" rel="noopener">mermaid.live</a>.</div>`;
    return;
  }
  try{
    if(!mermaidPret){ mermaid.initialize({startOnLoad:false, theme: document.documentElement.getAttribute('data-theme')==='dark'?'dark':'default'}); mermaidPret=true; }
    const id='mmd-'+Date.now();
    const {svg} = await mermaid.render(id, code);
    cible.innerHTML = svg;
  }catch(e){
    cible.innerHTML = `<pre class="topo-fallback">${code.replace(/&/g,'&amp;').replace(/</g,'&lt;')}</pre><div class="hint">Rendu impossible (${e.message||e}). Code Mermaid brut ci-dessus.</div>`;
  }
}
function fermerTopologie(){ $('#overlay-topo').classList.remove('open'); }

/* ── Lab aléatoire — pioche un preset au hasard OU compose 2-3 VMs random ── */
function labAleatoire(){
  const clesPresets = Object.keys(PRESETS);
  const composerAuHasard = Math.random() < 0.5;
  if(!composerAuHasard){
    const k = clesPresets[Math.floor(Math.random()*clesPresets.length)];
    loadPreset(k);
    return;
  }
  const toutesLesBoxes = CATALOGUE.flatMap(g=>g.boxes.filter(b=>!b.id.startsWith('gusztavvargadr/')));
  const nbVms = 2 + Math.floor(Math.random()*3); // 2 à 4
  const nomsPossibles = ['alpha','bravo','nova','orbit','zenith','flux','cosmo','pulse','delta','quartz','nimbus','vertex'];
  const sr = sousReseau();
  vms = [];
  openStates = {};
  for(let i=0;i<nbVms;i++){
    const box = toutesLesBoxes[Math.floor(Math.random()*toutesLesBoxes.length)];
    const v = makeVM(i);
    v.name = nomsPossibles[Math.floor(Math.random()*nomsPossibles.length)] + '-' + (i+1);
    v.box = box.id;
    v.memory = RAM_NIVEAUX[1+Math.floor(Math.random()*(RAM_NIVEAUX.length-2))][0];
    v.cpus = CPU_NIVEAUX[Math.floor(Math.random()*Math.min(3,CPU_NIVEAUX.length))][0];
    v.ip = sr+'.'+(10+i);
    v.syncedFolder = './'+v.name;
    if(Math.random()<0.5){ v.ports=[{guest:80,host:8080+i}]; }
    vms.push(v);
    openStates[v.id] = i===0;
  }
  rendre();
  confetti();
}

/* ── Petite pluie de confettis (canvas, zéro dépendance) ────── */
function confetti(){
  const nb=80, couleurs=['#6d5efc','#22d3c6','#f5a524','#ef4444','#34d399','#60a5fa'];
  const canvas=document.createElement('canvas');
  canvas.style.cssText='position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:9999;';
  canvas.width=window.innerWidth; canvas.height=window.innerHeight;
  document.body.appendChild(canvas);
  const ctx=canvas.getContext('2d');
  const parts=Array.from({length:nb},()=> ({
    x: Math.random()*canvas.width, y: -20-Math.random()*canvas.height*0.3,
    vx: (Math.random()-0.5)*3, vy: 2+Math.random()*3,
    taille: 4+Math.random()*5, coul: couleurs[Math.floor(Math.random()*couleurs.length)],
    rot: Math.random()*360, vrot: (Math.random()-0.5)*10,
  }));
  let frames=0;
  const boucle=()=>{
    frames++;
    ctx.clearRect(0,0,canvas.width,canvas.height);
    parts.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy; p.rot+=p.vrot;
      ctx.save(); ctx.translate(p.x,p.y); ctx.rotate(p.rot*Math.PI/180);
      ctx.fillStyle=p.coul; ctx.fillRect(-p.taille/2,-p.taille/2,p.taille,p.taille*0.6);
      ctx.restore();
    });
    if(frames<140) requestAnimationFrame(boucle);
    else canvas.remove();
  };
  requestAnimationFrame(boucle);
}

function ouvrirAide(){ $('#overlay').classList.add('open'); }
function fermerAide(){ $('#overlay').classList.remove('open'); }

function init(){
  const ICP={
    solo:['fa-server','ic-blue'], k3s:['fa-diagram-project','ic-cyan'],
    lamp:['fa-globe','ic-green'], devsecops:['fa-shield-halved','ic-amber'],
    pentest:['fa-user-secret','ic-red'], monitoring:['fa-chart-line','ic-cyan'],
    elk:['fa-magnifying-glass-chart','ic-amber'], wordpress:['fa-brands fa-wordpress','ic-blue'],
    'gitlab-runner':['fa-brands fa-gitlab','ic-amber'], nextcloud:['fa-cloud','ic-green'],
    'windows-ad':['fa-desktop','ic-blue'], hashistack:['fa-cubes','ic-violet'],
    matomo:['fa-chart-pie','ic-cyan'], minecraft:['fa-cube','ic-green'],
    openvpn:['fa-lock','ic-amber'], mattermost:['fa-comments','ic-blue'],
    'redis-cluster':['fa-layer-group','ic-red'],
    'haproxy-lb':['fa-scale-balanced','ic-cyan'], 'dns-dhcp':['fa-network-wired','ic-green'],
    wireguard:['fa-shield-halved','ic-violet'],
    'samba-ad':['fa-sitemap','ic-blue'], 'reverse-proxy-nginx':['fa-globe','ic-cyan'],
    'nfs-file-server':['fa-folder-open','ic-amber'], 'mail-server':['fa-envelope','ic-red'],
    'squid-proxy':['fa-filter','ic-green'],
    kubeadm:['fa-dharmachakra','ic-blue'], jenkins:['fa-brands fa-jenkins','ic-red'],
    'borg-backup':['fa-box-archive','ic-amber'], gitea:['fa-code-branch','ic-green'],
    'github-runner':['fa-brands fa-github','ic-violet'], awx:['fa-robot','ic-red'],
    duplicati:['fa-clock-rotate-left','ic-cyan'], 'docker-swarm':['fa-brands fa-docker','ic-blue']};
  $('#presets-grid').innerHTML=Object.entries(PRESETS).map(([k,p])=>{
    const [ic,cls]=ICP[k]||['fa-box','ic-violet'];
    const iconClass = ic.startsWith('fa-brands')?ic:`fa-solid ${ic}`;
    return `<button class="preset-card" data-preset="${k}" data-testid="preset-${k}-btn"><span class="preset-ic ${cls}"><i class="${iconClass}"></i></span><span class="preset-txt"><span class="t">${p.t}</span><span class="d">${p.d}</span></span></button>`;
  }).join('');
  document.querySelectorAll('[data-preset]').forEach(b=>b.addEventListener('click',()=>loadPreset(b.getAttribute('data-preset'))));
  $('#add-vm').addEventListener('click',addVM);
  $('#g-provider').addEventListener('change',rendre);
  $('#g-boxcheck').addEventListener('change',()=>{ renderOutput(); sauver(); });
  $('#g-subnet').addEventListener('input',()=>{ renderOutput(); sauver(); });

  $('#copy-btn').addEventListener('click',async()=>{ try{ await navigator.clipboard.writeText(window.__vf||''); const f=$('#flash'); f.classList.add('show'); setTimeout(()=>f.classList.remove('show'),1400); }catch(e){} });
  $('#dl-btn').addEventListener('click',()=>{
    telecharger(new Blob([window.__vf||''],{type:'application/octet-stream'}),'Vagrantfile');
    const {erreurs}=valider($('#g-provider').value,vms);
    if(!erreurs.length && vms.length) confetti();
  });
  $('#export-btn').addEventListener('click',exporter);
  $('#import-btn').addEventListener('click',()=>$('#import-file').click());
  $('#import-file').addEventListener('change',e=>{ if(e.target.files[0]) importer(e.target.files[0]); e.target.value=''; });
  $('#aide-btn').addEventListener('click',ouvrirAide);
  $('#modal-close').addEventListener('click',fermerAide);
  $('#overlay').addEventListener('click',e=>{ if(e.target===$('#overlay')) fermerAide(); });

  const themeBtn=$('#theme-btn'); if(themeBtn) themeBtn.addEventListener('click',basculerTheme);
  const langBtn=$('#lang-btn'); if(langBtn) langBtn.addEventListener('click',basculerLangue);
  const inventaireBtn=$('#inventaire-btn'); if(inventaireBtn) inventaireBtn.addEventListener('click',telechargerInventaire);
  const partageBtn=$('#partage-btn'); if(partageBtn) partageBtn.addEventListener('click',partagerLien);
  const topoBtn=$('#topo-btn'); if(topoBtn) topoBtn.addEventListener('click',ouvrirTopologie);
  const topoClose=$('#topo-close'); if(topoClose) topoClose.addEventListener('click',fermerTopologie);
  const overlayTopo=$('#overlay-topo'); if(overlayTopo) overlayTopo.addEventListener('click',e=>{ if(e.target===overlayTopo) fermerTopologie(); });
  const topoCopy=$('#topo-copy'); if(topoCopy) topoCopy.addEventListener('click',async()=>{ try{ await navigator.clipboard.writeText(window.__topoMermaid||''); }catch(e){} });
  const topoDl=$('#topo-dl'); if(topoDl) topoDl.addEventListener('click',()=>telecharger(new Blob([window.__topoMermaid||''],{type:'text/plain'}),'topologie.mmd'));
  const randomBtn=$('#random-btn'); if(randomBtn) randomBtn.addEventListener('click',labAleatoire);

  const moreBtn=$('#more-btn'), moreMenu=$('#more-menu');
  if(moreBtn && moreMenu){
    moreBtn.addEventListener('click',e=>{
      e.stopPropagation();
      const ouvert = moreMenu.classList.toggle('open');
      moreBtn.setAttribute('aria-expanded', ouvert ? 'true':'false');
    });
    moreMenu.querySelectorAll('.btn').forEach(b=>b.addEventListener('click',()=>{ moreMenu.classList.remove('open'); moreBtn.setAttribute('aria-expanded','false'); }));
    document.addEventListener('click',e=>{ if(!moreMenu.contains(e.target) && e.target!==moreBtn){ moreMenu.classList.remove('open'); moreBtn.setAttribute('aria-expanded','false'); } });
  }
  document.addEventListener('keydown',e=>{ if(e.key==='Escape'){ fermerAide(); fermerTopologie(); if(moreMenu) moreMenu.classList.remove('open'); } });

  $('#hamburger').addEventListener('click',()=>$('#menu-mobile').classList.toggle('open'));
  $('#menu-mobile').querySelectorAll('[data-menu]').forEach(b=>b.addEventListener('click',()=>{ const a=b.getAttribute('data-menu'); $('#menu-mobile').classList.remove('open'); if(a==='aide') ouvrirAide(); if(a==='topologie') ouvrirTopologie(); if(a==='aleatoire') labAleatoire(); if(a==='import') $('#import-file').click(); if(a==='export') exporter(); if(a==='inventaire') telechargerInventaire(); if(a==='partage') partagerLien(); if(a==='lang') basculerLangue(); }));
  document.querySelectorAll('.mobile-tabs button').forEach(b=>b.addEventListener('click',()=>{ document.body.dataset.vue=b.getAttribute('data-vue'); document.querySelectorAll('.mobile-tabs button').forEach(x=>x.classList.remove('actif')); b.classList.add('actif'); }));

  if(chargerDepuisHash()) rendre();
  else if(restaurer()) rendre();
  else addVM();

  // PWA : enregistrement du service worker (inactif en file://, normal).
  if('serviceWorker' in navigator && location.protocol!=='file:'){
    navigator.serviceWorker.register('service-worker.js').catch(()=>{});
  }
  let promptInstall=null;
  window.addEventListener('beforeinstallprompt', e=>{ e.preventDefault(); promptInstall=e; const b=$('#install-btn'); if(b) b.hidden=false; });
  const installBtn=$('#install-btn');
  if(installBtn) installBtn.addEventListener('click',async()=>{ if(!promptInstall) return; promptInstall.prompt(); await promptInstall.userChoice; promptInstall=null; installBtn.hidden=true; });
}
document.addEventListener('DOMContentLoaded',()=>{
  appliquerTheme(themeInitial());
  appliquerI18nStatique();
  const langBtn=document.getElementById('lang-btn'); if(langBtn) langBtn.textContent=t('nav.lang');
  const langBtnMobile=document.getElementById('lang-btn-mobile'); if(langBtnMobile) langBtnMobile.textContent=t('nav.lang');
  init();
});
