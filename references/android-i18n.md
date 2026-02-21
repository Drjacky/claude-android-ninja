# Internationalization & Localization (i18n/l10n)

This guide covers internationalization (i18n) and localization (l10n) for Android apps, with a Compose-first approach.

## Goals

- Support multiple languages and locales
- Handle RTL (Right-to-Left) layouts automatically
- Format dates, times, and currencies correctly for each locale
- Use plurals and quantity strings correctly
- Test localization thoroughly

## String Resources

### Basic String Resources

```xml
<!-- res/values/strings.xml (default - English) -->
<resources>
    <string name="app_name">My App</string>
    <string name="welcome_message">Welcome, %1$s!</string>
    <string name="login_button">Log In</string>
    <string name="email_hint">Email address</string>
</resources>

<!-- res/values-es/strings.xml (Spanish) -->
<resources>
    <string name="app_name">Mi App</string>
    <string name="welcome_message">¡Bienvenido, %1$s!</string>
    <string name="login_button">Iniciar sesión</string>
    <string name="email_hint">Correo electrónico</string>
</resources>

<!-- res/values-fa/strings.xml (Persian/Farsi - RTL) -->
<resources>
    <string name="app_name">برنامه من</string>
    <string name="welcome_message">خوش آمدید، %1$s!</string>
    <string name="login_button">ورود</string>
    <string name="email_hint">آدرس ایمیل</string>
</resources>
```

### Using String Resources in Compose

```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource

@Composable
fun AuthLoginScreen() {
    Column {
        Text(stringResource(R.string.welcome_message, "John"))
        
        Button(onClick = { /* ... */ }) {
            Text(stringResource(R.string.login_button))
        }
        
        OutlinedTextField(
            value = email,
            onValueChange = { email = it },
            label = { Text(stringResource(R.string.email_hint)) }
        )
    }
}
```

### Parameterized Strings

```xml
<!-- res/values/strings.xml -->
<string name="user_greeting">Hello, %1$s!</string>
<string name="items_selected">%1$d of %2$d items selected</string>
<string name="download_progress">Downloading %1$s (%2$d%%)</string>
```

```kotlin
@Composable
fun ProfileScreen(userName: String) {
    Text(stringResource(R.string.user_greeting, userName))
}

@Composable
fun SelectionStatus(selected: Int, total: Int) {
    Text(stringResource(R.string.items_selected, selected, total))
}
```

## Plurals (Quantity Strings)

### Defining Plurals

```xml
<!-- res/values/plurals.xml -->
<resources>
    <plurals name="notification_count">
        <item quantity="zero">No notifications</item>
        <item quantity="one">1 notification</item>
        <item quantity="other">%d notifications</item>
    </plurals>
    
    <plurals name="minutes_ago">
        <item quantity="one">1 minute ago</item>
        <item quantity="other">%d minutes ago</item>
    </plurals>
</resources>

<!-- res/values-ar/plurals.xml (Arabic has more plural forms) -->
<resources>
    <plurals name="notification_count">
        <item quantity="zero">لا توجد إشعارات</item>
        <item quantity="one">إشعار واحد</item>
        <item quantity="two">إشعاران</item>
        <item quantity="few">%d إشعارات</item>
        <item quantity="many">%d إشعارًا</item>
        <item quantity="other">%d إشعار</item>
    </plurals>
</resources>

<!-- res/values-ru/plurals.xml (Russian also has complex plural rules) -->
<resources>
    <plurals name="notification_count">
        <item quantity="one">%d уведомление</item>
        <item quantity="few">%d уведомления</item>
        <item quantity="many">%d уведомлений</item>
        <item quantity="other">%d уведомлений</item>
    </plurals>
</resources>
```

### Using Plurals in Compose

```kotlin
import androidx.compose.ui.res.pluralStringResource

@Composable
fun NotificationBadge(count: Int) {
    Text(
        text = pluralStringResource(
            R.plurals.notification_count,
            count,
            count
        )
    )
}

@Composable
fun TimestampText(minutesAgo: Int) {
    Text(
        text = pluralStringResource(
            R.plurals.minutes_ago,
            minutesAgo,
            minutesAgo
        )
    )
}
```

**Note**: The first `count` parameter is the quantity for plural selection, the second `count` is the formatting argument for `%d`.

## RTL (Right-to-Left) Support

### Automatic RTL in Compose

Compose automatically handles RTL layout for most components. Enable RTL support in your manifest:

