# Testing (quick)

Full guide: [testing.md](testing.md) (~2550 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#testingmd-2552-lines).

## Section routing

| Task | Open |
|------|------|
| Fakes vs mocks philosophy | [Testing Philosophy](testing.md#testing-philosophy) |
| `Fake*` repositories | [Test Doubles](testing.md#test-doubles) |
| ViewModel + Turbine | [ViewModel Tests](testing.md#viewmodel-tests) |
| Repository integration | [Repository Tests](testing.md#repository-tests) |
| `runTest`, time | [Coroutine Testing](testing.md#coroutine-testing) |
| `@HiltAndroidTest` | [Hilt Testing](testing.md#hilt-testing) |
| SDK 37 JVM tests | [Robolectric and SDK 37](testing.md#robolectric-and-sdk-37-android-17) |
| Room 3 in-memory / migrations | [Room Database Testing](testing.md#room-database-testing) |
| Navigation args | [SavedStateHandle Testing](testing.md#savedstatehandle-testing) |
| Navigators, Nav3 state | [Navigation Tests](testing.md#navigation-tests) |
| `am start`, App Links `pm` | [Testing Deep Links](testing.md#testing-deep-links) |
| Compose UI / Espresso | [UI Tests](testing.md#ui-tests) |
| ADB install, UIAutomator smoke | [Agent automation](testing.md#agent-automation-adb-and-uiautomator) |
| Empty / error / offline UI | [Pre-release UI state checklist](testing.md#pre-release-ui-state-checklist) |
| Screenshot / Roborazzi | [Screenshot Testing](testing.md#screenshot-testing) |
| Paging in tests | [Paging 3 Testing](testing.md#paging-3-testing) |

## Hard rules (summary)

**Required:**

- Google Truth for assertions; Turbine for multi-emission `Flow`.
- Hand-written fakes in `feature:*` and `core:*`; state + test hooks.
- MockK **only** in `app` for Navigation 3 framework types.
- Room 3 tests: `setDriver(BundledSQLiteDriver())`; migrations via `room3-testing` + `SQLiteConnection`.
- `MainDispatcherRule`; never bare `Dispatchers.Main` in tests.

**Forbidden:**

- Mocking libraries in feature/core modules.
- Feature-to-feature test dependencies; shared fakes live in `core:testing`.
- Production `adb install` / `pm clear` without explicit user OK (see agent automation section).

Open the full file for complete samples and CI YAML references.
