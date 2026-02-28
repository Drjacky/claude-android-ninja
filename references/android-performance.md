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

## App Startup & Initialization

Optimize cold start time by controlling when and how components initialize. Avoid ContentProvider-based auto-initialization and use the App Startup library for explicit control.

### ContentProvider Anti-Pattern

Many libraries auto-initialize via `ContentProvider.onCreate()`, which runs before `Application.onCreate()` on the main thread. Each ContentProvider adds overhead to cold start. Instead, disable auto-initialization and use the App Startup library or lazy initialization.

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

| Timing | Components |
|---|---|
| Eager (App Startup) | Crash reporter, logging, StrictMode |
| After first frame | Analytics, feature flags, remote config |
| On demand | Image loader, ML models, database migrations, WorkManager |

### Splash Screen

Use the `androidx.core:core-splashscreen` library for a consistent splash screen across API levels. It displays while App Startup initializers and early ViewModel loading complete.

**1. Define splash theme:**
```xml
<!-- app/src/main/res/values/themes.xml -->
<style name="Theme.App.Splash" parent="Theme.SplashScreen">
    <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
    <item name="windowSplashScreenBackground">@color/splash_background</item>
    <item name="postSplashScreenTheme">@style/Theme.App</item>
</style>

<!-- For animated icon with background circle (optional) -->
<style name="Theme.App.Splash.WithBackground" parent="Theme.SplashScreen.IconBackground">
    <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
    <item name="windowSplashScreenIconBackgroundColor">@color/splash_icon_bg</item>
    <item name="windowSplashScreenBackground">@color/splash_background</item>
    <item name="postSplashScreenTheme">@style/Theme.App</item>
</style>
```

**2. Set in manifest:**
```xml
<!-- app/src/main/AndroidManifest.xml -->
<activity
    android:name=".MainActivity"
    android:theme="@style/Theme.App.Splash"
    android:exported="true">
    <!-- ... intent filters ... -->
</activity>
```

**3. Install in Activity with Compose:**
```kotlin
// app/src/main/kotlin/com/example/app/MainActivity.kt
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen

class MainActivity : ComponentActivity() {
    private val viewModel: MainViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        val splashScreen = installSplashScreen()
        super.onCreate(savedInstanceState)

        // Keep splash screen visible while loading
        splashScreen.setKeepOnScreenCondition {
            viewModel.isLoading.value
        }

        enableEdgeToEdge()

        setContent {
            val isLoading by viewModel.isLoading.collectAsStateWithLifecycle()

            if (!isLoading) {
                AppTheme {
                    AppNavigation()
                }
            }
        }
    }
}
```

**4. MainViewModel for splash loading:**
```kotlin
@HiltViewModel
class MainViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {
    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        viewModelScope.launch {
            // Check auth state, load user prefs, etc.
            authRepository.isAuthenticated()
            _isLoading.value = false
        }
    }
}
```

**Key points:**
- Call `installSplashScreen()` before `super.onCreate()`
- `setKeepOnScreenCondition` callback runs on main thread before each draw - keep it fast (just read a boolean)
- The splash screen dismisses automatically once the condition returns `false`
- Animated icons are supported on API 31+; animation duration should not exceed 1000ms
- `postSplashScreenTheme` switches to your app theme after dismissal

### Startup Optimization Checklist

- [ ] Audit `ContentProvider` usage - remove or replace with App Startup initializers
- [ ] Classify initializers as eager, after-first-frame, or on-demand
- [ ] Use `installSplashScreen()` with `setKeepOnScreenCondition` for loading state
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
// Bad: reads in composition - recomposes every frame during animation
@Composable
fun AnimatedBox(offsetState: State<Float>) {
    val x = offsetState.value
    Box(modifier = Modifier.offset(x.dp, 0.dp))
}

// Good: reads in layout phase - no recomposition
@Composable
fun AnimatedBox(offsetState: State<Float>) {
    Box(
        modifier = Modifier.offset {
            IntOffset(offsetState.value.roundToInt(), 0)
        }
    )
}

// Best: reads in draw phase via graphicsLayer - no recomposition, no relayout
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

Enabled by default in modern Compose compiler. Changes how recomposition skipping works:

- Composables skip recomposition if all parameters are unchanged
- Lambdas are stable if all captured variables are stable
- `@Stable` and `@Immutable` annotations are critical for custom types

```kotlin
// Stable lambda - count is a stable type (Int)
@Composable
fun Counter(count: Int) {
    Button(onClick = { println(count) }) {
        Text("Count: $count")
    }
}

// Unstable parameter - causes recomposition every time
@Composable
fun UserCard(config: Config) { // Config not annotated = unstable
    Text(config.title)
}

// Fix: annotate or cache
@Immutable
data class Config(val title: String, val color: Color)
```

For stability annotations (`@Immutable`, `@Stable`), see [Performance Optimization > Stability Annotations](../references/compose-patterns.md#stability-annotations-immutable-vs-stable) in compose-patterns.md.

### derivedStateOf - Reducing Recomposition Frequency

Only recomposes when the derived result actually changes, not on every input change:

```kotlin
// Bad: filters on every recomposition
@Composable
fun FilteredList(items: List<Item>, query: String) {
    val filtered = items.filter { query in it.title }
    LazyColumn {
        items(filtered) { ItemRow(it) }
    }
}

// Good: only recomposes when the filtered result changes
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
// Recalculates on every recomposition - bad for expensive ops
val metadata = computeMetadata(id)

// Recalculates only when id changes
val metadata = remember(id) { computeMetadata(id) }

// Multiple keys
val data = remember(id, userId) { fetchData(id, userId) }
```

Skip `remember` for cheap operations (string literals, simple objects). Over-wrapping adds memory overhead.

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

See `templates/proguard-rules.pro.template` for the full R8 rules file.

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
// Bad: allocates string every recomposition
Text("Count: ${count}")
// Acceptable: Compose handles this efficiently for simple interpolation

// Bad: creates new ButtonColors every recomposition
Button(
    colors = ButtonDefaults.buttonColors(
        containerColor = if (isPressed) Color.Red else Color.Blue
    )
) { Text("Click") }
// Good: cache the colors
val buttonColors = remember(isPressed) {
    ButtonDefaults.buttonColors(
        containerColor = if (isPressed) Color.Red else Color.Blue
    )
}
Button(colors = buttonColors) { Text("Click") }

// Bad: filters without derivedStateOf - runs on every recomposition
LazyColumn {
    items(items.filter(predicate)) { ItemRow(it) }
}
// Good: derive the filtered list
val filtered by remember(items, predicate) {
    derivedStateOf { items.filter(predicate) }
}
LazyColumn {
    items(filtered) { ItemRow(it) }
}

// Bad: creating objects in item scope
LazyColumn {
    items(users) { user ->
        val state = remember { mutableStateOf(user) } // new state per recomposition
        UserRow(state.value)
    }
}
// Good: pass data directly with stable keys
LazyColumn {
    items(users, key = { it.id }) { user ->
        UserRow(user)
    }
}
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
