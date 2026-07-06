/* VagrantForge — données de référence (catalogue OS, compat, niveaux, presets).
   Chargé en global (pas de module ES) pour fonctionner aussi en file://. */

/* ── Catalogue d'OS (noms lisibles) ─────────────────────────── */
const CATALOGUE = [
  { famille:'Debian', boxes:[
    { id:'debian/bookworm64', nom:'Debian 12 « Bookworm » — stable (recommandé)' },
    { id:'debian/bullseye64', nom:'Debian 11 « Bullseye » — oldstable' },
    { id:'debian/testing64',  nom:'Debian testing « Trixie »' },
  ]},
  { famille:'Ubuntu', boxes:[
    { id:'ubuntu/noble64', nom:'Ubuntu 24.04 LTS « Noble »' },
    { id:'ubuntu/jammy64', nom:'Ubuntu 22.04 LTS « Jammy »' },
    { id:'ubuntu/focal64', nom:'Ubuntu 20.04 LTS « Focal »' },
  ]},
  { famille:'RHEL-like (Rocky / Alma / CentOS)', boxes:[
    { id:'generic/rocky9', nom:'Rocky Linux 9' },
    { id:'generic/rocky8', nom:'Rocky Linux 8' },
    { id:'generic/alma9',  nom:'AlmaLinux 9' },
    { id:'generic/alma8',  nom:'AlmaLinux 8' },
    { id:'bento/centos-stream-9', nom:'CentOS Stream 9' },
  ]},
  { famille:'Compatible VMware/Parallels (bento)', boxes:[
    { id:'bento/debian-12',    nom:'Debian 12 (bento — multi-provider)' },
    { id:'bento/debian-11',    nom:'Debian 11 (bento — multi-provider)' },
    { id:'bento/ubuntu-24.04', nom:'Ubuntu 24.04 (bento — multi-provider)' },
    { id:'bento/ubuntu-22.04', nom:'Ubuntu 22.04 (bento — multi-provider)' },
  ]},
  { famille:'Autres distributions', boxes:[
    { id:'generic/alpine319', nom:'Alpine Linux 3.19 — ultra-léger' },
    { id:'archlinux/archlinux', nom:'Arch Linux — rolling release' },
    { id:'opensuse/Leap-15.5.x86_64', nom:'openSUSE Leap 15.5' },
    { id:'generic/ubuntu2204', nom:'Ubuntu 22.04 (generic)' },
  ]},
  { famille:'Spécialisées', boxes:[
    { id:'kalilinux/rolling', nom:'Kali Linux — pentest' },
    { id:'generic/freebsd14', nom:'FreeBSD 14 — BSD' },
    { id:'generic/freebsd13', nom:'FreeBSD 13 — BSD' },
  ]},
];
const NOM_BOX = {};
CATALOGUE.forEach(g => g.boxes.forEach(b => NOM_BOX[b.id] = b.nom));

/* ── Compatibilité box <-> providers (validation) ───────────── */
const BOX_PROVIDERS = {
  'debian/bookworm64':['virtualbox','libvirt','hyperv','qemu'],
  'debian/bullseye64':['virtualbox','libvirt','hyperv','qemu'],
  'debian/testing64':['virtualbox','libvirt','hyperv','qemu'],
  'ubuntu/noble64':['virtualbox','libvirt','hyperv'],
  'ubuntu/jammy64':['virtualbox','libvirt','hyperv'],
  'ubuntu/focal64':['virtualbox','libvirt','hyperv'],
  'bento/debian-12':['virtualbox','vmware_desktop','parallels'],
  'bento/debian-11':['virtualbox','vmware_desktop','parallels'],
  'bento/ubuntu-24.04':['virtualbox','vmware_desktop','parallels'],
  'bento/ubuntu-22.04':['virtualbox','vmware_desktop','parallels'],
  'bento/centos-stream-9':['virtualbox','vmware_desktop','parallels'],
  'generic/rocky9':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/rocky8':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/alma9':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/alma8':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/ubuntu2204':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/freebsd14':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/freebsd13':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'generic/alpine319':['virtualbox','vmware_desktop','libvirt','hyperv','parallels'],
  'kalilinux/rolling':['virtualbox','vmware_desktop'],
  'archlinux/archlinux':['virtualbox','libvirt','hyperv','vmware_desktop'],
  'opensuse/Leap-15.5.x86_64':['virtualbox','libvirt','hyperv'],
};
function boxSupportsProvider(box, provider){
  const l = BOX_PROVIDERS[box];
  return l ? l.includes(provider) : null;
}

/* ── Niveaux de RAM & CPU ───────────────────────────────────── */
const RAM_NIVEAUX = [
  [512,'512 Mo — minimal'],
  [1024,'1 Go — léger'],
  [2048,'2 Go — confort (recommandé)'],
  [3072,'3 Go'],
  [4096,'4 Go — costaud'],
  [6144,'6 Go'],
  [8192,'8 Go — lourd'],
];
const CPU_NIVEAUX = [[1,'1 cœur'],[2,'2 cœurs'],[3,'3 cœurs'],[4,'4 cœurs']];

/* ── Langues (locale + clavier) ─────────────────────────────── */
const LOCALES = [
  ['', '', 'Ne pas changer (défaut de la box)'],
  ['fr_FR.UTF-8','fr','Français — clavier AZERTY (fr)'],
  ['en_US.UTF-8','us','Anglais US — clavier QWERTY (us)'],
  ['en_GB.UTF-8','gb','Anglais UK'],
  ['es_ES.UTF-8','es','Espagnol'],
  ['de_DE.UTF-8','de','Allemand'],
  ['it_IT.UTF-8','it','Italien'],
  ['pt_BR.UTF-8','br','Portugais (Brésil)'],
];

