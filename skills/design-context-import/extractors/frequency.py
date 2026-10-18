"""frequency.py — 兜底 extractor，掃 *.css/scss/jsx 抓出現頻率最高的 color / spacing

當 tailwind / css_vars / scss_vars 都抽不到時，至少能給 LLM 一個 baseline。

策略：
- 掃所有 *.{css,scss,jsx,tsx,vue} 檔
- 抽：
  - hex color（#abc / #abcdef / #abcdef88）
  - rgb()/rgba()/hsl()/hsla()
  - 數字 + px/rem 單位（spacing 候選）
- 統計頻率，取 top N（colors top 8、spacing top 8）
- 自動命名（color-1 / color-2 / spacing-xs / spacing-sm 等）

Part of design-context-import skill (fe-design v1.2.2 §10 P2.5)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .css_vars import SKIP_DIRS

SCAN_EXTS = ("css", "pcss", "postcss", "scss", "sass", "jsx", "tsx", "vue", "svelte")

COLOR_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|"
    r"\brgba?\([^)]+\)|"
    r"\bhsla?\([^)]+\)",
)

SPACING_RE = re.compile(r"\b(\d+(?:\.\d+)?)(px|rem)\b")

MIN_FREQ = 3
TOP_N_COLORS = 8
TOP_N_SPACING = 8


def _iter_files(root: Path):
    for ext in SCAN_EXTS:
        for f in root.glob(f"**/*.{ext}"):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            yield f


def _normalize_color(c: str) -> str:
    """正規化 hex 顏色為小寫；3 位 hex 展開為 6 位以避免重複計數。"""
    c = c.strip().lower()
    if re.match(r"^#[0-9a-f]{3}$", c):
        return "#" + "".join(ch * 2 for ch in c[1:])
    return c


def _name_spacing(value_px: float) -> str:
    """依 px 值給 spacing token 名（xs/sm/md/lg/xl）。"""
    if value_px <= 4:
        return "xs"
    if value_px <= 8:
        return "sm"
    if value_px <= 16:
        return "md"
    if value_px <= 32:
        return "lg"
    if value_px <= 64:
        return "xl"
    return "xxl"


def extract(root: Path) -> dict[str, dict[str, str]]:
    """主入口。回傳 frequency-based fallback tokens。"""
    color_counter: Counter[str] = Counter()
    spacing_counter: Counter[float] = Counter()

    for f in _iter_files(root):
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for c in COLOR_RE.findall(text):
            color_counter[_normalize_color(c)] += 1
        for num, unit in SPACING_RE.findall(text):
            try:
                value = float(num)
            except ValueError:
                continue
            # 統一轉 px（rem 假設 16px base）
            px_value = value * 16 if unit == "rem" else value
            # 跳過異常值
            if 0 < px_value <= 256:
                spacing_counter[round(px_value)] += 1

    result: dict[str, dict[str, str]] = {}

    # Colors
    top_colors = [
        (c, freq) for c, freq in color_counter.most_common(TOP_N_COLORS)
        if freq >= MIN_FREQ
    ]
    if top_colors:
        colors: dict[str, str] = {}
        for i, (color, _freq) in enumerate(top_colors, 1):
            colors[f"frequency-{i}"] = color
        result["colors"] = colors

    # Spacing — 依大小分配 token name；同一 size bucket 多個 px 值取最頻繁
    top_spacing = [
        (px, freq) for px, freq in spacing_counter.most_common(TOP_N_SPACING)
        if freq >= MIN_FREQ
    ]
    if top_spacing:
        spacing: dict[str, str] = {}
        used_names: dict[str, int] = {}
        for px, _freq in top_spacing:
            base_name = _name_spacing(px)
            count = used_names.get(base_name, 0)
            name = base_name if count == 0 else f"{base_name}-{count + 1}"
            used_names[base_name] = count + 1
            spacing[name] = f"{int(px)}px"
        result["spacing"] = spacing

    return result


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(
        description="Frequency-based fallback token extractor"
    )
    parser.add_argument("--root", default=".", help="Project root")
    args = parser.parse_args()
    print(json.dumps(extract(Path(args.root)), indent=2, ensure_ascii=False))
