"""Tests de la façade MCP (python3 -m unittest discover -s tests).

Pourquoi cette suite : elle protège le contrat vu par les agents — le
handshake (un client doit pouvoir se brancher), le skill servi avec ses
digests SHA-256 (c'est ce qui rend le workflow distribuable et vérifiable
— l'« auditable » du produit s'y joue), les outils de contenu du lot
(mode « pur MCP » : l'agent rend des résultats étiquetés, l'outil range)
et le confinement des appels : paramètres validés, aucun échappement de
chemin. Le test test_lot_entier_rendu_puis_check_vert est l'acceptation
du mode « pur MCP » : un lot complet rendu par les outils doit passer le
contrôle de traçabilité. Une régression ici rendrait l'outil inutilisable
— ou dangereux — depuis un contexte agentique.
"""

import http.server
import importlib.machinery
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = str(ROOT / "bin" / "skill-distiller")
sys.path.insert(0, str(ROOT / "src"))

import mcp_server  # noqa: E402  (chemin ajouté ci-dessus)

SKILL_URI = "skill://skill-distiller/SKILL.md"

# Fixtures d'un lot minimal valide (source unique, points tracés) — le
# test clé du « pur MCP » les rend entièrement par les outils de contenu.
FICHE = """sources:
  - ref: src-a
    langue: anglais
    snapshot: sources/src-a/
    date_fige: 2026-11-26
    points_a_retenir:
      - un point
    ignorer:
      - rien
langue_cible: français
"""

BRUTE = """# Synthèse brute — test

## 1. Règle une [A]

Contenu.
"""

AMENDEMENTS = """# Amendements

## Ajouts

Rien.

## Amendements

Aucune.

## Cadre

Français.
"""

FINAL = """---
name: skill-test
description: Un skill de test pour la suite MCP.
---

# Skill test

Contenu.
"""


class StdioClient:
    """Client MCP minimal sur tubes stdio — le vrai point d'entrée CLI."""

    def __init__(self):
        self.proc = subprocess.Popen(
            [sys.executable, BIN, "mcp"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        self.next_id = 0

    def request(self, method, params=None):
        self.next_id += 1
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "id": self.next_id,
             "method": method, "params": params or {}}) + "\n")
        self.proc.stdin.flush()
        line = self.proc.stdout.readline()
        if not line:
            raise AssertionError(
                f"aucune réponse pour {method} "
                f"(stderr : {self.proc.stderr.read()})")
        response = json.loads(line)
        if response.get("id") != self.next_id:
            raise AssertionError(f"identifiant de réponse inattendu : {response}")
        return response

    def notify(self, method):
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def close(self):
        for stream in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if stream:
                stream.close()
        self.proc.kill()
        self.proc.wait()


