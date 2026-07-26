# Code Coverage with JaCoCo

Required: ship JaCoCo on `debug` with unit-test execution data on every PR. Combined unit + instrumented reports are the default convention path; treat that path as **Tier 2** below.

## Table of Contents

1. [Coverage tiers](#coverage-tiers)
2. [Setup](#setup)
3. [Generating Coverage Reports](#generating-coverage-reports)
4. [Coverage Exclusions](#coverage-exclusions)
5. [CI Integration](#ci-integration)
6. [Rules](#rules)
7. [Troubleshooting](#troubleshooting)
8. [References](#references)

## Coverage tiers

| Tier       | Scope                                                                                                                                            | Use when                                                                                                                                           |
|------------|--------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| **Tier 1** | JaCoCo plugin + `enableUnitTestCoverage` / `enableAndroidTestCoverage` on `debug`, unit tests (`testDebugUnitTest`), optional instrumented tests | AGP upgrade surfaces `MissingValueException` / "provider has no value" during `compile*JavaWithJavac`, or configure-time failures before tests run |
| **Tier 2** | Tier 1 plus `createDebugCombinedCoverageReport` from `assets/convention/config/Jacoco.kt` (`ScopedArtifacts` wiring for merged class dirs)       | Green `./gradlew help` and stable `compile*JavaWithJavac` after the AGP bump                                                                       |

Escalate from Tier 1 to Tier 2 only after `./gradlew help` and `./gradlew testDebugUnitTest` succeed.

### Optional: AGP aggregated reports (AGP 9.2+)

If the goal is only a **readable cross-module dashboard** rather than a machine-parsable coverage XML for a CI gate, AGP can aggregate unit and instrumentation results itself:

```properties
# gradle.properties
android.experimental.reportAggregationSupport=true
```

Scope and limits:

- Aggregates **test results** across modules and variants into HTML. It is not a substitute for the JaCoCo XML that Codecov / a coverage threshold consumes.
- Experimental - the flag and output layout can change between AGP minors. Do not build a CI gate on it.
- Independent of the tier ladder above; it neither replaces nor requires the `ScopedArtifacts` wiring.

Use the JaCoCo convention plugins for any coverage number that gates a merge; use this flag for human inspection during a debugging session ([gradle-setup.md](gradle-setup.md#aggregated-test-and-coverage-reports-optional-agp-92)).

## Setup

### Apply Convention Plugins

**For app module** (`app/build.gradle.kts`):
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.android.application.jacoco)
}
```

**For library modules** (`:core:data`, `:feature:auth`, etc.):
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.android.library.jacoco)
}
```

The JaCoCo convention plugins (from `assets/convention/`) automatically:
- Apply the JaCoCo plugin
- Configure JaCoCo version from version catalog
- Enable coverage for debug builds only
- Exclude generated code (Hilt, R files, BuildConfig)
- Register combined coverage report tasks (Tier 2 `ScopedArtifacts` path)

## Generating Coverage Reports

Run tests then the combined report task when Tier 2 is enabled. Instrumented tests require a connected device or emulator:

```bash
./gradlew testDebugUnitTest connectedDebugAndroidTest
./gradlew createDebugCombinedCoverageReport
# library module variant:
./gradlew :core:data:createDebugCombinedCoverageReport
```

Output paths (per module under `build/reports/jacoco/createDebugCombinedCoverageReport/`):

- `createDebugCombinedCoverageReport.xml` - feed to CI/Codecov.
- `html/index.html` - per-package, class, method drilldown.

## Coverage Exclusions

The following are automatically excluded from coverage:
- Android generated files (`R.class`, `BuildConfig.class`, `Manifest`)
- Hilt generated classes (`*_Hilt*.class`, `Hilt_*.class`, `*_Factory.class`)
- Dagger components (`*Component.class`, `*Module.class`)
- Room 3 KSP output (`*_Impl.class` - generated DAO and `RoomDatabase` implementations)
- Compose compiler output (`ComposableSingletons*.class`, synthetic lambda holders)

Required: exclude generated code rather than writing tests for it. Room `_Impl` classes and Compose
`ComposableSingletons` are large, fully generated, and unreachable by unit tests, so leaving them in
deflates the coverage percentage and pushes an agent toward writing meaningless tests to recover it.
Test the DAO **interface** through an in-memory database instead ([testing.md](testing.md)).

## CI Integration

### GitHub Actions Example

```yaml
name: Code Coverage

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-java@v4
        with:
          distribution: 'zulu'
          java-version: '17'

      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3

      - name: Run Unit Tests
        run: ./gradlew testDebugUnitTest

      - name: Run Instrumented Tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 31
          target: google_apis
          arch: x86_64
          script: ./gradlew connectedDebugAndroidTest

      - name: Generate Coverage Report
        # Tier 2: requires working ScopedArtifacts + combined report task from JaCoCo convention
        run: ./gradlew createDebugCombinedCoverageReport

      - name: Upload Coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./build/reports/jacoco/createDebugCombinedCoverageReport/createDebugCombinedCoverageReport.xml
          flags: unittests
          name: codecov-umbrella
```

### Enforcing Minimum Coverage

```kotlin
// build.gradle.kts (project level or in a convention plugin)
tasks.withType<JacocoCoverageVerification>().configureEach {
    violationRules {
        rule {
            limit { minimum = "0.80".toBigDecimal() }
        }
    }
}
```

## Rules

Required:
- Run `testDebugUnitTest` on every PR; gate coverage on `core/domain` and `core/data` using whichever tier is active.
- Target >= 80% line coverage on `core/domain` and `core/data` when Tier 2 reports are enabled. UI modules are measured but not gated.
- Keep instrumented tests under `src/androidTest/` and unit tests under `src/test/`. Coverage tasks read both paths when Tier 2 runs.
- Cover Compose UI through Compose UI tests and screenshot tests, not by gating composable line coverage.

Forbidden:
- Adding tests solely to lift the coverage number (assertion-free `assertTrue(true)`, `runBlocking { fn() }` with no checks).
- Disabling exclusion patterns in `assets/convention/config/Jacoco.kt` to inflate coverage.

## Troubleshooting

| Symptom                             | Fix                                                                                                                                                                                                |
|-------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| No coverage data generated          | Confirm tests run and pass; confirm `src/test/` vs `src/androidTest/` placement; coverage runs on `debug` only.                                                                                    |
| Classes missing from report         | Check exclusion patterns in `assets/convention/config/Jacoco.kt`; confirm module applies the JaCoCo convention plugin.                                                                             |
| Robolectric / JDK 11+ class loading | Convention plugin already sets `isIncludeNoLocationClasses = true` and `excludes = listOf("jdk.internal.*")`. If overriding, keep both.                                                            |
| `MissingValueException` / unresolved `Provider` during `compile*JavaWithJavac` after AGP or API bump | Drop to **Tier 1**: remove `app.android.application.jacoco` / `app.android.library.jacoco` from the failing module temporarily or fork `Jacoco.kt` without the `ScopedArtifacts.forScope(...).toGet(...)` block; rerun `./gradlew help --stacktrace`. Re-enable Tier 2 only after configuration is green. |
| Unknown configure failure           | Run `./gradlew help --stacktrace` (and a build scan when CI allows) before bumping Kotlin or KSP; see [gradle-setup.md](gradle-setup.md#agp-9-verification).                            |

## References

- [JaCoCo Documentation](https://www.jacoco.org/jacoco/trunk/doc/)
- [Android Testing: Code Coverage](https://developer.android.com/studio/test/code-coverage)
- Convention plugin implementations: `assets/convention/AndroidApplicationJacocoConventionPlugin.kt`, `assets/convention/AndroidLibraryJacocoConventionPlugin.kt`, `assets/convention/config/Jacoco.kt`
