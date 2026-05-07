# Android CI/CD and Play release

Directives for **repo and CI files** an agent edits, versus **Play Console and credential work** only a human engineer performs. Signing env var **names** and `.gitignore` patterns: [android-security.md](android-security.md) → **CI/CD Security**. Build cache and convention plugins: [gradle-setup.md](gradle-setup.md). Vitals automation an agent wires in Gradle: [android-performance.md](android-performance.md#optional-play-vitals-observability-play-developer-reporting-api).

## Agent vs engineer

| Work                                                                       | Agent | Human engineer                                                 |
|----------------------------------------------------------------------------|-------|----------------------------------------------------------------|
| Edit Gradle so `bundleRelease` (or flavor task) produces `.aab`            | Yes   | Confirms flavor dimensions match Play listing                  |
| Add or fix GitHub Actions / CI YAML for `detekt`, tests, `bundleRelease`   | Yes   | Binds repo secrets; approves workflow scope                    |
| Add `.gitignore` rules and remove committed keystores or password files    | Yes   | Creates keys; stores secrets in CI or HSM                      |
| Choose next safe `versionCode` from Play history                           | No    | Supplies value or API output; agent wires injection only       |
| Upload AAB, create release, set track, set rollout %, promote              | No    | Play Console or authenticated CLI the engineer runs            |
| Complete Data safety, release notes, store listing text in Play            | No    | Agent drafts in-repo `CHANGELOG` / template text only if asked |
| Run `./gradlew` locally or in CI when the environment exposes Gradle + SDK | Yes   | Grants network / secrets where policy allows                   |
| Run `bundletool` when the binary is on disk and the tool is on `PATH`      | Yes   | Provides `.aab` path and device spec JSON when needed          |

Stop: do not fabricate `versionCode`, signing passwords, Play service account JSON, or upload actions that require Console login.

## Table of Contents

1. [Ship artifact format](#ship-artifact-format)
2. [versionCode and versionName](#versioncode-and-versionname)
3. [Release signing boundaries](#release-signing-boundaries)
4. [Play Console tracks](#play-console-tracks)
5. [Staged rollout on production](#staged-rollout-on-production)
6. [Upload automation routing](#upload-automation-routing)
7. [CI job composition (release lane)](#ci-job-composition-release-lane)
8. [Internal sharing without Play Console](#internal-sharing-without-play-console)
9. [Release notes and policy surfaces](#release-notes-and-policy-surfaces)

## Ship artifact format

Required for Gradle: release automation builds an Android App Bundle (`.aab`) via `bundleRelease` or the correct flavored bundle task when the listing path is Google Play.

Forbidden in repo config: default Play-bound `release` to a fat universal APK when the team distributes through Play with AAB support.

Use when: sideloading, MDM, or non-Play channels - document `bundletool build-apks` or flavor-scoped APK tasks for the engineer; agent adds Gradle wiring only where the project already uses APK outputs.

## versionCode and versionName

Play rejects uploads whose `versionCode` is not strictly greater than the max already accepted for that `applicationId`. An agent **never** picks the next integer from thin air.

Required for CI files: once the engineer states the next allowed `versionCode` (or a documented rule such as CI build number offset they own), inject it through `gradle.properties`, CI-generated props, or `build.gradle.kts` logic they approved.

Use `versionName` for human-readable labels in Gradle; do not encode Play ordering logic in `versionName` alone.

Forbidden: merge two branches that both bump `versionCode` to the same value without the engineer resolving Play state first.

## Release signing boundaries

Required for repo hygiene: no `*.jks`, `*.keystore`, passwords, or `signing.properties` with secrets in tracked files; align with [android-security.md](android-security.md) → **CI/CD Security** and `.gitignore` there.

Required for CI YAML: reference secret **names** (`KEYSTORE_PASSWORD`, etc.) only; never inline values.

Forbidden: add production `signingConfig` blocks that embed passwords in source readable on fork clones.

PR / topic branch workflows: use `assembleDebug` or unsigned `assembleRelease` patterns the project already uses; do not attach production signing to every pull request job.

Engineer-only: create upload keys, enroll Play App Signing, paste SHA-256 into `assetlinks.json` hosts ([android-navigation.md](android-navigation.md#where-to-get-the-sha-256)).

## Play Console tracks

Routing vocabulary for humans writing release policy; **no Console API calls from an agent unless the user explicitly runs a tool with credentials already configured.**

| Track            | Typical human use                       |
|------------------|-----------------------------------------|
| Internal testing | Fast validation on Play-signed binaries |
| Closed testing   | Named tester cohorts                    |
| Open testing     | Public opt-in beta                      |
| Production       | General availability after promotion    |

Default policy text for humans: high-risk launches pass through internal or closed testing before production unless release management documents an exception.

## Staged rollout on production

Human-only in Play Console: initial percentage, increases, and halts.

Agent-allowed in repo: document the team's rollout checklist in markdown the engineer follows; add links to vitals automation ([android-performance.md](android-performance.md#optional-play-vitals-observability-play-developer-reporting-api)) so humans see where to read signals before raising percentage.

## Upload automation routing

Agent-allowed: add `fastlane/Fastfile` skeletons, Gradle Play Publisher plugin declarations, or workflow steps **without** embedding JSON keys or passwords; use placeholder env names.

| Approach                                                    | Agent wires                                                                                  | Human runs                                                         |
|-------------------------------------------------------------|----------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| Manual Play Console upload                                  | Documents that `.aab` path is the handoff artifact                                           | Uploads in browser                                                 |
| fastlane (`supply`, `pilot`, etc.)                          | Ruby files, lane names, CI job shell that invokes `bundle exec fastlane` when env vars exist | Installs Ruby deps; stores API JSON; executes publish lanes        |
| Gradle Play Publisher (or other Play Developer API clients) | Plugin + task names in Gradle; CI step that calls the task                                   | Creates service account; grants Play permissions; stores key in CI |

Forbidden in CI design: publish tasks on arbitrary branch pushes without the same gates used on the protected integration branch.

## CI job composition (release lane)

Agent-executable when Gradle runs in the session:

- `./gradlew detekt` (or project baseline per [code-quality.md](code-quality.md)).
- Unit tests; add or adjust instrumented smoke jobs only where the project already has emulator CI or the user supplies a runner.
- `./gradlew bundleRelease` (or flavored bundle) only after the above succeed in the same pipeline definition.

Optional when `bundletool` exists and an `.aab` path is known: `bundletool validate` (or equivalent) in a workflow step the engineer can enable.

Native `.so` gates: point engineers at [migration.md](migration.md#16-kb-memory-page-size-play-and-native-code); agent adds CI grep / script steps only if the repo already uses that pattern.

## Internal sharing without Play Console

Agent-allowed: document the exact `bundletool build-apks` invocation and device-spec JSON layout; add a `Makefile` or script target that wraps the command when paths are parameterized.

Human: supplies `bundletool` JAR or install, signing trust for sideload, and target device parameters.

## Release notes and policy surfaces

Agent-allowed: draft `CHANGELOG.md` entries or in-repo release note snippets from merged PR titles.

Human-only: Play store listing text, Data safety questionnaire, and policy surfaces in Console ([android-security.md](android-security.md) → **Play Console Data Safety** and **Security Checklist**).

Forbidden for the org: shipping binaries whose permissions or data collection grew while Console Data safety answers and user-facing disclosure text stay unchanged - flag the mismatch in review comments; the engineer updates Console.
