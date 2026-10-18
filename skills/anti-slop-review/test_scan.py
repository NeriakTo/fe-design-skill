#!/usr/bin/env python3
"""test_scan.py — scan.py + token_resolver.py 測試基線。

覆蓋三層掃描（design-md-lint / trope / 7 sins）+ token resolver + 合併邏輯。
npx / vendored 外部依賴全 mock，確保 CI 環境不需 Node。
"""

from __future__ import annotations

import json
import importlib.util
import sys
import subprocess
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SPEC = importlib.util.spec_from_file_location('anti_slop_scan', Path(__file__).with_name('scan.py'))
scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scan
SPEC.loader.exec_module(scan)


class TestT271Motion:
    @pytest.mark.parametrize('content', [
        '.a { transition: all .2s; }', '.a { transition-property: all; }',
        '.a { TRANSITION : ALL .2s; }', '<div class="transition-all duration-200">',
        '<div class="hover:transition-all md:!transition-all">',
        "const classes = ['transition-all', 'opacity-100'];",
        '.a { transition: opacity .2s, all .3s; }',
    ])
    def test_trope18_bad(self, content):
        hits = [f for f in scan.scan_file_with_tropes(content, scan.load_patterns())
                if f.get('trope_id') == 'trope-18']
        assert len(hits) == 1
        assert hits[0]['severity'] == 'warning'
        assert hits[0]['remediation'] == '明列過渡屬性，例如 transform 與 opacity'

    @pytest.mark.parametrize('content', [
        '.a { transition: transform .2s, opacity .2s; }',
        '.a { transition-property: opacity; }',
        '<div class="transition-all-xxx my-transition-all transition-alligator">',
        'const identifier = transition_all;',
        '.a { --transition: all; custom-transition: all; transition: alligator .2s; }',
        '<div class="transition-all/50">',
    ])
    def test_trope18_good(self, content):
        assert not any(f.get('trope_id') == 'trope-18' for f in
                       scan.scan_file_with_tropes(content, scan.load_patterns()))

    @pytest.mark.parametrize('content', [
        '@keyframes enter { to { opacity: 1; } }',
        '.a { animation: enter .2s; }', '.a { transition: opacity .2s; }',
    ])
    def test_trope19_bad(self, content):
        hits = [f for f in scan.scan_file_with_tropes(content, scan.load_patterns())
                if f.get('trope_id') == 'trope-19']
        assert len(hits) == 1
        assert hits[0]['severity'] == 'info'
        assert '候選，需在瀏覽器切換減少動態設定確認' in hits[0]['trope_name']

    @pytest.mark.parametrize('content', [
        '.a { color: red; }',
        '.a { transition: opacity .2s; } @media (prefers-reduced-motion: reduce) {}',
        '@keyframes enter {} @media (PREFERS-REDUCED-MOTION: reduce) {}',
        '.a { --animation: custom; custom-transition: none; }',
    ])
    def test_trope19_good(self, content):
        assert not any(f.get('trope_id') == 'trope-19' for f in
                       scan.scan_file_with_tropes(content, scan.load_patterns()))

    @pytest.mark.parametrize('trope_id,content', [
        ('trope-18', '.a { transition: all .2s; }'),
        ('trope-19', '.a { animation: enter .2s; }'),
    ])
    def test_skip(self, trope_id, content):
        content = f'<!-- anti-slop-skip: {trope_id} -->\n' + content
        assert not any(f.get('trope_id') == trope_id for f in
                       scan.scan_file_with_tropes(content, scan.load_patterns()))

    def test_catalog(self):
        content = (Path(__file__).parent / 'trope-catalog.md').read_text()
        assert {'trope-18', 'trope-19'} <= scan.parse_skip_markers(content)
        assert not scan.scan_file_with_tropes(content, scan.load_patterns())

    @pytest.mark.parametrize('trope_id,bad,good', [
        ('trope-18', '.a { transition: all .2s; }', '.a { transition: opacity .2s; }'),
        ('trope-19', '.a { animation: enter .2s; }',
         '.a { animation: enter .2s; } @media (prefers-reduced-motion: reduce) {}'),
    ])
    def test_recursive(self, tmp_path, capsys, trope_id, bad, good):
        nested = tmp_path / 'src' / 'nested'
        nested.mkdir(parents=True)
        (nested / 'bad.css').write_text(bad)
        (tmp_path / 'good.vue').write_text(good)
        with patch('sys.argv', ['scan.py', str(tmp_path), '-r',
                                '--skip-design-md-lint', '--format', 'json']):
            assert scan.main() == 0
        results = json.loads(capsys.readouterr().out)['results']
        assert len(results) == 2
        hits = [r for r in results if any(f.get('trope_id') == trope_id
                                        for f in r['findings'])]
        assert len(hits) == 1
        assert Path(hits[0]['target']).name == 'bad.css'


