# Android Development

Create production-quality Android applications following Google's official architecture guidance and [NowInAndroid](https://github.com/android/nowinandroid) best practices.
Use when building Android apps with Kotlin, Jetpack Compose, MVVM architecture, Hilt dependency injection, Room database, or Android multi-module projects.
Triggers on requests to create Android projects, screens, ViewModels, repositories, feature modules, or when asked about Android architecture patterns.


## Quick Reference

| Task                                                 | Reference File                                        |
|------------------------------------------------------|-------------------------------------------------------|
| Project structure & modules                          | [modularization.md](references/modularization.md)     |
| Architecture layers (Presentation, Domain, Data, UI) | [architecture.md](references/architecture.md)         |
| Jetpack Compose patterns                             | [compose-patterns.md](references/compose-patterns.md) |
| Gradle & build configuration                         | [gradle-setup.md](references/gradle-setup.md)         |
| Testing approach                                     | [testing.md](references/testing.md)                   |
| Multi-module dependencies                            | [dependencies.md](references/dependencies.md)         |

## Workflow Decision Tree

**Creating a new project?**
→ Read [modularization.md](references/modularization.md) for project structure
→ Use templates in `assets/templates/`
→ Set up **app module** for navigation and DI setup
→ Configure **feature modules** and **core modules**

**Adding a new feature?**
→ Create **feature module** following naming convention `feature-[name]`
→ Implement **Presentation Layer** in feature module
→ Follow dependency flow: Feature → Core/Domain → Core/Data
→ Add navigation from **app module**

**Building UI screens?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Create Screen + ViewModel + UiState in **feature module**
→ Use shared components from `core/ui` when possible

**Setting up data layer?**
→ Read data layer section in [architecture.md](references/architecture.md)
→ Create Repository interfaces in `core/domain`
→ Implement Repository in `core/data`
→ Create DataSource + DAO in `core/data`

**Setting up navigation?**
→ Configure navigation graph in **app module**
→ Use feature module navigation destinations
→ Handle deep links and navigation arguments

## Core Principles

1. **Offline-first**: Local database is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use Kotlin Flow/StateFlow for all data exposure
4. **Modular by feature**: Each feature is self-contained with clear boundaries
5. **Testable by design**: Use interfaces and test doubles, no mocking libraries
6. **Layer separation**: Strict separation between Presentation, Domain, Data, and UI layers
7. **Dependency direction**: Features depend on Core modules, not on other features
8. **Navigation coordination**: App module coordinates navigation between features

