# Coroutines Patterns

## Android coroutine rules

Use coroutines in a testable, lifecycle-aware way. Reference: [developer.android.com/kotlin/coroutines/coroutines-best-practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices).

**Data Synchronization:** For retry mechanisms with exponential backoff and background sync patterns, see `references/android-data-sync.md`.

### Inject Dispatchers (Avoid Hardcoding)

Inject `CoroutineDispatcher` (or a small wrapper) so production and test behavior are consistent.
When providing multiple dispatchers of the same type, use `@Qualifier` annotations so Hilt can distinguish them (see `limitedParallelism` section below for a full example).

```kotlin
@Retention(AnnotationRetention.BINARY)
@Qualifier
annotation class IoDispatcher

class AuthRepository @Inject constructor(
    private val remote: AuthRemoteDataSource,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun login(email: String, password: String): AuthResult =
        withContext(ioDispatcher) {
            remote.login(email, password)
        }
}
```

### Use `limitedParallelism` for Custom Dispatcher Pools

Use `limitedParallelism` instead of custom `ExecutorService` dispatchers — fewer threads and proper structured-concurrency integration.

```kotlin
// Define qualifier annotations to distinguish dispatchers of the same type
@Retention(AnnotationRetention.BINARY)
@Qualifier
annotation class DatabaseDispatcher

@Retention(AnnotationRetention.BINARY)
@Qualifier
annotation class CryptoDispatcher

@Module
@InstallIn(SingletonComponent::class)
object DispatchersModule {
    // Single-threaded dispatcher (e.g., for Room or SQLite operations)
    @DatabaseDispatcher
    @Provides
    @Singleton
    fun provideDatabaseDispatcher(): CoroutineDispatcher =
        Dispatchers.IO.limitedParallelism(1)

    // Limited concurrency for CPU-intensive work
    @CryptoDispatcher
    @Provides
    @Singleton
    fun provideCryptoDispatcher(): CoroutineDispatcher =
        Dispatchers.Default.limitedParallelism(4)
}

// Usage - qualifier tells Hilt which dispatcher to inject
class AuthTokenEncryptor @Inject constructor(
    @CryptoDispatcher private val cryptoDispatcher: CoroutineDispatcher
) {
    suspend fun encrypt(token: AuthToken): EncryptedToken = withContext(cryptoDispatcher) {
        performEncryption(token)
    }
}
```

Benefits over custom ExecutorService:

- Shares thread pool with parent dispatcher (more efficient)
- Proper integration with structured concurrency
- Automatic cleanup and resource management
- Better debugging and profiling support

### Structured concurrency (not `GlobalScope`)

Use `viewModelScope`/`lifecycleScope` for UI and inject external scope only when work must outlive UI.

```kotlin
class AuthSessionRefresher(
    private val authStore: AuthStore,
    private val externalScope: CoroutineScope,
    private val ioDispatcher: CoroutineDispatcher
) {
    fun refreshSession() {
        externalScope.launch(ioDispatcher) {
            authStore.refresh()
        }
    }
}
```

### Make Coroutines Cancellable

For long-running loops or blocking work, check for cancellation to keep UI responsive.

```kotlin
class AuthLogUploader(
    private val uploader: LogUploader
) {
    suspend fun upload(files: List<AuthLogFile>) {
        for (file in files) {
            ensureActive()
            uploader.upload(file)
        }
    }
}
```

### Handle Exceptions Carefully

Catch expected exceptions inside the coroutine. Never swallow `CancellationException`.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {

    fun login(email: String, password: String) {
        viewModelScope.launch {
            try {
                loginUseCase(email, password)
            } catch (e: IOException) {
                // expose UI error state
            } catch (e: CancellationException) {
                throw e
            }
        }
    }
}
```

### Do Not Catch `Throwable`

Catch only expected exception types. Avoid `catch (Throwable)` because it includes fatal errors and
`CancellationException`. Use a `CoroutineExceptionHandler` for unexpected failures so cancellation
propagates correctly without manual rethrowing.

```kotlin
private val crashHandler = CoroutineExceptionHandler { _, throwable ->
    crashReporter.record(throwable)
}

fun launchWithCrashReporting(block: suspend () -> Unit) {
    viewModelScope.launch(crashHandler) {
        block()
    }
}
```

Note on `CoroutineExceptionHandler`:

- `CoroutineExceptionHandler` only works when passed to the root coroutine (the initial `launch` or `async`).
It is ignored if passed to `withContext` or nested coroutines.

If you must catch `Throwable` (rare), rethrow `CancellationException` immediately so structured
concurrency remains intact.

### StateFlow for new code (not LiveData)

Use `StateFlow` for observable state and `SharedFlow` or `Channel` for events. Reserve `LiveData` for interop
or legacy code that still requires it. **Migration Priority:** If the project plan allows, prioritize refactoring and migrating existing `LiveData` to `StateFlow` by following the guidelines in `references/migration.md` -> `## LiveData to StateFlow`.

#### StateFlow vs SharedFlow vs Channel

| Type         | Best For                                    | Behavior                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
|--------------|---------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `StateFlow`  | UI state (forms, loading, data)             | Always holds one value. New collectors get the current value immediately.                                                                                                                                                                                                                                                                                                                                                                                                            |
| `SharedFlow` | Data or signals many observers need at once | **Multicast:** every active collector can see the same emissions. Optional `replay` re-delivers the last N values to **new** collectors (watch for duplicate handling after rotation or back stack). With defaults similar to `MutableSharedFlow()`, `emit()` **suspends** until there is subscriber capacity rather than dropping; **loss** comes from `tryEmit`, `DROP_OLDEST` / `DROP_LATEST` under buffer pressure, or tight `replay` / buffer sizing. |
| `Channel`    | One-shot **commands** (navigate, snackbar)  | **Unicast:** each element is consumed once by one receiver. Buffered channels hold work until a collector runs; expose with `receiveAsFlow()` for lifecycle-aware collection. Design for **one** consumer (typical single UI collector).                                                                                                                                                                                                                                             |

**Commands vs data, unicast vs multicast**

Treat navigation, snackbars, and dialogs as **commands**: they should run once per logical occurrence, not replay to every new observer. A `Channel` matches that shape: queued delivery to a single consumer, no accidental replay when a new collector starts.

Treat "session invalidated", "theme changed", or global bus-style signals as **data** or **broadcasts**: several layers may need the same event. That is the natural fit for `SharedFlow` (multicast).

**Required semantics for `SharedFlow`**

