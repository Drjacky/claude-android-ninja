# Convention Plugins - Setup & Reference

Required: copy sources from `assets/convention/` into `build-logic/` per [Setup Instructions](#setup-instructions); consumer projects never edit `assets/convention/` in place.

Forbidden: drift `build-logic` from `assets/convention/` without re-copying — stale plugins ship wrong SDKs, Detekt rules, and Room 3 wiring.

## Table of Contents

- [Plugin Mapping](#plugin-mapping-table)
- [Common Plugin Combinations](#common-plugin-combinations)
- [Setup Instructions](#setup-instructions)
- [What Each Plugin Provides](#what-each-plugin-provides)
- [Version Catalog Requirements](#version-catalog-entries-libsversiontoml)
- [Troubleshooting](#troubleshooting)

## Plugin Mapping Table

| Plugin ID                          | File                                                   | Purpose                    | Common Apply To                  |
|------------------------------------|--------------------------------------------------------|----------------------------|----------------------------------|
| `app.android.application`          | `AndroidApplicationConventionPlugin.kt`                | Root app module config     | `:app`                           |
| `app.android.application.compose`  | `AndroidApplicationComposeConventionPlugin.kt`         | Compose for app            | `:app`                           |
| `app.android.application.baseline` | `AndroidApplicationBaselineProfileConventionPlugin.kt` | Baseline profiles          | `:app`                           |
| `app.android.application.jacoco`   | `AndroidApplicationJacocoConventionPlugin.kt`          | Code coverage for app      | `:app` (when coverage needed)    |
| `app.android.library`              | `AndroidLibraryConventionPlugin.kt`                    | Android library            | `:core:*`, `:feature:*`          |
| `app.android.library.compose`      | `AndroidLibraryComposeConventionPlugin.kt`             | Compose for library        | UI libraries                     |
| `app.android.library.jacoco`       | `AndroidLibraryJacocoConventionPlugin.kt`              | Code coverage for library  | Libraries (when coverage needed) |
| `app.android.feature`              | `AndroidFeatureConventionPlugin.kt`                    | Feature module             | `:feature:auth`, etc.            |
| `app.android.test`                 | `AndroidTestConventionPlugin.kt`                       | Test-only module           | `:benchmark`                     |
| `app.android.room`                 | `AndroidRoomConventionPlugin.kt`                       | Room 3 database            | Modules with DB                  |
| `app.android.lint`                 | `AndroidLintConventionPlugin.kt`                       | Lint analysis              | All Android modules              |
| `app.hilt`                         | `HiltConventionPlugin.kt`                              | Hilt DI                    | All modules                      |
| `app.detekt`                       | `DetektConventionPlugin.kt`                            | Detekt analysis            | All modules                      |
| `app.spotless`                     | `SpotlessConventionPlugin.kt`                          | Code formatting            | All modules                      |
| `app.jvm.library`                  | `JvmLibraryConventionPlugin.kt`                        | Pure Kotlin lib            | `:core:model`                    |
| `app.kotlin.serialization`         | `KotlinSerializationConventionPlugin.kt`               | JSON serialization         | Network/data modules             |
| `app.firebase`                     | `FirebaseConventionPlugin.kt`                          | Firebase Crashlytics       | `:app`                           |
| `app.sentry`                       | `SentryConventionPlugin.kt`                            | Sentry crash reporting     | `:app`                           |
| `app.play.vitals`                  | `PlayVitalsReportingConventionPlugin.kt`               | Root-only Play Vitals task | **Root** `build.gradle.kts` only |

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

### Root project (`app.play.vitals`)

Required: apply `app.play.vitals` only in the **root** `build.gradle.kts`, never in `:app`:
```kotlin
plugins {
    // alias(libs.plugins.app.play.vitals)
}
```
Play Vitals reporting plugin: [android-performance.md](../../references/android-performance.md).

## Setup Instructions

### Copy convention plugins

Required: copy every `.kt` from `assets/convention/` into:
```
build-logic/convention/src/main/kotlin/
```

### Create `build-logic` tree

```
build-logic/
├── convention/
│   ├── build.gradle.kts (from `assets/convention/build.gradle.kts`)
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

### Create `build-logic/settings.gradle.kts`

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

### Wire `includeBuild("build-logic")` in root `settings.gradle.kts`

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

### Register plugins in the version catalog

Required: merge the `[plugins]` block from `assets/libs.versions.toml.template` (search comment `Convention plugins`) into `gradle/libs.versions.toml`.

### Create Detekt configuration

Required: `config/detekt.yml` at repo root — start from `assets/detekt.yml.template`.

### Compose stability configuration

Use when: enabling Compose compiler stability packages for `core` model classes — add `compose_compiler_config.conf` at repo root:

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

### Room Plugin (Room 3)
- `androidx.room3` Gradle plugin + KSP
- `room3-runtime` + `sqlite-bundled` (for `BundledSQLiteDriver()` on `Room.databaseBuilder`)
- `room3-compiler` (KSP); DAOs use **`suspend`** and **`Flow`** (no separate Room KTX artifact)
- `room3 { schemaDirectory(...) }` for schema export and auto-migrations

### Hilt Plugin
- Hilt Android + KSP compiler
- Test dependencies (hilt-android-testing)
- KSP for test variants (main, test, androidTest)

### Detekt Plugin
- Detekt plugin + Compose rules
- Central config (`config/detekt.yml`)
- Module-specific overrides (`detekt.yml` beside the module when needed)
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

Forbidden: apply `app.firebase` and `app.sentry` together unless the product intentionally dual-reports crashes to both backends.

### JaCoCo Plugins (Code Coverage)
- JaCoCo plugin + version configuration
- Combined coverage reports (unit + instrumented tests)
- Exclusions for generated code (Hilt, R files, BuildConfig)
- XML and HTML reports
- Compatible with Robolectric
- Task: `create{Variant}CombinedCoverageReport`

JaCoCo workflow (commands, reports): [android-code-coverage.md](../../references/android-code-coverage.md).

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

Required: align `gradle/libs.versions.toml` with `assets/libs.versions.toml.template` — full copy for greenfield repos, selective merge when preserving existing catalog blocks.

## gradle.properties Flags

```properties
# Enable Compose compiler metrics
enableComposeCompilerMetrics=true
# Enable Compose compiler reports
enableComposeCompilerReports=true
```

Required output paths after enabling metrics:

- `build/compose-metrics/`
- `build/compose-reports/`

## Outcomes

| Outcome             | Mechanism                                  |
|---------------------|--------------------------------------------|
| Consistent SDKs     | Single `KotlinAndroid.kt` source           |
| Single edit point   | Convention plugins + shared `config/`      |
| Thin module scripts | `plugins { alias(...) }` only              |
| Typed Gradle DSL    | Kotlin + version catalog accessors         |
| Portable templates  | `assets/convention/` + `assets/*.template` |

## Troubleshooting

| Issue                           | Fix                                                                                              |
|---------------------------------|--------------------------------------------------------------------------------------------------|
| Plugin not found                | Add `includeBuild("build-logic")` to root `settings.gradle.kts`                                  |
| Version catalog not accessible  | Fix `build-logic/settings.gradle.kts` `from(files("../gradle/libs.versions.toml"))` path         |
| Type resolution fails in Detekt | `./gradlew --stop`; `./gradlew clean`; apply Android + Kotlin plugins before Detekt              |
| Resource prefix errors          | Module path must map to prefix (`:feature:auth` → `feature_auth_`)                               |
| Compose metrics not generated   | Set `gradle.properties` flags; apply Compose plugin in the module emitting UI                    |
| Hilt compiler errors            | Apply KSP plugin before Hilt in the same `plugins` block                                         |
| Room schemas not found          | Create `$projectDir/schemas/` or disable export until migrations exist                           |
| Room 3 build fails (driver)     | `Room.databaseBuilder` must call `.setDriver(BundledSQLiteDriver())` (or another `SQLiteDriver`) |

## Migration Checklist

Room 2→3, Navigation, Compose: [migration.md](../../references/migration.md).

## Setup Checklist

- [ ] Copy all `.kt` files to `build-logic/convention/src/main/kotlin/`
- [ ] Add `build-logic/convention/build.gradle.kts` (copy from `assets/convention/build.gradle.kts`)
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