class TestT271Targets:
    @pytest.mark.parametrize('recursive', [False, True])
    def test_extensions(self, tmp_path, recursive):
        extensions = {'.md', '.mdx', '.html', '.htm', '.jsx', '.tsx',
                      '.css', '.scss', '.js', '.mjs', '.ts', '.vue', '.svelte'}
        for ext in extensions:
            (tmp_path / ('sample' + ext.upper())).write_text('')
        (tmp_path / 'asset.png').write_text('')
        assert {p.suffix.lower() for p in scan.collect_targets(tmp_path, recursive)} == extensions

    @pytest.mark.parametrize('excluded', [
        'node_modules', '.git', 'dist', 'build', '.next', 'out', 'coverage',
    ])
    def test_excluded(self, tmp_path, excluded):
        nested = tmp_path / 'src' / excluded / 'nested'
        nested.mkdir(parents=True)
        (nested / 'bad.js').write_text('')
        (tmp_path / 'src' / 'good.js').write_text('')
        assert [p.name for p in scan.collect_targets(tmp_path, True)] == ['good.js']
        assert scan.collect_targets(tmp_path / 'src' / excluded, True) == []


class TestT271Unchecked:
    @pytest.mark.parametrize('output_format', ['text', 'json'])
    def test_reports(self, tmp_path, capsys, output_format):
        target = tmp_path / 'clean.css'
        target.write_text('/* clean */')
        with patch('sys.argv', ['scan.py', str(target), '--skip-design-md-lint',
                                '--severity-min', 'critical', '--format', output_format]):
            assert scan.main() == 0
        output = capsys.readouterr().out
        expected = {'trope-03', 'trope-13', 'trope-15', 'trope-16'}
        if output_format == 'json':
            result = json.loads(output)['results'][0]
            unchecked = result['unchecked_rules']
            assert {r['trope_id'] for r in unchecked} == expected
            assert all(r['status'] == '未實作、未檢查' for r in unchecked)
            assert all(r['type'] == 'structural' for r in unchecked)
            assert result['summary']['total'] == 0
        else:
            assert '未實作、未檢查' in output
            for trope in scan.load_patterns()['tropes']:
                if trope['id'] in expected:
                    assert trope['id'] in output
                    assert trope['name'] in output
from token_resolver import (
    build_resolved_theme,
    check_font_conflict,
    check_indigo_conflict,
    extract_css_tokens,
    extract_style_blocks,
    is_in_token_scope,
    resolve_css_var,
)

FIXTURES_DIR = Path(__file__).parent


# ── helpers ──────────────────────────────────────────────────────────


def load_patterns() -> dict[str, Any]:
    return scan.load_patterns()


@pytest.fixture()
def patterns():
    return load_patterns()


# ── infer_rule_id_from_message ───────────────────────────────────────


