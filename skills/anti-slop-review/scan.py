#!/usr/bin/env python3
# Copyright 2026 Kevin Du
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Original source: https://github.com/google-labs-code/design.md
# Pinned upstream commit: 8ecd4645b957e6a683a05fb9c79cd6c9028873d0 (2026-04-25)
# Pinned npm package: @google/design.md@0.1.1
# License copy: ./LICENSE-APACHE-2.0
#
# Modifications by Kevin Du (2026-04-25 → 2026-04-26):
#   - 自家 anti-slop-review scan.py（fe-design v1.2.2 §7.2 雙層架構主程式）
#   - 第一層：shell out `npx @google/design.md@0.1.1 lint`（8 條結構規則）
#   - 第二層：自家 22 條繁中 trope catalog（regex 與 CSS 值；結構型另揭露未檢查）
#   - 合併輸出：critical / warning / info / nit 四級
#   - severity remap：error→critical, warning→warning, orphaned-tokens→nit (local remap)

from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from token_resolver import (
    check_font_conflict,
    check_indigo_conflict,
    extract_css_tokens,
)

SCRIPT_DIR = Path(__file__).resolve().parent
PATTERNS_PATH = SCRIPT_DIR / "patterns.json"

# Severity ordering（critical 最嚴重）
SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2, "nit": 3}

# Google lint rule 原生 severity → 我方 severity remap
GOOGLE_SEVERITY_REMAP = {
    "error": "critical",
    "warning": "warning",
    "info": "info",
}

# Google lint rule 特殊本地降級（fe-design v1.2 §7.2 規範）
GOOGLE_RULE_LOCAL_REMAP = {
    "orphaned-tokens": "nit",  # 原生 warning，降為 nit（avoid noise on starters）
}

# Google CLI 的 finding 不直接帶 rule_id；從 message 文字推斷
# 對應 packages/cli/src/linter/linter/rules/*.ts 真實 message 文字
# （R1 修正：codex HIGH-01 抓到 broken-ref / missing-sections regex 不對齊 upstream）
GOOGLE_MESSAGE_TO_RULE = [
    (re.compile(r"is defined but never referenced by any component", re.I), "orphaned-tokens"),
    (re.compile(r"has contrast ratio.*below WCAG AA minimum", re.I), "contrast-ratio"),
    (re.compile(r"No 'primary' color defined", re.I), "missing-primary"),
    (re.compile(r"No typography tokens defined", re.I), "missing-typography"),
    (re.compile(r"appears before.*which is out of order", re.I), "section-order"),
    (re.compile(r"does not resolve to any defined token|is not a recognized component sub-token", re.I), "broken-ref"),
    (re.compile(r"No '\w+' section defined", re.I), "missing-sections"),
    (re.compile(r"Design system defines\s", re.I), "token-summary"),
]


def infer_rule_id_from_message(message: str) -> str:
    """從 finding message 推斷 Google rule id（CLI output 不直接帶 rule_id）."""
    for pattern, rule_id in GOOGLE_MESSAGE_TO_RULE:
        if pattern.search(message):
            return rule_id
    return ""

# Google CLI npm package pin
NPX_PACKAGE = "@google/design.md@0.1.1"

# P1.12: vendored tarball fallback（npx 不可用時）
VENDORED_TARBALL = SCRIPT_DIR / "vendored" / "google-design.md-0.1.1.tgz"
VENDORED_EXTRACT_DIR = Path.home() / ".cache" / "anti-slop-review" / "design-md-0.1.1"
VENDORED_CLI_ENTRY = VENDORED_EXTRACT_DIR / "package" / "dist" / "index.js"


def ensure_vendored_extracted() -> bool:
    """確保 vendored tarball 已解壓到 cache dir；first-call 時做 lazy extract。

    安全檢查（R3 LOW-04 採納）：
    - 拒絕絕對路徑與 .. 跳脫
    - 拒絕 symlink / hardlink member（避免 link-out-of-tree 攻擊）
    - 解壓後驗證所有目的路徑 resolve() 後仍位於 cache dir 內
    """
    if VENDORED_CLI_ENTRY.is_file():
        return True
    if not VENDORED_TARBALL.is_file():
        return False
    try:
        VENDORED_EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
        cache_root = VENDORED_EXTRACT_DIR.resolve()
        import tarfile
        with tarfile.open(VENDORED_TARBALL, "r:gz") as tf:
            members = tf.getmembers()
            for m in members:
                if m.name.startswith("/") or ".." in Path(m.name).parts:
                    return False
                if m.issym() or m.islnk():
                    return False
                # 解壓目的 resolve 後必須仍在 cache_root 之內
                dest = (VENDORED_EXTRACT_DIR / m.name).resolve()
                try:
                    dest.relative_to(cache_root)
                except ValueError:
                    return False
            tf.extractall(VENDORED_EXTRACT_DIR)
        return VENDORED_CLI_ENTRY.is_file()
    except (OSError, tarfile.TarError):
        return False


def run_vendored_design_md_lint(target: Path) -> dict[str, Any]:
    """vendored fallback：直接 node <vendored>/package/dist/index.js lint ..."""
    if not ensure_vendored_extracted():
        return {
            "ok": False,
            "reason": "vendored_unavailable",
            "findings": [],
            "raw_summary": None,
        }
    cmd = ["node", str(VENDORED_CLI_ENTRY), "lint", str(target), "--format", "json"]
    try:
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, timeout=120, check=False,
        )
    except FileNotFoundError:
        return {
            "ok": False,
            "reason": "node_not_found",
            "findings": [],
            "raw_summary": None,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "reason": "vendored_timeout",
            "findings": [],
            "raw_summary": None,
        }
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        return {
            "ok": False,
            "reason": "invalid_json_from_vendored",
            "stderr_snippet": result.stderr[-500:] if result.stderr else "",
            "findings": [],
            "raw_summary": None,
        }
    return {
        "ok": True,
        "source": "vendored",
        "raw_payload": payload,
    }


def load_patterns() -> dict[str, Any]:
    """Load patterns.json."""
    with PATTERNS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def is_design_md(path: Path) -> bool:
    """偵測是否為 DESIGN.md 格式（YAML frontmatter + markdown body）."""
    if path.suffix.lower() not in {".md", ".mdx"}:
        return False
    try:
        first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    except (OSError, IndexError):
        return False
    return bool(first_line and first_line[0].strip() == "---")


