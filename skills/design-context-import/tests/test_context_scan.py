"""test_scan.py — scan.py 的輸出路徑與 Theme Variants section 測試（stdlib unittest）

重點守兩件事：
1. `--out` 的相對路徑以「目前工作目錄」解析，不會寫進被掃描的 repo。
2. palette／dark 變體只出摘要（主題清單＋覆寫 token 數），不逐值複製。

執行：python3 -m unittest discover -s ~/.claude/skills/design-context-import/tests -t ...
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

import scan  # noqa: E402
from extractors import css_vars  # noqa: E402

V4_CSS = """@import "tailwindcss";

@theme {
  --color-primary: #6366F1;
  --color-surface: #FFFFFF;
  --spacing-sidebar: 240px;
}

[data-theme="warm"] {
  --color-primary: #C9542A;
  --color-surface: #FCFAF3;
}

html.dark {
  --color-primary: #818CF8;
}
"""


def make_project(tmp: str) -> Path:
    root = Path(tmp)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "globals.css").write_text(V4_CSS, encoding="utf-8")
    (root / "package.json").write_text('{"name": "fixture-app"}', encoding="utf-8")
    return root


class OutPathTest(unittest.TestCase):
    """`--out` 相對路徑必須落在 cwd，不得落進 --root 指的專案。"""

    def test_relative_out_resolves_against_cwd(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as cwd:
            root = make_project(proj)
            result = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "scan.py"),
                 "--root", str(root), "--out", "w3-out"],
                cwd=cwd, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(cwd) / "w3-out" / "DESIGN.md").is_file())
            self.assertFalse((root / "w3-out").exists())

    def test_default_out_does_not_touch_scanned_repo(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as cwd:
            root = make_project(proj)
            result = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "scan.py"), "--root", str(root)],
                cwd=cwd, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(cwd) / ".design" / "DESIGN.md").is_file())
            self.assertFalse((root / ".design").exists())

    def test_absolute_out_unchanged(self):
        with tempfile.TemporaryDirectory() as proj, tempfile.TemporaryDirectory() as out:
            root = make_project(proj)
            result = subprocess.run(
                [sys.executable, str(SKILL_ROOT / "scan.py"),
                 "--root", str(root), "--out", str(Path(out) / "abs")],
                cwd=out, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((Path(out) / "abs" / "DESIGN.md").is_file())


class ThemeVariantsSectionTest(unittest.TestCase):
    """Theme Variants section：只出摘要，不出數值。"""

    def _design_md(self, root: Path) -> str:
        sources, variants = scan.run_extractors(root, skip={"frequency"})
        merged = scan.merge_tokens(sources)
        return scan.assemble_design_md(merged, {}, "fixture-app", variants)

    def test_section_lists_palette_and_dark(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            doc = self._design_md(root)
        self.assertIn("## Theme Variants", doc)
        self.assertIn("palette: warm", doc)
        self.assertIn("dark mode", doc)
        self.assertIn('`[data-theme="warm"]`', doc)

    def test_section_omits_variant_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_project(tmp)
            doc = self._design_md(root)
        section = doc.split("## Theme Variants", 1)[1]
        for value in ("#C9542A", "#FCFAF3", "#818CF8"):
            self.assertNotIn(value, section)
        self.assertIn("#6366F1", doc)  # base 值仍在 frontmatter

    def test_no_section_when_no_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.css").write_text(":root { --color-primary: #111111; }", encoding="utf-8")
            doc = self._design_md(root)
        self.assertNotIn("## Theme Variants", doc)

    def test_render_helper_reports_counts(self):
        variant = css_vars.ThemeVariant(kind=css_vars.SCOPE_PALETTE, name="warm")
        variant.selectors.append('[data-theme="warm"]')
        variant.sources.append("globals.css:229")
        variant.tokens.update({("colors", f"t{i}") for i in range(31)})
        variant.declarations.update({f"color-t{i}" for i in range(31)})
        section = scan.render_theme_variants_section([variant])
        self.assertIn("| palette: warm |", section)
        self.assertIn("| 31 |", section)
        self.assertIn("`globals.css:229`", section)


if __name__ == "__main__":
    unittest.main()
