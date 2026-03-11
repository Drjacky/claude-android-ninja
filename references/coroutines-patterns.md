# Coroutines Patterns

## Coroutines Best Practices (Android)

Use coroutines in a testable, lifecycle-aware way. Highlights from Android guidance:
[https://developer.android.com/kotlin/coroutines/coroutines-best-practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)

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

Prefer `limitedParallelism` over creating custom `ExecutorService` dispatchers. This is more efficient and integrates better with structured concurrency.

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

// Usage — qualifier tells Hilt which dispatcher to inject
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

### Avoid GlobalScope, Prefer Structured Concurrency

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
`CancellationException`. Prefer a `CoroutineExceptionHandler` for unexpected failures so cancellation
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

### Prefer StateFlow Over LiveData for New Code

Use `StateFlow` for observable state and `SharedFlow` for events. Reserve `LiveData` for interop
or legacy code that still requires it.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.Loading)
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    // replay is for new collectors; extraBufferCapacity is for bursts from existing collectors
    private val _events = MutableSharedFlow<AuthEvent>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val events: SharedFlow<AuthEvent> = _events.asSharedFlow()
}
```

Note on buffering:

- `replay` controls how many values new subscribers receive.
- `extraBufferCapacity` adds temporary queue space for bursts from active emitters.
If you want new subscribers to receive only the latest value, use `replay = 1` and optionally
add `extraBufferCapacity` for bursty emissions.

Guidance for events vs state:

- Use `SharedFlow(replay = 0)` for one-shot, lossy UI events (toasts, dialogs, navigation).
- If an event must survive the UI being stopped, persist it as state and render it on resume
(StateFlow/ViewModel state/persistence), rather than relying on buffering.

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

Common mistake: Using `stateIn` with `Eagerly` by default. Prefer `WhileSubscribed` to avoid wasted resources.

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

### Prefer `launch` for Fire-and-Forget, `async` for Values, `withContext` for Sequential Work

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

Prefer `awaitAll()` so failures cancel remaining work promptly. It handles exceptions properly and cancels sibling coroutines when one fails.

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

#### Decision Guide


| Scenario                                    | Use                                           | Why                                           |
|---------------------------------------------|-----------------------------------------------|-----------------------------------------------|
| Suspend function, parallel independent work | `supervisorScope`                             | Scoped, automatic exception containment       |
| Long-lived scope (Service, Repository)      | `SupervisorJob` + `CoroutineExceptionHandler` | Explicit lifecycle, explicit error handling   |
| `withContext` + supervision needed          | `supervisorScope` inside `withContext`        | Never pass `SupervisorJob()` to `withContext` |


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

#### Decision Guide


| Scenario                                         | Operator                 | Effect                    |
|--------------------------------------------------|--------------------------|---------------------------|
| Slow collector, fast producer, all values matter | `buffer(capacity)`       | Queues emissions          |
| Slow collector, only latest value matters        | `conflate()`             | Skips intermediate        |
| Fast producer, drop old when full                | `buffer(n, DROP_OLDEST)` | Bounded buffer, drops old |
| User input (search, text)                        | `debounce(ms)`           | Waits for pause           |
| Continuous stream, periodic sampling             | `sample(ms)`             | Fixed-rate snapshots      |
| Suppress consecutive duplicates                  | `distinctUntilChanged()` | Filters equal             |


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

### Prefer `suspend` for One-Off Values

Use a suspending function when only a single value is expected.

```kotlin
interface AuthRepository {
    suspend fun fetchCurrentUser(): AuthUser
}
```

### Prefer Explicit Coroutine Names for Long-Lived Work

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

Passing a `Job` into `withContext` breaks structured concurrency. Prefer `coroutineScope`/`supervisorScope`
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

### Prefer Explicit Timeouts for Hardware and Uncontrolled APIs

Use `withTimeout` or `withTimeoutOrNull` for operations that can hang indefinitely when interacting with hardware or third-party SDKs without built-in timeout mechanisms.

Note: Modern HTTP clients (OkHttp, Ktor) have sophisticated timeout configuration. Configure those at the client level instead of wrapping each call. Use explicit timeouts only when the underlying API has no timeout control.

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

Important notes:

- `withTimeout` throws `TimeoutCancellationException` (a subclass of `CancellationException`), which will cancel the coroutine unless caught and handled
- Wrap `withContext` inside `withTimeout`, not the other way around, so the timeout covers the full operation including dispatcher switch
- Use `withTimeoutOrNull` when a null result is acceptable; use `withTimeout` with explicit timeout handling when you need to distinguish timeout from other failures

## Bridging Imperative Callbacks to Coroutines

Android and third-party SDKs expose many callback-based APIs. Use the right bridge depending on whether the callback produces **a stream of values** or **a single result**.


| Scenario                                               | Use                           |
|--------------------------------------------------------|-------------------------------|
| Callback fires **multiple times** (listener, observer) | `callbackFlow`                |
| Callback fires **once** (completion, result)           | `suspendCancellableCoroutine` |
| Need **multiple concurrent coroutine producers**       | `channelFlow`                 |


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

#### `callbackFlow` Anti-Patterns

```kotlin
// BAD: Missing awaitClose - flow completes immediately
fun badFlow(): Flow<Event> = callbackFlow {
    api.registerListener { trySend(it) }
    // Flow closes here! Listener never cleaned up
}