```xml
<!-- AndroidManifest.xml -->
<application
    android:supportsRtl="true"
    ... >
</application>
```

### Layout Direction Awareness

```kotlin
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.unit.LayoutDirection

@Composable
fun DirectionAwareContent() {
    val layoutDirection = LocalLayoutDirection.current
    
    when (layoutDirection) {
        LayoutDirection.Ltr -> {
            // Left-to-Right specific layout
        }
        LayoutDirection.Rtl -> {
            // Right-to-Left specific layout
        }
    }
}
```

### RTL-Friendly Modifiers

```kotlin
@Composable
fun ProfileCard(user: User) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        // Use start/end instead of left/right
        Image(
            painter = painterResource(R.drawable.avatar),
            contentDescription = null,
            modifier = Modifier
                .size(48.dp)
                .padding(end = 16.dp) // Automatically flips in RTL
        )
        
        Column(
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = user.name,
                // Text alignment automatically adjusts
                textAlign = TextAlign.Start
            )
        }
    }
}
```

**Best Practices:**
- Use `padding(start = ...)` and `padding(end = ...)` instead of `padding(left = ...)` and `padding(right = ...)`
- Use `Arrangement.Start` and `Arrangement.End` instead of `Arrangement.Left` and `Arrangement.Right`
- Use `TextAlign.Start` and `TextAlign.End` instead of `TextAlign.Left` and `TextAlign.Right`
- Icons that indicate direction should be mirrored in RTL (use `Modifier.mirror()` for custom icons)

### Force RTL for Testing

```kotlin
import androidx.compose.runtime.CompositionLocalProvider

@Preview
@Composable
fun PreviewRTL() {
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        ProfileCard(user = previewUser)
    }
}
```

### Custom Mirroring for Icons

```kotlin
import androidx.compose.ui.draw.scale

@Composable
fun DirectionalIcon() {
    val layoutDirection = LocalLayoutDirection.current
    val mirrorMultiplier = if (layoutDirection == LayoutDirection.Rtl) -1f else 1f
    
    Icon(
        painter = painterResource(R.drawable.ic_arrow_forward),
        contentDescription = null,
        modifier = Modifier.scale(scaleX = mirrorMultiplier, scaleY = 1f)
    )
}
```

## Date & Time Formatting

Use `kotlinx-datetime` for locale-aware date/time formatting.

### Dependencies

```kotlin
// Already in templates/libs.versions.toml.template
implementation(libs.kotlinx.datetime)
```

### Formatting with kotlinx-datetime

```kotlin
import kotlinx.datetime.*
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

class DateTimeFormatter {
    fun formatDate(
        instant: Instant,
        locale: Locale = Locale.getDefault()
    ): String {
        val localDateTime = instant.toLocalDateTime(TimeZone.currentSystemDefault())
        val javaLocalDate = java.time.LocalDate.of(
            localDateTime.year,
            localDateTime.monthNumber,
            localDateTime.dayOfMonth
        )
        
        return DateTimeFormatter
            .ofLocalizedDate(FormatStyle.MEDIUM)
            .withLocale(locale)
            .format(javaLocalDate)
    }
    
    fun formatTime(
        instant: Instant,
        locale: Locale = Locale.getDefault()
    ): String {
        val localDateTime = instant.toLocalDateTime(TimeZone.currentSystemDefault())
        val javaLocalTime = java.time.LocalTime.of(
            localDateTime.hour,
            localDateTime.minute
        )
        
        return DateTimeFormatter
            .ofLocalizedTime(FormatStyle.SHORT)
            .withLocale(locale)
            .format(javaLocalTime)
    }
    
    fun formatDateTime(
        instant: Instant,
        locale: Locale = Locale.getDefault()
    ): String {
        val localDateTime = instant.toLocalDateTime(TimeZone.currentSystemDefault())
        val javaLocalDateTime = java.time.LocalDateTime.of(
            localDateTime.year,
            localDateTime.monthNumber,
            localDateTime.dayOfMonth,
            localDateTime.hour,
            localDateTime.minute
        )
        
        return DateTimeFormatter
            .ofLocalizedDateTime(FormatStyle.MEDIUM)
            .withLocale(locale)
            .format(javaLocalDateTime)
    }
    
    // Relative time (e.g., "2 hours ago")
    fun formatRelativeTime(instant: Instant): String {
        val now = Clock.System.now()
        val duration = now - instant
        
        return when {
            duration.inWholeMinutes < 1 -> "Just now"
            duration.inWholeMinutes < 60 -> "${duration.inWholeMinutes} minutes ago"
            duration.inWholeHours < 24 -> "${duration.inWholeHours} hours ago"
            duration.inWholeDays < 7 -> "${duration.inWholeDays} days ago"
            else -> formatDate(instant)
        }
    }
}
```

