<p align="center">
  <img width="300px" src="/claude-android-ninja.png" />
</p>

# Android Agent Skill

![Kotlin](https://img.shields.io/badge/Kotlin-2.3.21-blue)
![AGP](https://img.shields.io/badge/AGP-9.2.0-orange)
![Min SDK](https://img.shields.io/badge/Min_SDK-24-green)
![Target SDK](https://img.shields.io/badge/Target_SDK-37-green)

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
- Material 3 theming (dynamic colors, typography, shapes, 8dp spacing tokens, app-category style fit, reserved resource names, dark/light mode)
- Navigation3 guidance (stable catalog pin, deep-link routing, SavedState Compose with `NavKey`), adaptive navigation, and large-screen quality tiers (phones, tablets, foldables, input expectations)
- Accessibility support (TalkBack, semantic properties, label copy, live regions, Espresso accessibility checks, WCAG alignment)
- Internationalization & localization (i18n/l10n, RTL support, plurals)
- Notifications (channels, styles, actions, foreground services, progress-centric, media/audio focus, PiP, system sharesheet, Navigation3 state from taps)
- Background media playback hardening at target SDK 37 (Media3 `MediaSessionService` for audio and video, `mediaPlayback` foreground service type, `FOREGROUND_SERVICE_MEDIA_PLAYBACK` permission, standalone `MediaPlayer`/`AudioTrack` forbidden in background, `requestAudioFocus` enforcement) and Media3 ExoPlayer catalog wiring with playback preloading guidance
- Data synchronization & offline-first (sync strategies, conflict resolution, cache invalidation)
- Material Symbols icons, adaptive launcher icon specs, graphics, custom drawing with Canvas, and Coil3 image loading patterns (AsyncImage, SubcomposeAsyncImage, Hilt ImageLoader)
- Gradle/build conventions, product flavors and BuildConfig, version catalog usage, KSP migration, Spotless formatting, and build performance optimization (diagnostics, lazy tasks, configuration cache)
- Testing practices with fakes, Hilt testing, Room 3 testing (`SQLiteDriver`, `room3-testing`), Compose Preview Screenshot Testing and Roborazzi trade routing, pre-release UI state checklist (empty, loading, error, offline, permissions), ADB device targeting, install or launch smoke, and UIAutomator black-box checks (`references/testing.md`)
- Coroutines patterns, structured concurrency, Flow (callbackFlow, backpressure, combine, shareIn), and common pitfalls
- Kotlin delegation patterns and composition over inheritance
- Dependency management rules and templates
- Crash reporting with provider-agnostic interfaces (Firebase/Sentry)
- Runtime permissions with Compose patterns (`references/android-permissions.md`) including contact picker, Embedded Photo Picker, and Android 17 location privacy; media playback, picking, FileProvider, and sharesheet routing (`references/android-media.md`)
- Performance benchmarking (Macrobenchmark, Microbenchmark, Baseline Profiles, ProfileInstaller, System Tracing), Android Performance Analyzer (APA) for Studio system traces, Perfetto UI for attached traces, Google Play Vitals context (crash/ANR bars, startup targets, frame budgets, battery/background), optional Play Developer Reporting API vitals, Compose recomposition optimization (three phases, deferred state reads, Strong Skipping Mode), and app startup optimization (App Startup library, splash screen, lazy initialization)
- StrictMode guardrails and Compose compiler stability diagnostics
- Code coverage with JaCoCo (unit + instrumented tests)
- Security (certificate pinning, encryption, biometrics, Credential Manager and passkeys, device identifiers and privacy, Play Data safety, Play Integrity Standard/Classic with server `decodeIntegrityToken`, `requestHash`/`nonce` binding, tiered policy, remediation, URI grants on outbound intents, local root/emulator checks as supplementary)
- Retrofit/networking patterns (service interfaces, nullable JSON DTOs, Hilt NetworkModule, AuthInterceptor)
- Haptic feedback, touch targets, and forms/input patterns (keyboard types, autofill, validation)
- Debugging guide (Logcat levels, ANR timeouts, Gradle error patterns, LeakCanary, Compose recomposition, R8 mapping and manual de-obfuscation, R8 keep-rules troubleshooting, process kill under memory caps / memory-limiter reproduction)
- Consolidated migration guide (XML to Compose, LiveData to StateFlow, RxJava to Coroutines, Navigation 2.x to Navigation3, Accompanist to official APIs, Material 2 to 3, Edge-to-Edge, Room 2.x to Room 3 (composite `@Relation` / `@Junction` keys), Android 17 / API 37 checklist (memory limiter, location privacy), 16 KB native page size and Play alignment, Compose-XML interop hardening, Splash Screen API; [`references/migration.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/migration.md))
- Code quality with Detekt and Compose rules
- Play CI/CD: AAB, release tracks, signing boundaries, staged rollout, upload automation (fastlane vs Gradle Play Publisher routing), and Play developer identity verification (Console human step outside the repo; [`references/android-ci-cd.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-ci-cd.md))

## Key Files
- [`SKILL.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/SKILL.md) - entry point and workflow decision tree
- [`references/architecture.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/architecture.md) - architecture principles, data/domain/ui/common layers, nullable network DTOs, and flows
- [`references/modularization.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/modularization.md) - module structure, dependency rules, and feature module creation
- [`references/android-navigation.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-navigation.md) - Navigation3 (stable pin, deep links, shared elements), adaptive navigation, large-screen quality tiers
- [`references/compose-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/compose-patterns.md) - Compose patterns, Material motion, animation, side effects, modifiers, stability, and migrations
- [`references/android-theming.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-theming.md) - Material 3 theming, spacing tokens, category style, colors, typography, shapes
- [`references/android-accessibility.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-accessibility.md) - accessibility, TalkBack, label copy, semantic properties, WCAG
- [`references/android-i18n.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-i18n.md) - internationalization, localization, RTL support, plurals
- [`references/android-notifications.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-notifications.md) - notifications, channels, media/PiP/sharesheet, foreground services
- [`references/android-media.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-media.md) - picking and sharing media/files (router), background playback at API 37 (Media3 `MediaSessionService`, FGS type, audio focus), and playback preloading
- [`references/android-data-sync.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-data-sync.md) - offline-first, sync strategies, conflict resolution
- [`references/kotlin-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/kotlin-patterns.md) - Kotlin best practices and View lifecycle interop (must-read for Kotlin code)
- [`references/coroutines-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/coroutines-patterns.md) - coroutines best practices and patterns
- [`references/gradle-setup.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/gradle-setup.md) - build logic, product flavors, BuildConfig, conventions, R8 Keep-Rules Audit, build files, and registering optional root tasks (for example Play Vitals reporting)
- [`references/android-ci-cd.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-ci-cd.md) - Play release AAB, tracks, signing boundaries, staged rollout, developer verification, bundletool sideloads, CI release lane ordering
- [`references/testing.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/testing.md) - testing patterns with fakes, Hilt, Room 3, Navigation3, Compose and UIAutomator smoke, ADB device targeting, pre-release UI state checklist, Preview vs Roborazzi visual regression routing, deep links, and screenshot testing
- [`references/android-graphics.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-graphics.md) - Material Symbols icons, adaptive launcher icons, Canvas drawing, Palette API
- [`references/android-permissions.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-permissions.md) - runtime permissions, contact picker, Embedded Photo Picker, Android 17 location privacy
- [`references/kotlin-delegation.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/kotlin-delegation.md) - delegation patterns and composition guidance
- [`references/crashlytics.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/crashlytics.md) - crash reporting with modular provider swaps
- [`references/android-strictmode.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-strictmode.md) - StrictMode guardrails and Compose stability
- [`references/android-code-coverage.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-code-coverage.md) - JaCoCo code coverage setup and CI integration
- [`references/android-security.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-security.md) - Play Integrity (Standard/Classic), server decode and verdict policy, `requestHash`/`nonce`, errors/remediation, device trust vs local root checks, Credential Manager, pinning, encryption, Data safety
- [`references/code-quality.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/code-quality.md) - Detekt setup and code quality rules
- [`references/dependencies.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/dependencies.md) - dependency rules and version catalog guidance (Navigation3, Room 3, Media3, SavedState Compose pins)
- [`references/android-performance.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-performance.md) - Play Vitals thresholds, optional Play Developer Reporting API (CI/Slack), benchmarking, APA and Perfetto trace routing, recomposition, app startup, splash screen
- [`references/android-debugging.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/android-debugging.md) - Logcat levels, ANR timeouts, LeakCanary, R8 de-obfuscation and keep-rules troubleshooting, memory-limiter reproduction, Gradle errors, Compose recomposition
- [`references/migration.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/migration.md) - XML to Compose, LiveData to StateFlow, RxJava, Navigation, Accompanist, Material, Edge-to-Edge, Room 2.x → Room 3, Android 17 / API 37 (memory limiter, location privacy), [16 KB native / Play](https://github.com/Drjacky/claude-android-ninja/blob/master/references/migration.md#16-kb-memory-page-size-play-and-native-code), [Compose-XML interop hardening](https://github.com/Drjacky/claude-android-ninja/blob/master/references/migration.md#compose-xml-interop-hardening), legacy splash
- [`references/design-patterns.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/references/design-patterns.md) - Android-focused design patterns
- [`assets/proguard-rules.pro.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/proguard-rules.pro.template) - R8/ProGuard rules for all libraries
- [`assets/detekt.yml.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/detekt.yml.template) - Detekt static analysis configuration
- [`assets/libs.versions.toml.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/libs.versions.toml.template) - Version catalog with all dependencies
- [`assets/settings.gradle.kts.template`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/settings.gradle.kts.template) - Project settings with repositories
- [`assets/convention/`](https://github.com/Drjacky/claude-android-ninja/tree/master/assets/convention) - Gradle convention plugins, `config/` helpers, and [`QUICK_REFERENCE.md`](https://github.com/Drjacky/claude-android-ninja/blob/master/assets/convention/QUICK_REFERENCE.md)

## Scope
This skill is focused on Android app development using:
- **Kotlin** (with coroutines, Flow, and kotlinx-datetime)
- **Jetpack Compose** and **Material 3** (dynamic color, Material Symbols icons, adaptive layouts: NavigationSuiteScaffold and pane scaffolds)
- **Navigation3** (type-safe routing)
- **Hilt** (dependency injection)
- **Room 3** (`androidx.room3`, KSP, `SQLiteDriver` / `sqlite-bundled`, Flow and `suspend` DAOs)
- **Retrofit** + **OkHttp** (networking)
- **Coil3** (image loading)
- **Media3** (ExoPlayer, session, playback preloading; catalog in `libs.versions.toml.template`)
- **Firebase Crashlytics** / **Sentry** (crash reporting)
- **Macrobenchmark** / **Microbenchmark** (performance testing)
- **Detekt** + **Compose Rules** (code quality)
- **Google Truth** + **Turbine** (testing assertions)

## Installation

Agent entry point after install: [`SKILL.md`](SKILL.md) (Quick Reference table and Workflow Decision Tree). Open `references/` files only for the task at hand. Format spec: [agentskills.io](https://agentskills.io/home).

### For AI agents

This skill uses the open [Agent Skills](https://agentskills.io/home) format: a folder named `claude-android-ninja/` with `SKILL.md`, `references/`, and `assets/`. Agents load skill metadata at session start; route Android work through [`SKILL.md`](SKILL.md) and open reference files only when needed.

| Agent                                                                                                             | Project path                                                                                                           | Global path                                          |
|-------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| [Claude Code](https://code.claude.com/docs/en/skills)                                                             | `.claude/skills/claude-android-ninja/`                                                                                 | `~/.claude/skills/claude-android-ninja/`             |
| [GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) (VS Code / agent mode)    | `.github/skills/claude-android-ninja/`                                                                                 | `~/.copilot/skills/claude-android-ninja/`            |
| [GitHub Copilot CLI](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)                       | Use [OpenSkills](#openskills-cli) `sync` into `AGENTS.md`, or copy to `.github/skills/` if your CLI build discovers it | `~/.copilot/skills/claude-android-ninja/`            |
| [Cursor](https://cursor.com/docs/context/skills)                                                                  | `.cursor/skills/claude-android-ninja/`                                                                                 | `~/.cursor/skills/claude-android-ninja/`             |
| [Gemini CLI](https://geminicli.com/docs/cli/skills/)                                                              | `.gemini/skills/claude-android-ninja/`                                                                                 | `~/.gemini/skills/claude-android-ninja/`             |
| [Codex](https://developers.openai.com/codex/skills)                                                               | `.codex/skills/claude-android-ninja/`                                                                                  | `~/.codex/skills/claude-android-ninja/`              |
| [Windsurf](https://docs.windsurf.com/windsurf/cascade/skills) (Cascade)                                           | `.windsurf/skills/claude-android-ninja/`                                                                               | `~/.codeium/windsurf/skills/claude-android-ninja/`   |
| [Cline](https://docs.cline.bot/cline/customization/skills) / [Roo Code](https://docs.roocode.com/features/skills) | `.agents/skills/claude-android-ninja/` (also `.cline/skills/`, `.roo/skills/`)                                         | `~/.agents/skills/claude-android-ninja/`             |
| [OpenCode](https://opencode.ai/docs/skills)                                                                       | `.opencode/skills/claude-android-ninja/`                                                                               | `~/.config/opencode/skills/claude-android-ninja/`    |
| [OpenClaw](https://github.com/openclaw/openclaw)                                                                  | `skills/claude-android-ninja/` (project root)                                                                          | `~/.openclaw/skills/claude-android-ninja/`           |
| [Hermes](https://github.com/NousResearch/hermes-agent)                                                            | `.hermes/skills/claude-android-ninja/`                                                                                 | `~/.hermes/skills/claude-android-ninja/`             |
| [Kilo Code](https://kilo.ai/docs/customize/skills)                                                                | `.kilo/skills/claude-android-ninja/` (also `.kilocode/skills/`, `.agents/skills/`)                                     | `~/.kilo/skills/claude-android-ninja/`               |
| [Google Antigravity](https://antigravity.google/docs/skills)                                                      | `.agent/skills/claude-android-ninja/`                                                                                  | `~/.gemini/antigravity/skills/claude-android-ninja/` |

**Multi-agent / one `AGENTS.md`:** install to a shared tree so Claude Code, Cursor, Codex, and others do not fight over `.claude/skills/`:

```bash
npx openskills install drjacky/claude-android-ninja --universal
npx openskills sync
```

That writes to `.agent/skills/claude-android-ninja/` (project) or `~/.agent/skills/` (global). Alternative installer: [`npx skills add drjacky/claude-android-ninja`](https://github.com/vercel-labs/skills) with `-a` for specific agents (50+ tools).

| Step | Action |
|------|--------|
| 1 | Install via the table above, [manual install](#manual-install), or [OpenSkills](#openskills-cli). |
| 2 | Start a **new** agent session (skills load at startup). |
| 3 | Route Android tasks through `SKILL.md`; load linked reference files on demand. |

Load without copying files (when [OpenSkills](https://github.com/numman-ali/openskills) is available):

```bash
npx openskills read claude-android-ninja
```

### Manual install

Clone this repo, then copy the whole folder into the **project** or **global** path for your agent from the table above (same tree for every tool):

```bash
git clone https://github.com/Drjacky/claude-android-ninja.git
# Example: Claude Code global — swap the destination for your agent's path
mkdir -p ~/.claude/skills
cp -r claude-android-ninja ~/.claude/skills/claude-android-ninja
```

Expected layout (destination varies by agent):

```
<agent-skills-dir>/claude-android-ninja/
├── SKILL.md
├── references/
└── assets/
```

Restart the agent or start a new session so the skill is discovered.

### OpenSkills CLI

[OpenSkills](https://github.com/numman-ali/openskills) installs the skill and can generate `AGENTS.md` / skills metadata for multiple agents.

```bash
npx openskills install drjacky/claude-android-ninja
npx openskills sync
```

Global install (`~/.claude/skills/`, shared across projects):

```bash
npx openskills install drjacky/claude-android-ninja --global
```

Universal install (shared across supported agents):

```bash
npx openskills install drjacky/claude-android-ninja --universal
```

### Verify install

- Folder contains `SKILL.md`, `references/`, and `assets/` (templates and convention plugins).
- Agent session was restarted after copy or install.
- Optional: `npx openskills read claude-android-ninja` prints skill content when using OpenSkills.

## Contributing

### Request Missing Best Practices

If you need a best practice topic or pattern that's missing from this SKILL, please create a feature request on GitHub. This helps us prioritize what to add next.

[Create a Feature Request](https://github.com/drjacky/claude-android-ninja/issues/new?template=feature_request.md)

### Report Issues

Found a bug, outdated pattern, or incorrect guidance? Please report it so we can fix it.

[Report a Bug](https://github.com/drjacky/claude-android-ninja/issues/new?template=bug_report.md)

### Star History Chart

[![Star History Chart](https://api.star-history.com/svg?repos=drjacky/claude-android-ninja&Date=&type=Date)](https://api.star-history.com/svg?repos=drjacky/claude-android-ninja&Date=&type=Date)
