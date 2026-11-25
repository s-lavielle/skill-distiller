"""Tests de la CLI skill-distiller (python3 -m unittest discover -s tests).

Pourquoi cette suite : elle protège les trois gestes du workflow outillé —
init (pré-remplissage des artefacts et gitignore du projet cible), check
(traçabilité : la valeur du produit est qu'aucun point ne part sans source),
diff (réintégration : comparer la copie figée à la source actuelle) et new
(ossature dérivée de la synthèse). Un contournement silencieux de ces
contrôles détruirait l'« auditable » du sous-titre du produit.
"""

import http.server
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

BIN = str(Path(__file__).resolve().parent.parent / "bin" / "skill-distiller")

FICHE_MONO = """sources:
  - ref: source-a
    langue: anglais
    points_a_retenir:
      - un point
    ignorer:
      - rien
langue_cible: français
"""

FICHE_MULTI = """sources:
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
"""

BRUTE_TRACEE = """# Synthèse brute — test

> Chaque point est tracé par [A] (source-a).

## 1. Règle une

### 1.1 Découpage [A]

Contenu.

### 1.2 Taille [A]

Contenu.
"""

AMENDEMENTS_OK = """# Amendements

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
"""

FINAL_REMPLI = """---
name: skill-test
description: Un skill de test.
---

# Skill test
"""


