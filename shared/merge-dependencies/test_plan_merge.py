"""Checks for the compatible merge to minimum-change plan handoff."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import plan_merge


class PlanMergeTests(unittest.TestCase):
    def setUp(self):
        self.folder = Path(__file__).parent / 'examples'
        self.texts = [(self.folder / f'plan-{part}.json').read_text()
                      for part in ('base', 'ours', 'theirs')]
        self.baseline = json.loads((self.folder / 'baseline.json').read_text())

    def test_real_metadata_merge_needs_one_change(self):
        before = [(self.folder / f'plan-{part}.json').read_bytes()
                  for part in ('base', 'ours', 'theirs')]
        result = plan_merge.check(*self.texts, self.baseline)
        self.assertEqual(result['status'], 'planned')
        self.assertEqual(result['checked_merge']['status'], 'resolved')
        self.assertEqual(result['checked_merge']['enumeration']['status'], 'resolved')
        self.assertEqual(result['plan']['minimum_change_count'], 1)
        self.assertEqual(result['plan']['changes'], [{
            'package': 'requests', 'before': '2.31.0', 'after': '2.32.5',
            'operation': 'change'}])
        self.assertEqual(result['plan']['selected']['idna'], '3.10')
        self.assertEqual(before, [(self.folder / f'plan-{part}.json').read_bytes()
                                  for part in ('base', 'ours', 'theirs')])
        self.assertEqual(self.baseline['requests'], '2.31.0')

    def test_incompatible_merge_does_not_invoke_planner(self):
        texts = [(self.folder / f'{part}.json').read_text()
                 for part in ('base', 'ours', 'theirs')]
        with patch.object(plan_merge.lock_plan, 'plan', side_effect=AssertionError):
            result = plan_merge.check(*texts, self.baseline)
        self.assertEqual(result['status'], 'incompatible')
        self.assertIsNone(result['plan'])

    def test_text_conflict_and_budget_skip_plan(self):
        base, ours, _ = self.texts
        competing = ours.replace('"requests": "==2.32.5"',
                                 '"requests": "==2.25.1"')
        with patch.object(plan_merge.lock_plan, 'plan', side_effect=AssertionError):
            conflict = plan_merge.check(base, ours, competing, self.baseline)
            limited = plan_merge.check(*self.texts, self.baseline,
                                       max_assignments=1)
        self.assertEqual(conflict['status'], 'text_conflict')
        self.assertEqual(limited['status'], 'inconclusive')
        self.assertIsNone(conflict['plan'])
        self.assertIsNone(limited['plan'])

    def test_planning_budget_and_invalid_baseline(self):
        result = plan_merge.check(*self.texts, self.baseline, max_plan_steps=1)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(result['plan']['status'], 'inconclusive')
        with self.assertRaises(ValueError):
            plan_merge.check(*self.texts, {'requests': 'invented'})
        with self.assertRaises(ValueError):
            plan_merge.check(*self.texts, self.baseline, max_plan_steps=0)

    def test_demo_cli_and_portable_copy(self):
        script = Path(__file__).parent / 'plan_merge.py'
        command = [sys.executable, '-B', str(script), 'demo']
        proc = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['status'], 'planned')
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            copy = Path(temp) / 'merge-dependencies'
            shutil.copytree(script.parent, copy)
            proc = subprocess.run([sys.executable, '-B', str(copy / 'plan_merge.py'),
                                   'demo'], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout)['plan']['minimum_change_count'], 1)


if __name__ == '__main__':
    unittest.main()
