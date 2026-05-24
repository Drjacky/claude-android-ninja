---
name: claude-android-ninja
description: Build and migrate Android apps with Kotlin, Jetpack Compose, MVVM, Hilt, Room 3 (KSP, SQLiteDriver, Flow/suspend DAOs), Navigation3, and multi-module Gradle. Use for new projects or modules, Compose screens and ViewModels, Room 3 and RemoteMediator, API 37 / targetSdk migration, Play Integrity client wiring, offline-first sync, and version-catalog alignment. Not for iOS, Flutter, React Native, KMP-only shared code without an Android app module, or backend-only APIs with no Android client.
compatibility: JDK 17+. Android Studio with Android SDK installed. Network access for Gradle dependency downloads. Version pins in assets/templates follow the repo catalog; align AGP/Kotlin/KSP with the user project before applying upgrades.
license: Apache-2.0
metadata:
  author: DrJacky
  version: "1.0.0"
  documentation: https://github.com/Drjacky/claude-android-ninja
  tags: android, kotlin, compose, mvvm, hilt, room, room3, datastore, paging, gradle, mobile
---
# Android Kotlin Compose Development

**Context ladder (smaller load first; full references stay complete):**

1. This file (`SKILL.md`) - routing, stop rules, examples.
2. `references/*-quick.md` when listed below - required/forbidden + section links (~40 lines).
3. One target section in the full `references/*.md` - code samples and checklists only.
4. [INDEX-sections.md](references/INDEX-sections.md) - anchor dump only when quick routing is insufficient.

Forbidden: load [INDEX-sections.md](references/INDEX-sections.md) or an entire multi-thousand-line reference when one section or a quick file covers the task.

Route tasks through the Quick Reference table. When no row matches, or the task needs greenfield bootstrap: [workflows.md](references/workflows.md). Full file list: [INDEX.md](references/INDEX.md).

**Required:**

