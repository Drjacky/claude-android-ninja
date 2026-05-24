# Workflow decision tree

Required: use when Quick Reference has no matching row, or the task needs greenfield bootstrap steps.

Pick one `**...?**` block below; follow its `→` lines only before opening unrelated references.

For files with a `-quick.md` companion, open the **quick** file first; open the full reference only for the linked section (samples, checklists, deep anchors).

**Existing project - first 5 minutes**

→ Read `settings.gradle.kts`, `gradle/libs.versions.toml`, and the `app` module `build.gradle.kts` (use the real app module name) - [dependencies.md → Existing project (brownfield)](dependencies.md#existing-project-brownfield), [modularization.md → Existing project alignment](modularization.md#existing-project-alignment)  
→ Note stack signals: Navigation 2 vs 3, Room 2 vs 3, single- vs multi-module, XML- vs Compose-heavy UI  
→ If the project stack differs from skill templates, open [migration.md](migration.md) before copying `assets/` or bumping catalog pins  
→ Forbidden: replace the user's `libs.versions.toml` with `assets/libs.versions.toml.template` without an explicit user request  
→ Then pick a `**...?**` block below for the task

**Multi-hop recipes (common paths)**

1. **New feature screen:** [modularization.md](modularization.md) → [compose-patterns-quick.md](compose-patterns-quick.md) → [architecture.md](architecture.md)  
2. **Offline-first list + API:** [android-data-sync-quick.md](android-data-sync-quick.md) → [compose-patterns.md → Offline-first paging](compose-patterns.md#offline-first-paging-and-remotemediator) → [architecture.md](architecture.md)  
3. **Brownfield toolchain bump:** [dependencies.md → Version strategy](dependencies.md#version-strategy) → [migration.md](migration.md) → `./gradlew help` then `:app:assembleDebug` per [gradle-setup.md → Verify after toolchain or module changes](gradle-setup.md#verify-after-toolchain-or-module-changes)

**Creating a new project?**
→ Start with `../assets/settings.gradle.kts.template` for settings and module includes  
→ Start with `../assets/libs.versions.toml.template` for the version catalog  
→ Copy all files from `../assets/convention/` to `build-logic/convention/src/main/kotlin/`  
→ Create `build-logic/settings.gradle.kts` (see `../assets/convention/QUICK_REFERENCE.md`)  
→ Add `includeBuild("build-logic")` to root `settings.gradle.kts`  
→ Add plugin entries to `gradle/libs.versions.toml` (see `../assets/convention/QUICK_REFERENCE.md`)
→ Copy `../assets/proguard-rules.pro.template` to `app/proguard-rules.pro`
→ Read [modularization.md](modularization.md) for structure and module types  
→ Use [gradle-setup.md](gradle-setup.md) for build files and build logic  

**Configuring Gradle/build files?**
→ Use [gradle-setup.md](gradle-setup.md) for module `build.gradle.kts` patterns  
→ Use [gradle-setup.md](gradle-setup.md) → "Build Performance" for optimization workflow, diagnostics, and bottleneck troubleshooting  
→ Copy convention plugins from `../assets/convention/` to `build-logic/` in your project  
→ See `../assets/convention/QUICK_REFERENCE.md` for setup instructions and examples  
→ Copy `../assets/proguard-rules.pro.template` to `app/proguard-rules.pro` for R8 rules  

**Setting up code quality / Detekt?**
→ Use [code-quality.md](code-quality.md) for Detekt convention plugin setup  
→ Start from `../assets/detekt.yml.template` for rules and enable Compose rules  

**Adding or updating dependencies?**
→ Follow [dependencies.md](dependencies.md)  
→ Update `../assets/libs.versions.toml.template` if the dependency is missing  

**Adding a new feature/module?**
→ Follow module naming in [modularization.md](modularization.md)  
→ Implement Presentation in the feature module  
→ Follow dependency flow: Feature → Core/Domain → Core/Data

**Building UI screens/components?**
→ Read [compose-patterns-quick.md](compose-patterns-quick.md); open [compose-patterns.md](compose-patterns.md) only for linked sections (e.g. [Loading and refresh UX](compose-patterns.md#loading-and-refresh-ux))  
→ Use [android-theming-quick.md](android-theming-quick.md) for Material 3 colors, typography, and shapes  
→ **Always** align Kotlin code with [kotlin-patterns.md](kotlin-patterns.md)  
→ Create Screen + ViewModel + UiState in the feature module  
→ Use shared components from `core/ui` when possible

**Handling State and Events?**
→ Use `StateFlow` for state; `Channel` + `receiveAsFlow()` for strict one-shot UI commands; `SharedFlow` for multicast or replay-intended events (see [coroutines-patterns-quick.md](coroutines-patterns-quick.md))
→ Survive process death with `SavedStateHandle` (see [compose-patterns.md → State Management](compose-patterns.md#state-management))

**Setting up app theme (colors, typography, shapes)?**
→ Follow [android-theming-quick.md](android-theming-quick.md); open [android-theming.md](android-theming.md) only for linked sections below  
→ Use semantic color roles from `MaterialTheme.colorScheme` (never hardcoded colors); pair every fill with its `on*` partner - see [Color Pairing Rules](android-theming.md#color-pairing-rules)  
→ Declare the **full** M3 color set in `Color.kt` (surface containers, dim/bright, `*Fixed`/`*FixedDim`) so dynamic color and contrast variants stay consistent - see [Full Color Role Reference](android-theming.md#full-color-role-reference-m3) and [Surface Container Hierarchy](android-theming.md#surface-container-hierarchy)  
→ Express depth via container tone first, shadows only for components that float over arbitrary content - see [Tonal Elevation vs Shadows](android-theming.md#tonal-elevation-vs-shadows)  
→ Use `outline` for interactive borders/focus, `outlineVariant` for decorative dividers - see [`outline` vs `outlineVariant`](android-theming.md#outline-vs-outlinevariant)  
→ Support light/dark themes with user preference toggle  
→ Enable dynamic color (Material You) for API 31+, harmonize brand/extended colors against `primary` - see [Brand Color Harmonization](android-theming.md#brand-color-harmonization)  
→ Honor the system contrast slider on Android 14+ (API 34) by shipping Medium/High-contrast scheme variants and reading `UiModeManager.getContrast()` - see [User Contrast Preference](android-theming.md#user-contrast-preference-android-14)  
→ For region-local palette overrides (destructive scopes, on-media toolbars), use a nested `MaterialTheme` with `colorScheme.copy(...)` - see [Scoped Themes](android-theming.md#scoped-themes)  
→ Pick `Card` / `OutlinedCard` / `ElevatedCard` by surface separation, not importance, and override shapes at the **token** level - see [Card Variants](compose-patterns.md#card-variants-filled-outlined-elevated) and [Component Shape Defaults](compose-patterns.md#component-shape-defaults)  

**Writing any Kotlin code?**
→ **Always** follow [kotlin-patterns.md](kotlin-patterns.md)  
→ Ensure practices align with [architecture.md](architecture.md), [modularization.md](modularization.md), and [compose-patterns-quick.md](compose-patterns-quick.md)

**Setting up data/domain layers?**
→ Read [architecture.md](architecture.md)  
→ Hilt `@Binds`, scopes, and DI anti-patterns: [architecture.md](architecture.md) -> Domain Layer -> "Dependency Injection Setup"  
→ Create Repository interfaces in `core/domain`  
→ Create implementations in `core/data` using Room 3/Retrofit/DataStore
→ Use DataStore for simple key-value pairs, Room 3 for complex relational data (`suspend` / `Flow` DAOs, `SQLiteDriver`)

**Implementing Lists and Scrolling?**
→ Use `LazyColumn`/`LazyRow` with stable keys and `contentType` (see [compose-patterns-quick.md](compose-patterns-quick.md) → Lists & Scrolling)
→ For large datasets, use Paging 3 (see [compose-patterns.md → Lists & Scrolling](compose-patterns.md#lists-scrolling))
→ For Room-backed grids with a remote API, use `RemoteMediator` ([compose-patterns.md](compose-patterns.md#offline-first-paging-and-remotemediator))

**Handling Navigation?**
→ Use Navigation3 for adaptive navigation (see [android-navigation-quick.md](android-navigation-quick.md))
→ Open [android-navigation.md](android-navigation.md) only for sections linked from the quick file (e.g. state management, anti-patterns)
→ See [modularization.md](modularization.md) for feature module navigation components (Destination, Navigator, Graph)
→ Configure navigation graph in the app module; use feature navigation destinations and navigator interfaces
→ Avoid navigation anti-patterns (see [android-navigation.md](android-navigation.md) -> "Navigation Anti-Patterns")

**Optimizing Performance?**
→ Follow the Performance Checklist in [android-performance.md](android-performance.md)
→ If the user asks for **automated Play Console vitals** (CI/Slack, no Play Console UI), use [android-performance.md](android-performance.md) → **Optional: Play Vitals observability (Play Developer Reporting API)**
→ Use `BasicTextField2` for high-frequency text input

**Auditing battery drain or stuck wake locks?**
→ Use [android-performance.md](android-performance.md) → "Excessive partial wake locks (Play Vitals core metric)" for the threshold (>2 hr cumulative non-exempt per session, >5% of sessions over 28 days, enforced March 2026), the use-case-to-substitute matrix, sensor batching, and stuck-worker diagnosis
→ Required: UIDT API for user-initiated transfers; WorkManager + `WorkInfo.stopReason` for syncs; manual wake lock acquired only **after** packet arrival on sockets
→ Forbidden: a manual wake lock alongside `FusedLocationProviderClient` callbacks, `MediaSessionService` audio, or any system API that already wakes the CPU

**Testing?**
→ Read [testing-quick.md](testing-quick.md) for testing philosophy and routing
→ Use Turbine for testing Flow emissions (see [testing.md → Testing Flow Emissions with Turbine](testing.md#testing-flow-emissions-with-turbine))

**Implementing offline-first or data synchronization?**
→ Follow [android-data-sync-quick.md](android-data-sync-quick.md); open [android-data-sync.md](android-data-sync.md) for Worker/repository samples  
→ Use Room 3 as single source of truth with sync metadata (syncStatus, lastModified)  
→ Schedule background sync with WorkManager  
→ Monitor network state before syncing  

**Setting up deep links, App Links, Digital Asset Links, verification, Dynamic App Links, or custom schemes?**
→ Read [android-navigation-quick.md](android-navigation-quick.md) first; then [android-navigation.md → Deep Links](android-navigation.md#deep-links) for `NavKey` parsing, synthetic back stack, manifest filters, `assetlinks.json`, verification, `DomainVerificationManager`, Dynamic App Links (API 35), custom schemes, troubleshooting  
→ Use [testing.md](testing.md) → "Testing Deep Links" for `am start`, `pm set-app-links` / `pm verify-app-links --re-verify` / `pm get-app-links` / `dumpsys package d`, Digital Asset Links REST (append `return_relation_extensions=true` for dynamic rules), custom-scheme launch semantics, and instrumented `onNewIntent` tests  
→ Required: Play Console → Release → Setup → App signing → uppercase SHA-256 in `assetlinks.json`; deep-link Activity `android:exported="true"`, `android:launchMode="singleTask"`, `onNewIntent` + `setIntent`; `android:autoVerify="true"` only on HTTPS intent-filters  
→ Forbidden: security-critical flows on custom URI schemes - use HTTPS App Links  

**Adding tests?**
→ Use [testing-quick.md](testing-quick.md) for patterns and routing; open [testing.md](testing.md) for linked sections below  
→ Use [testing.md](testing.md#pre-release-ui-state-checklist) for empty, loading, error, offline, permission-denied, and session-loss routing before tightening coverage  
→ Use [testing.md](testing.md#preview-screenshot-testing-vs-roborazzi) when choosing Compose Preview Screenshot Testing vs Roborazzi for visual regression  
→ Use [testing.md](testing.md) → "Screenshot Testing" for Compose Preview Screenshot Testing setup  
→ Keep test doubles in `core/testing`  

**Handling runtime permissions?**
→ Follow [android-permissions.md](android-permissions.md) for manifest declarations and Compose permission patterns  
→ Request permissions contextually and handle "Don't ask again" flows  
→ For Photo Picker, document contracts, FileProvider, URI grants, and sharesheet routing, use [android-media.md](android-media.md#picking-media-and-documents) and [android-media.md → Sharing media and files](android-media.md#sharing-media-and-files)  
→ Pick contacts without `READ_CONTACTS`: [android-permissions.md → Contact picker (privacy-first)](android-permissions.md#contact-picker-privacy-first)  
→ Inline picker UI: [android-permissions.md → Embedded Photo Picker](android-permissions.md#embedded-photo-picker)  
→ Target SDK 37 location: [android-permissions.md → Android 17 location privacy](android-permissions.md#android-17-location-privacy)

**Showing notifications or foreground services?**
→ Use [android-notifications.md](android-notifications.md) for notification channels, styles, actions, and foreground services  
→ Check POST_NOTIFICATIONS permission on API 33+ before showing notifications  
→ Create notification channels at app startup (required for API 26+)  

**Playing audio or video in the background (target SDK 37)?**
→ Use [android-media.md](android-media.md) → "Background media playback hardening (API 37)" for `MediaSessionService`, `mediaPlayback` foreground service type, and `MediaSession` lifecycle  
→ Add Media3 via `../assets/libs.versions.toml.template` (`media3` ref, `media3-playback` bundle); align pins with [dependencies.md → Media3](dependencies.md#media3)  
→ Required: declare `FOREGROUND_SERVICE_MEDIA_PLAYBACK` and `android:foregroundServiceType="mediaPlayback"`; build a `MediaSession` around a Media3 `Player`; release session and player in `onDestroy()`; stop the service on `Player.STATE_ENDED`  
→ Forbidden: standalone `MediaPlayer` / `AudioTrack` / raw `ExoPlayer` background playback without a `MediaSession`; `requestAudioFocus()` from a service with no session; manual wake locks alongside `MediaSessionService`  

**Preloading the next Media3 playback item?**
→ Use [android-media.md → Playback preloading (Media3)](android-media.md#playback-preloading-media3)  

**Sharing logic across ViewModels or avoiding base classes?**
→ Use delegation via interfaces as described in [kotlin-delegation.md](kotlin-delegation.md)  
→ Prefer small, injected delegates for validation, analytics, or feature flags  

**Adding crash reporting / monitoring?**
→ Follow [crashlytics.md](crashlytics.md) for provider-agnostic interfaces and module placement  
→ Use DI bindings to swap between Firebase Crashlytics or Sentry  

**Enabling StrictMode guardrails?**
→ Follow [android-strictmode.md](android-strictmode.md) for app-level setup and Compose compiler diagnostics  
→ Use Sentry/Firebase init from [crashlytics.md](crashlytics.md) to ship StrictMode logs  

**Choosing design patterns for a new feature, business logic, or system?**
→ Use [design-patterns-quick.md](design-patterns-quick.md) for Android-focused pattern routing  
→ Align with [architecture.md](architecture.md) and [modularization.md](modularization.md)  

**Measuring performance regressions or startup/jank?**
→ Use [android-performance.md](android-performance.md) for Macrobenchmark, Baseline Profiles, and ProfileInstaller setup  
→ Keep benchmark module aligned with `benchmark` build type in [gradle-setup.md](gradle-setup.md)  
→ Studio system traces: [android-performance.md → Android Performance Analyzer (APA)](android-performance.md#android-performance-analyzer-apa)  
→ If the user explicitly requests to investigate jank or add custom trace points, use [android-performance.md](android-performance.md) for System Tracing (`androidx.tracing`) setup  
→ For trace-backed debugging rules (what to require from the user, what not to infer without artifacts), use [android-performance.md → Perfetto (system traces)](android-performance.md#perfetto-system-traces)

**Setting up app initialization or splash screen?**
→ Follow [android-performance.md](android-performance.md) → "App Startup & Initialization" for App Startup library, lazy init, and splash screen  
→ Avoid ContentProvider-based auto-initialization - use `Initializer` interface instead  
→ Use `installSplashScreen()` with `setKeepOnScreenCondition` for loading state  
→ Migrate `windowBackground`-only splash, dedicated `SplashActivity`, or Android 12+ double-splash issues via [migration.md](migration.md) → **Legacy splash to Splash Screen API**

**Adding icons, images, or custom graphics?**
→ Use [android-graphics.md](android-graphics.md) for Material Symbols icons and custom drawing  
→ Download icons via Iconify API or Google Fonts (avoid deprecated `Icons.Default.*` library)  
→ Use `Modifier.drawWithContent`, `drawBehind`, or `drawWithCache` for custom graphics  

**Creating custom UI effects (glow, shadows, gradients)?**
→ Check [android-graphics.md](android-graphics.md) for Canvas drawing, BlendMode, and Palette API patterns  
→ Use `rememberInfiniteTransition` for animated effects  

**Ensuring accessibility compliance (TalkBack, touch targets, color contrast)?**
→ Follow [android-accessibility-quick.md](android-accessibility-quick.md); open [android-accessibility.md](android-accessibility.md) for WCAG tables and Espresso samples  
→ Provide `contentDescription` for all icons and images  
→ Ensure 48dp * 48dp minimum touch targets  
→ Test with TalkBack and Accessibility Scanner  

**Working with images and color extraction?**
→ Use [android-graphics.md](android-graphics.md) → "Image Loading with Coil3" for AsyncImage, SubcomposeAsyncImage, rememberAsyncImagePainter, and Hilt ImageLoader setup  
→ Use [android-graphics.md](android-graphics.md) for Palette API and color extraction  

**Implementing complex coroutine flows or background work?**
→ Follow [coroutines-patterns-quick.md](coroutines-patterns-quick.md); open [coroutines-patterns.md](coroutines-patterns.md) for `callbackFlow` samples and pitfall code blocks  
→ Use appropriate dispatchers (IO, Default, Main) and proper cancellation handling  
→ Prefer `StateFlow` (and `SharedFlow` where appropriate) over `Channel` for observable **state**; use `Channel` for one-shot commands as in [coroutines-patterns-quick.md](coroutines-patterns-quick.md)  
→ Use `callbackFlow` to wrap Android callback APIs (connectivity, sensors, location) into Flow  
→ Use `suspendCancellableCoroutine` for one-shot callbacks (Play Services tasks, biometrics)  
→ Use `combine()` to merge multiple Flows in ViewModels, `shareIn` to share expensive upstream  
→ Handle backpressure with `buffer`, `conflate`, `debounce`, or `sample`  

**Need to share behavior across multiple classes?**
→ Use [kotlin-delegation.md](kotlin-delegation.md) for interface delegation patterns  
→ Avoid base classes; prefer composition with delegated interfaces  
→ Examples: Analytics, FormValidator, CrashReporter  

**Refactoring existing code or improving architecture?**
→ Review [architecture.md](architecture.md) for layer responsibilities  
→ Read [architecture.md](architecture.md) -> "Cross-cutting anti-patterns (quick reference)" for common layering mistakes  
→ Check [design-patterns-quick.md](design-patterns-quick.md) for applicable patterns  
→ Follow [kotlin-patterns.md](kotlin-patterns.md) for Kotlin-specific improvements  
→ Ensure compliance with [modularization.md](modularization.md) dependency rules  

**Debugging crashes, ANRs, or obfuscated stack traces?**
→ Follow [android-debugging.md](android-debugging.md) for Logcat, ANR traces, and Compose recomposition debugging  
→ Use [android-debugging.md](android-debugging.md) for R8 mapping files and manual de-obfuscation  
→ Release-only shrinker crashes: [android-debugging.md → R8 keep-rules troubleshooting](android-debugging.md#r8-keep-rules-troubleshooting) and [gradle-setup.md → R8 Keep-Rules Audit](gradle-setup.md#r8-keep-rules-audit)  
→ Unexplained background kill on some devices: [android-debugging.md → Process kill under memory caps](android-debugging.md#process-kill-under-memory-caps) and [migration.md → Memory limiter](migration.md#memory-limiter-all-apps-on-affected-devices)  

**Proposing install, cold start, or black-box smoke driven by ADB or UIAutomator?**
→ Use [testing.md](testing.md#agent-automation-adb-and-uiautomator) for device targeting, `am start`, logcat smoke, and instrumented UIAutomator skeletons  
→ Use [testing.md](testing.md#testing-deep-links) for `am start` deep-link matrices and `pm verify-app-links` when the task is link verification, not generic launch  

**Auditing R8 keep rules / fixing release size or release-only crashes?**
→ Start at [android-debugging.md → R8 keep-rules troubleshooting](android-debugging.md#r8-keep-rules-troubleshooting)  
→ Use [gradle-setup.md → R8 Keep-Rules Audit](gradle-setup.md#r8-keep-rules-audit) for redundant-library removal, impact hierarchy, subsuming-rule detection, reflection narrowing, and AGP 9 default-optimization re-audit

**Going edge-to-edge / fixing IME, insets, or system-bar bugs?**
→ Use [compose-patterns-quick.md](compose-patterns-quick.md) first; then [compose-patterns.md → Edge-to-Edge (Mandatory on API 36)](compose-patterns.md#edge-to-edge-mandatory-on-api-36) for IME insets (`fitInside(WindowInsetsRulers.Ime.current)` vs `imePadding()` ordering and double-padding pitfalls), system-bar appearance/contrast (`isAppearanceLight*Bars`, `isNavigationBarContrastEnforced`), `NavigationSuiteScaffold` / pane-scaffold inset handling, full-screen `Dialog` `decorFitsSystemWindows`, `StatusBarProtection` scrim, and the per-Activity edge-to-edge checklist  
→ At target SDK 37, add IME visibility-after-rotation handling in the same guide's `#### IME (soft keyboard) insets` block  
→ Manifest must set `android:windowSoftInputMode="adjustResize"` for any Activity hosting text input

**Debugging performance issues or memory leaks?**
→ Enable [android-strictmode.md](android-strictmode.md) for development builds  
→ Use [android-performance.md](android-performance.md) for profiling and benchmarking  
→ System traces in Studio: [android-performance.md → Android Performance Analyzer (APA)](android-performance.md#android-performance-analyzer-apa)  
→ For ANR, jank, or main-thread claims without measurements, follow [android-performance.md → Perfetto (system traces)](android-performance.md#perfetto-system-traces) before concluding cause  
→ Use [android-debugging.md](android-debugging.md) for LeakCanary and heap dump analysis  
→ Check [coroutines-patterns-quick.md](coroutines-patterns-quick.md) for coroutine cancellation routing  

**Setting up CI/CD or code quality checks?**
→ Use [android-ci-cd.md](android-ci-cd.md) for Play-bound AAB, tracks, signing boundaries, staged rollout, and upload automation routing  
→ Play Console blocks upload for identity verification: [android-ci-cd.md → Play developer verification](android-ci-cd.md#play-developer-verification) (outside-repo human step)  
→ Use [code-quality.md](code-quality.md) for Detekt baseline and CI integration  
→ Use [gradle-setup.md](gradle-setup.md) for build cache and convention plugins  
→ Use [testing-quick.md](testing-quick.md) for test organization routing  

**Handling sensitive data or privacy concerns?**
→ Follow [crashlytics.md](crashlytics.md) for data scrubbing patterns  
→ Use [android-permissions.md](android-permissions.md) for proper permission justification  
→ Check [android-strictmode.md](android-strictmode.md) for detecting cleartext network traffic  

**Migrating legacy code (LiveData, Fragments, Accompanist, RxJava, Room 2.x)?**
→ Use [migration.md](migration.md) for all migration paths (including [Room 2.x → Room 3](migration.md#room-2x-to-room-3))  
→ Use [migration.md → Compose-XML interop (hardening)](migration.md#compose-xml-interop-hardening) when `ComposeView` / `AndroidView` share a screen with XML or focus-sensitive Views  
→ Follow [architecture.md](architecture.md) for MVVM patterns  

**Migrating to target SDK 37 (Android 17)?**
→ Walk [migration.md → Android 17 (API 37) Migration](migration.md#android-17-api-37-migration) top to bottom, then open each cross-link inside that section for full rules  
→ Ship JNI or bundled `.so` files: align ELF segments and Play 16 KB page-size checks per [migration.md → 16 KB memory page size](migration.md#16-kb-memory-page-size-play-and-native-code)  
→ Required: catalog `compileSdk` / `targetSdk` 37; pin `agp`, Gradle wrapper, `kotlin`, and `ksp` only after `./gradlew help` succeeds per [gradle-setup.md](gradle-setup.md) and [dependencies.md](dependencies.md); cleartext, loopback, CT, and URI grant rules per [android-security.md → URI grants on outbound intents](android-security.md#uri-grants-on-outbound-intents); adaptive large-screen layouts, `adjustResize` on the launcher Activity, and IME-after-rotation per [compose-patterns.md](compose-patterns.md); background audio/video via [android-media.md](android-media.md); [Android 17 location privacy](android-permissions.md#android-17-location-privacy); memory-limiter repro via [migration.md → Memory limiter](migration.md#memory-limiter-all-apps-on-affected-devices); Robolectric rules per [testing.md → Robolectric and SDK 37 (Android 17)](testing.md#robolectric-and-sdk-37-android-17) **only** when JVM tests use `RobolectricTestRunner`  
→ Forbidden: production-wide cleartext without domain-scoped Network Security Config; cross-process loopback without the API 37 permission where the platform requires it; background `MediaPlayer` / `AudioTrack` / raw `ExoPlayer` without Media3 `MediaSessionService` + `mediaPlayback` FGS + `MediaSession`; Robolectric releases older than 4.13 on current JDKs; assuming implicit URI grants on outbound intents outside `ACTION_SEND`, `ACTION_SEND_MULTIPLE`, and `ACTION_IMAGE_CAPTURE` (see [android-security.md](android-security.md#uri-grants-on-outbound-intents))  
→ `com.android.tools.build:gradle` HTTP 404: catalog `agp` is not published on `google()` yet; pick a published AGP that supports `compileSdk` 37 per [gradle-setup.md → AGP version pin](gradle-setup.md#agp-version-pin-resolve-before-merge)  
→ `MissingValueException` / unresolved providers on `compile*JavaWithJavac`: isolate JaCoCo Tier 2 (`ScopedArtifacts` combined report) per [android-code-coverage.md](android-code-coverage.md) before chasing Kotlin or KSP bumps  

**Adding Compose animations?**
→ Use [compose-patterns-quick.md](compose-patterns-quick.md) first; then [compose-patterns.md → Animation](compose-patterns.md#animation) for `AnimatedVisibility`, `AnimatedContent`, `animate*AsState`, `Animatable`, shared elements  
→ Use `graphicsLayer` for GPU-accelerated transforms (no recomposition)  
→ Always provide `label` parameter for Layout Inspector debugging  

**Using side effects (LaunchedEffect, DisposableEffect)?**
→ Use [compose-patterns-quick.md](compose-patterns-quick.md) first; then [compose-patterns.md → Side Effects](compose-patterns.md#side-effects) for effect selection guide  
→ `LaunchedEffect(key)` for state-driven coroutines, `rememberCoroutineScope` for event-driven  
→ `DisposableEffect` for listener/resource cleanup, always include `onDispose`  
→ `LifecycleResumeEffect` for onResume/onPause work (camera, media), `LifecycleStartEffect` for onStart/onStop (location, sensors)  

**Working with Modifier ordering or custom modifiers?**
→ Use [compose-patterns-quick.md](compose-patterns-quick.md) first; then [compose-patterns.md → Modifiers](compose-patterns.md#modifiers) for chain ordering rules and patterns  
→ Use `Modifier.Node` for custom modifiers (not deprecated `Modifier.composed`)  
→ Order: size → padding → drawing → interaction  

**Migrating from Accompanist or deprecated Compose APIs?**
→ Use [migration.md](migration.md) for Accompanist, Compose API, Material, Edge-to-Edge, and Room upgrades  
→ See [compose-patterns.md](compose-patterns.md) → "Deprecated Patterns & Migrations" for a summary list  

**Optimizing Compose recomposition or stability?**
→ Use [compose-patterns-quick.md](compose-patterns-quick.md) first; then [compose-patterns.md → Stability annotations](compose-patterns.md#stability-annotations-immutable-vs-stable) for `@Immutable`/`@Stable`  
→ Use [android-performance.md](android-performance.md) → "Compose Recomposition Performance" for three phases, deferred state reads, Strong Skipping Mode  
→ Check [gradle-setup.md](gradle-setup.md) for Compose Compiler metrics and stability reports  
→ Use [kotlin-patterns.md](kotlin-patterns.md) for immutable data structures  

**Working with databases (Room 3)?**
→ Define DAOs and entities in `core/database` per [modularization.md](modularization.md); use **`androidx.room3`**, KSP, and **`setDriver(BundledSQLiteDriver())`** on the builder (see `app.android.room` convention)  
→ Use [testing-quick.md](testing-quick.md) first; then [testing.md](testing.md) for in-memory database and Room 3 migration test samples  
→ Follow [architecture.md](architecture.md) for repository patterns  
→ Upgrading from Room 2.x: [migration.md → Room 2.x to Room 3](migration.md#room-2x-to-room-3)  

**Need internationalization/localization (i18n/l10n)?**
→ Use [android-i18n.md](android-i18n.md) for string resources, plurals, and RTL support  
→ Follow [compose-patterns-quick.md](compose-patterns-quick.md); open [compose-patterns.md](compose-patterns.md) for RTL layout samples  
→ Use [testing-quick.md](testing-quick.md); open [testing.md → Localization Testing](testing.md#localization-testing) for locale-specific testing  

**Implementing network calls (Retrofit)?**
→ Use [architecture.md](architecture.md) → "Network Layer Setup" for Retrofit service interfaces, Hilt NetworkModule, and AuthInterceptor  
→ Define API interfaces in `core/network` per [modularization.md](modularization.md)  
→ Follow [dependencies.md](dependencies.md) for Retrofit, OkHttp, and serialization setup  
→ Handle errors with generic `Result<T>` from [kotlin-patterns.md](kotlin-patterns.md)  

**Creating custom lint rules or code checks?**
→ Use [code-quality.md](code-quality.md) for Detekt custom rules  
→ Follow [gradle-setup.md](gradle-setup.md) for convention plugin setup  
→ Check [android-strictmode.md](android-strictmode.md) for runtime checks

**Need code coverage reporting?**
→ Use [android-code-coverage.md](android-code-coverage.md) for JaCoCo setup  
→ Follow [testing-quick.md](testing-quick.md) for test routing  
→ Check [gradle-setup.md](gradle-setup.md) for convention plugin integration

**Implementing security features (encryption, biometrics, pinning)?**
→ Use [android-security-quick.md](android-security-quick.md) for security routing; open [android-security.md](android-security.md) for Play Integrity samples and checklists  
→ Follow [android-permissions.md](android-permissions.md) for runtime permissions  
→ Check [crashlytics.md](crashlytics.md) for PII scrubbing and data privacy

**Implementing fraud-resistant or high-value flows (payments, session bootstrap, integrity-gated APIs)?**
→ Read [android-security-quick.md](android-security-quick.md) first; then [android-security.md](android-security.md) sections: [Device trust](android-security.md#device-trust-and-abuse-resistance), [Play Integrity API](android-security.md#play-integrity-api), [Root & Emulator Detection](android-security.md#root-emulator-detection), [Security Checklist](android-security.md#security-checklist)  
→ If Cloud Console / Play Console enablement or the **Google Cloud project number** is missing, list the missing prerequisites (see [android-security-quick.md](android-security-quick.md)) and stop before wiring client code
