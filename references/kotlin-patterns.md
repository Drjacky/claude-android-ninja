# Kotlin Patterns

Intermediate and advanced Kotlin rules for Android. Basic language features (data classes, null safety, scope functions) are assumed. Each item ships with a runnable example; large topics link to dedicated references.

Time-related examples use `kotlin.time.Duration` and `kotlinx.datetime.Clock`. Do not use `java.util.Date`/`Calendar` or `Long` millis in domain code.

## Table of Contents
1. [Kotlin 2.x and the K2 Compiler](#kotlin-2x-and-the-k2-compiler)
2. [Delegation (Composition over Inheritance)](#delegation-composition-over-inheritance)
3. [Pragmatic layering & import hygiene](#pragmatic-layering--import-hygiene)
4. [Collection APIs](#collection-apis)
5. [Sealed Classes & Exhaustive When](#sealed-classes--exhaustive-when)
6. [Generics & Reified Types](#generics--reified-types)
7. [Extension Functions](#extension-functions)
8. [Inline Value Classes](#inline-value-classes)
9. [Sequences for Lazy Evaluation](#sequences-for-lazy-evaluation)
10. [Companion Objects](#companion-objects)
11. [Type Aliases](#type-aliases)
12. [Android View Lifecycle (Interop)](#android-view-lifecycle-interop)
13. [Coroutines routing](#coroutines-routing)

## Kotlin 2.x and the K2 Compiler

Target **Kotlin 2.x**. Pinned version lives in `assets/libs.versions.toml.template`. K2 is the default and only supported frontend on Kotlin 2.0+. All patterns below assume K2.

### Behavioural differences vs K1

- Stricter nullability in generic chains. Declare explicit nullability instead of relying on inference.
- More aggressive smart-casts inside lambdas and local functions. Do not add redundant `!!` or re-checks.
- Tighter exhaustiveness checking on `when`. Treat new warnings as errors.
- New diagnostics may surface latent bugs in previously-compiling code. Fix them; do not downgrade.

### Compose compiler

Compose compiler ships with Kotlin 2.x. Apply it as a Gradle plugin. Do not depend on `androidx.compose.compiler:compiler` and do not set `kotlinCompilerExtensionVersion`.

```kotlin
plugins {
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}
```

Plugin id: `org.jetbrains.kotlin.plugin.compose`. Its version always matches `kotlin` in the catalog (see `kotlin-compose` in `assets/libs.versions.toml.template`).

Configure Compose-specific options via the plugin block, never via `freeCompilerArgs`:

```kotlin
composeCompiler {
    reportsDestination = layout.buildDirectory.dir("compose_compiler")
    stabilityConfigurationFiles.add(
        rootProject.layout.projectDirectory.file("compose_compiler_config.conf")
    )
}
```

Stability-report usage: `references/compose-patterns.md`. Convention plugin wiring: `references/gradle-setup.md`.

### Explicit API mode

Enable explicit API mode in every non-`:app` module. Required for `core:*` and `feature:*`. Skip for `:app`.

```kotlin
kotlin {
    explicitApi()
}
```

Per-compilation form: `explicitApi = ExplicitApiMode.Strict`.

### Things to remove on Kotlin 2.x

- `kotlinCompilerExtensionVersion = "…"` inside `composeOptions { }` - ignored, warns.
- `languageVersion = "1.9"` - obsolete.
- `useK2 = true` - obsolete; K2 is default.

## Delegation (Composition over Inheritance)

Use delegation (`by`) to compose shared behavior instead of base classes.

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    crashReporter: CrashReporter,
    logger: Logger
) : ViewModel(), 
    CrashReporter by crashReporter,
    Logger by logger {
    
    fun onLoginClicked() {
        log("Login clicked") // Delegated
        // ... logic
    }
}
```

Full delegation patterns and tests: `references/kotlin-delegation.md`.

## Pragmatic layering & import hygiene

Keep types and file structure easy to read. This aligns with `references/architecture.md` (layers) and `references/compose-patterns.md` (screens and state).

### Import hygiene

Never bury types behind long fully qualified names in business logic. Import at the top of the file; use `import … as …` when two layers expose the same simple name.

```kotlin
// Bad - package noise hides intent
val unit = com.example.app.data.db.entity.enums.WeightUnit.entries
    .find { it.name == rawValue }

// Good
import com.example.app.data.db.entity.enums.WeightUnit

val unit = WeightUnit.entries.find { it.name == rawValue }

// Good - clash between DB and domain enums
import com.example.app.data.db.entity.enums.WeightUnit as DbWeightUnit
import com.example.app.domain.model.WeightUnit

val dbUnit = DbWeightUnit.entries.find { it.name == rawValue }
val domainUnit = WeightUnit.fromDb(dbUnit)
```

**Alias naming:** suffix or prefix with the layer (`Db`, `Api`, `Dto`, `Ui`, `Domain`) so readers see which world a value belongs to.

### Use cases that only wrap repositories

A class that only forwards to a repository with no extra policy, validation, or reuse is **noise**:

```kotlin
// Often unnecessary - call the repository from the ViewModel instead
class GetSettingsUseCase(private val repository: SettingsRepository) {
    suspend operator fun invoke() = repository.getSettings()
}
```

Keep a **use case** (or domain service) when logic is multi-step, reused across features, policy-heavy, or worth unit-testing on its own - not when it is a one-line pass-through.

### State updates without extra type layers

Use **sealed actions**, **`UiState`**, and **one-shot events** (`SharedFlow` or `Channel`) from the ViewModel. Apply state changes with `when (action) { ... }` + `MutableStateFlow.update`.

Forbidden: a fourth parallel type (`Result`, `PartialState`, a mandatory pure `reduce`) when every action maps 1:1 to a state change.

Add a dedicated reducer or intermediate "result" type only when many sources (events, async completions, pushes, sockets) must funnel through one centralized transition function.

### Composable boundaries

Extract composables when there is **real reuse**, a **stable API**, or a clear visual/behavioral boundary. Do not extract one-line wrappers around `Text` / `Spacer` or "components" used only once - see `references/compose-patterns.md` → "View Composition Rules".

## Collection APIs

### Read-only collection APIs

Expose `List`, `Set`, or `Map` from public APIs and keep mutable collections private. This keeps
mutation localized and makes state transitions explicit.

```kotlin
class AuthSessionStore {
    private val sessions = mutableMapOf<String, Session>()

    fun upsert(session: Session) {
        sessions[session.id] = session
    }

    fun snapshot(): Map<String, Session> = sessions.toMap() // Return copy, not reference
}
```

### Use Explicit State Transitions for Collections

Model collection changes as pure transformations so updates are predictable and testable.
This also makes it clear what "state machine" step is happening on each event.

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

### Persistent Collections for State

When you store lists in Compose or ViewModel state, prefer persistent collections for structural
sharing and stable updates. See: `references/compose-patterns.md` → "Performance Optimization" → "Persistent Collections for Performance".

## Sealed Classes & Exhaustive When

Use sealed classes/interfaces for closed type hierarchies with exhaustive `when` expressions.

```kotlin
// Domain errors
sealed class AuthError(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class NetworkError(message: String, cause: Throwable? = null) : AuthError(message, cause)
    class InvalidCredentials(message: String) : AuthError(message)
    class ServerError(message: String, cause: Throwable? = null) : AuthError(message, cause)
}

// UI state
@Immutable
sealed interface AuthUiState {
    data object Loading : AuthUiState
    data class Form(val email: String, val error: String?) : AuthUiState
    data class Success(val user: User) : AuthUiState
}

// Exhaustive when (compiler enforces all cases)
fun handleAuthError(error: AuthError): String = when (error) {
    is AuthError.NetworkError -> "No internet connection"
    is AuthError.InvalidCredentials -> "Invalid credentials"
    is AuthError.ServerError -> "Server error"
} // No else needed; compiler ensures all cases covered

@Composable
fun AuthScreen(uiState: AuthUiState) {
    when (uiState) {
        is AuthUiState.Loading -> LoadingIndicator()
        is AuthUiState.Form -> LoginForm(uiState)
        is AuthUiState.Success -> WelcomeScreen(uiState.user)
    } // Exhaustive
}
```

See: `references/design-patterns.md` → "Kotlin-Specific Patterns" → "Sealed Classes for Exhaustive State".

## Generics & Reified Types

### Generic Result Wrapper

Use generics for type-safe wrappers and error handling:

```kotlin
// CORRECT: Generic Result type
sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val exception: Exception) : Result<Nothing>()
}

// Repository with generic Result
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    suspend fun getProfile(userId: String): Result<UserProfile>
}

// Usage
suspend fun handleLogin(email: String, password: String) {
    when (val result = authRepository.login(email, password)) {
        is Result.Success -> handleSuccess(result.data) // Type-safe: AuthToken
        is Result.Error -> handleError(result.exception)
    }
}
```

Kotlin stdlib ships `Result<T>`; add a sealed domain result when branches need more structure than `Result` exposes.

### Reified Type Parameters

Use `reified` with `inline` functions for runtime type information:

```kotlin
// CORRECT: Type-safe JSON parsing with reified
inline fun <reified T> parseJson(json: String): T {
    return Json.decodeFromString<T>(json)
}

// Usage (no need to pass class reference)
val user: User = parseJson(jsonString)
val token: AuthToken = parseJson(tokenJson)

// CORRECT: Type-safe navigation argument retrieval
inline fun <reified T> SavedStateHandle.getOrNull(key: String): T? =
    get<T>(key)

// CORRECT: Type-safe Retrofit service creation wrapper
inline fun <reified T> Retrofit.create(): T {
    return create(T::class.java)
}

// CORRECT: Room 3 DAO with reified type
inline fun <reified T> Database.dao(): T {
    return when (T::class) {
        UserDao::class -> userDao() as T
        AuthDao::class -> authDao() as T
        else -> error("Unknown DAO type")
    }
}
```

**Rules for Reified:**
- Only works with `inline` functions
- Provides compile-time type safety with runtime access
- Use for: Dependency injection helpers, JSON parsing, type-safe casting

### Generic Collections with Bounds

```kotlin
// Generic list processor with upper bound
fun <T : User> processUsers(users: List<T>): List<String> =
    users.map { it.name }

// Generic repository pattern
interface Repository<T, ID> {
    suspend fun getById(id: ID): Result<T>
    suspend fun save(entity: T): Result<Unit>
    fun observeAll(): Flow<List<T>>
}

class UserRepository @Inject constructor(
    private val dao: UserDao
) : Repository<User, String> {
    override suspend fun getById(id: String): Result<User> = runCatching {
        dao.getUserById(id)
    }
    
    override suspend fun save(entity: User): Result<Unit> = runCatching {
        dao.insert(entity)
    }
    
    override fun observeAll(): Flow<List<User>> = dao.observeAll()
}
```

## Extension Functions

Add domain-specific behavior to existing types without inheritance.

```kotlin
// Domain logic extensions
fun User.isActive(): Boolean = 
    isVerified && lastActiveAt > Clock.System.now().minus(30.days).toEpochMilliseconds()

fun User.displayName(): String = 
    name.ifEmpty { email.substringBefore("@") }

fun List<User>.filterActive(): List<User> = 
    filter { it.isActive() }

// UI formatting extensions
fun Long.toRelativeTime(): String {
    val now = Clock.System.now().toEpochMilliseconds()
    val diff = (now - this).milliseconds
    
    return when {
        diff < 1.minutes -> "Just now"
        diff < 1.hours -> "${diff.inWholeMinutes}m ago"
        diff < 1.days -> "${diff.inWholeHours}h ago"
        else -> "${diff.inWholeDays}d ago"
    }
}

// Flow extensions
fun <T> Flow<T>.throttle(period: Duration): Flow<T> = flow {
    var lastEmitTime = 0L
    collect { value ->
        val currentTime = Clock.System.now().toEpochMilliseconds()
        if (currentTime - lastEmitTime >= period.inWholeMilliseconds) {
            lastEmitTime = currentTime
            emit(value)
        }
    }
}

// Usage
@Composable
fun UserCard(user: User) {
    if (user.isActive()) {
        Text(user.displayName())
        Text(user.lastActiveAt.toRelativeTime())
    }
}
```

**Rules:**
- Keep extensions in the same module as the type, or in `core:common`.
- Use extension functions instead of `*Utils` classes.
- Name them so the call reads naturally: `user.displayName()`, never `UserUtils.getDisplayName(user)`.

See: `references/design-patterns.md` → "Kotlin-Specific Patterns" → "Extension Functions for Domain Logic".

## Inline Value Classes

Use inline value classes for type-safe wrappers with zero runtime overhead.

```kotlin
// CORRECT: Type-safe IDs
@JvmInline
value class UserId(val value: String)

@JvmInline
value class AuthToken(val value: String)

@JvmInline
value class Email(val value: String)

// CORRECT: Prevents mixing different ID types
interface UserRepository {
    suspend fun getUser(id: UserId): Result<User> // Can't pass Email by mistake
}

interface AuthRepository {
    suspend fun validateToken(token: AuthToken): Result<Boolean>
}

// Usage
val userId = UserId("123")
val email = Email("user@example.com")

userRepository.getUser(userId) // CORRECT: compiles — `UserId` matches repository API
userRepository.getUser(email) // WRONG: Compile error - type safety!

// CORRECT: Type-safe domain values
@JvmInline
value class Temperature(val celsius: Double) {
    fun toFahrenheit(): Double = celsius * 9.0 / 5.0 + 32.0
}

@JvmInline
value class Distance(val meters: Double) {
    fun toKilometers(): Double = meters / 1000.0
}

fun displayTemperature(temp: Temperature): String =
    "${temp.celsius}°C (${temp.toFahrenheit()}°F)"

displayTemperature(Temperature(25.0))
```

**Use when:**
- Wrapping primitive types for type safety (IDs, tokens, measurements)
- Domain-specific types that need compile-time enforcement
- No runtime overhead (inlined at compile time)

**Limitations:**
- Can only wrap a single property
- Some reflection limitations
- Must be public (can't be private)

## Sequences for Lazy Evaluation

Use `Sequence` for large collections or chained operations to avoid intermediate allocations.

### Avoid Memory Churn

Allocating short-lived objects inside hot loops triggers GC pauses and causes jank. Reuse buffers, or hoist the allocation out of the loop.

```kotlin
// WRONG: Allocates a new String per iteration (10,001 objects)
for (i in 0..10000) {
    val text = "Item number: $i"
    processText(text)
}

// CORRECT: Reuse StringBuilder
val builder = StringBuilder()
for (i in 0..10000) {
    builder.clear()
    builder.append("Item number: ").append(i)
    processText(builder.toString())
}

// WRONG: Creates new object each time
fun getCurrentDate(): Date {
    return Date() // Called 1000 times = 1000 objects
}

// CORRECT: Reuse if possible
private var cachedDate: Date? = null
fun getCurrentDate(): Date {
    return cachedDate ?: Date().also { cachedDate = it }
}
```

```kotlin
// WRONG: Eager evaluation - creates intermediate lists
val activeUserNames = users
    .filter { it.isActive() }       // Creates List
    .map { it.name }                // Creates another List
    .sortedBy { it.lowercase() }    // Creates another List
    .take(10)                       // Creates another List

// CORRECT: Lazy evaluation - single pass
val activeUserNames = users
    .asSequence()
    .filter { it.isActive() }
    .map { it.name }
    .sortedBy { it.lowercase() }
    .take(10)
    .toList() // Materialize only at the end

// CORRECT: Generate sequences lazily
fun generateUserIds(): Sequence<UserId> = sequence {
    var counter = 0
    while (true) {
        yield(UserId("user_${counter++}"))
    }
}

val first100Ids = generateUserIds().take(100).toList()

// CORRECT: File processing (avoid loading everything into memory)
fun processLargeFile(file: File): List<String> =
    file.useLines { lines ->
        lines
            .filter { it.isNotBlank() }
            .map { it.trim() }
            .filter { it.startsWith("ERROR") }
            .take(100)
            .toList()
    }
```

**Use when:**
- Large collections (1000+ items)
- Multiple chained operations
- Potentially infinite streams
- File/database cursor iteration

**When NOT to Use:**
- Small collections (<100 items)
- Single operation
- Need random access or size

## Companion Objects

### Constants and Factory Methods

```kotlin
// CORRECT: Constants in companion object
class AuthConfig {
    companion object {
        val SESSION_TIMEOUT = 30.minutes
        const val MAX_LOGIN_ATTEMPTS = 3
        val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
    }
}

// CORRECT: Factory methods
@Immutable
data class User private constructor(
    val id: String,
    val email: String,
    val name: String
) {
    companion object {
        fun create(email: String, name: String): Result<User> {
            if (!email.matches(EMAIL_REGEX)) {
                return Result.failure(ValidationError.InvalidEmail)
            }
            if (name.isBlank()) {
                return Result.failure(ValidationError.InvalidName)
            }
            return Result.success(User(
                id = UUID.randomUUID().toString(),
                email = email.lowercase(),
                name = name.trim()
            ))
        }
        
        private val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
    }
}

// Usage
val user = User.create("test@example.com", "Test User").getOrThrow()
```

**Top-Level vs Companion Object:**

```kotlin
// CORRECT: Top-level for pure utility functions
fun formatDuration(duration: Duration): String =
    "${duration.inWholeSeconds} seconds"

// CORRECT: Companion object for type-related constants/factories
class Session {
    companion object {
        val DEFAULT_TIMEOUT = 30.seconds
        fun create(userId: String): Session = Session(userId, Clock.System.now().toEpochMilliseconds())
    }
}
```

## Type Aliases

Use type aliases for readability and to simplify complex generic types.

```kotlin
// CORRECT: Simplify complex types
typealias UserId = String
typealias AuthCallback = (Result<AuthToken>) -> Unit
typealias ValidationRules = Map<String, (String) -> Boolean>

// CORRECT: Generic callback types
typealias Callback<T> = (Result<T>) -> Unit
typealias Listener<T> = (T) -> Unit

// Usage in function signatures
class AuthService {
    fun login(
        email: String,
        password: String,
        callback: AuthCallback
    ) {
        // ...
    }
}

// CORRECT: Flow types
typealias AuthStateFlow = StateFlow<AuthState>
typealias UserListFlow = Flow<List<User>>

class AuthViewModel {
    val authState: AuthStateFlow = _authState.asStateFlow()
}

// WRONG: Don't use for single-use types
typealias S = String // Too generic
typealias UEVM = UserEditViewModel // Unreadable abbreviation

// WRONG: Don't hide important type information
typealias IntList = List<Int> // Doesn't add value; use List<Int> directly
```

**Use when:**
- Complex generic types (`Map<String, List<Result<User>>>`)
- Commonly used callback signatures
- Domain-specific terminology (`UserId` vs raw `String`)

**When NOT to Use:**
- Simple types that don't benefit from aliasing
- When it obscures important type information

## Destructuring

Destructure data classes and Pairs for cleaner code:

```kotlin
// CORRECT: Data class destructuring
data class User(val id: String, val name: String, val email: String)

val user = User("1", "John", "john@example.com")
val (id, name, email) = user

// CORRECT: Useful in loops
val users = listOf(user1, user2, user3)
for ((id, name, _) in users) { // _ ignores email
    println("$id: $name")
}

// CORRECT: Map entries
val userMap = mapOf("1" to user1, "2" to user2)
for ((userId, user) in userMap) {
    println("User $userId: ${user.name}")
}

// CORRECT: Pairs from functions
fun getMinMax(numbers: List<Int>): Pair<Int, Int> =
    numbers.min() to numbers.max()

val (min, max) = getMinMax(listOf(1, 5, 3, 9, 2))

// CORRECT: Limited destructuring (only first N components)
data class SearchResult(val id: String, val title: String, val description: String, val score: Float)

val (id, title) = searchResult // Only destructure first 2
```

**Limitations:**
- Only first 5 components supported by default
- Position-based, not name-based
- Can reduce readability if overused

## Inline Functions & Reified Types

### Inline Functions

Use `inline` for higher-order functions to eliminate lambda overhead:

```kotlin
// CORRECT: Inline higher-order function
inline fun <T> measureTime(block: () -> T): Pair<T, Duration> {
    val start = Clock.System.now()
    val result = block()
    val elapsed = Clock.System.now() - start
    return result to elapsed
}

// Usage (no lambda allocation)
val (user, elapsed) = measureTime {
    repository.getUser()
}
println("Took ${elapsed.inWholeMilliseconds}ms")

// CORRECT: Inline for DSL builders
inline fun buildUser(init: UserBuilder.() -> Unit): User {
    val builder = UserBuilder()
    builder.init()
    return builder.build()
}

val user = buildUser {
    name = "John"
    email = "john@example.com"
    age = 30
}
```

### Reified Type Parameters

Retain type information at runtime with `reified`:

```kotlin
// CORRECT: Generic Activity start
inline fun <reified T : Activity> Context.startActivity() {
    startActivity(Intent(this, T::class.java))
}

// Usage
context.startActivity<MainActivity>() // Type-safe!

// CORRECT: Generic ViewModel retrieval with Hilt
@Composable
inline fun <reified T : ViewModel> hiltViewModel(): T {
    return androidx.hilt.navigation.compose.hiltViewModel()
}

// CORRECT: Type-safe navigation arguments
inline fun <reified T> SavedStateHandle.getOrThrow(key: String): T =
    get<T>(key) ?: error("Missing required argument: $key")

@HiltViewModel
class ProfileViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val userId: UserId = savedStateHandle.getOrThrow("userId")
}

// CORRECT: Generic JSON serialization
inline fun <reified T> Json.decodeFromString(string: String): T {
    return decodeFromString(serializer<T>(), string)
}

inline fun <reified T> Json.encodeToString(value: T): String {
    return encodeToString(serializer<T>(), value)
}
```

**Rules:**
- Must be `inline` to use `reified`
- Don't overuse; adds code size at call sites
- Best for: DSLs, type-safe wrappers, reflection avoidance

### `noinline` and `crossinline`

When a function is `inline`, all its lambda parameters are inlined by default. Use `noinline` and `crossinline` to change that behavior for specific lambdas.

#### `inline` (default) - Inlined at Call Site

All lambda parameters are inlined. Non-local `return` is allowed.

```kotlin
// Timing wrapper for repository calls - zero lambda overhead
inline fun <T> Repository.timed(tag: String, block: () -> T): T {
    val start = SystemClock.elapsedRealtime()
    val result = block()
    Log.d("Perf", "$tag took ${SystemClock.elapsedRealtime() - start}ms")
    return result
}

// Usage - block is inlined, no lambda object created
val user = userRepository.timed("fetchUser") {
    remoteDataSource.getUser(userId)
}

// Compose: inline builder for modifier chains
inline fun Modifier.conditionalPadding(
    condition: Boolean,
    block: Modifier.() -> Modifier
): Modifier = if (condition) block() else this
```

#### `noinline` - Opt a Lambda Out of Inlining

Use when the lambda must be stored, passed to another function, or returned. Inlined lambdas can't be treated as objects.

```kotlin
// Error handler must be stored in the WorkManager retry callback
inline fun <T> safeApiCall(
    crossinline call: suspend () -> T,
    noinline onError: (Throwable) -> Unit // stored in retry callback
): Flow<Result<T>> = flow {
    try {
        emit(Result.success(call()))
    } catch (e: Exception) {
        emit(Result.failure(e))
        RetryScheduler.schedule(onError) // passing lambda as object
    }
}

// Click listener stored in View - must be noinline
inline fun View.onDebouncedClick(
    debounceMs: Long = 300L,
    noinline action: (View) -> Unit // stored by setOnClickListener
) {
    var lastClickTime = 0L
    setOnClickListener { view ->
        val now = SystemClock.elapsedRealtime()
        if (now - lastClickTime >= debounceMs) {
            lastClickTime = now
            action(view)
        }
    }
}
```

#### `crossinline` - Forbid Non-Local Returns

Use when the lambda executes in a different context (another coroutine, thread, or lambda). Prevents the caller from using `return` to exit the outer function.

```kotlin
// Lambda runs inside launch {} - different coroutine context
inline fun ViewModel.launchWithLoading(
    state: MutableStateFlow<Boolean>,
    crossinline block: suspend () -> Unit
) {
    viewModelScope.launch {
        state.value = true
        try {
            block()
        } finally {
            state.value = false
        }
    }
}

// Usage
fun loadProfile() {
    launchWithLoading(_isLoading) {
        // return here would try to exit loadProfile() without crossinline
        val user = repository.getUser(userId)
        _profile.value = user
    }
}

// Lambda runs in Dispatchers.IO context
inline fun <T> runOnIo(crossinline block: () -> T, crossinline onResult: (T) -> Unit) {
    CoroutineScope(Dispatchers.IO).launch {
        val result = block()
        withContext(Dispatchers.Main) {
            onResult(result)
        }
    }
}
```

#### Decision Rules

| Modifier | Use when | Effect |
|----------|-------------|--------|
| (default) | Lambda used directly at call site | Inlined, non-local `return` allowed |
| `noinline` | Lambda stored, passed to another function, or returned | Not inlined, creates object |
| `crossinline` | Lambda runs in different execution context (launch, withContext) | Inlined, but non-local `return` forbidden |

## Named Arguments

Use named arguments for clarity, especially with multiple parameters of the same type:

```kotlin
// WRONG: Hard to read
authRepository.login("user@example.com", "password123")

// CORRECT: Clear and explicit
authRepository.login(
    email = "user@example.com",
    password = "password123"
)

// CORRECT: Essential for boolean parameters
Button(
    onClick = { },
    enabled = true,
    modifier = Modifier.fillMaxWidth()
)

// CORRECT: When parameters have default values
fun createUser(
    name: String,
    email: String,
    age: Int = 18,
    isVerified: Boolean = false,
    profileUrl: String? = null
) { }

createUser(
    name = "John",
    email = "john@example.com",
    isVerified = true // Skip age, profileUrl
)
```

**Use when:**
- Multiple parameters of same type
- Boolean parameters
- Parameters with defaults
- Builder-like function calls

## Android View Lifecycle (Interop)

Custom `View` subclasses (Compose `AndroidView`, legacy widgets, Canvas) sometimes register **lifecycle** observers or process listeners. **Add and remove in pairs** so you do not leak the activity or keep callbacks after the view is gone.

```kotlin
class MyView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs), DefaultLifecycleObserver {

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        findViewTreeLifecycleOwner()?.lifecycle?.addObserver(this)
    }

    override fun onDetachedFromWindow() {
        findViewTreeLifecycleOwner()?.lifecycle?.removeObserver(this)
        super.onDetachedFromWindow()
    }

    override fun onDestroy(owner: LifecycleOwner) {
        // Stop sensors, cancel work tied to this view
    }
}
```

Use `findViewTreeLifecycleOwner()` when the view lives under a `Fragment` or Compose host. For pure composables, use lifecycle-aware APIs from `references/compose-patterns.md` (`LifecycleResumeEffect`, `DisposableEffect`, etc.) instead of manual `View` hooks.

## Coroutines routing

### Structured Concurrency

Always use scoped coroutines; never `GlobalScope`.

```kotlin
// CORRECT: ViewModel scope
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    fun login(email: String, password: String) {
        viewModelScope.launch { // Canceled when ViewModel cleared
            authRepository.login(email, password)
        }
    }
}

// CORRECT: Custom scope for repositories
@Singleton
class AuthRepository @Inject constructor(
    @IoDispatcher private val dispatcher: CoroutineDispatcher
) {
    private val scope = CoroutineScope(dispatcher + SupervisorJob())
    
    fun cleanup() {
        scope.cancel()
    }
}
```

### Generic Suspending Functions

Use generics in suspend functions for reusable async patterns:

```kotlin
// CORRECT: Generic retry logic
suspend fun <T> retryWithBackoff(
    maxAttempts: Int = 3,
    initialDelay: Duration = 1.seconds,
    maxDelay: Duration = 10.seconds,
    factor: Double = 2.0,
    block: suspend () -> T
): Result<T> {
    var currentDelay = initialDelay
    var lastException: Exception? = null
    
    repeat(maxAttempts) { attempt ->
        try {
            return Result.success(block())
        } catch (e: Exception) {
            lastException = e
            if (attempt < maxAttempts - 1) {
                delay(currentDelay)
                currentDelay = (currentDelay * factor).coerceAtMost(maxDelay)
            }
        }
    }
    
    return Result.failure(lastException ?: Exception("Unknown error"))
}

// Usage
suspend fun login(email: String, password: String): Result<AuthToken> =
    retryWithBackoff {
        authApi.login(email, password)
    }

// CORRECT: Generic resource management
suspend fun <T> withTimeoutResult(
    timeout: Duration,
    block: suspend () -> T
): Result<T> = runCatching {
    withTimeout(timeout) {
        block()
    }
}
```

**Full coroutine patterns**: See `references/coroutines-patterns.md` for dispatchers, structured concurrency, cancellation, Flow patterns, testing, and more.

## Rules Summary

Required:
- Delegation over inheritance: use `by` for composition.
- Expose read-only collections; keep mutation private.
- Model UI/state with sealed classes for exhaustive `when`.
- Use `Result<T>`, generic repositories, and generic wrappers - never raw `Result`.
- Use `inline fun <reified T>` for type-safe runtime ops.
- Add behavior via extension functions, never `*Utils` objects.
- Wrap primitives in `@JvmInline value class` for IDs, tokens, and units.
- Use `Sequence` for chained transformations on large collections.
- Pass named arguments when a call has 3+ parameters or any boolean.
- For custom `View` code, pair `addObserver` with `removeObserver` (see [Android View Lifecycle (Interop)](#android-view-lifecycle-interop)).

Forbidden:
- `GlobalScope.launch` and `runBlocking` outside `main()` and tests.

For detailed patterns, see:
- **Delegation**: `references/kotlin-delegation.md`
- **Coroutines**: `references/coroutines-patterns.md`
- **Design Patterns**: `references/design-patterns.md`
- **Architecture**: `references/architecture.md`
