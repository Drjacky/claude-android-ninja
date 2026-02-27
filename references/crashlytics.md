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
        val user = User().apply { this.id = id }
        Sentry.setUser(user)
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
        context.forEach { (k, v) -> Sentry.setTag(k, v) }
        Sentry.captureException(throwable)
    }
}
```

## Sentry Setup (Convention Plugin + Compose)

Use the Sentry convention plugin for automatic setup. It applies the Gradle plugins, adds the Sentry SDK, and configures Compose integration.

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.sentry)
}
```

The `app.sentry` convention plugin (from `templates/convention/SentryConventionPlugin.kt`) automatically:
- Applies `io.sentry.android.gradle` plugin (auto-adds core SDK, uploads mapping files)
- Applies `io.sentry.kotlin.compiler.gradle` plugin (automatic @Composable tagging)
- Adds `sentry-android` dependency
- Adds `sentry-compose-android` dependency for Jetpack Compose integration

**Manual setup (if not using convention plugin):**

```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.sentry.android)
    alias(libs.plugins.sentry.kotlin.compiler)
}

dependencies {
    implementation(libs.sentry.android)
    implementation(libs.sentry.compose.android)
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
            
            // Profiling configuration:
            // profilesSampleRate: % of transactions to profile (requires tracesSampleRate > 0)
            // Use this for production profiling of sampled transactions
            options.profilesSampleRate = 1.0
            
            // Alternative: profileSessionSampleRate profiles % of sessions (not transactions)
            // Only use ONE of profilesSampleRate OR profileSessionSampleRate, not both
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

## Firebase Crashlytics Setup (Convention Plugin + Compose)

Use the Firebase convention plugin for automatic setup. The separate `-ktx` artifact is no longer required with the Firebase BoM.

```kotlin
// app/build.gradle.kts
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.firebase)
}
```

The `app.firebase` convention plugin (from `templates/convention/FirebaseConventionPlugin.kt`) automatically:
- Applies `com.google.gms.google-services` plugin
- Applies `com.google.firebase.crashlytics` plugin
- Adds Firebase BoM dependency (version managed centrally)
- Adds `firebase-analytics` and `firebase-crashlytics` libraries
- Configures native symbol uploads and debug build settings

**Manual setup (if not using convention plugin):**

```kotlin
// build.gradle.kts (project-level)
plugins {
    alias(libs.plugins.google.services) apply false
    alias(libs.plugins.firebase.crashlytics) apply false
}

// app/build.gradle.kts
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.google.services)
    alias(libs.plugins.firebase.crashlytics)
}

dependencies {
    val bom = libs.firebase.bom
    implementation(platform(bom))
    implementation(libs.firebase.analytics)
    implementation(libs.firebase.crashlytics)
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
See the centralized navigation setup in `references/android-navigation.md`.

```kotlin
@Composable
fun AppNavigation(
    analytics: Analytics // Injected via Hilt
) {
    val navigationState = rememberNavigationState(
        startRoute = TopLevelRoute.Auth,
        topLevelRoutes = setOf(
            TopLevelRoute.Auth,
            TopLevelRoute.Profile,
            TopLevelRoute.Settings
        )
    )

    LaunchedEffect(navigationState.topLevelRoute) {
        val currentStack = navigationState.backStacks[navigationState.topLevelRoute]
        val currentRoute = currentStack?.last()
        currentRoute?.let { route ->
            analytics.logScreenView(
                screenName = route::class.simpleName ?: "Unknown",
                screenClass = "MainActivity"
            )
        }
    }

    val entryProvider = entryProvider {
        authGraph(/* navigator */)
        profileGraph(/* navigator */)
        settingsGraph(/* navigator */)
    }

    NavDisplay(
        entries = navigationState.toEntries(entryProvider),
        onBack = { navigator.goBack() }
    )
}
```

### Capturing UI State (Delegation)

Use delegation to standardize custom keys and logs across ViewModels. See `references/kotlin-delegation.md` for more patterns.

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
    crashReporter: CrashReporter, // No private - delegated only
    logger: CrashlyticsStateLogger // No private - delegated only
) : ViewModel(), 
    CrashReporter by crashReporter,
    CrashlyticsStateLogger by logger {

    fun onRoleSelected(role: String) {
        logUiState("auth_role", role)
        logAction("Auth role selected: $role")
    }
    
    fun onLoginFailed(error: Throwable) {
        recordException(
            error,
            mapOf("action" to "login", "screen" to "auth")
        )
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

Use DI bindings to switch providers without changing feature code.

### Using Firebase Crashlytics

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class CrashReporterModule {
    @Binds
    abstract fun bindCrashReporter(
        impl: FirebaseCrashReporter
    ): CrashReporter
    
    @Provides
    @Singleton
    fun provideFirebaseCrashlytics(): FirebaseCrashlytics =
        FirebaseCrashlytics.getInstance()
}
```

Apply the Firebase convention plugin in `app/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.firebase)
}
```

### Using Sentry

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class CrashReporterModule {
    @Binds
    abstract fun bindCrashReporter(
        impl: SentryCrashReporter
    ): CrashReporter
}
```

