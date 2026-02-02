# Jetpack Compose Patterns

Modern UI patterns following Google's Material 3 guidelines with Navigation3, adaptive layouts, and our modular architecture.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

## Table of Contents
1. [Screen Architecture](#screen-architecture)
2. [State Management](#state-management)
3. [Component Patterns](#component-patterns)
4. [Adaptive UI](#adaptive-ui)
5. [Theming & Design System](#theming--design-system)
6. [Previews & Testing](#previews--testing)
7. [Performance Optimization](#performance-optimization)

## Screen Architecture

### Feature Screen Pattern

Separate navigation, state management, and pure UI concerns with our modular approach:

```kotlin
// feature-auth/presentation/AuthRoute.kt
// Note: AuthNavigator is defined in feature-auth/navigation/AuthNavigator.kt
// and implemented in the app module. See references/modularization.md
@Composable
fun AuthRoute(
    authNavigator: AuthNavigator,
    modifier: Modifier = Modifier,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Collect one-time navigation events
    LaunchedEffect(viewModel) {
        viewModel.navigationEvents.collect { event ->
            when (event) {
                is AuthNavigationEvent.LoginSuccess -> authNavigator.navigateToMainApp()
                is AuthNavigationEvent.RegisterSuccess -> authNavigator.navigateToMainApp()
            }
        }
    }
    
    LoginScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onRegisterClick = authNavigator::navigateToRegister,
        onForgotPasswordClick = authNavigator::navigateToForgotPassword,
        modifier = modifier
    )
}

// feature-auth/presentation/LoginScreen.kt
@Composable
fun LoginScreen(
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
            is AuthUiState.Error -> ErrorContent(uiState.message, uiState.canRetry) {
                onAction(AuthAction.Retry)
            }
            else -> Unit
        }
    }
}
```

### Benefits with Our Architecture:
- **Feature Isolation**: Screens are self-contained within feature modules
- **Testable Components**: Pure UI without ViewModel dependencies
- **Navigation Decoupling**: Screens call Navigator interfaces, not NavController directly
- **Lifecycle Awareness**: Built-in support with `collectAsStateWithLifecycle()`
- **Adaptive Ready**: Designed for `NavigationSuiteScaffold` and responsive layouts

Navigation setup, destination definitions, and navigator interfaces live in
`references/modularization.md`.

## State Management

### Sealed Interface for UI State

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

### Actions Pattern for User Interactions

```kotlin
// feature-auth/presentation/viewmodel/AuthActions.kt
sealed class AuthAction {
    // Login form actions
    data class EmailChanged(val email: String) : AuthAction()
    data class PasswordChanged(val password: String) : AuthAction()
    data object LoginClicked : AuthAction()
    data object ShowRegisterForm : AuthAction()
    data object ShowForgotPasswordForm : AuthAction()
    
    // Register form actions
    data class NameChanged(val name: String) : AuthAction()
    data class ConfirmPasswordChanged(val confirmPassword: String) : AuthAction()
    data object RegisterSubmit : AuthAction()
    data object ShowLoginForm : AuthAction()
    
    // Forgot password actions
    data object ResetPasswordClicked : AuthAction()
    
    // Error handling
    data object Retry : AuthAction()
    data object ClearError : AuthAction()
}
```

### Modern ViewModel with Form State

Use delegation for shared behavior (validation, analytics, feature flags) instead of base classes.
See `references/kotlin-delegation.md` for guidance and tradeoffs.

For process-death survival, include `SavedStateHandle` in ViewModels and persist critical UI state (forms, in-progress flows) using `savedStateHandle.getStateFlow()` for automatic restoration.

```kotlin
// feature-auth/presentation/viewmodel/AuthViewModel.kt
interface AuthFormValidator {
    fun validateEmail(email: String): String?
    fun validatePassword(password: String): String?
}

class DefaultAuthFormValidator @Inject constructor() : AuthFormValidator {
    override fun validateEmail(email: String): String? =
        if (email.contains("@")) null else "Invalid email"

    override fun validatePassword(password: String): String? =
        if (password.length >= 8) null else "Password too short"
}

// Navigation events (one-time events)
// These are internal to the feature and trigger navigation via AuthNavigator
sealed interface AuthNavigationEvent {
    data object LoginSuccess : AuthNavigationEvent
    data object RegisterSuccess : AuthNavigationEvent
}

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val registerUseCase: RegisterUseCase,
    private val resetPasswordUseCase: ResetPasswordUseCase,
    private val savedStateHandle: SavedStateHandle,
    validator: AuthFormValidator
) : ViewModel(), AuthFormValidator by validator {

    // UI State
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.LoginForm())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    // One-time navigation events (SharedFlow with no replay)
    private val _navigationEvents = MutableSharedFlow<AuthNavigationEvent>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val navigationEvents: SharedFlow<AuthNavigationEvent> = _navigationEvents.asSharedFlow()
    
    // Process-death survival: persist form state
    private val email = savedStateHandle.getStateFlow("email", "")
    
    init {
        // Restore email if saved
        if (email.value.isNotEmpty()) {
            _uiState.update { state ->
                if (state is AuthUiState.LoginForm) {
                    state.copy(email = email.value)
                } else state
            }
        }
    }
    
    fun onAction(action: AuthAction) {
        when (action) {
            is AuthAction.EmailChanged -> {
                savedStateHandle["email"] = action.email
                updateLoginForm {
                    it.copy(
                        email = action.email,
                        emailError = validateEmail(action.email)
                    )
                }
            }
            is AuthAction.PasswordChanged -> updateLoginForm {
                it.copy(
                    password = action.password,
                    passwordError = validatePassword(action.password)
                )
            }
            AuthAction.LoginClicked -> performLogin()
            AuthAction.ShowForgotPasswordForm -> _uiState.value = AuthUiState.ForgotPasswordForm()
            AuthAction.ShowRegisterForm -> _uiState.value = AuthUiState.RegisterForm()
            is AuthAction.NameChanged -> updateRegisterForm { it.copy(name = action.name) }
            is AuthAction.ConfirmPasswordChanged -> updateRegisterForm {
                it.copy(confirmPassword = action.confirmPassword)
            }
            AuthAction.RegisterSubmit -> performRegistration()
            AuthAction.ShowLoginForm -> _uiState.value = AuthUiState.LoginForm()
            AuthAction.ResetPasswordClicked -> performPasswordReset()
            AuthAction.Retry -> _uiState.value = AuthUiState.LoginForm()
            AuthAction.ClearError -> _uiState.value = AuthUiState.LoginForm()
        }
    }
    
    private fun performLogin() {
        val currentState = _uiState.value as? AuthUiState.LoginForm ?: return
        
        viewModelScope.launch {
            _uiState.update { AuthUiState.Loading }
            
            loginUseCase(currentState.email, currentState.password).fold(
                onSuccess = { user -> 
                    // Emit navigation event - AuthRoute will call authNavigator.navigateToMainApp()
                    _navigationEvents.emit(AuthNavigationEvent.LoginSuccess)
                },
                onFailure = { error ->
                    _uiState.update { 
                        AuthUiState.Error(error.message ?: "Login failed", canRetry = true)
                    }
                }
            )
        }
    }
    
    // Other helper methods omitted for brevity (updateLoginForm, updateRegisterForm, etc.)
}

### State Collection with Lifecycle

```kotlin
@Composable
fun AuthRoute(
    authNavigator: AuthNavigator,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Collect one-time navigation events
    LaunchedEffect(viewModel) {
        viewModel.navigationEvents.collect { event ->
            when (event) {
                is AuthNavigationEvent.LoginSuccess -> authNavigator.navigateToMainApp()
                is AuthNavigationEvent.RegisterSuccess -> authNavigator.navigateToMainApp()
            }
        }
    }
    
    LoginScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onRegisterClick = authNavigator::navigateToRegister,
        onForgotPasswordClick = authNavigator::navigateToForgotPassword
    )
}
```

### Lifecycle-Aware Flow Collection for Side Effects

Use `collectAsStateWithLifecycle()` for state observation. For side effects (toasts, analytics, dialogs) that cannot use state, collect flows inside `LaunchedEffect` with lifecycle awareness.

```kotlin
@Composable
fun AuthScreen(
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    // For single flow: use flowWithLifecycle
    LaunchedEffect(viewModel.toastEvents, lifecycleOwner) {
        viewModel.toastEvents
            .flowWithLifecycle(lifecycleOwner.lifecycle, Lifecycle.State.STARTED)
            .collect { message ->
                Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
            }
    }

    LoginScreen(
        uiState = uiState,
        onAction = viewModel::onAction
    )
}
```

For multiple flows or complex scoped operations, use `repeatOnLifecycle`:

```kotlin
@Composable
fun AuthScreen(
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    // For multiple flows: use repeatOnLifecycle
    LaunchedEffect(lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            launch {
                viewModel.toastEvents.collect { message ->
                    Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
                }
            }
            
            launch {
                viewModel.analyticsEvents.collect { event ->
                    // Log analytics event
                }
            }
            
            launch {
                viewModel.dialogEvents.collect { dialog ->
                    // Show dialog based on event
                }
            }
        }
    }

    LoginScreen(
        uiState = uiState,
        onAction = viewModel::onAction
    )
}
```

Key points:
- Use `collectAsStateWithLifecycle()` for state that drives UI
- Use `flowWithLifecycle` for a single side-effect flow
- Use `repeatOnLifecycle` for multiple flows or complex scoped operations
- Both prevent leaked collectors and wasted background work during lifecycle changes

## Component Patterns

### Stateless, Reusable Components

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

### Adaptive List Components

```kotlin
// core/ui/components/AuthActivityList.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AuthActivityList(
    events: List<AuthEvent>,
    isLoadingMore: Boolean = false,
    onItemClick: (AuthEvent) -> Unit,
    onLoadMore: () -> Unit,
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo(),
    modifier: Modifier = Modifier
) {
    val isWideScreen = windowAdaptiveInfo.windowSizeClass.widthSizeClass != WindowWidthSizeClass.Compact
    
    LazyColumn(
        modifier = modifier,
        contentPadding = PaddingValues(horizontal = if (isWideScreen) 32.dp else 16.dp, vertical = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        items(
            items = events,
            key = { authEventKey(it) }
        ) { event ->
            AuthEventCard(
                event = event,
                onClick = { onItemClick(event) },
                modifier = Modifier.fillMaxWidth()
            )
        }
        
        if (isLoadingMore) {
            item {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(modifier = Modifier.size(48.dp))
                }
            }
        }
        
        // Load more trigger: only when not already loading and reached end
        if (!isLoadingMore && events.isNotEmpty()) {
            item {
                LaunchedEffect(events.size) {
                    onLoadMore()
                }
            }
        }
    }
}

private fun authEventKey(event: AuthEvent): String = when (event) {
    is AuthEvent.SessionRefreshed -> "refreshed-${event.timestamp}"
    is AuthEvent.SessionExpired -> "expired-${event.reason}"
    is AuthEvent.Error -> "error-${event.message}-${event.retryable}"
}
```

### Shared Loading & Error States

```kotlin
// core/ui/components/loading/
@Composable
fun LoadingScreen(
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            CircularProgressIndicator()
            Text(
                text = "Loading...",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
fun ErrorContent(
    message: String,
    canRetry: Boolean,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = message,
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center
            )
            
            if (canRetry) {
                Button(onClick = onRetry) {
                    Text("Retry")
                }
            }
        }
    }
}
```

## Adaptive UI

### Responsive Layouts with Navigation3

```kotlin
// app/AdaptiveAppNavigation.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AdaptiveAppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    
    // Choose appropriate scaffold based on screen size
    when (windowAdaptiveInfo.windowSizeClass.widthSizeClass) {
        WindowWidthSizeClass.Compact -> {
            // Mobile: Bottom navigation
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Compact navigation items
                }
            ) {
                // NavHost content
            }
        }
        WindowWidthSizeClass.Medium -> {
            // Tablet: Navigation rail
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Medium navigation items
                }
            ) {
                // NavHost content
            }
        }
        WindowWidthSizeClass.Expanded -> {
            // Desktop: Navigation drawer
            NavigationSuiteScaffold(
                state = rememberNavigationSuiteScaffoldState(),
                windowAdaptiveInfo = windowAdaptiveInfo,
                navigationSuiteItems = {
                    // Expanded navigation items
                }
            ) {
                // NavHost content
            }
        }
    }
}
```

### List-Detail Layouts for Tablets

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AuthSessionListDetailLayout(
    viewModel: AuthSessionViewModel = hiltViewModel(),
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
    val authEvents by viewModel.events.collectAsStateWithLifecycle()
    val selectedEvent by viewModel.selectedEvent.collectAsStateWithLifecycle()
    val listDetailPaneScaffoldState = rememberListDetailPaneScaffoldState()
    
    ListDetailPaneScaffold(
        state = listDetailPaneScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        listPane = {
            // List view - session/activity list
            LazyColumn {
                items(authEvents) { event ->
                    AuthEventListItem(
                        event = event,
                        onClick = { viewModel.selectEvent(event) }
                    )
                }
            }
        },
        detailPane = {
            // Detail view - shows selected event
            selectedEvent?.let { event ->
                AuthEventDetailScreen(
                    event = event,
                    onBackClick = { viewModel.clearSelection() }
                )
            }
        }
    )
}
```