class TestInferRuleId:
    def test_orphaned_tokens(self):
        msg = "--accent-light is defined but never referenced by any component"
        assert scan.infer_rule_id_from_message(msg) == "orphaned-tokens"

    def test_contrast_ratio(self):
        msg = "#ffffff has contrast ratio 1.2 below WCAG AA minimum"
        assert scan.infer_rule_id_from_message(msg) == "contrast-ratio"

    def test_missing_primary(self):
        msg = "No 'primary' color defined"
        assert scan.infer_rule_id_from_message(msg) == "missing-primary"

    def test_missing_typography(self):
        msg = "No typography tokens defined"
        assert scan.infer_rule_id_from_message(msg) == "missing-typography"

    def test_section_order(self):
        msg = "'motion' appears before 'colors' which is out of order"
        assert scan.infer_rule_id_from_message(msg) == "section-order"

    def test_broken_ref(self):
        msg = "--foo does not resolve to any defined token"
        assert scan.infer_rule_id_from_message(msg) == "broken-ref"

    def test_broken_ref_alt(self):
        msg = "bar is not a recognized component sub-token"
        assert scan.infer_rule_id_from_message(msg) == "broken-ref"

    def test_missing_sections(self):
        msg = "No 'motion' section defined"
        assert scan.infer_rule_id_from_message(msg) == "missing-sections"

    def test_token_summary(self):
        msg = "Design system defines 24 tokens"
        assert scan.infer_rule_id_from_message(msg) == "token-summary"

    def test_unknown_message(self):
        assert scan.infer_rule_id_from_message("some random text") == ""


# ── parse_skip_markers ───────────────────────────────────────────────


class TestParseSkipMarkers:
    def test_single_skip(self):
        content = "<!-- anti-slop-skip: trope-01 -->"
        assert scan.parse_skip_markers(content) == {"trope-01"}

    def test_multiple_skip(self):
        content = "<!-- anti-slop-skip: trope-01, trope-05, trope-09 -->"
        assert scan.parse_skip_markers(content) == {"trope-01", "trope-05", "trope-09"}

    def test_multiple_markers(self):
        content = "<!-- anti-slop-skip: trope-01 -->\n<!-- anti-slop-skip: trope-02 -->"
        assert scan.parse_skip_markers(content) == {"trope-01", "trope-02"}

    def test_no_markers(self):
        assert scan.parse_skip_markers("<div>hello</div>") == set()

    def test_case_insensitive(self):
        content = "<!-- ANTI-SLOP-SKIP: trope-07 -->"
        assert scan.parse_skip_markers(content) == {"trope-07"}


# ── is_design_md ─────────────────────────────────────────────────────


class TestIsDesignMd:
    def test_valid_design_md(self, tmp_path):
        f = tmp_path / "DESIGN.md"
        f.write_text("---\nname: test\n---\n# Design\n")
        assert scan.is_design_md(f)

    def test_non_frontmatter_md(self, tmp_path):
        f = tmp_path / "README.md"
        f.write_text("# Just a README\n")
        assert not scan.is_design_md(f)

    def test_html_file(self, tmp_path):
        f = tmp_path / "index.html"
        f.write_text("<html></html>")
        assert not scan.is_design_md(f)

    def test_mdx_with_frontmatter(self, tmp_path):
        f = tmp_path / "DESIGN.mdx"
        f.write_text("---\ntitle: x\n---\ncontent")
        assert scan.is_design_md(f)


# ── severity_at_or_above ─────────────────────────────────────────────


class TestSeverityAtOrAbove:
    def test_critical(self):
        assert scan.severity_at_or_above("critical") == {"critical"}

    def test_warning(self):
        assert scan.severity_at_or_above("warning") == {"critical", "warning"}

    def test_info(self):
        assert scan.severity_at_or_above("info") == {"critical", "warning", "info"}

    def test_nit(self):
        assert scan.severity_at_or_above("nit") == {"critical", "warning", "info", "nit"}


# ── scan_file_with_tropes ───────────────────────────────────────────