### Using in Compose

```kotlin
@Composable
fun PostTimestamp(timestamp: Instant) {
    val formatter = remember { DateTimeFormatter() }
    
    Text(
        text = remember(timestamp) {
            formatter.formatRelativeTime(timestamp)
        }
    )
}
```

### Relative Time with Plurals

```xml
<!-- res/values/plurals.xml -->
<plurals name="minutes_ago">
    <item quantity="one">1 minute ago</item>
    <item quantity="other">%d minutes ago</item>
</plurals>

<plurals name="hours_ago">
    <item quantity="one">1 hour ago</item>
    <item quantity="other">%d hours ago</item>
</plurals>
```

```kotlin
@Composable
fun LocalizedRelativeTime(instant: Instant) {
    val now = Clock.System.now()
    val duration = now - instant
    
    val text = when {
        duration.inWholeMinutes < 1 -> stringResource(R.string.just_now)
        duration.inWholeMinutes < 60 -> {
            val minutes = duration.inWholeMinutes.toInt()
            pluralStringResource(R.plurals.minutes_ago, minutes, minutes)
        }
        duration.inWholeHours < 24 -> {
            val hours = duration.inWholeHours.toInt()
            pluralStringResource(R.plurals.hours_ago, hours, hours)
        }
        else -> {
            val formatter = remember { DateTimeFormatter() }
            formatter.formatDate(instant)
        }
    }
    
    Text(text)
}
```

## Currency Formatting

```kotlin
import java.text.NumberFormat
import java.util.Currency
import java.util.Locale

class CurrencyFormatter {
    fun formatCurrency(
        amount: Double,
        currencyCode: String,
        locale: Locale = Locale.getDefault()
    ): String {
        val formatter = NumberFormat.getCurrencyInstance(locale)
        formatter.currency = Currency.getInstance(currencyCode)
        return formatter.format(amount)
    }
    
    fun formatCurrencyCompact(
        amount: Double,
        currencyCode: String,
        locale: Locale = Locale.getDefault()
    ): String {
        return when {
            amount >= 1_000_000 -> {
                val millions = amount / 1_000_000
                "${formatCurrency(millions, currencyCode, locale)}M"
            }
            amount >= 1_000 -> {
                val thousands = amount / 1_000
                "${formatCurrency(thousands, currencyCode, locale)}K"
            }
            else -> formatCurrency(amount, currencyCode, locale)
        }
    }
}
```

```kotlin
@Composable
fun PriceDisplay(amount: Double, currencyCode: String) {
    val formatter = remember { CurrencyFormatter() }
    
    Text(
        text = remember(amount, currencyCode) {
            formatter.formatCurrency(amount, currencyCode)
        }
    )
}
```

## Locale-Specific Resource Qualifiers

### Common Qualifiers

```
res/
├── values/              # Default (English)
├── values-es/           # Spanish
├── values-fa/           # Persian/Farsi (RTL)
├── values-ar/           # Arabic (RTL)
├── values-fr/           # French
├── values-de/           # German
├── values-ja/           # Japanese
├── values-zh-rCN/       # Chinese (Simplified)
├── values-zh-rTW/       # Chinese (Traditional)
├── values-pt-rBR/       # Portuguese (Brazil)
├── values-pt-rPT/       # Portuguese (Portugal)
├── values-night/        # Dark mode (all locales)
├── values-es-night/     # Spanish + Dark mode
├── values-fa-night/     # Persian + Dark mode
└── values-ar-night/     # Arabic + Dark mode
```

### Combining Qualifiers

```
res/
├── drawable/              # Default
├── drawable-night/        # Dark mode
├── drawable-ldrtl/        # RTL layout direction
├── drawable-night-ldrtl/  # Dark mode + RTL
└── drawable-es/           # Spanish locale (if needed)
```

### String Arrays

