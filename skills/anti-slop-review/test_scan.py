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
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SPEC = importlib.util.spec_from_file_location('anti_slop_scan', Path(__file__).with_name('scan.py'))
scan = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = scan
SPEC.loader.exec_module(scan)


@pytest.mark.parametrize("kind", ["css", "html"])
def test_large_file_scan_under_two_seconds(kind):
    if kind == "css":
        lines = ['.c%d { color: #333; padding: 4px 8px; margin: 0; border-left: 1px solid var(--line); background: #fff; }' % i
                 for i in range(3000)]
        content = '\n'.join(lines)
    else:
        html = ['<div style="color: red; padding: 4px">x%d</div>' % i
                for i in range(2000)]
        content = '<html><body>' + '\n'.join(html) + '</body></html>'
    patterns = scan.load_patterns()
    started = time.perf_counter()
    scan.scan_file_with_tropes(content, patterns)
    elapsed = time.perf_counter() - started
    assert elapsed < 2, f"{kind} full scan took {elapsed:.3f}s (limit: 2s)"


def test_full_scan_parses_declarations_once():
    content = ('background: #fdf3e2; box-shadow: 0 0 40px #7c3aed; '
               'mask-image: linear-gradient(red, blue, green, yellow);')
    with patch.object(scan, 'css_declarations', wraps=scan.css_declarations) as parser:
        findings = scan.scan_file_with_tropes(content, scan.load_patterns())
    parser.assert_called_once_with(content)
    assert {f['trope_id'] for f in findings} == {'trope-20', 'trope-21'}


