# Android Theming

Material Design 3 theming: dynamic color, custom color schemes, typography scales, shape theming, dark/light mode.

All Kotlin code must align with `references/kotlin-patterns.md`. Theme usage in composables: `references/compose-patterns.md`. Color contrast targets: `references/android-accessibility.md`.

## Table of Contents

- [Material 3 Theme System](#material-3-theme-system)
- [Color Schemes](#color-schemes)
- [Color Pairing Rules](#color-pairing-rules)
- [`outline` vs `outlineVariant`](#outline-vs-outlinevariant)
- [Surface Container Hierarchy](#surface-container-hierarchy)
- [Tonal Elevation vs Shadows](#tonal-elevation-vs-shadows)
- [Dynamic Color (Material You)](#dynamic-color-material-you)
- [User Contrast Preference (Android 14+)](#user-contrast-preference-android-14)
- [Typography Scales](#typography-scales)
- [Shape Theming](#shape-theming)
- [Material 3 Expressive](#material-3-expressive)
- [Dark/Light Mode Switching](#darklight-mode-switching)
- [Theme Preferences](#theme-preferences)
- [Custom Theme Attributes](#custom-theme-attributes)
  - [Brand Color Harmonization](#brand-color-harmonization)
- [Scoped Themes](#scoped-themes)
- [Architecture Integration](#architecture-integration)
- [Testing](#testing)
- [Layout Spacing and Component Dimensions](#layout-spacing-and-component-dimensions)
- [Reserved Resource Names](#reserved-resource-names)
- [Visual Style by App Category](#visual-style-by-app-category)
- [Theme routing](#theme-routing)

## Material 3 Theme System

Material 3 uses a three-layer system: color scheme, typography, and shapes.

### Basic Theme Setup

```kotlin
// core/ui/theme/Theme.kt
package com.example.core.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### Using in MainActivity

Edge-to-edge is mandatory on API 36. Use `Scaffold` which handles system bar insets automatically.

```kotlin
// app/MainActivity.kt
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        enableEdgeToEdge()
        
        setContent {
            AppTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    MainNavigation(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}
```

## Color Schemes

### Full Color Role Reference (M3)

Material 3 defines ~40 semantic color roles. Use these on `MaterialTheme.colorScheme.*` instead of raw `Color(...)` so themes, dark mode, dynamic color, and user contrast all keep working.

**Accent roles** (3 groups: primary, secondary, tertiary)

| Role                                      | `colorScheme.*`      | Use for                                              |
|-------------------------------------------|----------------------|------------------------------------------------------|
| Primary                                   | `primary`            | High-emphasis fills, FAB, primary button             |
| On Primary                                | `onPrimary`          | Text/icons on `primary`                              |
| Primary Container                         | `primaryContainer`   | Standout container fill (selected chip, hero card)   |
| On Primary Container                      | `onPrimaryContainer` | Text/icons on `primaryContainer`                     |
| Secondary / On / Container / On Container | `secondary*`         | Less prominent accents (tonal buttons, filter chips) |
| Tertiary  / On / Container / On Container | `tertiary*`          | Contrasting accents (badges, complementary surfaces) |

**Error roles** (do not change with dynamic color)

| Role               | `colorScheme.*`    | Use for                          |
|--------------------|--------------------|----------------------------------|
| Error              | `error`            | Destructive action, validation   |
| On Error           | `onError`          | Text/icons on `error`            |
| Error Container    | `errorContainer`   | Error banner / inline error fill |
| On Error Container | `onErrorContainer` | Text/icons on `errorContainer`   |

**Surface roles** (the modern depth system - prefer over `background`)

| Role                      | `colorScheme.*`           | Use for                                                       |
|---------------------------|---------------------------|---------------------------------------------------------------|
| Surface                   | `surface`                 | Default screen background                                     |
| On Surface                | `onSurface`               | Primary text/icons on any surface                             |
| On Surface Variant        | `onSurfaceVariant`        | Lower-emphasis text/icons on surface                          |
| Surface Container Lowest  | `surfaceContainerLowest`  | Lowest-tone container (rarely used)                           |
| Surface Container Low     | `surfaceContainerLow`     | Cards in flow, low-emphasis containers                        |
| Surface Container         | `surfaceContainer`        | Default container (nav bar, persistent panels)                |
| Surface Container High    | `surfaceContainerHigh`    | Menus, scrolled top app bar                                   |
| Surface Container Highest | `surfaceContainerHighest` | Filled cards, highest-emphasis nested container               |
| Surface Dim               | `surfaceDim`              | Always-dimmest surface (both themes)                          |
| Surface Bright            | `surfaceBright`           | Always-brightest surface (both themes)                        |
| Surface Tint              | `surfaceTint`             | Tonal-elevation tint (set by `Surface(tonalElevation = ...)`) |

**Inverse roles** (for elements that contrast against the surrounding UI, e.g. snackbars)

| Role               | `colorScheme.*`    | Use for                              |
|--------------------|--------------------|--------------------------------------|
| Inverse Surface    | `inverseSurface`   | Snackbar background, inverted toast  |
| Inverse On Surface | `inverseOnSurface` | Text on `inverseSurface`             |
| Inverse Primary    | `inversePrimary`   | Actionable text on `inverseSurface`  |

**Outline roles**

| Role            | `colorScheme.*`  | Use for                                                  |
|-----------------|------------------|----------------------------------------------------------|
| Outline         | `outline`        | Interactive boundaries (text-field borders, focus rings) |
| Outline Variant | `outlineVariant` | Decorative dividers, card borders                        |

**Fixed accent roles** (same color in light **and** dark - keep brand identity inside scoped surfaces)

| Role                                                 | `colorScheme.*`         | Use for                                          |
|------------------------------------------------------|-------------------------|--------------------------------------------------|
| Primary Fixed                                        | `primaryFixed`          | Branded chip / badge that must not flip on theme |
| Primary Fixed Dim                                    | `primaryFixedDim`       | Dimmer companion to `primaryFixed`               |
| On Primary Fixed                                     | `onPrimaryFixed`        | Text/icons on `primaryFixed`                     |
| On Primary Fixed Variant                             | `onPrimaryFixedVariant` | Lower-emphasis text on `primaryFixed`            |
| (same shape for `secondaryFixed*`, `tertiaryFixed*`) | -                       | Brand-locked secondary/tertiary surfaces         |

Fixed roles do not adapt to theme - only use them where preserving identity matters more than contrast adjustment.

**Scrim**

| Role  | `colorScheme.*` | Use for                                        |
|-------|-----------------|------------------------------------------------|
| Scrim | `scrim`         | Modal backdrops behind dialogs / bottom sheets |

`background` / `onBackground` still exist for backwards compatibility; in new code prefer `surface` / `onSurface`.

### Default Light and Dark Schemes

Material 3 uses semantic color roles instead of hardcoded colors.

```kotlin
// core/ui/theme/Color.kt
package com.example.core.ui.theme

import androidx.compose.ui.graphics.Color

// Light theme colors
val md_theme_light_primary = Color(0xFF6750A4)
val md_theme_light_onPrimary = Color(0xFFFFFFFF)
val md_theme_light_primaryContainer = Color(0xFFEADDFF)
val md_theme_light_onPrimaryContainer = Color(0xFF21005D)
val md_theme_light_secondary = Color(0xFF625B71)
val md_theme_light_onSecondary = Color(0xFFFFFFFF)
val md_theme_light_secondaryContainer = Color(0xFFE8DEF8)
val md_theme_light_onSecondaryContainer = Color(0xFF1D192B)
val md_theme_light_tertiary = Color(0xFF7D5260)
val md_theme_light_onTertiary = Color(0xFFFFFFFF)
val md_theme_light_tertiaryContainer = Color(0xFFFFD8E4)
val md_theme_light_onTertiaryContainer = Color(0xFF31111D)
val md_theme_light_error = Color(0xFFB3261E)
val md_theme_light_errorContainer = Color(0xFFF9DEDC)
val md_theme_light_onError = Color(0xFFFFFFFF)
val md_theme_light_onErrorContainer = Color(0xFF410E0B)
val md_theme_light_background = Color(0xFFFFFBFE)
val md_theme_light_onBackground = Color(0xFF1C1B1F)
val md_theme_light_surface = Color(0xFFFFFBFE)
val md_theme_light_onSurface = Color(0xFF1C1B1F)
val md_theme_light_surfaceVariant = Color(0xFFE7E0EC)
val md_theme_light_onSurfaceVariant = Color(0xFF49454F)
val md_theme_light_outline = Color(0xFF79747E)
val md_theme_light_inverseOnSurface = Color(0xFFF4EFF4)
val md_theme_light_inverseSurface = Color(0xFF313033)
val md_theme_light_inversePrimary = Color(0xFFD0BCFF)
val md_theme_light_surfaceTint = Color(0xFF6750A4)
val md_theme_light_outlineVariant = Color(0xFFCAC4D0)
val md_theme_light_scrim = Color(0xFF000000)

// Surface containers (M3) - tonal hierarchy for nested surfaces
val md_theme_light_surfaceContainerLowest = Color(0xFFFFFFFF)
val md_theme_light_surfaceContainerLow = Color(0xFFF7F2FA)
val md_theme_light_surfaceContainer = Color(0xFFF3EDF7)
val md_theme_light_surfaceContainerHigh = Color(0xFFECE6F0)
val md_theme_light_surfaceContainerHighest = Color(0xFFE6E0E9)
val md_theme_light_surfaceDim = Color(0xFFDED8E1)
val md_theme_light_surfaceBright = Color(0xFFFEF7FF)

// Fixed accent roles (M3) - same color in light and dark
val md_theme_primaryFixed = Color(0xFFEADDFF)
val md_theme_primaryFixedDim = Color(0xFFD0BCFF)
val md_theme_onPrimaryFixed = Color(0xFF21005D)
val md_theme_onPrimaryFixedVariant = Color(0xFF4F378B)
val md_theme_secondaryFixed = Color(0xFFE8DEF8)
val md_theme_secondaryFixedDim = Color(0xFFCCC2DC)
val md_theme_onSecondaryFixed = Color(0xFF1D192B)
val md_theme_onSecondaryFixedVariant = Color(0xFF4A4458)
val md_theme_tertiaryFixed = Color(0xFFFFD8E4)
val md_theme_tertiaryFixedDim = Color(0xFFEFB8C8)
val md_theme_onTertiaryFixed = Color(0xFF31111D)
val md_theme_onTertiaryFixedVariant = Color(0xFF633B48)

// Dark theme colors
val md_theme_dark_primary = Color(0xFFD0BCFF)
val md_theme_dark_onPrimary = Color(0xFF381E72)
val md_theme_dark_primaryContainer = Color(0xFF4F378B)
val md_theme_dark_onPrimaryContainer = Color(0xFFEADDFF)
val md_theme_dark_secondary = Color(0xFFCCC2DC)
val md_theme_dark_onSecondary = Color(0xFF332D41)
val md_theme_dark_secondaryContainer = Color(0xFF4A4458)
val md_theme_dark_onSecondaryContainer = Color(0xFFE8DEF8)
val md_theme_dark_tertiary = Color(0xFFEFB8C8)
val md_theme_dark_onTertiary = Color(0xFF492532)
val md_theme_dark_tertiaryContainer = Color(0xFF633B48)
val md_theme_dark_onTertiaryContainer = Color(0xFFFFD8E4)
val md_theme_dark_error = Color(0xFFF2B8B5)
val md_theme_dark_errorContainer = Color(0xFF8C1D18)
val md_theme_dark_onError = Color(0xFF601410)
val md_theme_dark_onErrorContainer = Color(0xFFF9DEDC)
val md_theme_dark_background = Color(0xFF1C1B1F)
val md_theme_dark_onBackground = Color(0xFFE6E1E5)
val md_theme_dark_surface = Color(0xFF1C1B1F)
val md_theme_dark_onSurface = Color(0xFFE6E1E5)
val md_theme_dark_surfaceVariant = Color(0xFF49454F)
val md_theme_dark_onSurfaceVariant = Color(0xFFCAC4D0)
val md_theme_dark_outline = Color(0xFF938F99)
val md_theme_dark_inverseOnSurface = Color(0xFF1C1B1F)
val md_theme_dark_inverseSurface = Color(0xFFE6E1E5)
val md_theme_dark_inversePrimary = Color(0xFF6750A4)
val md_theme_dark_surfaceTint = Color(0xFFD0BCFF)
val md_theme_dark_outlineVariant = Color(0xFF49454F)
val md_theme_dark_scrim = Color(0xFF000000)

// Surface containers (M3) - tonal hierarchy for nested surfaces
val md_theme_dark_surfaceContainerLowest = Color(0xFF0F0D13)
val md_theme_dark_surfaceContainerLow = Color(0xFF1D1B20)
val md_theme_dark_surfaceContainer = Color(0xFF211F26)
val md_theme_dark_surfaceContainerHigh = Color(0xFF2B2930)
val md_theme_dark_surfaceContainerHighest = Color(0xFF36343B)
val md_theme_dark_surfaceDim = Color(0xFF141218)
val md_theme_dark_surfaceBright = Color(0xFF3B383E)

val LightColorScheme = lightColorScheme(
    primary = md_theme_light_primary,
    onPrimary = md_theme_light_onPrimary,
    primaryContainer = md_theme_light_primaryContainer,
    onPrimaryContainer = md_theme_light_onPrimaryContainer,
    secondary = md_theme_light_secondary,
    onSecondary = md_theme_light_onSecondary,
    secondaryContainer = md_theme_light_secondaryContainer,
    onSecondaryContainer = md_theme_light_onSecondaryContainer,
    tertiary = md_theme_light_tertiary,
    onTertiary = md_theme_light_onTertiary,
    tertiaryContainer = md_theme_light_tertiaryContainer,
    onTertiaryContainer = md_theme_light_onTertiaryContainer,
    error = md_theme_light_error,
    errorContainer = md_theme_light_errorContainer,
    onError = md_theme_light_onError,
    onErrorContainer = md_theme_light_onErrorContainer,
    background = md_theme_light_background,
    onBackground = md_theme_light_onBackground,
    surface = md_theme_light_surface,
    onSurface = md_theme_light_onSurface,
    surfaceVariant = md_theme_light_surfaceVariant,
    onSurfaceVariant = md_theme_light_onSurfaceVariant,
    outline = md_theme_light_outline,
    inverseOnSurface = md_theme_light_inverseOnSurface,
    inverseSurface = md_theme_light_inverseSurface,
    inversePrimary = md_theme_light_inversePrimary,
    surfaceTint = md_theme_light_surfaceTint,
    outlineVariant = md_theme_light_outlineVariant,
    scrim = md_theme_light_scrim,
    surfaceContainerLowest = md_theme_light_surfaceContainerLowest,
    surfaceContainerLow = md_theme_light_surfaceContainerLow,
    surfaceContainer = md_theme_light_surfaceContainer,
    surfaceContainerHigh = md_theme_light_surfaceContainerHigh,
    surfaceContainerHighest = md_theme_light_surfaceContainerHighest,
    surfaceDim = md_theme_light_surfaceDim,
    surfaceBright = md_theme_light_surfaceBright,
    primaryFixed = md_theme_primaryFixed,
    primaryFixedDim = md_theme_primaryFixedDim,
    onPrimaryFixed = md_theme_onPrimaryFixed,
    onPrimaryFixedVariant = md_theme_onPrimaryFixedVariant,
    secondaryFixed = md_theme_secondaryFixed,
    secondaryFixedDim = md_theme_secondaryFixedDim,
    onSecondaryFixed = md_theme_onSecondaryFixed,
    onSecondaryFixedVariant = md_theme_onSecondaryFixedVariant,
    tertiaryFixed = md_theme_tertiaryFixed,
    tertiaryFixedDim = md_theme_tertiaryFixedDim,
    onTertiaryFixed = md_theme_onTertiaryFixed,
    onTertiaryFixedVariant = md_theme_onTertiaryFixedVariant
)

val DarkColorScheme = darkColorScheme(
    primary = md_theme_dark_primary,
    onPrimary = md_theme_dark_onPrimary,
    primaryContainer = md_theme_dark_primaryContainer,
    onPrimaryContainer = md_theme_dark_onPrimaryContainer,
    secondary = md_theme_dark_secondary,
    onSecondary = md_theme_dark_onSecondary,
    secondaryContainer = md_theme_dark_secondaryContainer,
    onSecondaryContainer = md_theme_dark_onSecondaryContainer,
    tertiary = md_theme_dark_tertiary,
    onTertiary = md_theme_dark_onTertiary,
    tertiaryContainer = md_theme_dark_tertiaryContainer,
    onTertiaryContainer = md_theme_dark_onTertiaryContainer,
    error = md_theme_dark_error,
    errorContainer = md_theme_dark_errorContainer,
    onError = md_theme_dark_onError,
    onErrorContainer = md_theme_dark_onErrorContainer,
    background = md_theme_dark_background,
    onBackground = md_theme_dark_onBackground,
    surface = md_theme_dark_surface,
    onSurface = md_theme_dark_onSurface,
    surfaceVariant = md_theme_dark_surfaceVariant,
    onSurfaceVariant = md_theme_dark_onSurfaceVariant,
    outline = md_theme_dark_outline,
    inverseOnSurface = md_theme_dark_inverseOnSurface,
    inverseSurface = md_theme_dark_inverseSurface,
    inversePrimary = md_theme_dark_inversePrimary,
    surfaceTint = md_theme_dark_surfaceTint,
    outlineVariant = md_theme_dark_outlineVariant,
    scrim = md_theme_dark_scrim,
    surfaceContainerLowest = md_theme_dark_surfaceContainerLowest,
    surfaceContainerLow = md_theme_dark_surfaceContainerLow,
    surfaceContainer = md_theme_dark_surfaceContainer,
    surfaceContainerHigh = md_theme_dark_surfaceContainerHigh,
    surfaceContainerHighest = md_theme_dark_surfaceContainerHighest,
    surfaceDim = md_theme_dark_surfaceDim,
    surfaceBright = md_theme_dark_surfaceBright,
    primaryFixed = md_theme_primaryFixed,
    primaryFixedDim = md_theme_primaryFixedDim,
    onPrimaryFixed = md_theme_onPrimaryFixed,
    onPrimaryFixedVariant = md_theme_onPrimaryFixedVariant,
    secondaryFixed = md_theme_secondaryFixed,
    secondaryFixedDim = md_theme_secondaryFixedDim,
    onSecondaryFixed = md_theme_onSecondaryFixed,
    onSecondaryFixedVariant = md_theme_onSecondaryFixedVariant,
    tertiaryFixed = md_theme_tertiaryFixed,
    tertiaryFixedDim = md_theme_tertiaryFixedDim,
    onTertiaryFixed = md_theme_onTertiaryFixed,
    onTertiaryFixedVariant = md_theme_onTertiaryFixedVariant
)
```

### Generating Custom Color Schemes

Use Material Theme Builder to generate custom schemes:

1. Visit [Material Theme Builder](https://m3.material.io/theme-builder)
2. Select your brand color
3. Export as Compose (Kotlin)
4. Replace the color values in `Color.kt`

### Using Colors in Composables

Always use semantic color roles from `MaterialTheme.colorScheme`:

```kotlin
@Composable
fun ProfileCard(user: User) {
    Card(
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant,
            contentColor = MaterialTheme.colorScheme.onSurfaceVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = user.name,
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = user.email,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
```

## Color Pairing Rules

Every M3 color role has an `on*` partner that is contrast-tuned for it. Mixing partners - `onPrimary` over `surface`, `onSurface` over `primaryContainer` - silently breaks WCAG, dark mode, dynamic color, and user contrast all at once. The rule is mechanical: **pick a container role, then use its `on*` for everything drawn on top.**

### The pairing table

| Container / fill role              | Content / `on*` role                                                       | Typical use                           |
|------------------------------------|----------------------------------------------------------------------------|---------------------------------------|
| `primary`                          | `onPrimary`                                                                | Filled button, FAB                    |
| `primaryContainer`                 | `onPrimaryContainer`                                                       | Selected chip, hero card              |
| `secondary` / `secondaryContainer` | `onSecondary` / `onSecondaryContainer`                                     | Tonal button, filter chip             |
| `tertiary` / `tertiaryContainer`   | `onTertiary` / `onTertiaryContainer`                                       | Badge, complementary surface          |
| `error` / `errorContainer`         | `onError` / `onErrorContainer`                                             | Destructive action, error banner      |
| `surface` / `surfaceContainer*`    | `onSurface` (titles), `onSurfaceVariant` (secondary text, icons, dividers) | Most app content                      |
| `inverseSurface`                   | `inverseOnSurface`                                                         | Snackbar, tooltip                     |
| `*Fixed` / `*FixedDim`             | `on*Fixed` / `on*FixedVariant`                                             | Cross-mode media controls (see below) |

### Compose: pair containers and content explicitly

```kotlin
@Composable
fun PairedSurfaces() {
    Surface(
        color = MaterialTheme.colorScheme.primaryContainer,
        contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
        shape = MaterialTheme.shapes.medium,
    ) {
        Column(Modifier.padding(16.dp)) {
            Text("Hero card", style = MaterialTheme.typography.titleMedium)
            Text(
                text = "Auto-inherits onPrimaryContainer via LocalContentColor",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
```

Setting `Surface(contentColor = ...)` updates `LocalContentColor` so `Text`, `Icon`, and `IconButton` inside pick the right partner automatically - that's the idiomatic way to enforce pairing without naming colors at every `Text` call.

### Title vs supporting text on surfaces

On any `surface` / `surfaceContainer*` role, use **two** content roles, not one:

- `onSurface` for primary text (titles, body copy that must read).
- `onSurfaceVariant` for secondary text, icons, dividers, placeholders, helper text.

`onSurfaceVariant` is intentionally lower-contrast - using it for body copy fails WCAG; using `onSurface` for every label flattens the visual hierarchy.

### `*Fixed` / `*FixedDim`: keep tone constant across modes

`primaryFixed` / `primaryFixedDim` keep the **same tone** in light and dark themes - useful when a surface (album art controls, an embedded media widget) must visually match across modes. Pair them with `onPrimaryFixed` (titles) and `onPrimaryFixedVariant` (supporting text), the same way `surface` pairs with `onSurface` / `onSurfaceVariant`.

### Cross-references

- These pairs are also enforced by `Card`, `Button`, `Chip`, `NavigationBar` etc. via `*Defaults.colors(...)` - see `references/compose-patterns.md`.
- Anti-patterns for breaking pairing live in [Theme routing → Forbidden](#forbidden).

## `outline` vs `outlineVariant`

M3 has two outline roles, and they are not interchangeable. Picking the wrong one is the difference between a focusable, accessible boundary and a decorative hairline that disappears for low-vision users.

| Role             | Contrast                                | Use for                                                                                                    |
|------------------|-----------------------------------------|------------------------------------------------------------------------------------------------------------|
| `outline`        | High - meets non-text contrast (3:1)    | Interactive borders: outlined button/text field/chip, focus indicators, important dividers between regions |
| `outlineVariant` | Low - decorative, **does not** meet 3:1 | Subtle dividers between items in a list, decorative separators, disabled-state borders                     |

Rule of thumb: if a sighted user is supposed to **act on** the bordered thing, use `outline`. If the line is purely visual rhythm inside a single region, use `outlineVariant`.

### Compose: pick the role that matches the job

```kotlin
@Composable
fun OutlineDemo() {
    OutlinedTextField(
        value = "",
        onValueChange = {},
        label = { Text("Email") },
    )

    HorizontalDivider(
        color = MaterialTheme.colorScheme.outlineVariant,
    )

    Surface(
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outline),
    ) {
        Text(
            text = "Region boundary the user can tab to",
            modifier = Modifier
                .padding(16.dp)
                .focusable(),
        )
    }
}
```

`OutlinedTextField` already pulls `outline` (and `outlineVariant` for its disabled state) internally - that's the model to follow when you write your own outlined components: take `outline` for the resting interactive border, `outlineVariant` for disabled/decorative.

### Cross-references

- Anti-pattern lives in [Theme routing → Forbidden](#forbidden).
- Custom outlined components: see `references/compose-patterns.md` → component patterns.

## Surface Container Hierarchy

M3 expresses depth through **container tone**, not shadows. Pick the surface role that matches the component's job, not its visual weight. Nest by stepping **one level up** at each layer (`surface` → `surfaceContainerLow` → `surfaceContainer` → ...) so depth reads cleanly under any contrast or theme.

### Which level for what

| Container role            | Use for                                                                  |
|---------------------------|--------------------------------------------------------------------------|
| `surface`                 | Default screen background                                                |
| `surfaceContainerLowest`  | Component on a **busy** background that should recede (rare)             |
| `surfaceContainerLow`     | Cards laid out in flow on a `surface` background                         |
| `surfaceContainer`        | Persistent containers (navigation bar, side rail, bottom sheet at rest)  |
| `surfaceContainerHigh`    | Menus, scrolled top app bar, sheets while dragging                       |
| `surfaceContainerHighest` | Filled cards, deepest nested container (chip on a card on a sheet)       |
| `surfaceDim`              | Hero/empty-state surface that should always read as the dimmest area     |
| `surfaceBright`           | Hero/empty-state surface that should always read as the brightest area   |

### Compose nesting example

```kotlin
@Composable
fun NestedSurfacesDemo() {
    Surface(color = MaterialTheme.colorScheme.surface) {
        Column(modifier = Modifier.padding(16.dp)) {
            Surface(
                shape = MaterialTheme.shapes.medium,
                color = MaterialTheme.colorScheme.surfaceContainerLow,
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Card on surface",
                        color = MaterialTheme.colorScheme.onSurface,
                    )
                    Surface(
                        shape = MaterialTheme.shapes.small,
                        color = MaterialTheme.colorScheme.surfaceContainerHighest,
                        modifier = Modifier.padding(top = 12.dp)
                    ) {
                        Text(
                            text = "Chip nested inside the card",
                            color = MaterialTheme.colorScheme.onSurface,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                        )
                    }
                }
            }
        }
    }
}
```

The nested chip sits at `surfaceContainerHighest` so it stays distinguishable from the card (`surfaceContainerLow`) and the page (`surface`) regardless of light/dark, dynamic color, or user contrast.

### Avoid `surfaceVariant` for new containers

`surfaceVariant` predates the container hierarchy. Keep it only for **legacy** screens or for tinted decorative surfaces (e.g. inactive switch tracks). For any new container, pick a `surfaceContainer*` level instead.

## Tonal Elevation vs Shadows

In M3, depth is communicated through **container tone first**. Reach for a shadow only when a component must visually float over content the surface tone can't separate from (a FAB over a photo, a sheet over a busy feed). Stacking shadows for ordinary depth produces the cluttered, MD2-style look M3 was designed to retire.

### Map elevation level to surface role

| Elevation level | Tonal role                  | Components at rest                                                       |
|-----------------|-----------------------------|--------------------------------------------------------------------------|
| 0               | `surface`                   | Most resting components, top app bar (flat), filled/outlined/text button |
| 1               | `surfaceContainerLow`       | Elevated card, banner, modal bottom sheet                                |
| 2               | `surfaceContainer`          | Navigation bar, scrolled top app bar, menus, toolbar                     |
| 3               | `surfaceContainerHigh`      | FAB, dialogs, search bar, date/time pickers                              |
| 4–5             | `surfaceContainerHighest`   | Hover/focus increase only - never a resting state                        |

Setting `Surface(tonalElevation = 3.dp)` blends `surfaceTint` into `surface` to approximate level 3. **Use the explicit `surfaceContainer*` role** instead — clearer mapping, survives dynamic color and user contrast, and matches what M3 components do internally.

### Compose: prefer container role, add shadow only when needed

```kotlin
@Composable
fun ElevationDemo() {
    Surface(
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceContainer,
    ) {
        Text(
            text = "Menu surface - tone alone communicates level 2",
            color = MaterialTheme.colorScheme.onSurface,
            modifier = Modifier.padding(16.dp),
        )
    }

    Surface(
        shape = CircleShape,
        color = MaterialTheme.colorScheme.primaryContainer,
        shadowElevation = 6.dp,
    ) {
        Icon(
            imageVector = Icons.Filled.Add,
            contentDescription = "Compose",
            tint = MaterialTheme.colorScheme.onPrimaryContainer,
            modifier = Modifier.padding(16.dp),
        )
    }
}
```

The menu uses tone only. The FAB adds `shadowElevation` because it floats over arbitrary content - exactly the case where a shadow is justified.

### Hover/focus, not resting

Levels 4 and 5 are **interaction** levels. Bump elevation by **one step** on hover/focus (e.g. FAB level 3 → 4 on hover) and return to rest on release. Never ship a component at rest above level 3.

### Cross-references

- M3 Expressive components consume tonal/elevation tokens through `MaterialExpressiveTheme` and `MotionScheme.expressive()` - see [Material 3 Expressive](#material-3-expressive).
- Animation/feel of elevation transitions belongs in `references/compose-patterns.md` → "Animation".

## Dynamic Color (Material You)

Dynamic color extracts colors from the user's wallpaper (API 31+).

### Enabling Dynamic Color

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        // Dynamic color is available on API 31+ (Android 12+)
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(context)
            }
        }
        // Fallback to static color schemes
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### User Preference for Dynamic Color

Allow users to toggle dynamic colors:

```kotlin
// core/ui/theme/ThemePreference.kt
enum class ThemePreference {
    LIGHT,
    DARK,
    SYSTEM
}

data class ThemeConfig(
    val themePreference: ThemePreference = ThemePreference.SYSTEM,
    val useDynamicColor: Boolean = true
)
```

### Conditional Dynamic Color Support

```kotlin
@Composable
fun AppTheme(
    themeConfig: ThemeConfig,
    content: @Composable () -> Unit
) {
    val isDarkTheme = when (themeConfig.themePreference) {
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
    }

    val supportsDynamicColor = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
    val useDynamicColor = themeConfig.useDynamicColor && supportsDynamicColor

    val colorScheme = when {
        useDynamicColor -> {
            val context = LocalContext.current
            if (isDarkTheme) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(context)
            }
        }
        isDarkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

## User Contrast Preference (Android 14+)

Android 14 (API 34) added a system-wide **Contrast** slider in *Settings → Accessibility → Color and motion*. Users pick Standard / Medium / High, and the OS exposes the result via `UiModeManager.getContrast()` returning a `Float`:

| `getContrast()` value | Setting  | Use the scheme variant                         |
|-----------------------|----------|------------------------------------------------|
| `0.0f`                | Standard | Default `LightColorScheme` / `DarkColorScheme` |
| `0.5f`                | Medium   | Medium-contrast variant                        |
| `1.0f`                | High     | High-contrast variant                          |

Honoring the OS contrast choice is a low-cost M3 accessibility win: read `getContrast()` and select the matching scheme variant.

### Generate the contrast scheme variants

Use [Material Theme Builder](https://m3.material.io/theme-builder) → **Export** → it ships six schemes: `Light`, `LightMediumContrast`, `LightHighContrast`, `Dark`, `DarkMediumContrast`, `DarkHighContrast`. Drop them into `Color.kt` next to the existing pair.

### Compose helper: read contrast reactively

`UiModeManager.getContrast()` is API 34+ only, and the value can change while the app is foregrounded (user toggles the slider). Listen to `UiModeManager.ContrastChangeListener` and surface it through state.

```kotlin
import android.app.UiModeManager
import android.content.Context
import android.os.Build
import androidx.annotation.RequiresApi
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.getSystemService

enum class ContrastLevel { Standard, Medium, High }

@Composable
fun rememberContrastLevel(): ContrastLevel {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
        return ContrastLevel.Standard
    }
    val context = LocalContext.current
    val uiModeManager = remember(context) { context.getSystemService<UiModeManager>()!! }
    var level by remember { mutableStateOf(uiModeManager.contrastLevel()) }

    DisposableEffect(uiModeManager) {
        val executor = ContextCompat.getMainExecutor(context)
        val listener = UiModeManager.ContrastChangeListener { level = uiModeManager.contrastLevel() }
        uiModeManager.addContrastChangeListener(executor, listener)
        onDispose { uiModeManager.removeContrastChangeListener(listener) }
    }
    return level
}

@RequiresApi(Build.VERSION_CODES.UPSIDE_DOWN_CAKE)
private fun UiModeManager.contrastLevel(): ContrastLevel = when {
    contrast >= 0.75f -> ContrastLevel.High
    contrast >= 0.25f -> ContrastLevel.Medium
    else              -> ContrastLevel.Standard
}
```

The bucket boundaries (`0.25` / `0.75`) are intentional - the API is documented to return `0.0` / `0.5` / `1.0` today, but bucketing leaves room for future intermediate values without breaking the picker.

### Plug into `AppTheme`

Slot the contrast pick into the same `colorScheme` decision tree from [Conditional Dynamic Color Support](#conditional-dynamic-color-support) - pick the static variant that matches `(isDark, contrast)`. With **dynamic color**, `dynamicLightColorScheme(context)` / `dynamicDarkColorScheme(context)` already honor the user contrast on API 34+, so leave them alone.

```kotlin
@Composable
fun AppTheme(
    themeConfig: ThemeConfig,
    content: @Composable () -> Unit,
) {
    val isDarkTheme = when (themeConfig.themePreference) {
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
    }
    val dynamicColorActive =
        themeConfig.useDynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
    val contrast = rememberContrastLevel()

    val colorScheme = when {
        dynamicColorActive -> {
            val context = LocalContext.current
            if (isDarkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        isDarkTheme -> when (contrast) {
            ContrastLevel.High     -> DarkHighContrastColorScheme
            ContrastLevel.Medium   -> DarkMediumContrastColorScheme
            ContrastLevel.Standard -> DarkColorScheme
        }
        else -> when (contrast) {
            ContrastLevel.High     -> LightHighContrastColorScheme
            ContrastLevel.Medium   -> LightMediumContrastColorScheme
            ContrastLevel.Standard -> LightColorScheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content,
    )
}
```

### What this does **not** replace

User contrast scales the **color scheme**. It is not a substitute for:

- WCAG contrast checks on hard-coded brand colors (still required - see `references/android-accessibility.md`).
- A larger-text / display-density preference (those are separate system settings).
- Honoring user font scale (`fontScale` in `Configuration`) - that affects typography, not color.

### Testing

`adb shell settings put secure contrast_level 0.5` toggles the system value without going through the slider. Pair with the existing dark-mode preview pattern:

```kotlin
@Preview(name = "Light · Standard")
@Preview(name = "Light · Medium",  group = "contrast")
@Preview(name = "Light · High",    group = "contrast")
@Preview(name = "Dark · Standard", uiMode = Configuration.UI_MODE_NIGHT_YES)
@Preview(name = "Dark · High",     uiMode = Configuration.UI_MODE_NIGHT_YES, group = "contrast")
```

Previews can't read the live `UiModeManager`, so wrap your composable in a small test theme that takes `ContrastLevel` as a parameter.

## Typography Scales

Material 3 provides predefined typography scales.

### Default Typography

```kotlin
// core/ui/theme/Type.kt
package com.example.core.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// Custom font family (optional)
val Roboto = FontFamily(
    Font(R.font.roboto_regular, FontWeight.Normal),
    Font(R.font.roboto_medium, FontWeight.Medium),
    Font(R.font.roboto_bold, FontWeight.Bold)
)

val AppTypography = Typography(
    // Display styles - largest text
    displayLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 57.sp,
        lineHeight = 64.sp,
        letterSpacing = (-0.25).sp
    ),
    displayMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 45.sp,
        lineHeight = 52.sp,
        letterSpacing = 0.sp
    ),
    displaySmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 36.sp,
        lineHeight = 44.sp,
        letterSpacing = 0.sp
    ),
    
    // Headline styles
    headlineLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 32.sp,
        lineHeight = 40.sp,
        letterSpacing = 0.sp
    ),
    headlineMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 28.sp,
        lineHeight = 36.sp,
        letterSpacing = 0.sp
    ),
    headlineSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 24.sp,
        lineHeight = 32.sp,
        letterSpacing = 0.sp
    ),
    
    // Title styles
    titleLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 22.sp,
        lineHeight = 28.sp,
        letterSpacing = 0.sp
    ),
    titleMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.15.sp
    ),
    titleSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    
    // Body styles
    bodyLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        lineHeight = 24.sp,
        letterSpacing = 0.5.sp
    ),
    bodyMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.25.sp
    ),
    bodySmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.4.sp
    ),
    
    // Label styles
    labelLarge = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 14.sp,
        lineHeight = 20.sp,
        letterSpacing = 0.1.sp
    ),
    labelMedium = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 12.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    ),
    labelSmall = TextStyle(
        fontFamily = Roboto,
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        lineHeight = 16.sp,
        letterSpacing = 0.5.sp
    )
)
```

### Using Typography

```kotlin
@Composable
fun ArticleScreen(article: Article) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Use display for hero text
        Text(
            text = article.title,
            style = MaterialTheme.typography.displayMedium,
            color = MaterialTheme.colorScheme.onSurface
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        // Use body for content
        Text(
            text = article.content,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Use label for metadata
        Text(
            text = "By ${article.author}",
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
```

### Android 16 (API 36) Font Changes

Android 16 deprecates and disables the `elegantTextHeight` `TextView` attribute. The "UI fonts" controlled by this API are discontinued. Apps targeting API 36 must ensure layouts render correctly with the default readable font rendering for Arabic, Lao, Myanmar, Tamil, Gujarati, Kannada, Malayalam, Odia, Telugu, and Thai scripts.

**What changed:**
- In Android 15 (API 35), `elegantTextHeight` defaulted to `true`, replacing compact fonts with more readable ones
- In Android 16 (API 36), the attribute is ignored entirely -- readable fonts are always used
- Any layouts that relied on `elegantTextHeight = false` for compact rendering must be adapted

**Action required:**
- Remove any `elegantTextHeight` attribute usage from XML layouts and styles
- Do **not** set `elegantTextHeight` programmatically -- it has no effect on API 36
- Test text rendering for the affected scripts listed above and adjust layout spacing if needed
- Use Compose `Text` composables with `MaterialTheme.typography` scales (no `elegantTextHeight` concept in Compose)

### Adding Custom Fonts

Add fonts to `res/font/`:

```
res/
  font/
    roboto_regular.ttf
    roboto_medium.ttf
    roboto_bold.ttf
```

## Shape Theming

Material 3 uses four shape scales: Extra Small, Small, Medium, Large, Extra Large.

### Default Shapes

```kotlin
// core/ui/theme/Shape.kt
package com.example.core.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

val AppShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(28.dp)
)
```

### Custom Shape Scales

For more rounded or angular designs:

```kotlin
// Rounded design
val RoundedShapes = Shapes(
    extraSmall = RoundedCornerShape(8.dp),
    small = RoundedCornerShape(12.dp),
    medium = RoundedCornerShape(16.dp),
    large = RoundedCornerShape(20.dp),
    extraLarge = RoundedCornerShape(32.dp)
)

// Angular design
val AngularShapes = Shapes(
    extraSmall = RoundedCornerShape(2.dp),
    small = RoundedCornerShape(4.dp),
    medium = RoundedCornerShape(6.dp),
    large = RoundedCornerShape(8.dp),
    extraLarge = RoundedCornerShape(12.dp)
)
```

### Using Shapes

Components automatically use the correct shape from the theme:

```kotlin
@Composable
fun ProductCard(product: Product) {
    // Card automatically uses medium shape
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Image with large shape
            AsyncImage(
                model = product.imageUrl,
                contentDescription = product.name,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(200.dp)
                    .clip(MaterialTheme.shapes.large)
            )
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Text(
                text = product.name,
                style = MaterialTheme.typography.titleLarge
            )
            
            // Button uses large shape by default
            Button(
                onClick = { /* Add to cart */ },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Add to Cart")
            }
        }
    }
}
```

## Material 3 Expressive

Material 3 Expressive is the 2025+ refresh of Material 3. It adds a **motion scheme**, expressive color tokens, and shape/typography updates. In Compose it is exposed via `MaterialExpressiveTheme` and sibling color-scheme builders.

### Status

- API lives in `androidx.compose.material3` and is marked `@ExperimentalMaterial3ExpressiveApi`.
- Shipped in `androidx.compose.material3:material3:1.5.0-alpha16` and later.
- The pinned catalog version (`material3` in `assets/libs.versions.toml.template`) gates availability. On stable 1.4.x, Expressive APIs are **not** available; keep `MaterialTheme` as the canonical entry point.
- Do not mix `MaterialTheme` and `MaterialExpressiveTheme` in the same tree. Pick one per Activity/Composable root.

### Opt-in

Enable the opt-in at the file or module level:

```kotlin
@file:OptIn(ExperimentalMaterial3ExpressiveApi::class)
```

Module-wide (library modules, not `:app` per `references/kotlin-patterns.md`):

```kotlin
// build.gradle.kts (module)
kotlin {
    compilerOptions {
        optIn.add("androidx.compose.material3.ExperimentalMaterial3ExpressiveApi")
    }
}
```

### Wiring

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val context = LocalContext.current
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        darkTheme -> expressiveDarkColorScheme()
        else -> expressiveLightColorScheme()
    }

    MaterialExpressiveTheme(
        colorScheme = colorScheme,
        motionScheme = MotionScheme.expressive(),
        typography = Typography,
        shapes = Shapes,
        content = content
    )
}
```

### What changes vs `MaterialTheme`

| Slot       | `MaterialTheme`                            | `MaterialExpressiveTheme`                                      |
|------------|--------------------------------------------|----------------------------------------------------------------|
| Color      | `lightColorScheme()` / `darkColorScheme()` | `expressiveLightColorScheme()` / `expressiveDarkColorScheme()` |
| Motion     | Not a theme slot; per-component defaults   | `MotionScheme.expressive()` / `MotionScheme.standard()`        |
| Typography | `Typography`                               | Same `Typography` slot; expressive defaults differ             |
| Shapes     | `Shapes`                                   | Same `Shapes` slot; expressive defaults use larger corners     |

The `motionScheme` slot is the distinguishing feature: it centralises duration and easing tokens that Material 3 components (FAB, dialogs, switches, segmented buttons) pick up automatically.

### When to adopt

- Adopt when the catalog's `material3` is pinned to a version that ships the API as stable, or when the product explicitly signs off on using an experimental API.
- Until then, use stable `MaterialTheme` plus the token overrides shown above. Migration path: swap `MaterialTheme(...)` for `MaterialExpressiveTheme(...)` and add a `MotionScheme` argument.

## Dark/Light Mode Switching

### System Default

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### User-Controlled Theme

```kotlin
@Composable
fun AppTheme(
    themePreference: ThemePreference,
    useDynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val isDarkTheme = when (themePreference) {
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
    }

    val colorScheme = when {
        useDynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (isDarkTheme) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(context)
            }
        }
        isDarkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        shapes = AppShapes,
        content = content
    )
}
```

### Theme Switcher UI

```kotlin
@Composable
fun ThemeSettingsScreen(
    currentTheme: ThemePreference,
    useDynamicColor: Boolean,
    onThemeChange: (ThemePreference) -> Unit,
    onDynamicColorChange: (Boolean) -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        Text(
            text = "Theme Settings",
            style = MaterialTheme.typography.headlineMedium
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Theme selection
        Text(
            text = "Appearance",
            style = MaterialTheme.typography.titleMedium
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        ThemePreference.entries.forEach { preference ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .selectable(
                        selected = currentTheme == preference,
                        onClick = { onThemeChange(preference) },
                        role = Role.RadioButton
                    )
                    .padding(vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                RadioButton(
                    selected = currentTheme == preference,
                    onClick = null
                )
                Spacer(modifier = Modifier.width(16.dp))
                Text(
                    text = when (preference) {
                        ThemePreference.LIGHT -> "Light"
                        ThemePreference.DARK -> "Dark"
                        ThemePreference.SYSTEM -> "System default"
                    },
                    style = MaterialTheme.typography.bodyLarge
                )
            }
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Dynamic color toggle (API 31+)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .toggleable(
                        value = useDynamicColor,
                        onValueChange = onDynamicColorChange,
                        role = Role.Switch
                    )
                    .padding(vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Dynamic colors",
                        style = MaterialTheme.typography.bodyLarge
                    )
                    Text(
                        text = "Use colors from your wallpaper",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(
                    checked = useDynamicColor,
                    onCheckedChange = null
                )
            }
        }
    }
}
```

## Theme Preferences

### DataStore Implementation

```kotlin
// core/data/preferences/ThemePreferencesDataSource.kt
package com.example.core.data.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.example.core.ui.theme.ThemeConfig
import com.example.core.ui.theme.ThemePreference
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(
    name = "theme_preferences"
)

@Singleton
class ThemePreferencesDataSource @Inject constructor(
    @ApplicationContext private val context: Context
) {
    private object PreferencesKeys {
        val THEME_PREFERENCE = stringPreferencesKey("theme_preference")
        val USE_DYNAMIC_COLOR = booleanPreferencesKey("use_dynamic_color")
    }

    val themeConfig: Flow<ThemeConfig> = context.dataStore.data.map { preferences ->
        val themePreference = preferences[PreferencesKeys.THEME_PREFERENCE]?.let {
            ThemePreference.valueOf(it)
        } ?: ThemePreference.SYSTEM
        
        val useDynamicColor = preferences[PreferencesKeys.USE_DYNAMIC_COLOR] ?: true

        ThemeConfig(
            themePreference = themePreference,
            useDynamicColor = useDynamicColor
        )
    }

    suspend fun setThemePreference(preference: ThemePreference) {
        context.dataStore.edit { preferences ->
            preferences[PreferencesKeys.THEME_PREFERENCE] = preference.name
        }
    }

    suspend fun setUseDynamicColor(useDynamicColor: Boolean) {
        context.dataStore.edit { preferences ->
            preferences[PreferencesKeys.USE_DYNAMIC_COLOR] = useDynamicColor
        }
    }
}
```

### Repository

```kotlin
// core/domain/ThemeRepository.kt
package com.example.core.domain

import com.example.core.ui.theme.ThemeConfig
import com.example.core.ui.theme.ThemePreference
import kotlinx.coroutines.flow.Flow

interface ThemeRepository {
    val themeConfig: Flow<ThemeConfig>
    suspend fun setThemePreference(preference: ThemePreference)
    suspend fun setUseDynamicColor(useDynamicColor: Boolean)
}
```

```kotlin
// core/data/ThemeRepositoryImpl.kt
package com.example.core.data

import com.example.core.data.preferences.ThemePreferencesDataSource
import com.example.core.domain.ThemeRepository
import com.example.core.ui.theme.ThemeConfig
import com.example.core.ui.theme.ThemePreference
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ThemeRepositoryImpl @Inject constructor(
    private val themePreferencesDataSource: ThemePreferencesDataSource
) : ThemeRepository {

    override val themeConfig: Flow<ThemeConfig> = 
        themePreferencesDataSource.themeConfig

    override suspend fun setThemePreference(preference: ThemePreference) {
        themePreferencesDataSource.setThemePreference(preference)
    }

    override suspend fun setUseDynamicColor(useDynamicColor: Boolean) {
        themePreferencesDataSource.setUseDynamicColor(useDynamicColor)
    }
}
```

### Hilt Module

```kotlin
// core/di/ThemeModule.kt
package com.example.core.di

import com.example.core.data.ThemeRepositoryImpl
import com.example.core.domain.ThemeRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
abstract class ThemeModule {
    @Binds
    abstract fun bindThemeRepository(
        impl: ThemeRepositoryImpl
    ): ThemeRepository
}
```

## Custom Theme Attributes

### Extended Color Scheme

Add custom colors beyond Material 3's default palette:

```kotlin
// core/ui/theme/ExtendedColors.kt
package com.example.core.ui.theme

import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

@Immutable
data class ExtendedColors(
    val success: Color,
    val onSuccess: Color,
    val warning: Color,
    val onWarning: Color,
    val info: Color,
    val onInfo: Color
)

val LightExtendedColors = ExtendedColors(
    success = Color(0xFF4CAF50),
    onSuccess = Color(0xFFFFFFFF),
    warning = Color(0xFFFFC107),
    onWarning = Color(0xFF000000),
    info = Color(0xFF2196F3),
    onInfo = Color(0xFFFFFFFF)
)

val DarkExtendedColors = ExtendedColors(
    success = Color(0xFF81C784),
    onSuccess = Color(0xFF000000),
    warning = Color(0xFFFFD54F),
    onWarning = Color(0xFF000000),
    info = Color(0xFF64B5F6),
    onInfo = Color(0xFF000000)
)

val LocalExtendedColors = staticCompositionLocalOf { LightExtendedColors }
```

### Providing Extended Colors

```kotlin
// core/ui/theme/Theme.kt
@Composable
fun AppTheme(
    themeConfig: ThemeConfig,
    content: @Composable () -> Unit
) {
    val isDarkTheme = when (themeConfig.themePreference) {
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
    }

    val colorScheme = when {
        themeConfig.useDynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (isDarkTheme) {
                dynamicDarkColorScheme(context)
            } else {
                dynamicLightColorScheme(context)
            }
        }
        isDarkTheme -> DarkColorScheme
        else -> LightColorScheme
    }

    val extendedColors = if (isDarkTheme) {
        DarkExtendedColors
    } else {
        LightExtendedColors
    }

    CompositionLocalProvider(LocalExtendedColors provides extendedColors) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = AppTypography,
            shapes = AppShapes,
            content = content
        )
    }
}

// Extension for easy access
object AppTheme {
    val extendedColors: ExtendedColors
        @Composable
        get() = LocalExtendedColors.current
}
```

### Using Extended Colors

```kotlin
@Composable
fun StatusBadge(status: String) {
    val (backgroundColor, contentColor) = when (status) {
        "success" -> AppTheme.extendedColors.success to AppTheme.extendedColors.onSuccess
        "warning" -> AppTheme.extendedColors.warning to AppTheme.extendedColors.onWarning
        "info" -> AppTheme.extendedColors.info to AppTheme.extendedColors.onInfo
        else -> MaterialTheme.colorScheme.surface to MaterialTheme.colorScheme.onSurface
    }

    Surface(
        color = backgroundColor,
        shape = MaterialTheme.shapes.small,
        modifier = Modifier.padding(4.dp)
    ) {
        Text(
            text = status.uppercase(),
            color = contentColor,
            style = MaterialTheme.typography.labelSmall,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}
```

### Brand Color Harmonization

Hard-coded brand colors (`success`, `warning`, `info`, an "always-red" notification dot, a partner logo tint) clash visibly when [dynamic color](#dynamic-color-material-you) repaints the rest of the app from the user's wallpaper. M3 ships a fix: `MaterialColors.harmonize(...)` shifts a custom color's **hue** toward `colorScheme.primary` while preserving its **chroma and tone**, so `success` still reads as green and `warning` as yellow without fighting the wallpaper palette.

Add the dependency once in `build.gradle.kts`:

```kotlin
implementation("com.google.android.material:material:1.12.0")
```

#### Harmonize once when the scheme is built

`harmonize` is a pure color-math call. Run it where you build `ExtendedColors` so every consumer sees harmonized values automatically - never call it inside `Composable`s that recompose on every frame.

```kotlin
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import com.google.android.material.color.MaterialColors

private fun Color.harmonizeWith(primary: Color): Color =
    Color(MaterialColors.harmonize(this.toArgb(), primary.toArgb()))

@Composable
fun rememberHarmonizedExtendedColors(
    base: ExtendedColors,
    primary: Color = MaterialTheme.colorScheme.primary,
): ExtendedColors = remember(base, primary) {
    base.copy(
        success = base.success.harmonizeWith(primary),
        warning = base.warning.harmonizeWith(primary),
        info    = base.info.harmonizeWith(primary),
    )
}
```

`on*` partners stay as-is - they're chosen for contrast against the harmonized fill, and the fill's hue shift is too small to flip which on-color you need.

#### Plug into `AppTheme`

Replace the static `extendedColors` lookup in `AppTheme` with the harmonized version, but **only when dynamic color is actually active**. With the static `LightColorScheme` / `DarkColorScheme` there's nothing to harmonize against, so skip the cost.

```kotlin
@Composable
fun AppTheme(
    themeConfig: ThemeConfig,
    content: @Composable () -> Unit,
) {
    val isDarkTheme = when (themeConfig.themePreference) {
        ThemePreference.LIGHT -> false
        ThemePreference.DARK -> true
        ThemePreference.SYSTEM -> isSystemInDarkTheme()
    }

    val dynamicColorActive =
        themeConfig.useDynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S

    val colorScheme = when {
        dynamicColorActive -> {
            val context = LocalContext.current
            if (isDarkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        isDarkTheme -> DarkColorScheme
        else        -> LightColorScheme
    }

    val baseExtended = if (isDarkTheme) DarkExtendedColors else LightExtendedColors
    val extendedColors = if (dynamicColorActive) {
        rememberHarmonizedExtendedColors(baseExtended, colorScheme.primary)
    } else {
        baseExtended
    }

    CompositionLocalProvider(LocalExtendedColors provides extendedColors) {
        MaterialTheme(
            colorScheme = colorScheme,
            typography = AppTypography,
            shapes = AppShapes,
            content = content,
        )
    }
}
```

#### When to harmonize, when not to

- **Harmonize**: brand accents (`success`, `warning`, `info`), partner-tinted illustrations, a custom `notification` color, third-party SDK accent overrides.
- **Do not harmonize**: `error` (already part of `colorScheme`, must stay unmistakably red), pure neutrals (white, black, grays), brand colors with **legal/identity constraints** where the exact hex matters (logos, regulated marks).
- For static-only apps (no dynamic color anywhere), there's nothing to harmonize against - skip it entirely and keep the original brand values.

## Scoped Themes

Sometimes a single screen needs its own slice of theming - a settings *Danger Zone* whose primary is `error`, an "on-media" toolbar that sits over a dark hero image, an embedded brand surface inside a partner section. The right tool is **a nested `MaterialTheme`** that derives from the outer one with `colorScheme.copy(...)`. This keeps dynamic color, user contrast, and dark mode intact for the rest of the app while overriding only the roles you actually care about.

### Rule: `copy()` from the outer scheme, never rebuild

Always start from `MaterialTheme.colorScheme` and `.copy(...)` the roles you want to change. Re-instantiating `lightColorScheme(...)` from scratch silently throws away the user's dynamic palette and contrast pick.

```kotlin
@Composable
fun ErrorScope(content: @Composable () -> Unit) {
    val outer = MaterialTheme.colorScheme
    MaterialTheme(
        colorScheme = outer.copy(
            primary           = outer.error,
            onPrimary         = outer.onError,
            primaryContainer  = outer.errorContainer,
            onPrimaryContainer = outer.onErrorContainer,
        ),
        typography = MaterialTheme.typography,
        shapes     = MaterialTheme.shapes,
        content    = content,
    )
}

@Composable
fun DangerZone() {
    ErrorScope {
        Button(onClick = { /* ... */ }) {
            Text("Delete account")
        }
    }
}
```

The `Button` reads `colorScheme.primary` like any other M3 component; inside `ErrorScope` that role maps to `error`. No custom `ButtonColors`, no per-component overrides, no leakage outside the `ErrorScope` block.

### Common scoped-theme patterns

- **Destructive scope**: map `primary` → `error`, `primaryContainer` → `errorContainer` (above). Wrap the dangerous CTA only, not the whole screen.
- **On-media scope**: a toolbar over a photo can switch to `inverseSurface` / `inverseOnSurface` so icons stay legible regardless of the underlying image.
- **Brand-tinted section**: an embedded partner area can swap `primary` and `secondary` for the partner's harmonized brand color, keeping the surface hierarchy intact.
- **Forced light/dark**: a media player that should always render dark UI can pass a frozen dark `colorScheme` to its subtree without touching the rest of the app.

### Don'ts

- **Don't scope shapes or typography** unless the design genuinely diverges — those tokens rebuild the visual identity beyond palette swaps and rarely belong in a scope.
- **Don't scope to override a single component**. If only one `Button` needs a different fill, pass `ButtonDefaults.buttonColors(containerColor = ...)`. Reach for a scoped theme when **multiple** components in a subtree need the override.
- **Don't nest more than one level deep.** Two layered scopes mean the inner subtree should read the outer color roles instead of adding another theme layer.
- **Don't introduce a scoped theme for accessibility-critical actions** without re-checking contrast - the new pairing must still satisfy WCAG. Run the same checks as for the base scheme (see `references/android-accessibility.md`).

## Architecture Integration

### ViewModel Integration

```kotlin
// feature/settings/presentation/SettingsViewModel.kt
package com.example.feature.settings.presentation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.core.domain.ThemeRepository
import com.example.core.ui.theme.ThemeConfig
import com.example.core.ui.theme.ThemePreference
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val themeRepository: ThemeRepository
) : ViewModel() {

    val themeConfig: StateFlow<ThemeConfig> = themeRepository.themeConfig
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ThemeConfig()
        )

    fun setThemePreference(preference: ThemePreference) {
        viewModelScope.launch {
            themeRepository.setThemePreference(preference)
        }
    }

    fun setUseDynamicColor(useDynamicColor: Boolean) {
        viewModelScope.launch {
            themeRepository.setUseDynamicColor(useDynamicColor)
        }
    }
}
```

### App-Level Theme State

Edge-to-edge is mandatory on API 36. Use `Scaffold` for proper inset handling.

```kotlin
// app/MainActivity.kt
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    @Inject lateinit var themeRepository: ThemeRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        enableEdgeToEdge()
        
        setContent {
            val themeConfig by themeRepository.themeConfig
                .collectAsStateWithLifecycle(initialValue = ThemeConfig())

            AppTheme(themeConfig = themeConfig) {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    MainNavigation(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}
```

## Testing

### Fake Theme Repository

```kotlin
// core/testing/FakeThemeRepository.kt
package com.example.core.testing

import com.example.core.domain.ThemeRepository
import com.example.core.ui.theme.ThemeConfig
import com.example.core.ui.theme.ThemePreference
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class FakeThemeRepository : ThemeRepository {
    private val _themeConfig = MutableStateFlow(ThemeConfig())
    override val themeConfig: Flow<ThemeConfig> = _themeConfig.asStateFlow()

    override suspend fun setThemePreference(preference: ThemePreference) {
        _themeConfig.value = _themeConfig.value.copy(themePreference = preference)
    }

    override suspend fun setUseDynamicColor(useDynamicColor: Boolean) {
        _themeConfig.value = _themeConfig.value.copy(useDynamicColor = useDynamicColor)
    }

    fun setThemeConfig(config: ThemeConfig) {
        _themeConfig.value = config
    }
}
```

### Testing Theme Changes

```kotlin
// feature/settings/presentation/SettingsViewModelTest.kt
@Test
fun `setThemePreference updates theme config`() = runTest {
    val fakeThemeRepository = FakeThemeRepository()
    val viewModel = SettingsViewModel(fakeThemeRepository)

    viewModel.setThemePreference(ThemePreference.DARK)
    advanceUntilIdle()

    val themeConfig = viewModel.themeConfig.value
    assertEquals(ThemePreference.DARK, themeConfig.themePreference)
}

@Test
fun `setUseDynamicColor updates theme config`() = runTest {
    val fakeThemeRepository = FakeThemeRepository()
    val viewModel = SettingsViewModel(fakeThemeRepository)

    viewModel.setUseDynamicColor(false)
    advanceUntilIdle()

    val themeConfig = viewModel.themeConfig.value
    assertEquals(false, themeConfig.useDynamicColor)
}
```

### UI Testing with Theme

```kotlin
@Test
fun `theme settings screen shows correct theme selection`() {
    composeTestRule.setContent {
        AppTheme {
            ThemeSettingsScreen(
                currentTheme = ThemePreference.DARK,
                useDynamicColor = true,
                onThemeChange = {},
                onDynamicColorChange = {}
            )
        }
    }

    composeTestRule
        .onNodeWithText("Dark")
        .assertIsSelected()
}
```

## Layout Spacing and Component Dimensions

Use an **8 dp grid** for spacing (4 dp only for fine tuning). Map tokens to `Modifier.padding` / `Spacer` consistently across features.

| Token | Value | Typical use                          |
|-------|-------|--------------------------------------|
| xs    | 4 dp  | Icon padding, tight gaps             |
| sm    | 8 dp  | Inline spacing, dense lists          |
| md    | 16 dp | Default screen and card padding      |
| lg    | 24 dp | Section separation                   |
| xl    | 32 dp | Large gaps between groups            |
| xxl   | 48 dp | Screen edge margins on compact width |

**Common component heights** (Material 3; combine with minimum **48 dp** touch targets in `references/android-accessibility.md`)

| Component         | Height / size                 | Notes                             |
|-------------------|-------------------------------|-----------------------------------|
| Standard button   | 40 dp height, min width 64 dp | Touch target still at least 48 dp |
| FAB               | 56 x 56 dp                    | Mini FAB 40 dp when spec allows   |
| Text field        | 56 dp tall, min width ~280 dp | Includes label area               |
| Top app bar       | 64 dp                         |                                   |
| Bottom navigation | 80 dp                         |                                   |
| Navigation rail   | 80 dp width                   |                                   |

## Reserved Resource Names

Avoid **Android-reserved or overly generic** names for colors, drawables, and IDs. They can cause merge errors, shadow system resources, or confusing generated `R` fields.

| Category       | Avoid as a resource name                                                                                    |
|----------------|-------------------------------------------------------------------------------------------------------------|
| Colors         | `background`, `foreground`, `transparent`, `white`, `black` (prefer `app_background`, `icon_primary`, etc.) |
| Drawables      | `icon`, `logo`, `image`, `drawable`                                                                         |
| Generic        | `view`, `text`, `button`, `layout`, `container`                                                             |
| Meta           | `id`, `name`, `type`, `style`, `theme`, `color` as bare names                                               |
| Namespace-like | `app`, `android`, `content`, `data`, `action`                                                               |

In Kotlin, prefer descriptive names (`screenBackground`) over labels that read like framework APIs.

## Visual Style by App Category

Match **density, color, motion, and typography** to product category. Use the table below to pick defaults; deviate only with explicit product sign-off.

| App category           | Visual direction                                        | Interaction notes                                        |
|------------------------|---------------------------------------------------------|----------------------------------------------------------|
| Utility / tools        | Minimal, neutral palette, clear hierarchy               | Fast paths, little ornament                              |
| Finance / business     | Conservative colors, structured layout                  | Confirm destructive actions                              |
| Health / wellness      | Soft palette, generous whitespace                       | Encouraging, not alarming copy                           |
| Kids (younger)         | Bright colors, large type (18 sp+), very rounded shapes | Large targets (56 dp+), avoid text-only critical actions |
| Kids (older)           | Vibrant but readable                                    | Gamification ok; keep navigation obvious                 |
| Social / entertainment | Brand-forward, media-rich                               | Gestures ok if alternatives exist                        |
| Productivity           | High contrast options, dense modes                      | Keyboard and focus friendly                              |
| E-commerce             | Clear CTAs, scannable prices                            | Fast cart and checkout paths                             |
| Games                  | Theme-driven                                            | Follow platform sign-in and parent gates where required  |

**Style mismatches to avoid:** playful palette on finance, dense dashboards on meditation apps, tiny touch targets on kids flows, clownish UI on enterprise tools.

## Theme routing

### Required

1. **Use semantic color roles** from `MaterialTheme.colorScheme` (never hardcoded colors)
2. **Support both light and dark themes** with proper contrast
3. **Test accessibility** - ensure WCAG color contrast ratios (see `references/android-accessibility.md`)
4. **Use typography scales** from `MaterialTheme.typography` (avoid custom text sizes)
5. **Provide dynamic color support** on API 31+ for Material You
6. **Allow user theme preference** (Light/Dark/System)
7. **Use shape scales** from `MaterialTheme.shapes` for consistency
8. **Persist theme preferences** using DataStore (not SharedPreferences)
9. **Handle edge-to-edge** UI properly with `enableEdgeToEdge()` and `Scaffold` (mandatory on API 36)
10. **Test on both themes** to ensure content is readable
11. **Do not use `elegantTextHeight` attribute** - it is deprecated and ignored on API 36

### Forbidden

1. **Never hardcode colors** in composables (`Color(0xFFFF0000)`)
2. **Never hardcode text sizes** or font weights
3. **Never assume light theme** - always support dark theme
4. **Never use deprecated theming APIs** (MaterialTheme from material package)
5. **Never ignore system theme** unless user explicitly overrides
6. **Never forget to test color contrast** in dark mode
7. **Never use `isSystemInDarkTheme()` in ViewModels** (only in composables)
8. **Never create custom color attributes** without considering light/dark variants
9. **Never use `Color.Unspecified`** - always provide fallback colors
10. **Never test theme in emulator only** - test on real devices with different wallpapers
11. **Never mix color pairs** - `onPrimary` only goes on `primary`, `onPrimaryContainer` only on `primaryContainer` (see [Color Pairing Rules](#color-pairing-rules)); pulling content roles off their partner silently breaks contrast under dark mode, dynamic color, and user contrast
12. **Never use `onSurface` for everything on a surface** - secondary text, icons, dividers, and helper text belong on `onSurfaceVariant`; using `onSurface` everywhere flattens the visual hierarchy
13. **Never use `outlineVariant` for interactive borders** - it's a decorative role and does not meet 3:1 non-text contrast; outlined buttons, text fields, focus indicators, and region boundaries the user can tab to must use `outline` (see [`outline` vs `outlineVariant`](#outline-vs-outlinevariant))

### Color Naming Convention

Use semantic names, not visual descriptions:

```kotlin
// WRONG: visual descriptor names (`lightBlue`) instead of semantic roles
val lightBlue = Color(0xFF2196F3)
val darkBlue = Color(0xFF1976D2)

// CORRECT: semantic role names (`primary`, `primaryVariant`)
val primary = Color(0xFF2196F3)
val primaryVariant = Color(0xFF1976D2)
```

### Theme Transitions

For smooth theme transitions, use `animateColorAsState`:

```kotlin
@Composable
fun ThemedCard() {
    val backgroundColor by animateColorAsState(
        targetValue = MaterialTheme.colorScheme.surface,
        label = "background"
    )
    
    Card(
        colors = CardDefaults.cardColors(
            containerColor = backgroundColor
        )
    ) {
        // Content
    }
}
```

### Preview with Themes

Always preview both light and dark themes:

```kotlin
@Preview(name = "Light", showBackground = true)
@Preview(name = "Dark", showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
private fun ProfileCardPreview() {
    AppTheme {
        ProfileCard(
            user = User(name = "Jane Doe", email = "jane@example.com")
        )
    }
}
```

### Material Theme Builder

Use [Material Theme Builder](https://m3.material.io/theme-builder) to:
1. Generate custom color schemes from brand colors
2. Preview components with your theme
3. Export Compose code directly
4. Ensure WCAG contrast compliance

### Dynamic Color Considerations

- Dynamic colors work best for **content-focused apps** (news, social, productivity)
- Consider **disabling by default** for **brand-focused apps** (banking, enterprise)
- Always provide **static fallback** for API < 31
- Test with **various wallpapers** - light, dark, colorful, monochrome

## References

- [Material Design 3](https://m3.material.io/)
- [Material Theme Builder](https://m3.material.io/theme-builder)
- [Compose Material3 API](https://developer.android.com/reference/kotlin/androidx/compose/material3/package-summary)
- [Dynamic Color](https://m3.material.io/styles/color/dynamic-color/overview)
- [Typography](https://m3.material.io/styles/typography/overview)
- [Shape](https://m3.material.io/styles/shape/overview)
- [Color System](https://m3.material.io/styles/color/system/overview)
- [Accessibility Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