## Architecture Layers (Multi-Module)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FEATURE MODULES (feature/*)                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │              Presentation Layer                                  │    │
│  │  ┌──────────────┐    ┌─────────────────────────┐               │    │
│  │  │   Screen     │◄───│      ViewModel          │               │    │
│  │  │  (Compose)   │    │  (StateFlow<UiState>)   │               │    │
│  │  └──────────────┘    └───────────┬─────────────┘               │    │
│  │                                   │                             │    │
│  └───────────────────────────────────┼─────────────────────────────┘    │
│                                       │ Uses                             │
├───────────────────────────────────────┼──────────────────────────────────┤
│             CORE/DOMAIN Module        │                                  │
│  ┌────────────────────────────────────▼──────────────────────┐          │
│  │                    Domain Layer                           │          │
│  │  ┌────────────────────────────────────────────────────┐  │          │
│  │  │                Use Cases                           │  │          │
│  │  │           (combine/transform logic)                │  │          │
│  │  └───────────────────────┬────────────────────────────┘  │          │
│  │  ┌───────────────────────▼────────────────────────────┐  │          │
│  │  │             Repository Interfaces                   │  │          │
│  │  │           (contracts for data layer)               │  │          │
│  │  └───────────────────────┬────────────────────────────┘  │          │
│  │  ┌───────────────────────▼────────────────────────────┐  │          │
│  │  │                Domain Models                       │  │          │
│  │  │           (business entities)                      │  │          │
│  │  └────────────────────────────────────────────────────┘  │          │
│  └──────────────────────────────────────────────────────────┘          │
│                                       │ Implements                      │
├───────────────────────────────────────┼──────────────────────────────────┤
│               CORE/DATA Module        │                                  │
│  ┌────────────────────────────────────▼──────────────────────┐          │
│  │                    Data Layer                             │          │
│  │  ┌────────────────────────────────────────────────────┐  │          │
│  │  │              Repository Implementations             │  │          │
│  │  │    (offline-first, single source of truth)         │  │          │
│  │  └─────────┬─────────────────────┬────────────────────┘  │          │
│  │            │                     │                       │          │
│  │  ┌─────────▼─────────┐  ┌───────▼──────────────┐      │          │
│  │  │  Local DataSource │  │  Remote DataSource   │      │          │
│  │  │   (Room + DAO)    │  │     (Retrofit)       │      │          │
│  │  └─────────┬─────────┘  └──────────────────────┘      │          │
│  │            │                                           │          │
│  │  ┌─────────▼──────────────────────────────────────┐   │          │
│  │  │              Data Models                       │   │          │
│  │  │      (Entity, DTO, Response objects)           │   │          │
│  │  └────────────────────────────────────────────────┘   │          │
│  └────────────────────────────────────────────────────────┘          │
│                                                                       │
├───────────────────────────────────────────────────────────────────────┤
│                APP MODULE (Navigation & Coordination)                 │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              Navigation Coordination                            │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │        App NavHost + Navigator Implementations          │    │  │
│  │  │   (Coordinates all feature navigation)                  │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │        Dependency Injection Setup                        │    │  │
│  │  │   (Hilt modules, provides implementations)              │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                       │
├───────────────────────────────────────────────────────────────────────┤
│                CORE/UI Module (shared UI resources)                   │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    UI Layer                                     │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │        Shared UI Components                             │    │  │
│  │  │   (Buttons, Cards, Dialogs, etc.)                       │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │           Themes & Design System                         │    │  │
│  │  │   (Colors, Typography, Shapes)                           │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  │  ┌─────────────────────────────────────────────────────────┐    │  │
│  │  │         Base ViewModels / State Management              │    │  │
│  │  │   (BaseViewModel, UiState, etc.)                        │    │  │
│  │  └─────────────────────────────────────────────────────────┘    │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

## Dependency Flow Rules

```
feature/* → core/domain → core/data
    ↓                       ↓
core/ui (optional)       (no circular dependencies)

app → all feature modules (for navigation coordination)
app → all core modules (for DI setup)

NO feature-to-feature dependencies allowed
```

### Strict Rules:
1. **Feature modules can only depend on Core modules**
2. **Feature modules cannot depend on other feature modules**
3. **Core/Domain has no Android dependencies** (pure Kotlin)
4. **Core/Data depends on Core/Domain** (implements interfaces)
5. **Core/UI is optional** for features that need shared UI components
6. **App module depends on all features** for navigation coordination
7. **No circular dependencies** between any modules

## Creating a New Feature

### 1. Create Feature Module Structure

```
feature-auth/
├── build.gradle.kts
├── src/main/
│   ├── kotlin/com/example/feature/auth/
│   │   ├── presentation/              # UI Layer
│   │   │   ├── AuthScreen.kt          # Main composable
│   │   │   ├── AuthRoute.kt           # Navigation setup
│   │   │   ├── viewmodel/             
│   │   │   │   ├── AuthViewModel.kt   # State holder
│   │   │   │   ├── AuthUiState.kt     # UI state models
│   │   │   │   └── AuthActions.kt     # User actions
│   │   │   └── components/            # Smaller UI components
│   │   ├── navigation/                # Navigation Layer
│   │   │   ├── AuthDestination.kt     # Feature routes
│   │   │   ├── AuthNavigator.kt       # Navigation interface
│   │   │   └── AuthGraph.kt           # NavGraphBuilder extension
│   │   └── domain/                    # Optional: Feature-specific domain
│   │       ├── repository/
│   │       └── usecase/
│   └── res/                          # Feature resources
```