class TestScanFileWithTropes:
    def test_trope_01_colored_border(self, patterns):
        content = textwrap.dedent("""\
            <div class="border-l-4 border-l-blue-500 p-4">Card 1</div>
            <div class="border-l-4 border-l-green-500 p-4">Card 2</div>
            <div class="border-l-4 border-l-red-500 p-4">Card 3</div>
        """)
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-01" in ids

    def test_trope_01_css_border_left(self, patterns):
        content = textwrap.dedent("""\
            <div style="border-left: 3px solid #ff0000">A</div>
            <div style="border-left: 3px solid #00ff00">B</div>
            <div style="border-left: 3px solid #0000ff">C</div>
        """)
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-01" in ids

    def test_trope_01_below_min_count(self, patterns):
        content = '<div style="border-left: 3px solid #ff0000">Just one</div>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-01" not in ids

    def test_trope_02_tailwind_gradient(self, patterns):
        content = '<div class="from-purple-500 via-pink-500 to-red-500">grad</div>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-02" in ids

    def test_trope_04_inter_excluded_by_serif(self, patterns):
        content = textwrap.dedent("""\
            <style>
            body { font-family: Inter; }
            h1 { font-family: Playfair Display; }
            </style>
        """)
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-04" not in ids

    def test_trope_04_inter_no_serif(self, patterns):
        content = '<style>body { font-family: Inter; }</style>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-04" in ids

    def test_trope_09_hyperbolic_en(self, patterns):
        content = "This is a revolutionary and seamless platform."
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-09" in ids

    def test_trope_09_hyperbolic_zh(self, patterns):
        content = "這是一個顛覆業界的劃時代產品。"
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-09" in ids

    def test_trope_11_stock_names_en(self, patterns):
        content = "John Doe is our satisfied customer."
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-11" in ids

    def test_trope_11_stock_names_zh(self, patterns):
        content = "王小明表示非常滿意。"
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-11" in ids

    def test_skip_marker_suppresses_trope(self, patterns):
        content = textwrap.dedent("""\
            <!-- anti-slop-skip: trope-09 -->
            This is a revolutionary and seamless platform.
        """)
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-09" not in ids

    def test_clean_file_no_findings(self, patterns):
        content = "<div>Clean minimal content</div>"
        findings = scan.scan_file_with_tropes(content, patterns)
        assert len(findings) == 0

    def test_finding_has_excerpt(self, patterns):
        content = "John Doe is here."
        findings = scan.scan_file_with_tropes(content, patterns)
        trope_11 = [f for f in findings if f["trope_id"] == "trope-11"]
        assert trope_11
        assert trope_11[0]["excerpt"].startswith("L1:")

    def test_finding_has_remediation(self, patterns):
        content = "John Doe is here."
        findings = scan.scan_file_with_tropes(content, patterns)
        trope_11 = [f for f in findings if f["trope_id"] == "trope-11"]
        assert trope_11[0]["remediation"] != ""

    def test_trope_05_everything_centered(self, patterns):
        content = " ".join(
            [f'<div class="text-center items-center justify-center mx-auto">x</div>'] * 3
        )
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-05" in ids

    def test_trope_06_over_rounded(self, patterns):
        content = "\n".join(
            [f'<div class="rounded-3xl">r{i}</div>' for i in range(6)]
        )
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-06" in ids

    def test_trope_08_gradient_border(self, patterns):
        content = '<div style="border-image: linear-gradient(to right, red, blue) 1">x</div>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-08" in ids

    def test_trope_10_hover_overload(self, patterns):
        content = "\n".join(
            [f'<div class="hover:scale-105 hover:shadow-lg hover:rotate-1 hover:translate-y-1">h{i}</div>' for i in range(3)]
        )
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-10" in ids

    def test_trope_12_decorative_chart(self, patterns):
        content = "const fakeData = generateChart(randomData);"
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-12" in ids

    def test_trope_14_oversized_hero(self, patterns):
        content = '<h1 class="text-9xl">HUGE</h1>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-14" in ids

    def test_trope_16_excessive_nesting_regex(self, patterns):
        content = "flex items-center justify-center wrapper\n" * 4
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-16" in ids

    def test_trope_17_cjk_font_mismatch(self, patterns):
        content = '<style>h1 { font-family: Noto Serif TC, Noto Sans TC; }</style>'
        findings = scan.scan_file_with_tropes(content, patterns)
        ids = [f["trope_id"] for f in findings]
        assert "trope-17" in ids

    def test_trope_invalid_regex_no_crash(self, patterns):
        bad_patterns = {
            "tropes": [{
                "id": "trope-bad",
                "name": "Bad",
                "severity": "warning",
                "patterns": [{"type": "regex", "pattern": "[invalid(", "flags": ""}],
            }]
        }
        findings = scan.scan_file_with_tropes("test content", bad_patterns)
        nits = [f for f in findings if f["severity"] == "nit"]
        assert len(nits) == 1
        assert "regex error" in nits[0]["message"]


