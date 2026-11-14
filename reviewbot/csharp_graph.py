"""Text-level C# structure extraction: members, call edges, field fan-out, simple branch shapes.

Deterministic but NOT a compiler: graded HEURISTIC. The production design uses Roslyn
(SymbolFinder, ControlFlowGraph) to make these facts PROVEN lower bounds.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MODIFIERS = r"(?:public|private|protected|internal|static|readonly|async|override|virtual|sealed|new|unsafe|partial|extern|abstract)"
SIG_RE = re.compile(rf"^\s*(?:{MODIFIERS}\s+)+(?P<prefix>[^=;(]*?)\b(?P<name>[A-Za-z_]\w*)\s*(?:<[^>]*>)?\s*\(")
FIELD_RE = re.compile(rf"^\s*(?:{MODIFIERS}\s+)+[^=;(]*?\b(?P<name>[A-Za-z_]\w*)\s*(?:=[^>]|;)")
CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*(?:\?\.Invoke\s*)?\(")
KEYWORDS = {"if", "for", "foreach", "while", "switch", "catch", "using", "lock", "return", "new", "typeof",
            "nameof", "sizeof", "default", "when", "is", "as", "await", "throw", "base", "this", "checked"}


def strip_comments(lines: list[str]) -> list[str]:
    out, in_block = [], False
    for line in lines:
        res, i = "", 0
        while i < len(line):
            if in_block:
                j = line.find("*/", i)
                if j < 0:
                    i = len(line)
                else:
                    in_block, i = False, j + 2
                continue
            if line.startswith("//", i):
                break
            if line.startswith("/*", i):
                in_block, i = True, i + 2
                continue
            if line[i] == '"':  # skip simple string literal
                j = i + 1
                while j < len(line) and not (line[j] == '"' and line[j - 1] != "\\"):
                    j += 1
                res += '""'
                i = j + 1
                continue
            res += line[i]
            i += 1
        out.append(res)
    return out


@dataclass
class Member:
    name: str
    kind: str  # method | field
    start: int  # 1-based line
    end: int
    body: str = ""

    def contains(self, line: int) -> bool:
        return self.start <= line <= self.end


@dataclass
class Model:
    members: list[Member] = field(default_factory=list)
    code: list[str] = field(default_factory=list)  # comment-stripped lines

    def by_name(self, name: str) -> list[Member]:
        return [m for m in self.members if m.name == name]

    def member_at(self, line: int) -> Member | None:
        hits = [m for m in self.members if m.kind == "method" and m.contains(line)]
        return min(hits, key=lambda m: m.end - m.start) if hits else None

    def method_names(self) -> set[str]:
        return {m.name for m in self.members if m.kind == "method"}

    def field_names(self) -> set[str]:
        return {m.name for m in self.members if m.kind == "field"}


def _member_end(code: list[str], start_idx: int) -> int:
    """Return 0-based index of the last line of the member starting at start_idx."""
    depth, seen_brace, paren = 0, False, 0
    for idx in range(start_idx, len(code)):
        line = code[idx]
        for ch_i, ch in enumerate(line):
            if ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
            elif ch == "{":
                depth += 1
                seen_brace = True
            elif ch == "}":
                depth -= 1
                if seen_brace and depth == 0:
                    return idx
            elif ch == ";" and not seen_brace and paren <= 0:
                return idx  # expression-bodied or abstract member
    return len(code) - 1


def parse(source: str) -> Model:
    raw = source.splitlines()
    code = strip_comments(raw)
    model = Model(code=code)
    depth = 0
    idx = 0
    while idx < len(code):
        line = code[idx]
        at_member_depth = depth in (1, 2)
        if at_member_depth:
            m = SIG_RE.match(line)
            f = FIELD_RE.match(line) if not m else None
            if m and "class " not in line and "struct " not in line and "record " not in line:
                end = _member_end(code, idx)
                body = "\n".join(code[idx:end + 1])
                model.members.append(Member(m.group("name"), "method", idx + 1, end + 1, body))
                idx = end + 1
                continue
            if f and "class " not in line:
                model.members.append(Member(f.group("name"), "field", idx + 1, idx + 1, line))
        depth += line.count("{") - line.count("}")
        idx += 1
    return model


def calls_in(text: str, known: set[str]) -> set[str]:
    return {c for c in CALL_RE.findall(text) if c in known and c not in KEYWORDS}


def call_edges(model: Model) -> dict[str, set[str]]:
    known = model.method_names() | model.field_names()
    edges: dict[str, set[str]] = {}
    for m in model.members:
        if m.kind != "method":
            continue
        targets = calls_in(m.body, known) - {m.name}
        for fld in model.field_names():
            if re.search(rf"\b{re.escape(fld)}\s*(?:\?\.Invoke\s*)?\(", m.body):
                targets.add(fld)
        edges.setdefault(m.name, set()).update(targets)
    return edges


def field_invocations(model: Model, field_name: str) -> list[tuple[int, str]]:
    """Line numbers where a delegate field is invoked (?.Invoke(...) or direct call)."""
    pat = re.compile(rf"\b{re.escape(field_name)}\s*(?:\?\.Invoke\s*\(|\()")
    hits = []
    for i, line in enumerate(model.code, start=1):
        for _ in pat.finditer(line):
            owner = model.member_at(i)
            hits.append((i, owner.name if owner else "?"))
    return hits


def assigned_fields(lines: list[str]) -> list[tuple[str, str]]:
    """(field, right-hand side) for `this.F = expr;` assignments in the given lines."""
    out = []
    for line in lines:
        m = re.search(r"\bthis\.([A-Za-z_]\w*)\s*=(?!=)\s*(.+?);?\s*$", line)
        if m:
            out.append((m.group(1), m.group(2).rstrip(";").strip()))
    return out


def branch_shape(member: Member) -> list[dict]:
    """Very small CFG-lite: top-level `if (cond) { ... }` with/without else, and calls on each side."""
    body = member.body
    shapes = []
    for m in re.finditer(r"\bif\s*\(", body):
        i, depth = m.end(), 1
        while i < len(body) and depth:
            depth += {"(": 1, ")": -1}.get(body[i], 0)
            i += 1
        cond = " ".join(body[m.end():i - 1].split())
        rest = body[i:].lstrip()
        if rest.startswith("{"):
            j, d = 0, 0
            for j, ch in enumerate(rest):
                d += {"{": 1, "}": -1}.get(ch, 0)
                if d == 0:
                    break
            then_block, after = rest[1:j], rest[j + 1:].lstrip()
        else:
            semi = rest.find(";")
            then_block, after = rest[:semi + 1], rest[semi + 1:].lstrip()
        has_else = after.startswith("else")
        shapes.append({
            "cond": cond,
            "then_calls": sorted(set(CALL_RE.findall(then_block)) - KEYWORDS),
            "has_else": has_else,
        })
    return shapes
