import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'refclash'
loader = importlib.machinery.SourceFileLoader('refclash', str(TOOL))
spec = importlib.util.spec_from_loader(loader.name, loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
OID = 'a' * 40


def listing(*names):
    return ''.join(OID + '\t' + name + '\n' for name in names)


class RefClashTests(unittest.TestCase):
    def test_case(self):
        report = m.analyze(m.parse_refs(listing('refs/tags/V1', 'refs/tags/v1')))
        self.assertEqual(report['findings'], [{'kind': 'ascii_case', 'ref_count': 2}])
        self.assertNotIn('V1', json.dumps(report))

    def test_prefix(self):
        report = m.analyze(['refs/heads/Fix', 'refs/heads/fix/deep/topic'], True)
        self.assertEqual(report['findings'][0]['kind'], 'directory_prefix')
        self.assertEqual(len(report['findings'][0]['refs']), 2)

    def test_namespaces_separate(self):
        self.assertFalse(m.analyze(['refs/heads/A', 'refs/tags/a'])['findings'])

    def test_siblings_not_collision(self):
        self.assertFalse(m.analyze(['refs/heads/Fix/a', 'refs/heads/fix/b'])['findings'])

    def test_nonascii_not_normalized(self):
        report = m.analyze(['refs/tags/Ä', 'refs/tags/ä'])
        self.assertFalse(report['findings'])
        self.assertEqual(report['non_ascii_refs'], 2)

    def test_duplicates_peeled_and_head(self):
        self.assertEqual(m.parse_refs(listing('HEAD', 'refs/tags/v1', 'refs/tags/v1',
                                            'refs/tags/v1^{}')), ['refs/tags/v1'])

    def test_invalid(self):
        for name in ['refs/heads/a b', 'refs/heads/a..b', 'refs/heads/.hidden',
                     'refs/heads/x.lock', 'refs/heads/a//b']:
            with self.assertRaises(ValueError):
                m.parse_refs(listing(name))
        with self.assertRaises(ValueError):
            m.parse_refs('garbage')

    def test_sha256(self):
        self.assertEqual(len(m.parse_refs('b' * 64 + '\trefs/heads/main\n')), 1)

    def test_remote_validation_no_execution(self):
        from argparse import Namespace
        for url in ['ext::bad', 'file:///test', 'https://user:secret@example.com/repo',
                    'https://example.com/repo?token=secret']:
            with patch.object(m.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    m.git_listing(Namespace(remote=url, repo='.'))
                run.assert_not_called()

    def test_unknown_does_not_leak(self):
        result = subprocess.run([sys.executable, str(TOOL), '--stdin', '--json'],
                                input='private malformed secret', text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)['status'], 'UNKNOWN')
        self.assertNotIn('secret', result.stdout + result.stderr)

    def test_stdin_exit_codes(self):
        for names, code in [(('refs/heads/main',), 0),
                            (('refs/tags/A', 'refs/tags/a'), 2)]:
            result = subprocess.run([sys.executable, str(TOOL), '--stdin', '--json'],
                                    input=listing(*names), text=True, capture_output=True)
            self.assertEqual(result.returncode, code)

    def test_real_git_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(['git', 'init', '-q', tmp], check=True)
            env = dict(os.environ, GIT_AUTHOR_NAME='Fixture', GIT_AUTHOR_EMAIL='fixture@example.invalid',
                       GIT_COMMITTER_NAME='Fixture', GIT_COMMITTER_EMAIL='fixture@example.invalid')
            # Prevent commit-triggered background maintenance racing the snapshot.
            # Do not filter lock files: retain the full byte-for-byte assertion.
            subprocess.run(['git', '-C', tmp, '-c', 'core.hooksPath=/dev/null',
                            '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
                            'commit', '--allow-empty', '-qm', 'fixture'], env=env, check=True)
            before = {str(p.relative_to(tmp)): p.read_bytes() for p in Path(tmp).rglob('*') if p.is_file()}
            result = subprocess.run([sys.executable, str(TOOL), '--repo', tmp, '--json'],
                                    capture_output=True, text=True)
            after = {str(p.relative_to(tmp)): p.read_bytes() for p in Path(tmp).rglob('*') if p.is_file()}
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(json.loads(result.stdout)['refs_checked'], 1)
            self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
