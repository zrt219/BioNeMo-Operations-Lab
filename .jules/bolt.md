## 2025-03-01 - [Bolt: Fix Clinical Context Lexicon Generation Time]
**Learning:** The openmed project's `openmed.clinical.context` relies heavily on `_compiled_context_lexicon` which recursively compiles and computes large numbers of regexs. Because this wasn't cached, it added up linearly during multiple queries or requests (i.e. spans/modifiers evaluations in text).
**Action:** Use `functools.lru_cache` to cache deterministic regex compilations and lexicon generation in text/NLP pipelines.