```xml
<!-- res/values/arrays.xml -->
<resources>
    <string-array name="days_of_week">
        <item>Monday</item>
        <item>Tuesday</item>
        <item>Wednesday</item>
        <item>Thursday</item>
        <item>Friday</item>
        <item>Saturday</item>
        <item>Sunday</item>
    </string-array>
</resources>

<!-- res/values-es/arrays.xml -->
<resources>
    <string-array name="days_of_week">
        <item>Lunes</item>
        <item>Martes</item>
        <item>Miércoles</item>
        <item>Jueves</item>
        <item>Viernes</item>
        <item>Sábado</item>
        <item>Domingo</item>
    </string-array>
</resources>
```

```kotlin
@Composable
fun DayPicker() {
    val days = LocalContext.current.resources.getStringArray(R.array.days_of_week)
    
    LazyColumn {
        items(days) { day ->
            Text(day)
        }
    }
}
```

## String Resource Ownership

With `android.nonTransitiveRClass=true`, each module has its own R class containing only its own resources. Organize string resources by module responsibility:

### Module Organization

- **`core:common`** or **`core:domain`**: Generic error messages, result states used across multiple features
  ```xml
  <!-- core/common/src/main/res/values/strings.xml -->
  <string name="error_unknown">Unknown error occurred</string>
  <string name="error_network">Network connection failed</string>
  <string name="error_timeout">Request timed out</string>
  <string name="loading">Loading...</string>
  ```

- **`core:ui`**: Shared UI component labels, accessibility descriptions, common actions
  ```xml
  <!-- core/ui/src/main/res/values/strings.xml -->
  <string name="action_back">Back</string>
  <string name="action_close">Close</string>
  <string name="action_save">Save</string>
  <string name="theme_light">Light</string>
  <string name="theme_dark">Dark</string>
  <string name="cd_loading">Loading content</string>
  ```

- **`feature:xxx`**: Feature-specific strings (screen titles, labels, messages unique to that feature)
  ```xml
  <!-- feature/products/src/main/res/values/strings.xml -->
  <string name="products_title">Products</string>
  <string name="product_detail_title">Product Details</string>
  <string name="products_empty">No products available</string>
  <string name="product_add_to_cart">Add to Cart</string>
  ```

### Cross-Module Resource Access

When a feature needs to reference resources from another module:

```kotlin
// feature/products/presentation/ProductsListView.kt
import com.example.core.ui.R as CoreUiR
import com.example.feature.products.R

@Composable
fun ProductsListView(state: ProductsUiState) {
    when (state) {
        is Loading -> Text(stringResource(CoreUiR.string.loading))
        is Empty -> Text(stringResource(R.string.products_empty))
        is Error -> Text(stringResource(CoreUiR.string.error_unknown))
        is Success -> ProductsList(state.products)
    }
}
```

