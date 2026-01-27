# Gradle & Build Configuration

Build system patterns following our modern Android multi-module architecture with Navigation3, Jetpack Compose, and convention plugins.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Version Catalog](#version-catalog)
3. [Convention Plugins](#convention-plugins)
4. [Code Quality (Detekt)](#code-quality-detekt)
5. [Module Build Files](#module-build-files)
6. [Build Variants & Optimization](#build-variants--optimization)
7. [Build Performance](#build-performance)

## Project Structure

Project structure, module layout, and naming conventions are defined in
`references/modularization.md`.

## Version Catalog

The version catalog source of truth lives in `templates/libs.versions.toml.template`.
Use it to generate or update `gradle/libs.versions.toml` for each project.

## Convention Plugins

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

dependencies {
    compileOnly(libs.android.gradlePlugin)
    compileOnly(libs.kotlin.gradlePlugin)
    compileOnly(libs.hilt.gradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.plugin.detekt)
}

gradlePlugin {
    plugins {
        register("androidApplication") {
            id = "com.example.android.application"
            implementationClass = "com.example.convention.AndroidApplicationConventionPlugin"
        }
        register("androidLibrary") {
            id = "com.example.android.library"
            implementationClass = "com.example.convention.AndroidLibraryConventionPlugin"
        }
        register("androidFeature") {
            id = "com.example.android.feature"
            implementationClass = "com.example.convention.AndroidFeatureConventionPlugin"
        }
        register("androidCompose") {
            id = "com.example.android.compose"
            implementationClass = "com.example.convention.AndroidComposeConventionPlugin"
        }
        register("androidHilt") {
            id = "com.example.android.hilt"
            implementationClass = "com.example.convention.AndroidHiltConventionPlugin"
        }
        register("androidRoom") {
            id = "com.example.android.room"
            implementationClass = "com.example.convention.AndroidRoomConventionPlugin"
        }
        register("androidDetekt") {
            id = "com.example.android.detekt"
            implementationClass = "com.example.convention.DetektConventionPlugin"
        }
    }
}
```

### Shared Configuration

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidConvention.kt`:
```kotlin
import com.android.build.api.dsl.CommonExtension
import org.gradle.api.JavaVersion
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.provideDelegate
import org.jetbrains.kotlin.gradle.dsl.KotlinAndroidProjectExtension
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmOptions

/**
 * Configure base Kotlin Android options for all modules
 */
internal fun Project.configureAndroidCommon(
    commonExtension: CommonExtension<*, *, *, *, *, *>
) {
    commonExtension.apply {
        compileSdk = libs.findVersion("compileSdk").get().toInt()

        defaultConfig {
            minSdk = libs.findVersion("minSdk").get().toInt()
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }

        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
            isCoreLibraryDesugaringEnabled = true
        }

        kotlinOptions {
            jvmTarget = JavaVersion.VERSION_17.toString()
            freeCompilerArgs = freeCompilerArgs + listOf(
                "-opt-in=kotlin.RequiresOptIn",
                "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi",
                "-opt-in=androidx.compose.material3.ExperimentalMaterial3Api",
                "-opt-in=androidx.compose.material3.adaptive.ExperimentalMaterial3AdaptiveApi",
                "-opt-in=androidx.compose.foundation.ExperimentalFoundationApi",
            )
        }
    }

    dependencies {
        add("coreLibraryDesugaring", libs.findLibrary("android-desugar-jdk-libs").get())
    }
}

/**
 * Configure Kotlin options
 */
private fun CommonExtension<*, *, *, *, *, *>.kotlinOptions(block: KotlinJvmOptions.() -> Unit) {
    (this as ExtensionAware).extensions.configure<KotlinJvmOptions>("kotlinOptions", block)
}
```

### Application Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidApplicationConventionPlugin.kt`:
```kotlin
package com.example.convention

import com.android.build.api.dsl.ApplicationExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
                apply("kotlin-kapt")
                apply("com.google.dagger.hilt.android")
            }

            extensions.configure<ApplicationExtension> {
                configureAndroidCommon(this)
                
                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toInt()
                    versionCode = 1
                    versionName = "1.0"
                }
                
                buildTypes {
                    release {
                        isMinifyEnabled = true
                        proguardFiles(
                            getDefaultProguardFile("proguard-android-optimize.txt"),
                            "proguard-rules.pro"
                        )
                    }
                }
                
                packaging {
                    resources {
                        excludes += "/META-INF/{AL2.0,LGPL2.1}"
                    }
                }
            }
            
            configureAndroidDependencies()
        }
    }
}
```

### Library Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidLibraryConventionPlugin.kt`:
```kotlin
package com.example.convention

import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                configureAndroidCommon(this)
                defaultConfig.targetSdk = libs.findVersion("targetSdk").get().toInt()
                
                buildTypes {
                    release {
                        isMinifyEnabled = false
                    }
                }
            }
            
            configureAndroidDependencies()
        }
    }
}
```

### Feature Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidFeatureConventionPlugin.kt`:
```kotlin
package com.example.convention

import com.android.build.api.dsl.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.configure

class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("com.example.android.library")
                apply("com.example.android.compose")
                apply("com.example.android.hilt")
            }

            extensions.configure<LibraryExtension> {
                defaultConfig {
                    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                }
            }

            dependencies {
                // Core dependencies for all features
                add("implementation", project(":core:domain"))
                add("implementation", project(":core:ui"))
                
                // AndroidX
                add("implementation", libs.findLibrary("androidx.lifecycle.runtime.compose").get())
                add("implementation", libs.findLibrary("androidx.lifecycle.viewmodel.compose").get())
                add("implementation", libs.findLibrary("androidx.activity.compose").get())
                
                // Navigation3
                add("implementation", libs.bundles.navigation3)
                
                // DI
                add("implementation", libs.findLibrary("hilt.android").get())
                add("kapt", libs.findLibrary("hilt.android.compiler").get())
                
                // Testing
                add("testImplementation", libs.bundles.testing)
                add("androidTestImplementation", libs.bundles.compose.testing)
            }
        }
    }
}
```

### Compose Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidComposeConventionPlugin.kt`:
```kotlin
package com.example.convention

import com.android.build.api.dsl.CommonExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply("com.android.library")
            
            val extension = extensions.getByType<CommonExtension<*, *, *, *, *, *>>()
            configureAndroidCompose(extension)
        }
    }
}

internal fun Project.configureAndroidCompose(
    commonExtension: CommonExtension<*, *, *, *, *, *>
) {
    commonExtension.apply {
        buildFeatures {
            compose = true
        }

        composeOptions {
            kotlinCompilerExtensionVersion = libs.findVersion("composeCompiler").get().toString()
        }
    }

    dependencies {
        // Compose BOM
        val composeBom = libs.findLibrary("androidx.compose.bom").get()
        add("implementation", platform(composeBom))
        add("androidTestImplementation", platform(composeBom))
        
        // Compose dependencies
        add("implementation", libs.bundles.compose)
        add("debugImplementation", libs.findLibrary("androidx.compose.ui.tooling").get())
        add("debugImplementation", libs.findLibrary("androidx.compose.ui.test.manifest").get())
    }
}
```

### Hilt Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidHiltConventionPlugin.kt`:
```kotlin
package com.example.convention

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies

class AndroidHiltConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("kotlin-kapt")
                apply("com.google.dagger.hilt.android")
            }

            dependencies {
                add("implementation", libs.findLibrary("hilt.android").get())
                add("kapt", libs.findLibrary("hilt.android.compiler").get())
                add("androidTestImplementation", libs.findLibrary("hilt.android.testing").get())
                add("kaptAndroidTest", libs.findLibrary("hilt.android.compiler").get())
            }
        }
    }
}
```

### Room Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidRoomConventionPlugin.kt`:
```kotlin
package com.example.convention

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.kotlin.dsl.dependencies

class AndroidRoomConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            pluginManager.apply {
                apply("kotlin-kapt")
            }

            dependencies {
                add("implementation", libs.findLibrary("room.runtime").get())
                add("implementation", libs.findLibrary("room.ktx").get())
                add("kapt", libs.findLibrary("room.compiler").get())
                add("testImplementation", libs.findLibrary("room.testing").get())
            }
        }
    }
}

private fun Project.configureAndroidDependencies() {
    dependencies {
        // Common Android dependencies
        add("implementation", libs.findLibrary("androidx.core.ktx").get())
        add("implementation", libs.findLibrary("kotlinx.coroutines.android").get())
        
        // Testing
        add("testImplementation", libs.findLibrary("junit").get())
        add("androidTestImplementation", libs.findLibrary("androidx.test.ext.junit").get())
        add("androidTestImplementation", libs.findLibrary("androidx.test.espresso.core").get())
    }
}
```

### Detekt Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/DetektConventionPlugin.kt`:
```kotlin
package com.example.convention

import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.withType

class DetektConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        val libs = rootProject.extensions.getByType<VersionCatalogsExtension>().named("libs")
        val detektPluginId = libs.findPlugin("detekt").get().pluginId

        pluginManager.apply(detektPluginId)

        dependencies {
            add("detektPlugins", libs.findLibrary("compose-rules-detekt").get())
        }

        extensions.configure<DetektExtension> {
            buildUponDefaultConfig = true
            basePath = rootProject.projectDir.absolutePath
            parallel = true

            val rootConfig = rootProject.file("plugins/detekt.yml")
            val moduleConfig = file("detekt.yml")
            if (moduleConfig.exists()) {
                config.setFrom(moduleConfig, rootConfig)
            } else {
                config.setFrom(rootConfig)
            }
        }

        tasks.withType<Detekt>().configureEach {
            jvmTarget = "17"
        }
    }
}
```

## Module Build Files

### App Module

`app/build.gradle.kts`:
```kotlin
plugins {
    id("com.example.android.application")
    id("com.example.android.compose")
    id("com.example.android.hilt")
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
    
    // Enable view binding if needed
    buildFeatures {
        viewBinding = true
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
    
    // Compose runtime optimizations
    implementation(libs.findLibrary("androidx.compose.runtime").get())
    implementation(libs.findLibrary("androidx.compose.runtime.livedata").get())
    
    // Splash screen
    implementation(libs.findLibrary("androidx.core.splashscreen").get())
    
    // WorkManager for background tasks
    implementation(libs.findLibrary("androidx.work.runtime.ktx").get())
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.testing)
    androidTestImplementation(libs.bundles.compose.testing)
}
```

### Feature Module

`feature-auth/build.gradle.kts`:
```kotlin
plugins {
    id("com.example.android.feature")
    id("com.example.android.compose")
    id("com.example.android.hilt")
}

android {
    namespace = "com.example.feature.auth"
}

dependencies {
    // Core module dependencies
    implementation(project(":core:domain"))
    implementation(project(":core:ui"))
    
    // Feature-specific dependencies
    implementation(libs.findLibrary("androidx.constraintlayout.compose").get())
    implementation(libs.findLibrary("coil.compose").get())
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.testing)
    androidTestImplementation(libs.bundles.compose.testing)
}
```

### Core Domain Module (Pure Kotlin)

`core/domain/build.gradle.kts`:
```kotlin
plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.serialization")
}

android {
    namespace = "com.example.core.domain"
    
    // Domain module should be pure Kotlin
    compileSdk = libs.findVersion("compileSdk").get().toInt()
    
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }
}

dependencies {
    // Pure Kotlin dependencies only
    implementation(libs.findLibrary("kotlinx.coroutines.core").get())
    implementation(libs.findLibrary("kotlinx.serialization.json").get())
    
    // Testing
    testImplementation(libs.bundles.testing)
}
```

### Core Data Module

`core/data/build.gradle.kts`:
```kotlin
plugins {
    id("com.example.android.library")
    id("com.example.android.hilt")
    id("com.example.android.room")
}

android {
    namespace = "com.example.core.data"
}

dependencies {
    // Module dependencies following our architecture rules
    implementation(project(":core:domain"))
    
    // Data layer dependencies
    implementation(project(":core:database"))
    implementation(project(":core:network"))
    implementation(project(":core:datastore"))
    
    // Data serialization
    implementation(libs.findLibrary("kotlinx.serialization.json").get())
    implementation(libs.findLibrary("retrofit.kotlinx.serialization").get())
    
    // Paging if needed
    implementation(libs.findLibrary("androidx.paging.runtime").get())
    implementation(libs.findLibrary("androidx.paging.compose").get())
    
    // Testing
    testImplementation(project(":core:testing"))
    testImplementation(libs.bundles.testing)
}
```

### Core UI Module

`core/ui/build.gradle.kts`:
```kotlin
plugins {
    id("com.example.android.library")
    id("com.example.android.compose")
}

android {
    namespace = "com.example.core.ui"
}

dependencies {
    // Dependencies following our architecture
    implementation(project(":core:domain"))
    
    // Compose
    implementation(libs.bundles.compose)
    
    // Image loading
    implementation(libs.findLibrary("coil.compose").get())
    
    // Testing
    testImplementation(libs.bundles.testing)
    androidTestImplementation(libs.bundles.compose.testing)
}
```

### Benchmark Module (Optional)

Create a dedicated `:benchmark` test module for macrobenchmark performance testing. See `references/android-performance.md` for when to use.

`benchmark/build.gradle.kts`:
```kotlin
plugins {
    id("com.android.test")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.benchmark"
    compileSdk = libs.findVersion("compileSdk").get().toInt()

    targetProjectPath = ":app"
    testBuildType = "benchmark"

    defaultConfig {
        minSdk = 23
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

Note: The `benchmark` build type must be defined in the app module (shown in the app module example above).

## Code Quality (Detekt)

Detekt is integrated via a convention plugin to keep rules consistent across modules.
See `references/code-quality.md` for setup details, baseline usage, and CI guidance.

## Build Variants & Optimization

### Product Flavors for Different Environments

`app/build.gradle.kts`:
```kotlin
android {
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

### Build Optimization Configuration

`gradle.properties`:
```properties
# Build performance
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.configureondemand=true
org.gradle.jvmargs=-Xmx4096m -XX:MaxMetaspaceSize=1024m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
org.gradle.unsafe.configuration-cache=true
org.gradle.configuration-cache.problems=warn

# Android build optimization
android.enableBuildCache=true
android.useAndroidX=true
android.enableJetifier=true
kotlin.incremental=true
kotlin.caching.enabled=true

# Module metadata
android.defaults.buildfeatures.buildconfig=true
android.nonTransitiveRClass=true
```

### Proguard Rules for Release Builds

`app/proguard-rules.pro`:
```proguard
# Keep data classes used with serialization
-keep class com.example.core.domain.model.** { *; }
-keepclassmembers class com.example.core.domain.model.** {
    <fields>;
}

# Keep Room entities
-keep class * extends androidx.room.Entity { *; }
-keep class * extends androidx.room.Relation { *; }

# Keep Hilt
-keep class com.example.di.** { *; }
-keep class * extends dagger.hilt.android.internal.legacy.AggregatedElement { *; }

# Generic rules
-dontwarn kotlinx.coroutines.**
-dontwarn javax.annotation.**
```

## Build Performance

### Settings Configuration

Check `templates/settings.gradle.kts.template` as the source of truth for settings setup,
module includes, and repository configuration.

### Root Build File

`build.gradle.kts`:
```kotlin
buildscript {
    repositories {
        google()
        mavenCentral()
    }
}

// Top-level build file where you can add configuration options common to all sub-projects/modules.
plugins {
    id("com.diffplug.spotless") version "6.23.3" apply false
    id("org.jetbrains.kotlin.android") version "1.9.22" apply false
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
    
    // Apply spotless formatting
    apply(plugin = "com.diffplug.spotless")
    
    configure<com.diffplug.gradle.spotless.SpotlessExtension> {
        kotlin {
            target("**/*.kt")
            targetExclude("**/build/**")
            ktlint("1.0.1")
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
            ktlint("1.0.1")
        }
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
            push = true
        }
    }
    
    // Configure all projects
    for (project in projects) {
        project.configure<org.gradle.api.Project> {
            tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile>().configureEach {
                kotlinOptions {
                    allWarningsAsErrors = false
                    freeCompilerArgs = freeCompilerArgs + listOf(
                        "-Xcontext-receivers",
                        "-Xjvm-default=all",
                        "-opt-in=kotlin.ExperimentalStdlibApi"
                    )
                }
            }
        }
    }
}
```

## Best Practices

1. **Use Version Catalog**: Centralize dependency versions for consistency
2. **Convention Plugins**: Extract common build logic to avoid duplication
3. **Type-safe Project Accessors**: Enable for better IDE support
4. **Build Caching**: Configure local and remote caches for faster builds
5. **Modular Builds**: Use our strict dependency rules for clean architecture
6. **Progressive Enhancement**: Start simple, add flavors and optimizations as needed
7. **CI/CD Ready**: Ensure build configuration works well with CI systems
8. **Profile Builds**: Use `./gradlew assembleDebug --profile` to identify bottlenecks