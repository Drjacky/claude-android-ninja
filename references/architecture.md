# Architecture Guide

Based on Google's official Android architecture guidance with modern Jetpack Compose, Navigation3, and modular best practices.

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
5. **Testable by design**: Use interfaces and test doubles, no mocking libraries
6. **Layer separation**: Strict separation between Presentation, Domain, Data, and UI layers
7. **Dependency direction**: Features depend on Core modules, not on other features
8. **Navigation coordination**: App module coordinates navigation between features

## Module Structure

See the full module layout and naming conventions in `references/modularization.md`.

## Data Layer

### Principles
- **Offline-first**: Local database is the source of truth
- **Repository pattern**: Single public API for data access
- **Reactive streams**: All data exposed as `Flow<T>` or `StateFlow<T>`
- **Model mapping**: Separate Entity (database), DTO (network), and Domain models

### Repository Pattern

```kotlin
// core/domain - Repository interface (contract)
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    suspend fun resetPassword(email: String): Result<Unit>
    fun observeAuthState(): Flow<AuthState>
}

// core/data - Repository implementation
internal class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource,
    private val remoteDataSource: AuthRemoteDataSource,
    private val authMapper: AuthMapper
) : AuthRepository {

    override suspend fun login(email: String, password: String): Result<AuthToken> = runCatching {
        val response = remoteDataSource.login(email, password)
        localDataSource.saveAuthToken(response.token)
        localDataSource.saveUser(authMapper.toEntity(response.user))
        response.token
    }

    override suspend fun register(user: User): Result<Unit> = runCatching {
        remoteDataSource.register(authMapper.toNetwork(user))
        Unit
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
            .catch { e -> emit(AuthState.Error(e.message ?: "Unknown error")) }
}
```

### Data Sources

| Type        | Module         | Implementation  | Purpose                             |
|-------------|----------------|-----------------|-------------------------------------|
| Local       | core/database  | Room DAO        | Persistent storage, source of truth |
| Remote      | core/network   | Retrofit API    | Network data fetching               |
| Preferences | core/datastore | Proto DataStore | User settings, simple key-value     |

### Model Mapping Strategy

```kotlin
// core/data/mapping/AuthMapper.kt
class AuthMapper @Inject constructor() {
    
    // Entity → Domain
    fun toDomain(entity: UserEntity?): User = User(
        id = entity?.id.orEmpty(),
        email = entity?.email.orEmpty(),
        name = entity?.name.orEmpty(),
        profileImage = entity?.profileImage
    )
    
    // Network → Entity
    fun toEntity(user: NetworkUser): UserEntity = UserEntity(
        id = user.id,
        email = user.email,
        name = user.name,
        profileImage = user.profileImage
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
        runCatching {
            authRepository.refreshSession()
        }.fold(
            onSuccess = { Result.success() },
            onFailure = { Result.retry() }
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

### Use Case Pattern

```kotlin
// core/domain/usecase/LoginUseCase.kt
class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Result<AuthToken> =
        authRepository.login(email, password)
}

// core/domain/usecase/RegisterUseCase.kt
class RegisterUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(user: User): Result<Unit> =
        authRepository.register(user)
}

// core/domain/usecase/ObserveAuthStateUseCase.kt
class ObserveAuthStateUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    operator fun invoke(): Flow<AuthState> =
        authRepository.observeAuthState()
}

// core/domain/usecase/ResetPasswordUseCase.kt
class ResetPasswordUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String): Result<Unit> =
        authRepository.resetPassword(email)
}
```

### Repository Interface Pattern

```kotlin
// core/domain/repository/AuthRepository.kt
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    suspend fun resetPassword(email: String): Result<Unit>
    fun observeAuthState(): Flow<AuthState>
    fun observeAuthEvents(): Flow<AuthEvent>
}
```

### Domain Models

```kotlin
// core/domain/model/
data class User(
    val id: String,
    val email: String,
    val name: String,
    val profileImage: String? = null
)

data class AuthToken(
    val value: String,
    val user: User
)

sealed class AuthState {
    data object Loading : AuthState()
    data object Unauthenticated : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data class Error(val message: String) : AuthState()
}