class TestT501:
    @staticmethod
    def hits(content, trope_id):
        return [f for f in scan.scan_file_with_tropes(content, scan.load_patterns())
                if f.get('trope_id') == trope_id]

    @pytest.mark.parametrize('content', [
        '.form-msg.is-ok { border-left: 6px solid var(--green); }\n'
        '.form-msg.is-warn { border-left: 6px solid var(--amber); }\n'
        '.form-msg.is-error { border-left: 6px solid var(--red); }',
        '.situation { border-left: 6px solid var(--tc); }\n'
        '.vs { border-top: 6px solid var(--vc); }\n'
        '.bays li { border-top: 6px solid var(--tc); }',
    ])
    def test_border_required_examples(self, content):
        hits = self.hits(content, 'trope-01')
        assert len(hits) == 1
        assert hits[0]['match_count'] == 3
        assert hits[0]['min_count_threshold'] == 3

    @pytest.mark.parametrize('side', ['left', 'right', 'top', 'inline-start', 'inline-end'])
    @pytest.mark.parametrize('width', ['3px', '3.5px', '12px', '.2rem', '0.25em'])
    def test_border_sides_widths(self, side, width):
        assert len(self.hits(f'border-{side}: {width} solid var(--accent);\n' * 3,
                             'trope-01')) == 1

    @pytest.mark.parametrize('color', [
        '#f00', '#ff0000', '#f008', '#ff000080', 'rgb(255, 0, 0)',
        'rgba(255, 0, 0, .5)', 'hsl(30, 80%, 50%)', 'hsla(30, 80%, 50%, .5)',
        'rebeccapurple', 'coral', 'var(--any-name)',
    ])
    def test_border_colors(self, color):
        assert len(self.hits(f'border-left: 6px solid {color};\n' * 3, 'trope-01')) == 1

    @pytest.mark.parametrize('declarations', [
        'border-top: 1px solid var(--line);\nborder-bottom: 1px solid var(--line);\n'
        'border-top: 1px solid var(--line);',
        *[f'border-left: 6px solid {color};\n' * 3 for color in
          ['transparent', 'currentColor', 'inherit', 'initial', 'unset',
           'black', 'white', 'gray', 'grey', 'silver', 'notacolor']],
        'border-bottom: 6px solid var(--tc);\n' * 3,
        *[f'border-left: {width} solid red;\n' * 3 for width in
          ['1px', '2px', '2.9px', '.19rem', '0.1em']],
        'border-left-width: 6px;\n' * 3,
    ])
    def test_border_exclusions(self, declarations):
        assert not self.hits(declarations, 'trope-01')

    @pytest.mark.parametrize('side', ['l', 'r', 't'])
    def test_border_tailwind(self, side):
        assert len(self.hits(f'<div class="border-{side}-4 border-{side}-red-500">\n' * 3,
                             'trope-01')) == 1

    def test_border_tailwind_no_mismatched_side_or_thin(self):
        assert not self.hits('<div class="border-t-4 border-r-red-500">\n' * 3, 'trope-01')
        assert not self.hits('<div class="border-l-2 border-l-red-500">\n' * 3, 'trope-01')

    MASK = ('.plate { -webkit-mask-image: linear-gradient(to right, transparent 0, '
            '#000 0.7%, #000 99.3%, transparent 100%); mask-image: linear-gradient('
            'to right, transparent 0, #000 0.7%, #000 99.3%, transparent 100%); }')

    def test_mask_required_example(self):
        assert not self.hits(self.MASK, 'trope-02')

    @pytest.mark.parametrize('property_name', ['mask', '-webkit-mask', 'mask-image', '-webkit-mask-image'])
    def test_mask_each_declaration(self, property_name):
        content = f'.a {{ {property_name}:\nlinear-gradient(90deg, #f0f, #0ff, #ff0, #f00); }}'
        assert not self.hits(content, 'trope-02')

    def test_mask_keeps_hero_line(self):
        content = self.MASK + '\n.hero { background: linear-gradient(90deg, #f0f, #0ff, #ff0, #f00); }'
        hits = self.hits(content, 'trope-02')
        assert len(hits) == 1
        assert hits[0]['match_count'] == 1
        assert hits[0]['excerpt'].startswith('L2:')

    @pytest.mark.parametrize('declaration', [
        'background: #fdf3e2;', '--paper: #fdf6e3;',
        'background: rgba(255, 250, 242, 0.95);',
        'background-color: rgb(255, 250, 242);',
        '--bg-main: #fdf3e2;', '--background: #fdf3e2;', '--surface: #fdf3e2;',
        '--base-color: #fdf3e2;', 'BACKGROUND: #FDF3E2;', 'background: #fec;',
        'background: rgb(100% 98% 95% / .8);',
        'background: hsl(30, 20%, 90%);',
        'background-color: hsl(60, 20%, 90%);',
    ])
    def test_cream_positive(self, declaration):
        hits = self.hits(declaration, 'trope-20')
        assert len(hits) == 1
        assert hits[0]['severity'] == 'info'
        assert hits[0]['min_count_threshold'] == 1

    @pytest.mark.parametrize('declaration', [
        'background: #fff;', 'background: #f5f5f5;', 'background: #fff0ec;',
        'color: #fdf3e2;', 'border-color: #fdf3e2;', '--accent: #fdf3e2;',
        'background-image: url(#fdf3e2);', 'background: #653f1b;',
        'background: hsl(29, 50%, 95%);', 'background: hsl(61, 50%, 95%);',
        'background: hsl(40, 19%, 95%);', 'background: hsl(40, 50%, 89%);',
    ])
    def test_cream_negative(self, declaration):
        assert not self.hits(declaration, 'trope-20')

    @pytest.mark.parametrize('declaration', [
        'box-shadow: 0 0 40px rgba(124, 58, 237, 0.5);',
        'text-shadow: 0px 0px 20px #7c3aed;',
        'filter: drop-shadow(0 0 30px rgb(124, 58, 237));',
        'box-shadow: 0 4px 14px #000, 0 0 40px rgba(124, 58, 237, .5);',
        'box-shadow: 0 0 20px rgba(16, 0, 0, .5);',
    ])
    def test_glow_positive(self, declaration):
        hits = self.hits(declaration, 'trope-21')
        assert len(hits) == 1
        assert hits[0]['severity'] == 'info'

    @pytest.mark.parametrize('declaration', [
        'box-shadow: 0 4px 14px rgba(74, 42, 20, 0.22);',
        'box-shadow: inset 0 0 0 8px var(--wood);',
        'box-shadow: 0 0 40px rgba(0, 0, 0, 0.5);',
        'box-shadow: 0 0 40px rgba(100, 110, 115, .5);',
        'box-shadow: 0 0 19px #7c3aed;', 'box-shadow: 0 1px 40px #7c3aed;',
        'text-shadow: 0 0 40px #fff;', 'box-shadow: 0 0 40px gray;',
        'filter: blur(40px);',
    ])
    def test_glow_negative(self, declaration):
        assert not self.hits(declaration, 'trope-21')

    @pytest.mark.parametrize('declaration', [
        'background: repeating-linear-gradient(to bottom, transparent 0, transparent calc(12.5% - 4px), #5a3620 calc(12.5% - 4px), #5a3620 12.5%);',
        'background-image: repeating-radial-gradient(red, blue 20px);',
    ])
    def test_stripes_positive(self, declaration):
        hits = self.hits(declaration, 'trope-22')
        assert len(hits) == 1
        assert hits[0]['severity'] == 'info'

    @pytest.mark.parametrize('declaration', [
        'mask-image: repeating-linear-gradient(red, blue);',
        '--background: repeating-linear-gradient(red, blue);',
        'background: linear-gradient(red, blue);',
    ])
    def test_stripes_negative(self, declaration):
        assert not self.hits(declaration, 'trope-22')

    def test_css_skip_markers(self):
        content = '/* anti-slop-skip: trope-20,trope-21 */\nbackground: #fdf3e2;'
        assert scan.parse_skip_markers(content) == {'trope-20', 'trope-21'}
        assert not self.hits(content, 'trope-20')

    def test_cli_skip_tropes(self, tmp_path, capsys):
        target = tmp_path / 'sample.css'
        target.write_text('background: #fdf3e2; box-shadow: 0 0 40px #7c3aed;\n'
                          'background-image: repeating-linear-gradient(red, blue);')
        with patch('sys.argv', ['scan.py', str(target), '--skip-design-md-lint', '--format',
                                'json', '--skip-tropes', 'trope-20,trope-21']):
            assert scan.main() == 0
        hits = json.loads(capsys.readouterr().out)['results'][0]['findings']
        assert {f['trope_id'] for f in hits} == {'trope-22'}

    def test_cli_skip_unknown(self, tmp_path, capsys):
        target = tmp_path / 'sample.css'
        target.write_text('')
        with patch('sys.argv', ['scan.py', str(target), '--skip-tropes', 'trope-20,trope-99']):
            with pytest.raises(SystemExit) as error:
                scan.main()
        assert error.value.code == 2
        assert 'trope-99' in capsys.readouterr().err


