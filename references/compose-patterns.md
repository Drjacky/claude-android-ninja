# Jetpack Compose Patterns

Modern UI patterns following Google's Material 3 guidelines with Navigation3, adaptive layouts, and our modular architecture.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

**Accessibility:** All UI components must be accessible. See `references/android-accessibility.md` for semantic properties, touch targets, and TalkBack support.

**Theming:** Use Material 3 theming with semantic color roles and typography. See `references/android-theming.md` for theme setup, dynamic colors, and dark/light mode.

**Internationalization:** Use string resources for all text. See `references/android-i18n.md` for localization, RTL support, and plurals.

## Table of Contents

1. [Screen Architecture](#screen-architecture)
2. [State Management](#state-management)
3. [Component Patterns](#component-patterns)
4. [Adaptive UI](#adaptive-ui)
5. [Theming & Design System](#theming--design-system)
6. [Previews & Testing](#previews--testing)
7. [Performance Optimization](#performance-optimization)
8. [Animation](#animation)

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
`references/android-navigation.md`.

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

### Edge-to-Edge (Mandatory on API 36)

Starting with Android 16 (API 36), edge-to-edge is mandatory and cannot be opted out of. The `R.attr#windowOptOutEdgeToEdgeEnforcement` attribute is deprecated and disabled. All apps must handle system bar insets properly.

```kotlin
// app/MainActivity.kt
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()

        setContent {
            AppTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    MainNavigation(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}
```

**Key requirements:**

- Call `enableEdgeToEdge()` in `onCreate()` before `setContent`
- Use `Scaffold` which provides `innerPadding` that accounts for system bars
- Apply `innerPadding` to your content to avoid overlap with status bar and navigation bar
- For scrollable content, use `Modifier.consumeWindowInsets()` and `Modifier.windowInsetsPadding()`
- For bottom sheets, FABs, and overlays, use `WindowInsets.navigationBars` or `WindowInsets.ime`

```kotlin
@Composable
fun ScrollableContentWithInsets(modifier: Modifier = Modifier) {
    LazyColumn(
        modifier = modifier,
        contentPadding = WindowInsets.systemBars.asPaddingValues()
    ) {
        items(100) { index ->
            Text("Item $index", modifier = Modifier.padding(16.dp))
        }
    }
}
```

**Do NOT:**

- Set `fitsSystemWindows` in XML
- Use `windowOptOutEdgeToEdgeEnforcement` -- it is disabled on API 36
- Assume the content area excludes system bars

### Predictive Back (Mandatory on API 36)

Starting with Android 16 (API 36), predictive back system animations are enabled by default. `onBackPressed` is no longer called and `KeyEvent.KEYCODE_BACK` is not dispatched.

**Migration requirements:**

- Use `BackHandler` from `androidx.activity.compose` for all back handling
- Use `OnBackInvokedCallback` for non-Compose Activity/Fragment code
- Do **not** set `android:enableOnBackInvokedCallback="false"` as a permanent fix -- this is only a temporary escape hatch
- Register back callbacks ahead of time so the system can play predictive animations

```kotlin
// Correct: Use BackHandler (Compose)
@Composable
fun MyScreen(onNavigateBack: () -> Unit) {
    BackHandler {
        onNavigateBack()
    }
    // Screen content
}
```

```kotlin
// Correct: OnBackInvokedCallback (non-Compose, API 33+)
class MyActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            onBackInvokedDispatcher.registerOnBackInvokedCallback(
                OnBackInvokedDispatcher.PRIORITY_DEFAULT
            ) {
                handleBack()
            }
        }
    }
}
```

**Do NOT:**

- Override `onBackPressed()` -- it is no longer called on API 36
- Dispatch `KeyEvent.KEYCODE_BACK` -- it is no longer dispatched
- Use `android:enableOnBackInvokedCallback="false"` as a permanent solution

### Adaptive Layouts (Mandatory on API 36 for Large Screens)

Starting with Android 16 (API 36), orientation, resizability, and aspect ratio restrictions are ignored on displays with smallest width >= 600dp. Apps fill the entire display window regardless of declared constraints.

**What is ignored on large screens:**

- `screenOrientation` manifest attribute
- `resizableActivity="false"`
- `minAspectRatio` / `maxAspectRatio`
- `setRequestedOrientation()` / `getRequestedOrientation()`

**Exceptions:**

- Games (based on `android:appCategory="game"`)
- Screens smaller than `sw600dp`

**Build adaptive layouts by default:**

- Use `WindowSizeClass` to adapt layouts to any screen size
- Use `NavigationSuiteScaffold` for responsive navigation (auto-switches bar/rail/drawer)
- Use `NavigableListDetailPaneScaffold` for list-detail patterns (built-in nav + predictive back)
- Use `NavigableSupportingPaneScaffold` for main + supporting content patterns
- Save and restore UI state properly -- rotation causes activity re-creation
- Test on tablets, foldables, and desktop windowing modes

**Dependencies** (all included in the `adaptive` bundle):

```kotlin
implementation(libs.bundles.adaptive)
```

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AdaptiveScreen(
    windowAdaptiveInfo: WindowAdaptiveInfo = currentWindowAdaptiveInfo()
) {
    val isCompact = windowAdaptiveInfo.windowSizeClass.widthSizeClass == WindowWidthSizeClass.Compact

    if (isCompact) {
        CompactLayout()
    } else {
        ExpandedLayout()
    }
}
```

### Handling System Back Button

Use `BackHandler` from `androidx.activity.compose` to intercept system back button presses in Compose:

```kotlin
@Composable
fun ImageDetailScreen(
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    var isZoomed by remember { mutableStateOf(false) }
    
    // Intercept back press when zoomed - exits zoom mode instead of screen
    BackHandler(enabled = isZoomed) {
        isZoomed = false
    }
    
    Column(modifier = modifier) {
        IconButton(onClick = onBackClick) {
            Icon(painterResource(R.drawable.ic_back), "Back")
        }
        
        ZoomableImage(
            isZoomed = isZoomed,
            onZoomChange = { isZoomed = it }
        )
    }
}
```

**Common Use Cases:**

1. **Unsaved Changes Warning**

```kotlin
@Composable
fun FormScreen(
    viewModel: FormViewModel,
    onNavigateBack: () -> Unit
) {
    val hasUnsavedChanges by viewModel.hasUnsavedChanges.collectAsStateWithLifecycle()
    var showExitDialog by remember { mutableStateOf(false) }
    
    BackHandler(enabled = hasUnsavedChanges) {
        showExitDialog = true
    }
    
    if (showExitDialog) {
        AlertDialog(
            onDismissRequest = { showExitDialog = false },
            title = { Text("Unsaved Changes") },
            text = { Text("Are you sure you want to exit without saving?") },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.discardChanges()
                    onNavigateBack()
                }) {
                    Text("Discard")
                }
            },
            dismissButton = {
                TextButton(onClick = { showExitDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
    
    FormContent(viewModel = viewModel)
}
```

1. **Multi-Step Flow Navigation**

```kotlin
@Composable
fun OnboardingScreen(
    onComplete: () -> Unit,
    onCancel: () -> Unit
) {
    var currentStep by remember { mutableStateOf(0) }
    
    // Navigate to previous step on back press, exit on first step
    BackHandler {
        if (currentStep > 0) {
            currentStep--
        } else {
            onCancel()
        }
    }
    
    when (currentStep) {
        0 -> WelcomeStep(onNext = { currentStep++ })
        1 -> PermissionsStep(onNext = { currentStep++ }, onBack = { currentStep-- })
        2 -> PreferencesStep(onNext = onComplete, onBack = { currentStep-- })
    }
}
```

1. **Bottom Sheet or Modal State**

```kotlin
@Composable
fun ScreenWithSheet(
    onNavigateBack: () -> Unit
) {
    var showBottomSheet by remember { mutableStateOf(false) }
    
    // Close bottom sheet on back press instead of exiting screen
    BackHandler(enabled = showBottomSheet) {
        showBottomSheet = false
    }
    
    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { showBottomSheet = true }) {
                Icon(painterResource(R.drawable.ic_filter), "Filter")
            }
        }
    ) { padding ->
        ContentList(modifier = Modifier.padding(padding))
        
        if (showBottomSheet) {
            ModalBottomSheet(onDismissRequest = { showBottomSheet = false }) {
                FilterContent()
            }
        }
    }
}
```

**Key Points:**

- **Nested handlers**: Innermost enabled `BackHandler` takes precedence
- **Conditional interception**: Use `enabled` parameter to control when back is intercepted
- **Lifecycle-aware**: Automatically cleaned up when composable leaves composition
- **Don't block permanently**: Always provide a way to exit the screen eventually

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

### Adaptive Navigation with NavigationSuiteScaffold

`NavigationSuiteScaffold` automatically switches between bottom navigation bar, navigation rail, and navigation drawer based on `WindowSizeClass`. Do NOT manually branch on window size class -- the scaffold handles it.

```kotlin
// app/AdaptiveAppNavigation.kt
@Composable
fun AdaptiveAppNavigation() {
    var currentDestination by rememberSaveable { mutableStateOf(AppDestinations.HOME) }

    NavigationSuiteScaffold(
        navigationSuiteItems = {
            AppDestinations.entries.forEach { destination ->
                item(
                    icon = { Icon(destination.icon, contentDescription = stringResource(destination.contentDescription)) },
                    label = { Text(stringResource(destination.label)) },
                    selected = destination == currentDestination,
                    onClick = { currentDestination = destination }
                )
            }
        }
    ) {
        when (currentDestination) {
            AppDestinations.HOME -> HomeScreen()
            AppDestinations.FAVORITES -> FavoritesScreen()
            AppDestinations.SETTINGS -> SettingsScreen()
        }
    }
}

enum class AppDestinations(
    @StringRes val label: Int,
    val icon: ImageVector,
    @StringRes val contentDescription: Int
) {
    HOME(R.string.home, Icons.Default.Home, R.string.home),
    FAVORITES(R.string.favorites, Icons.Default.Favorite, R.string.favorites),
    SETTINGS(R.string.settings, Icons.Default.Settings, R.string.settings),
}
```

To override the navigation type for specific cases (e.g., permanent drawer on expanded):

```kotlin
val adaptiveInfo = currentWindowAdaptiveInfo()
val customNavSuiteType = with(adaptiveInfo) {
    if (windowSizeClass.isWidthAtLeastBreakpoint(WIDTH_DP_EXPANDED_LOWER_BOUND)) {
        NavigationSuiteType.NavigationDrawer
    } else {
        NavigationSuiteScaffoldDefaults.calculateFromAdaptiveInfo(adaptiveInfo)
    }
}

NavigationSuiteScaffold(
    navigationSuiteItems = { /* ... */ },
    layoutType = customNavSuiteType,
) {
    // Content
}
```

### List-Detail Layout (NavigableListDetailPaneScaffold)

Use `NavigableListDetailPaneScaffold` instead of raw `ListDetailPaneScaffold` -- it provides built-in navigation and predictive back handling.

- On expanded screens: list and detail side by side
- On compact/medium: one pane at a time with navigation between them

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AuthSessionListDetailLayout(
    viewModel: AuthSessionViewModel = hiltViewModel()
) {
    val authEvents by viewModel.events.collectAsStateWithLifecycle()
    val scaffoldNavigator = rememberListDetailPaneScaffoldNavigator<AuthEvent>()

    NavigableListDetailPaneScaffold(
        navigator = scaffoldNavigator,
        listPane = {
            AnimatedPane {
                LazyColumn {
                    items(authEvents) { event ->
                        AuthEventListItem(
                            event = event,
                            onClick = {
                                viewModel.selectEvent(event)
                                scaffoldNavigator.navigateTo(
                                    ListDetailPaneScaffoldRole.Detail,
                                    contentKey = event
                                )
                            }
                        )
                    }
                }
            }
        },
        detailPane = {
            AnimatedPane {
                scaffoldNavigator.currentDestination?.contentKey?.let { event ->
                    AuthEventDetailScreen(event = event)
                }
            }
        }
    )
}
```

For custom back behavior or more control, use `SupportingPaneScaffold` / `ListDetailPaneScaffold` directly with `ThreePaneScaffoldPredictiveBackHandler`:

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun CustomListDetailLayout() {
    val scaffoldNavigator = rememberListDetailPaneScaffoldNavigator<String>()

    ThreePaneScaffoldPredictiveBackHandler(
        navigator = scaffoldNavigator,
        backBehavior = BackNavigationBehavior.PopUntilScaffoldValueChange
    )

    ListDetailPaneScaffold(
        directive = scaffoldNavigator.scaffoldDirective,
        scaffoldState = scaffoldNavigator.scaffoldState,
        listPane = {
            AnimatedPane { /* list content */ }
        },
        detailPane = {
            AnimatedPane { /* detail content */ }
        }
    )
}
```

### Supporting Pane Layout (NavigableSupportingPaneScaffold)

Use `NavigableSupportingPaneScaffold` to display a main content pane with a contextual supporting pane. The supporting pane shows related info (e.g., similar items, metadata, tools).

- On expanded screens: main and supporting panes side by side
- On compact/medium: one pane at a time with navigation

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun MovieDetailWithSuggestions(movie: Movie) {
    val scaffoldNavigator = rememberSupportingPaneScaffoldNavigator()
    val scope = rememberCoroutineScope()

    NavigableSupportingPaneScaffold(
        navigator = scaffoldNavigator,
        mainPane = {
            AnimatedPane(modifier = Modifier.safeContentPadding()) {
                MovieDetailContent(
                    movie = movie,
                    onShowSuggestions = {
                        scope.launch {
                            scaffoldNavigator.navigateTo(SupportingPaneScaffoldRole.Supporting)
                        }
                    },
                    isSupportingPaneVisible = scaffoldNavigator.scaffoldValue[SupportingPaneScaffoldRole.Supporting] != PaneAdaptedValue.Hidden
                )
            }
        },
        supportingPane = {
            AnimatedPane(modifier = Modifier.safeContentPadding()) {
                Column {
                    if (scaffoldNavigator.scaffoldValue[SupportingPaneScaffoldRole.Supporting] == PaneAdaptedValue.Expanded) {
                        IconButton(
                            modifier = Modifier.align(Alignment.End).padding(16.dp),
                            onClick = {
                                scope.launch {
                                    scaffoldNavigator.navigateBack(BackNavigationBehavior.PopUntilScaffoldValueChange)
                                }
                            }
                        ) {
                            Icon(Icons.Default.Close, contentDescription = "Close")
                        }
                    }
                    SimilarMoviesList(movieId = movie.id)
                }
            }
        }
    )
}
```

### Extracting Pane Composables

Extract panes into separate composables using `ThreePaneScaffoldPaneScope` for reusability and testability:

```kotlin
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun ThreePaneScaffoldPaneScope.MainPane(
    showSupportingButton: Boolean,
    onNavigateToSupporting: () -> Unit,
    modifier: Modifier = Modifier
) {
    AnimatedPane(modifier = modifier.safeContentPadding()) {
        if (showSupportingButton) {
            Button(onClick = onNavigateToSupporting) {
                Text("Show details")
            }
        }
    }
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

    // Status bar appearance is handled by enableEdgeToEdge() in MainActivity.
    // Do NOT manually set statusBarColor or isAppearanceLightStatusBars here.

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

**Important:** `@Immutable` and `@Stable` come from `androidx.compose.runtime`. To use them in domain models:

- **Option 1**: Make your domain module depend on `androidx.compose.runtime` (it's a Kotlin-only library, no Android dependencies):
  ```kotlin
  // core/domain/build.gradle.kts
  plugins {
      alias(libs.plugins.app.android.library)  // or app.jvm.library
  }

  dependencies {
      implementation(platform(libs.androidx.compose.bom))
      implementation(libs.androidx.compose.runtime)  // For @Immutable/@Stable
  }
  ```
- **Option 2**: Only annotate UI-layer models (e.g., `UserUi` in feature modules) and use a stability configuration file for domain models (see [android-strictmode.md](android-strictmode.md#compose-stability-guardrails))

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
| ------------------------------ | ------------ | --------------------------------------------------- |
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

## Animation

### State-Based Animations

#### animate*AsState

Animate individual properties by targeting a value. The animation runs when the target changes.

```kotlin
val size by animateDpAsState(
    targetValue = if (isExpanded) 200.dp else 100.dp,
    animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy),
    label = "size"
)

Box(modifier = Modifier.size(size))
```

Common variants:

```kotlin
val color by animateColorAsState(targetValue = targetColor, label = "color")
val alpha by animateFloatAsState(targetValue = if (visible) 1f else 0f, label = "alpha")
val offset by animateIntOffsetAsState(targetValue = IntOffset(10, 20), label = "offset")
```

Always provide the `label` parameter - it enables debugging in Layout Inspector and animation preview tools.

#### AnimatedVisibility

Controls appear/disappear animations with enter and exit transitions.

```kotlin
var visible by remember { mutableStateOf(true) }

AnimatedVisibility(
    visible = visible,
    enter = slideInHorizontally(initialOffsetX = { -it }) + fadeIn(),
    exit = slideOutHorizontally(targetOffsetX = { -it }) + fadeOut()
) {
    Text("Animated content")
}
```

Built-in transitions (combine with `+`):

- `slideInVertically` / `slideOutVertically`
- `slideInHorizontally` / `slideOutHorizontally`
- `expandVertically` / `shrinkVertically`
- `expandHorizontally` / `shrinkHorizontally`
- `fadeIn` / `fadeOut`
- `scaleIn` / `scaleOut`

Custom animation specs per transition:

```kotlin
AnimatedVisibility(
    visible = visible,
    enter = slideInVertically(
        initialOffsetY = { fullHeight -> fullHeight },
        animationSpec = spring()
    ),
    exit = slideOutVertically(
        targetOffsetY = { fullHeight -> fullHeight },
        animationSpec = tween(durationMillis = 300)
    )
) {
    Box(Modifier.fillMaxWidth().height(100.dp).background(MaterialTheme.colorScheme.primary))
}
```

#### AnimatedContent

Replace content with smooth transitions between different states.

```kotlin
var count by remember { mutableIntStateOf(0) }

AnimatedContent(
    targetState = count,
    transitionSpec = {
        slideInVertically { it } + fadeIn() togetherWith
            slideOutVertically { -it } + fadeOut() using
            SizeTransform(clip = false)
    },
    label = "counter"
) { target ->
    Text("Count: $target", style = MaterialTheme.typography.headlineLarge)
}
```

`SizeTransform` animates container size smoothly during content changes. Use `togetherWith` to pair enter and exit transitions.

#### Crossfade

Simple content swap with fade effect. Lightweight alternative to `AnimatedContent` when you only need a fade.

```kotlin
var showFirst by remember { mutableStateOf(true) }

Crossfade(targetState = showFirst, label = "crossfade") { state ->
    if (state) {
        Text("First screen")
    } else {
        Text("Second screen")
    }
}
```

### Coordinated Animations

#### updateTransition

Coordinate multiple animated values with a single state change. All animations run in sync.

```kotlin
var expanded by remember { mutableStateOf(false) }
val transition = updateTransition(targetState = expanded, label = "expand")

val size by transition.animateDp(label = "size") { if (it) 200.dp else 100.dp }
val color by transition.animateColor(label = "color") {
    if (it) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
}
val cornerRadius by transition.animateDp(label = "corner") { if (it) 16.dp else 8.dp }

Box(
    modifier = Modifier
        .size(size)
        .clip(RoundedCornerShape(cornerRadius))
        .background(color)
        .clickable { expanded = !expanded }
)
```

Use for complex components with multiple animated properties that must stay synchronized.

#### rememberInfiniteTransition

Create looping animations for loading indicators and pulsing effects.

```kotlin
val infiniteTransition = rememberInfiniteTransition(label = "loading")

val alpha by infiniteTransition.animateFloat(
    initialValue = 0.3f,
    targetValue = 1f,
    animationSpec = infiniteRepeatable(
        animation = tween(1000),
        repeatMode = RepeatMode.Reverse
    ),
    label = "pulse"
)

Box(
    modifier = Modifier
        .size(48.dp)
        .alpha(alpha)
        .background(MaterialTheme.colorScheme.primary, CircleShape)
)
```

Runs continuously until the composable leaves composition.

### Imperative Animation Control

#### Animatable

Fine-grained animation control in coroutines. Use for gesture-driven animations and complex sequences.

```kotlin
val offsetX = remember { Animatable(0f) }

LaunchedEffect(shouldAnimate) {
    if (shouldAnimate) {
        offsetX.animateTo(
            targetValue = 300f,
            animationSpec = spring(dampingRatio = Spring.DampingRatioMediumBouncy)
        )
    } else {
        offsetX.snapTo(0f)
    }
}

Box(
    modifier = Modifier
        .size(100.dp)
        .graphicsLayer(translationX = offsetX.value)
        .background(MaterialTheme.colorScheme.primary)
)
```

Gesture-driven example with velocity:

```kotlin
val offsetX = remember { Animatable(0f) }

Box(
    modifier = Modifier
        .size(100.dp)
        .offset { IntOffset(offsetX.value.roundToInt(), 0) }
        .pointerInput(Unit) {
            detectHorizontalDragGestures(
                onDragEnd = {
                    scope.launch {
                        offsetX.animateTo(0f, animationSpec = spring())
                    }
                }
            ) { _, dragAmount ->
                scope.launch {
                    offsetX.snapTo(offsetX.value + dragAmount)
                }
            }
        }
        .background(MaterialTheme.colorScheme.primary)
)
```

### Animation Specifications


| Spec        | Use Case                                     | Parameters                    |
| ----------- | -------------------------------------------- | ----------------------------- |
| `spring`    | Interactive feedback, natural motion         | `dampingRatio`, `stiffness`   |
| `tween`     | Predictable timing, sequential animations    | `durationMillis`, `easing`    |
| `keyframes` | Complex choreography, frame-by-frame control | Values at specific timestamps |


```kotlin
// Spring - physics-based, no fixed duration (recommended for interactions)
spring(
    dampingRatio = Spring.DampingRatioMediumBouncy, // NoBouncy(1f), LowBouncy(0.75f), MediumBouncy(0.5f), HighBouncy(0.2f)
    stiffness = Spring.StiffnessLow // Low, Medium, MediumLow, High, VeryLow
)

// Tween - time-based with easing
tween(
    durationMillis = 300,
    easing = FastOutSlowInEasing // also: LinearEasing, EaseInOutCubic, EaseInQuad, EaseOutQuad
)

// Keyframes - exact values at timestamps
keyframes {
    durationMillis = 300
    0f at 0 using EaseInQuad
    0.5f at 150 using EaseOutQuad
    1f at 300
}
```

Prefer `spring` for user-driven interactions (feels natural, no fixed duration). Use `tween` for choreographed sequences with predictable timing.

### Layout Animations

#### animateContentSize

Smoothly animate container size when content changes. No explicit `AnimatedVisibility` or layout transitions needed.

```kotlin
var expanded by remember { mutableStateOf(false) }

Column(
    modifier = Modifier
        .animateContentSize(animationSpec = spring())
        .background(MaterialTheme.colorScheme.surfaceVariant, RoundedCornerShape(8.dp))
        .clickable { expanded = !expanded }
        .padding(16.dp)
) {
    Text("Header", style = MaterialTheme.typography.titleMedium)
    if (expanded) {
        Spacer(modifier = Modifier.height(8.dp))
        Text("Expanded content that appears with a smooth size animation.")
    }
}
```

#### animateItem in LazyLists

Animate item appearance, removal, and reordering. Requires stable keys.

```kotlin
LazyColumn {
    items(items, key = { it.id }) { item ->
        ItemRow(
            item = item,
            modifier = Modifier.animateItem()
        )
    }
}
```

`animateItem()` replaces the deprecated `animateItemPlacement()`. It automatically handles insert, remove, and reorder animations.

### Shared Element Transitions

Animate elements smoothly across screen transitions.

```kotlin
SharedTransitionLayout {
    AnimatedContent(targetState = showDetail, label = "shared") { isDetail ->
        if (isDetail) {
            DetailPane(
                sharedTransitionScope = this@SharedTransitionLayout,
                animatedVisibilityScope = this@AnimatedContent,
                onBack = { showDetail = false }
            )
        } else {
            ListPane(
                sharedTransitionScope = this@SharedTransitionLayout,
                animatedVisibilityScope = this@AnimatedContent,
                onItemClick = { showDetail = true }
            )
        }
    }
}
```

In list and detail screens, use the same key for matching elements:

```kotlin
// In ListPane
Image(
    painter = painterResource(R.drawable.photo),
    contentDescription = "Product photo",
    modifier = Modifier.sharedElement(
        state = rememberSharedContentState(key = "image-${item.id}"),
        animatedVisibilityScope = animatedVisibilityScope
    )
)

// In DetailPane - same key
Image(
    painter = painterResource(R.drawable.photo),
    contentDescription = "Product photo",
    modifier = Modifier.sharedElement(
        state = rememberSharedContentState(key = "image-${item.id}"),
        animatedVisibilityScope = animatedVisibilityScope
    )
)
```

- `sharedElement` - exact element matching (same content, animates position/size)
- `sharedBounds` - bounds morphing (different content, animates container bounds)

For navigation-specific shared element transitions with Navigation3, see `references/android-navigation.md`.

### graphicsLayer for Animation Performance

Use `graphicsLayer` for GPU-accelerated transforms that skip recomposition and relayout entirely.

```kotlin
// Good: GPU-accelerated, no recomposition or relayout
val offset by animateFloatAsState(targetValue = 100f, label = "offset")
Box(modifier = Modifier.graphicsLayer(translationX = offset))

// Bad: triggers relayout every frame
val offsetDp by animateDpAsState(targetValue = 100.dp, label = "offset")
Box(modifier = Modifier.offset(x = offsetDp))
```

Use `graphicsLayer` for:

- `translationX` / `translationY` - position
- `rotationX` / `rotationY` / `rotationZ` - rotation
- `scaleX` / `scaleY` - scale
- `alpha` - opacity

Use `Modifier.offset { }` (lambda version) as a middle ground - it defers reads to the layout phase, avoiding recomposition but still triggering relayout.

### Animation Anti-Patterns

```kotlin
// Bad: no animation on visibility change
if (visible) { Text("Content") }
// Good: animated
AnimatedVisibility(visible = visible) { Text("Content") }

// Bad: Animatable recreated every recomposition
val animatable = Animatable(0f)
// Good: wrapped in remember
val animatable = remember { Animatable(0f) }

// Bad: animating state in composition phase (infinite recomposition loop)
var position by remember { mutableFloatStateOf(0f) }
position += 10f
// Good: animate in a coroutine
LaunchedEffect(Unit) {
    repeat(10) { position += 10f; delay(16) }
}

// Bad: missing label (harder to debug in Layout Inspector)
val size by animateDpAsState(targetValue = 100.dp)
// Good: labeled
val size by animateDpAsState(targetValue = 100.dp, label = "card_size")
```

## Related Guides

- [Architecture Guide](architecture.md) - ViewModel patterns and state management
- [Modularization Guide](modularization.md) - Feature modules and dependency rules
- [Navigation Guide](android-navigation.md) - Navigation3 architecture and adaptive navigation
- [Android Accessibility](android-accessibility.md) - Semantic properties and TalkBack support
- [Android Theming](android-theming.md) - Material 3 theming, dynamic colors, typography
- [Android i18n](android-i18n.md) - Localization, RTL support, and string resources
- [Kotlin Patterns](kotlin-patterns.md) - Immutability and data class usage
- [Testing Guide](testing.md) - UI testing with Compose

