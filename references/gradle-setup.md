# Gradle & Build Configuration

Required: Gradle 9 / AGP 9.0, JVM 17+, KSP (never kapt), version catalog, convention plugins in `build-logic/convention`. Module structure follows [modularization.md](/references/modularization.md).

## AGP 9 Key Changes

- **Built-in Kotlin**: AGP 9 has built-in Kotlin support. The `org.jetbrains.kotlin.android` plugin is no longer needed for Android modules. Remove it from all `build.gradle.kts` files and convention plugins.
- **Compose Compiler**: The `org.jetbrains.kotlin.plugin.compose` plugin is still required for Compose modules.
- **compileSdk syntax**: Use `compileSdk { version = release(36) }` instead of `compileSdk = 36`.
- **Gradle Managed Devices**: Use `localDevices { create("name") { ... } }` instead of `devices { maybeCreate("name", ManagedVirtualDevice::class.java).apply { ... } }`. Device groups use `create("ci")` instead of `maybeCreate("ci")`. Reference devices via `localDevices[name]` instead of `devices[name]`.
- **Removed gradle.properties**: `org.gradle.configureondemand`, `android.enableBuildCache`, `android.enableJetifier`, `android.defaults.buildfeatures.aidl`, `android.defaults.buildfeatures.renderscript`, `android.defaults.buildfeatures.resvalues`, `android.defaults.buildfeatures.shaders`, and `org.gradle.configuration-cache.problems=warn` are removed.
- **CommonExtension**: Type parameters removed; use `CommonExtension` instead of `CommonExtension<*, *, *, *, *, *>`.
- **KotlinAndroidProjectExtension**: Not registered with built-in Kotlin; configure compiler options via `tasks.withType<KotlinCompile>().configureEach { compilerOptions { ... } }` instead.
- **Hilt**: Minimum version **2.59.2** required for AGP 9 (older versions access removed `BaseExtension`).
- **KSP**: Minimum version **2.3.6** required for AGP 9. Use `2.x` suffix (e.g., `2.3.6-…`) instead of `1.x` (e.g., `2.2.21-1.0.32`); `1.x` KSP is incompatible with AGP 9.
- **kapt fallback (`legacy-kapt`)**: Use KSP everywhere it exists. If a processor has no KSP equivalent under AGP 9, use the **`org.jetbrains.kotlin.kapt`** plugin (a.k.a. `legacy-kapt`) for that single module only; the new built-in Kotlin pipeline does not run kapt automatically.
- **Type-safe project accessors**: Enabled by default in Gradle 9; `enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")` is no longer needed in `settings.gradle.kts`.
- **JVM 17 minimum**: Gradle 9 requires JVM 17+ to run.
- **Legacy API removal**: `BaseExtension`, `applicationVariants.all`, `Convention` type, and `com.android.build.gradle.api.*` legacy APIs are removed. Use `androidComponents` API instead.

### AGP 9 Migration: Post-Upgrade Cleanup

After completing the AGP 9 upgrade, remove these now-obsolete flags from `gradle.properties` (they were only needed during incremental migration and are no-ops or warnings under AGP 9):

- `android.builtInKotlin`
- `android.newDsl`
- `android.uniquePackageNames`
- `android.enableAppCompileTimeRClass`

Do **not** add `android.disallowKotlinSourceSets=false`. It re-enables a removed escape hatch and masks real migration work.

### AGP 9 Verification

Run after every AGP 9 build-config change. Do **not** run `clean` first - it does not validate the DSL.

```bash
./gradlew help              # Gradle IDE-equivalent sync
./gradlew build --dry-run   # Configures every task without executing
```

On failure, the failing task name identifies the module / DSL block to fix.

### AGP 9 Toolchain Compatibility Notes

