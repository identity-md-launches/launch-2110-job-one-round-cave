"""Behavioral checks for cited corpus exploration; standard library only."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('guide', Path(__file__).with_name('guide.py'))
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def snapshot(**docs):
    return {'format': g.engine.FORMAT, 'documents': [
        {'path': name, 'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}
        for name, text in docs.items()]}


class GuideTests(unittest.TestCase):
    def test_every_reference_reproduces(self):
        index = snapshot(**{'a.md': '# Apple\r\n\r\nRare branch branch.\r\n', 'b.txt': 'Apple tree\n'})
        result = g.guide(index)
        docs = {d['path']: d for d in index['documents']}
        for source in result['sources']:
            for ref in source['headings'] + [t['source'] for t in source['search_starters']]:
                doc = docs[ref['path']]
                self.assertEqual(ref['sha256'], doc['sha256'])
                self.assertEqual(ref['text'], g.engine.source_lines(doc['text'])[ref['line_start'] - 1])
                self.assertEqual(ref['line_start'], ref['line_end'])
                self.assertEqual(ref['citation'], f"{ref['path']}:{ref['line_start']}-{ref['line_end']}")

    def test_distinctive_terms_before_common_terms(self):
        index = snapshot(**{'a.md': 'common common common rare rare other', 'b.md': 'common'})
        terms = g.guide(index)['sources'][0]['search_starters']
        self.assertEqual([t['term'] for t in terms], ['rare', 'other', 'common'])
        self.assertEqual(terms[0]['occurrences'], 2)
        self.assertEqual(terms[-1]['document_frequency'], 2)

    def test_order_independent_and_immutable(self):
        index = snapshot(**{'b.md': '# Bee\nBee', 'a.md': '# Ant\nAnt'})
        saved = copy.deepcopy(index)
        result = g.guide(index)
        self.assertEqual(index, saved)
        index['documents'].reverse()
        self.assertEqual(result, g.guide(index))

    def test_fences_and_heading_limit(self):
        index = snapshot(**{'a.md': '# One\n```md\n## fake\n````\n## Two\n~~~\n# fake\n~~~\n### Three\n'})
        item = g.guide(index, headings=1)['sources'][0]
        self.assertEqual(item['heading_count'], 3)
        self.assertEqual(item['headings_omitted'], 2)
        self.assertEqual(item['headings'][0]['text'], '# One')
        self.assertEqual(g.guide(index, headings=0)['sources'][0]['headings'], [])

    def test_unicode_normalization_and_stopwords(self):
        terms = g.guide(snapshot(**{'a.txt': 'The ＺＴＯ zto CAFÉ café 123 a x'}))['sources'][0]['search_starters']
        self.assertEqual([t['term'] for t in terms], ['café', 'zto'])
        self.assertEqual([t['occurrences'] for t in terms], [2, 2])

    def test_empty_and_blank_documents(self):
        self.assertEqual(g.guide(snapshot())['sources'], [])
        item = g.guide(snapshot(**{'a.md': ''}))['sources'][0]
        self.assertEqual((item['lines'], item['bytes'], item['search_starters']), (0, 0, []))

    def test_tampered_uncited_source_rejected(self):
        index = snapshot(**{'a.md': '# Good', 'b.md': 'other'})
        index['documents'][1]['text'] = 'forged'
        with self.assertRaises(g.engine.SearchError):
            g.guide(index)

    def test_input_validation(self):
        for field, values in [('terms', [0, 11, True, '5']), ('headings', [-1, 21, True, '5'])]:
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(g.engine.SearchError):
                    g.guide(snapshot(), **{field: value})
        for name in ['../a.md', '/a.md', '.secret.md']:
            with self.assertRaises(g.engine.SearchError):
                g.guide(snapshot(**{name: 'hello'}))

    def test_passage_budget(self):
        previous = g.engine.MAX_PASSAGES
        try:
            g.engine.MAX_PASSAGES = 1
            with self.assertRaises(g.engine.SearchError):
                g.guide(snapshot(**{'a.md': '\n'.join(['text'] * 20)}))
        finally:
            g.engine.MAX_PASSAGES = previous

    def test_digests_bind_bytes_and_options(self):
        first = g.guide(snapshot(**{'a.md': 'hello\n'}))
        changed = g.guide(snapshot(**{'a.md': 'hello\r\n'}))
        self.assertNotEqual(first['snapshot_sha256'], changed['snapshot_sha256'])
        short = g.guide(snapshot(**{'a.md': 'hello\n'}), terms=1)
        self.assertEqual(first['snapshot_sha256'], short['snapshot_sha256'])
        self.assertNotEqual(first['guide_sha256'], short['guide_sha256'])
        digest = first.pop('guide_sha256')
        self.assertEqual(digest, hashlib.sha256(g.canonical(first)).hexdigest())

    def test_scan_cli_no_writes_symlink_exclusion(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            root = Path(folder)
            (root / 'a.md').write_text('# Root\nSearchable\n')
            (root / 'ignored.md').symlink_to('a.md')
            before = sorted(root.iterdir())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = g.main(['scan', str(root)])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())['documents'], 1)
            self.assertEqual(sorted(root.iterdir()), before)

    def test_cli_error_atomic_output(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = g.main(['snapshot', '../outside.json'])
        self.assertEqual(status, 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('error', json.loads(err.getvalue()))

    def test_demo_suggested_query_retrieves_source(self):
        result = g.demo()
        trial = result['suggested_query_trial']
        self.assertTrue(any(hit['path'] == 'zto.md' for hit in trial['hits']))
        self.assertTrue(all(hit['source_verified'] for hit in trial['hits']))


if __name__ == '__main__':
    unittest.main()
