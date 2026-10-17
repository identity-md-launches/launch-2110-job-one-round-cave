# Lock Plan

Find a compatible selection that changes the fewest packages from a saved
selection. Use this when an updated requirement should preserve as much of a
worker's existing dependency choice as possible. It reports a proposed plan;
it never installs packages or changes the catalog or baseline.

Run the complete offline demonstration from the repository root:

```sh
python3 -B line-4/tools/lock-plan/plan.py demo
```

This run selected Requests **2.32.5** in place of **2.31.0**, retaining certifi
2025.8.3, charset-normalizer 3.4.3, idna 3.10 and urllib3 1.26.20. It proved a
minimum of **one package edit**, exhausting all reachable branches in **17 search
states**. The inherited resolver normally picks newer leaf versions; this
planner preserves the supplied baseline when that reduces edits.

The versions and requirements come from the existing [real PyPI metadata
projection](../offline-resolver/examples/sources.json). The bundled
[baseline](examples/baseline.json) is a chosen compatible selection from that
snapshot under the old `requests ==2.31.0` root, not an observed installation.
The current catalog requires `requests ==2.32.5` and `urllib3 <2`. No new metadata
was fetched. This is a historical finite-catalog example, not a recommendation
about which releases to use.

Requires Python 3.9+ and only the standard library. Keep the adjacent
`offline-resolver/` and `exhaustive-audit/` folders. Runtime has no network access,
package execution, account access, environment lookup or file writes. Inputs
must be explicit JSON files inside the current workspace, using the inherited
bounded loader. Paths escaping it, duplicate JSON keys and oversized inputs are
rejected before resolution. Output is JSON on stdout.

For your own catalog and saved package-to-version map:

```sh
python3 -B line-4/tools/lock-plan/plan.py path/to/catalog.json --baseline path/to/selection.json --max-steps 10000
```

A baseline is a plain object, for example `{"requests":"2.31.0","idna":"3.10"}`,
not a wrapped solver report. An empty baseline is allowed. Up to 1,000 entries
are accepted; names normalize case and punctuation as in Offline Resolver.
Alias collisions and unsupported numeric versions are rejected. Baseline
packages and versions may be absent from the new catalog, and the baseline need
not satisfy its new requirements. Those are normal inputs to migration planning.
The baseline does not pin anything: every mandatory root remains in force.

Catalogs use [Offline Resolver's exact schema and numeric constraint
grammar](../offline-resolver/README.md): one to four numeric version components,
conjunctions of comparisons or `*`, and mandatory release dependencies. Cycles
are supported. All selected packages must be reachable from current roots;
obsolete baseline packages are removed even if keeping an unused package would
cost fewer edits. Unreachable catalog releases have no effect.

Each **addition**, **removal**, or **version change** costs one package edit.
Changing a version counts once, not once for removal and once for addition.
Numeric aliases such as `1` and `1.0` compare equal and do not count as edits.
`changes` is sorted by canonical package name and gives each before/after version
and operation; an absent endpoint is JSON `null`. The selected map always uses
the catalog's version spellings. All packages have equal cost; this does not
minimize download size, operational risk, upgrade distance or security exposure.

The search chooses the currently needed package with the fewest viable releases,
then canonical name. For each package it tries a numerically equal baseline
release first, then newer numeric releases first. It backtracks over every
reachable selection, rebuilding requirements per branch so abandoned releases
leave no dependencies behind. Equal-cost ties retain the first assignment found
by that deterministic traversal. It does not globally maximize versions.

| Exit | Status | Claim |
| --- | --- | --- |
| 0 | `optimal` | A valid witness with `minimum_change_count`, proved by full branch exhaustion or attaining the zero lower bound. |
| 1 | `unsatisfiable` | Every reachable branch failed in this finite catalog. |
| 2 | `invalid` | Invalid input, unsupported grammar, path/read failure or rejected witness. |
| 3 | `inconclusive` | Budget/depth stopped the search; no minimum or impossibility claim. |

For `inconclusive`, an optional `best_found` contains a checked compatible
candidate and its edit count. This is an upper bound only: a later branch may
need fewer changes. There is no top-level `selected` or `minimum_change_count`
in that result. Never treat it as a completed optimization.

`--max-steps` accepts integers 1–1,000,000 (default 10,000). Each examined partial
selection, including the initial empty one, uses one state. Finishing exactly at
the budget succeeds. The search stops before selecting a 201st package on a
branch and reports inconclusive. Search is exponential; these limits do not
bound parsing, memory or wall-clock time. The implementation uses explicit
iterator frames rather than recursive search or a fully materialized frontier.

Every candidate witness is checked by Exhaustive Audit's separate iterative
edge/reachability checker, which does not use the planner's compatibility
predicate. Minimum claims still trust this planner's branch search. The
`input_sha256` binds normalized catalog plus baseline with sorted compact JSON;
it is not a signature. Constraint spelling and numeric version spelling can
change that digest even when their meanings match.

This is a compatibility plan, not an installable lockfile. Full packaging
semantics, interpreter/platform markers, extras, artifact hashes, availability,
security and publisher trust remain outside scope. Future or omitted releases
can change the optimum. It cannot certify the supplied baseline's provenance.

Checks:

```sh
python3 -B -m unittest discover -s line-4/tools/lock-plan -p 'test_*.py' -v
```

All **15 tests passed**, including 500 seeded catalogs compared against a separate
full Cartesian enumerator, a first-solution trap, nonoptimal candidates at budget
exhaustion, exact budget boundaries, cycles, abandoned dependencies, additions
and removals, missing historical versions, numeric aliases, deterministic ties,
depth limits, digest normalization, immutable inputs, separate witness rejection,
and CLI success/conflict/invalid/inconclusive paths. CLI loader tests write only
to `test/scratch/`; no test needs a network connection.