def run_design_md_lint(target: Path, npx_cmd: str = "npx") -> dict[str, Any]:
    """
    第一層：shell out `npx @google/design.md lint`。

    回傳 dict 含 findings（已 severity remap）+ raw_summary + ok flag。
    若 npx 不可用則回 ok=False + 空 findings。
    """
    cmd = [npx_cmd, "--yes", NPX_PACKAGE, "lint", str(target), "--format", "json"]
    npx_failure_reason: str | None = None
    payload: dict[str, Any] | None = None
    try:
        result = subprocess.run(  # noqa: S603 — 命令 list 不傳 shell=True
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except FileNotFoundError:
        npx_failure_reason = "npx_not_found"
    except subprocess.TimeoutExpired:
        npx_failure_reason = "npx_timeout"
    else:
        # R3 MED-02 採納：先檢 returncode；非零視為 npx failure，避免「成功 stdout 空白」誤判 0 findings
        # design.md@0.1.1 lint 在「全 PASS」時也是 returncode=0；warnings/errors 仍是 0；非零 = 真失敗
        if result.returncode != 0 and not result.stdout.strip():
            npx_failure_reason = f"npx_nonzero_exit_{result.returncode}"
        else:
            try:
                payload = json.loads(result.stdout) if result.stdout.strip() else {}
            except json.JSONDecodeError:
                npx_failure_reason = "invalid_json_from_npx"
            else:
                # stdout 有內容但 returncode 非零 — payload 可信，但記錄 reason 給 telemetry
                if result.returncode != 0:
                    sys.stderr.write(
                        f"[warn] anti-slop-review: npx returncode={result.returncode} "
                        f"但 stdout 含 JSON payload，採用 payload\n"
                    )

    # P1.12: npx 任何失敗都嘗試 vendored fallback（不放過任何能跑成功的機會）
    used_source = "npx"
    if payload is None:
        # 審查者 R3 LOW#2 採納：fallback 觸發時印 stderr 通知，提升 observability
        sys.stderr.write(
            f"[info] anti-slop-review: npx 失敗（{npx_failure_reason}），"
            f"falling back to vendored tarball...\n"
        )
        vendored = run_vendored_design_md_lint(target)
        if vendored.get("ok"):
            payload = vendored.get("raw_payload") or {}
            used_source = "vendored"
            sys.stderr.write("[info] anti-slop-review: vendored fallback 成功\n")
        else:
            return {
                "ok": False,
                "reason": npx_failure_reason or "unknown",
                "vendored_reason": vendored.get("reason"),
                "stderr_snippet": vendored.get("stderr_snippet", ""),
                "findings": [],
                "raw_summary": None,
            }

    raw_findings = payload.get("findings", [])
    summary = payload.get("summary", {})

    # remap severity（含 orphaned-tokens 本地降級）
    remapped: list[dict[str, Any]] = []
    for f in raw_findings:
        message = f.get("message", "")
        rule_id = f.get("rule") or f.get("id") or infer_rule_id_from_message(message)
        google_severity = (f.get("severity") or "info").lower()
        local_severity = GOOGLE_SEVERITY_REMAP.get(google_severity, "info")
        # 本地特殊降級
        if rule_id in GOOGLE_RULE_LOCAL_REMAP:
            local_severity = GOOGLE_RULE_LOCAL_REMAP[rule_id]
        remapped.append({
            "source": "design-md-lint",
            "rule_id": rule_id,
            "severity": local_severity,
            "google_severity": google_severity,
            "path": f.get("path", ""),
            "message": message,
        })

    return {
        "ok": True,
        "used_source": used_source,
        "findings": remapped,
        "raw_summary": summary,
    }


_SKIP_MARKER_RE = re.compile(
    r"(?:<!--\s*anti-slop-skip\s*:\s*([\w,\s-]+?)\s*-->"
    r"|/\*\s*anti-slop-skip\s*:\s*([\w,\s-]+?)\s*\*/)", re.IGNORECASE
)


def parse_skip_markers(content: str) -> set[str]:
    """解析檔案內 HTML 或 CSS 的 anti-slop-skip 註解，回傳要跳過的 trope id set。

    用途：規範文件本身列舉壞 pattern 範例會自觸發 trope，需文件自宣告 skip。
    """
    skip: set[str] = set()
    for match in _SKIP_MARKER_RE.finditer(content):
        for tid in (match.group(1) or match.group(2)).split(","):
            tid = tid.strip()
            if tid:
                skip.add(tid)
    return skip


_CSS_PROPERTY_RE = re.compile(
    r"(?<![\w-])(?P<property>--[\w-]+|-?[a-z][\w-]*)\s*:\s*", re.I
)
_CSS_DECL_RE = re.compile(_CSS_PROPERTY_RE.pattern + r"(?P<value>[\s\S]*)", re.I)
_COLOR_RE = re.compile(
    r"(?<![\w-])(?:#[\da-f]{8}\b|#[\da-f]{6}\b|#[\da-f]{4}\b|#[\da-f]{3}\b"
    r"|(?:rgba?|hsla?)\([^()]*\)|var\(--[\w-]+\)|[a-z]+)(?![\w-])", re.I
)
_CSS_COLOR_NAMES = set("""
aliceblue antiquewhite aqua aquamarine azure beige bisque black blanchedalmond blue
blueviolet brown burlywood cadetblue chartreuse chocolate coral cornflowerblue
cornsilk crimson cyan darkblue darkcyan darkgoldenrod darkgray darkgreen darkgrey
darkkhaki darkmagenta darkolivegreen darkorange darkorchid darkred darksalmon
darkseagreen darkslateblue darkslategray darkslategrey darkturquoise darkviolet
deeppink deepskyblue dimgray dimgrey dodgerblue firebrick floralwhite forestgreen
fuchsia gainsboro ghostwhite gold goldenrod gray green greenyellow grey honeydew
hotpink indianred indigo ivory khaki lavender lavenderblush lawngreen lemonchiffon
lightblue lightcoral lightcyan lightgoldenrodyellow lightgray lightgreen lightgrey
lightpink lightsalmon lightseagreen lightskyblue lightslategray lightslategrey
lightsteelblue lightyellow lime limegreen linen magenta maroon mediumaquamarine
mediumblue mediumorchid mediumpurple mediumseagreen mediumslateblue mediumspringgreen
mediumturquoise mediumvioletred midnightblue mintcream mistyrose moccasin navajowhite
navy oldlace olive olivedrab orange orangered orchid palegoldenrod palegreen
paleturquoise palevioletred papayawhip peachpuff peru pink plum powderblue purple
rebeccapurple red rosybrown royalblue saddlebrown salmon sandybrown seagreen seashell
sienna silver skyblue slateblue slategray slategrey snow springgreen steelblue tan
teal thistle tomato turquoise violet wheat white whitesmoke yellow yellowgreen
""".split())
_BORDER_EXCLUDED_COLORS = {
    "transparent", "currentcolor", "inherit", "initial", "unset",
    "black", "white", "gray", "grey", "silver",
}


class _StyleRegions(HTMLParser):
    """HTML 詞法區域；屬性保留原文位置，不解碼實體或解讀反斜線。"""

    def __init__(self, content: str):
        super().__init__(convert_charrefs=False)
        self.lines = [0] + [m.end() for m in re.finditer("\n", content)]
        self.regions = []
        self.has_tags = False
        self.in_style = False
        # CSS url() 中的內嵌標記是 URL 資料，不能拿來判定 HTML。
        detection = re.sub(r"/\*.*?(?:\*/|$)",
                           lambda m: re.sub(r"[^\r\n]", " ", m[0]), content,
                           flags=re.S)
        detection = re.sub(
            r"\burl\(\s*(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[^)]*)\s*\)",
            lambda m: m[0].replace("<", " ").replace(">", " "), detection,
            flags=re.I,
        )
        self.feed(detection)
        self.close()

    def source_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        self.has_tags = True
        raw = self.get_starttag_text()
        base = self.source_offset()
        cursor = re.match(r"<[^\s/>]+", raw).end()
        while cursor < len(raw):
            while cursor < len(raw) and raw[cursor].isspace():
                cursor += 1
            name = re.compile(r"[^\s=/>]+").match(raw, cursor)
            if not name:
                break
            key = name[0].lower()
            cursor = name.end()
            while cursor < len(raw) and raw[cursor].isspace():
                cursor += 1
            if cursor >= len(raw) or raw[cursor] != "=":
                continue
            cursor += 1
            while cursor < len(raw) and raw[cursor].isspace():
                cursor += 1
            quote = raw[cursor] if cursor < len(raw) and raw[cursor] in "\"'" else ""
            cursor += bool(quote)
            start = cursor
            while cursor < len(raw) and (raw[cursor] != quote if quote else
                                         not raw[cursor].isspace() and raw[cursor] != ">"):
                cursor += 1
            if key == "style":
                self.regions.append((base + start, base + cursor, True))
            cursor += bool(quote)
        self.in_style = tag == "style"

    def handle_endtag(self, tag):
        self.has_tags = True
        if tag == "style":
            self.in_style = False

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            start = self.source_offset()
            self.regions.append((start, start + len(data), False))

    def handle_comment(self, data):
        self.has_tags = True

    def handle_decl(self, decl):
        self.has_tags = True


_JS_WORD_RE = re.compile(r"[A-Za-z_$][\w$]*")
_TEMPLATE_TAG_RE = re.compile(
    r"(?<![\w$])(?:(styled)\s*[.(]|(?:css|createGlobalStyle|keyframes|injectGlobal)\b\s*)"
)
_BACKTICK_RUN_RE = re.compile(r"`+")


def _has_template_tag(content: str) -> bool:
    """只檢查標籤外形；泛型與候選搜尋共用單向游標，避免重掃前文。"""
    cursor = 0
    while match := _TEMPLATE_TAG_RE.search(content, cursor):
        if match[1]:
            return True
        cursor = match.end()
        if content[cursor:cursor + 1] == "<":
            depth = 1
            cursor += 1
            while cursor < len(content) and depth:
                char = content[cursor]
                if char in "\"'":
                    cursor = _js_string_end(content, cursor)
                    continue
                if char == "<":
                    depth += 1
                elif char == ">" and content[cursor - 1] != "=":
                    depth -= 1
                cursor += 1
            if depth:
                return False
            while cursor < len(content) and content[cursor].isspace():
                cursor += 1
        if content[cursor:cursor + 1] == "`":
            return True
    return False


def _js_string_end(content: str, start: int) -> int:
    quote, cursor = content[start], start + 1
    while cursor < len(content):
        char = content[cursor]
        if char == "\\":
            cursor += 2
            continue
        cursor += 1
        if char == quote or char in "\r\n":
            break
    return min(cursor, len(content))


def _template_end(content: str, start: int) -> tuple[int | None, list[tuple[int, int]]]:
    """單向走訪樣板與插值；只回傳最外層插值範圍，不遞迴重掃。"""
    end, spans, _, _ = _walk_template(content, start, False)
    return end, spans


def _template_token(content, cursor, tokens, groups):
    """外層程式與各插值共用同一組標籤判準。"""
    previous, state = tokens[-1] if tokens else ("", "")
    tag = ""
    char = content[cursor]
    if char in "\"'":
        cursor = _js_string_end(content, cursor)
        token = "string"
    else:
        word = _JS_WORD_RE.match(content, cursor)
        token = word[0] if word else char
        arrow = token == ">" and cursor > 0 and content[cursor - 1] == "="
        cursor = word.end() if word else cursor + 1
        if word:
            if previous == "." and len(tokens) >= 2:
                owner = tokens[-2][1]
                if owner == "root":
                    tag = "styled"
                elif owner == "styled" and token == "attrs":
                    tag = "attrs"
            elif previous != ".":
                if token == "styled":
                    tag = "root"
                elif token in ("css", "createGlobalStyle", "keyframes", "injectGlobal"):
                    tag = "tag"
        elif token == "(":
            groups["("].append(state)
        elif token == ")" and groups["("]:
            owner = groups["("].pop()
            if owner in ("root", "attrs"):
                tag = "styled"
        elif token == "<" and (state or groups["<"]):
            groups["<"].append(state)
        elif token == ">" and not arrow and groups["<"]:
            tag = groups["<"].pop()
    tokens.append((token, tag))
    return cursor


def _walk_template(content, start, tagged):
    """堆疊走訪一次，依原文順序產出互不重疊的樣式片段。"""
    # template: depth == 0; interpolation: depth > 0
    stack = [(0, start, tagged, [], {"(": [], "<": []})]
    spans, regions, owners = [], [], []
    cursor = start + 1
    segment = cursor
    while cursor < len(content):
        depth, opening, is_style, tokens, groups = stack[-1]
        char = content[cursor]
        if char == "\\":
            cursor += 2
            continue
        if content.startswith("```", cursor):
            cursor = _BACKTICK_RUN_RE.match(content, cursor).end()
            continue
        if not depth:
            if char == "`":
                if is_style and segment < cursor:
                    regions.append((segment, cursor, True))
                    owners.append(opening)
                stack.pop()
                if not stack:
                    # 同一樣板的宣告可跨一般插值；只有巢狀樣式才切開區域。
                    merged, previous_owner = [], None
                    for region, owner in zip(regions, owners):
                        if merged and owner == previous_owner:
                            merged[-1] = (merged[-1][0], region[1], True)
                        else:
                            merged.append(region)
                        previous_owner = owner
                    return cursor + 1, spans, regions, merged
                stack[-1][3].append(("template", ""))
            elif content.startswith("${", cursor):
                if is_style and segment < cursor:
                    regions.append((segment, cursor, True))
                    owners.append(opening)
                stack.append((1, cursor, False, [], {"(": [], "<": []}))
                cursor += 2
                continue
        elif content.startswith("//", cursor):
            end = content.find("\n", cursor + 2)
            cursor = len(content) if end < 0 else end
            continue
        elif content.startswith("/*", cursor):
            end = content.find("*/", cursor + 2)
            cursor = len(content) if end < 0 else end + 2
            continue
        elif char == "`":
            state = tokens[-1][1] if tokens else ""
            stack.append((0, cursor, state in ("styled", "tag"), [], {"(": [], "<": []}))
            segment = cursor + 1
        elif char == "{":
            stack[-1] = (depth + 1, opening, is_style, tokens, groups)
            cursor = _template_token(content, cursor, tokens, groups)
            continue
        elif char == "}":
            if depth == 1:
                if len(stack) == 2:
                    spans.append((opening, cursor + 1))
                stack.pop()
                segment = cursor + 1
            else:
                stack[-1] = (depth - 1, opening, is_style, tokens, groups)
                cursor = _template_token(content, cursor, tokens, groups)
                continue
        elif not char.isspace():
            cursor = _template_token(content, cursor, tokens, groups)
            continue
        cursor += 1
    return None, [], [], []


def _tagged_templates(content: str):
    """以詞元狀態辨認標籤；括號與泛型閉合時沿用開頭的標籤狀態。"""
    if "`" not in content or not _has_template_tag(content):
        return [], [], content
    tokens = []  # (text, tag state)
    groups = {"(": [], "<": []}
    templates, regions, masks = [], [], []
    cursor = 0
    while cursor < len(content):
        char = content[cursor]
        if char.isspace():
            cursor += 1
            continue
        if content.startswith("//", cursor):
            end = content.find("\n", cursor + 2)
            cursor = len(content) if end < 0 else end
            continue
        if content.startswith("/*", cursor):
            end = content.find("*/", cursor + 2)
            cursor = len(content) if end < 0 else end + 2
            continue
        if char == "`":
            if content.startswith("```", cursor):
                cursor = _BACKTICK_RUN_RE.match(content, cursor).end()
                tokens.append(("fence", ""))
                continue
            state = tokens[-1][1] if tokens else ""
            end, _, visible, styles = _walk_template(content, cursor, state in ("styled", "tag"))
            if end is None:
                break
            templates.append((cursor, end))
            regions.extend(styles)
            # 遮蔽樣板內非樣式部分；片段已排序且互不重疊，不按巢狀深度重掃。
            left = cursor
            for start, stop, _ in visible:
                masks.append((left, start))
                left = stop
            masks.append((left, end))
            cursor = end
            tokens.append(("template", ""))
        else:
            cursor = _template_token(content, cursor, tokens, groups)

    masked = list(content)
    for start, stop in masks:
        for index in range(start, stop):
            if masked[index] not in "\r\n":
                masked[index] = " "
    return templates, regions, "".join(masked)


def _style_regions(content: str):
    templates, tagged, masked = _tagged_templates(content)
    if not templates:
        html = _StyleRegions(content)
        return (html.regions if html.has_tags else [(0, len(content), "{" not in content)]), content
    detection = list(masked)
    for start, stop in templates:
        for index in range(start, stop):
            if detection[index] not in "\r\n":
                detection[index] = " "
    html = _StyleRegions("".join(detection))
    base = html.regions if html.has_tags else [(0, len(content), "{" not in content)]
    # 從原有區域扣掉所有樣板字串，避免同一宣告被解析兩次。
    regions, template_index = [], 0
    for start, stop, inline in base:
        while template_index < len(templates) and templates[template_index][1] <= start:
            template_index += 1
        index = template_index
        while index < len(templates) and templates[index][0] < stop:
            left, right = templates[index]
            if start < left:
                regions.append((start, left, inline))
            start = max(start, right)
            index += 1
        if start < stop:
            regions.append((start, stop, inline))
    # 兩份來源均按原文排序，線性合併以保留第一筆命中的位置。
    merged, i, j = [], 0, 0
    while i < len(regions) and j < len(tagged):
        if regions[i][0] < tagged[j][0]:
            merged.append(regions[i])
            i += 1
        else:
            merged.append(tagged[j])
            j += 1
    return merged + regions[i:] + tagged[j:], masked


def css_declarations(content: str) -> list[re.Match]:
    """解析 HTML 樣式區域或 CSS 區塊；無大括號的純文字視為宣告清單。"""
    regions, content = _style_regions(content)
    masked = list(content)
    for start, stop, _ in regions:
        for comment in re.compile(r"/\*.*?(?:\*/|$)", re.S).finditer(content, start, stop):
            for index in range(comment.start(), comment.end()):
                if masked[index] not in "\r\n":
                    masked[index] = " "
    content = "".join(masked)
    declarations = []
    for start, stop, inline in regions:
        cursor, blocks = start, 0
        while cursor < stop:
            while cursor < stop and content[cursor].isspace():
                cursor += 1
            header = _CSS_PROPERTY_RE.match(content, cursor, stop) if inline or blocks else None
            end = header.end() if header else cursor
            depth, brackets, quote = 0, 0, ""
            while end < stop:
                char = content[end]
                if char == "\\":
                    if end + 1 == stop:
                        break
                    end = min(end + 2, stop)
                    continue
                if quote:
                    if char in "\r\n\f":
                        break
                    if char == quote:
                        quote = ""
                elif char in "\"'":
                    quote = char
                elif char in "{}":
                    break
                elif char == "[":
                    brackets += 1
                elif char == "]":
                    brackets = max(0, brackets - 1)
                elif char == "(":
                    depth += 1
                elif char == ")":
                    depth = max(0, depth - 1)
                elif char == ";" and depth == 0 and brackets == 0:
                    break
                end += 1
            boundary = content[end] if end < stop else ""
            if header and boundary != "{":
                declaration = _CSS_DECL_RE.match(content, cursor, end)
                if declaration:
                    declarations.append(declaration)
            if boundary == "{":
                blocks += 1
            elif boundary == "}":
                blocks = max(0, blocks - 1)
            cursor = end + 1
    return declarations


def css_rgb(value: str) -> tuple[float, float, float] | None:
    """解析可見的 hex / rgb(a) / hsl(a)，不解析變數或具名色。"""
    value = value.lower().strip()
    if re.fullmatch(r"#[\da-f]{3,4}|#[\da-f]{6}(?:[\da-f]{2})?", value):
        digits = value[1:]
        if len(digits) in (3, 4):
            digits = "".join(c * 2 for c in digits)
        if len(digits) == 8 and int(digits[6:8], 16) == 0:
            return None
        return tuple(int(digits[i:i + 2], 16) / 255 for i in (0, 2, 4))
    function = re.fullmatch(r"(rgba?|hsla?)\(([^()]*)\)", value)
    if not function:
        return None
    parts = re.split(r"\s*[,/]\s*|\s+", function[2].strip())
    try:
        if len(parts) == 4 and float(parts[3].removesuffix("%")) == 0:
            return None
        if function[1].startswith("rgb"):
            channels = tuple(float(p[:-1]) / 100 if p.endswith("%") else float(p) / 255
                             for p in parts[:3])
            if len(channels) == 3 and all(0 <= c <= 1 for c in channels):
                return channels
        elif len(parts) >= 3 and parts[1].endswith("%") and parts[2].endswith("%"):
            angle = re.fullmatch(r"([-+]?(?:\d*\.)?\d+)(deg|turn|grad|rad)?", parts[0])
            if angle is None:
                return None
            scale = {None: 1, "deg": 1, "turn": 360, "grad": .9, "rad": 180 / math.pi}
            hue = float(angle[1]) * scale[angle[2]] % 360
            saturation, lightness = float(parts[1][:-1]) / 100, float(parts[2][:-1]) / 100
            if 0 <= saturation <= 1 and 0 <= lightness <= 1:
                return colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    except ValueError:
        pass
    return None


def css_value_matches(
    content: str, rule: str, declarations: list[re.Match] | None = None,
) -> list[re.Match]:
    """CSS 宣告候選；回傳原文 match，保留行號。每個宣告最多計一次。"""
    matches = []
    for declaration in (css_declarations(content) if declarations is None else declarations):
        prop, value = declaration["property"].lower(), declaration["value"].strip()
        if rule == "colored_border":
            if prop not in {"border-left", "border-right", "border-top",
                            "border-inline-start", "border-inline-end"}:
                continue
            border = re.fullmatch(
                r"(\d*\.?\d+)(px|rem|em)\s+"
                r"(?:solid|dashed|dotted|double|groove|ridge|inset|outset)\s+"
                r"(.+?)(?:\s*!important)?", value, re.I | re.S
            )
            if not border:
                continue
            width, unit, color = float(border[1]), border[2].lower(), border[3].lower()
            if width < (3 if unit == "px" else .2) or color in _BORDER_EXCLUDED_COLORS:
                continue
            if (css_rgb(color) is not None or color in _CSS_COLOR_NAMES
                    or re.fullmatch(r"var\(--[\w-]+\)", color)):
                matches.append(declaration)
        elif rule == "cream_background":
            if prop not in {"background", "background-color"} and not (
                prop.startswith("--") and re.search(r"bg|background|paper|surface|base", prop)
            ):
                continue
            # 不把 url()、漸層中的色碼視為整片底色。
            color = re.sub(r"\s*!important\s*$", "", value, flags=re.I)
            rgb = css_rgb(color)
            if rgb is not None:
                hue, lightness, saturation = colorsys.rgb_to_hls(*rgb)
                if (30 - 1e-9 <= hue * 360 <= 60 + 1e-9
                        and lightness >= .9 - 1e-9 and saturation >= .2 - 1e-9):
                    matches.append(declaration)
        elif rule == "colored_glow":
            if prop in {"box-shadow", "text-shadow"}:
                shadows = [value]
            elif prop == "filter":
                shadows = re.findall(r"drop-shadow\(((?:[^()]|\([^()]*\))*)\)", value, re.I)
            else:
                continue
            for shadow in shadows:
                found = False
                # 逗號分割僅限函式外，rgba() 內的逗號不切開。
                for layer in re.split(r",(?![^()]*\))", shadow):
                    colors = list(_COLOR_RE.finditer(layer))
                    colored = False
                    for color in colors:
                        rgb = css_rgb(color[0])
                        if rgb is not None and (max(rgb) - min(rgb)) * 255 >= 16 - 1e-9:
                            colored = True
                        elif color[0].lower() in _CSS_COLOR_NAMES and not re.search(
                            r"black|white|gr[ae]y|silver|gainsboro", color[0], re.I
                        ):
                            colored = True
                    lengths = _COLOR_RE.sub(" ", layer)
                    lengths = re.sub(r"\binset\b", "", lengths, flags=re.I).strip()
                    offsets = re.match(
                        r"^[-+]?0(?:\.0+)?(?:px|rem|em)?\s+"
                        r"[-+]?0(?:\.0+)?(?:px|rem|em)?\s+(\d*\.?\d+)px\b", lengths, re.I
                    )
                    if colored and offsets and float(offsets[1]) >= 20:
                        found = True
                        break
                if found:
                    matches.append(declaration)
                    break
    return matches


def scan_file_with_tropes(
    content: str, patterns: dict[str, Any], skip_tropes: set[str] | None = None,
) -> list[dict[str, Any]]:
    """
    第二層：對單一檔案內容跑 22 條繁中 trope 的 regex 與 CSS 值樣式。

    處理 patterns.json 中 type=regex / css_value 的 patterns（structural / context_check
    等高階分析尚未實作；報告另列未檢查的結構型樣式）。

    支援檔案內 HTML / CSS anti-slop-skip 註解及 CLI 跳過指定 trope。
    """
    findings: list[dict[str, Any]] = []
    skip_tropes = parse_skip_markers(content) | (skip_tropes or set())
    declarations: list[re.Match] | None = None

    for trope in patterns.get("tropes", []):
        trope_id = trope["id"]
        trope_name = trope["name"]
        trope_severity = trope["severity"]
        min_count = trope.get("min_count", 1)
        exclusion_pattern = trope.get("exclusion_pattern")
        exclusion_desc = trope.get("exclusion_description", "")

        # 文件層級 skip marker（給規範文件本身使用）
        if trope_id in skip_tropes:
            continue

        # 檢查 exclusion（若 file 含 exclusion pattern 則跳過此 trope）
        if exclusion_pattern:
            try:
                if re.search(exclusion_pattern, content, re.IGNORECASE):
                    continue
            except re.error:
                pass  # invalid exclusion regex 視為不豁免

        match_count = 0
        match_excerpt = ""
        for pat in trope.get("patterns", []):
            if pat.get("type") not in {"regex", "css_value"}:
                continue  # 未實作樣式由 collect_unchecked_rules 揭露於報告
            try:
                flags = 0
                if "i" in pat.get("flags", ""):
                    flags |= re.IGNORECASE
                if "g" in pat.get("flags", "") or "m" in pat.get("flags", ""):
                    flags |= re.MULTILINE
                if "u" in pat.get("flags", ""):
                    flags |= re.UNICODE
                if "s" in pat.get("flags", ""):
                    flags |= re.DOTALL
                excluded_properties = pat.get("exclude_properties", [])
                if declarations is None and (pat["type"] == "css_value" or excluded_properties):
                    declarations = css_declarations(content)
                if pat["type"] == "css_value":
                    matches = css_value_matches(content, pat["rule"], declarations)
                else:
                    matches = list(re.finditer(pat["pattern"], content, flags))
                if excluded_properties:
                    spans = [d.span("value") for d in declarations
                             if d["property"].lower() in excluded_properties]
                    matches = [m for m in matches if not any(
                        start <= m.start() < end for start, end in spans
                    )]
                if matches:
                    match_count += len(matches)
                    if not match_excerpt:
                        m = matches[0]
                        line_no = content.count("\n", 0, m.start()) + 1
                        match_excerpt = f"L{line_no}: {content[m.start():m.end()][:80]}"
            except re.error as exc:
                # invalid regex pattern — log 為 nit 自我提醒，不阻擋
                findings.append({
                    "source": "trope-scan",
                    "trope_id": trope_id,
                    "severity": "nit",
                    "message": f"[regex error] {trope_id} pattern invalid: {exc}",
                })

        if match_count >= min_count:
            findings.append({
                "source": "trope-scan",
                "trope_id": trope_id,
                "trope_name": trope_name,
                "severity": trope_severity,
                "match_count": match_count,
                "min_count_threshold": min_count,
                "excerpt": match_excerpt,
                "remediation": trope.get("remediation", ""),
                "exclusion_note": exclusion_desc if exclusion_pattern else None,
            })

    return findings


_EMOJI_IN_HEADING_RE = re.compile(
    r"<(?:h[1-6]|button|li)[^>]*>(?:[^<]*[\U0001f300-\U0001f9ff☀-➿⭐\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff])",
    re.IGNORECASE | re.UNICODE,
)

_EMOJI_IN_ICON_CLASS_RE = re.compile(
    r'class="[^"]*icon[^"]*"[^>]*>(?:[^<]*[\U0001f300-\U0001f9ff☀-➿⭐\U0001fa00-\U0001fa6f\U0001fa70-\U0001faff])',
    re.IGNORECASE | re.UNICODE,
)

_TRUST_GRADIENT_RE = re.compile(
    r"linear-gradient\([^)]*(?:"
    r"(?:purple|#[89a-f][0-9a-f]{5})[^)]*(?:blue|#[0-5][0-9a-f]{5})|"
    r"(?:blue|#[0-5][0-9a-f]{5})[^)]*(?:cyan|#[0-9a-f]{2}[f][0-9a-f]{3})|"
    r"(?:indigo|#[4-8][0-9a-f]{5})[^)]*(?:pink|#[f][0-9a-f]{5})"
    r")",
    re.IGNORECASE,
)

_ROUNDED_LEFT_BORDER_RE = re.compile(
    r"border-radius\s*:[^;]+;[^}]*border-left\s*:[^;]*\d+px\s+solid|"
    r"border-left\s*:[^;]*\d+px\s+solid[^}]*border-radius\s*:[^;]+;",
    re.IGNORECASE | re.DOTALL,
)

_INVENTED_METRIC_RE = re.compile(
    r"\b\d+[×x]\s+(?:faster|better|more|cheaper|efficient|productive|reliable)",
    re.IGNORECASE,
)

_FILLER_COPY_RE = re.compile(
    r"lorem ipsum|feature (?:one|two|three)|placeholder text|sample content|"
    r"your (?:company|product) (?:name|here)|click here to learn more",
    re.IGNORECASE,
)


def scan_seven_sins(content: str) -> list[dict[str, Any]]:
    """第三層：7 sins P0 硬擋（CSS token-aware）。僅對 HTML 檔案執行。

    v1.7 P9.4b: 從 open-design anti-ai-slop.md 萃取的 7 cardinal sins。
    Sin #1 和 Sin #4 使用 token_resolver.py 的 CSS 語義理解。
    """
    findings: list[dict[str, Any]] = []

    # Sin #1: Tailwind indigo (token-aware)
    findings.extend(check_indigo_conflict(content))

    # Sin #2: Two-stop trust gradient
    for match in _TRUST_GRADIENT_RE.finditer(content):
        line_no = content.count("\n", 0, match.start()) + 1
        findings.append({
            "source": "seven-sins",
            "severity": "critical",
            "id": "sin-2-trust-gradient",
            "message": "Two-stop trust gradient detected (purple→blue / blue→cyan / indigo→pink)",
            "fix": "Use solid surface + intentional typography instead of gradient",
            "snippet": match.group(0)[:100],
            "line": line_no,
        })

    # Sin #3: Emoji as feature icons
    for pattern in (_EMOJI_IN_HEADING_RE, _EMOJI_IN_ICON_CLASS_RE):
        for match in pattern.finditer(content):
            line_no = content.count("\n", 0, match.start()) + 1
            findings.append({
                "source": "seven-sins",
                "severity": "critical",
                "id": "sin-3-emoji-icon",
                "message": "Emoji used as feature icon in heading/button/li/icon element",
                "fix": "Use monoline SVG icon (1.6-1.8px stroke, currentColor)",
                "snippet": match.group(0)[:100],
                "line": line_no,
            })

    # Sin #4: Font conflict (token-aware)
    tokens = extract_css_tokens(content)
    findings.extend(check_font_conflict(content, tokens))

    # Sin #5: Rounded card + colored left-border
    for match in _ROUNDED_LEFT_BORDER_RE.finditer(content):
        line_no = content.count("\n", 0, match.start()) + 1
        findings.append({
            "source": "seven-sins",
            "severity": "critical",
            "id": "sin-5-rounded-left-border",
            "message": "Rounded card with colored left-border accent (canonical AI dashboard tile)",
            "fix": "Drop either the border-radius or the left border",
            "snippet": match.group(0)[:100],
            "line": line_no,
        })

    # Sin #6: Invented metrics
    for match in _INVENTED_METRIC_RE.finditer(content):
        line_no = content.count("\n", 0, match.start()) + 1
        findings.append({
            "source": "seven-sins",
            "severity": "critical",
            "id": "sin-6-invented-metric",
            "message": f"Invented metric without source: \"{match.group(0)}\"",
            "fix": "Pull from a real source or use a labelled placeholder with data-source attr",
            "snippet": match.group(0),
            "line": line_no,
        })

    # Sin #7: Filler copy
    for match in _FILLER_COPY_RE.finditer(content):
        line_no = content.count("\n", 0, match.start()) + 1
        findings.append({
            "source": "seven-sins",
            "severity": "critical",
            "id": "sin-7-filler-copy",
            "message": f"Filler copy detected: \"{match.group(0)}\"",
            "fix": "Remove or replace with real content; use composition to solve empty sections",
            "snippet": match.group(0),
            "line": line_no,
        })

    # Remap severity: seven-sins findings use "critical" internally → map to P0
    for f in findings:
        if f.get("severity") == "P0":
            f["severity"] = "critical"

    return findings


def collect_unchecked_rules(patterns: dict[str, Any]) -> list[dict[str, Any]]:
    """揭露未實作的結構型樣式；混合規則的 regex 仍會執行。"""
    return [
        {
            "trope_id": trope["id"],
            "trope_name": trope["name"],
            "type": "structural",
            "rule": pat["rule"],
            "status": "未實作、未檢查",
        }
        for trope in patterns.get("tropes", [])
        for pat in trope.get("patterns", [])
        if pat.get("type") == "structural"
    ]


def merge_findings(
    design_md_layer: dict[str, Any] | None,
    trope_layer: list[dict[str, Any]],
    sins_layer: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """合併三層 findings 並排序。"""
    findings: list[dict[str, Any]] = []

    if design_md_layer and design_md_layer.get("ok"):
        findings.extend(design_md_layer["findings"])
    findings.extend(trope_layer)
    if sins_layer:
        findings.extend(sins_layer)

    # 按 severity 排序（critical 最先）
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.get("severity", "info"), 99))

    summary = {
        "critical": sum(1 for f in findings if f["severity"] == "critical"),
        "warning": sum(1 for f in findings if f["severity"] == "warning"),
        "info": sum(1 for f in findings if f["severity"] == "info"),
        "nit": sum(1 for f in findings if f["severity"] == "nit"),
    }
    summary["total"] = sum(summary.values())

    return {
        "findings": findings,
        "summary": summary,
        "design_md_lint": design_md_layer or {"ok": False, "reason": "skipped"},
    }


