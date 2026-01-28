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
        } else {
            // Production: silent collection
            StrictMode.setVmPolicy(
                StrictMode.VmPolicy.Builder()
                    .detectLeakedClosableObjects()
                    .detectActivityLeaks()
                    // Use penaltyListener to ship violations to your crash reporter
                    .penaltyListener(mainExecutor) { violation ->
                        // Ship to Firebase Crashlytics, Sentry, etc.
                        FirebaseCrashlytics.getInstance().recordException(violation)
                    }
                    // Or use penaltyDropBox() for system-level logging
                    // .penaltyDropBox()
                    .build()
            )
        }
    }
}
```

**Production penalties:**
- `penaltyListener(executor, listener)` - Custom handling, ship to crash reporters
- `penaltyDropBox()` - Logs to system DropBoxManager (accessible via `adb shell dumpsys dropbox`)
- Avoid `penaltyDeath()` or `penaltyLog()` in production (crashes users or spam logs)

**When to use production StrictMode:**
- Collecting violation data from beta testers or internal builds
- Monitoring memory leaks in production (sample 1-5% of users)
- Verifying fixes are working in the wild

**See also:** `references/crashlytics.md` for crash reporter integration.

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

### Penalty Options

- `penaltyLog()` - Logs violations to Logcat. By Default, use this option.
- `penaltyDeath()` - Crashes the app on violation (useful for catching issues during development).
- `penaltyFlashScreen()` - Flashes the screen on violation (visual feedback).
- `penaltyDropBox()` - Logs violations to DropBoxManager for system-level tracking.

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

### Stability Configuration File

Create `compose-stability.conf` in your **root project directory** to mark external types as stable.

**Why use this?** Third-party libraries or generated code may have immutable types that aren't annotated with `@Stable` or `@Immutable`. Without annotation, Compose treats them as unstable, causing unnecessary recompositions.

**Common patterns to include:**

`compose-stability.conf`:
```text
// Kotlin immutable collections (mark all as stable)
kotlin.collections.*

// Kotlinx immutable collections
org.jetbrains.kotlinx.collections.immutable.*

// Third-party library models
com.external.library.models.*

// Generated data classes (e.g., from protobuf, Room)
com.example.data.generated.*
```

**When to add types:**
- External library data classes that are immutable but not annotated
- Generated code (Room entities, proto messages) that you control immutability for
- Sealed hierarchies from dependencies
- Value classes from third-party SDKs

**When NOT to add types:**
- Your own code (annotate directly with `@Stable`/`@Immutable`)
- Mutable types (this will cause bugs!)
- Types you're unsure about (verify immutability first)

### Analyzing Compose Metrics

After building, review the generated metrics:

```bash
# View unstable composables
cat build/compose_reports/module_composables.txt

# View detailed stability info
cat build/compose_reports/module_classes.txt
```

Look for:
- `unstable` parameters (mutable or unrecognized types)
- `skippable: false` composables (recompose unnecessarily)
- High `groups` counts (complex composition structure)

## 3) CI Guardrails (Optional)

See: `references/android-performance.md` → "Compose Stability Validation (Optional)".

## Uploading StrictMode Signals to Crash Reporters

**For debug builds:** StrictMode uses `.penaltyLog()` to emit violations to Logcat.

**For production/beta builds:** Use `.penaltyListener()` to ship violations directly to crash reporters:

```kotlin
StrictMode.setVmPolicy(
    StrictMode.VmPolicy.Builder()
        .detectLeakedClosableObjects()
        .penaltyListener(mainExecutor) { violation ->
            // Ship to Firebase Crashlytics:
            FirebaseCrashlytics.getInstance().recordException(violation)
            // Or ship to Sentry:
            Sentry.captureException(violation)
        }
        .build()
)
```

Alternatively, enable log/breadcrumb capture in your crash reporter to automatically collect `penaltyLog()` output:

- **Sentry**: enable logs in init (`options.logs.isEnabled = true`).
- **Firebase Crashlytics**: use Analytics + Crashlytics logging for breadcrumbs.

See `references/crashlytics.md` for provider initialization and wiring.

## References

- https://developer.android.com/reference/android/os/StrictMode
