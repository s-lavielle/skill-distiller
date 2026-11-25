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
const { spawnSync } = require('node:child_process');
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
