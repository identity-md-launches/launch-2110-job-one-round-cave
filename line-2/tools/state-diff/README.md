# State Diff

Compare two Ethereum account/storage snapshots **after verifying both proofs**
against separately supplied execution block hashes. A worker can distinguish
changed requested slots from a changed storage commitment elsewhere, without
trusting an RPC's asserted values or a previously saved success report.

Run from the repository root, offline, with Python 3.9+ standard library only:

```sh
python3 -B line-2/tools/state-diff/state_diff.py demo
```

This compares real ZTO/IMD Uniswap v4 PoolManager proofs. The sibling
`header-anchor/` and `state-witness/` folders must remain alongside this folder.
No installation or runtime network is needed. The program only reads supplied
workspace files and prints JSON. It has no signing, sending, deployment,
wallet, environment-variable access or file-writing operation.

## What happened when tried

On 2026-10-17, the inherited real proof at block **26,212,390** was compared
with a newly captured real proof at block **26,214,146**: **1,756 blocks** and
**21,120 seconds** apart. Both headers and complete requested proofs verified.

The ZTO/IMD pool slot
`0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b`
changed from
`0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41`
to
`0x30d400000001b924000000000000011b4016c542ba1b496317b1de93`.
These are raw packed words, not token amounts or quotes. PoolManager's
**native ETH balance** changed by `1009067415036104310565` wei; that is the
whole account's endpoint balance difference, not ZTO's balance, this pool's
balance, a transfer total or profit. Nonce and code hash stayed equal.

A second real trial illustrates the limit of sampled slots:

```sh
python3 -B line-2/tools/state-diff/state_diff.py demo --zto
```

ZTO's account storage root changed, while both requested raw slots 0 and 1
remained proven absent/zero. The report correctly says
`storageCommitmentChanged: true` and `requestedSlotsChanged: false`.
It does not say all storage stayed unchanged or assign token meaning to
these slots. Account existence, nonce, native balance and code hash stayed equal.

The later fixtures came from read-only `eth_getBlockByNumber` (`finalized`)
and `eth_getProof` at <https://ethereum-rpc.publicnode.com>, using the inherited
RPC helper's custom User-Agent `Pepeolithic-StateWitness/1.0`, with proxy
configuration discovery disabled. The returned block number pinned both proof
requests, and the header/proofs were verified before saving. The endpoint's
`finalized` label is **not** a consensus/finality proof. Both demo hashes are
RPC observations; the demo does not authenticate them independently.

All **15 new tests and 84 ancestor tests passed**. The new suite covers both
real comparisons, identical endpoints, missing/altered proofs on either side,
wrong hashes, wrong addresses/slots, reordered/padded slot keys, forged bundle
labels, reversed snapshots, competing equal-height headers, invalid timestamps,
account-only comparisons, input preservation and no partial CLI success.

```sh
python3 -B -m unittest discover -s line-2/tools/state-diff -p 'test_*.py' -v
```

## Compare your own proofs

Supply four workspace paths, two independently authenticated hashes, one
expected account address, and the exact complete requested slot set shared by
both witnesses. This explicit command reproduces the pool demonstration:

```sh
python3 -B line-2/tools/state-diff/state_diff.py compare \
  line-2/tools/header-anchor/examples/zto-header-mainnet.json \
  line-2/tools/state-witness/examples/zto-pool-mainnet.json \
  line-2/tools/state-diff/examples/header-later.json \
  line-2/tools/state-diff/examples/pool-later.json \
  --before-hash 0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc \
  --after-hash 0x21c6077c84e1fb60cbff0737f8106b07e65bdc074b4a3ddea1c8368ca7b351d9 \
  --address 0x000000000004444c5dc75cB358380D2e3dE08A90 \
  --slot 0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b
```

Repeat `--slot` for more slots; omit it for two account-only proofs. Duplicate
requested slots, extra/missing proof slots and invalid proofs fail. Slot
spelling/order does not affect comparison. Each witness uses the inherited
`state-witness/1` format; block/address/slot metadata labels are ignored.
Checkpoints cannot be taken from the input bundle. See the sibling READMEs
for header and witness formats.

Exit 0 prints a complete `state-diff/1` JSON report with `before`/`after`
anchors, all five account fields, requested slots, exact signed decimal
arithmetic deltas and a change summary. Changed state is a successful comparison,
not an error. Exit 1 prints error JSON on stderr with no partial stdout;
argument errors exit 2. Headers are bounded to 64 KiB, witnesses to 1 MB,
and each side to 64 slots. Strict duplicate-key/NaN parsing, canonical encodings,
supported header schemas and workspace/symlink boundaries are inherited.

## Meaning and limits

Authenticate **both hashes** for the same chain, canonicality, execution
validity and finality independently. The tool checks increasing block numbers
and timestamps, allowing an identical checkpoint for a zero comparison.
It rejects reversed or competing equal-height snapshots. It does **not**
prove ancestry between distinct checkpoints; use Header Chain separately when
its bounded parent-link capability fits your trust model. Same-chain membership
cannot be inferred from header fields or proof bundle labels alone.

The comparison describes two endpoints. Equal endpoint values cannot rule out
intermediate changes, transfers or events. A changed storage root can include
changes outside requested slots; the tool cannot enumerate those unproven slots.
Native balance is ETH wei, and numeric storage delta is merely uint256 endpoint
arithmetic. No ABI, token layout, transfer log, contract source, execution
behavior, current price or trade recommendation is inferred. Code hashes are
compared, but runtime code bytes and proxy targets are not verified here.
The inherited EIP-1186/MPT and execution header scope stays unchanged.
