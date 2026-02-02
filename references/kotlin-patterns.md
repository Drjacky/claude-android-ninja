# Kotlin Patterns & Best Practices

Concise Kotlin guidance for Android projects. Each item includes a short example so it is easy
to apply. If a topic is large, it lives in a dedicated reference and is linked here.

This guide focuses on intermediate and advanced Kotlin patterns. Basic language features (data classes, null safety, scope functions like `let`/`apply`/`run`) are assumed knowledge.

**Note**: All time-related examples use Kotlin Duration API (`kotlin.time.Duration`) and `kotlinx.datetime.Clock` for type-safe, readable time operations.

## Table of Contents
1. [Delegation (Composition over Inheritance)](#delegation-composition-over-inheritance)
2. [Collection APIs](#collection-apis)
3. [Sealed Classes & Exhaustive When](#sealed-classes--exhaustive-when)
4. [Generics & Reified Types](#generics--reified-types)
5. [Extension Functions](#extension-functions)
6. [Inline Value Classes](#inline-value-classes)
7. [Sequences for Lazy Evaluation](#sequences-for-lazy-evaluation)
8. [Companion Objects](#companion-objects)
9. [Type Aliases](#type-aliases)
10. [Coroutines Best Practices](#coroutines-best-practices)

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

See: `references/kotlin-delegation.md` for complete patterns, testing, and best practices.

## Collection APIs

### Prefer Read-Only Collection APIs

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
// ✅ Generic Result type
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

**Note**: Kotlin stdlib has `Result<T>`, but you can create custom result types for domain-specific error handling.

### Reified Type Parameters

Use `reified` with `inline` functions for runtime type information:

```kotlin
// ✅ Type-safe JSON parsing with reified
inline fun <reified T> parseJson(json: String): T {
    return Json.decodeFromString<T>(json)
}

// Usage (no need to pass class reference)
val user: User = parseJson(jsonString)
val token: AuthToken = parseJson(tokenJson)

// ✅ Type-safe navigation argument retrieval
inline fun <reified T> SavedStateHandle.getOrNull(key: String): T? =
    get<T>(key)

// ✅ Type-safe Retrofit service creation wrapper
inline fun <reified T> Retrofit.create(): T {
    return create(T::class.java)
}

// ✅ Room DAO with reified type
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

**Best Practices:**
- Keep extensions in the same module as the type or in `core:common`
- Prefer extension functions over utility classes
- Use descriptive names that read naturally: `user.displayName()` not `UserUtils.getDisplayName(user)`

See: `references/design-patterns.md` → "Kotlin-Specific Patterns" → "Extension Functions for Domain Logic".

## Inline Value Classes

Use inline value classes for type-safe wrappers with zero runtime overhead.

```kotlin
// ✅ Type-safe IDs
@JvmInline
value class UserId(val value: String)

@JvmInline
value class AuthToken(val value: String)

@JvmInline
value class Email(val value: String)

// ✅ Prevents mixing different ID types
interface UserRepository {
    suspend fun getUser(id: UserId): Result<User> // Can't pass Email by mistake
}

interface AuthRepository {
    suspend fun validateToken(token: AuthToken): Result<Boolean>
}

// Usage
val userId = UserId("123")
val email = Email("user@example.com")

userRepository.getUser(userId) // ✅ Correct
userRepository.getUser(email) // ❌ Compile error - type safety!

// ✅ Type-safe domain values
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

**When to Use:**
- Wrapping primitive types for type safety (IDs, tokens, measurements)
- Domain-specific types that need compile-time enforcement
- No runtime overhead (inlined at compile time)

**Limitations:**
- Can only wrap a single property
- Some reflection limitations
- Must be public (can't be private)

## Sequences for Lazy Evaluation

Use `Sequence` for large collections or chained operations to avoid intermediate allocations.

```kotlin
// ❌ Eager evaluation - creates intermediate lists
val activeUserNames = users
    .filter { it.isActive() }       // Creates List
    .map { it.name }                // Creates another List
    .sortedBy { it.lowercase() }    // Creates another List
    .take(10)                       // Creates another List

// ✅ Lazy evaluation - single pass
val activeUserNames = users
    .asSequence()
    .filter { it.isActive() }
    .map { it.name }
    .sortedBy { it.lowercase() }
    .take(10)
    .toList() // Materialize only at the end

// ✅ Generate sequences lazily
fun generateUserIds(): Sequence<UserId> = sequence {
    var counter = 0
    while (true) {
        yield(UserId("user_${counter++}"))
    }
}

val first100Ids = generateUserIds().take(100).toList()

// ✅ File processing (avoid loading everything into memory)
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

**When to Use:**
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
// ✅ Constants in companion object
class AuthConfig {
    companion object {
        val SESSION_TIMEOUT = 30.minutes
        const val MAX_LOGIN_ATTEMPTS = 3
        val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
    }
}

// ✅ Factory methods
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
// ✅ Top-level for pure utility functions
fun formatDuration(duration: Duration): String =
    "${duration.inWholeSeconds} seconds"

// ✅ Companion object for type-related constants/factories
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
// ✅ Simplify complex types
typealias UserId = String
typealias AuthCallback = (Result<AuthToken>) -> Unit
typealias ValidationRules = Map<String, (String) -> Boolean>

// ✅ Generic callback types
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

// ✅ Flow types
typealias AuthStateFlow = StateFlow<AuthState>
typealias UserListFlow = Flow<List<User>>

class AuthViewModel {
    val authState: AuthStateFlow = _authState.asStateFlow()
}

// ❌ Don't use for single-use types
typealias S = String // Too generic
typealias UEVM = UserEditViewModel // Unreadable abbreviation

// ❌ Don't hide important type information
typealias IntList = List<Int> // Doesn't add value; use List<Int> directly
```

**When to Use:**
- Complex generic types (`Map<String, List<Result<User>>>`)
- Commonly used callback signatures
- Domain-specific terminology (`UserId` vs raw `String`)

**When NOT to Use:**
- Simple types that don't benefit from aliasing
- When it obscures important type information

## Destructuring

Destructure data classes and Pairs for cleaner code:

```kotlin
// ✅ Data class destructuring
data class User(val id: String, val name: String, val email: String)

val user = User("1", "John", "john@example.com")
val (id, name, email) = user

// ✅ Useful in loops
val users = listOf(user1, user2, user3)
for ((id, name, _) in users) { // _ ignores email
    println("$id: $name")
}

// ✅ Map entries
val userMap = mapOf("1" to user1, "2" to user2)
for ((userId, user) in userMap) {
    println("User $userId: ${user.name}")
}

// ✅ Pairs from functions
fun getMinMax(numbers: List<Int>): Pair<Int, Int> =
    numbers.min() to numbers.max()

val (min, max) = getMinMax(listOf(1, 5, 3, 9, 2))

// ✅ Limited destructuring (only first N components)
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
// ✅ Inline higher-order function
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

// ✅ Inline for DSL builders
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
// ✅ Generic Activity start
inline fun <reified T : Activity> Context.startActivity() {
    startActivity(Intent(this, T::class.java))
}

// Usage
context.startActivity<MainActivity>() // Type-safe!

// ✅ Generic ViewModel retrieval with Hilt
@Composable
inline fun <reified T : ViewModel> hiltViewModel(): T {
    return androidx.hilt.navigation.compose.hiltViewModel()
}

// ✅ Type-safe navigation arguments
inline fun <reified T> SavedStateHandle.getOrThrow(key: String): T =
    get<T>(key) ?: error("Missing required argument: $key")

@HiltViewModel
class ProfileViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val userId: UserId = savedStateHandle.getOrThrow("userId")
}

// ✅ Generic JSON serialization
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

## Named Arguments

Use named arguments for clarity, especially with multiple parameters of the same type:

```kotlin
// ❌ Hard to read
authRepository.login("user@example.com", "password123")

// ✅ Clear and explicit
authRepository.login(
    email = "user@example.com",
    password = "password123"
)

// ✅ Essential for boolean parameters
Button(
    onClick = { },
    enabled = true,
    modifier = Modifier.fillMaxWidth()
)

// ✅ When parameters have default values
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

**When to Use:**
- Multiple parameters of same type
- Boolean parameters
- Parameters with defaults
- Builder-like function calls

## Coroutines Best Practices

### Structured Concurrency

Always use scoped coroutines; never `GlobalScope`.

```kotlin
// ✅ ViewModel scope
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

// ✅ Custom scope for repositories
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
// ✅ Generic retry logic
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

// ✅ Generic resource management
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

## Best Practices Summary

1. **Delegation over inheritance**: Use `by` for composition
2. **Read-only collections**: Expose immutable APIs, keep mutation private
3. **Sealed classes**: For exhaustive state modeling
4. **Generics**: Use `Result<T>` not raw `Result`; generic repositories and wrappers
5. **Reified types**: For type-safe runtime operations with `inline`
6. **Extension functions**: For domain logic on existing types
7. **Inline value classes**: For zero-cost type-safe wrappers
8. **Sequences**: For large collections with multiple transformations
9. **Named arguments**: For clarity with multiple parameters
10. **Avoid `GlobalScope`**: Always use scoped coroutines

For detailed patterns, see:
- **Delegation**: `references/kotlin-delegation.md`
- **Coroutines**: `references/coroutines-patterns.md`
- **Design Patterns**: `references/design-patterns.md`
- **Architecture**: `references/architecture.md`