## Theming & Design System

### Modern Material 3 Theme

```kotlin
// core/ui/theme/AppTheme.kt
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            // Use surface color for natural look
            window.statusBarColor = colorScheme.surface.toArgb()
            // Light status bar icons for light theme, dark icons for dark theme
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }
    
    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### Custom Design Tokens

```kotlin
// core/ui/theme/AppTypography.kt
val AppTypography = Typography(
    displayLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 57.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp,
    ),
    displayMedium = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 45.sp,
        lineHeight = 52.sp,
        letterSpacing = 0.sp,
    ),
    displaySmall = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.W400,
        fontSize = 36.sp,
        lineHeight = 44.sp,
        letterSpacing = 0.sp,
    ),
    // Add other text styles...
)
```

### Component-Specific Themes

```kotlin
// core/ui/components/ButtonStyles.kt
@Composable
fun PrimaryButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    text: @Composable () -> Unit,
    icon: @Composable (() -> Unit)? = null
) {
    Button(
        onClick = onClick,
        modifier = modifier,
        enabled = enabled,
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary
        ),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary),
        contentPadding = PaddingValues(horizontal = 24.dp, vertical = 12.dp)
    ) {
        if (icon != null) {
            icon()
            Spacer(modifier = Modifier.width(8.dp))
        }
        text()
    }
}
```

## Previews & Testing

### Comprehensive Preview Setup

```kotlin
// Preview annotations for different configurations
@Preview(name = "Light Mode")
@Preview(name = "Dark Mode", uiMode = Configuration.UI_MODE_NIGHT_YES)
annotation class ThemePreviews

