## Review Scope

Reviewed `mrhavens/becomingone` at current default branch head `6061f5c` (`fix(core): Address code review from Issue #1`). Focus areas: public API behavior, core temporal engine/transducer correctness, memory persistence/retrieval, LLM integration paths, and test reliability.

## Findings

### 1. API command-line configuration is overwritten before the server starts

**Severity:** High
**Files:** `becomingone/api.py:535-555`, `becomingone/api.py:386-391`, `becomingone/api.py:443`

`main()` initializes the engine with CLI values at `api.py:545-551`, but `run_server()` immediately calls `create_app()` at `api.py:443`, and `create_app()` calls `init_engine()` again with defaults at `api.py:390-391`. As a result, flags such as `--master-tau`, `--emissary-tau`, `--sync-tau`, `--coherence-threshold`, and `--witnessed` are silently ignored for the actual running server.

**Impact:** Operators can believe they are running with a specific coherence threshold or time constant while the API is actually running default dynamics.

**Suggestion:** Initialize exactly once. Either pass parsed config into `create_app()`/`run_server()`, or remove initialization from `create_app()` and require the caller to provide initialized components. Add an integration test that starts the app with non-default CLI values and asserts the effective component config.

### 2. The HTTP API reports successful HTTP status for not-found and application errors

**Severity:** High
**File:** `becomingone/api.py:344-380`

Unknown routes produce `result = {"error": "Not found", ...}` but still write `HTTP/1.1 200 OK` at `api.py:367`. Handler-level validation errors such as unknown input type also return normal JSON error bodies that are serialized as 200 responses. Only parser/runtime exceptions become 500s.

**Impact:** Health checks, clients, reverse proxies, and automation cannot reliably distinguish success from failure using HTTP semantics.

**Suggestion:** Return proper status codes: `404` for missing routes, `400` for invalid request bodies/input types, `405` for unsupported methods, `413` for oversized payloads, and `500` only for unexpected server failures. Consider replacing the handwritten HTTP parser with a small ASGI framework or at least centralizing `(status, body)` response handling.

### 3. Public `/reset` mutates global engine state without authentication, CSRF protection, or concurrency control

**Severity:** High
**Files:** `becomingone/api.py:288-323`, `becomingone/api.py:138-144`

`POST /reset` is exposed by default and calls `reset_engine()`, which rebuilds global engine components. There is no authn/authz, no CSRF protection, no localhost-only enforcement inside the handler, and no lock around `_engine_components` while requests are concurrently processing.

**Impact:** If the server is bound beyond localhost, any network client can wipe runtime state. Even on localhost, concurrent `/input`, `/coherence`, and `/reset` calls can observe partially replaced globals or lose in-flight state.

**Suggestion:** Require an explicit admin token or disable reset unless an `--enable-admin` flag is set. Protect component reads/writes with an `asyncio.Lock`, and make reset call component-level `reset()` methods rather than swapping globals mid-request.

### 4. Memory retrieval references a nonexistent `TemporalState.phase_history` attribute

**Severity:** High
**Files:** `becomingone/memory/temporal.py:342-365`, `becomingone/core/engine.py:44-50`

`TemporalMemory.retrieve()` reads `query_state.phase_history` at `temporal.py:358-359`, but `TemporalState` only defines `phase`, `coherence`, `timestamp`, and `metadata`. Any retrieval against a real `TemporalState` with stored signatures will raise `AttributeError` instead of returning memories.

**Impact:** The persistent memory system cannot perform associative recall through the class API, which breaks a core feature described in the README.

**Suggestion:** Use `query_state.phase` directly, or store the current phase vector in `TemporalState.metadata` and read from that consistently. Add a regression test that binds memory, encodes a signature, then calls `retrieve()` with a real state from `KAIROSTemporalEngine.temporalize()`.

### 5. Encoded memory signatures drop the actual phase vector produced by the engine

**Severity:** High
**Files:** `becomingone/memory/temporal.py:265-284`, `becomingone/core/engine.py:239-251`

`TemporalMemory.encode()` pulls `phase_vec = temporal_state.metadata.get("phase_vector", [])`, but `KAIROSTemporalEngine.temporalize()` stores `raw_angles`, `T_tau`, `collapsed`, `integration`, and `eigen_phase`; it does not store `phase_vector`. The resulting `TemporalSignature.phase_vector` is typically empty.

**Impact:** Persisted memories lose their semantic/phase payload, which makes later resonance scoring and echo creation mostly meaningless. It also interacts badly with `compute_resonance_score()`, which returns `0.0` when `signature.phase_vector` is empty.

**Suggestion:** Normalize one schema: either put `phase_vector` into `TemporalState.metadata` at creation time, or have `TemporalMemory.encode()` derive it from `temporal_state.phase`. Add tests that assert encoded signatures contain non-empty phase vectors and can be scored/retrieved.

