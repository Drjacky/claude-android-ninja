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
→ Set up app module for navigation and DI setup
→ Configure feature modules and core modules

**Adding a new feature?**
→ Create feature module following naming convention `feature-[name]`
→ Implement Presentation Layer in feature module
→ Follow dependency flow: Feature → Core/Domain → Core/Data
→ Add navigation from app module

**Building UI screens?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Create Screen + ViewModel + UiState in feature module
→ Use shared components from `core/ui` when possible

**Setting up data layer?**
→ Read data layer section in [architecture.md](references/architecture.md)
→ Create Repository interfaces in `core/domain`
→ Implement Repository in `core/data`
→ Create DataSource + DAO in `core/data`

**Setting up navigation?**
→ Configure navigation graph in app module
→ Use feature module navigation destinations
→ Handle deep links and navigation arguments

## Core Principles

1. **Offline-first**: Local database is source of truth, sync with remote
2. **Unidirectional data flow**: Events flow down, data flows up
3. **Reactive streams**: Use Kotlin Flow/StateFlow for all data exposure
4. **Modular by feature**: Each feature is self-contained with clear boundaries
5. **Testable by design**: Use interfaces and test doubles, no mocking libraries
6. **Layer separation**: Strict separation between Presentation, Domain, Data, and UI layers
7. **Dependency direction**: Features depend on Core modules, not vice versa

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
│                                       │ Dependencies                     │
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
│                                       │ Dependencies                     │
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

## Module Structure

```
app/                    # App module - navigation, DI setup, app entry point
feature/
  ├── feature-auth/     # Authentication feature
  ├── feature-home/     # Home screen feature
  ├── feature-profile/  # User profile feature
  ├── feature-settings/ # App settings feature
  └── feature-<name>/   # Additional features...
core/
  ├── domain/           # Pure Kotlin: Use Cases, Repository interfaces, Domain models
  ├── data/             # Data layer: Repository impl, DataSources, Data models
  ├── ui/               # Shared UI components, themes, base ViewModels
  ├── network/          # Retrofit, API models, network utilities
  ├── database/         # Room DAOs, entities, migrations
  ├── datastore/        # Preferences storage
  ├── common/           # Shared utilities, extensions
  └── testing/          # Test utilities, test doubles
```

## Dependency Flow Rules

```
feature/* → core/domain → core/data
    ↓           ↓            ↓
core/ui (optional)   core/domain (interfaces)
```

### Strict Rules:
1. **Feature modules can only depend on Core modules**
2. **Feature modules cannot depend on other feature modules**
3. **Core/Domain has no Android dependencies** (pure Kotlin)
4. **Core/Data depends on Core/Domain** (implements interfaces)
5. **Core/UI is optional** for features that need shared UI components
6. **No circular dependencies** between any modules

## Creating a New Feature

### 1. Create Feature Module Structure
```
feature-auth/
├── build.gradle.kts    # Apply Android library + feature convention plugins
├── src/main/
│   ├── kotlin/com/example/feature/auth/
│   │   ├── AuthScreen.kt         # Composable screen
│   │   ├── AuthViewModel.kt      # ViewModel
│   │   ├── AuthUiState.kt        # UI state sealed interface
│   │   ├── AuthActions.kt        # User actions
│   │   └── AuthRoute.kt          # Navigation route
│   └── res/                      # Feature-specific resources
```

### 2. Configure Feature Module Dependencies
```kotlin
// feature-auth/build.gradle.kts
dependencies {
    implementation(project(":core:domain"))
    implementation(project(":core:ui"))      // Optional for shared UI
    implementation(libs.androidx.compose.bom)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.hilt.android)
    kapt(libs.hilt.compiler)
}
```

### 3. Set Up Domain Layer (in core/domain)
```kotlin
// core/domain/src/main/kotlin/com/example/domain/auth/
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
    fun observeAuthState(): Flow<AuthState>
}

data class User(
    val id: String,
    val email: String,
    val name: String
)

sealed class AuthState {
    data object Loading : AuthState()
    data class Authenticated(val user: User) : AuthState()
    data object Unauthenticated : AuthState()
}

class LoginUseCase @Inject constructor(
    private val authRepository: AuthRepository
) {
    suspend operator fun invoke(email: String, password: String): Result<AuthToken> =
        authRepository.login(email, password)
}
```

