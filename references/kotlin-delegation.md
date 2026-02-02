# Kotlin Delegation (Composition over Inheritance)

Use Kotlin's class and property delegation (`by`) to share behavior across ViewModels and classes without relying on base classes or inheritance.
This keeps responsibilities explicit, improves testability, and avoids deep inheritance chains.

## Table of Contents
1. [Why Delegation in Android](#why-delegation-in-android)
2. [When to Use Delegation](#when-to-use-delegation)
3. [Class Delegation](#class-delegation)
4. [Property Delegation](#property-delegation)
5. [Advanced Patterns](#advanced-patterns)
6. [Testing with Delegation](#testing-with-delegation)
7. [Best Practices](#best-practices)

## Why Delegation in Android

- **Avoid base class bloat**: Split cross-cutting concerns (logging, validation, feature flags) into focused interfaces.
- **Swap implementations easily**: Delegates are injected, so tests can replace them with fakes.
- **Keep ViewModels lean**: Behavior is composed instead of inherited.
- **Enable decorators**: Layer additional behavior without modifying original classes.
- **No performance overhead**: Delegation creates minimal wrapper objects with negligible impact.

## When to Use Delegation

- Shared behavior across multiple ViewModels or classes
- Behavior not tied to Android framework inheritance requirements
- Logic that benefits from clear interfaces and DI (e.g., validators, analytics, feature flags)
- When you need to layer behavior (decorator pattern)
- State management in ViewModels (`by mutableStateOf`)

## When Not to Use It

- Single-use logic with no reuse potential
- Cases where delegation adds indirection without value
- Framework-required inheritance (e.g., `Activity`, `Application`, `ViewModel` itself)
- Extremely performance-critical paths (rare; measure first)

## Class Delegation

### Basic Pattern

```kotlin
interface Logger {
    fun log(message: String)
}

class ConsoleLogger : Logger {
    override fun log(message: String) {
        println("LOG: $message")
    }
}

class ExampleViewModel(
    private val savedStateHandle: SavedStateHandle,
    logger: Logger // No private - delegated only
) : ViewModel(), Logger by logger {
    fun runAction() {
        log("Action started") // Delegated method
    }
}
```

### Inheritance vs Delegation Comparison

```kotlin
// ❌ Bad: Deep inheritance hierarchy
abstract class BaseViewModel : ViewModel() {
    abstract fun log(message: String)
    abstract fun validateEmail(email: String): String?
    abstract fun trackEvent(name: String)
    
    fun commonLogic() {
        log("Common logic executed")
    }
}

class LoginViewModel : BaseViewModel() {
    override fun log(message: String) {
        println("LOG: $message")
    }
    
    override fun validateEmail(email: String): String? {
        return if (email.contains("@")) null else "Invalid email"
    }
    
    override fun trackEvent(name: String) {
        // Analytics logic
    }
    
    // Tightly coupled to base class
}

// ✅ Good: Composition with delegation
interface Logger {
    fun log(message: String)
}

interface FormValidator {
    fun validateEmail(email: String): ValidationResult
}

interface Analytics {
    fun trackEvent(name: String)
}

@HiltViewModel
class LoginViewModel @Inject constructor(
    logger: Logger,
    validator: FormValidator,
    analytics: Analytics
) : ViewModel(),
    Logger by logger,
    FormValidator by validator,
    Analytics by analytics {
    
    // Independent, testable, swappable behavior
    fun onLoginClicked(email: String) {
        val result = validateEmail(email)
        when (result) {
            is ValidationResult.Valid -> {
                log("Login attempt for: $email")
                trackEvent("login_clicked")
            }
            is ValidationResult.Invalid -> {
                log("Validation failed: ${result.error}")
            }
        }
    }
}
```

### Multiple Interface Delegation

```kotlin
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle,
    crashReporter: CrashReporter, // No private - delegated only
    logger: CrashlyticsStateLogger // No private - delegated only
) : ViewModel(), 
    CrashReporter by crashReporter,
    CrashlyticsStateLogger by logger {

    fun onRoleSelected(role: String) {
        logUiState("auth_role", role) // From CrashlyticsStateLogger
        logAction("Auth role selected: $role") // From CrashlyticsStateLogger
    }
    
    fun onLoginFailed(error: Throwable) {
        recordException( // From CrashReporter
            error,
            mapOf("action" to "login", "screen" to "auth")
        )
    }
}
```

### Overriding Delegated Methods

For the `CrashReporter` interface definition and implementations (`FirebaseCrashReporter`, `SentryCrashReporter`, `PrivacyAwareCrashReporter`), see `references/crashlytics.md` → "Provider-Agnostic Interface" and "Data Scrubbing (Privacy/GDPR)" sections.

Example of overriding delegated methods:

```kotlin
// Decorator pattern with delegation
// (Full CrashReporter interface in references/crashlytics.md → "Provider-Agnostic Interface")
class PrivacyAwareCrashReporter(
    crashReporter: CrashReporter // No private - delegated only
) : CrashReporter by crashReporter {
    
    // Override to add custom behavior
    override fun recordException(
        throwable: Throwable,
        context: Map<String, String>
    ) {
        // Custom pre-processing (scrub sensitive data)
        val scrubbedContext = scrubbingLogic(context)
        
        // Call delegated implementation
        super.recordException(throwable, scrubbedContext)
    }
    
    // Other methods (setUserId, setUserProperty, log) are fully delegated
}
```

### Form Validation with Sealed Errors

```kotlin
// core/domain - Sealed error types
sealed class ValidationError {
    data object InvalidEmail : ValidationError()
    data object PasswordTooShort : ValidationError()
    data object PasswordTooWeak : ValidationError()
    data object PasswordMismatch : ValidationError()
}

sealed class ValidationResult {
    data object Valid : ValidationResult()
    data class Invalid(val error: ValidationError) : ValidationResult()
}

// core/domain - Validator interface
interface FormValidator {
    fun validateEmail(email: String): ValidationResult
    fun validatePassword(password: String): ValidationResult
    fun validatePasswordMatch(password: String, confirmPassword: String): ValidationResult
}

// core/data - Implementation
class DefaultFormValidator @Inject constructor() : FormValidator {
    
    override fun validateEmail(email: String): ValidationResult =
        if (email.matches(EMAIL_REGEX)) {
            ValidationResult.Valid
        } else {
            ValidationResult.Invalid(ValidationError.InvalidEmail)
        }
    
    override fun validatePassword(password: String): ValidationResult =
        when {
            password.length < 8 -> ValidationResult.Invalid(ValidationError.PasswordTooShort)
            !password.matches(PASSWORD_STRENGTH_REGEX) -> ValidationResult.Invalid(ValidationError.PasswordTooWeak)
            else -> ValidationResult.Valid
        }
    
    override fun validatePasswordMatch(password: String, confirmPassword: String): ValidationResult =
        if (password == confirmPassword) {
            ValidationResult.Valid
        } else {
            ValidationResult.Invalid(ValidationError.PasswordMismatch)
        }
    
    companion object {
        private val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
        private val PASSWORD_STRENGTH_REGEX = Regex("^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d).+$")
    }
}

// feature/auth - ViewModel with delegation
@HiltViewModel
class RegisterViewModel @Inject constructor(
    private val registerUseCase: RegisterUseCase,
    private val savedStateHandle: SavedStateHandle,
    validator: FormValidator // No private - delegated only
) : ViewModel(), FormValidator by validator {

    private val _formState = MutableStateFlow(RegisterFormState())
    val formState: StateFlow<RegisterFormState> = _formState.asStateFlow()

    fun onEmailChanged(email: String) {
        _formState.update { it.copy(email = email) }
        
        val result = validateEmail(email) // Delegated method
        _formState.update {
            when (result) {
                is ValidationResult.Valid -> it.copy(emailError = null)
                is ValidationResult.Invalid -> it.copy(emailError = result.error.toMessage())
            }
        }
    }
    
    fun onPasswordChanged(password: String) {
        _formState.update { it.copy(password = password) }
        
        val result = validatePassword(password) // Delegated method
        _formState.update {
            when (result) {
                is ValidationResult.Valid -> it.copy(passwordError = null)
                is ValidationResult.Invalid -> it.copy(passwordError = result.error.toMessage())
            }
        }
    }
    
    private fun ValidationError.toMessage(): String = when (this) {
        ValidationError.InvalidEmail -> "Invalid email format"
        ValidationError.PasswordTooShort -> "Password must be at least 8 characters"
        ValidationError.PasswordTooWeak -> "Password must contain uppercase, lowercase, and number"
        ValidationError.PasswordMismatch -> "Passwords do not match"
    }
}
```

## Property Delegation

### Lazy Initialization

```kotlin
class UserRepository @Inject constructor(
    private val database: UserDatabase,
    private val api: UserApi
) {
    // Expensive object initialized only when first accessed
    private val userCache: MutableMap<String, User> by lazy {
        mutableMapOf<String, User>()
    }
    
    suspend fun getUser(userId: String): User =
        userCache.getOrPut(userId) {
            api.getUser(userId)
        }
}

// Analytics initialized only when needed
class AnalyticsManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private val analytics: FirebaseAnalytics by lazy {
        FirebaseAnalytics.getInstance(context)
    }
    
    fun logEvent(name: String) {
        analytics.logEvent(name, null)
    }
}
```

### State Delegation with mutableStateOf

```kotlin
@Stable
class SearchState {
    var query by mutableStateOf("")
        private set
    
    var isLoading by mutableStateOf(false)
        private set
    
    var results by mutableStateOf<List<SearchResult>>(emptyList())
        private set
    
    var error by mutableStateOf<String?>(null)
        private set
    
    fun updateQuery(newQuery: String) {
        query = newQuery
    }
    
    fun setLoading(loading: Boolean) {
        isLoading = loading
    }
    
    fun setResults(newResults: List<SearchResult>) {
        results = newResults
        error = null
    }
    
    fun setError(message: String) {
        error = message
        results = emptyList()
    }
}

@HiltViewModel
class SearchViewModel @Inject constructor(
    private val searchRepository: SearchRepository
) : ViewModel() {
    val state = SearchState()
    
    fun onQueryChanged(query: String) {
        state.updateQuery(query)
        search()
    }
    
    private fun search() {
        viewModelScope.launch {
            state.setLoading(true)
            searchRepository.search(state.query).fold(
                onSuccess = { state.setResults(it) },
                onFailure = { state.setError(it.message ?: "Unknown error") }
            )
            state.setLoading(false)
        }
    }
}
```

### Observable Properties (Custom Delegates)

```kotlin
// Custom delegate for observable properties
class Observable<T>(
    private var value: T,
    private val onChange: (T) -> Unit
) {
    operator fun getValue(thisRef: Any?, property: KProperty<*>): T = value
    
    operator fun setValue(thisRef: Any?, property: KProperty<*>, newValue: T) {
        if (value != newValue) {
            value = newValue
            onChange(newValue)
        }
    }
}

fun <T> observable(initialValue: T, onChange: (T) -> Unit) =
    Observable(initialValue, onChange)

// Usage
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository
) : ViewModel() {
    
    var darkMode by observable(false) { newValue ->
        // Called whenever darkMode changes
        viewModelScope.launch {
            settingsRepository.saveDarkMode(newValue)
        }
    }
    
    var notificationsEnabled by observable(true) { newValue ->
        viewModelScope.launch {
            settingsRepository.saveNotifications(newValue)
        }
    }
}
```

## Advanced Patterns

### Complex Real-World Example

**Note**: For `CrashReporter` interface and implementation details, see `references/crashlytics.md` → "Provider-Agnostic Interface" and "Implementation Examples" sections.

```kotlin
// Interfaces for different concerns
interface Logger {
    fun log(message: String)
    fun logError(message: String, throwable: Throwable)
}

// CrashReporter interface definition in references/crashlytics.md → "Provider-Agnostic Interface"
// interface CrashReporter { ... }

interface Analytics {
    fun trackEvent(name: String, properties: Map<String, Any> = emptyMap())
}

interface FormValidator {
    fun validateEmail(email: String): ValidationResult
    fun validatePassword(password: String): ValidationResult
}

// ViewModel composing all behaviors
@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val savedStateHandle: SavedStateHandle,
    logger: Logger,
    crashReporter: CrashReporter,
    analytics: Analytics,
    validator: FormValidator
) : ViewModel(),
    Logger by logger,
    CrashReporter by crashReporter,
    Analytics by analytics,
    FormValidator by validator {
    
    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    fun onLoginClicked(email: String, password: String) {
        viewModelScope.launch {
            // Validation (delegated)
            val emailResult = validateEmail(email)
            val passwordResult = validatePassword(password)
            
            if (emailResult is ValidationResult.Invalid) {
                logError("Email validation failed", Exception("Invalid: ${emailResult.error}"))
                _uiState.update { it.copy(emailError = emailResult.error.toMessage()) }
                return@launch
            }
            
            if (passwordResult is ValidationResult.Invalid) {
                logError("Password validation failed", Exception("Invalid: ${passwordResult.error}"))
                _uiState.update { it.copy(passwordError = passwordResult.error.toMessage()) }
                return@launch
            }
            
            // Logging (delegated)
            log("Login attempt started for: $email")
            
            // Set user context (delegated)
            setUserId(email)
            setUserProperty("login_method", "email")
            
            // Analytics (delegated)
            trackEvent("login_attempt", mapOf("method" to "email"))
            
            _uiState.update { it.copy(isLoading = true) }
            
            authRepository.login(email, password).fold(
                onSuccess = { token ->
                    log("Login successful")
                    trackEvent("login_success")
                    _uiState.update { it.copy(isLoading = false, success = true) }
                },
                onFailure = { error ->
                    logError("Login failed", error)
                    recordException(error, mapOf( // Crash reporting (delegated)
                        "screen" to "login",
                        "action" to "login_clicked",
                        "email_domain" to email.substringAfter("@")
                    ))
                    trackEvent("login_failure", mapOf("error" to error.message.orEmpty()))
                    _uiState.update { it.copy(isLoading = false, error = error.message) }
                }
            )
        }
    }
}
```

## Testing with Delegation

### Creating Test Fakes

**Note**: For `CrashReporter` interface, see `references/crashlytics.md` → "Provider-Agnostic Interface".

```kotlin
// Test fakes for delegated interfaces
class FakeLogger : Logger {
    val messages = mutableListOf<String>()
    val errors = mutableListOf<Pair<String, Throwable>>()
    
    override fun log(message: String) {
        messages.add(message)
    }
    
    override fun logError(message: String, throwable: Throwable) {
        errors.add(message to throwable)
    }
}

// Test fake for CrashReporter (interface in references/crashlytics.md → "Provider-Agnostic Interface")
class FakeCrashReporter : CrashReporter {
    var userId: String? = null
    val properties = mutableMapOf<String, String>()
    val logMessages = mutableListOf<String>()
    val exceptions = mutableListOf<Pair<Throwable, Map<String, String>>>()
    
    override fun setUserId(id: String?) {
        userId = id
    }
    
    override fun setUserProperty(key: String, value: String) {
        properties[key] = value
    }
    
    override fun log(message: String) {
        logMessages.add(message)
    }
    
    override fun recordException(throwable: Throwable, context: Map<String, String>) {
        exceptions.add(throwable to context)
    }
}

class FakeAnalytics : Analytics {
    val events = mutableListOf<Pair<String, Map<String, Any>>>()
    
    override fun trackEvent(name: String, properties: Map<String, Any>) {
        events.add(name to properties)
    }
}

class FakeFormValidator(
    private val emailResult: ValidationResult = ValidationResult.Valid,
    private val passwordResult: ValidationResult = ValidationResult.Valid
) : FormValidator {
    override fun validateEmail(email: String): ValidationResult = emailResult
    override fun validatePassword(password: String): ValidationResult = passwordResult
}

// Test using fakes
@Test
fun `login tracks analytics event on success`() = runTest {
    val fakeLogger = FakeLogger()
    val fakeAnalytics = FakeAnalytics()
    val fakeValidator = FakeFormValidator()
    val fakeCrashReporter = FakeCrashReporter()
    val fakeAuthRepository = FakeAuthRepository()
    
    val viewModel = AuthViewModel(
        authRepository = fakeAuthRepository,
        savedStateHandle = SavedStateHandle(),
        logger = fakeLogger,
        crashReporter = fakeCrashReporter,
        analytics = fakeAnalytics,
        validator = fakeValidator
    )
    
    viewModel.onLoginClicked("test@example.com", "password123")
    
    advanceUntilIdle()
    
    // Verify analytics was tracked via delegation
    assertThat(fakeAnalytics.events).contains(
        "login_attempt" to mapOf("method" to "email")
    )
    assertThat(fakeAnalytics.events).contains(
        "login_success" to emptyMap<String, Any>()
    )
    
    // Verify logging happened
    assertThat(fakeLogger.messages).contains("Login successful")
}

@Test
fun `login records crash on failure`() = runTest {
    val fakeCrashReporter = FakeCrashReporter()
    val fakeAuthRepository = FakeAuthRepository(shouldFail = true)
    
    val viewModel = AuthViewModel(
        authRepository = fakeAuthRepository,
        savedStateHandle = SavedStateHandle(),
        logger = FakeLogger(),
        crashReporter = fakeCrashReporter,
        analytics = FakeAnalytics(),
        validator = FakeFormValidator()
    )
    
    viewModel.onLoginClicked("test@example.com", "password123")
    
    advanceUntilIdle()
    
    // Verify crash was reported via delegation
    assertThat(fakeCrashReporter.exceptions).hasSize(1)
    assertThat(fakeCrashReporter.exceptions[0].second).containsEntry("screen", "login")
    assertThat(fakeCrashReporter.exceptions[0].second).containsEntry("email_domain", "example.com")
    
    // Verify user context was set
    assertThat(fakeCrashReporter.userId).isEqualTo("test@example.com")
    assertThat(fakeCrashReporter.properties).containsEntry("login_method", "email")
}
```

## Best Practices

### Interface Design
- **Keep interfaces focused**: Prefer 2-5 methods per interface. Split larger interfaces into smaller ones.
- **Delegate interfaces, not concrete classes**: Enables easy swapping and testing.
- **Use sealed types for errors**: Return `ValidationResult` or sealed error types, not nullable strings.

### Implementation
- **No `private` on delegated parameters**: Makes delegation explicit and prevents bypassing.
- **Use `super` in overrides**: When overriding delegated methods, call `super.method()` to use delegate.
- **Prefer DI for delegates**: Inject delegates via Hilt; avoid manual construction.
- **Document delegation intent**: Add comments explaining why delegation is used.

### Testing
- **Create simple fakes**: Test fakes should be straightforward, not mocks.
- **Verify delegated behavior**: Test that delegated methods are called correctly.
- **Test overrides separately**: If you override a delegated method, test the custom behavior.

### Performance
- **Negligible overhead**: Delegation creates minimal wrapper objects with no measurable impact.
- **Don't over-optimize**: Use delegation freely; it's a design tool, not a performance concern.

## Related References

- **Crash Reporting**: For `CrashReporter` interface and implementations, see `references/crashlytics.md`
- **Design Patterns**: See `references/design-patterns.md` for Decorator pattern with delegation
- **ViewModel Patterns**: Use with ViewModel patterns in `references/compose-patterns.md`
- **Architecture**: Fits into our layered architecture in `references/architecture.md`

## Sources

- https://kotlinlang.org/docs/delegation.html
- https://kotlinlang.org/docs/delegated-properties.html
