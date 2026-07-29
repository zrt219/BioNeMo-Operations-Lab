## 2024-07-29 - Memoization of NLP Lexicons
**Learning:** Deterministic regex compilations and lexicon generations in `openmed.clinical` (like `_compiled_context_lexicon` and `_alias_lookups`) are repeated continuously during string evaluations, causing significant performance overhead (e.g. 0.7s per 1000 calls).
**Action:** Always memoize deterministic lexicon building and regex compiling functions using `@functools.lru_cache` in text-processing pipelines to ensure they are only constructed once per language/configuration.
