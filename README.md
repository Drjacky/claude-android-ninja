<p align="center">
  <img width="300px" src="/claude-android-ninja.png" />
</p>

# Android Agent Skill

![Kotlin](https://img.shields.io/badge/Kotlin-2.2.21-blue)
![AGP](https://img.shields.io/badge/AGP-9.0.0-orange)
![Min SDK](https://img.shields.io/badge/Min_SDK-24-green)
![Target SDK](https://img.shields.io/badge/Target_SDK-36-green)

This repository is an **Agent Skill** package for Android development with Kotlin and Jetpack Compose.  
It provides a structured set of instructions, templates, and references that help agents build
production-quality Android apps consistently and efficiently.

Learn more about the Agent Skills format here: [agentskills.io](https://agentskills.io/home)

Browse this skill on [SkillsMP](https://skillsmp.com/skills/drjacky-claude-android-ninja-skill-md)

## What This Skill Covers
- Modular Android architecture (feature-first, core modules, strict dependencies)
- Domain/Data/UI layering patterns with auth-focused examples
- Jetpack Compose patterns, state management, animation, side effects, modifiers, and adaptive UI (NavigationSuiteScaffold, ListDetailPaneScaffold, SupportingPaneScaffold)
- Edge-to-edge display and predictive back gesture handling
- Material 3 theming (dynamic colors, typography, shapes, dark/light mode)
- Navigation3 guidance and navigation coordination
- Accessibility support (TalkBack, semantic properties, WCAG compliance)
- Internationalization & localization (i18n/l10n, RTL support, plurals)
- Notifications (channels, styles, actions, foreground services, progress-centric)
- Data synchronization & offline-first (sync strategies, conflict resolution, cache invalidation)
- Material Symbols icons, graphics, custom drawing with Canvas, and Coil3 image loading patterns (AsyncImage, SubcomposeAsyncImage, Hilt ImageLoader)
- Gradle/build conventions, version catalog usage, KSP migration, and build performance optimization (diagnostics, lazy tasks, configuration cache)
- Testing practices with fakes, Hilt testing, Room testing, and Compose Preview Screenshot Testing
- Coroutines patterns, structured concurrency, Flow (callbackFlow, backpressure, combine, shareIn), and common pitfalls
- Kotlin delegation patterns and composition over inheritance
- Dependency management rules and templates
- Crash reporting with provider-agnostic interfaces (Firebase/Sentry)
- Runtime permissions with Compose patterns
- Performance benchmarking (Macrobenchmark, Microbenchmark, Baseline Profiles, ProfileInstaller, System Tracing), Compose recomposition optimization (three phases, deferred state reads, Strong Skipping Mode), and app startup optimization (App Startup library, splash screen, lazy initialization)
- StrictMode guardrails and Compose compiler stability diagnostics
- Code coverage with JaCoCo (unit + instrumented tests)
- Security (certificate pinning, encryption, biometrics, root detection, Play Integrity)
- Retrofit/networking patterns (service interfaces, Hilt NetworkModule, AuthInterceptor)
- Haptic feedback, touch targets, and forms/input patterns (keyboard types, autofill, validation)
- Debugging guide (Logcat, ANR analysis, LeakCanary, Compose recomposition, R8 mapping and manual de-obfuscation)
- Consolidated migration guide (XML to Compose, LiveData to StateFlow, RxJava to Coroutines, Navigation 2.x to Navigation3, Accompanist to official APIs, Material 2 to 3, Edge-to-Edge)
- Code quality with Detekt and Compose rules

## Key Files
- [`SKILL.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/SKILL.md) - entry point and workflow decision tree
- [`references/architecture.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/architecture.md) - architecture principles, data/domain layers, and flows
- [`references/modularization.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/modularization.md) - module structure, dependency rules, and feature module creation
- [`references/android-navigation.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-navigation.md) - Navigation3 architecture, state management, and adaptive navigation
- [`references/compose-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/compose-patterns.md) - Compose patterns, animation, side effects, modifiers, stability, and migrations
- [`references/android-theming.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-theming.md) - Material 3 theming, colors, typography, shapes
- [`references/android-accessibility.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-accessibility.md) - accessibility, TalkBack, semantic properties, WCAG
- [`references/android-i18n.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-i18n.md) - internationalization, localization, RTL support, plurals
- [`references/android-notifications.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-notifications.md) - notifications, channels, styles, foreground services
- [`references/android-data-sync.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-data-sync.md) - offline-first, sync strategies, conflict resolution
- [`references/kotlin-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/kotlin-patterns.md) - Kotlin best practices (must-read for Kotlin code)
- [`references/coroutines-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/coroutines-patterns.md) - coroutines best practices and patterns
- [`references/gradle-setup.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/gradle-setup.md) - build logic, conventions, and build files
- [`references/testing.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/testing.md) - testing patterns with fakes, Hilt, Room, and Navigation3
- [`references/android-graphics.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-graphics.md) - Material Symbols icons, Canvas drawing, and Palette API
- [`references/android-permissions.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-permissions.md) - runtime permissions and best practices
- [`references/kotlin-delegation.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/kotlin-delegation.md) - delegation patterns and composition guidance
- [`references/crashlytics.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/crashlytics.md) - crash reporting with modular provider swaps
- [`references/android-strictmode.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-strictmode.md) - StrictMode guardrails and Compose stability
- [`references/android-code-coverage.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-code-coverage.md) - JaCoCo code coverage setup and CI integration
- [`references/android-security.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-security.md) - security, encryption, biometrics, certificate pinning, root detection
- [`references/code-quality.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/code-quality.md) - Detekt setup and code quality rules
- [`references/dependencies.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/dependencies.md) - dependency rules and version catalog guidance
- [`references/android-performance.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-performance.md) - benchmarking, recomposition performance, app startup optimization, and splash screen
- [`references/android-debugging.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-debugging.md) - Logcat, ANR, LeakCanary, R8 de-obfuscation, Gradle errors, Compose recomposition
- [`references/migration.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/migration.md) - XML to Compose, LiveData to StateFlow, RxJava, Navigation, Accompanist, Material migrations
- [`references/design-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/design-patterns.md) - Android-focused design patterns
- [`assets/proguard-rules.pro.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/proguard-rules.pro.template) - R8/ProGuard rules for all libraries
- [`assets/detekt.yml.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/detekt.yml.template) - Detekt static analysis configuration
- [`assets/libs.versions.toml.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/libs.versions.toml.template) - Version catalog with all dependencies
- [`assets/settings.gradle.kts.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/settings.gradle.kts.template) - Project settings with repositories
- [`assets/convention/`](https://github.com/Drjacky/claude-android-ninja/tree/master/assets/convention) - Convention plugin implementations (18 plugins + 7 config files)

## Scope
This skill is focused on Android app development using:
- **Kotlin** (with coroutines, Flow, and kotlinx-datetime)
- **Jetpack Compose** (Material 3 with Material Symbols icons)
- **Material 3 Adaptive** (NavigationSuiteScaffold, adaptive pane scaffolds)
- **Navigation3** (type-safe routing)
- **Material 3**
- **Hilt** (dependency injection)
- **Room** (database with KSP)
- **Retrofit** + **OkHttp** (networking)
- **Coil3** (image loading)
- **Firebase Crashlytics** / **Sentry** (crash reporting)
- **Macrobenchmark** / **Microbenchmark** (performance testing)
- **Detekt** + **Compose Rules** (code quality)
- **Google Truth** + **Turbine** (testing assertions)

## Installation

### 1. Claude Code (manual)
Clone or download this repo, then place it in Claude's skills folder and refresh skills.

```
~/.claude/skills/claude-android-ninja/
├── SKILL.md
├── references/
└── assets/
```

If you prefer project-local skills, use `.claude/skills/` inside your project.

### 2. OpenSkills CLI
[OpenSkills](https://github.com/numman-ali/openskills) can install any skill repo and generate the AGENTS/skills metadata for multiple agents.

```bash
npx openskills install drjacky/claude-android-ninja
npx openskills sync
```

Global install (installs to `~/.claude/skills/`, shared across all projects):
```bash
npx openskills install drjacky/claude-android-ninja --global
```

Optional universal install (shared across agents):
```bash
npx openskills install drjacky/claude-android-ninja --universal
```

## Contributing

### Request Missing Best Practices

If you need a best practice topic or pattern that's missing from this SKILL, please create a feature request on GitHub. This helps us prioritize what to add next.

[Create a Feature Request](https://github.com/drjacky/claude-android-ninja/issues/new?template=feature_request.md)

### Report Issues

Found a bug, outdated pattern, or incorrect guidance? Please report it so we can fix it.

[Report a Bug](https://github.com/drjacky/claude-android-ninja/issues/new?template=bug_report.md)