- `replay = 1` (or higher) fixes "missed last value" for late subscribers but **re-fires** that value whenever a new collector appears. Wrong shape for one-shot commands after configuration change.
- `MutableSharedFlow` defaults to `onBufferOverflow = BufferOverflow.SUSPEND`. You do not need to pass `SUSPEND` unless you want the call site to document intent; you pass a **non-default** overflow (for example `DROP_OLDEST`) when you intentionally prefer loss or conflation over blocking the emitter.
- With the default `SUSPEND`, `emit()` tends to **suspend** when there is no capacity, not silently drop. Loss is more tied to `tryEmit`, choosing `DROP_OLDEST` / `DROP_LATEST`, or tight buffer sizing under load.
- Larger `replay` or `extraBufferCapacity` with the default `SUSPEND` adds queue space before `emit()` suspends; the emitter can still wait until collectors drain the buffer (typical `viewModelScope` usage tolerates this; cancel when the `ViewModel` clears).

**Use when:** `Channel` + `receiveAsFlow()` for strict one-shot UI commands. `SharedFlow` when several collectors must observe the same emissions or when controlled replay is part of the product contract.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    // State: always has a value, conflates rapid updates
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.Loading)
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    // CORRECT: Channel = unicast one-shot commands; buffers until UI collects
    private val _events = Channel<AuthEvent>(Channel.BUFFERED)
    val events: Flow<AuthEvent> = _events.receiveAsFlow()

    // Use SharedFlow when several observers need the same event or replay/buffer tradeoffs are acceptable
    // private val _events = MutableSharedFlow<AuthEvent>(
    //     replay = 0,
    //     extraBufferCapacity = 1,
    //     onBufferOverflow = BufferOverflow.DROP_OLDEST
    // )
    // val events: SharedFlow<AuthEvent> = _events.asSharedFlow()

    fun login() {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            // ... do login ...
            _events.send(AuthEvent.LoginSuccess) // Channel: suspends if buffer is full
            // _events.emit(AuthEvent.LoginSuccess) // SharedFlow
        }
    }
}
```

**Common Mistake:** Using `StateFlow` for a one-off snackbar.
```kotlin
// Bad: StateFlow holds the value forever. You have to manually reset it to null after showing the snackbar.
private val _snackbarMessage = MutableStateFlow<String?>(null)

// Good: same patterns as other one-shot commands (Channel preferred; SharedFlow if you accept its tradeoffs)
private val _snackbarMessage = Channel<String>(Channel.BUFFERED)
val snackbarMessages: Flow<String> = _snackbarMessage.receiveAsFlow()
// Or: MutableSharedFlow<String>(replay = 0, extraBufferCapacity = 1, onBufferOverflow = BufferOverflow.DROP_OLDEST)
```

Note on buffering with SharedFlow:

- `replay` controls how many values new subscribers receive.
- `extraBufferCapacity` adds temporary queue space for bursts from active emitters.
- For **one-shot commands**, `replay = 1` (or higher) replays to every new collector — wrong default. Use `replay = 0` with an explicit buffer/overflow policy, or
  use a `Channel` instead of fighting multicast semantics.
When **late subscribers** must read only the **latest** value (state-like behavior),
`replay = 1` plus explicit `extraBufferCapacity` can match the product; treat that as sticky state, not
a consumed command.

Guidance for events vs state:

- **`Channel` + `receiveAsFlow()`** for strict one-shot commands (navigation, snackbars,
  one-time dialogs). **`SharedFlow`** when multiple collectors observe the same stream or
  replay to new subscribers is intended; size buffers and pick `onBufferOverflow` deliberately.
- **Best-effort** UI (some toasts, debug banners) may use a small `SharedFlow` if occasional drops are
  acceptable; do not label navigation that way unless the product truly allows missing the action.
- If an event must survive the UI being stopped, persist it as state and render it on resume
  (`StateFlow` / `ViewModel` state / persistence), rather than relying only on in-memory buffering.

### Convert Cold Flows to Hot StateFlows with `stateIn`

Use `stateIn` to share expensive Flow operations across multiple collectors and cache the latest value. 
This prevents repeated work when multiple UI components observe the same data.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    // Cold flow: each collector triggers separate database query
    private val authSessionFlow: Flow<AuthSession?> = authRepository.observeAuthSession()
    
    // Hot StateFlow: shared across all collectors, 5s stop timeout
    val authSession: StateFlow<AuthSession?> = authSessionFlow
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(stopTimeout = 5.seconds),
            initialValue = null
        )
}
```

Key `SharingStarted` strategies:

- `WhileSubscribed(5000)`: Stops upstream flow 5s after last collector unsubscribes. Best for most UI cases (survives quick config changes, saves resources when backgrounded).
- `Eagerly`: Starts immediately and never stops. Use for critical always-needed state (auth status, app config).
- `Lazily`: Starts on first subscriber, never stops. Use when you want to keep the flow hot after first access.

Common mistake: Using `stateIn` with `Eagerly` by default. Use `WhileSubscribed` to avoid wasted resources.

### Share Expensive Upstream with `shareIn`

Use `shareIn` to convert a cold Flow into a hot `SharedFlow` shared across multiple collectors. Unlike `stateIn`, it has no initial value and supports configurable replay.

```kotlin
@HiltViewModel
class NotificationsViewModel @Inject constructor(
    private val notificationRepository: NotificationRepository
) : ViewModel() {
    // Expensive upstream: WebSocket connection + parsing
    val notifications: SharedFlow<NotificationEvent> = notificationRepository
        .observeNotifications()
        .shareIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            replay = 0
        )
}
```

#### `stateIn` vs `shareIn`


|                   | `stateIn`                       | `shareIn`                    |
|-------------------|---------------------------------|------------------------------|
| Return type       | `StateFlow<T>`                  | `SharedFlow<T>`              |
| Initial value     | Required                        | Not needed                   |
| Replay            | Always 1 (latest)               | Configurable (0, 1, n)       |
| `.value` accessor | Yes                             | No                           |
| Use for           | UI state, always-available data | Event streams, notifications |


**Rule:** If collectors need `.value` or the current state at any time, use `stateIn`. If collectors only care about emissions after subscribing, use `shareIn`.

```kotlin
// stateIn: UI state - collectors need current value immediately
val userProfile: StateFlow<UserProfile?> = profileRepo.observe()
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

// shareIn: events - collectors only care about new emissions
val toastEvents: SharedFlow<ToastMessage> = eventBus.observe()
    .shareIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), replay = 0)
```

### Combine Multiple Flows with `combine`

Use `combine` to merge the **latest values** from multiple Flows into a single emission. Re-emits whenever any input Flow emits a new value.

```kotlin
@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val userRepository: UserRepository,
    private val settingsRepository: SettingsRepository,
    private val connectivityObserver: ConnectivityObserver
) : ViewModel() {
    val uiState: StateFlow<DashboardUiState> = combine(
        userRepository.observeUser(),
        settingsRepository.observeSettings(),
        connectivityObserver.observe()
    ) { user, settings, connectivity ->
        DashboardUiState(
            userName = user.displayName,
            theme = settings.theme,
            isOffline = connectivity == ConnectivityStatus.Lost
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = DashboardUiState()
    )
}
```

