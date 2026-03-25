# Architecture Guide

Based on Google's official Android architecture guidance with modern Jetpack Compose, Navigation3, and our modular best practices.
All Kotlin code in this architecture must align with `references/kotlin-patterns.md`.

**Data Synchronization:** For offline-first patterns, sync strategies, and conflict resolution, see `references/android-data-sync.md`.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Architecture Principles](#architecture-principles)
3. [Cross-cutting anti-patterns (quick reference)](#cross-cutting-anti-patterns-quick-reference)
4. [Data Layer](#data-layer)
5. [Domain Layer](#domain-layer)
6. [Presentation Layer](#presentation-layer)
7. [UI Layer](#ui-layer)
8. [Navigation](#navigation)
9. [Complete Architecture Flow](#complete-architecture-flow)

## Architecture Overview

Four-layer architecture with strict module separation and unidirectional data flow:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      FEATURE MODULES (feature/*)                        │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              Presentation Layer                                 │   │
│   │  ┌──────────────┐    ┌──────────────────────────┐               │   │
│   │  │   Screen     │◄───│      ViewModel           │               │   │
│   │  │  (Compose)   │    │  (StateFlow<UiState>)    │               │   │
│   │  └──────────────┘    └────────────┬─────────────┘               │   │
│   │                                   │                             │   │
│   └───────────────────────────────────┼─────────────────────────────┘   │
│                                       │ Uses                            │
├───────────────────────────────────────┼─────────────────────────────────┤
│              CORE/DOMAIN Module       │                                 │
│   ┌───────────────────────────────────▼──────────────────────┐          │
│   │                    Domain Layer                          │          │
│   │  ┌────────────────────────────────────────────────────┐  │          │
│   │  │                Use Cases                           │  │          │
│   │  │           (combine/transform logic)                │  │          │
│   │  └───────────────────────┬────────────────────────────┘  │          │
│   │  ┌───────────────────────▼────────────────────────────┐  │          │
│   │  │             Repository Interfaces                  │  │          │
│   │  │           (contracts for data layer)               │  │          │
│   │  └───────────────────────┬────────────────────────────┘  │          │
│   │  ┌───────────────────────▼────────────────────────────┐  │          │
│   │  │                Domain Models                       │  │          │
│   │  │           (business entities)                      │  │          │
│   │  └────────────────────────────────────────────────────┘  │          │
│   └────────────────────────────────────┬─────────────────────┘          │
│                                        │ Implements                     │
├────────────────────────────────────────┼────────────────────────────────┤
│                CORE/DATA Module        │                                │
│   ┌────────────────────────────────────▼──────────────────────┐         │
│   │                    Data Layer                             │         │
│   │  ┌────────────────────────────────────────────────────┐   │         │
│   │  │              Repository Implementations            │   │         │
│   │  │    (offline-first, single source of truth)         │   │         │
│   │  └─────────┬─────────────────────┬────────────────────┘   │         │
│   │            │                     │                        │         │
│   │  ┌─────────▼─────────┐  ┌────────▼──────────────┐         │         │
│   │  │  Local DataSource │  │  Remote DataSource    │         │         │
│   │  │   (Room 3 + DAO)  │  │     (Retrofit)        │         │         │
│   │  └─────────┬─────────┘  └───────────────────────┘         │         │
│   │            │                                              │         │
│   │  ┌─────────▼──────────────────────────────────────┐       │         │
│   │  │              Data Models                       │       │         │
│   │  │      (Entity, DTO, Response objects)           │       │         │
│   │  └────────────────────────────────────────────────┘       │         │
│   └───────────────────────────────────────────────────────────┘         │
├─────────────────────────────────────────────────────────────────────────┤
│                 CORE/UI Module (shared UI resources)                    │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    UI Layer                                     │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │        Shared UI Components                             │    │   │
│   │  │   (Buttons, Cards, Dialogs, etc.)                       │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │           Themes & Design System                        │    │   │
│   │  │   (Colors, Typography, Shapes)                          │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   │  ┌─────────────────────────────────────────────────────────┐    │   │
│   │  │         Base ViewModels / State Management              │    │   │
│   │  │   (BaseViewModel, UiState, etc.)                        │    │   │
│   │  └─────────────────────────────────────────────────────────┘    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Architecture Principles

1. **Offline-first**: Local database is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use Kotlin Flow/StateFlow for all data exposure
4. **Modular by feature**: Each feature is self-contained with clear boundaries
5. **Testable by design**: Use interfaces and fakes for testing; MockK only for framework classes in app module (see `references/testing.md`)
6. **Layer separation**: Strict separation between Presentation, Domain, Data, and UI layers
7. **Dependency direction**: Features depend on Core modules, not on other features
8. **Navigation coordination**: App module coordinates navigation between features
9. **Pattern fit**: Choose patterns that match Android constraints and the module boundaries (see `references/design-patterns.md`)

## Cross-cutting anti-patterns (quick reference)

Domain-specific pitfalls (navigation, Room 3, Paging, etc.) live in their topic references. This table is a **layering and state-shape** checklist. Deeper guidance on recomposition and stability: `references/android-performance.md` and `references/compose-patterns.md`.

| Anti-pattern                                                                       | Why it hurts                                                             | Prefer instead                                                                                                      |
|------------------------------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| Business logic in composables                                                      | Competing sources of truth, hard to test, work reruns during composition | ViewModel / domain services / repositories; composables map state → UI                                              |
| Oversized "god" ViewModel                                                          | Hard to own and change safely                                            | One ViewModel per screen or one coherent flow                                                                       |
| Unstable `UiState` (mutable collections, non-stable lambdas in state)              | Weakens Compose skipping, extra recompositions                           | Immutable `data class` / persistent collections; stable types                                                       |
| Duplicated derived fields (`total`, `formattedTotal`, `hasTotal` all stored)       | Fields drift out of sync                                                 | One canonical value; derive the rest (computed properties or at the UI edge)                                        |
| Parent reads too much `StateFlow` / state                                          | Recomposition fans out to the whole subtree                              | Pass only the slices each child needs                                                                               |
| One-shot UI as sticky state (`showSnackbarOnce = true`)                            | Can replay after config change or rotation                               | One-shot events: `SharedFlow` (or channel-backed flow) collected in the Route; see `references/compose-patterns.md` |
| `StateFlow` updates when nothing changed                                           | Wasted recompositions                                                    | Compare before `update` / avoid redundant `copy`                                                                    |
| ViewModel performs platform work (navigation, share sheet, analytics side effects) | Couples logic to Android, harder to test                                 | Emit one-shot events or callbacks; handle in Route / Activity edge                                                  |
| Display strings fully formatted in ViewModel                                       | Locale/layout rigidity, duplicated presentation                          | Keep canonical values; format with resources at the Compose boundary (`references/android-i18n.md`)                 |
| Lazy list keys missing or index-based                                              | Wrong item state after reorder/delete                                    | Stable domain id as key (`references/compose-patterns.md`)                                                          |
| Many trivial composables (thin wrappers around one `Text` / `Spacer`)              | Noise, weak boundaries                                                   | Extract only meaningful, reused UI blocks                                                                           |
| Fully qualified package names inline                                               | Hard to read                                                             | Top-level imports; `import … as …` when names clash (`references/kotlin-patterns.md`)                               |

## Module Structure

See the full module layout and naming conventions in `references/modularization.md`.

## Data Layer

### Principles
- **Offline-first**: Local database is the source of truth
- **Repository pattern**: Single public API for data access
- **Reactive streams**: All data exposed as `Flow<T>` or `StateFlow<T>`
- **Model mapping**: Separate Entity (database), DTO (network), and Domain models

### Repository Pattern

The repository interface is defined in `core/domain` (see [Repository Interface Pattern](#repository-interface-pattern) in Domain Layer section).

```kotlin
// core/data - Repository implementation
internal class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource,
    private val remoteDataSource: AuthRemoteDataSource,
    private val authMapper: AuthMapper,
    private val crashReporter: CrashReporter
) : AuthRepository {

    override suspend fun login(email: String, password: String): Result<AuthToken> =
        try {
            val response = remoteDataSource.login(email, password)
            localDataSource.saveAuthToken(response.token)
            localDataSource.saveUser(authMapper.toEntity(response.user))
            Result.success(response.token)
        } catch (e: IOException) {
            crashReporter.recordException(e, mapOf("action" to "login"))
            Result.failure(AuthError.NetworkError("No internet connection", e))
        } catch (e: HttpException) {
            when (e.code()) {
                401 -> Result.failure(AuthError.InvalidCredentials("Invalid email or password"))
                else -> {
                    crashReporter.recordException(e, mapOf("action" to "login", "code" to e.code()))
                    Result.failure(AuthError.ServerError("Server error", e))
                }
            }
        } catch (e: Exception) {
            crashReporter.recordException(e, mapOf("action" to "login"))
            Result.failure(AuthError.UnknownError("Unexpected error", e))
        }

    override suspend fun register(user: User): Result<Unit> =
        try {
            remoteDataSource.register(authMapper.toNetwork(user))
            Result.success(Unit)
        } catch (e: IOException) {
            crashReporter.recordException(e, mapOf("action" to "register"))
            Result.failure(AuthError.NetworkError("No internet connection", e))
        } catch (e: HttpException) {
            when (e.code()) {
                409 -> Result.failure(AuthError.UserAlreadyExists("Email already registered"))
                else -> {
                    crashReporter.recordException(e, mapOf("action" to "register", "code" to e.code()))
                    Result.failure(AuthError.ServerError("Server error", e))
                }
            }
        } catch (e: Exception) {
            crashReporter.recordException(e, mapOf("action" to "register"))
            Result.failure(AuthError.UnknownError("Unexpected error", e))
        }

    override suspend fun resetPassword(email: String): Result<Unit> =
        remoteDataSource.resetPassword(email)

    override fun observeAuthState(): Flow<AuthState> =
        localDataSource.observeAuthToken()
            .map { token ->
                if (token != null) {
                    val user = authMapper.toDomain(localDataSource.getUser())
                    AuthState.Authenticated(user)
                } else {
                    AuthState.Unauthenticated
                }
            }

    override fun observeAuthEvents(): Flow<AuthEvent> =
        localDataSource.observeAuthEvents()

    override suspend fun refreshSession(): Result<Unit> =
        remoteDataSource.refreshSession()
}
```

### Data Sources

| Type        | Module         | Implementation  | Purpose                             |
|-------------|----------------|-----------------|-------------------------------------|
| Local       | core/database  | Room 3 DAO      | Persistent storage, source of truth |
| Remote      | core/network   | Retrofit API    | Network data fetching               |
| Preferences | core/datastore | Proto DataStore | User settings, simple key-value     |

### DataStore (Preferences & Typed)

**When to use what:**
- **Room 3:** Relational data, SQL queries (`WHERE` / `JOIN`), indexes, unbounded or **large** collections (order-of **~100+ entries** is a common threshold), partial updates, referential integrity.
- **DataStore:** Small preference blobs: simple key-value pairs, typed settings objects, feature flags. Does **not** support partial updates, ad hoc queries, or relational integrity-use Room 3 when you need those.
- **Files:** Large media, blobs.
- **MultiProcessDataStoreFactory:** Only if accessing data across multiple processes-and then **every** reader/writer for that file must use the multi-process path (see Critical Rules).

**Critical Rules:**
1. **Never** create more than one instance of `DataStore` for a given file in the same process (it will throw `IllegalStateException`).
2. The generic type `T` in `DataStore<T>` **must be immutable**. Mutating it breaks consistency.
3. **Never mix access modes for the same file:** If any code path uses `MultiProcessDataStoreFactory`, **all** access to that file must use it. Do not combine it with single-process `PreferenceDataStoreFactory` or the `preferencesDataStore` delegate for the same backing store.

#### Preferences DataStore
Use for simple key-value pairs without type safety.

```kotlin
// Define keys
object PrefsKeys {
    val THEME_MODE = intPreferencesKey("theme_mode")
    val HAS_SEEN_ONBOARDING = booleanPreferencesKey("has_seen_onboarding")
}

// Read with error handling
fun getThemeMode(dataStore: DataStore<Preferences>): Flow<Int> = dataStore.data
    .catch { exception ->
        if (exception is IOException) emit(emptyPreferences()) else throw exception
    }
    .map { prefs -> prefs[PrefsKeys.THEME_MODE] ?: ThemeMode.SYSTEM }

// Write
suspend fun setThemeMode(dataStore: DataStore<Preferences>, mode: Int) {
    dataStore.edit { prefs ->
        prefs[PrefsKeys.THEME_MODE] = mode
    }
}
```

#### Typed DataStore (JSON / Proto)
Use for custom classes with type safety. Requires a `Serializer`.

```kotlin
@Serializable
data class UserSettings(
    val themeMode: Int = 0,
    val hasSeenOnboarding: Boolean = false
)

object UserSettingsSerializer : Serializer<UserSettings> {
    override val defaultValue: UserSettings = UserSettings()

    override suspend fun readFrom(input: InputStream): UserSettings = try {
        Json.decodeFromString(input.readBytes().decodeToString())
    } catch (e: SerializationException) {
        throw CorruptionException("Unable to read UserSettings", e)
    }

    override suspend fun writeTo(t: UserSettings, output: OutputStream) {
        output.write(Json.encodeToString(t).encodeToByteArray())
    }
}
```

#### SharedPreferences Migration
Easily migrate existing `SharedPreferences` to `DataStore` during creation:

```kotlin
val dataStore = PreferenceDataStoreFactory.create(
    migrations = listOf(SharedPreferencesMigration(context, "legacy_prefs")),
    produceFile = { context.preferencesDataStoreFile("settings") }
)
```

#### Hilt Setup

**Scope:** DataStore-only wiring below. For **Hilt module rules** (`@Binds` vs `@Provides`, scopes, anti-patterns, Navigation3 + `hiltViewModel`), see [Dependency Injection Setup](#dependency-injection-setup) under **Domain Layer**.

The `preferencesDataStore(name = ...)` property delegate on `Context` is fine for very small apps. Prefer an explicit `@Singleton` provider (below) when you want **test doubles** without tying tests to `Application` or static `Context`.

Always provide `DataStore` as a `@Singleton` to guarantee a single instance per file.

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DataStoreModule {
    
    @Provides
    @Singleton
    fun provideUserSettingsDataStore(
        @ApplicationContext context: Context
    ): DataStore<UserSettings> = DataStoreFactory.create(
        serializer = UserSettingsSerializer,
        produceFile = { context.dataStoreFile("user_settings.json") },
        corruptionHandler = ReplaceFileCorruptionHandler { UserSettings() }
    )
}
```

### Network Layer Setup (core/network)

#### Retrofit Service Interfaces

All endpoint functions must be `suspend`. Use `Response<T>` only when you need access to status
codes or error bodies; use the body type directly when 2xx is the only expected success case.

```kotlin
interface AuthApiService {

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): LoginResponse

    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<Unit>

    @GET("users/{id}")
    suspend fun getUser(@Path("id") userId: String): NetworkUser

    @GET("users/search")
    suspend fun searchUsers(
        @Query("q") query: String,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 20
    ): PaginatedResponse<NetworkUser>

    @Multipart
    @PUT("users/{id}/avatar")
    suspend fun uploadAvatar(
        @Path("id") userId: String,
        @Part avatar: MultipartBody.Part
    ): NetworkUser
}
```

#### Network DTOs and nullable JSON fields

Wire formats do not match your ideal domain model: fields can be **missing**, **null**, or **renamed** across API versions. Types used only for JSON (network DTOs) should reflect that.

- Prefer **nullable** properties for anything the server might omit or null out; map to non-null domain types in the repository or mapper after you decide defaults.
- Keep `Json { ignoreUnknownKeys = true }` (see `NetworkModule`) so new server fields do not crash deserialization.
- Avoid fake non-nulls such as `String = ""` for "missing" JSON keys unless you have a strict, documented contract. Empty string is ambiguous versus "present but empty".

```kotlin
@Serializable
data class NetworkUser(
    val id: String? = null,
    val displayName: String? = null,
    val avatarUrl: String? = null,
)
```

Use `@SerialName("json_name")` when wire names differ from Kotlin properties. Gson users apply the same idea with `@SerializedName`.

#### Hilt NetworkModule

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
        isLenient = true
    }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        authInterceptor: AuthInterceptor
    ): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(
            HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) {
                    HttpLoggingInterceptor.Level.BODY
                } else {
                    HttpLoggingInterceptor.Level.NONE
                }
            }
        )
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    @Provides
    @Singleton
    fun provideRetrofit(okHttpClient: OkHttpClient, json: Json): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()

    @Provides
    @Singleton
    fun provideAuthApiService(retrofit: Retrofit): AuthApiService =
        retrofit.create(AuthApiService::class.java)
}
```

#### Authentication Interceptor

Inject auth tokens via an `Interceptor` instead of adding `@Header` parameters to every endpoint:

```kotlin
class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenProvider.getToken()
            ?: return chain.proceed(chain.request())

        val request = chain.request().newBuilder()
            .header("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request)
    }
}
```

Network exceptions (`HttpException`, `IOException`) are caught and mapped to domain error types
in the repository layer - see [Repository Pattern](#repository-pattern) above and
[Domain-Specific Error Types](#domain-specific-error-types) below.

### Model Mapping Strategy

Use mappers when transformations add business logic, not for simple 1:1 field mappings.

```kotlin
// core/data/mapping/AuthMapper.kt
class AuthMapper @Inject constructor(
    private val dateFormatter: DateFormatter
) {
    
    // Entity → Domain (with date formatting)
    fun toDomain(entity: UserEntity?): User = User(
        id = entity?.id.orEmpty(),
        email = entity?.email.orEmpty(),
        name = entity?.name.orEmpty(),
        profileImage = entity?.profileImage,
        memberSince = entity?.createdAt?.let { dateFormatter.formatMemberSince(it) } ?: "Unknown",
        lastActive = entity?.lastActiveAt?.let { dateFormatter.formatRelativeTime(it) } ?: "Never"
    )
    
    // Network → Entity (with timestamp normalization)
    fun toEntity(user: NetworkUser): UserEntity = UserEntity(
        id = user.id,
        email = user.email.lowercase().trim(), // Normalize email
        name = user.name.trim(),
        profileImage = user.profileImage,
        createdAt = user.createdAt,
        lastActiveAt = Clock.System.now().toEpochMilliseconds() // Track local access time
    )
    
    // Domain → Network (for register/update)
    fun toNetwork(user: User): NetworkUser = NetworkUser(
        id = user.id,
        email = user.email,
        name = user.name,
        profileImage = user.profileImage
    )
}
```

### Domain-Specific Error Types

```kotlin
// core/domain/error/AuthError.kt
sealed class AuthError(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class NetworkError(message: String, cause: Throwable? = null) : AuthError(message, cause)
    class InvalidCredentials(message: String) : AuthError(message)
    class UserAlreadyExists(message: String) : AuthError(message)
    class ServerError(message: String, cause: Throwable? = null) : AuthError(message, cause)
    class UnknownError(message: String, cause: Throwable? = null) : AuthError(message, cause)
}
```

For crash reporting integration, see `references/crashlytics.md`.

### Data Synchronization

```kotlin
// core/data/sync/AuthSessionWorker.kt
@HiltWorker
class AuthSessionWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val authRepository: AuthRepository
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        authRepository.refreshSession().fold(
            onSuccess = { Result.success() },
            onFailure = { error ->
                when (error) {
                    is AuthError.NetworkError -> Result.retry()
                    is AuthError.ServerError -> if (runAttemptCount < 3) Result.retry() else Result.failure()
                    else -> Result.failure()
                }
            }
        )
    }
}
```

## Domain Layer

### Purpose
- **Pure business logic module** (minimal Android dependencies)
- Encapsulate complex business logic
- Remove duplicate logic from ViewModels
- Combine and transform data from multiple repositories
- **Optional but recommended** for complex applications

### Module Setup

Domain modules can be either:
- **Pure JVM/Kotlin modules** (`app.jvm.library`) - No Android dependencies
- **Android library modules** (`app.android.library`) - If you need `@Immutable`/`@Stable` annotations on domain models

```kotlin
// Option 1: Pure Kotlin module (no @Immutable annotations)
// core/domain/build.gradle.kts
plugins {
    alias(libs.plugins.app.jvm.library)
    alias(libs.plugins.app.hilt)
}

// Option 2: Android library (enables @Immutable for domain models)
// core/domain/build.gradle.kts
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
}

dependencies {
    // Only if using Option 2 and want @Immutable on domain models
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.runtime)  // Kotlin-only, no Android deps
}
```

**Note:** `androidx.compose.runtime` is a Kotlin-only library despite the `androidx` namespace. It contains `@Immutable` and `@Stable` annotations used for Compose compiler optimizations. See [compose-patterns.md](compose-patterns.md#stability-annotations-immutable-vs-stable) for details.

### Dependency Injection Setup

Hilt provides **compile-time DI** across features and core modules: `@Module` / `@InstallIn`, with `@HiltAndroidApp` and `@AndroidEntryPoint` entry points in the app module.

**Constructor injection:** Prefer `@Inject constructor(...)` on types Hilt builds. Avoid `@Inject lateinit var` on app or domain types (their dependencies are hidden and tests get harder). Platform types may still use field injection where the API requires it.

**`@Binds` vs `@Provides`:**
- **`@Binds`** - `abstract` method in a module; map an interface to an `@Inject`-constructable implementation (Hilt generates the binding).
- **`@Provides`** - you construct the instance (`OkHttpClient.Builder()`, `DataStoreFactory.create`, third-party SDKs). See **Hilt NetworkModule** and **DataStore** `#### Hilt Setup` in this Data Layer for real `@Provides` examples.

**Scopes (match real lifetime):**

| Annotation                | Lifetime                                       | Typical use                                          |
|---------------------------|------------------------------------------------|------------------------------------------------------|
| `@Singleton`              | Application                                    | Retrofit, `OkHttp`, Room 3, `DataStore`, dispatchers |
| `@ActivityRetainedScoped` | Survives config change until activity finished | Session-like state (use sparingly)                   |
| `@ViewModelScoped`        | Same as hosting `ViewModel`                    | Feature helpers (validators, calculators)            |
| `@ActivityScoped`         | Activity instance                              | Rare in Compose-first apps                           |
| `@FragmentScoped`         | Fragment instance                              | Rare when using Compose                              |

Over-scoping wastes memory; under-scoping duplicates heavy types or breaks singleton expectations.

**Modules:** Colocate modules with the **feature or layer** they wire (`AuthModule` in a feature, `DatabaseModule` in `core/data`). The app module owns the application graph entry points.

**Anti-patterns:**

| Problem                                                  | Why it hurts                   | Prefer                                                                    |
|----------------------------------------------------------|--------------------------------|---------------------------------------------------------------------------|
| `Activity` / `Fragment` in a `ViewModel`                 | Leaks, lifecycle mismatch      | Ids via `SavedStateHandle`, navigation args, repositories                 |
| Raw `Context` in a `ViewModel`                           | Same                           | `@ApplicationContext` in data/repository wiring, not in `ViewModel`       |
| `ViewModel` with `@Inject` but no `@HiltViewModel`       | Hilt does not own the instance | `@HiltViewModel` + `@Inject constructor` + `hiltViewModel()` in Compose   |
| Manual `ViewModel(...)` factories everywhere             | Bypasses graph                 | `hiltViewModel()` or Hilt-assisted factories                              |
| Feature-only deps in `SingletonComponent` "just in case" | Wrong lifetime, memory         | `ViewModelComponent` / `@ViewModelScoped` when only screens need the type |

**Navigation arguments and assisted injection:** `SavedStateHandle`, `@AssistedInject`, and `hiltViewModel` factory lambdas with Navigation3 - see `references/android-navigation.md` as the source of truth.

Official docs: [Hilt Android](https://developer.android.com/training/dependency-injection/hilt-android), [Hilt with Compose](https://developer.android.com/develop/ui/compose/libraries#hilt).

**Example - repository bindings in `core/data`:**

```kotlin
// core/data/di/DataModule.kt
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    
    @Binds
    @Singleton
    abstract fun bindAuthRepository(
        impl: AuthRepositoryImpl
    ): AuthRepository
    
    @Binds
    @Singleton
    abstract fun bindUserRepository(
        impl: UserRepositoryImpl
    ): UserRepository
}
```

### Use Case Pattern

Use cases are **optional** but recommended when:
1. Combining data from multiple repositories
2. Complex business logic that shouldn't be in ViewModels
3. Reusable operations across multiple features

**Simple pass-through use cases add unnecessary boilerplate.** ViewModels can call repositories directly for simple operations.

```kotlin
// ❌ Unnecessary use case (simple pass-through)
class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Result<AuthToken> =
        authRepository.login(email, password) // No added value
}

// ✅ Valuable use case (combines multiple repositories)
class GetUserProfileWithStatsUseCase @Inject constructor(
    private val userRepository: UserRepository,
    private val activityRepository: ActivityRepository,
    private val achievementRepository: AchievementRepository
) {
    operator fun invoke(userId: String): Flow<UserProfileWithStats> = combine(
        userRepository.observeUser(userId),
        activityRepository.observeActivityCount(userId),
        achievementRepository.observeAchievements(userId)
    ) { user, activityCount, achievements ->
        UserProfileWithStats(
            user = user,
            totalActivities = activityCount,
            achievements = achievements,
            completionRate = calculateCompletionRate(activityCount, achievements)
        )
    }
    
    private fun calculateCompletionRate(activities: Int, achievements: List<Achievement>): Float {
        if (activities == 0) return 0f
        val completed = achievements.count { it.isCompleted }
        return (completed.toFloat() / activities) * 100
    }
}

// ✅ Valuable use case (complex validation logic)
class ValidateRegistrationUseCase @Inject constructor() {
    operator fun invoke(email: String, password: String, confirmPassword: String): Result<Unit> {
        if (!email.matches(EMAIL_REGEX)) {
            return Result.failure(ValidationError.InvalidEmail)
        }
        if (password.length < 8) {
            return Result.failure(ValidationError.PasswordTooShort)
        }
        if (password != confirmPassword) {
            return Result.failure(ValidationError.PasswordMismatch)
        }
        if (!password.matches(PASSWORD_STRENGTH_REGEX)) {
            return Result.failure(ValidationError.PasswordTooWeak)
        }
        return Result.success(Unit)
    }
    
    companion object {
        private val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
        private val PASSWORD_STRENGTH_REGEX = Regex("^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$")
    }
}
```

### Repository Interface Pattern

```kotlin
// core/domain/repository/AuthRepository.kt
// ✅ @Stable: Interface contract guarantees observable changes
@Stable
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    suspend fun resetPassword(email: String): Result<Unit>
    fun observeAuthState(): Flow<AuthState> // Flow emissions are observable
    fun observeAuthEvents(): Flow<AuthEvent>
    suspend fun refreshSession(): Result<Unit>
}
```

### Domain Models

Domain models should be annotated with `@Immutable` for Compose stability. Use `@Immutable` for deeply immutable types (all `val` properties), and `@Stable` for mutable types with observable changes (see `references/compose-patterns.md` for detailed guidance).

```kotlin
// core/domain/model/

// ✅ @Immutable: Deeply immutable data
@Immutable
data class User(
    val id: String,
    val email: String,
    val name: String,
    val profileImage: String? = null
)

@Immutable
data class AuthToken(
    val value: String,
    val user: User
)

@Immutable
sealed class AuthState {
    data object Loading : AuthState()
    data object Unauthenticated : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data class Error(val message: String) : AuthState()
}

@Immutable
sealed class AuthEvent {
    data class SessionRefreshed(val timestamp: Instant) : AuthEvent()
    data class SessionExpired(val reason: String) : AuthEvent()
    data class Error(val message: String, val retryable: Boolean) : AuthEvent()
}

sealed class ValidationError : Exception() {
    data object InvalidEmail : ValidationError()
    data object PasswordTooShort : ValidationError()
    data object PasswordTooWeak : ValidationError()
    data object PasswordMismatch : ValidationError()
}
```

## Presentation Layer

### Location: Feature modules (`feature/*`)

### Components
- **Screen**: Main composable UI
- **ViewModel**: State holder and event processor
- **UiState**: Sealed interface representing all possible UI states
- **Actions**: Sealed class representing user interactions

### UiState, Actions, and ViewModel Patterns

Use `references/compose-patterns.md` for the detailed UiState, Action, and ViewModel
examples. Keep presentation logic in feature modules and keep UI composables stateless
where possible.

## UI Layer

### Location: `core/ui` (shared) and feature modules (specific)

### Screen Composition and Shared UI Components

Compose screen and component patterns live in `references/compose-patterns.md` to keep
UI guidance centralized.

## Navigation

For Navigation3 architecture, type-safe routing, state management, adaptive navigation
(`NavigationSuiteScaffold`), and migration guidance, see `references/android-navigation.md`.

## Complete Architecture Flow

### User Interaction Flow (UI → Data):
```
User Action → Screen → ViewModel → UseCase → Repository → Data Source
   (Event)   (UI)    (State)   (Business)  (Access)   (Persistence)
      ↓        ↓         ↓          ↓           ↓            ↓
   Click → Composable → Process → Transform → Retrieve → Local/Remote
```

### Data Response Flow (Data → UI):
```
Data Source → Repository → UseCase → ViewModel → UiState → Screen
   (Change)    (Update)   (Combine)   (Update)   (State)   (Render)
       ↓           ↓          ↓          ↓          ↓         ↓
  DB Update → Map Data → Business Logic → StateFlow → Observe → Recomposition
```

### Navigation Flow (Feature Coordination):
```
User Action → Screen → Navigator Interface → App Module → Navigation3
   (Navigate)   (Call)     (Contract)      (Implementation)  (Routing)
       ↓           ↓             ↓                ↓             ↓
   Tap Link → Call navigate() → Interface → App Navigator → NavController → Destination
```

## Combined Complete Flow Diagram:

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERACTION FLOW                                 │
│                                                                                    │
│  User Action (Event)                                                               │
│         ↓                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                             PRESENTATION LAYER                             │    │
│  │  ┌─────────────┐  ┌─────────────────────────┐  ┌──────────────────────┐    │    │
│  │  │   Screen    │  │      ViewModel          │  │    Navigator         │    │    │
│  │  │ (Composable)│  │  (StateFlow<UiState>)   │  │   (Interface)        │    │    │
│  │  └─────┬───────┘  └───────────┬─────────────┘  └──────────┬───────────┘    │    │
│  │        │                      │                           │                │    │
│  └────────┼──────────────────────┼───────────────────────────┼────────────────┘    │
│           │ onAction()           │ updateUiState()           │ navigate()          │
├───────────┼──────────────────────┼───────────────────────────┼─────────────────────┤
│           │                      │                           │                     │
│  ┌────────▼──────────┐ ┌─────────▼──────────┐      ┌─────────▼──────────────┐      │
│  │    DOMAIN LAYER   │ │    DATA LAYER      │      │    NAVIGATION          │      │
│  │  ┌─────────────┐  │ │  ┌──────────────┐  │      │  (App Module)          │      │
│  │  │   UseCase   │  │ │  │  Repository  │  │      │  ┌──────────────────┐  │      │
│  │  │ (Business)  │  │ │  │ (Data Access)│  │      │  │ App Navigator    │  │      │
│  │  └──────┬──────┘  │ │  └──────┬───────┘  │      │  │ (Implementation) │  │      │
│  │         │ invoke()│ │         │ getData()│      │  └──────────┬───────┘  │      │
│  └─────────┼─────────┘ └─────────┼──────────┘      └─────────────┼──────────┘      │
│            │                     │                               │                 │
│  ┌─────────▼─────────────────────▼───────────────────────────────▼──────────────┐  │
│  │                    DATA SOURCES / NAVIGATION ENGINE                          │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │  Local Storage  │  │  Remote API     │  │  Navigation3                 │  │  │
│  │  │   (Room 3)      │  │   (Retrofit)    │  │  (NavController)             │  │  │
│  │  └─────────────────┘  └─────────────────┘  └──────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                              DATA RESPONSE FLOW                                    │
│                                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │                    REACTIVE DATA STREAM                                    │    │
│  │                                                                            │    │
│  │  Data Change (Local/Remote) → Repository Flow → UseCase Transform →        │    │
│  │  ViewModel StateFlow → Screen Observation → UI Recomposition               │    │
│  │                                                                            │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────┤
│                              NAVIGATION RESPONSE FLOW                              │
│                                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐   │
│  │                    ADAPTIVE UI RENDERING                                    │   │
│  │                                                                             │   │
│  │  Navigation3 Route → Feature Graph → Screen Destination →                   │   │
│  │  NavigationSuiteScaffold → Adaptive Layout → UI Render                      │   │
│  │                                                                             │   │
│  └─────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Flow Rules:

### 1. **Unidirectional Event Flow (DOWN):**
```
User Action → Screen → ViewModel → UseCase → Repository → Data Source
     ↓           ↓         ↓         ↓          ↓           ↓
  Tap/Click → Handle → Process → Business → Data Access → Persist/Request
```

### 2. **Unidirectional Data Flow (UP):**
```
Data Source → Repository → UseCase → ViewModel → UiState → Screen → UI
     ↓           ↓         ↓         ↓          ↓         ↓       ↓
  DB/Network → Map → Combine → Update → Observe → Render → Display
```

### 3. **Unidirectional Navigation Flow:**
```
Screen → Navigator Interface → App Module → Navigation3 → Destination Screen
   ↓            ↓                  ↓            ↓             ↓
Call navigate() → Contract → Implementation → Routing → Render New UI
```

## Concrete Example Flow: Resetting a Password

### Phase 1: User Interaction (Event Flow DOWN)
```
1. User taps "Forgot Password?" on the login screen
2. Screen: LoginScreen calls viewModel.onAction(AuthAction.ForgotPasswordClicked)
3. ViewModel: AuthViewModel switches to AuthUiState.ForgotPasswordForm
4. User enters email and taps "Reset Password"
5. ViewModel: Calls ResetPasswordUseCase(email)
6. Repository: AuthRepository.resetPassword(email)
7. Data Source: RemoteAuthDataSource sends reset email
```

### Phase 2: Data Response (Data Flow UP)
```
1. Remote data source returns Result
2. Repository maps response to Result<Unit>
3. ViewModel updates uiState with isEmailSent or emailError
4. Screen observes uiState, shows confirmation or error
```

### Phase 3: Navigation Example (Separate Flow)
```
1. User taps "Create Account"
2. Screen: Calls authNavigator.navigateToRegister()
3. Navigator Interface: AuthNavigator.navigateToRegister() contract
4. App Module: AppNavigator implementation routes to "auth/register"
5. Navigation3: NavController navigates to register destination
6. Feature Graph: Renders RegisterScreen
7. UI: Shows registration form
```

This architecture ensures:
- **Responsive UI**: Immediate optimistic updates
- **Data consistency**: Single source of truth in local database
- **Offline support**: Works without network connection
- **Testability**: Each layer can be tested independently
- **Scalability**: Modular structure supports feature growth
- **Modern patterns**: Navigation3, Material3 adaptive design, predictive back gestures
- **Features are independent** (no feature-to-feature dependencies)
- **Navigation is coordinated centrally** (app module)
- **Data flows through defined layers** (UI → Domain → Data)
- **Each concern has clear boundaries** (navigation vs. business logic vs. UI rendering)