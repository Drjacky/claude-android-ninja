# Android Accessibility (Compose)

Modern accessibility patterns for Jetpack Compose applications. Following WCAG 2.1 Level AA guidelines and Android accessibility best practices for production apps.

Accessibility is not optional-it's required for Google Play, benefits all users, and is often a legal requirement. Build it in from the start.

## Table of Contents
1. [Semantic Properties](#semantic-properties)
2. [Touch Target Sizes](#touch-target-sizes)
3. [Screen Reader Navigation](#screen-reader-navigation)
4. [Color & Visual Accessibility](#color--visual-accessibility)
5. [Focus Management](#focus-management)
6. [Common Patterns](#common-patterns)
7. [Testing Accessibility](#testing-accessibility)

## Semantic Properties

Compose provides semantic properties that screen readers (TalkBack) use to describe UI to users.

### Content Description

The most important semantic property. Describes non-text elements to screen readers.

```kotlin
// ✅ Good: Descriptive, action-oriented
IconButton(
    onClick = { onDeleteItem(item.id) },
    modifier = Modifier.semantics {
        contentDescription = "Delete ${item.name}"
    }
) {
    Icon(painterResource(R.drawable.ic_delete), contentDescription = null)
}

// ✅ Good: Icon already has description
Icon(
    painterResource(R.drawable.ic_home),
    contentDescription = "Home"
)

// ❌ Bad: Missing description
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = null  // Only use null if parent has description
)

// ❌ Bad: Redundant description
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

### Merge Descendants

Combine multiple elements into a single accessibility node.

```kotlin
// ✅ Good: Merge card content for single announcement
@Composable
fun ArticleCard(article: Article, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.semantics(mergeDescendants = true) {
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

// ✅ Good: Merge form label and input
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
// ✅ Good: Hide decorative image from screen readers
Image(
    painterResource(R.drawable.decorative_pattern),
    contentDescription = null,
    modifier = Modifier.semantics { invisibleToUser() }
)

// ✅ Good: Clear default semantics for custom implementation
Box(
    modifier = Modifier
        .clearAndSetSemantics {
            // Completely replace default semantics
            contentDescription = "Custom rating: 4 out of 5 stars"
            role = Role.Button
        }
        .clickable { showRatingDialog() }
) {
    CustomStarRating(rating = 4)
}
```

## Touch Target Sizes

All interactive elements must have a minimum touch target size of **48dp × 48dp** for accessibility.

### Minimum Touch Targets

```kotlin
// ✅ Good: Sufficient touch target
IconButton(
    onClick = { onDeleteClick() }  // IconButton defaults to 48dp
) {
    Icon(painterResource(R.drawable.ic_delete), contentDescription = "Delete")
}

// ❌ Bad: Too small
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = "Settings",
    modifier = Modifier.clickable { }  // Only 24dp by default
)

// ✅ Good: Explicit padding to meet minimum
Icon(
    painterResource(R.drawable.ic_settings),
    contentDescription = "Settings",
    modifier = Modifier
        .clickable { onSettingsClick() }
        .size(24.dp)
        .padding(12.dp)  // Total: 48dp
)

// ✅ Good: Minimum touch target with custom size
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
// ✅ Good: Proper spacing between actions
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

// ❌ Bad: Actions too close together
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

**WCAG 2.1 Level AA:**
- **Normal text:** 4.5:1 contrast ratio
- **Large text** (18pt+/14pt+ bold): 3:1 contrast ratio
- **UI components:** 3:1 contrast ratio

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

// ❌ Bad: Insufficient contrast
@Composable
fun PoorContrastText() {
    Text(
        text = "Hard to read",
        color = Color(0xFFCCCCCC),  // Light gray on white background
        modifier = Modifier.background(Color.White)
    )
}

// ✅ Good: Check contrast programmatically
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
// ❌ Bad: Color only
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

// ✅ Good: Color + Icon + Text
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

// ✅ Good: Form validation with multiple indicators
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
3. Verify contrast ratios meet WCAG AA standards

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

## Best Practices Summary

**Always:**
- ✅ Provide `contentDescription` for all icons and images
- ✅ Ensure 48dp × 48dp minimum touch targets
- ✅ Use `mergeDescendants` to group related content
- ✅ Announce state changes with `stateDescription`
- ✅ Support dark mode and high contrast
- ✅ Test with TalkBack enabled

**Never:**
- ❌ Rely on color alone to convey information
- ❌ Use small touch targets (< 48dp)
- ❌ Ignore form validation error announcements
- ❌ Use `contentDescription` on decorative images
- ❌ Forget to test with accessibility services enabled
- ❌ Hardcode text (use string resources for i18n)

## References

- Official Android Accessibility: https://developer.android.com/guide/topics/ui/accessibility
- Compose Accessibility: https://developer.android.com/jetpack/compose/accessibility
- WCAG 2.1 Guidelines: https://www.w3.org/WAI/WCAG21/quickref/
- Material Design Accessibility: https://m3.material.io/foundations/accessible-design/overview
- TalkBack User Guide: https://support.google.com/accessibility/android/answer/6283677