def severity_at_or_above(min_severity: str) -> set[str]:
    """回傳大於等於 min_severity 的 severity 集合."""
    threshold = SEVERITY_ORDER.get(min_severity, 99)
    return {s for s, lvl in SEVERITY_ORDER.items() if lvl <= threshold}


def format_text_report(result: dict[str, Any], target: str) -> str:
    """Human-readable 報告."""
    summary = result["summary"]
    lines = [
        f"🚫 Anti-slop review: {target}",
        "",
        f"── Critical ──({summary['critical']})",
    ]
    for f in result["findings"]:
        if f["severity"] != "critical":
            continue
        lines.append(format_finding_line(f))

    lines.extend(["", f"── Warning ──({summary['warning']})"])
    for f in result["findings"]:
        if f["severity"] != "warning":
            continue
        lines.append(format_finding_line(f))

    lines.extend(["", f"── Info ──({summary['info']})"])
    for f in result["findings"]:
        if f["severity"] != "info":
            continue
        lines.append(format_finding_line(f))

    lines.extend(["", f"── Nit ──({summary['nit']})"])
    for f in result["findings"]:
        if f["severity"] != "nit":
            continue
        lines.append(format_finding_line(f))

    lines.extend([
        "",
        f"Total: {summary['total']} findings",
        f"  critical: {summary['critical']}",
        f"  warning:  {summary['warning']}",
        f"  info:     {summary['info']}",
        f"  nit:      {summary['nit']}",
    ])

    if result.get("unchecked_rules"):
        lines.extend(["", "── 未實作、未檢查（結構型樣式）──"])
        for rule in result["unchecked_rules"]:
            lines.append(f"  • [{rule['trope_id']}] {rule['trope_name']} ({rule['rule']})")

    if not result["design_md_lint"]["ok"]:
        reason = result["design_md_lint"].get("reason", "unknown")
        lines.extend([
            "",
            f"⚠ design-md-lint skipped: {reason}",
            "  Hint: 確保已跑 `npm install -g @google/design.md@0.1.1` 預熱本地 cache",
        ])

    return "\n".join(lines)


