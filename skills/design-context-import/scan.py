"""scan.py — design-context-import 主程式

掃描既有 codebase → 抽 design tokens（4 個 extractor 並行）→ 偵測 framework context
→ 輸出 `.design/DESIGN.md`（Google YAML frontmatter + Markdown body + ## Framework Context section）

Part of design-context-import skill (fe-design v1.2.2 §10 P2.8)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Make extractors importable when run as script
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from extractors import tailwind, css_vars, scss_vars, frequency, framework_detector  # noqa: E402

# Category 寫入 DESIGN.md frontmatter 的順序（依 Google design.md spec）
FRONTMATTER_ORDER = ("colors", "typography", "rounded", "spacing", "components")

# Extractor → category mapping（部分 extractor 用 fontSize/borderRadius，但 spec 用 typography/rounded）
SPEC_CATEGORY_MAP = {
    "colors": "colors",
    "spacing": "spacing",
    "borderRadius": "rounded",
    # typography 是合成欄位，包含 fontSize/lineHeight/fontFamily/fontWeight
}


def merge_tokens(
    sources: list[tuple[str, dict[str, dict[str, str]]]],
) -> dict[str, dict[str, str]]:
    """合併多個 extractor 結果；前者優先，後者只填前者缺的 key。

    sources: [(name, tokens), ...] — name 用於除錯，tokens 是 extract() 回傳格式
    """
    merged: dict[str, dict[str, str]] = {}
    for _name, tokens in sources:
        for category, items in tokens.items():
            existing = merged.setdefault(category, {})
            for key, value in items.items():
                if key not in existing:
                    existing[key] = value
    return merged


def synthesize_typography(merged: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """把 fontSize / lineHeight / fontFamily / fontWeight 合成 Google spec 的 typography 結構。

    Google typography format:
      typography:
        body-md:
          fontFamily: Inter
          fontSize: 16px
          lineHeight: 1.6

    我們的 extractor 抽出來是分散的（fontSize-body-md, lineHeight-body-md, ...）
    這裡用「token name 的 base」配對；單一 fontSize/lineHeight 也輸出。
    """
    typography: dict[str, dict[str, str]] = {}
    sizes = merged.get("fontSize", {})
    line_heights = merged.get("lineHeight", {})
    families = merged.get("fontFamily", {})
    weights = merged.get("fontWeight", {})
    # 以 fontSize 為主軸（typography 的核心是 size）
    for name, size in sizes.items():
        entry: dict[str, str] = {"fontSize": size}
        if name in line_heights:
            entry["lineHeight"] = line_heights[name]
        if name in families:
            entry["fontFamily"] = families[name]
        if name in weights:
            entry["fontWeight"] = weights[name]
        typography[name] = entry
    return typography


def render_yaml_frontmatter(merged: dict[str, dict[str, str]], project_name: str) -> str:
    """產出 Google design.md 格式的 YAML frontmatter。

    手刻 YAML（不用 PyYAML 避免 dependency）— 結構簡單，安全。
    """
    lines = ["---"]
    lines.append("version: alpha")
    lines.append(f"name: {project_name}")
    # colors
    if merged.get("colors"):
        lines.append("colors:")
        for key, val in merged["colors"].items():
            lines.append(f'  {key}: "{val}"')
    # typography（合成）
    typography = synthesize_typography(merged)
    if typography:
        lines.append("typography:")
        for name, entry in typography.items():
            lines.append(f"  {name}:")
            for k, v in entry.items():
                lines.append(f'    {k}: "{v}"')
    # rounded
    if merged.get("borderRadius"):
        lines.append("rounded:")
        for key, val in merged["borderRadius"].items():
            lines.append(f"  {key}: {val}")
    # spacing
    if merged.get("spacing"):
        lines.append("spacing:")
        for key, val in merged["spacing"].items():
            lines.append(f"  {key}: {val}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def render_markdown_body(merged: dict[str, dict[str, str]], project_name: str) -> str:
    """產出 Markdown body 段（Overview + 各 section 的人讀說明）。"""
    sections = [
        f"# {project_name} — Design System",
        "",
        "## Overview",
        f"由 design-context-import 自動掃描既有 codebase 抽取，作為 `.design/DESIGN.md` 單一可信來源。",
        "可由 `npx @google/design.md@0.1.1 lint` 反向驗證結構正確。",
        "",
    ]
    if merged.get("colors"):
        sections.extend([
            "## Colors",
            f"色彩 token 共 {len(merged['colors'])} 個。Primary / Secondary / Surface / On-surface 為核心；",
            "其餘為品牌延伸色。需保持 WCAG AA 對比（>= 4.5:1）。",
            "",
        ])
    if synthesize_typography(merged):
        sections.extend([
            "## Typography",
            "字體 hierarchy 應有 display / headline / body / label 四層；",
            "避免全站單一字重（trope-15）。",
            "",
        ])
    if merged.get("spacing"):
        sections.extend([
            "## Spacing",
            "8pt grid 為基準；xs(4) / sm(8) / md(16) / lg(32) / xl(64)。",
            "",
        ])
    if merged.get("borderRadius"):
        sections.extend([
            "## Shapes",
            "圓角 token；避免全站 rounded-lg+（trope-06）。",
            "",
        ])
    sections.extend([
        "## Components",
        "（components 為 starter 維護，不從程式碼自動抽取）",
        "",
        "## Do's and Don'ts",
        "- ✅ 使用 token 取代 inline 顏色／字級／間距",
        "- ✅ 對比度遵守 WCAG AA",
        "- ❌ 不使用 16 條 anti-slop trope（見 anti-slop-review skill）",
        "",
    ])
    return "\n".join(sections)


def render_framework_section(ctx: dict[str, str]) -> str:
    """產出 ## Framework Context section（沿用 framework_detector.render_section）。"""
    return framework_detector.render_section(ctx)