#### `combine` vs `zip`

- `combine` - emits on **any** input change using latest values from all. Use for independent state sources.
- `zip` - pairs emissions **1:1** in order, waits for both. Use for synchronized pairs.

```kotlin
// combine: re-emits when either changes (independent sources)
combine(userFlow, settingsFlow) { user, settings -> Pair(user, settings) }

// zip: waits for matching pairs (synchronized sources)
requestFlow.zip(responseFlow) { request, response -> Result(request, response) }
```

**Rule:** For ViewModel state composed from multiple repositories/data sources, always use `combine`. `zip` is rare - typically used for request/response pairing or synchronized streams.

### Avoid `async` with Immediate `await`

Don't use `async` followed immediately by `await` in the same scope. Use `withContext` for sequential work or call the suspend function directly.

```kotlin
// Good: direct call or withContext for sequential work
suspend fun fetchAuthProfile(): AuthProfile {
    val profile = withContext(Dispatchers.IO) {
        authRemote.fetchProfile()
    }
    return profile.toDomain()
}

// Good: simple sequential call
suspend fun refreshAuth(): AuthResult {
    return authRemote.refresh()
}
```

### `launch` vs `async` vs `withContext`

Use `launch` for side effects, `async` for parallel work that returns values, and `withContext` for sequential operations that need dispatcher switching or structured concurrency.

```kotlin
// launch: fire-and-forget side effects
fun refreshAuthState() {
    viewModelScope.launch {
        authSyncer.refreshSession()
    }
}

// async: parallel work returning values
suspend fun loadAuthDashboard(): AuthDashboard = coroutineScope {
    val deferreds = listOf(
        async { authRemote.fetchUser() },
        async { authRemote.fetchSessions() },
        async { authRemote.fetchSecurityStatus() }
    )

    val (user, sessions, security) = deferreds.awaitAll()

    AuthDashboard(user, sessions, security)
}

// withContext: sequential work with dispatcher switch
suspend fun processAuthData(data: AuthData): ProcessedAuth = withContext(Dispatchers.Default) {
    data.process()
}
```

### Use `awaitAll` for Parallel Work

Use `awaitAll()` so failures cancel remaining work promptly. It handles exceptions properly and cancels sibling coroutines when one fails.

```kotlin
suspend fun syncAuthData(): SyncResult = coroutineScope {
    try {
        val results = listOf(
            async { syncTokens() },
            async { syncPermissions() },
            async { syncPreferences() }
        ).awaitAll()
        
        SyncResult.Success(results)
    } catch (e: Exception) {
        // All remaining work is cancelled on first failure
        SyncResult.Failed(e)
    }
}
```

### Keep Suspend/Flow Thread-Safe

Suspend APIs must be safe to call from any dispatcher. Use `withContext` inside suspend functions and `flowOn` for
upstream flow work. Avoid dispatcher switching for trivial mapping logic, and keep domain and use-case layers dispatcher-agnostic.

```kotlin
class AuthAuditRepository(
    private val ioDispatcher: CoroutineDispatcher,
    private val auditStore: AuditStore
) {
    suspend fun readAuditLog(): List<AuthAuditEntry> =
        withContext(ioDispatcher) {
            auditStore.readAll()
        }
}
```

### Avoid Nested `withContext` Chains

Do not stack multiple `withContext` calls across layers. Switch dispatchers at clear boundaries
(typically data sources) and keep domain/use cases dispatcher-agnostic to avoid thread hopping.

```kotlin
class AuthRemoteDataSource(
    private val ioDispatcher: CoroutineDispatcher,
    private val api: AuthApi
) {
    suspend fun fetchUser(): AuthUser = withContext(ioDispatcher) {
        api.fetchUser()
    }
}

class FetchUserUseCase @Inject constructor(
    private val dataSource: AuthRemoteDataSource
) {
    suspend operator fun invoke(): AuthUser =
        dataSource.fetchUser()
}
```

### Avoid Blocking Calls in Coroutines

Do not call blocking APIs (`Thread.sleep`, blocking I/O, locks) on a coroutine thread. If unavoidable,
isolate the work on `Dispatchers.IO` (or a dedicated dispatcher).

```kotlin
class AuthLegacyKeyStore(
    private val ioDispatcher: CoroutineDispatcher,
    private val legacyStore: LegacyKeyStore
) {
    suspend fun loadKeys(): List<AuthKey> = withContext(ioDispatcher) {
        legacyStore.readKeysBlocking()
    }
}
```

### `coroutineScope` vs `supervisorScope` - Failure Propagation

Both are scope builders for use inside suspend functions. They differ on **what happens when one child fails**.

| Aspect                         | `coroutineScope { }`                                        | `supervisorScope { }`                                   |
|--------------------------------|-------------------------------------------------------------|---------------------------------------------------------|
| Child failure cancels siblings | Yes                                                         | No                                                      |
| Failure rethrown to caller     | Yes (first failure)                                         | No (contained per-child)                                |
| Use when                       | Children form one atomic unit. Partial results are useless. | Children are independent. Partial results are valuable. |

```kotlin
suspend fun loadDashboard() = coroutineScope {
    val user = async { api.fetchUser() }
    val orders = async { api.fetchOrders() }
    Dashboard(user.await(), orders.await())
}
```

If `fetchOrders()` fails, `fetchUser()` is cancelled and the exception is rethrown to the caller. Correct: there is no partial dashboard.

```kotlin
suspend fun warmCaches() = supervisorScope {
    launch { cache.warmTokens() }
    launch { cache.warmFeatures() }
    launch { cache.warmConfig() }
}
```

If `warmFeatures()` fails, `warmTokens` and `warmConfig` keep running. The function returns normally. Correct: a partially warmed cache is still a win.

**Decision rule:** ask "if one child fails, is there any value in the others' results?" Yes → `supervisorScope`. No → `coroutineScope`.

