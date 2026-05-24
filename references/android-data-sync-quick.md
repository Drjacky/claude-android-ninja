# Data sync (quick)

Full guide: [android-data-sync.md](android-data-sync.md) (~2350 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-data-syncmd-2350-lines).

## Section routing

| Task | Open |
|------|------|
| Offline-first layering | [Offline-First Architecture](android-data-sync.md#offline-first-architecture) |
| Room tuning | [Database Optimization](android-data-sync.md#database-optimization-roomsqlite) |
| Connectivity `Flow` | [Network State Monitoring](android-data-sync.md#network-state-monitoring) |
| When/how to sync | [Sync Strategies](android-data-sync.md#sync-strategies) |
| Merge policy | [Conflict Resolution](android-data-sync.md#conflict-resolution) |
| Cache keys | [Cache Invalidation](android-data-sync.md#cache-invalidation) |
| Backoff | [Retry Mechanisms](android-data-sync.md#retry-mechanisms) |
| Workers | [WorkManager Integration](android-data-sync.md#workmanager-integration) |
| Repository API shape | [Repository Pattern for Sync](android-data-sync.md#repository-pattern-for-sync) |
| ViewModel wiring | [Architecture Integration](android-data-sync.md#architecture-integration) |
| Fakes, offline tests | [Testing](android-data-sync.md#testing) |
| Full rule list | [Rules](android-data-sync.md#rules) |

## Hard rules (summary)

**Required:**

- UI reads Room only; network writes through repository into DB first.
- Sync metadata on entities: `syncStatus`, `lastModified`, `serverVersion` (or project equivalent).
- `NetworkMonitor` before sync; one conflict strategy per entity type documented on the repository.
- Exponential backoff with jitter; invalidate cache on writes.
- Partial sync failures surface counts; do not drop local edits on sync failure.

**Forbidden:**

- ViewModels calling Retrofit/OkHttp directly.
- Unbounded retries; silent conflict drops.
- Auto-sync on metered without opt-in.
- DataStore/SharedPreferences for relational list data.
- Leaked repository `CoroutineScope`.

Paging + remote: [compose-patterns.md → Offline-first paging](compose-patterns.md#offline-first-paging-and-remotemediator).
