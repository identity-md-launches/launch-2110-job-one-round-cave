"""Real-chain endpoint comparisons and adversarial checks; no networking."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('state_diff_tested', HERE / 'state_diff.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class StateDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = d.demo_inputs(True)
        cls.zto = d.demo_inputs(False)

    def verify(self, inputs=None, hashes=None, address=None, slots=None):
        return d.compare(*(self.pool if inputs is None else inputs),
                         *(hashes or (d.a.DEMO_HASH, d.DEMO_AFTER_HASH)),
                         d.w.POOL_MANAGER if address is None else address,
                         [d.a.POOL_SLOT] if slots is None else slots)

    def test_real_pool_changed_and_exact_arithmetic(self):
        result = self.verify()
        self.assertTrue(result['verified'])
        self.assertEqual(result['blockDistance'], 1756)
        self.assertEqual(result['elapsedSeconds'], 21120)
        self.assertEqual(result['summary']['changedAccountFields'], ['nativeBalanceWei', 'storageRoot'])
        self.assertEqual(result['summary']['changedRequestedSlots'], [d.a.POOL_SLOT])
        self.assertEqual(result['account'][2]['deltaDecimal'], '1009067415036104310565')
        row = result['storage'][0]
        self.assertEqual(row['before']['value'], '0x30d400000001b32f000000000000010675ff9d949ea2d3c11613bc41')
        self.assertEqual(row['after']['value'], '0x30d400000001b924000000000000011b4016c542ba1b496317b1de93')
        self.assertEqual(int(row['deltaDecimal']), int(row['after']['value'], 16) - int(row['before']['value'], 16))

    def test_real_zto_root_changed_but_sampled_slots_unchanged(self):
        result = self.verify(self.zto, address=d.w.ZTO, slots=['0x0', '0x1'])
        self.assertTrue(result['summary']['storageCommitmentChanged'])
        self.assertFalse(result['summary']['requestedSlotsChanged'])
        self.assertEqual(result['summary']['changedAccountFields'], ['storageRoot'])
        self.assertTrue(all(not s['before']['exists'] and not s['after']['exists'] for s in result['storage']))
        self.assertIn('intermediate changes', result['scope'])

    def test_identical_checkpoint_zero_changes(self):
        h, b = self.pool[:2]
        result = self.verify((h, b, h, b), hashes=(d.a.DEMO_HASH, d.a.DEMO_HASH))
        self.assertTrue(result['sameCheckpoint'])
        self.assertFalse(result['summary']['accountChanged'])
        self.assertFalse(result['summary']['requestedSlotsChanged'])
        self.assertEqual(result['blockDistance'], 0)

    def test_deterministic_and_inputs_unchanged(self):
        original = copy.deepcopy(self.pool)
        self.assertEqual(self.verify(), self.verify())
        self.assertEqual(self.pool, original)

    def test_both_explicit_hashes_bound(self):
        for hashes in ((d.DEMO_AFTER_HASH, d.DEMO_AFTER_HASH), (d.a.DEMO_HASH, d.a.DEMO_HASH)):
            with self.subTest(hashes=hashes), self.assertRaises(d.w.Invalid):
                self.verify(hashes=hashes)

    def test_bad_claims_and_missing_nodes_on_either_side(self):
        for side in (1, 3):
            for field in ('value', 'proof'):
                values = copy.deepcopy(self.pool)
                values[side]['proof']['storageProof'][0][field] = '0x1' if field == 'value' else []
                with self.subTest(side=side, field=field), self.assertRaises(d.w.Invalid):
                    self.verify(values)

    def test_forged_account_fields_on_both_sides(self):
        for side in (1, 3):
            values = copy.deepcopy(self.pool)
            values[side]['proof']['balance'] = '0x1'
            with self.subTest(side=side), self.assertRaises(d.w.Invalid):
                self.verify(values)

    def test_address_and_exact_slot_sets(self):
        for address, slots in ((d.w.ZTO, [d.a.POOL_SLOT]), (d.w.POOL_MANAGER, []),
                               (d.w.POOL_MANAGER, ['0x0']), (d.w.POOL_MANAGER, [d.a.POOL_SLOT] * 2)):
            with self.subTest(address=address, slots=slots), self.assertRaises(d.w.Invalid):
                self.verify(address=address, slots=slots)

    def test_order_and_padded_slot_spelling_do_not_create_false_diff(self):
        values = copy.deepcopy(self.zto)
        values[1]['proof']['storageProof'].reverse()
        result = self.verify(values, address=d.w.ZTO,
                             slots=['0x' + '0' * 63 + '1', '0x00'])
        self.assertEqual([r['slot'] for r in result['storage']], ['0x0', '0x1'])
        self.assertFalse(result['summary']['requestedSlotsChanged'])

    def test_untrusted_bundle_labels_ignored(self):
        values = copy.deepcopy(self.pool)
        for i in (1, 3):
            values[i].update(address='forged', slots=[], block={'hash': 'forged'}, chainId=999)
        self.assertEqual(self.verify(values), self.verify())

    def test_reverse_snapshots_rejected_even_with_right_hashes(self):
        h, b, ah, ab = self.pool
        with self.assertRaisesRegex(d.w.Invalid, 'block number'):
            self.verify((ah, ab, h, b), hashes=(d.DEMO_AFTER_HASH, d.a.DEMO_HASH))

    def test_equal_height_competing_header_and_bad_time_rejected(self):
        # Deliberately malformed headers are rehashed so hash verification passes;
        # ordering must still reject them. These are not chain demo fixtures.
        for field in ('number', 'timestamp'):
            values = copy.deepcopy(self.pool)
            values[2][field] = values[0][field]
            del values[2]['hash']
            raw, _ = d.a.encode_header(values[2])
            trusted = d.w.hex0(d.w.keccak256(raw))
            with self.subTest(field=field), self.assertRaises(d.w.Invalid):
                self.verify(values, hashes=(d.a.DEMO_HASH, trusted))

    def test_account_only_comparison(self):
        values = copy.deepcopy(self.pool)
        for side in (1, 3):
            values[side]['proof']['storageProof'] = []
        result = self.verify(values, slots=[])
        self.assertEqual(result['storage'], [])
        self.assertTrue(result['summary']['storageCommitmentChanged'])

    def test_cli_demos_and_failure_has_no_partial_stdout(self):
        for args in (['demo'], ['demo', '--zto']):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(d.main(args), 0)
            self.assertTrue(json.loads(out.getvalue())['verified'])
            self.assertEqual(err.getvalue(), '')
        args = ['compare', str(d.a.HERE/'examples/zto-header-mainnet.json'),
                str(HERE.parent/'state-witness/examples/zto-pool-mainnet.json'),
                str(HERE/'examples/header-later.json'), str(HERE/'examples/pool-later.json'),
                '--before-hash', d.a.DEMO_HASH, '--after-hash', d.a.DEMO_HASH,
                '--address', d.w.POOL_MANAGER, '--slot', d.a.POOL_SLOT]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(d.main(args), 1)
        self.assertEqual(out.getvalue(), '')
        self.assertFalse(json.loads(err.getvalue())['verified'])

    def test_workspace_boundary_is_retained(self):
        with self.assertRaises(d.w.Invalid):
            d.a.load_header(Path.cwd().parent / 'outside.json')
        with self.assertRaises(d.w.Invalid):
            d.w.load_bundle(Path.cwd().parent / 'outside.json')


if __name__ == '__main__':
    unittest.main()
