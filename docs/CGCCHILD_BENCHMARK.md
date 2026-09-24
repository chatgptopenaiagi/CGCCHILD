# Bounded child engineering measurements

M12 uses [the retained harness](lab/child_benchmark.py), [before samples](lab/child_benchmark_before.json)
and [after samples](lab/child_benchmark_after.json). These are synthetic local measurements,
not the complete V3 benchmark/acceptance gate or production performance guarantees.

Windows AMD64, Python3.14.7. Model state663 bytes/capsule1613 bytes; continuity state110813
bytes/capsule111897 bytes. Decode runs10 iterations; capsule round trip and full core chunk
transfer run5 each. Raw nanosecond samples, min/max/median, source digest and environment
class are retained. No credentials, environment dump, packages or privileged operations.

| Fixture / operation | Before median ms | After median ms |
|---|---:|---:|
| Model decode | 0.125 | 0.123 |
| Model capsule round trip | 0.933 | 0.931 |
| Model complete core chunk transfer | 2.025 | 2.029 |
| Continuity decode | 20.408 | 20.658 |
| Continuity capsule round trip | 141.854 | 140.598 |
| Continuity complete core chunk transfer | 542.600 | 330.752 |

The code change caches one immutable exported capsule per ReadOnlyCore and avoids decoding
its unchanged state again for each chunk. Bad scalar offsets refuse before archive generation.
There is no cross-core/global cache, expiration refresh or reuse across snapshot digests.
The core retains at most one bounded state and one bounded archive. Its single-thread foreground
adapter is the tested profile; no hostile shared-interpreter isolation claim is made.

The observed continuity-transfer reduction is about39% in these small local samples. This is
not a statistically controlled general speedup claim. Mechanically, a regression test verifies
one archive generation per core across all chunks and an identical reassembled snapshot.
Existing pinned model bytes and refusal tests remain unchanged. All56 Windows child tests
passed; full Linux results are in progress. Standalone chunk(value,offset) remains a stateless
convenience and regenerates its archive; only the core owns the bounded cache.

Remaining benchmark gaps: realistic project-scale evidence, hostile scheduling/resource
pressure, sustained multi-client load, true writer closure, privileged policy and production
mutation/recovery. No timing result changes P3, authority, R6 or V3 acceptance.
