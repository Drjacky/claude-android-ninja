# Design Patterns (Android-Focused)

This guide maps classic design patterns to practical Android usage while staying aligned with
our architecture (`references/architecture.md`), modularization rules (`references/modularization.md`), and Compose-first code.
Use this when designing new features, modules, pure business logic, or shared utilities.

## Table of Contents
1. [Principles for This Codebase](#principles-for-this-codebase)
2. [Architectural Patterns](#architectural-patterns)
3. [Creational Patterns](#creational-patterns)
4. [Structural Patterns](#structural-patterns)
5. [Behavioral Patterns](#behavioral-patterns)
6. [Kotlin-Specific Patterns](#kotlin-specific-patterns)
7. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)

## Principles for This Codebase
- **Prefer composition and delegation over inheritance.** See `references/kotlin-delegation.md`.
- **Keep patterns local to the layer they belong to** (UI vs Domain vs Data).
- **Avoid framework-heavy base classes**; keep components testable.
- **For app-wide lifetimes, rely on DI scopes** instead of manual singletons.
- **Start simple**: Don't add patterns preemptively. Add complexity only when needed.
- **Kotlin-first**: Leverage sealed classes, data classes, delegation, and coroutines.

## Architectural Patterns

### MVVM (Model-View-ViewModel)
- **When**: All feature modules (this is our base architecture).
- **Android use**: ViewModel holds `StateFlow<UiState>`, Composables observe and render.
- **Notes**: See `references/architecture.md` for full details.

```kotlin
// Feature: Auth
@Immutable
sealed interface AuthUiState {
    data object Loading : AuthUiState
    data class LoginForm(val email: String, val password: String, val error: String?) : AuthUiState
    data class Success(val user: User) : AuthUiState
}

sealed interface AuthAction {
    data class EmailChanged(val email: String) : AuthAction
    data class PasswordChanged(val password: String) : AuthAction
    data object LoginClicked : AuthAction
}

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.LoginForm("", "", null))
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    fun onAction(action: AuthAction) {
        when (action) {
            is AuthAction.EmailChanged -> updateEmail(action.email)
            is AuthAction.PasswordChanged -> updatePassword(action.password)
            AuthAction.LoginClicked -> login()
        }
    }
    
    private fun login() {
        viewModelScope.launch {
            _uiState.update { AuthUiState.Loading }
            authRepository.login(email, password).fold(
                onSuccess = { _uiState.update { AuthUiState.Success(it.user) } },
                onFailure = { _uiState.update { AuthUiState.LoginForm(email, password, it.message) } }
            )
        }
    }
}

@Composable
fun AuthRoute(
    viewModel: AuthViewModel = hiltViewModel(),
    authNavigator: AuthNavigator
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    AuthScreen(
        uiState = uiState,
        onAction = viewModel::onAction
    )
}
```

### Repository Pattern
- **When**: All data access (single source of truth).
- **Android use**: Hide local/remote/cache complexity behind a clean interface.
- **Notes**: See `references/architecture.md` for implementation details.

```kotlin
// core/domain
@Stable
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    fun observeAuthState(): Flow<AuthState>
}

// core/data
internal class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource,
    private val remoteDataSource: AuthRemoteDataSource
) : AuthRepository {
    override suspend fun login(email: String, password: String): Result<AuthToken> =
        try {
            val token = remoteDataSource.login(email, password)
            localDataSource.saveAuthToken(token)
            Result.success(token)
        } catch (e: IOException) {
            Result.failure(AuthError.NetworkError("No internet connection", e))
        }
    
    override fun observeAuthState(): Flow<AuthState> =
        localDataSource.observeAuthToken().map { token ->
            if (token != null) AuthState.Authenticated else AuthState.Unauthenticated
        }
}
```

## Creational Patterns

### Singleton
- **When**: You need a single, app-wide instance.
- **Android use**: Use DI with `@Singleton` for repositories, loggers, and crash reporters.
- **Notes**: Avoid `object` keyword with Android dependencies; use Hilt scopes instead.

```kotlin
// ❌ Bad: Holds context statically
object BadAnalytics {
    private lateinit var context: Context
    
    fun init(context: Context) {
        this.context = context.applicationContext
    }
}

// ✅ Good: DI-managed singleton
@Module
@InstallIn(SingletonComponent::class)
abstract class DataModule {
    @Binds
    @Singleton
    abstract fun bindAuthRepository(impl: AuthRepositoryImpl): AuthRepository
}

// Usage in ViewModel
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository // Always the same instance
) : ViewModel()
```

### Factory Method
- **When**: The concrete class should vary by environment or runtime.
- **Android use**: `ViewModelProvider.Factory`, `WorkManager` factories, Retrofit service creation.
- **Notes**: Keep factory interfaces in `core/domain` or `core/common`.

```kotlin
// core/domain
interface DataSourceFactory {
    fun createAuthDataSource(): AuthDataSource
}

// core/data - Production
class RemoteDataSourceFactory @Inject constructor(
    private val retrofit: Retrofit
) : DataSourceFactory {
    override fun createAuthDataSource(): AuthDataSource =
        retrofit.create(AuthDataSource::class.java)
}

// core/data - Testing
class FakeDataSourceFactory : DataSourceFactory {
    override fun createAuthDataSource(): AuthDataSource =
        FakeAuthDataSource()
}

// DI setup
@Module
@InstallIn(SingletonComponent::class)
abstract class DataSourceModule {
    @Binds
    abstract fun bindFactory(impl: RemoteDataSourceFactory): DataSourceFactory
}
```

### Abstract Factory
- **When**: You need families of related implementations.
- **Android use**: Swap entire provider families (Crashlytics vs Sentry, Firebase vs custom).
- **Notes**: Useful for build variants and testing.

```kotlin
// core/domain
interface CrashReporterFactory {
    fun createCrashReporter(): CrashReporter
    fun createAnalytics(): Analytics
}

// core/data - Firebase family
class FirebaseFactory @Inject constructor() : CrashReporterFactory {
    override fun createCrashReporter(): CrashReporter = FirebaseCrashReporter()
    override fun createAnalytics(): Analytics = FirebaseAnalytics()
}

// core/data - Sentry family
class SentryFactory @Inject constructor() : CrashReporterFactory {
    override fun createCrashReporter(): CrashReporter = SentryCrashReporter()
    override fun createAnalytics(): Analytics = SentryAnalytics()
}

// DI - Choose based on build variant
@Module
@InstallIn(SingletonComponent::class)
object ReporterModule {
    @Provides
    @Singleton
    fun provideFactory(): CrashReporterFactory =
        if (BuildConfig.USE_FIREBASE) FirebaseFactory() else SentryFactory()
}
```

### Builder
- **When**: Complex object configuration needs clarity or optional steps.
- **Android use**: `OkHttpClient.Builder`, `Retrofit.Builder`, custom config builders.
- **Notes**: Prefer immutable outputs; keep configuration in DI modules.

```kotlin
// core/network
class ApiClientBuilder @Inject constructor(
    private val loggingInterceptor: HttpLoggingInterceptor,
    private val authInterceptor: AuthInterceptor
) {
    private var baseUrl: String = ""
    private var timeout: Long = 30L
    private var retryOnConnectionFailure: Boolean = true
    
    fun baseUrl(url: String) = apply { this.baseUrl = url }
    fun timeout(seconds: Long) = apply { this.timeout = seconds }
    fun disableRetry() = apply { this.retryOnConnectionFailure = false }
    
    fun build(): OkHttpClient = OkHttpClient.Builder()
        .addInterceptor(authInterceptor)
        .addInterceptor(loggingInterceptor)
        .connectTimeout(timeout, TimeUnit.SECONDS)
        .retryOnConnectionFailure(retryOnConnectionFailure)
        .build()
}

// Usage in DI
@Provides
@Singleton
fun provideOkHttpClient(builder: ApiClientBuilder): OkHttpClient =
    builder
        .baseUrl(BuildConfig.API_URL)
        .timeout(60L)
        .build()
```

### Prototype
- **When**: Cloning is cheaper than new construction.
- **Android use**: Copying immutable UI models (`data class.copy`) for state updates.
- **Notes**: Works well with `UiState` and form screens.

```kotlin
@Immutable
data class RegisterFormState(
    val email: String = "",
    val password: String = "",
    val confirmPassword: String = "",
    val agreedToTerms: Boolean = false,
    val errors: Map<String, String> = emptyMap()
)

@HiltViewModel
class RegisterViewModel @Inject constructor() : ViewModel() {
    private val _formState = MutableStateFlow(RegisterFormState())
    val formState: StateFlow<RegisterFormState> = _formState.asStateFlow()
    
    fun onEmailChanged(email: String) {
        _formState.update { it.copy(email = email) } // Prototype pattern via copy()
    }
    
    fun onPasswordChanged(password: String) {
        _formState.update { it.copy(password = password) }
    }
    
    fun onAgreedToTermsChanged(agreed: Boolean) {
        _formState.update { it.copy(agreedToTerms = agreed) }
    }
}
```

## Structural Patterns

### Adapter
- **When**: You need to reconcile mismatched interfaces (DTOs → Domain models).
- **Android use**: Mapping network DTOs to domain models, database entities to domain.
- **Notes**: Keep adapters in `core/data` for data mappings.

```kotlin
// core/network - DTO (from API)
@Serializable
data class NetworkUser(
    @SerialName("user_id") val userId: String,
    @SerialName("email_address") val emailAddress: String,
    @SerialName("full_name") val fullName: String
)

// core/domain - Domain model
@Immutable
data class User(
    val id: String,
    val email: String,
    val name: String
)

// core/data - Adapter
class UserAdapter {
    fun toDomain(network: NetworkUser): User = User(
        id = network.userId,
        email = network.emailAddress,
        name = network.fullName
    )
    
    fun toNetwork(domain: User): NetworkUser = NetworkUser(
        userId = domain.id,
        emailAddress = domain.email,
        fullName = domain.name
    )
}
```

### Bridge
- **When**: You want abstraction to vary independently of implementation.
- **Android use**: `Navigator` interfaces in features with app-level implementations.
- **Notes**: Keeps features independent and testable.

```kotlin
// feature/auth - Abstraction
interface AuthNavigator {
    fun navigateToHome()
    fun navigateToRegister()
    fun navigateBack()
}

// feature/auth - Feature doesn't know about NavController
@Composable
fun LoginScreen(
    onLoginSuccess: () -> Unit, // Provided by abstraction
    onRegisterClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Button(onClick = onRegisterClick) {
        Text("Create Account")
    }
}

// app - Implementation (Bridge)
class AppAuthNavigator(
    private val navigator: Navigator
) : AuthNavigator {
    override fun navigateToHome() {
        navigator.navigate(TopLevelRoute.Home)
    }

    override fun navigateToRegister() {
        navigator.navigate(AuthDestination.Register)
    }

    override fun navigateBack() {
        navigator.goBack()
    }
}
```

### Composite
- **When**: You need tree-like structures with uniform treatment.
- **Android use**: Navigation graphs, UI component trees, menu structures.
- **Notes**: Helps build adaptive UI structures for tablets/foldables.

```kotlin
// core/ui - Component interface
sealed interface NavigationItem {
    val id: String
    val label: String
    val iconRes: Int
}

// Leaf node
@Immutable
data class NavScreen(
    override val id: String,
    override val label: String,
    override val iconRes: Int,
    val route: String
) : NavigationItem

// Composite node
@Immutable
data class NavGroup(
    override val id: String,
    override val label: String,
    override val iconRes: Int,
    val children: List<NavigationItem>
) : NavigationItem

// Usage
val navigationTree = listOf(
    NavScreen("home", "Home", R.drawable.ic_home, "home"),
    NavGroup(
        "settings",
        "Settings",
        R.drawable.ic_settings,
        children = listOf(
            NavScreen("profile", "Profile", R.drawable.ic_person, "settings/profile"),
            NavScreen("privacy", "Privacy", R.drawable.ic_lock, "settings/privacy"),
            NavScreen("about", "About", R.drawable.ic_info, "settings/about")
        )
    )
)

@Composable
fun NavigationMenu(items: List<NavigationItem>) {
    items.forEach { item ->
        when (item) {
            is NavScreen -> NavigationButton(item)
            is NavGroup -> {
                NavigationGroupHeader(item)
                NavigationMenu(item.children) // Recursive composite
            }
        }
    }
}
```

### Decorator
- **When**: Add behavior without modifying the original type.
- **Android use**: OkHttp interceptors, Compose `Modifier` chains, logging decorators.
- **Notes**: Keep decorators small and composable.

```kotlin
// core/domain - Base interface (see references/crashlytics.md → "Provider-Agnostic Interface")
interface CrashReporter {
    fun recordException(throwable: Throwable, context: Map<String, Any> = emptyMap())
    fun log(message: String)
}

// core/data - Base implementation
class FirebaseCrashReporter @Inject constructor(
    private val crashlytics: FirebaseCrashlytics
) : CrashReporter {
    override fun recordException(throwable: Throwable, context: Map<String, Any>) {
        crashlytics.recordException(throwable)
    }
    
    override fun log(message: String) {
        crashlytics.log(message)
    }
}

// core/data - Decorator (adds logging)
class LoggingCrashReporter(
    crashReporter: CrashReporter, // No private - delegated only
    private val logger: Logger
) : CrashReporter by crashReporter {
    override fun recordException(throwable: Throwable, context: Map<String, Any>) {
        logger.d("Recording exception: ${throwable.message}")
        super.recordException(throwable, context)
    }
}

// core/data - Another decorator (adds privacy scrubbing)
class PrivacyAwareCrashReporter(
    crashReporter: CrashReporter // No private - delegated only
) : CrashReporter by crashReporter {
    override fun recordException(throwable: Throwable, context: Map<String, Any>) {
        val scrubbedContext = context.filterKeys { it !in SENSITIVE_KEYS }
        super.recordException(throwable, scrubbedContext)
    }
    
    companion object {
        private val SENSITIVE_KEYS = setOf("password", "token", "apiKey")
    }
}

// DI - Stack decorators
@Provides
@Singleton
fun provideCrashReporter(
    firebase: FirebaseCrashReporter,
    logger: Logger
): CrashReporter =
    PrivacyAwareCrashReporter(
        LoggingCrashReporter(firebase, logger)
    )
```

### Delegation
- **When**: You want to reuse behavior without inheritance.
- **Android use**: Delegating interface implementations, ViewModel delegation, repository delegation.
- **Notes**: Use Kotlin's `by` keyword. See `references/kotlin-delegation.md`.

```kotlin
// core/domain
interface CrashlyticsStateLogger {
    fun logUiState(key: String, value: Any)
    fun logAction(action: String)
}

// core/data
class CrashlyticsStateLoggerImpl @Inject constructor(
    private val crashlytics: FirebaseCrashlytics
) : CrashlyticsStateLogger {
    override fun logUiState(key: String, value: Any) {
        crashlytics.setCustomKey(key, value.toString())
    }
    
    override fun logAction(action: String) {
        crashlytics.log("Action: $action")
    }
}

// feature/auth - ViewModel uses delegation
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    logger: CrashlyticsStateLogger
) : ViewModel(), CrashlyticsStateLogger by logger {
    
    fun onLoginClicked() {
        logAction("Login clicked") // Delegated method
        logUiState("screen", "login") // Delegated method
        // ... login logic
    }
}
```

### Facade
- **When**: Provide a simplified API to complex subsystems.
- **Android use**: Repositories hiding local/remote/cache details.
- **Notes**: Repositories should be the public entry for data access. See `references/architecture.md`.

```kotlin
// core/data - Complex subsystems (hidden)
internal interface AuthLocalDataSource {
    suspend fun saveAuthToken(token: String)
    suspend fun getAuthToken(): String?
    fun observeAuthToken(): Flow<String?>
}

internal interface AuthRemoteDataSource {
    suspend fun login(email: String, password: String): AuthToken
    suspend fun refreshToken(token: String): AuthToken
}

internal interface AuthCacheDataSource {
    fun cacheUser(user: User)
    fun getCachedUser(): User?
}

// core/data - Facade (simple public API)
@Singleton
class AuthRepositoryImpl @Inject constructor(
    private val local: AuthLocalDataSource,
    private val remote: AuthRemoteDataSource,
    private val cache: AuthCacheDataSource
) : AuthRepository {
    
    // Simple API hides complexity
    override suspend fun login(email: String, password: String): Result<AuthToken> =
        try {
            val token = remote.login(email, password)
            local.saveAuthToken(token.value)
            cache.cacheUser(token.user)
            Result.success(token)
        } catch (e: Exception) {
            Result.failure(e)
        }
    
    override fun observeAuthState(): Flow<AuthState> =
        local.observeAuthToken().map { token ->
            if (token != null) {
                val user = cache.getCachedUser() ?: return@map AuthState.Loading
                AuthState.Authenticated(user)
            } else {
                AuthState.Unauthenticated
            }
        }
}
```

### Flyweight
- **When**: You need to reduce memory by sharing common state.
- **Android use**: Image loading caches, shared UI resources, reused `Painter`s.
- **Notes**: Avoid recreating heavy objects inside composables.

```kotlin
// core/ui - Icon resource management
object IconResources {
    fun getIconRes(name: String): Int =
        when (name) {
            "home" -> R.drawable.ic_home
            "profile" -> R.drawable.ic_person
            "settings" -> R.drawable.ic_settings
            else -> R.drawable.ic_question_mark
        }
}

// Usage in Composable
@Composable
fun NavigationItem(iconName: String, label: String) {
    val iconRes = remember(iconName) { IconResources.getIconRes(iconName) }
    
    Icon(painter = painterResource(iconRes), contentDescription = label)
    Text(text = label)
}

// Better: Use rememberImagePainter for network images
@Composable
fun UserAvatar(imageUrl: String) {
    // Coil's internal cache acts as Flyweight
    AsyncImage(
        model = imageUrl,
        contentDescription = "User avatar",
        modifier = Modifier.size(48.dp)
    )
}
```

### Proxy
- **When**: You need to control access to an expensive or remote object.
- **Android use**: Lazy initialization for analytics/crash reporters, remote data sources.
- **Notes**: Keep proxy logic in the data layer.

```kotlin
// core/data - Proxy for lazy analytics initialization
class LazyAnalyticsProxy @Inject constructor(
    private val context: Context
) : Analytics {
    private val analytics: FirebaseAnalytics by lazy {
        FirebaseAnalytics.getInstance(context)
    }
    
    override fun logEvent(name: String, params: Map<String, Any>) {
        analytics.logEvent(name, bundleOf(*params.toList().toTypedArray()))
    }
    
    override fun setUserId(userId: String) {
        analytics.setUserId(userId)
    }
}

// core/data - Proxy for caching remote data
class CachedAuthDataSource @Inject constructor(
    private val remoteDataSource: AuthRemoteDataSource,
    private val cache: MutableMap<String, User> = mutableMapOf()
) : AuthDataSource {
    
    override suspend fun getUser(userId: String): User =
        cache.getOrPut(userId) {
            remoteDataSource.getUser(userId) // Only fetch if not cached
        }
    
    fun invalidateCache() {
        cache.clear()
    }
}
```

## Behavioral Patterns

### Observer
- **When**: Many dependents must react to state changes.
- **Android use**: `Flow`, `StateFlow` in ViewModels and repositories.
- **Notes**: Always use `Flow`/`StateFlow` (not LiveData) for consistency. See `references/coroutines-patterns.md`.

```kotlin
// core/domain
@Stable
interface AuthRepository {
    fun observeAuthState(): Flow<AuthState> // Observable
}

// core/data
class AuthRepositoryImpl @Inject constructor(
    private val localDataSource: AuthLocalDataSource
) : AuthRepository {
    private val _authState = MutableStateFlow<AuthState>(AuthState.Unauthenticated)
    
    override fun observeAuthState(): Flow<AuthState> = _authState.asStateFlow()
    
    suspend fun login(email: String, password: String) {
        _authState.value = AuthState.Loading
        // ... login logic
        _authState.value = AuthState.Authenticated(user)
    }
}

// feature/auth - Observer (ViewModel)
@HiltViewModel
class AuthViewModel @Inject constructor(
    authRepository: AuthRepository
) : ViewModel() {
    val authState: StateFlow<AuthState> = authRepository
        .observeAuthState()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = AuthState.Loading
        )
}

// feature/auth - Observer (UI)
@Composable
fun AuthScreen(viewModel: AuthViewModel = hiltViewModel()) {
    val authState by viewModel.authState.collectAsStateWithLifecycle()
    
    when (authState) {
        is AuthState.Loading -> LoadingIndicator()
        is AuthState.Authenticated -> WelcomeScreen()
        is AuthState.Unauthenticated -> LoginForm()
    }
}
```

### Strategy
- **When**: Multiple interchangeable algorithms are needed.
- **Android use**: Auth providers, caching strategies, feature flag resolution.
- **Notes**: Inject the strategy via DI; don't branch on build flavors in business logic.

```kotlin
// core/domain - Strategy interface
interface AuthStrategy {
    suspend fun authenticate(credentials: AuthCredentials): Result<AuthToken>
}

// core/data - Email/Password strategy
class EmailPasswordAuthStrategy @Inject constructor(
    private val api: AuthApi
) : AuthStrategy {
    override suspend fun authenticate(credentials: AuthCredentials): Result<AuthToken> =
        runCatching {
            api.loginWithEmail(credentials.email, credentials.password)
        }
}

// core/data - Google OAuth strategy
class GoogleAuthStrategy @Inject constructor(
    private val googleSignIn: GoogleSignInClient
) : AuthStrategy {
    override suspend fun authenticate(credentials: AuthCredentials): Result<AuthToken> =
        runCatching {
            val account = googleSignIn.signIn()
            api.loginWithGoogle(account.idToken)
        }
}

// core/data - Biometric strategy
class BiometricAuthStrategy @Inject constructor(
    private val biometricManager: BiometricManager
) : AuthStrategy {
    override suspend fun authenticate(credentials: AuthCredentials): Result<AuthToken> =
        suspendCancellableCoroutine { continuation ->
            biometricManager.authenticate(
                onSuccess = { continuation.resume(Result.success(it)) },
                onFailure = { continuation.resume(Result.failure(it)) }
            )
        }
}

// core/data - Repository uses injected strategy
class AuthRepositoryImpl @Inject constructor(
    @EmailPassword private val emailStrategy: AuthStrategy,
    @Google private val googleStrategy: AuthStrategy,
    @Biometric private val biometricStrategy: AuthStrategy
) : AuthRepository {
    
    override suspend fun login(type: AuthType, credentials: AuthCredentials): Result<AuthToken> {
        val strategy = when (type) {
            AuthType.EMAIL -> emailStrategy
            AuthType.GOOGLE -> googleStrategy
            AuthType.BIOMETRIC -> biometricStrategy
        }
        return strategy.authenticate(credentials)
    }
}
```

### Chain of Responsibility
- **When**: A request should pass through a sequence of handlers.
- **Android use**: OkHttp interceptors, validation pipelines, auth token refresh chain.
- **Notes**: Keep each handler focused and easily testable.

```kotlin
// core/network - Chain of interceptors
class AuthInterceptor @Inject constructor(
    private val tokenProvider: TokenProvider
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenProvider.getToken()
        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()
        return chain.proceed(request) // Pass to next handler
    }
}

class RetryInterceptor @Inject constructor() : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        var response = chain.proceed(request)
        
        var retryCount = 0
        while (!response.isSuccessful && retryCount < MAX_RETRIES) {
            response.close()
            retryCount++
            Thread.sleep(RETRY_DELAY_MS)
            response = chain.proceed(request)
        }
        
        return response
    }
    
    companion object {
        private const val MAX_RETRIES = 3
        private val RETRY_DELAY = 1.seconds
    }
}

class LoggingInterceptor @Inject constructor(
    private val logger: Logger
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        logger.d("Request: ${request.method} ${request.url}")
        
        val response = chain.proceed(request)
        
        logger.d("Response: ${response.code} ${request.url}")
        return response
    }
}

// DI setup - Chain is configured here
@Provides
@Singleton
fun provideOkHttpClient(
    authInterceptor: AuthInterceptor,
    retryInterceptor: RetryInterceptor,
    loggingInterceptor: LoggingInterceptor
): OkHttpClient = OkHttpClient.Builder()
    .addInterceptor(authInterceptor) // First handler
    .addInterceptor(retryInterceptor) // Second handler
    .addInterceptor(loggingInterceptor) // Third handler
    .build()
```

### Command
- **When**: You want to encapsulate actions as objects.
- **Android use**: UI actions/intents from screens → ViewModel.
- **Notes**: Prefer sealed `Action` types in the Presentation layer. See `references/compose-patterns.md`.

```kotlin
// feature/auth - Commands (Actions)
sealed interface AuthAction {
    data class EmailChanged(val email: String) : AuthAction
    data class PasswordChanged(val password: String) : AuthAction
    data object LoginClicked : AuthAction
    data object RegisterClicked : AuthAction
    data object ForgotPasswordClicked : AuthAction
    data object GoogleLoginClicked : AuthAction
}

// feature/auth - Command processor (ViewModel)
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    fun onAction(action: AuthAction) {
        when (action) {
            is AuthAction.EmailChanged -> handleEmailChanged(action.email)
            is AuthAction.PasswordChanged -> handlePasswordChanged(action.password)
            AuthAction.LoginClicked -> handleLogin()
            AuthAction.RegisterClicked -> handleRegister()
            AuthAction.ForgotPasswordClicked -> handleForgotPassword()
            AuthAction.GoogleLoginClicked -> handleGoogleLogin()
        }
    }
    
    private fun handleLogin() {
        viewModelScope.launch {
            authRepository.login(email, password)
        }
    }
    
    private fun handleGoogleLogin() {
        viewModelScope.launch {
            authRepository.loginWithGoogle()
        }
    }
}

// feature/auth - UI sends commands
@Composable
fun LoginScreen(onAction: (AuthAction) -> Unit) {
    Button(onClick = { onAction(AuthAction.LoginClicked) }) {
        Text("Login")
    }
    
    Button(onClick = { onAction(AuthAction.GoogleLoginClicked) }) {
        Text("Login with Google")
    }
}
```

### Iterator
- **When**: You need sequential access without exposing structure.
- **Android use**: Paging data flows, cursor traversal in data layer.
- **Notes**: Keep iteration in data/paging layers, not UI.

```kotlin
// core/data - Iterator for paginated data
class PaginatedUserIterator(
    private val api: UserApi,
    private val pageSize: Int = 20
) {
    private var currentPage = 0
    private var hasMore = true
    
    suspend fun hasNext(): Boolean = hasMore
    
    suspend fun next(): List<User> {
        if (!hasMore) return emptyList()
        
        val response = api.getUsers(page = currentPage, size = pageSize)
        currentPage++
        hasMore = response.users.size == pageSize
        
        return response.users
    }
}

// Better: Use Flow for continuous iteration
class UserRepository @Inject constructor(
    private val api: UserApi
) {
    fun getUsers(): Flow<PagingData<User>> = Pager(
        config = PagingConfig(pageSize = 20),
        pagingSourceFactory = { UserPagingSource(api) }
    ).flow
}

// core/database - Cursor iterator
class DatabaseCursor(private val cursor: Cursor) : Iterator<User> {
    override fun hasNext(): Boolean = !cursor.isAfterLast
    
    override fun next(): User {
        val user = User(
            id = cursor.getString(cursor.getColumnIndexOrThrow("id")),
            name = cursor.getString(cursor.getColumnIndexOrThrow("name"))
        )
        cursor.moveToNext()
        return user
    }
}
```

### Mediator
- **When**: Multiple components need coordinated interaction.
- **Android use**: App-level navigation coordinator (`AppNavigation`).
- **Notes**: Keeps features independent of each other. See `references/modularization.md`.

```kotlin
// app - Mediator coordinates feature navigation using Navigation3
class AppNavigationMediator @Inject constructor(
    private val navigator: Navigator
) : AuthNavigator, ProfileNavigator, SettingsNavigator {
    
    // AuthNavigator implementation
    override fun navigateToHome() {
        navigator.navigate(TopLevelRoute.Home)
    }
    
    override fun navigateToProfile() {
        navigator.navigate(TopLevelRoute.Profile)
    }
    
    // ProfileNavigator implementation
    override fun navigateToSettings() {
        navigator.navigate(TopLevelRoute.Settings)
    }
    
    override fun navigateToAuth() {
        navigator.navigate(TopLevelRoute.Auth)
    }
    
    // SettingsNavigator implementation
    override fun navigateBack() {
        navigator.goBack()
    }
    
    override fun logout() {
        navigator.navigate(TopLevelRoute.Auth)
    }
}

// Features don't know about each other, only their own Navigator interface
// The mediator coordinates cross-feature navigation
```

### Memento
- **When**: You must restore state without breaking encapsulation.
- **Android use**: `SavedStateHandle`, restoring form drafts or auth flows.
- **Notes**: Keep state snapshots minimal and serializable.

```kotlin
// feature/auth - Memento (state snapshot)
@Serializable
data class AuthFormMemento(
    val email: String,
    val password: String,
    val rememberMe: Boolean,
    val timestamp: Long = Clock.System.now().toEpochMilliseconds()
)

// feature/auth - Originator (creates and restores mementos)
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    
    private companion object {
        const val KEY_FORM_STATE = "auth_form_state"
    }
    
    init {
        // Restore from memento
        restoreState()
    }
    
    private val _email = MutableStateFlow("")
    val email: StateFlow<String> = _email.asStateFlow()
    
    private val _password = MutableStateFlow("")
    val password: StateFlow<String> = _password.asStateFlow()
    
    private val _rememberMe = MutableStateFlow(false)
    val rememberMe: StateFlow<Boolean> = _rememberMe.asStateFlow()
    
    fun onEmailChanged(value: String) {
        _email.value = value
        saveState()
    }
    
    fun onPasswordChanged(value: String) {
        _password.value = value
        saveState()
    }
    
    fun onRememberMeChanged(value: Boolean) {
        _rememberMe.value = value
        saveState()
    }
    
    private fun saveState() {
        val memento = AuthFormMemento(
            email = _email.value,
            password = _password.value,
            rememberMe = _rememberMe.value
        )
        savedStateHandle[KEY_FORM_STATE] = memento
    }
    
    private fun restoreState() {
        savedStateHandle.get<AuthFormMemento>(KEY_FORM_STATE)?.let { memento ->
            _email.value = memento.email
            _password.value = memento.password
            _rememberMe.value = memento.rememberMe
        }
    }
}
```

### State
- **When**: Behavior changes with state.
- **Android use**: `UiState` sealed types and state-driven UI.
- **Notes**: Keep transitions in ViewModel; UI only renders. See `references/compose-patterns.md`.

```kotlin
// feature/auth - State hierarchy
@Immutable
sealed interface AuthUiState {
    data object Loading : AuthUiState
    
    data class LoginForm(
        val email: String = "",
        val password: String = "",
        val error: String? = null,
        val isLoading: Boolean = false
    ) : AuthUiState
    
    data class TwoFactorRequired(
        val maskedPhone: String
    ) : AuthUiState
    
    data class Success(
        val user: User
    ) : AuthUiState
    
    data class Error(
        val message: String,
        val canRetry: Boolean = true
    ) : AuthUiState
}

// feature/auth - State machine (ViewModel)
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    private val _uiState = MutableStateFlow<AuthUiState>(AuthUiState.LoginForm())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    fun onLoginClicked() {
        val currentState = _uiState.value as? AuthUiState.LoginForm ?: return
        
        // Transition: LoginForm → Loading
        _uiState.value = currentState.copy(isLoading = true, error = null)
        
        viewModelScope.launch {
            authRepository.login(currentState.email, currentState.password).fold(
                onSuccess = { result ->
                    // Transition based on result
                    _uiState.value = when {
                        result.requires2FA -> AuthUiState.TwoFactorRequired(result.maskedPhone)
                        else -> AuthUiState.Success(result.user)
                    }
                },
                onFailure = { error ->
                    // Transition: Loading → LoginForm with error
                    _uiState.value = currentState.copy(
                        isLoading = false,
                        error = error.message
                    )
                }
            )
        }
    }
}

// feature/auth - State-driven UI
@Composable
fun AuthScreen(uiState: AuthUiState) {
    when (uiState) {
        is AuthUiState.Loading -> LoadingScreen()
        is AuthUiState.LoginForm -> LoginFormScreen(uiState)
        is AuthUiState.TwoFactorRequired -> TwoFactorScreen(uiState)
        is AuthUiState.Success -> SuccessScreen(uiState)
        is AuthUiState.Error -> ErrorScreen(uiState)
    }
}
```

### Template Method
- **When**: You need a fixed algorithm with varying steps.
- **Android use**: Base worker patterns or shared use case flows (use sparingly).
- **Notes**: Prefer composition/delegation over inheritance. See `references/kotlin-delegation.md`.

```kotlin
// ❌ Bad: Inheritance-based template method
abstract class BaseAuthUseCase {
    suspend fun execute(credentials: Credentials): Result<AuthToken> {
        validate(credentials)
        val token = authenticate(credentials)
        saveToken(token)
        return Result.success(token)
    }
    
    protected abstract fun validate(credentials: Credentials)
    protected abstract suspend fun authenticate(credentials: Credentials): AuthToken
    protected abstract suspend fun saveToken(token: AuthToken)
}

// ✅ Good: Composition-based (Strategy pattern)
interface CredentialsValidator {
    fun validate(credentials: Credentials)
}

interface Authenticator {
    suspend fun authenticate(credentials: Credentials): AuthToken
}

interface TokenStorage {
    suspend fun saveToken(token: AuthToken)
}

class LoginUseCase @Inject constructor(
    private val validator: CredentialsValidator,
    private val authenticator: Authenticator,
    private val storage: TokenStorage
) {
    suspend operator fun invoke(credentials: Credentials): Result<AuthToken> =
        runCatching {
            validator.validate(credentials)
            val token = authenticator.authenticate(credentials)
            storage.saveToken(token)
            token
        }
}
```

### Visitor
- **When**: You need to run operations over a structure without changing it.
- **Android use**: Analytics/event inspection over `UiState` or navigation events.
- **Notes**: Use only if it improves clarity; avoid overengineering.

```kotlin
// core/analytics - Visitor interface
interface AnalyticsVisitor {
    fun visit(state: AuthUiState.LoginForm)
    fun visit(state: AuthUiState.TwoFactorRequired)
    fun visit(state: AuthUiState.Success)
    fun visit(state: AuthUiState.Error)
}

// core/analytics - Concrete visitor
class FirebaseAnalyticsVisitor @Inject constructor(
    private val analytics: FirebaseAnalytics
) : AnalyticsVisitor {
    
    override fun visit(state: AuthUiState.LoginForm) {
        analytics.logEvent("auth_login_form_shown", bundleOf(
            "has_error" to (state.error != null)
        ))
    }
    
    override fun visit(state: AuthUiState.TwoFactorRequired) {
        analytics.logEvent("auth_2fa_required", bundleOf(
            "phone_masked" to state.maskedPhone
        ))
    }
    
    override fun visit(state: AuthUiState.Success) {
        analytics.logEvent("auth_success", bundleOf(
            "user_id" to state.user.id
        ))
    }
    
    override fun visit(state: AuthUiState.Error) {
        analytics.logEvent("auth_error", bundleOf(
            "error_message" to state.message,
            "can_retry" to state.canRetry
        ))
    }
}

// feature/auth - States accept visitors
@Immutable
sealed interface AuthUiState {
    fun accept(visitor: AnalyticsVisitor)
    
    data class LoginForm(...) : AuthUiState {
        override fun accept(visitor: AnalyticsVisitor) = visitor.visit(this)
    }
    
    data class TwoFactorRequired(...) : AuthUiState {
        override fun accept(visitor: AnalyticsVisitor) = visitor.visit(this)
    }
    
    data class Success(...) : AuthUiState {
        override fun accept(visitor: AnalyticsVisitor) = visitor.visit(this)
    }
    
    data class Error(...) : AuthUiState {
        override fun accept(visitor: AnalyticsVisitor) = visitor.visit(this)
    }
}

// Usage
val visitor = FirebaseAnalyticsVisitor(analytics)
uiState.accept(visitor)
```

## Kotlin-Specific Patterns

### Result Type
- **When**: Operations can fail and you need type-safe error handling.
- **Android use**: Repository methods, use cases, network calls.
- **Notes**: Prefer `Result<T>` over throwing exceptions for expected failures.

```kotlin
// core/domain - Use Result for fallible operations
@Stable
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
}

// core/data - Implementation
class AuthRepositoryImpl @Inject constructor(
    private val remoteDataSource: AuthRemoteDataSource
) : AuthRepository {
    
    override suspend fun login(email: String, password: String): Result<AuthToken> =
        try {
            val token = remoteDataSource.login(email, password)
            Result.success(token)
        } catch (e: IOException) {
            Result.failure(AuthError.NetworkError("No internet connection", e))
        } catch (e: HttpException) {
            when (e.code()) {
                401 -> Result.failure(AuthError.InvalidCredentials("Invalid credentials"))
                else -> Result.failure(AuthError.ServerError("Server error", e))
            }
        }
}

// feature/auth - Handle Result
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    
    fun onLoginClicked(email: String, password: String) {
        viewModelScope.launch {
            authRepository.login(email, password).fold(
                onSuccess = { token ->
                    _uiState.update { AuthUiState.Success(token.user) }
                },
                onFailure = { error ->
                    val message = when (error) {
                        is AuthError.NetworkError -> "No internet connection"
                        is AuthError.InvalidCredentials -> "Invalid email or password"
                        is AuthError.ServerError -> "Server error. Please try again"
                        else -> "Unknown error"
                    }
                    _uiState.update { AuthUiState.Error(message) }
                }
            )
        }
    }
}
```

### Sealed Classes for Exhaustive State
- **When**: You need a closed set of related types with exhaustive `when` checks.
- **Android use**: `UiState`, domain errors, navigation destinations, actions.
- **Notes**: Always use sealed classes/interfaces for state hierarchies.

```kotlin
// core/domain - Sealed error hierarchy
sealed class AuthError(message: String, cause: Throwable? = null) : Exception(message, cause) {
    class NetworkError(message: String, cause: Throwable? = null) : AuthError(message, cause)
    class InvalidCredentials(message: String) : AuthError(message)
    class UserAlreadyExists(message: String) : AuthError(message)
    class ServerError(message: String, cause: Throwable? = null) : AuthError(message, cause)
    class UnknownError(message: String, cause: Throwable? = null) : AuthError(message, cause)
}

// feature/auth - Exhaustive when
fun handleAuthError(error: AuthError): String = when (error) {
    is AuthError.NetworkError -> "No internet connection"
    is AuthError.InvalidCredentials -> "Invalid email or password"
    is AuthError.UserAlreadyExists -> "Email already registered"
    is AuthError.ServerError -> "Server error. Please try again"
    is AuthError.UnknownError -> "An unexpected error occurred"
} // Compiler ensures all cases are handled

// core/domain - Sealed navigation destinations
sealed interface AuthDestination {
    data object Login : AuthDestination
    data object Register : AuthDestination
    data class ResetPassword(val email: String) : AuthDestination
    data class TwoFactor(val phone: String) : AuthDestination
}
```

### Data Classes with Copy
- **When**: You need immutable value objects with easy modification.
- **Android use**: Domain models, UI state, DTOs.
- **Notes**: Mark with `@Immutable` for Compose stability.

```kotlin
@Immutable
data class User(
    val id: String,
    val email: String,
    val name: String,
    val profileUrl: String? = null,
    val isVerified: Boolean = false,
    val createdAt: Long = 0L
)

// Easy immutable updates with copy()
val user = User(id = "1", email = "test@example.com", name = "Test")
val verified = user.copy(isVerified = true) // New instance, original unchanged

// In ViewModel
@HiltViewModel
class ProfileViewModel @Inject constructor() : ViewModel() {
    private val _user = MutableStateFlow(User("", "", ""))
    val user: StateFlow<User> = _user.asStateFlow()
    
    fun updateName(newName: String) {
        _user.update { it.copy(name = newName) }
    }
    
    fun markVerified() {
        _user.update { it.copy(isVerified = true) }
    }
}
```

### Extension Functions for Domain Logic
- **When**: You need to add functionality to existing types without inheritance.
- **Android use**: Domain transformations, UI formatting, validation.
- **Notes**: Keep extensions in the same module as the type or in a shared `common` module.

```kotlin
// core/domain - Domain extensions
fun User.isActive(): Boolean = isVerified && createdAt > 0L

fun User.displayName(): String = name.ifEmpty { email.substringBefore("@") }

fun List<User>.filterActive(): List<User> = filter { it.isActive() }

// core/ui - UI extensions
fun User.toUiModel(): UserUiModel = UserUiModel(
    name = displayName(),
    email = email,
    avatarUrl = profileUrl,
    badge = if (isVerified) "Verified" else null
)

fun Instant.formatRelativeTime(): String {
    val now = Clock.System.now()
    val duration = now - this
    
    return when {
        duration < 1.minutes -> "Just now"
        duration < 1.hours -> "${duration.inWholeMinutes}m ago"
        duration < 24.hours -> "${duration.inWholeHours}h ago"
        else -> "${duration.inWholeDays}d ago"
    }
}

// Usage
@Composable
fun UserCard(user: User) {
    if (user.isActive()) {
        Text(text = user.displayName())
        Text(text = user.createdAt.formatRelativeTime())
    }
}
```

## Anti-Patterns to Avoid

### Static Context References
- **Problem**: Holding `Context` in static objects causes memory leaks.
- **Solution**: Inject `Context` via DI or use `Application` context.

```kotlin
// ❌ Bad: Static context
object BadLogger {
    private lateinit var context: Context
    
    fun init(context: Context) {
        this.context = context // Memory leak!
    }
}

// ✅ Good: Injected context
@Singleton
class Logger @Inject constructor(
    @ApplicationContext private val context: Context
)
```

### LiveData in New Code
- **Problem**: LiveData is lifecycle-aware but lacks Flow's power.
- **Solution**: Use `StateFlow` and `collectAsStateWithLifecycle()` in Compose.

```kotlin
// ❌ Bad: LiveData in new Compose code
class BadViewModel : ViewModel() {
    private val _state = MutableLiveData<UiState>()
    val state: LiveData<UiState> = _state
}

// ✅ Good: StateFlow
class GoodViewModel : ViewModel() {
    private val _state = MutableStateFlow<UiState>(UiState.Loading)
    val state: StateFlow<UiState> = _state.asStateFlow()
}
```

### God Objects
- **Problem**: One class does too much, violating Single Responsibility.
- **Solution**: Split into focused components.

```kotlin
// ❌ Bad: God object
class AuthManager {
    fun validateEmail(email: String): Boolean { }
    fun validatePassword(password: String): Boolean { }
    fun login(email: String, password: String) { }
    fun register(user: User) { }
    fun resetPassword(email: String) { }
    fun saveToken(token: String) { }
    fun getToken(): String? { }
    fun logout() { }
    fun refreshToken() { }
    fun checkAuthStatus() { }
}

// ✅ Good: Separated concerns
interface AuthRepository {
    suspend fun login(email: String, password: String): Result<AuthToken>
    suspend fun register(user: User): Result<Unit>
}

interface TokenStorage {
    suspend fun saveToken(token: String)
    suspend fun getToken(): String?
}

class EmailValidator {
    fun validate(email: String): Boolean
}

class PasswordValidator {
    fun validate(password: String): Boolean
}
```

### GlobalScope Usage
- **Problem**: Survives ViewModel/Activity lifecycle, causes leaks.
- **Solution**: Use `viewModelScope`, `lifecycleScope`, or custom scopes.

```kotlin
// ❌ Bad: GlobalScope
class BadViewModel : ViewModel() {
    fun loadData() {
        GlobalScope.launch { // Survives ViewModel!
            repository.getData()
        }
    }
}

// ✅ Good: viewModelScope
class GoodViewModel : ViewModel() {
    fun loadData() {
        viewModelScope.launch { // Canceled when ViewModel cleared
            repository.getData()
        }
    }
}
```

### Mutable Collections in Data Classes
- **Problem**: Breaks immutability contract; Compose can't detect changes.
- **Solution**: Use immutable collections or `PersistentList`.

```kotlin
// ❌ Bad: Mutable collection
@Immutable // This is a lie!
data class UserList(
    val users: MutableList<User>
)

// ✅ Good: Immutable collection
@Immutable
data class UserList(
    val users: List<User> // Immutable interface
)

// ✅ Better: Persistent collection
@Immutable
data class UserList(
    val users: PersistentList<User> // Efficient immutable updates
)
```

### Premature Abstraction
- **Problem**: Adding patterns before they're needed.
- **Solution**: Start simple, refactor when complexity emerges.

```kotlin
// ❌ Bad: Over-engineered for simple case
interface UserRepository {
    suspend fun getUser(): Result<User>
}

class UserRepositoryImpl @Inject constructor(
    private val dataSourceFactory: UserDataSourceFactory
) : UserRepository {
    override suspend fun getUser(): Result<User> {
        val dataSource = dataSourceFactory.create()
        return dataSource.fetch()
    }
}

// ✅ Good: Simple, direct
class UserRepository @Inject constructor(
    private val api: UserApi
) {
    suspend fun getUser(): Result<User> = runCatching {
        api.getUser()
    }
}
```

### Nested Callbacks (Callback Hell)
- **Problem**: Hard to read and maintain.
- **Solution**: Use coroutines and structured concurrency.

```kotlin
// ❌ Bad: Callback hell
fun login(email: String, password: String, callback: (Result) -> Unit) {
    validateEmail(email) { isValid ->
        if (isValid) {
            authenticateUser(email, password) { authResult ->
                if (authResult.success) {
                    saveToken(authResult.token) {
                        loadUserProfile(authResult.userId) { profile ->
                            callback(Result.Success(profile))
                        }
                    }
                } else {
                    callback(Result.Error("Auth failed"))
                }
            }
        } else {
            callback(Result.Error("Invalid email"))
        }
    }
}

// ✅ Good: Coroutines with sequential clarity
suspend fun login(email: String, password: String): Result<User> =
    try {
        validateEmail(email)
        val authResult = authenticateUser(email, password)
        saveToken(authResult.token)
        val profile = loadUserProfile(authResult.userId)
        Result.success(profile)
    } catch (e: Exception) {
        Result.failure(e)
    }
```

### Feature-to-Feature Dependencies
- **Problem**: Creates coupling; breaks modularity.
- **Solution**: Use app module as mediator with `Navigator` interfaces.

```kotlin
// ❌ Bad: Feature depends on another feature
// feature/profile
class ProfileViewModel @Inject constructor(
    private val authViewModel: AuthViewModel // Feature-to-feature dependency!
) : ViewModel()

// ✅ Good: Features depend on domain, app mediates
// feature/profile
interface ProfileNavigator {
    fun navigateToAuth()
}

class ProfileViewModel @Inject constructor(
    private val navigator: ProfileNavigator // Interface in feature, impl in app
) : ViewModel()

// app - Mediator
class AppNavigator(private val navigator: Navigator) : ProfileNavigator, AuthNavigator {
    override fun navigateToAuth() {
        navigator.navigate(TopLevelRoute.Auth)
    }
}
```

## Summary

- **MVVM** is our base architecture (see `references/architecture.md`)
- **Repository** pattern for all data access
- **Delegation** over inheritance (see `references/kotlin-delegation.md`)
- **Sealed classes** for exhaustive state modeling
- **Result<T>** for type-safe error handling
- **Flow/StateFlow** for reactive streams (see `references/coroutines-patterns.md`)
- **Navigator interfaces** for cross-feature navigation (see `references/modularization.md`)
- **Avoid**: LiveData, GlobalScope, god objects, premature abstraction, feature-to-feature dependencies

Use patterns to solve real problems, not to add complexity.
