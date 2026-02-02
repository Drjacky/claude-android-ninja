# Testing Patterns

Testing approach following our multi-module architecture with test doubles strategy (no mocking libraries)
and Google Truth for assertions.

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
12. [Performance Benchmarks](#performance-benchmarks)
13. [Test Utilities](#test-utilities)

## Testing Philosophy

### No Mocking Libraries

Our architecture avoids mocking libraries in feature and core modules, using test doubles instead.
We make an exception in the app module for navigation testing, where MockK is used to mock framework classes.
- **Feature modules**: No mocking libraries - use fake implementations that implement interfaces
- **Core modules**: No mocking libraries - use fakes and in-memory databases
- **App module**: **Use MockK** for Navigation3 testing only (NavigationState, Navigator)
- Create fake implementations that provide realistic behavior with test hooks
- Fakes provide working implementations, not just stubs
- Results in less brittle tests that exercise more production code
- Use Google Truth for fluent, readable assertions

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

        // Verify we're in error state
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

```kotlin
// core/testing/src/main/kotlin/com/example/testing/rule/TestDispatcherRule.kt
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

### Testing StateFlow with Turbine and Truth

Turbine is best for testing Flow emissions over time. Use `advanceUntilIdle()` for simple async operations.

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

### Key Coroutine Testing Principles

1. **Always use `runTest`**: Provides virtual time and automatic completion waiting
2. **Share test scheduler**: Use `UnconfinedTestDispatcher(testScheduler)` or `StandardTestDispatcher()`
3. **Inject dispatchers**: Never hardcode dispatchers in production code - always inject for testability
4. **Use `advanceUntilIdle()`**: Wait for all pending coroutines before assertions
5. **Use `advanceTimeBy()`**: Fast-forward time for delay/timeout testing without actually waiting
6. **Test cancellation**: Verify coroutines handle cancellation correctly
7. **Test cleanup**: Ensure resources are released even on cancellation

### Dispatcher Choices in Tests

```kotlin
// UnconfinedTestDispatcher: Executes coroutines immediately (eager)
// Good for: Most tests, when you want synchronous behavior
val unconfinedDispatcher = UnconfinedTestDispatcher(testScheduler)

// StandardTestDispatcher: Queues coroutines (requires advanceUntilIdle)
// Good for: Testing execution order, complex timing scenarios
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

### In-Memory Database for Tests

```kotlin
// core/database/src/androidTest/kotlin/com/example/database/AuthDaoTest.kt
import android.content.Context
import androidx.room.Room
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
        database = Room.inMemoryDatabaseBuilder(
            context,
            AppDatabase::class.java
        ).build()
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

```kotlin
// core/database/src/androidTest/kotlin/com/example/database/MigrationTest.kt
import androidx.room.testing.MigrationTestHelper
import androidx.test.platform.app.InstrumentationRegistry
import com.google.common.truth.Truth.assertThat

class MigrationTest {

    @get:Rule
    val helper = MigrationTestHelper(
        InstrumentationRegistry.getInstrumentation(),
        AppDatabase::class.java
    )

    @Test
    fun migrate1To2_containsCorrectData() {
        // Create database at version 1
        helper.createDatabase(TEST_DB, 1).apply {
            execSQL("INSERT INTO users VALUES ('1', 'test@example.com', 'Test User')")
            close()
        }

        // Run migration
        helper.runMigrationsAndValidate(TEST_DB, 2, true, MIGRATION_1_2)

        // Validate data after migration
        helper.runMigrationsAndValidate(TEST_DB, 2, true).apply {
            query("SELECT * FROM users WHERE id = '1'").use { cursor ->
                assertThat(cursor.moveToFirst()).isTrue()
                assertThat(cursor.getString(cursor.getColumnIndex("email")))
                    .isEqualTo("test@example.com")
            }
            close()
        }
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

Verify that `@Immutable` and `@Stable` annotations are correctly applied:

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

**Note**: Use Compose Compiler reports (`composeStabilityAnalyzer` Gradle plugin) to verify stability
at build time. See `references/gradle-setup.md` → "Compose Stability Analyzer".

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

## Key Testing Principles with Google Truth

1. **Fluent Assertions**: Use Truth's fluent API for readable, maintainable tests:
   ```kotlin
   // Instead of: assertEquals(expected, actual)
   assertThat(actual).isEqualTo(expected)
   
   // Instead of: assertTrue(condition)
   assertThat(condition).isTrue()
   
   // Instead of: assertNotNull(value)
   assertThat(value).isNotNull()
   ```

2. **Rich Failure Messages**: Truth provides detailed failure messages:
   ```kotlin
   // Failure message shows both values
   assertThat(actualUser.email).isEqualTo("expected@email.com")
   // Output: Not true that <actual@email.com> is equal to <expected@email.com>
   ```

3. **Collection Assertions**: Easy collection testing:
   ```kotlin
   assertThat(userList).hasSize(3)
   assertThat(userList).contains(user1)
   assertThat(userList).doesNotContain(invalidUser)
   ```

4. **Nullability Support**: Kotlin-friendly null checks:
   ```kotlin
   assertThat(nullableValue).isNull()
   assertThat(nonNullValue).isNotNull()
   ```

5. **Custom Subjects**: Extend Truth for domain-specific assertions:
   ```kotlin
   // In TestData.kt
   fun assertUserEquals(expected: User, actual: User) {
       assertThat(actual.id).isEqualTo(expected.id)
       assertThat(actual.email).isEqualTo(expected.email)
       assertThat(actual.name).isEqualTo(expected.name)
   }
   ```

## Key Testing Principles in Our Architecture

1. **Fakes Over Mocks**: Create realistic fake implementations that mirror production behavior
2. **Feature Isolation**: Each feature module tests its own ViewModel and UI independently  
3. **Navigation Testing**: Test navigator interfaces with fakes, not MockK
4. **Integration Testing**: Test repository implementations with fake data sources
5. **UI Testing**: Test composable screens with fake ViewModels and navigators
6. **No Feature Dependencies**: Test utilities in `core:testing` avoid feature-to-feature dependencies
7. **Hilt for DI Tests**: Use `@HiltAndroidTest` for testing with dependency injection
8. **In-Memory Database**: Use Room's in-memory database for DAO tests
9. **SavedStateHandle**: Test navigation arguments and process death scenarios
10. **Turbine for Flow**: Use Turbine for testing multiple Flow emissions over time