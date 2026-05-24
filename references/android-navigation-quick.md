# Navigation (quick)

Full guide: [android-navigation.md](android-navigation.md) (~2160 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-navigationmd-2160-lines).

## Section routing

| Task | Open |
|------|------|
| Nav3 mental model, modules | [Navigation3 Architecture](android-navigation.md#navigation3-architecture) |
| Tablets, foldables, quality tiers | [Adaptive Quality and Large Screens](android-navigation.md#adaptive-quality-and-large-screens) |
| First Nav3 graph | [Navigation 3 Quick Start](android-navigation.md#navigation-3-quick-start) |
| `app` wiring, `NavigationSuiteScaffold` | [App Navigation Setup](android-navigation.md#app-navigation-setup) |
| `NavigationState`, back stack | [Navigation 3 State Management](android-navigation.md#navigation-3-state-management) |
| Invariants | [Navigation invariants](android-navigation.md#navigation-invariants) |
| Transitions, predictive back | [Animations](android-navigation.md#animations) |
| List-detail / custom panes | [Scenes & Custom Layouts](android-navigation.md#scenes-custom-layouts) |
| HTTPS App Links, custom schemes | [Deep Links](android-navigation.md#deep-links) |
| Conditional routes | [Conditional Navigation](android-navigation.md#conditional-navigation) |
| Results between destinations | [Returning Results](android-navigation.md#returning-results) |
| `hiltViewModel` scope | [ViewModel Scoping](android-navigation.md#viewmodel-scoping) |
| What not to do | [Navigation Anti-Patterns](android-navigation.md#navigation-anti-patterns) |
| Nav 2 migration | [Migration](android-navigation.md#migration) |

## Hard rules (summary)

**Required:**

- `NavigationSuiteScaffold` for top-level chrome; Material3 adaptive list-detail scaffolds for panes.
- Type-safe `NavKey` + Navigation3; deep links parsed to synthetic back stack.
- `singleTask` deep-link Activity: `onNewIntent` + `setIntent` same as `onCreate` parser.
- `android:autoVerify="true"` only on HTTPS filters; uppercase SHA-256 in `assetlinks.json`.
- Predictive back follows back stack (API 36+ default).

**Forbidden:**

- Security-critical flows on custom URI schemes only.
- `hiltViewModel()` in nested composables (wrong scope).
- Parallel boolean flags for dismiss alongside stack-driven sheets.
- Swipe-only navigation with no visible alternative on large screens.

Verification commands: [testing.md → Testing Deep Links](testing.md#testing-deep-links).
