"""Tests de la façade MCP (python3 -m unittest discover -s tests).

Pourquoi cette suite : elle protège le contrat vu par les agents — le
handshake (un client doit pouvoir se brancher), le skill servi avec ses
digests SHA-256 (c'est ce qui rend le workflow distribuable et vérifiable
— l'« auditable » du produit s'y joue), et le confinement des appels :
quatre outils, paramètres validés, aucun échappement de chemin dans les
ressources. Une régression ici rendrait l'outil inutilisable — ou
dangereux — depuis un contexte agentique.
"""

import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = str(ROOT / "bin" / "skill-distiller")
sys.path.insert(0, str(ROOT / "src"))

import mcp_server  # noqa: E402  (chemin ajouté ci-dessus)

SKILL_URI = "skill://skill-distiller/SKILL.md"


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

    def test_tools_list_expose_les_quatre_commandes(self):
        response = self.client.request("tools/list")
        tools = {t["name"]: t for t in response["result"]["tools"]}
        self.assertEqual(set(tools), {
            "skill_distiller_init", "skill_distiller_check",
            "skill_distiller_diff", "skill_distiller_new"})
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


if __name__ == "__main__":
    unittest.main()
