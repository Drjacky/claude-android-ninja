# Design patterns (quick)

Full guide: [design-patterns.md](design-patterns.md) (~1760 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#design-patternsmd-1760-lines).

Required before introducing a pattern:

- Composition and delegation over inheritance - [kotlin-delegation.md](kotlin-delegation.md).
- Patterns stay in the correct layer (UI / Domain / Data) - [architecture.md](architecture.md), [modularization.md](modularization.md).
- Cache/sync/conflict patterns: [android-data-sync.md](android-data-sync.md) - not duplicated here.
- Start simple; add a pattern only when concrete pain forces it.

## Section routing

| Task | Open |
|------|------|
| When to use patterns, Kotlin-first rules | [Principles](design-patterns.md#principles) |
| MVVM, Repository | [Architectural Patterns](design-patterns.md#architectural-patterns) |
| Singleton, Factory, Builder, Prototype | [Creational Patterns](design-patterns.md#creational-patterns) |
| Adapter, Facade, Decorator, Proxy | [Structural Patterns](design-patterns.md#structural-patterns) |
| Observer, Strategy, State, Command | [Behavioral Patterns](design-patterns.md#behavioral-patterns) |
| `Result`, sealed state, extensions | [Kotlin-Specific Patterns](design-patterns.md#kotlin-specific-patterns) |
| God objects, GlobalScope, callback hell | [Anti-Patterns to Avoid](design-patterns.md#anti-patterns-to-avoid) |
| `@Upsert`, FTS, Room performance | [Room Database Patterns](design-patterns.md#room-database-patterns) |

## Hard rules (summary)

**Required:**

- DI scopes for app-wide lifetimes; no manual singletons.
- Feature modules must not depend on other feature modules.

**Forbidden:**

- Static `Context` references.
- `LiveData` in new code (use `StateFlow` - [migration.md](migration.md)).
- `GlobalScope` for app work.
- Premature abstraction before a second real use case.

Open the full file for Gang-of-Four examples, module placement, and Room FTS samples.
