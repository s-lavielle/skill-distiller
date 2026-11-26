#!/usr/bin/env python3
"""Façade MCP de skill-distiller : sert la CLI et le skill aux agents.

Un agent connecté (Claude Code, VS Code, Codex…) voit :
- quatre outils — les commandes de la CLI (init/check/diff/new) ;
- le skill `skill-distiller` (SKILL.md + templates/), au format Agent
  Skills via l'extension MCP Skills (SEP-2640, `io.modelcontextprotocol/
  skills`), avec ses digests SHA-256.

Le but : que l'outil reste autonome (CLI utilisable à la main) tout en
étant branchable par n'importe quel agent — MCP est la prise standard.
La façade ne réimplémente rien : chaque outil exécute la commande de la
CLI (bin/skill-distiller), qui reste la source de vérité.

Sans dépendance (bibliothèque standard Python 3). Deux transports :

    skill-distiller mcp                      # stdio (l'agent lance la commande)
    skill-distiller mcp --http 0.0.0.0:8080  # HTTP streamable (URL)

Garde-fous : pas d'outil de commande libre, paramètres validés (sujet en
slug, dir sur un seul segment), fichiers du skill servis depuis une liste
fermée (SKILL.md + templates/) — jamais d'arbitraire dans le chemin.
"""

import hashlib
import json
import re
import subprocess
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "bin" / "skill-distiller"
TEMPLATES_DIR = ROOT / "templates"
SKILL_MD = ROOT / "SKILL.md"

SERVER_NAME = "skill-distiller"
SERVER_VERSION = "0.1.0"  # version de la façade MCP (la CLI n'a pas de version)
SKILL_ROOT_URI = f"skill://{SERVER_NAME}"
SKILL_URI = f"{SKILL_ROOT_URI}/SKILL.md"

PROTOCOL_VERSION = "2026-07-28"
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-11-25", PROTOCOL_VERSION)

# CacheableResult (SEP-2640) : indice de fraîcheur pour les clients.
TTL_MS = 300000
CACHE_SCOPE = "public"

# Erreurs JSON-RPC.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Validations des paramètres d'outils (mêmes formats que les alias hôtes).
SUJET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DIR_RE = re.compile(r"^[A-Za-z0-9._-]+$")
HTTP_RE = r"^(?:(?P<host>[^:]+):)?(?P<port>\d+)$"

MIME_TYPES = {
    ".md": "text/markdown",
    ".yaml": "text/yaml",
    ".yml": "text/yaml",
    ".py": "text/x-python",
}
DIRECTORY_MIME = "inode/directory"


class RpcError(Exception):
    """Erreur JSON-RPC à renvoyer telle quelle au client."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


# ------------------------------------------------------------- le skill

def parse_frontmatter(text):
    """Front-matter du SKILL.md : paires `clé: valeur` (sous-ensemble plat).

    Le format Agent Skills n'exige que name et description, deux scalaires
    plats : ce lecteur suffit au skill servi. Un front-matter absent donne
    un dict vide (les valeurs par défaut comblent).
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            value = m.group(2).strip().strip('"').strip("'")
            fields[m.group(1)] = value
    return fields


def skill_file_map():
    """Fichiers du skill servi : chemin relatif → chemin absolu.

    Liste fermée : SKILL.md et templates/**, lus à la racine du dépôt —
    la source de vérité du skill, sans copie intermédiaire.
    """
    files = {"SKILL.md": SKILL_MD}
    if TEMPLATES_DIR.is_dir():
        for path in sorted(TEMPLATES_DIR.rglob("*")):
            if path.is_file():
                files[path.relative_to(ROOT).as_posix()] = path
    return files


def file_uri(rel):
    return f"{SKILL_ROOT_URI}/{rel}"


def digest_and_size(path):
    """Digest `sha256:{hex}` et taille, sur les octets bruts (SEP-2640)."""
    data = path.read_bytes()
    return "sha256:" + hashlib.sha256(data).hexdigest(), len(data)


def mime_of(rel):
    suffix = Path(rel).suffix.lower()
    return MIME_TYPES.get(suffix, "text/plain")


def skill_entry():
    """Entrée Skill (SEP-2640) : front-matter verbatim + manifeste complet."""
    frontmatter = parse_frontmatter(SKILL_MD.read_text(encoding="utf-8"))
    frontmatter.setdefault("name", SERVER_NAME)
    frontmatter.setdefault("description", "")
    resources = []
    for rel, path in skill_file_map().items():
        digest, size = digest_and_size(path)
        resources.append({"uri": file_uri(rel), "digest": digest, "size": size})
    return {"uri": SKILL_URI, "frontmatter": frontmatter, "resources": resources}