class TestT501Revision:
    hits = staticmethod(TestT501.hits)

    @pytest.mark.parametrize('trope_id,declarations', [
        ('trope-01', '.a { border-left: 6px solid var(--x); }\n' * 3),
        ('trope-20', 'background: #fdf3e2;'),
        ('trope-21', 'box-shadow: 0 0 40px rgba(124, 58, 237, .5);'),
    ])
    def test_css_comments_ignored_and_positions_preserved(self, trope_id, declarations):
        comment = '/* 範例：\n' + declarations + '\n*/\n'
        assert not self.hits(comment, trope_id)
        hits = self.hits(comment + declarations, trope_id)
        assert len(hits) == 1
        assert hits[0]['match_count'] == (3 if trope_id == 'trope-01' else 1)
        assert hits[0]['excerpt'].startswith(f'L{comment.count(chr(10)) + 1}:')

    def test_css_inline_comments_are_whitespace(self):
        hits = self.hits('background: /* 色票 */ #fdf3e2;', 'trope-20')
        assert len(hits) == 1
        assert hits[0]['excerpt'].startswith('L1:')

    def test_css_comments_do_not_change_regex_rules(self):
        # 註解中的 regex 命中保留；假 mask 宣告不得成為排除區間。
        gradient = 'linear-gradient(to right, transparent 0, #000 1%, #000 99%, transparent 100%)'
        hits = self.hits(f'/* mask-image: {gradient}; */', 'trope-02')
        assert len(hits) == 1
        assert hits[0]['match_count'] == 1

    @pytest.mark.parametrize('property_name', [
        'mask', '-webkit-mask', 'mask-image', '-webkit-mask-image',
    ])
    @pytest.mark.parametrize('url', [
        'url("data:image/svg+xml;utf8,<svg></svg>")',
        "url('data:image/svg+xml;utf8,<svg></svg>')",
        'url(data:image/svg+xml;utf8,svg)',
        r'url("data:a;test=\"quoted\";end")',
    ])
    def test_mask_url_semicolons_and_multiple_gradients(self, property_name, url):
        gradient = 'linear-gradient(to right, transparent 0, #000 1%, #000 99%, transparent 100%)'
        content = f'.m {{ {property_name}: {url}, {gradient}, {gradient}; }}'
        assert not self.hits(content, 'trope-02')
        hits = self.hits(content + f'\n.hero {{ background: {gradient}; }}', 'trope-02')
        assert len(hits) == 1
        assert hits[0]['match_count'] == 1
        assert hits[0]['excerpt'].startswith('L2:')

    @pytest.mark.parametrize('hue', ['0.11turn', '44grad', '0.6911503837897545rad',
                                     '1.11turn', '-356grad', '-5.592034923389832rad'])
    def test_hsl_angle_units_cream(self, hue):
        assert len(self.hits(f'background: hsl({hue} 80% 95%);', 'trope-20')) == 1

    @pytest.mark.parametrize('color', [
        'rgba(253, 243, 226, 0)', 'hsla(40, 80%, 95%, 0)',
        'rgb(253 243 226 / 0%)', 'hsl(40 80% 95% / 0%)',
        '#fec0', '#fdf3e200',
    ])
    @pytest.mark.parametrize('trope_id,template', [
        ('trope-01', 'border-left: 6px solid {color};\n' * 3),
        ('trope-20', 'background: {color};'),
        ('trope-21', 'box-shadow: 0 0 40px {color};'),
    ])
    def test_zero_alpha_not_colored(self, color, trope_id, template):
        assert not self.hits(template.format(color=color), trope_id)

    @pytest.mark.parametrize('color', [
        'rgba(253, 243, 226, .01)', 'hsla(40, 80%, 95%, .01)',
        'rgb(253 243 226 / 1%)', 'hsl(40 80% 95% / 1%)',
        '#fec1', '#fdf3e201',
    ])
    @pytest.mark.parametrize('trope_id,template', [
        ('trope-01', 'border-left: 6px solid {color};\n' * 3),
        ('trope-20', 'background: {color};'),
        ('trope-21', 'box-shadow: 0 0 40px {color};'),
    ])
    def test_nonzero_alpha_still_colored(self, color, trope_id, template):
        assert len(self.hits(template.format(color=color), trope_id)) == 1


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