class McpStdioTestCase(unittest.TestCase):
    def setUp(self):
        self.client = StdioClient()
        self.addCleanup(self.client.close)
        self.dir = Path(tempfile.mkdtemp(prefix="skill-distiller-mcp-"))
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.client.request("initialize", {"protocolVersion": "2026-07-28"})
        self.client.notify("notifications/initialized")

    def call_tool(self, name, arguments):
        response = self.client.request(
            "tools/call", {"name": name, "arguments": arguments})
        return response["result"]

    def init_lot(self, sujet="mon-sujet"):
        return self.call_tool(
            "skill_distiller_init", {"sujet": sujet, "project": str(self.dir)})

    def lot_write(self, ref, content, sujet="mon-sujet"):
        return self.call_tool(
            "skill_distiller_write",
            {"sujet": sujet, "project": str(self.dir),
             "ref": ref, "content": content})

    # handshake -------------------------------------------------------

    def test_initialize_negocie_le_protocole_et_declare_le_skill(self):
        response = self.client.request(
            "initialize", {"protocolVersion": "2026-07-28"})
        result = response["result"]
        self.assertEqual(result["protocolVersion"], "2026-07-28")
        self.assertEqual(result["serverInfo"]["name"], "skill-distiller")
        extensions = result["capabilities"]["extensions"]
        self.assertTrue(
            extensions["io.modelcontextprotocol/skills"]["directoryRead"])
        self.assertIn("resources", result["capabilities"])

    def test_initialize_version_inconnue_retombe_sur_la_version_du_serveur(self):
        client = StdioClient()
        self.addCleanup(client.close)
        response = client.request("initialize", {"protocolVersion": "1900-01-01"})
        self.assertEqual(response["result"]["protocolVersion"], "2026-07-28")

    def test_notification_ne_produit_pas_de_reponse(self):
        self.client.notify("notifications/initialized")
        response = self.client.request("ping")
        self.assertEqual(response["result"], {})

    def test_methode_inconnue_est_refusee(self):
        response = self.client.request("invented/method")
        self.assertEqual(response["error"]["code"], -32601)

    # outils ----------------------------------------------------------

    def test_tools_list_expose_commandes_et_contenu_du_lot(self):
        response = self.client.request("tools/list")
        tools = {t["name"]: t for t in response["result"]["tools"]}
        self.assertEqual(set(tools), {
            "skill_distiller_init", "skill_distiller_check",
            "skill_distiller_diff", "skill_distiller_new",
            "skill_distiller_state", "skill_distiller_read",
            "skill_distiller_write"})
        for tool in tools.values():
            self.assertIn("sujet", tool["inputSchema"]["properties"])

    def test_tools_call_init_puis_check_sur_le_projet_cible(self):
        result = self.call_tool(
            "skill_distiller_init", {"sujet": "mon-sujet", "project": str(self.dir)})
        self.assertFalse(result["isError"])
        self.assertIn("Lot prêt", result["content"][0]["text"])
        self.assertTrue(
            (self.dir / "threads/mon-sujet/00-fiche-sources.yaml").exists())

        result = self.call_tool(
            "skill_distiller_check", {"sujet": "mon-sujet", "project": str(self.dir)})
        self.assertTrue(result["isError"])  # lot au gabarit : erreurs attendues
        self.assertIn("erreur(s)", result["content"][0]["text"])

    def test_tools_call_refuse_sujet_et_projet_invalides(self):
        result = self.call_tool(
            "skill_distiller_init", {"sujet": "../escape", "project": str(self.dir)})
        self.assertTrue(result["isError"])
        self.assertIn("sujet", result["content"][0]["text"])

        result = self.call_tool(
            "skill_distiller_init",
            {"sujet": "ok", "project": str(self.dir / "inexistant")})
        self.assertTrue(result["isError"])
        self.assertIn("introuvable", result["content"][0]["text"])

        response = self.client.request(
            "tools/call", {"name": "outil-inconnu", "arguments": {}})
        self.assertEqual(response["error"]["code"], -32602)

    # contenu du lot ---------------------------------------------------

    def test_lot_write_range_au_bon_endroit_et_read_le_rend(self):
        self.init_lot()
        content = "ma fiche\n"
        result = self.lot_write("fiche", content)
        self.assertFalse(result["isError"])
        self.assertEqual(
            (self.dir / "threads/mon-sujet/00-fiche-sources.yaml").read_text(
                encoding="utf-8"),
            content)

        result = self.call_tool(
            "skill_distiller_read",
            {"sujet": "mon-sujet", "project": str(self.dir), "ref": "fiche"})
        self.assertEqual(result["content"][0]["text"], content)

        # Sources et cycles : l'agent étiquette, l'outil organise.
        self.assertFalse(self.lot_write("source:src-a/texte.md", "une source\n")["isError"])
        self.assertTrue(
            (self.dir / "threads/mon-sujet/sources/src-a/texte.md").exists())
        self.assertFalse(self.lot_write(
            "cycle:2026-01-02-1530:synthese-nouveautes", "nouveautés\n")["isError"])
        self.assertTrue((self.dir / "threads/mon-sujet/reintegrations/"
                         "2026-01-02-1530/02-synthese-nouveautes.md").exists())

    def test_lot_state_inventorie_le_lot(self):
        self.init_lot()
        self.lot_write("fiche", FICHE)
        result = self.call_tool(
            "skill_distiller_state",
            {"sujet": "mon-sujet", "project": str(self.dir)})
        text = result["content"][0]["text"]
        self.assertIn("00-fiche-sources.yaml (fiche", text)
        self.assertIn("01-synthese-brute.md (synthese-brute, absent)", text)
        self.assertIn("Sources figées : —", text)

    def test_lot_refuse_references_inconnues_et_echappements(self):
        self.init_lot()
        for ref in ("inconnu", "source:../x/f.md", "source:src-a/../../etc/passwd",
                    "cycle:2026-01-01:machin", "/etc/passwd", "fiche/../../../etc"):
            result = self.lot_write(ref, "x")
            self.assertTrue(result["isError"], ref)

        # Le lot doit exister avant toute consultation ou tout dépôt.
        result = self.call_tool(
            "skill_distiller_read",
            {"sujet": "absent", "project": str(self.dir), "ref": "fiche"})
        self.assertTrue(result["isError"])

    def test_lot_entier_rendu_puis_check_vert(self):
        """Acceptation du « pur MCP » : un lot complet est rendu par les
        outils de contenu — jamais d'écriture côté agent — et le contrôle
        de traçabilité passe au vert."""
        self.init_lot()
        for ref, content in (
            ("fiche", FICHE),
            ("source:src-a/texte.md", "Le texte de la source A.\n"),
            ("synthese-brute", BRUTE),
            ("amendements", AMENDEMENTS),
            ("skill-final", FINAL),
        ):
            result = self.lot_write(ref, content)
            self.assertFalse(result["isError"], ref)
        result = self.call_tool(
            "skill_distiller_check",
            {"sujet": "mon-sujet", "project": str(self.dir)})
        self.assertFalse(result["isError"])
        self.assertIn("0 erreur(s)", result["content"][0]["text"])

    # skill -----------------------------------------------------------

    def test_skills_list_publie_le_manifeste_avec_digests(self):
        response = self.client.request("skills/list")
        skills = response["result"]["skills"]
        self.assertEqual(len(skills), 1)
        entry = skills[0]
        self.assertEqual(entry["uri"], SKILL_URI)
        self.assertEqual(entry["frontmatter"]["name"], "skill-distiller")
        self.assertTrue(entry["frontmatter"]["description"])

        uris = {r["uri"]: r for r in entry["resources"]}
        self.assertIn(SKILL_URI, uris)
        self.assertIn("skill://skill-distiller/templates/fiche-sources.yaml", uris)

        raw = (ROOT / "SKILL.md").read_bytes()
        self.assertEqual(uris[SKILL_URI]["size"], len(raw))
        self.assertEqual(
            uris[SKILL_URI]["digest"],
            "sha256:" + __import__("hashlib").sha256(raw).hexdigest())

    def test_skills_get_renvoie_le_meme_entry_et_refuse_l_inconnu(self):
        response = self.client.request("skills/get", {"uri": SKILL_URI})
        self.assertEqual(response["result"]["skill"]["uri"], SKILL_URI)

        response = self.client.request(
            "skills/get", {"uri": "skill://skill-distiller/absent.md"})
        self.assertEqual(response["error"]["code"], -32602)

    def test_resources_read_sert_le_skill_et_confine_les_chemins(self):
        response = self.client.request("resources/read", {"uri": SKILL_URI})
        content = response["result"]["contents"][0]
        self.assertEqual(content["mimeType"], "text/markdown")
        self.assertTrue(content["text"].startswith("---"))

        response = self.client.request(
            "resources/read", {"uri": "skill://skill-distiller/templates/amendements.md"})
        self.assertIn("Amendements", response["result"]["contents"][0]["text"])

        for uri in (
            "skill://skill-distiller/templates/../../../etc/passwd",
            "skill://skill-distiller/inconnu.md",
            "file:///etc/passwd",
        ):
            response = self.client.request("resources/read", {"uri": uri})
            self.assertEqual(response["error"]["code"], -32602, uri)

    def test_resources_directory_read_liste_les_enfants(self):
        response = self.client.request(
            "resources/directory/read", {"uri": "skill://skill-distiller/templates"})
        names = [r["name"] for r in response["result"]["resources"]]
        self.assertIn("fiche-sources.yaml", names)
        self.assertIn("skill-final.md", names)

        response = self.client.request(
            "resources/directory/read", {"uri": "skill://skill-distiller"})
        children = {r["name"]: r["mimeType"] for r in response["result"]["resources"]}
        self.assertEqual(children.get("templates"), "inode/directory")

        # Un fichier n'est pas un répertoire.
        response = self.client.request(
            "resources/directory/read", {"uri": SKILL_URI})
        self.assertEqual(response["error"]["code"], -32602)


