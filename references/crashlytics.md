# Crash Reporting (Firebase Crashlytics / Sentry)

This guide shows how to integrate crash reporting in a **modular** Android app so the provider (Firebase Crashlytics or Sentry)
can be swapped without touching feature code.

## Goals

- Keep SDK-specific code **out of feature modules**
- Use an interface in `core` and inject implementations
- Allow easy provider swaps or dual reporting

## Architecture Placement

**Recommended modules:**

- `core:domain` (or `core:common`): interfaces and event models
- `core:data` (or `core:analytics`): SDK-specific implementations
- `app`: provider initialization and wiring

## Provider-Agnostic Interface

```kotlin
// core/domain/analytics/CrashReporter.kt
interface CrashReporter {
    fun setUserId(id: String?)
    fun setUserProperty(key: String, value: String)
    fun log(message: String)
    fun recordException(throwable: Throwable, context: Map<String, String> = emptyMap())
}
```

## Implementation Examples

### Firebase Crashlytics

```kotlin
// core/data/analytics/FirebaseCrashReporter.kt
class FirebaseCrashReporter @Inject constructor(
    private val crashlytics: FirebaseCrashlytics
) : CrashReporter {
    override fun setUserId(id: String?) {
        crashlytics.setUserId(id ?: "")
    }

    override fun setUserProperty(key: String, value: String) {
        crashlytics.setCustomKey(key, value)
    }

    override fun log(message: String) {
        crashlytics.log(message)
    }

    override fun recordException(
        throwable: Throwable,
        context: Map<String, String>
    ) {
        context.forEach { (k, v) -> crashlytics.setCustomKey(k, v) }
        crashlytics.recordException(throwable)
    }
}
```

### Sentry

```kotlin
// core/data/analytics/SentryCrashReporter.kt
class SentryCrashReporter @Inject constructor() : CrashReporter {
    override fun setUserId(id: String?) {
        Sentry.configureScope { scope ->
            scope.user = User().apply { this.id = id }
        }
    }

    override fun setUserProperty(key: String, value: String) {
        Sentry.setTag(key, value)
    }

    override fun log(message: String) {
        Sentry.addBreadcrumb(message)
    }

    override fun recordException(
        throwable: Throwable,
        context: Map<String, String>
    ) {
        Sentry.withScope { scope ->
            context.forEach { (k, v) -> scope.setTag(k, v) }
            Sentry.captureException(throwable)
        }
    }
}
```

## Sentry Setup (Plugin + Compose)

Use the Gradle plugin for setup; it auto-adds the core SDK and configures uploads.

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.sentry.android)
    alias(libs.plugins.sentry.kotlin.compiler)
}

dependencies {
    implementation(libs.sentry.compose.android)
    // The Sentry plugin automatically adds the core SDK.
}
```

### Manifest Configuration

Sentry uses a ContentProvider for auto-initialization. Configure via `AndroidManifest.xml`.

```xml
<application>
    <meta-data android:name="io.sentry.dsn" android:value="YOUR_DSN_HERE" />
    <meta-data android:name="io.sentry.traces.sample-rate" android:value="1.0" />
    <meta-data android:name="io.sentry.traces.user-interaction.enable" android:value="true" />
    <meta-data android:name="io.sentry.attach-view-hierarchy" android:value="true" />
    <meta-data android:name="io.sentry.attach-screenshot" android:value="true" />
</application>
```

### Application Initialization (Sentry)

Enable logs so StrictMode `.penaltyLog()` events can be shipped.

```kotlin
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        SentryAndroid.init(this) { options ->
            options.dsn = "YOUR_DSN_HERE"
            options.logs.isEnabled = true
            options.environment = if (BuildConfig.DEBUG) "debug" else "production"
            options.release = BuildConfig.VERSION_NAME
            options.tracesSampleRate = 1.0
            // options.tracesSampler = { 0.2 } // Prefer sampler when you need dynamic control.
            // options.tracePropagationTargets = listOf("api.example.com", "https://auth.example.com")
            // options.propagateTraceparent = true
            // options.traceOptionsRequests = false
            options.profilesSampleRate = 1.0
            // options.profileSessionSampleRate = 0.2
            // options.profileLifecycle = SentryOptions.ProfileLifecycle.TRACE
            // options.startProfilerOnAppStart = true
            options.enableAutoSessionTracking = true
            options.sendDefaultPii = false
            // options.sampleRate = 1.0 // Error event sampling.
            // options.maxBreadcrumbs = 100
            // options.attachStacktrace = true
            // options.attachThreads = false
            // options.collectAdditionalContext = true
            // options.inAppIncludes = listOf("com.example")
            // options.inAppExcludes = listOf("com.example.core.testing")
        }
    }
}
```

### Jetpack Compose Specifics

- **Automatic navigation tracking**: With `androidx.navigation`, Sentry records navigation breadcrumbs and transactions automatically via the plugin.
- **Automatic @Composable tagging**: The `sentry-kotlin-compiler` plugin tags composables based on function names (no manual `Modifier.sentryTag()` needed).
- **Manual tracing for critical screens**: Wrap key content with `SentryTraced`.

```kotlin
import io.sentry.compose.SentryTraced

