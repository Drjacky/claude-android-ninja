# Kotlin Patterns & Best Practices

Concise Kotlin guidance for Android projects. Each item includes a short example so it is easy
to apply. If a topic is large, it lives in a dedicated reference and is linked here.

## Delegation (Composition over Inheritance)
Use delegation (`by`) to compose shared behavior instead of base classes. See:
`references/kotlin-delegation.md`.

## Prefer Read-Only Collection APIs
Expose `List`, `Set`, or `Map` from public APIs and keep mutable collections private. This keeps
mutation localized and makes state transitions explicit.

```kotlin
class AuthSessionStore {
    private val sessions = mutableMapOf<String, Session>()

    fun upsert(session: Session) {
        sessions[session.id] = session
    }

    fun snapshot(): Map<String, Session> = sessions
}
```

## Use Explicit State Transitions for Collections
Model collection changes as pure transformations so updates are predictable and testable.
This also makes it clear what “state machine” step is happening on each event.

```kotlin
sealed interface SessionEvent {
    data class Added(val session: Session) : SessionEvent
    data class Removed(val id: String) : SessionEvent
}

fun reduceSessions(
    current: List<Session>,
    event: SessionEvent
): List<Session> = when (event) {
    is SessionEvent.Added -> current + event.session
    is SessionEvent.Removed -> current.filterNot { it.id == event.id }
}
```

## Persistent Collections for State
When you store lists in Compose or ViewModel state, prefer persistent collections for structural
sharing and stable updates. This is covered in
`references/compose-patterns.md` → “Stability, Immutability, and Persistent Collections”.

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

### Test with runTest and Shared Scheduler
Use `runTest` and share the same scheduler across test dispatchers.

```kotlin
@Test
fun login_updates_auth_state() = runTest {
    val testDispatcher = UnconfinedTestDispatcher(testScheduler)
    val repository = AuthRepository(
        remote = FakeAuthRemoteDataSource(),
        ioDispatcher = testDispatcher
    )

    repository.login("user@example.com", "password")

    assertThat(repository.isLoggedIn()).isTrue()
}
```

### Avoid `async` with Immediate `await`
If you need the result immediately, call the suspend function directly or use `withContext`.

```kotlin
suspend fun fetchAuthProfile(): AuthProfile {
    val profile = authRemote.fetchProfile()
    return profile.toDomain()
}
```

### Use `awaitAll` for Parallel Work
Prefer `awaitAll()` so failures cancel remaining work promptly.

```kotlin
suspend fun loadAuthDashboard(): AuthDashboard = coroutineScope {
    val deferreds = listOf(
        async { authRemote.fetchUser() },
        async { authRemote.fetchSessions() },
        async { authRemote.fetchSecurityStatus() }
    )

    val (user, sessions, security) = deferreds.awaitAll()

    AuthDashboard(user, sessions, security)
}
```

### Keep Suspend/Flow Thread-Safe
Suspending functions should handle their own dispatcher using `withContext`, and flows should
use `flowOn` for upstream work.

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

### Prefer `supervisorScope` for Independent Task Failures Avoid passing a `SupervisorJob` into `withContext`;
it doesn't provide the isolation most expect because the scope itself will still fail if a child does.
Use `supervisorScope` instead to ensure that a failure in one child coroutine doesn't automatically cancel its siblings or the parent.

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
