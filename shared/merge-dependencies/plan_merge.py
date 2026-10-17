#!/usr/bin/env python3
"""Plan the fewest version edits after a reviewed, compatible catalog merge."""
import argparse
import json
import sys

import check_merge as first
import lock_plan
import second_check


def check(base, ours, theirs, baseline, max_steps=10000,
          max_assignments=10000, max_plan_steps=10000):
    """Return a proposal only after both compatibility checks finish and agree."""
    if type(max_plan_steps) is not int or not 1 <= max_plan_steps <= 1000000:
        raise ValueError('max_plan_steps must be an integer from 1 to 1000000')
    baseline = lock_plan.baseline_versions(baseline)
    checked = second_check.check(base, ours, theirs, max_steps, max_assignments)
    status = checked['status']
    result = {'format': 'dependency-merge-lock-plan/v1', 'status': status,
              'checked_merge': checked, 'baseline': baseline, 'plan': None,
              'limits': [
                  'Review and proposal only; no catalog, baseline or package is changed.',
                  'A plan is attempted only after two completed compatible searches agree.',
                  'Minimum counts packages added, removed or version-changed in the finite catalog.',
                  'Publisher trust, artifacts, platform rules and installability are outside scope.']}
    if status == 'resolved':
        catalog = first.parse(checked['review']['merge']['merged'])
        proposal = lock_plan.plan(catalog, baseline, max_plan_steps)
        result['plan'] = proposal
        result['status'] = {'optimal': 'planned', 'inconclusive': 'inconclusive',
                            'unsatisfiable': 'disagreement'}[proposal['status']]
    elif status == 'unsatisfiable':
        result['status'] = 'incompatible'
    return result


def demo(max_steps=10000, max_assignments=10000, max_plan_steps=10000):
    folder = first.HERE / 'examples'
    texts = [first.review.engine.read_text(folder / f'plan-{part}.json')
             for part in ('base', 'ours', 'theirs')]
    baseline = lock_plan.fmt.load(folder / 'baseline.json')
    return check(*texts, baseline, max_steps, max_assignments, max_plan_steps)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('demo', 'check'):
        item = sub.add_parser(name)
        if name == 'check':
            for branch in ('base', 'ours', 'theirs'):
                item.add_argument(branch)
            item.add_argument('--baseline', required=True,
                              help='workspace-local package-to-version JSON')
        item.add_argument('--max-steps', type=int, default=10000)
        item.add_argument('--max-assignments', type=int, default=10000)
        item.add_argument('--max-plan-steps', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo(args.max_steps, args.max_assignments, args.max_plan_steps)
        else:
            texts = [first.review.engine.read_text(p) for p in
                     (args.base, args.ours, args.theirs)]
            baseline = lock_plan.fmt.load(args.baseline)
            result = check(*texts, baseline, args.max_steps,
                           args.max_assignments, args.max_plan_steps)
        code = {'planned': 0, 'incompatible': 1, 'text_conflict': 1,
                'invalid_catalog': 2, 'inconclusive': 3, 'disagreement': 4}[result['status']]
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (ValueError, OSError, TypeError, RecursionError):
        print(json.dumps({'status': 'invalid',
                          'error': 'Invalid workspace inputs or budgets.'}),
              file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
