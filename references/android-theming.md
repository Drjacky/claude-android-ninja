# Android Theming

Modern Material Design 3 theming with dynamic colors, custom color schemes, typography scales, shape theming, and dark/light mode switching.

All Kotlin code in this guide must align with `references/kotlin-patterns.md`.

**Related guides:** See `references/compose-patterns.md` for theme usage in composables and `references/android-accessibility.md` for color contrast requirements.

## Table of Contents

- [Material 3 Theme System](#material-3-theme-system)
- [Color Schemes](#color-schemes)
- [Dynamic Color (Material You)](#dynamic-color-material-you)
- [Typography Scales](#typography-scales)
- [Shape Theming](#shape-theming)
- [Dark/Light Mode Switching](#darklight-mode-switching)
- [Theme Preferences](#theme-preferences)
- [Custom Theme Attributes](#custom-theme-attributes)
- [Architecture Integration](#architecture-integration)
- [Testing](#testing)
- [Best Practices](#best-practices)

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
    scrim = md_theme_light_scrim
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
    scrim = md_theme_dark_scrim
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

## Best Practices

### ✅ Always Do

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
11. **Do not use `elegantTextHeight`** attribute -- it is deprecated and ignored on API 36

### ❌ Never Do

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

### Color Naming Convention

Use semantic names, not visual descriptions:

```kotlin
// ❌ Bad
val lightBlue = Color(0xFF2196F3)
val darkBlue = Color(0xFF1976D2)

// ✅ Good
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
