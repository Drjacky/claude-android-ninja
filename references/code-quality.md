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
- The Detekt plugin version and plugin ID.
- The Compose detekt rules dependency (`compose-rules-detekt`).

Use `templates/detekt.yml.template` as the baseline rules file; copy it to
`plugins/detekt.yml` and customize it there (modules can optionally provide
a local `detekt.yml` override).

## Detekt Convention Plugin (Build Logic)
Create `build-logic/convention/src/main/kotlin/com/example/convention/DetektConventionPlugin.kt`:
```kotlin
package com.example.convention

import io.gitlab.arturbosch.detekt.Detekt
import io.gitlab.arturbosch.detekt.DetektCreateBaselineTask
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

            // Use per-module baselines (not shared)
            val moduleBaseline = file("detekt-baseline.xml")
            if (moduleBaseline.exists()) {
                baseline = moduleBaseline
            }
        }

        // Enable type resolution and set consistent JDK target.
        tasks.withType<Detekt>().configureEach {
            jvmTarget = "17"
            
            // Enable type resolution for Android modules
            // This is critical for accurate Compose/Android analysis
            reports {
                html.required.set(true)
                xml.required.set(true)
                txt.required.set(false)
                sarif.required.set(true)
            }
        }
        
        // Configure baseline task
        tasks.withType<DetektCreateBaselineTask>().configureEach {
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

## Running Detekt

### Local Development

Run detekt for all modules:
```bash
./gradlew detekt
```

Run for specific module:
```bash
./gradlew :app:detekt
./gradlew :feature-auth:detekt
```

Run with type resolution (slower, more accurate):
```bash
./gradlew detektMain
```

### Excluding Generated Code

Add to `plugins/detekt.yml`:
```yaml
build:
  excludes:
    - '**/build/**'
    - '**/generated/**'
    - '**/*.kts'
    - '**/resources/**'
```

## Baselines & CI

### When to Use Baselines

**Use baselines when:**
- Adopting detekt in an existing project with many violations
- You want to prevent new issues without fixing old ones immediately
- You're enabling new rules gradually

**Don't use baselines when:**
- Starting a new project (fix issues instead)
- In active development (baselines hide problems)

### Creating Per-Module Baselines

Generate baseline for a specific module:
```bash
./gradlew :app:detektBaseline
```

This creates `app/detekt-baseline.xml` which suppresses existing issues in that module only.

Commit the baseline:
```bash
git add app/detekt-baseline.xml
git commit -m "Add detekt baseline for app module"
```

### CI Integration

**GitHub Actions example:**

```yaml
name: Code Quality

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  detekt:
    name: Detekt Check
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-java@v4
        with:
          distribution: 'zulu'
          java-version: '17'
      
      - name: Setup Gradle
        uses: gradle/actions/setup-gradle@v3
      
      - name: Run Detekt
        run: ./gradlew detekt
      
      - name: Upload SARIF to GitHub Security
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: build/reports/detekt/detekt.sarif
      
      - name: Upload HTML Reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: detekt-reports
          path: '**/build/reports/detekt/'
```

**Key CI considerations:**
- Use `if: always()` to upload reports even on failure
- Upload SARIF for GitHub Security tab integration
- Fail the build if issues are found (default behavior)
- Cache Gradle dependencies for faster builds

If the project uses Gradle toolchains, Detekt will resolve the proper JDK automatically.

## Compose Rules
The Compose detekt ruleset is configured in `templates/detekt.yml.template`. Use that template as-is.
For compatibility information and latest rules, see: [Compose rules + detekt compatibility](https://mrmans0n.github.io/compose-rules/detekt/)
