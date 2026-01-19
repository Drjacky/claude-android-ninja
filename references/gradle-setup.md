# Gradle & Build Configuration

Build system patterns following our modern Android multi-module architecture with Navigation3, Jetpack Compose, and convention plugins.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Version Catalog](#version-catalog)
3. [Convention Plugins](#convention-plugins)
4. [Module Build Files](#module-build-files)
5. [Build Variants & Optimization](#build-variants--optimization)
6. [Build Performance](#build-performance)

## Project Structure

```
project-root/
├── app/                              # App module - navigation, DI, entry point
│   └── build.gradle.kts
├── feature/                          # Feature modules
│   ├── feature-auth/
│   │   └── build.gradle.kts
│   ├── feature-home/
│   │   └── build.gradle.kts
│   ├── feature-profile/
│   │   └── build.gradle.kts
│   └── feature-settings/
│       └── build.gradle.kts
├── core/                             # Core modules
│   ├── domain/
│   │   └── build.gradle.kts
│   ├── data/
│   │   └── build.gradle.kts
│   ├── ui/
│   │   └── build.gradle.kts
│   ├── network/
│   │   └── build.gradle.kts
│   ├── database/
│   │   └── build.gradle.kts
│   ├── datastore/
│   │   └── build.gradle.kts
│   ├── common/
│   │   └── build.gradle.kts
│   └── testing/
│       └── build.gradle.kts
├── build-logic/                      # Convention plugins
│   ├── convention/
│   │   ├── build.gradle.kts
│   │   └── src/main/kotlin/com/example/convention/
│   │       ├── AndroidApplicationConventionPlugin.kt
│   │       ├── AndroidLibraryConventionPlugin.kt
│   │       ├── AndroidFeatureConventionPlugin.kt
│   │       ├── AndroidComposeConventionPlugin.kt
│   │       ├── AndroidHiltConventionPlugin.kt
│   │       └── AndroidRoomConventionPlugin.kt
│   └── settings.gradle.kts
├── gradle/
│   └── libs.versions.toml            # Version catalog
├── gradle.properties                 # Build properties
├── build.gradle.kts                  # Root build file
└── settings.gradle.kts               # Project settings
```

## Version Catalog

`gradle/libs.versions.toml`:

```toml
[versions]
# SDK versions
compileSdk = "34"
minSdk = "24"
targetSdk = "34"

# Kotlin
kotlin = "1.9.22"
kotlinxCoroutines = "1.7.3"
kotlinxSerialization = "1.6.0"

# Compose & Material 3
composeBom = "2024.02.01"
composeCompiler = "1.5.11"
material3Adaptive = "1.0.0-beta01"

# AndroidX
androidxCore = "1.12.0"
androidxLifecycle = "2.7.0"
androidxActivity = "1.8.2"
androidxNavigation3 = "1.4.0-beta01"

# Data Persistence
room = "2.6.1"
datastore = "1.0.0"

# Dependency Injection
hilt = "2.50"

# Networking
retrofit = "2.9.0"
okhttp = "4.12.0"

# Testing
junit = "4.13.2"
androidxTest = "1.5.0"
turbine = "1.1.0"

# Build Tools
androidGradlePlugin = "8.2.2"
ksp = "1.9.22-1.0.17"

[libraries]
# Kotlin
kotlin-stdlib = { group = "org.jetbrains.kotlin", name = "kotlin-stdlib", version.ref = "kotlin" }
kotlinx-coroutines-android = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-android", version.ref = "kotlinxCoroutines" }
kotlinx-coroutines-test = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-test", version.ref = "kotlinxCoroutines" }
kotlinx-serialization-json = { group = "org.jetbrains.kotlinx", name = "kotlinx-serialization-json", version.ref = "kotlinxSerialization" }

# AndroidX Core
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "androidxCore" }
androidx-lifecycle-runtime-compose = { group = "androidx.lifecycle", name = "lifecycle-runtime-compose", version.ref = "androidxLifecycle" }
androidx-lifecycle-viewmodel-compose = { group = "androidx.lifecycle", name = "lifecycle-viewmodel-compose", version.ref = "androidxLifecycle" }
androidx-activity-compose = { group = "androidx.activity", name = "activity-compose", version.ref = "androidxActivity" }

# Compose Platform
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }

# Compose UI
androidx-compose-ui = { group = "androidx.compose.ui", name = "ui" }
androidx-compose-ui-graphics = { group = "androidx.compose.ui", name = "ui-graphics" }
androidx-compose-ui-tooling = { group = "androidx.compose.ui", name = "ui-tooling" }
androidx-compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview" }
androidx-compose-ui-test-manifest = { group = "androidx.compose.ui", name = "ui-test-manifest" }
androidx-compose-ui-test-junit4 = { group = "androidx.compose.ui", name = "ui-test-junit4" }

# Material 3
androidx-compose-material3 = { group = "androidx.compose.material3", name = "material3" }
androidx-compose-material-icons-extended = { group = "androidx.compose.material", name = "material-icons-extended" }

# Navigation3
androidx-navigation3-compose = { group = "androidx.navigation3", name = "navigation3-compose", version.ref = "androidxNavigation3" }
androidx-material3-adaptive-navigation3 = { group = "androidx.compose.material3.adaptive", name = "adaptive-navigation3", version.ref = "material3Adaptive" }

# Dependency Injection
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-android-compiler = { group = "com.google.dagger", name = "hilt-android-compiler", version.ref = "hilt" }

# Room
room-runtime = { group = "androidx.room", name = "room-runtime", version.ref = "room" }
room-ktx = { group = "androidx.room", name = "room-ktx", version.ref = "room" }
room-compiler = { group = "androidx.room", name = "room-compiler", version.ref = "room" }

# DataStore
androidx-datastore-preferences = { group = "androidx.datastore", name = "datastore-preferences", version.ref = "datastore" }
androidx-datastore-core = { group = "androidx.datastore", name = "datastore-core", version.ref = "datastore" }

# Networking
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
retrofit-kotlinx-serialization = { group = "com.jakewharton.retrofit", name = "retrofit2-kotlinx-serialization-converter", version = "1.0.0" }
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
okhttp-logging-interceptor = { group = "com.squareup.okhttp3", name = "logging-interceptor", version.ref = "okhttp" }

# Testing
junit = { group = "junit", name = "junit", version.ref = "junit" }
androidx-test-ext-junit = { group = "androidx.test.ext", name = "junit", version = "1.1.5" }
androidx-test-espresso-core = { group = "androidx.test.espresso", name = "espresso-core", version = "3.5.1" }
turbine = { group = "app.cash.turbine", name = "turbine", version.ref = "turbine" }

# Build tools for convention plugins
android-gradlePlugin = { group = "com.android.tools.build", name = "gradle", version.ref = "androidGradlePlugin" }
kotlin-gradlePlugin = { group = "org.jetbrains.kotlin", name = "kotlin-gradle-plugin", version.ref = "kotlin" }
ksp-gradlePlugin = { group = "com.google.devtools.ksp", name = "com.google.devtools.ksp.gradle.plugin", version.ref = "ksp" }
hilt-gradlePlugin = { group = "com.google.dagger", name = "hilt-android-gradle-plugin", version.ref = "hilt" }

[bundles]
# Common dependency bundles
navigation3 = [
    "androidx-navigation3-compose",
    "androidx-material3-adaptive-navigation3"
]

compose = [
    "androidx-compose-ui",
    "androidx-compose-ui-tooling-preview",
    "androidx-compose-material3",
    "androidx-compose-foundation",
    "androidx-compose-material-icons-extended"
]

compose-testing = [
    "androidx-compose-ui-test-junit4",
    "androidx-compose-ui-test-manifest"
]

testing = [
    "junit",
    "androidx-test-ext-junit",
    "kotlinx-coroutines-test",
    "turbine"
]

[plugins]
# External plugins
android-application = { id = "com.android.application", version.ref = "androidGradlePlugin" }
android-library = { id = "com.android.library", version.ref = "androidGradlePlugin" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
kotlin-kapt = { id = "org.jetbrains.kotlin.kapt", version.ref = "kotlin" }
kotlin-serialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
hilt-android = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }

# Our convention plugins
android-application-convention = { id = "com.example.android.application", version = "unspecified" }
android-library-convention = { id = "com.example.android.library", version = "unspecified" }
android-feature-convention = { id = "com.example.android.feature", version = "unspecified" }
android-compose-convention = { id = "com.example.android.compose", version = "unspecified" }
android-hilt-convention = { id = "com.example.android.hilt", version = "unspecified" }
android-room-convention = { id = "com.example.android.room", version = "unspecified" }
```

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
    implementation(project(":feature-home"))
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
    implementation(project(":core:testing"))
    
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
android.enableJetifier=true
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

# Keep Navigation arguments
-keep class * implements androidx.navigation.NavArgs { *; }
-keep class * implements androidx.navigation.NavArgument { *; }

# Generic rules
-dontwarn kotlinx.coroutines.**
-dontwarn javax.annotation.**
```

## Build Performance

### Settings Configuration

`settings.gradle.kts`:
```kotlin
pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        
        // Add any custom repositories here
        maven { url = uri("https://jitpack.io") }
    }
    
    versionCatalogs {
        create("libs") {
            from(files("gradle/libs.versions.toml"))
        }
    }
}

enableFeaturePreview("TYPESAFE_PROJECT_ACCESSORS")
enableFeaturePreview("STABLE_CONFIGURATION_CACHE")

rootProject.name = "MyApp"

// App module
include(":app")

// Feature modules
include(":feature-auth")
include(":feature-home")
include(":feature-profile")
include(":feature-settings")

// Core modules
include(":core:domain")
include(":core:data")
include(":core:ui")
include(":core:network")
include(":core:database")
include(":core:datastore")
include(":core:common")
include(":core:testing")

// Build optimization
configureBuildOptimization()

fun configureBuildOptimization() {
    // Enable parallel build for modules
    gradle.settingsEvaluated {
        for (project in projects) {
            project.setBuildFileName("build.gradle.kts")
        }
    }
}
```

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