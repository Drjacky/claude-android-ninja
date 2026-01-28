<p align="center">
  <img width="300px" src="/claude-android-ninja.png" />
</p>

# Android Agent Skill

This repository is an **Agent Skill** package for Android development with Kotlin and Jetpack Compose.  
It provides a structured set of instructions, templates, and references that help agents build
production‑quality Android apps consistently and efficiently.

Learn more about the Agent Skills format here: [agentskills.io](https://agentskills.io/home)

## What This Skill Covers
- Modular Android architecture (feature‑first, core modules, strict dependencies)
- Domain/Data/UI layering patterns with auth‑focused examples
- Jetpack Compose patterns, state management, and adaptive UI
- Navigation3 guidance and navigation coordination
- Gradle/build conventions and version catalog usage
- Testing practices with test doubles and Google Truth
- Dependency management rules and templates

## Key Files
- `SKILL.md` - entry point and workflow decision tree
- `references/architecture.md` - architecture principles, data/domain layers, and flows
- `references/modularization.md` - module structure and navigation wiring
- `references/compose-patterns.md` - Compose UI patterns and best practices
- `references/kotlin-patterns.md` - Kotlin best practices (must-read for Kotlin code)
- `references/coroutines-patterns.md` - coroutines best practices and patterns
- `references/gradle-setup.md` - build logic, conventions, and build files
- `references/code-quality.md` - Detekt setup and code quality rules
- `references/android-permissions.md` - runtime permissions and best practices
- `references/kotlin-delegation.md` - delegation patterns and composition guidance
- `references/crashlytics.md` - crash reporting with modular provider swaps
- `references/android-strictmode.md` - StrictMode guardrails and Compose stability
- `references/testing.md` - testing patterns and examples
- `references/dependencies.md` - dependency rules and version catalog guidance
- `references/android-performance.md` - benchmarking and performance checks
- `references/design-patterns.md` - Android-focused design patterns
- `templates/detekt.yml.template` - Detekt rules baseline
- `templates/libs.versions.toml.template` - version catalog source of truth
- `templates/settings.gradle.kts.template` - Gradle settings source of truth

## Scope
This skill is focused on Android app development using:
- Kotlin
- Jetpack Compose
- Navigation3
- Material 3
- Hilt
- Room

## Installation

### 1) Claude Code (manual)
Clone or download this repo, then place it in Claude’s skills folder and refresh skills.

```
~/.claude/skills/claude-android-ninja/
├── SKILL.md
├── references/
└── templates/
```

If you prefer project‑local skills, use `.claude/skills/` inside your project.

### 2) OpenSkills CLI
[OpenSkills](https://github.com/numman-ali/openskills) can install any skill repo and generate the AGENTS/skills metadata for multiple agents.

```bash
npx openskills install drjacky/claude-android-ninja
npx openskills sync
```

Optional universal install (shared across agents):
```bash
npx openskills install drjacky/claude-android-ninja --universal
```

## Contributing

### Request Missing Best Practices

If you need a best practice topic or pattern that's missing from this SKILL, please create a feature request on GitHub. This helps us prioritize what to add next.

Examples of topics you might request:
- Testing patterns (unit tests, UI tests, integration tests)
- Specific library patterns (Paging, WorkManager, etc.)
- Build and CI/CD patterns
- Security best practices
- Accessibility patterns

[Create a Feature Request](https://github.com/drjacky/claude-android-ninja/issues/new?template=feature_request.md)

### Report Issues

Found a bug, outdated pattern, or incorrect guidance? Please report it so we can fix it.

[Report a Bug](https://github.com/drjacky/claude-android-ninja/issues/new?template=bug_report.md)