'use strict';

// Tests de la CLI skill-distiller (`node --test tests/`).
//
// Pourquoi cette suite : elle protège les trois gestes du workflow outillé —
// init (pré-remplissage des artefacts et gitignore du projet cible), check
// (traçabilité : la valeur du produit est qu'aucun point ne part sans source),
// new (ossature dérivée de la synthèse). Un contournement silencieux de ces
// contrôles détruirait l'« auditable » du sous-titre du produit.

const { test } = require('node:test');
const assert = require('node:assert');
const { spawnSync, spawn } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const BIN = path.resolve(__dirname, '..', 'bin', 'skill-distiller');

function tmpProject(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'skill-distiller-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  return dir;
}

function run(cwd, args) {
  return spawnSync(process.execPath, [BIN, ...args], { cwd, encoding: 'utf8' });
}

// Version asynchrone : indispensable quand le test héberge lui-même un
// serveur — spawnSync bloquerait la boucle d'événements du test et le
// serveur ne pourrait jamais répondre au CLI (deadlock).
function runAsync(cwd, args) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [BIN, ...args], { cwd });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => (stdout += d));
    child.stderr.on('data', (d) => (stderr += d));
    child.on('close', (status) => resolve({ status, stdout, stderr }));
  });
}

function write(cwd, name, content) {
  const file = path.join(cwd, name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
}

const FICHE_MONO = `sources:
  - ref: source-a
    langue: anglais
    points_a_retenir:
      - un point
    ignorer:
      - rien
langue_cible: français
`;

const FICHE_MULTI = `sources:
  - ref: source-a
    langue: anglais
    points_a_retenir:
      - un point
    ignorer:
      - rien
  - ref: source-b
    langue: anglais
    points_a_retenir:
      - un autre point
    ignorer:
      - rien
langue_cible: français
`;

const BRUTE_TRACEE = `# Synthèse brute — test

> Chaque point est tracé par [A] (source-a).

## 1. Règle une

### 1.1 Découpage [A]

Contenu.

### 1.2 Taille [A]

Contenu.
`;

const AMENDEMENTS_OK = `# Amendements

## Ajouts

### A1 — Un ajout

Texte libre.

## Amendements

### A2 — Une modification

- Cible : une section
- Contenu : le changement
- Conséquence : ce que ça change

## Cadre

- Langue cible : français
`;

const FINAL_REMPLI = `---
name: skill-test
description: Un skill de test.
---

# Skill test
`;

// Fiche avec une source figée (snapshot) pointant vers <ref>.
const ficheFigee = (ref) => `sources:
  - ref: ${ref}
    langue: anglais
    snapshot: sources/src-a/
    date_fige: 2026-01-01
    points_a_retenir:
      - un point
    ignorer:
      - rien
langue_cible: français
`;

// Lot minimal pour diff : copie figée sources/src-a/<fichier>.
function lotFige(cwd, fichier, contenu) {
  write(cwd, `threads/test/sources/src-a/${fichier}`, contenu);
}

function lotValide(cwd) {
  write(cwd, 'threads/test/00-fiche-sources.yaml', FICHE_MONO);
  write(cwd, 'threads/test/01-synthese-brute.md', BRUTE_TRACEE);
  write(cwd, 'threads/test/04-amendements.md', AMENDEMENTS_OK);
  write(cwd, 'threads/test/05-skill-final.md', FINAL_REMPLI);
}

// ---------------------------------------------------------------- init

test('init crée les artefacts et ignore le répertoire de travail', (t) => {
  const cwd = tmpProject(t);
  const r = run(cwd, ['init', 'mon-sujet']);
  assert.strictEqual(r.status, 0, r.stderr);
  for (const f of ['00-fiche-sources.yaml', '02-reconciliation.md', '04-amendements.md', '05-skill-final.md']) {
    assert.ok(fs.existsSync(path.join(cwd, 'threads', 'mon-sujet', f)), `manquant : ${f}`);
  }
  // Mémoire du lot : répertoire des copies figées (réintégration).
  assert.ok(fs.existsSync(path.join(cwd, 'threads', 'mon-sujet', 'sources')));
  assert.match(fs.readFileSync(path.join(cwd, '.gitignore'), 'utf8'), /^threads\/$/m);
  // Le sujet est reporté dans les titres des gabarits.
  const reconciliation = fs.readFileSync(path.join(cwd, 'threads', 'mon-sujet', '02-reconciliation.md'), 'utf8');
  assert.match(reconciliation, /Réconciliation — mon-sujet/);
});

test('init accepte une racine surchargeable (--dir) et la gitignore', (t) => {
  const cwd = tmpProject(t);
  const r = run(cwd, ['init', 'mon-sujet', '--dir', 'atelier']);
  assert.strictEqual(r.status, 0, r.stderr);
  assert.ok(fs.existsSync(path.join(cwd, 'atelier', 'mon-sujet', '00-fiche-sources.yaml')));
  assert.match(fs.readFileSync(path.join(cwd, '.gitignore'), 'utf8'), /^atelier\/$/m);
});

test('init refuse un lot déjà rempli', (t) => {
  const cwd = tmpProject(t);
  run(cwd, ['init', 'mon-sujet']);
  const r = run(cwd, ['init', 'mon-sujet']);
  assert.strictEqual(r.status, 2);
  assert.match(r.stderr, /déjà rempli/);
});

// ---------------------------------------------------------------- check

test('check passe sur un lot complet et tracé', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /0 erreur/);
});

test('check signale un point non tracé à sa source', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  write(cwd, 'threads/test/01-synthese-brute.md', BRUTE_TRACEE.replace('### 1.2 Taille [A]', '### 1.2 Taille'));
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 1);
  assert.match(r.stdout, /point non tracé — « 1\.2 Taille »/);
});

