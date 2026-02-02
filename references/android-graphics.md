# Android Graphics & Icons

Guide to icons, vector graphics, and custom drawing in Jetpack Compose.

## Table of Contents
1. [Material Symbols Icons](#material-symbols-icons)
2. [ImageVector Patterns](#imagevector-patterns)
3. [Custom Drawing with Canvas](#custom-drawing-with-canvas)
4. [Performance Optimizations](#performance-optimizations)

## Material Symbols Icons

Material Symbols is Google's current icon set (2,500+ glyphs) with variable font support.

### Why Material Symbols?

- **Modern**: Supersedes deprecated Material Icons library
- **Flexible**: Adjustable weight, fill, grade, and optical size
- **Performant**: Doesn't increase build time like the old `androidx.compose.material.icons` library
- **Consistent**: Follows Material Design 3 guidelines

### Downloading Icons

**Option 1: Using Iconify API (Recommended for automation)**

```bash
# Download icon as SVG using curl
curl -o app/src/main/res/drawable/ic_lock.xml \
  "https://api.iconify.design/material-symbols:lock.svg?download=true"

curl -o app/src/main/res/drawable/ic_person.xml \
  "https://api.iconify.design/material-symbols:person.svg?download=true"

curl -o app/src/main/res/drawable/ic_settings.xml \
  "https://api.iconify.design/material-symbols:settings.svg?download=true"

# With customization (outlined style)
curl -o app/src/main/res/drawable/ic_home_outlined.xml \
  "https://api.iconify.design/material-symbols:home-outline.svg?download=true"
```

**Option 2: Using Google Fonts Material Symbols**

1. Go to https://fonts.google.com/icons
2. Search for icon (e.g., "lock", "person", "settings")
3. Click icon → Download (downloads SVG)
4. Convert SVG to Android Vector Drawable:
   - Use Android Studio: Right-click `res/drawable` → New → Vector Asset → Local file
   - Or use online converter: https://svg2vector.com/
5. Place resulting XML in `app/src/main/res/drawable/`

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
    // ✅ Recommended: Using Material Symbols
    Icon(
        painter = painterResource(R.drawable.ic_lock),
        contentDescription = stringResource(R.string.lock_icon),
        modifier = Modifier.size(24.dp),
        tint = Color.Unspecified // Use SVG colors
    )
    
    // With theme color
    Icon(
        painter = painterResource(R.drawable.ic_settings),
        contentDescription = stringResource(R.string.settings_icon),
        tint = MaterialTheme.colorScheme.primary
    )
}

// ❌ Avoid: Deprecated Material Icons library
// import androidx.compose.material.icons.Icons
// import androidx.compose.material.icons.filled.Lock
// Icon(Icons.Default.Lock, contentDescription = null) // Don't use this!
```

**Why avoid `Icons.Default.*`?**
- No longer maintained by Google
- Contains older Material Design 2 look
- Significantly increases build time
- Missing many modern icons

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

## ImageVector Patterns

`ImageVector` is Compose's native format for vector graphics, offering pure Kotlin definitions without XML.

### Why ImageVector?

- **Pure Kotlin**: No XML parsing overhead
- **Type-safe**: Compile-time checking
- **Performant**: Lightweight, GPU-accelerated
- **Dynamic**: Generate icons programmatically

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

| Command | Description | Example |
|---------|-------------|---------|
| `moveTo(x, y)` | Move pen without drawing | `moveTo(10f, 10f)` |
| `lineTo(x, y)` | Draw line to point | `lineTo(20f, 20f)` |
| `horizontalLineTo(x)` | Horizontal line | `horizontalLineTo(50f)` |
| `verticalLineTo(y)` | Vertical line | `verticalLineTo(50f)` |
| `curveTo(...)` | Cubic Bézier curve (absolute) | `curveTo(10f, 20f, 30f, 40f, 50f, 60f)` |
| `curveToRelative(...)` | Cubic Bézier curve (relative) | `curveToRelative(10f, 20f, 30f, 40f, 50f, 60f)` |
| `reflectiveCurveTo(...)` | Smooth curve continuation | `reflectiveCurveTo(30f, 40f, 50f, 60f)` |
| `quadTo(...)` | Quadratic Bézier curve | `quadTo(30f, 20f, 50f, 40f)` |
| `arcTo(...)` | Elliptical arc | `arcTo(10f, 10f, 0f, false, true, 20f, 20f)` |
| `close()` | Close path to start | `close()` |

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

### Performance: drawWithCache vs drawBehind

```kotlin
// ✅ Good: Expensive operations cached
@Composable
fun CachedDrawing() {
    Box(
        modifier = Modifier.drawWithCache {
            val gradient = createExpensiveGradient() // Cached
            val path = createComplexPath() // Cached
            
            onDrawBehind {
                drawPath(path, brush = gradient)
            }
        }
    )
}

// ❌ Bad: Recalculated every frame
@Composable
fun UncachedDrawing() {
    Box(
        modifier = Modifier.drawBehind {
            val gradient = createExpensiveGradient() // ❌ Recreated every draw
            val path = createComplexPath() // ❌ Recreated every draw
            drawPath(path, brush = gradient)
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
    // ✅ Icon only recreated when isActive changes
    val icon = remember(isActive) {
        createAnimatedIcon(isActive)
    }
    
    Image(imageVector = icon, contentDescription = null)
}

@Composable
fun DerivedIcon(data: List<Int>) {
    // ✅ Icon only recreated when sum changes, not when list instance changes
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
    // ✅ Lazy initialization
    val Home: ImageVector by lazy { createHomeIcon() }
    val Settings: ImageVector by lazy { createSettingsIcon() }
    val Profile: ImageVector by lazy { createProfileIcon() }
    
    // ❌ Avoid: Eager initialization
    // val All = listOf(createHomeIcon(), createSettingsIcon(), ...) // Creates all immediately
}
```

## Best Practices

### DO ✅
- Use Material Symbols from Google Fonts (not deprecated library)
- Download icons via Iconify API for automation
- Use `ImageVector` for programmatic/dynamic icons
- Cache generated `ImageVector` instances
- Use `drawWithCache` for expensive drawing operations
- Layer paths from back to front
- Use alpha for shadows and highlights
- Organize icons in centralized objects
- Use `remember` to avoid unnecessary recreations

### DON'T ❌
- Use deprecated `androidx.compose.material.icons` library
- Generate `ImageVector` in `@Composable` without caching
- Use `drawBehind` for expensive operations (use `drawWithCache`)
- Hardcode theme-specific colors in icons
- Create custom icons for standard Material Symbols
- Mix absolute and relative path coordinates unnecessarily
- Forget to `close()` paths

## Additional Resources

- [Material Symbols](https://fonts.google.com/icons)
- [Iconify API](https://api.iconify.design/)
- [Compose Graphics API](https://developer.android.com/jetpack/compose/graphics)
- [ImageVector Reference](https://developer.android.com/reference/kotlin/androidx/compose/ui/graphics/vector/ImageVector)
- [Canvas in Compose](https://developer.android.com/jetpack/compose/graphics/draw/overview)
- [SVG Path Commands](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths)