### 6. Emissary action generation crashes for normal N-dimensional phases

**Severity:** Medium
**File:** `becomingone/transducers/emissary.py:222-225`

When coherence crosses the action threshold, `_generate_action()` eventually evaluates `float(np.angle(state.phase))`. `state.phase` is normally an array of complex oscillators, so converting the full angle array to `float` raises `TypeError: only 0-dimensional arrays can be converted to Python scalars`.

**Targeted reproduction:**

```bash
.venv/bin/python - <<'PY'
import asyncio
from becomingone.transducers.emissary import EmissaryTransducer, EmissaryConfig
async def main():
    e = EmissaryTransducer(EmissaryConfig(coherence_threshold=0.0))
    await e.respond('hello')
asyncio.run(main())
PY
```

Observed: `TypeError only 0-dimensional arrays can be converted to Python scalars`.

**Suggestion:** Reduce the phase vector intentionally, for example `float(np.angle(np.mean(state.phase)))`, or return the full vector/summary structure instead of a scalar. Add an awaited async test for `respond()` that forces the action path.

### 7. LLM CLI cannot construct `DualPathway`

**Severity:** Medium
**File:** `becomingone/llm_integrator.py:207-210`

The CLI passes `emissaary=...` instead of `emissary=...`, causing `TypeError: DualPathway.__init__() got an unexpected keyword argument 'emissaary'`.

**Reproduction:**

```bash
.venv/bin/python -m becomingone.llm_integrator --pathway emissary --prompt hi
```

**Suggestion:** Fix the typo and add a smoke test for `python -m becomingone.llm_integrator --pathway emissary --prompt hi` with network calls mocked.

### 8. Attention entropy calculation always fails for real float weights

**Severity:** Medium
**File:** `becomingone/llm_processor.py:127-130`

`encode_attention()` calls `(w + 1e-10).log2()` on Python floats. Floats do not have a `log2()` method, so attention encoding fails before any useful result is produced.

**Reproduction:**

```bash
.venv/bin/python - <<'PY'
from becomingone.llm_processor import LLMCoherenceEngine, AttentionPattern
LLMCoherenceEngine().encode_attention(AttentionPattern(0, 0, [0.5, 0.5], [0, 1], 1))
PY
```

Observed: `AttributeError 'float' object has no attribute 'log2'`.

**Suggestion:** Use `math.log2(w + eps)` or `np.log2(weights + eps)` and guard against empty weight lists. Add tests for uniform, peaked, and empty/malformed attention patterns.

### 9. The test suite gives false confidence around async behavior and optional dependencies

**Severity:** Medium
**Files:** `tests/test_core.py:32-41`, `requirements.txt`, `tests/test_unified_architecture.py`

Several tests call async methods without awaiting them, e.g. `engine.temporalize(0.1)` in `tests/test_core.py`. Pytest reports runtime warnings that the coroutine was never awaited, but the tests still pass. Separately, full collection fails in a minimal venv because root-level test scripts import `httpx`, and `tests/test_unified_architecture.py` imports `torch`, while `requirements.txt` does not clearly separate core, test, optional LLM, and heavyweight ML dependencies.

**Observed verification:**

```bash
python3 -m venv .venv
.venv/bin/pip install -q numpy pytest pytest-asyncio httpx loguru
.venv/bin/python -m pytest -q tests --ignore=tests/test_unified_architecture.py
```

Result: `1 failed, 57 passed, 5 warnings`. The failure is `TestPhaseEncoder.test_encode_different_inputs` because `sentence-transformers` is absent and `encode_to_phase()` falls back to the same all-zero vector for different inputs. Warnings include unawaited `KAIROSTemporalEngine.temporalize()` calls.

**Suggestion:** Convert async tests to `pytest.mark.asyncio` and `await` the coroutine bodies. Split dependencies into core/test/llm/dev extras, or skip tests requiring optional packages with clear markers. Treat unawaited coroutine warnings as failures in CI.

## Additional Notes

- `python -m compileall -q becomingone tests` passes.
- Full `pip install -r requirements.txt` was attempted in an isolated venv but did not complete in a reasonable review window because the ML dependency chain is heavy. The narrower verification above was used to avoid mutating system Python and to keep the review reproducible.
- The repo would benefit from a minimal CI matrix: syntax/import checks, core unit tests without ML dependencies, optional ML tests, and API integration tests.

## Suggested Priority Order

1. Fix API double initialization and HTTP status handling.
2. Lock down or gate `/reset` and other mutating admin endpoints.
3. Repair memory schema consistency (`TemporalState` to `TemporalSignature`) and add retrieval regression tests.
4. Fix action/LLM runtime crashes.
5. Rework dependency groups and async tests so CI catches these regressions.

Signed-off-by: Codex, GPT-5 coding agent

