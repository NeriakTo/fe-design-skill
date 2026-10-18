"""驗證彙整腳本在單項失敗後仍繼續，並保留略過結果。"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class VerifyTests(unittest.TestCase):
    def check(self, failed_suite, *args, missing_terms=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'repo'
            (root / 'tools').mkdir(parents=True)
            shutil.copy(Path(__file__).parents[1] / 'verify.sh', root / 'tools/verify.sh')
            if missing_terms:
                shutil.copy(Path(__file__).parents[1] / 'check_public.py', root / 'tools/check_public.py')
            tests = root / 'skills/starter-components/tools/test'
            tests.mkdir(parents=True)
            for name in ('demo-structure.mjs', 'regression.mjs'):
                (tests / name).touch()
            bin_dir = root / 'bin'
            bin_dir.mkdir()
            for name, script in {
                'python3': ('#!/bin/bash\necho "執行 $*"\n'
                            'if [ "$1" = "tools/check_public.py" ] && [ "$VERIFY_REAL_PUBLIC" = "1" ]; then\n'
                            '  exec "$VERIFY_REAL_PYTHON" "$@"\nfi\n'
                            'case "$*" in *"$FAIL_SUITE"*) exit 7;; esac\nexit 0\n'),
                'node': '#!/bin/bash\nif [ "$1" = "-e" ]; then exit 1; fi\nexit 0\n',
            }.items():
                path = bin_dir / name
                path.write_text(script)
                path.chmod(0o755)
            env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ['PATH'], FAIL_SUITE=failed_suite)
            env.update(VERIFY_REAL_PUBLIC=str(int(missing_terms)), VERIFY_REAL_PYTHON=sys.executable)
            if missing_terms:
                env['FE_DESIGN_PRIVATE_TERMS'] = str(Path(directory) / 'missing-terms.txt')
            return subprocess.run(['bash', str(root / 'tools/verify.sh'), *args], cwd=root,
                                  env=env, text=True, capture_output=True)

    def test_success_with_explicit_skip(self):
        result = self.check('no-match')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('SKIP (playwright 不存在)', result.stdout)
        self.assertIn('check-public: PASS', result.stdout)

    def test_failure_continues_to_public_check(self):
        result = self.check('anti-slop-review')
        self.assertEqual(result.returncode, 1)
        self.assertIn('anti-slop-review: FAIL (exit=7)', result.stdout)
        self.assertIn('check-public: PASS', result.stdout)

    def test_public_check_failure_propagates(self):
        result = self.check('check_public.py')
        self.assertEqual(result.returncode, 1)
        self.assertIn('check-public: FAIL (exit=7)', result.stdout)

    def test_missing_terms_allowed(self):
        result = self.check('no-match', '--allow-missing-terms', missing_terms=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('私有字樣未檢查', result.stdout)
        self.assertIn('check-public: PASS', result.stdout)

    def test_missing_terms_required_by_default(self):
        result = self.check('no-match', missing_terms=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('私有字樣未檢查', result.stdout)
        self.assertIn('check-public: FAIL (exit=2)', result.stdout)
