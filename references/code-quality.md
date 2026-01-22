# Code Quality (Detekt)

Detekt is the primary static analysis tool for this multi-module Android project.
We integrate it through build-logic convention plugins so every module is configured consistently.

## Goals
- Single source of truth for rules (`plugins/detekt.yml`) with optional per-module overrides.
- Type-resolution enabled tasks for accurate analysis in Android modules.
- Compose-specific rules via the Compose detekt ruleset plugin.
- Kotlin 2.2.x compatible configuration without legacy `buildscript` usage.

## Version Catalog
Use `templates/libs.versions.toml.template` as the source of truth for:
- The Detekt plugin version.
- The detekt rules dependency(including Compose rules) (`detekt.yml.template`).

If you move to Detekt 2.x, use the new plugin ID (`dev.detekt`) in the catalog.
For Detekt 1.23.x, the plugin ID remains `io.gitlab.arturbosch.detekt`.

## Detekt Convention Plugin (Build Logic)
Create `build-logic/convention/src/main/kotlin/com/example/convention/DetektConventionPlugin.kt`:
```kotlin
package com.example.convention

import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.extensions.DetektExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.JavaPluginExtension
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.getByType
import org.gradle.kotlin.dsl.withType
import org.gradle.api.artifacts.VersionCatalogsExtension

class DetektConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        val libs = rootProject.extensions.getByType<VersionCatalogsExtension>().named("libs")
        val detektPluginId = libs.findPlugin("detekt").get().pluginId

        pluginManager.apply(detektPluginId)

        dependencies {
            // Compose ruleset for Jetpack Compose best practices.
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

            val baselineFile = rootProject.file("plugins/detekt-baseline.xml")
            if (baselineFile.exists()) {
                baseline = baselineFile
            }
        }

        // Type resolution and consistent JDK target.
        tasks.withType<Detekt>().configureEach {
            jvmTarget = "17"
        }
    }
}
```

### Build Logic Registration
Register the plugin in `build-logic/convention/build.gradle.kts`:
```kotlin
gradlePlugin {
    plugins {
        register("androidDetekt") {
            id = "com.example.android.detekt"
            implementationClass = "com.example.convention.DetektConventionPlugin"
        }
    }
}
```

## Apply in Modules
Apply the convention plugin in every module:
```kotlin
plugins {
    id("com.example.android.detekt")
}
```

## Baselines & CI
- Generate a baseline: `./gradlew detektBaseline`
- Run in CI: `./gradlew detekt` (or `detektMain` for Android-only source sets)

If the project uses Gradle toolchains, Detekt will resolve the proper JDK automatically.
