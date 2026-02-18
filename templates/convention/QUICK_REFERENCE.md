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

| Plugin ID | File | Purpose | Common Apply To |
|-----------|------|---------|-----------------|
| `app.android.application` | `AndroidApplicationConventionPlugin.kt` | Root app module config | `:app` |
| `app.android.application.compose` | `AndroidApplicationComposeConventionPlugin.kt` | Compose for app | `:app` |
| `app.android.application.baseline` | `AndroidApplicationBaselineProfileConventionPlugin.kt` | Baseline profiles | `:app` |
| `app.android.library` | `AndroidLibraryConventionPlugin.kt` | Android library | `:core:*`, `:feature:*` |
| `app.android.library.compose` | `AndroidLibraryComposeConventionPlugin.kt` | Compose for library | UI libraries |
| `app.android.feature` | `AndroidFeatureConventionPlugin.kt` | Feature module | `:feature:auth`, etc. |
| `app.android.test` | `AndroidTestConventionPlugin.kt` | Test-only module | `:benchmark` |
| `app.android.room` | `AndroidRoomConventionPlugin.kt` | Room database | Modules with DB |
| `app.android.lint` | `AndroidLintConventionPlugin.kt` | Lint analysis | All Android modules |
| `app.hilt` | `HiltConventionPlugin.kt` | Hilt DI | All modules |
| `app.detekt` | `DetektConventionPlugin.kt` | Detekt analysis | All modules |
| `app.spotless` | `SpotlessConventionPlugin.kt` | Code formatting | All modules |
| `app.jvm.library` | `JvmLibraryConventionPlugin.kt` | Pure Kotlin lib | `:core:model` |
| `app.kotlin.serialization` | `KotlinSerializationConventionPlugin.kt` | JSON serialization | Network/data modules |
| `app.firebase` | `FirebaseConventionPlugin.kt` | Firebase | `:app` |

## Common Plugin Combinations

### Application Module
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
    alias(libs.plugins.app.firebase) // if using Firebase
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
│       ├── KotlinAndroid.kt
│       ├── AndroidCompose.kt
│       └── ... (all configuration files)
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

Add to `gradle/libs.versions.toml`:

```toml
[plugins]
# Convention plugins
app-android-application = { id = "app.android.application", version = "unspecified" }
app-android-application-compose = { id = "app.android.application.compose", version = "unspecified" }
app-android-application-baseline = { id = "app.android.application.baseline", version = "unspecified" }
app-android-library = { id = "app.android.library", version = "unspecified" }
app-android-library-compose = { id = "app.android.library.compose", version = "unspecified" }
app-android-feature = { id = "app.android.feature", version = "unspecified" }
app-android-test = { id = "app.android.test", version = "unspecified" }
app-android-room = { id = "app.android.room", version = "unspecified" }
app-android-lint = { id = "app.android.lint", version = "unspecified" }
app-hilt = { id = "app.hilt", version = "unspecified" }
app-detekt = { id = "app.detekt", version = "unspecified" }
app-spotless = { id = "app.spotless", version = "unspecified" }
app-jvm-library = { id = "app.jvm.library", version = "unspecified" }
app-kotlin-serialization = { id = "app.kotlin.serialization", version = "unspecified" }
app-firebase = { id = "app.firebase", version = "unspecified" }
```

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
- Kotlin Android configuration (compileSdk, minSdk, Java 17)
- Test instrumentation runner
- Gradle managed devices (Pixel 6 API 31, Pixel 8 API 34)
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

## Configuration Files

| File | Purpose |
|------|---------|
| `KotlinAndroid.kt` | Common Kotlin/Android config (SDK, Java 17, desugaring, opt-ins) |
| `AndroidCompose.kt` | Compose configuration (BOM, metrics, stability) |
| `ProjectExtensions.kt` | Version catalog access (`Project.libs`) |
| `GradleManagedDevices.kt` | Emulator configuration for tests (Pixel 6, Pixel 8) |
| `AndroidInstrumentationTest.kt` | Disable unnecessary Android tests |
| `PrintApksTask.kt` | Task to print APK paths |

## Version Catalog Entries (libs.versions.toml)

Required versions:
```toml
[versions]
compileSdk = "35"
minSdk = "24"
targetSdk = "35"
agp = "8.13.0"
kotlin = "2.2.21"
ksp = "2.2.21-1.0.32"
hilt = "2.50"
room = "2.6.1"
detekt = "2.0.0-alpha.1"
ktlint = "13.1.0"
```

Required libraries (for build-logic):
```toml
[libraries]
android-gradlePlugin = { group = "com.android.tools.build", name = "gradle", version.ref = "agp" }
kotlin-gradlePlugin = { group = "org.jetbrains.kotlin", name = "kotlin-gradle-plugin", version.ref = "kotlin" }
kotlin-composeGradlePlugin = { group = "org.jetbrains.kotlin", name = "compose-compiler-gradle-plugin", version.ref = "kotlin" }
ksp-gradlePlugin = { group = "com.google.devtools.ksp", name = "com.google.devtools.ksp.gradle.plugin", version.ref = "ksp" }
room-gradlePlugin = { group = "androidx.room", name = "room-gradle-plugin", version.ref = "room" }
plugin-detekt = { group = "io.gitlab.arturbosch.detekt", name = "detekt-gradle-plugin", version.ref = "detekt" }
```

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

| Issue | Solution |
|-------|----------|
| Plugin not found | Check `includeBuild("build-logic")` in root `settings.gradle.kts` |
| Version catalog not accessible | Verify `build-logic/settings.gradle.kts` references correct path |
| Type resolution fails in Detekt | Stop Gradle daemon, clean build, ensure Android/Kotlin plugins applied first |
| Resource prefix errors | Verify module path follows convention (`:feature:auth` → `feature_auth_`) |
| Compose metrics not generated | Add flags to `gradle.properties` and enable in individual modules |
| Hilt compiler errors | Ensure KSP is applied before Hilt plugin |
| Room schemas not found | Check `$projectDir/schemas/` directory exists |

## Migration Checklist

- [ ] Copy all `.kt` files to `build-logic/convention/src/main/kotlin/`
- [ ] Create `build-logic/convention/build.gradle.kts`
- [ ] Create `build-logic/settings.gradle.kts`
- [ ] Update root `settings.gradle.kts` with `includeBuild("build-logic")`
- [ ] Copy `detekt.yml.template` to `config/detekt.yml`
- [ ] Add version catalog entries for plugins
- [ ] Add version catalog entries for Gradle plugin dependencies
- [ ] Update module build files to use convention plugins
- [ ] Remove duplicated configuration from modules
- [ ] Test build with `./gradlew build`
- [ ] Verify Detekt with `./gradlew detekt`
- [ ] Verify tests with `./gradlew test`

## References

- [Sharing build logic (Gradle docs)](https://docs.gradle.org/current/userguide/sharing_build_logic_between_subprojects.html)
- [Now in Android - Convention plugins](https://github.com/android/nowinandroid/tree/main/build-logic)
- [Version catalogs (Gradle docs)](https://docs.gradle.org/current/userguide/platforms.html#sub:version-catalog)