### 4. Implement Data Layer (in core/data)
```kotlin
// core/data/src/main/kotlin/com/example/data/auth/
internal class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource,
    private val remoteDataSource: AuthRemoteDataSource,
) : AuthRepository {
    
    override suspend fun login(email: String, password: String): Result<AuthToken> {
        return try {
            val response = remoteDataSource.login(email, password)
            localDataSource.saveAuthToken(response.token)
            Result.success(response.token)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override fun observeAuthState(): Flow<AuthState> {
        return localDataSource.observeAuthToken().map { token ->
            if (token != null) {
                // Fetch user details
                AuthState.Authenticated(getUserFromToken(token))
            } else {
                AuthState.Unauthenticated
            }
        }
    }
}
```

### 5. Create UI in Feature Module
```kotlin
// feature-auth/src/main/kotlin/com/example/feature/auth/AuthViewModel.kt
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val loginUseCase: LoginUseCase,
    private val authRepository: AuthRepository,
) : ViewModel() {

    val uiState: StateFlow<AuthUiState> = authRepository
        .observeAuthState()
        .map { authState ->
            when (authState) {
                is AuthState.Authenticated -> AuthUiState.Authenticated(authState.user)
                is AuthState.Unauthenticated -> AuthUiState.LoginForm
                AuthState.Loading -> AuthUiState.Loading
            }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = AuthUiState.Loading,
        )
    
    fun onAction(action: AuthAction) {
        when (action) {
            is AuthAction.Login -> {
                viewModelScope.launch {
                    val result = loginUseCase(action.email, action.password)
                    // Handle result
                }
            }
        }
    }
}
```

### 6. Use Shared UI Components (Optional)
```kotlin
// feature-auth/src/main/kotlin/com/example/feature/auth/AuthScreen.kt
@Composable
fun AuthScreen(
    uiState: AuthUiState,
    onAction: (AuthAction) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Using shared components from core/ui
        AppLogo()
        Spacer(modifier = Modifier.height(32.dp))
        
        when (uiState) {
            is AuthUiState.LoginForm -> LoginForm(
                onLoginClick = { email, password ->
                    onAction(AuthAction.Login(email, password))
                }
            )
            is AuthUiState.Authenticated -> WelcomeMessage(uiState.user.name)
            is AuthUiState.Loading -> LoadingSpinner() // From core/ui
            is AuthUiState.Error -> ErrorCard(uiState.message) // From core/ui
        }
    }
}
```

## Standard File Patterns

### ViewModel Pattern (Feature Module)
```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val getDataUseCase: GetDataUseCase,      // From core/domain
    private val repository: FeatureRepository,       // Interface from core/domain
) : BaseViewModel() {                               // BaseViewModel from core/ui
    
    private val _uiState = MutableStateFlow<FeatureUiState>(FeatureUiState.Loading)
    val uiState: StateFlow<FeatureUiState> = _uiState.asStateFlow()
    
    init {
        loadData()
    }
    
    private fun loadData() {
        viewModelScope.launch {
            getDataUseCase()
                .onStart { _uiState.value = FeatureUiState.Loading }
                .catch { e -> _uiState.value = FeatureUiState.Error(e.message ?: "Unknown error") }
                .collect { data ->
                    _uiState.value = FeatureUiState.Success(data)
                }
        }
    }
    
    fun onUserAction(action: FeatureAction) {
        when (action) {
            is FeatureAction.Refresh -> loadData()
            // Handle other actions
        }
    }
}
```

### Repository Pattern (Core/Data)
```kotlin
// Repository interface in core/domain
interface TaskRepository {
    fun getTasks(): Flow<List<Task>>
    suspend fun addTask(task: Task)
    suspend fun updateTask(task: Task)
}

// Repository implementation in core/data
internal class TaskRepositoryImpl @Inject constructor(
    private val localDataSource: TaskLocalDataSource,
    private val remoteDataSource: TaskRemoteDataSource,
    private val taskMapper: TaskMapper,
) : TaskRepository {
    
    override fun getTasks(): Flow<List<Task>> {
        return localDataSource.observeTasks()
            .map { taskEntities ->
                taskEntities.map { taskMapper.toDomain(it) }
            }
    }
    
    override suspend fun addTask(task: Task) {
        val taskEntity = taskMapper.toEntity(task)
        localDataSource.insertTask(taskEntity)
        
        // Sync with remote in background
        viewModelScope.launch {
            try {
                remoteDataSource.addTask(task)
            } catch (e: Exception) {
                // Queue for later sync
            }
        }
    }
}
```

