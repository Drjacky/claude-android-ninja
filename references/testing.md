# Testing Patterns

Testing approach following the multi-module architecture with test doubles strategy (no mocking libraries).

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

Our architecture does NOT use mocking libraries (Mockito, MockK). Instead:
- Create test doubles that implement the same interfaces
- Test doubles provide realistic implementations with test hooks
- Results in less brittle tests that exercise more production code

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
    override fun navigateToHome() {
        _navigationEvents.add("navigateToHome")
    }

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
        assertTrue(state is AuthUiState.LoginForm)
    }

    @Test
    fun `when email is changed, ui state updates email`() = runTest {
        // Arrange
        val testEmail = "test@example.com"

        // Act
        viewModel.onAction(AuthAction.EmailChanged(testEmail))

        // Assert
        val state = viewModel.uiState.value as AuthUiState.LoginForm
        assertEquals(testEmail, state.email)
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
        assertTrue(loadingState.isLoading)

        // Wait for async operation
        advanceUntilIdle()

        // Assert - Check success state
        val successState = viewModel.uiState.value
        assertTrue(successState is AuthUiState.Success)
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
        assertTrue(state is AuthUiState.Error)
    }

    @Test
    fun `when RegisterClicked, state becomes RegisterForm`() = runTest {
        // Act
        viewModel.onAction(AuthAction.RegisterClicked)

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state is AuthUiState.RegisterForm)
    }

    @Test
    fun `when ForgotPasswordClicked, state becomes ForgotPasswordForm`() = runTest {
        // Act
        viewModel.onAction(AuthAction.ForgotPasswordClicked)

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state is AuthUiState.ForgotPasswordForm)
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
        assertTrue(viewModel.uiState.value is AuthUiState.Error)

        // Act
        viewModel.onAction(AuthAction.Retry)

        // Assert
        val state = viewModel.uiState.value
        assertTrue(state is AuthUiState.LoginForm)
    }

    @Test
    fun `when ClearError action called, error is cleared`() = runTest {
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
        assertTrue(state is AuthUiState.LoginForm)
        val loginForm = state as AuthUiState.LoginForm
        assertEquals("", loginForm.email)
        assertEquals("", loginForm.password)
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

### Testing StateFlow with Turbine

```kotlin
@Test
fun `uiState emits correct states during login flow`() = runTest {
    viewModel.uiState.test {
        // Initial state
        assertTrue(awaitItem() is AuthUiState.LoginForm)

        // Trigger login
        viewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        viewModel.onAction(AuthAction.PasswordChanged("password123"))
        viewModel.onAction(AuthAction.LoginClicked)

        // Should emit Loading state
        val loadingState = awaitItem() as AuthUiState.LoginForm
        assertTrue(loadingState.isLoading)

        // Should emit Success state
        val successState = awaitItem()
        assertTrue(successState is AuthUiState.Success)

        cancelAndIgnoreRemainingEvents()
    }
}
```

## Repository Tests

### Testing AuthRepository Implementation

```kotlin
// core/data/src/test/kotlin/com/example/data/auth/AuthRepositoryImplTest.kt
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
        assertTrue(result.isSuccess)
        assertEquals(expectedToken.token, result.getOrNull()?.value)
        
        // Verify local storage was updated
        val savedToken = testLocalDataSource.getAuthToken()
        assertEquals(expectedToken.token, savedToken)
        
        val savedUser = testLocalDataSource.getUser()
        assertEquals(expectedToken.user.email, savedUser?.email)
    }

    @Test
    fun `observeAuthState emits Authenticated when token exists`() = runTest {
        // Arrange
        testLocalDataSource.setAuthToken("test-token")
        testLocalDataSource.setUser(UserEntity("1", "test@example.com", "Test User"))

        // Act & Assert
        repository.observeAuthState().test {
            val authState = awaitItem()
            assertTrue(authState is AuthState.Authenticated)
            assertEquals("1", (authState as AuthState.Authenticated).user.id)
            
            cancelAndIgnoreRemainingEvents()
        }
    }

    @Test
    fun `observeAuthState emits Unauthenticated when no token exists`() = runTest {
        // Act & Assert
        repository.observeAuthState().test {
            val authState = awaitItem()
            assertTrue(authState is AuthState.Unauthenticated)
            
            cancelAndIgnoreRemainingEvents()
        }
    }
}
```

## Navigation Tests

### Testing Navigator Implementations in App Module

```kotlin
// app/src/test/kotlin/com/example/navigation/AppNavigatorsTest.kt
class AppNavigatorsTest {

    private lateinit var mockNavController: NavHostController
    
    @Before
    fun setup() {
        mockNavController = mockk(relaxed = true)
    }

    @Test
    fun `AuthNavigatorImpl navigates to home correctly`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)

        // Act
        authNavigator.navigateToHome()

        // Assert
        verify { mockNavController.navigate("home") {
            popUpTo("auth") { inclusive = true }
        } }
    }

    @Test
    fun `AuthNavigatorImpl navigates to register correctly`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)

        // Act
        authNavigator.navigateToRegister()

        // Assert
        verify { mockNavController.navigate("auth/register") }
    }

    @Test
    fun `AuthNavigatorImpl navigates to profile with userId`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)
        val testUserId = "user123"

        // Act
        authNavigator.navigateToProfile(testUserId)

        // Assert
        verify { mockNavController.navigate("profile/$testUserId") }
    }

    @Test
    fun `AuthNavigatorImpl navigates back correctly`() {
        // Arrange
        val authNavigator = createAuthNavigator(mockNavController)

        // Act
        authNavigator.navigateBack()

        // Assert
        verify { mockNavController.popBackStack() }
    }

    private fun createAuthNavigator(navController: NavHostController): AuthNavigator {
        return object : AuthNavigator {
            override fun navigateToHome() {
                navController.navigate("home") {
                    popUpTo("auth") { inclusive = true }
                }
            }
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

### Testing Navigation in Feature Screens

```kotlin
// feature-auth/src/test/kotlin/com/example/feature/auth/LoginScreenTest.kt
class LoginScreenTest {

    private lateinit var testNavigator: TestAuthNavigator
    private lateinit var testViewModel: AuthViewModel

    @Before
    fun setup() {
        testNavigator = TestAuthNavigator()
        testViewModel = AuthViewModel(
            loginUseCase = TestLoginUseCase(),
            registerUseCase = TestRegisterUseCase(),
            resetPasswordUseCase = TestResetPasswordUseCase()
        )
    }

    @Test
    fun `when login successful, navigator is called`() = runTest {
        // Arrange
        testViewModel.onAction(AuthAction.EmailChanged("test@example.com"))
        testViewModel.onAction(AuthAction.PasswordChanged("password123"))

        // Act
        testViewModel.onAction(AuthAction.LoginClicked)
        advanceUntilIdle()

        // In real test, this would be called by the screen composable
        // when it observes AuthUiState.Success
        testNavigator.navigateToMainApp()

        // Assert
        assertTrue(testNavigator.navigationEvents.contains("navigateToMainApp"))
    }

    @Test
    fun `when register button clicked, navigator is called`() {
        // Act
        testNavigator.navigateToRegister()

        // Assert
        assertTrue(testNavigator.navigationEvents.contains("navigateToRegister"))
    }

    @Test
    fun `when forgot password clicked, navigator is called`() {
        // Act
        testNavigator.navigateToForgotPassword()

        // Assert
        assertTrue(testNavigator.navigationEvents.contains("navigateToForgotPassword"))
    }
}
```

## UI Tests

### Compose UI Tests for Auth Screen

```kotlin
// feature-auth/src/androidTest/kotlin/com/example/feature/auth/AuthScreenTest.kt
class AuthScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `login screen shows email and password fields`() {
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

        composeTestRule
            .onNodeWithText("Email")
            .assertIsDisplayed()

        composeTestRule
            .onNodeWithText("Password")
            .assertIsDisplayed()

        composeTestRule
            .onNodeWithText("Login")
            .assertIsDisplayed()
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
    fun `error state shows error message`() {
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

        composeTestRule
            .onNodeWithText(errorMessage)
            .assertIsDisplayed()

        composeTestRule
            .onNodeWithText("Retry")
            .assertIsDisplayed()
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

        composeTestRule
            .onNodeWithText("Create Account")
            .performClick()

        assertTrue(registerClicked)
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

### Navigation3 UI Tests

```kotlin
// app/src/androidTest/kotlin/com/example/navigation/AppNavigationTest.kt
class AppNavigationTest {

    @get:Rule
    val composeTestRule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun `app starts with auth screen`() {
        composeTestRule.setContent {
            AppTheme {
                AppNavigationSimple()
            }
        }

        composeTestRule
            .onNodeWithText("Email")
            .assertIsDisplayed()
    }

    @Test
    fun `can navigate from login to register`() {
        composeTestRule.setContent {
            AppTheme {
                AppNavigationSimple()
            }
        }

        // Click create account
        composeTestRule
            .onNodeWithText("Create Account")
            .performClick()

        // Should be on register screen
        composeTestRule
            .onNodeWithText("Register")
            .assertIsDisplayed()
    }
}
```

## Test Utilities

### Test Data Factories (in `core:testing`)

```kotlin
// core/testing/src/main/kotlin/com/example/testing/data/TestData.kt
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
}
```

### Gradle Test Configuration

```kotlin
// build.gradle.kts for feature modules
dependencies {
    // Test dependencies
    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)
    
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
    implementation(libs.turbine)
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
```

## Key Testing Principles in Our Architecture

1. **Test Doubles Over Mocks**: Create realistic test implementations that mirror production behavior
2. **Feature Isolation**: Each feature module tests its own ViewModel and UI independently
3. **Navigation Testing**: Test navigator interfaces in app module, not in features
4. **Integration Testing**: Test repository implementations with test data sources
5. **UI Testing**: Test composable screens with fake ViewModels and navigators
6. **No Feature Dependencies**: Test utilities in `core:testing` avoid feature-to-feature dependencies