@Composable
fun AuthProfileScreen(userId: String) {
    SentryTraced(name = "auth_profile_screen") {
        Column {
            Text("User: $userId")
        }
    }
}
```

## Firebase Crashlytics Setup (Plugin + Compose)

Use the Gradle plugin and Firebase BoM. The separate `-ktx` artifact is no longer required.

```kotlin
// build.gradle.kts (project-level)
plugins {
    id("com.google.gms.google-services") version "4.4.2" apply false
    id("com.google.firebase.crashlytics") version "3.0.6" apply false
}
```

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    id("com.google.gms.google-services")
    id("com.google.firebase.crashlytics")
}

dependencies {
    implementation(platform("com.google.firebase:firebase-bom:34.8.0"))
    implementation("com.google.firebase:firebase-crashlytics")
    implementation("com.google.firebase:firebase-analytics") // Breadcrumbs + screen tracking
}
```

### Application Initialization (Firebase)

```kotlin
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        FirebaseApp.initializeApp(this)
    }
}
```

### Compose Screen Tracking (Navigation3)

Crashlytics breadcrumbs do not automatically include Compose destination names.
Log screen transitions in the **app-level** `AppNavigation()` coordinator.
See the centralized navigation setup in `references/modularization.md`.

```kotlin
@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val analytics = Firebase.analytics
    val backStackEntry by navController.currentBackStackEntryAsState()

    LaunchedEffect(backStackEntry) {
        val route = backStackEntry?.destination?.route ?: return@LaunchedEffect
        analytics.logEvent(FirebaseAnalytics.Event.SCREEN_VIEW) {
            param(FirebaseAnalytics.Param.SCREEN_NAME, route)
            param(FirebaseAnalytics.Param.SCREEN_CLASS, "MainActivity")
        }
    }

    NavHost(navController, startDestination = "auth/login") {
        composable("auth/login") { AuthLoginScreen() }
        composable("auth/forgot-password") { ForgotPasswordScreen() }
        composable("auth/profile") { AuthProfileScreen() }
    }
}
```

### Capturing UI State (Delegation)

Use delegation to standardize custom keys and logs across ViewModels.

```kotlin
interface CrashlyticsStateLogger {
    fun logUiState(key: String, value: String)
    fun logAction(message: String)
}

class FirebaseCrashlyticsStateLogger @Inject constructor(
    private val crashlytics: FirebaseCrashlytics
) : CrashlyticsStateLogger {
    override fun logUiState(key: String, value: String) {
        crashlytics.setCustomKey(key, value)
    }

    override fun logAction(message: String) {
        crashlytics.log(message)
    }
}

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle,
    logger: CrashlyticsStateLogger
) : ViewModel(), CrashlyticsStateLogger by logger {

    fun onRoleSelected(role: String) {
        logUiState("auth_role", role)
        logAction("Auth role selected: $role")
    }
}
```

### Non-fatal Exceptions in Coroutines

```kotlin
val crashHandler = CoroutineExceptionHandler { _, exception ->
    Firebase.crashlytics.recordException(exception)
}

viewModelScope.launch(crashHandler) {
    repository.refreshSession()
}
```

## Wiring in the App Module

Use DI bindings to switch providers without recalling features:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class CrashReporterModule {
    @Binds
    abstract fun bindCrashReporter(
        impl: FirebaseCrashReporter
    ): CrashReporter
}
```

Swap to Sentry by binding `SentryCrashReporter` instead.

## Compose + ViewModel Usage

Use delegation for cross-cutting concerns (see `references/kotlin-delegation.md`) to keep ViewModels lean.

```kotlin
@HiltViewModel
class LoginViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle,
    crashReporter: CrashReporter
) : ViewModel(), CrashReporter by crashReporter {
    fun onLoginFailed(error: Throwable) {
        recordException(
            error,
            mapOf("action" to "login")
        )
    }
}
```

## Best Practices

- **Initialize once** in the app module.
- **Avoid PII** in tags and logs; keep user identifiers minimal.
- **Use sampling** for performance tracing/profiling if enabled.
- **Send non-fatal errors intentionally**: log only what helps debugging.

## Gradle & Setup Guidance

- Keep SDK dependencies in the version catalog (`templates/libs.versions.toml.template`).
- Follow `references/gradle-setup.md` for plugin configuration patterns.
- For provider-specific setup, follow the official docs:
  - Sentry Android install and configuration: https://docs.sentry.io/platforms/android/
  - Sentry manual setup + plugin details: https://docs.sentry.io/platforms/android/manual-setup/
  - Firebase Crashlytics setup: https://firebase.google.com/docs/crashlytics/android/get-started
  - Crashlytics + Compose example: https://firebase.blog/posts/2022/06/adding-crashlytics-to-jetpack-compose-app/
  - Sentry + Compose integration: https://docs.sentry.io/platforms/android/integrations/jetpack-compose/