### Use Case Pattern (Core/Domain)
```kotlin
class GetTasksUseCase @Inject constructor(
    private val taskRepository: TaskRepository,
    private val dispatchers: CoroutineDispatchers,
) {
    operator fun invoke(): Flow<List<Task>> = taskRepository
        .getTasks()
        .flowOn(dispatchers.io)
}

class CompleteTaskUseCase @Inject constructor(
    private val taskRepository: TaskRepository,
    private val dispatchers: CoroutineDispatchers,
) {
    suspend operator fun invoke(taskId: String): Result<Unit> = withContext(dispatchers.io) {
        try {
            // Business logic here
            val task = // get task
            val updatedTask = task.copy(isCompleted = true)
            taskRepository.updateTask(updatedTask)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
```

### Shared UI Components (Core/UI)
```kotlin
// core/ui/src/main/kotlin/com/example/ui/components/
@Composable
fun LoadingSpinner(
    modifier: Modifier = Modifier,
    color: Color = MaterialTheme.colorScheme.primary,
) {
    CircularProgressIndicator(
        modifier = modifier,
        color = color,
        strokeWidth = 2.dp,
    )
}

// core/ui/src/main/kotlin/com/example/ui/theme/
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit,
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        shapes = Shapes,
        content = content,
    )
}
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
                add("implementation", libs.androidx.lifecycle.viewmodel.compose)
                add("implementation", libs.hilt.android)
                add("kapt", libs.hilt.compiler)
                
                // Optional UI dependency
                if (hasUiDependencies()) {
                    add("implementation", project(":core:ui"))
                }
            }
        }
    }
}
```

## Key Dependencies

```kotlin
// Gradle version catalog (libs.versions.toml)
[versions]
kotlin = "1.9.x"
compose-bom = "2024.x.x"
hilt = "2.48"
room = "2.6.x"
coroutines = "1.7.x"

[libraries]
# Core dependencies
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
kotlinx-coroutines-android = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-android", version.ref = "coroutines" }

# Feature module dependencies
androidx-lifecycle-viewmodel-compose = { group = "androidx.lifecycle", name = "lifecycle-viewmodel-compose", version = "2.7.x" }

# Core/UI dependencies
androidx-compose-material3 = { group = "androidx.compose.material3", name = "material3", version.ref = "compose-bom" }
androidx-compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview", version.ref = "compose-bom" }

[bundles]
compose = [
    "androidx-compose-ui",
    "androidx-compose-ui-tooling-preview",
    "androidx-compose-material3",
    "androidx-compose-foundation"
]

[plugins]
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
kotlin-kapt = { id = "org.jetbrains.kotlin.kapt", version.ref = "kotlin" }
```

## Testing Strategy

### Feature Module Tests:
```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/AuthViewModelTest.kt
@HiltAndroidTest
class AuthViewModelTest {
    
    @get:Rule
    val hiltRule = HiltAndroidRule(this)
    
    @Inject
    lateinit var authRepository: AuthRepository
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun `when login succeeds, state becomes authenticated`() = runTest {
        // Arrange
        val viewModel = AuthViewModel(authRepository)
        
        // Act
        viewModel.onAction(AuthAction.Login("test@email.com", "password"))
        
        // Assert
        val state = viewModel.uiState.first()
        assertTrue(state is AuthUiState.Authenticated)
    }
}
```

### Domain Layer Tests (Pure Kotlin):
```kotlin
// core/domain/src/test/kotlin/com/example/domain/auth/LoginUseCaseTest.kt
class LoginUseCaseTest {
    
    private lateinit var useCase: LoginUseCase
    private val mockRepository = mockk<AuthRepository>()
    
    @BeforeEach
    fun setup() {
        useCase = LoginUseCase(mockRepository)
    }
    
    @Test
    fun `invoke calls repository login`() = runTest {
        // Arrange
        val email = "test@email.com"
        val password = "password"
        val expectedToken = AuthToken("token123")
        
        coEvery { mockRepository.login(email, password) } returns Result.success(expectedToken)
        
        // Act
        val result = useCase(email, password)
        
        // Assert
        assertTrue(result.isSuccess)
        assertEquals(expectedToken, result.getOrNull())
        coVerify { mockRepository.login(email, password) }
    }
}
```

## Navigation Between Features

Use navigation keys or deep links for feature-to-feature navigation:

```kotlin
// In app module
@Composable
fun AppNavHost() {
    val navController = rememberNavController()
    
    NavHost(
        navController = navController,
        startDestination = "home"
    ) {
        // Feature modules provide their own composable destinations
        homeFeatureGraph(navController)
        authFeatureGraph(navController)
        profileFeatureGraph(navController)
    }
}

// In feature-auth module
fun NavController.navigateToAuth() {
    navigate("auth_route") {
        // Navigation options
    }
}
```