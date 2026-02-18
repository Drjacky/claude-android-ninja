# Convention Plugins

This directory contains Gradle convention plugins for consistent build configuration across modules.

## Overview

Convention plugins encapsulate common build configuration to reduce duplication and ensure consistency. Instead of copying the same configuration to every module, apply a convention plugin that provides the configuration you need.

## Available Plugins

### Android Plugins

| Plugin ID                          | Purpose                           | Apply To                                  |
|------------------------------------|-----------------------------------|-------------------------------------------|
| `app.android.application`          | Android application configuration | `:app` module                             |
| `app.android.application.compose`  | Compose for application           | `:app` with Compose UI                    |
| `app.android.application.baseline` | Baseline profiles                 | `:app` for performance                    |
| `app.android.library`              | Android library configuration     | Library modules (`:core:*`, `:feature:*`) |
| `app.android.library.compose`      | Compose for library               | Libraries with Compose UI                 |
| `app.android.feature`              | Feature module (UI + ViewModel)   | `:feature:*` modules                      |
| `app.android.test`                 | Android test module               | `:benchmark`, `:baselineprofile`          |
| `app.android.room`                 | Room database                     | Modules using Room                        |
| `app.android.lint`                 | Android Lint configuration        | All Android modules                       |

### Kotlin Plugins

| Plugin ID                  | Purpose                 | Apply To                       |
|----------------------------|-------------------------|--------------------------------|
| `app.jvm.library`          | Pure Kotlin/JVM library | `:core:model`, utility modules |
| `app.kotlin.serialization` | kotlinx-serialization   | Modules needing JSON           |

### Quality & Tooling Plugins

| Plugin ID      | Purpose                           | Apply To               |
|----------------|-----------------------------------|------------------------|
| `app.hilt`     | Hilt dependency injection         | All modules using Hilt |
| `app.detekt`   | Detekt static analysis            | All modules            |
| `app.spotless` | Code formatting (ktlint)          | All modules            |
| `app.firebase` | Firebase (Crashlytics, Analytics) | `:app` module          |

## Usage Examples

### Application Module (app/build.gradle.kts)

```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.firebase)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
}

android {
    namespace = "com.example.app"
    
    defaultConfig {
        applicationId = "com.example.app"
        versionCode = 1
        versionName = "1.0.0"
    }
}
```

### Feature Module (feature/auth/build.gradle.kts)

```kotlin
plugins {
    alias(libs.plugins.app.android.feature)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
}

android {
    namespace = "com.example.feature.auth"
}
```

### Data Module (core/data/build.gradle.kts)

```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.android.room)
    alias(libs.plugins.app.kotlin.serialization)
    alias(libs.plugins.app.detekt)
}

android {
    namespace = "com.example.core.data"
}
```

### Pure Kotlin Module (core/model/build.gradle.kts)

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
app-android-library = { id = "app.android.library", version = "unspecified" }
app-android-library-compose = { id = "app.android.library.compose", version = "unspecified" }
app-android-feature = { id = "app.android.feature", version = "unspecified" }
app-android-room = { id = "app.android.room", version = "unspecified" }
app-hilt = { id = "app.hilt", version = "unspecified" }
app-detekt = { id = "app.detekt", version = "unspecified" }
app-spotless = { id = "app.spotless", version = "unspecified" }
app-jvm-library = { id = "app.jvm.library", version = "unspecified" }
app-kotlin-serialization = { id = "app.kotlin.serialization", version = "unspecified" }
# ... add others as needed
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
- Gradle managed devices
- Lint configuration
- Core library desugaring
- Print APKs task

### Android Library Plugin
- Same as application + resource prefix based on module path
- Disables Android tests for modules without `src/androidTest`
- Standard testing dependencies (JUnit, kotlin-test)

### Compose Plugins
- Compose compiler plugin
- Compose BOM dependency
- UI tooling (preview + debug)
- Compiler metrics/reports (if enabled in gradle.properties)
- Stability configuration

### Feature Plugin
- Android library + Compose + Hilt
- Dependencies: `:core:ui`, `:core:domain`, `:core:data`
- Lifecycle (ViewModel + runtime-compose)
- Navigation3
- Managed devices

### Room Plugin
- Room plugin + KSP
- Room runtime + KTX
- Room compiler (KSP)
- Schema directory for migrations

### Hilt Plugin
- Hilt Android + KSP compiler
- Test dependencies (hilt-android-testing)
- KSP for test variants

### Detekt Plugin
- Detekt plugin + Compose rules
- Central config (`config/detekt.yml`)
- Module-specific overrides (optional `detekt.yml`)
- Type resolution enabled
- XML, HTML, SARIF reports

### Spotless Plugin
- ktlint for Kotlin formatting
- Format .kts files
- Format XML (for Android modules)
- Trim trailing whitespace
- Ensure newline at end of file

## Benefits

1. **Consistency**: All modules use the same configuration
2. **Maintainability**: Update configuration in one place
3. **Readability**: Module build files are concise and focused
4. **Type Safety**: Kotlin DSL with IDE support
5. **Reusability**: Share configurations across projects

## Troubleshooting

### Plugin not found
- Ensure `build-logic` is included in root `settings.gradle.kts`
- Check plugin registration in `build-logic/convention/build.gradle.kts`
- Verify plugin ID matches between registration and usage

### Version catalog not accessible
- Ensure `libs` is passed from root project
- Check `build-logic/settings.gradle.kts` has correct path to version catalog

### Type resolution errors in Detekt
- Run `./gradlew --stop` to stop Gradle daemon
- Clean build with `./gradlew clean`
- Ensure all Android/Kotlin plugins are applied before Detekt

## References

- [Sharing build logic (Gradle docs)](https://docs.gradle.org/current/userguide/sharing_build_logic_between_subprojects.html)
- [Now in Android - Convention plugins](https://github.com/android/nowinandroid/tree/main/build-logic)
- [Version catalogs (Gradle docs)](https://docs.gradle.org/current/userguide/platforms.html#sub:version-catalog)
