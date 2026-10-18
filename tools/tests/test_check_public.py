import contextlib
import importlib.util
import io
import tarfile
import zipfile
import unicodedata
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('check_public', Path(__file__).parents[1] / 'check_public.py')
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class PublicTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.addCleanup(self.work.cleanup)
        self.base = Path(self.work.name)
        self.root = self.base / 'repo'
        self.root.mkdir()
        self.terms = self.base / 'terms.txt'
        self.terms.write_text('# comment\nPRIVATE_[A-Z]+\n')

    def run_check(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = checker.main(['--root', str(self.root), '--terms', str(self.terms), *args])
        return rc, output.getvalue()

    def test_clean_and_version_strings(self):
        (self.root / 'good.py').write_text('只才准表台群吃峰核念干床后里\npackage.md@0.1.1\ngsap@3.14.2')
        self.assertEqual(self.run_check()[0], 0)

    def test_all_rules_and_line_numbers(self):
        values = ['/' + 'Users/demo', '/' + 'home/demo', 'C:' + chr(92) + 'Users' + chr(92) + 'demo',
                  'person' + '@' + 'example.org', '1' * 18, 'T-' + '123', 'wiki' + 'a1b2c3d4', 'PRIVATE_SAMPLE']
        (self.root / 'hit.txt').write_text('\n'.join(values))
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        for number in range(1, len(values) + 1):
            self.assertIn(f'hit.txt:{number}:', output)

    def test_simplified_and_big5(self):
        (self.root / 'sample.md').write_text('層只\n' + chr(0x5c42))
        rc, output = self.run_check()
        self.assertEqual(rc, 1)
        self.assertIn('sample.md:2:' + chr(0x5c42), output)
        self.assertNotIn('sample.md:1:', output)

    def test_exclusions_and_binary(self):
        for name in ('.git/private.txt', 'node_modules/private.js'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('PRIVATE_SAMPLE')
        (self.root / 'binary.bin').write_bytes(b'\x00PRIVATE_SAMPLE')
        (self.root / 'link').symlink_to(self.terms)
        rc, output = self.run_check()
        self.assertEqual(rc, 0, output)
        self.assertIn('未掃描的二進位檔：1', output)
        self.assertIn('binary.bin', output)
        (self.root / 'vendored').mkdir()
        (self.root / 'vendored' / 'source.py').write_text('PRIVATE_SAMPLE')
        self.assertEqual(self.run_check()[0], 1)

    def test_private_and_generic_rules_in_paths(self):
        for name in ('PRIVATE_FOLDER/clean.png', 'T-' + '1234/clean.txt'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'\x00')
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        self.assertIn('PRIVATE_FOLDER', output)
        self.assertIn('T-' + '1234', output)

    def test_empty_directory_and_symlink_names_are_checked_without_following(self):
        (self.root / 'PRIVATE_EMPTY').mkdir()
        (self.root / 'PRIVATE_LINK').symlink_to(self.terms)
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        self.assertIn('PRIVATE_EMPTY:1:', output)
        self.assertIn('PRIVATE_LINK:1:', output)
        self.assertNotIn('# comment', output)

    def test_text_detection_and_simplified_without_suffix_allowlist(self):
        for suffix in ('.svg', '.json', '.yml', '.yaml', '.toml', '.txt', '.css', '.HTML', '.SVG', ''):
            with self.subTest(suffix=suffix):
                path = self.root / ('sample' + suffix)
                path.write_text('PRIVATE_SAMPLE\n' + chr(0x5c42))
                rc, output = self.run_check()
                self.assertEqual(rc, 1, output)
                self.assertIn(path.name + ':1:PRIVATE_SAMPLE', output)
                self.assertIn(path.name + ':2:' + chr(0x5c42), output)
                path.unlink()

    def test_nul_after_first_8kb_still_scanned(self):
        (self.root / 'late.bin').write_bytes(b'a' * 8192 + b'\x00PRIVATE_SAMPLE')
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        self.assertIn('PRIVATE_SAMPLE', output)
        self.assertIn('未掃描的二進位檔：0', output)

    def test_archives_scan_contents_paths_and_binary_summary(self):
        members = {'nested/data.SVG': 'PRIVATE_SAMPLE\n'.encode() + chr(0x5c42).encode(),
                   'PRIVATE_FOLDER/image.bin': b'\x00data'}
        for suffix in ('.tgz', '.tar.gz', '.zip'):
            with self.subTest(suffix=suffix):
                path = self.root / 'vendored' / ('archive' + suffix)
                path.parent.mkdir(exist_ok=True)
                if suffix == '.zip':
                    with zipfile.ZipFile(path, 'w') as archive:
                        for name, data in members.items():
                            archive.writestr(name, data)
                else:
                    with tarfile.open(path, 'w:gz') as archive:
                        for name, data in members.items():
                            info = tarfile.TarInfo(name)
                            info.size = len(data)
                            archive.addfile(info, io.BytesIO(data))
                before = sorted(self.root.rglob('*'))
                rc, output = self.run_check()
                self.assertEqual(rc, 1, output)
                self.assertIn('!nested/data.SVG:1:PRIVATE_SAMPLE', output)
                self.assertIn('!nested/data.SVG:2:' + chr(0x5c42), output)
                self.assertIn('PRIVATE_FOLDER', output)
                self.assertIn('未掃描的二進位檔：1', output)
                self.assertEqual(sorted(self.root.rglob('*')), before)
                path.unlink()

    def test_corrupt_archive_fails_closed(self):
        (self.root / 'broken.zip').write_bytes(b'bad archive')
        rc, output = self.run_check()
        self.assertEqual(rc, 2, output)
        self.assertIn('壓縮檔無法檢查', output)

    def test_original_and_nfkc_are_both_checked(self):
        fullwidth = ''.join(chr(ord(c) + 0xfee0) if 0x21 <= ord(c) <= 0x7e else c
                            for c in 'PRIVATE_SAMPLE')
        self.terms.write_text('PRIVATE_[A-Z]+\n' + fullwidth + '\n')
        (self.root / (fullwidth + '.txt')).write_text(fullwidth)
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        self.assertIn(':1:' + fullwidth, output)
        self.assertIn(':1:' + unicodedata.normalize('NFKC', fullwidth), output)

    def test_ticket_number_three_to_four_digits(self):
        (self.root / 'tickets.txt').write_text('\n'.join('T-' + n for n in ('12', '123', '1234', '12345')))
        rc, output = self.run_check()
        self.assertEqual(rc, 1, output)
        self.assertIn('tickets.txt:2:', output)
        self.assertIn('tickets.txt:3:', output)
        self.assertNotIn('tickets.txt:1:', output)
        self.assertNotIn('tickets.txt:4:', output)

    def test_missing_terms(self):
        self.terms.unlink()
        rc, output = self.run_check()
        self.assertEqual(rc, 2)
        self.assertIn('私有字樣未檢查', output)
        self.assertEqual(self.run_check('--allow-missing-terms')[0], 0)

    def test_missing_opencc(self):
        with patch.object(checker.subprocess, 'run', side_effect=FileNotFoundError('missing')):
            rc, output = self.run_check('--allow-missing-terms')
        self.assertEqual(rc, 2)
        self.assertIn('簡體字未檢查', output)

    def test_invalid_regex_and_internal_terms(self):
        self.terms.write_text('[')
        self.assertEqual(self.run_check()[0], 2)
        self.terms = self.root / 'terms.txt'
        self.terms.write_text('secret')
        self.assertEqual(self.run_check()[0], 2)

    def test_environment_and_cli_precedence(self):
        script = str(Path(checker.__file__))
        env = dict(os.environ, FE_DESIGN_PRIVATE_TERMS=str(self.terms))
        result = subprocess.run(['python3', script, '--root', str(self.root)], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        result = subprocess.run(['python3', script, '--root', str(self.root), '--terms', str(self.base / 'absent')],
                                env=env, capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
