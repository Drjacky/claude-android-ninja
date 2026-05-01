# Android Performance

Required: measure with Macrobenchmark + Baseline Profiles before and after every change to startup, navigation, or list rendering. Track production via Play Vitals + Crashlytics/Sentry. Apply StrictMode guardrails ([android-strictmode.md](/references/android-strictmode.md)).

## Google Play Vitals and production targets

[Android vitals](https://developer.android.com/topic/performance/vitals) reports user-perceived crash rate, ANR rate, and slow-start metrics; exceeding bad-behavior thresholds reduces distribution and discovery.

### Core thresholds (Play Console)

Google publishes bad-behavior thresholds for **user-perceived** crash rate and ANR rate. Exceeding them can reduce distribution and discovery. Play Console help lists current values; historically the overall phone app bar is often stated around **1.09%** (crash rate) and **0.47%** (ANR rate). Per-device model buckets (and other form factors) can use different numbers.

| Metric                    | Typical overall threshold (verify in Play docs) | Notes                                  |
|---------------------------|-------------------------------------------------|----------------------------------------|
| User-perceived crash rate | Often cited around ~1.09% at overall tier       | Per phone model and watches may differ |
| User-perceived ANR rate   | Often cited around ~0.47% at overall tier       | Same: check model-specific rows        |

Use Vitals alongside Firebase Crashlytics or similar to see stack traces and release correlation.

### Optional: Play Vitals observability (Play Developer Reporting API)

This is **opt-in**. Use it when you explicitly want **Play Console-grade aggregates** (ANR rate, crash rate, slow start, stuck background wakelocks, error counts, and related metric sets) **automated in your repo and CI** - for example a daily **Slack** (or similar) summary so the team sees health **without opening Play Console**. It does **not** replace in-app crash reporting ([Crashlytics/Sentry](/references/crashlytics.md)); it complements it with **store-aggregated** signals.

The [Play Developer Reporting API](https://developers.google.com/play/developer/reporting/reference/rest) exposes the same families of metrics as the console: each metric set supports **`get`** (describe the set) and **`query`** with a **`TimelineSpec`** (for example **`DAILY`** aggregation; the API commonly expects timezone such as **`America/Los_Angeles`** for timeline bounds - follow the reference for current rules).

**Do not** put service account credentials or Reporting API calls inside the **`:app`** module or ship them in the APK. Align with this project's layout by implementing reporting as **Kotlin in `build-logic`** (or a small Gradle plugin module): a **`DefaultTask`** that queries the API and posts formatted output to Slack (Incoming Webhook or Slack Web API). That keeps secrets in **CI/environment variables** and leaves feature modules unchanged - see [modularization.md](/references/modularization.md) and [gradle-setup.md](/references/gradle-setup.md).

**Authentication:** use a Google Cloud **service account** with access to your Play Developer account; load JSON from an **environment variable** or CI secret (never commit keys). Request OAuth scope:

`https://www.googleapis.com/auth/playdeveloperreporting`

**Dependency:** add the generated client **`com.google.apis:google-api-services-playdeveloperreporting`** for API version **`v1beta1`**, with the revision pinned in **`gradle/libs.versions.toml`** (or `assets/libs.versions.toml.template` when creating a new project from this repo).

**Implementation sketch:** call **`query`** on the relevant metric set (for example crash rate, ANR rate) with your timeline and metric names; map **`MetricsRow`** results into small **Kotlin data classes** per set; optionally compare values to the **Core thresholds** table above for a simple green/yellow/red summary; format markdown or blocks for Slack.

#### Example (build-logic, schematic)

Keep all of this **outside** `:app` (for example under `build-logic/convention/` or a dedicated `build-logic/play-vitals/` module). Pin the client in the version catalog. **`build-logic/convention`** already includes **`kotlinx-coroutines-core`** for **`PlayVitalsReportingTask`**; add **`suspend`** + **`withContext`** usage in **`PlayVitalsRepository`** as shown below.

Version pins live in **`gradle/libs.versions.toml`**. Check [`assets/libs.versions.toml.template`](../assets/libs.versions.toml.template): **`googlePlayDeveloperReporting`**, **`googleAuthLibraryOauth2Http`**, and the **`google-api-services-playdeveloperreporting`** / **`google-auth-library-oauth2-http`** library aliases, then bump **`googlePlayDeveloperReporting`** when you adopt a newer generated client.

`build-logic` module `build.gradle.kts` - add these when you implement **`PlayVitalsRepository`** ( **`kotlinx-coroutines-core`** is already there for **`PlayVitalsReportingTask`**):

```kotlin
dependencies {
    implementation(libs.google.api.services.playdeveloperreporting)
    implementation(libs.google.auth.library.oauth2.http)
}
```

Domain-style models and a small repository: **suspend** functions perform HTTP on **`Dispatchers.IO`** (testable without a Gradle task). The generated client's **`execute()`** stays inside `withContext`.

```kotlin
// e.g. build-logic/.../reporting/AnrRateSummary.kt
data class AnrRateSummary(
    val dailyPercent: Float,
    val weighted7dPercent: Float,
    val weighted28dPercent: Float,
)

// e.g. build-logic/.../reporting/PlayVitalsRepository.kt
import com.google.api.client.googleapis.javanet.GoogleNetHttpTransport
import com.google.api.client.http.HttpRequestInitializer
import com.google.api.client.json.gson.GsonFactory
import com.google.api.services.playdeveloperreporting.Playdeveloperreporting
import com.google.api.services.playdeveloperreporting.model.GooglePlayDeveloperReportingV1beta1QueryAnrRateMetricSetRequest
import com.google.auth.http.HttpCredentialsAdapter
import com.google.auth.oauth2.GoogleCredentials
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private val PLAY_REPORTING_SCOPE = "https://www.googleapis.com/auth/playdeveloperreporting"

class PlayVitalsRepository(
    private val appName: String, // e.g. "apps/com.example.app" - resource name prefix for metric sets
    private val serviceAccountJson: String,
) {
    private val transport = GoogleNetHttpTransport.newTrustedTransport()
    private val jsonFactory = GsonFactory.getDefaultInstance()

    private val http: HttpRequestInitializer =
        HttpCredentialsAdapter(
            GoogleCredentials
                .fromStream(serviceAccountJson.byteInputStream())
                .createScoped(PLAY_REPORTING_SCOPE),
        )

    private val api: Playdeveloperreporting by lazy {
        Playdeveloperreporting.Builder(transport, jsonFactory, http)
            .setApplicationName("play-vitals-reporting")
            .build()
    }

    /** Returns null if the API returns no row (freshness lag, bad window) or on transport failure, do not fail the Gradle task. */
    suspend fun queryAnrRates(request: GooglePlayDeveloperReportingV1beta1QueryAnrRateMetricSetRequest): AnrRateSummary? =
        withContext(Dispatchers.IO) {
            val name = "$appName/anrRateMetricSet"
            val row = runCatching {
                api.vitals().anrrate().query(name, request).execute().rows?.firstOrNull()
            }.getOrElse { return@withContext null }
                ?: return@withContext null
            val byMetric = row.metrics.associate { metric ->
                metric.metric to (metric.decimalValue?.value?.toFloat()?.times(100f) ?: Float.NaN)
            }
            AnrRateSummary(
                dailyPercent = byMetric["anrRate"] ?: Float.NaN,
                weighted7dPercent = byMetric["anrRate7dUserWeighted"] ?: Float.NaN,
                weighted28dPercent = byMetric["anrRate28dUserWeighted"] ?: Float.NaN,
            )
        }
}
```

This runs only on the **build machine** (Gradle), not in the shipped app. Throwing **`error()`** / letting exceptions propagate would still **fail the task and can fail CI**. For optional health reporting, prefer **nullable / `Result`**, **`runCatching`**, Gradle **`logger.lifecycle` / `logger.warn`**, post "metrics unavailable" to Slack, and **return from `@TaskAction` without rethrowing** so the job exits successfully unless you explicitly want a red pipeline for misconfiguration.

Build a **`TimelineSpec`** (aggregation period, start/end in **`America/Los_Angeles`** as **`GoogleTypeDateTime`**) per the REST reference; reuse the same pattern for **`crashRateMetricSet`**, **`slowStartRateMetricSet`**, etc., changing the vitals client path and metric names.

**Gradle task entry point:** the canonical task body lives in **[`PlayVitalsReportingTask.kt`](../assets/convention/PlayVitalsReportingTask.kt)** - env check, then **`runBlocking { ... }`** with commented placeholders for **`PlayVitalsRepository`**, request, and Slack. Keep HTTP inside the repository's **`withContext(Dispatchers.IO)`** (avoid **`runBlocking(Dispatchers.IO)`** *and* another **`withContext(Dispatchers.IO)`** - pick one outer scope). Keep **`@TaskAction`** free of configuration-time work. **`build-logic/convention`** already depends on **`kotlinx-coroutines-core`** for **`runBlocking`**; add Reporting API artifacts when you uncomment the repository.

**Registration:** sources ship under **`assets/convention/`** ([`PlayVitalsReportingConventionPlugin.kt`](../assets/convention/PlayVitalsReportingConventionPlugin.kt), [`PlayVitalsReportingTask.kt`](../assets/convention/PlayVitalsReportingTask.kt)), registered in [`assets/convention/build.gradle.kts`](../assets/convention/build.gradle.kts). Add catalog plugin **`app-play-vitals`** from [`assets/libs.versions.toml.template`](../assets/libs.versions.toml.template) to **`gradle/libs.versions.toml`**. After you copy convention sources into **`build-logic`**, add **`alias(libs.plugins.app.play.vitals)`** to the **`plugins { }`** block in the **root** **`build.gradle.kts`**. Apply it there **only** (not in **`app`** or feature modules). For where to copy files, how the root block should look, and CI, see [gradle-setup.md](/references/gradle-setup.md) and [QUICK_REFERENCE.md](../assets/convention/QUICK_REFERENCE.md).

**CI/CD:** schedule a job (for example nightly) that runs `./gradlew <yourReportingTask>` and injects secrets at runtime: service account JSON, Slack token or webhook URL, and the **`apps/...`** resource name for the app you report on.

**Kotlin and coroutines:** Gradle tasks run on the build JVM; I/O belongs in **`@TaskAction`** (or a worker). Use **`suspend`** + **`withContext(Dispatchers.IO)`** in a dedicated class for clarity and tests; the task only **`runBlocking { … }`**. Avoid duplicate **`Dispatchers.IO`** if the task already uses **`runBlocking(Dispatchers.IO)`**. See [kotlin-patterns.md](/references/kotlin-patterns.md) and [coroutines-patterns.md](/references/coroutines-patterns.md). Avoid heavy work during **configuration** phase.

### Startup time (user experience)

Targets below are practical goals for **cold / warm / hot** start. If cold start routinely exceeds about **2 seconds** on mid-range hardware, show a splash or inline progress so the user sees feedback ([App Startup & Initialization](#app-startup--initialization)).

| Start type | Target (typical) | Investigate if worse than (rule of thumb) |
|------------|------------------|-------------------------------------------|
| Cold       | Under ~1 s       | ~2 s without progress UI                  |
| Warm       | Under ~500 ms    | ~1 s                                      |
| Hot        | Under ~100 ms    | ~500 ms                                   |

Align measurement with **TTID / TTFD** and Macrobenchmark `StartupTimingMetric()` (see below).

### Frame time and jank

Rendering should stay within the display's frame budget:

| Display | Frame budget (approx.) |
|---------|------------------------|
| 60 Hz   | ~16.7 ms per frame     |
| 90 Hz   | ~11.1 ms per frame     |
| 120 Hz  | ~8.3 ms per frame      |

**Slow frames** exceed the budget; **frozen frames** are long stalls (typically hundreds of ms or more). Investigate with `FrameTimingMetric()`, Perfetto, and Android Studio profilers.

### Background work and battery

Required:
- Use **WorkManager** for deferrable background work; foreground service only with a user-visible notification.
- Design for **Doze** and **App Standby**: batch work; use FCM for push.
- Release **WakeLocks** with timeouts; never hold partial wake locks across idle.

StrictMode and main-thread guardrails: [android-strictmode.md](/references/android-strictmode.md).

## Benchmark

Required: Macrobenchmark for end-to-end journeys (startup, scrolling, navigation). Microbenchmark for isolated code paths only.

### Macrobenchmark (Compose)

Use when:
- Investigating cold/warm start regressions.
- Measuring Compose navigation, list scrolling, or animation jank.
- Producing repeatable numbers for CI gating.

Module setup: see [gradle-setup.md](/references/gradle-setup.md) → "Benchmark Module (Optional)".

#### Compose Macrobenchmark Example
```kotlin
@RunWith(AndroidJUnit4::class)
class AuthStartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun coldStart() = benchmarkRule.measureRepeated(
        packageName = "com.example.app",
        metrics = listOf(StartupTimingMetric()),
        compilationMode = CompilationMode.Partial(),
        iterations = 5,
        startupMode = StartupMode.COLD
    ) {
        pressHome()
        startActivityAndWait()
    }
}
```

#### Macrobenchmark rules

- Use `CompilationMode.Partial()` to approximate Baseline Profile behavior when comparing changes.
- Use `StartupMode.COLD/WARM/HOT` to measure the scenario you care about.
- Keep actions in `measureRepeated` focused and deterministic (e.g., navigate to one screen, scroll one list).
- Wait for UI idleness with `device.waitForIdle()` between steps when needed.
- Use `FrameTimingMetric()` when measuring Compose list scroll or navigation jank.

#### Common Metrics
- `StartupTimingMetric()` for cold/warm start.
- `FrameTimingMetric()` for scrolling/jank.
- `MemoryUsageMetric()` for memory regressions.

#### Running Benchmarks
Use a **physical device** (emulators add noise). Disable system animations:
```bash
adb shell settings put global animator_duration_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global window_animation_scale 0
```

Run all benchmarks:
```bash
./gradlew :benchmark:connectedCheck
```

Run a single benchmark class:
```bash
./gradlew :benchmark:connectedAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.example.benchmark.AuthStartupBenchmark
```

#### Reports & Artifacts
Results are generated per device:
- `benchmark/build/outputs/connected_android_test_additional_output/` (JSON results)
- `benchmark/build/reports/androidTests/connected/` (HTML summary)

Use these in CI to detect regressions and track changes over time.

#### Custom System Tracing

Required: wrap app-level critical sections in `trace { }`. Macrobenchmark traces alone rarely surface in-app hotspots.

Use Tracing 2.0 (`tracing-wire-android`) for low overhead and Coroutine context propagation:
```kotlin
// app/build.gradle.kts
dependencies {
    implementation(libs.androidx.tracing.wire) // or libs.androidx.tracing
}
```

**Usage:**

Wrap the code you want to measure in a `trace` block:
```kotlin
import androidx.tracing.trace

fun processImage() {
    trace("processImage") {
        // Your work here will appear as a custom section in the system trace
        loadImage()
        sharpen()
    }
}
```

For Kotlin Coroutines, Tracing 2.0 supports context propagation to correctly visualize suspended and resumed tasks:
```kotlin
suspend fun taskOne(tracer: Tracer) {
    tracer.traceCoroutine(category = "main", "taskOne") {
        delay(100L)
    }
}
```

These custom sections will appear in the Perfetto trace when you run your Macrobenchmarks, allowing you to see exactly how long your specific methods take.

### Startup Performance Metrics (TTID & TTFD)

Android provides two key metrics for measuring app startup performance:

#### Time to Initial Display (TTID)
The time until the first frame is drawn. This is automatically measured by the system and reported in Logcat.

#### Time to Full Display (TTFD)
The time until your app is fully interactive with all critical content loaded. You must explicitly call `reportFullyDrawn()` to measure this.

#### ReportDrawn APIs (Compose)

Use `androidx.activity.compose` APIs to declaratively report when your Compose UI is ready:

```kotlin
@Composable
fun UserListRoute(
    viewModel: UserListViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    // Report fully drawn when data is loaded and UI is ready
    ReportDrawnWhen { uiState is UserListUiState.Success }
    
    UserListScreen(uiState = uiState)
}
```

**Available APIs:**

1. **ReportDrawn()** - Reports immediately (use when no async loading needed)
```kotlin
@Composable
fun StaticScreen() {
    ReportDrawn()  // Screen is immediately ready
    Text("Welcome")
}
```

2. **ReportDrawnWhen(predicate)** - Reports when condition is true
```kotlin
@Composable
fun DataScreen(viewModel: DataViewModel) {
    val isDataLoaded by viewModel.isDataLoaded.collectAsStateWithLifecycle()
    
    ReportDrawnWhen { isDataLoaded }
    
    if (isDataLoaded) {
        DataContent()
    } else {
        LoadingIndicator()
    }
}
```

3. **ReportDrawnAfter { }** - Reports after suspending block completes
```kotlin
@Composable
fun AsyncScreen() {
    ReportDrawnAfter {
        // Suspend until critical data is ready
        awaitCriticalData()
    }
    
    ScreenContent()
}
```

#### `ReportDrawn*` rules

- **Call once per screen**: Multiple `ReportDrawnWhen` calls become no-ops after the first reports
- **Handle error states**: Report even on errors to avoid blocking metrics
```kotlin
ReportDrawnWhen { 
    uiState is UserListUiState.Success || uiState is UserListUiState.Error 
}
```
- **Don't wait for everything**: Report when the primary content is visible, not when all images/ads load
- **Test with Macrobenchmark**: Combine with `StartupTimingMetric()` to measure TTFD in benchmarks

#### Viewing TTFD in Logcat

After calling `reportFullyDrawn()` (or via ReportDrawn APIs), look for:
```
ActivityTaskManager: Fully drawn com.example.app/.MainActivity: +850ms
```

This metric is crucial for understanding real user experience beyond initial frame rendering.

### Baseline Profiles

Baseline Profiles improve app startup and runtime performance by pre-compiling critical code paths. They are automatically generated and included in release builds.

#### Use baseline profiles when:

- Cold start time must drop (typical gains 10–30%).
- Critical journeys (scroll, navigation, animation) need AOT coverage.
- High-traffic screens show persistent jank without profiles.

#### Module Setup

Create a `:baselineprofile` test module using pure Gradle configuration (no GUI templates needed).

`baselineprofile/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.android.test)
    alias(libs.plugins.androidx.baselineprofile)
}

android {
    namespace = "com.example.baselineprofile"
    compileSdk {
        version = release(libs.findVersion("compileSdk").get().toInt())
    }

    targetProjectPath = ":app"

    defaultConfig {
        minSdk = libs.findVersion("minSdk").get().toString().toInt()
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    testOptions.managedDevices.localDevices {
        create("pixel6Api31") {
            device = "Pixel 6"
            apiLevel = 31
            systemImageSource = "aosp"
        }
    }
}

dependencies {
    implementation(libs.androidx.test.ext.junit)
    implementation(libs.androidx.test.espresso.core)
    implementation(libs.androidx.test.uiautomator)
    implementation(libs.androidx.benchmark.macro.junit4)
}

baselineProfile {
    managedDevices += "pixel6Api31"
    useConnectedDevices = false
}
```

Update `app/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.android.application.baseline)
    alias(libs.plugins.app.hilt)
}

dependencies {
    baselineProfile(project(":baselineprofile"))
}
```

The `app.android.application.baseline` convention plugin (from `assets/convention/AndroidApplicationBaselineProfileConventionPlugin.kt`) automatically applies the `androidx.baselineprofile` plugin and configures it for your app module.

#### Define the Baseline Profile Generator

`baselineprofile/src/main/java/.../BaselineProfileGenerator.kt`:
```kotlin
@RunWith(AndroidJUnit4::class)
class BaselineProfileGenerator {
    @get:Rule
    val rule = BaselineProfileRule()

    @Test
    fun generate() = rule.collect(
        packageName = "com.example.app",
        includeInStartupProfile = true,
        profileBlock = {
            startActivityAndWait()
            
            // Add critical user journeys here
            device.wait(Until.hasObject(By.res("auth_form")), 5000)
            
            // Navigate through key screens
            device.findObject(By.text("Login")).click()
            device.waitForIdle()
        }
    )
}
```

#### Generate the Baseline Profile

Run the generation task:
```bash
./gradlew :app:generateReleaseBaselineProfile
```

The generated profile is automatically placed in `app/src/release/generated/baselineProfiles/baseline-prof.txt` and included in release builds.

#### Benchmark the Baseline Profile

Compare performance with and without Baseline Profiles:

```kotlin
@RunWith(AndroidJUnit4::class)
class StartupBenchmark {
    @get:Rule
    val benchmarkRule = MacrobenchmarkRule()

    @Test
    fun startupNoCompilation() = startup(CompilationMode.None())

    @Test
    fun startupWithBaselineProfiles() = startup(
        CompilationMode.Partial(
            baselineProfileMode = BaselineProfileMode.Require
        )
    )

    private fun startup(compilationMode: CompilationMode) =
        benchmarkRule.measureRepeated(
            packageName = "com.example.app",
            metrics = listOf(StartupTimingMetric()),
            compilationMode = compilationMode,
            iterations = 10,
            startupMode = StartupMode.COLD
        ) {
            pressHome()
            startActivityAndWait()
        }
}
```

#### Key Points
- Baseline Profiles are only installed in release builds.
- Use physical devices or GMDs with `systemImageSource = "aosp"`.
- Update profiles when adding new features or changing critical paths.
- Include both startup and runtime journeys (scrolling, navigation) for best results.

#### ProfileInstaller

Required: add `androidx.profileinstaller` so ART compiles Baseline Profiles on first launch (mandatory for non-Play distribution; redundant only when Play Store cloud profiles cover every install path).

```kotlin
// app/build.gradle.kts
dependencies {
    implementation(libs.androidx.profileinstaller)
}
```

## Compose Stability Validation (Optional)

Use [Compose Stability Analyzer](https://github.com/skydoves/compose-stability-analyzer) for CI gating on composable skippability.

### IDE Plugin (Optional)

Install: **Settings** → **Plugins** → **Marketplace** → "Compose Stability Analyzer". Surfaces gutter icons, hover tooltips, inline parameter stability hints, and inspections.

### Gradle Plugin for CI/CD

Setup: [gradle-setup.md](/references/gradle-setup.md) → "Compose Stability Analyzer (Optional)".

#### Generate Baseline

Create a snapshot of current composables' stability:
```bash
./gradlew :app:stabilityDump
```

Commit the generated `.stability` file to version control.

#### Validate in CI

Check for stability changes:
```bash
./gradlew :app:stabilityCheck
```

The build fails if composable stability regresses, preventing performance issues from reaching production.

#### GitHub Actions Example

```yaml
stability_check:
  name: Compose Stability Check
  runs-on: ubuntu-latest
  needs: build
  steps:
    - uses: actions/checkout@v5
    - uses: actions/setup-java@v5
      with:
        distribution: 'zulu'
        java-version: 21
    - name: Stability Check
      run: ./gradlew stabilityCheck
```

## CPU Optimization

Required:

1. **Hoist invariants out of loops.**
```kotlin
// Bad
for (i in 0 until items.size) {
    process(items[i])
}

// Good
items.forEach(::process)
```

2. **Use `StringBuilder` for any concatenation in a loop.**
```kotlin
// Bad
var result = ""
for (i in 1..1000) {
    result += "Item $i\n"
}

// Good
val result = StringBuilder()
for (i in 1..1000) {
    result.append("Item $i\n")
}
```

3. **Cache compiled `Regex` instances.**
```kotlin
// Bad
fun validateEmail(email: String): Boolean =
    email.matches(Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$"))

// Good
private val EMAIL_REGEX = Regex("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$")

fun validateEmail(email: String): Boolean = email.matches(EMAIL_REGEX)
```

## Battery Optimization

Required:

1. **Always release `WakeLock` or acquire with a timeout.**
```kotlin
// Bad
wakeLock.acquire()

// Good
wakeLock.acquire(10 * 60 * 1000L)
```

2. **Use `PRIORITY_BALANCED_POWER_ACCURACY` and intervals ≥ 30 s for foreground location.**
```kotlin
// Bad
locationManager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, listener)

// Good
val locationRequest = LocationRequest.create().apply {
    interval = 60000
    fastestInterval = 30000
    priority = LocationRequest.PRIORITY_BALANCED_POWER_ACCURACY
}
```

## Network Performance Optimization

Required: never run network on the main thread; cache responses; batch requests; enable HTTP/2.

1. **OkHttp/Retrofit with `Cache`.**
```kotlin
val cacheSize = 10 * 1024 * 1024L // 10 MB
val cache = Cache(context.cacheDir, cacheSize)

val okHttpClient = OkHttpClient.Builder()
    .cache(cache)
    .addInterceptor { chain ->
        var request = chain.request()
        request = if (hasNetwork(context)) {
            request.newBuilder().header("Cache-Control", "public, max-age=60").build()
        } else {
            request.newBuilder().header("Cache-Control", "public, only-if-cached, max-stale=86400").build()
        }
        chain.proceed(request)
    }
    .build()
```

2. **Compress Images Before Upload**: Compress images locally before sending them to the server.
```kotlin
bitmap.compress(Bitmap.CompressFormat.JPEG, 80, outputStream) // 80% quality
```

3. **Batch Network Requests**: Instead of making 100 separate network calls for individual items, make a single batch request.

4. **Enable HTTP/2**: HTTP/2 multiplexes requests over a single connection, making it faster.
```kotlin
val okHttpClient = OkHttpClient.Builder()
    .protocols(listOf(Protocol.HTTP_2, Protocol.HTTP_1_1))
    .build()
```

## Image Optimization

Required:

1. **Coil for all network images.** Forbidden: direct `BitmapFactory.decodeStream` from network.
```kotlin
imageView.load(imageUrl) {
    crossfade(true)
    placeholder(R.drawable.placeholder)
}
```

2. **Decode at display size.** Never decode a 4000×3000 bitmap into a 200 dp view; let Coil size it.

3. **Format selection:** JPEG for photos, PNG for transparent icons, **WebP** for everything else (smaller than JPEG, supports transparency).

4. **Vector drawables for icons.** Forbidden: shipping per-density PNG sets when an `.xml` vector exists.

## APK Size Optimization

Required:

1. **Enable R8.** `isMinifyEnabled = true` and `isShrinkResources = true` on every release build.
2. **Ship AAB, not APK.** Play Store generates per-device splits.
3. **Filter resources via `resConfigs`** to ship only supported languages.
```kotlin
android {
    defaultConfig {
        resConfigs("en", "es") // Only keep English and Spanish
    }
}
```
4. **Convert PNG → WebP** wherever it preserves quality.
5. **Filter NDK ABIs** to common architectures.
```kotlin
android {
    defaultConfig {
        ndk {
            abiFilters.addAll(listOf("armeabi-v7a", "arm64-v8a"))
        }
    }
}
```

## App Startup & Initialization

Required: control component initialization explicitly. Forbidden: per-library `ContentProvider` auto-initialization. Use `androidx.startup` or lazy initialization.

### ContentProvider Anti-Pattern

Library `ContentProvider.onCreate()` runs before `Application.onCreate()` on the main thread; each one adds cold-start cost. Disable per-library auto-initialization and route through `androidx.startup`.

**Disable a library's auto-initialization** (e.g., WorkManager):
```xml
<!-- app/src/main/AndroidManifest.xml -->
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    <!-- Disable WorkManager's auto-initialization -->
    <meta-data
        android:name="androidx.work.WorkManagerInitializer"
        android:value="androidx.startup"
        tools:node="remove" />
</provider>
```

### App Startup Library

Use `androidx.startup:startup-runtime` to consolidate initialization into a single shared ContentProvider with explicit dependency ordering.

**1. Implement an `Initializer`:**
```kotlin
// core/common/src/main/kotlin/com/example/core/startup/TimberInitializer.kt
import android.content.Context
import androidx.startup.Initializer
import timber.log.Timber

class TimberInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }
    }

    override fun dependencies(): List<Class<out Initializer<*>>> = emptyList()
}
```

**2. Initializer with dependencies:**
```kotlin
// core/common/src/main/kotlin/com/example/core/startup/CrashReporterInitializer.kt
class CrashReporterInitializer : Initializer<Unit> {
    override fun create(context: Context) {
        CrashReporter.init(context)
    }

    override fun dependencies(): List<Class<out Initializer<*>>> = listOf(
        TimberInitializer::class.java
    )
}
```

**3. Register in AndroidManifest:**
```xml
<!-- app/src/main/AndroidManifest.xml -->
<provider
    android:name="androidx.startup.InitializationProvider"
    android:authorities="${applicationId}.androidx-startup"
    android:exported="false"
    tools:node="merge">
    <!-- Only list leaf initializers - dependencies are resolved automatically -->
    <meta-data
        android:name="com.example.core.startup.CrashReporterInitializer"
        android:value="androidx.startup" />
</provider>
```

**4. Lazy initialization (on-demand):**

Remove the `<meta-data>` entry from the manifest and initialize manually when needed:
```kotlin
AppInitializer.getInstance(context)
    .initializeComponent(CrashReporterInitializer::class.java)
```

### Lazy Initialization Strategies

Defer non-essential work until after the first frame is drawn:

```kotlin
// In Application or MainActivity
class MyApplication : Application() {
    override fun onCreate() {
        super.onCreate()

        // Critical path only - keep minimal
        // App Startup handles TimberInitializer, CrashReporterInitializer

        // Defer non-critical initialization
        ProcessLifecycleOwner.get().lifecycle.addObserver(
            object : DefaultLifecycleObserver {
                override fun onStart(owner: LifecycleOwner) {
                    // First time app becomes visible - initialize non-critical components
                    initializeNonCritical()
                    owner.lifecycle.removeObserver(this)
                }
            }
        )
    }

    private fun initializeNonCritical() {
        // Analytics, feature flags, prefetch, etc.
    }
}
```

**In Compose - defer heavy content until first frame:**
```kotlin
@Composable
fun DeferredContent(content: @Composable () -> Unit) {
    var shouldLoad by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        // Yield to let the first frame draw
        withContext(Dispatchers.Main) {
            shouldLoad = true
        }
    }

    if (shouldLoad) {
        content()
    }
}
```

**What to initialize eagerly vs lazily:**

| Timing              | Components                                                |
|---------------------|-----------------------------------------------------------|
| Eager (App Startup) | Crash reporter, logging, StrictMode                       |
| After first frame   | Analytics, feature flags, remote config                   |
| On demand           | Image loader, ML models, database migrations, WorkManager |

### Splash Screen

Required: Add `androidx.core:core-splashscreen` to `:app` (`implementation(libs.androidx.core.splashscreen)`); pin the version in `gradle/libs.versions.toml` using `assets/libs.versions.toml.template` (`splashscreen`). Module wiring: [gradle-setup.md](/references/gradle-setup.md).

Required: Call `installSplashScreen()` on the process launcher activity before `super.onCreate()` so Android 12+ system splash and compat pre-12 share one theme-backed path. Attribute list and platform rules: [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen). Legacy `windowBackground` themes and dedicated splash activities: [migration.md](/references/migration.md) → **Legacy splash to Splash Screen API**.

**Icon mask:** Size `windowSplashScreenAnimatedIcon` per [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen): with `Theme.SplashScreen.IconBackground`, use **240×240 dp** artwork inside a **160 dp** diameter circle; with `Theme.SplashScreen` only, **288×288 dp** inside **192 dp**. Re-read the live doc when bumping `compileSdk`. On API 31+, check that doc for optional `splashScreenIconSize`.

Use `Theme.SplashScreen.IconBackground` when the foreground needs a solid circular plate behind transparent artwork.

| Setup                                 | Behavior                                                                                                                              |
|---------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `core-splashscreen`, API 30 and below | Library-backed splash; same theme attributes the compat library applies on that level.                                                |
| API 31+                               | System splash; animated icon and `windowSplashScreenAnimationDuration` (milliseconds, max **1000** on API 31+) follow platform rules. |

**Required: `onCreate` call order**

`installSplashScreen()` → `super.onCreate()` → `setKeepOnScreenCondition { }` (if used) → `enableEdgeToEdge()` → `setContent { }`. The splash window is system-drawn until handoff; first app frames still need inset handling (`Scaffold` / `innerPadding` - see [migration.md](/references/migration.md) Edge-to-Edge, `references/compose-patterns.md`).

Splash dismissal merges system-controlled minimum visibility, `windowSplashScreenAnimationDuration` when set (API 31+, max 1000 ms), and `setKeepOnScreenCondition` when registered. Copy the exact interaction from [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen) when auditing a new `compileSdk`.

Test the launcher activity on **minSdk**, on **API 31+**, on at least one gesture or default edge-to-edge configuration, and on foldables **when** large-screen layouts ship.

After handoff to Compose, call `ReportDrawn*` so metrics track full display when primary UI is ready, not only splash dismissal ([Startup Performance Metrics (TTID & TTFD)](#startup-performance-metrics-ttid--ttfd)).

**Forbidden when:** Holding the splash for open-ended network work; dismiss for local readiness and use in-app placeholders for long remote work ([migration.md](/references/migration.md) → **Legacy splash to Splash Screen API**).

**Wrong:**

`setContent` omits `AppTheme` / root navigation while `isLoading` is true, so no composition subtree mounts under the splash.

**Correct:**

Always mount `AppTheme` and a composable root; branch **inside** the tree for loading vs main UI (or rely only on `setKeepOnScreenCondition` without stripping the root).

**Required: splash theme (values)**

```xml
<!-- app/src/main/res/values/themes.xml -->
<style name="Theme.App.Splash" parent="Theme.SplashScreen">
    <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
    <item name="windowSplashScreenBackground">@color/splash_background</item>
    <item name="windowSplashScreenAnimationDuration">1000</item>
    <item name="postSplashScreenTheme">@style/Theme.App</item>
    <!-- optional API 31+: windowSplashScreenBrandingImage -->
</style>

<style name="Theme.App.Splash.WithBackground" parent="Theme.SplashScreen.IconBackground">
    <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
    <item name="windowSplashScreenIconBackgroundColor">@color/splash_icon_bg</item>
    <item name="windowSplashScreenBackground">@color/splash_background</item>
    <item name="windowSplashScreenAnimationDuration">1000</item>
    <item name="postSplashScreenTheme">@style/Theme.App</item>
</style>
```

**Required: manifest (launcher activity)**

```xml
<!-- app/src/main/AndroidManifest.xml -->
<activity
    android:name=".MainActivity"
    android:theme="@style/Theme.App.Splash"
    android:exported="true">
    <!-- ... intent filters ... -->
</activity>
```

**Required: launcher `Activity` (Compose)**

```kotlin
// app/src/main/kotlin/com/example/app/MainActivity.kt
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)

        splashScreen.setKeepOnScreenCondition {
            viewModel.isLoading.value
        }

        enableEdgeToEdge()

        setContent {
            val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()
            AppTheme {
                if (isLoading) {
                    Box(Modifier.fillMaxSize())
                } else {
                    AppNavigation()
                }
            }
        }
    }
}
```

**ViewModel driving `setKeepOnScreenCondition`**

```kotlin
@HiltViewModel
class MainViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        viewModelScope.launch {
            authRepository.isAuthenticated()
            _isLoading.value = false
        }
    }
}
```

**Use when:** custom exit animation from the splash surface to the first frame - `setOnExitAnimationListener { splashScreenView -> ... }`; end with `splashScreenView.remove()` after the animator finishes. API and sample: [Splash screen](https://developer.android.com/develop/ui/views/launch/splash-screen).

**Required:**

- Call `installSplashScreen()` before `super.onCreate()`.
- `setKeepOnScreenCondition` runs on the main thread before each draw; return only from cheap reads (multiple primitive flag reads allowed). Forbidden: I/O, network, heavy work, allocation, or `runBlocking` inside the lambda.
- `setKeepOnScreenCondition` absent or returning `false` allows splash dismissal per platform timing; when present, the splash stays until the predicate is `false`.
- Animated drawable and `windowSplashScreenAnimationDuration` apply on API 31+; cap duration at **1000** ms on API 31+.
- Set `postSplashScreenTheme` to the theme used after splash handoff.

### Startup Optimization Checklist

- [ ] Audit `ContentProvider` usage - remove or replace with App Startup initializers
- [ ] Classify initializers as eager, after-first-frame, or on-demand
- [ ] Use `installSplashScreen()` with `setKeepOnScreenCondition` for loading state
- [ ] Test launcher splash on **minSdk**, **API 31+**, and at least one edge-to-edge or gesture-nav configuration ([Splash Screen](#splash-screen))
- [ ] Generate Baseline Profiles for startup paths (see [Benchmark](#benchmark) section)
- [ ] Measure cold start time with Macrobenchmark before/after changes
- [ ] Avoid blocking the main thread with I/O, network, or heavy computation during startup
- [ ] Use `ProcessLifecycleOwner` or `Lifecycle` callbacks to defer non-critical work

## Compose Recomposition Performance

### Three Phases of Compose

Every frame runs three phases. State reads in each phase only trigger work for that phase and later ones.

| Phase | What Runs | State Read Triggers |
|-------|----------|-------------------|
| Composition | Composable functions, evaluates state | Recomposition of the reading scope |
| Layout | `measure` and `layout` blocks | Relayout only (no recomposition) |
| Drawing | `Canvas`, `DrawScope`, `drawBehind` | Redraw only (no recomposition or relayout) |

**Rule:** Push state reads to the latest possible phase to minimize work.

### Deferred State Reads

Read state in the layout or draw phase instead of composition to avoid recomposition:

```kotlin
// Bad: read in composition phase
@Composable
fun AnimatedBox(offsetState: State<Float>) {
    val x = offsetState.value
    Box(modifier = Modifier.offset(x.dp, 0.dp))
}

// Good: deferred to layout phase
@Composable
fun AnimatedBox(offsetState: State<Float>) {
    Box(
        modifier = Modifier.offset {
            IntOffset(offsetState.value.roundToInt(), 0)
        }
    )
}

// Best: deferred to draw phase
@Composable
fun AnimatedBox(offsetState: State<Float>) {
    Box(
        modifier = Modifier.graphicsLayer {
            translationX = offsetState.value
        }
    )
}
```

Key lambda-based modifiers that defer reads:
- `Modifier.offset { }` - defers to layout phase
- `Modifier.graphicsLayer { }` - defers to draw phase
- `Modifier.drawBehind { }` - defers to draw phase

### Strong Skipping Mode

Enabled by default on the current Compose compiler. Recomposition skipping rules:

- Composables skip recomposition if all parameters are unchanged
- Lambdas are stable if all captured variables are stable
- `@Stable` and `@Immutable` annotations are critical for custom types

```kotlin
// Good: stable lambda (captures only stable Int)
@Composable
fun Counter(count: Int) {
    Button(onClick = { println(count) }) {
        Text("Count: $count")
    }
}

// Bad: unstable parameter
@Composable
fun UserCard(config: Config) {
    Text(config.title)
}

// Fix
@Immutable
data class Config(val title: String, val color: Color)
```

Stability annotations (`@Immutable`, `@Stable`): [compose-patterns.md → Stability Annotations](/references/compose-patterns.md#stability-annotations-immutable-vs-stable).

### derivedStateOf - Reducing Recomposition Frequency

Only recomposes when the derived result actually changes, not on every input change:

```kotlin
// Bad: filter recomputed every recomposition
@Composable
fun FilteredList(items: List<Item>, query: String) {
    val filtered = items.filter { query in it.title }
    LazyColumn {
        items(filtered) { ItemRow(it) }
    }
}

// Good
@Composable
fun FilteredList(items: List<Item>, query: String) {
    val filtered by remember(items, query) {
        derivedStateOf { items.filter { query in it.title } }
    }
    LazyColumn {
        items(filtered) { ItemRow(it) }
    }
}
```

Also useful for scroll-dependent UI:

```kotlin
val listState = rememberLazyListState()
val showScrollToTop by remember {
    derivedStateOf { listState.firstVisibleItemIndex > 0 }
}
```

Only use `derivedStateOf` for non-trivial computations. For cheap operations (string concat, simple boolean), the overhead isn't worth it.

### remember with Keys

```kotlin
// Bad: recomputed every recomposition
val metadata = computeMetadata(id)

// Good
val metadata = remember(id) { computeMetadata(id) }

// Multiple keys
val data = remember(id, userId) { fetchData(id, userId) }
```

Forbidden: wrapping cheap values (literals, primitives, single-property data classes) in `remember`.

### R8/ProGuard Compose Rules

Preserve stability annotations in release builds:

```proguard
# Keep Compose stability annotations for recomposition skipping
-keep @androidx.compose.runtime.Stable class **
-keep @androidx.compose.runtime.Immutable class **
-keepclassmembers class * {
    @androidx.compose.runtime.Stable <methods>;
}
```

Ensure `minifyEnabled` and `shrinkResources` are enabled:

```kotlin
// app/build.gradle.kts
android {
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
}
```

Full R8 rules: `assets/proguard-rules.pro.template`.

### Layout Inspector - Recomposition Counts

Measure recompositions in Android Studio:

1. Run app on device
2. **Tools > Layout Inspector** > select process
3. Enable **Show Composition Counts** toggle
4. Interact with the app - counts show how many times each composable recomposed

High recomposition counts indicate:
- Unstable parameters (add `@Immutable`/`@Stable`)
- State reads in wrong scope (defer to layout/draw phase)
- Missing `remember` on expensive computations
- Lambda allocations (wrap in `remember` or use method references)

### Common Hot Paths

```kotlin
// Bad: new ButtonColors per recomposition
Button(
    colors = ButtonDefaults.buttonColors(
        containerColor = if (isPressed) Color.Red else Color.Blue
    )
) { Text("Click") }
// Good
val buttonColors = remember(isPressed) {
    ButtonDefaults.buttonColors(
        containerColor = if (isPressed) Color.Red else Color.Blue
    )
}
Button(colors = buttonColors) { Text("Click") }

// Bad: filter inside items()
LazyColumn {
    items(items.filter(predicate)) { ItemRow(it) }
}
// Good
val filtered by remember(items, predicate) {
    derivedStateOf { items.filter(predicate) }
}
LazyColumn {
    items(filtered) { ItemRow(it) }
}

// Bad: per-item remember + missing key
LazyColumn {
    items(users) { user ->
        val state = remember { mutableStateOf(user) }
        UserRow(state.value)
    }
}
// Good
LazyColumn {
    items(users, key = { it.id }) { user ->
        UserRow(user)
    }
}
```

### Text Input Performance

`BasicTextField2` (`rememberTextFieldState()`) is required for high-frequency input; `TextField` / `OutlinedTextField` round-trip through the ViewModel and drop keystrokes under load.

```kotlin
// Bad
var text by remember { mutableStateOf("") }
TextField(value = text, onValueChange = { text = it })

// Good
val state = rememberTextFieldState()
BasicTextField2(state = state)
```

### Performance Checklist

- [ ] Use `BasicTextField2` for all text inputs to prevent dropped keystrokes.
- [ ] Use `derivedStateOf` when reading scroll state or filtering lists.
- [ ] Defer state reads to the layout or draw phase when animating (e.g., `Modifier.offset { }`, `Modifier.graphicsLayer { }`).
- [ ] Ensure all domain models passed to Compose are `@Immutable` or `@Stable`.
- [ ] Use `key` and `contentType` in all `LazyColumn`/`LazyRow` items.
- [ ] Avoid calling `refresh()` on PagingData inside a composable body.

## References
- Splash screen: https://developer.android.com/develop/ui/views/launch/splash-screen
- Migrate to the Splash Screen API: https://developer.android.com/develop/ui/views/launch/splash-screen/migrate
- Benchmarking overview: https://developer.android.com/topic/performance/benchmarking/benchmarking-overview
- Macrobenchmark overview: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview
- Macrobenchmark metrics: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-metrics
- Macrobenchmark control app: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-control-app
- Baseline Profiles overview: https://developer.android.com/topic/performance/baselineprofiles/overview
- Create Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/create-baselineprofile
- Configure Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/configure-baselineprofiles
- Measure Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/measure-baselineprofile
