# Gradle & Build Configuration

Build system patterns following our modern Android multi-module architecture with Navigation3, Jetpack Compose, KSP, and convention plugins.

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

Key points:
- **KSP over kapt**: This SKILL uses KSP for annotation processing (2x faster than kapt)
- **Kotlin Compose Plugin**: Compose compiler is managed via `kotlin-compose` plugin (Kotlin 2.0+)
- **Bundles**: Use `unit-test` and `android-test` bundles for consistent testing dependencies

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
    compileOnly(libs.kotlin.composeGradlePlugin)
    compileOnly(libs.ksp.gradlePlugin)
    compileOnly(libs.hilt.gradlePlugin)
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
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType
import org.jetbrains.kotlin.gradle.dsl.KotlinJvmOptions

/**
 * Configure base Kotlin Android options for all modules
 */
internal fun Project.configureAndroidCommon(
    commonExtension: CommonExtension<*, *, *, *, *, *>
) {
    val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
    
    commonExtension.apply {
        compileSdk = libs.findVersion("compileSdk").get().toString().toInt()

        defaultConfig {
            minSdk = libs.findVersion("minSdk").get().toString().toInt()
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }

        compileOptions {
            sourceCompatibility = JavaVersion.VERSION_17
            targetCompatibility = JavaVersion.VERSION_17
            isCoreLibraryDesugaringEnabled = true // Required for API < 26 (java.time, Duration API)
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
        add("coreLibraryDesugaring", libs.findLibrary("androidx.core.desugaring").get())
    }
}

/**
 * Configure common Android dependencies
 */
internal fun Project.configureAndroidDependencies() {
    val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
    
    dependencies {
        // Common Android dependencies
        add("implementation", libs.findLibrary("androidx-core-ktx").get())
        add("implementation", libs.findLibrary("kotlinx-coroutines-android").get())
        
        // Testing
        add("testImplementation", libs.findLibrary("junit").get())
        add("androidTestImplementation", libs.findLibrary("androidx-junit").get())
        add("androidTestImplementation", libs.findLibrary("androidx-espresso-core").get())
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
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.getByType

class AndroidApplicationConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            pluginManager.apply {
                apply("com.android.application")
                apply("org.jetbrains.kotlin.android")
                apply(libs.findPlugin("ksp").get().get().pluginId)
                apply("com.google.dagger.hilt.android")
            }

            extensions.configure<ApplicationExtension> {
                configureAndroidCommon(this)
                
                defaultConfig {
                    targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
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
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.getByType

class AndroidLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            pluginManager.apply {
                apply("com.android.library")
                apply("org.jetbrains.kotlin.android")
            }

            extensions.configure<LibraryExtension> {
                configureAndroidCommon(this)
                defaultConfig.targetSdk = libs.findVersion("targetSdk").get().toString().toInt()
                
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
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidFeatureConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
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
                add("implementation", libs.findLibrary("androidx-lifecycle-runtime-compose").get())
                add("implementation", libs.findLibrary("androidx-lifecycle-viewmodel-compose").get())
                add("implementation", libs.findLibrary("androidx-activity-compose").get())
                
                // Navigation3
                add("implementation", libs.findBundle("navigation3").get())
                
                // DI
                add("implementation", libs.findLibrary("hilt-android").get())
                add("ksp", libs.findLibrary("hilt-compiler").get())
                
                // Testing
                add("testImplementation", libs.findBundle("unit-test").get())
                add("androidTestImplementation", libs.findBundle("android-test").get())
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
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidComposeConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            pluginManager.apply {
                apply("com.android.library")
                apply(libs.findPlugin("kotlin-compose").get().get().pluginId)
            }
            
            val extension = extensions.getByType<CommonExtension<*, *, *, *, *, *>>()
            configureAndroidCompose(extension)
        }
    }
}

internal fun Project.configureAndroidCompose(
    commonExtension: CommonExtension<*, *, *, *, *, *>
) {
    val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
    
    commonExtension.apply {
        buildFeatures {
            compose = true
        }
        
        // Compose compiler is configured via kotlin-compose plugin
        // No manual composeOptions needed with Kotlin 2.0+
    }

    dependencies {
        // Compose BOM
        val composeBom = libs.findLibrary("androidx-compose-bom").get()
        add("implementation", platform(composeBom))
        add("androidTestImplementation", platform(composeBom))
        
        // Compose dependencies
        add("implementation", libs.findBundle("compose").get())
        add("debugImplementation", libs.findLibrary("androidx-compose-ui-tooling").get())
        add("debugImplementation", libs.findLibrary("androidx-compose-ui-test-manifest").get())
    }
}
```

### Hilt Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidHiltConventionPlugin.kt`:
```kotlin
package com.example.convention

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidHiltConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            pluginManager.apply {
                apply(libs.findPlugin("ksp").get().get().pluginId)
                apply("com.google.dagger.hilt.android")
            }

            dependencies {
                add("implementation", libs.findLibrary("hilt-android").get())
                add("ksp", libs.findLibrary("hilt-compiler").get())
                add("androidTestImplementation", libs.findLibrary("hilt-android-testing").get())
                add("kspAndroidTest", libs.findLibrary("hilt-compiler").get())
            }
        }
    }
}
```

### Room Convention Plugin

`build-logic/convention/src/main/kotlin/com/example/convention/AndroidRoomConventionPlugin.kt`:
```kotlin
package com.example.convention

import androidx.room.gradle.RoomExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.artifacts.VersionCatalogsExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType

class AndroidRoomConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) {
        with(target) {
            val libs = extensions.getByType<VersionCatalogsExtension>().named("libs")
            
            pluginManager.apply {
                apply(libs.findPlugin("ksp").get().get().pluginId)
                apply("androidx.room")
            }
            
            extensions.configure<RoomExtension> {
                // Generate Kotlin code instead of Java
                schemaDirectory("$projectDir/schemas")
            }

            dependencies {
                add("implementation", libs.findLibrary("room-runtime").get())
                add("implementation", libs.findLibrary("room-ktx").get())
                add("ksp", libs.findLibrary("room-compiler").get())
                add("testImplementation", libs.findLibrary("room-testing").get())
            }
        }
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
        val detektPluginId = libs.findPlugin("detekt").get().get().pluginId

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
    id("com.example.android.feature")
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
    id("java-library")
    alias(libs.plugins.kotlin.jvm)
    alias(libs.plugins.kotlin.serialization)
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
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
    id("com.example.android.library")
    id("com.example.android.hilt")
    alias(libs.plugins.kotlin.serialization)
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
    id("com.example.android.library")
    id("com.example.android.hilt")
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
    id("com.example.android.library")
    id("com.example.android.room")
    id("com.example.android.hilt")
}

android {
    namespace = "com.example.core.database"
}

dependencies {
    implementation(project(":core:domain"))
    
    // Room (configured by convention plugin)
    // Testing
    testImplementation(libs.bundles.unit.test)
}
```

### Benchmark Module (Optional)

Create a dedicated `:benchmark` test module for macrobenchmark performance testing. See `references/android-performance.md` for when to use.

`benchmark/build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.android.test)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "com.example.benchmark"
    compileSdk = libs.versions.compileSdk.get().toInt()

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

### Compose Stability Analyzer (Optional)

For real-time stability analysis and CI validation of Jetpack Compose composables. See `references/android-performance.md` → "Compose Stability Validation (Optional)" for when to use.

Root `build.gradle.kts`:
```kotlin
plugins {
    alias(libs.plugins.compose.stability.analyzer) apply false
}
```

Module `build.gradle.kts` (typically app or feature modules):
```kotlin
plugins {
    id("com.example.android.application")
    alias(libs.plugins.compose.stability.analyzer)
}

composeStabilityAnalyzer {
    stabilityValidation {
        enabled.set(true)
        outputDir.set(layout.projectDirectory.dir("stability"))
        includeTests.set(false)
        failOnStabilityChange.set(true) // Fail build on stability regressions
        
        // Optional: Exclude specific packages or classes
        ignoredPackages.set(listOf("com.example.internal"))
        ignoredClasses.set(listOf("PreviewComposables"))
    }
}
```

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

# Configuration cache (Gradle 8.1+)
org.gradle.configuration-cache=true
org.gradle.configuration-cache.problems=warn

# Android build optimization
android.enableBuildCache=true
android.useAndroidX=true
android.enableJetifier=false
kotlin.incremental=true
kotlin.caching.enabled=true

# Module metadata
android.defaults.buildfeatures.buildconfig=true
android.nonTransitiveRClass=true

# KSP optimization
ksp.incremental=true
ksp.incremental.log=false
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

# Keep kotlinx-serialization
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Keep Retrofit
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepattributes AnnotationDefault
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}

# Generic rules
-dontwarn kotlinx.coroutines.**
-dontwarn javax.annotation.**
-dontwarn org.conscrypt.**
-dontwarn org.bouncycastle.**
-dontwarn org.openjsse.**
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
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.android.library) apply false
    alias(libs.plugins.android.test) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.jvm) apply false
    alias(libs.plugins.kotlin.serialization) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.hilt) apply false
    alias(libs.plugins.detekt) apply false
    alias(libs.plugins.spotless) apply false
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
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

## Best Practices

1. **Use Version Catalog**: Centralize dependency versions for consistency
2. **Convention Plugins**: Extract common build logic to avoid duplication
3. **KSP over kapt**: 2x faster annotation processing (see `references/dependencies.md`)
4. **Type-safe Project Accessors**: Enable for better IDE support
5. **Build Caching**: Configure local and remote caches for faster builds
6. **Modular Builds**: Use our strict dependency rules for clean architecture
7. **Progressive Enhancement**: Start simple, add flavors and optimizations as needed
8. **CI/CD Ready**: Ensure build configuration works well with CI systems
9. **Profile Builds**: Use `./gradlew assembleDebug --profile` to identify bottlenecks
10. **Compose-First**: No View binding or legacy View system support

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
