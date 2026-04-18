# Code Coverage with JaCoCo

Required: combined unit + instrumented coverage on every PR. Apply via the JaCoCo convention plugins in `assets/convention/`.

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
- Create combined coverage report tasks

## Generating Coverage Reports

Run tests then the combined report task. Instrumented tests require a connected device or emulator:

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
- Run `createDebugCombinedCoverageReport` on every PR.
- Target ≥ 80% line coverage on `core/domain` and `core/data`. UI modules are measured but not gated.
- Keep instrumented tests under `src/androidTest/` and unit tests under `src/test/`. Coverage tasks read both paths.
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

## References

- [JaCoCo Documentation](https://www.jacoco.org/jacoco/trunk/doc/)
- [Android Testing: Code Coverage](https://developer.android.com/studio/test/code-coverage)
- Convention plugin implementations: `assets/convention/AndroidApplicationJacocoConventionPlugin.kt`, `assets/convention/AndroidLibraryJacocoConventionPlugin.kt`, `assets/convention/config/Jacoco.kt`
