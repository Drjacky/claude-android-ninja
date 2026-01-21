# Crash Reporting (Firebase Crashlytics / Sentry)

This guide shows how to integrate crash reporting in a **modular** Android app so the provider (Firebase Crashlytics or Sentry) can be swapped without touching feature code.

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

Keep logging in ViewModels or use delegated helpers (see `references/kotlin-delegation.md`).

```kotlin
@HiltViewModel
class LoginViewModel @Inject constructor(
    private val crashReporter: CrashReporter
) : ViewModel() {
    fun onLoginFailed(error: Throwable) {
        crashReporter.recordException(
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
  - Firebase Crashlytics setup: https://firebase.google.com/docs/crashlytics/android/get-started
  - Crashlytics + Compose example: https://firebase.blog/posts/2022/06/adding-crashlytics-to-jetpack-compose-app/
  - Sentry + Compose integration: https://docs.sentry.io/platforms/android/integrations/jetpack-compose/
