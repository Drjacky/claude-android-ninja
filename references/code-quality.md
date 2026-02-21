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

The `DetektConventionPlugin` is available in `templates/convention/DetektConventionPlugin.kt`.

Copy it to `build-logic/convention/src/main/kotlin/DetektConventionPlugin.kt` in your project.

Key features:
- Applies Detekt plugin from version catalog
- Adds Compose rules automatically
- Configures central config file (`config/detekt.yml`)
- Supports module-specific overrides
- Enables type resolution for Android modules
- Generates XML, HTML, and SARIF reports

### Build Logic Registration

The Detekt plugin is already registered in the build script available at `templates/convention/build.gradle.kts`. 

When you copy the build script to your project's `build-logic/convention/build.gradle.kts`, the Detekt plugin registration is included:

```kotlin
register("detekt") {
    id = "app.detekt"
    implementationClass = "DetektConventionPlugin"
}
```

## Apply in Modules

Apply the convention plugin in every module:
```kotlin
plugins {
    alias(libs.plugins.app.detekt)
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

## Suppressing Violations

### Acceptable Suppressions for Compose

Jetpack Compose composables are declarative UI functions that naturally differ from imperative code. The following suppressions are acceptable when applied to `@Composable` functions:

#### `@Suppress("LongMethod")`
Composable UI functions declare layout trees and are naturally longer than business logic functions.

```kotlin
@Suppress("LongMethod")
@Composable
fun ProductDetailScreen(
    product: Product,
    onAddToCart: () -> Unit,
    onNavigateBack: () -> Unit
) {
    Scaffold(
        topBar = { /* AppBar with 10+ lines */ },
        bottomBar = { /* Actions with 10+ lines */ }
    ) { padding ->
        LazyColumn(Modifier.padding(padding)) {
            item { /* Hero image section 15+ lines */ }
            item { /* Title and price section 10+ lines */ }
            item { /* Description section 10+ lines */ }
            item { /* Specifications section 20+ lines */ }
            item { /* Reviews section 15+ lines */ }
            // Total: 80+ lines is normal for a detail screen
        }
    }
}
```

#### `@Suppress("LongParameterList")`
Route/Screen composables accept ViewModels, callbacks, modifiers, and navigation arguments.

```kotlin
@Suppress("LongParameterList")
@Composable
fun ProductDetailRoute(
    productId: String,
    viewModel: ProductDetailViewModel = hiltViewModel(),
    navigator: ProductNavigator,
    onAddToCart: (Product) -> Unit,
    onShareProduct: (Product) -> Unit,
    modifier: Modifier = Modifier
) {
    // 6+ parameters is normal for feature entry points
}
```

#### `@Suppress("CyclomaticComplexMethod")`
Composables handling UI state often have multiple `when` branches for different states.

```kotlin
@Suppress("CyclomaticComplexMethod")
@Composable
fun ProductsContent(state: ProductsUiState) {
    when (state) {
        is Loading -> LoadingIndicator()
        is Empty -> EmptyState()
        is Error -> ErrorMessage(state.message)
        is Success -> when {
            state.products.isEmpty() -> EmptyProductsList()
            state.isFiltered -> FilteredProductsList(state.products, state.filter)
            else -> ProductsList(state.products)
        }
    }
    // Multiple when branches for UI states is normal
}
```

**Placement:** Place `@Suppress` directly above `@Composable`:
```kotlin
@Suppress("LongMethod", "CyclomaticComplexMethod")
@Composable
fun MyScreen() { /* ... */ }
```

### Targeted Suppressions

#### `@Suppress` on Catch Parameters
For `TooGenericExceptionCaught`, place `@Suppress` on the catch parameter for maximum precision:

```kotlin
try {
    riskyOperation()
} catch (@Suppress("TooGenericExceptionCaught") e: Exception) {
    // Sometimes catching Exception is the right choice
    // (e.g., unknown third-party library exceptions)
    crashReporter.recordException(e)
}
```

This is more precise than suppressing the entire function.

#### File-Level Suppressions

Use `@file:Suppress` when an issue affects the entire file:

```kotlin
@file:Suppress("MatchingDeclarationName")
package com.example.ui.view

// File: AnAnimatedComposableExampleView.kt
// Contains helper enum + main composable

enum class CirclePosition { START, END }

@Composable
fun AnAnimatedComposableExampleView(...) { /* ... */ }
```

**When to use:**
- `MatchingDeclarationName`: File has a primary composable plus supporting types (enums, sealed classes, data classes)
- `TooManyFunctions`: Composable files with many small helper composables
- `MagicNumber`: UI files with many layout dimensions

### When NOT to Suppress

Avoid suppressing these without fixing the underlying issue:
- `ComplexMethod` in ViewModels or business logic → Refactor the code
- `LongParameterList` in data classes → Consider builder pattern or DSL
- `TooGenericExceptionCaught` when you can handle specific exceptions → Use specific catches
- `UnusedPrivateProperty` → Remove the property

## Best Practices

1. **Fix, don't suppress**: Suppressions should be rare. Refactor code instead.
2. **Justify suppressions**: Add a comment explaining why the suppression is necessary.
3. **Be specific**: Use targeted suppressions (catch parameters, single functions) over file-level.
4. **Review suppressions**: Suppressions added "temporarily" tend to become permanent. Review regularly.
5. **Compose is different**: Accept that Compose composables naturally violate some imperative code rules.
