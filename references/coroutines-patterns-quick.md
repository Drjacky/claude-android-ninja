# Coroutines patterns (quick)

Full guide: [coroutines-patterns.md](coroutines-patterns.md) (~1630 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#coroutines-patternsmd-1633-lines).

Required before coroutine work in ViewModels/repositories:

- Inject `CoroutineDispatcher` with `@Qualifier`; no hardcoded `Dispatchers.IO` in production code.
- `viewModelScope` / `lifecycleScope` for UI; no `GlobalScope`.
- `StateFlow` for UI state; `Channel` + `receiveAsFlow()` for strict one-shot commands; `SharedFlow` only when multicast/replay is intended.
- ViewModels launch coroutines; repositories/use cases expose `suspend` / `Flow` - they do not launch.
- Retry/backoff/sync: [android-data-sync.md](android-data-sync.md). RxJava bridge: [migration.md](migration.md#rxjava-to-coroutines).

## Section routing

| Task | Open |
|------|------|
| Dispatchers, scopes, cancellation, exceptions | [Android coroutine rules](coroutines-patterns.md#android-coroutine-rules) |
| `StateFlow` vs `SharedFlow` vs `Channel` | [Android coroutine rules](coroutines-patterns.md#stateflow-for-new-code-not-livedata) |
| `stateIn`, `shareIn`, `combine` | [Android coroutine rules](coroutines-patterns.md#convert-cold-flows-to-hot-stateflows-with-statein) |
| `flatMapLatest`, backpressure, debounce | [Android coroutine rules](coroutines-patterns.md#flatmaplatest-for-sequential-flow-switching-flatmapmerge-for-concurrent) |
| `callbackFlow`, `suspendCancellableCoroutine` | [Bridging Imperative Callbacks to Coroutines](coroutines-patterns.md#bridging-imperative-callbacks-to-coroutines) |
| SupervisorJob, `combine` side effects, search debounce | [Common Pitfalls](coroutines-patterns.md#common-pitfalls) |
| Legacy RxJava coexistence | [Coexisting with RxJava](coroutines-patterns.md#coexisting-with-rxjava-legacy-code) |

## Hard rules (summary)

**Required:**

- `ensureActive()` in long loops; timeouts for hardware/uncontrolled APIs.
- `.value =` on `MutableStateFlow`; `emit()` on `MutableSharedFlow` when suspension matters.
- `withContext` for dispatcher switches; avoid nested `withContext` chains.

**Forbidden:**

- Catching bare `Throwable` in coroutine code.
- Blocking calls on the main dispatcher.
- `StateFlow` for one-shot snackbars/navigation (use `Channel` or deliberate `SharedFlow` policy).
- Repositories launching their own coroutines.

Open the full file for Hilt dispatcher modules, `callbackFlow` samples, and pitfall code blocks.
