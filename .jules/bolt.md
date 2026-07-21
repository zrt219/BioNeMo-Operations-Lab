## 2024-03-14 - Regex Compilation Bottleneck in ConText Cue Matching
**Learning:** Instantiating complex regex pipelines for every NLP span processed (e.g., repeatedly calling unmemoized regex compilers during ConText modifier scanning) introduces severe latency overhead, inflating processing time by up to 40x.
**Action:** When adding or maintaining deterministic text-processing functions that compile regular expressions or lexicons based on simple inputs (like a language code), always apply `@functools.lru_cache` to memoize the compiled output.