def format_finding_line(f: dict[str, Any]) -> str:
    """單條 finding 的單行顯示."""
    if f["source"] == "design-md-lint":
        return f"  • [{f.get('rule_id', '?')}] {f.get('path', '')}: {f.get('message', '')}"
    # trope-scan
    excerpt = f.get("excerpt", "")
    name = f.get("trope_name", f.get("trope_id", "?"))
    count = f.get("match_count", 0)
    threshold = f.get("min_count_threshold", 1)
    remediation = f.get("remediation", "")
    line = f"  • [{f.get('trope_id', '?')}] {name} (×{count}/{threshold}): {excerpt}"
    if remediation:
        line += f"\n      → {remediation}"
    return line


SCAN_EXTENSIONS = {
    ".md", ".mdx", ".html", ".htm", ".jsx", ".tsx",
    ".css", ".scss", ".js", ".mjs", ".ts", ".vue", ".svelte",
}
EXCLUDED_DIRECTORIES = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage"}


def collect_targets(target: Path, recursive: bool) -> list[Path]:
    """單檔或目錄掃描；遞迴時先剪除依賴與產物目錄，不追蹤目錄符號連結。"""
    if target.is_file():
        return [target]
    if target.is_dir():
        if target.name in EXCLUDED_DIRECTORIES:
            return []
        if recursive:
            targets = []
            for root, directories, filenames in os.walk(target, followlinks=False):
                directories[:] = sorted(d for d in directories if d not in EXCLUDED_DIRECTORIES)
                for name in sorted(filenames):
                    path = Path(root) / name
                    if path.is_file() and path.suffix.lower() in SCAN_EXTENSIONS:
                        targets.append(path)
            return targets
        return sorted(p for p in target.iterdir() if p.is_file() and p.suffix.lower() in SCAN_EXTENSIONS)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="anti-slop-review scan.py — fe-design v1.2.2 §7.2 雙層 anti-slop review",
    )
    parser.add_argument("target", help="要 review 的檔案或目錄")
    parser.add_argument(
        "--skip-design-md-lint",
        action="store_true",
        help="跳過第一層（npx @google/design.md lint），只跑 trope 層",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="目錄遞迴掃描",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="輸出格式（default: text）",
    )
    parser.add_argument(
        "--severity-min",
        choices=["critical", "warning", "info", "nit"],
        default="info",
        help="輸出此 severity 以上的 finding（default: info）",
    )
    parser.add_argument(
        "--exit-code",
        choices=["always-zero", "fail-on-critical", "fail-on-warning"],
        default="fail-on-critical",
        help="exit code 策略（default: fail-on-critical）",
    )
    parser.add_argument(
        "--skip-tropes", default="", help="跳過指定規則，以逗號分隔，例如 trope-20,trope-21",
    )
    args = parser.parse_args()
    patterns = load_patterns()
    skip_tropes = {tid.strip() for tid in args.skip_tropes.split(",") if tid.strip()}
    unknown = skip_tropes - {trope["id"] for trope in patterns["tropes"]}
    if unknown:
        parser.error("未知的 trope 編號：" + ", ".join(sorted(unknown)))

    target_path = Path(args.target).expanduser().resolve()
    if not target_path.exists():
        print(f"❌ Target not found: {target_path}", file=sys.stderr)
        return 2

    targets = collect_targets(target_path, args.recursive)

    if not targets:
        print(f"❌ No reviewable files in {target_path}", file=sys.stderr)
        return 2

    all_results: list[dict[str, Any]] = []
    for t in targets:
        # 第一層：DESIGN.md lint（僅對 DESIGN.md 跑）
        design_md_layer: dict[str, Any] | None = None
        if not args.skip_design_md_lint and is_design_md(t):
            design_md_layer = run_design_md_lint(t)

        # 第二層：trope scan
        try:
            content = t.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            print(f"⚠ Failed to read {t}: {exc}", file=sys.stderr)
            continue
        trope_layer = scan_file_with_tropes(content, patterns, skip_tropes)

        # 第三層：7 sins（僅 HTML/HTM/JSX/TSX）
        sins_layer: list[dict[str, Any]] | None = None
        if t.suffix.lower() in {".html", ".htm", ".jsx", ".tsx"}:
            sins_layer = scan_seven_sins(content)

        # 合併
        merged = merge_findings(design_md_layer, trope_layer, sins_layer)
        merged["target"] = str(t)
        merged["unchecked_rules"] = [
            rule for rule in collect_unchecked_rules(patterns)
            if rule["trope_id"] not in (skip_tropes | parse_skip_markers(content))
        ]

        # 過濾 severity_min（R1 MED-04 修正：過濾後重算各級數量，不只改 total）
        allowed_severities = severity_at_or_above(args.severity_min)
        merged["findings"] = [
            f for f in merged["findings"] if f["severity"] in allowed_severities
        ]
        merged["summary"] = {
            "critical": sum(1 for f in merged["findings"] if f["severity"] == "critical"),
            "warning": sum(1 for f in merged["findings"] if f["severity"] == "warning"),
            "info": sum(1 for f in merged["findings"] if f["severity"] == "info"),
            "nit": sum(1 for f in merged["findings"] if f["severity"] == "nit"),
            "total": len(merged["findings"]),
        }
        all_results.append(merged)

    # 輸出
    if args.format == "json":
        print(json.dumps({"results": all_results}, ensure_ascii=False, indent=2))
    else:
        for r in all_results:
            print(format_text_report(r, r["target"]))
            print()

    # exit code
    aggregate_critical = sum(r["summary"].get("critical", 0) for r in all_results)
    aggregate_warning = sum(r["summary"].get("warning", 0) for r in all_results)
    if args.exit_code == "fail-on-critical" and aggregate_critical > 0:
        return 1
    if args.exit_code == "fail-on-warning" and (aggregate_critical > 0 or aggregate_warning > 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
