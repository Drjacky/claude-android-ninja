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

## Build Configuration

Convention plugin definitions and examples live in:
- `assets/convention/` - All plugin source files (.kt)
- `references/gradle-setup.md` - Detailed build configuration patterns
- `assets/convention/QUICK_REFERENCE.md` - Setup instructions and examples

Copy plugin files from `assets/convention/` to `build-logic/convention/src/main/kotlin/` in your project.

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
- `AppNavigation` composable with `NavigationSuiteScaffold`
- `NavigationState` and `Navigator` for state management
- `entryProvider` with all feature destinations
- `NavDisplay` to render current destination
- `Navigator` implementations for feature coordination
- Hilt DI setup and component

**Dependencies**: All feature modules, all core modules

### Feature Modules (`feature/*`)
Self-contained features with clear boundaries and no inter-feature dependencies.
See [Feature Module Structure](#feature-module-structure) for the full directory layout.

### Core Modules (`core/`)
Shared library code used across features with strict dependency direction.

| Module           | Purpose                                         | Dependencies                                        | Key Classes                                                         |
|------------------|-------------------------------------------------|-----------------------------------------------------|---------------------------------------------------------------------|
| `core:domain`    | Domain models, use cases, repository interfaces | None (pure Kotlin)                                  | `AuthToken`, `User`, `LoginUseCase`, `AuthRepository` interface     |
| `core:data`      | Repository implementations, data coordination   | `core:domain`                                       | `AuthRepositoryImpl`, `AuthRemoteDataSource`, `AuthLocalDataSource` |
| `core:database`  | Room 3 database, DAOs, entities                 | `core:model` (if separate), otherwise `core:domain` | `AuthDatabase`, `AuthTokenDao`, `UserEntity`                        |
| `core:network`   | Retrofit API, network models                    | `core:model` (if separate), otherwise `core:domain` | `AuthApi`, `NetworkAuthResponse`                                    |
| `core:datastore` | Proto DataStore preferences                     | None                                                | `AuthPreferencesDataSource`                                         |
| `core:common`    | Shared utilities, extensions                    | None                                                | `AppDispatchers`, `ResultExtensions`                                |
| `core:ui`        | Reusable UI components, themes, base ViewModels | `core:domain` (optional)                            | `AuthForm`, `AuthTheme`, `BaseViewModel`                            |
| `core:testing`   | Test utilities, test doubles                    | Depends on module being tested                      | `TestDispatcherRule`, `FakeAuthRepository`                          |

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
  ├── database/         # Room 3 DAOs, entities, migrations
  ├── datastore/        # Preferences storage
  ├── common/           # Shared utilities, extensions
  └── testing/          # Test utilities, test doubles
build-logic/            # Convention plugins for consistent builds
        ├── convention/
        │   ├── src/main/kotlin/
        │   │   ├── AndroidApplicationConventionPlugin.kt
        │   │   ├── AndroidApplicationComposeConventionPlugin.kt
        │   │   ├── AndroidApplicationBaselineProfileConventionPlugin.kt
        │   │   ├── AndroidApplicationJacocoConventionPlugin.kt
        │   │   ├── AndroidLibraryConventionPlugin.kt
        │   │   ├── AndroidLibraryComposeConventionPlugin.kt
        │   │   ├── AndroidLibraryJacocoConventionPlugin.kt
        │   │   ├── AndroidFeatureConventionPlugin.kt
        │   │   ├── AndroidTestConventionPlugin.kt
        │   │   ├── AndroidRoomConventionPlugin.kt
        │   │   ├── AndroidLintConventionPlugin.kt
        │   │   ├── HiltConventionPlugin.kt
        │   │   ├── DetektConventionPlugin.kt
        │   │   ├── SpotlessConventionPlugin.kt
        │   │   ├── JvmLibraryConventionPlugin.kt
        │   │   ├── KotlinSerializationConventionPlugin.kt
        │   │   ├── FirebaseConventionPlugin.kt
        │   │   ├── SentryConventionPlugin.kt
        │   │   └── config/
        │   │       ├── KotlinAndroid.kt
        │   │       ├── AndroidCompose.kt
        │   │       ├── ProjectExtensions.kt
        │   │       ├── GradleManagedDevices.kt
        │   │       ├── AndroidInstrumentationTest.kt
        │   │       ├── PrintApksTask.kt
        │   │       └── Jacoco.kt
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
import androidx.compose.runtime.Immutable
import androidx.navigation3.runtime.NavKey
import kotlinx.serialization.Serializable

@Immutable
sealed interface AuthDestination : NavKey {
    @Serializable
    data object Login : AuthDestination
    
    @Serializable
    data object Register : AuthDestination
    
    @Serializable
    data object ForgotPassword : AuthDestination
    
    @Serializable
    data class Profile(val userId: String) : AuthDestination
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
import androidx.navigation3.runtime.EntryProviderScope
import androidx.navigation3.runtime.NavKey

fun EntryProviderScope<NavKey>.authGraph(
    authNavigator: AuthNavigator
) {
    entry<AuthDestination.Login> {
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
    
    entry<AuthDestination.Register> {
        RegisterScreen(
            onRegisterSuccess = { user ->
                authNavigator.navigateToMainApp()
            },
            onNavigateToLogin = {
                authNavigator.navigateBack()
            }
        )
    }
    
    entry<AuthDestination.ForgotPassword> {
        ForgotPasswordScreen(
            onResetSuccess = {
                authNavigator.navigateBack()
            },
            onNavigateBack = {
                authNavigator.navigateBack()
            }
        )
    }
    
    entry<AuthDestination.Profile> { key ->
        ProfileScreen(
            userId = key.userId,
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

**Step 2: Create navigation state and navigator**

Create `NavigationState.kt` and `Navigator.kt` for managing app navigation state.
See `references/android-navigation.md` → "Navigation 3 State Management" for complete implementation.

**Step 3: Create app navigation**

See `references/android-navigation.md` → "App Navigation Setup" for the complete `AppNavigation` composable
with `NavigationSuiteScaffold`, `TopLevelRoute`, navigator implementations, and icon resources.

## Navigation Coordination

For Navigation3 quick start, app navigation setup, state management (`NavigationState`, `Navigator`),
key principles, and migration guidance, see `references/android-navigation.md`.

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