- **Paparazzi**: Versions **`<= 2.0.0-alpha04`** are incompatible with AGP 9. Upgrade to a release that explicitly supports AGP 9 before flipping the AGP version, or temporarily disable Paparazzi modules.
- **KMP**: This AGP 9 path is Android-only. Kotlin Multiplatform projects require a separate migration.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Version Catalog](#version-catalog)
3. [Convention Plugins](#convention-plugins) (includes [root-level reporting task registration](#registering-a-root-level-reporting-task-play-vitals-example))
4. [Code Quality (Detekt)](#code-quality-detekt)
5. [Module Build Files](#module-build-files)
6. [Build Variants & Optimization](#build-variants--optimization)
7. [Build Performance](#build-performance)

## Project Structure

Module layout and naming: [modularization.md](/references/modularization.md).

## Version Catalog

Source of truth: `assets/libs.versions.toml.template`. Generate / update `gradle/libs.versions.toml` from it.

Required:
- KSP for all annotation processing; kapt is forbidden.
- Room 3 via `androidx.room3` artifacts and the `androidx.room3` plugin; use `sqlite-bundled` with `BundledSQLiteDriver()` (configured by the `app.android.room` convention plugin).
- Compose compiler via the `kotlin-compose` plugin (Kotlin 2.0+).
- Use `unit-test` and `android-test` bundles for testing dependencies.

## Convention Plugins

Plugin sources live in `assets/convention/`:
- `*ConventionPlugin.kt` (incl. `PlayVitalsReportingConventionPlugin.kt` for root-only Play Vitals), `PlayVitalsReportingTask.kt`, and related `.kt` files.
- `config/` (`KotlinAndroid.kt`, `AndroidCompose.kt`, `Jacoco.kt`, …).
- `build.gradle.kts`, `QUICK_REFERENCE.md`.

Copy them to `build-logic/convention/src/main/kotlin/`.

### Build Logic Setup

`build-logic/convention/build.gradle.kts`:
```kotlin
plugins {
    `kotlin-dsl`
}

group = "com.example.buildlogic"

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.kotlin.composeGradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.room3.gradlePlugin)
    implementation(libs.plugin.detekt)
    implementation(libs.kotlinx.coroutines.core)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "app.android.application"
            implementationClass = "AndroidApplicationConventionPlugin"
        }
        register("androidApplicationCompose") {
            id = "app.android.application.compose"
            implementationClass = "AndroidApplicationComposeConventionPlugin"
        }
        register("androidApplicationBaselineProfile") {
            id = "app.android.application.baseline"
            implementationClass = "AndroidApplicationBaselineProfileConventionPlugin"
        }
        register("androidLibrary") {
            id = "app.android.library"
            implementationClass = "AndroidLibraryConventionPlugin"
        }
        register("androidLibraryCompose") {
            id = "app.android.library.compose"
            implementationClass = "AndroidLibraryComposeConventionPlugin"
        }
        register("androidFeature") {
            id = "app.android.feature"
            implementationClass = "AndroidFeatureConventionPlugin"
        }
        register("androidTest") {
            id = "app.android.test"
            implementationClass = "AndroidTestConventionPlugin"
        }
        register("androidRoom") {
            id = "app.android.room"
            implementationClass = "AndroidRoomConventionPlugin"
        }
        register("androidLint") {
            id = "app.android.lint"
            implementationClass = "AndroidLintConventionPlugin"
        }
        register("hilt") {
            id = "app.hilt"
            implementationClass = "HiltConventionPlugin"
        }
        register("detekt") {
            id = "app.detekt"
            implementationClass = "DetektConventionPlugin"
        }
        register("spotless") {
            id = "app.spotless"
            implementationClass = "SpotlessConventionPlugin"
        }
        register("jvmLibrary") {
            id = "app.jvm.library"
            implementationClass = "JvmLibraryConventionPlugin"
        }
        register("kotlinSerialization") {
            id = "app.kotlin.serialization"
            implementationClass = "KotlinSerializationConventionPlugin"
        }
        register("firebase") {
            id = "app.firebase"
            implementationClass = "FirebaseConventionPlugin"
        }
        register("playVitals") {
            id = "app.play.vitals"
            implementationClass = "PlayVitalsReportingConventionPlugin"
        }
    }
}
```

### Convention Plugin Files

Implementations in `assets/convention/`:

**Core Plugins:**
- `AndroidApplicationConventionPlugin.kt` - Root app module configuration
- `AndroidLibraryConventionPlugin.kt` - Android library modules
- `AndroidFeatureConventionPlugin.kt` - Feature modules with UI + ViewModel
- `AndroidTestConventionPlugin.kt` - Test-only modules

**Compose & Build Plugins:**
- `AndroidApplicationComposeConventionPlugin.kt` - Compose for application
- `AndroidLibraryComposeConventionPlugin.kt` - Compose for libraries
- `AndroidApplicationBaselineProfileConventionPlugin.kt` - Baseline profiles
- `AndroidRoomConventionPlugin.kt` - Room 3 database (`androidx.room3`, KSP, `sqlite-bundled`)
- `AndroidLintConventionPlugin.kt` - Android Lint configuration

**Testing & Quality Plugins:**
- `AndroidApplicationJacocoConventionPlugin.kt` - Code coverage for apps
- `AndroidLibraryJacocoConventionPlugin.kt` - Code coverage for libraries
- `HiltConventionPlugin.kt` - Hilt dependency injection
- `DetektConventionPlugin.kt` - Static analysis
- `SpotlessConventionPlugin.kt` - Code formatting

**Other Plugins:**
- `JvmLibraryConventionPlugin.kt` - Pure Kotlin libraries
- `KotlinSerializationConventionPlugin.kt` - JSON serialization
- `FirebaseConventionPlugin.kt` - Firebase Crashlytics integration
- `SentryConventionPlugin.kt` - Sentry crash reporting integration
- `PlayVitalsReportingConventionPlugin.kt` - Optional root `playVitalsReport` task ([Play Vitals reporting](/references/android-performance.md)); pairs with `PlayVitalsReportingTask.kt`

**Configuration Files (in config/ subdirectory):**
- `config/KotlinAndroid.kt` - Common Kotlin/Android setup
- `config/AndroidCompose.kt` - Compose configuration
- `config/ProjectExtensions.kt` - Version catalog access
- `config/GradleManagedDevices.kt` - Emulator configuration
- `config/AndroidInstrumentationTest.kt` - Test optimization
- `config/PrintApksTask.kt` - APK path printing
- `config/Jacoco.kt` - Code coverage configuration

Setup and usage: `assets/convention/QUICK_REFERENCE.md`.

### Registering a root-level reporting task (Play Vitals)

Optional Play Vitals reporting ([android-performance.md](/references/android-performance.md)) ships as a convention plugin to copy into `build-logic`:

| Source (copy to `build-logic/convention/src/main/kotlin/`)                                                                | Role                                                                                                                              |
|---------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| [`assets/convention/PlayVitalsReportingConventionPlugin.kt`](../assets/convention/PlayVitalsReportingConventionPlugin.kt) | Registers **`playVitalsReport`** on **`rootProject` only** (`id`: **`app.play.vitals`**)                                          |
| [`assets/convention/PlayVitalsReportingTask.kt`](../assets/convention/PlayVitalsReportingTask.kt)                         | Default task body: env check + lifecycle log; add **`PlayVitalsRepository`** per [android-performance.md](/references/android-performance.md) |

The plugin is already wired in [`assets/convention/build.gradle.kts`](../assets/convention/build.gradle.kts) (`gradlePlugin { register("playVitals") { ... } }`). **`gradle/libs.versions.toml`** should include **`app-play-vitals`** from [`assets/libs.versions.toml.template`](../assets/libs.versions.toml.template) (`[plugins]`).

Required:
- Apply `alias(libs.plugins.app.play.vitals)` in the **root** `build.gradle.kts` only.
- Forbidden in `app/build.gradle.kts` or feature modules.
- Forbidden inside `subprojects { }` / `allprojects { }` (duplicates / wrong scope).
- Wire CI to run `./gradlew playVitalsReport` on a schedule.

Query payload and HTTP code: [android-performance.md](/references/android-performance.md). This section only covers Gradle wiring.

## Module Build Files

### App Module

`app/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.app.android.application.compose)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.example.app"
    
    defaultConfig {
        applicationId = "com.example.app"
        versionCode = 1
        versionName = "1.0"
        
        // Enable multi-dex for larger apps
        multiDexEnabled = true
    }
    
    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            isDebuggable = true
        }
        
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        
        create("benchmark") {
            initWith(getByName("release"))
            signingConfig = signingConfigs.getByName("debug")
            isDebuggable = false
        }
    }
}

dependencies {
    // Feature modules
    implementation(project(":feature-auth"))
    implementation(project(":feature-onboarding"))
    implementation(project(":feature-profile"))
    implementation(project(":feature-settings"))
    
    // Core modules
    implementation(project(":core:domain"))
    implementation(project(":core:data"))
    implementation(project(":core:ui"))
    implementation(project(":core:network"))
    implementation(project(":core:database"))
    implementation(project(":core:datastore"))
    implementation(project(":core:common"))
    
    // Navigation3 for adaptive UI
    implementation(libs.bundles.navigation3)
    
    // Adaptive layouts (NavigationSuiteScaffold, ListDetailPaneScaffold, SupportingPaneScaffold)
    implementation(libs.bundles.adaptive)
    
    // Splash screen
    implementation(libs.androidx.core.splashscreen)
    
    // WorkManager for background tasks
    implementation(libs.androidx.work.runtime.ktx)
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.unit.test)
    androidTestImplementation(libs.bundles.android.test)
}
```

### Feature Module

`feature-auth/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.feature)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.app.spotless)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.example.feature.auth"
}

dependencies {
    // Core module dependencies
    implementation(project(":core:domain"))
    implementation(project(":core:ui"))
    
    // Feature-specific dependencies
    implementation(libs.androidx.constraintlayout.compose)
    implementation(libs.coil.compose)
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.unit.test)
    androidTestImplementation(libs.bundles.android.test)
}
```

### Core Domain Module (Pure Kotlin)

`core/domain/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.jvm.library)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.kotlin.serialization)
}

dependencies {
    // Pure Kotlin dependencies only
    implementation(libs.kotlinx.coroutines.core)
    implementation(libs.kotlinx.serialization)
    implementation(libs.kotlinx.collections.immutable)
    implementation(libs.kotlinx.datetime) // For Clock.System and Duration API
    
    // DI
    implementation(libs.java.inject)
    
    // Testing
    testImplementation(libs.bundles.unit.test)
}
```

### Core Data Module

`core/data/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.example.core.data"
}

dependencies {
    implementation(project(":core:domain"))
    
    // Data layer dependencies
    implementation(project(":core:database"))
    implementation(project(":core:network"))
    implementation(project(":core:datastore"))
    
    // Data serialization
    implementation(libs.kotlinx.serialization)
    implementation(libs.retrofit2.kotlinx.serialization.converter)
    
    // Paging if needed
    implementation(libs.androidx.paging.runtime)
    implementation(libs.androidx.paging.compose)
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.unit.test)
}
```

### Core UI Module

`core/ui/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.android.library.compose)
    alias(libs.plugins.app.detekt)
}

android {
    namespace = "com.example.core.ui"
}

dependencies {
    implementation(project(":core:domain"))
    
    // Compose
    implementation(libs.bundles.compose)
    
    // Image loading
    implementation(libs.coil.compose)
    implementation(libs.coil.network.okhttp)
    
    // Testing
    testImplementation(libs.bundles.unit.test)
    androidTestImplementation(libs.bundles.android.test)
}
```

### Core Network Module

`core/network/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
    alias(libs.plugins.kotlin.serialization)
}

android {
    namespace = "com.example.core.network"
}

dependencies {
    implementation(project(":core:domain"))
    
    // Networking
    implementation(libs.retrofit2)
    implementation(libs.retrofit2.kotlinx.serialization.converter)
    implementation(libs.okhttp3.logging.interceptor)
    implementation(libs.kotlinx.serialization)
    
    // Testing
    testImplementation(libs.bundles.unit.test)
}
```

### Core Database Module

`core/database/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.app.android.library)
    alias(libs.plugins.app.android.room)
    alias(libs.plugins.app.hilt)
    alias(libs.plugins.app.detekt)
}

android {
    namespace = "com.example.core.database"
}

dependencies {
    implementation(project(":core:domain"))
    
    // Room 3 runtime + sqlite-bundled + compiler via app.android.room convention
    // Testing
    testImplementation(libs.bundles.unit.test)
}
```

### Benchmark module

**Use when:** macrobenchmark coverage from [android-performance.md](/references/android-performance.md) applies. Host it in a dedicated `:benchmark` test module.

`benchmark/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.android.test)
}

android {
    namespace = "com.example.benchmark"
    compileSdk {
        version = release(libs.versions.compileSdk.get().toInt())
    }

    targetProjectPath = ":app"
    testBuildType = "benchmark"

    defaultConfig {
        minSdk = libs.findVersion("minSdk").get().toString().toInt()
        testInstrumentationRunner = "androidx.benchmark.junit4.AndroidBenchmarkRunner"
    }
}

dependencies {
    implementation(libs.androidx.benchmark.macro.junit4)
    implementation(libs.androidx.junit)
    implementation(libs.androidx.test.runner)
    implementation(libs.androidx.test.uiautomator)
}
```

**Required:** `:app` declares a matching `benchmark` build type (`create("benchmark")` under Module Build Files).

### Compose stability analyzer

**Use when:** CI must gate composable stability per [android-performance.md → Compose Stability Validation](/references/android-performance.md#compose-stability-validation-optional).

Root `build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.compose.stability.analyzer) apply false
}
```

Module `build.gradle.kts` (app or heavy UI modules):
```kotlin
plugins {
    alias(libs.plugins.app.android.application)
    alias(libs.plugins.compose.stability.analyzer)
}

composeStabilityAnalyzer {
    stabilityValidation {
        enabled.set(true)
        outputDir.set(layout.projectDirectory.dir("stability"))
        includeTests.set(false)
        failOnStabilityChange.set(true) // Fail build on stability regressions
        
        // Allowed: exclude internal packages from fail-on-change
        ignoredPackages.set(listOf("com.example.internal"))
        ignoredClasses.set(listOf("PreviewComposables"))
    }
}
```

## Code Quality (Detekt)

Required: apply Detekt via the `app.detekt` convention plugin in every module. Setup, baselines, CI: [code-quality.md](/references/code-quality.md).

## Build Variants & Optimization

### Product Flavors for Different Environments

`app/build.gradle.kts`:
```kotlin
android {
    buildFeatures {
        buildConfig = true // Required when using buildConfigField (off by default in AGP 8+)
    }

    flavorDimensions += "environment"

    productFlavors {
        create("development") {
            dimension = "environment"
            applicationIdSuffix = ".dev"
            versionNameSuffix = "-dev"
            buildConfigField("String", "BASE_URL", "\"https://api.dev.example.com/\"")
        }

        create("staging") {
            dimension = "environment"
            applicationIdSuffix = ".staging"
            versionNameSuffix = "-staging"
            buildConfigField("String", "BASE_URL", "\"https://api.staging.example.com/\"")
        }

        create("production") {
            dimension = "environment"
            buildConfigField("String", "BASE_URL", "\"https://api.example.com/\"")
        }
    }
}
```

**BuildConfig:** From AGP 8.0 onward, `BuildConfig` is not generated unless `buildFeatures.buildConfig` is enabled. You need this for `buildConfigField` values (e.g. `BuildConfig.BASE_URL`) and `BuildConfig.DEBUG`.

**Variant names:** Gradle names variants `{productFlavor}{buildType}` with **capitalized** build type - for example `developmentDebug`, `stagingRelease`, `productionRelease`.

**Common Gradle commands:**

```bash
# List build-related tasks
./gradlew tasks --group="build"

# Assemble or install a specific variant (flavor + build type)
./gradlew :app:assembleDevelopmentDebug
./gradlew :app:assembleStagingRelease
./gradlew :app:assembleProductionRelease
./gradlew :app:installDevelopmentDebug
./gradlew :app:installProductionRelease

# All debug or all release variants across flavors
./gradlew :app:assembleDebug
./gradlew :app:assembleRelease

# Deeper dependency / sync issues
./gradlew :app:dependencies
./gradlew assembleDevelopmentDebug --stacktrace
./gradlew --refresh-dependencies
```

**Flavor-specific source sets:** Optional overrides live next to `main` - for example `app/src/development/`, `app/src/staging/`, `app/src/production/` for resources or code only for that flavor; `app/src/debug/` and `app/src/release/` apply per build type across flavors.

**Multiple flavor dimensions:** If you add another dimension (e.g. `tier` = `free` / `paid`), variants become combinations such as `developmentFreeDebug`. Cap flavor dimensions — each new dimension multiplies variant count and CI time.

### Build Optimization Configuration

`gradle.properties`:
```properties
# Build performance
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=1024m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8

# Configuration cache
org.gradle.configuration-cache=true

# Android build optimization
android.useAndroidX=true
kotlin.incremental=true
kotlin.caching.enabled=true

# Module metadata
android.nonTransitiveRClass=true

# KSP optimization
ksp.incremental=true
ksp.incremental.log=false
```

### Non-Transitive R Classes

With `android.nonTransitiveRClass=true`, each module generates its own R class containing **only its own resources**. This improves build performance but requires explicit imports when accessing resources from other modules.

**Key implications:**

1. **Each module has its own R class** with its full package name:
   ```kotlin
   // In :feature:products module
   com.example.feature.products.R
   
   // In :core:ui module
   com.example.core.ui.R
   ```

2. **Unqualified `R` may not resolve** if your file is in a sub-package:
   ```kotlin
   // File: feature/products/presentation/detail/ProductDetailView.kt
   // Package: com.example.feature.products.presentation.detail
   
   // This may fail:
   stringResource(R.string.product_title) // WRONG: Unresolved reference
   
   // Fix: Import the module's R class explicitly
   import com.example.feature.products.R
   stringResource(R.string.product_title) // CORRECT: Works
   ```

3. **Cross-module resources require import aliases**:
   ```kotlin
   // Accessing strings from core:ui in feature:products
   import com.example.core.ui.R as CoreUiR
   
   @Composable
   fun ErrorMessage() {
       Text(stringResource(CoreUiR.string.error_unknown))
       Text(stringResource(CoreUiR.string.error_network))
   }
   ```

4. **Fully qualified references** (alternative to imports):
   ```kotlin
   Text(stringResource(com.example.core.ui.R.string.loading))
   ```

**Required:**
- Use import aliases (`as CoreUiR`) when one file pulls strings from multiple foreign modules.
- Group cross-module resource imports at the top of the file.
- String ownership rules: [android-i18n.md → String resource ownership](/references/android-i18n.md#string-resource-ownership).

### R8 / ProGuard Configuration

R8 is the default code shrinker and obfuscator in AGP. Enable it in release builds:

```kotlin
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
```

Copy `assets/proguard-rules.pro.template` to `app/proguard-rules.pro` and adjust `com.example.*` package names to match your project. The template includes rules for every library in the version catalog.

**Required:**
- Rely on AndroidX/Jetpack consumer rules inside AARs; add manual keep rules only when library docs or R8 full-mode errors demand it.
- Ship Retrofit keep rules for R8 full-mode (`Proxy`-generated interfaces stay invisible to static analysis).
- Add `-dontwarn` for Tink error-prone annotations when using `EncryptedSharedPreferences`.
- Keep SQLCipher native methods in shrinker output.
- Upload `mapping.txt` to Crashlytics/Sentry so release stacks decode (Gradle plugins wire this when configured).

**Debugging shrunk builds:**

```bash
# Build release with full R8 output
./gradlew assembleRelease

# Decode an obfuscated stack trace
retrace build/outputs/mapping/release/mapping.txt stacktrace.txt
```

Check `build/outputs/mapping/release/` for the mapping file after each release build.

See [android-security.md](/references/android-security.md#proguard--r8-hardening) for security-specific hardening rules (log stripping, aggressive obfuscation, manifest settings).

### R8 Keep-Rules Audit

Run when `proguard-rules.pro` grows past ~50 lines, release APK/AAB size regresses, or a release-only crash points at a missing class/member. Steps are ordered worst-impact first; skip any step whose rule class does not appear in the file.

**Step 1 - Drop redundant library rules.** The libraries below ship consumer rules inside the AAR/JAR. App-side duplicates only mask narrower rules - delete them first.

| Library group                                          | App-side rules needed?                                                                                                                                  |
|--------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| AndroidX / Jetpack (lifecycle, room3, paging, work, …) | No. Consumer rules are bundled.                                                                                                                         |
| Kotlin stdlib, kotlinx.coroutines, kotlinx.collections | No. Only `-dontwarn kotlinx.coroutines.**` for residual warnings.                                                                                       |
| kotlinx.serialization                                  | Library bundles rules since 1.6+. Keep only the **`@Serializable` generic-parameter** rules (R8 full-mode strips classes used only as `List<MyModel>`). |
| Retrofit / OkHttp                                      | Retrofit needs the `@retrofit2.http.*` interface keeps for R8 full-mode (Proxy). OkHttp 5.x: only `-dontwarn` for optional Conscrypt/BouncyCastle.      |
| Gson / Moshi (codegen)                                 | No. Codegen variants ship rules. Reflective Gson **does** need `-keep` on the model package.                                                            |
| Hilt / Dagger                                          | No. Only `-dontwarn dagger.hilt.internal.**` and project-level DI keep if you reflect into it.                                                          |
| Google Play services (incl. Play Integrity, Play Core) | No. Only `-dontwarn` for optional sub-packages.                                                                                                         |
| Firebase SDKs                                          | No. Mapping upload is handled by the Gradle plugin.                                                                                                     |
| Coil 3, Compose, Compose-runtime                       | No (Compose-stability annotations are the only edge case worth keeping).                                                                                |

If a release build fails after deleting one of the above, the failure points to a **reflection** site in app code (see step 4), not a missing library keep.

**Step 2 - Score remaining rules by impact (broad → narrow).** Use the narrowest rule that works. Top-row rules are size-regression suspects:

| Tier (worst → best) | Pattern                                                   | Effect                                                                                                                      |
|---------------------|-----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
| 1 - Package-wide    | `-keep class com.example.** { *; }`                       | Disables shrinking, optimization, and obfuscation for the whole tree. Forbidden in app code unless step 4 cannot narrow it. |
| 2 - Class-wide      | `-keep class com.example.Foo { *; }`                      | Keeps every member; disables member-level optimization for that class.                                                      |
| 3 - Method/field    | `-keepclassmembers class com.example.Foo { void bar(); }` | Keeps only what reflection touches; R8 shrinks/optimizes the rest.                                                          |
| 4 - Conditional     | `-if @MyAnnotation class ** -keep class <1> { *; }`       | Required form for annotation-driven reflection.                                                                             |

**Step 3 - Detect subsuming rules and remove the broader half.** When two rules overlap, keep only the narrower one:

- `-keep class com.example.Foo { *; }` subsumes any `-keepclassmembers class com.example.Foo { … }` - **delete the class-wide rule**, keep the member rule.
- `-keep class com.example.** { *; }` subsumes every per-class rule under that package - **delete the package-wide rule**, keep the per-class rules.
- A conditional `-if … -keep <1>` subsumes the equivalent unconditional `-keep` for the same class - delete the unconditional one.

R8 emits no "redundant rule" report. To verify a suspected redundancy, comment the broader rule out, run `./gradlew assembleRelease`, and confirm `mapping.txt` still contains the narrower-kept symbol.

**Step 4 - Narrow reflection-driven keeps.** For every remaining package- or class-wide rule, locate the reflection site (search for `Class.forName`, `::class.java`, `getDeclaredMethod`, `getDeclaredField`, JNI symbol lookups, `META-INF/services/` entries, Gson `TypeToken`, Moshi adapter lookups, Retrofit `Proxy`). Replace the broad rule with one that targets only the reflected members:

```proguard
# Before: package-wide
-keep class com.example.api.models.** { *; }

# After: only what Gson reads via reflection
-keep class com.example.api.models.** {
    <init>();
    <fields>;
}

# Before: class-wide because one method is called via Class.forName
-keep class com.example.plugins.AnalyticsPlugin { *; }

# After: only the constructor + entry point
-keep class com.example.plugins.AnalyticsPlugin {
    <init>();
    public void initialize(android.content.Context);
}
```

For annotation-driven reflection, use `-if @YourAnnotation class **` so the rule scales as new annotated classes are added.

**Step 5 - AGP 9 default optimizations.** AGP 9 enables additional R8 optimizations by default. Re-run steps 1-4 after every AGP upgrade and every major library bump. Track release APK/AAB size as a CI metric to surface silent regressions.

**Final guardrail.** Before shipping any `proguard-rules.pro` change:

1. `./gradlew assembleRelease` (or `bundleRelease`) succeeds.
2. Run a UI Automator smoke test over the packages whose rules changed (see [testing.md](/references/testing.md)).
3. Diff `mapping.txt` line count against the previous release. Drops are the win signal; jumps mean a broader keep slipped in.

## Build Performance

### Settings Configuration

Check `assets/settings.gradle.kts.template` as the source of truth for settings setup,
module includes, and repository configuration.

### Root Build File

`build.gradle.kts`:
```kotlin
// Top-level build. Repositories are configured in settings.gradle.kts via dependencyResolutionManagement.
// AGP 9+ ships built-in Kotlin support; do not apply org.jetbrains.kotlin.android.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.android.test) apply false
    alias(libs.plugins.kotlin.jvm) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.detekt) apply false
    alias(libs.plugins.spotless) apply false
}

// Apply spotless formatting to root project
plugins.apply(libs.plugins.spotless.get().pluginId)

configure<com.diffplug.gradle.spotless.SpotlessExtension> {
    kotlin {
        target("**/*.kt")
        targetExclude("**/build/**")
        ktlint(libs.versions.ktlint.get())
            .editorConfigOverride(
                mapOf(
                    "indent_size" to "4",
                    "continuation_indent_size" to "4",
                    "max_line_length" to "120",
                    "disabled_rules" to "no-wildcard-imports"
                )
            )
        licenseHeaderFile(rootProject.file("spotless/copyright.kt"))
    }
    
    kotlinGradle {
        target("**/*.gradle.kts")
        ktlint(libs.versions.ktlint.get())
    }
}
```

### Build Cache Configuration

Create `gradle/init.gradle.kts` for team-wide build optimization:
```kotlin
gradle.settingsEvaluated {
    // Enable build cache for all projects
    buildCache {
        local {
            isEnabled = true
            directory = File(rootDir, ".gradle/build-cache")
            removeUnusedEntriesAfterDays = 7
        }
        
        remote<HttpBuildCache> {
            isEnabled = false // Set to true for CI/CD shared cache
            url = uri("https://example.com/cache/")
            isPush = true
        }
    }
}
```

### Optimization Workflow

Required: change one variable at a time; measure before and after.

1. Baseline: `./gradlew clean assembleDebug` and an incremental build.
2. Build Scan: `./gradlew assembleDebug --scan`.
3. In the scan, identify the slow phase (Initialization / Configuration / Execution) under **Performance → Build timeline**.
4. Apply one change.
5. Re-measure; revert if no improvement.

Local-only profile (no upload): `./gradlew assembleDebug --profile` → `build/reports/profile/`.

### Lazy Task Configuration

Required: `tasks.register` for every custom task; `tasks.create` is forbidden (eagerly configures on every build).

```kotlin
// Bad
tasks.create("generateBuildInfo") {
    doLast { /* ... */ }
}

// Good
tasks.register("generateBuildInfo") {
    doLast { /* ... */ }
}
```

### Avoid I/O During Configuration

Forbidden in configuration phase: `File.readText()`, network calls, `exec { }`. They run every build and break the configuration cache. Defer via `providers`.

```kotlin
// Bad
val version = file("version.txt").readText()

// Good
val version = providers.fileContents(layout.projectDirectory.file("version.txt")).asText
```

```kotlin
// Bad
val gitHash = Runtime.getRuntime().exec("git rev-parse --short HEAD")
    .inputStream.bufferedReader().readText().trim()

// Good
val gitHash = providers.exec {
    commandLine("git", "rev-parse", "--short", "HEAD")
}.standardOutput.asText.map { it.trim() }
```

### Pin Dependency Versions

Forbidden: dynamic versions (`1.+`, `latest.release`, `-SNAPSHOT`). Always pin via the version catalog.

```kotlin
// Bad
implementation("com.example:lib:1.0.+")

// Good
implementation(libs.example.lib)
```

### Bottleneck Troubleshooting

| Symptom                       | Fix                                                                                                                                                |
|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Slow configuration phase      | Use `tasks.register`; defer I/O via `providers`; move plugins into convention plugins; remove `subprojects { }` / `allprojects { }`.              |
| Slow execution phase          | Migrate kapt → KSP ([dependencies.md](/references/dependencies.md)); enable `org.gradle.caching=true`; enable `org.gradle.parallel=true`; raise `-Xmx`. |
| Slow dependency resolution    | Pin exact versions in the catalog; order `google()` before `mavenCentral()`; remove unused repos; ensure `org.gradle.caching=true`.               |

## Rules

Required:
- Centralize all versions in `gradle/libs.versions.toml`.
- Extract every reusable build configuration into a convention plugin.
- Use KSP for annotation processing ([dependencies.md](/references/dependencies.md)).
- Enable type-safe project accessors and local + remote build cache.
- Apply Compose-only UI; no View binding, no legacy `View` system.

Forbidden:
- Dynamic versions (`1.+`, `latest.release`, `-SNAPSHOT`).
- Inline build logic duplicated across modules instead of a convention plugin.
- I/O, `exec`, or `Runtime.getRuntime()` during the configuration phase.

## Common Gradle Commands

```bash
# Clean build
./gradlew clean

# Build debug APK
./gradlew assembleDebug

# Build release APK
./gradlew assembleRelease

# Run unit tests
./gradlew test

# Run instrumented tests
./gradlew connectedAndroidTest

# Run detekt
./gradlew detekt

# Run spotless format check
./gradlew spotlessCheck

# Apply spotless formatting
./gradlew spotlessApply

# Generate dependency report
./gradlew dependencies

# Profile build
./gradlew assembleDebug --profile

# Build with configuration cache
./gradlew assembleDebug --configuration-cache

# Build all variants
./gradlew assemble
```