KIND_LABEL = {
    "palette": "palette",
    "palette-dark": "palette dark",
    "dark": "dark mode",
}


def render_theme_variants_section(variants) -> str:
    """產出 ## Theme Variants section（只列覆寫規模，不複製各主題數值）。

    刻意不逐值輸出：數值的 canonical 是原始 CSS，複製一份進 DESIGN.md 會變成
    第二個會漂移的來源。此節只回答「有哪些主題、各覆寫多少個 token、在哪一行」。
    """
    if not variants:
        return ""
    palettes = [v for v in variants if v.kind == "palette"]
    palette_darks = [v for v in variants if v.kind == "palette-dark"]
    darks = [v for v in variants if v.kind == "dark"]
    summary_bits = []
    if palettes:
        summary_bits.append(f"{len(palettes)} 組 `[data-theme]` palette")
    if palette_darks:
        summary_bits.append(f"{len(palette_darks)} 組逐 palette 深色覆寫")
    if darks:
        summary_bits.append(f"{len(darks)} 組全域深色覆寫")
    lines = [
        "## Theme Variants",
        f"偵測到 {'、'.join(summary_bits)}。上方 frontmatter 的 token 值是 base"
        "（`@theme` / `:root`）。",
        "下表只記各變體覆寫了多少個 token 與出處；數值一律以原始 CSS 為準，"
        "不在本檔複製，避免形成第二來源。",
        "",
        "| 變體 | 選擇器 | 覆寫 token 數 | 來源 |",
        "|---|---|---|---|",
    ]
    for v in variants:
        label = KIND_LABEL.get(v.kind, v.kind)
        name = label if v.kind == "dark" else f"{label}: {v.name}"
        selector = "、".join(f"`{s}`" for s in v.selectors)
        count = str(v.token_count)
        if v.unclassified_count:
            count += f"（另有 {v.unclassified_count} 個未分類自訂屬性）"
        source = "、".join(f"`{s}`" for s in v.sources)
        lines.append(f"| {name} | {selector} | {count} | {source} |")
    lines.append("")
    return "\n".join(lines)


def assemble_design_md(
    merged: dict[str, dict[str, str]],
    framework_ctx: dict[str, str],
    project_name: str,
    variants=(),
) -> str:
    """組合完整 DESIGN.md 內容。"""
    parts = [
        render_yaml_frontmatter(merged, project_name),
        "",
        render_markdown_body(merged, project_name),
    ]
    variants_section = render_theme_variants_section(variants)
    if variants_section:
        parts.append(variants_section)
    parts.append(render_framework_section(framework_ctx))
    return "\n".join(parts)


