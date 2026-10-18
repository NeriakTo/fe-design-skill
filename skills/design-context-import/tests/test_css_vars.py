"""test_css_vars.py — css_vars extractor 的區塊辨識回歸測試（stdlib unittest）

涵蓋五種 fixture：`:root`、`@theme`、`[data-theme="x"]`、`html.dark`、
`[data-theme="x"].dark`（W2 前瞻），外加後代選擇器不得誤收的防漏測試。

執行：python3 -m unittest discover -s ~/.claude/skills/design-context-import/tests -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from extractors import css_vars  # noqa: E402


def write_css(tmpdir: str, content: str, name: str = "app.css") -> Path:
    root = Path(tmpdir)
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return root


class RootBlockTest(unittest.TestCase):
    """Fixture 1：`:root` — 既有行為必須不變。"""

    CSS = """
:root {
  --color-primary: #6366F1;
  --color-surface: #FFFFFF;
  --spacing-gutter: 16px;
  --radius-card: 8px;
  --font-body: Inter, sans-serif;
}
"""

    def test_root_tokens_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"], {"primary": "#6366F1", "surface": "#FFFFFF"})
        self.assertEqual(tokens["spacing"], {"gutter": "16px"})
        self.assertEqual(tokens["borderRadius"], {"card": "8px"})
        self.assertEqual(tokens["fontFamily"], {"body": "Inter, sans-serif"})

    def test_first_occurrence_wins(self):
        css = self.CSS + "\n:root { --color-primary: #000000; }\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["primary"], "#6366F1")

    def test_root_inside_media_query_still_found(self):
        css = "@media (min-width: 40rem) { :root { --color-wide: #111111; } }"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["wide"], "#111111")


class ThemeBlockTest(unittest.TestCase):
    """Fixture 2：Tailwind v4 `@theme`（含 `@import` 前導陳述式）。"""

    CSS = """@import "tailwindcss";

@theme {
  --color-primary: #6366F1;
  --color-accent: #0891B2;
  --spacing-sidebar: 240px;
  --radius-bubble: 12px;
  --font-heading: var(--font-space-grotesk), sans-serif;
}
"""

    def test_theme_block_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"], {"primary": "#6366F1", "accent": "#0891B2"})
        self.assertEqual(tokens["spacing"], {"sidebar": "240px"})
        self.assertEqual(tokens["borderRadius"], {"bubble": "12px"})
        self.assertEqual(tokens["fontFamily"],
                         {"heading": "var(--font-space-grotesk), sans-serif"})

    def test_import_statement_does_not_swallow_theme_selector(self):
        """`@import "...";` 若被黏進 prelude，選擇器就不再是 @theme，token 會歸零。"""
        selectors = [r.selector for r in css_vars.iter_rules(css_vars.parse_rules(self.CSS))]
        self.assertIn("@theme", selectors)

    def test_theme_inline_variant(self):
        css = "@theme inline {\n  --color-brand: #ABCDEF;\n}"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["brand"], "#ABCDEF")

    def test_keyframes_not_parsed_as_token_block(self):
        css = self.CSS + """
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
.code-block { --color-should-not-leak: #FF0000; }
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertNotIn("should-not-leak", tokens["colors"])


class DataThemePaletteTest(unittest.TestCase):
    """Fixture 3：`[data-theme="x"]` palette 覆寫。"""

    CSS = """@theme {
  --color-primary: #6366F1;
  --color-surface: #FFFFFF;
}

[data-theme="warm"] {
  --color-primary: #C9542A;
  --color-surface: #FCFAF3;
  --color-accent: #DDA74A;
}

[data-theme='ocean'] {
  --color-primary: #0E6BA8;
}
"""

    def test_palette_does_not_override_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            base, _variants = css_vars.extract_detailed(root)
        self.assertEqual(base["colors"]["primary"], "#6366F1")
        self.assertNotIn("accent", base["colors"])

    def test_palette_recorded_as_variant(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            _base, variants = css_vars.extract_detailed(root)
        by_name = {v.name: v for v in variants}
        self.assertEqual(sorted(by_name), ["ocean", "warm"])
        self.assertEqual(by_name["warm"].kind, css_vars.SCOPE_PALETTE)
        self.assertEqual(by_name["warm"].token_count, 3)
        self.assertEqual(by_name["ocean"].token_count, 1)
        self.assertTrue(by_name["warm"].sources[0].endswith("app.css:6"))


class DarkOverrideTest(unittest.TestCase):
    """Fixture 4：`html.dark` / `.dark` 深色覆寫。"""

    CSS = """:root {
  --color-primary: #6366F1;
  --color-text-primary: #0F172A;
}

html.dark {
  --color-primary: #818CF8;
  --color-text-primary: #F8FAFC;
  --color-surface: #1E1B2E;
}

.dark body, html.dark body {
  background: #000000;
}

html.dark .prose {
  --tw-prose-body: var(--color-text-primary);
  --color-must-not-leak: #FF0000;
}

html.dark img:not([data-no-dim]) {
  filter: brightness(0.9);
}
"""

    def test_dark_recorded_and_base_intact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            base, variants = css_vars.extract_detailed(root)
        self.assertEqual(base["colors"]["primary"], "#6366F1")
        self.assertNotIn("surface", base["colors"])
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].kind, css_vars.SCOPE_DARK)
        self.assertEqual(variants[0].token_count, 3)

    def test_descendant_selector_never_counted(self):
        """`html.dark .prose` 若被誤收，未分類的 --tw-prose-* 會混進 dark 區塊。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            base, variants = css_vars.extract_detailed(root)
        self.assertNotIn("must-not-leak", base.get("colors", {}))
        self.assertEqual(variants[0].unclassified_count, 0)
        self.assertNotIn("tw-prose-body", variants[0].declarations)
        self.assertEqual(variants[0].selectors, ["html.dark"])

    def test_bare_dark_class(self):
        css = ":root { --color-a: #111111; }\n.dark { --color-a: #EEEEEE; }"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            base, variants = css_vars.extract_detailed(root)
        self.assertEqual(base["colors"]["a"], "#111111")
        self.assertEqual(variants[0].kind, css_vars.SCOPE_DARK)


class PaletteDarkCombinationTest(unittest.TestCase):
    """Fixture 5：`[data-theme="x"].dark` 組合選擇器（W2 前瞻）。"""

    CSS = """@theme {
  --color-primary: #6366F1;
}

