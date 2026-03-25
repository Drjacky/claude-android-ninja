# Jetpack Compose Patterns

Modern UI patterns following Google's Material 3 guidelines with Navigation3, adaptive layouts, and our modular architecture.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

**Accessibility:** All UI components must be accessible. See `references/android-accessibility.md` for semantic properties, touch targets, and TalkBack support.

**Theming:** Use Material 3 theming with semantic color roles and typography. See `references/android-theming.md` for theme setup, dynamic colors, and dark/light mode.

**Internationalization:** Use string resources for all text. See `references/android-i18n.md` for localization, RTL support, and plurals.

## Table of Contents

1. [Screen Architecture](#screen-architecture)
2. [State Management](#state-management)
   - [Loading and refresh UX](#loading-and-refresh-ux)
3. [Component Patterns](#component-patterns)
4. [Adaptive UI](#adaptive-ui)
5. [Theming & Design System](#theming--design-system)
6. [Previews & Testing](#previews--testing)
7. [Performance Optimization](#performance-optimization)
8. [Animation](#animation)
9. [Side Effects](#side-effects)
10. [Modifiers](#modifiers)
11. [Deprecated Patterns & Migrations](#deprecated-patterns--migrations)
12. [CompositionLocal](#compositionlocal)
13. [Lists & Scrolling](#lists--scrolling)
14. [View Composition Rules](#view-composition-rules)
15. [Forms & Input](#forms--input)

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
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(viewModel.navigationEvents, lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.navigationEvents.collect { event ->
                when (event) {
                    is AuthNavigationEvent.LoginSuccess -> authNavigator.navigateToMainApp()
                    is AuthNavigationEvent.RegisterSuccess -> authNavigator.navigateToMainApp()
                }
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

## Naming Conventions

Follow these conventions when naming Compose functions:

### Components

Components are functions that emit UI elements.

- **Name:** `UpperCamelCase` (e.g., `FancyButton`, `ScrollAwareHeader`)
- **Return Type:** `Unit` (does not return a value)
- **Parameters:** Should have a `modifier` parameter at the first optional position
- **Usage:** Uses the `modifier` parameter at the top of the UI root

```kotlin
@Composable
fun FancyButton(
    text: String,
    modifier: Modifier = Modifier
) {
    Text(
        text = text,
        modifier = modifier
    )
}
```

### Factory Functions

Factory functions are used to create objects or state, usually involving `remember`.

- **Name:** `lowerCamelCase` (e.g., `defaultStyle`, `rememberCoroutineScope`)
- **Return Type:** Returns a result (e.g., `Style`, `CoroutineScope`)
- **UI Emission:** Does not emit UI
- **Usage:** Uses `@Composable` only if it needs to `remember` or use `CompositionLocal`

```kotlin
@Composable
fun defaultStyle(): Style = // ...

@Composable
fun rememberCoroutineScope(): CoroutineScope = // ...
```

## State Management

### Loading and refresh UX

Prefer **stable layout** and **preserved context** while data loads or refreshes. Users should not lose visible content, scroll position, or typed input because a network call started.

| Situation                                                  | Default                                                                                           |
|------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| First load, layout shape is known                          | Skeleton or placeholder in a **fixed-height** slot                                                |
| Refresh while previous data exists                         | Keep previous content; show **inline** progress (pull-to-refresh, small indicator on the section) |
| Recalculate / refine result while an older result is valid | Keep old result visible; show "updating" until the new payload arrives                            |
| Empty and idle                                             | Empty state copy, not a blocking spinner                                                          |
| Blocking work with **no** stable structure                 | Full-screen spinner is acceptable but should be rare                                              |

**Do not:** replace the whole screen with a spinner on every refresh, clear forms when a reload runs, or drop the last good result on transient errors.

```kotlin
// Bad - content disappears, layout jumps, user loses context
@Composable
fun SummarySection(summary: SummaryUi?, isLoading: Boolean) {
    if (isLoading) {
        CircularProgressIndicator()
    } else if (summary != null) {
        SummaryContent(summary = summary, refreshing = false)
    }
}

// Good - stable slot; previous data stays visible while refreshing
@Composable
fun SummarySection(summary: SummaryUi?, isLoading: Boolean) {
    SummaryCardSlot {
        when {
            summary != null -> SummaryContent(summary = summary, refreshing = isLoading)
            isLoading -> SummarySkeleton()
            else -> SummaryEmptyState()
        }
    }
}

@Composable
private fun SummaryCardSlot(content: @Composable BoxScope.() -> Unit) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 180.dp)
    ) {
        content()
    }
}
```

Model **refreshing** as a flag on the content state (e.g. `isRefreshing` on a data class) or a small overlay, not as a mode that **hides** the main UI unless there is nothing to show yet.

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
    
    // Recommended: One-time navigation events using SharedFlow
    private val _navigationEvents = MutableSharedFlow<AuthNavigationEvent>(
        replay = 0,
        extraBufferCapacity = 1,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val navigationEvents: SharedFlow<AuthNavigationEvent> = _navigationEvents.asSharedFlow()

    // Alternative: Using Channel for guaranteed delivery (buffers if no collectors)
    // private val _navigationEvents = Channel<AuthNavigationEvent>(Channel.BUFFERED)
    // val navigationEvents: Flow<AuthNavigationEvent> = _navigationEvents.receiveAsFlow()
    
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
                    _navigationEvents.emit(AuthNavigationEvent.LoginSuccess) // For SharedFlow
                    // _navigationEvents.send(AuthNavigationEvent.LoginSuccess) // For Channel
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
```

### Initial Data Load Strategies

There is no single "correct" answer for where initial load logic should live in Jetpack Compose-the decision depends on your specific constraints and context. Here are the four established patterns:

#### 1. ViewModel `init {}` Block
- **How it works:** Executes when the ViewModel is created.
- **Pros:** Decouples logic from the composable, making it more testable and reusable. Best when data is always needed.
- **Cons:** Limited control over re-triggering; harder to test timing.

```kotlin
class MyViewModel(private val repository: MyRepository) : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState = _uiState.asStateFlow()

    init {
        loadData()
    }

    private fun loadData() {
        viewModelScope.launch {
            _uiState.value = repository.getData()
        }
    }
}
```

#### 2. `LaunchedEffect(Unit)` in Composable
- **How it works:** Ties data fetching to the composable's composition lifecycle.
- **Pros:** Simple and intuitive with minimal boilerplate. Lifecycle-aware.
- **Cons:** Couples fetching logic to UI; risk of multiple triggers.

```kotlin
@Composable
fun MyScreen(viewModel: MyViewModel = hiltViewModel()) {
    LaunchedEffect(Unit) {
        viewModel.loadData() // Triggered when composable enters composition
    }
    
    // ... UI rendering
}
```

#### 3. `.onStart` + `stateIn` Pattern (Without Retry)
- **How it works:** A reactive approach using Flow operators, triggering on first collection.
- **Pros:** Excellent for handling configuration changes and persistent state. Fully reactive.
- **Cons:** Can be more complex to set up for simple one-shot loads. Lacks an easy way to retry failed requests.

```kotlin
class MyViewModel(repository: MyRepository) : ViewModel() {
    val uiState: StateFlow<UiState> = repository.dataFlow()
        .map { UiState.Success(it) }
        .onStart { emit(UiState.Loading) }
        .catch { emit(UiState.Error(it)) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UiState.Loading
        )
}
```

#### 4. Reactive Trigger / Action-driven (`flatMapLatest`) (With Retry)
- **How it works:** Uses a trigger state (e.g., a refresh counter or action intent) combined with `flatMapLatest` to fetch data.
- **Pros:** Makes retrying, pull-to-refresh, and error recovery trivial. Retains all the benefits of the reactive `.onStart` approach.
- **Cons:** Slightly more boilerplate than a simple `init` block or `.onStart`.

```kotlin
class MyViewModel(private val repository: MyRepository) : ViewModel() {
    // Trigger for initial load and subsequent retries/refreshes
    private val loadTrigger = MutableSharedFlow<Unit>(
        replay = 1, 
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )

    val uiState: StateFlow<UiState> = loadTrigger
        .onStart { emit(Unit) } // Fire initial load
        .flatMapLatest {
            repository.dataFlow()
                .map { UiState.Success(it) }
                .onStart { emit(UiState.Loading) }
                .catch { emit(UiState.Error(it)) }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = UiState.Loading
        )

    fun retry() {
        loadTrigger.tryEmit(Unit)
    }
}
```

#### Decision Framework
Choose your approach based on:
- **Retry logic / Pull-to-refresh:** Use the **Reactive Trigger (`flatMapLatest`)** approach (Pattern 4) if you anticipate needing to retry failed requests or support pull-to-refresh.
- **Screen complexity:** Reactive-heavy screens benefit from `.onStart + stateIn` (Pattern 3) or the Reactive Trigger approach (Pattern 4).
- **Configuration changes:** Prefer `ViewModel init` (Pattern 1) or `.onStart + stateIn` (Patterns 3 & 4) if data must persist across configuration changes without reloading.
- **Simplicity:** For simple, one-shot loads tied to the UI lifecycle without retries, `LaunchedEffect` (Pattern 2) is acceptable but often less robust than ViewModel-driven approaches.

### State Collection with Lifecycle

```kotlin
@Composable
fun AuthRoute(
    authNavigator: AuthNavigator,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Collect one-time navigation events using repeatOnLifecycle
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(viewModel.navigationEvents, lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.navigationEvents.collect { event ->
                when (event) {
                    is AuthNavigationEvent.LoginSuccess -> authNavigator.navigateToMainApp()
                    is AuthNavigationEvent.RegisterSuccess -> authNavigator.navigateToMainApp()
                }
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

### Primitive State Specializations

Avoid boxing overhead - use type-specific state holders:

```kotlin
var count by remember { mutableIntStateOf(0) }       // not mutableStateOf(0)
var progress by remember { mutableFloatStateOf(0f) }  // not mutableStateOf(0f)
var timestamp by remember { mutableLongStateOf(0L) }  // not mutableStateOf(0L)
var enabled by remember { mutableStateOf(true) }      // Boolean has no specialization
```

### snapshotFlow - Compose State to Flow

Converts Compose state reads into a Kotlin Flow. Use inside `LaunchedEffect` to react to state changes with Flow operators (debounce, distinctUntilChanged, filter).

```kotlin
@Composable
fun SearchScreen(viewModel: SearchViewModel) {
    var query by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        snapshotFlow { query }
            .debounce(300)
            .distinctUntilChanged()
            .collect { viewModel.search(it) }
    }

    TextField(value = query, onValueChange = { query = it })
}
```

```kotlin
// Bad: accessing state directly in LaunchedEffect doesn't track changes
LaunchedEffect(Unit) {
    viewModel.search(query) // captures initial value only
}

// Bad: using query as key restarts the entire effect on every keystroke
LaunchedEffect(query) {
    delay(300) // crude debounce, cancelled on every change
    viewModel.search(query)
}
```

### SnapshotStateList and SnapshotStateMap

Observable collections that trigger recomposition on structural changes.

```kotlin
val items = remember { mutableStateListOf<Item>() }
val cache = remember { mutableStateMapOf<String, User>() }

// These trigger recomposition:
items.add(Item(1, "First"))
items[0] = Item(1, "Updated")
items.removeAt(0)
cache["key"] = user
```

**Gotcha:** In-place mutation of elements does NOT trigger recomposition:

```kotlin
// Bad: mutating in place - Compose won't see the change
items[0].name = "Updated"

// Good: replace with copy
items[0] = items[0].copy(name = "Updated")
```

For ViewModel-level state, prefer `StateFlow<PersistentList<T>>` (see [Persistent Collections](#persistent-collections-for-performance)) over `SnapshotStateList`. Use `SnapshotStateList` only for UI-local state.

### remember, rememberSaveable, and rememberSerializable

These APIs differ in **how long** state is kept and **what types** you can store. Official overview: [State lifespans in Compose](https://developer.android.com/develop/ui/compose/state-lifespans).

|                                       | `remember`           | `rememberSaveable`                                                                                                                     | `rememberSerializable`                                                     |
|---------------------------------------|----------------------|----------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| Survives recompositions               | Yes                  | Yes                                                                                                                                    | Yes                                                                        |
| Survives activity / config recreation | No                   | Yes (restored value may be a **new** instance, `==` but not `===`)                                                                     | Same as `rememberSaveable`                                                 |
| Survives process death                | No                   | Yes                                                                                                                                    | Yes                                                                        |
| Custom / complex types                | Any (in memory only) | Primitives, `String`, arrays, built-in support for common types (`List`, `Map`, `State`, …), **`@Parcelize`**, or a **custom `Saver`** | Types you can represent with **`kotlinx.serialization`** (`@Serializable`) |

**When to use which**

- **`remember`** - Default for composable-scoped state that can be recreated without harming UX: animation state, internal helpers, `LazyListState` when you do not need process death, ephemeral expand/collapse, hover. **Do not** store irreplaceable user input or form data in plain `remember`; it is cleared on configuration change and process death.

- **`rememberSaveable`** - User-visible state the app cannot easily reload from elsewhere: text fields, toggles, scroll position, selected tab, navigation arguments mirrored in UI. Use this when your type is already `Parcelable`, fits the built-in `Saver` rules, or you hand-write a `Saver` / `mapSaver` / `listSaver`.

- **`rememberSerializable`** - Same persistence guarantees as `rememberSaveable`, but **automatic persistence for `@Serializable` models** via `kotlinx.serialization`. Prefer it when your domain or UI model is already (or can be) marked `@Serializable`; use **`rememberSaveable`** for primitives, `Parcelable`, or manual `Saver`s when you are not using kotlinx.serialization.

Both saveable variants serialize into a `Bundle`, so restored values are **equivalent** copies, not the same object identity.

#### rememberSaveable with custom types

`rememberSaveable` survives process death and configuration changes. Custom types need a `Saver`, `@Parcelize`, or supported primitives/collections:

```kotlin
// Option 1: Saver (pure Kotlin, no Android dependency)
data class FilterState(val category: String, val sortOrder: String)

val filterSaver = Saver<FilterState, List<String>>(
    save = { listOf(it.category, it.sortOrder) },
    restore = { FilterState(category = it[0], sortOrder = it[1]) }
)

var filter by rememberSaveable(stateSaver = filterSaver) {
    mutableStateOf(FilterState("all", "newest"))
}

// Option 2: @Parcelize (requires kotlin-parcelize plugin)
@Parcelize
data class FilterState(val category: String, val sortOrder: String) : Parcelable

var filter by rememberSaveable { mutableStateOf(FilterState("all", "newest")) }

// Option 3: mapSaver for quick key-value serialization
val filterSaver = mapSaver(
    save = { mapOf("category" to it.category, "sortOrder" to it.sortOrder) },
    restore = { FilterState(it["category"] as String, it["sortOrder"] as String) }
)
```

#### rememberSerializable with @Serializable types

Use when your state is modeled with kotlinx.serialization (same lifecycle as `rememberSaveable`; do not wrap the same state in both `rememberSaveable` and `rememberSerializable`). The `MutableState` overload infers a `KSerializer` for the reified type `T`:

```kotlin
import androidx.compose.runtime.saveable.rememberSerializable
import kotlinx.serialization.Serializable

@Serializable
data class FilterState(val category: String, val sortOrder: String)

var filter by rememberSerializable { mutableStateOf(FilterState("all", "newest")) }
```

For a non-state value, use the overload whose `init` returns `T` directly. If you need an explicit `KSerializer` (custom serializers, polymorphism, etc.), use the overloads that take `serializer:` or `stateSerializer:` - see [`rememberSerializable`](https://developer.android.com/reference/kotlin/androidx/compose/runtime/saveable/package-summary#rememberSerializable(kotlin.Array,kotlinx.serialization.KSerializer,androidx.savedstate.serialization.SavedStateConfiguration,kotlin.Function0)).

For other APIs that sit between these lifespans (for example **`retain`**, which survives configuration change but not process death), see the same [State lifespans](https://developer.android.com/develop/ui/compose/state-lifespans) guide.

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

### Touch Targets

Every interactive element must have a minimum touch area of **48x48dp**. If the visual element is
smaller, expand the touch area. Keep at least **8dp** between adjacent targets to prevent mis-taps.

```kotlin
IconButton(onClick = onClose) {
    Icon(Icons.Default.Close, contentDescription = "Close")
}

Box(
    modifier = Modifier
        .minimumInteractiveComponentSize()
        .clickable { onAction() },
    contentAlignment = Alignment.Center
) {
    Icon(modifier = Modifier.size(24.dp), imageVector = Icons.Default.Star, contentDescription = "Rate")
}
```

### Haptic Feedback

Use haptics to confirm significant actions - destructive operations, toggles, long-press confirmations:

```kotlin
@Composable
fun DeleteButton(onDelete: () -> Unit) {
    val haptic = LocalHapticFeedback.current
    Button(
        onClick = {
            haptic.performHapticFeedback(HapticFeedbackType.LongPress)
            onDelete()
        }
    ) {
        Text("Delete")
    }
}
```

Do not add haptics to every tap - reserve them for actions where physical confirmation improves UX.

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


| Type Characteristics           | Annotation   | Example                                                         |
|--------------------------------|--------------|-----------------------------------------------------------------|
| All `val`, deeply immutable    | `@Immutable` | `data class User(val id: String, val name: String)`             |
| Mutable with `mutableStateOf`  | `@Stable`    | `var count by mutableStateOf(0)`                                |
| Mutable with `StateFlow`       | `@Stable`    | `val state: StateFlow<T>`                                       |
| Interface with stable contract | `@Stable`    | `interface Repository`                                          |
| Regular mutable class          | **None**     | Let Compose treat as unstable                                   |
| `java.time` classes            | **None**     | `LocalDate`, `LocalTime`, `LocalDateTime` (Unstable by default) |

> **Warning:** Standard Java time classes like `LocalDate`, `LocalTime`, and `LocalDateTime` are considered **unstable** by Compose. If you use them in your state, you must either wrap them in a stable class, map them to primitives (like epoch milliseconds), or configure them as stable via a stability configuration file.


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

### Hoistable Stable State Pattern

For complex components, extract state into a hoistable stable state interface with a private implementation and a factory function. This allows callers to either provide their own state or let the component manage it.

```kotlin
@Stable
interface VerticalScrollerState {
    var scrollPosition: Int
    var scrollRange: Int
}

private class VerticalScrollerStateImpl(
    scrollPosition: Int = 0,
    scrollRange: Int = 0
) : VerticalScrollerState {
    private var _scrollPosition by mutableIntStateOf(scrollPosition)
    
    override var scrollRange by mutableIntStateOf(scrollRange)
    
    override var scrollPosition: Int
        get() = _scrollPosition
        set(value) {
            _scrollPosition = value.coerceIn(0, scrollRange)
        }
}

// Factory function
fun VerticalScrollerState(): VerticalScrollerState = VerticalScrollerStateImpl()

@Composable
fun VerticalScroller(
    modifier: Modifier = Modifier,
    state: VerticalScrollerState = remember { VerticalScrollerState() }
) {
    val scrollPosition = state.scrollPosition
    val scrollRange = state.scrollRange
    
    // Use state...
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

Animate a single property toward a target value. Restarts when the target changes.

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

Always provide `label` - required for debugging in Layout Inspector.

#### AnimatedVisibility

Enter/exit animations for showing and hiding content.

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

Per-transition animation specs:

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

Smooth transitions when swapping content based on state.

```kotlin
var count by remember { mutableIntStateOf(0) }

AnimatedContent(
    targetState = count,
    transitionSpec = {
        if (targetState > initialState) {
            slideInVertically { it } + fadeIn() togetherWith slideOutVertically { -it } + fadeOut()
        } else {
            slideInVertically { -it } + fadeIn() togetherWith slideOutVertically { it } + fadeOut()
        }.using(SizeTransform(clip = false))
    },
    label = "counter"
) { target ->
    Text("Count: $target", style = MaterialTheme.typography.headlineLarge)
}
```

`SizeTransform` animates container size during content changes. `togetherWith` pairs enter and exit transitions.

#### Crossfade

Fade-only content swap. Lightweight alternative to `AnimatedContent`.

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

Multiple animated values synchronized by a single state change.

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

#### rememberInfiniteTransition

Looping animations for loading indicators and pulsing effects.

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

Runs until composable leaves composition.

### Imperative Animation Control

#### Animatable

Coroutine-based animation control. Use for gesture-driven animations and complex sequences.

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

Gesture-driven:

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

Prefer `spring` for user-driven interactions. Use `tween` for choreographed sequences.

### Material Design motion (duration and easing)

Material motion uses consistent **durations** and **easing** so transitions feel intentional. Align `tween`/`keyframes` with these bands when you pick fixed timings (springs stay physics-driven).

**Durations by interaction type**

| Band   | Duration   | Typical use                                 |
|--------|------------|---------------------------------------------|
| Micro  | 50-100 ms  | Ripples, small state toggles, hover         |
| Short  | 100-200 ms | Simple transitions, fades                   |
| Medium | 200-300 ms | Expand/collapse, bottom sheet motion        |
| Long   | 300-500 ms | Larger choreography, complex screen changes |

Keep most UI transitions under about **400 ms** unless you are showing loading or long-form motion. Tablet/desktop can feel slightly slower; wearables often use shorter motion. See [Motion](https://m3.material.io/styles/motion/overview) for the full system.

**Easing roles** (Material names map to cubic-bezier curves in design specs; in Compose use `FastOutSlowInEasing`, `LinearEasing`, or custom `CubicBezierEasing` as needed)

| Role       | Typical use                  |
|------------|------------------------------|
| Standard   | Default enter/exit           |
| Emphasized | Prominent transitions        |
| Decelerate | Elements entering the screen |
| Accelerate | Elements leaving permanently |
| Sharp      | Temporary exit and return    |

**Reduced motion:** Always respect `LocalReducedMotion` for enter/exit (see **Animation Anti-Patterns** below).

### Layout Animations

#### animateContentSize

Automatic container size animation when content changes.

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

Animates item insert, remove, and reorder. Requires stable keys. Replaces deprecated `animateItemPlacement()`.

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

### Shared Element Transitions

Animate matching elements across screen transitions.

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

Both screens must use the same key:

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

- `sharedElement` - exact match (same content, animates position/size)
- `sharedBounds` - bounds morph (different content, animates container bounds)

For Navigation3-specific shared elements, see `references/android-navigation.md`.

### graphicsLayer for Animation Performance

GPU-accelerated transforms that skip recomposition and relayout.

```kotlin
// Good: GPU-accelerated, no recomposition or relayout
val offset by animateFloatAsState(targetValue = 100f, label = "offset")
Box(modifier = Modifier.graphicsLayer(translationX = offset))

// Bad: triggers relayout every frame
val offsetDp by animateDpAsState(targetValue = 100.dp, label = "offset")
Box(modifier = Modifier.offset(x = offsetDp))
```

`graphicsLayer` properties: `translationX/Y`, `rotationX/Y/Z`, `scaleX/Y`, `alpha`.

`Modifier.offset { }` (lambda version) is a middle ground - defers reads to layout phase, avoids recomposition but still triggers relayout.

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

// Bad: ignoring user's reduced motion preference
AnimatedVisibility(visible = visible, enter = fadeIn() + slideInVertically()) { Content() }
// Good: respect reduced motion
val reducedMotion = LocalReducedMotion.current
AnimatedVisibility(
    visible = visible,
    enter = if (reducedMotion) EnterTransition.None else fadeIn() + slideInVertically()
) { Content() }
```

## Side Effects

Use the correct effect for each scenario. Misuse causes stale state, resource leaks, or infinite recomposition loops.

**Execution order:** Composition -> Side effects -> Layout -> Drawing. Effects only run after successful composition.

### LaunchedEffect - Coroutines Scoped to Composition

Coroutine tied to composable lifecycle. Cancelled when the key changes or composable leaves composition.

```kotlin
@Composable
fun DataLoader(userId: String) {
    var data by remember { mutableStateOf<UserData?>(null) }

    LaunchedEffect(userId) {
        data = repository.loadUser(userId)
    }

    data?.let { UserContent(it) } ?: LoadingScreen()
}
```

#### Key Selection Rules

```kotlin
// Key = Unit: runs once when composable enters composition, never restarts
LaunchedEffect(Unit) {
    analytics.logScreenView("home")
}

// Key = specific value: restarts whenever the value changes
LaunchedEffect(userId) {
    data = repository.loadUser(userId)
}

// Multiple keys: restarts if ANY key changes
LaunchedEffect(userId, filterType) {
    data = repository.loadFiltered(userId, filterType)
}
```

#### Cancellation and Cleanup

When the key changes, the current coroutine is cancelled before the new one starts. Use `finally` for cleanup:

```kotlin
LaunchedEffect(connectionId) {
    val connection = openConnection(connectionId)
    try {
        connection.listen { message ->
            processMessage(message)
        }
    } finally {
        connection.close()
    }
}
```

### DisposableEffect - Resource Cleanup

Use for listeners, registrations, and resources that need explicit cleanup via `onDispose`.

```kotlin
@Composable
fun ScreenWithLifecycle(onResume: () -> Unit, onPause: () -> Unit) {
    val lifecycle = LocalLifecycleOwner.current.lifecycle

    DisposableEffect(lifecycle) {
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_RESUME -> onResume()
                Lifecycle.Event.ON_PAUSE -> onPause()
                else -> Unit
            }
        }
        lifecycle.addObserver(observer)

        onDispose {
            lifecycle.removeObserver(observer)
        }
    }
}
```

Prefer over `LaunchedEffect` when cleanup isn't coroutine-based (removing listeners, unregistering callbacks).

```kotlin
@Composable
fun BroadcastListener(context: Context, action: String, onReceive: (Intent) -> Unit) {
    DisposableEffect(action) {
        val receiver = object : BroadcastReceiver() {
            override fun onReceive(ctx: Context, intent: Intent) {
                onReceive(intent)
            }
        }
        val filter = IntentFilter(action)
        context.registerReceiver(receiver, filter)

        onDispose {
            context.unregisterReceiver(receiver)
        }
    }
}
```

### SideEffect - After Every Composition

Runs after *every* successful composition. No keys, no cleanup. Use sparingly.

```kotlin
@Composable
fun TrackScreenView(screenName: String) {
    SideEffect {
        analytics.logScreenView(screenName)
    }
}
```

Only for: analytics logging, synchronizing with non-Compose UI, one-way state sync without cleanup.
Never for: resource allocation (`DisposableEffect`) or coroutines (`LaunchedEffect`).

### rememberCoroutineScope - Launching from Event Handlers

Coroutine scope tied to composable lifecycle. Use for launching coroutines from callbacks (clicks, gestures) - not for state-driven work (use `LaunchedEffect` instead).

```kotlin
@Composable
fun SnackbarDemo(snackbarHostState: SnackbarHostState) {
    val scope = rememberCoroutineScope()

    Button(
        onClick = {
            scope.launch {
                snackbarHostState.showSnackbar("Action completed")
            }
        }
    ) {
        Text("Show Snackbar")
    }
}
```

```kotlin
// Bad: blocks UI thread
Button(onClick = {
    runBlocking { fetchData() }
}) { Text("Fetch") }

// Good: launches on proper scope
val scope = rememberCoroutineScope()
Button(onClick = {
    scope.launch { fetchData() }
}) { Text("Fetch") }
```

### rememberUpdatedState - Capturing Latest Values

Keeps a reference to the latest value without restarting a long-running effect.

```kotlin
@Composable
fun TimedMessage(
    message: String,
    onTimeout: () -> Unit,
    timeoutMillis: Long = 5000L
) {
    val currentOnTimeout by rememberUpdatedState(onTimeout)

    LaunchedEffect(timeoutMillis) {
        delay(timeoutMillis)
        currentOnTimeout()
    }
}
```

Without it, changing `onTimeout` either restarts the effect (if used as key) or calls a stale callback (if captured directly):

```kotlin
// Bad: effect restarts when onTimeout changes (common with lambda parameters)
LaunchedEffect(onTimeout) {
    delay(5000)
    onTimeout()
}

// Bad: captures initial onTimeout, ignores later changes
LaunchedEffect(Unit) {
    delay(5000)
    onTimeout() // stale reference
}
```

### produceState - Converting External State to Compose State

Converts imperative sources (callbacks, flows, suspend functions) into Compose `State`. Combines `remember` + `LaunchedEffect` + state creation.

```kotlin
@Composable
fun NetworkStatus(): State<Boolean> {
    val context = LocalContext.current

    return produceState(initialValue = true) {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) { value = true }
            override fun onLost(network: Network) { value = false }
        }

        val connectivityManager = context.getSystemService<ConnectivityManager>()
        connectivityManager?.registerDefaultNetworkCallback(callback)

        awaitDispose {
            connectivityManager?.unregisterNetworkCallback(callback)
        }
    }
}

@Composable
fun AppContent() {
    val isOnline by NetworkStatus()

    if (!isOnline) {
        OfflineBanner()
    }
}
```

Use `awaitDispose` for cleanup (equivalent to `onDispose` in `DisposableEffect`).

### LifecycleResumeEffect - onResume / onPause

Runs code when the `LifecycleOwner` reaches `RESUMED` state. Cleanup runs on `onPause` or when the composable leaves composition. Use for work that must only be active while the screen is visible and interactive.

```kotlin
@Composable
fun CameraPreview(cameraController: CameraController) {
    LifecycleResumeEffect(cameraController) {
        cameraController.startPreview()

        onPauseOrDispose {
            cameraController.stopPreview()
        }
    }

    // camera UI...
}
```

Common use cases:
- Start/stop camera or media playback
- Resume/pause sensor updates
- Register/unregister push notification listeners
- Analytics screen-view tracking (fires on return from background)

```kotlin
@Composable
fun ScreenAnalytics(screenName: String) {
    LifecycleResumeEffect(screenName) {
        analytics.logScreenView(screenName)

        onPauseOrDispose { }
    }
}
```

**Rule:** `onPauseOrDispose` block is mandatory - compiler enforces it.

### LifecycleStartEffect - onStart / onStop

Same pattern as `LifecycleResumeEffect` but maps to `STARTED` state. Runs on `onStart`, cleans up on `onStop` or dispose.

```kotlin
@Composable
fun LocationTracker(locationManager: LocationManager) {
    LifecycleStartEffect(Unit) {
        val listener = LocationListener { location -> updateMap(location) }
        locationManager.requestLocationUpdates(
            LocationManager.GPS_PROVIDER, 5000L, 10f, listener
        )

        onStopOrDispose {
            locationManager.removeUpdates(listener)
        }
    }
}
```

#### When to Use Which Lifecycle Effect

| Effect | Active During | Use For |
|--------|--------------|---------|
| `LifecycleResumeEffect` | `onResume` to `onPause` | Camera, media playback, interactive features |
| `LifecycleStartEffect` | `onStart` to `onStop` | Location, sensors, background-visible work |
| `DisposableEffect` | Composition to disposal | Not lifecycle-dependent, just composition-scoped |

**Rule:** Prefer `LifecycleResumeEffect`/`LifecycleStartEffect` over manually observing `LocalLifecycleOwner` with `DisposableEffect` + `LifecycleEventObserver`. They provide the same behavior with less boilerplate and no risk of forgetting cleanup.

```kotlin
// BAD: Manual lifecycle observer boilerplate
DisposableEffect(lifecycleOwner) {
    val observer = LifecycleEventObserver { _, event ->
        when (event) {
            Lifecycle.Event.ON_RESUME -> startCamera()
            Lifecycle.Event.ON_PAUSE -> stopCamera()
            else -> {}
        }
    }
    lifecycleOwner.lifecycle.addObserver(observer)
    onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
}

// GOOD: Dedicated lifecycle effect
LifecycleResumeEffect(Unit) {
    startCamera()
    onPauseOrDispose { stopCamera() }
}
```

### Effect Decision Guide


| Scenario                                            | Effect                        | Why                               |
| --------------------------------------------------- | ----------------------------- | --------------------------------- |
| Load data when key changes                          | `LaunchedEffect(key)`         | Coroutine restarts on key change  |
| One-time setup (analytics, logging)                 | `LaunchedEffect(Unit)`        | Runs once, no restart needed      |
| Register/unregister listener                        | `DisposableEffect(key)`       | Needs deterministic cleanup       |
| Work active only while resumed (camera, media)      | `LifecycleResumeEffect`       | Pauses on `onPause`, resumes on `onResume` |
| Work active while started (location, sensors)       | `LifecycleStartEffect`        | Stops on `onStop`, starts on `onStart` |
| Sync with external system after every recomposition | `SideEffect`                  | No keys, no cleanup               |
| Launch coroutine from click handler                 | `rememberCoroutineScope`      | Event-driven, not state-driven    |
| Keep latest callback in long-running effect         | `rememberUpdatedState`        | Avoid restart or stale capture    |
| Convert imperative source to Compose state          | `produceState`                | Bridges callback/suspend to State |


### Side Effect Anti-Patterns

```kotlin
// Bad: LaunchedEffect(Unit) when key should change - only loads first userId
@Composable
fun UserProfile(userId: String) {
    var user by remember { mutableStateOf<User?>(null) }
    LaunchedEffect(Unit) {
        user = repository.loadUser(userId) // never re-runs when userId changes
    }
}
// Good: use userId as key
LaunchedEffect(userId) {
    user = repository.loadUser(userId)
}

// Bad: forgetting onDispose (resource leak)
DisposableEffect(Unit) {
    val listener = Listener()
    manager.register(listener)
    // missing onDispose!
}
// Good: always clean up
DisposableEffect(Unit) {
    val listener = Listener()
    manager.register(listener)
    onDispose { manager.unregister(listener) }
}

// Bad: reading state directly in LaunchedEffect(Unit) - captures initial value only
var count by remember { mutableIntStateOf(0) }
LaunchedEffect(Unit) {
    delay(1000)
    println(count) // always prints 0
}
// Good: use snapshotFlow to observe state changes in effects
LaunchedEffect(Unit) {
    snapshotFlow { count }
        .collect { println("Count: $it") }
}

// Bad: navigating during composition (runs on every recomposition)
if (isLoggedIn) {
    navigator.navigateToHome()
}
// Good: navigate in a LaunchedEffect
LaunchedEffect(isLoggedIn) {
    if (isLoggedIn) {
        navigator.navigateToHome()
    }
}
```

## Modifiers

Modifiers apply layout, drawing, gesture, and accessibility behavior. **Order matters** - modifiers apply left-to-right in the chain.

### Modifier Chain Ordering

```kotlin
// Red background THEN padding THEN size - red fills behind padding
Box(
    Modifier
        .background(Color.Red)
        .padding(16.dp)
        .size(100.dp)
)

// Size THEN padding THEN red background - different result
Box(
    Modifier
        .size(100.dp)
        .padding(16.dp)
        .background(Color.Red)
)
```

**Rule:** Order from outer (layout/sizing) to inner (styling/interaction):

1. Size constraints (`size`, `fillMaxWidth`, `sizeIn`)
2. Padding / margin (`padding`)
3. Drawing (`background`, `border`, `clip`)
4. Interaction (`clickable`, `pointerInput`)

### Common Modifier Patterns

#### Sizing

```kotlin
Box(Modifier.size(100.dp))
Box(Modifier.size(width = 200.dp, height = 100.dp))
Box(Modifier.fillMaxWidth(0.8f))  // 80% of parent width
Box(Modifier.fillMaxSize())
Box(Modifier.sizeIn(minWidth = 48.dp, minHeight = 48.dp))  // minimum touch target
```

#### Background and Border

```kotlin
// Apply clip before background for shape consistency
Box(
    Modifier
        .clip(RoundedCornerShape(8.dp))
        .background(MaterialTheme.colorScheme.surface)
        .border(1.dp, MaterialTheme.colorScheme.outline, RoundedCornerShape(8.dp))
        .padding(16.dp)
)
```

#### Clipping

```kotlin
// Clip content to shape - apply BEFORE background
Box(
    Modifier
        .clip(RoundedCornerShape(8.dp))
        .background(MaterialTheme.colorScheme.primaryContainer)
) {
    AsyncImage(model = url, contentDescription = "Photo")
}
```

#### Drawing

Use `drawWithCache` to optimize drawing operations by persisting objects across draw calls. The cache is re-created only when the drawing area size changes or any state objects read within the cache block change.

```kotlin
Box(
    Modifier
        .drawWithCache {
            // Objects created here are cached
            val brush = Brush.linearGradient(listOf(Color.Red, Color.Blue))
            onDrawBehind {
                // Drawing logic using cached objects
                drawRect(brush)
            }
        }
)
```

### Clickable and CombinedClickable

```kotlin
// Basic clickable with Material ripple
Box(
    Modifier
        .clip(RoundedCornerShape(8.dp))
        .clickable { onItemClick() }
        .padding(16.dp)
)

// Long press + double click + click
Box(
    Modifier
        .clip(RoundedCornerShape(8.dp))
        .combinedClickable(
            onClick = { onItemClick() },
            onLongClick = { onLongPress() },
            onDoubleClick = { onDoubleTap() }
        )
        .padding(16.dp)
)
```

Place `clickable` AFTER `clip` (for ripple bounds) but BEFORE `padding` (for larger touch target).

### Conditional Modifiers

Use `Modifier.then()` for conditional chaining:

```kotlin
// Good: conditional modifier with then()
Box(
    Modifier
        .fillMaxWidth()
        .then(if (isSelected) Modifier.background(selectedColor) else Modifier)
        .padding(16.dp)
)

// Bad: breaks chain readability
val mod = if (isSelected) Modifier.background(selectedColor) else Modifier
Box(mod.padding(16.dp))
```

### Custom Modifiers with Modifier.Node

`Modifier.Node` is the recommended API for custom modifiers. `Modifier.composed` is deprecated.

```kotlin
// Modifier.Node API (recommended)
private class HighlightNode(var color: Color) : DrawModifierNode, Modifier.Node() {
    override fun ContentDrawScope.draw() {
        drawContent()
        drawRect(color = color, alpha = 0.1f)
    }
}

private data class HighlightElement(val color: Color) : ModifierNodeElement<HighlightNode>() {
    override fun create() = HighlightNode(color)
    override fun update(node: HighlightNode) { node.color = color }
}

fun Modifier.highlight(color: Color) = this then HighlightElement(color)

// Usage
Box(Modifier.highlight(MaterialTheme.colorScheme.primary))
```

```kotlin
// Deprecated: Modifier.composed - do NOT use for new code
fun Modifier.oldStyleModifier() = composed {
    val state = remember { mutableStateOf(false) }
    this.background(if (state.value) Color.Blue else Color.Gray)
}
```

### Layout vs Drawing vs Pointer Input


| Category      | When It Runs               | Use For                                                 |
| ------------- | -------------------------- | ------------------------------------------------------- |
| Layout        | Measurement/placement pass | `size`, `padding`, `offset`, custom `LayoutModifier`    |
| Drawing       | Draw pass (after layout)   | `background`, `border`, `drawBehind`, `drawWithContent` |
| Pointer Input | Input event handling       | `clickable`, `pointerInput`, `draggable`                |


```kotlin
// Custom drawing - runs in draw phase, no recomposition
fun Modifier.debugBorder() = drawBehind {
    drawRect(color = Color.Red, style = Stroke(width = 2f))
}

// Custom gesture - runs in pointer input phase
fun Modifier.onSwipeRight(onSwipe: () -> Unit) = pointerInput(Unit) {
    detectHorizontalDragGestures { _, dragAmount ->
        if (dragAmount > 50f) onSwipe()
    }
}
```

### graphicsLayer - GPU Transforms

Applies transforms at the GPU level - no recomposition, no relayout. Prefer for animations.

```kotlin
Box(
    Modifier.graphicsLayer(
        scaleX = 1.2f,
        scaleY = 1.2f,
        rotationZ = 45f,
        alpha = 0.8f,
        translationX = 10f
    )
)
```

See [Animation > graphicsLayer](#graphicslayer-for-animation-performance) for animation-specific usage.

### Semantics and TestTag

```kotlin
// Accessibility semantics
Box(
    Modifier
        .semantics {
            contentDescription = "User avatar"
            role = Role.Image
        }
        .size(48.dp)
)

// Test tag for UI tests
Box(Modifier.testTag("submit_button"))

// In tests:
composeTestRule.onNodeWithTag("submit_button").performClick()
```

For comprehensive accessibility patterns, see `references/android-accessibility.md`.

### Always Accept Modifier Parameter

Every public composable must accept a `modifier` parameter with `Modifier` as default:

```kotlin
// Good: accepts and applies modifier
@Composable
fun UserCard(
    user: User,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(modifier = modifier.clickable { onClick() }) {
        Text(user.name)
    }
}

// Bad: no modifier parameter - caller cannot customize layout
@Composable
fun UserCard(user: User, onClick: () -> Unit) {
    Card { Text(user.name) }
}
```

### Modifier Anti-Patterns

```kotlin
// Bad: size after padding - padding excluded from final size
Modifier.padding(16.dp).size(100.dp)
// Good: size first
Modifier.size(100.dp).padding(16.dp)

// Bad: clickable before clip - ripple extends beyond bounds
Modifier.clickable { }.clip(RoundedCornerShape(8.dp))
// Good: clip before clickable
Modifier.clip(RoundedCornerShape(8.dp)).clickable { }

// Bad: background before clip - background extends beyond shape
Modifier.background(Color.Blue).clip(RoundedCornerShape(8.dp))
// Good: clip before background
Modifier.clip(RoundedCornerShape(8.dp)).background(Color.Blue)

// Bad: hardcoded modifier in composable body
@Composable
fun BadCard() {
    Box(Modifier.padding(16.dp).background(Color.Blue)) { }
}
// Good: accept modifier parameter
@Composable
fun GoodCard(modifier: Modifier = Modifier) {
    Box(modifier.padding(16.dp).background(Color.Blue)) { }
}
```

## CompositionLocal

Implicit data passing down the composition tree without threading through every parameter. Use for configuration-like values (theme, locale, density), not for general dependency injection.

### compositionLocalOf vs staticCompositionLocalOf

```kotlin
// compositionLocalOf: use when value changes and consumers need updates
val LocalUserPreferences = compositionLocalOf<UserPreferences> {
    error("UserPreferences not provided")
}

// staticCompositionLocalOf: use when value rarely/never changes (no change tracking overhead)
val LocalAnalytics = staticCompositionLocalOf<Analytics> {
    error("Analytics not provided")
}

// compositionLocalWithComputedDefaultOf: computed default based on other locals
val LocalContentAlpha = compositionLocalWithComputedDefaultOf<Float> { 1f }
```

| Type | Recomposition Behavior | Use When |
|------|----------------------|----------|
| `compositionLocalOf` | All consumers recompose on value change | Theme colors, user preferences, frequently changing config |
| `staticCompositionLocalOf` | Only direct readers update | Analytics, loggers, app version, static config |
| `compositionLocalWithComputedDefaultOf` | Computed default from other locals | Derived configuration values |

### Providing and Reading Values

```kotlin
// Provide values
CompositionLocalProvider(
    LocalUserPreferences provides userPrefs,
    LocalAnalytics provides analytics
) {
    AppContent()
}

// Read values
@Composable
fun UserAvatar() {
    val prefs = LocalUserPreferences.current
    // use prefs...
}
```

Values are scoped to descendants. Inner providers override outer ones.

### Built-In CompositionLocals

| Local                             | Type                          | Access Pattern                             |
|-----------------------------------|-------------------------------|--------------------------------------------|
| `LocalContext`                    | `Context`                     | `val context = LocalContext.current`       |
| `LocalConfiguration`              | `Configuration`               | Screen size, orientation, density          |
| `LocalDensity`                    | `Density`                     | dp/px conversions                          |
| `LocalLayoutDirection`            | `LayoutDirection`             | LTR/RTL                                    |
| `LocalLifecycleOwner`             | `LifecycleOwner`              | Activity/Fragment lifecycle                |
| `LocalView`                       | `View`                        | Underlying Android View                    |
| `LocalSoftwareKeyboardController` | `SoftwareKeyboardController?` | Control software keyboard (hide/show)      |
| `LocalFocusManager`               | `FocusManager`                | Control focus within Compose (clear focus) |
| `LocalClipboard`                  | `Clipboard`                   | Platform clipboard service (copy/paste)    |
| `LocalUriHandler`                 | `UriHandler`                  | Open URIs (e.g., in a browser)             |
| `LocalHapticFeedback`             | `HapticFeedback`              | Provide haptic feedback (vibrations)       |

### When to Use vs When NOT to Use

**Use CompositionLocal for:**
- Values needed by many descendants across the tree
- Configuration data (theme, locale, feature flags)
- Avoiding deep parameter drilling (5+ levels)

**Do NOT use CompositionLocal for:**
- Data only 1-2 levels deep - pass as parameters
- Frequently changing values that need precise control - use State/ViewModel
- General dependency injection - use Hilt

### CompositionLocal Anti-Patterns

```kotlin
// Bad: using CompositionLocal as generic DI container
val LocalEverything = compositionLocalOf { AppContainer() }

// Bad: storing MutableState in CompositionLocal - changes won't propagate correctly
val LocalCounter = compositionLocalOf { mutableStateOf(0) }

// Good: provide the value, not the State
val LocalCount = compositionLocalOf { 0 }
@Composable
fun Parent() {
    var count by remember { mutableIntStateOf(0) }
    CompositionLocalProvider(LocalCount provides count) {
        Child()
    }
}
```

## Lists & Scrolling

### Paging 3

Paging 3 is the standard for loading large datasets in chunks.

#### Five Critical Rules
1. **Never embed `PagingData` in `UiState`**: `PagingData` is a self-contained stream. Expose it as a separate `Flow<PagingData<T>>`.
2. **No new `Pager` per recomposition**: Create the `Pager` once in the ViewModel.
3. **Always use `cachedIn(viewModelScope)`**: Prevents duplicate network requests and crashes on configuration changes.
4. **Stable keys**: Always provide a stable `key` in `items()` using the item's unique ID.
5. **Dynamic queries**: Use `flatMapLatest` for parameter changes (e.g., search query), not naive `combine`.

#### ViewModel Pattern
```kotlin
@HiltViewModel
class SearchViewModel @Inject constructor(
    private val repository: SearchRepository
) : ViewModel() {

    private val _query = MutableStateFlow("")
    val query = _query.asStateFlow()

    // Separate Flow for PagingData, distinct from regular UiState
    @OptIn(ExperimentalCoroutinesApi::class)
    val searchResults: Flow<PagingData<SearchResult>> = _query
        .debounce(300)
        .distinctUntilChanged()
        .flatMapLatest { q ->
            Pager(
                config = PagingConfig(pageSize = 20, enablePlaceholders = false),
                pagingSourceFactory = { repository.search(q) }
            ).flow
        }
        .cachedIn(viewModelScope) // CRITICAL

    fun setQuery(newQuery: String) {
        _query.value = newQuery
    }
}
```

#### Compose UI Pattern
```kotlin
@Composable
fun SearchScreen(viewModel: SearchViewModel = hiltViewModel()) {
    val query by viewModel.query.collectAsStateWithLifecycle()
    val searchResults = viewModel.searchResults.collectAsLazyPagingItems()

    Column {
        SearchBar(query = query, onQueryChange = viewModel::setQuery)

        LazyColumn {
            items(
                count = searchResults.itemCount,
                key = searchResults.itemKey { it.id }, // CRITICAL: Stable key
                contentType = searchResults.itemContentType { "search_result" }
            ) { index ->
                val item = searchResults[index]
                if (item != null) {
                    SearchResultRow(item)
                } else {
                    SearchResultPlaceholder()
                }
            }

            // LoadState handling
            when (val appendState = searchResults.loadState.append) {
                is LoadState.Loading -> item { LoadingSpinner() }
                is LoadState.Error -> item { ErrorRow(appendState.error) }
                is LoadState.NotLoading -> Unit
            }
        }
    }
}
```

**Anti-pattern:** Never call `searchResults.refresh()` directly in the composable body (it will loop infinitely). Call it only in event handlers (e.g., `PullToRefresh` or a retry button).

#### Offline-first and `RemoteMediator`

For **paged** lists backed by **Room 3** plus a remote API, use a [`RemoteMediator`](https://developer.android.com/topic/libraries/architecture/paging/v3-network-db) to load pages from the network into the local database and expose a `PagingSource` from the DAO to the `Pager`. In **Room 3**, add **`androidx.room3:room3-paging`** and **`@DaoReturnTypeConverters(PagingSourceDaoReturnTypeConverter::class)`** on the DAO (or `@Database`) per [Room 3 release notes](https://developer.android.com/jetpack/androidx/releases/room3). That keeps the UI on a single `Flow<PagingData<T>>` while the database stays the source of truth. For broader sync, conflict handling, and invalidation patterns check `references/android-data-sync.md`.

### Flow Layouts

Use `FlowRow` and `FlowColumn` for wrapping content (like chips or tags) when it exceeds the available space.

```kotlin
FlowRow(
    modifier = Modifier.fillMaxWidth(),
    horizontalArrangement = Arrangement.spacedBy(8.dp),
    verticalArrangement = Arrangement.spacedBy(8.dp),
    maxItemsInEachRow = 3 // Optional: force wrapping after N items
) {
    tags.forEach { tag ->
        FilterChip(
            selected = tag.isSelected,
            onClick = { onTagClick(tag) },
            label = { Text(tag.name) }
        )
    }
}
```

### contentType for Recycling Optimization

When rendering different item types, `contentType` enables layout reuse between items of the same type:

```kotlin
sealed class FeedItem {
    data class Header(val title: String) : FeedItem()
    data class Post(val id: String, val content: String) : FeedItem()
    data class Ad(val id: String) : FeedItem()
}

LazyColumn {
    items(
        items = feedItems,
        key = { item ->
            when (item) {
                is FeedItem.Header -> "header-${item.title}"
                is FeedItem.Post -> item.id
                is FeedItem.Ad -> item.id
            }
        },
        contentType = { item ->
            when (item) {
                is FeedItem.Header -> "header"
                is FeedItem.Post -> "post"
                is FeedItem.Ad -> "ad"
            }
        }
    ) { item ->
        when (item) {
            is FeedItem.Header -> HeaderRow(item)
            is FeedItem.Post -> PostCard(item)
            is FeedItem.Ad -> AdBanner(item)
        }
    }
}
```

Without `contentType`, all items share one pool. With it, items reuse layouts efficiently. If two headers could share the same title, give `Header` a stable unique id and use that in the `key` lambda instead of `title`.

### LazyListState - Programmatic Scrolling

`LazyColumn` and `LazyRow` take `state: LazyListState = rememberLazyListState()` by default. **If you do not need a reference to the list's scroll state, omit `state` entirely** - the default remembers scroll for you inside the lazy list.

**Hoist `LazyListState` explicitly** (create `val listState = rememberLazyListState()` and pass `state = listState`) only when something in **your** composable tree must call into that same instance - for example:

- `animateScrollToItem` / `scrollToItem` (FAB, deep link, 'jump to')
- Reading `firstVisibleItemIndex`, `firstVisibleItemScrollOffset`, or `layoutInfo` (progress indicators, scroll-aware headers)
- `derivedStateOf { … }` tied to scroll (e.g. show/hide scroll-to-top)
- `Modifier.nestedScroll` or other APIs that need the list's `NestedScrollConnection` / state

If none of that applies, use a plain `LazyColumn { … }` with no `state` parameter.

**Do not** copy `firstVisibleItemIndex`, `firstVisibleItemScrollOffset`, or similar into the ViewModel's `StateFlow` for a normal feed - those values change constantly and will spam state updates without business value.

Hoist or persist scroll only when there is a **clear requirement**: e.g. **process death** / configuration recovery (persist minimal scroll hints via `SavedStateHandle` or `rememberSaveable` when you own the saver), or a spec that ties list position to something outside the composable. Otherwise treat scroll position as **UI-local**, like other transient layout state.

```kotlin
val listState = rememberLazyListState()
val scope = rememberCoroutineScope()

LazyColumn(state = listState) {
    items(items, key = { it.id }) { item -> ItemRow(item) }
}

// Scroll to item
Button(onClick = { scope.launch { listState.animateScrollToItem(0) } }) {
    Text("Scroll to top")
}

// Read scroll position
val firstVisibleIndex = listState.firstVisibleItemIndex
val firstVisibleOffset = listState.firstVisibleItemScrollOffset
```

Use `derivedStateOf` for scroll-dependent UI to avoid recomposing the entire list:

```kotlin
val showScrollToTop by remember {
    derivedStateOf { listState.firstVisibleItemIndex > 5 }
}

if (showScrollToTop) {
    FloatingActionButton(onClick = { scope.launch { listState.animateScrollToItem(0) } }) {
        Icon(painterResource(R.drawable.ic_arrow_up), "Scroll to top")
    }
}
```

### Sticky Headers

```kotlin
LazyColumn {
    groupedItems.forEach { (category, items) ->
        stickyHeader(key = "header-$category") {
            Surface(
                color = MaterialTheme.colorScheme.surfaceVariant,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(
                    text = category,
                    style = MaterialTheme.typography.titleSmall,
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
        items(items, key = { it.id }) { item ->
            ItemRow(item)
        }
    }
}
```

### Grids

```kotlin
// Fixed columns
LazyVerticalGrid(columns = GridCells.Fixed(3)) {
    items(items, key = { it.id }) { GridItem(it) }
}

// Adaptive - fills available space with min column width
LazyVerticalGrid(columns = GridCells.Adaptive(minSize = 120.dp)) {
    items(items, key = { it.id }) { GridItem(it) }
}
```

Prefer `GridCells.Adaptive` for responsive layouts.

### Staggered Grid

Pinterest-style layout with variable heights:

```kotlin
LazyVerticalStaggeredGrid(
    columns = StaggeredGridCells.Fixed(2),
    contentPadding = PaddingValues(16.dp),
    verticalItemSpacing = 8.dp,
    horizontalArrangement = Arrangement.spacedBy(8.dp)
) {
    items(images, key = { it.id }) { image ->
        AsyncImage(
            model = image.url,
            contentDescription = image.description,
            modifier = Modifier.fillMaxWidth()
        )
    }
}
```

### Pager

```kotlin
val pagerState = rememberPagerState(pageCount = { pages.size })

HorizontalPager(state = pagerState) { page ->
    PageContent(pages[page])
}

// Programmatic scroll
val scope = rememberCoroutineScope()
Button(onClick = { scope.launch { pagerState.animateScrollToPage(2) } }) {
    Text("Go to page 3")
}
```

`VerticalPager` works the same for vertical swiping. Replaces deprecated `accompanist-pager`.

### Nested Scrolling Pitfalls

```kotlin
// Bad: scrollable modifier inside LazyColumn - two scroll containers fight
LazyColumn {
    item {
        Column(Modifier.verticalScroll(rememberScrollState())) {
            Text("Double scrollable!")
        }
    }
}

// OK: nested LazyRow inside LazyColumn (different scroll axes)
LazyColumn {
    item {
        LazyRow {
            items(horizontalItems) { HorizontalCard(it) }
        }
    }
}

// For complex same-axis nesting, use nestedScroll:
val nestedScrollConnection = remember {
    object : NestedScrollConnection {
        override fun onPreScroll(available: Offset, source: NestedScrollSource): Offset {
            return Offset.Zero // custom handling
        }
    }
}
LazyColumn(Modifier.nestedScroll(nestedScrollConnection)) {
    items(100) { Text("Item $it") }
}
```

### Lists Rules

- Always provide stable, unique `key` for mutable lists (IDs, not indices)
- Use `contentType` for multi-type lists
- Use `Column`/`Row` for small fixed lists (< 10 items) - `LazyColumn` is overkill
- Never use indices as keys - list mutations corrupt item state
- Use `derivedStateOf` for scroll-dependent UI
- Omit `state` on `LazyColumn`/`LazyRow` when you do not need programmatic scroll APIs; default `rememberLazyListState()` inside the lazy list is enough
- When you do hoist `LazyListState`, keep it in composition; avoid mirroring scroll indices into ViewModel state unless restoring scroll or meeting an explicit product requirement

## View Composition Rules

### Composable Naming

- **PascalCase nouns** for UI components: `UserCard`, `LoginScreen`, `CheckboxWithLabel`
- **PascalCase verbs** for effect-only composables: `LaunchedEffect`, `TrackScreenView`
- Never ambiguous names like `HandleLogin` - is it UI or an effect?

### Slot Pattern

Accept `@Composable` lambda parameters for flexible, reusable containers:

```kotlin
@Composable
fun SectionCard(
    title: @Composable () -> Unit,
    modifier: Modifier = Modifier,
    actions: @Composable RowScope.() -> Unit = {},
    content: @Composable ColumnScope.() -> Unit
) {
    Card(modifier = modifier) {
        Column(Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                title()
                Row(content = actions)
            }
            Spacer(Modifier.height(8.dp))
            content()
        }
    }
}

// Usage - caller controls content
SectionCard(
    title = { Text("Recent Activity", style = MaterialTheme.typography.titleMedium) },
    actions = {
        IconButton(onClick = { }) {
            Icon(painterResource(R.drawable.ic_filter), "Filter")
        }
    }
) {
    ActivityList(items = events)
}
```

Pass `@Composable` lambdas, not pre-composed values. Optional slots use nullable lambdas with `?.invoke()`.

### Never Return Values from Composables

Composables execute during composition at unpredictable times. Always use callbacks:

```kotlin
// Bad: composables don't return values
@Composable
fun UserInput(): String {
    var text by remember { mutableStateOf("") }
    TextField(value = text, onValueChange = { text = it })
    return text
}

// Good: callback pattern
@Composable
fun UserInput(onValueChange: (String) -> Unit) {
    var text by remember { mutableStateOf("") }
    TextField(
        value = text,
        onValueChange = {
            text = it
            onValueChange(it)
        }
    )
}
```

### Screen-Level Composable Structure

Screens are a thin ViewModel integration layer. Keep ViewModel at screen level only - never pass to child composables:

```kotlin
// Screen composable: connects ViewModel to pure UI
@Composable
fun ProductDetailScreen(viewModel: ProductDetailViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    ProductDetailContent(uiState = uiState, onAction = viewModel::onAction)
}

// Content composable: pure, testable, previewable
@Composable
private fun ProductDetailContent(
    uiState: ProductUiState,
    onAction: (ProductAction) -> Unit,
    modifier: Modifier = Modifier
) {
    // Pure UI rendering - no ViewModel dependency
}

// Bad: passing ViewModel to children
@Composable
fun ProductCard(viewModel: ProductDetailViewModel) { } // couples child to ViewModel

// Good: pass only data
@Composable
fun ProductCard(product: Product, onClick: () -> Unit) { }
```

### Extraction Guidelines

**Extract when:**
- Reused in multiple places
- Composable exceeds ~50 lines
- Independent concern (header, form, list item)
- Needs independent testing/preview

**Don't extract when:**
- Single use and under ~10 lines (single `Text()` or `Icon()`)
- Would require passing 5+ parameters (over-extraction)
- Tightly coupled to parent logic

## Deprecated Patterns & Migrations

All migration guides have been consolidated into [migration.md](migration.md). It covers:

- Accompanist to official APIs
- Compose API migrations (`collectAsStateWithLifecycle`, `mutableIntStateOf`, `animateItem`, `Modifier.Node`)
- Material 2 to Material 3
- Scaffold `innerPadding` (mandatory)
- `@ExperimentalMaterial3Api` graduations
- Edge-to-edge
- Navigation string routes to Navigation3
- XML to Compose
- LiveData to StateFlow
- RxJava to Coroutines

## Forms & Input

### Keyboard Configuration

Set semantic `KeyboardOptions` so the system shows the correct keyboard layout:

```kotlin
TextField(
    value = email,
    onValueChange = { email = it },
    keyboardOptions = KeyboardOptions(
        keyboardType = KeyboardType.Email,
        imeAction = ImeAction.Next
    ),
    keyboardActions = KeyboardActions(
        onNext = { focusManager.moveFocus(FocusDirection.Down) }
    )
)
```

Common keyboard types:

| Input type | `keyboardType`          |
|------------|-------------------------|
| Email      | `KeyboardType.Email`    |
| Phone      | `KeyboardType.Phone`    |
| Integer    | `KeyboardType.Number`   |
| Decimal    | `KeyboardType.Decimal`  |
| Password   | `KeyboardType.Password` |
| URL        | `KeyboardType.Uri`      |

### Autofill

Enable autofill by setting `contentType` in semantics:

```kotlin
TextField(
    value = email,
    onValueChange = { email = it },
    modifier = Modifier.semantics {
        contentType = ContentType.EmailAddress
    }
)

TextField(
    value = password,
    onValueChange = { password = it },
    visualTransformation = PasswordVisualTransformation(),
    modifier = Modifier.semantics {
        contentType = ContentType.Password
    }
)
```

### Password Visibility Toggle

```kotlin
@Composable
fun PasswordField(
    password: String,
    onPasswordChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var passwordVisible by rememberSaveable { mutableStateOf(false) }

    TextField(
        value = password,
        onValueChange = onPasswordChange,
        visualTransformation = if (passwordVisible) {
            VisualTransformation.None
        } else {
            PasswordVisualTransformation()
        },
        trailingIcon = {
            IconButton(onClick = { passwordVisible = !passwordVisible }) {
                Icon(
                    imageVector = if (passwordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                    contentDescription = if (passwordVisible) "Hide password" else "Show password"
                )
            }
        },
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
        modifier = modifier
    )
}
```

### Validation Timing

Validate on focus-out, not on every keystroke. Per-keystroke validation creates a noisy experience
where errors flash while the user is still typing.

```kotlin
@Composable
fun ValidatedEmailField(
    email: String,
    onEmailChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    var hasBlurred by rememberSaveable { mutableStateOf(false) }
    val isError = hasBlurred && !Patterns.EMAIL_ADDRESS.matcher(email).matches()

    TextField(
        value = email,
        onValueChange = onEmailChange,
        isError = isError,
        supportingText = if (isError) {{ Text("Invalid email address") }} else null,
        modifier = modifier.onFocusChanged { state ->
            if (!state.isFocused && email.isNotEmpty()) {
                hasBlurred = true
            }
        }
    )
}
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
- [Migration Guide](migration.md) - Accompanist, Compose API, Material, RxJava, and Navigation migrations

