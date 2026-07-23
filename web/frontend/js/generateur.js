/* VagrantForge — génération du Vagrantfile côté client.
   Miroir fidèle de core/generateur.py (aperçu instantané hors-ligne). */

function escRuby(s){ return String(s).replace(/"/g,'\\"'); }
function nomVariable(nom){ let v=String(nom||'vm').replace(/[^a-zA-Z0-9_]/g,'_'); if(/^[0-9]/.test(v)) v='vm_'+v; return v; }

const PREFIXES_BOX_WINDOWS = ['gusztavvargadr/', 'StefanScherer/'];
function estBoxWindows(v){
  if(v.guestOs) return v.guestOs === 'windows';
  const box = v.box || '';
  return PREFIXES_BOX_WINDOWS.some(p => box.startsWith(p));
}

function blocDisques(vn, provider, disques){
  disques = (disques||[]).filter(d=>d && d.sizeGb);
  if(!disques.length) return '';
  let o = '';
  if(provider==='virtualbox'){
    disques.forEach((d,i)=>{
      const nomDisque = d.name || `disque${i+1}`;
      const tailleMo = parseInt(d.sizeGb)*1024;
      const fichier = escRuby(`${vn}_${nomDisque}_${i}.vdi`);
      o += `    ${vn}.vm.provider "virtualbox" do |vb|\n`;
      o += `      disque_${i} = File.join(Dir.pwd, ".vagrant", "disques", "${fichier}")\n`;
      o += `      FileUtils.mkdir_p(File.dirname(disque_${i})) unless Dir.exist?(File.dirname(disque_${i}))\n`;
      o += `      vb.customize ["createhd", "--filename", disque_${i}, "--size", ${tailleMo}] unless File.exist?(disque_${i})\n`;
      o += `      vb.customize ["storageattach", :id, "--storagectl", "SATA Controller", "--port", ${i+1}, "--device", 0, "--type", "hdd", "--medium", disque_${i}]\n`;
      o += `    end\n`;
    });
  } else if(provider==='libvirt'){
    disques.forEach((d,i)=>{
      const nomDisque = escRuby(d.name || `disque${i+1}`);
      o += `    ${vn}.vm.provider "libvirt" do |lv|\n      lv.storage :file, size: "${parseInt(d.sizeGb)}G", path: "${nomDisque}-disque${i}.qcow2"\n    end\n`;
    });
  } else {
    const noms = disques.map((d,i)=>d.name||`disque${i+1}`).join(', ');
    o += `    # Disque(s) additionnel(s) demandé(s) (${noms}) : non automatisable avec le provider "${provider}" — à créer/attacher manuellement.\n`;
  }
  return o;
}

function blocLocale(vn, locale, keymap){
  if(!locale && !keymap) return '';
  let s = '      # ── Langue & clavier (familles Debian/Ubuntu) ──\n      export DEBIAN_FRONTEND=noninteractive\n';
  if(locale){ s += `      sed -i 's/^# *${locale} UTF-8/${locale} UTF-8/' /etc/locale.gen\n      locale-gen\n      update-locale LANG=${locale}\n`; }
  if(keymap){ s += `      echo "XKBLAYOUT=${keymap}" > /etc/default/keyboard\n      setupcon -k --force || true\n`; }
  return `    ${vn}.vm.provision "shell", inline: <<-SHELL\n${s}    SHELL\n`;
}

/* Pont snake_case → camelCase pour les VMs.
 *
 * `configCourante()` (app.js) produit un objet cfg en snake_case (même
 * convention que core/schema.py côté Python), mais le code plus bas de ce
 * fichier a été écrit contre des clés camelCase (v.publicNetwork,
 * v.boxVersion, v.sshUsername, v.rootPassword, d.sizeGb…). Sans ce pont,
 * ces champs sont silencieusement `undefined` : le réseau public, les
 * identifiants SSH/WinRM, le mot de passe root et la taille des disques
 * additionnels disparaissaient du Vagrantfile généré côté navigateur (et
 * donc du fichier téléchargé) alors que la config les contenait bel et
 * bien. Corrigé une fois ici plutôt que dans chaque fonction. */
function normaliserVMs(vms){
  return (vms||[]).map(v=>({
    ...v,
    boxVersion: v.boxVersion ?? v.box_version,
    guestOs: v.guestOs ?? v.guest_os,
    publicNetwork: v.publicNetwork ?? v.public_network ?? false,
    syncedFolder: v.syncedFolder ?? v.synced_folder,
    disableSyncedFolder: v.disableSyncedFolder ?? v.disable_synced_folder ?? false,
    sshUsername: v.sshUsername ?? v.ssh_username,
    sshPassword: v.sshPassword ?? v.ssh_password,
    winrmUsername: v.winrmUsername ?? v.winrm_username,
    winrmPassword: v.winrmPassword ?? v.winrm_password,
    rootPassword: v.rootPassword ?? v.root_password,
    provisionType: v.provisionType ?? (v.provision && v.provision.type),
    provisionScript: v.provisionScript ?? (v.provision && v.provision.script),
    extraDisks: (v.extraDisks ?? v.extra_disks ?? []).map(d=>({
      ...d, sizeGb: d.sizeGb ?? d.size_gb,
    })),
  }));
}

function buildVagrantfile(cfg){
  const pg = cfg.provider || 'virtualbox';
  const vms = normaliserVMs(cfg.vms || []);
  const ram = vms.reduce((s,v)=>s+(parseInt(v.memory)||0),0);
  const cpu = vms.reduce((s,v)=>s+(parseInt(v.cpus)||0),0);
  const jour = new Date().toISOString().slice(0,10);
  const barre = '='.repeat(66);
  let o = `# -*- mode: ruby -*-\n# vi: set ft=ruby :\n#\n# ${barre}\n`;
  o += `#  Vagrantfile généré par VagrantForge — ${jour}\n`;
  o += `#  ${vms.length} VM(s) | ${ram} Mo RAM | ${cpu} vCPU | provider : ${pg}\n`;
  o += `#  Démarrage : vagrant up   |   État : vagrant status\n# ${barre}\n\n`;
  o += `Vagrant.require_version ">= 2.3.0"\n\nVagrant.configure("2") do |config|\n`;
  o += `  config.vm.box_check_update = ${cfg.box_check_update?'true':'false'}\n\n`;

  vms.forEach(v=>{
    const vn = nomVariable(v.name);
    const prov = v.provider || pg;
    o += `  # ── ${v.name} — ${v.box} | ${v.memory} Mo | ${v.cpus} vCPU | ${v.ip||'IP dynamique'}\n`;
    o += `  config.vm.define "${escRuby(v.name)}" do |${vn}|\n`;
    o += `    ${vn}.vm.box = "${escRuby(v.box)}"\n`;
    if(v.boxVersion) o += `    ${vn}.vm.box_version = "${escRuby(v.boxVersion)}"\n`;
    o += `    ${vn}.vm.hostname = "${escRuby(v.name)}"\n`;
    if(v.ip) o += `    ${vn}.vm.network "private_network", ip: "${escRuby(v.ip)}"\n`;
    if(v.publicNetwork) o += `    ${vn}.vm.network "public_network"  # pont réseau, interface choisie au démarrage\n`;
    (v.ports||[]).forEach(p=>{ o += `    ${vn}.vm.network "forwarded_port", guest: ${p.guest}, host: ${p.host}, auto_correct: true, id: "port-${p.guest}"\n`; });
    if(v.disableSyncedFolder) o += `    ${vn}.vm.synced_folder ".", "/vagrant", disabled: true\n`;
    else if(v.syncedFolder){ const ft = prov==='vmware_desktop'?'vmware':(prov==='virtualbox'?'virtualbox':null); o += `    ${vn}.vm.synced_folder "${escRuby(v.syncedFolder)}", "/vagrant"${ft?`, type: "${ft}"`:''}\n`; }
    const windows = estBoxWindows(v);
    if(windows){
      o += `    ${vn}.vm.guest = :windows\n    ${vn}.vm.communicator = "winrm"\n    ${vn}.vm.boot_timeout = 600\n`;
      if(v.winrmUsername) o += `    ${vn}.winrm.username = "${escRuby(v.winrmUsername)}"\n`;
      if(v.winrmPassword) o += `    ${vn}.winrm.password = "${escRuby(v.winrmPassword)}"\n`;
    } else {
      if(v.sshUsername) o += `    ${vn}.ssh.username = "${escRuby(v.sshUsername)}"\n`;
      if(v.sshPassword){ o += `    ${vn}.ssh.password = "${escRuby(v.sshPassword)}"\n    ${vn}.ssh.insert_key = false\n`; }
    }

    if(prov==='virtualbox'){
      o += `    ${vn}.vm.provider "virtualbox" do |vb|\n      vb.name = "${escRuby(v.name)}"\n      vb.memory = ${v.memory}\n      vb.cpus = ${v.cpus}\n      vb.gui = ${v.gui?'true':'false'}\n    end\n`;
    } else if(prov==='vmware_desktop'){
      o += `    ${vn}.vm.provider "vmware_desktop" do |vw|\n      vw.gui = ${v.gui?'true':'false'}\n      vw.vmx["displayName"] = "${escRuby(v.name)}"\n      vw.vmx["memsize"] = "${v.memory}"\n      vw.vmx["numvcpus"] = "${v.cpus}"\n      vw.vmx["cpuid.coresPerSocket"] = "${v.cpus}"\n`;
      if(v.ip) o += `      vw.vmx["ethernet0.virtualDev"] = "vmxnet3"  # évite les soucis d'IP statique avec l'adaptateur par défaut\n`;
      o += `    end\n`;
    } else if(prov==='libvirt'){
      o += `    ${vn}.vm.provider "libvirt" do |lv|\n      lv.memory = ${v.memory}\n      lv.cpus = ${v.cpus}\n    end\n`;
    }

    o += blocDisques(vn, prov, v.extraDisks);

    if(!windows) o += blocLocale(vn, v.locale, v.keymap);

    if(v.provisionType==='shell'){
      let full = v.provisionScript||'';
      if(v.rootPassword){
        full = windows
          ? `$mdp = ConvertTo-SecureString "${escRuby(v.rootPassword)}" -AsPlainText -Force\nSet-LocalUser -Name "Administrator" -Password $mdp\n` + full
          : `echo "root:${escRuby(v.rootPassword)}" | chpasswd\n` + full;
      }
      if(windows) full = '#ps1_sysnative\n' + full;
      const sc = full.split('\n').map(l=>'      '+l).join('\n');
      o += `    ${vn}.vm.provision "shell", inline: <<-SHELL\n${sc}\n    SHELL\n`;
    } else if(v.provisionType==='ansible'){
      o += `    ${vn}.vm.provision "ansible" do |ansible|\n      ansible.playbook = "${escRuby(v.provisionScript)}"\n    end\n`;
      if(v.rootPassword) o += `    ${vn}.vm.provision "shell", inline: 'echo "root:${escRuby(v.rootPassword)}" | chpasswd'\n`;
    } else if(v.rootPassword){
      o += `    ${vn}.vm.provision "shell", inline: 'echo "root:${escRuby(v.rootPassword)}" | chpasswd'\n`;
    }
    o += `  end\n\n`;
  });
  o += `end\n`;
  return o;
}

/* Inventaire Ansible (INI) — miroir de core/generateur.py::construire_inventaire_ansible. */
function groupeAnsible(nom){ const b=(nom||'').split(/[-_]/)[0]; return b||'vagrantforge'; }
function buildAnsibleInventory(cfg){
  const vms = normaliserVMs(cfg.vms||[]);
  if(!vms.length) return '# Aucune VM dans la config : inventaire vide.\n';
  const groupes = {};
  let o = '# Inventaire Ansible généré par VagrantForge — statique, format INI.\n';
  o += '# Utilisation : ansible-playbook -i inventaire.ini playbook.yml\n\n';
  o += "[tous:vars]\nansible_ssh_common_args='-o StrictHostKeyChecking=no'\n\n[tous]\n";
  vms.forEach(v=>{
    const nom=v.name||'vm', cible=v.ip||nom, windows=estBoxWindows(v);
    const vars=[`ansible_host=${cible}`];
    if(windows){
      vars.push('ansible_connection=winrm','ansible_winrm_transport=basic','ansible_port=5985');
      if(v.winrmUsername) vars.push(`ansible_user=${v.winrmUsername}`);
      if(v.winrmPassword) vars.push(`ansible_password=${v.winrmPassword}`);
    } else {
      vars.push(`ansible_user=${v.sshUsername||'vagrant'}`);
      if(v.sshPassword) vars.push(`ansible_password=${v.sshPassword}`);
    }
    o += `${nom} ${vars.join(' ')}\n`;
    const g=groupeAnsible(nom); (groupes[g]=groupes[g]||[]).push(nom);
  });
  o += '\n';
  Object.entries(groupes).forEach(([g,membres])=>{
    if(membres.length<2 && g!=='vagrantforge') return;
    o += `[${g}]\n${membres.join('\n')}\n\n`;
  });
  return o.replace(/\n+$/,'\n');
}
/* Inventaire Ansible (YAML) — miroir de core/generateur.py::construire_inventaire_ansible_yaml. */
function buildAnsibleInventoryYaml(cfg){
  const vms = normaliserVMs(cfg.vms||[]);
  if(!vms.length) return '# Aucune VM dans la config : inventaire vide.\nall:\n  hosts: {}\n';
  const groupes = {};
  const ligneHote = v=>{
    const nom=v.name||'vm', ip=v.ip||nom, windows=estBoxWindows(v);
    const varsHote=[`ansible_host: ${ip}`];
    if(windows){
      varsHote.push('ansible_connection: winrm','ansible_winrm_transport: basic','ansible_port: 5985');
      if(v.winrmUsername) varsHote.push(`ansible_user: ${v.winrmUsername}`);
      if(v.winrmPassword) varsHote.push(`ansible_password: ${v.winrmPassword}`);
    } else {
      varsHote.push(`ansible_user: ${v.sshUsername||'vagrant'}`);
      if(v.sshPassword) varsHote.push(`ansible_password: ${v.sshPassword}`);
    }
    return [`    ${nom}:`, ...varsHote.map(l=>`      ${l}`)];
  };
  vms.forEach(v=>{ const g=groupeAnsible(v.name||'vm'); (groupes[g]=groupes[g]||[]).push(v); });
  let sortie = ['# Inventaire Ansible généré par VagrantForge — YAML.',
    '# Utilisation : ansible-playbook -i inventaire.yml playbook.yml',
    'all:', '  vars:', "    ansible_ssh_common_args: '-o StrictHostKeyChecking=no'", '  hosts:'];
  vms.forEach(v=>{ sortie = sortie.concat(ligneHote(v)); });
  const groupesMulti = Object.entries(groupes).filter(([,m])=>m.length>=2);
  if(groupesMulti.length){
    sortie.push('  children:');
    groupesMulti.forEach(([g,membres])=>{
      sortie.push(`    ${g}:`); sortie.push('      hosts:');
      membres.forEach(v=>sortie.push(`        ${v.name||'vm'}: {}`));
    });
  }
  return sortie.join('\n')+'\n';
}

/* Diagramme de topologie réseau (Mermaid) — miroir de core/topologie.py. */
function buildTopologyMermaid(cfg){
  const vms = normaliserVMs(cfg.vms||[]);
  if(!vms.length) return 'graph LR\n  vide["Aucune VM dans la config"]\n';
  const lignes = ['graph LR', '  reseau(("Réseau privé<br/>Vagrant"))'];
  vms.forEach(v=>{
    const vn = nomVariable(v.name);
    const icone = estBoxWindows(v) ? '🪟' : '🐧';
    const etiquette = [icone, v.name||'vm', v.box||'?', `${v.memory||'?'} Mo · ${v.cpus||'?'} vCPU`];
    if(v.ip) etiquette.push(v.ip);
    lignes.push(`  ${vn}["${etiquette.join('<br/>')}"]`);
    lignes.push(`  reseau --- ${vn}`);
    (v.ports||[]).forEach(p=>{
      if(p.guest==null||p.host==null) return;
      const hoteId = `hote_${vn}_${p.host}`;
      lignes.push(`  ${hoteId}(["hôte:${p.host}"])`);
      lignes.push(`  ${hoteId} -.->|forward| ${vn}`);
      lignes.push(`  ${vn} -.-|:${p.guest}| ${hoteId}`);
    });
    if(v.publicNetwork) lignes.push(`  internet((Internet)) --- ${vn}`);
  });
  return lignes.join('\n')+'\n';
}

function highlightRuby(code){
  const lignes = code.split('\n').map(line=>{
    let l = line.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    if(/^\s*#/.test(l)){ l = `<span class="tok-comment">${l}</span>`; }
    else {
      l = l.replace(/"([^"]*)"/g,'<span class="tok-str">"$1"</span>');
      l = l.replace(/\b(Vagrant|configure|require_version|do|end)\b/g,'<span class="tok-kw">$1</span>');
      l = l.replace(/\b(true|false|nil)\b/g,'<span class="tok-const">$1</span>');
      l = l.replace(/\b(\d+)\b/g,'<span class="tok-num">$1</span>');
    }
    return `<span class="cl">${l || '​'}</span>`;
  }).join('');
  return `<div class="code">${lignes}</div>`;
}
