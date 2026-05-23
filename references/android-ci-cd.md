# Android CI/CD and Play release

Directives for **repo and CI files** an agent edits, versus **Play Console, credentials, and store policy** handled outside tracked Gradle and YAML. Signing env var **names** and `.gitignore` patterns: [android-security.md](android-security.md) → **CI/CD Security**. Build cache and convention plugins: [gradle-setup.md](gradle-setup.md). Vitals automation an agent wires in Gradle: [android-performance.md](android-performance.md#optional-play-vitals-observability-play-developer-reporting-api).

## Agent vs outside-repo work

| Work                                                                       | Agent | Outside repo                                                  |
|----------------------------------------------------------------------------|-------|---------------------------------------------------------------|
| Edit Gradle so `bundleRelease` (or flavor task) produces `.aab`            | Yes   | Flavor dimensions match Play listing                          |
| Add or fix GitHub Actions / CI YAML for `detekt`, tests, `bundleRelease`   | Yes   | Repo secrets bound; workflow scope approved                   |
| Add `.gitignore` rules and remove committed keystores or password files    | Yes   | Keys created; secrets stored in CI or HSM                     |
| Choose next safe `versionCode` from Play history                           | No    | Next value or API output supplied; agent wires injection only |
| Upload AAB, create release, set track, set rollout %, promote              | No    | Play Console or authenticated publish CLI                     |
| Complete Play developer identity verification                            | No    | Play Console or Android Developer Console (human step)        |
| Complete Data safety, release notes, store listing text in Play            | No    | In-repo `CHANGELOG` / templates drafted on request only       |
| Run `./gradlew` locally or in CI when the environment exposes Gradle + SDK | Yes   | Network and secrets policy satisfied                          |
| Run `bundletool` when the binary is on disk and the tool is on `PATH`      | Yes   | `.aab` path and device spec JSON available                    |

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
9. [Play developer verification](#play-developer-verification)
10. [Release notes and policy surfaces](#release-notes-and-policy-surfaces)

## Ship artifact format

Required for Gradle: release automation builds an Android App Bundle (`.aab`) via `bundleRelease` or the correct flavored bundle task when the listing path is Google Play.

Forbidden in repo config: default Play-bound `release` to a fat universal APK when the team distributes through Play with AAB support.

Use when: sideloading, MDM, or non-Play channels - document `bundletool build-apks` or flavor-scoped APK tasks for upload handoff; agent adds Gradle wiring only where the project already uses APK outputs.

## versionCode and versionName

Play rejects uploads whose `versionCode` is not strictly greater than the max already accepted for that `applicationId`. An agent **never** picks the next integer from thin air.

Required for CI files: once the next allowed `versionCode` is supplied (or a documented allocator such as CI build number offset is approved), inject it through `gradle.properties`, CI-generated props, or `build.gradle.kts` logic.

Use `versionName` for human-readable labels in Gradle; do not encode Play ordering logic in `versionName` alone.

Forbidden: merge two branches that both bump `versionCode` to the same value without resolving Play upload history first.

## Release signing boundaries

Required for repo hygiene: no `*.jks`, `*.keystore`, passwords, or `signing.properties` with secrets in tracked files; align with [android-security.md](android-security.md) → **CI/CD Security** and `.gitignore` there.

Required for CI YAML: reference secret **names** (`KEYSTORE_PASSWORD`, etc.) only; never inline values.

Forbidden: add production `signingConfig` blocks that embed passwords in source readable on fork clones.

PR / topic branch workflows: use `assembleDebug` or unsigned `assembleRelease` patterns the project already uses; do not attach production signing to every pull request job.

Create upload keys, enroll Play App Signing, and paste SHA-256 into `assetlinks.json` hosts outside Gradle ([android-navigation.md](android-navigation.md#where-to-get-the-sha-256)).

## Play Console tracks

Routing vocabulary for release policy; **no Console API calls from an agent unless the user explicitly runs a tool with credentials already configured.**

| Track            | Typical use                             |
|------------------|-----------------------------------------|
| Internal testing | Fast validation on Play-signed binaries |
| Closed testing   | Named tester cohorts                    |
| Open testing     | Public opt-in beta                      |
| Production       | General availability after promotion    |

Default policy text: high-risk launches pass through internal or closed testing before production unless release management documents an exception.

## Staged rollout on production

Use when: blast radius must stay limited after production promotion.

Required: open production below 100% first unless a written hotfix policy demands full rollout; raise percentage only after crash and ANR signals from reporters and vitals look stable.

Agent-allowed in repo: document the team's rollout checklist in markdown; add links to vitals automation ([android-performance.md](android-performance.md#optional-play-vitals-observability-play-developer-reporting-api)) so signals are read before raising percentage.

## Upload automation routing

Agent-allowed: add `fastlane/Fastfile` skeletons, Gradle Play Publisher plugin declarations, or workflow steps **without** embedding JSON keys or passwords; use placeholder env names.

| Approach                                                    | Agent wires                                                                                  | Runs outside repo                            |
|-------------------------------------------------------------|----------------------------------------------------------------------------------------------|----------------------------------------------|
| Manual Play Console upload                                  | Documents that `.aab` path is the handoff artifact                                           | Browser upload                               |
| fastlane (`supply`, `pilot`, etc.)                          | Ruby files, lane names, CI job shell that invokes `bundle exec fastlane` when env vars exist | Ruby deps, API JSON, publish lanes           |
| Gradle Play Publisher (or other Play Developer API clients) | Plugin + task names in Gradle; CI step that calls the task                                   | Service account, Play permissions, key in CI |

Forbidden in CI design: publish tasks on arbitrary branch pushes without the same gates used on the protected integration branch.

## CI job composition (release lane)

Agent-executable when Gradle runs in the session:

- `./gradlew detekt` (or project baseline per [code-quality.md](code-quality.md)).
- Unit tests; add or adjust instrumented smoke jobs only where the project already has emulator CI or the user supplies a runner.
- `./gradlew bundleRelease` (or flavored bundle) only after the above succeed in the same pipeline definition.

Optional when `bundletool` exists and an `.aab` path is known: `bundletool validate` (or equivalent) in a workflow step enabled when ready.

Native `.so` gates: reference [migration.md](migration.md#16-kb-memory-page-size-play-and-native-code); agent adds CI grep / script steps only if the repo already uses that pattern.

## Internal sharing without Play Console

Agent-allowed: document the exact `bundletool build-apks` invocation and device-spec JSON layout; add a `Makefile` or script target that wraps the command when paths are parameterized.

## Play developer verification

Google requires [Android developer verification](https://developer.android.com/blog/posts/android-developer-verification-rolling-out-to-all-developers-on-play-console-and-android-developer-console) for developers using Play Console and the Android Developer Console.

Required: complete verification in Console before upload, signing, or policy actions that the UI blocks.

Forbidden for an agent: substitute Gradle or CI changes for identity verification; the human account owner must finish Console steps.

Use when: CI fails only at upload with a Console policy error about verification - route the user to Console, not repo edits.

## Release notes and policy surfaces

Agent-allowed: draft `CHANGELOG.md` entries or in-repo release note snippets from merged PR titles.

Play store listing text, Data safety questionnaire, and policy surfaces in Console: [android-security.md](android-security.md) → **Play Console Data Safety** and **Security Checklist**.

Forbidden for the org: shipping binaries whose permissions or data collection grew while Console Data safety answers and user-facing disclosure text stay unchanged - flag the mismatch in review comments before release.
