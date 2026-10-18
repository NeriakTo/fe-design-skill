"""framework_detector.py — 偵測前端專案技術棧版本

讀取 package.json + tailwind.config.* + lock files，產出可寫入 DESIGN.md
`## Framework Context` section 的 dict。

Part of design-context-import skill (fe-design v1.2.2 §10 P2.6)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# 主要可偵測的依賴套件對應表（package.json 內的 key）
REACT_PKG = "react"
NEXT_PKG = "next"
TS_PKG = "typescript"
TAILWIND_PKG = "tailwindcss"
VITE_PKG = "vite"

# Lock file → package manager 對照
LOCK_TO_PM = {
    "pnpm-lock.yaml": "pnpm",
    "yarn.lock": "yarn",
    "bun.lockb": "bun",
    "bun.lock": "bun",
    "package-lock.json": "npm",
}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _extract_major(version: str) -> str | None:
    """從 npm version 字串抽 major version。

    範例：
      ^19.0.0 → 19
      ~5.7.2  → 5.7（保留 minor 因 TypeScript 慣例）
      18.3.1  → 18
      workspace:*, link:..., 等 → None
    """
    if not isinstance(version, str):
        return None
    # 跳過 workspace / link / file / git 協定
    if re.match(r"^(workspace|link|file|git|http|github):", version):
        return None
    # 抽 leading semver
    m = re.search(r"(\d+)(?:\.(\d+))?", version)
    if not m:
        return None
    return f"{m.group(1)}.{m.group(2)}" if m.group(2) and m.group(1) == "5" else m.group(1)


def _resolve_pkg_version(pkg_json: dict[str, Any], pkg: str) -> str | None:
    """從 dependencies / devDependencies 找指定套件的 major version。"""
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        deps = pkg_json.get(section) or {}
        if pkg in deps:
            return _extract_major(deps[pkg])
    return None


def detect_pkg_manager(root: Path) -> str:
    """依 lock file 判斷 package manager；無 lock 則回 'npm' 為 fallback。"""
    for lock_name, pm in LOCK_TO_PM.items():
        if (root / lock_name).is_file():
            return pm
    return "npm"


def detect_nodejs(root: Path) -> str | None:
    """依優先序：.nvmrc → .node-version → package.json engines.node。"""
    nvmrc = root / ".nvmrc"
    if nvmrc.is_file():
        try:
            content = nvmrc.read_text(encoding="utf-8").strip().lstrip("v")
            major = _extract_major(content)
            if major:
                return major
        except OSError:
            pass
    nv = root / ".node-version"
    if nv.is_file():
        try:
            content = nv.read_text(encoding="utf-8").strip().lstrip("v")
            major = _extract_major(content)
            if major:
                return major
        except OSError:
            pass
    pkg_json = _read_json(root / "package.json")
    if pkg_json:
        engines = pkg_json.get("engines") or {}
        node_spec = engines.get("node")
        if isinstance(node_spec, str):
            return _extract_major(node_spec)
    return None


def detect_tailwind(root: Path, pkg_json: dict[str, Any] | None) -> str:
    """偵測 Tailwind major 版本（v3 / v4 / none）。

    v4 偵測優先序：
      1. tailwind.config.* 內含 `@import "tailwindcss"` 或 `@theme {}` → v4
      2. package.json tailwindcss ^4 → v4
      3. tailwind.config.js + module.exports + theme.extend → v3
      4. 無 → none
    """
    # 先看 package.json 的版本
    if pkg_json:
        v = _resolve_pkg_version(pkg_json, TAILWIND_PKG)
        if v:
            return f"v{v}"
    # 看 config 檔內容
    for fname in ("tailwind.config.js", "tailwind.config.ts", "tailwind.config.mjs",
                  "tailwind.config.cjs"):
        f = root / fname
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8")
                if "@theme" in content or '@import "tailwindcss"' in content:
                    return "v4"
                if "module.exports" in content or "export default" in content:
                    return "v3"
            except OSError:
                pass
    # 看是否有 v4 入口 CSS（任何 .css / .pcss 檔含 @import "tailwindcss"）
    for ext in ("css", "pcss", "postcss"):
        for css_file in root.glob(f"**/*.{ext}"):
            # 跳過 node_modules / dist / .next
            if any(part in (".next", "node_modules", "dist", "build", ".turbo")
                   for part in css_file.parts):
                continue
            try:
                head = css_file.read_text(encoding="utf-8", errors="ignore")[:500]
                if '@import "tailwindcss"' in head or "@import 'tailwindcss'" in head:
                    return "v4"
            except OSError:
                pass
    return "none"


def detect_vite(pkg_json: dict[str, Any] | None) -> str | None:
    if not pkg_json:
        return None
    v = _resolve_pkg_version(pkg_json, VITE_PKG)
    return v


def detect_app_router(root: Path) -> bool:
    """Next.js 是否用 App Router（src/app/ 或 app/ 目錄存在）。"""
    return (root / "app").is_dir() or (root / "src" / "app").is_dir()


def detect_framework_context(root: Path) -> dict[str, str]:
    """主入口：產出可寫入 DESIGN.md `## Framework Context` 的 dict。

    Returns:
      dict with required keys (react/next/tailwind/typescript/nodejs/pkg_manager)
      and optional keys (vite/app_router) if偵測到。
    """
    root = root.resolve()
    pkg_json = _read_json(root / "package.json")
    ctx: dict[str, str] = {}

    if pkg_json:
        react_v = _resolve_pkg_version(pkg_json, REACT_PKG)
        ctx["react"] = react_v if react_v else "none"
        next_v = _resolve_pkg_version(pkg_json, NEXT_PKG)
        ctx["next"] = next_v if next_v else "none"
        ts_v = _resolve_pkg_version(pkg_json, TS_PKG)
        ctx["typescript"] = ts_v if ts_v else "none"
    else:
        ctx["react"] = "none"
        ctx["next"] = "none"
        ctx["typescript"] = "none"

    ctx["tailwind"] = detect_tailwind(root, pkg_json)
    nodejs = detect_nodejs(root)
    ctx["nodejs"] = nodejs if nodejs else "none"
    ctx["pkg_manager"] = detect_pkg_manager(root)

    # 選填 key
    vite_v = detect_vite(pkg_json)
    if vite_v:
        ctx["vite"] = vite_v
    if ctx["next"] != "none" and detect_app_router(root):
        ctx["app_router"] = "true"

    return ctx


def render_section(ctx: dict[str, str]) -> str:
    """把偵測結果格式化為 markdown section 字串。"""
    # 必填 key 先列，選填 key 後列
    REQUIRED_ORDER = ["react", "next", "tailwind", "typescript", "nodejs", "pkg_manager"]
    OPTIONAL_ORDER = ["vite", "app_router", "rsc", "bundler"]
    lines = ["## Framework Context"]
    for key in REQUIRED_ORDER:
        if key in ctx:
            lines.append(f"- {key}: {ctx[key]}")
    for key in OPTIONAL_ORDER:
        if key in ctx:
            lines.append(f"- {key}: {ctx[key]}")
    # 額外的未列入 ORDER 的 key（forward compatibility）
    listed = set(REQUIRED_ORDER) | set(OPTIONAL_ORDER)
    for key, val in ctx.items():
        if key not in listed:
            lines.append(f"- {key}: {val}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Detect framework context for a project root")
    parser.add_argument("--root", default=".", help="Project root to scan")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()
    ctx = detect_framework_context(Path(args.root))
    if args.format == "json":
        print(json.dumps(ctx, indent=2, ensure_ascii=False))
    else:
        print(render_section(ctx), end="")