**With `async`:** in `supervisorScope`, exceptions thrown inside `async` are stored on the `Deferred` and only raised when you call `await()`. Always `await()` (or `awaitAll()`) every `async` you launch - see [Unawaited async in supervisorScope](#unawaited-async-in-supervisorscope).

### `supervisorScope` vs `SupervisorJob` - Independent Child Failures

Both let children fail independently without cancelling siblings. The difference is **where you use them** and **how exceptions are handled**.

#### `supervisorScope` - Scoped Supervision with Automatic Exception Containment

Use inside suspend functions. Child failures are contained automatically - they don't cancel siblings or propagate to the parent. The scope integrates with structured concurrency.

```kotlin
suspend fun refreshAuthCaches(): Unit = supervisorScope {
    launch { authCache.refreshTokens() }   // if this fails, sessions still runs
    launch { authCache.refreshSessions() } // independent of tokens
}
```

Exceptions from failed children are **contained** - they don't crash the app or propagate upward. You can optionally catch them inside each child for logging/recovery.

#### `SupervisorJob` - Explicit Scope with Manual Error Handling

Use when creating a `CoroutineScope` (Services, Repositories, custom scopes). Children fail independently, BUT **you must handle exceptions explicitly** - unhandled child exceptions still propagate to the `CoroutineExceptionHandler` or crash the app.

```kotlin
class RelayConnectionService : Service() {
    private val exceptionHandler = CoroutineExceptionHandler { _, throwable ->
        Log.e("RelayService", "Child failed: ${throwable.message}", throwable)
    }

    // SupervisorJob: children fail independently
    // CoroutineExceptionHandler: REQUIRED to catch unhandled child exceptions
    private val scope = CoroutineScope(
        SupervisorJob() + Dispatchers.IO + exceptionHandler
    )

    fun connectToRelays(relays: List<Relay>) {
        relays.forEach { relay ->
            scope.launch {
                relay.connect() // if this throws, other relays continue
            }
        }
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }
}
```

Without the `CoroutineExceptionHandler`, an unhandled exception from any child would crash the app - `SupervisorJob` only prevents sibling cancellation, it does not swallow exceptions.

#### Use when

| Scenario                                    | Use                                           |
|---------------------------------------------|-----------------------------------------------|
| Suspend function, parallel independent work | `supervisorScope`                             |
| Long-lived scope (Service, Repository)      | `SupervisorJob` + `CoroutineExceptionHandler` |
| `withContext` + supervision needed          | `supervisorScope` inside `withContext`        |

Forbidden: `withContext(SupervisorJob())` - see anti-pattern below.


#### Anti-Pattern: `withContext(SupervisorJob())`

Never pass `SupervisorJob()` directly to `withContext`. It creates an orphaned root Job - cancellation from outside won't propagate in, and child exceptions have no handler.

```kotlin
// BAD: orphaned Job, breaks structured concurrency, unhandled exceptions crash
suspend fun bad() = withContext(SupervisorJob()) {
    launch { throw Exception() } // no handler - crashes app
    launch { delay(1000) }       // parent cancellation won't reach here
}

// GOOD: supervisorScope for scoped supervision in suspend functions
suspend fun good() = supervisorScope {
    launch { throw Exception() } // contained, siblings continue
    launch { delay(1000) }       // runs independently
}

// GOOD: SupervisorJob scope with explicit error handling
val exceptionHandler = CoroutineExceptionHandler { _, throwable ->
    Log.e("Sync", "Child failed: ${throwable.message}", throwable)
}
val supervisedScope = CoroutineScope(SupervisorJob() + Dispatchers.IO + exceptionHandler)

fun startParallelSync() {
    supervisedScope.launch { syncUsers() }    // if this fails, orders sync continues
    supervisedScope.launch { syncOrders() }   // independent of users sync
}
```

### Functions Returning `Flow` Should Not Be `suspend`

Wrap any suspend setup inside the flow builder so collection triggers all work.

```kotlin
fun observeAuthEvents(): Flow<AuthEvent> = flow {
    val sources = authEventSources()
    emitAll(sources.asFlow().flatMapMerge { it.observe() })
}
```

### Use `flatMapLatest` for Sequential Flow Switching, `flatMapMerge` for Concurrent

Choose the right flattening operator based on whether you want to cancel previous work or run it concurrently.

```kotlin
// flatMapLatest: Cancels previous flow when input changes (search queries, user selections)
fun searchAuth(query: StateFlow<String>): Flow<List<AuthUser>> =
    query.flatMapLatest { searchQuery ->
        if (searchQuery.isEmpty()) {
            flowOf(emptyList())
        } else {
            authRepository.search(searchQuery)
        }
    }

// flatMapMerge: Runs flows concurrently (multiple independent data sources)
fun observeAuthEvents(): Flow<AuthEvent> = flow {
    val sources = authEventSources()
    emitAll(sources.asFlow().flatMapMerge { it.observe() })
}

// flatMapConcat: Sequential, waits for each flow to complete (rare, order-dependent processing)
fun processAuthBatches(batches: Flow<AuthBatch>): Flow<ProcessedBatch> =
    batches.flatMapConcat { batch ->
        flow { emit(processBatch(batch)) }
    }
```

When to use each:

- `flatMapLatest`: User-driven changes (search, filters, selections) where only the latest matters
- `flatMapMerge`: Multiple independent sources running in parallel
- `flatMapConcat`: Order-dependent sequential processing (rare)

### Backpressure & Rate Limiting

When a Flow producer emits faster than the collector can process, the producer suspends by default (back-pressured). Use these operators to control that behavior explicitly.

#### `buffer` - Decouple Producer and Collector

Run producer and collector concurrently with a buffer in between. Producer keeps emitting without waiting for slow collector.

```kotlin
sensorReadings()
    .buffer(64)
    .collect { reading ->
        // Slow processing - producer keeps emitting into buffer
        saveToDisk(reading)
    }
```

With overflow strategy:

```kotlin
highFrequencyEvents()
    .buffer(capacity = 100, onBufferOverflow = BufferOverflow.DROP_OLDEST)
    .collect { event ->
        processEvent(event)
    }
```

`BufferOverflow` strategies:

- `SUSPEND` (default) - suspends producer when buffer full
- `DROP_OLDEST` - drops oldest buffered value, never suspends producer
- `DROP_LATEST` - drops newest emission, never suspends producer

#### `conflate` - Keep Only Latest

Shorthand for `buffer(CONFLATED)`. Collector always gets the most recent emission, skipping intermediate values.

```kotlin
// UI only needs latest state - skip intermediate updates
locationUpdates()
    .conflate()
    .collect { location ->
        updateMapMarker(location)
    }
```

#### `debounce` - Wait for Quiet Period

Emit only after no new emissions for the specified duration. Restarts timer on each emission.

```kotlin
searchQueryFlow
    .debounce(300)
    .distinctUntilChanged()
    .flatMapLatest { query -> repository.search(query) }
    .collect { results -> updateUi(results) }
```

#### `sample` - Periodic Snapshots

Emit the most recent value at fixed intervals, regardless of emission frequency.

```kotlin
// Emit latest sensor reading every 100ms, even if sensor fires at 1000Hz
accelerometerFlow()
    .sample(100)
    .collect { reading -> updateDisplay(reading) }
```

#### Use when

| Scenario                                         | Operator                 |
|--------------------------------------------------|--------------------------|
| Slow collector, fast producer, all values matter | `buffer(capacity)`       |
| Slow collector, only latest value matters        | `conflate()`             |
| Fast producer, drop old when full                | `buffer(n, DROP_OLDEST)` |
| User input (search, text)                        | `debounce(ms)`           |
| Continuous stream, periodic sampling             | `sample(ms)`             |
| Suppress consecutive duplicates                  | `distinctUntilChanged()` |


#### Anti-Pattern

```kotlin
// BAD: Slow collector blocks fast producer, no backpressure handling
fastProducer()
    .collect { item ->
        heavyProcessing(item) // Producer suspended until this completes
    }

// GOOD: Buffer decouples producer and collector
fastProducer()
    .buffer(64, BufferOverflow.DROP_OLDEST)
    .collect { item ->
        heavyProcessing(item)
    }
```

### `suspend` for one-off values

Use a suspending function when only a single value is expected.

```kotlin
interface AuthRepository {
    suspend fun fetchCurrentUser(): AuthUser
}
```

### Coroutine names for long-lived work

For long-lived or background work, add `CoroutineName` to improve debugging and structured logs.

```kotlin
class AuthSessionRefresher(
    private val authStore: AuthStore,
    private val externalScope: CoroutineScope,
    private val ioDispatcher: CoroutineDispatcher
) {
    fun startPeriodicRefresh() {
        externalScope.launch(ioDispatcher + CoroutineName("AuthSessionRefresher")) {
            while (isActive) {
                authStore.refreshSessions()
                delay(30.minutes)
            }
        }
    }
}
```

### Avoid `Job` in `withContext` or Ad-Hoc `Job()` Usage

Passing a `Job` into `withContext` breaks structured concurrency. Use `coroutineScope`/`supervisorScope`
and keep a reference to the returned `Job` when you need cancellation.

```kotlin
class AuthSyncService(
    private val scope: CoroutineScope,
    private val authSyncer: AuthSyncer
) {
    private var syncJob: Job? = null

    fun startSync() {
        syncJob?.cancel()
        syncJob = scope.launch {
            authSyncer.syncAll()
        }
    }
}
```

### Yield During Heavy Work

For long-running CPU-bound loops, periodically call `yield()` to allow rescheduling, or `ensureActive()` when only
cancellation checks are needed. Avoid using either in short-lived or already suspending work.

```kotlin
suspend fun reconcileSessions(sessions: List<AuthSession>) = withContext(Dispatchers.Default) {
    sessions.forEachIndexed { index, session ->
        if (index % 50 == 0) {
            yield()
        }
        reconcile(session)
    }
}
```

### ViewModels Should Launch Coroutines (Not Expose `suspend`)

Keep async orchestration in the ViewModel. Expose UI triggers and let the ViewModel launch work.
Repositories/use cases remain `suspend`/`Flow`.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    fun onLoginClick(email: String, password: String) {
        viewModelScope.launch {
            loginUseCase(email, password)
        }
    }
}
```

### Repositories/Use Cases Should Not Launch Coroutines

Non-UI layers should expose `suspend` functions or `Flow` and let callers control scope/lifecycle.
This avoids hidden lifetimes and keeps cancellation/testability predictable.

```kotlin
class AuthRepository(
    private val remote: AuthRemoteDataSource
) {
    suspend fun refreshSession(): AuthSession =
        remote.refreshSession()
}

