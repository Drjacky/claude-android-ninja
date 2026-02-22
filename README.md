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
- Jetpack Compose patterns, state management, and adaptive UI (NavigationSuiteScaffold, ListDetailPaneScaffold, SupportingPaneScaffold)
- Edge-to-edge display and predictive back gesture handling
- Material 3 theming (dynamic colors, typography, shapes, dark/light mode)
- Navigation3 guidance and navigation coordination
- Accessibility support (TalkBack, semantic properties, WCAG compliance)
- Internationalization & localization (i18n/l10n, RTL support, plurals)
- Notifications (channels, styles, actions, foreground services, progress-centric)
- Data synchronization & offline-first (sync strategies, conflict resolution, cache invalidation)
- Material Symbols icons, graphics, and custom drawing with Canvas
- Gradle/build conventions, version catalog usage, and KSP migration
- Testing practices with fakes, Hilt testing, and Room testing
- Coroutines patterns, structured concurrency, and Flow
- Kotlin delegation patterns and composition over inheritance
- Dependency management rules and templates
- Crash reporting with provider-agnostic interfaces (Firebase/Sentry)
- Runtime permissions with Compose patterns
- Performance benchmarking (Macrobenchmark, Microbenchmark, Baseline Profiles)
- StrictMode guardrails and Compose compiler stability diagnostics
- Code coverage with JaCoCo (unit + instrumented tests)
- Security (certificate pinning, encryption, biometrics, root detection, Play Integrity)
- Code quality with Detekt and Compose rules

## Key Files
- `SKILL.md` - entry point and workflow decision tree
- `references/architecture.md` - architecture principles, data/domain layers, and flows
- `references/modularization.md` - module structure and Navigation3 wiring
- `references/compose-patterns.md` - Compose UI patterns and best practices
- `references/android-theming.md` - Material 3 theming, colors, typography, shapes
- `references/android-accessibility.md` - accessibility, TalkBack, semantic properties, WCAG
- `references/android-i18n.md` - internationalization, localization, RTL support, plurals
- `references/android-notifications.md` - notifications, channels, styles, foreground services
- `references/android-data-sync.md` - offline-first, sync strategies, conflict resolution
- `references/kotlin-patterns.md` - Kotlin best practices (must-read for Kotlin code)
- `references/coroutines-patterns.md` - coroutines best practices and patterns
- `references/gradle-setup.md` - build logic, conventions, and build files
- `references/testing.md` - testing patterns with fakes, Hilt, Room, and Navigation3
- `references/android-graphics.md` - Material Symbols icons, Canvas drawing, and Palette API
- `references/android-permissions.md` - runtime permissions and best practices
- `references/kotlin-delegation.md` - delegation patterns and composition guidance
- `references/crashlytics.md` - crash reporting with modular provider swaps
- `references/android-strictmode.md` - StrictMode guardrails and Compose stability
- `references/android-code-coverage.md` - JaCoCo code coverage setup and CI integration
- `references/android-security.md` - security, encryption, biometrics, certificate pinning, root detection
- `references/code-quality.md` - Detekt setup and code quality rules
- `references/dependencies.md` - dependency rules and version catalog guidance
- `references/android-performance.md` - benchmarking and performance checks
- `references/design-patterns.md` - Android-focused design patterns
- `templates/proguard-rules.pro.template` - R8/ProGuard rules for all libraries
- `templates/detekt.yml.template` - Detekt static analysis configuration
- `templates/libs.versions.toml.template` - Version catalog with all dependencies
- `templates/settings.gradle.kts.template` - Project settings with repositories
- `templates/convention/` - Convention plugin implementations (18 plugins + 7 config files)

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
└── templates/
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
