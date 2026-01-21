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
class SentryCrashReporter @Inject constructor(
    private val hub: IHub
) : CrashReporter {
    override fun setUserId(id: String?) {
        hub.setUser { user ->
            user.id = id
        }
    }

    override fun setUserProperty(key: String, value: String) {
        hub.setTag(key, value)
    }

    override fun log(message: String) {
        hub.addBreadcrumb(message)
    }

    override fun recordException(
        throwable: Throwable,
        context: Map<String, String>
    ) {
        hub.withScope { scope ->
            context.forEach { (k, v) -> scope.setTag(k, v) }
            hub.captureException(throwable)
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