### 2. Configure Feature Module Dependencies

```kotlin
// feature-auth/build.gradle.kts
dependencies {
    // Core dependencies
    implementation(project(":core:domain"))
    implementation(project(":core:ui"))      // Optional for shared UI
    
    // AndroidX dependencies
    implementation(libs.androidx.compose.bom)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.bundles.navigation3)
    
    // DI
    implementation(libs.hilt.android)
    kapt(libs.hilt.compiler)
    
    // Optional: Navigation3 for adaptive UI
    // implementation(libs.androidx.navigation3.compose)
    // implementation(libs.androidx.material3.adaptive.navigation3)
}
```

### 3. Create Domain Layer Contracts (in core/domain)

```kotlin
// core/domain/src/main/kotlin/com/example/domain/auth/
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    suspend fun resetPassword(email: String): Result<Unit>
    fun observeAuthState(): Flow<AuthState>
}

data class User(
    val id: String,
    val email: String,
    val name: String,
    val profileImage: String? = null
)

sealed class AuthState {
    data object Loading : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data object Unauthenticated : AuthState()
    data class Error(val message: String) : AuthState()
}

class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Result<AuthToken> =
        authRepository.login(email, password)
}

class RegisterUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(user: User): Result<Unit> =
        authRepository.register(user)
}
```

### 4. Implement Data Layer (in core/data)

```kotlin
// core/data/src/main/kotlin/com/example/data/auth/
internal class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource,
    private val remoteDataSource: AuthRemoteDataSource,
    private val authMapper: AuthMapper
) : AuthRepository {
    
    override suspend fun login(email: String, password: String): Result<AuthToken> {
        return try {
            val response = remoteDataSource.login(email, password)
            localDataSource.saveAuthToken(response.token)
            localDataSource.saveUser(authMapper.toEntity(response.user))
            Result.success(response.token)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override fun observeAuthState(): Flow<AuthState> {
        return localDataSource.observeAuthToken().map { token ->
            if (token != null) {
                val userEntity = localDataSource.getUser()
                AuthState.Authenticated(authMapper.toDomain(userEntity))
            } else {
                AuthState.Unauthenticated
            }
        }.catch { e ->
            emit(AuthState.Error(e.message ?: "Unknown error"))
        }
    }
}
```

### 5. Create UI in Feature Module

#### AuthUiState.kt (`presentation/viewmodel/`)
```kotlin
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

#### AuthActions.kt (`presentation/viewmodel/`)
```kotlin
sealed class AuthAction {
    // Login Screen Actions
    data class EmailChanged(val email: String) : AuthAction()
    data class PasswordChanged(val password: String) : AuthAction()
    data object LoginClicked : AuthAction()
    data object ForgotPasswordClicked : AuthAction()
    data object RegisterClicked : AuthAction()
    
    // Register Screen Actions
    data class NameChanged(val name: String) : AuthAction()
    data class ConfirmPasswordChanged(val confirmPassword: String) : AuthAction()
    data object RegisterSubmit : AuthAction()
    data object NavigateToLogin : AuthAction()
    
    // Forgot Password Actions
    data object ResetPasswordClicked : AuthAction()
    
