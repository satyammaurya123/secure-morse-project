#!/usr/bin/env python3
"""
Repo guard - Claude Code PreToolUse hook that enforces AGENTS.md.

Reads the tool call (JSON) from stdin and prints one decision:
  deny  -> always blocked (destructive database operations)
  ask   -> the owner must approve (git writes, deletes, moves, new files,
           paths outside the repo, database writes, rule-file edits)
  (no output) -> normal Claude Code permission flow

If anything goes wrong inside this script it answers "ask", never "allow".
"""
import json
import os
import re
import sys
import tempfile

FILE_TOOLS = {"Read", "Write", "Edit", "MultiEdit", "NotebookEdit", "Glob", "Grep"}
SHELL_TOOLS = {"Bash", "PowerShell"}

# ---------------------------------------------------------------- shell words
PREFIX_WORDS = {"sudo", "command", "exec", "time", "nohup", "env", "xargs", "&", ".", "call", "start"}
NESTED_SHELLS = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh"}
DELETE_CMDS = {"rm", "rmdir", "del", "erase", "rd", "unlink", "shred", "remove-item", "ri", "rimraf", "trash"}
MOVE_CMDS = {"mv", "move", "move-item", "mi", "ren", "rename", "rename-item", "rni"}
CREATE_CMDS = {"touch", "mkdir", "md", "new-item", "ni"}
COPY_CMDS = {"cp", "copy", "copy-item", "cpi", "xcopy", "robocopy"}
WRITE_CMDS = {"tee", "set-content", "sc", "out-file", "add-content", "ac"}
READ_CMDS = {"cat", "head", "tail", "grep", "rg", "type", "get-content", "gc", "less", "more",
             "ls", "dir", "wc", "jq", "select-string", "sls", "diff", "fc", "findstr", "stat",
             "get-item", "get-childitem", "gci", "test-path", "file"}

GIT_READ = {"status", "log", "diff", "show", "blame", "ls-files", "ls-tree", "ls-remote", "rev-parse",
            "rev-list", "describe", "shortlog", "grep", "cat-file", "help", "version", "whatchanged",
            "show-ref", "for-each-ref", "check-ignore", "name-rev", "merge-base", "count-objects", "var"}
GIT_BRANCH_READ_FLAGS = {"-a", "--all", "-r", "--remotes", "-v", "-vv", "--verbose", "--list", "-l",
                         "--show-current", "--merged", "--no-merged", "--color", "--no-color"}
GH_READ_ACTIONS = {"view", "list", "status", "diff", "checks"}

# ------------------------------------------------------------ database rules
DB_EXEC = re.compile(
    r"\b(psql|pg_restore|sqlite3|mysql|neonctl)\b"
    r"|manage\.py\s+(shell|dbshell|runscript)\b"
    r"|\bpython[\w.]*\s+(-c|-)\s", re.I)
DESTRUCTIVE_SQL = re.compile(
    r"\b(drop\s+(table|database|schema|index|view|role|user|owned|sequence|function|extension)"
    r"|truncate|delete\s+from)\b", re.I)
WRITE_SQL = re.compile(
    r"\b(insert\s+into|update\s+\w+\s+set|alter\s+(table|database|schema|role|user)"
    r"|create\s+(table|database|schema|index|view|role|user|extension)"
    r"|grant|revoke|copy\s+\w+\s+from|vacuum|reindex)\b", re.I)
READ_SQL = re.compile(r"^\s*(select|show|explain|with|table|\\d\w*|\\l|\\conninfo)\b", re.I)
ORM_DELETE = re.compile(r"\.delete\(\s*\)|\.objects\.[^\n;]*\.delete\(", re.I)
ORM_WRITE = re.compile(
    r"\.(save|create|bulk_create|bulk_update|update|get_or_create|update_or_create|set_password)\(", re.I)
MANAGE = re.compile(r"(?:python[\w.]*\s+(?:\S*[\\/])?|\./)manage\.py\s+([\w-]+)([^\n]*)", re.I)
MANAGE_DENY = {"flush", "reset_db", "reset_schema"}
MANAGE_ASK = {"migrate", "makemigrations", "loaddata", "createsuperuser", "changepassword", "shell",
              "dbshell", "test", "runscript", "squashmigrations", "createcachetable", "clearsessions",
              "remove_stale_contenttypes"}