class RefreshSessionUseCase @Inject constructor(
    private val repository: AuthRepository
) {
    suspend operator fun invoke(): AuthSession =
        repository.refreshSession()
}

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val refreshSessionUseCase: RefreshSessionUseCase,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    fun onRefreshSession() {
        viewModelScope.launch {
            refreshSessionUseCase()
        }
    }
}
```

### Treat NonCancellable as a Last Resort

Use `NonCancellable` only for critical resource cleanup (such as camera, sensors, database connections, file handles) that
must complete even when the coroutine is cancelled. This prevents resource leaks but should be used sparingly.

`NonCancellable` doesn't prevent cancellation; it allows suspended functions to complete during the cancelling state. Keep cleanup code fast and bounded.

```kotlin
class CameraRepository(
    private val camera: Camera,  // CameraX or hardware wrapper
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun capturePhoto(): Photo = withContext(ioDispatcher) {
        try {
            camera.open()
            camera.capture()
        } finally {
            // Critical: release hardware even if cancelled
            withContext(NonCancellable) {
                camera.close()
            }
        }
    }
}
```

Warning: Never wrap normal business logic in `NonCancellable`. It should only guard cleanup code that prevents resource leaks or corruption.

### Timeouts for hardware and uncontrolled APIs

Use `withTimeout` or `withTimeoutOrNull` for operations that can hang indefinitely when interacting with hardware or third-party SDKs without built-in timeout mechanisms.

Configure HTTP timeouts at the client level (OkHttp, Ktor). Use `withTimeout`/`withTimeoutOrNull` only for APIs that expose no timeout control of their own (hardware SDKs, third-party callbacks).

```kotlin
class BiometricAuthRepository(
    private val biometricSdk: ThirdPartyBiometricSdk,
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun authenticate(): BiometricResult? =
        withTimeoutOrNull(30.seconds) {
            withContext(ioDispatcher) {
                biometricSdk.authenticate()
            }
        }
}

