# Navigation

Required: Navigation 3 with type-safe `@Serializable` `NavKey` destinations, feature-defined `Navigator` interfaces, app-module wiring. Kotlin code must align with [kotlin-patterns.md](/references/kotlin-patterns.md). Versions live in `assets/libs.versions.toml.template` (`navigation3` bundle).

Navigation 3 is still under active development; pin a stable version from [Navigation 3 releases](https://developer.android.com/jetpack/androidx/releases/navigation3) before shipping.

## Table of Contents
1. [Navigation3 Architecture](#navigation3-architecture)
2. [Quick Start](#navigation-3-quick-start)
3. [App Navigation Setup](#app-navigation-setup)
4. [Navigation State Management](#navigation-3-state-management)
5. [Navigation invariants](#navigation-invariants)
6. [Navigation Flow](#navigation-flow)
7. [Migration](#migration)
8. [Animations](#animations)
9. [Scenes & Custom Layouts](#scenes--custom-layouts)
10. [Deep Links](#deep-links)
11. [Conditional Navigation](#conditional-navigation)
12. [Returning Results](#returning-results)
13. [ViewModel Scoping](#viewmodel-scoping)
14. [Adaptive Quality and Large Screens](#adaptive-quality-and-large-screens)

## Navigation3 Architecture

Feature-level navigation components (`AuthDestination`, `AuthNavigator`, `AuthGraph`) are created as part of the feature module setup in [modularization.md → Create Feature Module → Step 4](/references/modularization.md).

Required:
- Each feature owns its `Destination` sealed interface (implements `NavKey`, `@Serializable`) and a `Navigator` interface.
- App module owns the back stack, implements every feature's `Navigator`, and registers entries in a single `NavDisplay`.
- Top-level chrome uses `NavigationSuiteScaffold` so bar/rail/drawer tracks window size automatically.
- Multi-pane layouts use `NavigableListDetailPaneScaffold` / `NavigableSupportingPaneScaffold` from Material 3 Adaptive - never hand-rolled width branching.
- Predictive back is on by default (required on API 36).

## Adaptive Quality and Large Screens

`NavigationSuiteScaffold` and pane scaffolds decide *where* navigation chrome lives; the [Adaptive app guidance](https://developer.android.com/large-screens) defines *how complete* the experience is per form factor.

### Quality tiers

Required floor: tier 3 on every build. Target tier 2 for productivity and tablet-heavy audiences. Target tier 1 only when foldables, Chromebooks, or stylus-first workflows are first-class.

| Tier                            | Required behaviour                                                                               |
|---------------------------------|--------------------------------------------------------------------------------------------------|
| **3 - Adaptive ready**          | No letterboxing, handles rotation and resizing, split-screen works, basic keyboard/mouse         |
| **2 - Adaptive optimized**      | Responsive layouts at all widths, stronger keyboard shortcuts and hover, state survives resize   |
| **1 - Adaptive differentiated** | Multitasking (drag and drop where relevant), fold postures, stylus, desktop-style windowing      |

### Width and layout (with Navigation3)

| Window width           | Typical layout (Material adaptive)                   |
|------------------------|------------------------------------------------------|
| Compact (under 600 dp) | Bottom bar, single pane                              |
| Medium (600-840 dp)    | Navigation rail; add list-detail when content needs split panes |
| Expanded (over 840 dp) | Rail or persistent drawer, list-detail or multi-pane |

Use `WindowSizeClass` / `currentWindowAdaptiveInfo()` for custom splits; use `NavigationSuiteScaffold` so bar vs rail vs drawer tracks size without manual branching.

### Configuration and state

Handle **configuration changes** without losing user context: rotation, fold/unfold, multi-window resize, split-screen enter/exit, hardware keyboard attach/detach.

- Keep UI state in **ViewModel** and process death in **SavedStateHandle** (see [compose-patterns.md](/references/compose-patterns.md) and modularization docs).
- Test with **Don't keep activities** during development to flush out lost state.

### Foldables

| Posture                                 | Notes for UI                                                  |
|-----------------------------------------|---------------------------------------------------------------|
| Flat / open                             | Treat like tablet or large phone                              |
| Tabletop / half-open (horizontal hinge) | Avoid primary actions on the hinge; split content per segment |
| Book / vertical hinge                   | Same: no critical tap targets on the fold                     |
| Folded closed                           | Single outer display; navigation matches compact patterns |

Use Jetpack **WindowManager** (`androidx.window`) when you need explicit fold or posture; not for everyday bar vs rail decisions.

### Pointer, keyboard, and desktop expectations

| Input            | Expectation                                                                               |
|------------------|-------------------------------------------------------------------------------------------|
| Keyboard         | Tab order matches visual order; Enter/Space activate; arrow keys in lists                 |
| Mouse / trackpad | Hover states on clickable rows; scroll wheels work; context menus where users expect them |
| Stylus           | Pressure/tilt only if you draw; otherwise ignore safely                                   |

Large screens are often **not** touch-only. Do not rely on swipe-only shortcuts without a visible alternative.

### Multi-window

Assume the app **does not own the full display**. Support minimum resize width (on the order of ~220 dp per platform guidance), preserve state across bounds changes, and avoid modal flows that break when the window is half width.

### Testing matrix (manual)

| Scenario                          | Priority                          |
|-----------------------------------|-----------------------------------|
| Phone portrait and landscape      | Required                          |
| Tablet portrait and landscape     | Required if you ship large-screen |
| Foldable fold/unfold              | High if you target foldables      |
| Desktop / Chromebook windowed     | Medium for those form factors     |
| Split-screen and free-form resize | Required for tier 2+              |

## Navigation 3 Quick Start

Navigation 3 uses type-safe data classes as navigation keys. Minimal wiring:

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
            // Top-level route: swap the active tab instead of pushing a child.
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

## Navigation invariants

1. **Feature Independence**: Features define `Navigator` interfaces
2. **Central Coordination**: App module implements all navigators
3. **Type-Safe Routes**: Routes implement `NavKey` with `@Serializable` and `@Immutable`
4. **Explicit State Management**: `NavigationState` + `Navigator` manage navigation state
5. **Adaptive Navigation**: `NavigationSuiteScaffold` auto-switches between bar/rail/drawer based on window size

## Navigation Flow

End-to-end flow diagrams (UI → data → navigation): [architecture.md](/references/architecture.md).

## Migration

Navigation 2.x → Navigation3: [migration.md → Navigation 2.x to Navigation3](/references/migration.md#navigation-2x-to-navigation3).

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

**Required:**
- Pass `DialogSceneStrategy<NavKey>()` as `sceneStrategy` to `NavDisplay`.
- Mark dialog entries with `metadata = DialogSceneStrategy.dialog(DialogProperties(...))`.
- Dialog entries render as overlays above the previous entry.
- Wrap navigations that open dialogs in `dropUnlessResumed` to block double taps during transitions.

### Bottom Sheet Navigation

Navigation 3 ships no first-party `BottomSheetSceneStrategy`. Use the custom strategy below: it renders the top entry inside a Material 3 `ModalBottomSheet` and keeps the previous entry visible underneath.

```kotlin
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.navigation3.runtime.NavEntry
import androidx.navigation3.scene.Scene
import androidx.navigation3.scene.SceneStrategy
import androidx.navigation3.scene.SinglePaneSceneStrategy

private const val BOTTOM_SHEET_KEY = "BottomSheetSceneStrategy"

class BottomSheetSceneStrategy<T : Any>(
    private val onDismiss: () -> Unit,
) : SceneStrategy<T> {

    override fun SceneStrategyScope<T>.calculateScene(
        entries: List<NavEntry<T>>,
    ): Scene<T>? {
        val top = entries.lastOrNull() ?: return null
        if (top.metadata[BOTTOM_SHEET_KEY] != true) return null

        val previous = entries.dropLast(1)
        return object : Scene<T> {
            override val key: Any = top.contentKey
            override val entries: List<NavEntry<T>> = listOf(top)
            override val previousEntries: List<NavEntry<T>> = previous
            override val content: @Composable () -> Unit = {
                previous.lastOrNull()?.Content()

                val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)
                ModalBottomSheet(
                    onDismissRequest = onDismiss,
                    sheetState = sheetState,
                ) {
                    top.Content()
                }
            }
        }
    }

    companion object {
        fun bottomSheet(): Map<String, Any> = mapOf(BOTTOM_SHEET_KEY to true)
    }
}

@Composable
fun BottomSheetExample() {
    val backStack = rememberNavBackStack(HomeRoute)
    val bottomSheetStrategy = remember {
        BottomSheetSceneStrategy<NavKey>(onDismiss = { backStack.removeLastOrNull() })
    }

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        sceneStrategy = bottomSheetStrategy,
        entryProvider = entryProvider {
            entry<HomeRoute> {
                HomeScreen(
                    onShowFilters = dropUnlessResumed { backStack.add(FiltersRoute) }
                )
            }
            entry<FiltersRoute>(
                metadata = BottomSheetSceneStrategy.bottomSheet()
            ) {
                FiltersBottomSheet(
                    onApply = { backStack.removeLastOrNull() }
                )
            }
        }
    )
}
```

**Required:**
- Mark sheet entries with `metadata = BottomSheetSceneStrategy.bottomSheet()`; unmarked entries keep `SinglePaneSceneStrategy`.
- Bind `onDismissRequest` to `backStack.removeLastOrNull()` so scrim and swipe-dismiss stay stack-driven — no parallel boolean dismiss flags.
- Predictive back follows the back stack without extra glue.

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
- `ListDetailSceneStrategy.listPane(detailPlaceholder = { ... })` — marks the list pane; supply `detailPlaceholder` when the detail pane can be empty
- `ListDetailSceneStrategy.detailPane()` - marks entry as detail pane
- `ListDetailSceneStrategy.extraPane()` - marks entry as extra pane (three-pane layout)

The Material3 `ListDetailSceneStrategy` automatically handles pane arrangement, predictive back, and window size adaptation. For supporting-pane layouts, use `rememberSupportingPaneSceneStrategy()` with matching metadata.

## Deep Links

Required: parse `Intent.data` into a `NavKey`, push the result onto the back stack, and keep Up/Back aligned with [Principles of Navigation](https://developer.android.com/guide/navigation/principles).

### Parsing an Intent into a NavKey

Required: decode the incoming `Intent` data URI with `kotlinx.serialization` and the Navigation 3 `DeepLinkPattern` / `KeyDecoder` pipeline.

Required: declare every supported URI in `deepLinkPatterns`:
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

Required: parse in `Activity.onCreate` (or the shared entry used by `onCreate` and `onNewIntent`):
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

Required roles per parse:

- `DeepLinkPattern` maps a URI pattern to a `NavKey` serializer; `{path}` and `?query` placeholders bind to `@Serializable` fields.
- `DeepLinkRequest` materialises path segments and query parameters for matching.
- `DeepLinkMatcher` selects the first matching pattern.
- `KeyDecoder` decodes matched arguments into the concrete `NavKey`.

### Synthetic Back Stack

Required on the new-task deep-link path: build a synthetic back stack so Up/Back walks parent screens instead of exiting after one pop.

Required: model `DeepLinkKey.parent` for every deep-linked destination:
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

Required: walk `DeepLinkKey.parent` from the leaf key to the root to build the list:
```kotlin
fun buildSyntheticBackStack(deepLinkKey: NavKey): List<NavKey> = buildList {
    var current: NavKey? = deepLinkKey
    while (current != null) {
        add(0, current)
        current = (current as? DeepLinkKey)?.parent
    }
}
```

Required: pass the synthetic list into `rememberNavBackStack` before `NavDisplay`:
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

Required stack shape for `ProductDetail("abc")`: `[HomeRoute, ProductListRoute, ProductDetail("abc")]`; Back pops in reverse order.

### Task Management

Required: branch on `Intent.FLAG_ACTIVITY_NEW_TASK` - new task vs existing task changes whether a synthetic stack is mandatory vs optional.

Required: read `intent.flags` in `onCreate` before branching:
```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    val isNewTask = intent.flags and Intent.FLAG_ACTIVITY_NEW_TASK != 0
    val deepLinkKey = parseDeepLink(intent)

    if (isNewTask) {
        val syntheticBackStack = buildSyntheticBackStack(deepLinkKey)
        // CORRECT: new task - seed stack with syntheticBackStack before NavDisplay.
    } else {
        // CORRECT: existing task - append deepLinkKey to the live stack (or replace per app policy).
    }
}
```

Required on the original task: restart the Activity in a new task so Up stays inside the app:
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

| Scenario      | Back                | Up                                   | Synthetic back stack?     |
|---------------|---------------------|--------------------------------------|---------------------------|
| New task      | Parent screen       | Parent screen                        | Yes, on Activity creation |
| Existing task | Previous app/screen | Parent screen (restarts in new task) | Optional                  |

Forbidden: show Up on the start destination - no in-app parent exists.

Forbidden: route Up out of the app - Up targets only in-app parents (including synthetic-stack parents).

Required: synthetic stack models the manual path from the root destination to the deep-linked key.

### AndroidManifest Setup

Required on the deep-link `Activity`: `android:exported="true"` (mandatory on Android 12+ for any Activity with an intent-filter), `android:launchMode="singleTask"` so re-entering the app reuses the existing Activity via `onNewIntent` (see [onNewIntent for singleTask](#onnewintent-for-singletask)).

Required: keep HTTPS App Links and custom schemes in **separate** `<intent-filter>` blocks. `android:autoVerify="true"` only works on the HTTPS filter and verifies every `<data>` host inside that single filter.

```xml
<!-- app/src/main/AndroidManifest.xml -->
<activity
    android:name=".MainActivity"
    android:exported="true"
    android:launchMode="singleTask">

    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" />
        <data android:host="example.com" />
        <data android:host="www.example.com" />
        <data android:pathPrefix="/products" />
        <data android:pathPrefix="/users" />
        <data android:pathPattern="/orders/.*/items/.*" />
    </intent-filter>

    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" android:host="open" />
    </intent-filter>
</activity>
```

`<data>` matching rules:

| Attribute                     | Use when                                                                             |
|-------------------------------|--------------------------------------------------------------------------------------|
| `android:scheme`              | Required first. Declare once per filter (`https` for App Links).                     |
| `android:host`                | Declare once per host. List every host in the same `autoVerify` filter.              |
| `android:pathPrefix`          | Default. Matches `/products`, `/products/123`, `/products/anything`.                 |
| `android:pathSuffix`          | Use when the dynamic segment is the prefix (`/share/abc.png`, suffix `.png`).        |
| `android:path`                | Use for an exact-match URL with no parameters (`/about`).                            |
| `android:pathPattern`         | Use when prefix/suffix cannot express the rule. `.*` = any chars, `\\*` = literal *. |
| `android:pathAdvancedPattern` | Use for full regex (`[a-z]{2,4}/.*`) on API 31+. Falls back to no-match below 31.    |

Required: every `<data>` host inside an `autoVerify` filter must be served by a Digital Asset Links file (see [App Links Verification](#app-links-verification)). On Android 11 and lower, **one** unverifiable host fails verification for **all** hosts in that filter.

Forbidden: `android:autoVerify="true"` on a custom-scheme filter. App Links verification is HTTPS-only; the attribute is silently ignored on other schemes (see [Custom-Scheme Deep Linking](#custom-scheme-deep-linking)).

Forbidden: combining `<data android:scheme="https" />` and `<data android:scheme="myapp" />` in one filter - every scheme/host pair becomes a verification target and the non-https schemes break `autoVerify`.

Required: keep `pathPrefix` entries narrow. Forbidden: `pathPrefix="/"` on production builds - claims every URL on the host and the system rejects the verification batch.

### onNewIntent for singleTask

Required when `android:launchMode="singleTask"`: implement `onNewIntent` so a deep link delivered to an already-running Activity updates the back stack instead of being dropped on the floor.

Required: route both the `onCreate` initial intent and every subsequent `onNewIntent` through the same `parseDeepLink` function so behaviour stays consistent.

```kotlin
// app/MainActivity.kt
class MainActivity : ComponentActivity() {

    private val pendingDeepLink = mutableStateOf<NavKey?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val initialKey = parseDeepLink(intent) ?: HomeRoute

        setContent {
            val backStack = rememberNavBackStack(initialKey)

            LaunchedEffect(Unit) {
                snapshotFlow { pendingDeepLink.value }
                    .filterNotNull()
                    .collect { key ->
                        backStack.add(key)
                        pendingDeepLink.value = null
                    }
            }

            NavDisplay(
                backStack = backStack,
                onBack = { backStack.removeLastOrNull() },
                entryProvider = entryProvider { /* ... */ }
            )
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // CORRECT: setIntent so any later getIntent() read sees the new URI, not the original.
        setIntent(intent)
        parseDeepLink(intent)?.let { pendingDeepLink.value = it }
    }

    private fun parseDeepLink(intent: Intent): NavKey? {
        val uri = intent.data ?: return null
        if (!DeepLinkValidator.validate(uri)) return null
        val request = DeepLinkRequest(uri)
        val match = deepLinkPatterns.firstNotNullOfOrNull { pattern ->
            DeepLinkMatcher(request, pattern).match()
        } ?: return null
        return KeyDecoder(match.args).decodeSerializableValue(match.serializer)
    }
}
```

Forbidden: reading `intent.data` directly inside Composables - `intent` does not change reference when `onNewIntent` fires; route the new URI through state (`mutableStateOf`, `Channel`, `SharedFlow`).

Forbidden: omitting `setIntent(intent)` in `onNewIntent` - leaves stale `getIntent()` results for any later code path (notification action handlers, restored process death).

Use when: `Intent.FLAG_ACTIVITY_NEW_TASK` is set - seed the stack from [Synthetic Back Stack](#synthetic-back-stack) before the first frame.

Use when: the Activity stays in the existing task - append the parsed key to the live back stack (or replace the stack per app policy).

### App Links Verification

Required for HTTPS deep links: publish a Digital Asset Links file (`assetlinks.json`) on every host declared in the `autoVerify` intent-filter.

Forbidden: ship `autoVerify` hosts without a reachable `assetlinks.json` - opens the browser or the disambiguation dialog.

#### Server contract

Required, all of:

| Rule             | Value                                                                                           |
|------------------|-------------------------------------------------------------------------------------------------|
| URL              | `https://<host>/.well-known/assetlinks.json` (exact path)                                       |
| Scheme           | HTTPS only. HTTP is rejected.                                                                   |
| Status           | HTTP 200. **Any redirect fails verification.**                                                  |
| Content-Type     | `application/json`                                                                              |
| Auth             | None. No cookies, no Basic auth, no IP allowlist.                                               |
| Apex consistency | `https://example.com.` (with trailing dot) must serve identical bytes to `https://example.com`. |

Forbidden redirects: `http://example.com` → `https://example.com`, `example.com` → `www.example.com`. Both kill verification for the entire app on Android 12+.

#### `assetlinks.json` template

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.example.app",
      "sha256_cert_fingerprints": [
        "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99",
        "11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF:00"
      ]
    }
  }
]
```

Required: every fingerprint string is **uppercase**, colon-separated SHA-256. Lowercase fingerprints fail silently.

Required fingerprints: include every certificate that signs an APK that ships to a real device - Play-managed signing key, upload key (only when not enrolled in Play App Signing), debug key (for QA tracks).

#### Where to get the SHA-256

Use Play App Signing when enrolled - local `keytool` output is **not** the runtime fingerprint:

| App-signing setup                       | Source of the SHA-256                                                                                                                        |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Play App Signing (default for new apps) | Play Console → Release → Setup → App signing → "App signing key certificate". Copy the SHA-256. Console also exposes the upload-key SHA-256. |
| Self-managed release keystore           | `keytool -list -v -keystore release.jks -alias <alias>`. Copy the `SHA256:` line.                                                            |
| Debug builds                            | `keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android`.                                            |

Forbidden: shipping only the upload-key SHA-256 when Play App Signing is enrolled - installs from the Play Store carry the Play-managed signature, not the upload signature, and verification fails on every Play install.

#### Multi-app per domain

Required when several apps share a host (separate consumer + B2B builds, vendor split): one statement file with multiple `target` blocks. Different apps may handle different path prefixes via their own intent-filters.

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.example.consumer",
      "sha256_cert_fingerprints": ["AA:BB:..."]
    }
  },
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.example.b2b",
      "sha256_cert_fingerprints": ["CC:DD:..."]
    }
  }
]
```

#### Multi-domain per app

Required when one app handles several hosts: publish an identical `assetlinks.json` at each `https://<host>/.well-known/assetlinks.json` and list every host in the same `autoVerify` intent-filter (see [AndroidManifest Setup](#androidmanifest-setup)).

Forbidden on Android 11 and lower: declaring a host you cannot serve `assetlinks.json` for - fails verification for **every** host in that filter (all-or-nothing).

#### Verify the file is reachable

Required: hit the Digital Asset Links REST endpoint from CI or a laptop before blocking on-device `pm get-app-links` - no device required.

```bash
curl 'https://digitalassetlinks.googleapis.com/v1/statements:list?\
source.web.site=https://example.com&\
relation=delegate_permission/common.handle_all_urls'
```

Required JSON shape in the response: a non-empty `statements` array containing the package name and uppercase fingerprint that match the manifest. Empty array = file unreachable, malformed, or wrong content-type.

Per-device verification (`pm set-app-links`, `pm verify-app-links --re-verify`, `pm get-app-links`) and the return-code legend: [testing.md → Testing Deep Links](/references/testing.md#testing-deep-links).

### Dynamic App Links (Android 15+, API 35)

API floor: 35. Devices with Google Play services periodically refresh `assetlinks.json` and merge server-side rules with manifest filters. Older devices ignore the dynamic block.

Required: dynamic rules can only **narrow** what the manifest declares. Set the broadest scope (scheme + host) in the manifest; refine path / query / fragment server-side.

Forbidden: relying on dynamic rules to add a host or scheme not in the manifest. The system silently drops them.

#### `dynamic_app_link_components` shape

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.example.app",
      "sha256_cert_fingerprints": ["AA:BB:..."]
    },
    "relation_extensions": {
      "delegate_permission/common.handle_all_urls": {
        "dynamic_app_link_components": [
          {"/": "/products/*"},
          {"/": "/shoes", "?": {"in_app": "true"}},
          {"#": "app"},
          {"?": {"dl": "*"}},
          {"/": "/internal/*", "exclude": true},
          {"/": "*"}
        ]
      }
    }
  }
]
```

Required: each rule object may set any of these keys; every set key must match the URL:

| Key         | Type    | Matches                                                                                                                            |
|-------------|---------|------------------------------------------------------------------------------------------------------------------------------------|
| `"/"`       | string  | URL path. Wildcards: `*` (zero or more chars), `?` (single char), `?*` (one or more chars).                                        |
| `"#"`       | string  | URL fragment (after `#`). Same wildcards as path.                                                                                  |
| `"?"`       | object  | Query parameter dict. Every entry must match a `key=value` pair in the URL. Order does not matter; extra query params are allowed. |
| `"exclude"` | boolean | When `true`, matching URLs **do not** open the app. Default `false`.                                                               |

#### Ordering rules

Required: declare more specific rules first. Evaluation stops at the first match.

```json
{"/": "/path1"},
{"/": "*", "exclude": true}
```

Outcome for `{"/": "/path1"}` then `{"/": "*", "exclude": true}`: `/path1` opens the app; every other path is excluded.

```json
{"/": "*", "exclude": true},
{"/": "/path1"}
```

Outcome for `{"/": "*", "exclude": true}` then `{"/": "/path1"}`: no URL opens the app - the `*` exclude rule matches first for every path including `/path1`.

#### "Exclude one path, allow the rest"

Required pattern: exclude rule, then catch-all allow rule. Omitting the catch-all excludes every URL not matched by an earlier rule.

```json
{"/": "/admin/*", "exclude": true},
{"/": "*"}
```

Forbidden: ending the list with only excludes. Unmatched URLs default to **excluded**, breaking every host the manifest still declares.

#### Failure modes

Required: validate JSON server-side before publishing. Malformed `relation_extensions` or empty `dynamic_app_link_components` makes the device discard all dynamic rules and fall back to the manifest filter alone - silently.

Required after every server-side rule change: force a re-fetch with `adb shell pm verify-app-links --re-verify com.example.app` (per-device cache; eventual consistency without it). Production devices pick up the new file on their own refresh schedule.

Required: cross-check live rules against the Digital Asset Links REST response; append `&return_relation_extensions=true`:

```bash
curl 'https://digitalassetlinks.googleapis.com/v1/statements:list?\
source.web.site=https://example.com&\
relation=delegate_permission/common.handle_all_urls&\
return_relation_extensions=true'
```

Required: the REST JSON exposes `dynamic_app_link_components` under the same relation key as the published `assetlinks.json`. Empty or missing field means devices never load those rules.

### DomainVerificationManager Runtime Check

API floor: 31. Required guard: `Build.VERSION.SDK_INT >= Build.VERSION_CODES.S` before any `DomainVerificationManager` call.

Use `DomainVerificationManager` when: surfacing a Settings CTA for hosts stuck in `DOMAIN_STATE_NONE`, or hiding in-app copy that assumes verified App Links when the host map says otherwise.

```kotlin
// app/deeplink/AppLinkVerificationStatus.kt
import android.content.Context
import android.content.pm.verify.domain.DomainVerificationManager
import android.content.pm.verify.domain.DomainVerificationUserState
import android.os.Build
import androidx.annotation.RequiresApi

data class AppLinkStatus(
    val verified: List<String>,
    val userSelected: List<String>,
    val unapproved: List<String>,
)

@RequiresApi(Build.VERSION_CODES.S)
fun Context.appLinkStatus(): AppLinkStatus {
    val manager = getSystemService(DomainVerificationManager::class.java)
    val state = manager.getDomainVerificationUserState(packageName) ?: return AppLinkStatus(emptyList(), emptyList(), emptyList())

    val grouped = state.hostToStateMap.entries.groupBy { (_, value) ->
        when (value) {
            DomainVerificationUserState.DOMAIN_STATE_VERIFIED -> "verified"
            DomainVerificationUserState.DOMAIN_STATE_SELECTED -> "selected"
            else -> "unapproved"
        }
    }
    return AppLinkStatus(
        verified = grouped["verified"].orEmpty().map { it.key },
        userSelected = grouped["selected"].orEmpty().map { it.key },
        unapproved = grouped["unapproved"].orEmpty().map { it.key },
    )
}
```

Required when `unapproved` is non-empty: open `Settings.ACTION_APP_OPEN_BY_DEFAULT_SETTINGS` for the package. No API grants verification without user or verifier action.

```kotlin
// app/deeplink/AppLinkSettings.kt
import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.core.net.toUri

fun Context.openAppLinkSettings() {
    val intent = Intent(
        Settings.ACTION_APP_OPEN_BY_DEFAULT_SETTINGS,
        "package:$packageName".toUri()
    ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    startActivity(intent)
}
```

Required in Compose: gate the banner on API 31+ (`Build.VERSION.SDK_INT >= Build.VERSION_CODES.S`) before calling `appLinkStatus()`.

```kotlin
@Composable
fun AppLinkApprovalBanner(onOpenSettings: () -> Unit) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return

    val context = LocalContext.current
    val status = remember { context.appLinkStatus() }

    if (status.unapproved.isEmpty()) return

    Banner(
        message = "Approve ${status.unapproved.size} link(s) in Settings",
        action = "Open settings",
        onAction = onOpenSettings,
    )
}
```

Forbidden: caching the result across process restarts - verification state changes when the user toggles defaults, when the app re-runs verification, or when Play re-installs.

Forbidden: show the Settings CTA when every declared host is already `DOMAIN_STATE_VERIFIED` - nothing left to approve.

Required: map `hostToStateMap` integer values using this table:

| Constant                         | Meaning                                                                       |
|----------------------------------|-------------------------------------------------------------------------------|
| `DOMAIN_STATE_VERIFIED`          | Auto-verified via Digital Asset Links. App opens the link without a dialog.   |
| `DOMAIN_STATE_SELECTED`          | User manually picked this app as the default for the host in system settings. |
| `DOMAIN_STATE_NONE`              | Not verified and not user-selected. Link goes to browser or disambiguation.   |

### URI Pattern Matching

Required: register one `DeepLinkPattern` per supported URI shape; placeholders bind to `@Serializable` fields on the `NavKey`.

```kotlin
// app/deeplink/DeepLinkPatterns.kt

private const val BASE_URL = "https://example.com"

internal val deepLinkPatterns: List<DeepLinkPattern<out NavKey>> = listOf(
    // Exact match
    DeepLinkPattern(
        serializer = HomeRoute.serializer(),
        pattern = "$BASE_URL/home".toUri()
    ),
    // Path parameter: /products/{productId}
    DeepLinkPattern(
        serializer = ProductDetail.serializer(),
        pattern = "$BASE_URL/products/{productId}".toUri()
    ),
    // Multiple path parameters: /orders/{orderId}/items/{itemId}
    DeepLinkPattern(
        serializer = OrderItemDetail.serializer(),
        pattern = "$BASE_URL/orders/{orderId}/items/{itemId}".toUri()
    ),
    // Query parameters: /search?query={query}&category={category}
    DeepLinkPattern(
        serializer = SearchRoute.serializer(),
        pattern = "$BASE_URL/search?query={query}&category={category}".toUri()
    ),
    // Custom scheme: myapp://open/profile/{userId}
    DeepLinkPattern(
        serializer = UserProfile.serializer(),
        pattern = "myapp://open/profile/{userId}".toUri()
    ),
)
```

`{placeholder}` names must match the `@Serializable` field names in the corresponding `NavKey`:
```kotlin
@Serializable
data class OrderItemDetail(val orderId: String, val itemId: String) : NavKey
```

### Deep Link Security

Required: treat every deep link as untrusted input - validate, allowlist, then navigate.

```kotlin
// app/deeplink/DeepLinkValidator.kt
object DeepLinkValidator {

    private val ALLOWED_HOSTS = setOf("example.com", "www.example.com")
    private val ALLOWED_SCHEMES = setOf("https", "myapp")

    fun validate(uri: Uri): Boolean {
        if (uri.scheme !in ALLOWED_SCHEMES) return false
        if (uri.scheme == "https" && uri.host !in ALLOWED_HOSTS) return false
        return true
    }

    fun sanitizeArgument(value: String, maxLength: Int = 256): String {
        return value.take(maxLength).replace(Regex("[^a-zA-Z0-9_\\-.]"), "")
    }
}
```

Wire in `Activity`:
```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    val deepLinkKey: NavKey = intent.data?.let { uri ->
        if (!DeepLinkValidator.validate(uri)) return@let null

        val request = DeepLinkRequest(uri)
        val match = deepLinkPatterns.firstNotNullOfOrNull { pattern ->
            DeepLinkMatcher(request, pattern).match()
        }
        match?.let {
            KeyDecoder(match.args).decodeSerializableValue(match.serializer)
        }
    } ?: HomeRoute

    // ...
}
```

Handle `onNewIntent` for `singleTask`:
```kotlin
override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    intent.data?.let { uri ->
        if (DeepLinkValidator.validate(uri)) {
            val key = parseDeepLink(uri)
            // CORRECT: push key or reset stack - match onNewIntent for singleTask wiring.
        }
    }
}
```

Required: validate `scheme` and `host` against allowlists before parsing.

Required: sanitize path segments and query values - attacker-controlled.

Required: gate protected `NavKey` targets on auth state ([Conditional Navigation](#conditional-navigation)).

Forbidden: load deep-link URLs in a `WebView` without an allowlist that matches the parser.

Use HTTPS App Links for untrusted ingress. Forbidden: custom URI schemes as the only entry for auth, payments, or account recovery.

Required: log deep-link attempts for anomaly detection ([crashlytics.md](references/crashlytics.md)).

### Custom-Scheme Deep Linking

Use HTTPS App Links for production ingress. Use a custom scheme (`myapp://`) only when:

- The OAuth library or third-party SDK requires a non-HTTPS redirect URI.
- A vendor-internal IPC link must reach a sibling app on the same device.
- Internal QA shortcuts that never ship to production.

Forbidden in app code for: payments, auth tokens, password reset, magic-link sign-in, anything that grants account access. Custom schemes are unverifiable - any other installed app can register the same scheme and silently steal the URL.

Required: declare the custom scheme in a **separate** `<intent-filter>` from the HTTPS App Links filter (see [AndroidManifest Setup](#androidmanifest-setup)). Mixing schemes inside one filter breaks `autoVerify` for the HTTPS hosts.

```xml
<activity android:name=".MainActivity" android:exported="true" android:launchMode="singleTask">

    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" />
        <data android:host="example.com" />
        <data android:pathPrefix="/products" />
    </intent-filter>

    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="myapp" android:host="open" />
    </intent-filter>
</activity>
```

Forbidden: `android:autoVerify="true"` on a custom-scheme filter - silently ignored. Verification is HTTPS-only.

Required: route the custom scheme through the same `DeepLinkPattern` list and `DeepLinkValidator` allowlist as the HTTPS patterns. The validator's `ALLOWED_SCHEMES` set decides which schemes survive parsing.

```kotlin
DeepLinkPattern(
    serializer = UserProfile.serializer(),
    pattern = "myapp://open/profile/{userId}".toUri()
),
```

Required when both HTTPS and a custom scheme reach the same `NavKey`: use HTTPS in every outbound link (email, SMS, push). Use the custom scheme only for intra-device callbacks where no HTTPS URL exists.

Required for inbound custom-scheme links: validate the host as well as the scheme. `myapp://` with no `host` constraint matches `myapp://anything`, including paths an attacker can craft to confuse the parser.

Custom-scheme `adb shell am start` probes: [testing.md → Testing Deep Links](/references/testing.md#testing-deep-links).

### Testing Deep Links

ADB, REST checks, instrumented `onNewIntent`, and host-state tables: [testing.md → Testing Deep Links](/references/testing.md#testing-deep-links).

### Troubleshooting Deep Links

Required: match a symptom row, run the linked ADB or REST check from [testing.md → Testing Deep Links](/references/testing.md#testing-deep-links), then edit manifest or server data.

| Symptom                                                       | Likely cause                                                                                           | Fix                                                                                                                                                  |
|---------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|
| Link opens browser instead of app                             | `assetlinks.json` unreachable, malformed, or fingerprint mismatch.                                     | Hit the Digital Asset Links REST endpoint (see [App Links Verification](#app-links-verification)). Confirm uppercase SHA-256 and `application/json`. |
| Disambiguation dialog appears every time                      | User previously chose another handler, or hosts are only `DOMAIN_STATE_SELECTED`.                      | `pm set-app-links --package com.example.app 0 all` then `pm verify-app-links --re-verify com.example.app`.                                         |
| Lowercase fingerprint in `assetlinks.json`                    | Generator produced lowercase, or hand-edited.                                                          | Convert to uppercase, colon-separated. Lowercase fails silently.                                                                                     |
| Debug APK ignores deep link                                   | Debug fingerprint missing from `assetlinks.json`.                                                      | Add the debug-keystore SHA-256 alongside release/Play fingerprints.                                                                                  |
| Play-installed APK ignores deep link, side-loaded build works | Only the upload-key SHA-256 is published; runtime install carries the Play-managed signature.          | Add the Play App Signing key SHA-256 from Play Console → Setup → App signing.                                                                        |
| Verification works for one host, fails for others             | One host in the same `autoVerify` filter has no `assetlinks.json`. Android 11 and lower fails the lot. | Publish the file on every host, or split unverifiable hosts into a separate filter without `autoVerify`.                                             |
| Verification fails after server change                        | HTTP→HTTPS redirect, apex→www redirect, or `Content-Type: text/html`.                                  | Serve the file directly with HTTP 200 and `application/json`. No redirects of any kind.                                                              |
| Apex domain works, `www` does not (or vice-versa)             | Hosts treated as separate; only one has the file.                                                      | Publish the same JSON at both `https://example.com/.well-known/assetlinks.json` and `https://www.example.com/.well-known/assetlinks.json`.           |
| `intent.data` is `null` after `onNewIntent`                   | `setIntent(intent)` not called.                                                                        | See [onNewIntent for singleTask](#onnewintent-for-singletask) - the new intent must replace the cached one.                                          |
| Activity restarts on every deep link                          | `launchMode` is `standard` or `singleTop`.                                                             | Set `android:launchMode="singleTask"` on the deep-link Activity.                                                                                     |
| Deep link drops the user on a screen with no Up target        | No synthetic back stack on the new-task path.                                                          | Build one (see [Synthetic Back Stack](#synthetic-back-stack)) and use it when `Intent.FLAG_ACTIVITY_NEW_TASK` is present.                            |
| `pathPattern` matches unintended URLs                         | `.*` is greedy and matches `/anything`.                                                                | Anchor with explicit segments: `/orders/[^/]+/items/[^/]+`.                                                                                          |
| Custom-scheme link silently hijacked by another app           | Custom schemes are unverifiable by design.                                                             | Move security-critical flows (auth, payments, magic links) to HTTPS App Links. See [Custom-Scheme Deep Linking](#custom-scheme-deep-linking).        |
| Dynamic-rule update on Android 15+ not taking effect          | Server cache; verifier has not re-fetched.                                                             | `pm verify-app-links --re-verify com.example.app`. See [Dynamic App Links](#dynamic-app-links-android-15-api-35).                                    |
| `pm get-app-links` returns `none` on every host               | Verifier has not run yet, or device offline.                                                           | Wait at least 20 seconds after install. Confirm network. Re-run `pm verify-app-links --re-verify`.                                                   |

Forbidden: editing the manifest before reading `pm get-app-links` output. The status field tells you whether the failure is server-side (fingerprint, redirect) or client-side (filter, scheme, path).

## Conditional Navigation

Redirect users to a different flow based on app state (e.g., authentication, onboarding). The pattern uses a `requiresLogin` flag on navigation keys and a redirect mechanism.

### Define Auth-Gated Keys

```kotlin
@Serializable
sealed class AppNavKey(val requiresLogin: Boolean = false) : NavKey

@Serializable
data object Home : AppNavKey()

@Serializable
data object Profile : AppNavKey(requiresLogin = true)

@Serializable
data class Login(val redirectToKey: AppNavKey? = null) : AppNavKey()
```

### Navigator with Auth Check

```kotlin
class AppNavigator(
    private val backStack: NavBackStack<AppNavKey>,
    private val isLoggedIn: () -> Boolean,
    private val onNavigateToRestrictedKey: (AppNavKey) -> Login
) {
    fun navigate(route: AppNavKey) {
        if (route.requiresLogin && !isLoggedIn()) {
            backStack.add(onNavigateToRestrictedKey(route))
        } else {
            backStack.add(route)
        }
    }

    fun goBack() {
        backStack.removeLastOrNull()
    }
}
```

### Wire Up in Composable

```kotlin
@Composable
fun ConditionalNavExample() {
    val backStack = rememberNavBackStack(Home)
    var isLoggedIn by rememberSaveable { mutableStateOf(false) }

    val navigator = remember {
        AppNavigator(
            backStack = backStack,
            isLoggedIn = { isLoggedIn },
            onNavigateToRestrictedKey = { redirectToKey -> Login(redirectToKey) }
        )
    }

    NavDisplay(
        backStack = backStack,
        onBack = { navigator.goBack() },
        entryProvider = entryProvider {
            entry<Home> {
                HomeScreen(
                    isLoggedIn = isLoggedIn,
                    onProfileClick = dropUnlessResumed { navigator.navigate(Profile) },
                    onLoginClick = dropUnlessResumed { navigator.navigate(Login()) }
                )
            }
            entry<Profile> {
                ProfileScreen(
                    onLogout = dropUnlessResumed {
                        isLoggedIn = false
                        navigator.navigate(Home)
                    }
                )
            }
            entry<Login> { key ->
                LoginScreen(
                    onLoginSuccess = dropUnlessResumed {
                        isLoggedIn = true
                        key.redirectToKey?.let { target ->
                            backStack.remove(key)
                            navigator.navigate(target)
                        }
                    }
                )
            }
        }
    )
}
```

**How it works:**
- Navigating to `Profile` while logged out redirects to `Login(redirectToKey = Profile)`
- After successful login, the `Login` entry is removed from the back stack and the user is sent to the original target
- `dropUnlessResumed` prevents navigation during transitions (e.g., double-clicks)
- Use `rememberSaveable` for `isLoggedIn` so auth state survives configuration changes; in production, back this with a ViewModel or repository

## Returning Results

Pass data back from one screen to another. Navigation 3 offers two patterns: event-based (one-shot delivery) and callback-based (via Navigator interface).

### Callback-Based Results

Define the result callback on the Navigator interface and let the app module own the hoisted state.

**1. Feature module defines the callback:**
```kotlin
// feature/picker/navigation/ColorPickerNavigator.kt
interface ColorPickerNavigator {
    fun navigateBackWithColor(color: String)
    fun navigateBack()
}
```

**2. App module implements it by modifying the caller's state:**
```kotlin
// app/navigation/AppNavigation.kt
@Composable
fun AppNavigation() {
    val backStack = rememberNavBackStack(HomeRoute)
    var selectedColor by rememberSaveable { mutableStateOf<String?>(null) }

    val colorPickerNavigator = remember {
        object : ColorPickerNavigator {
            override fun navigateBackWithColor(color: String) {
                selectedColor = color
                backStack.removeLastOrNull()
            }
            override fun navigateBack() {
                backStack.removeLastOrNull()
            }
        }
    }

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = entryProvider {
            entry<HomeRoute> {
                HomeScreen(
                    selectedColor = selectedColor,
                    onPickColor = dropUnlessResumed {
                        backStack.add(ColorPickerRoute)
                    }
                )
            }
            entry<ColorPickerRoute> {
                ColorPickerScreen(navigator = colorPickerNavigator)
            }
        }
    )
}
```

### Event-Based Results

For decoupled result delivery without direct state hoisting, use a result map keyed by the caller's content key:

```kotlin
@Composable
fun EventResultExample() {
    val backStack = rememberNavBackStack(ScreenA)
    val resultMap = remember { mutableMapOf<Any, Any>() }

    NavDisplay(
        backStack = backStack,
        onBack = { backStack.removeLastOrNull() },
        entryProvider = entryProvider {
            entry<ScreenA> {
                val result = resultMap.remove(ScreenA) as? String

                LaunchedEffect(result) {
                    result?.let { name ->
                        // Handle the returned result
                    }
                }

                ScreenAContent(
                    lastResult = result,
                    onRequestName = dropUnlessResumed {
                        backStack.add(ScreenB)
                    }
                )
            }
            entry<ScreenB> {
                ScreenBContent(
                    onReturnName = dropUnlessResumed { name ->
                        resultMap[ScreenA] = name
                        backStack.removeLastOrNull()
                    }
                )
            }
        }
    )
}
```

### State-Based Results (CompositionLocal)

Use when several screens must observe the same result (global "selected filter", multi-step wizard value). Expose the result as **state via a `CompositionLocal`** scoped to the `NavDisplay`. Receivers read the value; producers write it before popping.

```kotlin
class FilterResultHolder {
    var value by mutableStateOf<FilterResult?>(null)
        private set

    fun set(result: FilterResult) { value = result }
    fun consume(): FilterResult? = value.also { value = null }
}

val LocalFilterResult = compositionLocalOf<FilterResultHolder> {
    error("FilterResultHolder not provided")
}

@Composable
fun AppNavigation() {
    val backStack = rememberNavBackStack(HomeRoute)
    val filterResult = remember { FilterResultHolder() }

    CompositionLocalProvider(LocalFilterResult provides filterResult) {
        NavDisplay(
            backStack = backStack,
            onBack = { backStack.removeLastOrNull() },
            entryProvider = entryProvider {
                entry<HomeRoute> {
                    val applied = LocalFilterResult.current.value
                    HomeScreen(
                        appliedFilter = applied,
                        onOpenFilters = dropUnlessResumed { backStack.add(FiltersRoute) }
                    )
                }
                entry<FiltersRoute> {
                    FiltersScreen(
                        onApply = dropUnlessResumed { result ->
                            LocalFilterResult.current.set(result)
                            backStack.removeLastOrNull()
                        }
                    )
                }
            }
        )
    }
}
```

**Required:**
- Scope result holders to the `backStack` (`remember` inside `AppNavigation`) so they survive stack mutations and dispose with `NavDisplay`.
- Receivers **read** `LocalFilterResult.current.value` like any other state — skip `LaunchedEffect` bridges.
- One-shot results expose `consume()` that clears after read; sticky results expose `value` directly.
- One `CompositionLocal` holder per result type — no generic cross-feature result bus.

### Choosing a pattern

| Pattern                        | Use when                                                                                                  | Avoid when                                                                              |
|--------------------------------|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------|
| Callback-based                 | Default. Result is type-safe and the caller already exposes hoisted state.                                | Caller cannot hold the receiving state (cross-feature).                                 |
| Event-based                    | Receiver is decoupled from the Navigator and you only need a one-shot delivery.                           | You need Compose-observable updates or shared state.                                    |
| State-based (CompositionLocal) | Several screens read the same result, or the receiver wants idiomatic Compose state instead of callbacks. | A single caller/receiver pair (use callback-based) or cross-process delivery is needed. |

Default to callback-based; it stays type-safe and matches the `Navigator` interface pattern used everywhere else. Reach for state-based only when multiple consumers are involved.

## ViewModel Scoping

By default, ViewModels are scoped to the Activity. Navigation 3 provides `NavEntryDecorator` to scope ViewModels to individual back stack entries - the ViewModel is created when the entry is added and cleared when it is popped.

### NavEntryDecorators

Add decorators to `NavDisplay` via the `entryDecorators` parameter:

```kotlin
import androidx.lifecycle.viewmodel.navigation3.rememberViewModelStoreNavEntryDecorator
import androidx.navigation3.runtime.rememberSaveableStateHolderNavEntryDecorator
import androidx.navigation3.ui.NavDisplay

NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    entryDecorators = listOf(
        rememberSaveableStateHolderNavEntryDecorator(),
        rememberViewModelStoreNavEntryDecorator()
    ),
    entryProvider = entryProvider {
        // ViewModels created inside entries are now scoped to that entry
    }
)
```

**Built-in decorators:**
- `rememberSaveableStateHolderNavEntryDecorator()` - saves/restores UI state (included by default)
- `rememberViewModelStoreNavEntryDecorator()` - provides a `ViewModelStoreOwner` per entry, so `viewModel()` and `hiltViewModel()` are scoped to the entry's lifetime on the back stack

**Dependency:** `androidx.lifecycle:lifecycle-viewmodel-navigation3` (already in `assets/libs.versions.toml.template`)

### Passing NavKey Arguments to Hilt ViewModels

Navigation 3 uses assisted injection to pass `NavKey` arguments directly to ViewModels:

**1. Define the ViewModel with assisted `NavKey`:**
```kotlin
// feature/products/presentation/ProductDetailViewModel.kt
@HiltViewModel(assistedFactory = ProductDetailViewModel.Factory::class)
class ProductDetailViewModel @AssistedInject constructor(
    @Assisted private val productKey: ProductsDestination.ProductDetail,
    private val getProductUseCase: GetProductUseCase
) : ViewModel() {

    val uiState: StateFlow<ProductDetailUiState> = getProductUseCase(productKey.productId)
        .map { ProductDetailUiState(product = it) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ProductDetailUiState())

    @AssistedFactory
    interface Factory {
        fun create(productKey: ProductsDestination.ProductDetail): ProductDetailViewModel
    }
}
```

**2. Use in the entry with `hiltViewModel`:**
```kotlin
entry<ProductsDestination.ProductDetail> { key ->
    val viewModel = hiltViewModel<ProductDetailViewModel, ProductDetailViewModel.Factory> { factory ->
        factory.create(key)
    }
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    ProductDetailScreen(state = uiState)
}
```

This approach is type-safe, avoids `SavedStateHandle` string-key lookups, and works with Hilt's dependency graph.

### Shared ViewModel Between Screens

Share a ViewModel between a parent and child entry using a custom `NavEntryDecorator`:

**1. Create the shared decorator:**
```kotlin
// app/navigation/SharedViewModelStoreNavEntryDecorator.kt
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.lifecycle.ViewModelStoreOwner
import androidx.lifecycle.viewmodel.compose.LocalViewModelStoreOwner
import androidx.navigation3.runtime.NavEntry
import androidx.navigation3.runtime.NavEntryDecorator

class SharedViewModelStoreNavEntryDecorator : NavEntryDecorator {

    @Composable
    override fun DecorateEntry(entry: NavEntry<*>) {
        val parentKey = entry.metadata[PARENT_KEY] as? Any
        val currentOwner = LocalViewModelStoreOwner.current

        if (parentKey != null && currentOwner != null) {
            // Child entry uses parent's ViewModelStoreOwner
            entry.Content()
        } else {
            entry.Content()
        }
    }

    override fun onPop(contentKey: Any) { }

    companion object {
        private const val PARENT_KEY = "SharedViewModelStore-Parent"

        fun parent(parentContentKey: Any) = mapOf(PARENT_KEY to parentContentKey)
    }
}

@Composable
fun rememberSharedViewModelStoreNavEntryDecorator(): SharedViewModelStoreNavEntryDecorator {
    return remember { SharedViewModelStoreNavEntryDecorator() }
}
```

**2. Use in NavDisplay:**
```kotlin
NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    entryDecorators = listOf(
        rememberSaveableStateHolderNavEntryDecorator(),
        rememberSharedViewModelStoreNavEntryDecorator(),
    ),
    entryProvider = entryProvider {
        entry<ParentScreen>(
            clazzContentKey = { key -> key.toContentKey() },
        ) {
            val viewModel = viewModel<SharedCounterViewModel>()
            ParentContent(count = viewModel.count, onIncrement = { viewModel.count++ })
        }
        entry<ChildScreen>(
            metadata = SharedViewModelStoreNavEntryDecorator.parent(
                ParentScreen.toContentKey()
            ),
        ) {
            val parentViewModel = viewModel<SharedCounterViewModel>()
            ChildContent(parentCount = parentViewModel.count)
        }
    }
)

fun NavKey.toContentKey() = this.toString()
```

The child entry's `viewModel<SharedCounterViewModel>()` call resolves to the same instance as the parent's, because both share the same `ViewModelStoreOwner`.

## Navigation Anti-Patterns

### `hiltViewModel()` Scope Mistakes

```kotlin
// Bad: hiltViewModel() inside a nested composable (wrong scope)
@Composable
fun ProductCard() {
    // ViewModelStore follows the NavEntry — every ProductCard shares one ViewModel.
    // Multiple ProductCards will share the exact same ViewModel instance.
    val viewModel: ProductViewModel = hiltViewModel() 
}

// Good: Pass state and callbacks down from the route/screen level
@Composable
fun ProductCard(product: Product, onClick: () -> Unit) {
    // Pure UI component
}
```

### ViewModel Navigation

```kotlin
// Bad: Passing Navigator to ViewModel (breaks unidirectional data flow and testability)
class AuthViewModel(private val navigator: AuthNavigator) : ViewModel() {
    fun login() {
        // ...
        navigator.navigateToMainApp() // ViewModel shouldn't drive navigation directly
    }
}

// Good: Emit a one-shot event, let the Route composable handle navigation
class AuthViewModel : ViewModel() {
    private val _events = Channel<AuthEvent>()
    val events = _events.receiveAsFlow()

    fun login() {
        // ...
        _events.trySend(AuthEvent.LoginSuccess)
    }
}
```

### Passing Complex Objects in NavKeys

```kotlin
// Bad: Passing large or complex objects in navigation routes
@Serializable
data class ProductDetail(
    val product: Product // Product can exceed SavedStateHandle limits or hold non-Parcelable fields
) : ProductsDestination

// Good: Pass only IDs, fetch data in the destination
@Serializable
data class ProductDetail(
    val productId: String // Small, easily serializable ID
) : ProductsDestination
```
