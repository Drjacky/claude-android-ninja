# Compose patterns (quick)

Full guide: [compose-patterns.md](compose-patterns.md) (~4100 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#compose-patternsmd-4105-lines).

Required before UI work:

- Route + stateless `Screen`; `collectAsStateWithLifecycle()`; one-shot events via `Channel` + `receiveAsFlow()` in the Route.
- Material 3 semantic colors only - [android-theming.md](android-theming.md).
- String resources only - [android-i18n.md](android-i18n.md).
- Accessibility on every interactive/icon node - [android-accessibility-quick.md](android-accessibility-quick.md).

## Section routing

| Task | Open |
|------|------|
| Screen / Route split, naming | [Screen Architecture](compose-patterns.md#screen-architecture) |
| UiState, loading without wiping layout | [State Management](compose-patterns.md#state-management) |
| Cards, buttons, chips | [Component Patterns](compose-patterns.md#component-patterns) |
| Phone / tablet / foldable | [Adaptive UI](compose-patterns.md#adaptive-ui) |
| Theme tokens in composables | [Theming & Design System](compose-patterns.md#theming-design-system) |
| `@Preview`, stability | [Previews & Testing](compose-patterns.md#previews-testing) |
| `@Immutable` / `@Stable` | [Stability annotations](compose-patterns.md#stability-annotations-immutable-vs-stable) |
| Motion | [Animation](compose-patterns.md#animation) |
| LaunchedEffect, DisposableEffect, lifecycle effects | [Side Effects](compose-patterns.md#side-effects) |
| Modifier order, custom `Modifier.Node` | [Modifiers](compose-patterns.md#modifiers) |
| LazyColumn, Paging, scroll state | [Lists & Scrolling](compose-patterns.md#lists-scrolling) |
| `AndroidView`, interop | [View Composition Rules](compose-patterns.md#view-composition-rules) |
| Accompanist / API migrations | [Deprecated Patterns & Migrations](compose-patterns.md#deprecated-patterns-migrations) |
| Text fields, validation | [Forms & Input](compose-patterns.md#forms-input) |
| Edge-to-edge, IME insets (API 36+) | [Edge-to-Edge](compose-patterns.md#edge-to-edge-mandatory-on-api-36) in full file |
| Offline Paging + `RemoteMediator` | [Offline-first paging](compose-patterns.md#offline-first-paging-and-remotemediator) |

## Hard rules (summary)

**Required:**

- Stable layout during load/refresh; keep scroll and form state.
- `LifecycleResumeEffect` / `LifecycleStartEffect` for lifecycle-bound work (not manual `LifecycleEventObserver` in `DisposableEffect`).
- Validate gestures for trackpad, mouse, and stylus - not touch-only.
- At target SDK 37: explicit IME visibility handling after rotation (see edge-to-edge section in full file).

**Forbidden:**

- Full-screen spinner that replaces entire screen content on refresh.
- `PointerType.Touch`-only gesture branches.
- Hardcoded colors or user-visible literals in composables.

Open the full file only for code samples, migration tables, or edge-to-edge checklist detail.