class McpHttpTestCase(unittest.TestCase):
    """Transport HTTP : même protocole, avec session légère."""

    def setUp(self):
        self.server = mcp_server.McpHttpServer(
            ("127.0.0.1", 0), mcp_server.McpProcessor())
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/mcp"

    def post(self, message, session=None):
        import urllib.request
        request = urllib.request.Request(
            self.url, data=json.dumps(message).encode("utf-8"),
            headers={"Content-Type": "application/json",
                     **({"Mcp-Session-Id": session} if session else {})})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_http_initialize_cree_une_session_puis_les_appels_suivent(self):
        status, headers, body = self.post(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2026-07-28"}})
        self.assertEqual(status, 200)
        session = headers.get("Mcp-Session-Id")
        self.assertTrue(session)
        self.assertEqual(json.loads(body)["result"]["serverInfo"]["name"],
                         "skill-distiller")

        status, _, body = self.post(
            {"jsonrpc": "2.0", "id": 2, "method": "skills/list"}, session=session)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["result"]["skills"][0]["uri"], SKILL_URI)

        status, _, _ = self.post(
            {"jsonrpc": "2.0", "id": 3, "method": "ping"}, session="inconnue")
        self.assertEqual(status, 404)


class HttpExploitationTestCase(unittest.TestCase):
    """Sonde /health, jeton Bearer optionnel et repli d'adresse par env.

    Pourquoi : ces contrats d'exploitation sont ce qui rend la façade
    utilisable depuis n'importe quel contexte agentique — un superviseur
    (Docker HEALTHCHECK, Kubernetes) a besoin d'une sonde stable, un
    déploiement exposé d'une authentification sans couche en amont, un
    orchestrateur d'un pilotage par variables d'environnement. Une
    régression ici rendrait le service inexploitable — ou dangereux.
    """

    def _server(self, token=None):
        server = mcp_server.McpHttpServer(
            ("127.0.0.1", 0), mcp_server.McpProcessor(), token=token)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f"http://127.0.0.1:{server.server_address[1]}"

    def _request(self, base, path, method="POST", headers=None, message=None):
        import urllib.request
        data = json.dumps(message).encode("utf-8") if message is not None else None
        request = urllib.request.Request(
            base + path, data=data, method=method,
            headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status
        except urllib.error.HTTPError as exc:
            return exc.code

    def test_health_repond_200_et_le_get_reste_refuse_ailleurs(self):
        base = self._server()
        self.assertEqual(self._request(base, "/health", method="GET"), 200)
        self.assertEqual(self._request(base, "/mcp", method="GET"), 405)

    def test_health_rest_disponible_sans_jeton(self):
        """La sonde ne révèle que l'existence du service : elle reste
        ouverte même quand le jeton protège /mcp."""
        base = self._server(token="secret")
        self.assertEqual(self._request(base, "/health", method="GET"), 200)

    def test_jeton_bearer_exige_quand_il_est_configure(self):
        base = self._server(token="secret")
        ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
        self.assertEqual(self._request(base, "/mcp", message=ping), 401)
        self.assertEqual(
            self._request(base, "/mcp", message=ping,
                          headers={"Authorization": "Bearer mauvais"}), 401)
        self.assertEqual(
            self._request(base, "/mcp", message=ping,
                          headers={"Authorization": "Bearer secret"}), 200)

    def test_sans_jeton_le_service_rest_ouvert(self):
        """Comportement d'origine préservé : sans variable, pas de contrôle."""
        base = self._server()
        self.assertEqual(
            self._request(base, "/mcp",
                          message={"jsonrpc": "2.0", "id": 1, "method": "ping"}),
            200)

    def test_adresse_http_l_argument_cli_prime_sur_l_env(self):
        with unittest.mock.patch.dict(
                os.environ, {"SKILL_DISTILLER_MCP_ADDR": "0.0.0.0:9999"}):
            self.assertEqual(mcp_server.http_addr("0.0.0.0:8080"), "0.0.0.0:8080")
            self.assertEqual(mcp_server.http_addr(), "0.0.0.0:9999")

    def test_adresse_http_absente_laisse_le_stdio(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(mcp_server.http_addr())


class RangementTestCase(unittest.TestCase):
    """Le plan de rangement des références doit suivre celui de la CLI.

    L'outil « organise chez lui » : si les deux plans diverent, un lot
    rendu par MCP ne serait plus lisible par `check` ni par la CLI.
    """

    def test_artifact_refs_suivent_files_de_la_cli(self):
        loader = importlib.machinery.SourceFileLoader("skill_distiller_cli", BIN)
        spec = importlib.util.spec_from_file_location(
            "skill_distiller_cli", BIN, loader=loader)
        cli = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cli)
        self.assertEqual(mcp_server.ARTIFACT_REFS, {
            "fiche": cli.FILES["fiche"],
            "synthese-brute": cli.FILES["brute"],
            "reconciliation": cli.FILES["reconciliation"],
            "synthese-reconciliee": cli.FILES["reconciliee"],
            "amendements": cli.FILES["amendements"],
            "skill-final": cli.FILES["final"],
        })


if __name__ == "__main__":
    unittest.main()