# ── scan_seven_sins ──────────────────────────────────────────────────


class TestScanSevenSins:
    def test_sin2_trust_gradient(self):
        content = '<div style="background: linear-gradient(to right, purple, blue)">trust</div>'
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-2-trust-gradient" in ids

    def test_sin3_emoji_in_heading(self):
        content = "<h1>🚀 Launch</h1>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-3-emoji-icon" in ids

    def test_sin3_emoji_in_button(self):
        content = "<button>⭐ Star</button>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-3-emoji-icon" in ids

    def test_sin5_rounded_left_border(self):
        content = "<style>.card { border-radius: 12px; border-left: 4px solid #6366f1; }</style>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-5-rounded-left-border" in ids

    def test_sin6_invented_metric(self):
        content = "<p>10x faster than competitors</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-6-invented-metric" in ids

    def test_sin7_filler_copy(self):
        content = "<p>Lorem ipsum dolor sit amet</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-7-filler-copy" in ids

    def test_sin7_placeholder(self):
        content = "<p>Your company name goes here. Click here to learn more.</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f["id"] for f in findings]
        assert "sin-7-filler-copy" in ids

    def test_clean_html_no_sins(self):
        content = textwrap.dedent("""\
            <style>
            :root { --accent: #2563eb; }
            .card { border-radius: 8px; padding: 16px; }
            </style>
            <div class="card"><h2>Real heading</h2><p>Real content here.</p></div>
        """)
        findings = scan.scan_seven_sins(content)
        assert len(findings) == 0

    def test_sin_findings_have_critical_severity(self):
        content = "<p>Lorem ipsum dolor sit amet</p>"
        findings = scan.scan_seven_sins(content)
        for f in findings:
            assert f["severity"] == "critical"

    def test_sin2_no_false_positive_single_color(self):
        content = '<div style="background: linear-gradient(to right, #eee, #fff)">ok</div>'
        findings = scan.scan_seven_sins(content)
        ids = [f.get("id") for f in findings]
        assert "sin-2-trust-gradient" not in ids

    def test_sin3_no_false_positive_text_emoji(self):
        content = "<p>This is great 🎉 and works well</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f.get("id") for f in findings]
        assert "sin-3-emoji-icon" not in ids

    def test_sin5_no_false_positive_radius_only(self):
        content = "<style>.card { border-radius: 12px; padding: 16px; }</style>"
        findings = scan.scan_seven_sins(content)
        ids = [f.get("id") for f in findings]
        assert "sin-5-rounded-left-border" not in ids

    def test_sin6_no_false_positive_grid_layout(self):
        content = "<p>2x layout grid configuration</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f.get("id") for f in findings]
        assert "sin-6-invented-metric" not in ids

    def test_sin7_no_false_positive_real_content(self):
        content = "<p>Our platform reduces onboarding time by 40%.</p>"
        findings = scan.scan_seven_sins(content)
        ids = [f.get("id") for f in findings]
        assert "sin-7-filler-copy" not in ids


# ── sin 1 + sin 4 (token-aware) ─────────────────────────────────────


class TestTokenAwareSins:
    def test_sin1_indigo_outside_token_scope(self):
        content = textwrap.dedent("""\
            <style>
            :root { --bg: #ffffff; }
            .btn { color: #6366f1; }
            </style>
        """)
        findings = check_indigo_conflict(content)
        ids = [f["id"] for f in findings]
        assert "sin-1-tailwind-indigo" in ids

    def test_sin1_indigo_inside_token_scope_ok(self):
        content = textwrap.dedent("""\
            <style>
            :root { --accent: #6366f1; }
            </style>
        """)
        findings = check_indigo_conflict(content)
        assert len(findings) == 0

    def test_sin4_font_conflict(self):
        content = textwrap.dedent("""\
            <style>
            :root { --font-display: "Playfair Display", serif; }
            h1 { font-family: Inter, sans-serif; }
            </style>
        """)
        tokens = extract_css_tokens(content)
        findings = check_font_conflict(content, tokens)
        ids = [f["id"] for f in findings]
        assert "sin-4-font-conflict" in ids

    def test_sin4_no_conflict_when_sans(self):
        content = textwrap.dedent("""\
            <style>
            :root { --font-display: Inter, sans-serif; }
            h1 { font-family: Inter, sans-serif; }
            </style>
        """)
        tokens = extract_css_tokens(content)
        findings = check_font_conflict(content, tokens)
        assert len(findings) == 0


