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

## References
- Benchmarking overview: https://developer.android.com/topic/performance/benchmarking/benchmarking-overview
- Macrobenchmark overview: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview
- Macrobenchmark metrics: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-metrics
- Macrobenchmark control app: https://developer.android.com/topic/performance/benchmarking/macrobenchmark-control-app
