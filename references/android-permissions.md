# Android Runtime Permissions

Practical, Compose-first patterns for requesting permissions in Android apps. This guide follows modern Android best practices and our modular architecture.

All code must align with `references/kotlin-patterns.md` and `references/compose-patterns.md`.

## Table of Contents
1. [Where Permissions Live](#where-permissions-live)
2. [Common Permission Sets](#common-permission-sets)
3. [Requesting Runtime Permissions in Compose](#requesting-runtime-permissions-in-compose)
4. [Requesting Special Permissions](#requesting-special-permissions)
5. [Rationale and Don't Ask Again](#rationale-and-dont-ask-again)
6. [Version-Specific Handling](#version-specific-handling)
7. [Android 16 (API 36) Permission Changes](#android-16-api-36-permission-changes)
8. [Testing](#testing)

## Where Permissions Live

- Declare permissions in the **app** module `AndroidManifest.xml`.
- Feature modules should expose capabilities (e.g., "requires camera") and the app decides whether to include and request them.

```xml
<!-- app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
<uses-permission android:name="android.permission.READ_MEDIA_VISUAL_USER_SELECTED" />
```

## Common Permission Sets

### Network (Normal)
Auto-granted when declared. No runtime request needed.

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### Camera (Runtime)

```xml
<uses-permission android:name="android.permission.CAMERA" />
```

### Media Access (Runtime, Android 13+)
Prefer Photo Picker when possible to avoid permission requests entirely.

```xml
<!-- Android 14+ partial access -->
<uses-permission android:name="android.permission.READ_MEDIA_VISUAL_USER_SELECTED" />

<!-- Android 13+ full access -->
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
<uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />

<!-- Legacy storage (Android 12 and below) -->
<uses-permission
    android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
```

### Notifications (Runtime, Android 13+)

```xml
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

**Note:** See `references/android-notifications.md` for notification implementation patterns, channels, and foreground services.

### Location (Runtime)

```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

## Requesting Runtime Permissions in Compose

Use `rememberLauncherForActivityResult` with `ActivityResultContracts.RequestPermission` or `RequestMultiplePermissions`.

**Note**: Accompanist library is deprecated. Use native Compose APIs shown below.

### Single Permission (Camera)

Place permission logic in Screen composables (not ViewModels) following our architecture.

```kotlin
@Composable
fun CameraScreen(
    onPhotoCaptured: (Bitmap) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }
    
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            // Open camera
        } else {
            showRationale = true
        }
    }
    
    Column(modifier = modifier.fillMaxSize()) {
        if (showRationale) {
            PermissionRationaleCard(
                title = "Camera Access Required",
                description = "We need camera access to take photos.",
                onDismiss = { showRationale = false },
                onOpenSettings = { openAppSettings(context) }
            )
        }
        
        Button(
            onClick = {
                when (PackageManager.PERMISSION_GRANTED) {
                    ContextCompat.checkSelfPermission(
                        context,
                        Manifest.permission.CAMERA
                    ) -> {
                        // Open camera
                    }
                    else -> launcher.launch(Manifest.permission.CAMERA)
                }
            }
        ) {
            Text("Take Photo")
        }
    }
}
```

### Multiple Permissions (Media Access)

```kotlin
@Composable
fun MediaPickerScreen(
    onMediaSelected: (Uri) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }
    
    val permissions = buildMediaPermissions()
    
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissionsMap ->
        when {
            permissionsMap.values.any { it } -> {
                // At least one permission granted
            }
            else -> showRationale = true
        }
    }
    
    Button(
        onClick = {
            val hasPermission = permissions.any { permission ->
                ContextCompat.checkSelfPermission(
                    context,
                    permission
                ) == PackageManager.PERMISSION_GRANTED
            }
            
            if (hasPermission) {
                // Open media picker
            } else {
                launcher.launch(permissions.toTypedArray())
            }
        }
    ) {
        Text("Choose Media")
    }
}
```

### Notifications Permission (Android 13+)

Request notifications contextually after user performs an action that benefits from notifications.

```kotlin
@Composable
fun NotificationSettingsScreen(
    viewModel: NotificationViewModel = hiltViewModel(),
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        viewModel.onNotificationPermissionResult(isGranted)
    }
    
    Column(modifier = modifier.fillMaxSize()) {
        SwitchRow(
            title = "Enable Notifications",
            description = "Get notified about important updates",
            checked = uiState.notificationsEnabled,
            onCheckedChange = { enabled ->
                if (enabled && Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    when (PackageManager.PERMISSION_GRANTED) {
                        ContextCompat.checkSelfPermission(
                            context,
                            Manifest.permission.POST_NOTIFICATIONS
                        ) -> viewModel.enableNotifications()
                        else -> launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
                    }
                } else {
                    viewModel.toggleNotifications(enabled)
                }
            }
        )
    }
}
```

### Photo Picker (Preferred for Media on Android 13+)

Photo Picker avoids permission requests entirely. Use this instead of requesting media permissions when possible.

**Note:** Photo Picker requires API 33+. For API 24-32, use the legacy media permission approach (READ_EXTERNAL_STORAGE).

```kotlin
@Composable
fun PhotoPickerScreen(
    onPhotoSelected: (Uri) -> Unit,
    modifier: Modifier = Modifier
) {
    // Photo Picker requires API 33+ (Android 13+)
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val launcher = rememberLauncherForActivityResult(
            contract = ActivityResultContracts.PickVisualMedia()
        ) { uri ->
            uri?.let { onPhotoSelected(it) }
        }
        
        Button(
            onClick = {
                launcher.launch(
                    PickVisualMediaRequest(
                        mediaType = ActivityResultContracts.PickVisualMedia.ImageOnly
                    )
                )
            }
        ) {
            Text("Choose Photo")
        }
    } else {
        // Fallback for API < 33: Use legacy image picker with READ_EXTERNAL_STORAGE permission
        val launcher = rememberLauncherForActivityResult(
            contract = ActivityResultContracts.GetContent()
        ) { uri ->
            uri?.let { onPhotoSelected(it) }
        }
        
        Button(
            onClick = { launcher.launch("image/*") }
        ) {
            Text("Choose Photo")
        }
    }
}

// For multiple photos
@Composable
fun MultiPhotoPickerScreen(
    onPhotosSelected: (List<Uri>) -> Unit,
    maxItems: Int = 10,
    modifier: Modifier = Modifier
) {
    // Photo Picker requires API 33+ (Android 13+)
    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val launcher = rememberLauncherForActivityResult(
            contract = ActivityResultContracts.PickMultipleVisualMedia(maxItems)
        ) { uris ->
            if (uris.isNotEmpty()) {
                onPhotosSelected(uris)
            }
        }
        
        Button(
            onClick = {
                launcher.launch(
                    PickVisualMediaRequest(
                        mediaType = ActivityResultContracts.PickVisualMedia.ImageOnly
                    )
                )
            }
        ) {
            Text("Choose Photos")
        }
    } else {
        // Fallback for API < 33: Use legacy multiple files picker
        val launcher = rememberLauncherForActivityResult(
            contract = ActivityResultContracts.OpenMultipleDocuments()
        ) { uris ->
            if (uris.isNotEmpty()) {
                onPhotosSelected(uris)
            }
        }
        
        Button(
            onClick = { launcher.launch(arrayOf("image/*")) }
        ) {
            Text("Choose Photos")
        }
    }
}
```

## Requesting Special Permissions

Special permissions (like exact alarms, all files access) require users to grant them from system settings. Apps cannot show a permission dialog; instead, they redirect users to the settings page.

### Exact Alarms (Special Permission)

```kotlin
@Composable
fun ScheduleEmailScreen(
    viewModel: EmailViewModel = hiltViewModel(),
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val alarmManager = remember { context.getSystemService<AlarmManager>()!! }
    var showRationale by remember { mutableStateOf(false) }
    
    val settingsLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        // Check permission on return
    }
    
    LaunchedEffect(Unit) {
        // Check permission on resume
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (!alarmManager.canScheduleExactAlarms()) {
                showRationale = true
            }
        }
    }
    
    if (showRationale) {
        AlertDialog(
            onDismissRequest = { showRationale = false },
            title = { Text("Exact Alarm Permission Required") },
            text = { 
                Text("To send your email at the exact time you choose, we need permission to schedule exact alarms. Tap 'Grant' to open settings.") 
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showRationale = false
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                            settingsLauncher.launch(
                                Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM)
                            )
                        }
                    }
                ) {
                    Text("Grant")
                }
            },
            dismissButton = {
                TextButton(onClick = { showRationale = false }) {
                    Text("Cancel")
                }
            }
        )
    }
    
    Button(
        onClick = {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                if (alarmManager.canScheduleExactAlarms()) {
                    viewModel.scheduleEmail()
                } else {
                    showRationale = true
                }
            } else {
                viewModel.scheduleEmail()
            }
        }
    ) {
        Text("Schedule Email")
    }
}
```

### All Files Access (Special Permission)

```kotlin
@Composable
fun FileManagerScreen(
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var showRationale by remember { mutableStateOf(false) }
    
    val settingsLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.StartActivityForResult()
    ) {
        // Check permission on return
    }
    
    if (showRationale) {
        AlertDialog(
            onDismissRequest = { showRationale = false },
            title = { Text("All Files Access Required") },
            text = { 
                Text("To manage all your files, we need access to all storage. Tap 'Grant' to open settings and enable 'All files access'.") 
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showRationale = false
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                            settingsLauncher.launch(
                                Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION).apply {
                                    data = Uri.fromParts("package", context.packageName, null)
                                }
                            )
                        }
                    }
                ) {
                    Text("Grant")
                }
            },
            dismissButton = {
                TextButton(onClick = { showRationale = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
```

## Rationale and Don't Ask Again

### Best Practices
- Request permissions **contextually** (when user taps "Take Photo", not on app startup).
- Show rationale explaining **why** the permission is needed and **what benefits** it provides.
- If user denies multiple times, guide them to settings.
- Track denial count in ViewModel/SavedStateHandle (not with `shouldShowRationale` which is unreliable).

### Open App Settings

```kotlin
fun openAppSettings(context: Context) {
    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.fromParts("package", context.packageName, null)
    }
    context.startActivity(intent)
}
```

### Rationale Dialog Component

```kotlin
@Composable
fun PermissionRationaleCard(
    title: String,
    description: String,
    onDismiss: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium
            )
            Text(
                text = description,
                style = MaterialTheme.typography.bodyMedium
            )
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                TextButton(onClick = onDismiss) {
                    Text("Not Now")
                }
                Button(onClick = onOpenSettings) {
                    Text("Open Settings")
                }
            }
        }
    }
}
```

### Track Denial Count (Proper Pattern)

```kotlin
@HiltViewModel
class CameraViewModel @Inject constructor(
    private val savedStateHandle: SavedStateHandle
) : ViewModel() {
    private var denialCount: Int
        get() = savedStateHandle["camera_denial_count"] ?: 0
        set(value) { savedStateHandle["camera_denial_count"] = value }
    
    fun onPermissionDenied() {
        denialCount++
    }
    
    fun shouldShowSettings(): Boolean = denialCount >= 2
}
```

## Version-Specific Handling

### Media Permissions (Android 14+ Partial Access)

Android 14 introduced partial media access where users can grant access to selected photos only.

```kotlin
fun buildMediaPermissions(): List<String> = when {
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE -> listOf(
        Manifest.permission.READ_MEDIA_IMAGES,
        Manifest.permission.READ_MEDIA_VIDEO,
        Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED
    )
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU -> listOf(
        Manifest.permission.READ_MEDIA_IMAGES,
        Manifest.permission.READ_MEDIA_VIDEO
    )
    else -> listOf(
        Manifest.permission.READ_EXTERNAL_STORAGE
    )
}

fun checkMediaPermission(context: Context): MediaAccessLevel = when {
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE -> {
        when {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_MEDIA_IMAGES
            ) == PackageManager.PERMISSION_GRANTED -> MediaAccessLevel.Full
            
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_MEDIA_VISUAL_USER_SELECTED
            ) == PackageManager.PERMISSION_GRANTED -> MediaAccessLevel.Partial
            
            else -> MediaAccessLevel.None
        }
    }
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU -> {
        if (ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_MEDIA_IMAGES
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            MediaAccessLevel.Full
        } else {
            MediaAccessLevel.None
        }
    }
    else -> {
        if (ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.READ_EXTERNAL_STORAGE
            ) == PackageManager.PERMISSION_GRANTED
        ) {
            MediaAccessLevel.Full
        } else {
            MediaAccessLevel.None
        }
    }
}

enum class MediaAccessLevel {
    Full, Partial, None
}
```

### Notification Permissions (Android 13+)

```kotlin
fun shouldRequestNotificationPermission(context: Context): Boolean {
    return Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
        ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.POST_NOTIFICATIONS
        ) != PackageManager.PERMISSION_GRANTED
}
```

## Android 16 (API 36) Permission Changes

### Health & Fitness Permissions

Apps targeting API 36 must migrate from `BODY_SENSORS` / `BODY_SENSORS_BACKGROUND` to granular `android.permissions.health` permissions. This affects heart rate, SpO2, and skin temperature sensors.

```xml
<!-- Before (API 35 and below) -->
<uses-permission android:name="android.permission.BODY_SENSORS" />
<uses-permission android:name="android.permission.BODY_SENSORS_BACKGROUND" />

<!-- After (API 36+) -->
<uses-permission android:name="android.permission.health.READ_HEART_RATE" />
<uses-permission android:name="android.permission.health.READ_OXYGEN_SATURATION" />
<uses-permission android:name="android.permission.health.READ_SKIN_TEMPERATURE" />
<uses-permission android:name="android.permission.health.READ_HEALTH_DATA_IN_BACKGROUND" />
```

**Important:** Mobile apps using these granular health permissions must declare an activity to display the app's privacy policy (same requirement as Health Connect). Failure to provide this rationale will result in the permission being revoked.

```kotlin
fun buildHealthPermissions(): List<String> = when {
    Build.VERSION.SDK_INT >= 36 -> listOf(
        "android.permission.health.READ_HEART_RATE",
        "android.permission.health.READ_OXYGEN_SATURATION"
    )
    else -> listOf(
        Manifest.permission.BODY_SENSORS
    )
}
```

### Local Network Permission

Android 16 introduces local network access protection. Apps that access devices on the local network (mDNS, SSDP, NsdManager, raw sockets to LAN addresses) will need user permission.

**Current state (API 36 opt-in phase):**
- Feature is opt-in for testing; enforcement begins in a future release
- Declare `NEARBY_WIFI_DEVICES` permission for local network access
- All networking APIs are affected (sockets, OkHttp, Cronet, etc.)

```xml
<uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES" />
```

**What is affected:**
- Outgoing/incoming TCP connections to LAN addresses
- UDP unicast, multicast, and broadcast to/from LAN
- mDNS and SSDP service discovery
- Any traffic to RFC1918 addresses (10.x, 172.16.x, 192.168.x), link-local, and multicast

**Exceptions:**
- DNS traffic to a local DNS server (port 53)
- Normal internet traffic is unaffected

```kotlin
@Composable
fun LocalNetworkPermissionRequest(
    onPermissionResult: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        onPermissionResult(isGranted)
    }

    Button(
        onClick = {
            launcher.launch(Manifest.permission.NEARBY_WIFI_DEVICES)
        },
        modifier = modifier
    ) {
        Text("Grant Network Access")
    }
}
```

### App-Owned Photos Pre-Selection

When targeting API 36, the photo picker pre-selects photos owned by the requesting app. Users can deselect these to revoke access. No code changes are needed, but be aware that users may deselect previously accessible photos.

## Testing

### Grant Permission in Tests

```kotlin
@get:Rule
val permissionRule = GrantPermissionRule.grant(
    Manifest.permission.CAMERA,
    Manifest.permission.POST_NOTIFICATIONS
)

@Test
fun testCameraFeature() {
    // Permission automatically granted
    composeTestRule.setContent {
        CameraScreen(onPhotoCaptured = {})
    }
    
    composeTestRule.onNodeWithText("Take Photo").performClick()
}
```

### Test Permission Denial Flow

```kotlin
@Test
fun testPermissionDenialShowsRationale() {
    composeTestRule.setContent {
        CameraScreen(onPhotoCaptured = {})
    }
    
    composeTestRule.onNodeWithText("Take Photo").performClick()
    
    // Simulate denial
    composeTestRule.onNodeWithText("Camera Access Required").assertIsDisplayed()
}
```

### Performance Checks (Macrobenchmark)
If permission flows impact startup or navigation timing, use Macrobenchmark to measure. See `references/android-performance.md` for setup.

## References
- Request runtime permissions: https://developer.android.com/training/permissions/requesting
- Request special permissions: https://developer.android.com/training/permissions/requesting-special
- Photo Picker: https://developer.android.com/training/data-storage/shared/photopicker
- App permissions best practices: https://developer.android.com/training/permissions/best-practices