# ── token_resolver ───────────────────────────────────────────────────


class TestTokenResolver:
    def test_extract_style_blocks(self):
        html = "<style>body{color:red}</style><div></div><style>.x{}</style>"
        blocks = extract_style_blocks(html)
        assert len(blocks) == 2
        assert "body{color:red}" in blocks[0]

    def test_extract_css_tokens_root(self):
        html = "<style>:root { --accent: #2563eb; --bg: #fff; }</style>"
        tokens = extract_css_tokens(html)
        assert ":root" in tokens
        assert tokens[":root"]["--accent"] == "#2563eb"
        assert tokens[":root"]["--bg"] == "#fff"

    def test_extract_css_tokens_data_theme(self):
        html = '<style>[data-theme="dark"] { --bg: #1a1a2e; }</style>'
        tokens = extract_css_tokens(html)
        assert any("data-theme" in k for k in tokens)

    def test_extract_css_tokens_ignores_component(self):
        html = "<style>.card { --card-padding: 16px; }</style>"
        tokens = extract_css_tokens(html)
        assert len(tokens) == 0

    def test_resolve_simple_var(self):
        theme = {"--accent": "#2563eb"}
        assert resolve_css_var("var(--accent)", theme) == "#2563eb"

    def test_resolve_nested_var(self):
        theme = {"--primary": "var(--accent)", "--accent": "#ff0000"}
        assert resolve_css_var("var(--primary)", theme) == "#ff0000"

    def test_resolve_with_fallback(self):
        theme: dict[str, str] = {}
        assert resolve_css_var("var(--missing, #ccc)", theme) == "#ccc"

    def test_resolve_max_depth(self):
        theme = {f"--v{i}": f"var(--v{i + 1})" for i in range(10)}
        result = resolve_css_var("var(--v0)", theme)
        assert "var(--v" in result

    def test_build_resolved_theme_priority(self):
        tokens = {
            ":root": {"--accent": "#aaa"},
            "html": {"--accent": "#bbb"},
            '[data-theme="dark"]': {"--accent": "#ccc"},
        }
        resolved = build_resolved_theme(tokens)
        assert resolved["--accent"] == "#ccc"

    def test_is_in_token_scope_root(self):
        css = ":root { --accent: #fff; } .card { color: red; }"
        pos_root = css.index("--accent")
        pos_card = css.index("color")
        assert is_in_token_scope(css, pos_root)
        assert not is_in_token_scope(css, pos_card)

    def test_resolve_nested_fallback_with_var(self):
        theme = {"--a": "#ff0000"}
        result = resolve_css_var("var(--missing, var(--a))", theme)
        assert result == "#ff0000"

    def test_extract_empty_style_block(self):
        html = "<style></style><style>   </style>"
        blocks = extract_style_blocks(html)
        assert len(blocks) == 2

    def test_extract_css_tokens_empty_style(self):
        html = "<style></style>"
        tokens = extract_css_tokens(html)
        assert len(tokens) == 0


# ── merge_findings ───────────────────────────────────────────────────


class TestMergeFindings:
    def test_merge_all_three_layers(self):
        design = {
            "ok": True,
            "findings": [{"source": "design-md-lint", "severity": "warning", "message": "x"}],
        }
        trope = [{"source": "trope-scan", "severity": "info", "trope_id": "trope-01"}]
        sins = [{"source": "seven-sins", "severity": "critical", "id": "sin-2"}]
        result = scan.merge_findings(design, trope, sins)
        assert result["summary"]["critical"] == 1
        assert result["summary"]["warning"] == 1
        assert result["summary"]["info"] == 1
        assert result["summary"]["total"] == 3
        assert result["findings"][0]["severity"] == "critical"

    def test_merge_skipped_design_md(self):
        result = scan.merge_findings(None, [], None)
        assert result["summary"]["total"] == 0
        assert result["design_md_lint"]["ok"] is False

    def test_merge_sorts_by_severity(self):
        trope = [
            {"source": "trope-scan", "severity": "nit"},
            {"source": "trope-scan", "severity": "critical"},
            {"source": "trope-scan", "severity": "warning"},
        ]
        result = scan.merge_findings(None, trope)
        severities = [f["severity"] for f in result["findings"]]
        assert severities == ["critical", "warning", "nit"]


