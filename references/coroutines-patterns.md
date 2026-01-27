# Coroutines Patterns

## Coroutines Best Practices (Android)
Use coroutines in a testable, lifecycle-aware way. Highlights from Android guidance:
https://developer.android.com/kotlin/coroutines/coroutines-best-practices

### Inject Dispatchers (Avoid Hardcoding)
Inject `CoroutineDispatcher` (or a small wrapper) so production and test behavior are consistent.

```kotlin
class AuthRepository(
    private val remote: AuthRemoteDataSource,
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun login(email: String, password: String): AuthResult =
        withContext(ioDispatcher) {
            remote.login(email, password)
        }
}
```

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

### Test with runTest and Shared Scheduler
Use `runTest` and share the same scheduler across test dispatchers.

```kotlin
@Test
fun `login updates auth state`() = runTest {
    val testDispatcher = UnconfinedTestDispatcher(testScheduler)
    val repository = AuthRepository(
        remote = FakeAuthRemoteDataSource(),
        ioDispatcher = testDispatcher
    )

    repository.login("user@example.com", "password")

    assertThat(repository.isLoggedIn()).isTrue()
}
```

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
        extraBufferCapacity = 1
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

### Prefer `supervisorScope` for Independent Task Failures
Avoid passing a `SupervisorJob` into `withContext`; it doesn't provide the isolation most expect because the scope itself
will still fail if a child does. Use `supervisorScope` instead so one child failure doesn't cancel siblings or the parent.

```kotlin
suspend fun refreshAuthCaches(): Unit = supervisorScope {
    launch { authCache.refreshTokens() }
    launch { authCache.refreshSessions() }
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
    private val camera: Camera2,
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
    suspend fun authenticate(): BiometricResult? = withContext(ioDispatcher) {
        // Third-party SDK has no timeout mechanism, so we add one
        withTimeoutOrNull(30.seconds) {
            biometricSdk.authenticate()
        }
    }
}

class HardwarePrinterRepository(
    private val printerSdk: ThirdPartyPrinterSdk,
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun print(document: PrintDocument): PrintResult = withContext(ioDispatcher) {
        // Hardware operations can hang on device issues
        try {
            withTimeout(60.seconds) {
                printerSdk.print(document)
            }
        } catch (e: TimeoutCancellationException) {
            // Handle timeout as a specific failure case
            PrintResult.Timeout
        }
    }
}
```

Important notes:
- `withTimeout` throws `TimeoutCancellationException` (a subclass of `CancellationException`), which will cancel the coroutine unless caught and handled
- Wrap `withContext` with timeout, not the other way around, so the timeout covers the full operation including dispatcher switch
- Use `withTimeoutOrNull` when a null result is acceptable; use `withTimeout` with explicit timeout handling when you need to distinguish timeout from other failures