test('check exige la réconciliation quand la fiche porte plusieurs sources', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  write(cwd, 'threads/test/00-fiche-sources.yaml', FICHE_MULTI);
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 1);
  assert.match(r.stdout, /02-reconciliation\.md manquant/);
  assert.match(r.stdout, /03-synthese-reconciliee\.md manquant/);
});

test('check signale un champ d\'amendement absent', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  write(cwd, 'threads/test/04-amendements.md', AMENDEMENTS_OK.replace('- Conséquence : ce que ça change\n', ''));
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 1);
  assert.match(r.stdout, /champ Conséquence absent ou à remplir/);
});

test('check signale un skill final laissé au gabarit', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  write(cwd, 'threads/test/05-skill-final.md', '---\nname: <nom-du-skill>\ndescription: <à compléter>\n---\n');
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 1);
  assert.match(r.stdout, /name absent ou gabarit/);
});

// ---------------------------------------------------------------- new

test('new génère l\'ossature depuis la synthèse et la fiche', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  write(cwd, 'threads/test/05-skill-final.md', '---\nname: <nom-du-skill>\ndescription: <x>\n---\n');
  const r = run(cwd, ['new', 'test']);
  assert.strictEqual(r.status, 0, r.stderr);
  const final = fs.readFileSync(path.join(cwd, 'threads', 'test', '05-skill-final.md'), 'utf8');
  assert.match(final, /^name: test$/m);
  assert.match(final, /1\. Découpage —/);
  assert.match(final, /2\. Taille —/);
  assert.match(final, /- source-a/);
});

test('new refuse d\'écraser un skill final rempli, sauf --force', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd);
  const r = run(cwd, ['new', 'test']);
  assert.strictEqual(r.status, 2);
  assert.match(r.stderr, /--force/);
  const r2 = run(cwd, ['new', 'test', '--force']);
  assert.strictEqual(r2.status, 0, r2.stderr);
});

// ---------------------------------------------------------------- diff

test('check signale une source sans copie figée (avertissement)', (t) => {
  const cwd = tmpProject(t);
  lotValide(cwd); // FICHE_MONO ne porte pas de snapshot
  const r = run(cwd, ['check', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /sans copie figée/);
});

test('diff signale une source identique', (t) => {
  const cwd = tmpProject(t);
  lotFige(cwd, 'SKILL.md', 'contenu\n');
  const src = path.join(cwd, 'source-live');
  write(cwd, 'source-live/SKILL.md', 'contenu\n');
  write(cwd, 'threads/test/00-fiche-sources.yaml', ficheFigee(src));
  const r = run(cwd, ['diff', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /identique/);
});

test('diff détecte les changements et produit un patch', (t) => {
  const cwd = tmpProject(t);
  lotFige(cwd, 'SKILL.md', 'ligne une\nligne deux\n');
  write(cwd, 'source-live/SKILL.md', 'ligne une\nligne deux modifiée\n');
  write(cwd, 'source-live/NOUVEAU.md', 'ajouté\n');
  const src = path.join(cwd, 'source-live');
  write(cwd, 'threads/test/00-fiche-sources.yaml', ficheFigee(src));
  const r = run(cwd, ['diff', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /modifié \(1 modifié\(s\), 1 nouveau\(x\)\)/);
  const cycles = fs.readdirSync(path.join(cwd, 'threads', 'test', 'reintegrations'));
  assert.strictEqual(cycles.length, 1);
  const cycle = path.join(cwd, 'threads', 'test', 'reintegrations', cycles[0]);
  assert.ok(fs.existsSync(path.join(cycle, '01-etat-des-sources.md')));
  const patch = fs.readFileSync(path.join(cycle, 'diff-src-a.patch'), 'utf8');
  assert.match(patch, /-ligne deux\n\+ligne deux modifiée/);
  assert.match(fs.readFileSync(path.join(cycle, '01-etat-des-sources.md'), 'utf8'), /NOUVEAU\.md/);
});

test('diff signale une source non résoluble, puis la compare via sources-actuelles', (t) => {
  const cwd = tmpProject(t);
  lotFige(cwd, 'SKILL.md', 'v1\n');
  write(cwd, 'threads/test/00-fiche-sources.yaml', ficheFigee('mattpocock/skills — to-tickets (via mhrsdev)'));
  const r = run(cwd, ['diff', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /à rafraîchir/);

  // L'agent dépose le contenu actuel, puis relance.
  write(cwd, 'threads/test/sources-actuelles/src-a/SKILL.md', 'v2\n');
  const r2 = run(cwd, ['diff', 'test']);
  assert.strictEqual(r2.status, 0, r2.stdout + r2.stderr);
  assert.match(r2.stdout, /modifié \(1 modifié\(s\)\)/);
});

test('diff --fetch compare une source http', async (t) => {
  const cwd = tmpProject(t);
  lotFige(cwd, 'contenu.txt', 'v1\n');
  const server = require('node:http').createServer((req, res) => {
    res.end('v2\n');
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  t.after(() => {
    server.closeAllConnections();
    server.close();
  });
  const url = `http://127.0.0.1:${server.address().port}/skill.txt`;
  write(cwd, 'threads/test/00-fiche-sources.yaml', ficheFigee(url));
  const r = await runAsync(cwd, ['diff', 'test', '--fetch']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /modifié \(1 modifié\(s\)\)/);
});

test('diff signale une source non figée', (t) => {
  const cwd = tmpProject(t);
  write(cwd, 'threads/test/00-fiche-sources.yaml', FICHE_MONO);
  const r = run(cwd, ['diff', 'test']);
  assert.strictEqual(r.status, 0, r.stdout + r.stderr);
  assert.match(r.stdout, /non figée/);
});
