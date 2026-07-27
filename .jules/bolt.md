## 2025-10-31 - Memoizing Lexicon Regex Compilations
**Learning:** In the openmed NLP pipelines (e.g., `openmed.clinical.context`), deterministic regex compilations (`_compiled_context_lexicon`) and lexicon generation can cause severe performance bottlenecks during repeated evaluations across text spans.
**Action:** Always memoize deterministic lexicon and regex compilations (using `@functools.lru_cache`) when processing spans or lexicons dynamically in text pipelines.
