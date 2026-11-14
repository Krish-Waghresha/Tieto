"""Parse a unified git diff into files and hunks with stable IDs (deterministic, no LLM)."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class Hunk:
    path: str
    old_start: int
    old_len: int
    new_start: int
    new_len: int
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return f"{self.path}#L{self.new_start}"

    @property
    def short_id(self) -> str:
        return f"{self.path.rsplit('/', 1)[-1]}#L{self.new_start}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "short_id": self.short_id,
            "path": self.path,
            "old_start": self.old_start,
            "old_len": self.old_len,
            "new_start": self.new_start,
            "new_len": self.new_len,
            "added": len(self.added),
            "removed": len(self.removed),
            "whitespace_only": self.whitespace_only(),
        }

    def whitespace_only(self) -> bool:
        """Only leading/trailing whitespace or blank lines changed. Never for indentation-sensitive files."""
        if self.path.endswith((".py", ".yml", ".yaml", ".mk", "Makefile")):
            return False
        norm = lambda lines: [l.strip() for l in lines if l.strip()]
        return norm(self.removed) == norm(self.added)


@dataclass
class FileDiff:
    path: str
    status: str  # A, M, D
    hunks: list[Hunk] = field(default_factory=list)
    binary: bool = False

    @property
    def added(self) -> int:
        return sum(len(h.added) for h in self.hunks)

    @property
    def removed(self) -> int:
        return sum(len(h.removed) for h in self.hunks)


def git_diff(base: str, head: str, paths: list[str] | None = None, cwd: str = ".") -> str:
    cmd = ["git", "-c", "core.quotePath=false", "diff", "--no-color", "--no-ext-diff", "--no-renames", "-U0", f"{base}..{head}", "--"]
    cmd += paths or []
    return subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True).stdout


def parse(diff_text: str) -> list[FileDiff]:
    files: list[FileDiff] = []
    cur: FileDiff | None = None
    hunk: Hunk | None = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+) b/(.+)$", line)
            cur = FileDiff(path=m.group(2) if m else line, status="M")
            files.append(cur)
            hunk = None
        elif cur is None:
            continue
        elif line.startswith("new file mode"):
            cur.status = "A"
        elif line.startswith("deleted file mode"):
            cur.status = "D"
        elif line.startswith("Binary files ") or line.startswith("old mode") or line.startswith("new mode"):
            cur.binary = cur.binary or line.startswith("Binary files ")
        elif line.startswith("@@"):
            m = HUNK_RE.match(line)
            if not m:
                continue
            hunk = Hunk(
                path=cur.path,
                old_start=int(m.group(1)),
                old_len=int(m.group(2)) if m.group(2) is not None else 1,
                new_start=int(m.group(3)),
                new_len=int(m.group(4)) if m.group(4) is not None else 1,
            )
            cur.hunks.append(hunk)
        elif hunk is not None and line.startswith("+") and not line.startswith("+++"):
            hunk.added.append(line[1:])
        elif hunk is not None and line.startswith("-") and not line.startswith("---"):
            hunk.removed.append(line[1:])
    return files


def show(rev: str, path: str, cwd: str = ".") -> str:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=cwd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""