    // Common Actions
    data object Retry : AuthAction()
    data object ClearError : AuthAction()
    data object NavigateBack : AuthAction()
}
```

#### AuthViewModel.kt (`presentation/viewmodel/`)
```kotlin
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
            // Login actions
            is AuthAction.EmailChanged -> updateLoginForm { it.copy(email = action.email) }
            is AuthAction.PasswordChanged -> updateLoginForm { it.copy(password = action.password) }
            AuthAction.LoginClicked -> performLogin()
            
            // Register actions
            is AuthAction.NameChanged -> updateRegisterForm { it.copy(name = action.name) }
            is AuthAction.ConfirmPasswordChanged -> updateRegisterForm { 
                it.copy(confirmPassword = action.confirmPassword) 
            }
            AuthAction.RegisterSubmit -> performRegistration()
            
            // Navigation actions
            AuthAction.RegisterClicked -> {
                _uiState.value = AuthUiState.RegisterForm()
            }
            AuthAction.ForgotPasswordClicked -> {
                _uiState.value = AuthUiState.ForgotPasswordForm()
            }
            AuthAction.NavigateToLogin -> {
                _uiState.value = AuthUiState.LoginForm()
            }
            AuthAction.Retry -> handleRetry()
            AuthAction.ClearError -> clearError()
            AuthAction.ResetPasswordClicked -> performPasswordReset()
            AuthAction.NavigateBack -> {
                // Navigation handled by screen via navigator
            }
        }
    }
    
    private fun performLogin() {
        viewModelScope.launch {
            _uiState.value = when (val current = _uiState.value) {
                is AuthUiState.LoginForm -> current.copy(isLoading = true)
                else -> return@launch
            }
            
            val result = loginUseCase(
                email = (_uiState.value as AuthUiState.LoginForm).email,
                password = (_uiState.value as AuthUiState.LoginForm).password
            )
            
            _uiState.value = when (result) {
                is Result.Success -> AuthUiState.Success(result.data.user)
                is Result.Error -> AuthUiState.Error(
                    message = result.exception.message ?: "Login failed",
                    canRetry = true
                )
            }
        }
    }
    
    private fun updateLoginForm(transform: (AuthUiState.LoginForm) -> AuthUiState.LoginForm) {
        _uiState.value = when (val current = _uiState.value) {
            is AuthUiState.LoginForm -> transform(current)
            else -> current
        }
    }
    
    private fun updateRegisterForm(transform: (AuthUiState.RegisterForm) -> AuthUiState.RegisterForm) {
        _uiState.value = when (val current = _uiState.value) {
            is AuthUiState.RegisterForm -> transform(current)
            else -> current
        }
    }
    
    private fun clearError() {
        _uiState.value = when (val current = _uiState.value) {
            is AuthUiState.Error -> AuthUiState.LoginForm()
            else -> current
        }
    }
    
    private fun handleRetry() {
        when (val current = _uiState.value) {
            is AuthUiState.Error -> {
                if (current.message.contains("login", ignoreCase = true)) {
                    _uiState.value = AuthUiState.LoginForm()
                }
            }
            else -> {}
        }
    }
    
    private fun performPasswordReset() {
        viewModelScope.launch {
            _uiState.value = when (val current = _uiState.value) {
                is AuthUiState.ForgotPasswordForm -> current.copy(isLoading = true)
                else -> return@launch
            }
            
            val email = (_uiState.value as AuthUiState.ForgotPasswordForm).email
            val result = resetPasswordUseCase(email)
            
            _uiState.value = when (result) {
                is Result.Success -> AuthUiState.ForgotPasswordForm(
                    email = email,
                    isEmailSent = true
                )
                is Result.Error -> AuthUiState.ForgotPasswordForm(
                    email = email,
                    emailError = result.exception.message ?: "Failed to send reset email"
                )
            }
        }
    }
}
```

#### AuthDestination.kt (`navigation/`)
```kotlin
sealed class AuthDestination(val route: String) {
    object Login : AuthDestination("auth/login")
    object Register : AuthDestination("auth/register")
    object ForgotPassword : AuthDestination("auth/forgot_password")
    
    object Profile : AuthDestination("auth/profile/{userId}") {
        fun createRoute(userId: String) = "auth/profile/$userId"
    }
    
    object VerifyEmail : AuthDestination("auth/verify/{token}") {
        fun createRoute(token: String) = "auth/verify/$token"
    }
    
