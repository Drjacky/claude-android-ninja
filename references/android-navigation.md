# Navigation Guide

Navigation3 architecture with type-safe routing, adaptive navigation, and multi-module coordination.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

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
import androidx.navigation3.runtime.NavDisplay
import androidx.navigation3.runtime.rememberNavBackStack

@Composable
fun AppNavigation() {
    val backStack = rememberNavBackStack(
        startDestination = ProductsDestination.ProductsList(categoryId = "all")
    )
    
    // Implement navigator
    val productsNavigator = remember {
        object : ProductsNavigator {
            override fun navigateToDetail(productId: String) {
                backStack.push(ProductsDestination.ProductDetail(productId))
            }
            override fun navigateBack() {
                backStack.pop()
            }
        }
    }
    
    // Define routes
    NavDisplay(backStack = backStack) {
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