class HardwarePrinterRepository(
    private val printerSdk: ThirdPartyPrinterSdk,
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun print(document: PrintDocument): PrintResult =
        try {
            withTimeout(60.seconds) {
                withContext(ioDispatcher) {
                    printerSdk.print(document)
                }
            }
        } catch (e: TimeoutCancellationException) {
            PrintResult.Timeout
        }
}
```

- `withTimeout` throws `TimeoutCancellationException` (a `CancellationException`); it cancels the coroutine unless caught.
- Always wrap `withContext` *inside* `withTimeout`, never the reverse. The timeout must cover the dispatcher switch.
- Use `withTimeoutOrNull` when `null` is an acceptable outcome. Use `withTimeout` when timeout must be distinguished from other failures.

## Bridging Imperative Callbacks to Coroutines

Android and third-party SDKs expose many callback-based APIs. Use the right bridge depending on whether the callback produces **a stream of values** or **a single result**.


| Scenario                                               | Use                           |
|--------------------------------------------------------|-------------------------------|
| Callback fires **multiple times** (listener, observer) | `callbackFlow`                |
| Need **multiple concurrent coroutine producers**       | `channelFlow`                 |
| Callback fires **once** (completion, result)           | `suspendCancellableCoroutine` |


### `callbackFlow` - Callback Stream to Flow

Use `callbackFlow` to convert listener/observer callback APIs into cold Flows. Required for Android system APIs that use listener/callback patterns (ConnectivityManager, LocationManager, sensors, BroadcastReceiver).

### Core Pattern

```kotlin
fun observeNetworkStatus(
    connectivityManager: ConnectivityManager
): Flow<NetworkStatus> = callbackFlow {
    val callback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            trySend(NetworkStatus.Available)
        }
        override fun onLost(network: Network) {
            trySend(NetworkStatus.Lost)
        }
        override fun onCapabilitiesChanged(
            network: Network,
            capabilities: NetworkCapabilities
        ) {
            trySend(NetworkStatus.Changed(capabilities))
        }
    }

    val request = NetworkRequest.Builder()
        .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
        .build()

    connectivityManager.registerNetworkCallback(request, callback)

    awaitClose {
        connectivityManager.unregisterNetworkCallback(callback)
    }
}
```

**Rules:**

- **Always call `awaitClose {}`** - even if cleanup is empty. Without it, the flow closes immediately after the builder block completes.
- **Use `trySend()` from callbacks, not `send()`** - `trySend` is non-suspending and safe to call from any thread. `send()` is suspending and will throw if called from a non-coroutine context.
- **Callback registration APIs must be thread-safe** - `awaitClose` cleanup can race callback delivery, so `register`/`unregister` must be safe under concurrent calls.
- **Emit initial state before registering callback** - prevents collectors from missing the current value.
- **Unregister/cleanup in `awaitClose`** - mirrors the lifecycle of the collector.

#### Emit Initial State

```kotlin
fun observeLocationUpdates(
    locationManager: LocationManager
): Flow<Location> = callbackFlow {
    // Emit last known location immediately
    val lastKnown = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
    lastKnown?.let { trySend(it) }

    val listener = LocationListener { location -> trySend(location) }

    locationManager.requestLocationUpdates(
        LocationManager.GPS_PROVIDER, 5000L, 10f, listener
    )

    awaitClose { locationManager.removeUpdates(listener) }
}
```

#### BroadcastReceiver as Flow

```kotlin
fun Context.observeBatteryLevel(): Flow<Int> = callbackFlow {
    val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            trySend(level)
        }
    }

    registerReceiver(receiver, IntentFilter(Intent.ACTION_BATTERY_CHANGED))

    awaitClose { unregisterReceiver(receiver) }
}
```

#### Stabilize Rapidly Changing Callbacks

Combine `callbackFlow` with Flow operators to stabilize flapping signals:

```kotlin
fun observeStableNetworkStatus(
    connectivityManager: ConnectivityManager
): Flow<NetworkStatus> =
    observeNetworkStatus(connectivityManager)
        .distinctUntilChanged()
        .debounce(200)
        .flowOn(Dispatchers.IO)
```

#### `callbackFlow` Anti-Patterns

```kotlin
// BAD: Missing awaitClose - flow completes immediately
fun badFlow(): Flow<Event> = callbackFlow {
    api.registerListener { trySend(it) }
    // Flow closes here! Listener never cleaned up
}

// GOOD: Always include awaitClose
fun goodFlow(): Flow<Event> = callbackFlow {
    val cleanedUp = java.util.concurrent.atomic.AtomicBoolean(false)
    val listener = EventListener { trySend(it) }
    fun cleanupOnce() {
        if (cleanedUp.compareAndSet(false, true)) {
            api.unregisterListener(listener)
        }
    }
    api.registerListener(listener)
    awaitClose { cleanupOnce() }
}
```

```kotlin
// BAD: Using send() from callback thread
fun badFlow(): Flow<Event> = callbackFlow {
    api.registerListener { event ->
        send(event) // Compile error or crash: send is suspending
    }
    awaitClose { api.unregisterListener() }
}

// GOOD: Use trySend() from callbacks
fun goodFlow(): Flow<Event> = callbackFlow {
    api.registerListener { event ->
        trySend(event) // Non-suspending, thread-safe
    }
    awaitClose { api.unregisterListener() }
}
```

```kotlin
// BAD: Non-thread-safe awaitClose cleanup (races with callback thread cleanup)
fun badCleanupFlow(): Flow<Event> = callbackFlow {
    var cleanedUp = false

    val callback = object : StreamingCallback<Event> {
        override fun onNext(event: Event) {
            trySend(event)
        }

        override fun onClosed() {
            if (!cleanedUp) {
                cleanedUp = true
                api.unregisterCallback(this) // can race with awaitClose path
            }
            channel.close()
        }
    }

    api.registerCallback(callback)

    awaitClose {
        if (!cleanedUp) { // Race: callback thread may pass this check too
            cleanedUp = true
            api.unregisterCallback(callback)
        }
    }
}

// GOOD: Idempotent cleanup shared by callback and awaitClose
fun goodCleanupFlow(): Flow<Event> = callbackFlow {
    val cleanedUp = java.util.concurrent.atomic.AtomicBoolean(false)

    val callback = object : StreamingCallback<Event> {
        override fun onNext(event: Event) {
            trySend(event)
        }

        override fun onClosed() {
            cleanupOnce()
            channel.close()
        }
    }

    fun cleanupOnce() {
        if (cleanedUp.compareAndSet(false, true)) {
            api.unregisterCallback(callback)
        }
    }

    api.registerCallback(callback)
    awaitClose { cleanupOnce() }
}
```

#### `channelFlow` - Multiple Coroutine Producers

Use `channelFlow` when you need multiple coroutines producing into the same Flow. No `awaitClose` requirement.

```kotlin
fun mergeFeeds(repos: List<FeedRepository>): Flow<FeedItem> = channelFlow {
    repos.forEach { repo ->
        launch {
            repo.getFeed().collect { send(it) }
        }
    }
}
```

### `suspendCancellableCoroutine` - One-Shot Callback to Suspend

Use `suspendCancellableCoroutine` to convert a **single-result** callback into a suspend function. The coroutine suspends until `resume` or `resumeWithException` is called exactly once.

**Always prefer `suspendCancellableCoroutine` over `suspendCoroutine`** - it supports cancellation, which is critical for structured concurrency.

`suspendCoroutine` is acceptable only for narrow cases where all of the following are true:

- The API is truly one-shot and guaranteed to invoke exactly one terminal callback.
- There is no meaningful cancellation or cleanup path to execute.
- The operation is short-lived and does not hold scarce resources while waiting.
- You still enforce exact-once resume semantics.

#### Core Pattern

```kotlin
suspend fun authenticate(biometricManager: BiometricManager): AuthResult =
    suspendCancellableCoroutine { continuation ->
        biometricManager.authenticate(
            onSuccess = { token ->
                continuation.resume(token)
            },
            onError = { error ->
                continuation.resumeWithException(AuthException(error))
            }
        )

        continuation.invokeOnCancellation {
            biometricManager.cancel()
        }
    }