[data-theme="warm"] {
  --color-primary: #C9542A;
}

[data-theme="warm"].dark {
  --color-primary: #E87A4C;
  --color-surface: #241C17;
}

html.dark[data-theme="ocean"] {
  --color-primary: #38BDF8;
}
"""

    def test_combined_selector_recognised(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            base, variants = css_vars.extract_detailed(root)
        self.assertEqual(base["colors"]["primary"], "#6366F1")
        kinds = {(v.kind, v.name): v for v in variants}
        self.assertIn((css_vars.SCOPE_PALETTE, "warm"), kinds)
        self.assertIn((css_vars.SCOPE_PALETTE_DARK, "warm"), kinds)
        self.assertIn((css_vars.SCOPE_PALETTE_DARK, "ocean"), kinds)
        self.assertEqual(kinds[(css_vars.SCOPE_PALETTE_DARK, "warm")].token_count, 2)

    def test_palette_before_palette_dark_in_output_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, self.CSS)
            _base, variants = css_vars.extract_detailed(root)
        self.assertEqual(variants[0].kind, css_vars.SCOPE_PALETTE)
        self.assertEqual(variants[-1].kind, css_vars.SCOPE_PALETTE_DARK)


class StringAndCommentTest(unittest.TestCase):
    """字串／註解／巢狀層級必須由同一個掃描器處理（R1 維護者實測破口）。"""

    def test_brace_inside_string_value(self):
        css = ':root {\n  --color-brace: "{";\n  --color-after: #111111;\n}'
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["brace"], '"{"')
        self.assertEqual(tokens["colors"]["after"], "#111111")

    def test_semicolon_inside_string_value(self):
        css = ':root {\n  --color-data: "a;b";\n  --color-after: #111111;\n}'
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["data"], '"a;b"')
        self.assertEqual(tokens["colors"]["after"], "#111111")

    def test_comment_literal_inside_string_kept(self):
        css = ':root {\n  --color-literal: "/* literal */";\n}'
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["literal"], '"/* literal */"')

    def test_real_comment_still_removed(self):
        css = ':root {\n  /* --color-ghost: #000000; */\n  --color-real: #111111;\n}'
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertNotIn("ghost", tokens["colors"])
        self.assertEqual(tokens["colors"]["real"], "#111111")

    def test_apostrophe_inside_comment_does_not_open_string(self):
        css = ":root {\n  /* don't break here */\n  --color-real: #111111;\n}"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["real"], "#111111")

    def test_semicolon_inside_parentheses(self):
        css = (':root {\n'
               '  --color-bg: url(data:image/svg+xml;base64,AAAA);\n'
               '  --color-after: #111111;\n}')
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["bg"], "url(data:image/svg+xml;base64,AAAA)")
        self.assertEqual(tokens["colors"]["after"], "#111111")

    def test_nested_rule_declarations_are_not_base(self):
        """CSS nesting：`:root { .component { … } }` 的區域 token 不屬於 base。"""
        css = (':root {\n'
               '  --color-base: #111111;\n'
               '  .component {\n    --color-local: #bad000;\n  }\n'
               '  --color-tail: #222222;\n}')
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["base"], "#111111")
        self.assertEqual(tokens["colors"]["tail"], "#222222")
        self.assertNotIn("local", tokens["colors"])

    def test_nested_palette_inside_theme_scope_not_base(self):
        css = ('@theme {\n  --color-primary: #6366F1;\n}\n'
               '[data-theme="warm"] {\n'
               '  --color-primary: #C9542A;\n'
               '  .badge { --color-inner: #bad000; }\n}')
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            base, variants = css_vars.extract_detailed(root)
        self.assertEqual(base["colors"]["primary"], "#6366F1")
        self.assertNotIn("inner", base["colors"])
        self.assertEqual(variants[0].token_count, 1)


class LegacyRootCompatTest(unittest.TestCase):
    """舊版 `:root\\s*\\{` regex 抽得到的合法選擇器，新版不得漏掉。"""

    def test_html_root_compound(self):
        css = "html:root { --color-a: #111111; }"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["a"], "#111111")

    def test_universal_root_compound(self):
        css = "*:root { --color-a: #111111; }"
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["a"], "#111111")

    def test_cross_extension_priority_css_first(self):
        """既有合約：css → pcss → postcss，跨副檔名先出現者勝，不是全路徑排序。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z.css").write_text(":root { --color-a: #111111; }", encoding="utf-8")
            (root / "a.pcss").write_text(":root { --color-a: #222222; }", encoding="utf-8")
            (root / "a.postcss").write_text(":root { --color-a: #333333; }", encoding="utf-8")
            tokens = css_vars.extract(root)
        self.assertEqual(tokens["colors"]["a"], "#111111")


class UnclassifiedCountTest(unittest.TestCase):
    """unclassified_count 要數「真的沒分類的宣告」，不是靠去重後的差額推。"""

    def test_alias_prefixes_are_not_reported_as_unclassified(self):
        css = (":root { --color-a: #111111; }\n"
               "html.dark { --color-a: #222222; --c-a: #333333; }")
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            _base, variants = css_vars.extract_detailed(root)
        self.assertEqual(variants[0].token_count, 1)
        self.assertEqual(variants[0].unclassified_count, 0)

    def test_genuine_unclassified_counted(self):
        css = (":root { --color-a: #111111; }\n"
               "html.dark { --color-a: #222222; --tw-prose-body: #333333; }")
        with tempfile.TemporaryDirectory() as tmp:
            root = write_css(tmp, css)
            _base, variants = css_vars.extract_detailed(root)
        self.assertEqual(variants[0].token_count, 1)
        self.assertEqual(variants[0].unclassified_count, 1)


class R2BoundaryTest(unittest.TestCase):
    """R2 跨模型審查的十組邊界攻擊（`/tmp/design_context_r2_attack.py`）。

    前四個是 R2 判 FAIL 的紅燈案例，後六個是 R2 已通過、鎖住不得退化的。
    """

    def _colors(self, content: str) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "attack.css").write_bytes(content.encode("utf-8"))
            return css_vars.extract(Path(tmp)).get("colors", {})

    # ---- R2 紅燈 ----

    def test_bom_does_not_swallow_first_rule(self):
        """CSS Syntax L3 允許 BOM 宣告編碼；U+FEFF 不得讓第一個 `:root` 被拒。"""
        # BOM 用跳脫寫法，不放字面 U+FEFF——不可見字元一旦被編輯器清掉，
        # fixture 會退化成普通 `:root` 而讓這個測試假綠。
        colors = self._colors(
            "\ufeff"
            ":root {\r\n  --color-bom: #445566;\r\n}\r\n"
            ":root {\r\n  --color-after: #556677;\r\n}\r\n"
        )
        self.assertEqual(colors.get("bom"), "#445566")
        self.assertEqual(colors.get("after"), "#556677")  # CRLF 回歸鎖

    def test_escaped_semicolon_outside_string(self):
        colors = self._colors(r''':root {
  --color-escaped: foo\;bar;
  --color-after: #667788;
}''')
        self.assertEqual(colors.get("escaped"), r"foo\;bar")
        self.assertEqual(colors.get("after"), "#667788")

    def test_escaped_brace_outside_string(self):
        colors = self._colors(r''':root {
  --color-escaped-brace: foo\{bar;
  --color-after: #718293;
}''')
        self.assertEqual(colors.get("escaped-brace"), r"foo\{bar")
        self.assertEqual(colors.get("after"), "#718293")

    def test_unterminated_string_recovers_later_rule(self):
        """CSS bad-string：未跳脫換行處終止字串，後續規則要能復原。"""
        colors = self._colors(''':root {
  --color-broken: "never closes
  --color-after: #99AABB;
}
:root { --color-later-rule: #AABBCC; }''')
        self.assertEqual(colors.get("later-rule"), "#AABBCC")

    # ---- R2 已通過，鎖住不得退化 ----

    def test_escaped_quotes_and_backslashes(self):
        colors = self._colors(r''':root {
  --color-double: "a\";{b";
  --color-single: 'c\';}d';
  --color-slashes: "x\\\\\";y";
  --color-after: #123456;
}''')
        self.assertEqual(colors.get("after"), "#123456")

    def test_complex_import_then_theme(self):
        colors = self._colors(
            '@import url("data:text/css;charset=utf-8,a;b") layer(base) screen;\n'
            '@theme {\n  --color-import-survives: #112233;\n}'
        )
        self.assertEqual(colors.get("import-survives"), "#112233")

    def test_quoted_url_with_syntax_chars(self):
        colors = self._colors(r''':root {
  --color-image: url("data:image/svg+xml,<svg data-x=';{}/*literal*/'>");
  --color-after: #223344;
}''')
        self.assertEqual(colors.get("after"), "#223344")

    def test_empty_blocks(self):
        colors = self._colors(''':root {}
@theme {/**/}
[data-theme="empty"] {}
:root { --color-after-empty: #334455; }''')
        self.assertEqual(colors.get("after-empty"), "#334455")

    def test_unterminated_comment(self):
        colors = self._colors(''':root {
  --color-before: #778899;
  /* comment never closes
  --color-after: #8899AA;
}''')
        self.assertEqual(colors, {"before": "#778899"})


