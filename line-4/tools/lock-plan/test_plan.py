import copy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('lock_plan', Path(__file__).with_name('plan.py'))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PlanTests(unittest.TestCase):
    def trap(self):
        # The first baseline-preferred branch needs two changes; another needs one.
        return {'packages': {'a': {'1': {'x': '==2', 'y': '==2'},
                                  '2': {'x': '==1', 'y': '==1'}},
                             'x': {'1': {}, '2': {}}, 'y': {'1': {}, '2': {}}},
                'roots': {'a': '*'}}

    def test_global_minimum_not_first_solution(self):
        result = p.plan(self.trap(), {'a': '1', 'x': '1', 'y': '1'})
        self.assertEqual(result['status'], 'optimal')
        self.assertEqual(result['minimum_change_count'], 1)
        self.assertEqual(result['selected'], {'a': '2', 'x': '1', 'y': '1'})
        self.assertEqual(result['changes'], [{'package': 'a', 'before': '1',
                                             'after': '2', 'operation': 'change'}])

    def test_budget_keeps_witness_without_minimum_claim(self):
        result = p.plan(self.trap(), {'a': '1', 'x': '1', 'y': '1'}, 4)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertEqual(result['best_found']['change_count'], 2)
        self.assertNotIn('minimum_change_count', result)
        self.assertNotIn('selected', result)
        data = self.trap()
        self.assertEqual(p.checker.assignment(data['packages'], data['roots'],
                                             result['best_found']['selected']),
                         result['best_found']['selected'])
        early = p.plan(data, {}, 1)
        self.assertNotIn('best_found', early)

    def test_exact_budget_edges(self):
        data, baseline = self.trap(), {'a': '1', 'x': '1', 'y': '1'}
        complete = p.plan(data, baseline)
        self.assertEqual(p.plan(data, baseline, complete['steps'])['status'], 'optimal')
        self.assertEqual(p.plan(data, baseline, complete['steps'] - 1)['status'], 'inconclusive')
        bad = {'packages': {}, 'roots': {'missing': '*'}}
        self.assertEqual(p.plan(bad, {}, 1)['status'], 'unsatisfiable')

    def test_zero_changes_equivalent_numeric_spelling(self):
        data = {'packages': {'A_B': {'1.0': {}, '2': {}}}, 'roots': {'a.b': '*'}}
        result = p.plan(data, {'A-B': '1'}, 2)
        self.assertEqual(result['status'], 'optimal')
        self.assertEqual(result['minimum_change_count'], 0)
        self.assertEqual(result['selected'], {'a-b': '1.0'})
        self.assertEqual(result['optimality'], 'zero lower bound attained')

    def test_add_remove_and_unknown_historical_version(self):
        data = {'packages': {'a': {'2': {'b': '*'}}, 'b': {'1': {}}}, 'roots': {'a': '*'}}
        result = p.plan(data, {'a': '1', 'unused': '9'})
        self.assertEqual(result['minimum_change_count'], 3)
        self.assertEqual([c['operation'] for c in result['changes']], ['change', 'add', 'remove'])
        self.assertEqual([c['package'] for c in result['changes']], ['a', 'b', 'unused'])

    def test_backtrack_discards_old_dependencies(self):
        data = {'packages': {'a': {'1': {'missing': '*'}, '2': {}},
                             'unused': {'1': {'missing': '*'}}}, 'roots': {'a': '*'}}
        result = p.plan(data, {'a': '1'})
        self.assertEqual(result['selected'], {'a': '2'})
        self.assertEqual(result['minimum_change_count'], 1)

    def test_cycles_and_unsatisfiable(self):
        data = {'packages': {'a': {'1': {'b': '==1'}}, 'b': {'1': {'a': '==1'}}},
                'roots': {'a': '*'}}
        self.assertEqual(p.plan(data, {})['selected'], {'a': '1', 'b': '1'})
        data['packages']['b']['1']['a'] = '==2'
        result = p.plan(data, {})
        self.assertEqual(result['status'], 'unsatisfiable')
        self.assertNotIn('selected', result)
        self.assertNotIn('minimum_change_count', result)

    def test_determinism_normalization_immutability_and_digest(self):
        data, baseline = self.trap(), {'a': '1', 'x': '1', 'y': '1'}
        before = copy.deepcopy((data, baseline))
        result = p.plan(data, baseline)
        data['packages'] = dict(reversed(list(data['packages'].items())))
        self.assertEqual(result, p.plan(data, dict(reversed(list(baseline.items())))))
        self.assertEqual((data, baseline), before)
        self.assertNotEqual(result['input_sha256'], p.plan(data, {})['input_sha256'])
        a = p.plan({'packages': {'A_B': {'1': {}}}, 'roots': {'A.B': '*'}}, {'A-B': '1'})
        b = p.plan({'packages': {'a-b': {'1': {}}}, 'roots': {'a-b': '*'}}, {'a-b': '1'})
        self.assertEqual(a, b)

    def test_tie_uses_baseline_then_high_versions(self):
        data = {'packages': {'a': {'1': {}, '2': {}, '3': {}}}, 'roots': {'a': '*'}}
        self.assertEqual(p.plan(data, {})['selected'], {'a': '3'})
        self.assertEqual(p.plan(data, {'a': '1'})['selected'], {'a': '1'})
        data['roots']['a'] = '>=2'
        self.assertEqual(p.plan(data, {'a': '1'})['selected'], {'a': '3'})

    def test_depth_limit_is_inconclusive(self):
        packages = {'p' + str(i): {'1': {'p' + str(i+1): '*'}} for i in range(201)}
        packages['p201'] = {'1': {}}
        result = p.plan({'packages': packages, 'roots': {'p0': '*'}}, {}, 1000)
        self.assertEqual(result['status'], 'inconclusive')
        self.assertIn('depth', result['reason'])
        self.assertNotIn('minimum_change_count', result)

    def test_invalid_baselines_catalogs_and_budgets(self):
        for baseline in ([], None, {'a': None}, {'a': 'v1'}, {'a': '01'},
                         {'A_B': '1', 'a.b': '2'}, {'../a': '1'},
                         {'p'+str(i): '1' for i in range(1001)}):
            with self.assertRaises(p.fmt.Invalid):
                p.plan(self.trap(), baseline)
        for value in (True, 0, -1, 1000001, 1.5):
            with self.assertRaises(p.fmt.Invalid):
                p.plan(self.trap(), {}, value)
        with self.assertRaises(p.fmt.Invalid):
            p.plan({'packages': {}, 'roots': {}}, {})
        with self.assertRaises(p.fmt.Invalid):
            p.plan({'packages': {}, 'roots': {'a': '^1'}}, {})

    def test_independent_witness_check_rejects_bad_search(self):
        with patch.object(p.checker, 'assignment', return_value=None):
            with self.assertRaises(p.fmt.Invalid):
                p.plan(self.trap(), {})

    def test_seeded_all_assignments_oracle(self):
        rng = random.Random(2504)
        for _ in range(500):
            names = ['a', 'b', 'c', 'd']
            packages = {a: {v: {b: rng.choice(['==1', '==2', '*', '!=1'])
                                     for b in names + ['missing'] if rng.random() < .15}
                            for v in ['1', '2'] if rng.random() < .85} for a in names}
            roots = {a: rng.choice(['*', '==1', '==2'])
                     for a in rng.sample(names, rng.randint(1, 4))}
            baseline = {a: rng.choice(['1', '2', '3'])
                        for a in names + ['obsolete'] if rng.random() < .6}
            result = p.plan({'packages': packages, 'roots': roots}, baseline)
            costs = []
            # Independent full Cartesian oracle includes absent/unreachable
            # choices, unlike the planner's reachable search and pruning.
            for values in itertools.product(*[[None] + list(packages[a]) for a in names]):
                chosen = p.checker.assignment(packages, roots, dict(zip(names, values)))
                if chosen is not None:
                    # Independent edit count, not plan.changes().
                    costs.append(sum(baseline.get(a) != chosen.get(a)
                                     for a in baseline.keys() | chosen.keys()))
            if costs:
                self.assertEqual(result['status'], 'optimal')
                self.assertEqual(result['minimum_change_count'], min(costs))
                self.assertEqual(p.checker.assignment(packages, roots, result['selected']),
                                 result['selected'])
            else:
                self.assertEqual(result['status'], 'unsatisfiable')

    def test_custom_cli_and_bounded_duplicate_key_loader(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, '-B', str(Path(__file__).with_name('plan.py'))]
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            catalog, baseline = Path(temp) / 'catalog.json', Path(temp) / 'baseline.json'
            catalog.write_text(json.dumps(self.trap()))
            baseline.write_text(json.dumps({'a': '1', 'x': '1', 'y': '1'}))
            args = command + [str(catalog), '--baseline', str(baseline)]
            run = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)['minimum_change_count'], 1)
            for text in ('{"a":"1","a":"2"}', ' ' * 1000001, '{broken', '[]'):
                baseline.write_text(text)
                run = subprocess.run(args, capture_output=True, text=True)
                self.assertEqual(run.returncode, 2, run.stderr)
                self.assertEqual(json.loads(run.stdout)['status'], 'invalid')
            baseline.write_text('{}')
            catalog.write_text('{"packages":{},"roots":{"missing":"*"}}')
            run = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'], 'unsatisfiable')

    def test_real_demo_and_cli_codes(self):
        command = [sys.executable, '-B', str(Path(__file__).with_name('plan.py'))]
        run = subprocess.run(command + ['demo'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['minimum_change_count'], 1)
        self.assertEqual([c['package'] for c in result['changes']], ['requests'])
        for args, code in ((['demo', '--max-steps', '1'], 3),
                           (['demo', '--max-steps', '0'], 2),
                           (['demo', '--baseline', 'ignored.json'], 2),
                           (['missing.json'], 2),
                           (['/etc/passwd', '--baseline', '/etc/passwd'], 2)):
            run = subprocess.run(command + args, capture_output=True, text=True)
            self.assertEqual(run.returncode, code, run.stderr)
            json.loads(run.stdout)


if __name__ == '__main__':
    unittest.main()