    companion object {
        fun fromRoute(route: String?): AuthDestination? {
            return when {
                route?.startsWith("auth/profile/") == true -> Profile
                route?.startsWith("auth/verify/") == true -> VerifyEmail
                route == Login.route -> Login
                route == Register.route -> Register
                route == ForgotPassword.route -> ForgotPassword
                else -> null
            }
        }
    }
}
```

#### AuthNavigator.kt (`navigation/`)
```kotlin
interface AuthNavigator {
    // Navigation to other screens within this feature
    fun navigateToRegister()
    fun navigateToForgotPassword()
    fun navigateBack()
    
    // Navigation to other features (implemented in app module)
    fun navigateToHome()
    fun navigateToProfile(userId: String)
    fun navigateToMainApp()
    
    // Deep link navigation
    fun navigateToVerifyEmail(token: String)
    fun navigateToResetPassword(token: String)
}
```

#### AuthGraph.kt (`navigation/`)
```kotlin
fun NavGraphBuilder.authGraph(
    authNavigator: AuthNavigator,
    startDestination: String = AuthDestination.Login.route
) {
    composable(
        route = AuthDestination.Login.route,
        arguments = listOf(
            navArgument("deepLinkToken") {
                type = NavType.StringType
                nullable = true
                defaultValue = null
            }
        )
    ) { backStackEntry ->
        val deepLinkToken = backStackEntry.arguments?.getString("deepLinkToken")
        
        LoginScreen(
            deepLinkToken = deepLinkToken,
            onLoginSuccess = { user ->
                authNavigator.navigateToMainApp()
            },
            onRegisterClick = {
                authNavigator.navigateToRegister()
            },
            onForgotPasswordClick = {
                authNavigator.navigateToForgotPassword()
            }
        )
    }
    
    composable(route = AuthDestination.Register.route) {
        RegisterScreen(
            onRegisterSuccess = { user ->
                authNavigator.navigateToMainApp()
            },
            onNavigateToLogin = {
                authNavigator.navigateBack()
            }
        )
    }
    
    composable(route = AuthDestination.ForgotPassword.route) {
        ForgotPasswordScreen(
            onResetSuccess = {
                authNavigator.navigateBack()
            },
            onNavigateBack = {
                authNavigator.navigateBack()
            }
        )
    }
    
    composable(
        route = AuthDestination.VerifyEmail.route,
        arguments = listOf(navArgument("token") { type = NavType.StringType })
    ) { backStackEntry ->
        val token = backStackEntry.arguments?.getString("token")
        VerifyEmailScreen(
            token = token ?: "",
            onVerificationComplete = {
                authNavigator.navigateToLogin()
            }
        )
    }
}
```

#### AuthScreen.kt (`presentation/`)
```kotlin
@Composable
fun LoginScreen(
    deepLinkToken: String? = null,
    onLoginSuccess: (User) -> Unit,
    onRegisterClick: () -> Unit,
    onForgotPasswordClick: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Handle deep links
    LaunchedEffect(deepLinkToken) {
        deepLinkToken?.let { token ->
            // Process verification token
            viewModel.onAction(AuthAction.EmailChanged(extractEmailFromToken(token)))
        }
    }
    
    // Handle successful login
    LaunchedEffect(uiState) {
        if (uiState is AuthUiState.Success) {
            val user = (uiState as AuthUiState.Success).user
            onLoginSuccess(user)
        }
    }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        contentAlignment = Alignment.Center
    ) {
        when (val state = uiState) {
            is AuthUiState.LoginForm -> {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Using shared components from core/ui
                    AppLogo()
                    
                    OutlinedTextField(
                        value = state.email,
                        onValueChange = { viewModel.onAction(AuthAction.EmailChanged(it)) },
                        label = { Text("Email") },
                        isError = state.emailError != null,
                        supportingText = {
                            state.emailError?.let { Text(it) }
                        }
                    )
                    
                    OutlinedTextField(
                        value = state.password,
                        onValueChange = { viewModel.onAction(AuthAction.PasswordChanged(it)) },
                        label = { Text("Password") },
                        visualTransformation = PasswordVisualTransformation(),
                        isError = state.passwordError != null,
                        supportingText = {
                            state.passwordError?.let { Text(it) }
                        }
                    )
                    
                    Button(
                        onClick = { viewModel.onAction(AuthAction.LoginClicked) },
                        enabled = state.email.isNotBlank() && 
                                 state.password.isNotBlank() && 
                                 !state.isLoading,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        if (state.isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                strokeWidth = 2.dp
                            )
                        } else {
                            Text("Login")
                        }
                    }
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        TextButton(onClick = onRegisterClick) {
                            Text("Create Account")
                        }
                        
                        TextButton(onClick = onForgotPasswordClick) {
                            Text("Forgot Password?")
                        }
                    }
                }
            }
            
            is AuthUiState.Loading -> {
                LoadingSpinner()
            }
            
            is AuthUiState.Error -> {
                ErrorCard(
                    message = state.message,
                    onRetry = {
                        if (state.canRetry) {
                            viewModel.onAction(AuthAction.Retry)
                        }
                    }
                )
            }
            
            else -> {
                // Should not happen for login screen
                Text("Unexpected state")
            }
        }
    }
}
```

### 6. Set Up App Module Navigation

```kotlin
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.adaptive.ExperimentalMaterial3AdaptiveApi
import androidx.compose.material3.adaptive.WindowAdaptiveInfo
import androidx.compose.material3.adaptive.currentWindowAdaptiveInfo
import androidx.compose.material3.adaptive.layout.ListDetailPaneScaffold
import androidx.compose.material3.adaptive.layout.ListDetailPaneScaffoldRole
import androidx.compose.material3.adaptive.layout.rememberListDetailPaneScaffoldState
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffoldState
import androidx.compose.material3.adaptive.navigationsuite.rememberNavigationSuiteScaffoldState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation3.NavHost
import androidx.navigation3.compose.rememberNavController