class TestStyleRegions:
    @pytest.mark.parametrize("content", [
        "<p>Note: don't use</p><style>.card { background: #fdf3e2; }</style>",
        """a[title="Tip: don't"] { background: #fdf3e2; }""",
        """const s = '<div style="background: #fdf3e2\\"></div>';""",
        """<div title='see style="color:red' style="background: #fdf3e2"></div>""",
    ], ids=["Q1a", "Q1b", "Q2a", "Q2b"])
    def test_reproductions(self, content):
        hits = TestT501.hits(content, "trope-20")
        assert len(hits) == 1
        assert hits[0]["match_count"] == 1

    @pytest.mark.parametrize("prefix", [
        "Note: don't", 'Tip: "unclosed', "calc(100% - ",
        """a[title="x: y'"]""", '<!-- style="x -->',
        "<script>var a = {b: 'c'};</script>",
    ])
    @pytest.mark.parametrize("separator", ["", "\n"])
    def test_interference(self, prefix, separator):
        content = prefix + separator + "<style>.card { background: #fdf3e2; }</style>"
        hits = TestT501.hits(content, "trope-20")
        assert len(hits) == 1
        assert hits[0]["excerpt"].startswith(f"L{1 + separator.count(chr(10))}:")

    @pytest.mark.parametrize("content", [
        "background: #fdf3e2;\n.a { color: red; }",
        """a[title="background: #fdf3e2;"] {}""",
        "@supports (background: #fdf3e2) {}",
        '<p style-note="background: #fdf3e2">background: #fdf3e2;</p>',
        """<script>const x = '<div style="background: #fdf3e2"></div>';</script>""",
        '<!-- <div style="background: #fdf3e2"> --><p>x</p>',
    ])
    def test_outside_regions_ignored(self, content):
        assert not TestT501.hits(content, "trope-20")

    def test_non_html_without_braces_parsed_as_declaration_list(self):
        content = "background: #fdf3e2;"
        hits = TestT501.hits(content, "trope-20")
        assert len(hits) == 1
        assert hits[0]["match_count"] == 1

    @pytest.mark.parametrize("content", [
        '<div style=background:#fdf3e2></div>',
        "<div STYLE='background: #fdf3e2'></div>",
        '@media screen { @supports (display: grid) { .a { background: #fdf3e2; } } }',
        '.a { &:hover { background: #fdf3e2; } }',
        """<style media="screen">a[title="Tip: don't"] { background: #fdf3e2; }</style>""",
    ])
    def test_region_forms(self, content):
        assert len(TestT501.hits(content, "trope-20")) == 1


