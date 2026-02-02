# Architecture Guide

Based on Google's official Android architecture guidance with modern Jetpack Compose, Navigation3, and our modular best practices.
All Kotlin code in this architecture must align with `references/kotlin-patterns.md`.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Architecture Principles](#architecture-principles)
3. [Data Layer](#data-layer)
4. [Domain Layer](#domain-layer)
5. [Presentation Layer](#presentation-layer)
6. [UI Layer](#ui-layer)
7. [Navigation](#navigation)
8. [Complete Architecture Flow](#complete-architecture-flow)

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
│   │  │   (Room + DAO)    │  │     (Retrofit)        │         │         │
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
| Local       | core/database  | Room DAO        | Persistent storage, source of truth |
| Remote      | core/network   | Retrofit API    | Network data fetching               |
| Preferences | core/datastore | Proto DataStore | User settings, simple key-value     |

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
- **Pure Kotlin module** (no Android dependencies)
- Encapsulate complex business logic
- Remove duplicate logic from ViewModels
- Combine and transform data from multiple repositories
- **Optional but recommended** for complex applications

### Dependency Injection Setup

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

### Navigation3 Architecture

Implementation examples for `AppNavigation`, `AuthDestination`, `AuthNavigator`, and `AuthGraph` live in
`references/modularization.md` to keep navigation wiring in one place.

### When to Use Navigation3:
- **All new Compose projects should use Navigation3** as it's the modern navigation API
- Building responsive UIs for phones, tablets, foldables, or desktop
- Need automatic navigation adaptation with `NavigationSuiteScaffold`
- Want Material 3 adaptive navigation patterns and list-detail layouts
- **Important**: Navigation3 is in active development; check current stability status before production use

### Key Benefits of Navigation3 Architecture:

1. **Feature Independence**: Features don't depend on each other; only app module coordinates navigation via `Navigator` interfaces
2. **Type-Safe Navigation**: Sealed `Destination` classes with `createRoute()` functions
3. **Testable Navigation**: `Navigator` interfaces allow easy mocking without NavController dependencies
4. **Adaptive UI**: `NavigationSuiteScaffold` automatically adapts between navigation bar, rail, and drawer based on `windowAdaptiveInfo`
5. **Single Backstack**: One `NavHost` controls entire app flow within `NavigationSuiteScaffold`
6. **Material 3 Integration**: Built-in support for Material 3 adaptive design with `ListDetailPaneScaffold`
7. **Modern API**: Latest navigation patterns including support for predictive back gestures
8. **Multi-pane Support**: Native support for list-detail layouts on tablets and foldables
9. **Window Adaptive Integration**: Direct access to `windowAdaptiveInfo` for responsive layouts
10. **Predictive Back Gestures**: Built-in support for Android's predictive back gesture system
11. **Compose-First Design**: Designed specifically for Jetpack Compose, not adapted from View system
12. **`windowAdaptiveInfo`**: Provides screen size/type information for adaptive decisions
13. **`ListDetailPaneScaffold`**: For tablet/foldable list-detail layouts
14. **`NavHost` from `androidx.navigation3`**: The Navigation3 version of NavHost
15. **`composable` from `androidx.navigation3.compose`**: Navigation3's composable destination

### Migration Note:
If migrating from Navigation 2.x to Navigation3:
1. Update imports from `androidx.navigation.*` to `androidx.navigation3.*`
2. Add `windowAdaptiveInfo` parameter to `NavigationSuiteScaffold`
3. Update `NavHost` and `rememberNavController()` imports
4. Consider implementing `ListDetailPaneScaffold` for tablet-optimized layouts

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
│  │  │   (Room)        │  │   (Retrofit)    │  │  (NavController)             │  │  │
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