def resolve_skill_uri(uri):
    """URI `skill://skill-distiller/<chemin>` → chemin relatif, sinon None.

    Confinement : seul un fichier de la liste fermée est servi ; tout
    échappement (`..`, chemin absolu, inconnu) est refusé en aval.
    """
    prefix = SKILL_ROOT_URI + "/"
    if not uri.startswith(prefix):
        return None
    rel = uri[len(prefix):]
    if not rel or rel.startswith("/") or ".." in rel.split("/"):
        return None
    return rel


# -------------------------------------------------------------- les outils

TOOL_COMMANDS = {
    "skill_distiller_init": ("init", []),
    "skill_distiller_check": ("check", []),
    "skill_distiller_diff": ("diff", ["fetch"]),
    "skill_distiller_new": ("new", ["force"]),
}

_COMMON_PROPERTIES = {
    "sujet": {
        "type": "string",
        "description": "sujet du lot — slug (lettres, chiffres, points, tirets) : threads/<sujet>/",
    },
    "dir": {
        "type": "string",
        "description": "racine des artefacts, un seul segment (défaut : threads/)",
    },
    "project": {
        "type": "string",
        "description": "racine du projet cible (défaut : répertoire de travail du serveur)",
    },
}


def _tool(name, description, extra=None):
    properties = dict(_COMMON_PROPERTIES)
    if extra:
        properties.update(extra)
    return {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": ["sujet"],
        },
    }


TOOLS = [
    _tool(
        "skill_distiller_init",
        "Crée le lot threads/<sujet>/ du projet cible et pré-remplit les artefacts "
        "(équivalent de `skill-distiller init`). Le workflow à suivre ensuite est "
        "servi comme skill : skills/list.",
    ),
    _tool(
        "skill_distiller_check",
        "Vérifie le lot : traçabilité, étapes complètes, amendements cohérents "
        "(équivalent de `skill-distiller check`). Sortie non nulle s'il reste des "
        "erreurs — le rapport les liste.",
    ),
    _tool(
        "skill_distiller_diff",
        "Compare les copies figées des sources aux sources actuelles et produit le "
        "rapport d'état (équivalent de `skill-distiller diff`) : première étape de "
        "la réintégration.",
        extra={"fetch": {"type": "boolean",
                         "description": "télécharger les sources http(s) (défaut : non)"}},
    ),
    _tool(
        "skill_distiller_new",
        "Génère l'ossature du skill final depuis la synthèse amendée "
        "(équivalent de `skill-distiller new`).",
        extra={"force": {"type": "boolean",
                         "description": "écraser un 05-skill-final.md déjà rempli (défaut : non)"}},
    ),
]


