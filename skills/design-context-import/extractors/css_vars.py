r"""css_vars.py — 從 CSS 自訂屬性抽 design tokens（含 Tailwind v4 CSS-first 語法）

次優 extractor — 用於沒有 tailwind config 的專案（Tailwind v4 一律屬於此類：
v4 CSS-first 不再產生 `tailwind.config.*`，token 全部寫在 CSS 裡）。

認得的 token 宣告區塊：

| 選擇器 | 語意 | 進 frontmatter |
|---|---|---|
| `:root` / `html` / `html:root` / `*:root` | base token | 是 |
| `@theme` / `@theme inline`（Tailwind v4） | base token | 是 |
| `[data-theme="x"]` | palette 變體覆寫 | 否（只出摘要） |
| `.dark` / `html.dark` / `:root.dark` | 深色模式覆寫 | 否（只出摘要） |
| `[data-theme="x"].dark` / `html.dark[data-theme="x"]` | 逐 palette 深色覆寫 | 否（只出摘要） |

解析策略——**單一字元級狀態掃描器**（`parse_rules()`），一趟同時處理：

- 註解 `/* … */`：只在字串外辨識；字串內的 `/* */` 是字面值
- 字串 `"…"` / `'…'`：只在註解外辨識；字串內的 `; { } /* */` 全部是字面值；
  遇未跳脫換行即終止（CSS §4.3.5 bad-string），不讓沒閉合的引號吃掉整份樣式表
- 跳脫 `\x`：字串內外都認（CSS §4.3.8），`foo\;bar` / `foo\{bar` 不觸發語意
- 括號深度：`url(data:image/svg+xml;base64,…)` 內的 `;` 不切斷宣告
- 大括號層級：產出規則樹，巢狀規則（CSS nesting）的宣告歸屬於**該層**，
  不會被誤算成外層 base token
- 頂層 `;`（如 `@import "tailwindcss";`）結束的是陳述式 at-rule，不是宣告

不要再往這裡疊獨立 regex 補丁：註解、字串、宣告、層級四者互相決定邊界，
分開處理必然在某個組合上破功（2026-07-29 R1 跨模型審查實測四個破口）。

其餘規則：
- 讀檔用 `utf-8-sig`：CSS 允許以 BOM 宣告編碼，留著會讓第一個選擇器變成 `<U+FEFF>:root`
- glob `**/*.{css,pcss,postcss}`，跳過 node_modules / build dirs
- 副檔名優先序 css → pcss → postcss（既有合約，跨副檔名 first-wins 靠它決勝）
- base token 依 prefix 分類為 colors / spacing / fontSize / borderRadius /
  lineHeight / fontFamily / fontWeight
- 每個 unique token 只取第一次出現（base 不會被後面的 palette／dark 覆寫）
- palette 與 dark 區塊**不併入 base**，只回傳摘要（主題名＋覆寫 token 數＋出處），
  避免在 DESIGN.md 內複製出第二份會漂移的 token 來源

Part of design-context-import skill (fe-design v1.2.2 §10 P2.3；W3 補 Tailwind v4)
Copyright 2026 Kevin Du
Licensed under the Apache License, Version 2.0
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

SKIP_DIRS = {"node_modules", "dist", "build", ".next", ".turbo", ".vercel",
             ".cache", "out", ".git", ".pnpm-store"}

# 副檔名優先序：跨副檔名的 first-wins 由此決定，順序不可調
CSS_EXTENSIONS = ("css", "pcss", "postcss")

# CSS variable prefix 分類規則（部分匹配 prefix → 對應 category）
CATEGORY_RULES = [
    (re.compile(r"^(?:color|c)-?", re.I),       "colors"),
    (re.compile(r"^(?:spacing|space|gap)-?", re.I), "spacing"),
    (re.compile(r"^(?:font-size|fs|text)-?", re.I), "fontSize"),
    (re.compile(r"^(?:radius|rounded|r)-?", re.I), "borderRadius"),
    (re.compile(r"^(?:line-height|lh|leading)-?", re.I), "lineHeight"),
    (re.compile(r"^(?:font-family|ff|font)-?(?!size|weight)", re.I), "fontFamily"),
    (re.compile(r"^(?:font-weight|fw)-?", re.I), "fontWeight"),
]

# CSS 換行字元（CSS Syntax L3 §3.3：CR / FF / LF；CRLF 由 CR 先命中）
NEWLINES = "\n\r\f"

# 區塊語意
SCOPE_BASE = "base"
SCOPE_DARK = "dark"
SCOPE_PALETTE = "palette"
SCOPE_PALETTE_DARK = "palette-dark"

_CUSTOM_PROP_RE = re.compile(r"^--([a-zA-Z][a-zA-Z0-9_-]*)\s*:\s*(.*)$", re.DOTALL)
# 屬性選擇器：引號內的 `]` 是字面值
_ATTR_RE = re.compile(r"""\[(?:[^\]"']|"[^"]*"|'[^']*')*\]""")
_DATA_THEME_RE = re.compile(
    r"""\[\s*data-theme\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\]\s"']+))\s*[iIsS]?\s*\]"""
)
_DARK_RE = re.compile(r"\.dark(?![\w-])")
_COMBINATOR_RE = re.compile(r"[ >+~]")
# base 形態允許的元素部分（其後可接任意個 `:root`）
_ELEMENT_RE = re.compile(r"^(html|\*)", re.I)


@dataclass
class Rule:
    """一條 CSS 規則；`declarations` 只含本層，巢狀規則另存 `children`。"""

    selector: str
    line: int
    declarations: list[tuple[str, str]] = field(default_factory=list)
    children: list["Rule"] = field(default_factory=list)


@dataclass
class ThemeVariant:
    """一組 palette／dark 覆寫區塊的摘要（不保存數值，避免第二來源）。"""

    kind: str                                    # palette / dark / palette-dark
    name: str                                    # 主題名；kind=dark 時為 "dark"
    selectors: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)   # "相對路徑:行號"
    tokens: set[tuple[str, str]] = field(default_factory=set)  # (category, token)
    declarations: set[str] = field(default_factory=set)        # 全部 --name
    unclassified: set[str] = field(default_factory=set)        # 分類失敗的 --name

    @property
    def token_count(self) -> int:
        """已分類（會進 design token 體系）的覆寫數量。"""
        return len(self.tokens)

    @property
    def unclassified_count(self) -> int:
        """逐宣告實數：分類失敗的自訂屬性有幾個（不是用去重差額推算）。"""
        return len(self.unclassified)

    def category_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for category, _token in self.tokens:
            counts[category] = counts.get(category, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "name": self.name,
            "selectors": list(self.selectors),
            "sources": list(self.sources),
            "token_count": self.token_count,
            "unclassified_count": self.unclassified_count,
            "categories": self.category_counts(),
        }


# --------------------------------------------------------------------------
# 掃描器
# --------------------------------------------------------------------------

def _string_end(text: str, start: int) -> int:
    """start 指向引號；回傳字串結束後的下一個索引。

    CSS Syntax L3 §4.3.5：字串遇到**未跳脫的換行**即成為 bad-string，到此為止，
    換行本身留給外層繼續解析——不這樣做，一個沒閉合的引號會把後面整份樣式表吃掉。
    跳脫換行（`\\` 接換行）是合法續行，照常吞掉。
    """
    quote = text[start]
    i = start + 1
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "\\":
            i += 2
            continue
        if ch == quote:
            return i + 1
        if ch in NEWLINES:
            return i  # bad-string：不吞換行
        i += 1
    return n


def _flush_declaration(buf: list[str], stack: list[Rule]) -> None:
    """把緩衝區內容當一筆宣告收進目前規則；非自訂屬性與頂層內容一律丟棄。"""
    if not stack:
        return
    text = "".join(buf).strip()
    if not text:
        return
    m = _CUSTOM_PROP_RE.match(text)
    if m:
        stack[-1].declarations.append((m.group(1), m.group(2).strip()))


def parse_rules(text: str) -> list[Rule]:
    """單趟掃描整份樣式表，回傳頂層規則樹。

    同一個狀態機同時追蹤：註解、字串（單／雙引號）、括號深度、大括號層級。
    """
    top: list[Rule] = []
    stack: list[Rule] = []
    buf: list[str] = []
    paren_depth = 0
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # 註解：掃到這裡代表不在字串內，才成立
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            buf.append(" ")  # 註解等同一個空白分隔
            continue
        # 字串：內容原樣保留，裡面的 ; { } /* */ 全是字面值
        if ch in "\"'":
            end = _string_end(text, i)
            buf.append(text[i:end])
            i = end
            continue
        # 字串外的跳脫（CSS Syntax L3 §4.3.8 valid escape）：反斜線後一個字元原樣直通，
        # 不觸發分號／大括號語意。反斜線後接換行不是合法跳脫，當普通字元處理。
        if ch == "\\":
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt and nxt not in NEWLINES:
                buf.append(text[i:i + 2])
                i += 2
                continue
            buf.append(ch)
            i += 1
            continue
        if ch == "(":
            paren_depth += 1
        elif ch == ")":
            paren_depth = max(paren_depth - 1, 0)
        elif ch == "{":
            paren_depth = 0  # 括號未配對時的復原點
            rule = Rule(selector="".join(buf).strip(),
                        line=text.count("\n", 0, i) + 1)
            (stack[-1].children if stack else top).append(rule)
            stack.append(rule)
            buf = []
            i += 1
            continue
        elif ch == "}":
            paren_depth = 0
            _flush_declaration(buf, stack)  # 區塊最後一筆可省略分號
            buf = []
            if stack:
                stack.pop()
            i += 1
            continue
        elif ch == ";" and paren_depth == 0:
            _flush_declaration(buf, stack)  # 頂層 `;` 是陳述式 at-rule，會被丟棄
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    _flush_declaration(buf, stack)  # 檔尾未閉合區塊的最後一筆
    return top


def iter_rules(rules: list[Rule]):
    """深度優先走訪規則樹（含巢狀），維持文件順序。"""
    for rule in rules:
        yield rule
        yield from iter_rules(rule.children)


# --------------------------------------------------------------------------
# 選擇器判定
# --------------------------------------------------------------------------

def _split_selector_list(selector: str) -> list[str]:
    """依頂層逗號拆選擇器清單（括號與引號內的逗號不拆）。"""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    i = 0
    while i < len(selector):
        ch = selector[i]
        if ch in "\"'":
            end = _string_end(selector, i)
            buf.append(selector[i:end])
            i = end
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth <= 0:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return [p.strip() for p in parts if p.strip()]


def _parse_base_shape(remainder: str) -> tuple[str, bool] | None:
    """判定「可選元素＋任意個 `:root`」形態，回傳 (元素, 是否含 :root)。

    收：`:root`、`html`、`html:root`、`*:root`、`:root:root`。
    不收：`body`、`.card`、單獨的 `*`（無 `:root` 的萬用選擇器不是 token 宣告慣例），
    以及任何殘留的 class／id／偽類。
    """
    rest = remainder.strip()
    element = ""
    m = _ELEMENT_RE.match(rest)
    if m:
        element = m.group(1).lower()
        rest = rest[m.end():]
    has_root = False
    while rest.startswith(":root"):
        has_root = True
        rest = rest[len(":root"):]
    if rest:
        return None
    return element, has_root


def _classify_part(part: str) -> tuple[str, str] | None:
    """單一選擇器 → (scope_kind, theme_name)；不是 token 宣告區塊則回 None。"""
    part = re.sub(r"\s+", " ", part).strip()
    if not part:
        return None
    lowered = part.lower()
    if lowered == "@theme" or lowered.startswith("@theme "):
        return SCOPE_BASE, ""
    if part.startswith("@"):
        return None

    attrs = list(_ATTR_RE.finditer(part))
    masked = list(part)
    for m in attrs:
        for idx in range(m.start(), m.end()):
            masked[idx] = "\x00"
    masked_str = "".join(masked)
    if _COMBINATOR_RE.search(masked_str):
        return None  # 後代／子選擇器（如 `html.dark .prose`）不是 token 宣告區塊

    theme = ""
    if len(attrs) > 1:
        return None
    if attrs:
        theme_match = _DATA_THEME_RE.fullmatch(attrs[0].group(0))
        if not theme_match:
            return None  # 其他屬性選擇器語意不明，不當 token 區塊
        theme = next(g for g in theme_match.groups() if g is not None)
        if not theme:
            return None

    remainder = masked_str.replace("\x00", "")
    has_dark = bool(_DARK_RE.search(remainder))
    remainder = _DARK_RE.sub("", remainder)
    shape = _parse_base_shape(remainder)
    if shape is None:
        return None
    element, has_root = shape

    if theme:
        return (SCOPE_PALETTE_DARK if has_dark else SCOPE_PALETTE), theme
    if has_dark:
        return SCOPE_DARK, "dark"
    if has_root or element == "html":
        return SCOPE_BASE, ""
    return None


def classify_selector(selector: str) -> list[tuple[str, str]]:
    """選擇器（可含逗號清單）→ 去重後的 (scope_kind, theme_name) 清單。"""
    scopes: list[tuple[str, str]] = []
    for part in _split_selector_list(selector):
        scope = _classify_part(part)
        if scope and scope not in scopes:
            scopes.append(scope)
    return scopes


# --------------------------------------------------------------------------
# 抽取
# --------------------------------------------------------------------------

def _classify(var_name: str) -> tuple[str, str] | None:
    """把 CSS var 名分類到 category；回傳 (category, token_name) 或 None。"""
    for prefix_re, category in CATEGORY_RULES:
        m = prefix_re.match(var_name)
        if m:
            token_name = var_name[m.end():] or var_name
            return category, token_name
    return None


def _iter_css_files(root: Path):
    """依副檔名優先序（css → pcss → postcss）列檔；此順序即 first-wins 順序。"""
    for ext in CSS_EXTENSIONS:
        for f in root.glob(f"**/*.{ext}"):
            if any(part in SKIP_DIRS for part in f.parts):
                continue
            yield f


def extract_detailed(root: Path) -> tuple[dict[str, dict[str, str]], list[ThemeVariant]]:
    """回傳 (base tokens, palette/dark 變體摘要)。

    base tokens 格式同 `extract()`；變體只帶數量與出處，不帶數值。
    """
    result: dict[str, dict[str, str]] = {}
    seen: set[tuple[str, str]] = set()  # (category, token_name) 只取第一次
    variants: dict[tuple[str, str], ThemeVariant] = {}

    for f in _iter_css_files(root):
        try:
            # utf-8-sig：CSS Syntax L3 允許以 BOM 宣告編碼，只剝掉開頭單一 U+FEFF；
            # 留著它會讓第一個選擇器變成 `<U+FEFF>:root` 而整塊被分類器拒絕。
            text = f.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        try:
            rel = str(f.relative_to(root))
        except ValueError:
            rel = str(f)
        for rule in iter_rules(parse_rules(text)):
            if not rule.declarations:
                continue
            for kind, name in classify_selector(rule.selector):
                if kind == SCOPE_BASE:
                    for var_name, value in rule.declarations:
                        classified = _classify(var_name)
                        if not classified or classified in seen:
                            continue
                        seen.add(classified)
                        category, token_name = classified
                        result.setdefault(category, {})[token_name] = value
                    continue
                key = (kind, name)
                variant = variants.get(key)
                if variant is None:
                    variant = ThemeVariant(kind=kind, name=name)
                    variants[key] = variant
                sel_norm = re.sub(r"\s+", " ", rule.selector).strip()
                if sel_norm not in variant.selectors:
                    variant.selectors.append(sel_norm)
                source = f"{rel}:{rule.line}"
                if source not in variant.sources:
                    variant.sources.append(source)
                for var_name, _value in rule.declarations:
                    variant.declarations.add(var_name)
                    classified = _classify(var_name)
                    if classified:
                        variant.tokens.add(classified)
                    else:
                        variant.unclassified.add(var_name)

    order = {SCOPE_PALETTE: 0, SCOPE_PALETTE_DARK: 1, SCOPE_DARK: 2}
    ordered = sorted(variants.values(), key=lambda v: order.get(v.kind, 9))
    return result, ordered


def extract(root: Path) -> dict[str, dict[str, str]]:
    """主入口。回傳 `{"colors": {...}, "spacing": {...}, ...}`（僅 base token）。"""
    tokens, _variants = extract_detailed(root)
    return tokens


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Extract design tokens from CSS variables")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--variants", action="store_true",
                        help="同時輸出 palette／dark 變體摘要")
    args = parser.parse_args()
    base, theme_variants = extract_detailed(Path(args.root))
    if args.variants:
        payload = {"base": base, "variants": [v.to_dict() for v in theme_variants]}
    else:
        payload = base
    print(json.dumps(payload, indent=2, ensure_ascii=False))