DOCKER_VOLUME_DELETE = re.compile(
    r"\bdocker(-compose|\s+compose)?\s+(?:[^\n;&|]*\s)?"
    r"(down\b[^\n;&|]*\s(-v|--volumes)\b|volume\s+(rm|prune)\b|system\s+prune\b[^\n;&|]*--volumes)", re.I)
DOCKER_DELETE = re.compile(r"\bdocker(-compose|\s+compose)?\s+(rm|rmi|[^\n;&|]*\bprune)\b", re.I)

# ------------------------------------------------------- files, paths, rules
CODE_DELETE = re.compile(
    r"shutil\.rmtree|os\.(remove|unlink|rmdir|removedirs)\(|\.unlink\(|\.rmdir\("
    r"|fs\.(rm|rmSync|unlink|unlinkSync|rmdir|rmdirSync)\(", re.I)
PROTECTED_MENTION = re.compile(r"AGENTS\.md|CLAUDE\.md|\.claude[\\/]+(settings(\.local)?\.json|hooks)", re.I)
GUARD_RUN = re.compile(r"^\S*python[\w.]*\s+\"?[^\"]*[\\/]\.claude[\\/]+hooks[\\/]+guard\.py\"?\s*$", re.I)
PATH_LIKE = re.compile(
    r"^(?:[A-Za-z]:[\\/]|/[\w.~-]+/|~(?:[\\/]|$)|\.\.(?:[\\/]|$)"
    r"|\$\{?[A-Za-z_]\w*\}?[\\/]|\$env:\w+[\\/]|%\w+%[\\/])", re.I)
POSIX_SKIP = ("/dev/", "/proc/", "/tmp/", "/usr/", "/bin/", "/sbin/")
NULL_TARGETS = {"/dev/null", "nul", "$null", "/dev/stderr", "/dev/stdout"}
REDIRECT = re.compile(r"(?<![-=<>&\w])\d?>>?(?!&)\s*(\"[^\"]*\"|'[^']*'|[^\s|;&<>()]+)")
WORD = re.compile(r"\"[^\"]*\"|'[^']*'|[^\s\"'|;&<>(){}`]+")


# ------------------------------------------------------------ text helpers
def unquote(text):
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def quote_mask(text):
    """True for every character that sits inside quotes."""
    mask, quote = [], None
    for ch in text:
        if quote:
            mask.append(True)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            mask.append(True)
        else:
            mask.append(False)
    return mask


def segments(cmd):
    """Split a command line into simple commands (on ; & | newlines and brackets outside quotes)."""
    parts, buf = [], []
    for ch, quoted in zip(cmd, quote_mask(cmd)):
        if not quoted and ch in ";&|\n(){}`":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def tokens(segment):
    return [unquote(t) for t in re.findall(r"\"[^\"]*\"|'[^']*'|\S+", segment)]


def command_of(toks):
    """Return (command name, args), skipping sudo/env/VAR=x style prefixes."""
    i = 0
    while i < len(toks):
        low = toks[i].lower()
        after_prefix = i > 0 and toks[i - 1].lower() in PREFIX_WORDS
        if low in PREFIX_WORDS or re.match(r"^\w+=", toks[i]) or (after_prefix and low.startswith("-")):
            i += 1
            continue
        break
    if i >= len(toks):
        return None, []
    name = re.split(r"[\\/]", toks[i])[-1].lower()
    if name.endswith(".exe"):
        name = name[:-4]
    return name, toks[i + 1:]


def strip_heredocs(cmd):
    """Drop heredoc / here-string bodies: their text is file content, not commands."""
    cmd = re.sub(r"@(['\"])\r?\n.*?\r?\n\1@", "@''@", cmd, flags=re.S)
    out, lines, i = [], cmd.split("\n"), 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        match = re.search(r"<<-?\s*(['\"]?)(\w+)\1", line)
        if match:
            while i < len(lines) and lines[i].strip() != match.group(2):
                i += 1
            if i < len(lines):
                out.append(lines[i])
                i += 1
    return "\n".join(out)


def plain_args(args):
    return [a for a in args if not a.startswith("-")]


