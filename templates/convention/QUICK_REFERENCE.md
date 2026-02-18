# Convention Plugins Quick Reference

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

## Configuration Files

| File | Purpose |
|------|---------|
| `KotlinAndroid.kt` | Common Kotlin/Android config (SDK, Java 17, desugaring) |
| `AndroidCompose.kt` | Compose configuration (BOM, metrics, stability) |
| `ProjectExtensions.kt` | Version catalog access (`Project.libs`) |
| `GradleManagedDevices.kt` | Emulator configuration for tests |
| `AndroidInstrumentationTest.kt` | Disable unnecessary Android tests |
| `PrintApksTask.kt` | Task to print APK paths |

## What Gets Configured

### By `AndroidApplicationConventionPlugin`
- `compileSdk`, `minSdk`, `targetSdk` (from version catalog)
- Java 17 + Kotlin JVM target 17
- Core library desugaring (for API < 26)
- Kotlin compiler opt-ins
- Test instrumentation runner
- Gradle managed devices (Pixel 6 API 31, Pixel 8 API 34)
- Lint (XML + SARIF reports)
- Print APKs task

### By `AndroidLibraryConventionPlugin`
- Everything from application plugin +
- Resource prefix based on module path (e.g., `feature_auth_`)
- Disables Android tests for modules without `src/androidTest/`
- Standard test dependencies (JUnit, kotlin-test)

### By `AndroidFeatureConventionPlugin`
- Applies `app.android.library` + `app.android.library.compose` + `app.hilt`
- Auto-adds dependencies:
  - `:core:ui`, `:core:domain`, `:core:data`
  - Lifecycle (ViewModel + runtime-compose)
  - Navigation3 (runtime + compose)

### By Compose Plugins
- Compose compiler plugin
- Compose BOM (all Compose versions aligned)
- UI tooling (preview + debug)
- Compiler metrics/reports (if enabled via gradle.properties)
- Stability configuration (from `compose_compiler_config.conf`)

### By `HiltConventionPlugin`
- Hilt plugin + KSP
- Hilt runtime + compiler
- Test dependencies (hilt-android-testing)
- KSP for all variants (main, test, androidTest)

### By `DetektConventionPlugin`
- Detekt plugin
- Compose rules for Detekt
- Central config (`config/detekt.yml`)
- Module overrides (optional `detekt.yml` in module)
- Baseline support (`detekt-baseline.xml`)
- Type resolution enabled
- XML, HTML, SARIF reports

## Project Structure

```
project-root/
├── build-logic/
│   ├── convention/
│   │   ├── build.gradle.kts
│   │   └── src/main/kotlin/
│   │       ├── AndroidApplicationConventionPlugin.kt
│   │       ├── AndroidLibraryConventionPlugin.kt
│   │       ├── ... (all convention plugins)
│   │       ├── KotlinAndroid.kt
│   │       ├── AndroidCompose.kt
│   │       └── ... (all config files)
│   └── settings.gradle.kts
├── config/
│   └── detekt.yml (from templates/detekt.yml.template)
├── compose_compiler_config.conf (optional)
├── gradle/
│   └── libs.versions.toml
└── settings.gradle.kts (includes build-logic)
```

## Required Files

1. **config/detekt.yml** - Copy from `templates/detekt.yml.template`
2. **compose_compiler_config.conf** (optional) - For Compose stability
3. **build-logic/settings.gradle.kts** - Must reference version catalog

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

Required plugins (for module build files):
```toml
[plugins]
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
```

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