class TestTaggedTemplateRegions:
    @staticmethod
    def assert_cream(content, line=None):
        hits = TestT501.hits(content, "trope-20")
        assert len(hits) == 1
        assert hits[0]["match_count"] == 1
        if line is not None:
            assert hits[0]["excerpt"].startswith(f"L{line}:")

    @pytest.mark.parametrize("suffix", ["", "\nexport function Card() { return <Box>hi</Box>; }"])
    def test_reproductions(self, suffix):
        self.assert_cream("const Box = styled.div`\n  background: #fdf3e2;\n`;" + suffix, 2)

    @pytest.mark.parametrize("tag", [
        "styled.div", "styled(Button)", "styled.div<Props>",
        "styled.div<Props<{ value: string }>>", "styled(Button)<Props>",
        "styled.div.attrs({ role: 'button' })",
        "styled(Button).attrs({ type: 'button' })",
        "styled.div.attrs<Props>({ role: 'button' })<Props>",
        "css", "createGlobalStyle", "keyframes", "injectGlobal",
    ])
    def test_tags(self, tag):
        self.assert_cream(f"const Box = {tag}  `background: #fdf3e2;`;\n<Box />")

    @pytest.mark.parametrize("header", ["&:hover", "@media (min-width: 1px)", "&:hover { &:focus"])
    def test_nested_blocks(self, header):
        self.assert_cream("const Box = styled.div`" + header + " { background: #fdf3e2; } }`; <Box />")

    @pytest.mark.parametrize("expression", [
        "p => p.c", "p => p.ok ? '{' : '}'",
        "p => ({ a: { b: 'background: #fdf3e2;' } })",
        'p => `value ${p.ok ? `nested ${"}"}` : "{"}`',
        'p => { /* } ` */ return "}"; // } `\n }',
    ])
    def test_interpolation_masked_and_recovers(self, expression):
        content = "const Box = styled.div`\n  color: ${" + expression + "};\n  background: #fdf3e2;\n`; <Box />"
        self.assert_cream(content, 4 if "\n" in expression else 3)

    @pytest.mark.parametrize("prefix", ["", "const Box = styled.div`color: red;`;\n"])
    def test_untagged_template_ignored(self, prefix):
        assert not TestT501.hits(prefix + "const s = `background: #fdf3e2;`; <Box>hi</Box>", "trope-20")

    def test_escaped_backtick(self):
        self.assert_cream(r'const Box = styled.div`content: "\`"; background: #fdf3e2;`; <Box />')

    def test_region_coexistence(self):
        self.assert_cream('const Box = styled.div`color: red;`;\n'
                          '<style>.a { background: #fdf3e2; }</style>', 2)

    def test_css_block_coexistence_and_no_duplicate(self):
        self.assert_cream('const Box = styled.div`background: #fdf3e2; &:hover { color: red; }`; .a { color: red; }')

    @pytest.mark.parametrize("content", [
        'const s = "styled.div`background: #fdf3e2;`"; <Box />',
        '// styled.div`background: #fdf3e2;`\n<Box />',
        'const s = other.css`background: #fdf3e2;`; <Box />',
        'const Box = styled.div`@supports (background: #fdf3e2) {} &:background {} `; <Box />',
    ])
    def test_non_style_content_ignored(self, content):
        assert not TestT501.hits(content, "trope-20")

    @pytest.mark.parametrize("tag", [
        "styled.button<{ onClick: () => void }>",
        "styled.button<{ onClick: () => void; size?: number }>",
        "styled(Button)<{ render: (a: number) => string }>",
        "css<{ f: () => void }>",
    ])
    def test_arrow_function_generic(self, tag):
        self.assert_cream("const Btn = " + tag + "`\n  background: #fdf3e2;\n`;\n<Btn />", 2)

    def test_conditional_tagged_interpolation(self):
        self.assert_cream("const Box = styled.div<{ $active?: boolean }>`\n"
                          "  ${({ $active }) => $active && css`\n"
                          "    background: #fdf3e2;\n  `}\n`;\n<Box />", 3)

    @pytest.mark.parametrize("expression", [
        'p => css`background: #fdf3e2;`',
        'p => p.on ? css`background: #fdf3e2;` : css`color: red;`',
        'p => css`${p => p.x && css`background: #fdf3e2;`}`',
    ])
    def test_nested_tagged_interpolations(self, expression):
        self.assert_cream('const Box = styled.div`${' + expression + '}`; <Box />', 1)

    @pytest.mark.parametrize("expression", [
        'p => `background: #fdf3e2;`',
        'p => other.css`background: #fdf3e2;`',
    ])
    def test_non_style_interpolation_templates_ignored(self, expression):
        assert not TestT501.hits('const Box = styled.div`${' + expression + '}`; <Box />', "trope-20")

    @pytest.mark.parametrize("tag", [
        "css", "keyframes", "createGlobalStyle", "injectGlobal", "styled.div",
        "styled(Button)", "styled.div.attrs({})<{ f: () => void }>",
    ])
    def test_nested_tags_share_rules(self, tag):
        self.assert_cream('const Box = styled.div`${p => ' + tag
                          + '`background: #fdf3e2;`}`; <Box />', 1)

    def test_declaration_across_interpolation_preserved(self):
        self.assert_cream('const Box = styled.div`background: ${p => p.bg} #fdf3e2;`; <Box />')

    def test_deep_interpolations_without_recursion(self):
        self.assert_cream('const Box = styled.div`' + '${p => css`' * 1100
                          + 'background: #fdf3e2;' + '`}' * 1100 + '`; <Box />', 1)

    def test_template_end_return_shape(self):
        content = '`color: ${p => css`background: ${q => q.c};`};`'
        start, stop = content.index('${'), content.rindex('}') + 1
        assert scan._template_end(content, 0) == (len(content), [(start, stop)])
        assert scan._template_end(content[:-1], 0) == (None, [])

    def test_template_parsed_once(self):
        content = 'const Box = styled.div`background: #fdf3e2;`; <Box />'
        with patch.object(scan, 'css_declarations', wraps=scan.css_declarations) as parser:
            self.assert_cream(content)
        parser.assert_called_once_with(content)