@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    val navigationSuiteScaffoldState = rememberNavigationSuiteScaffoldState()
    
    // Create navigators in app module
    val authNavigator = remember {
        object : AuthNavigator {
            override fun navigateToHome() {
                navController.navigate("home") {
                    popUpTo("auth") { inclusive = true }
                }
            }
            override fun navigateToRegister() = navController.navigate("auth/register")
            override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
            override fun navigateBack() = navController.popBackStack()
            override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
            override fun navigateToMainApp() {
                navController.navigate("main") {
                    popUpTo("auth") { inclusive = true }
                }
            }
            override fun navigateToVerifyEmail(token: String) = navController.navigate("auth/verify/$token")
            override fun navigateToResetPassword(token: String) = navController.navigate("auth/reset/$token")
        }
    }
    
    NavigationSuiteScaffold(
        state = navigationSuiteScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        navigationSuiteItems = {
            item(
                icon = androidx.compose.material.icons.Icons.Default.Home,
                label = "Home",
                selected = navController.currentDestination?.route?.startsWith("home") == true ||
                          navController.currentDestination?.route == "main",
                onClick = { navController.navigate("home") }
            )
            item(
                icon = androidx.compose.material.icons.Icons.Default.Person,
                label = "Profile",
                selected = navController.currentDestination?.route?.startsWith("profile") == true,
                onClick = { navController.navigate("profile/current") }
            )
            item(
                icon = androidx.compose.material.icons.Icons.Default.Settings,
                label = "Settings",
                selected = navController.currentDestination?.route?.startsWith("settings") == true,
                onClick = { navController.navigate("settings") }
            )
        }
    ) {
        NavHost(
            navController = navController,
            startDestination = "auth",
            modifier = Modifier.fillMaxSize()
        ) {
            authGraph(authNavigator)
            homeGraph(
                homeNavigator = remember {
                    object : HomeNavigator {
                        override fun navigateToDetails(itemId: String) = 
                            navController.navigate("home/details/$itemId")
                        override fun navigateBack() = navController.popBackStack()
                    }
                }
            )
            settingsGraph()
            
            // Main app screen (could be tab navigation)
            composable("main") {
                MainAppScreen(
                    onLogout = {
                        navController.navigate("auth") {
                            popUpTo("main") { inclusive = true }
                        }
                    }
                )
            }
            
            // Profile feature
            composable(
                route = "profile/{userId}",
                arguments = listOf(navArgument("userId") { type = NavType.StringType })
            ) { backStackEntry ->
                ProfileScreen(
                    userId = backStackEntry.arguments?.getString("userId") ?: "",
                    onNavigateBack = { navController.popBackStack() }
                )
            }
        }
    }
}

