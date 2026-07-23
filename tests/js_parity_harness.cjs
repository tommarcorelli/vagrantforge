/* VagrantForge — harnais de parité JS <-> Python.
 *
 * Charge web/frontend/js/{donnees,generateur}.js dans un contexte Node (via
 * le module `vm`), sans navigateur ni DOM : ces fichiers sont déjà
 * indépendants du DOM, donc aucun shim n'est nécessaire.
 *
 * Lit une config JSON sur stdin, appelle les 4 fonctions de génération
 * miroir du cœur Python, et écrit le résultat en JSON sur stdout :
 *   { vagrantfile, inventaire_ini, inventaire_yaml, topologie }
 *
 * Utilisé par tests/test_parite_js.py pour détecter toute divergence entre
 * le moteur Python (core/) et son miroir JS (web/frontend/js/), la « règle
 * d'or » du projet n'étant pas auto-vérifiée autrement.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const jsDir = path.join(__dirname, '..', 'web', 'frontend', 'js');
const contexte = { console };
vm.createContext(contexte);

for (const fichier of ['donnees.js', 'generateur.js']) {
  const code = fs.readFileSync(path.join(jsDir, fichier), 'utf8');
  vm.runInContext(code, contexte, { filename: fichier });
}

let entree = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { entree += chunk; });
process.stdin.on('end', () => {
  let cfg;
  try {
    cfg = JSON.parse(entree);
  } catch (e) {
    process.stderr.write('JSON invalide sur stdin : ' + e.message + '\n');
    process.exit(2);
  }
  try {
    const resultat = {
      vagrantfile: contexte.buildVagrantfile(cfg),
      inventaire_ini: contexte.buildAnsibleInventory(cfg),
      inventaire_yaml: contexte.buildAnsibleInventoryYaml(cfg),
      topologie: contexte.buildTopologyMermaid(cfg),
    };
    process.stdout.write(JSON.stringify(resultat));
  } catch (e) {
    process.stderr.write('Erreur pendant la génération JS : ' + (e.stack || e.message) + '\n');
    process.exit(1);
  }
});