class TestTemplateActivation:
    CASES = [
        "<p>Press the ` key</p>\n<style>.a { background: #fdf3e2; }</style>",
        '<pre>a ` b</pre>\n<div style="background: #fdf3e2">x</div>',
        "# Tokens\n\nUse `--bg` token.\n\n```css\n.a { background: #fdf3e2; }\n```",
        "<p>Use `npm i`, then don't forget</p>\n<style>.a { background: #fdf3e2; }</style>",
        '.a::after { content: "`"; }\n.b { background: #fdf3e2; }',
        '<template><div>{{ msg }}</div></template>\n<script>const s = `hi ${name}`;</script>\n'
        '<style scoped>.a { background: #fdf3e2; }</style>',
    ]

    @pytest.mark.parametrize("content", CASES,
                             ids=["stray.html", "attr.html", "DESIGN.md", "code.html", "tick.css", "comp.vue"])
    def test_without_tag_preserves_styles(self, content):
        TestTaggedTemplateRegions.assert_cream(content)

    @pytest.mark.parametrize("content", CASES)
    def test_without_tag_does_not_parse_templates(self, content):
        with patch.object(scan, "_template_end", side_effect=AssertionError("不應啟動樣板解析")):
            scan.css_declarations(content)

    @pytest.mark.parametrize("content", [
        'const Box = styled.div`\n  background: #fdf3e2;\n`;\nconst note = "x"; // press ` key\n',
        'const Box = styled.div`color: red;`;\n` press key\n'
        '<style>.a { background: #fdf3e2; }</style>',
    ], ids=["requested-tsx", "unclosed-before-style"])
    def test_unclosed_backtick_not_masked(self, content):
        TestTaggedTemplateRegions.assert_cream(content)
        templates, _, masked = scan._tagged_templates(content)
        stray = content.rindex("`")
        assert all(not (start <= stray < stop) for start, stop in templates)
        assert masked[stray:] == content[stray:]

    @pytest.mark.parametrize("fence", ["```", "````"])
    def test_fences_with_tag_preserve_styles(self, fence):
        content = ('const Box = styled.div`color: red;`;\n' + fence + 'css\n'
                   '.a { background: #fdf3e2; }\n' + fence)
        TestTaggedTemplateRegions.assert_cream(content)
        templates, _, _ = scan._tagged_templates(content)
        assert len(templates) == 1