# ------------------------------------------------------------------ guard
class Guard:
    def __init__(self, data):
        self.cwd = data.get("cwd") or os.getcwd()
        raw_project = (os.environ.get("CLAUDE_PROJECT_DIR") or self.cwd).rstrip("\\/")
        self.project = self.resolve(raw_project)
        slug = re.sub(r"[^A-Za-z0-9]", "-", raw_project)
        self.memory = self.resolve(os.path.join(os.path.expanduser("~"), ".claude", "projects", slug, "memory"))
        temp_roots = [tempfile.gettempdir(), "/tmp"]
        if os.environ.get("LOCALAPPDATA"):
            temp_roots.append(os.path.join(os.environ["LOCALAPPDATA"], "Temp"))
        self.scratch = [self.resolve(os.path.join(root, "claude")) for root in temp_roots]
        self.protected_files = {self.resolve(os.path.join(raw_project, name)) for name in
                                ("AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json")}
        self.protected_dir = self.resolve(os.path.join(raw_project, ".claude", "hooks"))
        self.asks, self.denies = [], []

    # ---- decisions
    def ask(self, reason):
        if reason not in self.asks:
            self.asks.append(reason)

    def deny(self, reason):
        if reason not in self.denies:
            self.denies.append(reason)

    # ---- paths
    def resolve(self, raw):
        """Turn a path from a tool call into an absolute, comparable path (None if unknown)."""
        path = unquote(raw.strip())
        if not path:
            return None
        path = re.sub(r"\$\{?env:(\w+)\}?", lambda m: os.environ.get(m.group(1), m.group(0)), path, flags=re.I)
        path = os.path.expandvars(os.path.expanduser(path))
        if "$" in path or re.search(r"%\w+%", path):
            return None
        if os.name == "nt":
            drive = re.match(r"^/([a-zA-Z])(/|$)", path)  # Git Bash style: /c/Users/...
            if drive:
                path = drive.group(1) + ":/" + path[3:]
        if not os.path.isabs(path):
            path = os.path.join(self.cwd, path)
        return os.path.normcase(os.path.abspath(path))

    @staticmethod
    def inside(path, root):
        if not path or not root:
            return False
        return path == root or path.startswith(root.rstrip("\\/") + os.sep)

    def in_scratch(self, path):
        return any(self.inside(path, root) for root in self.scratch)

    def agent_space(self, path):
        return self.inside(path, self.memory) or self.in_scratch(path)

    def allowed(self, path):
        return self.inside(path, self.project) or self.agent_space(path)

    def is_protected(self, path):
        return path in self.protected_files or self.inside(path, self.protected_dir)

    def resolve_all(self, args):
        return [self.resolve(a) for a in plain_args(args)]

    # ---- file tools
    def check_file_tool(self, tool, inp):
        if tool in ("Glob", "Grep"):
            targets = [inp["path"]] if inp.get("path") else []
            pattern = inp.get("pattern", "") if tool == "Glob" else ""
            if PATH_LIKE.match(pattern):
                targets.append(re.split(r"[*?\[{]", pattern)[0])
            for raw in targets:
                path = self.resolve(raw)
                if path and not self.allowed(path):
                    self.ask(f"{tool} outside the repo: {raw}")
            return

        raw = inp.get("file_path") or inp.get("notebook_path") or ""
        path = self.resolve(raw)
        if not path:
            return
        if not self.allowed(path):
            self.ask(f"{tool} outside the repo: {raw}")
        if tool == "Read":
            return
        if self.is_protected(path):
            self.ask(f"{tool} on a rule file: {raw}")
        if tool == "Write" and not os.path.exists(path) and not self.agent_space(path):
            self.ask(f"Creates a new file: {raw}")

    # ---- shell tools
    def check_shell(self, cmd, depth=0):
        if not cmd.strip() or depth > 3:
            return
        self.check_db(cmd)
        if CODE_DELETE.search(cmd):
            self.ask("Code in this command deletes files")
        for segment in segments(cmd):
            self.check_segment(segment, depth)
        stripped = strip_heredocs(cmd)
        self.check_redirects(stripped)
        self.check_paths(stripped)

    def check_segment(self, seg, depth):
        toks = tokens(seg)
        name, args = command_of(toks)
        if not name:
            return

        # A shell started further along, e.g. `docker compose exec web sh -c "..."`
        for i in range(1, len(toks) - 2):
            shell = re.split(r"[\\/]", toks[i])[-1].lower().removesuffix(".exe")
            if shell in NESTED_SHELLS and toks[i + 1].lower() in ("-c", "/c", "/k", "-command"):
                self.check_shell(" ".join(toks[i + 2:]), depth + 1)

        if name in NESTED_SHELLS:
            rest = list(args)
            while rest and (rest[0].startswith("-") or rest[0].startswith("/")):
                rest.pop(0)
            if rest:
                self.check_shell(rest[0] if len(rest) == 1 else " ".join(rest), depth + 1)
        elif name == "git":
            self.check_git(args, seg)
        elif name == "gh":
            self.check_gh(args, seg)
        elif name in DELETE_CMDS or name in MOVE_CMDS:
            targets = self.resolve_all(args)
            if not targets or not all(t and self.in_scratch(t) for t in targets):
                verb = "Deletes" if name in DELETE_CMDS else "Moves/renames"
                self.ask(f"{verb} files: {seg}")
        elif name in CREATE_CMDS:
            targets = self.resolve_all(args)
            if not targets or not all(t and self.agent_space(t) for t in targets):
                self.ask(f"Creates new files/folders: {seg}")
        elif name in COPY_CMDS:
            dest = None
            for i, arg in enumerate(args):
                if arg.lower() == "-destination" and i + 1 < len(args):
                    dest = args[i + 1]
            if dest is None and plain_args(args):
                dest = plain_args(args)[-1]
            dest_path = self.resolve(dest) if dest else None
            if not dest_path or not self.agent_space(dest_path):
                self.ask(f"Copies files (creates new files): {seg}")
        elif name in WRITE_CMDS:
            self.check_write_cmd(name, args)
        elif name == "find" and ("-delete" in args or "rm" in args or "-exec" in args):
            self.ask(f"find that deletes or runs commands: {seg}")
        elif name == "dropdb":
            self.deny("dropdb deletes a database - never allowed")
        elif name in ("createdb", "pg_restore", "sqlite3", "mysql"):
            self.ask(f"Database tool that can write: {seg}")
        elif name == "psql":
            self.check_psql(args, seg)
        elif name == "neonctl":
            words = [w.lower() for w in plain_args(args)]
            if any(w in ("delete", "reset", "restore") for w in words):
                self.deny("neonctl delete/reset/restore - never allowed")
            elif words and not any(w in ("list", "get", "me", "connection-string", "cs", "help") for w in words):
                self.ask(f"neonctl change: {seg}")

        if PROTECTED_MENTION.search(seg) and name not in READ_CMDS and name != "git" and not GUARD_RUN.match(seg):
            self.ask(f"Touches a rule file (AGENTS.md / CLAUDE.md / .claude settings or hooks): {seg}")

    def check_git(self, args, seg):
        i = 0
        while i < len(args):
            if args[i] in ("-C", "-c", "--git-dir", "--work-tree", "--namespace"):
                i += 2
            elif args[i].startswith("-"):
                i += 1
            else:
                break
        if i >= len(args):
            return
        sub, rest = args[i].lower(), args[i + 1:]
        if not self.git_is_read(sub, rest):
            self.ask(f"git {sub} changes the repository (needs owner approval): {seg}")

    @staticmethod
    def git_is_read(sub, rest):
        first = rest[0].lower() if rest else ""
        if sub in GIT_READ:
            return True
        if sub == "branch":
            return not plain_args(rest) and all(r in GIT_BRANCH_READ_FLAGS for r in rest)
        if sub == "remote":
            return first in ("", "-v", "--verbose", "show", "get-url")
        if sub == "tag":
            return first in ("", "-l", "--list")
        if sub == "reflog":
            return first in ("", "show")
        if sub in ("stash", "worktree", "notes", "submodule"):
            return first in ("list", "show", "status")
        if sub == "config":
            return any(r in ("--get", "--get-all", "--get-regexp", "--list", "-l") for r in rest)
        return False

    def check_gh(self, args, seg):
        words = [w.lower() for w in plain_args(args)]
        if not words or (len(words) >= 2 and words[1] in GH_READ_ACTIONS):
            return
        self.ask(f"GitHub CLI action (needs owner approval): {seg}")

    def check_psql(self, args, seg):
        sql = None
        for i, arg in enumerate(args):
            if arg in ("-c", "--command") and i + 1 < len(args):
                sql = args[i + 1]
            elif arg.startswith("--command="):
                sql = arg.split("=", 1)[1]
        uses_file = any(a in ("-f", "--file") or a.startswith("--file=") for a in args)
        if sql is None or uses_file or "<" in seg:
            self.ask(f"psql session/script (only single read queries run freely): {seg}")
        elif DESTRUCTIVE_SQL.search(sql):
            self.deny("Destructive SQL (DROP / TRUNCATE / DELETE FROM) - never allowed")
        elif not READ_SQL.match(sql) or WRITE_SQL.search(sql):
            self.ask(f"Database write: {seg}")

    def check_db(self, cmd):
        exec_ctx = bool(DB_EXEC.search(cmd))
        if exec_ctx and DESTRUCTIVE_SQL.search(cmd):
            self.deny("Destructive SQL (DROP / TRUNCATE / DELETE FROM) - never allowed")
        if exec_ctx and ORM_DELETE.search(cmd):
            self.deny("ORM .delete() on the database - never allowed")
        mask = quote_mask(cmd)
        for match in MANAGE.finditer(cmd):
            if mask[match.start()]:
                continue  # text inside quotes, e.g. a grep pattern
            sub, rest = match.group(1).lower(), match.group(2)
            if sub in MANAGE_DENY:
                self.deny(f"manage.py {sub} wipes database data - never allowed")
            elif sub == "migrate" and re.search(r"\bzero\b", rest):
                self.deny("manage.py migrate ... zero drops tables - never allowed")
            elif sub in MANAGE_ASK or sub.startswith("seed"):
                self.ask(f"manage.py {sub} writes to the database")
        if DOCKER_VOLUME_DELETE.search(cmd):
            self.deny("Deleting Docker volumes deletes database data - never allowed")
        elif DOCKER_DELETE.search(cmd):
            self.ask("Docker rm/prune deletes containers or images")
        if exec_ctx and WRITE_SQL.search(cmd):
            self.ask("Database write (SQL)")
        if exec_ctx and ORM_WRITE.search(cmd):
            self.ask("Database write (ORM)")

    def check_write_cmd(self, name, args):
        if name == "tee":
            targets = plain_args(args)
        else:
            targets = [args[i + 1] for i, a in enumerate(args)
                       if a.lower() in ("-path", "-filepath", "-literalpath") and i + 1 < len(args)]
            if not targets and plain_args(args):
                targets = plain_args(args)[:1]
        for target in targets:
            self.check_write_target(target, name)

    def check_write_target(self, raw, what):
        if raw.lower() in NULL_TARGETS or raw.startswith("&"):
            return
        path = self.resolve(raw)
        if not path:
            return
        if not self.allowed(path):
            self.ask(f"{what} writes outside the repo: {raw}")
        if self.is_protected(path):
            self.ask(f"{what} writes into a rule file: {raw}")
        if not os.path.exists(path) and not self.agent_space(path):
            self.ask(f"{what} creates a new file: {raw}")

    def check_redirects(self, cmd):
        mask = quote_mask(cmd)
        for match in REDIRECT.finditer(cmd):
            if mask[match.start() + match.group(0).index(">")]:
                continue
            self.check_write_target(unquote(match.group(1)), "Redirect")

    def check_paths(self, cmd):
        for match in WORD.finditer(cmd):
            word = match.group(0)
            if word[0] in "\"'":
                content = word[1:-1]
                candidates = [content] if PATH_LIKE.match(content) else \
                    [w.split("=")[-1] for w in re.findall(r"[^\s|;&<>(){}`]+", content)]
            else:
                candidates = [word.split("=")[-1]]
            for cand in candidates:
                if not PATH_LIKE.match(cand) or cand.lower().startswith(POSIX_SKIP) or cand.lower() in NULL_TARGETS:
                    continue
                path = self.resolve(cand)
                if path and not self.allowed(path):
                    self.ask(f"Path outside the repo: {cand}")

    # ---- MCP tools that talk to a database
    def check_mcp(self, tool, inp):
        name, blob = tool.lower(), json.dumps(inp)
        if re.search(r"delete|drop|reset|truncate|remove|destroy", name) or DESTRUCTIVE_SQL.search(blob):
            self.deny(f"Destructive database action via {tool} - never allowed")
        elif WRITE_SQL.search(blob) or re.search(r"create|update|insert|migrat|alter|apply|restore|provision|write", name):
            self.ask(f"Database write via {tool}")


def emit(decision, reasons):
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": "Repo guard (AGENTS.md): " + " | ".join(reasons),
        }
    }))


def main():
    data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace") or "{}")
    tool = data.get("tool_name", "")
    inp = data.get("tool_input") or {}
    guard = Guard(data)

    if tool in SHELL_TOOLS:
        guard.check_shell(inp.get("command", ""))
    elif tool in FILE_TOOLS:
        guard.check_file_tool(tool, inp)
    elif tool.startswith("mcp__"):
        guard.check_mcp(tool, inp)

    if guard.denies:
        emit("deny", guard.denies)
    elif guard.asks:
        emit("ask", guard.asks)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never fail open
        emit("ask", [f"guard error ({exc.__class__.__name__}: {exc}) - asking to be safe"])