Apply the Sentry convention plugin in `app/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.sentry)
}
```

**Switching providers:** Simply change the binding and convention plugin. Feature modules remain unchanged.

## Best Practices

- **Initialize once** in the app module.
- **Avoid PII** in tags and logs; keep user identifiers minimal. Use data scrubbing for sensitive information.
- **Use sampling** for performance tracing/profiling if enabled.
- **Send non-fatal errors intentionally**: log only what helps debugging.
- **Quality breadcrumbs**: Focus on user actions and state changes, not internal implementation details.
- **Upload mapping files**: Ensure ProGuard/R8 mappings are uploaded for symbolicated stack traces.

## ProGuard/R8 Mapping Upload

Both providers require mapping file upload for symbolicated crashes in release builds. See [gradle-setup.md](gradle-setup.md#r8--proguard-configuration) for R8 build configuration and `templates/proguard-rules.pro.template` for all keep rules.

### Firebase Crashlytics

The Firebase Crashlytics Gradle plugin automatically uploads mapping files during the build. No additional keep rules needed - apply the convention plugin and enable minification:

```kotlin
plugins {
    alias(libs.plugins.app.firebase)
}
```

### Sentry

The Sentry Gradle plugin handles mapping upload automatically. Configure it in the app module:

```kotlin
plugins {
    alias(libs.plugins.app.sentry)
}

sentry {
    includeSourceContext.set(true)
    autoInstallation.sentryVersion.set(libs.versions.sentry.get())
    includeProguardMapping.set(true)
    autoUploadProguardMapping.set(true)
    org.set("your-org")
    projectName.set("your-project")
    authToken.set(System.getenv("SENTRY_AUTH_TOKEN"))
}

## Breadcrumb Best Practices

Good breadcrumbs help reconstruct user actions leading to a crash. Bad breadcrumbs create noise.

### Good Breadcrumbs (User Actions & State Changes)

```kotlin
// User navigation
Sentry.addBreadcrumb(Breadcrumb().apply {
    message = "User navigated to profile screen"
    category = "navigation"
    level = SentryLevel.INFO
})

// User interactions
Sentry.addBreadcrumb(Breadcrumb().apply {
    message = "User clicked logout button"
    category = "ui.click"
    level = SentryLevel.INFO
    data = mapOf("button_id" to "logout_btn")
})

// Important state changes
Sentry.addBreadcrumb(Breadcrumb().apply {
    message = "Auth state changed to logged out"
    category = "state"
    level = SentryLevel.INFO
})
```

### Bad Breadcrumbs (Too Much Noise)

```kotlin
// Don't: Internal implementation details
Sentry.addBreadcrumb("Coroutine launched on IO dispatcher") // ❌

// Don't: Every method call
Sentry.addBreadcrumb("getUserId() called") // ❌

// Don't: Verbose data dumps
Sentry.addBreadcrumb("User data: $entireUserObject") // ❌ (also PII risk)
```

### Automatic Navigation Breadcrumbs

Both providers automatically track navigation in Jetpack Compose with Navigation library. For custom breadcrumbs, add them in the app-level navigation coordinator.

## Network Request Tracking

### Failed Network Requests

Track failed API calls to understand network-related crashes.

```kotlin
// In OkHttp interceptor or repository layer
class AuthRepository @Inject constructor(
    crashReporter: CrashReporter // No private - delegated only
) : CrashReporter by crashReporter {
    suspend fun login(email: String, password: String): Result<AuthToken> {
        return try {
            val response = authApi.login(email, password)
            Result.success(response)
        } catch (e: IOException) {
            // Network error
            log("Network error during login: ${e.message}")
            recordException(e, mapOf(
                "endpoint" to "auth/login",
                "error_type" to "network"
            ))
            Result.failure(e)
        } catch (e: HttpException) {
            // HTTP error (4xx, 5xx)
            log("HTTP error during login: ${e.code()}")
            recordException(e, mapOf(
                "endpoint" to "auth/login",
                "status_code" to e.code().toString(),
                "error_type" to "http"
            ))
            Result.failure(e)
        }
    }
}
```

**Note**: For Sentry with OkHttp, use `sentry-okhttp` integration for automatic network breadcrumbs: https://docs.sentry.io/platforms/android/integrations/okhttp/

## Testing Crash Reporting

### Test Crashes in Development

Add a debug-only method to test crash reporting:

```kotlin
@HiltViewModel
class DebugViewModel @Inject constructor(
    crashReporter: CrashReporter // No private - delegated only
) : ViewModel(), CrashReporter by crashReporter {
    
    // Only available in debug builds
    fun testCrash() {
        if (BuildConfig.DEBUG) {
            // Test non-fatal exception
            recordException(
                RuntimeException("Test crash from debug menu"),
                mapOf("test" to "true", "source" to "debug_menu")
            )
            
            // Test fatal crash (uncomment to test)
            // throw RuntimeException("Test fatal crash")
        }
    }
}

// In your debug/settings screen
@Composable
fun DebugScreen(viewModel: DebugViewModel = hiltViewModel()) {
    Button(onClick = { viewModel.testCrash() }) {
        Text("Test Non-Fatal Crash")
    }
}
```

### Disable Crash Reporting in Debug (Optional)

To avoid polluting production data with debug crashes:

**Firebase:**
```xml
<application>
  <meta-data
    android:name="firebase_crashlytics_collection_enabled"
    android:value="false" 
  />
</application>
```

Enable at runtime:
```kotlin
if (BuildConfig.DEBUG) {
    FirebaseCrashlytics.getInstance().setCrashlyticsCollectionEnabled(false)
}
```

**Sentry:**
```kotlin
SentryAndroid.init(this) { options ->
    options.environment = if (BuildConfig.DEBUG) "debug" else "production"
    // Optional: disable entirely in debug
    options.dsn = if (BuildConfig.DEBUG) "" else "YOUR_DSN_HERE"
}
```

## Data Scrubbing (Privacy/GDPR)

Remove sensitive information before sending to crash reporters.

### Built-in Scrubbing (Sentry)

Sentry automatically scrubs common PII fields:

```kotlin
SentryAndroid.init(this) { options ->
    // Disable automatic PII scrubbing if you need custom control
    options.sendDefaultPii = false
    
    // Add custom data scrubbing
    options.setBeforeSend { event, hint ->
        // Scrub email addresses from exception messages
        event.message?.message = event.message?.message?.replace(
            Regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"),
            "[REDACTED_EMAIL]"
        )
        
        // Remove specific tags that might contain PII
        event.removeTag("user_email")
        event.removeExtra("raw_user_data")
        
        event
    }
}
```

### Custom Scrubbing for Both Providers

Implement scrubbing in your `CrashReporter` wrapper:

```kotlin
class PrivacyAwareCrashReporter @Inject constructor(
    crashReporter: CrashReporter // No private - delegated only
) : CrashReporter by crashReporter {
    
    private val emailRegex = Regex("[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}")
    private val sensitiveKeys = setOf("password", "token", "secret", "key", "auth")
    
    override fun recordException(
        throwable: Throwable,
        context: Map<String, String>
    ) {
        // Scrub context
        val scrubbedContext = context.filterKeys { key ->
            !sensitiveKeys.any { key.contains(it, ignoreCase = true) }
        }.mapValues { (_, value) ->
            value.replace(emailRegex, "[REDACTED_EMAIL]")
        }
        
        // Use super to call the delegated implementation
        super.recordException(throwable, scrubbedContext)
    }
    
    override fun log(message: String) {
        val scrubbedMessage = message.replace(emailRegex, "[REDACTED_EMAIL]")
        super.log(scrubbedMessage)
    }
}
```

Wire it in DI:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class CrashReporterModule {
    @Binds
    abstract fun bindCrashReporter(
        impl: PrivacyAwareCrashReporter
    ): CrashReporter
    
    @Provides
    @Singleton
    fun providePrivacyAwareCrashReporter(
        @Named("raw") rawReporter: CrashReporter
    ): PrivacyAwareCrashReporter = PrivacyAwareCrashReporter(rawReporter)
    
    @Provides
    @Singleton
    @Named("raw")
    fun provideRawCrashReporter(): CrashReporter = FirebaseCrashReporter(
        FirebaseCrashlytics.getInstance()
    )
}
```

## Gradle & Setup Guidance

- Keep SDK dependencies in the version catalog (`templates/libs.versions.toml.template`).
- Follow `references/gradle-setup.md` for plugin configuration patterns.
- For provider-specific setup, follow the official docs:
  - Sentry Android install and configuration: https://docs.sentry.io/platforms/android/
  - Sentry manual setup + plugin details: https://docs.sentry.io/platforms/android/manual-setup/
  - Firebase Crashlytics setup: https://firebase.google.com/docs/crashlytics/android/get-started
  - Crashlytics + Compose example: https://firebase.blog/posts/2022/06/adding-crashlytics-to-jetpack-compose-app/
  - Sentry + Compose integration: https://docs.sentry.io/platforms/android/integrations/jetpack-compose/
