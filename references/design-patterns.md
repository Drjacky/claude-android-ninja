# Design Patterns (Android-Focused)

This guide maps classic design patterns to practical Android usage while staying aligned with
our architecture (`references/architecture.md`), modularization rules (`references/modularization.md`), and Compose-first code.
Use this when designing new features, modules, pure business logic, or shared utilities.

## Principles for This Codebase
- Prefer composition and delegation over inheritance. See `references/kotlin-delegation.md`.
- Keep patterns local to the layer they belong to (UI vs Domain vs Data).
- Avoid framework-heavy base classes; keep components testable.
- For app-wide lifetimes, rely on DI scopes instead of manual singletons.

## Creational Patterns

### Singleton
- **When**: You need a single, app-wide instance.
- **Android use**: Use DI with `@Singleton` for repositories, loggers, and crash reporters.
- **Notes**: Avoid holding `Context` in static objects; inject `Application` if needed.

### Factory Method
- **When**: The concrete class should vary by environment or runtime.
- **Android use**: `ViewModelProvider.Factory`, `WorkManager` factories, Retrofit service creation.
- **Notes**: Keep factory interfaces in `core/domain` or `core/common`.

### Abstract Factory
- **When**: You need families of related implementations.
- **Android use**: Provide `RemoteAuthDataSource` + `LocalAuthDataSource` families for prod vs mock.
- **Notes**: Useful for swapping providers (e.g., Crashlytics vs Sentry).

### Builder
- **When**: Complex object configuration needs clarity or optional steps.
- **Android use**: `OkHttpClient.Builder`, `Retrofit.Builder`, `NotificationCompat.Builder`.
- **Notes**: Prefer immutable outputs; keep configuration in one place (e.g., DI module).

### Prototype
- **When**: Cloning is cheaper than new construction.
- **Android use**: Copying immutable UI models (`data class.copy`) for state updates.
- **Notes**: Works well with `UiState` and form screens.

## Structural Patterns

### Adapter
- **When**: You need to reconcile mismatched interfaces.
- **Android use**: Mapping network DTOs to domain models; legacy View adapters.
- **Notes**: Keep adapters in `core/data` or `core/ui` depending on direction.

### Bridge
- **When**: You want UI to vary independently of its implementation.
- **Android use**: `Navigator` interfaces in features with app-level implementations.
- **Notes**: Keeps features independent and testable.

### Composite
- **When**: You need tree-like structures with uniform treatment.
- **Android use**: Navigation graphs, UI component trees, menu structures.
- **Notes**: Helps build adaptive UI structures for tablets/foldables.

### Decorator
- **When**: Add behavior without modifying the original type.
- **Android use**: OkHttp interceptors, Compose `Modifier` chains, logging decorators.
- **Notes**: Keep decorators small and composable.

### Facade
- **When**: Provide a simplified API to complex subsystems.
- **Android use**: Repositories hiding local/remote/cache details.
- **Notes**: Repositories should be the public entry for data access.

### Flyweight
- **When**: You need to reduce memory by sharing common state.
- **Android use**: Image loading caches, shared UI resources, reused `Painter`s.
- **Notes**: Avoid recreating heavy objects inside composables.

### Proxy
- **When**: You need to control access to an expensive or remote object.
- **Android use**: Remote data sources, lazy initialization for analytics/crash reporters.
- **Notes**: Keep proxy logic in the data layer.

## Behavioral Patterns

### Observer
- **When**: Many dependents must react to state changes.
- **Android use**: `Flow`, `StateFlow`, `LiveData` in ViewModels and repositories.
- **Notes**: Prefer `Flow` for consistency and testability.

### Strategy
- **When**: Multiple interchangeable algorithms are needed.
- **Android use**: Auth providers, caching strategies, feature flag resolution.
- **Notes**: Inject the strategy; don’t branch on build flavors in business logic.

### Chain of Responsibility
- **When**: A request should pass through a sequence of handlers.
- **Android use**: OkHttp interceptors, validation pipelines, auth token refresh chain.
- **Notes**: Keep each handler focused and easily testable.

### Command
- **When**: You want to encapsulate actions as objects.
- **Android use**: UI actions/intents from screens → ViewModel.
- **Notes**: Prefer sealed `Action` types in the Presentation layer.

### Iterator
- **When**: You need sequential access without exposing structure.
- **Android use**: Paging data flows, cursor traversal in data layer.
- **Notes**: Keep iteration in data/paging layers, not UI.

### Mediator
- **When**: Multiple components need coordinated interaction.
- **Android use**: App-level navigation coordinator (`AppNavigation`).
- **Notes**: Keeps features independent from each other.

### Memento
- **When**: You must restore state without breaking encapsulation.
- **Android use**: `SavedStateHandle`, restoring form drafts or auth flows.
- **Notes**: Keep state snapshots minimal and serializable.

### State
- **When**: Behavior changes with state.
- **Android use**: `UiState` sealed types and state-driven UI.
- **Notes**: Keep transitions in ViewModel; UI only renders.

### Template Method
- **When**: You need a fixed algorithm with varying steps.
- **Android use**: Base worker patterns or shared use case flows.
- **Notes**: Prefer composition/delegation before inheritance.

### Visitor
- **When**: You need to run operations over a structure without changing it.
- **Android use**: Analytics/event inspection over `UiState` or navigation events.
- **Notes**: Use only if it improves clarity; avoid overengineering.
