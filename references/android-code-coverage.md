# Code Coverage with JaCoCo

JaCoCo provides code coverage reports for Android projects, combining data from both unit tests and instrumented tests.

## When to Use

- **CI/CD pipelines**: Enforce minimum coverage thresholds
- **Code review**: Identify untested code paths
- **Quality metrics**: Track coverage trends over time
- **Team standards**: Maintain consistent test coverage

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

The JaCoCo convention plugins (from `templates/convention/`) automatically:
- Apply the JaCoCo plugin
- Configure JaCoCo version from version catalog
- Enable coverage for debug builds only
- Exclude generated code (Hilt, R files, BuildConfig)
- Create combined coverage report tasks

## Generating Coverage Reports

### Step 1: Run Tests

Run unit tests and instrumented tests:
```bash
# Unit tests
./gradlew testDebugUnitTest

# Instrumented tests (requires connected device/emulator)
./gradlew connectedDebugAndroidTest
```

### Step 2: Generate Coverage Report

```bash
# For app module
./gradlew createDebugCombinedCoverageReport

# For library module
./gradlew :core:data:createDebugCombinedCoverageReport
```

### Step 3: View Reports

Reports are generated in:
- **XML**: `build/reports/jacoco/createDebugCombinedCoverageReport/createDebugCombinedCoverageReport.xml`
- **HTML**: `build/reports/jacoco/createDebugCombinedCoverageReport/html/index.html`

Open the HTML report in a browser to view coverage by package, class, and method.

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

Add coverage verification to your build:

```kotlin
// build.gradle.kts (project level or in a convention plugin)
tasks.withType<JacocoCoverageVerification>().configureEach {
    violationRules {
        rule {
            limit {
                minimum = "0.80".toBigDecimal() // 80% coverage
            }
        }
    }
}
```

## Best Practices

1. **Run coverage regularly**: Include in CI pipeline
2. **Focus on business logic**: Don't obsess over 100% coverage
3. **Exclude UI code**: UI tests provide better coverage for Compose
4. **Review trends**: Track coverage changes over time
5. **Don't game the metrics**: Write meaningful tests, not just for coverage

## Troubleshooting

### No coverage data generated

- Ensure tests are actually running and passing
- Check that tests are in the correct directories (`src/test/` for unit, `src/androidTest/` for instrumented)
- Verify debug build is being used (coverage only enabled for debug)

### Missing classes in report

- Check exclusion patterns in `config/Jacoco.kt`
- Ensure the module has the JaCoCo plugin applied

### Robolectric compatibility issues

The convention plugin automatically configures:
```kotlin
isIncludeNoLocationClasses = true
excludes = listOf("jdk.internal.*")
```

This fixes compatibility with Robolectric and JDK 11+.

## References

- [JaCoCo Documentation](https://www.jacoco.org/jacoco/trunk/doc/)
- [Android Testing: Code Coverage](https://developer.android.com/studio/test/code-coverage)
- Convention plugin implementations: `templates/convention/AndroidApplicationJacocoConventionPlugin.kt`, `templates/convention/AndroidLibraryJacocoConventionPlugin.kt`, `templates/convention/config/Jacoco.kt`
