# Dependencies

Required: every dependency goes through `assets/libs.versions.toml.template`. Do not hard-code coordinates or versions in module `build.gradle.kts`.

## Table of Contents

1. [Version Catalog Source of Truth](#version-catalog-source-of-truth)
2. [Dependency Selection](#dependency-selection)
3. [Version Strategy](#version-strategy)
4. [Kotlin & Compose Compiler Compatibility](#kotlin--compose-compiler-compatibility)
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
| AndroidX             | Base artifact where KTX was merged in (`androidx.core:core`); `-ktx` only where it still ships code (`lifecycle-runtime-ktx`, `work-runtime-ktx`) | `com.android.support.*` (deprecated); `core-ktx`, `palette-ktx`, `sqlite-ktx` (empty shims) |

Hilt module patterns, scopes, and anti-patterns: [architecture.md → Dependency Injection Setup](architecture.md#dependency-injection-setup).

### Merged KTX artifacts (do not add the `-ktx` coordinate)

These `-ktx` artifacts are now **empty compatibility shims**; their extensions moved into the base artifact. Depend on the base coordinate only.

| Forbidden coordinate      | Use instead              | Merged in            |
|---------------------------|--------------------------|----------------------|
| `androidx.core:core-ktx`  | `androidx.core:core`     | `core` 1.19.0        |
| `androidx.sqlite:sqlite-ktx` | `androidx.sqlite:sqlite` | `sqlite` 2.7.0    |
| `androidx.palette:palette-ktx` | `androidx.palette:palette` | `palette` 1.1.0 |

`lifecycle-*-ktx` and `work-runtime-ktx` are **not** affected - keep those `-ktx` coordinates.

### androidx.hilt artifacts

All share the `androidxHilt` version ref (currently `1.4.0`). These are **separate** from the Dagger Hilt `hilt` ref.

| Artifact                                        | Add when                                                                 |
|-------------------------------------------------|--------------------------------------------------------------------------|
| `hilt-lifecycle-viewmodel-compose`              | Any `hiltViewModel()` call site (wired by the feature convention plugin)   |
| `hilt-work` + `hilt-compiler` (on `ksp`)        | Any `@HiltWorker` ([android-data-sync.md](android-data-sync.md#hiltworker-prerequisites)) |

Forbidden: `hilt-navigation-compose` - deprecated, and it pulls `navigation-compose` (Navigation 2) into a Navigation3 project ([architecture.md](architecture.md#hiltviewmodel-artifact-and-import)).

`androidx.hilt` 1.4.0 compiles against `compileSdk` 37, so Compose usage requires **AGP >= 9.2.0**.

### Room 3

Room 3 is **stable** (`androidx.room3` `3.0.0`). Room 2.x (`androidx.room`) is in maintenance (patch releases only).

Required artifacts: `androidx.room3:room3-runtime`, `sqlite-bundled`, KSP `room3-compiler` (see version catalog). DAOs are coroutine-first (`suspend`, `Flow`). Add `room3-paging` only when a DAO returns `PagingSource`; `room3-testing` only for instrumented DB tests.

Optional artifacts, add only when the matching call site exists:

| Artifact               | Add when                                                                                  |
|------------------------|-------------------------------------------------------------------------------------------|
| `room3-paging`         | A DAO returns `PagingSource` (also register `PagingSourceDaoReturnTypeConverter`)          |
| `room3-testing`        | Instrumented migration tests (`MigrationTestHelper`)                                       |
| `room3-sqlite-wrapper` | Bridging **legacy `SupportSQLite` call sites** only - never as a substitute for a driver    |

Forbidden in this stack: `room3-livedata`, `room3-rxjava3`, `room3-guava`. This stack is coroutine-first; a DAO that needs one of those return types is a design problem, not a dependency problem.

`androidx.sqlite` sets a **minSdk 23** floor, so Room 3 cannot ship below API 23 (the template `minSdk` is 24, which satisfies this).

### Media3
Required for background playback at target SDK 37: `androidx.media3:media3-exoplayer`, `media3-session` (catalog `media3` version ref, bundle `media3-playback`). Pin from [Media3 releases](https://developer.android.com/jetpack/androidx/releases/media3). Playback rules: [android-media.md](android-media.md).

Optional Media3 artifacts - add a `[libraries]` entry reusing `version.ref = "media3"` only when a call site needs one:

| Artifact                   | Add when                                                          |
|----------------------------|-------------------------------------------------------------------|
| `media3-ui-compose`, `media3-ui-compose-material3` | Compose-native player UI (**not** at parity with `media3-ui`) |
| `media3-inspector-frame`   | `FrameExtractor` (moved out of `media3-inspector` in 1.10.0)        |
| `media3-effect-lottie`     | `LottieOverlay` (moved in 1.10.0)                                  |

Template pins `1.10.1` stable; `1.11.0` is `rc01` ([android-media.md → Media3 version and artifacts](android-media.md#media3-version-and-artifacts)).

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
- **Room 3:** `3.0.0` is stable - ship it. Do not pin a `3.0.0-alphaNN` / `-rc` build ([Room 3 releases](https://developer.android.com/jetpack/androidx/releases/room3)).

**Experimental projects:**
- Can use alpha/beta for evaluation
- Document experimental versions clearly

### Pinned prerelease required for feature parity

These catalog entries stay on a prerelease line until a feature-equivalent stable release ships. Replace each pin with the stable release as soon as one exists. Every other catalog entry must be stable.

- `materialAdaptive` - [Material3 Adaptive 1.2.0](https://developer.android.com/jetpack/androidx/releases/compose-material3-adaptive) is stable, but `material3-adaptive-navigation3` still ships only on the 1.3 pre-release line (currently `1.3.0-rc01`); keep `materialAdaptive` on the 1.3 line until the bridge artifact has a stable coordinate. This artifact is also **not managed by the Compose BOM** - it needs its own version ref.
- `androidxBiometric` - 1.1.0 stable lacks `BiometricPrompt` content view, logo, and `registerForAuthenticationResult()`; the alpha line is the only source for those APIs.
- `tracing` - `tracing-wire-android` (Perfetto in-process tracing) is 2.x-only (currently `2.0.0-beta01`); the 1.3 stable line cannot be substituted.
- `detekt` - 2.x is a new artifact group (`dev.detekt`); 1.23.x lives at `io.gitlab.arturbosch.detekt` and would require swapping coordinates.
- `screenshot` - Compose Preview Screenshot Testing plugin line (currently `0.0.1-alpha15`); still pre-stable on every stack - bump only from Android Studio / AGP release notes and re-run `screenshotTest` validation after every pin change. Roborazzi is optional visual-regression tooling; pin `io.github.takahirom.roborazzi` artifacts in the catalog only when the project adopts it ([testing.md → Preview Screenshot Testing vs Roborazzi](testing.md#preview-screenshot-testing-vs-roborazzi)).

Stable pins with a prerelease line deliberately **not** adopted:

- `navigation3` - template pins the latest **stable** (`1.1.4`). Deep-link APIs (`DeepLinkRequest`, `DeepLinkMatcher`, `UriDeepLinkMatcher`) exist only on the **1.2** alpha line, whose API is still churning ([release notes](https://developer.android.com/jetpack/androidx/releases/navigation3)). 1.2 also raises `compileSdk` to 37 and therefore requires **AGP >= 9.2.0**. Adopt it only when a deep-link requirement cannot wait for 1.2 stable.
- `material3` - template pins `1.4.0` stable. Material 3 **Expressive** APIs ship only on the `1.5.0-alphaNN` line and were removed from the 1.4 line; they are not in the Compose BOM either. Do not mix a 1.5.0-alpha API into a 1.4.0 pin.
- `media3` - template pins `1.10.1` stable; `1.11.0` is at `rc01`.
- `robolectric` - template pins `4.16.1` stable; `4.17` is beta.
- `leakcanary` - template pins `2.14` stable; `3.0` is alpha.

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
        force("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.11.0")
    }
}
```

## Kotlin & Compose Compiler Compatibility

**Critical**: Kotlin and Compose compiler versions must be compatible. Mismatches cause compile errors.

Current template versions:
- Kotlin: `2.3.21`
- KSP: `2.3.10`
- AGP: `9.3.1`
- Compose BOM: `2026.06.01` (Compose `1.11.4`, `material3` `1.4.0`)
- Compose Compiler: Managed by `kotlin-compose` plugin

The `kotlin-compose` plugin (formerly `compose-compiler`) is now part of Kotlin and automatically matches the Kotlin version.

### Kotlin requires a matching AGP / R8

Kotlin bytecode version gates the AGP (and bundled R8) you can build with. Do not bump catalog `kotlin` past what the pinned AGP supports.

| Kotlin | Required AGP  | Required R8 |
|--------|---------------|-------------|
| 2.4    | 8.5.2+        | 9.1.29      |
| 2.3    | 8.2.2 - 8.13  | 8.13.19     |
| 2.2    | 7.3.1 - 8.10  | 8.10.21     |

Additional constraint: **AGP / R8 9.x builds before `9.0.28` do not support Kotlin 2.3** ([AGP Kotlin support](https://developer.android.com/build/kotlin-support)).

Why the template stays on Kotlin `2.3.21` even though `2.4.x` is stable: Kotlin 2.4 needs R8 `9.1.29`, which is not what the pinned AGP ships. Moving to 2.4 is a paired AGP+R8 decision, not a one-line catalog bump - verify `./gradlew help` **and** a release (`assembleRelease`) build before adopting it.

**When updating Kotlin:**
1. Check Compose compatibility: https://developer.android.com/jetpack/androidx/releases/compose-kotlin
2. Check the Kotlin / AGP / R8 table above and bump `agp` in the same change when required
3. Update both `kotlin` and `compose-bom` versions together
4. Pick the matching KSP line on Maven Central or [KSP releases](https://github.com/google/ksp/releases); catalog `ksp` may use a `kotlinVersion-kspToolVersion` string or a standalone KSP release (patch digits need not match Kotlin)
5. Run `./gradlew help` before committing

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

### Not covered by the Compose BOM

These need their own catalog version ref even though they look like Compose artifacts. Removing their `version.ref` silently drops resolution.

| Artifact                                                    | Catalog ref        |
|-------------------------------------------------------------|--------------------|
| `androidx.compose.material3:material3`                      | `material3`        |
| `androidx.compose.material3:material3-adaptive-navigation-suite` | `material3`    |
| `androidx.compose.material3.adaptive:adaptive*`              | `materialAdaptive` |
| `androidx.graphics:graphics-shapes`                          | own ref if adopted |

`material3` and `material3-adaptive` are versioned independently of the BOM's Compose line: BOM `2026.06.01` carries Compose `1.11.4` but `material3` `1.4.0`. The BOM never ships `material3` `1.5.0-alphaNN` or `material3-adaptive` `1.3.x`.

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
- Under AGP 9 built-in Kotlin, `org.jetbrains.kotlin.kapt` / `kotlin("kapt")` is **incompatible** and must be removed. The only fallback for a processor with no KSP implementation is the `com.android.legacy-kapt` plugin, versioned with AGP - see [gradle-setup.md](gradle-setup.md#agp-9-key-changes).
- Minimum floors for AGP 9: **KSP >= 2.3.6**, **Hilt >= 2.59.2**.

To decide whether a processor supports KSP, inspect its jar for a
`META-INF/services/com.google.devtools.ksp.processing.SymbolProcessorProvider` entry; if absent, it is kapt-only.

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

// New - apply via alias(libs.plugins.ksp) so the version stays in the catalog
plugins {
    alias(libs.plugins.ksp)
}

dependencies {
    ksp(libs.hilt.compiler)
    ksp(libs.room3.compiler)
    // Room 3 also requires a SQLite driver at runtime, e.g. sqlite-bundled (see app.android.room convention)
}
```

## ProGuard/R8 Considerations

Use `assets/proguard-rules.pro.template` as the source of truth for all keep rules. It includes rules for every library in the version catalog (Retrofit, kotlinx-serialization, Room 3, OkHttp, Hilt, SQLCipher, etc.).

Copy the template to `app/proguard-rules.pro` and adjust `com.example.*` package names. See [gradle-setup.md](gradle-setup.md#r8-and-proguard-configuration) for build configuration.

## Adding a New Dependency

Checklist (in order, fail-fast):

- [ ] Confirm it is not already in `assets/libs.versions.toml.template`.
- [ ] Confirm the coordinate **actually resolves** at the intended version on `google()` / `mavenCentral()` before writing it into the catalog. A plausible-looking artifact id is not proof it is published.
- [ ] Stable channel exists (Hilt/Coroutines/Retrofit/Coil must be stable). A prerelease pin requires an entry in [Pinned prerelease required for feature parity](#pinned-prerelease-required-for-feature-parity) justifying it.
- [ ] If it is an AndroidX `-ktx` artifact, check it is not an empty shim ([Merged KTX artifacts](#merged-ktx-artifacts-do-not-add-the--ktx-coordinate)).
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