def detect_project_name(root: Path) -> str:
    """從 package.json 或 dir name 取專案名。"""
    try:
        import json
        pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
        name = pkg.get("name")
        if isinstance(name, str) and name.strip():
            # 去 scope 前綴 @org/
            return name.split("/")[-1]
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return root.resolve().name


def run_extractors(
    root: Path, skip: set[str],
) -> tuple[list[tuple[str, dict[str, dict[str, str]]]], list]:
    """並行跑 4 個 extractor，回傳 ([(name, tokens), ...] 依優先序, theme 變體清單)。

    theme 變體來自 css_vars（palette / dark 覆寫區塊），不併入 token 合併流程。
    """
    variants_holder: dict[str, list] = {}

    def css_vars_task(target: Path) -> dict[str, dict[str, str]]:
        tokens, variants = css_vars.extract_detailed(target)
        variants_holder["css_vars"] = variants
        return tokens

    tasks = [
        ("tailwind", tailwind.extract),
        ("css_vars", css_vars_task),
        ("scss_vars", scss_vars.extract),
        ("frequency", frequency.extract),
    ]
    tasks = [(name, fn) for name, fn in tasks if name not in skip]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(fn, root): name for name, fn in tasks}
        results: dict[str, dict[str, dict[str, str]]] = {}
        for fut in futures:
            name = futures[fut]
            try:
                results[name] = fut.result()
            except Exception as e:  # noqa: BLE001 — 容錯：個別 extractor 失敗不該拖垮主流程
                sys.stderr.write(f"[warn] extractor {name} failed: {e}\n")
                results[name] = {}
    # 維持原 priority 順序
    return ([(name, results.get(name, {})) for name, _ in tasks],
            variants_holder.get("css_vars", []))


def main():
    parser = argparse.ArgumentParser(
        description="design-context-import — 掃描專案抽 design tokens + framework context",
    )
    parser.add_argument("--root", default=".", help="專案根目錄（預設 .）")
    parser.add_argument(
        "--out", default=".design",
        help="輸出目錄，相對路徑一律以「目前工作目錄」解析（不是 --root）。"
             "預設 .design/；要寫進被掃描的專案請用 --out <root>/.design 或先 cd 過去",
    )
    parser.add_argument("--name", default=None, help="專案名稱（預設從 package.json 抽）")
    parser.add_argument("--dry-run", action="store_true", help="只印不寫檔")
    parser.add_argument("--skip-tailwind", action="store_true")
    parser.add_argument("--skip-css", action="store_true", help="跳過 css_vars extractor")
    parser.add_argument("--skip-scss", action="store_true")
    parser.add_argument("--skip-frequency", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        sys.stderr.write(f"[error] root not a directory: {root}\n")
        return 1

    skip: set[str] = set()
    if args.skip_tailwind: skip.add("tailwind")
    if args.skip_css:      skip.add("css_vars")
    if args.skip_scss:     skip.add("scss_vars")
    if args.skip_frequency: skip.add("frequency")

    project_name = args.name or detect_project_name(root)
    sys.stderr.write(f"[info] scanning project: {project_name} ({root})\n")

    sources, variants = run_extractors(root, skip)
    for name, tokens in sources:
        category_count = len(tokens)
        token_count = sum(len(v) for v in tokens.values())
        sys.stderr.write(f"[info] {name:10s}: {category_count} categories / {token_count} tokens\n")
    if variants:
        sys.stderr.write(
            f"[info] theme     : {len(variants)} 個 palette／dark 覆寫區塊"
            f"（{', '.join(f'{v.name}={v.token_count}' for v in variants)}）\n"
        )

    merged = merge_tokens(sources)
    framework_ctx = framework_detector.detect_framework_context(root)

    design_md = assemble_design_md(merged, framework_ctx, project_name, variants)

    if args.dry_run:
        sys.stdout.write(design_md)
        sys.stderr.write("[info] --dry-run: 未寫檔\n")
        return 0

    # --out 一律以「目前工作目錄」解析（不是 --root）：
    # 舊行為把相對路徑接在 --root 底下，會在掃描別人的 repo 時把輸出寫進對方工作樹。
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "DESIGN.md"
    out_file.write_text(design_md, encoding="utf-8")
    sys.stderr.write(f"[info] ✓ 寫入 {out_file} ({len(design_md)} bytes)\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
