/* VagrantForge — i18n minimal (FR ↔ EN), zéro dépendance.
 *
 * Portée assumée : l'interface (nav, hero, en-têtes, libellés de formulaire,
 * modale d'aide, presets) bascule en anglais. Restent volontairement en
 * français : les messages de validation produits par le cœur (core/schema.py
 * et son miroir validation.js — un gros chantier à part, documenté dans
 * PROMPT-PROJET.md), et le contenu généré dans le Vagrantfile lui-même
 * (commentaires, scripts de provisioning) puisqu'il s'agit de code, pas
 * d'interface.
 *
 * Utilisation :
 *   - Texte statique : <span data-i18n="nav.aide">Comment ça marche</span>
 *   - Attribut (ex. title d'un ⓘ) : data-i18n-title="tip.provider"
 *   - Placeholder : data-i18n-placeholder="champ.recherche"
 *   - Dans le JS : t('nav.aide')  → chaîne dans la langue courante
 */

const I18N = {
  fr: {
    'nav.theme': 'Basculer thème clair/sombre',
    'nav.aide': 'Comment ça marche',
    'nav.topologie': 'Topologie',
    'nav.aleatoire': 'Lab aléatoire',
    'nav.plus': 'Plus',
    'nav.partager': 'Partager',
    'nav.inventaire': 'Inventaire Ansible',
    'nav.importer': 'Importer',
    'nav.exporter': 'Exporter',
    'nav.installer': "Installer l'appli",
    'nav.telecharger': 'Télécharger le projet',
    'nav.lang': 'English',

    'hero.titre1': 'Forge tes labs de VMs',
    'hero.titre2': 'sans écrire une ligne de Ruby',
    'hero.sous': "Décris tes machines dans le formulaire — VagrantForge écrit le Vagrantfile, validé, commenté et prêt à vagrant up. Tout tourne dans ton navigateur.",
    'hero.commencer': 'Commencer',
    'hero.telecharger': 'Télécharger le projet',
    'feat.multivm.t': 'Multi-VM', 'feat.multivm.d': 'Autant de machines que tu veux',
    'feat.lang.t': 'Langue & clavier', 'feat.lang.d': 'AZERTY réglé au 1er boot',
    'feat.presets.t': 'Presets', 'feat.presets.d': "Labs prêts à l'emploi",
    'feat.valid.t': 'Validation live', 'feat.valid.d': 'Erreurs & alertes en direct',

    'tabs.config': 'Configuration', 'tabs.apercu': 'Aperçu',

    'g.titre': 'Réglages globaux',
    'g.provider': 'Logiciel de virtualisation (provider)',
    'g.provider.tip': 'Le logiciel qui fait tourner les VMs sur ta machine. VirtualBox est gratuit et le plus répandu — choisis-le en cas de doute.',
    'g.provider.vb': 'VirtualBox — gratuit, le plus courant',
    'g.provider.vm': 'VMware Desktop — payant, rapide',
    'g.provider.lv': 'libvirt (KVM/QEMU) — Linux',
    'g.boxcheck': 'Vérifier les mises à jour des images au démarrage',
    'g.boxcheck.tip': 'Si coché, Vagrant vérifie une nouvelle version de l\u2019image à chaque « vagrant up ». Décoché = démarrage plus rapide et reproductible.',
    'g.hostsfile': 'Résolution des noms entre VMs (/etc/hosts)',
    'g.hostsfile.tip': 'Si coché, chaque VM ayant une IP reçoit une entrée /etc/hosts (ou le fichier hosts Windows) pour toutes les autres VMs de la config — elles peuvent alors se joindre par nom (ping web, curl http://db) sans serveur DNS.',
    'g.subnet': "Réseau privé — plage d'adresses",
    'g.subnet.tip': 'Les VMs communiquent entre elles et avec ton PC sur ce réseau isolé (host-only). Chaque VM prend une adresse ici : .10, .11, .12…',
    'g.subnet.hint': "C'est un réseau <b>privé</b> entre ton PC et les VMs (rien à voir avec Internet). Chaque VM ajoutée reçoit l'adresse suivante : 192.168.56.<b>10</b>, .<b>11</b>, .<b>12</b>…",

    'p.titre': 'Démarrages rapides', 'p.vider': 'tout vider',
    'v.titre': 'Machines virtuelles', 'v.ajouter': 'ajouter une VM',

    'term.copier': 'copier', 'term.telecharger': 'télécharger', 'term.copie': 'copié ✓', 'term.lien_copie': 'lien copié ✓',

    'footer': 'Forgé avec <span class="grad"><i class="fa-solid fa-hammer"></i> VagrantForge</span> — décris, valide, <code>vagrant up</code>.',

    'modal.titre': 'Comment ça marche',
    'modal.intro': 'VagrantForge fabrique un <b>Vagrantfile</b> : le plan de montage de tes machines virtuelles. Tu remplis un formulaire, le fichier se génère tout seul à droite.',
    'modal.etapes': 'En 4 étapes',
    'modal.etape1': 'Choisis ton <b>provider</b> (VirtualBox si tu ne sais pas) dans les réglages globaux.',
    'modal.etape2': '<b>Ajoute des VMs</b> : leur OS, leur RAM, leur réseau, leur langue, ce qu\u2019elles installent au démarrage.',
    'modal.etape3': 'Le <b>Vagrantfile</b> apparaît à droite, coloré et validé en temps réel.',
    'modal.etape4': '<b>Télécharge-le</b> dans un dossier vide, ouvre un terminal dedans et lance <code>vagrant up</code>. C\u2019est parti.',
    'modal.vocab': 'Le vocabulaire',
    'modal.box.t': 'box (image)', 'modal.box.d': 'Le disque de départ d\u2019une VM (ex. Debian 12). VagrantForge te propose les vraies images publiques, par leur nom complet.',
    'modal.provider.t': 'provider', 'modal.provider.d': 'Le logiciel qui exécute les VMs sur ton PC : VirtualBox, VMware ou libvirt.',
    'modal.ip.t': 'IP privée (host-only)', 'modal.ip.d': 'L\u2019adresse pour joindre la VM depuis ton PC et pour que les VMs se parlent entre elles, sur un réseau isolé. Ex. <code>192.168.56.10</code>.',
    'modal.port.t': 'port redirigé', 'modal.port.d': 'Rend un service de la VM accessible depuis ton PC : « guest 80 → host 8080 » = <code>localhost:8080</code> ouvre le port 80 de la VM.',
    'modal.prov.t': 'provisioning', 'modal.prov.d': 'Les commandes lancées automatiquement au premier démarrage (installer nginx, Docker…). Utilise l\u2019aide « insérer une commande ».',
    'modal.creds.t': 'identifiants SSH/mot de passe root', 'modal.creds.d': 'Laisse tout vide dans la plupart des cas : Vagrant se connecte tout seul avec sa propre clé SSH. Ne remplis « SSH — mot de passe » ou « mot de passe root » que si tu as un besoin précis (login GUI, mot de passe imposé par un TP).',
    'modal.pont.t': 'réseau en pont (public_network)', 'modal.pont.d': 'Met la VM directement sur ton vrai réseau (au lieu du réseau privé Vagrant isolé). À activer seulement si tu sais pourquoi — sinon laisse décoché.',
    'modal.avant.titre': 'Avant de lancer <code>vagrant up</code>',
    'modal.avant.1': 'Installe <b>Vagrant</b> et au moins un provider (VirtualBox est le plus simple). Si tu utilises la CLI VagrantForge, <code>forge doctor</code> vérifie tout ça pour toi.',
    'modal.avant.2': 'Télécharge le Vagrantfile dans un <b>dossier vide</b> dédié à ce lab (un dossier = un lab).',
    'modal.avant.3': 'Regarde les <b>diagnostics</b> sous l\u2019aperçu : les ✗ (erreurs) empêchent une génération propre, les ⚠ (avertissements) sont à lire mais souvent sans gravité pour un lab jetable.',
    'modal.astuce': '<b>Astuce :</b> tu peux exporter ta config en JSON (bouton « Exporter ») pour la sauvegarder ou la partager, et la réimporter plus tard. Le bouton <b>« Télécharger le projet »</b> te donne tout le code (web + CLI + API) dans une archive.',

    'topo.titre': 'Topologie du lab',
    'topo.intro': "Vue d'ensemble du réseau : VMs, IP privées, ports redirigés et accès public éventuel.",
    'topo.copier': 'copier le code Mermaid',
    'topo.telecharger': 'télécharger (.mmd)',

    // Libellés de la carte VM (générés en JS)
    'vm.nom': 'Nom de la VM',
    'vm.os': "Système d'exploitation (OS)",
    'vm.os.tip': "L'image de départ de la VM. Choisis par son nom : « Debian 12 » = la version stable actuelle. Les images bento marchent aussi sous VMware.",
    'vm.version': "Version de l'image",
    'vm.version.tip': "Laisse « dernière » pour la plus récente. Fige un numéro pour un lab 100 % reproductible dans le temps. Format propre à chaque box (ex: 12.20240905.1 pour Debian) — utilise le bouton pour voir les vraies versions publiées.",
    'vm.ram': 'Mémoire vive (RAM)',
    'vm.cpu': 'Processeurs (vCPU)',
    'vm.langue': 'Langue & clavier de la VM',
    'vm.langue.tip': 'Règle la langue du système et la disposition du clavier au premier démarrage (familles Debian/Ubuntu). Pratique pour un clavier AZERTY.',
    'vm.ip': 'IP privée (réseau host-only)',
    'vm.ip.tip': 'Adresse fixe pour joindre la VM depuis ton PC et entre VMs, sur un réseau isolé. Laisse vide pour une IP automatique.',
    'vm.provider': 'Provider spécifique (sinon : global)',
    'vm.provider.tip': "Laisse « hérite du global » sauf besoin précis (ex. une seule VM Windows qui doit tourner sous VMware pendant que les autres sont en VirtualBox).",
    'vm.gui': 'Afficher la fenêtre de la VM (utile pour debug)',
    'vm.gui.tip': "Ouvre la fenêtre d'affichage de la VM au démarrage (utile pour une install graphique ou du débogage). Décoché : la VM tourne en tâche de fond, ce qui est le cas normal pour un serveur.",
    'vm.pont': 'Interface en pont (public_network) — la VM sur ton vrai réseau',
    'vm.pont.tip': "⚠️ Branche la VM directement sur ton réseau local (pas seulement le réseau privé Vagrant) — elle devient joignable par les autres appareils du réseau, et inversement. À activer seulement si tu sais pourquoi (ex. serveur DHCP/PXE, VPN). Vagrant demandera quelle interface réseau utiliser au premier démarrage.",
    'vm.dossier': 'Dossier partagé PC → /vagrant',
    'vm.dossier.tip': "Un dossier de ton PC visible dans la VM sous /vagrant. Pratique pour éditer du code côté PC et l'exécuter dans la VM.",
    'vm.dossier_off': 'Désactiver le dossier partagé (contourne un bug du plugin VMware récent)',
    'vm.winrm_user': 'WinRM — utilisateur', 'vm.winrm_pass': 'WinRM — mot de passe',
    'vm.winrm.tip': "Identifiants pour piloter la VM Windows à distance (pas de SSH sur Windows). Laisse vide pour utiliser ceux par défaut de la box (souvent vagrant/vagrant) — vérifie la doc de la box sur Vagrant Cloud si la connexion échoue.",
    'vm.admin_pass': 'Mot de passe Administrator',
    'vm.admin_pass.tip': "Change le mot de passe du compte Administrator local au premier démarrage. Laisse vide pour garder celui de la box telle quelle.",
    'vm.ssh_user': 'SSH — utilisateur', 'vm.ssh_pass': 'SSH — mot de passe',
    'vm.ssh.tip': "Laisse les deux vides dans la grande majorité des cas : Vagrant se connecte tout seul via sa clé SSH insérée automatiquement (utilisateur « vagrant »). Ne renseigne un mot de passe que si tu dois te logger en SSH avec un mot de passe classique plutôt qu'une clé.",
    'vm.root_pass': 'Mot de passe root (login console/GUI)',
    'vm.root_pass.tip': "Change le mot de passe du compte root au premier démarrage — utile pour te logger sur la console (fenêtre GUI) plutôt qu'en SSH. N'a aucun rapport avec la connexion SSH elle-même.",
    'vm.ports': 'Ports redirigés (VM → PC)',
    'vm.ports.tip': 'Rend un service de la VM accessible depuis ton PC. Ex. guest 80 → host 8080 : http://localhost:8080 ouvre le port 80 de la VM.',
    'vm.disques': 'Disques additionnels',
    'vm.disques.tip': "Ajoute un disque virtuel supplémentaire à la VM (en plus du disque système). Utile pour du stockage de données séparé. VirtualBox et libvirt uniquement.",
    'vm.provision': 'Provisioning — que faire au démarrage ?',
    'vm.provision.tip': "Ce qui s'exécute automatiquement au premier « vagrant up ». « script shell » pour des commandes directes (apt install…), « playbook Ansible » si tu pilotes la config avec Ansible, « rien » pour une VM vierge.",
    'vm.aide_cmd': 'Aide : insérer une commande toute prête',
    'vm.aide_cmd.tip': "Choisis une commande courante, elle s'ajoute au script ci-dessous. Tu peux en empiler plusieurs.",
    'vm.script': 'Script shell (lancé en root au 1er démarrage)',
    'vm.playbook': 'Chemin du playbook',
    'vm.playbook.tip': "Chemin du fichier .yml, relatif au dossier où tu lances « vagrant up » (là où se trouve le Vagrantfile). Ex. « provisioning/playbook.yml » si ton playbook est dans un sous-dossier provisioning/.",
  },

  en: {
    'nav.theme': 'Toggle light/dark theme',
    'nav.aide': 'How it works',
    'nav.topologie': 'Topology',
    'nav.aleatoire': 'Random lab',
    'nav.plus': 'More',
    'nav.partager': 'Share',
    'nav.inventaire': 'Ansible inventory',
    'nav.importer': 'Import',
    'nav.exporter': 'Export',
    'nav.installer': 'Install the app',
    'nav.telecharger': 'Download the project',
    'nav.lang': 'Français',

    'hero.titre1': 'Forge your VM labs',
    'hero.titre2': 'without writing a line of Ruby',
    'hero.sous': "Describe your machines in the form — VagrantForge writes the Vagrantfile, validated, commented and ready for vagrant up. Everything runs in your browser.",
    'hero.commencer': 'Get started',
    'hero.telecharger': 'Download the project',
    'feat.multivm.t': 'Multi-VM', 'feat.multivm.d': 'As many machines as you need',
    'feat.lang.t': 'Language & keyboard', 'feat.lang.d': 'Set on first boot',
    'feat.presets.t': 'Presets', 'feat.presets.d': 'Ready-to-use labs',
    'feat.valid.t': 'Live validation', 'feat.valid.d': 'Errors & warnings in real time',

    'tabs.config': 'Configuration', 'tabs.apercu': 'Preview',

    'g.titre': 'Global settings',
    'g.provider': 'Virtualization software (provider)',
    'g.provider.tip': "The software that runs the VMs on your machine. VirtualBox is free and the most common — pick it if unsure.",
    'g.provider.vb': 'VirtualBox — free, most common',
    'g.provider.vm': 'VMware Desktop — paid, fast',
    'g.provider.lv': 'libvirt (KVM/QEMU) — Linux',
    'g.boxcheck': 'Check for image updates on start',
    'g.boxcheck.tip': 'If checked, Vagrant checks for a newer image version on every "vagrant up". Unchecked = faster, reproducible boot.',
    'g.hostsfile': 'Name resolution between VMs (/etc/hosts)',
    'g.hostsfile.tip': 'If checked, every VM with an IP gets an /etc/hosts entry (or the Windows hosts file) for every other VM in the config — they can then reach each other by name (ping web, curl http://db) with no DNS server.',
    'g.subnet': 'Private network — address range',
    'g.subnet.tip': 'VMs talk to each other and to your PC on this isolated (host-only) network. Each VM gets an address here: .10, .11, .12…',
    'g.subnet.hint': "This is a <b>private</b> network between your PC and the VMs (nothing to do with the Internet). Each VM added gets the next address: 192.168.56.<b>10</b>, .<b>11</b>, .<b>12</b>…",

    'p.titre': 'Quick starts', 'p.vider': 'clear all',
    'v.titre': 'Virtual machines', 'v.ajouter': 'add a VM',

    'term.copier': 'copy', 'term.telecharger': 'download', 'term.copie': 'copied ✓', 'term.lien_copie': 'link copied ✓',

    'footer': 'Forged with <span class="grad"><i class="fa-solid fa-hammer"></i> VagrantForge</span> — describe, validate, <code>vagrant up</code>.',

    'modal.titre': 'How it works',
    'modal.intro': 'VagrantForge builds a <b>Vagrantfile</b>: the blueprint for your virtual machines. Fill in the form, the file generates itself on the right.',
    'modal.etapes': 'In 4 steps',
    'modal.etape1': 'Pick your <b>provider</b> (VirtualBox if unsure) in the global settings.',
    'modal.etape2': '<b>Add VMs</b>: their OS, RAM, network, language, what they install on boot.',
    'modal.etape3': 'The <b>Vagrantfile</b> appears on the right, syntax-highlighted and validated live.',
    'modal.etape4': '<b>Download it</b> into an empty folder, open a terminal there and run <code>vagrant up</code>. That\u2019s it.',
    'modal.vocab': 'Vocabulary',
    'modal.box.t': 'box (image)', 'modal.box.d': 'The starting disk of a VM (e.g. Debian 12). VagrantForge offers the real public images, by their full name.',
    'modal.provider.t': 'provider', 'modal.provider.d': 'The software that runs the VMs on your PC: VirtualBox, VMware, or libvirt.',
    'modal.ip.t': 'private IP (host-only)', 'modal.ip.d': 'The address to reach the VM from your PC, and for VMs to talk to each other, on an isolated network. E.g. <code>192.168.56.10</code>.',
    'modal.port.t': 'forwarded port', 'modal.port.d': 'Makes a VM service reachable from your PC: "guest 80 → host 8080" = <code>localhost:8080</code> opens port 80 of the VM.',
    'modal.prov.t': 'provisioning', 'modal.prov.d': 'Commands run automatically on first boot (install nginx, Docker…). Use the "insert a command" helper.',
    'modal.creds.t': 'SSH credentials/root password', 'modal.creds.d': 'Leave everything empty in most cases: Vagrant connects on its own using its own SSH key. Only fill in "SSH — password" or "root password" if you have a specific need (GUI login, a password required by an assignment).',
    'modal.pont.t': 'bridged network (public_network)', 'modal.pont.d': "Puts the VM directly on your real network (instead of the isolated private Vagrant network). Only enable it if you know why — otherwise leave it unchecked.",
    'modal.avant.titre': 'Before running <code>vagrant up</code>',
    'modal.avant.1': 'Install <b>Vagrant</b> and at least one provider (VirtualBox is the simplest). If you use the VagrantForge CLI, <code>forge doctor</code> checks all of this for you.',
    'modal.avant.2': 'Download the Vagrantfile into an <b>empty folder</b> dedicated to this lab (one folder = one lab).',
    'modal.avant.3': 'Check the <b>diagnostics</b> under the preview: ✗ (errors) prevent a clean generation, ⚠ (warnings) are worth reading but are often harmless for a throwaway lab.',
    'modal.astuce': '<b>Tip:</b> you can export your config as JSON ("Export" button) to save or share it, and re-import it later. The <b>"Download the project"</b> button gives you all the code (web + CLI + API) in one archive.',

    'topo.titre': 'Lab topology',
    'topo.intro': 'Network overview: VMs, private IPs, forwarded ports, and any public access.',
    'topo.copier': 'copy Mermaid code',
    'topo.telecharger': 'download (.mmd)',

    'vm.nom': 'VM name',
    'vm.os': 'Operating system (OS)',
    'vm.os.tip': 'The VM\u2019s starting image. Pick by name: "Debian 12" = the current stable release. Bento images also work under VMware.',
    'vm.version': 'Image version',
    'vm.version.tip': 'Leave "latest" for the newest. Pin a number for a lab that stays 100% reproducible over time. Format is specific to each box (e.g. 12.20240905.1 for Debian) — use the button to see the real published versions.',
    'vm.ram': 'Memory (RAM)',
    'vm.cpu': 'Processors (vCPU)',
    'vm.langue': 'VM language & keyboard',
    'vm.langue.tip': 'Sets the system language and keyboard layout on first boot (Debian/Ubuntu families). Handy for a non-US keyboard layout.',
    'vm.ip': 'Private IP (host-only network)',
    'vm.ip.tip': 'Fixed address to reach the VM from your PC and between VMs, on an isolated network. Leave empty for an automatic IP.',
    'vm.provider': 'VM-specific provider (else: global)',
    'vm.provider.tip': "Leave it on \"inherits from global\" unless you have a specific need (e.g. a single Windows VM that must run under VMware while the others use VirtualBox).",
    'vm.gui': 'Show the VM window (useful for debugging)',
    'vm.gui.tip': "Opens the VM's display window on boot (useful for a graphical install or debugging). Unchecked: the VM runs in the background, which is the normal case for a server.",
    'vm.pont': 'Bridged interface (public_network) — VM on your real network',
    'vm.pont.tip': "⚠️ Plugs the VM directly onto your local network (not just the private Vagrant network) — it becomes reachable from other devices on the network, and vice versa. Only enable this if you know why (e.g. a DHCP/PXE server, a VPN). Vagrant will ask which network interface to use on first boot.",
    'vm.dossier': 'Shared folder PC → /vagrant',
    'vm.dossier.tip': 'A folder from your PC visible inside the VM at /vagrant. Handy for editing code on your PC and running it in the VM.',
    'vm.dossier_off': 'Disable the shared folder (works around a recent VMware plugin bug)',
    'vm.winrm_user': 'WinRM — username', 'vm.winrm_pass': 'WinRM — password',
    'vm.winrm.tip': "Credentials to control the Windows VM remotely (no SSH on Windows). Leave empty to use the box's defaults (often vagrant/vagrant) — check the box's page on Vagrant Cloud if the connection fails.",
    'vm.admin_pass': 'Administrator password',
    'vm.admin_pass.tip': "Changes the local Administrator account password on first boot. Leave empty to keep the box's own password.",
    'vm.ssh_user': 'SSH — username', 'vm.ssh_pass': 'SSH — password',
    'vm.ssh.tip': "Leave both empty in the vast majority of cases: Vagrant connects on its own via its auto-inserted SSH key (\"vagrant\" user). Only set a password if you need to log in with a plain password instead of a key.",
    'vm.root_pass': 'Root password (console/GUI login)',
    'vm.root_pass.tip': "Changes the root account password on first boot — useful for logging in on the console (GUI window) rather than over SSH. Unrelated to the SSH connection itself.",
    'vm.ports': 'Forwarded ports (VM → PC)',
    'vm.ports.tip': 'Makes a VM service reachable from your PC. E.g. guest 80 → host 8080: http://localhost:8080 opens port 80 of the VM.',
    'vm.disques': 'Additional disks',
    'vm.disques.tip': 'Adds an extra virtual disk to the VM (besides the system disk). Useful for separate data storage. VirtualBox and libvirt only.',
    'vm.provision': 'Provisioning — what to do on boot?',
    'vm.provision.tip': "What runs automatically on the first \"vagrant up\". \"shell script\" for direct commands (apt install…), \"Ansible playbook\" if you drive the config with Ansible, \"nothing\" for a blank VM.",
    'vm.aide_cmd': 'Help: insert a ready-made command',
    'vm.aide_cmd.tip': 'Pick a common command, it gets appended to the script below. You can stack several.',
    'vm.script': 'Shell script (run as root on first boot)',
    'vm.playbook': 'Playbook path',
    'vm.playbook.tip': "Path to the .yml file, relative to the folder where you run \"vagrant up\" (where the Vagrantfile lives). E.g. \"provisioning/playbook.yml\" if your playbook sits in a provisioning/ subfolder.",
  },
};

