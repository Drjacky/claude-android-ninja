# Android StrictMode (Compose + Multi-Module)

StrictMode is a three-tier guardrail in modern Compose apps:
1) classic thread/VM checks, 2) Compose compiler stability diagnostics, 3) CI guardrails.

## 1) Classic StrictMode (Thread + VM)

Initialize in `Application` for debug builds. Keep it app-level only.

```kotlin
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        if (BuildConfig.DEBUG) {
            StrictMode.setThreadPolicy(
                StrictMode.ThreadPolicy.Builder()
                    .detectAll()
                    .penaltyLog()
                    .penaltyFlashScreen() // Visual feedback during development.
                    .build()
            )
            StrictMode.setVmPolicy(
                StrictMode.VmPolicy.Builder()
                    .detectLeakedSqlLiteObjects() // Detects SQLite cursor objects that have not been closed.
                    .detectLeakedClosableObjects() // Detects when Closeable objects are not closed.
                    // .detectActivityLeaks() // Detects Activity object leaks.
                    // .detectFileUriExposure() // Detects when a file:// URI is exposed outside the app.
                    // .detectCleartextNetwork() // Detects unencrypted network traffic (HTTP instead of HTTPS).
                    // .detectUnsafeIntentLaunch() // Detects unsafe intent launches.
                    // or .detectAll() for all VM policy checks
                    .penaltyLog()
                    .build()
            )
        }
    }
}
```

### ThreadPolicy Options

- `detectAll()` - Enables all thread policy checks.
- `detectDiskReads()` - Detects reading data from disk.
- `detectDiskWrites()` - Detects writing data to disk.
- `detectNetwork()` - Detects network operations (HTTP requests, etc.).
- `detectCustomSlowCalls()` - Detects slow operations (e.g., SQLite queries).
- `permitAll()` - Disables all thread policy detections.

### VmPolicy Options

- `detectAll()` - Enables all VM policy checks.
- `detectActivityLeaks()` - Detects Activity object leaks.
- `detectLeakedClosableObjects()` - Detects when Closeable objects are not closed properly.
- `detectLeakedSqlLiteObjects()` - Detects SQLite cursor objects that have not been closed.
- `detectFileUriExposure()` - Detects when a file:// URI is exposed outside the app.
- `detectCleartextNetwork()` - Detects unencrypted network traffic (HTTP instead of HTTPS).
- `detectUnsafeIntentLaunch()` - Detects unsafe intent launches.

## 2) Compose Stability Guardrails

Enable compiler reports + metrics for Compose stability diagnostics.

```kotlin
// module build.gradle.kts
composeCompiler {
    metricsDestination = layout.buildDirectory.dir("compose_metrics")
    reportsDestination = layout.buildDirectory.dir("compose_reports")
    enableStrongSkippingMode = true
    stabilityConfigurationFile = rootProject.file("compose-stability.conf")
}
```

`compose-stability.conf` example:

```text
kotlin.collections.*
com.external.library.models.*
```

## 3) CI Guardrails

Fail CI on stability regressions by parsing Compose reports in a custom Gradle task
or CI job. Keep this in build logic or CI configuration, not in feature modules.

## Uploading StrictMode Signals to Crash Reporters

StrictMode uses `.penaltyLog()` to emit violations to Logcat. To ship these
signals to crash providers, enable log/breadcrumb capture:

- **Sentry**: enable logs in init (`options.logs.isEnabled = true`).
- **Firebase Crashlytics**: use Analytics + Crashlytics logging for breadcrumbs.

See `references/crashlytics.md` for provider initialization and wiring.

## References

- https://developer.android.com/reference/android/os/StrictMode