```

#### Common Use Cases

For Google Play Services and Firebase APIs that return `Task<T>`, prefer the official coroutine
adapter from `kotlinx-coroutines-play-services` (`import kotlinx.coroutines.tasks.await`) instead of
maintaining custom `Task<T>.await()` bridges.

```kotlin
import kotlinx.coroutines.tasks.await

// One-shot location request via official Task.await()
suspend fun getLastLocation(
    fusedLocationClient: FusedLocationProviderClient
): Location =
    fusedLocationClient.lastLocation.await()
        ?: throw LocationNotFoundException()
```

#### Returning Closeable Resources Safely

`suspendCancellableCoroutine` has prompt cancellation guarantees. If a callback returns a closeable
resource, cancellation may happen after `resume(resource)` but before the caller receives it. Use
`resume(value) { ... }` to close the resource in that race window.

```kotlin
suspend fun openFileHandle(api: FileApi): FileHandle =
    suspendCancellableCoroutine { cont ->
        api.openAsync(
            onSuccess = { handle ->
                cont.resume(handle) { _, handleToClose, _ ->
                    handleToClose.close()
                }
            },
            onError = { error ->
                cont.resumeWithException(error)
            }
        )

        cont.invokeOnCancellation {
            api.cancelOpen()
        }
    }
```

#### Rules

- **For APIs returning `Task<T>`, use official `await()` adapters** - prefer `kotlinx.coroutines.tasks.await` over custom bridge extensions.
- **Use `suspendCancellableCoroutine` for one-shot callbacks that are not `Task<T>`** - custom bridging still applies when no official adapter exists.
- **When resuming with closeable resources, use `resume(value) { ... }`** - ensures cancellation-time cleanup if the coroutine is cancelled before the caller observes the resource.
- **Treat `suspendCoroutine` as an exception, not a default** - use it only for truly non-cancellable, short-lived one-shot callbacks with no cleanup requirements.
- **Call `resume`/`resumeWithException` exactly once** - multiple calls throw `IllegalStateException`. Guard with `cont.isActive` when the callback can fire after cancellation.
- **Always implement `invokeOnCancellation`** - clean up resources (cancel requests, unregister listeners) when the coroutine is cancelled.
- **Cancellation cleanup must be thread-safe** - callbacks may fire concurrently with `invokeOnCancellation`, so cancellation/unregister logic must tolerate races.
- **Never block inside the lambda** - the lambda runs synchronously on the caller's thread. Register the callback and return immediately.

#### One-Shot Bridge Checklist

Before merging any `suspendCancellableCoroutine` bridge, confirm:

- Every success/error/disconnect callback path either `resume(...)` or `resumeWithException(...)`.
- No path can resume twice (guard multi-fire callbacks with `cont.isActive` and idempotent cleanup).
- Cancellation unregisters/cancels underlying work via `invokeOnCancellation`.
- If the API can stall indefinitely, wrap the bridge call with `withTimeout`/`withTimeoutOrNull`.
- Cleanup/unregister logic is race-safe between callback thread and cancellation thread.

```kotlin
suspend fun awaitConnectSafe(client: LegacyClient): Connection =
    withTimeout(5.seconds) {
        suspendCancellableCoroutine { cont ->
            val cleanedUp = java.util.concurrent.atomic.AtomicBoolean(false)

            fun cleanupOnce() {
                if (cleanedUp.compareAndSet(false, true)) {
                    client.disconnect()
                }
            }

            client.connect(
                onConnected = { connection ->
                    if (cont.isActive) cont.resume(connection)
                    cleanupOnce()
                },
                onError = { error ->
                    if (cont.isActive) cont.resumeWithException(error)
                    cleanupOnce()
                },
                onDisconnected = {
                    if (cont.isActive) {
                        cont.resumeWithException(IllegalStateException("Disconnected before connect"))
                    }
                    cleanupOnce()
                }
            )

            cont.invokeOnCancellation { cleanupOnce() }
        }
    }
```

#### Anti-Patterns

```kotlin
// BAD: Using suspendCoroutine - ignores cancellation
suspend fun badFetch(): Result = suspendCoroutine { cont ->
    api.fetch { result -> cont.resume(result) }
    // If coroutine is cancelled, api.fetch keeps running and cont.resume may crash
}

// GOOD: Using suspendCancellableCoroutine
suspend fun goodFetch(): Result = suspendCancellableCoroutine { cont ->
    val call = api.fetch { result ->
        if (cont.isActive) cont.resume(result)
    }
    cont.invokeOnCancellation { call.cancel() }
}
```

```kotlin
// BAD: Resuming multiple times
suspend fun bad(): String = suspendCancellableCoroutine { cont ->
    api.onSuccess { cont.resume(it) }
    api.onRetry { cont.resume(it) } // Crash: already resumed
}

// GOOD: Guard with isActive
suspend fun good(): String = suspendCancellableCoroutine { cont ->
    api.onSuccess { if (cont.isActive) cont.resume(it) }
    api.onRetry { if (cont.isActive) cont.resume(it) }
}
```

```kotlin
// BAD: Non-thread-safe invokeOnCancellation cleanup (races with callback thread)
suspend fun badCleanup(): Result = suspendCancellableCoroutine { cont ->
    var cleanedUp = false

    val callback = object : ApiCallback<Result> {
        override fun onSuccess(value: Result) {
            if (cont.isActive) cont.resume(value)
            if (!cleanedUp) {
                cleanedUp = true
                api.unregister(this)
            }
        }

        override fun onError(error: Throwable) {
            if (cont.isActive) cont.resumeWithException(error)
            if (!cleanedUp) {
                cleanedUp = true
                api.unregister(this)
            }
        }
    }

    api.register(callback)

    cont.invokeOnCancellation {
        if (!cleanedUp) { // Race: callback thread may pass this check too
            cleanedUp = true
            api.unregister(callback)
        }
    }
}

// GOOD: Idempotent cleanup shared by callback and cancellation paths
suspend fun goodCleanup(): Result = suspendCancellableCoroutine { cont ->
    val cleanedUp = java.util.concurrent.atomic.AtomicBoolean(false)

    val callback = object : ApiCallback<Result> {
        override fun onSuccess(value: Result) {
            if (cont.isActive) cont.resume(value)
            cleanupOnce()
        }

        override fun onError(error: Throwable) {
            if (cont.isActive) cont.resumeWithException(error)
            cleanupOnce()
        }
    }

    fun cleanupOnce() {
        if (cleanedUp.compareAndSet(false, true)) {
            api.unregister(callback)
        }
    }

    api.register(callback)
    cont.invokeOnCancellation { cleanupOnce() }
}
```

### Preserve Error Shape in Bridge APIs

When bridging callback APIs to suspend functions, keep the callback's data shape and error semantics
intact instead of flattening everything to generic `Exception(message)`.

#### Multi-Value Success -> Wrapper Result Type

If success callbacks return multiple values, wrap them in a single result type so the suspend API
stays explicit and strongly typed.

```kotlin
data class PurchaseBridgeResult(
    val transaction: StoreTransaction,
    val customerInfo: CustomerInfo
)