**Best practices:**
- **Never duplicate strings** across modules, even if they have the same text
- Use import aliases (`as CoreUiR`) for clarity when accessing cross-module resources
- If multiple features need the same string, move it to `core:common` or `core:ui`
- Feature modules should depend on `core:ui` for shared UI strings
- See [gradle-setup.md](gradle-setup.md#non-transitive-r-classes) for technical details on non-transitive R classes

## Architecture Integration

### Repository Layer

```kotlin
// core/domain/model/LocalizedContent.kt
data class LocalizedContent(
    val titleKey: String,
    val descriptionKey: String,
    val imageUrl: String
)

// core/data/repository/ContentRepository.kt
interface ContentRepository {
    suspend fun getContent(locale: Locale): Result<List<LocalizedContent>>
}

class ContentRepositoryImpl @Inject constructor(
    private val contentApi: ContentApi,
    private val contentDao: ContentDao
) : ContentRepository {
    override suspend fun getContent(locale: Locale): Result<List<LocalizedContent>> {
        return try {
            val languageCode = locale.language
            val response = contentApi.getContent(languageCode)
            contentDao.insertAll(response)
            Result.success(response)
        } catch (e: Exception) {
            // Fallback to cached content
            Result.success(contentDao.getAll())
        }
    }
}
```

### ViewModel Layer

```kotlin
@HiltViewModel
class ContentViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<ContentUiState>(ContentUiState.Loading)
    val uiState: StateFlow<ContentUiState> = _uiState.asStateFlow()
    
    init {
        loadContent()
    }
    
    private fun loadContent() {
        viewModelScope.launch {
            val locale = Locale.getDefault()
            contentRepository.getContent(locale)
                .onSuccess { content ->
                    _uiState.value = ContentUiState.Success(content)
                }
                .onFailure { error ->
                    _uiState.value = ContentUiState.Error(error.message ?: "Unknown error")
                }
        }
    }
}
```

### UI Layer

```kotlin
@Composable
fun ContentScreen(viewModel: ContentViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    when (val state = uiState) {
        is ContentUiState.Loading -> LoadingIndicator()
        is ContentUiState.Success -> ContentList(state.content)
        is ContentUiState.Error -> ErrorMessage(state.message)
    }
}
```

## Testing Localization

### Testing Different Locales

```kotlin
@RunWith(AndroidJUnit4::class)
class LocalizationTest {
    @get:Rule
    val composeTestRule = createComposeRule()
    
    @Test
    fun testEnglishStrings() {
        setLocale(Locale.ENGLISH)
        
        composeTestRule.setContent {
            AuthLoginScreen()
        }
        
        composeTestRule
            .onNodeWithText("Log In")
            .assertIsDisplayed()
    }
    
    @Test
    fun testSpanishStrings() {
        setLocale(Locale("es"))
        
        composeTestRule.setContent {
            AuthLoginScreen()
        }
        
        composeTestRule
            .onNodeWithText("Iniciar sesión")
            .assertIsDisplayed()
    }
    
    @Test
    fun testArabicRTL() {
        setLocale(Locale("ar"))
        
        composeTestRule.setContent {
            ProfileCard(previewUser)
        }
        
        composeTestRule.onRoot().assertLayoutDirectionEquals(LayoutDirection.Rtl)
    }
    
    private fun setLocale(locale: Locale) {
        val config = Configuration(
            InstrumentationRegistry.getInstrumentation()
                .targetContext.resources.configuration
        )
        config.setLocale(locale)
        
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        context.createConfigurationContext(config)
        Locale.setDefault(locale)
    }
}
```

### Testing Plurals

```kotlin
@Test
fun testPlurals() {
    composeTestRule.setContent {
        Column {
            NotificationBadge(count = 0)
            NotificationBadge(count = 1)
            NotificationBadge(count = 5)
        }
    }
    
    composeTestRule
        .onNodeWithText("No notifications")
        .assertIsDisplayed()
    
    composeTestRule
        .onNodeWithText("1 notification")
        .assertIsDisplayed()
    
    composeTestRule
        .onNodeWithText("5 notifications")
        .assertIsDisplayed()
}
```

### Parameterized Tests for Multiple Locales

```kotlin
@RunWith(Parameterized::class)
class LocalizationParameterizedTest(
    private val locale: Locale,
    private val expectedText: String
) {
    companion object {
        @JvmStatic
        @Parameterized.Parameters(name = "{0}")
        fun data() = listOf(
            arrayOf(Locale.ENGLISH, "Log In"),
            arrayOf(Locale("es"), "Iniciar sesión"),
            arrayOf(Locale("fr"), "Se connecter"),
            arrayOf(Locale("de"), "Anmelden")
        )
    }
    
    @get:Rule
    val composeTestRule = createComposeRule()
    
    @Test
    fun testLoginButton() {
        setLocale(locale)
        
        composeTestRule.setContent {
            Button(onClick = {}) {
                Text(stringResource(R.string.login_button))
            }
        }
        
        composeTestRule
            .onNodeWithText(expectedText)
            .assertIsDisplayed()
    }
    
    private fun setLocale(locale: Locale) {
        val config = Configuration()
        config.setLocale(locale)
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        context.createConfigurationContext(config)
        Locale.setDefault(locale)
    }
}
```

### Screenshot Testing for RTL

```kotlin
@Test
fun testRTLScreenshots() {
    val locales = listOf(
        Locale.ENGLISH,
        Locale("ar"), // RTL
        Locale("he")  // RTL
    )
    
    locales.forEach { locale ->
        setLocale(locale)
        
        composeTestRule.setContent {
            ProfileScreen()
        }
        
        // Take screenshot (using Screenshot Testing library)
        composeTestRule
            .onRoot()
            .captureToImage()
            .assertAgainstGolden("profile_screen_${locale.language}")
    }
}
```

## Best Practices

### 1. Always Use String Resources

❌ **Bad:**
```kotlin
Text("Welcome to My App")
Button(onClick = {}) { Text("Submit") }
```

✅ **Good:**
```kotlin
Text(stringResource(R.string.welcome_message))
Button(onClick = {}) { Text(stringResource(R.string.submit_button)) }
```

### 2. Use Plurals for Quantities

❌ **Bad:**
```kotlin
val text = if (count == 1) "$count item" else "$count items"
```

✅ **Good:**
```kotlin
val text = pluralStringResource(R.plurals.item_count, count, count)
```

### 3. Never Concatenate Strings

❌ **Bad:**
```kotlin
Text("Hello " + userName + ", welcome back!")
```

✅ **Good:**
```xml
<string name="welcome_back">Hello %1$s, welcome back!</string>
```
```kotlin
Text(stringResource(R.string.welcome_back, userName))
```

### 4. Use Start/End Instead of Left/Right

❌ **Bad:**
```kotlin
Modifier.padding(left = 16.dp, right = 16.dp)
```

✅ **Good:**
```kotlin
Modifier.padding(start = 16.dp, end = 16.dp)
```

### 5. Test RTL Layouts

Always test with RTL locales (Arabic, Hebrew, Persian):
```kotlin
@Preview(locale = "ar")
@Composable
fun PreviewArabic() {
    MyScreen()
}
```

### 6. Use Locale-Aware Formatting

❌ **Bad:**
```kotlin
Text("Price: $${amount}")
Text("Date: ${year}-${month}-${day}")
```

✅ **Good:**
```kotlin
Text(currencyFormatter.formatCurrency(amount, "USD"))
Text(dateFormatter.formatDate(instant))
```

### 7. Handle Text Expansion

Some languages (German, Finnish) have longer words. Design UI with flexibility:
```kotlin
Button(
    onClick = {},
    modifier = Modifier.widthIn(min = 120.dp) // Allow expansion
) {
    Text(
        text = stringResource(R.string.login_button),
        maxLines = 1,
        overflow = TextOverflow.Ellipsis
    )
}
```

### 8. Provide Context for Translators

```xml
<!-- Add context comments for translators -->
<resources>
    <!-- Button text for logging into the application -->
    <string name="login_button">Log In</string>
    
    <!-- Greeting shown on the home screen. %1$s is the user's first name -->
    <string name="welcome_message">Welcome, %1$s!</string>
</resources>
```

### 9. Use ICU MessageFormat for Complex Plurals

For very complex plural rules, consider using ICU MessageFormat:
```xml
<resources>
    <string name="notification_summary">
        {count, plural,
            =0 {No new notifications}
            =1 {1 new notification}
            other {# new notifications}}
    </string>
</resources>
```

### 10. Avoid Hardcoded Measurements

Some languages (Thai, Japanese) may need different line heights or text sizes:
```kotlin
Text(
    text = stringResource(R.string.description),
    style = MaterialTheme.typography.bodyMedium.copy(
        // Use relative line height instead of absolute
        lineHeight = 1.5.em
    )
)
```

## CI/CD Integration

### Automated String Checks

```yaml
# .github/workflows/i18n-check.yml
name: I18n Checks

on: [pull_request]

jobs:
  check-strings:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check for hardcoded strings
        run: |
          # Find hardcoded strings in Kotlin files
          if grep -r "Text(\"" app/src/main/java/; then
            echo "Found hardcoded strings. Use stringResource() instead."
            exit 1
          fi
      
      - name: Validate all translations exist
        run: |
          # Check that all string keys exist in all locales
          ./scripts/validate_translations.sh
```

## Common Pitfalls

### 1. Forgetting RTL Support

Always enable RTL and test with Arabic/Hebrew:
```xml
<application android:supportsRtl="true">
```

### 2. Using String Concatenation

This breaks word order in other languages. Always use parameterized strings.

### 3. Hardcoding Dates/Times

Always use locale-aware formatters.

### 4. Assuming English Word Order

Different languages have different grammar rules. Use placeholders:
```xml
<!-- English: "5 items found" -->
<string name="search_results">%1$d items found</string>

<!-- Japanese: "5個のアイテムが見つかりました" -->
<string name="search_results">%1$d個のアイテムが見つかりました</string>
```

### 5. Not Testing Text Expansion

German and Finnish translations can be 30-40% longer. Test UI flexibility.

## Related Guides

- [Compose Patterns](compose-patterns.md) - Compose UI patterns including RTL support
- [Testing Guide](testing.md) - Testing strategies including localization tests
- [Kotlin Patterns](kotlin-patterns.md) - String formatting and handling

## External Resources

- [Android Localization](https://developer.android.com/guide/topics/resources/localization)
- [Supporting RTL Languages](https://developer.android.com/training/basics/supporting-devices/languages#CreateRtl)
- [ICU MessageFormat](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
- [kotlinx-datetime](https://github.com/Kotlin/kotlinx-datetime)