class TestDeclarationRecovery:
    @pytest.mark.parametrize("prefix", ["<p>Note: don't use this</p>", "<p>Note don't use this</p>"],
                             ids=["reproduction", "control"])
    def test_n1a_text_apostrophe(self, prefix):
        content = prefix + "\n<style>.card { background: #fdf3e2; }</style>"
        findings = scan.scan_file_with_tropes(content, scan.load_patterns())
        assert {f["trope_id"] for f in findings} == {"trope-20"}

    @pytest.mark.parametrize("value", ["calc(100% - 10px", "100% - 10px"],
                             ids=["reproduction", "control"])
    def test_n1b_unclosed_parenthesis(self, value):
        content = ".a { width: " + value + "; }\n.b { background: #fdf3e2; }"
        findings = scan.scan_file_with_tropes(content, scan.load_patterns())
        assert {f["trope_id"] for f in findings} == {"trope-20"}

    @pytest.mark.parametrize("value", ['"Inter', "Inter"],
                             ids=["reproduction", "control"])
    def test_n1c_unclosed_quote(self, value):
        content = ".a { font-family: " + value + "; }\n.b { background: #fdf3e2; }"
        findings = scan.scan_file_with_tropes(content, scan.load_patterns())
        assert {f["trope_id"] for f in findings} == {"trope-04", "trope-20"}

    @pytest.mark.parametrize("attribute", ['data-style="a" ', ""],
                             ids=["reproduction", "control"])
    def test_n2_style_attribute_boundary(self, attribute):
        content = ('<div ' + attribute + 'style="background: #fdf3e2"></div>'
                   '<div class="x" style="box-shadow: 0 0 40px #7c3aed"></div>')
        findings = scan.scan_file_with_tropes(content, scan.load_patterns())
        assert {f["trope_id"] for f in findings} == {"trope-20", "trope-21"}


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
