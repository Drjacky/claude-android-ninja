# Android Performance

Performance guidance for this multi-module, Compose-first architecture. Use this when you need
repeatable metrics for startup, navigation, or UI rendering changes.

## Benchmark

Benchmarking is for measuring **real performance** (not just profiling). Use it to detect
regressions and compare changes objectively. Android provides two libraries:
- **Macrobenchmark**: end-to-end user journeys (startup, scrolling, navigation).
- **Microbenchmark**: small, isolated code paths.

This guide focuses on **Macrobenchmark** for Compose apps.

### Macrobenchmark (Compose)

#### When to Use
- Startup time regressions (cold/warm start).
- Compose screen navigation and list scrolling.
- Animation/jank investigations that need repeatable results.

#### Module Setup
Create a dedicated `:benchmark` test module. See `references/gradle-setup.md` → "Benchmark Module (Optional)" for the complete module setup and app build type configuration.

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

#### Macrobenchmark Best Practices
- Prefer `CompilationMode.Partial()` to approximate Baseline Profile behavior when comparing changes.
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

#### Best Practices

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

#### When to Use
- Improve cold start time (10-30% faster).
- Optimize critical user journeys (scrolling, navigation, animations).
- Reduce jank in frequently used screens.

#### Module Setup

Create a `:baselineprofile` test module using pure Gradle configuration (no GUI templates needed).

`baselineprofile/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.android.test)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.androidx.baselineprofile)
}

android {
    namespace = "com.example.baselineprofile"
    compileSdk = libs.findVersion("compileSdk").get().toInt()

    targetProjectPath = ":app"

    defaultConfig {
        minSdk = libs.findVersion("minSdk").get().toString().toInt()
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    testOptions.managedDevices.devices {
        create<com.android.build.api.dsl.ManagedVirtualDevice>("pixel6Api31") {
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

The `app.android.application.baseline` convention plugin (from `templates/convention/AndroidApplicationBaselineProfileConventionPlugin.kt`) automatically applies the `androidx.baselineprofile` plugin and configures it for your app module.

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

## Compose Stability Validation (Optional)

The [Compose Stability Analyzer](https://github.com/skydoves/compose-stability-analyzer) provides real-time analysis and CI guardrails for Jetpack Compose stability.

### IDE Plugin (Optional)

The Compose Stability Analyzer IntelliJ Plugin provides real-time visual feedback in Android Studio:
- **Gutter Icons**: Colored dots showing if a composable is skippable.
- **Hover Tooltips**: Detailed stability information and reasons.
- **Inline Parameter Hints**: Badges showing parameter stability.
- **Code Inspections**: Quick fixes and warnings for unstable composables.

Install via: **Settings** → **Plugins** → **Marketplace** → "Compose Stability Analyzer"

### Gradle Plugin for CI/CD

For setup instructions, see `references/gradle-setup.md` → "Compose Stability Analyzer (Optional)".

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

## References
- Benchmarking overview: https://developer.android.com/topic/performance/benchmarking/benchmarking-overview
- Macrobenchmark overview: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview
- Macrobenchmark metrics: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-metrics
- Macrobenchmark control app: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-control-app
- Baseline Profiles overview: https://developer.android.com/topic/performance/baselineprofiles/overview
- Create Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/create-baselineprofile
- Configure Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/configure-baselineprofiles
- Measure Baseline Profiles: https://developer.android.com/topic/performance/baselineprofiles/measure-baselineprofile
