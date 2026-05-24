# Reference index

Required: pick **one** file per task from [SKILL.md](../SKILL.md) Quick Reference or this index; read the linked section only.

Forbidden: load every file below; load a multi-thousand-line file in full when a `-quick.md` companion exists.

## Summary table

| File                                                 | Lines | Open when                                                                                                            | Quick                                                            |
|------------------------------------------------------|------:|----------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [android-accessibility.md](android-accessibility.md) |  1526 | TalkBack, semantics, touch targets, contrast, WCAG, Espresso a11y checks                                             | [android-accessibility-quick.md](android-accessibility-quick.md) |
| [android-ci-cd.md](android-ci-cd.md)                 |   129 | Play AAB, tracks, signing boundaries, rollout, upload automation, Play developer verification; agent vs Console work | -                                                                |
| [android-code-coverage.md](android-code-coverage.md) |   168 | JaCoCo unit + instrumented coverage, CI, ScopedArtifacts pitfalls                                                    | -                                                                |
| [android-data-sync.md](android-data-sync.md)         |  2344 | Offline-first, WorkManager sync, conflict resolution, cache invalidation                                             | [android-data-sync-quick.md](android-data-sync-quick.md)         |
| [android-debugging.md](android-debugging.md)         |   355 | Logcat, ANR, R8 mapping, release crashes, memory-limiter repro                                                       | -                                                                |
| [android-graphics.md](android-graphics.md)           |  1194 | Icons, adaptive launcher specs, custom drawing, Material Symbols, Coil3, Canvas                                      | -                                                                |
| [android-i18n.md](android-i18n.md)                   |  1057 | strings.xml, plurals, RTL, locale formatting, translation CI                                                         | -                                                                |
| [android-media.md](android-media.md)                 |   120 | Media3 background playback API 37, picking, sharing, preloading                                                      | -                                                                |
| [android-navigation.md](android-navigation.md)       |  2152 | Navigation3, deep links, App Links, adaptive layouts, large screens                                                  | [android-navigation-quick.md](android-navigation-quick.md)       |
| [android-notifications.md](android-notifications.md) |  1239 | Channels, FGS, MediaStyle, PiP, sharesheet from notification taps                                                    | -                                                                |
| [android-performance.md](android-performance.md)     |  1384 | Macrobenchmark, baseline profiles, vitals, recomposition, startup, APA/Perfetto                                      | -                                                                |
| [android-permissions.md](android-permissions.md)     |   811 | Runtime permissions, Photo Picker, contacts, API 37 location privacy                                                 | -                                                                |
| [android-security.md](android-security.md)           |  1795 | Play Integrity (Standard/Classic), `requestHash`/`nonce`, pinning, encryption, biometrics, Credential Manager        | [android-security-quick.md](android-security-quick.md)           |
| [android-strictmode.md](android-strictmode.md)       |   236 | StrictMode, cleartext detection, Compose stability diagnostics                                                       | -                                                                |
| [android-theming.md](android-theming.md)             |  2118 | Material 3 color roles, dynamic color, contrast, typography, shapes                                                  | [android-theming-quick.md](android-theming-quick.md)             |
| [architecture.md](architecture.md)                   |   961 | MVVM layers, repositories, DI, network, DataStore vs Room                                                            | -                                                                |
| [code-quality.md](code-quality.md)                   |   319 | Detekt convention plugin, custom rules, CI                                                                           | -                                                                |
| [compose-patterns.md](compose-patterns.md)           |  4092 | Screens, state, side effects, lists, edge-to-edge, forms, animation                                                  | [compose-patterns-quick.md](compose-patterns-quick.md)           |
| [coroutines-patterns.md](coroutines-patterns.md)     |  1625 | Dispatchers, Flow, StateFlow, testing coroutines, callbackFlow                                                       | [coroutines-patterns-quick.md](coroutines-patterns-quick.md)     |
| [crashlytics.md](crashlytics.md)                     |   709 | Firebase/Sentry interfaces, breadcrumbs, PII scrubbing                                                               | -                                                                |
| [dependencies.md](dependencies.md)                   |   289 | Version catalog, BOMs, pins, brownfield alignment, multi-module dependencies                                         | -                                                                |
| [design-patterns.md](design-patterns.md)             |  1750 | Gang-of-four style patterns adapted for Android modules                                                              | [design-patterns-quick.md](design-patterns-quick.md)             |
| [gradle-setup.md](gradle-setup.md)                   |  1086 | Convention plugins, flavors, R8 audit, build performance, verify Gradle                                              | -                                                                |
| [kotlin-delegation.md](kotlin-delegation.md)         |   750 | Interface delegation instead of base ViewModels                                                                      | -                                                                |
| [kotlin-patterns.md](kotlin-patterns.md)             |  1049 | Kotlin style, Result types, ViewModel patterns (all Kotlin code)                                                     | -                                                                |
| [migration.md](migration.md)                         |   802 | XML→Compose, LiveData, RxJava, Nav2→3, Room 2→3, API 37                                                              | -                                                                |
| [modularization.md](modularization.md)               |   417 | Module types, dependency rules, feature modules, existing-project alignment                                          | -                                                                |
| [testing.md](testing.md)                             |  2544 | Pre-release UI states, ADB/UIAutomator, Fakes, Turbine, Hilt tests, Compose UI, deep links                           | [testing-quick.md](testing-quick.md)                             |
| [workflows.md](workflows.md)                         |   322 | Task not in Quick Reference; greenfield bootstrap; multi-topic routing                                               | -                                                                |

## Quick companions (read before the full file)

| Quick                                                            | Full file                                            | Lines |
|------------------------------------------------------------------|------------------------------------------------------|------:|
| [android-accessibility-quick.md](android-accessibility-quick.md) | [android-accessibility.md](android-accessibility.md) |  1526 |
| [android-security-quick.md](android-security-quick.md)           | [android-security.md](android-security.md)           |  1795 |
| [coroutines-patterns-quick.md](coroutines-patterns-quick.md)     | [coroutines-patterns.md](coroutines-patterns.md)     |  1625 |
| [design-patterns-quick.md](design-patterns-quick.md)             | [design-patterns.md](design-patterns.md)             |  1750 |
| [compose-patterns-quick.md](compose-patterns-quick.md)           | [compose-patterns.md](compose-patterns.md)           |  4092 |
| [testing-quick.md](testing-quick.md)                             | [testing.md](testing.md)                             |  2544 |
| [android-data-sync-quick.md](android-data-sync-quick.md)         | [android-data-sync.md](android-data-sync.md)         |  2344 |
| [android-navigation-quick.md](android-navigation-quick.md)       | [android-navigation.md](android-navigation.md)       |  2152 |
| [android-theming-quick.md](android-theming-quick.md)             | [android-theming.md](android-theming.md)             |  2118 |


Detailed section anchors (open only when quick routing is insufficient): [INDEX-sections.md](INDEX-sections.md).
