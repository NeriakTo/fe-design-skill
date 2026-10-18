#!/usr/bin/env python3
"""CSS Token Resolver — extract and resolve CSS custom properties from HTML.

fe-design v1.7 P9.4a: stdlib-only implementation (no pip dependencies).
Provides token-aware context for the 7 sins anti-slop linter.
"""

from __future__ import annotations

import re
from typing import Any


_STYLE_BLOCK_RE = re.compile(
    r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE
)

_RULE_BLOCK_RE = re.compile(
    r"([^{}]+)\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", re.DOTALL
)

_TOKEN_SCOPE_RE = re.compile(
    r"^\s*(:root|html|\[data-theme[^\]]*\])\s*$", re.IGNORECASE
)

_CSS_VAR_DECL_RE = re.compile(
    r"(--[\w-]+)\s*:\s*([^;]+);", re.IGNORECASE
)

_CSS_VAR_REF_RE = re.compile(
    r"var\(\s*(--[\w-]+)(?:\s*,\s*([^)]*))?\)", re.IGNORECASE
)

_MAX_VAR_DEPTH = 4


def extract_style_blocks(html: str) -> list[str]:
    """Extract all <style> block contents from HTML."""
    return _STYLE_BLOCK_RE.findall(html)


def extract_css_tokens(html: str) -> dict[str, dict[str, str]]:
    """Extract CSS custom properties grouped by scope selector.

    Returns: {":root": {"--accent": "#6366f1", ...}, "[data-theme=dark]": {...}}
    Only extracts from token-scope selectors (:root, html, [data-theme=*]).
    """
    tokens: dict[str, dict[str, str]] = {}
    for style_content in extract_style_blocks(html):
        for match in _RULE_BLOCK_RE.finditer(style_content):
            selector = match.group(1).strip()
            body = match.group(2)
            if not _TOKEN_SCOPE_RE.match(selector):
                continue
            scope_key = selector.strip()
            if scope_key not in tokens:
                tokens[scope_key] = {}
            for decl_match in _CSS_VAR_DECL_RE.finditer(body):
                prop_name = decl_match.group(1)
                prop_value = decl_match.group(2).strip()
                tokens[scope_key][prop_name] = prop_value
    return tokens


def resolve_css_var(value: str, theme_map: dict[str, str], depth: int = 0) -> str:
    """Resolve var() references up to _MAX_VAR_DEPTH levels deep.

    Args:
        value: A CSS value potentially containing var() references
        theme_map: Flat map of --name → value (merged from all scopes)
        depth: Current recursion depth (internal)

    Returns:
        The fully resolved value, or the last fallback, or the raw var() if unresolvable.
    """
    if depth >= _MAX_VAR_DEPTH:
        return value

    match = _CSS_VAR_REF_RE.search(value)
    if not match:
        return value

    var_name = match.group(1)
    fallback = match.group(2)

    resolved = theme_map.get(var_name)
    if resolved is not None:
        resolved = resolve_css_var(resolved, theme_map, depth + 1)
    elif fallback is not None:
        resolved = resolve_css_var(fallback.strip(), theme_map, depth + 1)
    else:
        return value

    result = value[: match.start()] + resolved + value[match.end() :]
    return resolve_css_var(result, theme_map, depth + 1)


def build_resolved_theme(tokens: dict[str, dict[str, str]]) -> dict[str, str]:
    """Build a flat resolved token map by merging all scopes (:root first).

    Scope priority: :root < html < [data-theme=*]
    """
    merged: dict[str, str] = {}
    priority_order = [":root", "html"]

    for scope in priority_order:
        if scope in tokens:
            merged.update(tokens[scope])

    for scope, props in tokens.items():
        if scope not in priority_order:
            merged.update(props)

    resolved: dict[str, str] = {}
    for name, value in merged.items():
        resolved[name] = resolve_css_var(value, merged)
    return resolved


def is_in_token_scope(css_content: str, position: int) -> bool:
    """Check if a position in CSS content is inside a :root/[data-theme] block.

    Used to distinguish legitimate token definitions from component-level usage.
    """
    depth = 0
    current_selector = ""
    i = 0
    while i < position:
        char = css_content[i]
        if char == "{":
            depth += 1
            if depth == 1:
                current_selector = css_content[max(0, i - 200) : i].strip()
                last_close = current_selector.rfind("}")
                if last_close >= 0:
                    current_selector = current_selector[last_close + 1 :].strip()
        elif char == "}":
            depth -= 1
            if depth == 0:
                current_selector = ""
        i += 1

    return bool(_TOKEN_SCOPE_RE.match(current_selector))


def check_indigo_conflict(html: str) -> list[dict[str, Any]]:
    """Sin #1: Detect Tailwind default indigo used outside token scopes.

    Returns list of findings with line number and snippet.
    """
    indigo_colors = {
        "#6366f1", "#4f46e5", "#4338ca", "#3730a3",
        "#8b5cf6", "#7c3aed", "#a855f7",
    }
    indigo_re = re.compile(
        r"(#(?:6366f1|4f46e5|4338ca|3730a3|8b5cf6|7c3aed|a855f7))",
        re.IGNORECASE,
    )

    findings: list[dict[str, Any]] = []
    for style_content in extract_style_blocks(html):
        for match in indigo_re.finditer(style_content):
            if not is_in_token_scope(style_content, match.start()):
                line_num = style_content[: match.start()].count("\n") + 1
                findings.append({
                    "severity": "P0",
                    "id": "sin-1-tailwind-indigo",
                    "message": f"AI-default indigo {match.group(1)} used outside token scope",
                    "fix": "Replace with var(--accent) from your DESIGN.md",
                    "snippet": _get_line_context(style_content, match.start()),
                    "line": line_num,
                })
    return findings


def check_font_conflict(html: str, tokens: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    """Sin #4: Detect sans-serif on display when DESIGN.md binds a serif.

    Checks if --font-display resolves to a serif font but h1/h2 use sans-serif.
    """
    resolved = build_resolved_theme(tokens)
    font_display = resolved.get("--font-display", "")

    font_lower = font_display.lower()
    if "sans-serif" in font_lower:
        return []
    serif_indicators = ["serif", "georgia", "times", "playfair", "merriweather", "lora"]
    is_serif_display = any(s in font_lower for s in serif_indicators)

    if not is_serif_display:
        return []

    sans_overrides = re.compile(
        r"(h[12]|\.heading|\.title)[^{]*\{[^}]*font-family\s*:\s*"
        r"(Inter|Roboto|system-ui|sans-serif|Helvetica|Arial)",
        re.IGNORECASE | re.DOTALL,
    )

    findings: list[dict[str, Any]] = []
    for style_content in extract_style_blocks(html):
        for match in sans_overrides.finditer(style_content):
            findings.append({
                "severity": "P0",
                "id": "sin-4-font-conflict",
                "message": f"Display heading uses {match.group(2)} but --font-display is serif ({font_display})",
                "fix": "Use var(--font-display) for h1/h2",
                "snippet": _get_line_context(style_content, match.start()),
            })
    return findings


def _get_line_context(content: str, position: int) -> str:
    """Get the line containing a position for snippet display."""
    line_start = content.rfind("\n", 0, position) + 1
    line_end = content.find("\n", position)
    if line_end == -1:
        line_end = len(content)
    return content[line_start:line_end].strip()[:120]
