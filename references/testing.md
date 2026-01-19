# Testing Patterns

Testing approach following our multi-module architecture with test doubles strategy (no mocking libraries)
and Google Truth for assertions.

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Test Doubles](#test-doubles)
3. [ViewModel Tests](#viewmodel-tests)
4. [Repository Tests](#repository-tests)
5. [Navigation Tests](#navigation-tests)
6. [UI Tests](#ui-tests)
7. [Test Utilities](#test-utilities)

## Testing Philosophy

### No Mocking Libraries

Our architecture avoids mocking libraries in feature and core modules, using test doubles instead.
We make an exception in the app module for navigation testing, where MockK is used to mock framework classes like NavController.
- **Feature modules**: No mocking libraries - use test doubles that implement interfaces
- **Core modules**: No mocking libraries - use test doubles and in-memory databases
- **App module**: **Use MockK** for navigation testing only (NavController, NavHostController)
- Create test doubles that implement the same interfaces
- Test doubles provide realistic implementations with test hooks
- Results in less brittle tests that exercise more production code
- Use Google Truth for fluent, readable assertions

### Test Types by Module

| Module          | Test Type         | Location           | Purpose                   |
|-----------------|-------------------|--------------------|---------------------------|
| Feature modules | Unit tests        | `src/test/`        | ViewModel, UI logic       |
| Core/Domain     | Unit tests        | `src/test/`        | Use Cases, business logic |
| Core/Data       | Integration tests | `src/test/`        | Repository, DataSource    |
| Core/UI         | UI tests          | `src/androidTest/` | Shared components         |
| App module      | Navigation tests  | `src/test/`        | Navigator implementations |

## Test Doubles

### Test Repository Pattern (in `core:testing` module)

```kotlin
// core/testing/src/main/kotlin/com/example/testing/auth/
class TestAuthRepository : AuthRepository {

    private val authStateFlow = MutableStateFlow<AuthState>(AuthState.Unauthenticated)
    private val users = mutableMapOf<String, User>()
    private val authTokens = mutableMapOf<String, AuthToken>()

    // Test hooks
    fun sendAuthState(authState: AuthState) {
        authStateFlow.value = authState
    }

    fun addUser(user: User) {
        users[user.id] = user
    }

    fun setAuthToken(email: String, token: AuthToken) {
        authTokens[email] = token
    }

    // Interface implementation
    override suspend fun login(email: String, password: String): Result<AuthToken> {
        return authTokens[email]?.let { Result.success(it) }
            ?: Result.failure(Exception("Invalid credentials"))
    }

    override suspend fun register(user: User): Result<Unit> {
        users[user.id] = user
        return Result.success(Unit)
    }

    override fun observeAuthState(): Flow<AuthState> = authStateFlow

    override suspend fun resetPassword(email: String): Result<Unit> {
        return Result.success(Unit)
    }
}
```

### Test Navigator Pattern

```kotlin
// core/testing/src/main/kotlin/com/example/testing/navigation/
class TestAuthNavigator : AuthNavigator {
    
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

    // Test helper
    fun clearEvents() {
        _navigationEvents.clear()
    }
}
```

### Test UseCase Pattern

```kotlin
// core/testing/src/main/kotlin/com/example/testing/domain/
class TestLoginUseCase : LoginUseCase {
    
    var shouldSucceed = true
    var delayMillis: Long = 0
    
    override suspend fun invoke(email: String, password: String): Result<AuthToken> {
        if (delayMillis > 0) {
            delay(delayMillis)
        }
        
        return if (shouldSucceed) {
            Result.success(AuthToken("test-token", User("1", email, "Test User")))
        } else {
            Result.failure(Exception("Login failed"))
        }
    }
}
```

## ViewModel Tests

### AuthViewModel Test with Test Doubles

```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/AuthViewModelTest.kt
import com.google.common.truth.Truth.assertThat

class AuthViewModelTest {

    @get:Rule
    val dispatcherRule = TestDispatcherRule()

    private lateinit var testAuthRepository: TestAuthRepository
    private lateinit var testLoginUseCase: TestLoginUseCase
    private lateinit var testRegisterUseCase: TestRegisterUseCase
    private lateinit var viewModel: AuthViewModel

    @Before
    fun setup() {
        testAuthRepository = TestAuthRepository()
        testLoginUseCase = TestLoginUseCase()
        testRegisterUseCase = TestRegisterUseCase()
        
        viewModel = AuthViewModel(
            loginUseCase = testLoginUseCase,
            registerUseCase = testRegisterUseCase,
            resetPasswordUseCase = TestResetPasswordUseCase()
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
        testLoginUseCase.shouldSucceed = false
        
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
        testLoginUseCase.shouldSucceed = false
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
        testLoginUseCase.shouldSucceed = false
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

```kotlin
import com.google.common.truth.Truth.assertThat
import app.cash.turbine.test

@Test
fun `uiState emits correct states during login flow`() = runTest {
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
    testLoginUseCase.shouldSucceed = false
    
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

    private lateinit var testLocalDataSource: TestAuthLocalDataSource
    private lateinit var testRemoteDataSource: TestAuthRemoteDataSource
    private lateinit var authMapper: AuthMapper
    private lateinit var repository: AuthRepositoryImpl

    @Before
    fun setup() {
        testLocalDataSource = TestAuthLocalDataSource()
        testRemoteDataSource = TestAuthRemoteDataSource()
        authMapper = AuthMapper()
        
        repository = AuthRepositoryImpl(
            localDataSource = testLocalDataSource,
            remoteDataSource = testRemoteDataSource,
            authMapper = authMapper
        )
    }

    @Test
    fun `login success saves token and user to local storage`() = runTest {
        // Arrange
        val testEmail = "test@example.com"
        val testPassword = "password123"
        val expectedToken = AuthTokenResponse("test-token", NetworkUser("1", testEmail, "Test User"))
        testRemoteDataSource.setLoginResponse(expectedToken)

        // Act
        val result = repository.login(testEmail, testPassword)

        // Assert
        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()?.value).isEqualTo(expectedToken.token)
        
        // Verify local storage was updated
        val savedToken = testLocalDataSource.getAuthToken()
        assertThat(savedToken).isEqualTo(expectedToken.token)
        
        val savedUser = testLocalDataSource.getUser()
        assertThat(savedUser?.email).isEqualTo(expectedToken.user.email)
    }

    @Test
    fun `login failure returns error result`() = runTest {
        // Arrange
        val testEmail = "test@example.com"
        val testPassword = "wrong-password"
        testRemoteDataSource.shouldFailLogin = true

        // Act
        val result = repository.login(testEmail, testPassword)

        // Assert
        assertThat(result.isFailure).isTrue()
        assertThat(result.exceptionOrNull()?.message).contains("Invalid")
    }

    @Test
    fun `observeAuthState emits Authenticated when token exists`() = runTest {
        // Arrange
        testLocalDataSource.setAuthToken("test-token")
        testLocalDataSource.setUser(UserEntity("1", "test@example.com", "Test User"))

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
        testLocalDataSource.shouldFail = true

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
        testRemoteDataSource.setRegisterResponse(Unit)

        // Act
        val result = repository.register(testUser)

        // Assert
        assertThat(result.isSuccess).isTrue()
        val savedUser = testLocalDataSource.getUser()
        assertThat(savedUser?.email).isEqualTo(testUser.email)
        assertThat(savedUser?.name).isEqualTo(testUser.name)
    }
}
```

## Navigation Tests

### Testing Navigator Implementations in App Module with Truth

```kotlin
// app/src/test/kotlin/com/example/navigation/AppNavigatorsTest.kt
import com.google.common.truth.Truth.assertThat
import io.mockk.every
import io.mockk.mockk
import io.mockk.verify

class AppNavigatorsTest {

    private lateinit var mockNavController: NavHostController
    
    @Before
    fun setup() {
        mockNavController = mockk(relaxed = true)
        // Mock current destination
        every { mockNavController.currentDestination } returns mockk {
            every { route } returns "auth"
        }
    }

    @Test
fun `AuthNavigatorImpl navigates to main app with correct pop behavior`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)

        // Act
    authNavigator.navigateToMainApp()

        // Assert
        verify { 
        mockNavController.navigate(
            match { it == "main" },
            match { 
                it?.popUpTo?.route == "auth" && 
                it.popUpTo.inclusive == true 
            }
        ) 
    }
    }

    @Test
    fun `AuthNavigatorImpl navigation methods call correct routes`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)

        // Test each navigation method
        val testCases = listOf(
            { authNavigator.navigateToRegister() } to "auth/register",
            { authNavigator.navigateToForgotPassword() } to "auth/forgot_password",
            { authNavigator.navigateToProfile("user123") } to "profile/user123",
            { authNavigator.navigateToVerifyEmail("token123") } to "auth/verify/token123",
            { authNavigator.navigateToResetPassword("reset123") } to "auth/reset/reset123"
        )

        testCases.forEach { (action, expectedRoute) ->
            // Act
            action()

            // Assert
            verify { mockNavController.navigate(match { it == expectedRoute }, any()) }
        }
    }

    @Test
    fun `TestAuthNavigator tracks all navigation events`() {
        // Arrange
        val testNavigator = TestAuthNavigator()

        // Act
    testNavigator.navigateToMainApp()
        testNavigator.navigateToRegister()
        testNavigator.navigateToProfile("user123")
        testNavigator.navigateBack()

        // Assert
        assertThat(testNavigator.navigationEvents).hasSize(4)
    assertThat(testNavigator.navigationEvents[0]).isEqualTo("navigateToMainApp")
    assertThat(testNavigator.navigationEvents[1]).isEqualTo("navigateToRegister")
    assertThat(testNavigator.navigationEvents[2]).isEqualTo("navigateToProfile:user123")
    assertThat(testNavigator.navigationEvents[3]).isEqualTo("navigateBack")
    }

    @Test
    fun `TestAuthNavigator clearEvents works correctly`() {
        // Arrange
        val testNavigator = TestAuthNavigator()
    testNavigator.navigateToMainApp()
        testNavigator.navigateToRegister()
        
        // Pre-condition
        assertThat(testNavigator.navigationEvents).isNotEmpty()

        // Act
        testNavigator.clearEvents()

        // Assert
        assertThat(testNavigator.navigationEvents).isEmpty()
    }

    private fun createAuthNavigator(navController: NavHostController): AuthNavigator {
        return object : AuthNavigator {
            override fun navigateToRegister() = navController.navigate("auth/register")
            override fun navigateToForgotPassword() = navController.navigate("auth/forgot_password")
            override fun navigateBack() = navController.popBackStack()
            override fun navigateToProfile(userId: String) = navController.navigate("profile/$userId")
            override fun navigateToMainApp() {
                navController.navigate("main") {
                    popUpTo("auth") { inclusive = true }
                }
            }
            override fun navigateToVerifyEmail(token: String) = navController.navigate("auth/verify/$token")
            override fun navigateToResetPassword(token: String) = navController.navigate("auth/reset/$token")
        }
    }
}
```

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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(AuthUiState.LoginForm())
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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(
                        AuthUiState.LoginForm(isLoading = true)
                    )
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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(
                        AuthUiState.Error(errorMessage, canRetry = true)
                    )
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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(AuthUiState.LoginForm())
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
                    onLoginSuccess = {},
                    onRegisterClick = { registerClicked = true },
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(AuthUiState.LoginForm())
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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = { forgotPasswordClicked = true },
                    viewModel = FakeAuthViewModel(AuthUiState.LoginForm())
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
                    onLoginSuccess = {},
                    onRegisterClick = {},
                    onForgotPasswordClick = {},
                    viewModel = FakeAuthViewModel(
                        AuthUiState.LoginForm(isLoading = true)
                    )
                )
            }
        }

        // Assert login button is disabled
        composeTestRule
            .onNodeWithText("Login")
            .assertIsNotEnabled()
    }
}

// Fake ViewModel for UI tests
class FakeAuthViewModel(private val initialState: AuthUiState) : AuthViewModel(
    loginUseCase = TestLoginUseCase(),
    registerUseCase = TestRegisterUseCase(),
    resetPasswordUseCase = TestResetPasswordUseCase()
) {
    private val _uiState = MutableStateFlow(initialState)
    override val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()
    
    override fun onAction(action: AuthAction) {
        // No-op for UI tests
    }
}
```

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

### Gradle Test Configuration with Truth

```kotlin
// libs.versions.toml
[versions]
truth = "1.1.5"
turbine = "1.0.0"

[libraries]
google-truth = { group = "com.google.truth", name = "truth", version.ref = "truth" }
cashapp-turbine = { group = "app.cash.turbine", name = "turbine", version.ref = "turbine" }

// build.gradle.kts for feature modules
dependencies {
    // Test dependencies
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.google.truth)
    testImplementation(libs.cashapp.turbine)
    
    // Android test dependencies
    androidTestImplementation(libs.androidx.test.ext.junit)
    androidTestImplementation(libs.androidx.test.espresso.core)
    androidTestImplementation(libs.androidx.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.compose.ui.test.manifest)
    
    // Test utilities from core
    testImplementation(project(":core:testing"))
    androidTestImplementation(project(":core:testing"))
}

// build.gradle.kts for core:testing module
dependencies {
    // Depend on all core modules for test utilities
    implementation(project(":core:domain"))
    implementation(project(":core:data"))
    implementation(project(":core:ui"))
    
    // Testing libraries
    implementation(libs.junit)
    implementation(libs.kotlinx.coroutines.test)
    implementation(libs.google.truth)
    implementation(libs.cashapp.turbine)
    implementation(libs.androidx.test.core)
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

1. **Test Doubles Over Mocks**: Create realistic test implementations that mirror production behavior
2. **Feature Isolation**: Each feature module tests its own ViewModel and UI independently
3. **Navigation Testing**: Test navigator interfaces in app module, not in features
4. **Integration Testing**: Test repository implementations with test data sources
5. **UI Testing**: Test composable screens with fake ViewModels and navigators
6. **No Feature Dependencies**: Test utilities in `core:testing` avoid feature-to-feature dependencies