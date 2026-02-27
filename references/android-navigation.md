# Navigation Guide

Navigation3 architecture with type-safe routing, adaptive navigation, and multi-module coordination.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.
**Dependencies**: See `templates/libs.versions.toml.template` for Navigation 3 versions and the `navigation3` bundle.

## Table of Contents
1. [Navigation3 Architecture](#navigation3-architecture)
2. [When to Use Navigation3](#when-to-use-navigation3)
3. [Key Benefits](#key-benefits-of-navigation3-architecture)
4. [Quick Start](#navigation-3-quick-start)
5. [App Navigation Setup](#app-navigation-setup)
6. [Navigation State Management](#navigation-3-state-management)
7. [Key Principles](#key-principles)
8. [Navigation Flow](#navigation-flow)
9. [Migration Note](#migration-note)

## Navigation3 Architecture

Feature-level navigation components (`AuthDestination`, `AuthNavigator`, `AuthGraph`) are created as part
of the feature module setup in `references/modularization.md` → "Create Feature Module" → Step 4.

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
4. **Adaptive UI**: `NavigationSuiteScaffold` auto-switches between navigation bar, rail, and drawer based on window size class
5. **Single Backstack**: One `NavHost` controls entire app flow within `NavigationSuiteScaffold`
6. **Material 3 Integration**: Built-in support for Material 3 adaptive design with `NavigableListDetailPaneScaffold` and `NavigableSupportingPaneScaffold`
7. **Modern API**: Latest navigation patterns including support for predictive back gestures
8. **Multi-pane Support**: `NavigableListDetailPaneScaffold` and `NavigableSupportingPaneScaffold` for tablets and foldables
9. **Predictive Back Gestures**: Built-in support for Android's predictive back gesture system (mandatory on API 36)
10. **Compose-First Design**: Designed specifically for Jetpack Compose, not adapted from View system
11. **`NavigableListDetailPaneScaffold`**: For tablet/foldable list-detail layouts with built-in navigation and predictive back
12. **`NavigableSupportingPaneScaffold`**: For main + supporting content layouts
13. **`NavHost` from `androidx.navigation3`**: The Navigation3 version of NavHost

## Navigation 3 Quick Start

Navigation 3 uses type-safe data classes as navigation keys. Here's a minimal example:

#### 1. Define Destinations (Feature Module)

```kotlin
// feature/products/navigation/ProductsDestination.kt
import kotlinx.serialization.Serializable
import androidx.navigation3.runtime.NavKey

@Serializable
sealed interface ProductsDestination : NavKey {
    @Serializable
    data class ProductsList(val categoryId: String) : ProductsDestination
    
    @Serializable
    data class ProductDetail(val productId: String) : ProductsDestination
}
```

#### 2. Define Navigator Interface (Feature Module)

```kotlin
// feature/products/navigation/ProductsNavigator.kt
interface ProductsNavigator {
    fun navigateToDetail(productId: String)
    fun navigateBack()
}
```

#### 3. Use in Route Composable (Feature Module)

```kotlin
// feature/products/presentation/ProductsRoute.kt
@Composable
fun ProductsRoute(
    categoryId: String,
    navigator: ProductsNavigator,
    viewModel: ProductsViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    ProductsListScreen(
        state = uiState,
        onProductClick = { productId ->
            navigator.navigateToDetail(productId)
        },
        onBackClick = navigator::navigateBack
    )
}
```

#### 4. Register in App Module

```kotlin
// app/navigation/AppNavigation.kt
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay

@Composable
fun AppNavigation() {
    val backStack = rememberNavBackStack(
        startDestination = ProductsDestination.ProductsList(categoryId = "all")
    )
    
    // Implement navigator
    val productsNavigator = remember {
        object : ProductsNavigator {
            override fun navigateToDetail(productId: String) {
                backStack.add(ProductsDestination.ProductDetail(productId))
            }
            override fun navigateBack() {
                backStack.removeLastOrNull()
            }
        }
    }
    
    // Define routes
    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = entryProvider {
            entry<ProductsDestination.ProductsList> { key ->
                ProductsRoute(
                    categoryId = key.categoryId,
                    navigator = productsNavigator
                )
            }
            entry<ProductsDestination.ProductDetail> { key ->
                ProductDetailRoute(
                    productId = key.productId,
                    navigator = productsNavigator
                )
            }
        }
    )
}
```

**Key Points:**
- Routes are `@Serializable` data classes (type-safe, saved across process death)
- Feature modules define `Navigator` interfaces (no navigation logic)
- App module implements `Navigator` and registers all routes
- Use `rememberNavBackStack()` for simple navigation or `rememberNavigationState()` for multi-stack (bottom nav)

## App Navigation Setup

```kotlin
// app/src/main/kotlin/com/example/app/navigation/AppNavigation.kt
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.ui.NavDisplay
import kotlinx.serialization.Serializable

@Immutable
sealed interface TopLevelRoute : NavKey {
    @Serializable data object Auth : TopLevelRoute
    @Serializable data object Profile : TopLevelRoute
    @Serializable data object Settings : TopLevelRoute
}

@Composable
fun AppNavigation(
    analytics: Analytics
) {
    // Create navigation state (survives config changes and process death)
    val navigationState = rememberNavigationState(
        startRoute = TopLevelRoute.Auth,
        topLevelRoutes = setOf(
            TopLevelRoute.Auth,
            TopLevelRoute.Profile,
            TopLevelRoute.Settings
        )
    )
    
    val navigator = remember(navigationState) { Navigator(navigationState) }
    
    // Track screen views for analytics/crashlytics
    LaunchedEffect(navigationState.topLevelRoute) {
        val currentStack = navigationState.backStacks[navigationState.topLevelRoute]
        val currentRoute = currentStack?.last()
        currentRoute?.let { route ->
            analytics.logScreenView(
                screenName = route::class.simpleName ?: "Unknown",
                screenClass = "MainActivity"
            )
        }
    }
    
    // Create navigator implementations
    val authNavigator = remember(navigator) {
        object : AuthNavigator {
            override fun navigateToRegister() = navigator.navigate(AuthDestination.Register)
            override fun navigateToForgotPassword() = navigator.navigate(AuthDestination.ForgotPassword)
            override fun navigateBack() = navigator.goBack()
            override fun navigateToProfile(userId: String) = navigator.navigate(AuthDestination.Profile(userId))
            override fun navigateToMainApp() = navigator.navigate(TopLevelRoute.Profile)
        }
    }
    
    // Define all app destinations
    val entryProvider = entryProvider {
        authGraph(authNavigator)
        profileGraph()
        settingsGraph()
    }
    
    // NavigationSuiteScaffold auto-switches between bar/rail/drawer based on window size
    NavigationSuiteScaffold(
        navigationSuiteItems = {
            item(
                icon = { Icon(painterResource(R.drawable.ic_lock), contentDescription = null) },
                label = { Text("Auth") },
                selected = navigationState.topLevelRoute == TopLevelRoute.Auth,
                onClick = { navigator.navigate(TopLevelRoute.Auth) }
            )
            item(
                icon = { Icon(painterResource(R.drawable.ic_person), contentDescription = null) },
                label = { Text("Profile") },
                selected = navigationState.topLevelRoute == TopLevelRoute.Profile,
                onClick = { navigator.navigate(TopLevelRoute.Profile) }
            )
            item(
                icon = { Icon(painterResource(R.drawable.ic_settings), contentDescription = null) },
                label = { Text("Settings") },
                selected = navigationState.topLevelRoute == TopLevelRoute.Settings,
                onClick = { navigator.navigate(TopLevelRoute.Settings) }
            )
        }
    ) {
        NavDisplay(
            entries = navigationState.toEntries(entryProvider),
            onBack = { navigator.goBack() },
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

**Icon Resources**: See `references/android-graphics.md` for complete guidance on:
- Material Symbols icons (download via Iconify API or Google Fonts)
- ImageVector patterns for programmatic icons
- Custom drawing with Canvas
- Performance optimizations

**Quick example:**
```kotlin
// Download icon
curl -o app/src/main/res/drawable/ic_lock.xml \
  "https://api.iconify.design/material-symbols:lock.svg?download=true"

// Usage
Icon(
    painter = painterResource(R.drawable.ic_lock),
    contentDescription = stringResource(R.string.lock_icon)
)
```

**Analytics Integration**: Inject `Analytics` interface (from `references/crashlytics.md`) instead of using Firebase directly. This provides abstraction for crash reporting and analytics.

## Navigation 3 State Management

Navigation 3 uses explicit state management with Unidirectional Data Flow:

**1. NavigationState** - Holds current route and back stacks:
```kotlin
// Copy this into NavigationState.kt in your app module
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSerializable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.runtime.toMutableStateList
import androidx.navigation3.runtime.NavBackStack
import androidx.navigation3.runtime.NavEntry
import androidx.navigation3.runtime.NavKey
import androidx.navigation3.runtime.rememberDecoratedNavEntries
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.runtime.rememberSaveableStateHolderNavEntryDecorator
import androidx.navigation3.runtime.serialization.NavKeySerializer
import androidx.savedstate.compose.serialization.serializers.MutableStateSerializer

@Composable
fun rememberNavigationState(
    startRoute: NavKey,
    topLevelRoutes: Set<NavKey>
): NavigationState {
    val topLevelRoute = rememberSerializable(
        startRoute, topLevelRoutes,
        serializer = MutableStateSerializer(NavKeySerializer())
    ) {
        mutableStateOf(startRoute)
    }

    val backStacks = topLevelRoutes.associateWith { key -> rememberNavBackStack(key) }

    return remember(startRoute, topLevelRoutes) {
        NavigationState(
            startRoute = startRoute,
            topLevelRoute = topLevelRoute,
            backStacks = backStacks
        )
    }
}

class NavigationState(
    val startRoute: NavKey,
    topLevelRoute: MutableState<NavKey>,
    val backStacks: Map<NavKey, NavBackStack<NavKey>>
) {
    var topLevelRoute: NavKey by topLevelRoute
    val stacksInUse: List<NavKey>
        get() = if (topLevelRoute == startRoute) {
            listOf(startRoute)
        } else {
            listOf(startRoute, topLevelRoute)
        }
}

@Composable
fun NavigationState.toEntries(
    entryProvider: (NavKey) -> NavEntry<NavKey>
): SnapshotStateList<NavEntry<NavKey>> {
    val decoratedEntries = backStacks.mapValues { (_, stack) ->
        val decorators = listOf(
            rememberSaveableStateHolderNavEntryDecorator<NavKey>(),
        )
        rememberDecoratedNavEntries(
            backStack = stack,
            entryDecorators = decorators,
            entryProvider = entryProvider
        )
    }

    return stacksInUse
        .flatMap { decoratedEntries[it] ?: emptyList() }
        .toMutableStateList()
}
```

**2. Navigator** - Modifies navigation state:
```kotlin
// Copy this into Navigator.kt in your app module
import androidx.navigation3.runtime.NavKey

class Navigator(val state: NavigationState) {
    fun navigate(route: NavKey) {
        if (route in state.backStacks.keys) {
            // This is a top level route, just switch to it.
            state.topLevelRoute = route
        } else {
            state.backStacks[state.topLevelRoute]?.add(route)
        }
    }

    fun goBack() {
        val currentStack = state.backStacks[state.topLevelRoute] ?:
            error("Stack for ${state.topLevelRoute} not found")
        val currentRoute = currentStack.last()

        // If we're at the base of the current route, go back to the start route stack.
        if (currentRoute == state.topLevelRoute) {
            state.topLevelRoute = state.startRoute
        } else {
            currentStack.removeLastOrNull()
        }
    }
}
```

**3. Feature Navigator Interface**:
```kotlin
// feature-auth/navigation/AuthNavigator.kt
interface AuthNavigator {
    fun navigateToRegister()
    fun navigateToForgotPassword()
    fun navigateBack()
    fun navigateToProfile(userId: String)
    fun navigateToMainApp()
}

// In App module implementation:
val authNavigator = remember(navigator) {
    object : AuthNavigator {
        override fun navigateToRegister() = navigator.navigate(AuthDestination.Register)
        override fun navigateToForgotPassword() = navigator.navigate(AuthDestination.ForgotPassword)
        override fun navigateBack() = navigator.goBack()
        override fun navigateToProfile(userId: String) = navigator.navigate(AuthDestination.Profile(userId))
        override fun navigateToMainApp() = navigator.navigate(TopLevelRoute.Profile)
    }
}
```

**Architecture principles:** These classes follow Unidirectional Data Flow:
- The `Navigator` handles navigation events and updates `NavigationState`
- The UI (provided by `NavDisplay`) observes `NavigationState` and reacts to changes

## Key Principles

1. **Feature Independence**: Features define `Navigator` interfaces
2. **Central Coordination**: App module implements all navigators
3. **Type-Safe Routes**: Routes implement `NavKey` with `@Serializable` and `@Immutable`
4. **Explicit State Management**: `NavigationState` + `Navigator` manage navigation state
5. **Adaptive Navigation**: `NavigationSuiteScaffold` auto-switches between bar/rail/drawer based on window size

## Navigation Flow

For end-to-end flow diagrams (UI → data → navigation), see the Complete Architecture
Flow section in `references/architecture.md`.

## Migration Note

If migrating from Navigation 2.x to Navigation3:
1. Update imports from `androidx.navigation.*` to `androidx.navigation3.*`
2. Use `NavigationSuiteScaffold` (it handles adaptive switching automatically)
3. Update `NavHost` and `rememberNavController()` imports
4. Use `NavigableListDetailPaneScaffold` / `NavigableSupportingPaneScaffold` for tablet-optimized layouts

## Animations

`NavDisplay` provides built-in animation support via `ContentTransform`. Customize globally or per-entry.

### Global Transitions

Set default animations for all destinations on `NavDisplay`:

```kotlin
NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    transitionSpec = {
        // Forward navigation: slide in from right
        slideInHorizontally(initialOffsetX = { it }) togetherWith
            slideOutHorizontally(targetOffsetX = { -it })
    },
    popTransitionSpec = {
        // Back navigation: slide in from left
        slideInHorizontally(initialOffsetX = { -it }) togetherWith
            slideOutHorizontally(targetOffsetX = { it })
    },
    predictivePopTransitionSpec = {
        // Predictive back gesture: same as popTransitionSpec
        slideInHorizontally(initialOffsetX = { -it }) togetherWith
            slideOutHorizontally(targetOffsetX = { it })
    },
    entryProvider = entryProvider {
        // ...
    }
)
```

**Parameters:**
- `transitionSpec` - `ContentTransform` when content is added to back stack (navigating forward)
- `popTransitionSpec` - `ContentTransform` when content is removed from back stack (navigating back)
- `predictivePopTransitionSpec` - `ContentTransform` during predictive back gestures (Android 14+)

### Per-Entry Overrides

Override global transitions for specific entries using metadata helper functions:

```kotlin
entry<ScreenC>(
    metadata = NavDisplay.transitionSpec {
        // Slide up from bottom, keep old content underneath
        slideInVertically(
            initialOffsetY = { it },
            animationSpec = tween(1000)
        ) togetherWith ExitTransition.KeepUntilTransitionsFinished
    } + NavDisplay.popTransitionSpec {
        // Slide down, reveal content underneath
        EnterTransition.None togetherWith
            slideOutVertically(
                targetOffsetY = { it },
                animationSpec = tween(1000)
            )
    } + NavDisplay.predictivePopTransitionSpec {
        EnterTransition.None togetherWith
            slideOutVertically(
                targetOffsetY = { it },
                animationSpec = tween(1000)
            )
    }
) {
    ScreenCContent()
}
```

**Metadata keys** (combine with `+`):
- `NavDisplay.transitionSpec { ... }` - forward animation for this entry
- `NavDisplay.popTransitionSpec { ... }` - back animation for this entry
- `NavDisplay.predictivePopTransitionSpec { ... }` - predictive back animation for this entry

Per-entry metadata overrides the global `NavDisplay` transitions.

### Common Animation Patterns

```kotlin
// Fade
fadeIn(tween(300)) togetherWith fadeOut(tween(300))

// Horizontal slide
slideInHorizontally(initialOffsetX = { it }) togetherWith
    slideOutHorizontally(targetOffsetX = { -it })

// Vertical slide (bottom sheet style)
slideInVertically(initialOffsetY = { it }) togetherWith
    ExitTransition.KeepUntilTransitionsFinished

// No animation
EnterTransition.None togetherWith ExitTransition.None
```

## Scenes & Custom Layouts

A `Scene` is the fundamental rendering unit in Navigation 3. It renders one or more `NavEntry` instances, allowing single-pane, multi-pane, dialog, and bottom sheet layouts. A `SceneStrategy` determines how back stack entries are arranged into a `Scene`.

### Scene Interface

```kotlin
interface Scene<T : Any> {
    val key: Any
    val entries: List<NavEntry<T>>
    val previousEntries: List<NavEntry<T>>
    val content: @Composable () -> Unit
}
```

- `key` - unique identifier driving top-level animation when the Scene changes
- `entries` - the `NavEntry` objects this Scene displays
- `previousEntries` - entries for calculating predictive back state
- `content` - composable rendering the Scene's entries

### SceneStrategy

A `SceneStrategy` decides whether it can create a `Scene` from the current back stack entries:

```kotlin
interface SceneStrategy<T : Any> {
    fun SceneStrategyScope<T>.calculateScene(
        entries: List<NavEntry<T>>
    ): Scene<T>?
}
```

Returns `null` if it cannot handle the entries, letting the next strategy try. Built-in strategies:
- `SinglePaneSceneStrategy` - displays the last entry full-screen (default)
- `DialogSceneStrategy` - renders entries marked as dialogs in an overlay

### Dialog Navigation

Use `DialogSceneStrategy` to show entries as dialogs:

```kotlin
import androidx.compose.ui.window.DialogProperties
import androidx.lifecycle.compose.dropUnlessResumed
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.scene.DialogSceneStrategy
import androidx.navigation3.ui.NavDisplay

@Composable
fun DialogExample() {
    val backStack = rememberNavBackStack(HomeRoute)
    val dialogStrategy = remember { DialogSceneStrategy<NavKey>() }

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        sceneStrategy = dialogStrategy,
        entryProvider = entryProvider {
            entry<HomeRoute> {
                HomeScreen(
                    onShowDialog = dropUnlessResumed {
                        backStack.add(ConfirmRoute("Are you sure?"))
                    }
                )
            }
            entry<ConfirmRoute>(
                metadata = DialogSceneStrategy.dialog(
                    DialogProperties(dismissOnClickOutside = true)
                )
            ) { key ->
                ConfirmDialog(
                    message = key.message,
                    onDismiss = { backStack.removeLastOrNull() }
                )
            }
        }
    )
}
```

**Key points:**
- Pass `DialogSceneStrategy<NavKey>()` as `sceneStrategy` to `NavDisplay`
- Mark dialog entries with `metadata = DialogSceneStrategy.dialog(DialogProperties(...))`
- The dialog renders as an overlay on top of the previous entry
- Use `dropUnlessResumed` to prevent double-clicks during transitions

### Custom Scene: List-Detail Layout

Create a custom `Scene` and `SceneStrategy` for adaptive layouts (e.g., list-detail on wide screens):

```kotlin
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.adaptive.currentWindowAdaptiveInfo
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.navigation3.runtime.NavEntry
import androidx.navigation3.scene.Scene
import androidx.navigation3.scene.SceneStrategy
import androidx.window.core.layout.WIDTH_DP_MEDIUM_LOWER_BOUND
import androidx.window.core.layout.WindowSizeClass

class ListDetailScene<T : Any>(
    override val key: Any,
    override val previousEntries: List<NavEntry<T>>,
    val listEntry: NavEntry<T>,
    val detailEntry: NavEntry<T>,
) : Scene<T> {
    override val entries: List<NavEntry<T>> = listOf(listEntry, detailEntry)
    override val content: @Composable (() -> Unit) = {
        Row(modifier = Modifier.fillMaxSize()) {
            Column(modifier = Modifier.weight(0.4f)) {
                listEntry.Content()
            }
            Column(modifier = Modifier.weight(0.6f)) {
                detailEntry.Content()
            }
        }
    }
}

class ListDetailSceneStrategy<T : Any>(
    val windowSizeClass: WindowSizeClass
) : SceneStrategy<T> {

    override fun SceneStrategyScope<T>.calculateScene(
        entries: List<NavEntry<T>>
    ): Scene<T>? {
        if (!windowSizeClass.isWidthAtLeastBreakpoint(WIDTH_DP_MEDIUM_LOWER_BOUND)) {
            return null
        }

        val detailEntry = entries.lastOrNull()
            ?.takeIf { it.metadata.containsKey(DETAIL_KEY) } ?: return null
        val listEntry = entries.findLast {
            it.metadata.containsKey(LIST_KEY)
        } ?: return null

        return ListDetailScene(
            key = listEntry.contentKey,
            previousEntries = entries.dropLast(1),
            listEntry = listEntry,
            detailEntry = detailEntry
        )
    }

    companion object {
        internal const val LIST_KEY = "ListDetailScene-List"
        internal const val DETAIL_KEY = "ListDetailScene-Detail"

        fun listPane() = mapOf(LIST_KEY to true)
        fun detailPane() = mapOf(DETAIL_KEY to true)
    }
}

@Composable
fun <T : Any> rememberListDetailSceneStrategy(): ListDetailSceneStrategy<T> {
    val windowSizeClass = currentWindowAdaptiveInfo().windowSizeClass
    return remember(windowSizeClass) { ListDetailSceneStrategy(windowSizeClass) }
}
```

**Usage:**
```kotlin
val listDetailStrategy = rememberListDetailSceneStrategy<NavKey>()

NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    sceneStrategy = listDetailStrategy,
    entryProvider = entryProvider {
        entry<ConversationList>(
            metadata = ListDetailSceneStrategy.listPane()
        ) {
            ConversationListScreen(onSelect = { id ->
                backStack.removeIf { it is ConversationDetail }
                backStack.add(ConversationDetail(id))
            })
        }
        entry<ConversationDetail>(
            metadata = ListDetailSceneStrategy.detailPane()
        ) { key ->
            ConversationDetailScreen(conversationId = key.id)
        }
    }
)
```

On wide screens, list and detail show side-by-side (40/60 split). On narrow screens, the strategy returns `null` and the default `SinglePaneSceneStrategy` takes over.

### Material3 Adaptive Scenes

For production list-detail and supporting-pane layouts, use the pre-built Material3 Adaptive scenes from `androidx.compose.material3.adaptive:adaptive-navigation3`:

```kotlin
import androidx.compose.material3.adaptive.navigation3.ListDetailSceneStrategy
import androidx.compose.material3.adaptive.navigation3.rememberListDetailSceneStrategy

@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun MaterialListDetailExample() {
    val backStack = rememberNavBackStack(ProductList)
    val listDetailStrategy = rememberListDetailSceneStrategy<NavKey>()

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        sceneStrategy = listDetailStrategy,
        entryProvider = entryProvider {
            entry<ProductList>(
                metadata = ListDetailSceneStrategy.listPane(
                    detailPlaceholder = {
                        Text("Select a product from the list")
                    }
                )
            ) {
                ProductListScreen(onProductClick = { id ->
                    backStack.add(ProductDetail(id))
                })
            }
            entry<ProductDetail>(
                metadata = ListDetailSceneStrategy.detailPane()
            ) { key ->
                ProductDetailScreen(productId = key.id)
            }
            entry<ProductProfile>(
                metadata = ListDetailSceneStrategy.extraPane()
            ) {
                ProductProfileScreen()
            }
        }
    )
}
```

**Material3 metadata helpers:**
- `ListDetailSceneStrategy.listPane(detailPlaceholder = { ... })` - marks entry as list pane, with optional placeholder when no detail is selected
- `ListDetailSceneStrategy.detailPane()` - marks entry as detail pane
- `ListDetailSceneStrategy.extraPane()` - marks entry as extra pane (three-pane layout)

The Material3 `ListDetailSceneStrategy` automatically handles pane arrangement, predictive back, and window size adaptation. For supporting-pane layouts, use `rememberSupportingPaneSceneStrategy()` with matching metadata.

## Deep Links

Navigation 3 gives you direct control over deep link handling — you parse the intent, create the `NavKey`, and manage the back stack yourself. This section follows the [Principles of Navigation](https://developer.android.com/guide/navigation/principles).

### Parsing an Intent into a NavKey

Convert the incoming `Intent` data URI into a navigation key using `kotlinx.serialization`:

**1. Define deep link patterns:**
```kotlin
// app/deeplink/DeepLinkPatterns.kt
import androidx.navigation3.runtime.NavKey

internal val deepLinkPatterns: List<DeepLinkPattern<out NavKey>> = listOf(
    DeepLinkPattern(
        serializer = HomeRoute.serializer(),
        pattern = "https://example.com/home".toUri()
    ),
    DeepLinkPattern(
        serializer = ProductDetail.serializer(),
        pattern = "https://example.com/products/{productId}".toUri()
    ),
    DeepLinkPattern(
        serializer = UserProfile.serializer(),
        pattern = "https://example.com/users/{userId}".toUri()
    ),
)
```

**2. Parse and match in Activity:**
```kotlin
// app/MainActivity.kt
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    val deepLinkKey: NavKey = intent.data?.let { uri ->
        val request = DeepLinkRequest(uri)

        val match = deepLinkPatterns.firstNotNullOfOrNull { pattern ->
            DeepLinkMatcher(request, pattern).match()
        }

        match?.let {
            KeyDecoder(match.args).decodeSerializableValue(match.serializer)
        }
    } ?: HomeRoute

    setContent {
        val backStack = rememberNavBackStack(deepLinkKey)
        // ... NavDisplay setup
    }
}
```

**Key points:**
- `DeepLinkPattern` maps a URI pattern to a `NavKey` serializer, extracting `{path}` and `?query` arguments
- `DeepLinkRequest` parses the incoming URI into path segments and query parameters
- `DeepLinkMatcher` compares the request against each pattern
- `KeyDecoder` uses `kotlinx.serialization` to decode matched arguments into the `NavKey`

### Synthetic Back Stack

When a deep link launches directly to a destination, build a synthetic back stack so Up/Back navigates naturally to parent screens:

**1. Define parent relationships:**
```kotlin
interface DeepLinkKey : NavKey {
    val parent: NavKey
}

@Serializable
data object HomeRoute : NavKey

@Serializable
data object ProductListRoute : DeepLinkKey {
    override val parent: NavKey = HomeRoute
}

@Serializable
data class ProductDetail(val productId: String) : DeepLinkKey {
    override val parent: NavKey = ProductListRoute
}
```

**2. Build the synthetic back stack:**
```kotlin
fun buildSyntheticBackStack(deepLinkKey: NavKey): List<NavKey> = buildList {
    var current: NavKey? = deepLinkKey
    while (current != null) {
        add(0, current)
        current = (current as? DeepLinkKey)?.parent
    }
}
```

**3. Use with NavDisplay:**
```kotlin
val syntheticBackStack = buildSyntheticBackStack(deepLinkKey)

setContent {
    val backStack = rememberNavBackStack(*syntheticBackStack.toTypedArray())

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = entryProvider { /* ... */ }
    )
}
```

For `ProductDetail("abc")`, the back stack becomes: `[HomeRoute, ProductListRoute, ProductDetail("abc")]` — pressing Back walks through parents naturally.

### Task Management

Deep link behavior differs based on whether the Activity is started in a new task or the existing task:

**Detect the task:**
```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    val isNewTask = intent.flags and Intent.FLAG_ACTIVITY_NEW_TASK != 0
    val deepLinkKey = parseDeepLink(intent)

    if (isNewTask) {
        // Build synthetic back stack for proper Up/Back
        val syntheticBackStack = buildSyntheticBackStack(deepLinkKey)
        // Use syntheticBackStack with rememberNavBackStack(...)
    } else {
        // Add deep link destination to existing back stack
        // Use deepLinkKey directly with rememberNavBackStack(...)
    }
}
```

**Up button behavior on original task** — restart the Activity in a new task so Up navigates within the app:
```kotlin
fun navigateUp(deepLinkKey: NavKey, activity: Activity) {
    val parentKey = (deepLinkKey as? DeepLinkKey)?.parent

    val intent = Intent(activity, activity::class.java).apply {
        if (parentKey is DeepLinkKey) {
            data = parentKey.toDeepLinkUri()
        }
        addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)
    }

    TaskStackBuilder.create(activity)
        .addNextIntentWithParentStack(intent)
        .startActivities()
    activity.finish()
}
```

**Summary:**

| Scenario | Back | Up | Synthetic back stack? |
|---|---|---|---|
| New task | Parent screen | Parent screen | Yes, on Activity creation |
| Existing task | Previous app/screen | Parent screen (restarts in new task) | Optional |

**Guidelines:**
- Up button never exits the app — disable it on the start destination
- Deep linking simulates manual navigation via synthetic back stack
- The start destination should never show an Up button