suspend fun purchase(params: PurchaseParams): PurchaseBridgeResult =
    suspendCancellableCoroutine { cont ->
        sdk.purchase(
            params = params,
            onSuccess = { tx, info ->
                cont.resume(PurchaseBridgeResult(tx, info))
            },
            onError = { error ->
                cont.resumeWithException(PurchaseBridgeException(error))
            }
        )
    }
```

#### Typed Exceptions -> Preserve Programmatic Handling

Map SDK/domain errors to typed exceptions that keep machine-readable fields (codes, cancellation
reason, retryability) so callers can branch safely.

```kotlin
open class PurchaseBridgeException(
    val error: PurchaseError
) : Exception(error.message)

class PurchaseCancelledException(
    error: PurchaseError
) : PurchaseBridgeException(error)

suspend fun restorePurchases(): CustomerInfo =
    suspendCancellableCoroutine { cont ->
        sdk.restore(
            onSuccess = { info -> cont.resume(info) },
            onError = { error ->
                val exception = if (error.code == PurchaseErrorCode.UserCancelled) {
                    PurchaseCancelledException(error)
                } else {
                    PurchaseBridgeException(error)
                }
                cont.resumeWithException(exception)
            }
        )
    }
```

#### Anti-Pattern: Losing Error Metadata

```kotlin
// BAD: Throws away typed error code/cause metadata
onError = { error ->
    cont.resumeWithException(Exception(error.message))
}

// GOOD: Preserve structured error for caller handling
onError = { error ->
    cont.resumeWithException(PurchaseBridgeException(error))
}
```

## Common Pitfalls

Quick-reference table of coroutine and Flow mistakes that are easy to miss during code review.

### Redundant SupervisorJob in ViewModel

`viewModelScope` already uses `SupervisorJob` internally. Adding another one creates a detached scope
that breaks structured concurrency.

```kotlin
// BAD: redundant SupervisorJob, creates orphaned scope
class MyViewModel : ViewModel() {
    private val scope = CoroutineScope(viewModelScope.coroutineContext + SupervisorJob())

    fun load() {
        scope.launch { /* ... */ } // not cancelled when ViewModel clears
    }
}

// GOOD: viewModelScope already has SupervisorJob
class MyViewModel : ViewModel() {
    fun load() {
        viewModelScope.launch { /* ... */ }
    }
}
```

### Unawaited async in supervisorScope

In `supervisorScope`, exceptions from unawaited `async` blocks are silently swallowed. The deferred
completes exceptionally but nobody observes it. Use `launch` when you don't need the result.

```kotlin
// BAD: exception silently lost - nobody calls await()
suspend fun syncAll() = supervisorScope {
    async { syncUsers() }   // if this throws, nobody knows
    async { syncOrders() }  // same problem
}

// GOOD: use launch when you don't need the return value
suspend fun syncAll() = supervisorScope {
    launch { syncUsers() }
    launch { syncOrders() }
}
```

### Side Effects Inside combine/map Transforms

Transform lambdas in `combine`, `map`, and similar operators re-execute on every resubscription
(e.g., after screen rotation). Launching coroutines or emitting events inside them causes
duplicate side effects.

```kotlin
// BAD: launches a coroutine on every resubscription (rotation fires it again)
val uiState = combine(userFlow, settingsFlow) { user, settings ->
    viewModelScope.launch { analytics.trackView(user.id) } // fires on every rotation
    UiState(user, settings)
}

// GOOD: move side effects to onEach or a dedicated handler
val uiState = combine(userFlow, settingsFlow) { user, settings ->
    UiState(user, settings)
}.onEach { state ->
    analytics.trackView(state.user.id)
}
```

### Collecting a Flow Inside a Transform

Calling `.first()` or `.firstOrNull()` inside a `map` or `combine` lambda creates a hidden
sequential fetch that re-executes on every upstream emission. Use `combine` to merge both flows
reactively instead.

```kotlin
// BAD: hidden suspend call inside combine, re-fetches on every emission
val uiState = userFlow.map { user ->
    val settings = settingsFlow.first() // blocks, re-fetches every time userFlow emits
    UiState(user, settings)
}

// GOOD: combine both flows reactively
val uiState = combine(userFlow, settingsFlow) { user, settings ->
    UiState(user, settings)
}
```

### Manual Job Cancellation Instead of flatMapLatest

A common pattern is cancelling a previous `Job` and re-launching on new input. `flatMapLatest`
handles this automatically and is less error-prone.

```kotlin
// BAD: manual Job? tracking
class SearchViewModel : ViewModel() {
    private var searchJob: Job? = null

    fun onQueryChanged(query: String) {
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            val results = repository.search(query)
            _uiState.update { it.copy(results = results) }
        }
    }
}

// GOOD: flatMapLatest cancels previous automatically
class SearchViewModel : ViewModel() {
    private val query = MutableStateFlow("")

    val uiState = query
        .debounce(300)
        .flatMapLatest { q -> repository.search(q) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    fun onQueryChanged(q: String) { query.value = q }
}
```

### `emit` vs `tryEmit`

`emit` suspends until the value is delivered. `tryEmit` returns `Boolean` (`false` = dropped because the buffer was full). Inside a coroutine, default to `emit`. Use `tryEmit` only from non-suspending contexts, or when dropping a value is acceptable.

With `BufferOverflow.DROP_OLDEST`/`DROP_LATEST`, `tryEmit` always returns `true`. Still prefer `emit` inside coroutines so the call stays correct if the overflow strategy changes.

### Using emit() on MutableStateFlow

`MutableStateFlow.emit()` is a suspending function but behaves identically to `.value =` assignment.
Using `emit()` misleads readers into thinking suspension is meaningful and adds unnecessary overhead.

```kotlin
// MISLEADING: emit() suspends but does nothing extra on MutableStateFlow
viewModelScope.launch {
    _uiState.emit(UiState.Loading) // no benefit over .value =
}

// CLEAR: direct assignment
_uiState.value = UiState.Loading
```

Use `.value =` for `MutableStateFlow`. Reserve `emit()` for `MutableSharedFlow` where suspension
actually matters (it suspends when the buffer is full).

## Coexisting with RxJava (Legacy Code)

For RxJava coexistence patterns (StateFlow bridge, disposal management, paging) and the
RxJava-to-Coroutines migration path, see [migration.md](/references/migration.md#rxjava-to-coroutines).