const CLE_LANGUE = 'vagrantforge.lang';

function langueInitiale(){
  try{ const s = localStorage.getItem(CLE_LANGUE); if(s) return s; }catch(e){}
  return (navigator.language || 'fr').toLowerCase().startsWith('en') ? 'en' : 'fr';
}

let LANGUE_COURANTE = langueInitiale();

function t(cle){
  const dico = I18N[LANGUE_COURANTE] || I18N.fr;
  return (dico[cle] !== undefined ? dico[cle] : (I18N.fr[cle] !== undefined ? I18N.fr[cle] : cle));
}

/* Applique la langue courante à tous les éléments statiques marqués
 * data-i18n / data-i18n-title / data-i18n-placeholder dans le DOM. */
function appliquerI18nStatique(racine){
  const scope = racine || document;
  scope.querySelectorAll('[data-i18n]').forEach(el=>{
    const html = t(el.getAttribute('data-i18n'));
    el.innerHTML = html;
  });
  scope.querySelectorAll('[data-i18n-title]').forEach(el=>{
    el.setAttribute('title', t(el.getAttribute('data-i18n-title')));
  });
  scope.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{
    el.setAttribute('placeholder', t(el.getAttribute('data-i18n-placeholder')));
  });
  scope.querySelectorAll('[data-i18n-aria]').forEach(el=>{
    el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria')));
  });
  document.documentElement.lang = LANGUE_COURANTE;
}

function basculerLangue(){
  LANGUE_COURANTE = LANGUE_COURANTE === 'fr' ? 'en' : 'fr';
  try{ localStorage.setItem(CLE_LANGUE, LANGUE_COURANTE); }catch(e){}
  appliquerI18nStatique();
  const btn = document.getElementById('lang-btn');
  if(btn) btn.textContent = t('nav.lang');
  const btnMobile = document.getElementById('lang-btn-mobile');
  if(btnMobile) btnMobile.textContent = t('nav.lang');
  if(typeof rendre === 'function') rendre();
}