- **Existing project:** read `settings.gradle.kts`, `gradle/libs.versions.toml`, and the `app` module build file before copying from `assets/` - [dependencies.md](references/dependencies.md#existing-project-brownfield), [modularization.md](references/modularization.md#existing-project-alignment). Stack migrations: [migration.md](references/migration.md).
- **Greenfield:** [workflows.md](references/workflows.md) → "Creating a new project?"
- After module, DI, navigation, Room schema, or AGP/Kotlin/KSP changes: `./gradlew help` then `:app:assembleDebug` (use the real app module name) - [gradle-setup.md](references/gradle-setup.md#verify-after-toolchain-or-module-changes).

**Outside-repo stop rules (do not substitute repo edits):** Play upload, tracks, rollout, `versionCode` - [android-ci-cd.md](references/android-ci-cd.md); Play Integrity prerequisites (Console/Cloud setup) - [android-security-quick.md](references/android-security-quick.md); production `adb install` / `pm clear` - [testing.md](references/testing.md#agent-automation-adb-and-uiautomator).

## Quick Reference

Rare or niche topics not listed here are in [INDEX.md](references/INDEX.md) (complete file list).

| Task                                                                                                           | Reference                                                                                                                                                                                                     |
|----------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Task not in table, greenfield bootstrap, multi-topic setup                                                     | [workflows.md](references/workflows.md)                                                                                                                                                                       |
| Full index of all reference files                                                                              | [INDEX.md](references/INDEX.md)                                                                                                                                                                               |
| Version catalog, pins, alpha policy, brownfield alignment                                                      | [dependencies.md](references/dependencies.md#version-strategy)                                                                                                                                                |
| Adding or updating dependencies (catalog aliases)                                                              | [dependencies.md](references/dependencies.md)                                                                                                                                                                 |
| Multi-module dependencies                                                                                      | [dependencies.md](references/dependencies.md)                                                                                                                                                                 |
| Project structure and modules                                                                                  | [modularization.md](references/modularization.md)                                                                                                                                                             |
| MVVM layers, repositories, DI                                                                                  | [architecture.md](references/architecture.md)                                                                                                                                                                 |
| Retrofit / OkHttp, NetworkModule, nullable DTOs, AuthInterceptor                                               | [architecture.md](references/architecture.md#network-layer-setup-corenetwork); [dependencies.md](references/dependencies.md)                                                                                  |
| DataStore (preferences, typed), Room vs DataStore rules                                                        | [architecture.md](references/architecture.md#datastore-preferences-typed)                                                                                                                                     |
| Code formatting (Spotless, `spotlessCheck` / `spotlessApply`)                                                  | [assets/convention/QUICK_REFERENCE.md](assets/convention/QUICK_REFERENCE.md#spotless-plugin); [gradle-setup.md](references/gradle-setup.md)                                                                   |
| Compose patterns, motion, animation, modifiers, stability                                                      | [compose-patterns-quick.md](references/compose-patterns-quick.md)                                                                                                                                             |
| Paging 3 + Room + network (`RemoteMediator`, remote keys, `initialize`)                                        | [compose-patterns.md](references/compose-patterns.md#offline-first-paging-and-remotemediator)                                                                                                                 |
| Accessibility, TalkBack, label copy, live regions, Espresso a11y                                               | [android-accessibility-quick.md](references/android-accessibility-quick.md)                                                                                                                                   |
| Notifications, foreground services, MediaStyle, PiP, sharesheet                                                | [android-notifications.md](references/android-notifications.md)                                                                                                                                               |
| Media: API 37 background playback, Media3, picking, FileProvider, sharesheet                                   | [android-media.md](references/android-media.md)                                                                                                                                                               |
| Data sync and offline-first patterns                                                                           | [android-data-sync-quick.md](references/android-data-sync-quick.md)                                                                                                                                           |
| Material 3 theming, spacing tokens, dynamic colors                                                             | [android-theming-quick.md](references/android-theming-quick.md)                                                                                                                                               |
| Navigation3, deep links, App Links, adaptive layouts                                                           | [android-navigation-quick.md](references/android-navigation-quick.md)                                                                                                                                         |
| Kotlin patterns, View lifecycle interop                                                                        | [kotlin-patterns.md](references/kotlin-patterns.md)                                                                                                                                                           |
| Coroutine patterns (`StateFlow`, `Channel`, `callbackFlow`)                                                    | [coroutines-patterns-quick.md](references/coroutines-patterns-quick.md)                                                                                                                                       |
| Gradle, product flavors, BuildConfig, build performance, R8                                                    | [gradle-setup.md](references/gradle-setup.md)                                                                                                                                                                 |
| Code quality (Detekt convention plugin, CI)                                                                    | [code-quality.md](references/code-quality.md)                                                                                                                                                                 |
| Testing approach (unit, instrumented, Compose UI)                                                              | [testing-quick.md](references/testing-quick.md)                                                                                                                                                               |
| Internationalization and localization                                                                          | [android-i18n.md](references/android-i18n.md)                                                                                                                                                                 |
| Runtime permissions, Photo Picker, API 37 location privacy                                                     | [android-permissions.md](references/android-permissions.md)                                                                                                                                                   |
| Kotlin delegation patterns                                                                                     | [kotlin-delegation.md](references/kotlin-delegation.md)                                                                                                                                                       |
| Crash reporting (Firebase / Sentry interfaces, PII scrubbing)                                                  | [crashlytics.md](references/crashlytics.md)                                                                                                                                                                   |
| Design patterns (GoF-style, Room FTS)                                                                          | [design-patterns-quick.md](references/design-patterns-quick.md)                                                                                                                                               |
| Performance, Play Vitals, startup, recomposition, jank, APA, Perfetto                                          | [android-performance.md](references/android-performance.md)                                                                                                                                                   |
| Debugging, Logcat, ANR, Gradle errors, R8 mapping, memory leaks                                                | [android-debugging.md](references/android-debugging.md)                                                                                                                                                       |
| Migrations (XML, RxJava, Navigation, Compose, Room 2→3, API 37, 16 KB native, Compose-XML interop)             | [migration.md](references/migration.md); [16 KB page size](references/migration.md#16-kb-memory-page-size-play-and-native-code); [Compose-XML interop](references/migration.md#compose-xml-interop-hardening) |

## Examples

**Greenfield Android app with convention plugins**

User goal: new repo matching the skill stack.

Actions: copy `assets/settings.gradle.kts.template`, `assets/libs.versions.toml.template`, `assets/convention/` into `build-logic/` per `assets/convention/QUICK_REFERENCE.md`; wire `includeBuild("build-logic")`; read [modularization.md](references/modularization.md) and [gradle-setup.md](references/gradle-setup.md).

Result: root + `app` + core modules with version catalog and convention plugins applied.

**New feature screen (Compose + ViewModel)**

User goal: one new flow in a feature module.

Actions: [modularization.md](references/modularization.md) for module naming and dependency direction; [compose-patterns-quick.md](references/compose-patterns-quick.md) for Screen, state, effects; [kotlin-patterns.md](references/kotlin-patterns.md) + [coroutines-patterns-quick.md](references/coroutines-patterns-quick.md) for `StateFlow` / events; [architecture.md](references/architecture.md) for domain vs data boundaries.

Result: feature module with Screen composable, ViewModel, `UiState`, and DI aligned to existing graphs.

**Offline-first list with Room 3 and remote API**

User goal: cached list + network refresh.

Actions: [compose-patterns.md](references/compose-patterns.md#offline-first-paging-and-remotemediator) for Paging 3 + `RemoteMediator`; [architecture.md](references/architecture.md) for repository placement; Room 3 + `SQLiteDriver` per [workflows.md](references/workflows.md) (Working with databases) and [migration.md](references/migration.md#room-2x-to-room-3) if upgrading.

Result: single source of truth in Room, UI driven by `PagingData` or equivalent pattern from the guide.

**Target SDK / compile SDK bump (e.g. API 37)**

User goal: migrate toolchain and platform requirements.

Actions: walk [migration.md](references/migration.md#android-17-api-37-migration); pin AGP/Kotlin/KSP using [gradle-setup.md](references/gradle-setup.md) and [dependencies.md](references/dependencies.md); cross-check edge-to-edge, media, security per [workflows.md](references/workflows.md) (Migrating to target SDK 37).

Result: `compileSdk` / `targetSdk` raised with manifest, Gradle, and feature code adjusted per the migration doc.

## Troubleshooting

| Symptom                                                              | Likely cause                                                                   | Fix                                                                                                                                                                                              |
|----------------------------------------------------------------------|--------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Gradle sync fails, plugin not found, or version catalog errors       | Missing `google()` / `mavenCentral()`, wrong plugin id, or catalog alias drift | [gradle-setup.md](references/gradle-setup.md); align with `assets/libs.versions.toml.template` when bootstrapping                                                                                |
| KSP errors on Room, or Room 3 builder rejects missing driver         | Room 3 expects `setDriver(BundledSQLiteDriver())` (or project equivalent)      | [migration.md](references/migration.md#room-2x-to-room-3); [modularization.md](references/modularization.md); [architecture.md](references/architecture.md)                                      |
| Compose runtime warnings about unstable / skippable recompositions   | Unstable parameter types or state held incorrectly                             | [compose-patterns-quick.md](references/compose-patterns-quick.md); [android-performance.md](references/android-performance.md); [kotlin-patterns.md](references/kotlin-patterns.md)              |
| Release build crashes, `ClassNotFoundException`, or missing R8 rules | Shrinking removed reflective or JNI entry points                               | [android-debugging.md](references/android-debugging.md#r8-keep-rules-troubleshooting); [gradle-setup.md](references/gradle-setup.md#r8-keep-rules-audit)                                         |
| ANR or jank claims without evidence                                  | Main-thread or measurement assumptions                                         | [android-performance.md](references/android-performance.md#android-performance-analyzer-apa) or [Perfetto](references/android-performance.md#perfetto-system-traces) before architecture changes |
