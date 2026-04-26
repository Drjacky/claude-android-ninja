# Android Accessibility (Compose)

Required target: **WCAG 2.2 Level AA** plus the Android-specific rules below (48dp touch targets, TalkBack semantics, Material 3 contrast tokens). WCAG 2.2 is backwards-compatible with 2.1; every 2.1 AA criterion still applies.

## Table of Contents
1. [WCAG 2.2 Criteria That Apply Here](#wcag-22-criteria-that-apply-here)
2. [Semantic Properties](#semantic-properties)
3. [Touch Target Sizes](#touch-target-sizes)
4. [Screen Reader Navigation](#screen-reader-navigation)
5. [Color & Visual Accessibility](#color--visual-accessibility)
6. [Focus Management](#focus-management)
7. [Common Patterns](#common-patterns)
8. [Testing Accessibility](#testing-accessibility)

## WCAG 2.2 Criteria That Apply Here

WCAG 2.2 adds nine success criteria on top of 2.1. Required on Android Compose:

| Criterion                                 | Rule                                                                                                                                                               | Where it is handled                                                                                                  |
|-------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| 2.4.11 Focus Not Obscured (Minimum)       | A focused element must not be fully hidden by author-created overlays (bottom sheets, IME, snackbars).                                                             | `#focus-management`; apply `Modifier.imePadding()` and inset-aware Scaffolds (see `references/compose-patterns.md`). |
| 2.5.7 Dragging Movements                  | Every drag gesture must have a single-pointer alternative (tap, long-press, button).                                                                               | Sliders, reorderable lists, maps, swipe-to-dismiss. Provide explicit buttons.                                        |
| 2.5.8 Target Size (Minimum)               | Interactive targets must be at least 24 × 24 CSS px.                                                                                                               | Android's 48dp × 48dp rule is stricter; enforce 48dp. See `#touch-target-sizes`.                                     |
| 3.2.6 Consistent Help                     | Help mechanisms (contact, chat, FAQ) must appear in the same relative order on every screen.                                                                       | App-level navigation, not per-screen.                                                                                |
| 3.3.7 Redundant Entry                     | Do not ask the user for the same info twice in one session. Prefill or pull from state.                                                                            | Multi-step forms, signup-then-onboarding flows.                                                                      |
| 3.3.8 Accessible Authentication (Minimum) | Do not require a cognitive test (puzzle, exact recall, captcha without alternative) unless another factor exists. Paste and autofill must work on password fields. | Login, signup, password reset. Use Credential Manager - see `references/android-security.md`.                        |

Always-applicable 2.1 AA criteria still in force: **1.4.3 Contrast (Minimum)** and **2.4.7 Focus Visible** - see `#color--visual-accessibility` and `#focus-management`.

## Semantic Properties

Set semantics on every interactive composable. TalkBack reads only the semantics tree.

### Content Description

Required on every non-text interactive element (icons, image buttons, decorative-but-tappable surfaces). Set `contentDescription = null` only when an adjacent text label already conveys the action.

```kotlin
// CORRECT: Descriptive, action-oriented
IconButton(
    onClick = { onDeleteItem(item.id) },
    modifier = Modifier.semantics {
        contentDescription = "Delete ${item.name}"
    }
) {
    Icon(painterResource(R.drawable.ic_delete), contentDescription = null)
}

// CORRECT: Icon already has description
Icon(
    painterResource(R.drawable.ic_home),
    contentDescription = "Home"
)

// WRONG: Missing description
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = null  // Only use null if parent has description
)

// WRONG: Redundant description
Button(onClick = { }) {
    Icon(
        painterResource(R.drawable.ic_save),
        contentDescription = "Save"  // Redundant! Button already has "Save" text
    )
    Text("Save")
}
```

**Rules:**
- **Always provide** `contentDescription` for icons, images, and custom graphics
- **Set to null** if the element is decorative or its parent already describes it
- **Be specific**: "Delete Shopping List" not "Delete"
- **Include state**: "Favorite, added" not just "Favorite"

### Label copy (TalkBack)

TalkBack already announces the **role** (button, image). Labels should describe **purpose**, not control type.

| Use                     | Avoid                  |
|-------------------------|------------------------|
| "Save"                  | "Save button"          |
| "Submit"                | "Click here to submit" |
| "Profile photo of Alex" | "Image" or "Image 1"   |
| "Delete message"        | "Button" (generic)     |

Do not put "tap" or "click" in descriptions (input method varies). Keep labels **short** and **unique in context** (for example "Delete draft" vs "Delete message" when both exist). For **editable fields**, use Material `label` / `placeholder` semantics; do not duplicate the same text in `contentDescription` in a way that makes TalkBack repeat itself.

### State Description

Describes dynamic state changes for screen readers.

```kotlin
@Composable
fun ToggleButton(
    isEnabled: Boolean,
    onToggle: () -> Unit,
    label: String,
    modifier: Modifier = Modifier
) {
    Button(
        onClick = onToggle,
        modifier = modifier.semantics {
            stateDescription = if (isEnabled) "Enabled" else "Disabled"
        }
    ) {
        Text(label)
    }
}

// Usage example: Notification toggle
@Composable
fun NotificationToggle(
    isEnabled: Boolean,
    onToggleNotifications: (Boolean) -> Unit
) {
    var enabled by remember { mutableStateOf(isEnabled) }
    
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .toggleable(
                value = enabled,
                onValueChange = { 
                    enabled = it
                    onToggleNotifications(it)
                },
                role = Role.Switch
            )
            .padding(16.dp)
            .semantics(mergeDescendants = true) {
                stateDescription = if (enabled) {
                    "Notifications enabled"
                } else {
                    "Notifications disabled"
                }
            },
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("Push Notifications", style = MaterialTheme.typography.bodyLarge)
        Switch(
            checked = enabled,
            onCheckedChange = null  // Handled by Row toggleable
        )
    }
}
```

### Role Property

Defines the semantic role of a composable for assistive technologies.

```kotlin
import androidx.compose.ui.semantics.Role

// Built-in roles
Button(
    onClick = { },
    modifier = Modifier.semantics { role = Role.Button }  // Implicit for Button
) { Text("Submit") }

// Custom clickable with explicit role
Box(
    modifier = Modifier
        .clickable(
            onClick = { navigateToProfile() },
            role = Role.Button  // Announces as a button
        )
        .semantics { contentDescription = "View profile" }
) {
    ProfileAvatar()
}

// Checkbox role
Row(
    modifier = Modifier
        .selectable(
            selected = isSelected,
            onClick = { onToggle() },
            role = Role.Checkbox
        )
        .semantics(mergeDescendants = true) {}
) {
    Checkbox(checked = isSelected, onCheckedChange = null)
    Text("Accept terms and conditions")
}

// Tab role for navigation
TabRow(selectedTabIndex = selectedTab) {
    tabs.forEachIndexed { index, tab ->
        Tab(
            selected = selectedTab == index,
            onClick = { onTabSelected(index) },
            modifier = Modifier.semantics { role = Role.Tab }
        ) {
            Text(tab.title)
        }
    }
}
```

**Available Roles:**
- `Role.Button`
- `Role.Checkbox`
- `Role.Switch`
- `Role.RadioButton`
- `Role.Tab`
- `Role.Image`
- `Role.DropdownList`

### Custom Actions

Provide additional actions for screen readers.

```kotlin
@Composable
fun EmailListItem(
    email: Email,
    onMarkAsRead: () -> Unit,
    onArchive: () -> Unit,
    onDelete: () -> Unit,
    modifier: Modifier = Modifier
) {
    ListItem(
        headlineContent = { Text(email.subject) },
        supportingContent = { Text(email.preview) },
        leadingContent = {
            Icon(
                painterResource(
                    if (email.isRead) R.drawable.ic_mail_open 
                    else R.drawable.ic_mail
                ),
                contentDescription = if (email.isRead) "Read" else "Unread"
            )
        },
        modifier = modifier
            .clickable { /* Open email */ }
            .semantics {
                // Custom actions accessible via TalkBack menu
                customActions = listOf(
                    CustomAccessibilityAction("Mark as read") {
                        onMarkAsRead()
                        true
                    },
                    CustomAccessibilityAction("Archive") {
                        onArchive()
                        true
                    },
                    CustomAccessibilityAction("Delete") {
                        onDelete()
                        true
                    }
                )
            }
    )
}
```

### Merge Descendants vs ClearAndSetSemantics

Use `mergeDescendants = true` when you want to combine the semantics of child elements into a single announcement (e.g., a card with a title and subtitle).

Use `clearAndSetSemantics` when you want to completely replace the semantics of child elements with a custom description, ignoring what the children would normally announce.

```kotlin
// CORRECT: Merge card content for single announcement
@Composable
fun ArticleCard(article: Article, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.semantics(mergeDescendants = true) {
            // Screen reader will read this, plus any other semantics from children
            // that aren't explicitly overridden here.
            contentDescription = "${article.title}. ${article.author}. ${article.date}"
        }
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(article.title, style = MaterialTheme.typography.titleMedium)
            Text(article.author, style = MaterialTheme.typography.bodySmall)
            Text(article.date, style = MaterialTheme.typography.bodySmall)
        }
    }
}

// CORRECT: Merge form label and input
@Composable
fun LabeledTextField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    error: String? = null,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier.semantics(mergeDescendants = true) {}) {
        Text(label, style = MaterialTheme.typography.labelMedium)
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            isError = error != null,
            modifier = Modifier.fillMaxWidth()
        )
        if (error != null) {
            Text(
                text = error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}
```

### Clear Semantics

Hide or override default semantics when needed.

```kotlin
// CORRECT: Hide decorative image from screen readers
Image(
    painterResource(R.drawable.decorative_pattern),
    contentDescription = null,
    modifier = Modifier.semantics { invisibleToUser() }
)

// CORRECT: Clear default semantics for custom implementation
Box(
    modifier = Modifier
        .clearAndSetSemantics {
            // Completely replace default semantics. Children are ignored.
            contentDescription = "Custom rating: 4 out of 5 stars"
            role = Role.Button
        }
        .clickable { showRatingDialog() }
) {
    CustomStarRating(rating = 4)
}
```

### Semantic Keys

Compose uses `SemanticsPropertyKey` to define semantic properties. You can create custom keys for specific use cases, though the built-in ones (`contentDescription`, `stateDescription`, `role`, etc.) cover most needs.

```kotlin
// Define a custom semantic key
val IsFavoriteKey = SemanticsPropertyKey<Boolean>("IsFavorite")

// Apply it
Modifier.semantics {
    set(IsFavoriteKey, true)
}
```

## Touch Target Sizes

All interactive elements must have a minimum touch target size of **48dp × 48dp** for accessibility.

### Minimum Touch Targets

```kotlin
// CORRECT: Sufficient touch target
IconButton(
    onClick = { onDeleteClick() }  // IconButton defaults to 48dp
) {
    Icon(painterResource(R.drawable.ic_delete), contentDescription = "Delete")
}

// WRONG: Too small
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = "Settings",
    modifier = Modifier.clickable { }  // Only 24dp by default
)

// CORRECT: Explicit padding to meet minimum
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = "Settings",
    modifier = Modifier
        .clickable { onSettingsClick() }
        .size(24.dp)
        .padding(12.dp)  // Total: 48dp
)

// CORRECT: Minimum touch target with custom size
Box(
    modifier = Modifier
        .clickable { onItemClick() }
        .sizeIn(minWidth = 48.dp, minHeight = 48.dp)  // Enforce minimum
        .padding(8.dp),
    contentAlignment = Alignment.Center
) {
    Icon(
        painterResource(R.drawable.ic_custom),
        contentDescription = "Custom action",
        modifier = Modifier.size(32.dp)
    )
}
```

### Spacing Between Targets

Maintain adequate spacing between interactive elements.

```kotlin
// CORRECT: Proper spacing between actions
Row(
    modifier = Modifier.padding(16.dp),
    horizontalArrangement = Arrangement.spacedBy(8.dp)  // Minimum 8dp spacing
) {
    IconButton(onClick = { onFavorite() }) {
        Icon(painterResource(R.drawable.ic_favorite), "Add to favorites")
    }
    IconButton(onClick = { onShare() }) {
        Icon(painterResource(R.drawable.ic_share), "Share")
    }
    IconButton(onClick = { onDownload() }) {
        Icon(painterResource(R.drawable.ic_download), "Download")
    }
}

// WRONG: Actions too close together
Row(modifier = Modifier.padding(16.dp)) {
    Icon(
        painterResource(R.drawable.ic_favorite),
        contentDescription = "Favorite",
        modifier = Modifier.clickable { }
    )
    Icon(  // Too close to previous icon!
        painterResource(R.drawable.ic_share),
        contentDescription = "Share",
        modifier = Modifier.clickable { }
    )
}
```

### Testing Touch Targets

```kotlin
// In tests: Verify touch target sizes
@Test
fun deleteButton_meetsMinimumTouchTarget() {
    composeTestRule.setContent {
        DeleteButton(onDelete = {})
    }
    
    composeTestRule
        .onNodeWithContentDescription("Delete")
        .assertWidthIsAtLeast(48.dp)
        .assertHeightIsAtLeast(48.dp)
}
```

## Screen Reader Navigation

Control how TalkBack navigates and announces your UI.

### Traversal Order

Control the order in which screen readers navigate elements.

```kotlin
@Composable
fun ProfileHeader(
    name: String,
    bio: String,
    avatarUrl: String,
    onEditProfile: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        // Avatar (traversal order: 1)
        AsyncImage(
            model = avatarUrl,
            contentDescription = "Profile picture",
            modifier = Modifier
                .size(64.dp)
                .clip(CircleShape)
                .semantics { traversalIndex = 0f }  // Visit first
        )
        
        // Name and bio (traversal order: 2)
        Column(
            modifier = Modifier
                .weight(1f)
                .padding(horizontal = 16.dp)
                .semantics { traversalIndex = 1f }  // Visit second
        ) {
            Text(name, style = MaterialTheme.typography.titleLarge)
            Text(bio, style = MaterialTheme.typography.bodyMedium)
        }
        
        // Edit button (traversal order: 3)
        IconButton(
            onClick = onEditProfile,
            modifier = Modifier.semantics { traversalIndex = 2f }  // Visit last
        ) {
            Icon(painterResource(R.drawable.ic_edit), "Edit profile")
        }
    }
}
```

### Heading Structure

Define content hierarchy for screen readers.

```kotlin
@Composable
fun ArticleScreen(article: Article) {
    LazyColumn {
        item {
            // H1: Article title
            Text(
                text = article.title,
                style = MaterialTheme.typography.headlineLarge,
                modifier = Modifier.semantics { heading() }
            )
        }
        
        item {
            // Metadata (not a heading)
            Text("${article.author} · ${article.date}")
        }
        
        items(article.sections) { section ->
            Column {
                // H2: Section titles
                Text(
                    text = section.title,
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.semantics { heading() }
                )
                Text(section.content)
            }
        }
    }
}
```

### Live Region Announcements

Announce dynamic content changes to screen readers.

**Modes:** In `Modifier.semantics`, `liveRegion = LiveRegionMode.Polite` queues announcements when the user is idle; `LiveRegionMode.Assertive` interrupts — reserve it for critical errors. Default to **polite** live regions on the composable that changed, or rely on **stateDescription** / **error** semantics so TalkBack picks up updates without extra noise.

**Avoid** firing raw `AccessibilityEvent.TYPE_ANNOUNCEMENT` for every minor UI tick. Drive updates through semantics; emit one-off announcements only when no stable node can carry the change.

```kotlin
@Composable
fun ToastMessage(message: String?, onDismiss: () -> Unit) {
    val context = LocalContext.current
    
    LaunchedEffect(message) {
        message?.let {
            // Announce to screen reader immediately
            val announcement = android.view.accessibility.AccessibilityEvent.obtain(
                android.view.accessibility.AccessibilityEvent.TYPE_ANNOUNCEMENT
            )
            announcement.text.add(it)
            context.findActivity()?.let { activity ->
                activity.window.decorView.sendAccessibilityEvent(announcement)
            }
            
            delay(3.seconds)
            onDismiss()
        }
    }
    
    if (message != null) {
        Snackbar(
            modifier = Modifier.semantics {
                liveRegion = LiveRegionMode.Polite
            }
        ) {
            Text(message)
        }
    }
}

// ViewModel announcing state changes
@HiltViewModel
class ItemsViewModel @Inject constructor(
    private val repository: ItemsRepository
) : ViewModel() {
    private val _toastMessage = MutableSharedFlow<String>(replay = 0)
    val toastMessage: SharedFlow<String> = _toastMessage.asSharedFlow()
    
    fun deleteItem(itemId: String) {
        viewModelScope.launch {
            repository.deleteItem(itemId)
                .onSuccess {
                    _toastMessage.emit("Item deleted")  // Announced by screen reader
                }
                .onFailure {
                    _toastMessage.emit("Failed to delete item")
                }
        }
    }
}
```

### Skip to Content

Allow users to bypass repetitive navigation.

```kotlin
@Composable
fun MainScreen(
    showTopBar: Boolean = true,
    topBarContent: @Composable () -> Unit = {},
    content: @Composable () -> Unit
) {
    Scaffold(
        topBar = {
            if (showTopBar) {
                Column {
                    topBarContent()
                    
                    // Skip to main content button (hidden visually)
                    TextButton(
                        onClick = { /* Focus on content */ },
                        modifier = Modifier
                            .semantics { contentDescription = "Skip to main content" }
                            .size(1.dp)  // Visually hidden but accessible
                            .alpha(0f)
                    ) {
                        Text("Skip to content")
                    }
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .padding(padding)
                .semantics { heading() }  // Mark main content
        ) {
            content()
        }
    }
}
```

## Color & Visual Accessibility

Ensure sufficient color contrast and don't rely on color alone.

### Color Contrast Requirements

**WCAG 2.2 Level AA (1.4.3 Contrast Minimum, 1.4.11 Non-text Contrast):**
- **Normal text:** 4.5:1 contrast ratio
- **Large text** (18pt+/14pt+ bold): 3:1 contrast ratio
- **UI components and graphical objects:** 3:1 contrast ratio

```kotlin
@Composable
fun AccessibleButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    // Material 3 automatically provides sufficient contrast
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.primary,  // Sufficient contrast
            contentColor = MaterialTheme.colorScheme.onPrimary
        ),
        modifier = modifier
    ) {
        Text(text)
    }
}

// WRONG: Insufficient contrast
@Composable
fun PoorContrastText() {
    Text(
        text = "Hard to read",
        color = Color(0xFFCCCCCC),  // Light gray on white background
        modifier = Modifier.background(Color.White)
    )
}

// CORRECT: Check contrast programmatically
@Composable
fun DynamicContrastText(
    text: String,
    backgroundColor: Color
) {
    val textColor = if (backgroundColor.luminance() > 0.5) {
        Color.Black  // Dark text on light background
    } else {
        Color.White  // Light text on dark background
    }
    
    Text(
        text = text,
        color = textColor,
        modifier = Modifier.background(backgroundColor)
    )
}
```

### Don't Rely on Color Alone

Use multiple indicators (color + icon + text).

```kotlin
// WRONG: Color only
@Composable
fun StatusBadge(status: Status) {
    Box(
        modifier = Modifier
            .size(12.dp)
            .background(
                when (status) {
                    Status.Success -> Color.Green
                    Status.Error -> Color.Red
                    Status.Warning -> Color.Yellow
                },
                CircleShape
            )
    )
}

// CORRECT: Color + Icon + Text
@Composable
fun AccessibleStatusBadge(status: Status) {
    val (icon, color, text) = when (status) {
        Status.Success -> Triple(R.drawable.ic_check, Color.Green, "Success")
        Status.Error -> Triple(R.drawable.ic_error, Color.Red, "Error")
        Status.Warning -> Triple(R.drawable.ic_warning, Color.Yellow, "Warning")
    }
    
    Row(
        modifier = Modifier.semantics(mergeDescendants = true) {
            contentDescription = "$text status"
        },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Icon(
            painterResource(icon),
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(16.dp)
        )
        Text(text, style = MaterialTheme.typography.labelSmall)
    }
}

// CORRECT: Form validation with multiple indicators
@Composable
fun AccessibleTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    error: String? = null,
    modifier: Modifier = Modifier
) {
    Column(modifier = modifier) {
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            label = { Text(label) },
            isError = error != null,
            trailingIcon = if (error != null) {
                {
                    Icon(
                        painterResource(R.drawable.ic_error),
                        contentDescription = "Error",
                        tint = MaterialTheme.colorScheme.error
                    )
                }
            } else null,
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (error != null) {
                        // Announce error state
                        error(error)
                    }
                }
        )
        
        if (error != null) {
            Row(
                modifier = Modifier.padding(start = 16.dp, top = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    painterResource(R.drawable.ic_error),
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.error,
                    modifier = Modifier.size(16.dp)
                )
                Text(
                    text = error,
                    color = MaterialTheme.colorScheme.error,
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}
```

### Dark Mode & High Contrast

Support system-wide accessibility settings.

```kotlin
@Composable
fun ThemedContent() {
    // Material 3 automatically handles dark/light theme
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) {
            darkColorScheme()
        } else {
            lightColorScheme()
        }
    ) {
        // Content automatically adapts
        Surface(
            color = MaterialTheme.colorScheme.background,
            contentColor = MaterialTheme.colorScheme.onBackground
        ) {
            AppContent()
        }
    }
}

// Check for high contrast mode (Android 14+)
@Composable
fun HighContrastAwareButton(
    text: String,
    onClick: () -> Unit
) {
    val configuration = LocalConfiguration.current
    val isHighContrast = remember(configuration) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
            configuration.isScreenWideColorGamut  // Proxy for high contrast
        } else {
            false
        }
    }
    
    Button(
        onClick = onClick,
        colors = ButtonDefaults.buttonColors(
            containerColor = if (isHighContrast) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.primaryContainer
            }
        )
    ) {
        Text(text)
    }
}
```

## Focus Management

Control keyboard and accessibility focus.

### Focus Order

```kotlin
@Composable
fun LoginForm(
    email: String,
    onEmailChange: (String) -> Unit,
    password: String,
    onPasswordChange: (String) -> Unit,
    onLogin: () -> Unit
) {
    val focusManager = LocalFocusManager.current
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // First field focuses automatically
        OutlinedTextField(
            value = email,
            onValueChange = onEmailChange,
            label = { Text("Email") },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next
            ),
            keyboardActions = KeyboardActions(
                onNext = { focusManager.moveFocus(FocusDirection.Down) }
            ),
            modifier = Modifier.fillMaxWidth()
        )
        
        OutlinedTextField(
            value = password,
            onValueChange = onPasswordChange,
            label = { Text("Password") },
            visualTransformation = PasswordVisualTransformation(),
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = { 
                    focusManager.clearFocus()
                    onLogin()
                }
            ),
            modifier = Modifier.fillMaxWidth()
        )
        
        Button(
            onClick = {
                focusManager.clearFocus()
                onLogin()
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Login")
        }
    }
}
```

### Request Focus

```kotlin
@Composable
fun SearchScreen() {
    val focusRequester = remember { FocusRequester() }
    
    Column {
        OutlinedTextField(
            value = "",
            onValueChange = { },
            label = { Text("Search") },
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester)
        )
        
        // Auto-focus search field when screen appears
        LaunchedEffect(Unit) {
            delay(100.milliseconds)  // Small delay for layout
            focusRequester.requestFocus()
        }
    }
}
```

### Focus Indicators

Ensure visible focus indicators for keyboard navigation.

```kotlin
@Composable
fun AccessibleClickableCard(
    title: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        onClick = onClick,
        modifier = modifier.focusable(),  // Shows focus indicator
        border = BorderStroke(
            width = 2.dp,
            color = MaterialTheme.colorScheme.primary.copy(alpha = 0.5f)
        )
    ) {
        Text(
            text = title,
            modifier = Modifier.padding(16.dp)
        )
    }
}
```

## Common Patterns

Accessibility patterns for common UI components.

### Lists

```kotlin
@Composable
fun AccessibleUserList(
    users: List<User>,
    onUserClick: (User) -> Unit
) {
    LazyColumn(
        modifier = Modifier.semantics {
            // Announce list size to screen readers
            contentDescription = "${users.size} users"
        }
    ) {
        items(users) { user ->
            ListItem(
                headlineContent = { Text(user.name) },
                supportingContent = { Text(user.email) },
                leadingContent = {
                    AsyncImage(
                        model = user.avatarUrl,
                        contentDescription = "${user.name}'s profile picture",
                        modifier = Modifier
                            .size(40.dp)
                            .clip(CircleShape)
                    )
                },
                modifier = Modifier
                    .clickable { onUserClick(user) }
                    .semantics(mergeDescendants = true) {
                        contentDescription = "${user.name}, ${user.email}"
                    }
            )
        }
    }
}
```

### Dialogs

```kotlin
@Composable
fun AccessibleDeleteDialog(
    itemName: String,
    onConfirm: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                "Delete item",
                modifier = Modifier.semantics { heading() }
            )
        },
        text = {
            Text(
                "Are you sure you want to delete \"$itemName\"? This action cannot be undone.",
                modifier = Modifier.semantics {
                    // Make dialog content clear to screen readers
                    liveRegion = LiveRegionMode.Polite
                }
            )
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onConfirm()
                    onDismiss()
                },
                modifier = Modifier.semantics {
                    contentDescription = "Confirm delete $itemName"
                }
            ) {
                Text("Delete")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
        modifier = Modifier.semantics {
            // Announce dialog appearance
            liveRegion = LiveRegionMode.Polite
        }
    )
}
```

### Bottom Navigation

```kotlin
@Composable
fun AccessibleBottomNavigation(
    selectedRoute: String,
    onNavigate: (String) -> Unit
) {
    NavigationBar {
        NavigationBarItem(
            selected = selectedRoute == "home",
            onClick = { onNavigate("home") },
            icon = {
                Icon(
                    painterResource(R.drawable.ic_home),
                    contentDescription = null  // Label provides description
                )
            },
            label = { Text("Home") },
            modifier = Modifier.semantics(mergeDescendants = true) {
                contentDescription = if (selectedRoute == "home") {
                    "Home, selected"
                } else {
                    "Home"
                }
            }
        )
        
        NavigationBarItem(
            selected = selectedRoute == "search",
            onClick = { onNavigate("search") },
            icon = {
                Icon(
                    painterResource(R.drawable.ic_search),
                    contentDescription = null
                )
            },
            label = { Text("Search") },
            modifier = Modifier.semantics(mergeDescendants = true) {
                contentDescription = if (selectedRoute == "search") {
                    "Search, selected"
                } else {
                    "Search"
                }
            }
        )
        
        NavigationBarItem(
            selected = selectedRoute == "profile",
            onClick = { onNavigate("profile") },
            icon = {
                Icon(
                    painterResource(R.drawable.ic_person),
                    contentDescription = null
                )
            },
            label = { Text("Profile") },
            modifier = Modifier.semantics(mergeDescendants = true) {
                contentDescription = if (selectedRoute == "profile") {
                    "Profile, selected"
                } else {
                    "Profile"
                }
            }
        )
    }
}
```

### Forms with Validation

```kotlin
@Composable
fun AccessibleRegistrationForm(
    viewModel: RegistrationViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val focusManager = LocalFocusManager.current
    
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(
            text = "Create Account",
            style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.semantics { heading() }
        )
        
        // Name field
        OutlinedTextField(
            value = uiState.name,
            onValueChange = { viewModel.onNameChange(it) },
            label = { Text("Full Name *") },
            isError = uiState.nameError != null,
            supportingText = uiState.nameError?.let { 
                { 
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            painterResource(R.drawable.ic_error),
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.error
                        )
                        Text(it)
                    }
                } 
            },
            keyboardOptions = KeyboardOptions(
                imeAction = ImeAction.Next
            ),
            keyboardActions = KeyboardActions(
                onNext = { focusManager.moveFocus(FocusDirection.Down) }
            ),
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (uiState.nameError != null) {
                        error(uiState.nameError!!)
                    }
                }
        )
        
        // Email field
        OutlinedTextField(
            value = uiState.email,
            onValueChange = { viewModel.onEmailChange(it) },
            label = { Text("Email *") },
            isError = uiState.emailError != null,
            supportingText = uiState.emailError?.let {
                {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            painterResource(R.drawable.ic_error),
                            contentDescription = null,
                            modifier = Modifier.size(16.dp),
                            tint = MaterialTheme.colorScheme.error
                        )
                        Text(it)
                    }
                }
            },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Email,
                imeAction = ImeAction.Next
            ),
            keyboardActions = KeyboardActions(
                onNext = { focusManager.moveFocus(FocusDirection.Down) }
            ),
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (uiState.emailError != null) {
                        error(uiState.emailError!!)
                    }
                }
        )
        
        // Password field with strength indicator
        OutlinedTextField(
            value = uiState.password,
            onValueChange = { viewModel.onPasswordChange(it) },
            label = { Text("Password *") },
            visualTransformation = PasswordVisualTransformation(),
            isError = uiState.passwordError != null,
            supportingText = {
                Column {
                    if (uiState.passwordError != null) {
                        Row(
                            horizontalArrangement = Arrangement.spacedBy(4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                painterResource(R.drawable.ic_error),
                                contentDescription = null,
                                modifier = Modifier.size(16.dp),
                                tint = MaterialTheme.colorScheme.error
                            )
                            Text(uiState.passwordError!!)
                        }
                    } else {
                        Text("Password strength: ${uiState.passwordStrength}")
                    }
                }
            },
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Password,
                imeAction = ImeAction.Done
            ),
            keyboardActions = KeyboardActions(
                onDone = {
                    focusManager.clearFocus()
                    viewModel.onSubmit()
                }
            ),
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (uiState.passwordError != null) {
                        error(uiState.passwordError!!)
                    } else {
                        stateDescription = "Password strength: ${uiState.passwordStrength}"
                    }
                }
        )
        
        // Submit button
        Button(
            onClick = {
                focusManager.clearFocus()
                viewModel.onSubmit()
            },
            enabled = uiState.isValid && !uiState.isLoading,
            modifier = Modifier
                .fillMaxWidth()
                .semantics {
                    if (!uiState.isValid) {
                        stateDescription = "Form has errors. Please fix them to continue."
                    }
                }
        ) {
            if (uiState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("Create Account")
            }
        }
    }
}
```

## Testing Accessibility

Test accessibility with automated tools and manual verification.

### Compose Testing

```kotlin
@Test
fun loginButton_hasAccessibleTouchTarget() {
    composeTestRule.setContent {
        LoginScreen()
    }
    
    composeTestRule
        .onNodeWithText("Login")
        .assertWidthIsAtLeast(48.dp)
        .assertHeightIsAtLeast(48.dp)
}

@Test
fun deleteIcon_hasContentDescription() {
    composeTestRule.setContent {
        ItemCard(item = testItem, onDelete = {})
    }
    
    composeTestRule
        .onNodeWithContentDescription("Delete ${testItem.name}")
        .assertExists()
}

@Test
fun formError_isAnnounced() {
    composeTestRule.setContent {
        EmailField(
            value = "invalid",
            onValueChange = {},
            error = "Invalid email address"
        )
    }
    
    composeTestRule
        .onNodeWithText("Email")
        .assert(
            SemanticsMatcher.expectValue(
                SemanticsProperties.Error,
                "Invalid email address"
            )
        )
}

@Test
fun toggleButton_announcesState() {
    var isEnabled by mutableStateOf(false)
    
    composeTestRule.setContent {
        ToggleButton(
            isEnabled = isEnabled,
            onToggle = { isEnabled = !isEnabled },
            label = "Notifications"
        )
    }
    
    // Initial state
    composeTestRule
        .onNodeWithText("Notifications")
        .assert(
            SemanticsMatcher.expectValue(
                SemanticsProperties.StateDescription,
                "Disabled"
            )
        )
    
    // After toggle
    composeTestRule
        .onNodeWithText("Notifications")
        .performClick()
    
    composeTestRule
        .onNodeWithText("Notifications")
        .assert(
            SemanticsMatcher.expectValue(
                SemanticsProperties.StateDescription,
                "Enabled"
            )
        )
}
```

### Espresso accessibility checks (instrumented)

For **View-based** or hybrid screens, enable Espresso's built-in checks so basic a11y violations fail tests early. Add the `espresso-accessibility` artifact (see `references/testing.md` and your version catalog), then:

```kotlin
import androidx.test.espresso.accessibility.AccessibilityChecks

@Before
fun enableA11yChecks() {
    AccessibilityChecks.enable()
}
```

Compose UI tests assert **semantics** directly for most flows. Use Espresso accessibility checks when `ActivityScenario` / `Espresso` or `AndroidView` interop still owns the surface under test.

### Accessibility Scanner

Use Android Accessibility Scanner for manual testing:

```kotlin
// In debug builds, enable accessibility test mode
@Composable
fun AppContent() {
    if (BuildConfig.DEBUG) {
        // Enable test tags for accessibility scanner
        CompositionLocalProvider(
            LocalInspectionMode provides true
        ) {
            MainContent()
        }
    } else {
        MainContent()
    }
}
```

### Manual Testing Checklist

**Test with TalkBack:**
1. Enable TalkBack in Settings → Accessibility
2. Navigate through each screen
3. Verify all interactive elements are announced
4. Check that images have proper descriptions
5. Confirm form errors are announced
6. Test custom actions in long-press menu

**Test with Switch Access:**
1. Enable Switch Access in Settings → Accessibility
2. Navigate using keyboard or external switch
3. Verify all interactive elements are accessible
4. Check focus order makes sense

**Test with Font Scaling:**
1. Settings → Display → Font size → Largest
2. Verify all text remains readable
3. Check that touch targets don't overlap
4. Ensure no text is cut off

**Test Color Contrast:**
1. Enable high contrast mode (Android 14+)
2. Use Accessibility Scanner app
3. Verify contrast ratios meet WCAG 2.2 AA (1.4.3, 1.4.11)

### Integration with CI/CD

```kotlin
// In app/build.gradle.kts
android {
    lint {
        enable += setOf(
            "ContentDescription",
            "TouchTargetSizeCheck",
            "TextContrastCheck",
            "ClickableViewAccessibility"
        )
        
        // Treat accessibility issues as errors in CI
        abortOnError = System.getenv("CI") == "true"
    }
}
```

## Rules

**Required:**
- Provide `contentDescription` for all icons and images
- Write concise labels (purpose, not "button" / "tap here")
- Ensure 48dp × 48dp minimum touch targets
- Use `mergeDescendants` to group related content
- Announce state changes with `stateDescription`
- Support dark mode and high contrast
- Test with TalkBack enabled

**Forbidden:**
- Rely on color alone to convey information
- Use small touch targets (< 48dp)
- Ignore form validation error announcements
- Use `contentDescription` on decorative images
- Forget to test with accessibility services enabled
- Hardcode text (use string resources for i18n)

## References

- Official Android Accessibility: https://developer.android.com/guide/topics/ui/accessibility
- Compose Accessibility: https://developer.android.com/jetpack/compose/accessibility
- WCAG 2.2 Guidelines: https://www.w3.org/WAI/WCAG22/quickref/
- WCAG 2.2 What's New: https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- Material Design Accessibility: https://m3.material.io/foundations/accessible-design/overview
- TalkBack User Guide: https://support.google.com/accessibility/android/answer/6283677
