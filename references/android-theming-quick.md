# Theming (quick)

Full guide: [android-theming.md](android-theming.md) (~2130 lines). Section anchors: [INDEX-sections.md](INDEX-sections.md#android-themingmd-2126-lines).

## Section routing

| Task | Open |
|------|------|
| `MaterialTheme` setup | [Material 3 Theme System](android-theming.md#material-3-theme-system) |
| `Color.kt`, roles | [Color Schemes](android-theming.md#color-schemes) |
| `on*` pairing | [Color Pairing Rules](android-theming.md#color-pairing-rules) |
| Borders / dividers | [`outline` vs `outlineVariant`](android-theming.md#outline-vs-outlinevariant) |
| Surface containers | [Surface Container Hierarchy](android-theming.md#surface-container-hierarchy) |
| Elevation vs shadow | [Tonal Elevation vs Shadows](android-theming.md#tonal-elevation-vs-shadows) |
| Material You | [Dynamic Color](android-theming.md#dynamic-color-material-you) |
| Contrast slider API 34+ | [User Contrast Preference](android-theming.md#user-contrast-preference-android-14) |
| Type scale | [Typography Scales](android-theming.md#typography-scales) |
| Shapes | [Shape Theming](android-theming.md#shape-theming) |
| Dark/light toggle | [Dark/Light Mode Switching](android-theming.md#darklight-mode-switching) |
| User preference storage | [Theme Preferences](android-theming.md#theme-preferences) |
| Nested `MaterialTheme` | [Scoped Themes](android-theming.md#scoped-themes) |
| ViewModel / DataStore | [Architecture Integration](android-theming.md#architecture-integration) |
| 8dp spacing, category fit | [Layout Spacing](android-theming.md#layout-spacing-and-component-dimensions), [Visual Style by App Category](android-theming.md#visual-style-by-app-category) |

## Hard rules (summary)

**Required:**

- Semantic roles from `MaterialTheme.colorScheme`; never hardcoded brand colors in composables.
- Full M3 role set in `Color.kt` when using dynamic color.
- Depth via container tone first; shadows only when content is unknown underneath.
- `outline` for interactive borders; `outlineVariant` for decorative dividers.
- Compose UI: [compose-patterns.md → Theming & Design System](compose-patterns.md#theming-design-system).

**Forbidden:**

- Raw `Color(0xFF...)` for theme surfaces without scoped override.
- `left`/`right` padding for RTL-sensitive layout (use start/end).

Open the full file for harmonization math, expressive M3, and preview setup.