@Preview(name = "Phone", device = Devices.PHONE)
@Preview(name = "Tablet", device = Devices.TABLET)
@Preview(name = "Desktop", device = Devices.DESKTOP)
annotation class DevicePreviews

@Preview(name = "English", locale = "en")
@Preview(name = "Arabic", locale = "ar")
annotation class LocalePreviews
```

### Preview with Realistic Data

```kotlin
// feature-auth/presentation/preview/LoginScreenPreview.kt
@ThemePreviews
@DevicePreviews
@Composable
fun LoginScreenPreview() {
    AppTheme {
        LoginScreen(
            uiState = AuthUiState.LoginForm(
                email = "user@example.com",
                password = "password123",
                isLoading = false
            ),
            onAction = { },
            onRegisterClick = { },
            onForgotPasswordClick = { },
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

### Preview Parameter Providers

```kotlin
class AuthUiStatePreviewParameterProvider : PreviewParameterProvider<AuthUiState> {
    override val values: Sequence<AuthUiState> = sequenceOf(
        AuthUiState.Loading,
        AuthUiState.LoginForm(),
        AuthUiState.ForgotPasswordForm(email = "user@example.com"),
        AuthUiState.Error(
            message = "Invalid credentials",
            canRetry = true
        )
    )
}

@ThemePreviews
@Composable
fun LoginScreenAllStatesPreview(
    @PreviewParameter(AuthUiStatePreviewParameterProvider::class) uiState: AuthUiState
) {
    AppTheme {
        LoginScreen(
            uiState = uiState,
            onAction = { },
            onRegisterClick = { },
            onForgotPasswordClick = { },
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

## Performance Optimization

### Stability Annotations: `@Immutable` vs `@Stable`

Compose can skip recomposition when inputs are stable. Use these annotations to help Compose's compiler understand stability contracts:

#### When to Use `@Immutable`

Use `@Immutable` when a type is **deeply immutable**: all properties are `val`, and all property types are primitives or also immutable. Once created, the object never changes.

```kotlin
// ✅ Correct: All properties are val and immutable
@Immutable
data class User(
    val id: String,
    val name: String,
    val email: String,
    val profileUrl: String?
)

// ✅ Correct: Nested types are also immutable
@Immutable
data class AuthState(
    val user: User?, // User is @Immutable
    val isLoading: Boolean,
    val error: String?
)

// ✅ Correct: Sealed class with immutable children
@Immutable
sealed interface UiState {
    data object Loading : UiState
    data class Success(val data: String) : UiState
    data class Error(val message: String) : UiState
}

// ❌ Wrong: Contains mutable property
@Immutable // This is a lie!
data class MutableUser(
    val id: String,
    var name: String // var makes this mutable
)

// ❌ Wrong: Contains mutable collection
@Immutable // This is a lie!
data class UserList(
    val users: MutableList<User> // Mutable collection
)
```

#### When to Use `@Stable`

Use `@Stable` when a type has **observable mutations**: it may be mutable, but Compose will be notified of all changes (e.g., via `mutableStateOf`, `StateFlow`, or MutableState).

```kotlin
// ✅ Correct: Mutable but observable by Compose
@Stable
class AuthFormState {
    var email by mutableStateOf("")
        private set
    
    var password by mutableStateOf("")
        private set
    
    var isLoading by mutableStateOf(false)
        private set
    
    fun updateEmail(value: String) {
        email = value
    }
    
    fun updatePassword(value: String) {
        password = value
    }
    
    fun setLoading(loading: Boolean) {
        isLoading = loading
    }
}

// ✅ Correct: Wraps StateFlow (observable)
@Stable
class SearchRepository @Inject constructor(
    private val api: SearchApi
) {
    private val _results = MutableStateFlow<List<SearchResult>>(emptyList())
    val results: StateFlow<List<SearchResult>> = _results.asStateFlow()
    
    suspend fun search(query: String) {
        _results.value = api.search(query)
    }
}

// ✅ Correct: Interface can be marked @Stable if implementations guarantee stability
// See references/crashlytics.md → "Provider-Agnostic Interface" for full implementation
@Stable
interface CrashReporter {
    fun log(message: String)
    fun recordException(throwable: Throwable)
}

// ❌ Wrong: Mutable and NOT observable by Compose
@Stable // This is a lie!
class BadFormState {
    var email: String = "" // No mutableStateOf - Compose won't see changes!
    var password: String = ""
}

// ❌ Wrong: Truly immutable, should use @Immutable instead
@Stable // Use @Immutable instead
data class Config(
    val apiUrl: String,
    val timeout: Int
)
```

#### Decision Matrix

| Type Characteristics           | Annotation   | Example                                             |
|--------------------------------|--------------|-----------------------------------------------------|
| All `val`, deeply immutable    | `@Immutable` | `data class User(val id: String, val name: String)` |
| Mutable with `mutableStateOf`  | `@Stable`    | `var count by mutableStateOf(0)`                    |
| Mutable with `StateFlow`       | `@Stable`    | `val state: StateFlow<T>`                           |
| Interface with stable contract | `@Stable`    | `interface Repository`                              |
| Regular mutable class          | **None**     | Let Compose treat as unstable                       |

#### Persistent Collections for Performance

For collections held in state, prefer persistent collections to enable structural sharing, so unchanged items and structure are reused and unaffected composables are not unnecessarily invalidated.

```kotlin
import kotlinx.collections.immutable.PersistentList
import kotlinx.collections.immutable.persistentListOf
import kotlinx.collections.immutable.toPersistentList

@Immutable
data class AuthEventUi(
    val id: String,
    val label: String
)

@HiltViewModel
class AuthEventsViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private val _events = MutableStateFlow<PersistentList<AuthEventUi>>(persistentListOf())
    val events: StateFlow<PersistentList<AuthEventUi>> = _events.asStateFlow()

    fun onEventAdded(event: AuthEventUi) {
        _events.update { it.add(event) } // Structural sharing - only new item allocated
    }

    fun onEventsLoaded(events: List<AuthEventUi>) {
        _events.value = events.toPersistentList()
    }
}
```

#### Key Rules

1. **Don't guess**: Only add annotations when you have **proven performance issues** (use Compose Compiler reports)
2. **Don't lie**: Never annotate a type as `@Immutable` or `@Stable` unless it truly meets the contract
3. **Domain models**: Always `@Immutable` (from `core/domain`)
4. **UI models**: Usually `@Immutable` (display-only data)
5. **ViewModels**: Never annotate (already stable via Hilt/Compose integration)
6. **Repositories**: Mark interface `@Stable` if implementations guarantee stability
7. **Form state classes**: Use `@Stable` with `mutableStateOf` properties

### Lazy Composition

```kotlin
@Composable
fun AuthActivityListOptimized(
    events: List<AuthEvent>,
    onItemClick: (AuthEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(
            items = events,
            key = { authEventKey(it) } // Essential for stable keys
        ) { event ->
            // Use remember for expensive computations
            val title = remember(event) { 
                formatAuthEventTitle(event) 
            }
            
            AuthEventCard(
                event = event,
                title = title,
                onClick = { onItemClick(event) }
            )
        }
    }
}
```

### State Hoisting for Performance

```kotlin
@Composable
fun SearchableAuthActivity(
    events: List<AuthEvent>,
    modifier: Modifier = Modifier
) {
    var searchQuery by remember { mutableStateOf("") }
    
    // Hoist expensive filtering
    val filteredEvents by remember(events, searchQuery) {
        derivedStateOf {
            if (searchQuery.isEmpty()) {
                events
            } else {
                events.filter { event ->
                    formatAuthEventTitle(event).contains(searchQuery, ignoreCase = true)
                }
            }
        }
    }
    
    Column(modifier = modifier) {
        SearchBar(
            query = searchQuery,
            onQueryChange = { searchQuery = it }
        )
        
        AuthActivityList(
            events = filteredEvents,
            onItemClick = { /* ... */ },
            onLoadMore = { /* ... */ }
        )
    }
}
```

### Remember/Lambda Best Practices

**Default approach (99% of cases):** Keep it simple. Let Compose handle optimizations automatically when your data types are stable/immutable.

```kotlin
@Composable
fun AuthEventCard(
    event: AuthEvent,  // Make sure AuthEvent is @Immutable
    onClick: (AuthEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    // Direct lambda is fine - no premature optimization needed
    Card(
        onClick = { onClick(event) },
        modifier = modifier
    ) {
        // Card content...
    }
}

// Ensure your data model is immutable for Compose stability
@Immutable
data class AuthEvent(
    val id: String,
    val name: String,
    val timestamp: Long
)
```

**When `onClick` changes frequently and performance matters (deeply nested/large lists):** Use `rememberUpdatedState` to always reference the latest callback without recreating the lambda.

```kotlin
@Composable
fun AuthEventCard(
    event: AuthEvent,
    onClick: (AuthEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    // Keeps reference to latest onClick without recreating lambda
    val currentOnClick by rememberUpdatedState(onClick)
    
    Card(
        onClick = { currentOnClick(event) },
        modifier = modifier
    ) {
        // Card content...
    }
}
```

**When both `event` and `onClick` change independently and you need true memoization (rare):**

```kotlin
@Composable
fun AuthEventCard(
    event: AuthEvent,
    onClick: (AuthEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    // Creates one lambda per unique (event, onClick) pair
    val onClickMemoized = remember(event, onClick) {
        { onClick(event) }
    }
    
    Card(
        onClick = onClickMemoized,
        modifier = modifier
    ) {
        // Card content...
    }
}
```

**Key takeaway:** Start simple. Only optimize if profiling shows actual performance issues. Premature optimization adds complexity without benefit.