def fiche_figee(ref):
    """Fiche avec une source figée (snapshot) pointant vers <ref>."""
    return f"""sources:
  - ref: {ref}
    langue: anglais
    snapshot: sources/src-a/
    date_fige: 2026-01-01
    points_a_retenir:
      - un point
    ignorer:
      - rien
langue_cible: français
"""


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="skill-distiller-"))
        self.addCleanup(shutil.rmtree, self.dir, True)

    # helpers ---------------------------------------------------------

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, BIN, *args],
            cwd=self.dir, capture_output=True, text=True, timeout=30,
        )

    def write(self, name, content):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def lot_fige(self, fichier, contenu):
        """Lot minimal pour diff : copie figée sources/src-a/<fichier>."""
        self.write(f"threads/test/sources/src-a/{fichier}", contenu)

    def lot_valide(self):
        self.write("threads/test/00-fiche-sources.yaml", FICHE_MONO)
        self.write("threads/test/01-synthese-brute.md", BRUTE_TRACEE)
        self.write("threads/test/04-amendements.md", AMENDEMENTS_OK)
        self.write("threads/test/05-skill-final.md", FINAL_REMPLI)

    # init ------------------------------------------------------------

    def test_init_cree_artefacts_et_ignore_repertoire(self):
        r = self.run_cli("init", "mon-sujet")
        self.assertEqual(r.returncode, 0, r.stderr)
        for name in ("00-fiche-sources.yaml", "02-reconciliation.md",
                     "04-amendements.md", "05-skill-final.md"):
            self.assertTrue((self.dir / "threads" / "mon-sujet" / name).exists(),
                            f"manquant : {name}")
        # Mémoire du lot : répertoire des copies figées (réintégration).
        self.assertTrue((self.dir / "threads" / "mon-sujet" / "sources").is_dir())
        self.assertRegex((self.dir / ".gitignore").read_text(),
                         re.compile(r"^threads/$", re.M))
        # Le sujet est reporté dans les titres des gabarits.
        reconciliation = (self.dir / "threads" / "mon-sujet" / "02-reconciliation.md")
        self.assertIn("Réconciliation — mon-sujet", reconciliation.read_text())

    def test_init_racine_surchargeable(self):
        r = self.run_cli("init", "mon-sujet", "--dir", "atelier")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.dir / "atelier" / "mon-sujet" / "00-fiche-sources.yaml").exists())
        self.assertRegex((self.dir / ".gitignore").read_text(),
                         re.compile(r"^atelier/$", re.M))

    def test_init_refuse_lot_rempli(self):
        self.run_cli("init", "mon-sujet")
        r = self.run_cli("init", "mon-sujet")
        self.assertEqual(r.returncode, 2)
        self.assertIn("déjà rempli", r.stderr)

    # check -----------------------------------------------------------

    def test_check_passe_sur_lot_complet_et_trace(self):
        self.lot_valide()
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("0 erreur", r.stdout)

    def test_check_signale_point_non_trace(self):
        self.lot_valide()
        self.write("threads/test/01-synthese-brute.md",
                   BRUTE_TRACEE.replace("### 1.2 Taille [A]", "### 1.2 Taille"))
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("point non tracé — « 1.2 Taille »", r.stdout)

    def test_check_exige_reconciliation_si_sources_multiples(self):
        self.lot_valide()
        self.write("threads/test/00-fiche-sources.yaml", FICHE_MULTI)
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("02-reconciliation.md manquant", r.stdout)
        self.assertIn("03-synthese-reconciliee.md manquant", r.stdout)

    def test_check_signale_champ_amendement_absent(self):
        self.lot_valide()
        self.write("threads/test/04-amendements.md",
                   AMENDEMENTS_OK.replace("- Conséquence : ce que ça change\n", ""))
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("champ Conséquence absent ou à remplir", r.stdout)

    def test_check_signale_skill_final_au_gabarit(self):
        self.lot_valide()
        self.write("threads/test/05-skill-final.md",
                   "---\nname: <nom-du-skill>\ndescription: <à compléter>\n---\n")
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 1)
        self.assertIn("name absent ou gabarit", r.stdout)

    def test_check_signale_source_sans_copie_figee(self):
        self.lot_valide()  # FICHE_MONO ne porte pas de snapshot
        r = self.run_cli("check", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("sans copie figée", r.stdout)

    # new -------------------------------------------------------------

    def test_new_genere_ossature_depuis_synthese_et_fiche(self):
        self.lot_valide()
        self.write("threads/test/05-skill-final.md",
                   "---\nname: <nom-du-skill>\ndescription: <x>\n---\n")
        r = self.run_cli("new", "test")
        self.assertEqual(r.returncode, 0, r.stderr)
        final = (self.dir / "threads" / "test" / "05-skill-final.md").read_text()
        self.assertRegex(final, re.compile(r"^name: test$", re.M))
        self.assertIn("1. Découpage —", final)
        self.assertIn("2. Taille —", final)
        self.assertIn("- source-a", final)

    def test_new_refuse_ecraser_sans_force(self):
        self.lot_valide()
        r = self.run_cli("new", "test")
        self.assertEqual(r.returncode, 2)
        self.assertIn("--force", r.stderr)
        r2 = self.run_cli("new", "test", "--force")
        self.assertEqual(r2.returncode, 0, r2.stderr)

    # diff ------------------------------------------------------------

    def test_diff_source_identique(self):
        self.lot_fige("SKILL.md", "contenu\n")
        self.write("source-live/SKILL.md", "contenu\n")
        self.write("threads/test/00-fiche-sources.yaml",
                   fiche_figee(str(self.dir / "source-live")))
        r = self.run_cli("diff", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("identique", r.stdout)

    def test_diff_detecte_changements_et_produit_patch(self):
        self.lot_fige("SKILL.md", "ligne une\nligne deux\n")
        self.write("source-live/SKILL.md", "ligne une\nligne deux modifiée\n")
        self.write("source-live/NOUVEAU.md", "ajouté\n")
        self.write("threads/test/00-fiche-sources.yaml",
                   fiche_figee(str(self.dir / "source-live")))
        r = self.run_cli("diff", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("modifié (1 modifié(s), 1 nouveau(x))", r.stdout)
        cycles = list((self.dir / "threads" / "test" / "reintegrations").iterdir())
        self.assertEqual(len(cycles), 1)
        cycle = cycles[0]
        self.assertTrue((cycle / "01-etat-des-sources.md").exists())
        patch = (cycle / "diff-src-a.patch").read_text()
        self.assertIn("-ligne deux\n+ligne deux modifiée", patch)
        self.assertIn("NOUVEAU.md", (cycle / "01-etat-des-sources.md").read_text())

    def test_diff_non_resoluble_puis_sources_actuelles(self):
        self.lot_fige("SKILL.md", "v1\n")
        self.write("threads/test/00-fiche-sources.yaml",
                   fiche_figee("mattpocock/skills — to-tickets (via mhrsdev)"))
        r = self.run_cli("diff", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("à rafraîchir", r.stdout)

        # L'agent dépose le contenu actuel, puis relance.
        self.write("threads/test/sources-actuelles/src-a/SKILL.md", "v2\n")
        r2 = self.run_cli("diff", "test")
        self.assertEqual(r2.returncode, 0, r2.stdout + r2.stderr)
        self.assertIn("modifié (1 modifié(s))", r2.stdout)

    def test_diff_fetch_compare_source_http(self):
        self.lot_fige("contenu.txt", "v1\n")

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"v2\n"
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_address[1]}/skill.txt"
        self.write("threads/test/00-fiche-sources.yaml", fiche_figee(url))
        r = self.run_cli("diff", "test", "--fetch")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("modifié (1 modifié(s))", r.stdout)

    def test_diff_signale_source_non_figee(self):
        self.write("threads/test/00-fiche-sources.yaml", FICHE_MONO)
        r = self.run_cli("diff", "test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("non figée", r.stdout)


if __name__ == "__main__":
    unittest.main()
