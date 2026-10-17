#!/usr/bin/env python3
"""Compare two independently block-hash-anchored Ethereum state witnesses offline."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'header_anchor_for_diff', HERE.parent / 'header-anchor' / 'anchor.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
w = a.w
DEMO_AFTER_HASH = '0x21c6077c84e1fb60cbff0737f8106b07e65bdc074b4a3ddea1c8368ca7b351d9'
FIELDS = ('accountExists', 'nonce', 'nativeBalanceWei', 'storageRoot', 'codeHash')


def compare(before_header, before_bundle, after_header, after_bundle,
            before_hash, after_hash, address, slots):
    """Verify both complete inputs before deriving any differences.

    Both hashes are caller trust inputs. Block ordering is not ancestry proof.
    Deltas are endpoint differences, never sums of transfers or intermediate events.
    """
    before = a.verify(before_header, before_bundle, before_hash, address, slots)
    after = a.verify(after_header, after_bundle, after_hash, address, slots)
    bh, ah = before['anchor'], after['anchor']
    same = bh['blockHash'] == ah['blockHash']
    if not same:
        w.require(int(ah['blockNumber'], 16) > int(bh['blockNumber'], 16),
                  'after block number must be greater than before block number')
        w.require(int(ah['timestamp'], 16) > int(bh['timestamp'], 16),
                  'after timestamp must be greater than before timestamp')
    bs, ass = before['state'], after['state']
    account = []
    for field in FIELDS:
        old, new = bs[field], ass[field]
        row = {'field': field, 'before': old, 'after': new, 'changed': old != new}
        if field in ('nonce', 'nativeBalanceWei'):
            base = 16 if field == 'nonce' else 10
            row['deltaDecimal'] = str(int(new, base) - int(old, base))
        account.append(row)
    # Ancestor verification normalizes/sorts slots and enforces the same exact
    # requested set on each side. Still map by key rather than input order.
    old_slots = {row['slot']: row for row in bs['storage']}
    storage = []
    for new in ass['storage']:
        old = old_slots[new['slot']]
        storage.append({'slot': new['slot'],
                        'before': {'value': old['value'], 'exists': old['exists']},
                        'after': {'value': new['value'], 'exists': new['exists']},
                        'changed': (old['value'], old['exists']) != (new['value'], new['exists']),
                        'deltaDecimal': str(int(new['value'], 16) - int(old['value'], 16))})
    changed_fields = [row['field'] for row in account if row['changed']]
    changed_slots = [row['slot'] for row in storage if row['changed']]
    return {
        'format': 'state-diff/1', 'verified': True, 'address': bs['address'],
        'before': bh, 'after': ah, 'sameCheckpoint': same,
        'blockDistance': int(ah['blockNumber'], 16) - int(bh['blockNumber'], 16),
        'elapsedSeconds': int(ah['timestamp'], 16) - int(bh['timestamp'], 16),
        'account': account, 'storage': storage,
        'summary': {'accountChanged': bool(changed_fields),
                    'changedAccountFields': changed_fields,
                    'changedRequestedSlots': changed_slots,
                    'requestedSlotsChanged': bool(changed_slots),
                    'storageCommitmentChanged': bs['storageRoot'] != ass['storageRoot']},
        'scope': 'Account fields and exactly the requested storage slots at two endpoints. A changed storage root may reflect unrequested slots. Equal endpoints do not exclude intermediate changes. Native balance is ETH wei, not a token balance. Raw slots have no inferred ABI or layout.',
        'trust': 'Both supplied block hashes must be independently authenticated for the same chain, canonicality, execution validity and finality. Header ordering is checked but ancestry and consensus are not. Bundled metadata and RPC labels are not trust anchors. Deltas are signed endpoint arithmetic, not transfers, events, profit or a current quote.',
    }


def demo_inputs(pool=False):
    name = 'pool' if pool else 'zto'
    old_name = 'zto-pool-mainnet.json' if pool else 'zto-mainnet.json'
    return (a.load_header(a.HERE / 'examples/zto-header-mainnet.json'),
            w.load_bundle(HERE.parent / 'state-witness/examples' / old_name),
            a.load_header(HERE / 'examples/header-later.json'),
            w.load_bundle(HERE / 'examples' / (name + '-later.json')))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='compare real historical ZTO/IMD pool proofs offline')
    demo.add_argument('--zto', action='store_true', help='compare ZTO account and raw slots 0 and 1 instead')
    check = sub.add_parser('compare', help='verify and compare two caller-anchored snapshots')
    for name in ('before_header', 'before_witness', 'after_header', 'after_witness'):
        check.add_argument(name)
    check.add_argument('--before-hash', required=True)
    check.add_argument('--after-hash', required=True)
    check.add_argument('--address', required=True)
    check.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            pool = not args.zto
            result = compare(*demo_inputs(pool), a.DEMO_HASH, DEMO_AFTER_HASH,
                             w.POOL_MANAGER if pool else w.ZTO,
                             [a.POOL_SLOT] if pool else ['0x0', '0x1'])
            result['demo'] = 'Real historical mainnet RPC observations; bundled hashes are not independently authenticated checkpoints.'
        else:
            result = compare(a.load_header(args.before_header), w.load_bundle(args.before_witness),
                             a.load_header(args.after_header), w.load_bundle(args.after_witness),
                             args.before_hash, args.after_hash, args.address, args.slot)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed header or witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
