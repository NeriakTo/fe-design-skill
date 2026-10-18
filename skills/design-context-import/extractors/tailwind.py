"""tailwind.py — 從 tailwind.config.{js,ts,mjs,cjs} 抽 design tokens

最權威 extractor — 若有 tailwind config 應作為 ground truth；其他 extractor 僅補不足。

支援：
- `theme.extend.{colors, spacing, fontSize, borderRadius, lineHeight}`
- 純 colors 物件 + flat / nested（如 `slate: { 50: '#...', 100: '#...' }`）
- 字串值 + 巢狀物件
- v3 `module.exports = { theme: { extend: { ... } } }` 格式
- v4 `@theme { --color-...: ...; }` CSS 格式

策略：用 regex 抽出 theme.extend block（avoid spawning Node.js parser，純 Python 即可）。

Part of design-context-import skill (fe-design v1.2.2 §10 P2.2)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re
from pathlib import Path

# 支援的 token category（與 Google design.md 對齊）
CATEGORIES = ("colors", "spacing", "fontSize", "borderRadius", "lineHeight",
              "fontFamily", "fontWeight")

# CSS 變數前綴 → Google design.md category 對照（v4 用）
V4_PREFIX_MAP = {
    "color": "colors",
    "spacing": "spacing",
    "font-size": "fontSize",
    "radius": "borderRadius",
    "line-height": "lineHeight",
    "font-weight": "fontWeight",
    "font-family": "fontFamily",
}


def _find_config_file(root: Path) -> Path | None:
    for fname in ("tailwind.config.js", "tailwind.config.ts",
                  "tailwind.config.mjs", "tailwind.config.cjs"):
        f = root / fname
        if f.is_file():
            return f
    return None


def _parse_v3_extend_block(content: str) -> dict[str, dict[str, str]]:
    """從 `module.exports = { theme: { extend: { ... } } }` 抽 token。

    Limitation：純 regex 不解析 spread (...preset) 或 import 的 theme，
    只抽 inline literal。複雜情境建議跑 `npx tailwindcss --print`（未做）。
    """
    result: dict[str, dict[str, str]] = {}
    extend_match = re.search(
        r'extend\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
        content, re.DOTALL,
    )
    if not extend_match:
        # 也許不用 extend，直接 theme: { colors: {...} }
        extend_block = content
    else:
        extend_block = extend_match.group(1)

    for cat in CATEGORIES:
        # 抓單層 token block
        block_re = re.compile(
            rf'\b{cat}\s*:\s*\{{([^{{}}]*(?:\{{[^{{}}]*\}}[^{{}}]*)*)\}}',
            re.DOTALL,
        )
        m = block_re.search(extend_block)
        if not m:
            continue
        inner = m.group(1)
        tokens: dict[str, str] = {}
        # 抓 `key: 'value'` 或 `key: "value"` 或 `key: 數字`
        # 同時處理 nested object：`slate: { 50: '#xxx' }`，flatten 為 `slate-50: '#xxx'`
        for token_match in re.finditer(
            r"['\"]?([a-zA-Z0-9_-]+)['\"]?\s*:\s*"
            r"(?:['\"]([^'\"]+)['\"]|"  # quoted string value
            r"\{([^{}]*)\}|"             # nested object
            r"(\d+(?:\.\d+)?(?:px|rem|em|%)?))",  # bare number
            inner,
        ):
            key = token_match.group(1)
            quoted_val = token_match.group(2)
            nested = token_match.group(3)
            bare_val = token_match.group(4)
            if quoted_val is not None:
                tokens[key] = quoted_val
            elif bare_val is not None:
                tokens[key] = bare_val
            elif nested is not None:
                # Flatten nested：slate: { 50: '#xxx' } → slate-50: '#xxx'
                for sub in re.finditer(
                    r"['\"]?([a-zA-Z0-9_-]+)['\"]?\s*:\s*"
                    r"(?:['\"]([^'\"]+)['\"]|"
                    r"(\d+(?:\.\d+)?(?:px|rem|em|%)?))",
                    nested,
                ):
                    sub_key = sub.group(1)
                    sub_val = sub.group(2) or sub.group(3)
                    if sub_val:
                        tokens[f"{key}-{sub_key}"] = sub_val
        if tokens:
            result[cat] = tokens
    return result


def _parse_v4_theme_block(content: str) -> dict[str, dict[str, str]]:
    """從 `@theme { --color-primary: #6366f1; }` 抽 token（Tailwind v4 格式）。"""
    result: dict[str, dict[str, str]] = {}
    theme_match = re.search(r'@theme\s*\{([^}]+)\}', content, re.DOTALL)
    if not theme_match:
        return result
    body = theme_match.group(1)
    for line_match in re.finditer(
        r'--([a-zA-Z]+)-([a-zA-Z0-9_-]+)\s*:\s*([^;]+);',
        body,
    ):
        prefix = line_match.group(1)
        token_name = line_match.group(2)
        value = line_match.group(3).strip()
        category = V4_PREFIX_MAP.get(prefix)
        if not category:
            continue
        result.setdefault(category, {})[token_name] = value
    return result


def extract(root: Path) -> dict[str, dict[str, str]]:
    """主入口。回傳 `{"colors": {...}, "spacing": {...}, ...}`，無資料則回空 dict。"""
    config = _find_config_file(root)
    if not config:
        return {}
    try:
        content = config.read_text(encoding="utf-8")
    except OSError:
        return {}
    # 先試 v4（@theme）
    v4_tokens = _parse_v4_theme_block(content)
    if v4_tokens:
        return v4_tokens
    # 再試 v3（theme.extend）
    return _parse_v3_extend_block(content)


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Extract design tokens from tailwind config")
    parser.add_argument("--root", default=".", help="Project root with tailwind.config.*")
    args = parser.parse_args()
    print(json.dumps(extract(Path(args.root)), indent=2, ensure_ascii=False))
