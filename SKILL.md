---
name: claude-android-ninja
description: Build Android apps with Kotlin, Jetpack Compose, MVVM, Hilt, Room 3 (KSP, SQLiteDriver, Flow/suspend DAOs), and multi-module architecture. Triggers on requests to create Android projects, modules, screens, ViewModels, repositories, or Android architecture questions. Not for iOS, Flutter, React Native, KMP-only shared code without an Android app module, or backend-only APIs with no Android client.
compatibility: JDK 17+. Android Studio with Android SDK installed. Network access for Gradle dependency downloads. Version pins in assets/templates follow the repo catalog; align AGP/Kotlin/KSP with the user project before applying upgrades.
license: Apache-2.0
metadata:
  author: DrJacky
  version: 1.0.0
  documentation: https://github.com/Drjacky/claude-android-ninja
  tags: [android, kotlin, compose, mvvm, hilt, room, room3, datastore, paging, gradle, mobile]
---
# Android Kotlin Compose Development

Route tasks through the Quick Reference table and Workflow Decision Tree; open linked `references/` files only for the active task.

## Quick Reference

| Task                                                                                                                                                                  | Reference File                                                                                |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| Project structure & modules                                                                                                                                           | [modularization.md](references/modularization.md)                                             |
| Architecture layers, (Domain, Data, UI, Common, ...)                                                                                                                  | [architecture.md](references/architecture.md)                                                 |
| Compose patterns, Material motion, animation, modifiers, stability                                                                                                    | [compose-patterns.md](references/compose-patterns.md)                                         |
| Paging 3 + Room + network (`RemoteMediator`, remote keys, `initialize`)                                                                                               | [compose-patterns.md](references/compose-patterns.md#offline-first-paging-and-remotemediator) |
| Accessibility, TalkBack, label copy, live regions, Espresso a11y checks                                                                                               | [android-accessibility.md](references/android-accessibility.md)                               |
| Notifications, foreground services, media-style notifications, PiP, sharesheet                                                                                        | [android-notifications.md](references/android-notifications.md)                               |
| Background media playback (audio/video) at API 37, `MediaSessionService`, FGS type, audio focus                                                                       | [android-media.md](references/android-media.md)                                               |
| Data sync & offline-first patterns                                                                                                                                    | [android-data-sync.md](references/android-data-sync.md)                                       |
| Material 3 theming, spacing tokens, category fit, dynamic colors                                                                                                      | [android-theming.md](references/android-theming.md)                                           |
| Navigation3, adaptive navigation, large-screen quality tiers                                                                                                          | [android-navigation.md](references/android-navigation.md)                                     |
| Kotlin patterns, View lifecycle interop                                                                                                                               | [kotlin-patterns.md](references/kotlin-patterns.md)                                           |
| Coroutine patterns                                                                                                                                                    | [coroutines-patterns.md](references/coroutines-patterns.md)                                   |
| Gradle, product flavors, BuildConfig, build performance                                                                                                               | [gradle-setup.md](references/gradle-setup.md)                                                 |
| Testing approach                                                                                                                                                      | [testing.md](references/testing.md)                                                           |
| Internationalization & localization                                                                                                                                   | [android-i18n.md](references/android-i18n.md)                                                 |
| Icons, adaptive launcher specs, custom drawing                                                                                                                        | [android-graphics.md](references/android-graphics.md)                                         |
| Runtime permissions                                                                                                                                                   | [android-permissions.md](references/android-permissions.md)                                   |
| Kotlin delegation patterns                                                                                                                                            | [kotlin-delegation.md](references/kotlin-delegation.md)                                       |
| Crash reporting                                                                                                                                                       | [crashlytics.md](references/crashlytics.md)                                                   |
| StrictMode guardrails                                                                                                                                                 | [android-strictmode.md](references/android-strictmode.md)                                     |
| Multi-module dependencies                                                                                                                                             | [dependencies.md](references/dependencies.md)                                                 |
| Code quality (Detekt)                                                                                                                                                 | [code-quality.md](references/code-quality.md)                                                 |
| Code coverage (JaCoCo)                                                                                                                                                | [android-code-coverage.md](references/android-code-coverage.md)                               |
| Security, Play Integrity (Standard/Classic), server decode, `requestHash`/`nonce`, tiered policy, remediation; Credential Manager; local root checks as supplementary | [android-security.md](references/android-security.md)                                         |
| Design patterns                                                                                                                                                       | [design-patterns.md](references/design-patterns.md)                                           |
| Performance, Play Vitals, Play Developer Reporting API (CI vitals), startup, recomposition, jank, battery, Perfetto / system traces                                   | [android-performance.md](references/android-performance.md)                                   |
| Debugging, Logcat levels, ANR, Gradle error patterns, R8, memory leaks                                                                                                | [android-debugging.md](references/android-debugging.md)                                       |
| Migration guides (XML, RxJava, Navigation, Compose, Room 2→3, Android 17 / API 37)                                                                                    | [migration.md](references/migration.md)                                                       |

## Examples

**Greenfield Android app with convention plugins**

User goal: new repo matching the skill stack.

Actions: copy `assets/settings.gradle.kts.template`, `assets/libs.versions.toml.template`, `assets/convention/` into `build-logic/` per `assets/convention/QUICK_REFERENCE.md`; wire `includeBuild("build-logic")`; read [modularization.md](references/modularization.md) and [gradle-setup.md](references/gradle-setup.md).

Result: root + `app` + core modules with version catalog and convention plugins applied.

**New feature screen (Compose + ViewModel)**

User goal: one new flow in a feature module.

Actions: [modularization.md](references/modularization.md) for module naming and dependency direction; [compose-patterns.md](references/compose-patterns.md) for Screen, state, effects; [kotlin-patterns.md](references/kotlin-patterns.md) + [coroutines-patterns.md](references/coroutines-patterns.md) for `StateFlow` / events; [architecture.md](references/architecture.md) for domain vs data boundaries.

Result: feature module with Screen composable, ViewModel, `UiState`, and DI aligned to existing graphs.

**Offline-first list with Room 3 and remote API**

User goal: cached list + network refresh.

Actions: [compose-patterns.md](references/compose-patterns.md#offline-first-paging-and-remotemediator) for Paging 3 + `RemoteMediator`; [architecture.md](references/architecture.md) for repository placement; Room 3 + `SQLiteDriver` per Workflow Decision Tree database bullets and [migration.md](references/migration.md#room-2x-to-room-3) if upgrading.

Result: single source of truth in Room, UI driven by `PagingData` or equivalent pattern from the guide.

**Target SDK / compile SDK bump (e.g. API 37)**

User goal: migrate toolchain and platform requirements.

Actions: walk [migration.md](references/migration.md#android-17-api-37-migration); pin AGP/Kotlin/KSP using [gradle-setup.md](references/gradle-setup.md) and [dependencies.md](references/dependencies.md); cross-check edge-to-edge, media, security sections linked from the Workflow Decision Tree for API 37.

Result: `compileSdk` / `targetSdk` raised with manifest, Gradle, and feature code adjusted per the migration doc.

## Troubleshooting

| Symptom                                                              | Likely cause                                                                             | Fix                                                                                                                                                                                                                                   |
|----------------------------------------------------------------------|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Gradle sync fails, plugin not found, or version catalog errors       | Missing `google()` / `mavenCentral()`, wrong plugin id, or catalog alias drift           | [gradle-setup.md](references/gradle-setup.md) for repositories, plugins, and catalog wiring; align with `assets/libs.versions.toml.template` when bootstrapping                                                                       |
| KSP errors on Room, or Room 3 builder rejects missing driver         | Room 3 expects `setDriver(BundledSQLiteDriver())` (or project equivalent) per convention | [migration.md](references/migration.md#room-2x-to-room-3); module layout in [modularization.md](references/modularization.md); DAO patterns in [architecture.md](references/architecture.md)                                          |
| Compose runtime warnings about unstable / skippable recompositions   | Unstable parameter types or state held incorrectly                                       | [compose-patterns.md](references/compose-patterns.md) stability sections; [android-performance.md](references/android-performance.md) Compose recomposition; [kotlin-patterns.md](references/kotlin-patterns.md) for immutable models |
| Release build crashes, `ClassNotFoundException`, or missing R8 rules | Shrinking removed reflective or JNI entry points                                         | [gradle-setup.md](references/gradle-setup.md) R8 keep-rules audit; [android-debugging.md](references/android-debugging.md) for stack traces and mapping files                                                                         |
| ANR or jank claims without evidence                                  | Main-thread or measurement assumptions                                                   | [android-performance.md](references/android-performance.md#perfetto-system-traces) before changing architecture; [android-debugging.md](references/android-debugging.md) for ANR traces                                               |

## Workflow Decision Tree

**Creating a new project?**
→ Start with `assets/settings.gradle.kts.template` for settings and module includes  
→ Start with `assets/libs.versions.toml.template` for the version catalog  
→ Copy all files from `assets/convention/` to `build-logic/convention/src/main/kotlin/`  
→ Create `build-logic/settings.gradle.kts` (see `assets/convention/QUICK_REFERENCE.md`)  
→ Add `includeBuild("build-logic")` to root `settings.gradle.kts`  
→ Add plugin entries to `gradle/libs.versions.toml` (see `assets/convention/QUICK_REFERENCE.md`)
→ Copy `assets/proguard-rules.pro.template` to `app/proguard-rules.pro`
→ Read [modularization.md](references/modularization.md) for structure and module types  
→ Use [gradle-setup.md](references/gradle-setup.md) for build files and build logic  

**Configuring Gradle/build files?**
→ Use [gradle-setup.md](references/gradle-setup.md) for module `build.gradle.kts` patterns  
→ Use [gradle-setup.md](references/gradle-setup.md) → "Build Performance" for optimization workflow, diagnostics, and bottleneck troubleshooting  
→ Copy convention plugins from `assets/convention/` to `build-logic/` in your project  
→ See `assets/convention/QUICK_REFERENCE.md` for setup instructions and examples  
→ Copy `assets/proguard-rules.pro.template` to `app/proguard-rules.pro` for R8 rules  

**Setting up code quality / Detekt?**
→ Use [code-quality.md](references/code-quality.md) for Detekt convention plugin setup  
→ Start from `assets/detekt.yml.template` for rules and enable Compose rules  

**Adding or updating dependencies?**
→ Follow [dependencies.md](references/dependencies.md)  
→ Update `assets/libs.versions.toml.template` if the dependency is missing  

**Adding a new feature/module?**
→ Follow module naming in [modularization.md](references/modularization.md)  
→ Implement Presentation in the feature module  
→ Follow dependency flow: Feature → Core/Domain → Core/Data

**Building UI screens/components?**
→ Read [compose-patterns.md](references/compose-patterns.md) for screen architecture, state, components, modifiers  
→ Use [compose-patterns.md](references/compose-patterns.md) -> State Management -> "Loading and refresh UX" for stable layout during loads and refreshes (avoid full-screen spinners that wipe context)  
→ Use [android-theming.md](references/android-theming.md) for Material 3 colors, typography, and shapes  
→ **Always** align Kotlin code with [kotlin-patterns.md](references/kotlin-patterns.md)  
→ Create Screen + ViewModel + UiState in the feature module  
→ Use shared components from `core/ui` when possible

**Handling State and Events?**
→ Use `StateFlow` for state; `Channel` + `receiveAsFlow()` for strict one-shot UI commands; `SharedFlow` for multicast or replay-intended events (see [coroutines-patterns.md](references/coroutines-patterns.md))
→ Survive process death with `SavedStateHandle` (see [compose-patterns.md](references/compose-patterns.md))

**Setting up app theme (colors, typography, shapes)?**
→ Follow [android-theming.md](references/android-theming.md) for Material 3 theming and dynamic colors  
→ Use semantic color roles from `MaterialTheme.colorScheme` (never hardcoded colors); pair every fill with its `on*` partner - see [Color Pairing Rules](references/android-theming.md#color-pairing-rules)  
→ Declare the **full** M3 color set in `Color.kt` (surface containers, dim/bright, `*Fixed`/`*FixedDim`) so dynamic color and contrast variants stay consistent - see [Full Color Role Reference](references/android-theming.md#full-color-role-reference-m3) and [Surface Container Hierarchy](references/android-theming.md#surface-container-hierarchy)  
→ Express depth via container tone first, shadows only for components that float over arbitrary content - see [Tonal Elevation vs Shadows](references/android-theming.md#tonal-elevation-vs-shadows)  
→ Use `outline` for interactive borders/focus, `outlineVariant` for decorative dividers - see [`outline` vs `outlineVariant`](references/android-theming.md#outline-vs-outlinevariant)  
→ Support light/dark themes with user preference toggle  
→ Enable dynamic color (Material You) for API 31+, harmonize brand/extended colors against `primary` - see [Brand Color Harmonization](references/android-theming.md#brand-color-harmonization)  
→ Honor the system contrast slider on Android 14+ (API 34) by shipping Medium/High-contrast scheme variants and reading `UiModeManager.getContrast()` - see [User Contrast Preference](references/android-theming.md#user-contrast-preference-android-14)  
→ For region-local palette overrides (destructive scopes, on-media toolbars), use a nested `MaterialTheme` with `colorScheme.copy(...)` - see [Scoped Themes](references/android-theming.md#scoped-themes)  
→ Pick `Card` / `OutlinedCard` / `ElevatedCard` by surface separation, not importance, and override shapes at the **token** level - see [Card Variants](references/compose-patterns.md#card-variants-filled--outlined--elevated) and [Component Shape Defaults](references/compose-patterns.md#component-shape-defaults)  

**Writing any Kotlin code?**
→ **Always** follow [kotlin-patterns.md](references/kotlin-patterns.md)  
→ Ensure practices align with [architecture.md](references/architecture.md), [modularization.md](references/modularization.md), and [compose-patterns.md](references/compose-patterns.md)

**Setting up data/domain layers?**
→ Read [architecture.md](references/architecture.md)  
→ Hilt `@Binds`, scopes, and DI anti-patterns: [architecture.md](references/architecture.md) -> Domain Layer -> "Dependency Injection Setup"  
→ Create Repository interfaces in `core/domain`  
→ Create implementations in `core/data` using Room 3/Retrofit/DataStore
→ Use DataStore for simple key-value pairs, Room 3 for complex relational data (`suspend` / `Flow` DAOs, `SQLiteDriver`)

**Implementing Lists and Scrolling?**
→ Use `LazyColumn`/`LazyRow` with stable keys and `contentType` (see [compose-patterns.md](references/compose-patterns.md))
→ For large datasets, use Paging 3 (see [compose-patterns.md](references/compose-patterns.md) -> "Paging 3")
→ For Room-backed grids with a remote API, use `RemoteMediator` ([compose-patterns.md](references/compose-patterns.md#offline-first-paging-and-remotemediator))

**Handling Navigation?**
→ Use Navigation3 for adaptive navigation (see [android-navigation.md](references/android-navigation.md))
→ Avoid navigation anti-patterns (see [android-navigation.md](references/android-navigation.md) -> "Navigation Anti-Patterns")

**Optimizing Performance?**
→ Follow the Performance Checklist in [android-performance.md](references/android-performance.md)
→ If the user asks for **automated Play Console vitals** (CI/Slack, no Play Console UI), use [android-performance.md](references/android-performance.md) → **Optional: Play Vitals observability (Play Developer Reporting API)**
→ Use `BasicTextField2` for high-frequency text input

**Auditing battery drain or stuck wake locks?**
→ Use [android-performance.md](references/android-performance.md) → "Excessive partial wake locks (Play Vitals core metric)" for the threshold (>2 hr cumulative non-exempt per session, >5% of sessions over 28 days, enforced March 2026), the use-case-to-substitute matrix, sensor batching, and stuck-worker diagnosis
→ Required: UIDT API for user-initiated transfers; WorkManager + `WorkInfo.stopReason` for syncs; manual wake lock acquired only **after** packet arrival on sockets
→ Forbidden: a manual wake lock alongside `FusedLocationProviderClient` callbacks, `MediaSessionService` audio, or any system API that already wakes the CPU

**Testing?**
→ Read [testing.md](references/testing.md) for testing philosophy and patterns
→ Use Turbine for testing Flow emissions (see [testing.md](references/testing.md) -> "Testing Flow Emissions with Turbine")
→ Create Repository interfaces in `core/domain`
→ Implement Repository in `core/data`
→ Create DataSource + DAO in `core/data`

**Implementing offline-first or data synchronization?**
→ Follow [android-data-sync.md](references/android-data-sync.md) for sync strategies, conflict resolution, and cache invalidation  
→ Use Room 3 as single source of truth with sync metadata (syncStatus, lastModified)  
→ Schedule background sync with WorkManager  
→ Monitor network state before syncing  

**Setting up navigation?**
→ Follow [android-navigation.md](references/android-navigation.md) for Navigation3 architecture, state management, and adaptive navigation  
→ See [modularization.md](references/modularization.md) for feature module navigation components (Destination, Navigator, Graph)  
→ Configure navigation graph in the app module  
→ Use feature navigation destinations and navigator interfaces  

**Setting up deep links, App Links, Digital Asset Links, verification, Dynamic App Links, or custom schemes?**
→ Read [android-navigation.md](references/android-navigation.md) → "Deep Links" for `NavKey` parsing, synthetic back stack, manifest filters, `assetlinks.json`, verification, `DomainVerificationManager`, Dynamic App Links (API 35), custom schemes, troubleshooting  
→ Use [testing.md](references/testing.md) → "Testing Deep Links" for `am start`, `pm set-app-links` / `pm verify-app-links --re-verify` / `pm get-app-links` / `dumpsys package d`, Digital Asset Links REST (append `return_relation_extensions=true` for dynamic rules), custom-scheme launch semantics, and instrumented `onNewIntent` tests  
→ Required: Play Console → Release → Setup → App signing → uppercase SHA-256 in `assetlinks.json`; deep-link Activity `android:exported="true"`, `android:launchMode="singleTask"`, `onNewIntent` + `setIntent`; `android:autoVerify="true"` only on HTTPS intent-filters  
→ Forbidden: security-critical flows on custom URI schemes - use HTTPS App Links  

**Adding tests?**
→ Use [testing.md](references/testing.md) for patterns and examples  
→ Use [testing.md](references/testing.md) → "Screenshot Testing" for Compose Preview Screenshot Testing setup  
→ Keep test doubles in `core/testing`  

**Handling runtime permissions?**
→ Follow [android-permissions.md](references/android-permissions.md) for manifest declarations and Compose permission patterns  
→ Request permissions contextually and handle "Don't ask again" flows  

**Showing notifications or foreground services?**
→ Use [android-notifications.md](references/android-notifications.md) for notification channels, styles, actions, and foreground services  
→ Check POST_NOTIFICATIONS permission on API 33+ before showing notifications  
→ Create notification channels at app startup (required for API 26+)  

**Playing audio or video in the background (target SDK 37)?**
→ Use [android-media.md](references/android-media.md) → "Background media playback hardening (API 37)" for `MediaSessionService`, `mediaPlayback` foreground service type, and `MediaSession` lifecycle  
→ Required: declare `FOREGROUND_SERVICE_MEDIA_PLAYBACK` and `android:foregroundServiceType="mediaPlayback"`; build a `MediaSession` around a Media3 `Player`; release session and player in `onDestroy()`; stop the service on `Player.STATE_ENDED`  
→ Forbidden: standalone `MediaPlayer` / `AudioTrack` / raw `ExoPlayer` background playback without a `MediaSession`; `requestAudioFocus()` from a service with no session; manual wake locks alongside `MediaSessionService`  

**Sharing logic across ViewModels or avoiding base classes?**
→ Use delegation via interfaces as described in [kotlin-delegation.md](references/kotlin-delegation.md)  
→ Prefer small, injected delegates for validation, analytics, or feature flags  

**Adding crash reporting / monitoring?**
→ Follow [crashlytics.md](references/crashlytics.md) for provider-agnostic interfaces and module placement  
→ Use DI bindings to swap between Firebase Crashlytics or Sentry  

**Enabling StrictMode guardrails?**
→ Follow [android-strictmode.md](references/android-strictmode.md) for app-level setup and Compose compiler diagnostics  
→ Use Sentry/Firebase init from [crashlytics.md](references/crashlytics.md) to ship StrictMode logs  

**Choosing design patterns for a new feature, business logic, or system?**
→ Use [design-patterns.md](references/design-patterns.md) for Android-focused pattern guidance  
→ Align with [architecture.md](references/architecture.md) and [modularization.md](references/modularization.md)  

**Measuring performance regressions or startup/jank?**
→ Use [android-performance.md](references/android-performance.md) for Macrobenchmark, Baseline Profiles, and ProfileInstaller setup  
→ Keep benchmark module aligned with `benchmark` build type in [gradle-setup.md](references/gradle-setup.md)  
→ If the user explicitly requests to investigate jank or add custom trace points, use [android-performance.md](references/android-performance.md) for System Tracing (`androidx.tracing`) setup  
→ For trace-backed debugging rules (what to require from the user, what not to infer without artifacts), use [android-performance.md](references/android-performance.md#perfetto-system-traces)

**Setting up app initialization or splash screen?**
→ Follow [android-performance.md](references/android-performance.md) → "App Startup & Initialization" for App Startup library, lazy init, and splash screen  
→ Avoid ContentProvider-based auto-initialization - use `Initializer` interface instead  
→ Use `installSplashScreen()` with `setKeepOnScreenCondition` for loading state  
→ Migrate `windowBackground`-only splash, dedicated `SplashActivity`, or Android 12+ double-splash issues via [migration.md](references/migration.md) → **Legacy splash to Splash Screen API**

**Adding icons, images, or custom graphics?**
→ Use [android-graphics.md](references/android-graphics.md) for Material Symbols icons and custom drawing  
→ Download icons via Iconify API or Google Fonts (avoid deprecated `Icons.Default.*` library)  
→ Use `Modifier.drawWithContent`, `drawBehind`, or `drawWithCache` for custom graphics  

**Creating custom UI effects (glow, shadows, gradients)?**
→ Check [android-graphics.md](references/android-graphics.md) for Canvas drawing, BlendMode, and Palette API patterns  
→ Use `rememberInfiniteTransition` for animated effects  

**Ensuring accessibility compliance (TalkBack, touch targets, color contrast)?**
→ Follow [android-accessibility.md](references/android-accessibility.md) for semantic properties and WCAG guidelines  
→ Provide `contentDescription` for all icons and images  
→ Ensure 48dp × 48dp minimum touch targets  
→ Test with TalkBack and Accessibility Scanner  

**Working with images and color extraction?**
→ Use [android-graphics.md](references/android-graphics.md) → "Image Loading with Coil3" for AsyncImage, SubcomposeAsyncImage, rememberAsyncImagePainter, and Hilt ImageLoader setup  
→ Use [android-graphics.md](references/android-graphics.md) for Palette API and color extraction  

**Implementing complex coroutine flows or background work?**
→ Follow [coroutines-patterns.md](references/coroutines-patterns.md) for structured concurrency patterns  
→ Use appropriate dispatchers (IO, Default, Main) and proper cancellation handling  
→ Prefer `StateFlow` (and `SharedFlow` where appropriate) over `Channel` for observable **state**; use `Channel` for one-shot commands as in [coroutines-patterns.md](references/coroutines-patterns.md)  
→ Use `callbackFlow` to wrap Android callback APIs (connectivity, sensors, location) into Flow  
→ Use `suspendCancellableCoroutine` for one-shot callbacks (Play Services tasks, biometrics)  
→ Use `combine()` to merge multiple Flows in ViewModels, `shareIn` to share expensive upstream  
→ Handle backpressure with `buffer`, `conflate`, `debounce`, or `sample`  

**Need to share behavior across multiple classes?**
→ Use [kotlin-delegation.md](references/kotlin-delegation.md) for interface delegation patterns  
→ Avoid base classes; prefer composition with delegated interfaces  
→ Examples: Analytics, FormValidator, CrashReporter  

**Refactoring existing code or improving architecture?**
→ Review [architecture.md](references/architecture.md) for layer responsibilities  
→ Read [architecture.md](references/architecture.md) -> "Cross-cutting anti-patterns (quick reference)" for common layering mistakes  
→ Check [design-patterns.md](references/design-patterns.md) for applicable patterns  
→ Follow [kotlin-patterns.md](references/kotlin-patterns.md) for Kotlin-specific improvements  
→ Ensure compliance with [modularization.md](references/modularization.md) dependency rules  

**Debugging crashes, ANRs, or obfuscated stack traces?**
→ Follow [android-debugging.md](references/android-debugging.md) for Logcat, ANR traces, and Compose recomposition debugging  
→ Use [android-debugging.md](references/android-debugging.md) for R8 mapping files and manual de-obfuscation  
→ See [gradle-setup.md](references/gradle-setup.md) for R8 build configuration and keep rules

**Auditing R8 keep rules / fixing release size or release-only crashes?**
→ Use [gradle-setup.md](references/gradle-setup.md) → "R8 Keep-Rules Audit" for the redundant-library list, impact hierarchy, subsuming-rule detection, reflection-narrowing playbook, and AGP 9 default-optimization re-audit

**Going edge-to-edge / fixing IME, insets, or system-bar bugs?**
→ Use [compose-patterns.md](references/compose-patterns.md) → "Edge-to-Edge (Mandatory on API 36)" for IME insets (`fitInside(WindowInsetsRulers.Ime.current)` vs `imePadding()` ordering and double-padding pitfalls), system-bar appearance/contrast (`isAppearanceLight*Bars`, `isNavigationBarContrastEnforced`), `NavigationSuiteScaffold` / pane-scaffold inset handling, full-screen `Dialog` `decorFitsSystemWindows`, `StatusBarProtection` scrim, and the per-Activity edge-to-edge checklist  
→ At target SDK 37, add IME visibility-after-rotation handling in the same guide's `#### IME (soft keyboard) insets` block  
→ Manifest must set `android:windowSoftInputMode="adjustResize"` for any Activity hosting text input

**Debugging performance issues or memory leaks?**
→ Enable [android-strictmode.md](references/android-strictmode.md) for development builds  
→ Use [android-performance.md](references/android-performance.md) for profiling and benchmarking  
→ For ANR, jank, or main-thread claims without measurements, follow [android-performance.md](references/android-performance.md#perfetto-system-traces) before concluding cause  
→ Use [android-debugging.md](references/android-debugging.md) for LeakCanary and heap dump analysis  
→ Check [coroutines-patterns.md](references/coroutines-patterns.md) for coroutine cancellation patterns  

**Setting up CI/CD or code quality checks?**
→ Use [code-quality.md](references/code-quality.md) for Detekt baseline and CI integration  
→ Use [gradle-setup.md](references/gradle-setup.md) for build cache and convention plugins  
→ Use [testing.md](references/testing.md) for test organization and coverage  

**Handling sensitive data or privacy concerns?**
→ Follow [crashlytics.md](references/crashlytics.md) for data scrubbing patterns  
→ Use [android-permissions.md](references/android-permissions.md) for proper permission justification  
→ Check [android-strictmode.md](references/android-strictmode.md) for detecting cleartext network traffic  

**Migrating legacy code (LiveData, Fragments, Accompanist, RxJava, Room 2.x)?**
→ Use [migration.md](references/migration.md) for all migration paths (including [Room 2.x → Room 3](references/migration.md#room-2x-to-room-3))  
→ Follow [architecture.md](references/architecture.md) for MVVM patterns  

**Migrating to target SDK 37 (Android 17)?**
→ Walk [migration.md → Android 17 (API 37) Migration](references/migration.md#android-17-api-37-migration) top to bottom, then open each cross-link inside that section for full rules  
→ Required: catalog `compileSdk` / `targetSdk` 37; pin `agp`, Gradle wrapper, `kotlin`, and `ksp` only after `./gradlew help` succeeds per [gradle-setup.md](references/gradle-setup.md) and [dependencies.md](references/dependencies.md); cleartext, loopback, CT, and explicit URI grants per [android-security.md](references/android-security.md); adaptive large-screen layouts, `adjustResize` on the launcher Activity, and IME-after-rotation per [compose-patterns.md](references/compose-patterns.md); background audio/video via [android-media.md](references/android-media.md); Robolectric rules per [testing.md → Robolectric and SDK 37 (Android 17)](references/testing.md#robolectric-and-sdk-37-android-17) **only** when JVM tests use `RobolectricTestRunner`  
→ Forbidden: production-wide cleartext without domain-scoped Network Security Config; cross-process loopback without the API 37 permission where the platform requires it; background `MediaPlayer` / `AudioTrack` / raw `ExoPlayer` without Media3 `MediaSessionService` + `mediaPlayback` FGS + `MediaSession`; Robolectric releases older than 4.13 on current JDKs; `ACTION_SEND` (and similar) intents that attach `content` URIs without explicit `FLAG_GRANT_READ_URI_PERMISSION` or `FLAG_GRANT_WRITE_URI_PERMISSION`  
→ `com.android.tools.build:gradle` HTTP 404: catalog `agp` is not published on `google()` yet; pick a published AGP that supports `compileSdk` 37 per [gradle-setup.md → AGP version pin](references/gradle-setup.md#agp-version-pin-resolve-before-merge)  
→ `MissingValueException` / unresolved providers on `compile*JavaWithJavac`: isolate JaCoCo Tier 2 (`ScopedArtifacts` combined report) per [android-code-coverage.md](references/android-code-coverage.md) before chasing Kotlin or KSP bumps  

**Adding Compose animations?**
→ Use [compose-patterns.md](references/compose-patterns.md) → "Animation" for `AnimatedVisibility`, `AnimatedContent`, `animate*AsState`, `Animatable`, shared elements  
→ Use `graphicsLayer` for GPU-accelerated transforms (no recomposition)  
→ Always provide `label` parameter for Layout Inspector debugging  

**Using side effects (LaunchedEffect, DisposableEffect)?**
→ Use [compose-patterns.md](references/compose-patterns.md) → "Side Effects" for effect selection guide  
→ `LaunchedEffect(key)` for state-driven coroutines, `rememberCoroutineScope` for event-driven  
→ `DisposableEffect` for listener/resource cleanup, always include `onDispose`  
→ `LifecycleResumeEffect` for onResume/onPause work (camera, media), `LifecycleStartEffect` for onStart/onStop (location, sensors)  

**Working with Modifier ordering or custom modifiers?**
→ Use [compose-patterns.md](references/compose-patterns.md) → "Modifiers" for chain ordering rules and patterns  
→ Use `Modifier.Node` for custom modifiers (not deprecated `Modifier.composed`)  
→ Order: size → padding → drawing → interaction  

**Migrating from Accompanist or deprecated Compose APIs?**
→ Use [migration.md](references/migration.md) for Accompanist, Compose API, Material, Edge-to-Edge, and Room upgrades  
→ See [compose-patterns.md](references/compose-patterns.md) → "Deprecated Patterns & Migrations" for a summary list  

**Optimizing Compose recomposition or stability?**
→ Use [compose-patterns.md](references/compose-patterns.md) for `@Immutable`/`@Stable` annotations  
→ Use [android-performance.md](references/android-performance.md) → "Compose Recomposition Performance" for three phases, deferred state reads, Strong Skipping Mode  
→ Check [gradle-setup.md](references/gradle-setup.md) for Compose Compiler metrics and stability reports  
→ Use [kotlin-patterns.md](references/kotlin-patterns.md) for immutable data structures  

**Working with databases (Room 3)?**
→ Define DAOs and entities in `core/database` per [modularization.md](references/modularization.md); use **`androidx.room3`**, KSP, and **`setDriver(BundledSQLiteDriver())`** on the builder (see `app.android.room` convention)  
→ Use [testing.md](references/testing.md) for in-memory database testing and Room 3 migration tests  
→ Follow [architecture.md](references/architecture.md) for repository patterns  
→ Upgrading from Room 2.x: [migration.md → Room 2.x to Room 3](references/migration.md#room-2x-to-room-3)  

**Need internationalization/localization (i18n/l10n)?**
→ Use [android-i18n.md](references/android-i18n.md) for string resources, plurals, and RTL support  
→ Follow [compose-patterns.md](references/compose-patterns.md) for RTL-aware Compose layouts  
→ Use [testing.md](references/testing.md) for locale-specific testing  

**Implementing network calls (Retrofit)?**
→ Use [architecture.md](references/architecture.md) → "Network Layer Setup" for Retrofit service interfaces, Hilt NetworkModule, and AuthInterceptor  
→ Define API interfaces in `core/network` per [modularization.md](references/modularization.md)  
→ Follow [dependencies.md](references/dependencies.md) for Retrofit, OkHttp, and serialization setup  
→ Handle errors with generic `Result<T>` from [kotlin-patterns.md](references/kotlin-patterns.md)  

**Creating custom lint rules or code checks?**
→ Use [code-quality.md](references/code-quality.md) for Detekt custom rules  
→ Follow [gradle-setup.md](references/gradle-setup.md) for convention plugin setup  
→ Check [android-strictmode.md](references/android-strictmode.md) for runtime checks

**Need code coverage reporting?**
→ Use [android-code-coverage.md](references/android-code-coverage.md) for JaCoCo setup  
→ Follow [testing.md](references/testing.md) for test strategies  
→ Check [gradle-setup.md](references/gradle-setup.md) for convention plugin integration

**Implementing security features (encryption, biometrics, pinning)?**
→ Use [android-security.md](references/android-security.md) for comprehensive security guide  
→ Follow [android-permissions.md](references/android-permissions.md) for runtime permissions  
→ Check [crashlytics.md](references/crashlytics.md) for PII scrubbing and data privacy

**Implementing fraud-resistant or high-value flows (payments, session bootstrap, integrity-gated APIs)?**
→ Read [android-security.md](references/android-security.md): **Device trust and abuse resistance**, **Play Integrity API** (prerequisites, Standard vs Classic, server checklist, errors, remediation), **Root and Emulator Detection** (how this fits next to Play Integrity), **Security Checklist**  
→ If Cloud Console / Play Console enablement or the **Google Cloud project number** is missing, list the missing prerequisites (see that guide) and stop before wiring client code
