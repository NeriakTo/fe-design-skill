"""tailwind_v4_adapter.py — Tailwind v3 theme.extend → v4 @theme {} CSS

`npx @google/design.md@0.1.1 export DESIGN.md --format tailwind` 產出的是
Tailwind v3 寫法（`module.exports = { theme: { extend: { ... } } }` 內的 config object）。
Tailwind v4 改為純 CSS-first（`@theme { --color-primary: #...; }`）。

本 adapter 把 v3 config object 轉成 v4 `@theme {}` CSS 片段。

對應規則（依 Tailwind v4 docs）:
  v3 colors.primary: '#6366f1'           → --color-primary: #6366f1;
  v3 colors.slate: { 500: '#xxx' }       → --color-slate-500: #xxx;
  v3 spacing.md: '16px'                  → --spacing-md: 16px;
  v3 borderRadius.lg: '12px'             → --radius-lg: 12px;
  v3 fontSize.body: '16px'               → --font-size-body: 16px;
  v3 fontSize.body: ['16px', { lineHeight: '1.6' }]
                                          → --font-size-body: 16px;
                                          → --line-height-body: 1.6;
  v3 fontFamily.sans: ['Inter', 'sans-serif']
                                          → --font-family-sans: Inter, sans-serif;
  v3 fontWeight.bold: '700'              → --font-weight-bold: 700;
  v3 lineHeight.body: '1.6'              → --line-height-body: 1.6;

輸入支援兩種：
  - 純 JSON config object（最理想；如 `npx ... export` 直接 stdout）
  - JS module 格式（`module.exports = { theme: { extend: { ... } } }`）— regex 抽出後處理

Part of design-context-import skill (fe-design v1.2.2 §10 P2.9)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# v3 category → v4 CSS variable prefix
V3_TO_V4_PREFIX = {
    "colors":       "--color",
    "spacing":      "--spacing",
    "fontSize":     "--font-size",
    "borderRadius": "--radius",
    "lineHeight":   "--line-height",
    "fontFamily":   "--font-family",
    "fontWeight":   "--font-weight",
}


def _flatten(obj: dict, prefix: str = "") -> dict[str, str]:
    """把 nested object 攤平：{slate: {500: '#xxx'}} → {slate-500: '#xxx'}"""
    out: dict[str, str] = {}
    for key, val in obj.items():
        full = f"{prefix}-{key}" if prefix else str(key)
        if isinstance(val, dict):
            out.update(_flatten(val, full))
        elif isinstance(val, list):
            # 字型 fallback list 或 fontSize tuple
            out[full] = val  # 保留 list 給後續 handle
        else:
            out[full] = val
    return out


def _extract_config_object(text: str) -> dict | None:
    """從 JS source / JSON 抽出最外層 config object。

    優先 JSON.parse；失敗時用 regex 抽 module.exports = { ... } 內的 theme.extend。
    """
    # 嘗試直接 parse 為 JSON
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 抽 module.exports / export default 的 theme.extend block
    m = re.search(
        r'(?:module\.exports|export\s+default)\s*=?\s*\{[^{}]*?theme\s*:\s*\{[^{}]*?'
        r'extend\s*:\s*(\{(?:[^{}]|\{[^{}]*\})*\})',
        text,
        re.DOTALL,
    )
    if m:
        # 嘗試把 JS object literal 變 JSON：把 unquoted key 加引號 + 單引號改雙引號
        js_obj = m.group(1)
        # unquoted key: { key: ... }
        normalized = re.sub(r'([{,]\s*)([a-zA-Z_$][a-zA-Z0-9_$-]*)\s*:', r'\1"\2":', js_obj)
        # 單引號字串
        normalized = re.sub(r"'([^']*)'", r'"\1"', normalized)
        # trailing comma
        normalized = re.sub(r',\s*([}\]])', r'\1', normalized)
        try:
            return json.loads(normalized)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"[error] failed to parse extracted theme.extend: {e}\n")
            return None
    return None


def _emit_simple(category: str, items: dict[str, str]) -> list[str]:
    """簡單 category（colors/spacing/borderRadius/lineHeight/fontWeight）→ flat CSS variables。"""
    prefix = V3_TO_V4_PREFIX[category]
    flat = _flatten(items)
    lines = []
    for key, value in flat.items():
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        lines.append(f"  {prefix}-{key}: {value};")
    return lines


def _emit_font_size(items: dict) -> list[str]:
    """fontSize 特殊處理：value 可能是 string 或 [size, { lineHeight, letterSpacing }]"""
    prefix = V3_TO_V4_PREFIX["fontSize"]
    lh_prefix = V3_TO_V4_PREFIX["lineHeight"]
    lines = []
    for key, value in items.items():
        if isinstance(value, list) and len(value) >= 1:
            size = value[0]
            lines.append(f"  {prefix}-{key}: {size};")
            if len(value) >= 2 and isinstance(value[1], dict):
                meta = value[1]
                if "lineHeight" in meta:
                    lines.append(f"  {lh_prefix}-{key}: {meta['lineHeight']};")
                if "letterSpacing" in meta:
                    lines.append(f"  --letter-spacing-{key}: {meta['letterSpacing']};")
        else:
            lines.append(f"  {prefix}-{key}: {value};")
    return lines


def _emit_font_family(items: dict) -> list[str]:
    """fontFamily 特殊處理：value 通常是 list（fallback chain）。"""
    prefix = V3_TO_V4_PREFIX["fontFamily"]
    lines = []
    for key, value in items.items():
        if isinstance(value, list):
            joined = ", ".join(
                f'"{v}"' if isinstance(v, str) and " " in v else str(v) for v in value
            )
        else:
            joined = str(value)
        lines.append(f"  {prefix}-{key}: {joined};")
    return lines


def convert(config: dict) -> str:
    """主入口：v3 config object → v4 @theme {} CSS 片段"""
    lines = ["@theme {"]
    # 順序：colors → fontFamily → fontSize → fontWeight → lineHeight → spacing → borderRadius
    ORDER = ["colors", "fontFamily", "fontSize", "fontWeight",
             "lineHeight", "spacing", "borderRadius"]
    for category in ORDER:
        items = config.get(category)
        if not items:
            continue
        if category == "fontSize":
            lines.extend(_emit_font_size(items))
        elif category == "fontFamily":
            lines.extend(_emit_font_family(items))
        else:
            lines.extend(_emit_simple(category, items))
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Convert Tailwind v3 theme.extend config to v4 @theme {} CSS",
    )
    parser.add_argument("--in", dest="input", required=True,
                        help="輸入 JSON / JS config 檔（npx @google/design.md export --format tailwind）")
    parser.add_argument("--out", dest="output", default=None,
                        help="輸出 CSS 檔（預設 stdout）")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.is_file():
        sys.stderr.write(f"[error] input not found: {in_path}\n")
        return 1
    text = in_path.read_text(encoding="utf-8")
    config = _extract_config_object(text)
    if not config:
        sys.stderr.write("[error] 無法解析 input；請確認是純 JSON 或標準 JS module 格式\n")
        return 1
    css = convert(config)
    if args.output:
        Path(args.output).write_text(css, encoding="utf-8")
        sys.stderr.write(f"[info] ✓ 寫入 {args.output} ({len(css)} bytes)\n")
    else:
        sys.stdout.write(css)
    return 0


if __name__ == "__main__":
    sys.exit(main())
