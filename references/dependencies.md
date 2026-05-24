# Dependencies

Required: every dependency goes through `assets/libs.versions.toml.template`. Do not hard-code coordinates or versions in module `build.gradle.kts`.

## Table of Contents

1. [Version Catalog Source of Truth](#version-catalog-source-of-truth)
2. [Dependency Selection](#dependency-selection)
3. [Version Strategy](#version-strategy)
4. [Kotlin & Compose Compiler Compatibility](#kotlin-compose-compiler-compatibility)
5. [Platform Dependencies (BOMs)](#platform-dependencies-boms)
6. [Testing Dependencies](#testing-dependencies)
7. [Build Performance Considerations](#build-performance-considerations)
8. [ProGuard/R8 Considerations](#proguardr8-considerations)
9. [Adding a New Dependency](#adding-a-new-dependency)

## Version Catalog Source of Truth
Always check `assets/libs.versions.toml.template` before adding or changing dependencies.

### Rules
1. **Reuse existing catalog entries** before inventing new coordinates
2. **If a dependency is missing**, add it to `libs.versions.toml` following the same grouping and naming conventions
3. **Keep versions centralized** in the `[versions]` section; reference them by `version.ref`
4. **Use bundles** when multiple libraries ship together (e.g., Compose, Navigation, Testing)
5. **Use platform dependencies** (BOMs) for coordinated version management (Compose, Firebase)

## Dependency Selection

| Concern              | Use                                                                          | Avoid / Only-if-migrating                          |
|----------------------|------------------------------------------------------------------------------|----------------------------------------------------|
| REST networking      | Retrofit + OkHttp + `retrofit2-kotlinx-serialization-converter`              | Ktor Client (reserve for Kotlin Multiplatform)     |
| Image loading        | Coil 3.x (`coil-compose` + `coil-network-okhttp`)                            | Glide (only when migrating heavy View-based usage) |
| JSON serialization   | `kotlinx-serialization`                                                      | Gson (only with deep existing investment)          |
| Dependency injection | Hilt (required)                                                              | Manual DI, Koin                                    |
| AndroidX             | `-ktx` artifacts (`core-ktx`, `lifecycle-runtime-ktx`, ...)                    | `com.android.support.*` (deprecated)               |

Hilt module patterns, scopes, and anti-patterns: [architecture.md → Dependency Injection Setup](architecture.md#dependency-injection-setup).

### Room 3
Required artifacts: `androidx.room3:room3-runtime`, `sqlite-bundled`, KSP `room3-compiler` (see version catalog). DAOs are coroutine-first (`suspend`, `Flow`). Add `room3-paging` only when a DAO returns `PagingSource`; `room3-testing` only for instrumented DB tests.

### Media3
Required for background playback at target SDK 37: `androidx.media3:media3-exoplayer`, `media3-session` (catalog `media3` version ref, bundle `media3-playback`). Pin from [Media3 releases](https://developer.android.com/jetpack/androidx/releases/media3). Playback rules: [android-media.md](android-media.md).

### Navigation3 and SavedState
Pin `navigation3` from [Navigation 3 releases](https://developer.android.com/jetpack/androidx/releases/navigation3) (template: latest stable). Pin `savedstateCompose` from [SavedState releases](https://developer.android.com/jetpack/androidx/releases/savedstate) when using `savedstate-compose` with `@Serializable` `NavKey` graphs.

### Paging 3 test artifact
Use `androidx.paging:paging-testing` on test source sets only (`testImplementation(libs.androidx.paging.testing)` from the version catalog). Keep the `paging` version ref aligned with `paging-runtime` / `paging-compose`. Align snapshot and scroll test code with [Test your Paging implementation](https://developer.android.com/topic/libraries/architecture/paging/test).

## Version Strategy

### Existing project (brownfield)

Required before changing versions in a user repo:

1. Treat the project's `gradle/libs.versions.toml` (or equivalent) as source of truth, not `assets/libs.versions.toml.template`.
2. Read `compileSdk`, `targetSdk`, and applied AGP/Kotlin/KSP lines from convention plugins or the `app` module.
3. Propose template/catalog upgrades only when the user asks, `./gradlew help` fails, or a migration doc in [migration.md](migration.md) requires a bump.
4. After any catalog or AGP/Kotlin/KSP bump: `./gradlew help` must pass before merge.

Forbidden:

- Overwrite the user's version catalog with `assets/libs.versions.toml.template` without explicit request.
- Bump AGP/Kotlin/KSP/Room in the same task as an unrelated feature without `./gradlew help` passing on the result.
- Assume `compileSdk` / `targetSdk` 37 when the project pins lower values.

Greenfield bootstrap pins: [workflows.md](workflows.md) ("Creating a new project?") and `assets/libs.versions.toml.template`.

### Stability Requirements

**Production apps:**
- Use **stable** versions only (e.g., `1.0.0`) for libraries that offer a stable channel
- Avoid alpha/beta/RC for **Hilt** and **Coroutines** in production
- **Room 3:** Ship **stable** `androidx.room3` builds from [Room 3 releases](https://developer.android.com/jetpack/androidx/releases/room3). Preview builds require pinning the exact version from that page and scheduling the upgrade to stable.

**Experimental projects:**
- Can use alpha/beta for evaluation
- Document experimental versions clearly

### Pinned alpha required for feature parity

These catalog entries stay on alpha until a feature-equivalent stable release ships. Replace each pin with the stable release as soon as one exists.

- `room3` - no stable Room 3 release yet; template pins `3.0.0-alpha05` (track [Room 3 releases](https://developer.android.com/jetpack/androidx/releases/room3) and bump on every alpha tick).
- `materialAdaptive` - [Material3 Adaptive 1.2.0](https://developer.android.com/jetpack/androidx/releases/compose-material3-adaptive) is stable, but `material3-adaptive-navigation3` still ships only on the 1.3 alpha line; keep `materialAdaptive` on 1.3 alpha until the bridge artifact has a stable coordinate.
- `navigation3` - production template uses latest **stable** (currently `1.1.2`). `DeepLinkRequest` / `UriDeepLinkMatcher` require Navigation3 **1.2** ([release notes](https://developer.android.com/jetpack/androidx/releases/navigation3)); adopt 1.2 only on an alpha pin when the feature is required before 1.2 stable.
- `androidxBiometric` - 1.1.0 stable lacks `BiometricPrompt` content view, logo, and `registerForAuthenticationResult()`; the alpha line is the only source for those APIs.
- `tracing` - `tracing-wire-android` (Perfetto in-process tracing) is 2.x-only; the 1.3 stable line cannot be substituted.
- `detekt` - 2.x is a new artifact group (`dev.detekt`); 1.23.x lives at `io.gitlab.arturbosch.detekt` and would require swapping coordinates.
- `screenshot` - Compose Preview Screenshot Testing plugin line; still pre-stable on many stacks - bump only from Android Studio / AGP release notes and re-run `screenshotTest` validation after every pin change. Roborazzi is optional visual-regression tooling; pin `io.github.takahirom.roborazzi` artifacts in the catalog only when the project adopts it ([testing.md → Preview Screenshot Testing vs Roborazzi](testing.md#preview-screenshot-testing-vs-roborazzi)).

### Visual regression tooling (catalog)

| Tooling                            | Catalog                                                                                     | Rule                                                                                |
|------------------------------------|---------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Compose Preview Screenshot Testing | `screenshot` plugin + `screenshot-validation-api` from `assets/libs.versions.toml.template` | Keep in `screenshotTest`; align pins with Studio docs                               |
| Roborazzi                          | Not in the template catalog until a project adds explicit coordinates                       | Add `io.github.takahirom.roborazzi` modules only when Roborazzi is the chosen stack |

### Version update cadence

**Security patches:**

- Update immediately for CVEs
- Check dependency-check tools or GitHub security alerts

**Feature updates:**

- Update when needed for specific features
- Test thoroughly in feature branches

**Breaking changes:**

- Update during planned refactoring windows
- Review migration guides first

### Version Conflict Resolution

**Use platform dependencies (BOMs) for coordinated versioning:**

```kotlin
dependencies {
    // Compose BOM manages all Compose library versions
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3) // Version from BOM
    
    // Firebase BOM
    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.crashlytics) // Version from BOM
    implementation(libs.firebase.analytics)
}
```

**Force specific versions when needed:**

```kotlin
configurations.all {
    resolutionStrategy {
        force("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.10.2")
    }
}
```

## Kotlin & Compose Compiler Compatibility

**Critical**: Kotlin and Compose compiler versions must be compatible. Mismatches cause compile errors.

Current template versions:
- Kotlin: `2.3.21`
- Compose BOM: `2026.04.01`
- Compose Compiler: Managed by `kotlin-compose` plugin

The `kotlin-compose` plugin (formerly `compose-compiler`) is now part of Kotlin and automatically matches the Kotlin version.

**When updating Kotlin:**
1. Check Compose compatibility: https://developer.android.com/jetpack/androidx/releases/compose-kotlin
2. Update both `kotlin` and `compose-bom` versions together
3. Pick the matching KSP line on Maven Central or [KSP releases](https://github.com/google/ksp/releases); catalog `ksp` may use a `kotlinVersion-kspToolVersion` string or a standalone KSP release (patch digits need not match Kotlin)
4. Run `./gradlew help` before committing

## Platform Dependencies (BOMs)

BOMs (Bill of Materials) manage versions of related libraries, ensuring compatibility.

**Use BOMs when:**

```kotlin
// Compose BOM - manages all androidx.compose.* versions
implementation(platform(libs.androidx.compose.bom))

// Firebase BOM - manages all firebase.* versions  
implementation(platform(libs.firebase.bom))
```

**Don't specify versions for BOM-managed dependencies:**

```kotlin
// CORRECT: version from BOM
implementation(libs.androidx.compose.ui)

// WRONG: explicit version overrides BOM
implementation("androidx.compose.ui:ui:1.7.0")
```

## Testing Dependencies

### Test Scopes

**`testImplementation`** - Unit tests (JVM)
- `junit`, `kotlin-test`, `mockk`, `kotlinx-coroutines-test`, `turbine`, `google-truth`

**`androidTestImplementation`** - Instrumented tests (Android device/emulator)
- `androidx-junit`, `androidx-espresso-core`, `androidx-compose-ui-test-junit4`

**`debugImplementation`** - Debug builds only
- `leakcanary-android`, `androidx-compose-ui-tooling`, `androidx-compose-ui-test-manifest`

### Test Bundles

Use `libs.bundles.unit-test` and `libs.bundles.android-test` for consistent test dependencies across modules. 
These are defined in `assets/libs.versions.toml.template`.

## Build Performance Considerations

### `api` vs `implementation`

**`implementation`:** default for module-private dependencies - hides transitives from downstream compilation units and limits recompilation when internals change.

**`api`:** dependency types appear in the module's public API (signatures, public properties), e.g. `core:domain` exporting `Flow` from `kotlinx-coroutines`.

```kotlin
// core:domain/build.gradle.kts
dependencies {
    // Coroutines types are in public API (suspend, Flow)
    api(libs.kotlinx.coroutines.core)
    
    // Inject is only used internally
    implementation(libs.java.inject)
}
```

### Annotation Processing: KSP > Kapt

**Required: KSP (Kotlin Symbol Processing).**
- 2x faster than kapt
- **Room 3 is KSP-only** (no kapt/Java annotation processing for Room)
- Hilt supports KSP
- Catalog `kotlin` and `ksp` are a **tested pair**, not identical patch strings. KSP ships on its own schedule; choose the highest KSP release that supports the catalog Kotlin version, then verify `./gradlew help`.

**Migrate from kapt to KSP:**

```kotlin
// Old
plugins {
    id("kotlin-kapt")
}

kapt {
    correctErrorTypes = true
}

dependencies {
    kapt(libs.hilt.compiler)
    kapt("androidx.room:room-compiler:<room2Version>") // Room 2.x: pin <room2Version> locally; not in template catalog
}

// New
plugins {
    id("com.google.devtools.ksp") version "2.3.7"
}

dependencies {
    ksp(libs.hilt.compiler)
    ksp(libs.room3.compiler)
    // Room 3 also requires a SQLite driver at runtime, e.g. sqlite-bundled (see app.android.room convention)
}
```

## ProGuard/R8 Considerations

Use `assets/proguard-rules.pro.template` as the source of truth for all keep rules. It includes rules for every library in the version catalog (Retrofit, kotlinx-serialization, Room 3, OkHttp, Hilt, SQLCipher, etc.).

Copy the template to `app/proguard-rules.pro` and adjust `com.example.*` package names. See [gradle-setup.md](gradle-setup.md#r8-proguard-configuration) for build configuration.

## Adding a New Dependency

Checklist (in order, fail-fast):

- [ ] Confirm it is not already in `assets/libs.versions.toml.template`.
- [ ] Stable channel exists (Hilt/Coroutines/Retrofit/Coil must be stable).
- [ ] Actively maintained (commit/release within last 12 months).
- [ ] License is Apache 2.0 or MIT (or pre-approved equivalent).
- [ ] APK size impact measured for app modules.
- [ ] Add `[versions]` + `[libraries]` entries in `libs.versions.toml` (and a bundle if used together).
- [ ] Reference via `libs.<group>.<name>` in module `build.gradle.kts` - never raw coordinates.
- [ ] Add ProGuard/R8 keep rules to `assets/proguard-rules.pro.template` if the library uses reflection or annotations.
- [ ] Run `./gradlew assembleDebug testDebugUnitTest` before commit.

Example wiring after the catalog entries are added:

```kotlin
dependencies {
    implementation(libs.ktor.client.core)
    implementation(libs.ktor.client.android)
}
```

Convention-plugin and module wiring details: [gradle-setup.md](gradle-setup.md).