sealed class AuthEvent {
    data class SessionRefreshed(val timestamp: Instant) : AuthEvent()
    data class SessionExpired(val reason: String) : AuthEvent()
    data class Error(val message: String, val retryable: Boolean) : AuthEvent()
}
```

## Presentation Layer

### Location: Feature modules (`feature/*`)

### Components
- **Screen**: Main composable UI
- **ViewModel**: State holder and event processor
- **UiState**: Sealed interface representing all possible UI states
- **Actions**: Sealed class representing user interactions

### UiState Modeling

```kotlin
// feature-auth/presentation/viewmodel/AuthUiState.kt
sealed interface AuthUiState {
    data object Loading : AuthUiState
    
    data class LoginForm(
        val email: String = "",
        val password: String = "",
        val isLoading: Boolean = false,
        val emailError: String? = null,
        val passwordError: String? = null
    ) : AuthUiState
    
    data class RegisterForm(
        val email: String = "",
        val password: String = "",
        val confirmPassword: String = "",
        val name: String = "",
        val isLoading: Boolean = false,
        val errors: Map<String, String> = emptyMap()
    ) : AuthUiState
    
    data class ForgotPasswordForm(
        val email: String = "",
        val isLoading: Boolean = false,
        val emailError: String? = null,
        val isEmailSent: Boolean = false
    ) : AuthUiState
    
    data class Success(val user: User) : AuthUiState
    
    data class Error(
        val message: String,
        val canRetry: Boolean = true
    ) : AuthUiState
}
```

### Actions Pattern

```kotlin
// feature-auth/presentation/viewmodel/AuthActions.kt
sealed class AuthAction {
    // Login screen actions
    data class EmailChanged(val email: String) : AuthAction()
    data class PasswordChanged(val password: String) : AuthAction()
    data object LoginClicked : AuthAction()
    data object ForgotPasswordClicked : AuthAction()
    data object RegisterClicked : AuthAction()
    
    // Register screen actions
    data class NameChanged(val name: String) : AuthAction()
    data class ConfirmPasswordChanged(val confirmPassword: String) : AuthAction()
    data object RegisterSubmit : AuthAction()
    data object NavigateToLogin : AuthAction()
    
    // Forgot password actions
    data object ResetPasswordClicked : AuthAction()
    
    // Error handling
    data object Retry : AuthAction()
    data object ClearError : AuthAction()
    
    // Navigation
    data object NavigateBack : AuthAction()
}
```

### ViewModel Pattern

```kotlin
// feature-auth/presentation/viewmodel/AuthViewModel.kt
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val registerUseCase: RegisterUseCase,
    private val resetPasswordUseCase: ResetPasswordUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.LoginForm())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    fun onAction(action: AuthAction) {
            when (action) {
            is AuthAction.EmailChanged -> updateLoginForm { it.copy(email = action.email) }
            is AuthAction.PasswordChanged -> updateLoginForm { it.copy(password = action.password) }
            AuthAction.LoginClicked -> performLogin()
            AuthAction.ForgotPasswordClicked -> _uiState.value = AuthUiState.ForgotPasswordForm()
            AuthAction.RegisterClicked -> _uiState.value = AuthUiState.RegisterForm()
            is AuthAction.NameChanged -> updateRegisterForm { it.copy(name = action.name) }
            is AuthAction.ConfirmPasswordChanged -> updateRegisterForm {
                it.copy(confirmPassword = action.confirmPassword)
            }
            AuthAction.RegisterSubmit -> performRegistration()
            AuthAction.NavigateToLogin -> _uiState.value = AuthUiState.LoginForm()
            AuthAction.ResetPasswordClicked -> performPasswordReset()
            AuthAction.Retry -> _uiState.value = AuthUiState.LoginForm()
            AuthAction.ClearError -> _uiState.value = AuthUiState.LoginForm()
            AuthAction.NavigateBack -> Unit
        }
    }
    
    private fun performLogin() {
        viewModelScope.launch {
            val current = _uiState.value as? AuthUiState.LoginForm ?: return@launch
            _uiState.value = current.copy(isLoading = true)
            val result = loginUseCase(current.email, current.password)
            _uiState.value = result.fold(
                onSuccess = { token -> AuthUiState.Success(token.user) },
                onFailure = { error -> AuthUiState.Error(error.message ?: "Login failed") }
            )
        }
    }
    
    private fun performPasswordReset() {
        viewModelScope.launch {
            val current = _uiState.value as? AuthUiState.ForgotPasswordForm ?: return@launch
            _uiState.value = current.copy(isLoading = true)
            val result = resetPasswordUseCase(current.email)
            _uiState.value = result.fold(
                onSuccess = { current.copy(isLoading = false, isEmailSent = true) },
                onFailure = { error -> current.copy(isLoading = false, emailError = error.message) }
            )
        }
    }
    
    private fun performRegistration() {
        viewModelScope.launch {
            val current = _uiState.value as? AuthUiState.RegisterForm ?: return@launch
            _uiState.value = current.copy(isLoading = true)
            val user = User(id = "", email = current.email, name = current.name)
            val result = registerUseCase(user)
            _uiState.value = result.fold(
                onSuccess = { AuthUiState.Success(user) },
                onFailure = { error -> AuthUiState.Error(error.message ?: "Registration failed") }
            )
        }
    }
    
    private fun updateLoginForm(transform: (AuthUiState.LoginForm) -> AuthUiState.LoginForm) {
        val current = _uiState.value as? AuthUiState.LoginForm ?: return
        _uiState.value = transform(current)
    }
    
    private fun updateRegisterForm(
        transform: (AuthUiState.RegisterForm) -> AuthUiState.RegisterForm
    ) {
        val current = _uiState.value as? AuthUiState.RegisterForm ?: return
        _uiState.value = transform(current)
    }
}
```

## UI Layer

### Location: `core/ui` (shared) and feature modules (specific)

### Screen Composition Pattern

```kotlin
// feature-auth/presentation/LoginScreen.kt
@Composable
fun LoginScreen(
    onRegisterClick: () -> Unit,
    onForgotPasswordClick: () -> Unit,
    onLoginSuccess: (User) -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    LaunchedEffect(uiState) {
        if (uiState is AuthUiState.Success) {
            onLoginSuccess((uiState as AuthUiState.Success).user)
        }
    }
    
    AuthContent(
        uiState = uiState,
        onAction = viewModel::onAction,
        onRegisterClick = onRegisterClick,
        onForgotPasswordClick = onForgotPasswordClick,
        modifier = Modifier.fillMaxSize()
    )
}

@Composable
private fun AuthContent(
    uiState: AuthUiState,
    onAction: (AuthAction) -> Unit,
    onRegisterClick: () -> Unit,
    onForgotPasswordClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(modifier = modifier) {
        when (uiState) {
            AuthUiState.Loading -> LoadingScreen()
            is AuthUiState.LoginForm -> AuthFormCard(
                state = uiState,
                onEmailChanged = { onAction(AuthAction.EmailChanged(it)) },
                onPasswordChanged = { onAction(AuthAction.PasswordChanged(it)) },
                onLoginClick = { onAction(AuthAction.LoginClicked) },
                onRegisterClick = onRegisterClick,
                onForgotPasswordClick = onForgotPasswordClick
            )
            is AuthUiState.ForgotPasswordForm -> ForgotPasswordCard(
                state = uiState,
                onEmailChanged = { onAction(AuthAction.EmailChanged(it)) },
                onResetClick = { onAction(AuthAction.ResetPasswordClicked) },
                onBackClick = { onAction(AuthAction.NavigateBack) }
            )
            is AuthUiState.Error -> ErrorContent(uiState.message, onRetry = { onAction(AuthAction.Retry) })
            is AuthUiState.Success -> Unit
        }
    }
}
```

### Shared UI Components

```kotlin
// core/ui/components/AuthFormCard.kt
@Composable
fun AuthFormCard(
    state: AuthUiState.LoginForm,
    onEmailChanged: (String) -> Unit,
    onPasswordChanged: (String) -> Unit,
    onLoginClick: () -> Unit,
    onRegisterClick: () -> Unit,
    onForgotPasswordClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("Welcome back", style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = state.email,
                onValueChange = onEmailChanged,
                label = { Text("Email") },
                isError = state.emailError != null
            )
            OutlinedTextField(
                value = state.password,
                onValueChange = onPasswordChanged,
                label = { Text("Password") },
                visualTransformation = PasswordVisualTransformation(),
                isError = state.passwordError != null
            )
            Button(
                onClick = onLoginClick,
                enabled = state.email.isNotBlank() && state.password.isNotBlank() && !state.isLoading
            ) {
                Text(if (state.isLoading) "Signing in..." else "Login")
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(onClick = onRegisterClick) { Text("Create account") }
                TextButton(onClick = onForgotPasswordClick) { Text("Forgot password?") }
            }
        }
    }
}
```

## Navigation

### Navigation3 Architecture

Implementation examples for `AppNavigation`, `AuthDestination`, `AuthNavigator`, and `AuthGraph` live in
`references/modularization.md` to keep navigation wiring in one place.

### When to Use Navigation3:
- **All new Compose projects should use Navigation3** as it's the modern navigation API
- Building responsive UIs for phones, tablets, foldables, or desktop
- Need automatic navigation adaptation with `NavigationSuiteScaffold`
- Want Material 3 adaptive navigation patterns and list-detail layouts
- **Important**: Navigation3 is currently in beta (1.4.0-beta01), suitable for production but expect minor API changes

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