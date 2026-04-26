# Android Graphics & Icons

Required: ship every icon as Material Symbols (drawable XML) or `ImageVector`. Custom drawing goes through `Canvas` / `Modifier.drawWithCache`. Never depend on the deprecated `androidx.compose.material.icons` artifact.

## Table of Contents
1. [Material Symbols Icons](#material-symbols-icons)
2. [Adaptive Launcher Icons](#adaptive-launcher-icons)
3. [ImageVector Patterns](#imagevector-patterns)
4. [Custom Drawing with Canvas](#custom-drawing-with-canvas)
5. [Performance Optimizations](#performance-optimizations)

## Material Symbols Icons

Use Material Symbols (drawable XML) for every standard glyph. Avoid `androidx.compose.material.icons.*`: it is deprecated, ships M2 visuals, and inflates build time.

### Downloading Icons

Iconify API (preferred for automation):

```bash
# Download icon as SVG using curl
curl -o app/src/main/res/drawable/ic_lock.xml \
  "https://api.iconify.design/material-symbols:lock.svg?download=true"

curl -o app/src/main/res/drawable/ic_person.xml \
  "https://api.iconify.design/material-symbols:person.svg?download=true"

curl -o app/src/main/res/drawable/ic_settings.xml \
  "https://api.iconify.design/material-symbols:settings.svg?download=true"

# Outlined variant
curl -o app/src/main/res/drawable/ic_home_outlined.xml \
  "https://api.iconify.design/material-symbols:home-outline.svg?download=true"
```

Manual fallback: download SVG from https://fonts.google.com/icons, convert to a Vector Drawable via Android Studio (`res/drawable` → New → Vector Asset → Local file) or https://svg2vector.com/, place under `app/src/main/res/drawable/`.

### Usage in Compose

```kotlin
import androidx.compose.foundation.Image
import androidx.compose.material3.Icon
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp

@Composable
fun MaterialSymbolExample() {
    Icon(
        painter = painterResource(R.drawable.ic_lock),
        contentDescription = stringResource(R.string.lock_icon),
        modifier = Modifier.size(24.dp),
        tint = Color.Unspecified // Use SVG colors
    )

    Icon(
        painter = painterResource(R.drawable.ic_settings),
        contentDescription = stringResource(R.string.settings_icon),
        tint = MaterialTheme.colorScheme.primary
    )
}
```

Forbidden: `androidx.compose.material.icons.Icons.*` (e.g. `Icons.Default.Lock`). The artifact is unmaintained, ships M2 visuals, and inflates build time.

### Icon Organization

```kotlin
// app/src/main/kotlin/com/example/app/ui/icons/AppIcons.kt
object AppIcons {
    val Lock = R.drawable.ic_lock
    val Person = R.drawable.ic_person
    val Settings = R.drawable.ic_settings
    val Home = R.drawable.ic_home
    val Info = R.drawable.ic_info
}

// Usage
Icon(
    painter = painterResource(AppIcons.Lock),
    contentDescription = stringResource(R.string.lock_icon)
)
```

## Adaptive Launcher Icons

Launcher icons are **adaptive** on API 26+: foreground and background layers mask to different shapes per OEM.

**Key specs**

| Item                   | Value                                                      |
|------------------------|------------------------------------------------------------|
| Layer canvas           | 108 x 108 dp per layer (foreground and background)         |
| Safe zone (full asset) | Keep critical logo inside center **66 dp** diameter circle |
| Logo artwork           | Often ~48-66 dp so it is not clipped by masks              |
| Monochrome             | API 33+ optional monochrome layer for themed icons         |

Place `mipmap-anydpi-v26/ic_launcher.xml` with `<adaptive-icon>` pointing at foreground and background drawables. Provide legacy mipmaps (mdpi through xxxhdpi) for older APIs as needed.

See [Adaptive icons](https://developer.android.com/develop/ui/views/launch/icon_design_adaptive) for exports from design tools.

## ImageVector Patterns

Use `ImageVector` for icons that must be parameterized at runtime (themed colors, dynamic counts, generated paths). Use Material Symbols drawables for everything static.

### Basic ImageVector Creation

```kotlin
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.vector.path
import androidx.compose.ui.unit.dp

val CustomCheckIcon: ImageVector = ImageVector.Builder(
    name = "CustomCheck",
    defaultWidth = 24.dp,
    defaultHeight = 24.dp,
    viewportWidth = 24f,
    viewportHeight = 24f
).apply {
    path(
        fill = SolidColor(Color.Black),
        stroke = null,
        strokeLineWidth = 0f,
        strokeLineCap = StrokeCap.Butt,
        strokeLineJoin = StrokeJoin.Miter,
        strokeLineMiter = 4f,
        pathFillType = PathFillType.NonZero
    ) {
        moveTo(9f, 16.17f)
        lineTo(4.83f, 12f)
        lineToRelative(-1.42f, 1.41f)
        lineTo(9f, 19f)
        lineTo(21f, 7f)
        lineToRelative(-1.41f, -1.41f)
        close()
    }
}.build()
```

### PathData DSL

Compose's PathData provides SVG-like commands:

```kotlin
import androidx.compose.ui.graphics.vector.PathBuilder

fun PathBuilder.drawCircle(cx: Float, cy: Float, radius: Float) {
    moveTo(cx + radius, cy)
    // Approximate circle with cubic Bézier curves
    val c = 0.552284749831f * radius
    curveTo(cx + radius, cy + c, cx + c, cy + radius, cx, cy + radius)
    curveTo(cx - c, cy + radius, cx - radius, cy + c, cx - radius, cy)
    curveTo(cx - radius, cy - c, cx - c, cy - radius, cx, cy - radius)
    curveTo(cx + c, cy - radius, cx + radius, cy - c, cx + radius, cy)
    close()
}

val CircleIcon: ImageVector = ImageVector.Builder(
    name = "Circle",
    defaultWidth = 24.dp,
    defaultHeight = 24.dp,
    viewportWidth = 24f,
    viewportHeight = 24f
).apply {
    path(fill = SolidColor(Color.Blue)) {
        drawCircle(12f, 12f, 10f)
    }
}.build()
```

### PathData Commands Reference

| Command                  | Description                   | Example                                         |
|--------------------------|-------------------------------|-------------------------------------------------|
| `moveTo(x, y)`           | Move pen without drawing      | `moveTo(10f, 10f)`                              |
| `lineTo(x, y)`           | Draw line to point            | `lineTo(20f, 20f)`                              |
| `horizontalLineTo(x)`    | Horizontal line               | `horizontalLineTo(50f)`                         |
| `verticalLineTo(y)`      | Vertical line                 | `verticalLineTo(50f)`                           |
| `curveTo(...)`           | Cubic Bézier curve (absolute) | `curveTo(10f, 20f, 30f, 40f, 50f, 60f)`         |
| `curveToRelative(...)`   | Cubic Bézier curve (relative) | `curveToRelative(10f, 20f, 30f, 40f, 50f, 60f)` |
| `reflectiveCurveTo(...)` | Smooth curve continuation     | `reflectiveCurveTo(30f, 40f, 50f, 60f)`         |
| `quadTo(...)`            | Quadratic Bézier curve        | `quadTo(30f, 20f, 50f, 40f)`                    |
| `arcTo(...)`             | Elliptical arc                | `arcTo(10f, 10f, 0f, false, true, 20f, 20f)`    |
| `close()`                | Close path to start           | `close()`                                       |

### Dynamic Icon Generation

Generate icons programmatically with parameters:

```kotlin
fun createBadgeIcon(count: Int, backgroundColor: Color): ImageVector {
    return ImageVector.Builder(
        name = "Badge",
        defaultWidth = 24.dp,
        defaultHeight = 24.dp,
        viewportWidth = 24f,
        viewportHeight = 24f
    ).apply {
        // Background circle
        path(fill = SolidColor(backgroundColor)) {
            moveTo(12f, 2f)
            curveTo(6.48f, 2f, 2f, 6.48f, 2f, 12f)
            curveTo(2f, 17.52f, 6.48f, 22f, 12f, 22f)
            curveTo(17.52f, 22f, 22f, 17.52f, 22f, 12f)
            curveTo(22f, 6.48f, 17.52f, 2f, 12f, 2f)
            close()
        }
        
        // You could add text rendering here for the count
        // (though for actual text, use Text composable overlays)
    }.build()
}

@Composable
fun NotificationBadge(count: Int) {
    val badgeColor = if (count > 99) Color.Red else MaterialTheme.colorScheme.primary
    
    Image(
        imageVector = createBadgeIcon(count, badgeColor),
        contentDescription = "$count notifications"
    )
}
```

### Icon Collections

Organize custom icons in a centralized object:

```kotlin
// core/ui/icons/CustomIcons.kt
object CustomIcons {
    val Zap: ImageVector by lazy {
        ImageVector.Builder(
            name = "Zap",
            defaultWidth = 24.dp,
            defaultHeight = 24.dp,
            viewportWidth = 24f,
            viewportHeight = 24f
        ).apply {
            path(fill = SolidColor(Color(0xFFFFD700))) { // Gold
                moveTo(13f, 2f)
                lineTo(3f, 14f)
                horizontalLineTo(12f)
                lineTo(11f, 22f)
                lineTo(21f, 10f)
                horizontalLineTo(12f)
                close()
            }
        }.build()
    }
    
    val Relay: ImageVector by lazy {
        ImageVector.Builder(
            name = "Relay",
            defaultWidth = 24.dp,
            defaultHeight = 24.dp,
            viewportWidth = 24f,
            viewportHeight = 24f
        ).apply {
            // Relay icon paths
            path(fill = SolidColor(Color.Black)) {
                moveTo(12f, 2f)
                lineTo(2f, 7f)
                verticalLineTo(17f)
                lineTo(12f, 22f)
                lineTo(22f, 17f)
                verticalLineTo(7f)
                close()
            }
        }.build()
    }
}

// Usage
Icon(CustomIcons.Zap, contentDescription = "Lightning")
Icon(CustomIcons.Relay, contentDescription = "Relay indicator")
```

### Themed Icons

Parameterize colors for theme adaptation:

```kotlin
@Composable
fun ThemedIcon(
    modifier: Modifier = Modifier,
    contentDescription: String?
) {
    val primary = MaterialTheme.colorScheme.primary
    val surface = MaterialTheme.colorScheme.surface
    
    val themedIcon = remember(primary, surface) {
        ImageVector.Builder(
            name = "ThemedIcon",
            defaultWidth = 24.dp,
            defaultHeight = 24.dp,
            viewportWidth = 24f,
            viewportHeight = 24f
        ).apply {
            // Background
            path(fill = SolidColor(surface)) {
                moveTo(12f, 2f)
                curveTo(6.48f, 2f, 2f, 6.48f, 2f, 12f)
                curveTo(2f, 17.52f, 6.48f, 22f, 12f, 22f)
                curveTo(17.52f, 22f, 22f, 17.52f, 22f, 12f)
                curveTo(22f, 6.48f, 17.52f, 2f, 12f, 2f)
                close()
            }
            
            // Foreground
            path(fill = SolidColor(primary)) {
                moveTo(12f, 6f)
                lineTo(18f, 12f)
                lineTo(12f, 18f)
                lineTo(6f, 12f)
                close()
            }
        }.build()
    }
    
    Image(
        imageVector = themedIcon,
        contentDescription = contentDescription,
        modifier = modifier
    )
}
```

### Layered Icons with Alpha

Build complex icons with multiple layers:

```kotlin
val LayeredIcon: ImageVector = ImageVector.Builder(
    name = "Layered",
    defaultWidth = 24.dp,
    defaultHeight = 24.dp,
    viewportWidth = 24f,
    viewportHeight = 24f
).apply {
    // Layer 1: Background (bottom)
    path(fill = SolidColor(Color.White)) {
        moveTo(0f, 0f)
        lineTo(24f, 0f)
        lineTo(24f, 24f)
        lineTo(0f, 24f)
        close()
    }
    
    // Layer 2: Shadow
    path(
        fill = SolidColor(Color.Black),
        fillAlpha = 0.2f
    ) {
        moveTo(13f, 13f)
        curveTo(13f, 15.76f, 10.76f, 18f, 8f, 18f)
        curveTo(5.24f, 18f, 3f, 15.76f, 3f, 13f)
        curveTo(3f, 10.24f, 5.24f, 8f, 8f, 8f)
        curveTo(10.76f, 8f, 13f, 10.24f, 13f, 13f)
        close()
    }
    
    // Layer 3: Main shape
    path(fill = SolidColor(Color.Blue)) {
        moveTo(12f, 12f)
        curveTo(12f, 14.76f, 9.76f, 17f, 7f, 17f)
        curveTo(4.24f, 17f, 2f, 14.76f, 2f, 12f)
        curveTo(2f, 9.24f, 4.24f, 7f, 7f, 7f)
        curveTo(9.76f, 7f, 12f, 9.24f, 12f, 12f)
        close()
    }
    
    // Layer 4: Highlight
    path(
        fill = SolidColor(Color.White),
        fillAlpha = 0.3f
    ) {
        moveTo(9f, 10f)
        curveTo(9f, 11.1f, 8.1f, 12f, 7f, 12f)
        curveTo(5.9f, 12f, 5f, 11.1f, 5f, 10f)
        curveTo(5f, 8.9f, 5.9f, 8f, 7f, 8f)
        curveTo(8.1f, 8f, 9f, 8.9f, 9f, 10f)
        close()
    }
    
    // Layer 5: Outline (top)
    path(
        fill = null,
        stroke = SolidColor(Color.Black),
        strokeLineWidth = 1.5f
    ) {
        moveTo(12f, 12f)
        curveTo(12f, 14.76f, 9.76f, 17f, 7f, 17f)
        curveTo(4.24f, 17f, 2f, 14.76f, 2f, 12f)
        curveTo(2f, 9.24f, 4.24f, 7f, 7f, 7f)
        curveTo(9.76f, 7f, 12f, 9.24f, 12f, 12f)
        close()
    }
}.build()
```

**Render order**: Bottom to top (first path = bottom layer)

## Custom Drawing with Canvas

For complex graphics beyond icons, use Compose's Canvas APIs.

### Drawing Modifiers

#### `Modifier.drawWithContent`

Draw behind or in front of composable content:

```kotlin
@Composable
fun GradientText(text: String) {
    val gradient = Brush.linearGradient(
        colors = listOf(Color.Blue, Color.Cyan, Color.Green)
    )
    
    Text(
        text = text,
        style = MaterialTheme.typography.headlineLarge,
        modifier = Modifier.drawWithContent {
            drawContent() // Draw the text first
            
            // Draw gradient overlay
            drawRect(
                brush = gradient,
                blendMode = BlendMode.SrcAtop
            )
        }
    )
}
```

#### `Modifier.drawBehind`

Draw behind composable content:

```kotlin
@Composable
fun HighlightedText(text: String) {
    Text(
        text = text,
        modifier = Modifier.drawBehind {
            val cornerRadius = 8.dp.toPx()
            drawRoundRect(
                color = Color.Yellow.copy(alpha = 0.3f),
                cornerRadius = CornerRadius(cornerRadius)
            )
        }
    )
}
```

#### `Modifier.drawWithCache`

Cache drawing operations for better performance:

```kotlin
@Composable
fun ComplexBackground() {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .drawWithCache {
                val gradient = Brush.radialGradient(
                    colors = listOf(Color.Blue, Color.Transparent),
                    center = Offset(size.width / 2, size.height / 2),
                    radius = size.maxDimension / 2
                )
                
                onDrawBehind {
                    drawRect(gradient)
                }
            }
    )
}
```

### Canvas Composable

Full control over drawing:

```kotlin
@Composable
fun CustomChart(data: List<Float>) {
    Canvas(modifier = Modifier.fillMaxSize()) {
        val barWidth = size.width / data.size
        val maxValue = data.maxOrNull() ?: 1f
        
        data.forEachIndexed { index, value ->
            val barHeight = (value / maxValue) * size.height
            
            drawRect(
                color = Color.Blue,
                topLeft = Offset(
                    x = index * barWidth,
                    y = size.height - barHeight
                ),
                size = Size(
                    width = barWidth * 0.8f,
                    height = barHeight
                )
            )
        }
    }
}
```

### Advanced Canvas Techniques

#### Clipping

```kotlin
Canvas(modifier = Modifier.size(200.dp)) {
    // Clip to circle
    clipPath(Path().apply {
        addOval(Rect(0f, 0f, size.width, size.height))
    }) {
        // Everything drawn here is clipped to circle
        drawRect(
            brush = Brush.linearGradient(
                colors = listOf(Color.Red, Color.Blue)
            )
        )
    }
}
```

#### Transformations

```kotlin
Canvas(modifier = Modifier.size(200.dp)) {
    // Rotate
    rotate(45f, pivot = center) {
        drawRect(
            color = Color.Blue,
            size = Size(100f, 100f)
        )
    }
    
    // Scale
    scale(1.5f, pivot = center) {
        drawCircle(
            color = Color.Red,
            radius = 50f,
            center = center
        )
    }
    
    // Translate
    translate(left = 50f, top = 50f) {
        drawLine(
            color = Color.Green,
            start = Offset.Zero,
            end = Offset(100f, 100f),
            strokeWidth = 5f
        )
    }
}
```

#### Custom Shapes with Path

```kotlin
@Composable
fun StarShape() {
    Canvas(modifier = Modifier.size(100.dp)) {
        val path = Path().apply {
            val centerX = size.width / 2
            val centerY = size.height / 2
            val outerRadius = size.minDimension / 2
            val innerRadius = outerRadius * 0.4f
            val points = 5
            
            for (i in 0 until points * 2) {
                val radius = if (i % 2 == 0) outerRadius else innerRadius
                val angle = (i * Math.PI / points).toFloat()
                val x = centerX + radius * cos(angle)
                val y = centerY + radius * sin(angle)
                
                if (i == 0) moveTo(x, y)
                else lineTo(x, y)
            }
            close()
        }
        
        drawPath(
            path = path,
            color = Color(0xFFFFD700), // Gold
            style = Fill
        )
        
        drawPath(
            path = path,
            color = Color.Black,
            style = Stroke(width = 2.dp.toPx())
        )
    }
}
```

#### Blend Modes

```kotlin
Canvas(modifier = Modifier.size(200.dp)) {
    // Draw two overlapping circles with blend mode
    drawCircle(
        color = Color.Red,
        radius = 80f,
        center = Offset(60f, 100f)
    )
    
    drawCircle(
        color = Color.Blue,
        radius = 80f,
        center = Offset(140f, 100f),
        blendMode = BlendMode.Multiply // Try different blend modes
    )
}
```

**Common Blend Modes:**
- `BlendMode.Screen` - Additive blending for glow effects
- `BlendMode.Multiply` - Darkening/shadow effects  
- `BlendMode.SrcAtop` - Mask content to layer below
- `BlendMode.Plus` - Additive color (brightening)
- `BlendMode.Overlay` - Combination of multiply and screen
- `BlendMode.Lighten` - Keep lighter pixels
- `BlendMode.Darken` - Keep darker pixels

### Glow Effects with Radial Gradients

Create dynamic glow effects using radial gradients and `BlendMode.Screen`:

```kotlin
@Composable
fun GlowEffect(
    glowColor: Color,
    glowIntensity: Float = 0.6f,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val radius = size.minDimension / 2f
        
        // Outer glow
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    glowColor.copy(alpha = 0.6f * glowIntensity),
                    glowColor.copy(alpha = 0.2f * glowIntensity),
                    Color.Transparent
                ),
                center = center,
                radius = radius * 1.2f
            ),
            radius = radius * 1.5f,
            center = center,
            blendMode = BlendMode.Screen // Additive blending for glow
        )
        
        // Inner highlight
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color.White.copy(alpha = 0.1f * glowIntensity),
                    Color.Transparent
                ),
                center = center,
                radius = radius * 0.5f
            ),
            radius = radius * 0.8f,
            center = center,
            blendMode = BlendMode.Screen
        )
    }
}
```

### Animated Pulsing Glow

Combine infinite animation with glow effects:

```kotlin
@Composable
fun PulsingGlow(
    glowColor: Color,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "glow_pulse")
    val pulseIntensity by infiniteTransition.animateFloat(
        initialValue = 0.3f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(2200, easing = LinearEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )
    
    Canvas(modifier = modifier.fillMaxSize()) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val baseRadius = size.minDimension / 2f
        val animatedRadius = baseRadius * (1f + 0.2f * pulseIntensity)
        
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    glowColor.copy(alpha = 0.6f * pulseIntensity),
                    glowColor.copy(alpha = 0.2f * pulseIntensity),
                    Color.Transparent
                ),
                center = center,
                radius = animatedRadius
            ),
            radius = animatedRadius * 1.2f,
            center = center,
            blendMode = BlendMode.Screen
        )
    }
}
```

### Multi-Color Glow Pattern

Position multiple colored glows in a circular arrangement:

```kotlin
@Composable
fun MultiColorGlow(
    colors: List<Color>,
    pulseIntensity: Float,
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier.fillMaxSize()) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val radius = size.minDimension / 2f
        val spread = radius * 0.3f
        
        colors.forEachIndexed { index, color ->
            // Position glows in a circle using trigonometry
            val angle = 2f * Math.PI.toFloat() * index / colors.size
            val colorCenter = Offset(
                center.x + cos(angle) * radius * 0.2f,
                center.y + sin(angle) * radius * 0.2f
            )
            
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        color.copy(alpha = 0.6f * pulseIntensity),
                        color.copy(alpha = 0.2f * pulseIntensity),
                        Color.Transparent
                    ),
                    center = colorCenter,
                    radius = radius * 0.6f
                ),
                radius = radius * 0.8f,
                center = colorCenter,
                blendMode = BlendMode.Screen
            )
        }
        
        // Overall white glow overlay
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(
                    Color.White.copy(alpha = 0.05f * pulseIntensity),
                    Color.Transparent
                ),
                center = center,
                radius = radius * 0.8f
            ),
            radius = radius * 1.2f,
            center = center,
            blendMode = BlendMode.Screen
        )
    }
}
```

### Color Extraction from Images

Use Android Palette API to extract colors from images:

```kotlin
import androidx.palette.graphics.Palette
import android.graphics.Bitmap

/**
 * Extracts vibrant color from a bitmap
 */
fun extractVibrantColor(bitmap: Bitmap, isDark: Boolean = true): Color {
    // Convert hardware bitmap to software bitmap if needed
    val softwareBitmap = if (bitmap.config == Bitmap.Config.HARDWARE) {
        bitmap.copy(Bitmap.Config.ARGB_8888, false)
    } else {
        bitmap
    }

    val palette = Palette.from(softwareBitmap).generate()

    // Use vibrant swatches when sampling wallpaper colors
    val vibrantSwatch = if (isDark) {
        palette.darkVibrantSwatch
            ?: palette.vibrantSwatch
            ?: palette.dominantSwatch
    } else {
        palette.lightVibrantSwatch
            ?: palette.vibrantSwatch
            ?: palette.dominantSwatch
    }

    return if (vibrantSwatch != null) {
        Color(vibrantSwatch.rgb)
    } else {
        Color(0xFF6B6B6B) // Fallback
    }
}

/**
 * Extract colors from different regions of the image
 */
fun extractMultipleColorsFromRegions(
    bitmap: Bitmap,
    numberOfRegions: Int
): List<Color> {
    val colors = mutableListOf<Color>()
    
    // Define regions based on grid layout
    val regions = when (numberOfRegions) {
        4 -> listOf(
            android.graphics.Rect(0, 0, bitmap.width / 2, bitmap.height / 2), // Top-left
            android.graphics.Rect(bitmap.width / 2, 0, bitmap.width, bitmap.height / 2), // Top-right
            android.graphics.Rect(0, bitmap.height / 2, bitmap.width / 2, bitmap.height), // Bottom-left
            android.graphics.Rect(bitmap.width / 2, bitmap.height / 2, bitmap.width, bitmap.height) // Bottom-right
        )
        6 -> listOf(
            android.graphics.Rect(0, 0, bitmap.width / 2, bitmap.height / 3), // Top-left
            android.graphics.Rect(bitmap.width / 2, 0, bitmap.width, bitmap.height / 3), // Top-right
            android.graphics.Rect(0, bitmap.height / 3, bitmap.width / 2, 2 * bitmap.height / 3), // Middle-left
            android.graphics.Rect(bitmap.width / 2, bitmap.height / 3, bitmap.width, 2 * bitmap.height / 3), // Middle-right
            android.graphics.Rect(0, 2 * bitmap.height / 3, bitmap.width / 2, bitmap.height), // Bottom-left
            android.graphics.Rect(bitmap.width / 2, 2 * bitmap.height / 3, bitmap.width, bitmap.height) // Bottom-right
        )
        else -> listOf(android.graphics.Rect(0, 0, bitmap.width, bitmap.height))
    }
    
    regions.forEach { region ->
        val subBitmap = Bitmap.createBitmap(
            bitmap,
            region.left,
            region.top,
            region.width(),
            region.height()
        )
        colors.add(extractVibrantColor(subBitmap))
        subBitmap.recycle()
    }
    
    return colors.distinct()
}
```

### Dynamic Size Tracking

Get composable size for drawing calculations:

```kotlin
@Composable
fun DynamicSizeCanvas() {
    var containerSize by remember { mutableStateOf<Size?>(null) }
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .onGloballyPositioned { coordinates ->
                containerSize = Size(
                    coordinates.size.width.toFloat(),
                    coordinates.size.height.toFloat()
                )
            }
    ) {
        containerSize?.let { size ->
            Canvas(modifier = Modifier.fillMaxSize()) {
                // Use size for calculations
                val center = Offset(size.width / 2f, size.height / 2f)
                val radius = minOf(size.width, size.height) / 2f
                
                drawCircle(
                    color = Color.Blue,
                    radius = radius,
                    center = center
                )
            }
        }
    }
}
```

### Image Loading with Coil3

#### AsyncImage (Primary API)

Use `AsyncImage` for the vast majority of cases. It resolves image size from layout constraints
automatically, avoiding oversized bitmap loading.

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data("https://example.com/avatar.jpg")
        .crossfade(true)
        .build(),
    contentDescription = stringResource(R.string.user_avatar),
    contentScale = ContentScale.Crop,
    placeholder = painterResource(R.drawable.ic_placeholder),
    error = painterResource(R.drawable.ic_error),
    modifier = Modifier
        .size(64.dp)
        .clip(CircleShape)
)
```

#### SubcomposeAsyncImage (Custom State Composables)

Use only when you need fully custom composables for loading, success, and error states.
**Never use inside `LazyColumn` / `LazyRow`** - subcomposition is significantly slower than
regular composition and causes scroll jank.

```kotlin
SubcomposeAsyncImage(
    model = "https://example.com/hero.jpg",
    contentDescription = null
) {
    when (painter.state) {
        is AsyncImagePainter.State.Loading -> CircularProgressIndicator()
        is AsyncImagePainter.State.Error -> Icon(Icons.Default.BrokenImage, null)
        else -> SubcomposeAsyncImageContent()
    }
}
```

#### rememberAsyncImagePainter (Low-Level)

Use only when a `Painter` is strictly required (e.g., `Canvas`, `Icon`, or a custom draw
operation). Unlike `AsyncImage`, it does **not** infer display size - without an explicit
`.size()`, it loads the image at original dimensions, wasting memory.

```kotlin
val painter = rememberAsyncImagePainter(
    model = ImageRequest.Builder(LocalContext.current)
        .data("https://example.com/image.jpg")
        .size(Size.ORIGINAL)
        .build()
)
Image(painter = painter, contentDescription = null)
```

#### ImageRequest Configuration

```kotlin
ImageRequest.Builder(context)
    .data(imageUrl)
    .crossfade(300)
    .size(200, 200)
    .scale(Scale.CROP)
    .transformations(CircleCropTransformation())
    .memoryCachePolicy(CachePolicy.ENABLED)
    .diskCachePolicy(CachePolicy.ENABLED)
    .build()
```

#### Hilt ImageLoader Setup

Provide a single `ImageLoader` instance app-wide to share disk and memory caches:

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object ImageModule {

    @Provides
    @Singleton
    fun provideImageLoader(@ApplicationContext context: Context): ImageLoader =
        ImageLoader.Builder(context)
            .crossfade(true)
            .respectCacheHeaders(false)
            .build()
}
```

Pass it to `AsyncImage` via injection or `CompositionLocal`:

```kotlin
AsyncImage(
    model = url,
    contentDescription = null,
    imageLoader = imageLoader
)
```

#### Which API to Use

- **Standard image loading** → `AsyncImage`
- **Need `Painter` for `Canvas` / `Icon`** → `rememberAsyncImagePainter` + explicit `.size()`
- **Custom loading/error composables** → `SubcomposeAsyncImage` (never in lists)
- **Decorative image** → `contentDescription = null`

#### Color Extraction from Loaded Images

```kotlin
import coil3.ImageLoader
import coil3.compose.AsyncImage
import coil3.request.ImageRequest
import coil3.request.SuccessResult
import coil3.request.allowHardware

suspend fun loadImageAndExtractColor(
    context: Context,
    imageUrl: String
): Color? {
    return try {
        val imageLoader = ImageLoader(context)
        val request = ImageRequest.Builder(context)
            .data(imageUrl)
            .allowHardware(false) // Required for Palette API
            .build()

        val result = imageLoader.execute(request)
        if (result is SuccessResult) {
            val drawable = result.image.asDrawable(context.resources)
            val bitmap = drawable.toBitmap()
            extractVibrantColor(bitmap)
        } else {
            null
        }
    } catch (e: Exception) {
        null
    }
}

@Composable
fun ImageWithExtractedGlow(imageUrl: String) {
    val context = LocalContext.current
    var glowColor by remember(imageUrl) { mutableStateOf<Color?>(null) }
    
    LaunchedEffect(imageUrl) {
        glowColor = loadImageAndExtractColor(context, imageUrl)
    }
    
    Box {
        // Glow effect using extracted color
        glowColor?.let { color ->
            PulsingGlow(glowColor = color, modifier = Modifier.matchParentSize())
        }
        
        // Image on top
        AsyncImage(
            model = imageUrl,
            contentDescription = null,
            modifier = Modifier.fillMaxSize()
        )
    }
}
```

### Blend Modes

### Performance: drawWithCache vs drawBehind

`drawWithCache` allocates expensive objects (`Brush`, `Path`, gradients) once and reuses them across draws. `drawBehind` re-runs its block on every frame; reserve it for cheap, layout-dependent operations.

```kotlin
@Composable
fun CachedDrawing() {
    Box(
        modifier = Modifier.drawWithCache {
            val gradient = createExpensiveGradient()
            val path = createComplexPath()

            onDrawBehind {
                drawPath(path, brush = gradient)
            }
        }
    )
}
```

## Performance Optimizations

### Icon Caching

Cache dynamically generated ImageVectors:

```kotlin
object IconCache {
    private val cache = mutableMapOf<String, ImageVector>()
    
    fun getOrCreate(key: String, builder: () -> ImageVector): ImageVector {
        return cache.getOrPut(key, builder)
    }
}

@Composable
fun CachedIcon(userId: String) {
    val icon = remember(userId) {
        IconCache.getOrCreate(userId) {
            generateUserIcon(userId)
        }
    }
    
    Image(imageVector = icon, contentDescription = "User avatar")
}
```

### Avoid Recomposition

Use `remember` and `derivedStateOf` appropriately:

```kotlin
@Composable
fun AnimatedIcon(isActive: Boolean) {
    // CORRECT: Icon only recreated when isActive changes
    val icon = remember(isActive) {
        createAnimatedIcon(isActive)
    }
    
    Image(imageVector = icon, contentDescription = null)
}

@Composable
fun DerivedIcon(data: List<Int>) {
    // CORRECT: Icon only recreated when sum changes, not when list instance changes
    val icon = remember {
        derivedStateOf { createIcon(data.sum()) }
    }.value
    
    Image(imageVector = icon, contentDescription = null)
}
```

### Lazy Icon Loading

Don't create all icons upfront:

```kotlin
object AppIcons {
    // CORRECT: Lazy initialization
    val Home: ImageVector by lazy { createHomeIcon() }
    val Settings: ImageVector by lazy { createSettingsIcon() }
    val Profile: ImageVector by lazy { createProfileIcon() }
    
    // WRONG: Avoid Eager initialization
    // val All = listOf(createHomeIcon(), createSettingsIcon(), ...) // Creates all immediately
}
```

## Rules

Required:
- Source standard glyphs from Material Symbols (drawable XML).
- Reserve `ImageVector` for programmatic / themed / dynamic icons; cache results behind `by lazy` or `remember(keys)`.
- Wrap expensive draw setup in `Modifier.drawWithCache`; keep `Modifier.drawBehind` for cheap, per-frame work only.
- Layer paths bottom-to-top inside one `ImageVector.Builder`; close every sub-path with `close()`.
- Centralize icon references in an `AppIcons` / `CustomIcons` object.
- Resolve theme colors via `MaterialTheme.colorScheme.*` and pass them in; never hard-code theme-specific colors inside an icon definition.
- Use `AsyncImage` for network/disk images; `SubcomposeAsyncImage` only outside lazy lists; `rememberAsyncImagePainter` only when a `Painter` is required (with explicit `.size()`).

Forbidden:
- `androidx.compose.material.icons.Icons.*` and any artifact under `androidx.compose.material.icons:*`.
- Building an `ImageVector` inside a `@Composable` without `remember` / `by lazy`.
- Replacing a standard Material Symbol with a hand-rolled custom icon.
- Mixing absolute and relative path commands within the same path without reason.
- `SubcomposeAsyncImage` inside `LazyColumn` / `LazyRow` (causes scroll jank).

## Additional Resources

- [Material Symbols](https://fonts.google.com/icons)
- [Iconify API](https://api.iconify.design/)
- [Compose Graphics API](https://developer.android.com/jetpack/compose/graphics)
- [ImageVector Reference](https://developer.android.com/reference/kotlin/androidx/compose/ui/graphics/vector/ImageVector)
- [Canvas in Compose](https://developer.android.com/jetpack/compose/graphics/draw/overview)
- [SVG Path Commands](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths)
