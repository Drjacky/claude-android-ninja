# Dependencies Guide

Use this guide for dependency selection, versioning strategy, and best practices for Android projects using the version catalog.

## When to Use This Guide
- **New project**: Start by reviewing the version catalog template
- **New feature**: Confirm required libraries are already defined
- **Any new code**: Verify you are using approved dependencies and current versions
- **Dependency conflicts**: Resolve version mismatches
- **Library evaluation**: Decide between competing libraries

## Version Catalog Source of Truth
Always check `templates/libs.versions.toml.template` before adding or changing dependencies.

### Rules
1. **Prefer existing entries** in the template when adding dependencies
2. **If a dependency is missing**, add it to `libs.versions.toml` following the same grouping and naming conventions
3. **Keep versions centralized** in the `[versions]` section; reference them by `version.ref`
4. **Use bundles** when multiple libraries are typically used together (e.g., Compose, Navigation, Testing)
5. **Use platform dependencies** (BOMs) for coordinated version management (Compose, Firebase)

## Dependency Selection Criteria

### Network Libraries

**Retrofit + OkHttp (Recommended for REST APIs)**
- ✅ Use for: Traditional REST APIs, existing projects
- ✅ Mature, stable, extensive ecosystem
- ✅ Interceptor support for logging, auth, retries
- Use `retrofit2-kotlinx-serialization-converter` for Kotlin serialization

**Ktor Client (Alternative)**
- ✅ Use for: Pure Kotlin multiplatform projects
- ❌ Avoid for: Android-only apps (Retrofit is more established)

### Image Loading

**Coil 3.x (Recommended)**
- ✅ Use for: All Compose projects
- ✅ Kotlin-first, Compose-native, smallest APK impact
- ✅ Built-in support for OkHttp, async image loading
- Use `coil-compose` + `coil-network-okhttp`

**Glide (Legacy)**
- ❌ Avoid for: New Compose projects
- Use only if: Migrating from View-based UI with heavy Glide usage

### Serialization

**kotlinx-serialization (Recommended)**
- ✅ Use for: All new projects
- ✅ Kotlin-first, compile-time safety, faster than Gson
- ✅ Works with Retrofit via `retrofit2-kotlinx-serialization-converter`

**Gson (Legacy)**
- ❌ Avoid for: New projects
- Use only if: Heavy investment in existing Gson code

### Dependency Injection

**Hilt (Required)**
- ✅ Built on Dagger, Android-optimized
- ✅ Compile-time safety, ViewModel integration
- ✅ This SKILL requires Hilt for all projects

### AndroidX Libraries

**Prefer `-ktx` extensions:**
- `core-ktx`, `lifecycle-runtime-ktx`, `room-ktx`
- Provide Kotlin-friendly APIs and coroutine support

**Never use legacy support libraries:**
- ❌ `com.android.support.*` (deprecated)
- ✅ Always use `androidx.*`

## Version Strategy

### Stability Requirements

**Production apps:**
- ✅ Use **stable** versions only (e.g., `2.6.1`, `1.0.0`)
- ✅ Exception: AndroidX alpha/beta when required for critical features (Navigation3)
- ❌ Avoid alpha/beta/RC for core dependencies (Hilt, Room, Coroutines)

**Experimental projects:**
- ✅ Can use alpha/beta for evaluation
- Document experimental versions clearly

### When to Update

**Security patches:**
- 🔴 Update immediately for CVEs
- Check dependency-check tools or GitHub security alerts

**Feature updates:**
- 🟡 Update when needed for specific features
- Test thoroughly in feature branches

**Breaking changes:**
- 🟢 Update during planned refactoring windows
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
- Kotlin: `2.2.21`
- Compose BOM: `2025.10.01`
- Compose Compiler: Managed by `kotlin-compose` plugin

The `kotlin-compose` plugin (formerly `compose-compiler`) is now part of Kotlin and automatically matches the Kotlin version.

**When updating Kotlin:**
1. Check Compose compatibility: https://developer.android.com/jetpack/androidx/releases/compose-kotlin
2. Update both `kotlin` and `compose-bom` versions together
3. Test compilation before committing

## Platform Dependencies (BOMs)

BOMs (Bill of Materials) manage versions of related libraries, ensuring compatibility.

**When to use BOMs:**

```kotlin
// Compose BOM - manages all androidx.compose.* versions
implementation(platform(libs.androidx.compose.bom))

// Firebase BOM - manages all firebase.* versions  
implementation(platform(libs.firebase.bom))
```

**Don't specify versions for BOM-managed dependencies:**

```kotlin
// ✅ Correct: version from BOM
implementation(libs.androidx.compose.ui)

// ❌ Wrong: explicit version overrides BOM
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
These are defined in `templates/libs.versions.toml.template`.

## Build Performance Considerations

### `api` vs `implementation`

**`implementation`** (Preferred)
- ✅ Hides dependency from consumers
- ✅ Faster builds (changes don't trigger recompilation of consumers)

**`api`** (Use sparingly)
- ✅ Use when: Dependency types are part of your public API
- Example: Domain module exposes `Flow` from coroutines

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

**Prefer KSP (Kotlin Symbol Processing):**
- ✅ 2x faster than kapt
- ✅ Room 2.6+ supports KSP
- ✅ Hilt supports KSP

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
    kapt(libs.room.compiler)
}

// New
plugins {
    id("com.google.devtools.ksp") version "2.2.21-1.0.32"
}

dependencies {
    ksp(libs.hilt.compiler)
    ksp(libs.room.compiler)
}
```

## ProGuard/R8 Considerations

Some libraries require ProGuard/R8 keep rules:
- **Room**, **Retrofit**, **kotlinx-serialization**: Require keep rules (usually auto-added)
- Check library documentation for required rules
- Convention plugins in this SKILL handle common cases automatically

For manual rules, add to `proguard-rules.pro` in the module.

## Adding a New Dependency

### Step-by-Step

1. **Check if it exists** in `templates/libs.versions.toml.template`
2. **Evaluate the library:**
   - Is it stable? (Avoid alpha/beta for production)
   - Is it maintained? (Check last update, GitHub activity)
   - License compatible? (Apache 2.0, MIT preferred)
   - Size impact? (Check APK size increase)
3. **Add to `libs.versions.toml`:**

```toml
[versions]
ktor = "3.0.3"

[libraries]
ktor-client-core = { group = "io.ktor", name = "ktor-client-core", version.ref = "ktor" }
ktor-client-android = { group = "io.ktor", name = "ktor-client-android", version.ref = "ktor" }
```

4. **Use in `build.gradle.kts`:**

```kotlin
dependencies {
    implementation(libs.ktor.client.core)
    implementation(libs.ktor.client.android)
}
```

5. **Test thoroughly** before committing

For setup patterns and convention plugins, see `references/gradle-setup.md`.