# ── format_text_report ───────────────────────────────────────────────


class TestFormatTextReport:
    def test_report_contains_target(self):
        result = {
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0, "nit": 0, "total": 0},
            "design_md_lint": {"ok": True},
        }
        report = scan.format_text_report(result, "test.html")
        assert "test.html" in report

    def test_report_shows_skipped_lint(self):
        result = {
            "findings": [],
            "summary": {"critical": 0, "warning": 0, "info": 0, "nit": 0, "total": 0},
            "design_md_lint": {"ok": False, "reason": "npx_not_found"},
        }
        report = scan.format_text_report(result, "test.md")
        assert "npx_not_found" in report

    def test_format_finding_line_trope(self):
        f = {
            "source": "trope-scan",
            "trope_id": "trope-01",
            "trope_name": "彩色邊條卡片",
            "severity": "warning",
            "match_count": 4,
            "min_count_threshold": 3,
            "excerpt": "L5: border-left: 3px solid #ff0000",
            "remediation": "用留白取代",
        }
        line = scan.format_finding_line(f)
        assert "trope-01" in line
        assert "×4/3" in line
        assert "用留白取代" in line

    def test_format_finding_line_design_md(self):
        f = {
            "source": "design-md-lint",
            "rule_id": "contrast-ratio",
            "severity": "warning",
            "path": "DESIGN.md",
            "message": "Low contrast",
        }
        line = scan.format_finding_line(f)
        assert "contrast-ratio" in line
        assert "DESIGN.md" in line


# ── run_design_md_lint (mocked) ──────────────────────────────────────


class TestRunDesignMdLint:
    def test_npx_success(self, tmp_path):
        target = tmp_path / "DESIGN.md"
        target.write_text("---\nname: t\n---\n")
        mock_output = json.dumps({
            "findings": [
                {"severity": "warning", "message": "No 'primary' color defined", "path": "DESIGN.md"}
            ],
            "summary": {"warnings": 1},
        })
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = scan.run_design_md_lint(target)
        assert result["ok"]
        assert len(result["findings"]) == 1
        assert result["findings"][0]["severity"] == "warning"
        assert result["findings"][0]["rule_id"] == "missing-primary"

    def test_npx_not_found_with_vendored_fallback(self, tmp_path):
        target = tmp_path / "DESIGN.md"
        target.write_text("---\nname: t\n---\n")
        with patch("subprocess.run", side_effect=FileNotFoundError):
            with patch.object(scan, "run_vendored_design_md_lint", return_value={
                "ok": True,
                "raw_payload": {"findings": [], "summary": {}},
            }):
                result = scan.run_design_md_lint(target)
        assert result["ok"]
        assert result["used_source"] == "vendored"

    def test_npx_timeout(self, tmp_path):
        target = tmp_path / "DESIGN.md"
        target.write_text("---\nname: t\n---\n")
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="npx", timeout=120)):
            with patch.object(scan, "run_vendored_design_md_lint", return_value={
                "ok": False,
                "reason": "vendored_unavailable",
                "findings": [],
                "raw_summary": None,
            }):
                result = scan.run_design_md_lint(target)
        assert not result["ok"]
        assert result["reason"] == "npx_timeout"

    def test_severity_remap_orphaned_tokens(self, tmp_path):
        target = tmp_path / "DESIGN.md"
        target.write_text("---\nname: t\n---\n")
        mock_output = json.dumps({
            "findings": [
                {"severity": "warning", "message": "--foo is defined but never referenced by any component"}
            ],
            "summary": {},
        })
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = mock_output
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result = scan.run_design_md_lint(target)
        assert result["findings"][0]["severity"] == "nit"
        assert result["findings"][0]["rule_id"] == "orphaned-tokens"


