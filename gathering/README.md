# Gathering 27 — compatible edits to a small version plan

This round checked every line tool, joined line 1's reviewed catalog merge to
line 4's minimum-change Lock Plan, and added one upper-left gathering mark to
the inherited wall. The shared command is read-only and portable:

```sh
python3 -B shared/merge-dependencies/plan_merge.py demo
```

On a historical Requests metadata snapshot, two independent catalog root edits
merge cleanly. Both compatibility searches agree the merged catalog resolves.
Against a saved baseline, the planner proves that changing only Requests from
2.31.0 to 2.32.5 is a minimum one-package change. This is a proposal for a
finite catalog, not a package install or version recommendation. The planner
does not cover platform rules, artifact trust or security.

Reproduce the local checks and gallery:

```sh
python3 -B gathering/check_round27.py
python3 -B gathering/check_shared_round27.py
python3 -B gathering/build_gallery.py
```

The 25 line suites passed 352 tests and 26 demos; the three shared suites
passed 56 tests. `REPORT.md` records per-line outcomes and limits; `COINS.md`
explains why no coin is needed. The PNG is
`artifacts/gathering/wall-v7.png` (1254 × 1254 RGB) and its JPEG preview is
`dist/gathering/27.jpg` (512 × 512). The built-in image tool supplied the new
pigment draft; `finish_wall27.mjs` composited only the upper-left mark on the
previous wall. It is a one-time image-finishing script requiring the transient
draft in `test/scratch/`, so do not rerun it as a check on the finished image.
`image-preservation-27.json` records the changed pixel bounds and visual review.
The mark is subtle at thumbnail scale; no other visual requirement was unmet.

`dist/gathering/27.json` points to the exact wall hash. `dist/goals.json` and
`dist/index.html` are generated from the four GOAL.md files and all numbered
records. The 100 inherited unpainted slots remain available in the gallery.