/* ── Bibliothèque de commandes shell (aide provisioning) ────── */
const SNIPPETS = [
  ['Système', [
    ['MàJ complète du système', 'apt-get update -y && apt-get upgrade -y\n'],
    ['Outils de base (git, curl, vim…)', 'apt-get install -y curl wget git vim htop unzip ca-certificates\n'],
    ['Fuseau horaire Paris', 'timedatectl set-timezone Europe/Paris\n'],
  ]],
  ['Serveurs web', [
    ['Nginx', 'apt-get install -y nginx\nsystemctl enable --now nginx\n'],
    ['Apache', 'apt-get install -y apache2\nsystemctl enable --now apache2\n'],
  ]],
  ['Bases de données', [
    ['MariaDB', 'apt-get install -y mariadb-server\nsystemctl enable --now mariadb\n'],
    ['PostgreSQL', 'apt-get install -y postgresql\nsystemctl enable --now postgresql\n'],
  ]],
  ['Conteneurs & langages', [
    ['Docker + Compose', 'curl -fsSL https://get.docker.com | sh\nusermod -aG docker vagrant\n'],
    ['Node.js (LTS)', 'curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -\napt-get install -y nodejs\n'],
    ['Python 3 + pip + venv', 'apt-get install -y python3 python3-pip python3-venv\n'],
  ]],
  ['Sécurité', [
    ['Pare-feu UFW (SSH ouvert)', 'apt-get install -y ufw\nufw allow OpenSSH\nufw --force enable\n'],
    ['fail2ban', 'apt-get install -y fail2ban\nsystemctl enable --now fail2ban\n'],
    ['Utilisateur sudo « devops »', "useradd -m -s /bin/bash devops\necho 'devops ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/devops\n"],
  ]],
];

/* ── Presets ────────────────────────────────────────────────── */
function _vmp(nom, box, memory, cpus, sr, ip, ports, script, extra){
  return Object.assign({name:nom, box, memory, cpus, ip: ip?sr+'.'+ip:'',
    syncedFolder:'./'+nom, ports:ports||[],
    provisionType: script?'shell':'none', provisionScript: script||''}, extra||{});
}
const PRESETS = {
  solo: {t:'VM unique', d:'Une Debian 12 minimale pour bidouiller.', build:sr=>[
    _vmp('box','debian/bookworm64',1024,1,sr,10,[], 'apt-get update -y\n')]},
  k3s: {t:'Cluster K3s', d:'1 master + 2 workers Kubernetes léger.', build:sr=>[
    _vmp('k3s-master','debian/bookworm64',2048,2,sr,10,[], 'apt-get update -y\ncurl -sfL https://get.k3s.io | sh -\ncat /var/lib/rancher/k3s/server/node-token\n'),
    _vmp('k3s-worker1','debian/bookworm64',1536,1,sr,11,[], 'apt-get update -y\n# Rejoindre : K3S_URL=https://'+sr+'.10:6443 K3S_TOKEN=<token> curl -sfL https://get.k3s.io | sh -\n'),
    _vmp('k3s-worker2','debian/bookworm64',1536,1,sr,12,[], 'apt-get update -y\n# Rejoindre : K3S_URL=https://'+sr+'.10:6443 K3S_TOKEN=<token> curl -sfL https://get.k3s.io | sh -\n')]},
  lamp: {t:'LAMP + pfSense', d:'Serveur web/PHP/MySQL derrière un pare-feu.', build:sr=>[
    _vmp('pfsense','generic/freebsd14',1024,1,sr,1,[], '# pfSense : configuration via console/web GUI\n'),
    _vmp('lamp','debian/bookworm64',1024,1,sr,20,[{guest:80,host:8080}], 'apt-get update -y\napt-get install -y apache2 mariadb-server php libapache2-mod-php php-mysql\nsystemctl enable --now apache2 mariadb\n')]},
  devsecops: {t:'DevSecOps CI/CD', d:'GitLab + SonarQube + Vault/monitoring.', build:sr=>[
    _vmp('gitlab-ci','debian/bookworm64',2048,2,sr,30,[{guest:80,host:8090}], 'apt-get update -y\n# Runner GitLab CI à configurer\n'),
    _vmp('sonarqube','debian/bookworm64',2048,2,sr,31,[{guest:9000,host:9000}], 'apt-get update -y\nsysctl -w vm.max_map_count=524288\n'),
    _vmp('vault-monitoring','debian/bookworm64',1536,1,sr,32,[{guest:8200,host:8200},{guest:3000,host:3000}], 'apt-get update -y\n# Vault + Grafana/Prometheus\n')]},
  pentest: {t:'Lab pentest', d:'Kali attaquant + cible vulnérable isolée.', build:sr=>[
    _vmp('kali','kalilinux/rolling',3072,2,sr,5,[], 'apt-get update -y\n# Kali déjà outillée\n', {locale:'fr_FR.UTF-8',keymap:'fr'}),
    _vmp('cible','debian/bookworm64',1024,1,sr,6,[{guest:80,host:8081}], 'apt-get update -y\n# ATTENTION : volontairement faible, réseau privé UNIQUEMENT\napt-get install -y apache2 vsftpd\n', {rootPassword:'toor'})]},
};