# ── ensure_vendored_extracted ─────────────────────────────────────────


class TestEnsureVendoredExtracted:
    def test_already_extracted(self, tmp_path):
        cli_entry = tmp_path / "package" / "dist" / "index.js"
        cli_entry.parent.mkdir(parents=True)
        cli_entry.write_text("// cli")
        with patch.object(scan, "VENDORED_CLI_ENTRY", cli_entry):
            assert scan.ensure_vendored_extracted() is True

    def test_tarball_not_found(self, tmp_path):
        fake_entry = tmp_path / "no" / "index.js"
        fake_tarball = tmp_path / "no.tgz"
        with patch.object(scan, "VENDORED_CLI_ENTRY", fake_entry):
            with patch.object(scan, "VENDORED_TARBALL", fake_tarball):
                assert scan.ensure_vendored_extracted() is False


# ── collect_targets ──────────────────────────────────────────────────


class TestCollectTargets:
    def test_single_file(self, tmp_path):
        f = tmp_path / "test.html"
        f.write_text("<div></div>")
        targets = scan.collect_targets(f, recursive=False)
        assert len(targets) == 1
        assert targets[0] == f

    def test_directory_non_recursive(self, tmp_path):
        (tmp_path / "a.html").write_text("<div></div>")
        (tmp_path / "b.md").write_text("# Title")
        (tmp_path / "c.py").write_text("pass")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "d.html").write_text("<div></div>")
        targets = scan.collect_targets(tmp_path, recursive=False)
        exts = {t.suffix for t in targets}
        assert ".py" not in exts
        assert len(targets) == 2

    def test_directory_recursive(self, tmp_path):
        (tmp_path / "a.html").write_text("<div></div>")
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "b.html").write_text("<div></div>")
        targets = scan.collect_targets(tmp_path, recursive=True)
        assert len(targets) == 2

    def test_nonexistent(self, tmp_path):
        targets = scan.collect_targets(tmp_path / "nope.html", recursive=False)
        assert len(targets) == 0


# ── Google severity remap ────────────────────────────────────────────


class TestGoogleSeverityRemap:
    def test_error_to_critical(self):
        assert scan.GOOGLE_SEVERITY_REMAP["error"] == "critical"

    def test_warning_stays(self):
        assert scan.GOOGLE_SEVERITY_REMAP["warning"] == "warning"

    def test_orphaned_tokens_local_remap(self):
        assert scan.GOOGLE_RULE_LOCAL_REMAP["orphaned-tokens"] == "nit"


# ── 整合測試：trope + 7 sins 混合場景 ─────────────────────────────────


class TestIntegration:
    def test_html_with_multiple_issues(self, patterns):
        content = textwrap.dedent("""\
            <style>
            :root { --bg: #fff; }
            .btn { color: #6366f1; }
            .card { border-radius: 12px; border-left: 4px solid #6366f1; }
            </style>
            <h1>🚀 Launch</h1>
            <p>This is a revolutionary and seamless platform.</p>
            <p>10x faster than competitors</p>
            <p>Lorem ipsum dolor sit amet</p>
        """)
        trope_findings = scan.scan_file_with_tropes(content, patterns)
        sin_findings = scan.scan_seven_sins(content)
        merged = scan.merge_findings(None, trope_findings, sin_findings)
        assert merged["summary"]["total"] > 0
        assert merged["summary"]["critical"] > 0
        sources = {f.get("source", "") for f in merged["findings"]}
        assert "trope-scan" in sources or "seven-sins" in sources

    def test_clean_design_md_minimal_findings(self, patterns):
        content = textwrap.dedent("""\
            ---
            name: Clean Design
            ---
            ## Colors
            Primary: #2563eb
            ## Typography
            Display: Source Serif 4
            Body: Inter
        """)
        findings = scan.scan_file_with_tropes(content, patterns)
        critical = [f for f in findings if f["severity"] == "critical"]
        assert len(critical) == 0
