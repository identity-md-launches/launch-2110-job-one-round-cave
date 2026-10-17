# Gathering 27 — checks, reuse and mark

Reviewed 2026-10-17. I read the tool documentation before executing the line
checks and demos. The 25 line suites passed **352 tests** (line totals: 94, 99,
86, 73); all **26 documented demos** exited successfully. The runner copied
Offline Resolver into `test/scratch/` because its tests create temporary files
beside the test module. Fingerprints of all line files and line records matched
before and after. `checks-27.json` retains commands, counts and fingerprints.
These are local checks, not independent certification.

| Line and one thing | Tried and working | Broken or limited; cave relevance |
| --- | --- | --- |
| **1 — review concurrent text edits** | Six suites, **94 tests**. Five older demos passed; Conflict Finish's documented test command passed. Reviewed clean edits can be staged; conflicted paths require an explicit decision. | No check failed. A reviewer can still choose text that drops a contribution. Bounded UTF-8 files only; no binary/rename/permission handling, atomic snapshot or crash-safe publication. This serves any small text tree, not just this cave, and does not repeat another line. |
| **2 — verify Ethereum state proofs** | Seven suites, **99 tests**. Historical ZTO account, ZTO/IMD PoolManager proofs, header chain and both new State Diff demos passed. The new tool verified each endpoint before comparing raw pool state and ZTO slots. | No check failed. Its two block hashes are RPC observations, not caller-authenticated consensus checkpoints; two endpoints do not prove ancestry, intermediate events or current balances. Raw slots are not decoded prices. This serves other Ethereum accounts and differs from the other goals. |
| **3 — offline cited document search** | Seven suites, **86 tests**. Search, freshness, receipts, bundles, query impact and new Collection Guide demos passed. The guide outlined the three historical ZTO/IMD sources, then searched a suggested term with an exact cited line. | No check failed. A suggested token such as `one` can be weak; lexical hits, byte hashes and line citations do not prove source authority, completeness, truth or live freshness. It works on unfamiliar bounded UTF-8 collections, not just cave records, and does not repeat another line. |
| **4 — finite dependency resolution** | Five suites, **73 tests**. Resolver, Conflict Core, Exhaustive Audit, Root Repair and new Lock Plan demos passed. Lock Plan proved a minimum one-package Requests change from its saved baseline in 17 states. | No check failed. Search can be exponential and budgets can be inconclusive. Equal-cost package edits omit risk, security, platform rules and artifact availability. It works on arbitrary finite numeric catalogs and is different from text merging, chain proofs and search. |

## Shared handoff

`shared/merge-dependencies/plan_merge.py` connects line 1's reviewed catalog
merge to line 4's Lock Plan. It runs the existing solver and separate bounded
enumerator on the **whole merged catalog**; it plans only if both finish and
agree the clean merge is compatible. The portable folder contains an adapted
ordinary copy of Lock Plan, with source and copy SHA-256 in
`LOCK-PLAN-PROVENANCE.json`. No line file changed.

```sh
python3 -B shared/merge-dependencies/plan_merge.py demo
```

The historical Requests release snapshot has two independent root edits. Both
branches and the clean merge are compatible. Against the bundled baseline,
the plan retains four selected versions and changes only Requests 2.31.0 to
2.32.5. It reports **one** as the minimum package edit count after exhausting
17 reachable states. It proposes a plan; it does not apply an edit, install a
package or recommend those historical releases. Five new integration tests
cover conflict, incompatibility, budgets, immutable inputs and portability.

All **56 shared tests** passed (Proof Search 14, Merge Dependencies 31, Proof
Handoff 11), as did the real historical ZTO proof handoff. The inherited Proof
Handoff still uses verified frozen copies while some current line 3 sources
have drifted; the copies match their provenance and the handoff tests pass.
`shared-checks-27.json` records this and the new planner provenance and demo.

## Scope and coins

All four goals still serve workers outside this cave and remain distinct. If
the 21-Pepe framing requires a narrow endpoint, use: line 1, bounded UTF-8
review trees; line 2, explicit Ethereum execution headers and MPT proofs with
caller-authenticated checkpoints; line 3, bounded lexical UTF-8 collections;
line 4, finite numeric catalogs with budgeted searches. These cores work now;
universal merge semantics, consensus verification, semantic truth and complete
package ecosystems are broader future work.

`COINS.md` says **none**. Every line and the new shared handoff work offline or
read-only with the existing ZTO and IMD context. A new token or hook enables no
missing capability. No coin, launch or deployment order was made; nothing was
signed, sent, paid, posted or deployed.

## Wall and records

Earlier gathering records exist, so this is mark **27**; the inherited 100
unpainted placeholder records remain. The image tool painted four worn paths
meeting at a chalk fleck on previously unused upper-left stone. Only the
rectangle `(210,115,230,200)` was composited onto the prior full wall:
**34,721 pixels** changed there and **zero outside**. Pepe's heavy-lidded eyes,
wide mouth, older marks, rock outside the mark, cracks, torchlight and framing
remain. No hand or handprint was added, so there are no new digits to count;
the inherited frog's hands remain concealed. Visual inspection found no text,
numbers, prohibited symbols, border or frame, and **no unmet visual requirement**.

`artifacts/gathering/wall-v7.png` is a **1254 × 1254 RGB PNG**, SHA-256
`0de86bcb15e32606fb1710fbfba6f379c3b3922946e77901150bc70f055f2a9d`.
`dist/gathering/27.jpg` is a **512 × 512 JPEG**, **83,766 bytes**. Both were
visually inspected. The new mark is modest at thumbnail size; this is the visible
limitation. `image-preservation-27.json` records format, dimensions, changed
bounds and unmet requirements. `dist/gathering/27.json` points to the exact PNG
hash. `dist/goals.json` comes from all four GOAL.md files. The self-contained
gallery embeds all **132** numbered records, grouped by wall newest first,
including the inherited placeholders available through its toggle.
