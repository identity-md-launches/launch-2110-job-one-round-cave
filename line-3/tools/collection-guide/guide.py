#!/usr/bin/env python3
"""Explore an unfamiliar offline corpus with cited headings and search starters."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ENGINE_PATH = Path(__file__).absolute().parents[1] / 'evidence-search' / 'search.py'
_spec = importlib.util.spec_from_file_location('collection_guide_search', ENGINE_PATH)
engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(engine)
FORMAT = 'evidence-collection-guide/v1'
# Deliberately small, fixed English function-word list; no external vocabulary.
STOP = frozenset('a an and are as at be been but by for from has have he her his i in is it its of on or our she that the their them there these they this to was we were will with you your'.split())


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def reference(document, line, text):
    return {'path': document['path'], 'line_start': line, 'line_end': line,
            'citation': f"{document['path']}:{line}-{line}",
            'sha256': document['sha256'], 'text': text}


def guide(index, terms=5, headings=5):
    """Validate the whole snapshot, then outline sources without reading a root."""
    if type(terms) is not int or not 1 <= terms <= 10:
        raise engine.SearchError('terms must be an integer between 1 and 10')
    if type(headings) is not int or not 0 <= headings <= 20:
        raise engine.SearchError('headings must be an integer between 0 and 20')
    engine.validate_index(index)
    engine.passages(index)  # Enforce the existing engine's whole-corpus budget.
    documents = sorted(index['documents'], key=lambda doc: doc['path'])
    profiles, frequency = [], Counter()
    for document in documents:
        lines = engine.source_lines(document['text'])
        counts, first, outline = Counter(), {}, []
        fenced = None
        for number, text in enumerate(lines, 1):
            # Terms remain searchable even within code; code headings are skipped.
            for term in engine.tokens(text):
                if len(term) >= 2 and len(term) <= 80 and not term.isdecimal() and term not in STOP:
                    counts[term] += 1
                    first.setdefault(term, (number, text))
            fence = re.match(r'^ {0,3}(`{3,}|~{3,})', text)
            if fence:
                marker = fence.group(1)
                if fenced is None:
                    fenced = marker
                elif marker[0] == fenced[0] and len(marker) >= len(fenced) and not text[fence.end():].strip():
                    fenced = None
                continue
            heading = re.match(r'^ {0,3}(#{1,6})[ \t]+\S', text)
            if fenced is None and heading:
                outline.append(dict(reference(document, number, text), level=len(heading.group(1))))
        profiles.append((document, lines, counts, first, outline))
        frequency.update(counts.keys())
    summaries = []
    for document, lines, counts, first, outline in profiles:
        # Rare-in-collection terms first, then frequent-in-source, then lexical.
        selected = sorted(counts, key=lambda term: (frequency[term], -counts[term], term))[:terms]
        hints = []
        for term in selected:
            number, text = first[term]
            hints.append({'term': term, 'occurrences': counts[term],
                          'document_frequency': frequency[term],
                          'query': term, 'source': reference(document, number, text)})
        summaries.append({'path': document['path'], 'sha256': document['sha256'],
                          'bytes': len(document['text'].encode('utf-8')), 'lines': len(lines),
                          'heading_count': len(outline), 'headings': outline[:headings],
                          'headings_omitted': max(0, len(outline) - headings), 'search_starters': hints})
    normalized = {'format': engine.FORMAT, 'documents': documents}
    result = {'format': FORMAT, 'snapshot_sha256': hashlib.sha256(canonical(normalized)).hexdigest(),
              'verification_scope': 'embedded source bytes only; no live freshness, authority or truth check',
              'selection': {'terms_per_document': terms, 'headings_per_document': headings,
                            'term_order': 'document frequency ascending, occurrence count descending, token ascending'},
              'documents': len(documents), 'total_bytes': sum(d['bytes'] for d in summaries),
              'total_lines': sum(d['lines'] for d in summaries), 'sources': summaries}
    result['guide_sha256'] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def demo():
    root = ENGINE_PATH.parent / 'examples' / 'docs'
    index = engine.build_index(root)
    overview = guide(index)
    # Demonstrate that a suggested query produces a real hash-checked citation.
    source = next(s for s in overview['sources'] if s['path'] == 'zto.md')
    query = source['search_starters'][0]['query']
    return {'guide': overview, 'suggested_query_trial': engine.search(index, query, root, limit=3)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='outline historical ZTO/IMD evidence and try a suggested query')
    for command, arg in [('scan', 'root'), ('snapshot', 'index')]:
        item = sub.add_parser(command)
        item.add_argument(arg)
        item.add_argument('--terms', type=int, default=5)
        item.add_argument('--headings', type=int, default=5)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            result = demo()
        else:
            index = engine.build_index(args.root) if args.command == 'scan' else engine.load_index(args.index)
            result = guide(index, args.terms, args.headings)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (engine.SearchError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
