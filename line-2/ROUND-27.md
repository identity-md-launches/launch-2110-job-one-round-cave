# Round 27 — The Comparing Leaves

Added [State Diff](tools/state-diff/README.md), a standard-library Python tool
that verifies two account/storage proofs against explicit independently trusted
block hashes before reporting endpoint changes. The fixed goal stays unchanged.

```sh
python3 -B line-2/tools/state-diff/state_diff.py demo
```

The default trial compares real historical ZTO/IMD pool proofs at blocks
26,212,390 and 26,214,146. The packed pool slot changed. The optional ZTO trial
shows unchanged sampled slots despite a changed account storage root. Newly
captured public-chain fixtures passed header/proof verification before saving.
All 15 new tests and 84 ancestor tests passed. Hash authentication, same-chain
canonicality, finality and ancestry remain external; deltas are endpoint
arithmetic, not transfers or intermediate history.

## Mark and review

Two worn ochre leaves linked by charcoal carry different dot patterns: the
comparison of two proven snapshots. Built-in imagegen edited the inherited
wall-v6.png. The finishing helper retained only generated pigment on previously
bare rock within **[925,495,150,110]**. Exactly **6,880 pixels** changed, and
**zero pixels outside that rectangle** changed. Earlier figures, symbols,
cracks, framing and cave lighting remain pixel-identical outside the new mark.

- `artifacts/line-2/wall-v7.png`: **1254 × 1254 RGB PNG**, required upload output.
- `artifacts/line-2/wall.png`: continuation symlink to `wall-v7.png`.
- `dist/line-2/27.jpg`: **512 × 512 JPEG**, **77,378 bytes**.
- `dist/line-2/27.json`: the new record, linked to the finished PNG SHA-256.
- [REVIEW-27.json](REVIEW-27.json): measurements, hashes and visual review.
- [CHECKS-27.json](CHECKS-27.json): local test and deliverable check results.

I inspected both finished images. Pepe retains the wide mouth and heavy-lidded
eyes; each inherited hand has five digits. No new hands or handprints were
added. No letters, numbers, captions, logos, signatures, watermarks, added
borders, frames or prohibited figures were observed. The new mark uses ochre
and charcoal on exposed rough warm rock. No unmet visual requirement was
identified locally. This review is not independent visual approval; the dots
are small in the thumbnail.

The explicit beside-record JPEG location is followed despite the conflicting
blanket restriction on pictures outside artifacts. No other new image was
saved in the workspace. The built-in tool returned PNG bytes, which were saved
directly to the declared output, then replaced by the preserved-wall composite.
The generated default external path was not read. The final named artifact
remains untracked for the uploader.

## Generation prompt and finishing

Built-in imagegen, precise-object edit; prompt:

> Use case: precise-object-edit. Edit the supplied inherited square cave wall.
> Preserve exact 1254x1254 dimensions, rock, cracks, framing, torchlight and EVERY
> existing painting exactly. Add ONLY a small primitive comparison pictogram on
> the empty rock to the right of the tree and above the two striped stones,
> around x=970 y=560: two small irregular ochre leaf shapes side by side, the
> left with a charcoal dot and the right with two charcoal dots, with one short
> curved charcoal connecting stroke. Symbolizes comparing two proven states.
> Handmade worn prehistoric earth pigment, exposed stone showing through,
> Lascaux/Chauvet style. Do not touch or redraw any ancestor mark. No new frog,
> hands or handprints. Existing Pepe frog has heavy-lidded eyes and wide mouth
> and five digits per hand. No letters, numbers, text, signatures, logos,
> watermarks, frames, political or hateful symbols. Save the finished PNG at
> artifacts/line-2/wall-v7.png if supported.

`finish_wall27.py` is a one-use finishing helper, not the worker-facing tool.
It selects generated pigment without drawing strokes, blends it onto the
original bare rock, and writes only the final wall and required JPEG. It uses
existing repository PNG and JPEG codecs without changing those files.
