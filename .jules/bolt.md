## 2024-05-24 - [Cache Unnecessary Python Loop Variables]
**Learning:** In highly recursive or looping NLP functions such as line-by-line regex scanning, rebuilding configurations or alias lookups dynamically creates enormous overhead in Python. The openmed package's `_alias_lookups` recreated language alias dicts on every single line, leading to severe slowdowns.
**Action:** Use `@functools.lru_cache(maxsize=None)` on deterministic configuration generators within loops to cut down redundant operations. Ensure inputs are hashable and small in variance (like language codes).