def run_tool(name, args):
    """Exécute la commande CLI correspondante et rend son résultat.

    La CLI est appelée en sous-processus depuis la racine du projet cible :
    comportement identique à un usage terminal, zéro logique dupliquée.
    """
    subcommand, bool_flags = TOOL_COMMANDS[name]
    if not isinstance(args, dict):
        return _tool_error("arguments invalides : objet attendu")

    sujet = args.get("sujet")
    if not isinstance(sujet, str) or not SUJET_RE.match(sujet):
        return _tool_error(f"paramètre « sujet » invalide : {sujet!r} "
                           "(attendu : slug, ex. mon-sujet)")

    argv = [sys.executable, str(BIN), subcommand, sujet]

    dir_arg = args.get("dir")
    if dir_arg is not None:
        if not isinstance(dir_arg, str) or not DIR_RE.match(dir_arg):
            return _tool_error(f"paramètre « dir » invalide : {dir_arg!r} "
                               "(attendu : un seul segment, ex. atelier)")
        argv += ["--dir", dir_arg]

    for flag in bool_flags:
        value = args.get(flag, False)
        if not isinstance(value, bool):
            return _tool_error(f"paramètre « {flag} » invalide : booléen attendu")
        if value:
            argv.append(f"--{flag}")

    project = args.get("project", str(Path.cwd()))
    if not isinstance(project, str):
        return _tool_error("paramètre « project » invalide : chemin attendu")
    project_path = Path(project)
    if not project_path.is_dir():
        return _tool_error(f"projet cible introuvable : {project}")

    try:
        proc = subprocess.run(
            argv, cwd=project_path, capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return _tool_error(f"{subcommand} : délai dépassé (300 s)")
    except OSError as exc:
        return _tool_error(f"{subcommand} : exécution impossible ({exc})")

    text = proc.stdout.strip()
    if proc.stderr.strip():
        text = f"{text}\n{proc.stderr.strip()}".strip()
    if not text:
        text = f"{subcommand} : sortie vide (code {proc.returncode})"
    return {"content": [{"type": "text", "text": text}],
            "isError": proc.returncode != 0}


def _tool_error(message):
    return {"content": [{"type": "text", "text": message}], "isError": True}


# ------------------------------------------------------------ le protocole

class McpProcessor:
    """Cœur JSON-RPC : indépendant du transport (stdio ou HTTP)."""

    def handle(self, message):
        """Traite un message ; None pour une notification (sans réponse)."""
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return _error_response(_id_of(message), INVALID_REQUEST,
                                   "requête JSON-RPC 2.0 attendue")
        msg_id = message.get("id")
        method = message.get("method")
        if not isinstance(method, str):
            return None  # réponse ou notification malformée : ignorer
        params = message.get("params") or {}
        if msg_id is None:
            return None  # notification (ex. notifications/initialized)
        try:
            result = self._dispatch(method, params)
        except RpcError as exc:
            return _error_response(msg_id, exc.code, exc.message)
        except Exception as exc:  # jamais laisser le serveur mourir
            return _error_response(msg_id, INTERNAL_ERROR,
                                   f"{type(exc).__name__}: {exc}")
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _dispatch(self, method, params):
        if method == "initialize":
            return self._initialize(params)
        if method == "ping":
            return {}
        if method == "tools/list":
            return {"resultType": "complete", "tools": TOOLS,
                    "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}
        if method == "tools/call":
            return self._tools_call(params)
        if method == "skills/list":
            return {"resultType": "complete", "skills": [skill_entry()],
                    "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}
        if method == "skills/get":
            return self._skills_get(params)
        if method == "resources/list":
            return self._resources_list()
        if method == "resources/read":
            return self._resources_read(params)
        if method == "resources/directory/read":
            return self._directory_read(params)
        raise RpcError(METHOD_NOT_FOUND, f"méthode inconnue : {method}")

    def _initialize(self, params):
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOLS else PROTOCOL_VERSION
        return {
            "protocolVersion": version,
            "capabilities": {
                "tools": {},
                "resources": {},
                "extensions": {
                    "io.modelcontextprotocol/skills": {"directoryRead": True},
                },
            },
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                "skill-distiller : création de skills par distillation de sources. "
                "Le workflow complet (5 étapes, validations humaines) est servi comme "
                "skill (skills/list, skill://skill-distiller/SKILL.md) ; lisez-le avant "
                "d'agir. Les commandes sont les outils skill_distiller_init/check/"
                "diff/new, exécutées depuis la racine du projet cible (paramètre "
                "project, ou répertoire de travail du serveur)."
            ),
        }

    def _tools_call(self, params):
        name = params.get("name")
        if name not in TOOL_COMMANDS:
            raise RpcError(INVALID_PARAMS, f"outil inconnu : {name}")
        return run_tool(name, params.get("arguments") or {})

    def _skills_get(self, params):
        uri = params.get("uri")
        if uri != SKILL_URI:
            raise RpcError(INVALID_PARAMS, f"aucun skill servi à {uri}")
        return {"resultType": "complete", "skill": skill_entry(),
                "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}

    def _resources_list(self):
        """Ressources du skill (clients sans extension Skills : lecture simple)."""
        entry = skill_entry()
        by_uri = {item["uri"]: item for item in entry["resources"]}
        resources = []
        for rel in skill_file_map():
            uri = file_uri(rel)
            item = {"uri": uri, "mimeType": mime_of(rel),
                    "name": SERVER_NAME if rel == "SKILL.md" else rel}
            if rel == "SKILL.md":
                item["description"] = entry["frontmatter"].get("description", "")
            item["size"] = by_uri[uri]["size"]
            resources.append(item)
        return {"resultType": "complete", "resources": resources,
                "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}

    def _resources_read(self, params):
        uri = params.get("uri")
        rel = resolve_skill_uri(uri) if isinstance(uri, str) else None
        files = skill_file_map()
        if rel not in files:
            raise RpcError(INVALID_PARAMS, f"aucune ressource servie à {uri}")
        text = files[rel].read_text(encoding="utf-8", errors="replace")
        return {"resultType": "complete",
                "contents": [{"uri": uri, "mimeType": mime_of(rel), "text": text}],
                "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}

    def _directory_read(self, params):
        uri = params.get("uri")
        files = skill_file_map()
        rel_dir = "" if uri == SKILL_ROOT_URI else (
            resolve_skill_uri(uri) if isinstance(uri, str) else None)
        # Refusé si inconnu, ou si c'est un fichier plutôt qu'un répertoire.
        if rel_dir is None or (rel_dir != "" and (
                rel_dir in files
                or not any(r.startswith(rel_dir + "/") for r in files))):
            raise RpcError(INVALID_PARAMS,
                           f"{uri} n'est pas une ressource répertoire")
        # Enfants directs : fichiers servis + sous-répertoires dérivés.
        children = {}
        for rel in files:
            if rel_dir == "":
                rest = rel
            elif rel.startswith(rel_dir + "/"):
                rest = rel[len(rel_dir) + 1:]
            else:
                continue
            first, _, tail = rest.partition("/")
            child_uri = file_uri(f"{rel_dir}/{first}".lstrip("/"))
            if first not in children:
                children[first] = {"uri": child_uri, "name": first,
                                   "mimeType": DIRECTORY_MIME if tail else mime_of(rel)}
        return {"resultType": "complete",
                "resources": sorted(children.values(), key=lambda r: r["name"]),
                "ttlMs": TTL_MS, "cacheScope": CACHE_SCOPE}


def _id_of(message):
    return message.get("id") if isinstance(message, dict) else None


def _error_response(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id,
            "error": {"code": code, "message": message}}


# ------------------------------------------------------------ les transports

def run_stdio(processor):
    """Transport stdio : un message JSON par ligne, réponse sur stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response = _error_response(None, PARSE_ERROR, f"JSON invalide : {exc}")
        else:
            response = processor.handle(message)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


class McpHttpServer(ThreadingHTTPServer):
    """Serveur HTTP streamable : le point d'entrée /mcp, sessions légères."""

    daemon_threads = True

    def __init__(self, address, processor):
        super().__init__(address, McpHttpHandler)
        self.processor = processor
        self.sessions = set()


class McpHttpHandler(BaseHTTPRequestHandler):
    """Transport HTTP streamable (simplifié) : POST = requête JSON-RPC.

    Réponses JSON directes (pas de flux SSE) ; GET est refusé (405) car le
    serveur n'initie jamais de messages. Une session est créée à
    l'initialisation (en-tête Mcp-Session-Id) ; les requêtes sans session
    sont tolérées pour rester compatible avec les clients simples.
    """

    server_version = "skill-distiller-mcp"

    def do_POST(self):
        if self.path.rstrip("/") != "/mcp":
            self.send_error(404)
            return
        session = self.headers.get("Mcp-Session-Id")
        if session and session not in self.server.sessions:
            self.send_error(404, "session inconnue")
            return
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        try:
            message = json.loads(body)
        except json.JSONDecodeError as exc:
            self._send_json(_error_response(None, PARSE_ERROR,
                                            f"JSON invalide : {exc}"), 400)
            return
        response = self.server.processor.handle(message)
        if response is None:
            self.send_response(202)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        headers = {}
        if isinstance(message, dict) and message.get("method") == "initialize":
            session = uuid.uuid4().hex
            self.server.sessions.add(session)
            headers["Mcp-Session-Id"] = session
        elif session:
            headers["Mcp-Session-Id"] = session
        self._send_json(response, 200, headers)

    def do_GET(self):
        self.send_error(405, "pas de flux serveur (POST uniquement)")

    def do_DELETE(self):
        session = self.headers.get("Mcp-Session-Id")
        if session in self.server.sessions:
            self.server.sessions.discard(session)
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_error(405, "sessions non gérées côté client")

    def _send_json(self, payload, status, headers=None):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        """Journal silencieux : stdout = protocole, stderr = rien d'utile ici."""
        pass


def run_http(processor, spec):
    """Démarre le serveur HTTP sur HOST:PORT (host défaut : 127.0.0.1)."""
    m = re.match(HTTP_RE, spec)
    if not m:
        raise RpcError(INVALID_PARAMS,
                       f"adresse HTTP invalide : {spec!r} (attendu HOST:PORT)")
    host = m.group("host") or "127.0.0.1"
    port = int(m.group("port"))
    if not 1 <= port <= 65535:
        raise RpcError(INVALID_PARAMS, f"port invalide : {port}")
    server = McpHttpServer((host, port), processor)
    shown_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    print(f"MCP HTTP sur http://{shown_host}:{server.server_address[1]}/mcp")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def serve(http=None):
    """Point d'entrée appelé par la CLI : stdio par défaut, HTTP avec --http."""
    processor = McpProcessor()
    if http is not None:
        run_http(processor, http)
    else:
        run_stdio(processor)


if __name__ == "__main__":
    serve(sys.argv[1] if len(sys.argv) > 1 else None)
