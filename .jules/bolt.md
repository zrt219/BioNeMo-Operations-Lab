## 2024-07-23 - Context Lexicon Regex Compilation Bottleneck
**Learning:** Deterministic lexicon processing (like negation and temporality cues) creates massive regular expression alternations across clinical pipelines. Re-compiling these every time `_compiled_context_lexicon` was called caused a significant CPU bottleneck.
**Action:** Use `@functools.lru_cache` to cache compiled regular expressions and lexicons. Ensure that arguments to these functions (e.g. `cues`) are typed as `tuple` rather than unhashable `Iterable` to be compatible with caching.
