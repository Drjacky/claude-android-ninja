# Jetpack Compose Patterns

Modern UI patterns following Google's Material 3 guidelines with Navigation3, adaptive layouts, and our modular architecture.

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
@Composable
fun AuthRoute(
    onRegisterClick: () -> Unit,
    onForgotPasswordClick: () -> Unit,
    onLoginSuccess: (User) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    LaunchedEffect(uiState) {
        if (uiState is AuthUiState.Success) {
            onLoginSuccess((uiState as AuthUiState.Success).user)
        }
    }
    
    LoginScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onRegisterClick = onRegisterClick,
        onForgotPasswordClick = onForgotPasswordClick,
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

### Modern ViewModel with Form State

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
}
```

### State Collection with Lifecycle

```kotlin
@Composable
fun AuthRoute(viewModel: AuthViewModel = hiltViewModel()) {
    // Lifecycle-aware state collection
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Coroutine scope for handling actions
    val coroutineScope = rememberCoroutineScope()
    
    LoginScreen(
        uiState = uiState,
        onAction = { action ->
            coroutineScope.launch {
                viewModel.onAction(action)
            }
        },
        onRegisterClick = { viewModel.onAction(AuthAction.RegisterClicked) },
        onForgotPasswordClick = { viewModel.onAction(AuthAction.ForgotPasswordClicked) }
    )
}
```

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
            key = { it.hashCode() }
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
        
        // Load more trigger
        item {
            LaunchedEffect(Unit) {
                onLoadMore()
            }
        }
    }
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
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
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
                        onClick = {
                            // Update detail pane
                        }
                    )
                }
            }
        },
        detailPane = {
            // Detail view - shows selected event
            AuthEventDetailScreen(
                event = selectedEvent,
                onBackClick = {
                    // Handle back navigation in detail pane
                }
            )
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
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = darkTheme
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
            key = { it.hashCode() } // Essential for stable keys
        ) { event ->
            val title by remember(event) {
                derivedStateOf { formatAuthEventTitle(event) }
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

```kotlin
@Composable
fun AuthEventCardOptimized(
    event: AuthEvent,
    onClick: (AuthEvent) -> Unit,
    modifier: Modifier = Modifier
) {
    // Use rememberUpdatedState for lambdas that change
    val currentOnClick by rememberUpdatedState(onClick)
    
    // Memoize expensive callbacks
    val onClickMemoized = remember(event) {
        { currentOnClick(event) }
    }
    
    Card(
        onClick = onClickMemoized,
        modifier = modifier
    ) {
        // Card content...
    }
}
```