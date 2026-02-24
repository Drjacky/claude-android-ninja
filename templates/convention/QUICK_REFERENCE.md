# Convention Plugins - Setup & Reference

This directory contains Gradle convention plugins for consistent build configuration across modules. Convention plugins encapsulate common build configuration to reduce duplication and ensure consistency.

## Table of Contents
1. [Plugin Mapping](#plugin-mapping-table)
2. [Common Plugin Combinations](#common-plugin-combinations)
3. [Setup Instructions](#setup-instructions)
4. [What Each Plugin Provides](#what-each-plugin-provides)
5. [Version Catalog Requirements](#version-catalog-entries-libsversiontoml)
6. [Troubleshooting](#troubleshooting)

## Plugin Mapping Table

| Plugin ID                           | File                                                    | Purpose                      | Common Apply To                  |
|-------------------------------------|---------------------------------------------------------|------------------------------|----------------------------------|
| `app.android.application`           | `AndroidApplicationConventionPlugin.kt`                 | Root app module config       | `:app`                           |
| `app.android.application.compose`   | `AndroidApplicationComposeConventionPlugin.kt`          | Compose for app              | `:app`                           |
| `app.android.application.baseline`  | `AndroidApplicationBaselineProfileConventionPlugin.kt`  | Baseline profiles            | `:app`                           |
| `app.android.application.jacoco`    | `AndroidApplicationJacocoConventionPlugin.kt`           | Code coverage for app        | `:app` (when coverage needed)    |
| `app.android.library`               | `AndroidLibraryConventionPlugin.kt`                     | Android library              | `:core:*`, `:feature:*`          |
| `app.android.library.compose`       | `AndroidLibraryComposeConventionPlugin.kt`              | Compose for library          | UI libraries                     |
| `app.android.library.jacoco`        | `AndroidLibraryJacocoConventionPlugin.kt`               | Code coverage for library    | Libraries (when coverage needed) |
| `app.android.feature`               | `AndroidFeatureConventionPlugin.kt`                     | Feature module               | `:feature:auth`, etc.            |
| `app.android.test`                  | `AndroidTestConventionPlugin.kt`                        | Test-only module             | `:benchmark`                     |
| `app.android.room`                  | `AndroidRoomConventionPlugin.kt`                        | Room database                | Modules with DB                  |
| `app.android.lint`                  | `AndroidLintConventionPlugin.kt`                        | Lint analysis                | All Android modules              |
| `app.hilt`                          | `HiltConventionPlugin.kt`                               | Hilt DI                      | All modules                      |
| `app.detekt`                        | `DetektConventionPlugin.kt`                             | Detekt analysis              | All modules                      |
| `app.spotless`                      | `SpotlessConventionPlugin.kt`                           | Code formatting              | All modules                      |
| `app.jvm.library`                   | `JvmLibraryConventionPlugin.kt`                         | Pure Kotlin lib              | `:core:model`                    |
| `app.kotlin.serialization`          | `KotlinSerializationConventionPlugin.kt`                | JSON serialization           | Network/data modules             |
| `app.firebase`                      | `FirebaseConventionPlugin.kt`                           | Firebase Crashlytics         | `:app`                           |
| `app.sentry`                        | `SentryConventionPlugin.kt`                             | Sentry crash reporting       | `:app`                           |

## Common Plugin Combinations

### Application Module
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
    alias(libs.plugins.app.firebase) // if using Firebase Crashlytics
    alias(libs.plugins.app.sentry) // OR if using Sentry (not both)
    alias(libs.plugins.app.android.application.jacoco) // if code coverage needed
}
```

### Feature Module
```kotlin
plugins {
    alias(libs.plugins.app.android.feature) // includes library + compose + hilt
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
}
```

### Data Layer (with Room)
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.android.room)
    alias(libs.plugins.app.kotlin.serialization)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.android.library.jacoco) // if code coverage needed
}
```

### UI Library (Compose)
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.android.library.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
}
```

### Domain/Model (Pure Kotlin)
```kotlin
plugins {
    alias(libs.plugins.app.jvm.library)
    alias(libs.plugins.app.kotlin.serialization)
    alias(libs.plugins.app.detekt)
}
```

## Setup Instructions

### 1. Copy Convention Plugins

Copy all `.kt` files from this directory to:
```
build-logic/convention/src/main/kotlin/
```

### 2. Create build-logic Structure

```
build-logic/
├── convention/
│   ├── build.gradle.kts (from build.gradle.kts in this folder)
│   └── src/main/kotlin/
│       ├── AndroidApplicationConventionPlugin.kt
│       ├── AndroidLibraryConventionPlugin.kt
│       ├── ... (all other .kt files)
│       └── config/
│           ├── KotlinAndroid.kt
│           ├── AndroidCompose.kt
│           └── ... (all configuration files)
└── settings.gradle.kts
```

### 3. Create build-logic/settings.gradle.kts

```kotlin
dependencyResolutionManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    versionCatalogs {
        create("libs") {
            from(files("../gradle/libs.versions.toml"))
        }
    }
}

rootProject.name = "build-logic"
include(":convention")
```

### 4. Include in Root settings.gradle.kts

```kotlin
pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
```

### 5. Register Plugins in Version Catalog

Convention plugin entries are already defined in `templates/libs.versions.toml.template` under the `[plugins]` section (look for the "Convention plugins" comment).

Copy the entire `[plugins]` section from the template to your project's `gradle/libs.versions.toml`.

### 6. Create Detekt Configuration

Create `config/detekt.yml` in project root (copy from `templates/detekt.yml.template`).

### 7. Create Compose Stability Configuration (Optional)

Create `compose_compiler_config.conf` in project root:

```
// Classes that should be considered stable for Compose
com.example.core.model.*
```

## What Each Plugin Provides

### Android Application Plugin
- Android configuration with built-in Kotlin (compileSdk, minSdk, Java 17)
- Test instrumentation runner
- Gradle managed devices (Pixel 6 API 31, Pixel 8 API 34, Pixel 9 API 36)
- Lint configuration
- Core library desugaring (for API < 26)
- Print APKs task

### Android Library Plugin
- Same as application + resource prefix based on module path (e.g., `feature_auth_`)
- Disables Android tests for modules without `src/androidTest/`
- Standard testing dependencies (JUnit, kotlin-test)

### Compose Plugins
- Compose compiler plugin
- Compose BOM dependency (all Compose versions aligned)
- UI tooling (preview + debug)
- Compiler metrics/reports (if enabled via gradle.properties)
- Stability configuration (from `compose_compiler_config.conf`)

### Feature Plugin
- Android library + Compose + Hilt
- Auto-adds dependencies: `:core:ui`, `:core:domain`, `:core:data`
- Lifecycle (ViewModel + runtime-compose)
- Navigation3 (runtime + compose)
- Adaptive layouts (adaptive, adaptive-layout, adaptive-navigation, navigation-suite)
- Managed devices

### Room Plugin
- Room plugin + KSP
- Room runtime + KTX
- Room compiler (KSP)
- Schema directory for migrations

### Hilt Plugin
- Hilt Android + KSP compiler
- Test dependencies (hilt-android-testing)
- KSP for test variants (main, test, androidTest)

### Detekt Plugin
- Detekt plugin + Compose rules
- Central config (`config/detekt.yml`)
- Module-specific overrides (optional `detekt.yml`)
- Baseline support (`detekt-baseline.xml`)
- Type resolution enabled
- XML, HTML, SARIF reports

### Spotless Plugin
- ktlint for Kotlin formatting
- Format .kts files
- Format XML (for Android modules)
- Trim trailing whitespace
- Ensure newline at end of file

### Firebase Plugin
- Google Services plugin
- Firebase Crashlytics plugin
- Firebase BOM dependency
- Crashlytics and Analytics libraries
- Crashlytics configuration (native symbols, debug builds)

### Sentry Plugin
- Sentry Android Gradle plugin
- Sentry Kotlin Compiler plugin (automatic @Composable tagging)
- Sentry Android SDK
- Sentry Compose integration
- Automatic mapping file upload and source context

**Note:** Use either `app.firebase` OR `app.sentry`, not both (unless implementing dual reporting).

### JaCoCo Plugins (Code Coverage)
- JaCoCo plugin + version configuration
- Combined coverage reports (unit + instrumented tests)
- Exclusions for generated code (Hilt, R files, BuildConfig)
- XML and HTML reports
- Compatible with Robolectric
- Task: `create{Variant}CombinedCoverageReport`

For usage steps (running tests, generating reports, viewing output), see `references/android-code-coverage.md` → "Generating Coverage Reports".

## Configuration Files

Configuration utilities are located in the `config/` subdirectory:

| File                                   | Purpose                                                          |
|----------------------------------------|------------------------------------------------------------------|
| `config/KotlinAndroid.kt`              | Common Kotlin/Android config (SDK, Java 17, desugaring, opt-ins) |
| `config/AndroidCompose.kt`             | Compose configuration (BOM, metrics, stability)                  |
| `config/ProjectExtensions.kt`          | Version catalog access (`Project.libs`)                          |
| `config/GradleManagedDevices.kt`       | Emulator configuration for tests (Pixel 6, Pixel 8, Pixel 9)     |
| `config/AndroidInstrumentationTest.kt` | Disable unnecessary Android tests                                |
| `config/PrintApksTask.kt`              | Task to print APK paths                                          |

## Version Catalog Entries (libs.versions.toml)

All required versions, libraries, and plugin entries are defined in `templates/libs.versions.toml.template`. Copy the entire file to your project's `gradle/libs.versions.toml` or merge the relevant sections if you have an existing version catalog.

## gradle.properties Flags

```properties
# Enable Compose compiler metrics
enableComposeCompilerMetrics=true
# Enable Compose compiler reports
enableComposeCompilerReports=true
```

Reports will be generated in:
- `build/compose-metrics/`
- `build/compose-reports/`

## Benefits

1. **Consistency**: All modules use the same configuration
2. **Maintainability**: Update configuration in one place
3. **Readability**: Module build files are concise and focused
4. **Type Safety**: Kotlin DSL with IDE support
5. **Reusability**: Share configurations across projects

## Troubleshooting

| Issue                           | Solution                                                                     |
|---------------------------------|------------------------------------------------------------------------------|
| Plugin not found                | Check `includeBuild("build-logic")` in root `settings.gradle.kts`            |
| Version catalog not accessible  | Verify `build-logic/settings.gradle.kts` references correct path             |
| Type resolution fails in Detekt | Stop Gradle daemon, clean build, ensure Android/Kotlin plugins applied first |
| Resource prefix errors          | Verify module path follows convention (`:feature:auth` → `feature_auth_`)    |
| Compose metrics not generated   | Add flags to `gradle.properties` and enable in individual modules            |
| Hilt compiler errors            | Ensure KSP is applied before Hilt plugin                                     |
| Room schemas not found          | Check `$projectDir/schemas/` directory exists                                |

## Migration Checklist
.
## Setup Checklist

- [ ] Copy all `.kt` files to `build-logic/convention/src/main/kotlin/`
- [ ] Add `build-logic/convention/build.gradle.kts` (from build.gradle.kts in this folder)
- [ ] Add `build-logic/settings.gradle.kts` (see step 3 above)
- [ ] Update root `settings.gradle.kts` with `includeBuild("build-logic")`
- [ ] Copy `detekt.yml.template` to `config/detekt.yml`
- [ ] Add convention plugin entries to `gradle/libs.versions.toml` (from template)
- [ ] Ensure Gradle plugin dependencies are in `gradle/libs.versions.toml` (from template)
- [ ] Update module build files to use convention plugins
- [ ] Remove duplicated configuration from modules
- [ ] Test build with `./gradlew build`
- [ ] Verify Detekt with `./gradlew detekt`
- [ ] Verify tests with `./gradlew test`

## References

- [Sharing build logic (Gradle docs)](https://docs.gradle.org/current/userguide/sharing_build_logic_between_subprojects.html)
- [Now in Android - Convention plugins](https://github.com/android/nowinandroid/tree/main/build-logic)
- [Version catalogs (Gradle docs)](https://docs.gradle.org/current/userguide/platforms.html#sub:version-catalog)
