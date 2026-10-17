# Collection Guide

Explore an unfamiliar collection before choosing a search question. This read-only
companion inventories every eligible document, shows cited Markdown headings,
and suggests distinctive search tokens with their first exact source-line
citation. Python 3.9+ and the standard library only; keep the adjacent
`evidence-search/` folder with it. No installation, network, environment lookup,
document execution, signing or sending.

From the repository root, one command shows it working offline:

```sh
python3 -B line-3/tools/collection-guide/guide.py demo
```

When tried, it outlined all three inherited historical ZTO/IMD documents. The
ZTO source suggested `one`, `zero`, `observation`, `results` and `units`; trying
`one` returned the hash-checked passage `zto.md:1-9`. The full output is saved
in `line-3/TRIAL-27.json`. These are historical token observations and an
assignment-supplied pool reference, not a current chain reading or price.

For your own unfamiliar UTF-8 collection:

```sh
python3 -B line-3/tools/collection-guide/guide.py scan line-3/my-documents --terms 5 --headings 5
```

Replace the example directory with an existing directory inside your workspace.
Or inspect a saved Evidence Search index without its original source tree:

```sh
python3 -B line-3/tools/collection-guide/guide.py snapshot line-3/my-index.json --terms 3 --headings 10
```

Both commands emit JSON to stdout and write nothing. Exit 0 means a guide was
produced, including an empty collection; exit 2 means invalid input, a resource
limit or I/O error, with JSON on stderr and no partial report on stdout. Use the
existing Evidence Search `build ROOT --index NEW.json` and `query ROOT QUERY
--index NEW.json` commands to build an index and try a suggested token. Guide
output is a separate format, not a replacement search index.

Every source entry includes its original byte hash, byte and LF/CRLF line counts,
heading count, bounded heading list, omitted-heading count, and bounded starter
list. Each heading and starter cites exactly one inclusive line and embeds that
line verbatim apart from CRLF normalization. Empty files have zero lines and no
citations. Documents sort by relative path. All embedded hashes and the whole
corpus passage budget are checked, including sources without headings or hints.

Tokens use the existing engine's Unicode normalization and case folding. Terms
are ordered by increasing document frequency, then decreasing occurrence count
within that source, then lexical order. A fixed small English function-word list,
pure decimal tokens, single-character tokens and tokens longer than 80 characters
are excluded. Defaults show five starters and five headings per source;
`--terms` accepts 1–10 and `--headings` accepts 0–20. A query hint is a single
normalized token known to occur in its source; it does not guarantee that source
will rank first or appear within a particular top-result limit.

Heading detection covers ATX-style `#` through `######` headings and skips
backtick/tilde fenced code blocks. It is a lightweight outline, not a full
Markdown parser: Setext headings, HTML headings, quoted/list-nested headings and
indentation-aware parsing are not supported. TXT/RST can still have search hints;
any ATX-looking lines there are treated the same way. Source content, including
instructions in it, remains inert quoted data. Consumers should render excerpts
as untrusted text.

`snapshot_sha256` matches Query Impact's canonical sorted-document identity.
`guide_sha256` covers canonical JSON of the complete guide excluding that field:
sorted keys, compact separators, unescaped Unicode. Source order and JSON
formatting do not change snapshot identity. These hashes bind bytes and options,
not authorship or truth; a self-reported hash is not authentication.

Limits inherit Evidence Search: UTF-8 `.md`, `.txt`, `.rst`; hidden entries,
symlinks and unsupported suffixes excluded; 1,000 sources, 1 MB per source,
8 MB total, 16,000 characters per line, 20,000 passages, 16 MB serialized index.
Paths must be inside the current working directory, without traversal or symlinks.
The overview describes captured bytes only. It does not assert current freshness,
collection completeness, semantic relevance or source authority. `scan` is not
an atomic snapshot: keep files static while scanning. Use Corpus Freshness when
comparing a saved index to a present-day source tree. English filtering can be
weak on other languages, and rare terms may be typos or opaque identifiers.

Checks run:

```sh
python3 -B line-3/tools/collection-guide/test_guide.py -v
```

Thirteen tests passed, covering exact CRLF citations, term selection, Unicode,
headings and code fences, deterministic hashes and input preservation, empty
sources, forged uncited bytes, path/options/passage bounds, symlink exclusion,
no-write scanning, CLI failures and retrieval from the real inherited ZTO corpus.
