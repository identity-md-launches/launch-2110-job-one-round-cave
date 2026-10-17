#!/usr/bin/env python3
"""Find a compatible finite-catalog selection with minimum package edits."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def module(name, relative):
    path = Path(__file__).resolve().parent / relative
    if not path.is_relative_to(Path.cwd().resolve()):
        raise RuntimeError('run from the workspace containing the tools')
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


fmt = module('lock_plan_format', 'resolve.py')
checker = module('lock_plan_checker', 'exhaustive.py')


def baseline_versions(data):
    if not isinstance(data, dict) or len(data) > 1000:
        raise fmt.Invalid('baseline must be an object of at most 1000 package versions')
    result = {}
    for raw, release in data.items():
        package = fmt.name(raw)
        fmt.version(release)
        if package in result:
            raise fmt.Invalid('duplicate canonical baseline package ' + package)
        result[package] = release
    return dict(sorted(result.items()))


def changes(before, after):
    """Version spelling aliases compare numerically; every package operation costs 1."""
    result = []
    for package in sorted(before.keys() | after.keys()):
        old, new = before.get(package), after.get(package)
        if old is not None and new is not None and fmt.version(old) == fmt.version(new):
            continue
        result.append({'package': package, 'before': old, 'after': new,
                       'operation': 'add' if old is None else 'remove' if new is None else 'change'})
    return result


def plan(data, baseline, max_steps=10000):
    if type(max_steps) is not int or not 1 <= max_steps <= 1000000:
        raise fmt.Invalid('max_steps must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    baseline = baseline_versions(baseline)
    bound_input = {'catalog': {'packages': packages, 'roots': roots}, 'baseline': baseline}
    digest = hashlib.sha256(json.dumps(bound_input, sort_keys=True,
                                      separators=(',', ':')).encode()).hexdigest()
    base = {'method': 'minimum-package-edits-v1', 'input_sha256': digest,
            'baseline': baseline, 'max_steps': max_steps}
    steps = 0
    best = None
    # Explicit DFS frames retain iterators instead of materializing every branch.
    # Each selection is reachable: only a currently needed package is added.
    frames = [iter([{}])]

    def incomplete(reason):
        result = dict(base, status='inconclusive', steps=steps, reason=reason)
        if best is not None:
            result['best_found'] = best
        return result

    while frames:
        selected = next(frames[-1], None)
        if selected is None:
            frames.pop()
            continue
        if steps == max_steps:
            return incomplete('search state budget exhausted')
        steps += 1
        needed = {p: [s] for p, s in roots.items()}
        for p, v in selected.items():
            for q, constraint in packages[p][v].items():
                needed.setdefault(q, []).append(constraint)
        choices = []
        impossible = False
        for p in sorted(needed):
            constraints = needed[p]
            if p in selected:
                if not all(fmt.accepts(selected[p], s) for s in constraints):
                    impossible = True
                    break
            else:
                allowed = [v for v in packages.get(p, {})
                           if all(fmt.accepts(v, s) for s in constraints)]
                if not allowed:
                    impossible = True
                    break
                allowed.sort(key=fmt.version, reverse=True)
                old = baseline.get(p)
                if old is not None:
                    allowed.sort(key=lambda v: fmt.version(v) != fmt.version(old))
                choices.append((len(allowed), p, allowed))
        if impossible:
            continue
        if not choices:
            selected = dict(sorted(selected.items()))
            if checker.assignment(packages, roots, selected) != selected:
                raise fmt.Invalid('search returned an invalid or unreachable assignment')
            edits = changes(baseline, selected)
            candidate = {'selected': selected, 'changes': edits, 'change_count': len(edits)}
            if best is None or len(edits) < best['change_count']:
                best = candidate
            if best['change_count'] == 0:
                return dict(base, status='optimal', steps=steps,
                            optimality='zero lower bound attained', minimum_change_count=0, **best)
            continue
        if len(selected) >= 200:
            return incomplete('selection depth exceeds 200 packages')
        _, p, allowed = min(choices)
        # Bind parent/package as function arguments: suspended frames must never
        # capture loop variables changed by a deeper search state.
        def children(parent, package, versions):
            for v in versions:
                yield dict(parent, **{package: v})
        frames.append(children(selected, p, allowed))
    if best is None:
        return dict(base, status='unsatisfiable', steps=steps)
    return dict(base, status='optimal', steps=steps, optimality='all reachable branches exhausted',
                minimum_change_count=best['change_count'], **best)