// For list-detail layouts (tablets, foldables)
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigationWithListDetail(
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
    val navController = rememberNavController()
    val listDetailPaneScaffoldState = rememberListDetailPaneScaffoldState()
    
    ListDetailPaneScaffold(
        state = listDetailPaneScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        listPane = {
            // Left pane - list view
            Column(modifier = Modifier.fillMaxSize()) {
                // List items that can navigate to detail
            }
        },
        detailPane = {
            // Right pane - detail view
            NavHost(
                navController = navController,
                startDestination = "auth"
            ) {
                authGraph(/* ... */)
                // Other graphs
            }
        }
    )
}

// Simple version without adaptive UI (if needed)
@Composable
fun AppNavigationSimple() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "auth"
    ) {
        authGraph(
            authNavigator = remember {
                object : AuthNavigator {
                    override fun navigateToHome() = navController.navigate("home")
                    override fun navigateToRegister() = navController.navigate("auth/register")
                    override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
                    override fun navigateBack() = navController.popBackStack()
                    override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
                    override fun navigateToMainApp() = navController.navigate("main")
                    override fun navigateToVerifyEmail(token: String) = navController.navigate("auth/verify/$token")
                    override fun navigateToResetPassword(token: String) = navController.navigate("auth/reset/$token")
                }
            }
        )
        homeGraph(
            homeNavigator = remember {
                object : HomeNavigator {
                    override fun navigateToDetails(itemId: String) = navController.navigate("home/details/$itemId")
                    override fun navigateBack() = navController.popBackStack()
                }
            }
        )
        // Other feature graphs
    }
}
```

Based on the updated Navigation3 implementation, here are the necessary changes:

## Navigation Patterns Summary

### When to Use Navigation3:
- **All new Compose projects should use Navigation3** as it's the modern navigation API
- Building responsive UIs for phones, tablets, foldables, or desktop
- Need automatic navigation adaptation with `NavigationSuiteScaffold`
- Want Material 3 adaptive navigation patterns and list-detail layouts
- **Important**: Navigation3 is currently in beta (1.4.0-beta01), suitable for production but expect minor API changes

### Key Benefits of Navigation3 Architecture:

1. **✅ Feature Independence**: Features don't depend on each other; only app module coordinates navigation via `Navigator` interfaces
2. **✅ Type-Safe Navigation**: Sealed `Destination` classes with `createRoute()` functions
3. **✅ Testable Navigation**: `Navigator` interfaces allow easy mocking without NavController dependencies
4. **✅ Adaptive UI**: `NavigationSuiteScaffold` automatically adapts between navigation bar, rail, and drawer based on `windowAdaptiveInfo`
5. **✅ Single Backstack**: One `NavHost` controls entire app flow within `NavigationSuiteScaffold`
6. **✅ Material 3 Integration**: Built-in support for Material 3 adaptive design with `ListDetailPaneScaffold`
7. **✅ Modern API**: Latest navigation patterns including support for predictive back gestures
8. **✅ Multi-pane Support**: Native support for list-detail layouts on tablets and foldables

### Navigation3-Specific Benefits Added:
9. **✅ Window Adaptive Integration**: Direct access to `windowAdaptiveInfo` for responsive layouts
10. **✅ Predictive Back Gestures**: Built-in support for Android's predictive back gesture system
11. **✅ Compose-First Design**: Designed specifically for Jetpack Compose, not adapted from View system

### Updated Navigation Flow:
```
User Action → Screen → ViewModel (business logic) → UiState Update
      ↓
