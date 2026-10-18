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
#   - 第二層：自家 19 條繁中 trope catalog（regex；結構型另揭露未檢查）
#   - 合併輸出：critical / warning / info / nit 四級
#   - severity remap：error→critical, warning→warning, orphaned-tokens→nit (local remap)

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
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
    r"<!--\s*anti-slop-skip\s*:\s*([\w,\s-]+?)\s*-->", re.IGNORECASE
)


def parse_skip_markers(content: str) -> set[str]:
    """解析檔案內 `<!-- anti-slop-skip: trope-NN,trope-MM -->` 注解，回傳要跳過的 trope id set。

    用途：規範文件本身列舉壞 pattern 範例會自觸發 trope，需文件自宣告 skip。
    """
    skip: set[str] = set()
    for match in _SKIP_MARKER_RE.finditer(content):
        for tid in match.group(1).split(","):
            tid = tid.strip()
            if tid:
                skip.add(tid)
    return skip


def scan_file_with_tropes(content: str, patterns: dict[str, Any]) -> list[dict[str, Any]]:
    """
    第二層：對單一檔案內容跑 19 條繁中 trope 的 regex 樣式。

    只處理 patterns.json 中 type=regex 的 patterns（structural / context_check
    等高階分析尚未實作；報告另列未檢查的結構型樣式）。

    支援檔案內 `<!-- anti-slop-skip: trope-NN -->` 注解跳過指定 trope（給規範文件用）。
    """
    findings: list[dict[str, Any]] = []
    skip_tropes = parse_skip_markers(content)

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
            if pat.get("type") != "regex":
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
                matches = list(re.finditer(pat["pattern"], content, flags))
                if matches:
                    match_count += len(matches)
                    if not match_excerpt:
                        m = matches[0]
                        line_no = content.count("\n", 0, m.start()) + 1
                        match_excerpt = f"L{line_no}: {m.group(0)[:80]}"
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
    args = parser.parse_args()

    target_path = Path(args.target).expanduser().resolve()
    if not target_path.exists():
        print(f"❌ Target not found: {target_path}", file=sys.stderr)
        return 2

    patterns = load_patterns()
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
        trope_layer = scan_file_with_tropes(content, patterns)

        # 第三層：7 sins（僅 HTML/HTM/JSX/TSX）
        sins_layer: list[dict[str, Any]] | None = None
        if t.suffix.lower() in {".html", ".htm", ".jsx", ".tsx"}:
            sins_layer = scan_seven_sins(content)

        # 合併
        merged = merge_findings(design_md_layer, trope_layer, sins_layer)
        merged["target"] = str(t)
        merged["unchecked_rules"] = collect_unchecked_rules(patterns)

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
