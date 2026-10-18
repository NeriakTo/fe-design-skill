"""scss_vars.py — 從 SCSS `$foo: bar;` 抽 design tokens

再次優 extractor — 用於老 SCSS 專案。

策略：
- glob `**/*.{scss,sass}`，跳過 node_modules / build dirs
- regex 抽 top-level `$name: value;`（跳過 nested rule 內的）
- 同樣依 prefix 分類

Part of design-context-import skill (fe-design v1.2.2 §10 P2.4)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re
from pathlib import Path

# 共用同 css_vars 的分類邏輯（透過 import 避免重複）
from .css_vars import CATEGORY_RULES, SKIP_DIRS


def _classify(var_name: str) -> tuple[str, str] | None:
    for prefix_re, category in CATEGORY_RULES:
        m = prefix_re.match(var_name)
        if m:
            token_name = var_name[m.end():] or var_name
            return category, token_name
    return None


def _iter_scss_files(root: Path):
    for ext in ("scss", "sass"):
        for f in root.glob(f"**/*.{ext}"):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            yield f


def _extract_top_level_vars(text: str) -> list[tuple[str, str]]:
    """抽 top-level `$foo: bar;` 對；跳過 nested block 內的。

    簡化策略：只看 `^` (line start) 開頭的 `$var:`。
    嚴謹策略需要追蹤 brace depth；對 design tokens 場景沒必要。
    """
    result: list[tuple[str, str]] = []
    for line_match in re.finditer(
        r"^\s*\$([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*([^;]+);",
        text,
        re.MULTILINE,
    ):
        name = line_match.group(1)
        value = line_match.group(2).strip()
        # 跳過 SCSS 函式呼叫如 `$primary: darken($base, 10%);` 太複雜的值
        # 簡單值才採（hex / rgb / 數字 + 單位 / 字串 / var(...)）
        if not re.match(
            r"^(?:#[0-9a-fA-F]{3,8}|"            # hex color
            r"rgb\([^)]+\)|rgba\([^)]+\)|"        # rgb/rgba
            r"hsl\([^)]+\)|hsla\([^)]+\)|"        # hsl/hsla
            r"\d+(?:\.\d+)?(?:px|rem|em|%|vh|vw)?|"  # number + unit
            r"['\"][^'\"]+['\"]|"                # string
            r"var\(--[\w-]+\))",                 # var()
            value,
        ):
            continue
        # 去掉外層 quote
        value = value.strip("\"'")
        result.append((name, value))
    return result


def extract(root: Path) -> dict[str, dict[str, str]]:
    """主入口。"""
    result: dict[str, dict[str, str]] = {}
    seen: set[tuple[str, str]] = set()
    for f in _iter_scss_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, value in _extract_top_level_vars(text):
            classified = _classify(name)
            if not classified:
                continue
            category, token_name = classified
            if (category, token_name) in seen:
                continue
            seen.add((category, token_name))
            result.setdefault(category, {})[token_name] = value
    return result


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Extract design tokens from SCSS variables")
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()
    print(json.dumps(extract(Path(args.root)), indent=2, ensure_ascii=False))