Screen observes UiState → Calls Navigator Interface
      ↓
App Module implements Navigator → Coordinates between features
      ↓
Navigation3 NavController navigates → Feature Graph (NavGraphBuilder extension) renders screen
      ↓
NavigationSuiteScaffold adapts UI based on windowAdaptiveInfo
```

### Key Navigation3 Components:
- **`NavigationSuiteScaffold`**: Adaptive container that switches between navigation modes
- **`windowAdaptiveInfo`**: Provides screen size/type information for adaptive decisions
- **`ListDetailPaneScaffold`**: For tablet/foldable list-detail layouts
- **`NavHost` from `androidx.navigation3`**: The Navigation3 version of NavHost
- **`composable` from `androidx.navigation3.compose`**: Navigation3's composable destination

### Migration Note:
If migrating from Navigation 2.x to Navigation3:
1. Update imports from `androidx.navigation.*` to `androidx.navigation3.*`
2. Add `windowAdaptiveInfo` parameter to `NavigationSuiteScaffold`
3. Update `NavHost` and `rememberNavController()` imports
4. Consider implementing `ListDetailPaneScaffold` for tablet-optimized layouts

## Key Dependencies

```kotlin
// libs.versions.toml
[versions]
kotlin = "1.9.22"
compose-bom = "2024.02.01"
hilt = "2.50"
room = "2.6.1"
coroutines = "1.7.3"
navigation3 = "1.4.0-beta01"
material3-adaptive = "1.0.0-beta01"

[libraries]
# Core dependencies
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
kotlinx-coroutines-android = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-android", version.ref = "coroutines" }

# Navigation3 dependencies
androidx-navigation3-compose = { group = "androidx.navigation3", name = "navigation3-compose", version.ref = "navigation3" }
androidx-material3-adaptive-navigation3 = { group = "androidx.compose.material3.adaptive", name = "adaptive-navigation3", version.ref = "material3-adaptive" }

# UI dependencies
androidx-compose-material3 = { group = "androidx.compose.material3", name = "material3", version.ref = "compose-bom" }
androidx-compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview", version.ref = "compose-bom" }
androidx-lifecycle-viewmodel-compose = { group = "androidx.lifecycle", name = "lifecycle-viewmodel-compose", version = "2.7.0" }

[bundles]
compose = [
    "androidx-compose-ui",
    "androidx-compose-ui-tooling-preview",
    "androidx-compose-material3",
    "androidx-compose-foundation"
]

navigation3 = [
    "androidx-navigation3-compose",
    "androidx-material3-adaptive-navigation3"
]

[plugins]
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
kotlin-kapt = { id = "org.jetbrains.kotlin.kapt", version.ref = "kotlin" }
```

## Build Configuration

Use convention plugins in `build-logic/` for consistent configuration:

### Convention Plugins:
- `AndroidApplicationConventionPlugin` - App module
- `AndroidLibraryConventionPlugin` - Core library modules
- `AndroidFeatureConventionPlugin` - Feature modules
- `AndroidComposeConventionPlugin` - Compose setup
- `AndroidHiltConventionPlugin` - Hilt setup
- `AndroidRoomConventionPlugin` - Room database setup

### Feature Module Build Configuration:
```kotlin
// build-logic/convention/src/main/kotlin/AndroidFeatureConventionPlugin.kt
class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
                apply("kotlin-kapt")
                apply("dagger.hilt.android.plugin")
            }
            
            extensions.configure<LibraryExtension> {
                configureAndroidCommon(this)
                defaultConfig {
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }
            }
            
            dependencies {
                add("implementation", project(":core:domain"))
                add("implementation", project(":core:ui"))
                add("implementation", libs.bundles.compose)
                add("implementation", libs.androidx.lifecycle.viewmodel.compose)
                add("implementation", libs.bundles.navigation3)
                add("implementation", libs.hilt.android)
                add("kapt", libs.hilt.compiler)
            }
        }
    }
}
```