class SelectorClassificationTest(unittest.TestCase):
    """選擇器分類的邊界條件。"""

    def test_accepted(self):
        cases = {
            ":root": (css_vars.SCOPE_BASE, ""),
            "html": (css_vars.SCOPE_BASE, ""),
            "@theme": (css_vars.SCOPE_BASE, ""),
            ".dark": (css_vars.SCOPE_DARK, "dark"),
            "html.dark": (css_vars.SCOPE_DARK, "dark"),
            ":root.dark": (css_vars.SCOPE_DARK, "dark"),
            '[data-theme="warm"]': (css_vars.SCOPE_PALETTE, "warm"),
            "[data-theme=warm]": (css_vars.SCOPE_PALETTE, "warm"),
            'html[data-theme="warm"]': (css_vars.SCOPE_PALETTE, "warm"),
            '[data-theme="warm"].dark': (css_vars.SCOPE_PALETTE_DARK, "warm"),
        }
        for selector, expected in cases.items():
            with self.subTest(selector=selector):
                self.assertEqual(css_vars.classify_selector(selector), [expected])

    def test_rejected(self):
        for selector in ("body", ".card", "html.dark .prose", "*", ".chat:focus-within",
                         "[data-mode='dark']", "html.dark img:not([data-no-dim])",
                         "@keyframes blink", "@font-face"):
            with self.subTest(selector=selector):
                self.assertEqual(css_vars.classify_selector(selector), [])

    def test_selector_list_splits(self):
        self.assertEqual(
            css_vars.classify_selector(':root, [data-theme="warm"]'),
            [(css_vars.SCOPE_BASE, ""), (css_vars.SCOPE_PALETTE, "warm")],
        )


if __name__ == "__main__":
    unittest.main()
