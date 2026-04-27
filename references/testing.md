# Testing Patterns

Required: hand-written fakes (no mocking libraries) in feature/core modules; Google Truth for assertions; Turbine for `Flow`; Hilt + Robolectric/Compose UI for integration. MockK is permitted only inside the `app` module for Navigation 3 framework types. Layered targets follow [architecture.md](/references/architecture.md) and [modularization.md](/references/modularization.md).

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Doubles](#test-doubles)
3. [ViewModel Tests](#viewmodel-tests)
4. [Repository Tests](#repository-tests)
5. [Coroutine Testing](#coroutine-testing)
6. [Hilt Testing](#hilt-testing)
7. [Room Database Testing](#room-database-testing)
8. [SavedStateHandle Testing](#savedstatehandle-testing)
9. [Navigation Tests](#navigation-tests)
10. [Compose Stability Testing](#testing-compose-stability-annotations)
11. [UI Tests](#ui-tests)
12. [Screenshot Testing](#screenshot-testing)
13. [Performance Benchmarks](#performance-benchmarks)
14. [Test Utilities](#test-utilities)
15. [Rules](#rules)
16. [Paging 3 Testing](#paging-3-testing)
17. [Localization Testing](#localization-testing)

## Testing Philosophy

### No Mocking Libraries

Required:
- **Feature modules**: hand-written fakes implementing the production interface; no mocking libraries.
- **Core modules**: fakes plus Room in-memory databases.
- **App module**: MockK is permitted **only** for Navigation 3 framework types (`NavigationState`, `Navigator`).
- Fakes carry real state and test hooks; never stub-only.
- Use Google Truth for assertions.

### Test Doubles Naming Convention

- **Fake** prefix: Working implementations with test hooks (e.g., `FakeAuthRepository`)
- Used in production test code that runs against realistic implementations
- Contains business logic and state management

### Test Types by Module

| Module          | Test Type         | Location           | Purpose                   |
|-----------------|-------------------|--------------------|---------------------------|
| Feature modules | Unit tests        | `src/test/`        | ViewModel, UI logic       |
| Core/Domain     | Unit tests        | `src/test/`        | Use Cases, business logic |
| Core/Data       | Integration tests | `src/test/`        | Repository, DataSource    |
| Core/UI         | UI tests          | `src/androidTest/` | Shared components         |
| App module      | Navigation tests  | `src/test/`        | Navigator implementations |

## Test Doubles

### Fake Repository Pattern (in `core:testing` module)

```kotlin
// core/testing/src/main/kotlin/com/example/testing/auth/
class FakeAuthRepository : AuthRepository {

    private val authStateFlow = MutableStateFlow<AuthState>(AuthState.Unauthenticated)
    private val authEventsFlow = MutableSharedFlow<AuthEvent>()
    private val users = mutableMapOf<String, User>()
    private val authTokens = mutableMapOf<String, AuthToken>()

    // Test control hooks
    var shouldFailLogin = false
    var shouldFailRegister = false
    var loginDelay = 0.seconds
    var networkError: Exception? = null

    // Test setup methods
    fun sendAuthState(authState: AuthState) {
        authStateFlow.value = authState
    }

    fun addUser(user: User) {
        users[user.id] = user
    }

    fun setAuthToken(email: String, token: AuthToken) {
        authTokens[email] = token
    }
    
    fun sendAuthEvent(event: AuthEvent) {
        authEventsFlow.tryEmit(event)
    }

    // Interface implementation
    override suspend fun login(email: String, password: String): Result<AuthToken> {
        if (loginDelay > 0.seconds) {
            delay(loginDelay)
        }
        
        if (shouldFailLogin) {
            return Result.failure(networkError ?: Exception("Login failed"))
        }
        
        return authTokens[email]?.let { Result.success(it) }
            ?: Result.failure(Exception("Invalid credentials"))
    }

    override suspend fun register(user: User): Result<Unit> {
        if (shouldFailRegister) {
            return Result.failure(networkError ?: Exception("Registration failed"))
        }
        
        users[user.id] = user
        return Result.success(Unit)
    }

    override fun observeAuthState(): Flow<AuthState> = authStateFlow
    
    override fun observeAuthEvents(): Flow<AuthEvent> = authEventsFlow

    override suspend fun resetPassword(email: String): Result<Unit> {
        return Result.success(Unit)
    }
    
    override suspend fun refreshSession(): Result<Unit> {
        return Result.success(Unit)
    }
    
    // Test helpers
    fun reset() {
        shouldFailLogin = false
        shouldFailRegister = false
        loginDelay = 0.seconds
        networkError = null
        users.clear()
        authTokens.clear()
        authStateFlow.value = AuthState.Unauthenticated
    }
}
```

### Fake Navigator Pattern

```kotlin
// core/testing/src/main/kotlin/com/example/testing/navigation/
class FakeAuthNavigator : AuthNavigator {
    
    private val _navigationEvents = mutableListOf<String>()
    val navigationEvents: List<String> get() = _navigationEvents

    // Interface implementation with tracking
    override fun navigateToRegister() {
        _navigationEvents.add("navigateToRegister")
    }

    override fun navigateToForgotPassword() {
        _navigationEvents.add("navigateToForgotPassword")
    }

    override fun navigateBack() {
        _navigationEvents.add("navigateBack")
    }

    override fun navigateToProfile(userId: String) {
        _navigationEvents.add("navigateToProfile:$userId")
    }

    override fun navigateToMainApp() {
        _navigationEvents.add("navigateToMainApp")
    }

    override fun navigateToVerifyEmail(token: String) {
        _navigationEvents.add("navigateToVerifyEmail:$token")
    }

    override fun navigateToResetPassword(token: String) {
        _navigationEvents.add("navigateToResetPassword:$token")
    }

    // Test helpers
    fun clearEvents() {
        _navigationEvents.clear()
    }
    
    fun getLastEvent(): String? = _navigationEvents.lastOrNull()
}
```

### UseCase Setup Pattern

Use real use cases wired to fake dependencies so you exercise production logic:

```kotlin
@Before
fun setup() {
    fakeAuthRepository = FakeAuthRepository()
    loginUseCase = LoginUseCase(fakeAuthRepository)
    registerUseCase = RegisterUseCase(fakeAuthRepository)
}
```

## ViewModel Tests

### AuthViewModel Test with Fakes

```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/AuthViewModelTest.kt
import com.google.common.truth.Truth.assertThat

class AuthViewModelTest {

    @get:Rule
    val dispatcherRule = TestDispatcherRule()

    private lateinit var fakeAuthRepository: FakeAuthRepository
    private lateinit var loginUseCase: LoginUseCase
    private lateinit var registerUseCase: RegisterUseCase
    private lateinit var resetPasswordUseCase: ResetPasswordUseCase
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setup() {
        fakeAuthRepository = FakeAuthRepository()
        loginUseCase = LoginUseCase(fakeAuthRepository)
        registerUseCase = RegisterUseCase(fakeAuthRepository)
        resetPasswordUseCase = ResetPasswordUseCase(fakeAuthRepository)
        
        viewModel = AuthViewModel(
            loginUseCase = loginUseCase,
            registerUseCase = registerUseCase,
            resetPasswordUseCase = resetPasswordUseCase
        )
    }

    @Test
    fun `initial state is LoginForm`() = runTest {
        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.LoginForm::class.java)
    }

    @Test
    fun `when email is changed, ui state updates email`() = runTest {
        // Arrange
        val testEmail = "test@example.com"

        // Act
        viewModel.onAction(AuthAction.EmailChanged(testEmail))

        // Assert
        val state = viewModel.uiState.value as AuthUiState.LoginForm
        assertThat(state.email).isEqualTo(testEmail)
    }

    @Test
    fun `when login clicked with valid credentials, state becomes Loading then Success`() = runTest {
        // Arrange
        val testEmail = "test@example.com"
        val testPassword = "password123"
        fakeAuthRepository.setAuthToken(
            testEmail,
            AuthToken("test-token", User("1", testEmail, "Test User"))
        )
        
        viewModel.onAction(AuthAction.EmailChanged(testEmail))
        viewModel.onAction(AuthAction.PasswordChanged(testPassword))

        // Act
        viewModel.onAction(AuthAction.LoginClicked)

        // Assert - Check loading state
        val loadingState = viewModel.uiState.value as AuthUiState.LoginForm
        assertThat(loadingState.isLoading).isTrue()

        // Wait for async operation
        advanceUntilIdle()

        // Assert - Check success state
        val successState = viewModel.uiState.value
        assertThat(successState).isInstanceOf(AuthUiState.Success::class.java)
    }

    @Test
    fun `when login fails, state becomes Error`() = runTest {
        // Arrange
        fakeAuthRepository.shouldFailLogin = true
        
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("wrong"))

        // Act
        viewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.Error::class.java)
    }

    @Test
    fun `when RegisterClicked, state becomes RegisterForm`() = runTest {
        // Act
        viewModel.onAction(AuthAction.RegisterClicked)

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.RegisterForm::class.java)
    }

    @Test
    fun `when ForgotPasswordClicked, state becomes ForgotPasswordForm`() = runTest {
        // Act
        viewModel.onAction(AuthAction.ForgotPasswordClicked)

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.ForgotPasswordForm::class.java)
    }

    @Test
    fun `when Retry action called after error, state returns to LoginForm`() = runTest {
        // Arrange - cause an error
        fakeAuthRepository.shouldFailLogin = true
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("wrong"))
        viewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()

        // Verify error state
        assertThat(viewModel.uiState.value).isInstanceOf(AuthUiState.Error::class.java)

        // Act
        viewModel.onAction(AuthAction.Retry)

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.LoginForm::class.java)
    }

    @Test
    fun `when ClearError action called, error is cleared and form is reset`() = runTest {
        // Arrange - cause an error
        fakeAuthRepository.shouldFailLogin = true
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("wrong"))
        viewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()

        // Act
        viewModel.onAction(AuthAction.ClearError)

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(AuthUiState.LoginForm::class.java)
        val loginForm = state as AuthUiState.LoginForm
        assertThat(loginForm.email).isEmpty()
        assertThat(loginForm.password).isEmpty()
        assertThat(loginForm.emailError).isNull()
        assertThat(loginForm.passwordError).isNull()
    }

    @Test
    fun `when login form has validation errors, error messages are set`() = runTest {
        // Arrange
        viewModel.onAction(AuthAction.EmailChanged("invalid-email"))
        viewModel.onAction(AuthAction.PasswordChanged(""))

        // Act
        viewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value as AuthUiState.LoginForm
        assertThat(state.emailError).isNotNull()
        assertThat(state.passwordError).isNotNull()
    }
}
```

### Test Dispatcher Rule (in `core:testing`)

See [Coroutine Testing → Test Dispatcher Rule](#test-dispatcher-rule-in-coretesting-1) for the full implementation.

### Testing StateFlow with Turbine and Truth

Required: Turbine for multi-emission `Flow` assertions; `advanceUntilIdle()` for simple async completion.

**When to use Turbine:**
- Testing multiple emissions from a Flow
- Verifying emission order and values
- Testing Flow transformations

**When to use `advanceUntilIdle()`:**
- Testing final StateFlow value after operation
- Simple async operations with one result
- No need to inspect intermediate states

```kotlin
import com.google.common.truth.Truth.assertThat
import app.cash.turbine.test

@Test
fun `uiState emits correct states during login flow`() = runTest {
    // Arrange
    fakeAuthRepository.setAuthToken(
        "test@example.com",
        AuthToken("test-token", User("1", "test@example.com", "Test User"))
    )
    
    viewModel.uiState.test {
        // Initial state
        assertThat(awaitItem()).isInstanceOf(AuthUiState.LoginForm::class.java)

        // Trigger login
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("password123"))
        viewModel.onAction(AuthAction.LoginClicked)

        // Should emit Loading state
        val loadingState = awaitItem()
        assertThat(loadingState).isInstanceOf(AuthUiState.LoginForm::class.java)
        assertThat((loadingState as AuthUiState.LoginForm).isLoading).isTrue()

        // Should emit Success state
        val successState = awaitItem()
        assertThat(successState).isInstanceOf(AuthUiState.Success::class.java)
        assertThat((successState as AuthUiState.Success).user.email).isEqualTo("test@example.com")

        cancelAndIgnoreRemainingEvents()
    }
}

@Test
fun `uiState emits Loading, Error when login fails`() = runTest {
    // Arrange
    fakeAuthRepository.shouldFailLogin = true
    
    viewModel.uiState.test {
        // Skip initial state
        skipItems(1)
        
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("wrong"))
        viewModel.onAction(AuthAction.LoginClicked)

        // Should emit Loading state
        val loadingState = awaitItem() as AuthUiState.LoginForm
        assertThat(loadingState.isLoading).isTrue()

        // Should emit Error state
        val errorState = awaitItem()
        assertThat(errorState).isInstanceOf(AuthUiState.Error::class.java)
        assertThat((errorState as AuthUiState.Error).message).isNotEmpty()
        assertThat(errorState.canRetry).isTrue()

        cancelAndIgnoreRemainingEvents()
    }
}
```

## Repository Tests

### Testing AuthRepository Implementation with Truth

```kotlin
// core/data/src/test/kotlin/com/example/data/auth/AuthRepositoryImplTest.kt
import com.google.common.truth.Truth.assertThat

class AuthRepositoryImplTest {

    private lateinit var fakeLocalDataSource: FakeAuthLocalDataSource
    private lateinit var fakeRemoteDataSource: FakeAuthRemoteDataSource
    private lateinit var authMapper: AuthMapper
    private lateinit var repository: AuthRepositoryImpl

    @Before
    fun setup() {
        fakeLocalDataSource = FakeAuthLocalDataSource()
        fakeRemoteDataSource = FakeAuthRemoteDataSource()
        authMapper = AuthMapper()
        
        repository = AuthRepositoryImpl(
            localDataSource = fakeLocalDataSource,
            remoteDataSource = fakeRemoteDataSource,
            authMapper = authMapper
        )
    }

    @Test
    fun `login success saves token and user to local storage`() = runTest {
        // Arrange
        val testEmail = "test@example.com"
        val testPassword = "password123"
        val expectedToken = AuthTokenResponse("test-token", NetworkUser("1", testEmail, "Test User"))
        fakeRemoteDataSource.setLoginResponse(expectedToken)

        // Act
        val result = repository.login(testEmail, testPassword)

        // Assert
        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()?.value).isEqualTo(expectedToken.token)
        
        // Verify local storage was updated
        val savedToken = fakeLocalDataSource.getAuthToken()
        assertThat(savedToken).isEqualTo(expectedToken.token)
        
        val savedUser = fakeLocalDataSource.getUser()
        assertThat(savedUser?.email).isEqualTo(expectedToken.user.email)
    }

    @Test
    fun `login failure returns error result`() = runTest {
        // Arrange
        val testEmail = "test@example.com"
        val testPassword = "wrong-password"
        fakeRemoteDataSource.shouldFailLogin = true

        // Act
        val result = repository.login(testEmail, testPassword)

        // Assert
        assertThat(result.isFailure).isTrue()
        assertThat(result.exceptionOrNull()?.message).contains("Invalid")
    }

    @Test
    fun `observeAuthState emits Authenticated when token exists`() = runTest {
        // Arrange
        fakeLocalDataSource.setAuthToken("test-token")
        fakeLocalDataSource.setUser(UserEntity("1", "test@example.com", "Test User"))

        // Act & Assert
        repository.observeAuthState().test {
            val authState = awaitItem()
            assertThat(authState).isInstanceOf(AuthState.Authenticated::class.java)
            assertThat((authState as AuthState.Authenticated).user.id).isEqualTo("1")
            assertThat(authState.user.email).isEqualTo("test@example.com")
            
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `observeAuthState emits Unauthenticated when no token exists`() = runTest {
        // Act & Assert
        repository.observeAuthState().test {
            val authState = awaitItem()
            assertThat(authState).isInstanceOf(AuthState.Unauthenticated::class.java)
            
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `observeAuthState emits Error when local data source fails`() = runTest {
        // Arrange
        fakeLocalDataSource.shouldFail = true

        // Act & Assert
        repository.observeAuthState().test {
            val authState = awaitItem()
            assertThat(authState).isInstanceOf(AuthState.Error::class.java)
            assertThat((authState as AuthState.Error).message).isNotEmpty()
            
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `register success saves user to local storage`() = runTest {
        // Arrange
        val testUser = User("1", "test@example.com", "Test User")
        fakeRemoteDataSource.setRegisterResponse(Unit)

        // Act
        val result = repository.register(testUser)

        // Assert
        assertThat(result.isSuccess).isTrue()
        val savedUser = fakeLocalDataSource.getUser()
        assertThat(savedUser?.email).isEqualTo(testUser.email)
        assertThat(savedUser?.name).isEqualTo(testUser.name)
    }
}
```

## Coroutine Testing

### Test Dispatcher Rule (in `core:testing`)

Use a custom JUnit rule to set `Dispatchers.Main` to a test dispatcher for all coroutine tests.

```kotlin
// core/testing/src/main/kotlin/com/example/testing/rule/TestDispatcherRule.kt
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.TestDispatcher
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.rules.TestWatcher
import org.junit.runner.Description

class TestDispatcherRule(
    private val testDispatcher: TestDispatcher = StandardTestDispatcher(),
) : TestWatcher() {

    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

### Testing with `runTest` and Shared Scheduler

Use `runTest` for coroutine tests. Share the same scheduler across test dispatchers for predictable timing.

```kotlin
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import com.google.common.truth.Truth.assertThat

class AuthRepositoryTest {

    @get:Rule
    val dispatcherRule = TestDispatcherRule()

    @Test
    fun `login updates auth state`() = runTest {
        // Arrange
        val testDispatcher = UnconfinedTestDispatcher(testScheduler)
        val repository = AuthRepository(
            remote = FakeAuthRemoteDataSource(),
            ioDispatcher = testDispatcher
        )

        // Act
        repository.login("user@example.com", "password")

        // Assert
        assertThat(repository.isLoggedIn()).isTrue()
    }
}
```

### Using `advanceUntilIdle()` for Async Operations

Use `advanceUntilIdle()` to wait for all pending coroutines to complete in tests.

```kotlin
@Test
fun `login triggers loading then success state`() = runTest {
    // Arrange
    val viewModel = AuthViewModel(loginUseCase, savedStateHandle)
    
    // Act
    viewModel.onAction(AuthAction.LoginClicked)
    
    // Assert loading state
    val loadingState = viewModel.uiState.value
    assertThat((loadingState as AuthUiState.LoginForm).isLoading).isTrue()
    
    // Wait for async work to complete
    advanceUntilIdle()
    
    // Assert final state
    val finalState = viewModel.uiState.value
    assertThat(finalState).isInstanceOf(AuthUiState.Success::class.java)
}
```

### Testing Delays and Timeouts with `advanceTimeBy()`

Use `advanceTimeBy()` to test time-dependent coroutine logic without actually waiting.

```kotlin
@Test
fun `session refresh happens after 30 minutes`() = runTest {
    // Arrange
    val fakeAuthStore = FakeAuthStore()
    val sessionRefresher = AuthSessionRefresher(
        authStore = fakeAuthStore,
        externalScope = this,
        ioDispatcher = UnconfinedTestDispatcher(testScheduler)
    )
    
    // Act
    sessionRefresher.startPeriodicRefresh()
    
    // Fast-forward 30 minutes
    advanceTimeBy(30.minutes)
    
    // Assert
    assertThat(fakeAuthStore.refreshCallCount).isEqualTo(1)
    
    // Fast-forward another 30 minutes
    advanceTimeBy(30.minutes)
    
    // Assert second refresh
    assertThat(fakeAuthStore.refreshCallCount).isEqualTo(2)
}
```

### Testing Timeout Behavior

Test `withTimeout` and `withTimeoutOrNull` behavior using virtual time.

```kotlin
@Test
fun `biometric authentication times out after 30 seconds`() = runTest {
    // Arrange
    val slowBiometricSdk = FakeBiometricSdk(responseDelay = 40.seconds)
    val repository = BiometricAuthRepository(
        biometricSdk = slowBiometricSdk,
        ioDispatcher = UnconfinedTestDispatcher(testScheduler)
    )
    
    // Act
    val result = repository.authenticate()
    
    // Fast-forward past the timeout
    advanceTimeBy(35.seconds)
    
    // Assert - should return null due to timeout
    assertThat(result).isNull()
}

@Test
fun `printer returns timeout result when operation hangs`() = runTest {
    // Arrange
    val hangingPrinterSdk = FakePrinterSdk(hangOnPrint = true)
    val repository = HardwarePrinterRepository(
        printerSdk = hangingPrinterSdk,
        ioDispatcher = UnconfinedTestDispatcher(testScheduler)
    )
    
    // Act
    val resultDeferred = async { repository.print(testDocument) }
    
    // Fast-forward past the 60s timeout
    advanceTimeBy(65.seconds)
    val result = resultDeferred.await()
    
    // Assert
    assertThat(result).isEqualTo(PrintResult.Timeout)
}
```

### Checking Virtual Time with `currentTime`

Use `currentTime` to verify time progression in tests.

```kotlin
@Test
fun `exponential backoff delays increase correctly`() = runTest {
    // Arrange
    val retryManager = AuthRetryManager()
    val startTime = currentTime
    
    // Act & Assert
    retryManager.retryWithBackoff(attempt = 1)
    assertThat(currentTime - startTime).isEqualTo(1000L) // 1 second
    
    retryManager.retryWithBackoff(attempt = 2)
    assertThat(currentTime - startTime).isEqualTo(3000L) // +2 seconds
    
    retryManager.retryWithBackoff(attempt = 3)
    assertThat(currentTime - startTime).isEqualTo(7000L) // +4 seconds
}
```

### Testing Flow Emissions with Turbine

Use Turbine library for testing Flow emissions over time.

```kotlin
import app.cash.turbine.test
import com.google.common.truth.Truth.assertThat

@Test
fun `auth state flow emits correct states`() = runTest {
    // Arrange
    val fakeDataSource = FakeAuthDataSource()
    val repository = AuthRepository(fakeDataSource, UnconfinedTestDispatcher(testScheduler))
    
    // Act & Assert
    repository.observeAuthState().test {
        // Initial state
        assertThat(awaitItem()).isInstanceOf(AuthState.Unauthenticated::class.java)
        
        // Trigger login
        repository.login("user@example.com", "password")
        advanceUntilIdle()
        
        // Should emit Authenticated
        val authState = awaitItem()
        assertThat(authState).isInstanceOf(AuthState.Authenticated::class.java)
        assertThat((authState as AuthState.Authenticated).user.email).isEqualTo("user@example.com")
        
        cancelAndIgnoreRemainingEvents()
    }
}

@Test
fun `session refresh flow emits at correct intervals`() = runTest {
    // Arrange
    val fakeStore = FakeAuthStore()
    val refresher = AuthSessionRefresher(fakeStore, this, UnconfinedTestDispatcher(testScheduler))
    
    // Act & Assert
    fakeStore.sessionUpdates.test {
        refresher.startPeriodicRefresh()
        
        // First refresh happens immediately
        assertThat(awaitItem()).isNotNull()
        
        // Advance 30 minutes
        advanceTimeBy(30.minutes)
        assertThat(awaitItem()).isNotNull()
        
        // Advance another 30 minutes
        advanceTimeBy(30.minutes)
        assertThat(awaitItem()).isNotNull()
        
        cancelAndIgnoreRemainingEvents()
    }
}

@Test
fun `channel events are received correctly`() = runTest {
    // Arrange
    val viewModel = AuthViewModel(loginUseCase, savedStateHandle)
    
    // Act & Assert
    viewModel.navigationEvents.test {
        viewModel.login()
        advanceUntilIdle()
        
        assertThat(awaitItem()).isEqualTo(AuthNavigationEvent.LoginSuccess)
        
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Testing Cancellation

Test that coroutines respond to cancellation correctly.

```kotlin
@Test
fun `auth log upload stops on cancellation`() = runTest {
    // Arrange
    val fakeUploader = FakeLogUploader()
    val uploader = AuthLogUploader(fakeUploader)
    val job = launch {
        uploader.upload(listOf(file1, file2, file3, file4, file5))
    }
    
    // Act - cancel after some uploads
    advanceTimeBy(100L)
    job.cancel()
    advanceUntilIdle()
    
    // Assert - not all files were uploaded
    assertThat(fakeUploader.uploadedFiles.size).isLessThan(5)
}

@Test
fun `camera cleanup happens even when cancelled`() = runTest {
    // Arrange
    val fakeCamera = FakeCamera()
    val repository = CameraRepository(fakeCamera, UnconfinedTestDispatcher(testScheduler))
    
    // Act - start capture then cancel
    val job = launch {
        try {
            repository.capturePhoto()
        } catch (e: CancellationException) {
            // Expected
        }
    }
    
    advanceTimeBy(50L)
    job.cancel()
    advanceUntilIdle()
    
    // Assert - camera was closed despite cancellation (NonCancellable cleanup)
    assertThat(fakeCamera.isClosed).isTrue()
}
```

### Coroutine test rules

Required:
- Wrap every coroutine test in `runTest { }`.
- Share the scheduler: `UnconfinedTestDispatcher(testScheduler)` or `StandardTestDispatcher(testScheduler)`.
- Inject dispatchers in production code; never hardcode `Dispatchers.IO` / `Dispatchers.Default`.
- `advanceUntilIdle()` before assertions; `advanceTimeBy(...)` for delay/timeout coverage.
- Cover cancellation paths and cleanup of resources held inside `NonCancellable`/`finally` blocks.

### Dispatcher Choices in Tests

| Dispatcher                  | Use when                                                      |
|-----------------------------|---------------------------------------------------------------|
| `UnconfinedTestDispatcher`  | Default - eager execution, synchronous-style assertions.      |
| `StandardTestDispatcher`    | Need explicit ordering or virtual-time stepping.              |

```kotlin
val unconfinedDispatcher = UnconfinedTestDispatcher(testScheduler)
val standardDispatcher = StandardTestDispatcher(testScheduler)
```

## Hilt Testing

### Testing Hilt-Injected ViewModels

```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/AuthViewModelHiltTest.kt
import dagger.hilt.android.testing.HiltAndroidTest
import dagger.hilt.android.testing.HiltAndroidRule
import dagger.hilt.android.testing.HiltTestApplication
import dagger.hilt.android.testing.BindValue
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@HiltAndroidTest
@RunWith(RobolectricTestRunner::class)
@Config(application = HiltTestApplication::class)
class AuthViewModelHiltTest {

    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)
    
    @get:Rule(order = 1)
    val dispatcherRule = TestDispatcherRule()

    // Replace real implementation with fake for testing
    @BindValue
    @JvmField
    val authRepository: AuthRepository = FakeAuthRepository()

    @Inject
    lateinit var viewModel: AuthViewModel

    @Before
    fun setup() {
        hiltRule.inject()
    }

    @Test
    fun `ViewModel receives injected fake repository`() = runTest {
        // The ViewModel is injected with FakeAuthRepository via @BindValue
        viewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()
        
        // Verify fake was used
        assertThat((authRepository as FakeAuthRepository).shouldFailLogin).isFalse()
    }
}
```

### Custom Test Module

```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/di/TestAuthModule.kt
@Module
@TestInstallIn(
    components = [SingletonComponent::class],
    replaces = [AuthModule::class] // Replace production module
)
object TestAuthModule {

    @Provides
    @Singleton
    fun provideAuthRepository(): AuthRepository = FakeAuthRepository()
    
    @Provides
    @Singleton
    fun provideAuthApi(): AuthApi = FakeAuthApi()
}
```

### Testing Without Hilt

For unit tests that don't need DI, construct dependencies manually:

```kotlin
@Test
fun `ViewModel without Hilt injection`() = runTest {
    // Arrange - manual construction
    val fakeRepo = FakeAuthRepository()
    val viewModel = AuthViewModel(
        loginUseCase = LoginUseCase(fakeRepo),
        registerUseCase = RegisterUseCase(fakeRepo),
        resetPasswordUseCase = ResetPasswordUseCase(fakeRepo)
    )
    
    // Test normally
    viewModel.onAction(AuthAction.LoginClicked)
    advanceUntilIdle()
    
    assertThat(viewModel.uiState.value).isInstanceOf(AuthUiState.Error::class.java)
}
```

## Room Database Testing

Room 3 requires a [`SQLiteDriver`](https://developer.android.com/kotlin/multiplatform/sqlite#sqlite-driver) on the database builder (the `app.android.room` convention adds `sqlite-bundled`). Use [`BundledSQLiteDriver`](https://developer.android.com/reference/kotlin/androidx/sqlite/driver/bundled/BundledSQLiteDriver) in tests the same way as in production code.

For **migration** instrumentation tests, add **`androidTestImplementation(libs.room3.testing)`** and ensure exported schemas are available to the test APK (the Room Gradle plugin can copy schemas into `androidTest` assets; see [Test migrations](https://developer.android.com/training/data-storage/room/migrating-db-versions#test) and [`MigrationTestHelper`](https://developer.android.com/reference/kotlin/androidx/room3/testing/MigrationTestHelper)).

### In-Memory Database for Tests

```kotlin
// core/database/src/androidTest/kotlin/com/example/database/AuthDaoTest.kt
import android.content.Context
import androidx.room3.Room
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.test.core.app.ApplicationProvider
import com.google.common.truth.Truth.assertThat
import org.junit.After
import org.junit.Before

class AuthDaoTest {

    private lateinit var database: AppDatabase
    private lateinit var authDao: AuthDao

    @Before
    fun createDb() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        database = Room.inMemoryDatabaseBuilder<AppDatabase>(context)
            .setDriver(BundledSQLiteDriver())
            .build()
        authDao = database.authDao()
    }

    @After
    fun closeDb() {
        database.close()
    }

    @Test
    fun insertAndRetrieveAuthToken() = runTest {
        // Arrange
        val authToken = AuthTokenEntity(
            token = "test-token",
            userId = "user-123",
            expiresAt = Clock.System.now().plus(1.hours).toEpochMilliseconds()
        )

        // Act
        authDao.insertAuthToken(authToken)
        val retrieved = authDao.getAuthToken()

        // Assert
        assertThat(retrieved).isNotNull()
        assertThat(retrieved?.token).isEqualTo("test-token")
        assertThat(retrieved?.userId).isEqualTo("user-123")
    }

    @Test
    fun observeAuthToken_emitsUpdates() = runTest {
        // Arrange
        val token1 = AuthTokenEntity("token-1", "user-1", 0)
        val token2 = AuthTokenEntity("token-2", "user-2", 0)

        // Act & Assert
        authDao.observeAuthToken().test {
            // Initial state - null
            assertThat(awaitItem()).isNull()

            // Insert first token
            authDao.insertAuthToken(token1)
            assertThat(awaitItem()?.token).isEqualTo("token-1")

            // Update with second token
            authDao.insertAuthToken(token2)
            assertThat(awaitItem()?.token).isEqualTo("token-2")

            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun deleteAuthToken_removesData() = runTest {
        // Arrange
        val authToken = AuthTokenEntity("token", "user", 0)
        authDao.insertAuthToken(authToken)

        // Act
        authDao.deleteAuthToken()

        // Assert
        val retrieved = authDao.getAuthToken()
        assertThat(retrieved).isNull()
    }

    @Test
    fun getUserById_returnsCorrectUser() = runTest {
        // Arrange
        val user1 = UserEntity("1", "user1@example.com", "User One")
        val user2 = UserEntity("2", "user2@example.com", "User Two")
        authDao.insertUser(user1)
        authDao.insertUser(user2)

        // Act
        val retrieved = authDao.getUserById("2")

        // Assert
        assertThat(retrieved).isNotNull()
        assertThat(retrieved?.id).isEqualTo("2")
        assertThat(retrieved?.email).isEqualTo("user2@example.com")
    }
}
```

### Testing Database Migrations

`MigrationTestHelper` APIs are **suspend** and return [`SQLiteConnection`](https://developer.android.com/reference/kotlin/androidx/sqlite/SQLiteConnection) (not `SupportSQLiteDatabase`). Use **`runBlocking`** (or another coroutine test harness) from instrumentation tests. Validate rows with **`prepare` / `step` / `getText`** (see [`SQLiteStatement`](https://developer.android.com/reference/kotlin/androidx/sqlite/SQLiteStatement)).

```kotlin
// core/database/src/androidTest/kotlin/com/example/database/MigrationTest.kt
import androidx.room3.testing.MigrationTestHelper
import androidx.sqlite.driver.bundled.BundledSQLiteDriver
import androidx.sqlite.execSQL
import androidx.test.platform.app.InstrumentationRegistry
import com.google.common.truth.Truth.assertThat
import kotlinx.coroutines.runBlocking
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class MigrationTest {

    private val instrumentation = InstrumentationRegistry.getInstrumentation()

    @get:Rule
    val helper = MigrationTestHelper(
        instrumentation = instrumentation,
        file = instrumentation.targetContext.getDatabasePath(TEST_DB),
        driver = BundledSQLiteDriver(),
        databaseClass = AppDatabase::class,
    )

    @Before
    fun deleteDb() {
        instrumentation.targetContext.deleteDatabase(TEST_DB)
    }

    @Test
    fun migrate1To2_containsCorrectData() = runBlocking {
        helper.createDatabase(1).apply {
            execSQL("INSERT INTO users VALUES ('1', 'test@example.com', 'Test User')")
            close()
        }

        val migrated = helper.runMigrationsAndValidate(2, listOf(MIGRATION_1_2))
        migrated.prepare("SELECT email FROM users WHERE id = '1'").use { stmt ->
            assertThat(stmt.step()).isTrue()
            assertThat(stmt.getText(0)).isEqualTo("test@example.com")
        }
        migrated.close()
    }

    companion object {
        private const val TEST_DB = "migration-test"
    }
}
```

## SavedStateHandle Testing

### Testing Navigation Arguments

```kotlin
// feature-profile/src/test/kotlin/com/example/feature/profile/ProfileViewModelTest.kt
import androidx.lifecycle.SavedStateHandle
import com.google.common.truth.Truth.assertThat

class ProfileViewModelTest {

    @get:Rule
    val dispatcherRule = TestDispatcherRule()

    private lateinit var fakeUserRepository: FakeUserRepository
    private lateinit var savedStateHandle: SavedStateHandle
    private lateinit var viewModel: ProfileViewModel

    @Test
    fun `ViewModel loads user from navigation argument`() = runTest {
        // Arrange
        val userId = "user-123"
        savedStateHandle = SavedStateHandle(mapOf("userId" to userId))
        
        val expectedUser = User(userId, "test@example.com", "Test User")
        fakeUserRepository = FakeUserRepository().apply {
            addUser(expectedUser)
        }
        
        viewModel = ProfileViewModel(
            userRepository = fakeUserRepository,
            savedStateHandle = savedStateHandle
        )

        // Act
        advanceUntilIdle()

        // Assert
        val state = viewModel.uiState.value
        assertThat(state).isInstanceOf(ProfileUiState.Success::class.java)
        assertThat((state as ProfileUiState.Success).user.id).isEqualTo(userId)
    }

    @Test
    fun `ViewModel handles missing navigation argument`() = runTest {
        // Arrange - no userId in SavedStateHandle
        savedStateHandle = SavedStateHandle()
        fakeUserRepository = FakeUserRepository()
        
        // Act & Assert
        val exception = assertThrows<IllegalStateException> {
            ProfileViewModel(
                userRepository = fakeUserRepository,
                savedStateHandle = savedStateHandle
            )
        }
        
        assertThat(exception.message).contains("userId")
    }

    @Test
    fun `SavedStateHandle survives process death simulation`() = runTest {
        // Arrange
        val userId = "user-123"
        savedStateHandle = SavedStateHandle(mapOf("userId" to userId))
        fakeUserRepository = FakeUserRepository()
        
        val viewModel = ProfileViewModel(fakeUserRepository, savedStateHandle)
        
        // Simulate state saving
        val savedState = savedStateHandle.keys().associateWith { savedStateHandle.get<Any?>(it) }
        
        // Simulate process death and restoration
        val restoredHandle = SavedStateHandle(savedState)
        val restoredViewModel = ProfileViewModel(fakeUserRepository, restoredHandle)
        
        // Assert - restored ViewModel has same userId
        assertThat(restoredHandle.get<String>("userId")).isEqualTo(userId)
    }
}
```

### Testing State Persistence

```kotlin
@Test
fun `form state is saved to SavedStateHandle`() = runTest {
    // Arrange
    savedStateHandle = SavedStateHandle()
    viewModel = AuthViewModel(
        loginUseCase = loginUseCase,
        savedStateHandle = savedStateHandle
    )
    
    val testEmail = "test@example.com"
    val testPassword = "password123"
    
    // Act
    viewModel.onAction(AuthAction.EmailChanged(testEmail))
    viewModel.onAction(AuthAction.PasswordChanged(testPassword))
    
    // Assert - state is saved
    assertThat(savedStateHandle.get<String>("email")).isEqualTo(testEmail)
    assertThat(savedStateHandle.get<String>("password")).isEqualTo(testPassword)
}
```

## Navigation Tests

### Testing Navigator Implementations in App Module

Navigation3 uses `NavigationState` and `Navigator` instead of `NavController`. Test navigator interfaces
with fake implementations.

```kotlin
// app/src/test/kotlin/com/example/navigation/AppNavigatorsTest.kt
import com.google.common.truth.Truth.assertThat

class AppNavigatorsTest {

    private lateinit var fakeAuthNavigator: FakeAuthNavigator
    
    @Before
    fun setup() {
        fakeAuthNavigator = FakeAuthNavigator()
    }

    @Test
    fun `FakeAuthNavigator tracks all navigation events`() {
        // Act
        fakeAuthNavigator.navigateToMainApp()
        fakeAuthNavigator.navigateToRegister()
        fakeAuthNavigator.navigateToProfile("user123")
        fakeAuthNavigator.navigateBack()

        // Assert
        assertThat(fakeAuthNavigator.navigationEvents).hasSize(4)
        assertThat(fakeAuthNavigator.navigationEvents[0]).isEqualTo("navigateToMainApp")
        assertThat(fakeAuthNavigator.navigationEvents[1]).isEqualTo("navigateToRegister")
        assertThat(fakeAuthNavigator.navigationEvents[2]).isEqualTo("navigateToProfile:user123")
        assertThat(fakeAuthNavigator.navigationEvents[3]).isEqualTo("navigateBack")
    }

    @Test
    fun `FakeAuthNavigator clearEvents works correctly`() {
        // Arrange
        fakeAuthNavigator.navigateToMainApp()
        fakeAuthNavigator.navigateToRegister()
        
        // Pre-condition
        assertThat(fakeAuthNavigator.navigationEvents).isNotEmpty()

        // Act
        fakeAuthNavigator.clearEvents()

        // Assert
        assertThat(fakeAuthNavigator.navigationEvents).isEmpty()
    }
    
    @Test
    fun `FakeAuthNavigator getLastEvent returns most recent navigation`() {
        // Act
        fakeAuthNavigator.navigateToRegister()
        fakeAuthNavigator.navigateToProfile("user123")
        
        // Assert
        assertThat(fakeAuthNavigator.getLastEvent()).isEqualTo("navigateToProfile:user123")
    }
}
```

### Testing Navigation3 State

```kotlin
// app/src/test/kotlin/com/example/navigation/NavigationStateTest.kt
import androidx.navigation3.runtime.NavKey
import com.google.common.truth.Truth.assertThat
import kotlinx.serialization.Serializable

@Serializable
sealed interface TestRoute : NavKey {
    @Serializable data object Home : TestRoute
    @Serializable data object Profile : TestRoute
    @Serializable data object Settings : TestRoute
    @Serializable data class Detail(val id: String) : TestRoute
}

class NavigationStateTest {

    @Test
    fun `Navigator switches between top-level routes`() {
        // Arrange
        val topLevelRoutes = setOf<NavKey>(TestRoute.Home, TestRoute.Profile, TestRoute.Settings)
        val state = NavigationState(
            startRoute = TestRoute.Home,
            topLevelRoute = mutableStateOf(TestRoute.Home),
            backStacks = topLevelRoutes.associateWith { FakeNavBackStack<NavKey>(it) }
        )
        val navigator = Navigator(state)

        // Act
        navigator.navigate(TestRoute.Profile)

        // Assert
        assertThat(state.topLevelRoute).isEqualTo(TestRoute.Profile)
    }

    @Test
    fun `Navigator adds child routes to current stack`() {
        // Arrange
        val topLevelRoutes = setOf<NavKey>(TestRoute.Home)
        val homeStack = FakeNavBackStack<NavKey>(TestRoute.Home)
        val state = NavigationState(
            startRoute = TestRoute.Home,
            topLevelRoute = mutableStateOf(TestRoute.Home),
            backStacks = mapOf(TestRoute.Home to homeStack)
        )
        val navigator = Navigator(state)

        // Act
        navigator.navigate(TestRoute.Detail("123"))

        // Assert
        assertThat(homeStack.entries).contains(TestRoute.Detail("123"))
    }

    @Test
    fun `Navigator goBack pops current stack`() {
        // Arrange
        val topLevelRoutes = setOf<NavKey>(TestRoute.Home)
        val homeStack = FakeNavBackStack<NavKey>(TestRoute.Home).apply {
            add(TestRoute.Detail("123"))
        }
        val state = NavigationState(
            startRoute = TestRoute.Home,
            topLevelRoute = mutableStateOf(TestRoute.Home),
            backStacks = mapOf(TestRoute.Home to homeStack)
        )
        val navigator = Navigator(state)

        // Act
        navigator.goBack()

        // Assert
        assertThat(homeStack.entries).doesNotContain(TestRoute.Detail("123"))
        assertThat(homeStack.last()).isEqualTo(TestRoute.Home)
    }
}

// Fake NavBackStack for testing
class FakeNavBackStack<T : NavKey>(startRoute: T) {
    val entries = mutableListOf<T>(startRoute)
    
    fun add(route: T) {
        entries.add(route)
    }
    
    fun removeLastOrNull(): T? = entries.removeLastOrNull()
    
    fun last(): T = entries.last()
}
```

### Testing Compose Stability Annotations

Required: assert `@Immutable` / `@Stable` on UI-owned models in unit tests before relying on Compose compiler stability output:

```kotlin
// core/domain/src/test/kotlin/com/example/domain/model/StabilityTest.kt
import androidx.compose.runtime.Stable
import androidx.compose.runtime.Immutable
import com.google.common.truth.Truth.assertThat
import kotlin.reflect.full.findAnnotation

class StabilityTest {

    @Test
    fun `User model is annotated with @Immutable`() {
        // Assert
        val annotation = User::class.findAnnotation<Immutable>()
        assertThat(annotation).isNotNull()
    }

    @Test
    fun `AuthRepository interface is annotated with @Stable`() {
        // Assert
        val annotation = AuthRepository::class.findAnnotation<Stable>()
        assertThat(annotation).isNotNull()
    }

    @Test
    fun `User model has only val properties`() {
        // Get all properties
        val properties = User::class.members.filterIsInstance<KProperty<*>>()
        
        // Assert all are val (immutable)
        properties.forEach { property ->
            assertThat(property is KMutableProperty<*>).isFalse()
        }
    }
    
    @Test
    fun `UiState sealed interface types are @Immutable`() {
        // Check all sealed subclasses
        val subclasses = AuthUiState::class.sealedSubclasses
        
        subclasses.forEach { subclass ->
            val annotation = subclass.findAnnotation<Immutable>()
            assertThat(annotation).isNotNull()
        }
    }
}
```

Required after changing `@Immutable` / `@Stable` on UI-facing models: run Compose Compiler reports via the `composeStabilityAnalyzer` Gradle plugin ([gradle-setup.md](gradle-setup.md) → "Compose Stability Analyzer").

### Testing Deep Links

Required: wait at least 20 seconds after `adb install` before the first `pm get-app-links` read - the verifier runs asynchronously.

#### Launch deep links (`am start`)

```bash
adb shell am start -W -a android.intent.action.VIEW \
    -d "https://example.com/products/abc123" \
    com.example.app

adb shell am start -W -a android.intent.action.VIEW \
    -d "myapp://open/profile/user42" \
    com.example.app

adb shell am start -W -a android.intent.action.VIEW \
    -d "https://example.com/search?query=shoes&category=footwear" \
    com.example.app

adb shell am start -W -a android.intent.action.VIEW \
    --activity-new-task \
    -d "https://example.com/products/abc123" \
    com.example.app
```

#### Custom-scheme launch (`am start`)

Required: when validating custom-scheme routing, run the `adb shell am start` line that uses `-d "myapp://open/profile/user42"` from Launch deep links (`am start`).

Forbidden: treating a successful custom-scheme launch as proof of HTTPS App Links verification - `pm get-app-links` never inspects custom schemes; the disambiguation dialog and default-handler state apply only to `http`/`https` filters with `autoVerify`.

Forbidden: security-critical flows (auth callback, payment return) on custom schemes in production - any package can register the same scheme (see [android-navigation.md → Custom-Scheme Deep Linking](android-navigation.md#custom-scheme-deep-linking)).

#### App Links verification (`pm` + `dumpsys`)

```bash
adb shell pm set-app-links --package com.example.app 0 all

adb shell pm verify-app-links --re-verify com.example.app

adb shell pm get-app-links com.example.app

adb shell pm get-app-links --user cur com.example.app

adb shell dumpsys package d
```

| Command                                  | Use when                                                                       |
|------------------------------------------|--------------------------------------------------------------------------------|
| `pm set-app-links --package <pkg> 0 all` | Reset every domain to unselected before a clean re-verify.                     |
| `pm verify-app-links --re-verify <pkg>`  | Force the verifier to re-fetch `assetlinks.json` after server changes.         |
| `pm get-app-links <pkg>`                 | Read per-host verification state for the default user.                         |
| `pm get-app-links --user cur <pkg>`      | Same as above when multiple users exist on the device.                         |
| `dumpsys package d`                      | Dump domain-preferred-apps for every package (alias: `domain-preferred-apps`). |

#### Domain verification state legend

Required: read the `Domain verification state:` block from `pm get-app-links` output before interpreting host status.

| State               | Meaning                                                                |
|---------------------|------------------------------------------------------------------------|
| `verified`          | Digital Asset Links succeeded for that host.                           |
| `approved`          | User or shell forced approval; not the same as automatic verification. |
| `denied`            | User or shell forced denial.                                           |
| `legacy_failure`    | Legacy verifier rejected the host; reason not surfaced.                |
| `migrated`          | Result carried over from legacy verification.                          |
| `restored`          | Approved after backup restore; assumed previously verified.            |
| `system_configured` | OEM or policy pre-approved the domain.                                 |
| `none`              | No record yet - wait, re-run `--re-verify`, or confirm network.        |
| `1024` or higher    | Device-specific verifier error code; retry after network is stable.    |

Required: treat the hex suffix after `Status: always` in `dumpsys package d` as user preference metadata - it does not replace per-host `verified` / `none` lines from `pm get-app-links`.

#### Pre-Android-12 verification compat

Use when the app targets below API 31 and you need the Android-12+ verifier behaviour on an older test image:

```bash
adb shell am compat enable 175408749 com.example.app
```

#### Digital Asset Links REST (no device)

```bash
curl 'https://digitalassetlinks.googleapis.com/v1/statements:list?\
source.web.site=https://example.com&\
relation=delegate_permission/common.handle_all_urls'
```

Required: HTTP 200 JSON body with a non-empty `statements` array before expecting `verified` on device.

#### Dynamic App Links REST validation

Required when server-side `dynamic_app_link_components` exists: query with `return_relation_extensions=true` and assert the extension payload before writing device tests (see [android-navigation.md → Dynamic App Links](android-navigation.md#dynamic-app-links-android-15-api-35)).

```bash
curl 'https://digitalassetlinks.googleapis.com/v1/statements:list?\
source.web.site=https://example.com&\
relation=delegate_permission/common.handle_all_urls&\
return_relation_extensions=true'
```

Required: locate `dynamic_app_link_components` under the relation-extension map for `delegate_permission/common.handle_all_urls` inside a `statements[]` entry; assert it is a non-empty JSON array when dynamic rules are active.

Forbidden: omitting `return_relation_extensions=true` when the test asserts dynamic path/query/fragment behaviour - the verifier omits that field without the flag.

#### Dynamic rules device refresh

Required after every deploy that edits `dynamic_app_link_components` in `assetlinks.json`:

```bash
adb shell pm verify-app-links --re-verify com.example.app
adb shell pm get-app-links com.example.app
```

Required: every host that participates in dynamic routing shows `verified` in `pm get-app-links` output before closing the change (or document an intentional `approved` / `selected` user override from [Domain verification state legend](#domain-verification-state-legend)).

#### Unit tests (parsing + stack)

```kotlin
class DeepLinkParsingTest {

    @Test
    fun `product deep link parses productId correctly`() {
        val uri = "https://example.com/products/abc123".toUri()
        val request = DeepLinkRequest(uri)

        val match = deepLinkPatterns.firstNotNullOfOrNull { pattern ->
            DeepLinkMatcher(request, pattern).match()
        }

        assertThat(match).isNotNull()
        val key = KeyDecoder(match!!.args)
            .decodeSerializableValue(match.serializer)
        assertThat(key).isEqualTo(ProductDetail(productId = "abc123"))
    }

    @Test
    fun `invalid host is rejected`() {
        val uri = "https://evil.com/products/abc123".toUri()
        assertThat(DeepLinkValidator.validate(uri)).isFalse()
    }

    @Test
    fun `synthetic back stack includes all parents`() {
        val key = ProductDetail(productId = "abc123")
        val stack = buildSyntheticBackStack(key)

        assertThat(stack).containsExactly(
            HomeRoute,
            ProductListRoute,
            ProductDetail(productId = "abc123")
        ).inOrder()
    }
}
```

#### Instrumented `onNewIntent` test

Required: the deep-link `Activity` uses `android:launchMode="singleTask"` and forwards `onNewIntent` through the same parser as `onCreate` ([android-navigation.md → onNewIntent for singleTask](android-navigation.md#onnewintent-for-singletask)).

Required: the destination composable root exposes `Modifier.testTag("…")` for every node the test asserts.

Forbidden: launching a second `Activity` with `startActivity` to simulate a second link - `singleTask` reuses the instance; call `onNewIntent` on the running `Activity` only.

```kotlin
// app/src/androidTest/kotlin/com/example/app/MainActivityDeepLinkTest.kt
import android.content.Intent
import android.net.Uri
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.example.app.MainActivity
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MainActivityDeepLinkTest {

    @get:Rule(order = 1)
    val composeRule = createAndroidComposeRule<MainActivity>()

    @Test
    fun onNewIntentNavigatesToParsedDestination() {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://example.com/products/deeplink-id"))
        InstrumentationRegistry.getInstrumentation().runOnMainSync {
            composeRule.activity.onNewIntent(intent)
        }
        composeRule.waitUntil(timeoutMillis = 5_000) {
            composeRule.onAllNodesWithTag("product_detail_screen").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithTag("product_detail_screen").assertIsDisplayed()
    }
}
```

Patterns, manifest, App Links, Dynamic App Links, security: [android-navigation.md](android-navigation.md#deep-links).

## UI Tests

### Compose UI Tests for Auth Screen with Truth

```kotlin
// feature-auth/src/androidTest/kotlin/com/example/feature/auth/AuthScreenTest.kt
import com.google.common.truth.Truth.assertThat
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput

class AuthScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `login screen shows all required UI elements`() {
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {}
                )
            }
        }

        // Assert all UI elements are displayed
        composeTestRule.onNodeWithText("Email").assertIsDisplayed()
        composeTestRule.onNodeWithText("Password").assertIsDisplayed()
        composeTestRule.onNodeWithText("Login").assertIsDisplayed()
        composeTestRule.onNodeWithText("Create Account").assertIsDisplayed()
        composeTestRule.onNodeWithText("Forgot Password?").assertIsDisplayed()
    }

    @Test
    fun `loading state shows progress indicator`() {
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(isLoading = true),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {}
                )
            }
        }

        composeTestRule
            .onNodeWithTag("loadingIndicator")
            .assertIsDisplayed()
    }

    @Test
    fun `error state shows error message and retry button`() {
        val errorMessage = "Invalid credentials"
        
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.Error(errorMessage, canRetry = true),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {}
                )
            }
        }

        // Assert error message is displayed
        composeTestRule
            .onNodeWithText(errorMessage)
            .assertIsDisplayed()

        // Assert retry button is displayed
        composeTestRule
            .onNodeWithText("Retry")
            .assertIsDisplayed()
    }

    @Test
    fun `user can input email and password`() {
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {}
                )
            }
        }

        // Input email
        val email = "test@example.com"
        composeTestRule
            .onNodeWithText("Email")
            .performTextInput(email)

        // Input password
        val password = "password123"
        composeTestRule
            .onNodeWithText("Password")
            .performTextInput(password)

        // Assert the inputs were captured (in real app, would verify ViewModel state)
        // This test ensures UI components are interactive
    }

    @Test
    fun `clicking create account triggers callback`() {
        var registerClicked = false
        
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(),
                    onAction = {},
                    onRegisterClick = { registerClicked = true },
                    onForgotPasswordClick = {}
                )
            }
        }

        // Click create account
        composeTestRule
            .onNodeWithText("Create Account")
            .performClick()

        // Assert callback was triggered
        assertThat(registerClicked).isTrue()
    }

    @Test
    fun `clicking forgot password triggers callback`() {
        var forgotPasswordClicked = false
        
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = { forgotPasswordClicked = true }
                )
            }
        }

        // Click forgot password
        composeTestRule
            .onNodeWithText("Forgot Password?")
            .performClick()

        // Assert callback was triggered
        assertThat(forgotPasswordClicked).isTrue()
    }

    @Test
    fun `login button is disabled when form is loading`() {
        composeTestRule.setContent {
            AppTheme {
                LoginScreen(
                    uiState = AuthUiState.LoginForm(isLoading = true),
                    onAction = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {}
                )
            }
        }

        // Assert login button is disabled
        composeTestRule
            .onNodeWithText("Login")
            .assertIsNotEnabled()
    }
}

```

## Screenshot Testing

Required: use [Compose Preview Screenshot Testing](https://developer.android.com/studio/preview/compose-screenshot-testing) (host JVM, reuses `@Preview`). One test per meaningful state (loading, success, error, empty) for every key screen.

### Setup

**1. `gradle.properties`:**
```properties
android.experimental.enableScreenshotTest=true
```

**2. Version catalog:** The `screenshot` version, `screenshot-validation-api` library, and `screenshot` plugin are defined in `assets/libs.versions.toml.template`.

**3. Module `build.gradle.kts`:**
```kotlin
plugins {
    alias(libs.plugins.screenshot)
}

android {
    experimentalProperties["android.experimental.enableScreenshotTest"] = true
}

dependencies {
    screenshotTestImplementation(libs.screenshot.validation.api)
    screenshotTestImplementation(libs.androidx.compose.ui.tooling)
}
```

### Writing Screenshot Tests

Place tests in the `screenshotTest` source set. Annotate with both `@PreviewTest` and `@Preview`:

```kotlin
// app/src/screenshotTest/kotlin/com/example/app/LoginScreenScreenshotTest.kt
package com.example.app

import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import com.android.tools.screenshot.PreviewTest
import com.example.app.ui.theme.AppTheme

@PreviewTest
@Preview(showBackground = true)
@Composable
fun LoginScreen_Loading() {
    AppTheme {
        LoginScreen(uiState = LoginUiState.Loading, onAction = {})
    }
}

@PreviewTest
@Preview(showBackground = true)
@Composable
fun LoginScreen_Success() {
    AppTheme {
        LoginScreen(
            uiState = LoginUiState.LoginForm(
                email = "user@example.com",
                password = "password123"
            ),
            onAction = {}
        )
    }
}

@PreviewTest
@Preview(showBackground = true)
@Composable
fun LoginScreen_Error() {
    AppTheme {
        LoginScreen(
            uiState = LoginUiState.Error("Invalid credentials", canRetry = true),
            onAction = {}
        )
    }
}
```

### Multi-Preview for Theme/Device Variants

Use `@Preview` parameters or custom multi-preview annotations to test across configurations:

```kotlin
@PreviewTest
@Preview(showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_NO, name = "Light")
@Preview(showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_YES, name = "Dark")
@Composable
fun LoginScreen_Themes() {
    AppTheme {
        LoginScreen(uiState = LoginUiState.LoginForm(), onAction = {})
    }
}

@PreviewTest
@Preview(showBackground = true, fontScale = 1.0f, name = "Default font")
@Preview(showBackground = true, fontScale = 1.5f, name = "Large font")
@Preview(showBackground = true, fontScale = 2.0f, name = "Largest font")
@Composable
fun LoginScreen_FontScales() {
    AppTheme {
        LoginScreen(uiState = LoginUiState.LoginForm(), onAction = {})
    }
}
```

### Configuring Image Difference Threshold

```kotlin
// module build.gradle.kts
android {
    testOptions {
        screenshotTests {
            imageDifferenceThreshold = 0.0001f // 0.01% tolerance
        }
    }
}
```

### Gradle Commands

```bash
# Generate/update reference images (run once, then commit to VCS)
./gradlew updateDebugScreenshotTest

# Update for a specific module
./gradlew :feature:auth:updateDebugScreenshotTest

# Validate screenshots against references (run in CI)
./gradlew validateDebugScreenshotTest

# Validate for a specific module
./gradlew :feature:auth:validateDebugScreenshotTest
```

Reference images: `{module}/src/screenshotTestDebug/reference/` - commit to VCS. Validation report: `{module}/build/reports/screenshotTest/preview/debug/index.html`.

### Requirements

- AGP 8.5+ (Gradle tasks); AGP 9.0+ for full IDE integration.
- JDK 17+.
- `com.android.compose.screenshot` plugin 0.0.1-alpha13+.

### Rules

Required:
- Wrap every preview in the app theme (`AppTheme { }`).
- Cover light and dark via `uiMode` or a multi-preview annotation.
- Cover at least one large `fontScale` to catch overflow.
- Keep tests in the `screenshotTest` source set; do not mix with unit or instrumented tests.
- Commit reference images alongside source.

## Performance Benchmarks

Use Macrobenchmark for end-to-end performance checks (startup, navigation, and Compose scrolling).
Setup and commands live in `references/android-performance.md`.

## Test Utilities

### Test Data Factories (in `core:testing`)

```kotlin
// core/testing/src/main/kotlin/com/example/testing/data/TestData.kt
import com.google.common.truth.Truth.assertThat

object TestData {
    
    // Auth test data
    val testUser = User(
        id = "user-123",
        email = "test@example.com",
        name = "Test User",
        profileImage = null
    )
    
    val testAuthToken = AuthToken("token-123", testUser)
    
    fun createLoginForm(
        email: String = "test@example.com",
        password: String = "password123",
        isLoading: Boolean = false,
        emailError: String? = null,
        passwordError: String? = null
    ) = AuthUiState.LoginForm(
        email = email,
        password = password,
        isLoading = isLoading,
        emailError = emailError,
        passwordError = passwordError
    )
    
    fun createRegisterForm(
        email: String = "test@example.com",
        password: String = "password123",
        confirmPassword: String = "password123",
        name: String = "Test User",
        isLoading: Boolean = false,
        errors: Map<String, String> = emptyMap()
    ) = AuthUiState.RegisterForm(
        email = email,
        password = password,
        confirmPassword = confirmPassword,
        name = name,
        isLoading = isLoading,
        errors = errors
    )
    
    fun createErrorState(
        message: String = "Something went wrong",
        canRetry: Boolean = true
    ) = AuthUiState.Error(message, canRetry)
    
    // Network test data
    val testNetworkUser = NetworkUser(
        id = "user-123",
        email = "test@example.com",
        name = "Test User"
    )
    
    val testAuthTokenResponse = AuthTokenResponse(
        token = "token-123",
        user = testNetworkUser
    )
    
    // Entity test data
    val testUserEntity = UserEntity(
        id = "user-123",
        email = "test@example.com",
        name = "Test User"
    )
    
    // Test assertions
    fun assertUserEquals(expected: User, actual: User) {
        assertThat(actual.id).isEqualTo(expected.id)
        assertThat(actual.email).isEqualTo(expected.email)
        assertThat(actual.name).isEqualTo(expected.name)
        assertThat(actual.profileImage).isEqualTo(expected.profileImage)
    }
    
    fun assertAuthTokenEquals(expected: AuthToken, actual: AuthToken) {
        assertThat(actual.value).isEqualTo(expected.value)
        assertUserEquals(expected.user, actual.user)
    }
}
```

### Running Tests

```bash
# Run all unit tests
./gradlew test

# Run tests for specific feature
./gradlew :feature:auth:test

# Run instrumented tests
./gradlew connectedAndroidTest

# Run tests with coverage
./gradlew testDebugUnitTestCoverage

# Run specific test class
./gradlew :feature:auth:testDebugUnitTest --tests "*AuthViewModelTest"

# Run tests with Truth assertions enabled
./gradlew test --info
```

## Rules

Required:
- Use Google Truth (`assertThat(actual).isEqualTo(expected)`); never JUnit `assertEquals` / `assertTrue` / `assertNotNull`.
- Use Truth subject methods (`hasSize`, `contains`, `isInstanceOf`, `isNull`, `isNotNull`) instead of hand-rolled boolean assertions.
- Hand-written fakes mirror production behaviour with state and test hooks; never stub-only.
- Test each feature module's ViewModel and UI in isolation; never depend on another feature module from tests.
- Test `Navigator` interfaces with fakes; MockK only for Navigation 3 framework types in `app`.
- Use `@HiltAndroidTest` with a test-scoped `@Module` for DI tests.
- Use Room 3 in-memory builder with `setDriver(BundledSQLiteDriver())` for DAO tests; use `room3-testing` + `MigrationTestHelper` + `SQLiteConnection` for migration tests.
- Cover `SavedStateHandle` paths (navigation args + process-death restore).
- Use Turbine for any `Flow` that emits more than once.

Forbidden:
- Mocking libraries in `feature:*` and `core:*` modules.
- Sharing test fixtures across feature modules (place them in `core:testing`).
- Relying on `Dispatchers.Main` directly; always use the project's `MainDispatcherRule`.

## Paging 3 Testing

### Testing ViewModels with PagingData

When testing ViewModels that expose `PagingData<T>`, use `PagingData.from()` to create test data:

```kotlin
// core/testing/FakePagingRepository.kt
class FakeProductRepository : ProductRepository {
    private val pagingFlow = MutableSharedFlow<PagingData<Product>>(replay = 1)
    
    fun emitProducts(products: List<Product>) {
        pagingFlow.tryEmit(PagingData.from(products))
    }
    
    fun emitError() {
        // CORRECT: PagingData has no error channel — surface failures via Result or a parallel error Flow
        pagingFlow.tryEmit(PagingData.empty())
    }
    
    override fun getProducts(query: String): Flow<PagingData<Product>> = pagingFlow
}

// feature/products/ProductsViewModelTest.kt
@Test
fun `when products loaded then state is success`() = runTest {
    // Given
    val testProducts = listOf(
        Product(id = "1", name = "Product 1", price = 10.0),
        Product(id = "2", name = "Product 2", price = 20.0)
    )
    
    // When
    fakeRepository.emitProducts(testProducts)
    advanceUntilIdle()
    
    // Then
    val state = viewModel.uiState.value
    assertThat(state).isInstanceOf(ProductsUiState.Success::class.java)
}
```

### Important: `cachedIn()` Limitations

**Warning:** `cachedIn(viewModelScope)` caches `PagingData` and can swallow exceptions, making error-state testing unreliable.

```kotlin
// WRONG: Problematic for error testing
class ProductsViewModel @Inject constructor(
    private val repository: ProductRepository
) : ViewModel() {
    val products: Flow<PagingData<Product>> = repository
        .getProducts()
        .cachedIn(viewModelScope)  // Caches data, swallows some errors
}
```

**Solutions:**

1. **Test error handling via non-paging use cases:**
   ```kotlin
   // For error scenarios, use a separate Result-based flow
   val productsResult: StateFlow<Result<List<Product>>> = repository
       .getProductsAsList()
       .catch { emit(Result.failure(it)) }
       .stateIn(viewModelScope, SharingStarted.Lazily, Result.success(emptyList()))
   
   // Test error handling here instead
   @Test
   fun `when fetch fails then error state is shown`() = runTest {
       fakeRepository.emitError(NetworkException())
       advanceUntilIdle()
       
       val result = viewModel.productsResult.value
       assertThat(result.isFailure).isTrue()
   }
   ```

2. **Use separate error/loading states:**
   ```kotlin
   class ProductsViewModel @Inject constructor(
       private val repository: ProductRepository
   ) : ViewModel() {
       private val _errorState = MutableStateFlow<String?>(null)
       val errorState: StateFlow<String?> = _errorState.asStateFlow()
       
       val products: Flow<PagingData<Product>> = repository
           .getProducts()
           .catch { error ->
               _errorState.value = error.message
               emit(PagingData.empty())
           }
           .cachedIn(viewModelScope)
   }
   
   @Test
   fun `when fetch fails then error message is set`() = runTest {
       fakeRepository.emitError()
       advanceUntilIdle()
       
       assertThat(viewModel.errorState.value).isNotNull()
   }
   ```

### Testing with AsyncPagingDataDiffer

For more advanced testing (checking actual loaded items), use `AsyncPagingDataDiffer`:

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
@Test
fun `paging data contains expected items`() = runTest {
    val testDispatcher = UnconfinedTestDispatcher(testScheduler)
    
    val differ = AsyncPagingDataDiffer(
        diffCallback = object : DiffUtil.ItemCallback<Product>() {
            override fun areItemsTheSame(oldItem: Product, newItem: Product) =
                oldItem.id == newItem.id
            override fun areContentsTheSame(oldItem: Product, newItem: Product) =
                oldItem == newItem
        },
        updateCallback = object : ListUpdateCallback {
            override fun onInserted(position: Int, count: Int) {}
            override fun onRemoved(position: Int, count: Int) {}
            override fun onMoved(fromPosition: Int, toPosition: Int) {}
            override fun onChanged(position: Int, count: Int, payload: Any?) {}
        },
        workerDispatcher = testDispatcher
    )
    
    val testProducts = listOf(
        Product(id = "1", name = "Product 1", price = 10.0),
        Product(id = "2", name = "Product 2", price = 20.0)
    )
    
    fakeRepository.emitProducts(testProducts)
    
    viewModel.products.collect { pagingData ->
        differ.submitData(pagingData)
    }
    
    advanceUntilIdle()
    
    assertThat(differ.snapshot().items).hasSize(2)
    assertThat(differ.snapshot().items[0].id).isEqualTo("1")
    assertThat(differ.snapshot().items[1].id).isEqualTo("2")
}
```

### `paging-testing`: `asSnapshot` and `TestPager`

Required: `testImplementation(libs.androidx.paging.testing)` and catalog rules in [dependencies.md](/references/dependencies.md#paging-3-test-artifact). Keep the `paging` version ref aligned with `paging-runtime` and `paging-compose`.

Use `Flow<PagingData<T>>.asSnapshot { }` when the test drives the same `Flow` the UI collects and asserts the rendered item list after explicit loads, scrolls, or refresh.

Inside the block the receiver is `SnapshotLoader`: call `scrollTo`, `refresh`, `appendScrollWhile`, `prependScrollWhile`, or `flingTo`, then return the snapshot list. `asSnapshot` is suspending; invoke it only from `runTest` (`kotlinx-coroutines-test`).

```kotlin
import androidx.paging.testing.asSnapshot
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class ProductsPagingTest {
    @Test
    fun first_page_matches_repository() = runTest {
        val items: List<Product> = viewModel.products.asSnapshot {
            refresh()
        }
        assertEquals(2, items.size)
    }
}
```

Use `TestPager` when the test targets a `PagingSource` in isolation (page keys, invalidation, error paths) without a ViewModel or `Flow` wrapper. [`androidx.paging.testing`](https://developer.android.com/reference/kotlin/androidx/paging/testing/package-summary) lists `TestPager` and related types.

Use `PagingData.from()` / fakes when only static list-shaped `PagingData` is required.

Use `AsyncPagingDataDiffer` when verifying diff callbacks and `ListUpdateCallback` behavior against submitted `PagingData`.

### Paging rules

Required:
- Use `PagingData.from(list)` for the common path.
- Hold error and loading state in a sibling `StateFlow`; do not assert errors through `PagingData` because `cachedIn` swallows them.
- Use `AsyncPagingDataDiffer` only when verifying actual loaded items.
- Use `asSnapshot` when asserting loaded content through the real `Flow<PagingData<T>>` pipeline.
- Use `TestPager` for direct `PagingSource` unit tests.
- `advanceUntilIdle()` before every assertion when the test mixes `runTest` with non-suspending collection patterns.

Forbidden:
- Testing the Paging library's internal pagination logic.

## Localization Testing

See [android-i18n.md](/references/android-i18n.md#testing-localization) for locales, plurals, RTL, parameterized locale tests, RTL screenshots, and date/time/currency formatting.
- [Hilt Testing](https://developer.android.com/training/dependency-injection/hilt-testing) - Official Hilt testing guide
