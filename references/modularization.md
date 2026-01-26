# Modularization Guide

Based on our modern Android multi-module architecture with Navigation3, Jetpack Compose, and strict dependency rules.
All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

## Table of Contents
1. [Benefits](#benefits)
2. [Module Types](#module-types)
3. [Module Structure](#module-structure)
4. [Dependency Rules](#dependency-rules)
5. [Creating Modules](#creating-modules)
6. [Navigation Coordination](#navigation-coordination)
7. [Build Configuration](#build-configuration)

## Benefits

- **Scalability**: Changes in one module don't cascade to others
- **Parallel development**: Teams work independently on different features
- **Build speed**: Incremental builds only recompile changed modules
- **Reusability**: Core modules can be shared across apps
- **Encapsulation**: Clear boundaries and visibility controls
- **Testability**: Each module can be tested in isolation
- **Feature Independence**: Features don't depend on each other
- **Navigation Centralization**: App module coordinates all navigation
- **Adaptive UI Support**: Navigation3 enables responsive designs across form factors

## Module Types

### App Module (`app/`)
Entry point that brings everything together with Navigation3 adaptive navigation.

**Contains**:
- `MainActivity` with `NavigationSuiteScaffold`
- `AppNavigation` composable with `windowAdaptiveInfo`
- `NavHost` with all feature graphs
- `Navigator` implementations for feature coordination
- Hilt DI setup and component

**Dependencies**: All feature modules, all core modules

### Feature Modules (`feature/*`)
Self-contained features with clear boundaries and no inter-feature dependencies.

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

### Core Modules (`core/`)
Shared library code used across features with strict dependency direction.

| Module           | Purpose                                         | Dependencies                                        | Key Classes                                                                            |
|------------------|-------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------------|
| `core:domain`    | Domain models, use cases, repository interfaces | None (pure Kotlin)                                  | `AuthToken`, `User`, `LoginUseCase`, `AuthRepository` interface                        |
| `core:data`      | Repository implementations, data coordination   | `core:domain`                                       | `AuthRepositoryImpl`, `AuthRemoteDataSource`, `AuthLocalDataSource`                    |
| `core:database`  | Room database, DAOs, entities                   | `core:model` (if separate), otherwise `core:domain` | `AuthDatabase`, `AuthTokenDao`, `UserEntity`                                           |
| `core:network`   | Retrofit API, network models                    | `core:model` (if separate), otherwise `core:domain` | `AuthApi`, `NetworkAuthResponse`                                                       |
| `core:datastore` | Proto DataStore preferences                     | None                                                | `AuthPreferencesDataSource`                                                            |
| `core:common`    | Shared utilities, extensions                    | None                                                | `AppDispatchers`, `ResultExtensions`                                                   |
| `core:ui`        | Reusable UI components, themes, base ViewModels | `core:domain` (optional)                            | `AuthForm`, `AuthTheme`, `BaseViewModel`                                               |
| `core:testing`   | Test utilities, test doubles                    | Depends on module being tested                      | `TestDispatcherRule`, `TestAuthRepository`                                             |

## Module Structure

### Complete Project Structure

```
app/                    # App module - navigation, DI setup, app entry point
feature/
  ├── feature-auth/       # Authentication feature
  ├── feature-onboarding/ # Signup and onboarding flow
  ├── feature-profile/    # User profile feature
  ├── feature-settings/   # App settings feature
  └── feature-<name>/     # Additional features...
core/
  ├── domain/           # Pure Kotlin: Use Cases, Repository interfaces, Domain models
  ├── data/             # Data layer: Repository impl, DataSources, Data models
  ├── ui/               # Shared UI components, themes, base ViewModels
  ├── network/          # Retrofit, API models, network utilities
  ├── database/         # Room DAOs, entities, migrations
  ├── datastore/        # Preferences storage
  ├── common/           # Shared utilities, extensions
  └── testing/          # Test utilities, test doubles
build-logic/            # Convention plugins for consistent builds
├── convention/
│   ├── src/main/kotlin/
│   │   ├── AndroidApplicationConventionPlugin.kt # App module
│   │   ├── AndroidLibraryConventionPlugin.kt     # Core library modules
│   │   ├── AndroidFeatureConventionPlugin.kt     # Feature modules
│   │   ├── AndroidComposeConventionPlugin.kt     # Compose setup
│   │   ├── AndroidHiltConventionPlugin.kt        # Hilt setup
│   │   └── AndroidRoomConventionPlugin.kt        # Room setup
│   └── build.gradle.kts
```

### Feature Module Structure

```
feature-auth/
├── build.gradle.kts
├── src/main/
│   ├── kotlin/com/example/feature/auth/
│   │   ├── presentation/              # Presentation Layer
│   │   │   ├── AuthScreen.kt          # Main composable
│   │   │   ├── AuthRoute.kt           # Feature route composable
│   │   │   ├── viewmodel/             
│   │   │   │   ├── AuthViewModel.kt   # State holder
│   │   │   │   ├── AuthUiState.kt     # UI state models
│   │   │   │   └── AuthActions.kt     # User actions
│   │   │   └── components/            # Feature-specific UI components
│   │   │       ├── AuthFormCard.kt
│   │   │       └── AuthHeader.kt
│   │   ├── navigation/                # Navigation Layer
│   │   │   ├── AuthDestination.kt     # Feature routes (sealed class)
│   │   │   ├── AuthNavigator.kt       # Navigation interface
│   │   │   └── AuthGraph.kt           # NavGraphBuilder extension
│   │   └── di/                        # Feature-specific DI
│   │       └── AuthModule.kt          # Hilt module
│   └── res/                          # Feature resources
│       ├── drawable/
│       └── values/
└── src/test/                         # Feature tests
    └── kotlin/com/example/feature/auth/
        ├── presentation/viewmodel/
        │   └── AuthViewModelTest.kt
        └── navigation/
            └── AuthDestinationTest.kt
```

### Core Module Structure

```
core/domain/
├── build.gradle.kts
├── src/main/kotlin/com/example/core/domain/
│   ├── model/                         # Domain models
│   │   ├── User.kt
│   │   ├── AuthToken.kt
│   │   └── AuthState.kt
│   ├── repository/                    # Repository interfaces
│   │   └── AuthRepository.kt
│   ├── usecase/                       # Use cases
│   │   ├── LoginUseCase.kt
│   │   ├── RegisterUseCase.kt
│   │   ├── ResetPasswordUseCase.kt
│   │   └── ObserveAuthStateUseCase.kt
│   └── di/                           # Domain DI (if needed)
│       └── DomainModule.kt
└── src/test/kotlin/com/example/core/domain/
    ├── model/
    └── usecase/
```

## Dependency Rules

### Allowed Dependencies

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

### Visual Dependency Graph

```mermaid
graph TB
    subgraph "App Module"
        App[app<br/>Navigation & DI]
    end
    
    subgraph "Feature Modules"
        Auth[feature-auth]
        Onboarding[feature-onboarding]
        Profile[feature-profile]
        Settings[feature-settings]
    end
    
    subgraph "Core Modules"
        UI[core/ui]
        Domain[core/domain]
        Data[core/data]
        Network[core/network]
        Database[core/database]
        Common[core/common]
    end
    
    App --> Auth
    App --> Onboarding
    App --> Profile
    App --> Settings
    
    App --> UI
    App --> Domain
    App --> Data
    App --> Network
    App --> Database
    App --> Common
    
    Auth -.-> Domain
    Auth -.-> UI
    
    Onboarding -.-> Domain
    Onboarding -.-> UI
    
    Profile -.-> Domain
    Profile -.-> UI
    
    Settings -.-> Domain
    Settings -.-> UI
    
    Data --> Domain
    Data --> Network
    Data --> Database
    
    Network --> Domain
    Database --> Domain
    
    UI -.-> Domain
    
    style Auth fill:#e1f5fe
    style Onboarding fill:#e1f5fe
    style Profile fill:#e1f5fe
    style Settings fill:#e1f5fe
    style UI fill:#f3e5f5
    style Domain fill:#e8f5e8
    style Data fill:#fff3e0
    style Network fill:#fff3e0
    style Database fill:#fff3e0
    style Common fill:#f5f5f5
```

## Creating Modules

### 1. Create Feature Module

**Step 1: Create directory structure**
```
mkdir -p feature-auth/src/main/kotlin/com/example/feature/auth/{presentation/{viewmodel,components},navigation,di}
mkdir -p feature-auth/src/test/kotlin/com/example/feature/auth
```

**Step 2: Configure build.gradle.kts**
Use the Feature Module build file template in `references/gradle-setup.md`.
It includes the feature convention plugins, core module dependencies, Navigation3,
and test bundles.

**Step 3: Register in settings.gradle.kts**
```kotlin
include(":feature-auth")
```

**Step 4: Create navigation components**
```kotlin
// feature-auth/navigation/AuthDestination.kt
sealed class AuthDestination(val route: String) {
    object Login : AuthDestination("auth/login")
    object Register : AuthDestination("auth/register")
    object ForgotPassword : AuthDestination("auth/forgot_password")
    
    object Profile : AuthDestination("auth/profile/{userId}") {
        fun createRoute(userId: String) = "auth/profile/$userId"
    }
    
    companion object {
        fun fromRoute(route: String?): AuthDestination? {
            return when {
                route?.startsWith("auth/profile/") == true -> Profile
                route == Login.route -> Login
                route == Register.route -> Register
                route == ForgotPassword.route -> ForgotPassword
                else -> null
            }
        }
    }
}

// feature-auth/navigation/AuthNavigator.kt
interface AuthNavigator {
    fun navigateToRegister()
    fun navigateToForgotPassword()
    fun navigateBack()
    fun navigateToProfile(userId: String)
    fun navigateToMainApp()
}

// feature-auth/navigation/AuthGraph.kt
fun NavGraphBuilder.authGraph(
    authNavigator: AuthNavigator,
    startDestination: String = AuthDestination.Login.route
) {
    composable(route = AuthDestination.Login.route) {
        LoginScreen(
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
}
```

### 2. Create Core Module

**Step 1: Create directory structure**
```
mkdir -p core/domain/src/main/kotlin/com/example/core/domain/{model,repository,usecase}
mkdir -p core/domain/src/test/kotlin/com/example/core/domain
```

**Step 2: Configure build.gradle.kts**
Use the Core Domain module build file template in `references/gradle-setup.md`.
It keeps the module pure Kotlin and includes serialization and test dependencies.

**Step 3: Create domain models and contracts**

Define domain models, repository interfaces, and use cases in `core/domain`.
For detailed patterns and examples, see the Domain Layer section in
`references/architecture.md`.

### 3. Create App Module Configuration

**Step 1: Configure app module dependencies**
Use the App module build file template in `references/gradle-setup.md`.
It includes feature/core module wiring, Navigation3, and DI configuration.

**Step 2: Create app navigation**
```kotlin
// app/src/main/kotlin/com/example/app/navigation/AppNavigation.kt
@OptIn(ExperimentalMaterial3AdaptiveApi::class)
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val windowAdaptiveInfo = currentWindowAdaptiveInfo()
    val navigationSuiteScaffoldState = rememberNavigationSuiteScaffoldState()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val analytics = Firebase.analytics
    
    LaunchedEffect(backStackEntry) {
        val route = backStackEntry?.destination?.route ?: return@LaunchedEffect
        analytics.logEvent(FirebaseAnalytics.Event.SCREEN_VIEW) {
            param(FirebaseAnalytics.Param.SCREEN_NAME, route)
            param(FirebaseAnalytics.Param.SCREEN_CLASS, "MainActivity")
        }
    }
    
    // Create navigator implementations
    val authNavigator = remember {
        object : AuthNavigator {
            override fun navigateToRegister() = navController.navigate("auth/register")
            override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
            override fun navigateBack() = navController.popBackStack()
            override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
            override fun navigateToMainApp() {
                navController.navigate("main") {
                    popUpTo("auth") { inclusive = true }
                }
            }
        }
    }
    
    NavigationSuiteScaffold(
        state = navigationSuiteScaffoldState,
        windowAdaptiveInfo = windowAdaptiveInfo,
        navigationSuiteItems = {
            item(
                icon = Icons.Default.Lock,
                label = "Auth",
                selected = navController.currentDestination?.route?.startsWith("auth") == true,
                onClick = { navController.navigate("auth") }
            )
            item(
                icon = Icons.Default.Person,
                label = "Profile",
                selected = navController.currentDestination?.route?.startsWith("profile") == true,
                onClick = { navController.navigate("profile") }
            )
            item(
                icon = Icons.Default.Settings,
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
            profileGraph()
            settingsGraph()
            
            composable("main") {
                MainAppScreen(
                    onLogout = {
                        navController.navigate("auth") {
                            popUpTo("main") { inclusive = true }
                        }
                    }
                )
            }
        }
    }
}
```

This app-level screen tracking is optional and typically used to provide Firebase Crashlytics
breadcrumbs or analytics screen views. Sentry handles screen tracking via its plugin.
For more details, see `references/crashlytics.md`.

## Navigation Coordination

### Key Principles

1. **Feature Independence**: Features define `Navigator` interfaces
2. **Central Coordination**: App module implements all navigators
3. **Type-Safe Routes**: Sealed `Destination` classes with `createRoute()` functions
4. **Adaptive Navigation**: `NavigationSuiteScaffold` adapts based on `windowAdaptiveInfo`

### Navigation Flow

For end-to-end flow diagrams (UI → data → navigation), see the Complete Architecture
Flow section in `references/architecture.md`.

### Example: Auth Feature Navigation

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
val authNavigator = remember {
    object : AuthNavigator {
        override fun navigateToRegister() = navController.navigate("auth/register")
        override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
        override fun navigateBack() = navController.popBackStack()
        override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
        override fun navigateToMainApp() = navController.navigate("main")
    }
}
```

## Build Configuration

Convention plugin definitions and examples live in `references/gradle-setup.md`
so all build logic stays centralized in one place.

## Best Practices

1. **Start Simple**: Begin with app + core modules, add features as needed
2. **Feature Independence**: Features should work in isolation
3. **Navigation Contracts**: Use interfaces, not direct NavController access
4. **Pure Kotlin Core**: Keep `core:domain` free of Android dependencies
5. **Consistent Naming**: Use `feature-{name}` pattern for features
6. **Test Isolation**: Each module should have its own test suite
7. **Build Caching**: Use convention plugins for consistent configuration
8. **Dependency Direction**: Always follow `feature → core:domain → core:data`
9. **No Feature-to-Feature**: Never create dependencies between features
10. **Adaptive UI Ready**: Design for all form factors with Navigation3