// GOOD: Always include awaitClose
fun goodFlow(): Flow<Event> = callbackFlow {
    val listener = EventListener { trySend(it) }
    api.registerListener(listener)
    awaitClose { api.unregisterListener(listener) }
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

### `suspendCancellableCoroutine` - One-Shot Callback to Suspend

Use `suspendCancellableCoroutine` to convert a **single-result** callback into a suspend function. The coroutine suspends until `resume` or `resumeWithException` is called exactly once.

**Always prefer `suspendCancellableCoroutine` over `suspendCoroutine`** - it supports cancellation, which is critical for structured concurrency.

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

```kotlin
// One-shot location request
suspend fun getLastLocation(
    fusedLocationClient: FusedLocationProviderClient
): Location = suspendCancellableCoroutine { cont ->
    fusedLocationClient.lastLocation
        .addOnSuccessListener { location ->
            if (location != null) cont.resume(location)
            else cont.resumeWithException(LocationNotFoundException())
        }
        .addOnFailureListener { e ->
            cont.resumeWithException(e)
        }

    cont.invokeOnCancellation {
        // FusedLocationProviderClient tasks auto-cancel
    }
}

// Play Services Task to suspend
suspend fun <T> Task<T>.await(): T = suspendCancellableCoroutine { cont ->
    addOnSuccessListener { cont.resume(it) }
    addOnFailureListener { cont.resumeWithException(it) }
    addOnCanceledListener { cont.cancel() }
}
```

#### Rules

- **Use `suspendCancellableCoroutine`, not `suspendCoroutine`** - `suspendCoroutine` ignores cancellation, leaking work and preventing structured concurrency from cleaning up.
- **Call `resume`/`resumeWithException` exactly once** - multiple calls throw `IllegalStateException`. Use `cont.isActive` check if the callback might fire after cancellation.
- **Always implement `invokeOnCancellation`** - clean up resources (cancel requests, unregister listeners) when the coroutine is cancelled.
- **Never block inside the lambda** - the lambda runs synchronously on the caller's thread. Register the callback and return immediately.

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

## Coexisting with RxJava (Legacy Code)

When maintaining projects with both RxJava and Coroutines (migration not planned):

### Use StateFlow for All UI State

Even for RxJava-based ViewModels, expose UI state via `StateFlow` (not `LiveData`):

```kotlin
@HiltViewModel
class ProductsViewModel @Inject constructor(
    private val getProductsUseCase: GetProductsUseCase,  // RxJava-based
    private val disposables: CompositeDisposable
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<ProductsUiState>(ProductsUiState.Loading)
    val uiState: StateFlow<ProductsUiState> = _uiState.asStateFlow()
    
    fun loadProducts() {
        getProductsUseCase.execute()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .autoDispose(this)  // Or use disposables.add()
            .subscribe(
                { products ->
                    _uiState.value = ProductsUiState.Success(products)
                },
                { error ->
                    _uiState.value = ProductsUiState.Error(error.message ?: "Unknown error")
                }
            )
    }
    
    override fun onCleared() {
        super.onCleared()
        disposables.clear()
    }
}
```

### Compose Collection Remains Consistent

UI code uses `collectAsStateWithLifecycle()` regardless of whether ViewModel uses Coroutines or RxJava:

```kotlin
@Composable
fun ProductsRoute(viewModel: ProductsViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    ProductsScreen(
        state = uiState,
        onRetry = viewModel::loadProducts
    )
}
```

### Disposal Management

**Option 1: CompositeDisposable (recommended)**

```kotlin
class ProductsViewModel : ViewModel() {
    private val disposables = CompositeDisposable()
    
    fun loadProducts() {
        getProductsUseCase()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .subscribe(...)
            .also { disposables.add(it) }
    }
    
    override fun onCleared() {
        super.onCleared()
        disposables.clear()
    }
}
```

**Option 2: AutoDispose (third-party, requires base ViewModel)**

```kotlin
dependencies {
    implementation(libs.autodispose.android)
    implementation(libs.autodispose.android.archcomponents)
}

class ProductsViewModel : ViewModel(), LifecycleScopeProvider by AndroidLifecycleScopeProvider.from(this) {
    fun loadProducts() {
        getProductsUseCase()
            .subscribeOn(Schedulers.io())
            .observeOn(AndroidSchedulers.mainThread())
            .autoDispose(this)
            .subscribe(...)
    }
}
```

### Paging with RxJava

Use `paging-rxjava3` alongside `paging-compose`:

```kotlin
dependencies {
    implementation(libs.androidx.paging.runtime)
    implementation(libs.androidx.paging.compose)
    implementation(libs.androidx.paging.rxjava3)  // For RxJava sources
}

class ProductsPagingSource(
    private val productsApi: ProductsApi  // Returns RxJava observables
) : RxPagingSource<Int, Product>() {
    
    override fun loadSingle(params: LoadParams<Int>): Single<LoadResult<Int, Product>> {
        val page = params.key ?: 1
        
        return productsApi.getProducts(page, params.loadSize)
            .map { response ->
                LoadResult.Page(
                    data = response.products,
                    prevKey = if (page == 1) null else page - 1,
                    nextKey = if (response.hasMore) page + 1 else null
                ) as LoadResult<Int, Product>
            }
            .onErrorReturn { error ->
                LoadResult.Error(error)
            }
    }
    
    override fun getRefreshKey(state: PagingState<Int, Product>): Int? {
        return state.anchorPosition?.let { anchorPosition ->
            state.closestPageToPosition(anchorPosition)?.prevKey?.plus(1)
                ?: state.closestPageToPosition(anchorPosition)?.nextKey?.minus(1)
        }
    }
}

// ViewModel bridges to Flow for Compose
class ProductsViewModel @Inject constructor(
    private val productsApi: ProductsApi
) : ViewModel() {
    val products: Flow<PagingData<Product>> = Pager(
        config = PagingConfig(pageSize = 20),
        pagingSourceFactory = { ProductsPagingSource(productsApi) }
    ).flow
        .cachedIn(viewModelScope)
}
```

### Best Practices

1. **Unified UI layer**: Always use `StateFlow` for UI state, even when ViewModels use RxJava
2. **Isolate RxJava**: Keep RxJava usage in data/domain layers, convert to `StateFlow` at ViewModel boundary
3. **Dispose properly**: Use AutoDispose or `CompositeDisposable` to prevent leaks
4. **Don't mix in same function**: A function should be either fully Coroutines or fully RxJava, not both
5. **Prefer Coroutines for new code**: Only use RxJava for existing legacy code that won't be migrated

### Migration Path (When Ready)

When planning RxJava → Coroutines migration:

1. Start with data layer (repositories)
2. Then domain layer (use cases)
3. Finally ViewModels
4. UI layer already uses `StateFlow.collectAsStateWithLifecycle()`, so no changes needed

See [RxJava to Coroutines migration guide](https://developer.android.com/kotlin/coroutines/coroutines-adv#additional-resources) for detailed migration strategies.