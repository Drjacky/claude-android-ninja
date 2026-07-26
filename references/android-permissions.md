# Android Runtime Permissions

Compose-first runtime permission patterns. Declare in the `:app` manifest only; request contextually from Screen composables. All code must align with `references/kotlin-patterns.md` and `references/compose-patterns.md`.

## Table of Contents
1. [Where Permissions Live](#where-permissions-live)
2. [Common Permission Sets](#common-permission-sets)
3. [Requesting Runtime Permissions in Compose](#requesting-runtime-permissions-in-compose)
4. [Requesting Special Permissions](#requesting-special-permissions)
5. [Rationale and Don't Ask Again](#rationale-and-dont-ask-again)
6. [Version-Specific Handling](#version-specific-handling)
7. [Android 16 (API 36) Permission Changes](#android-16-api-36-permission-changes)
8. [Android 17 (API 37) Permission Changes](#android-17-api-37-permission-changes) - [local network](#local-network-access-api-37), [location privacy](#android-17-location-privacy), [location button](#system-location-button-one-time-precise-access-no-permission)
9. [Testing](#testing)

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
**Required:** use the Photo Picker when UX allows picking without `READ_MEDIA_*`; it avoids those runtime permissions on supported APIs.

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

Notification implementation, channels, and foreground services: `references/android-notifications.md`.

### Location (Runtime)

```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
```

API 37-specific routing (approximate-first, background, FGS): [Android 17 location privacy](#android-17-location-privacy).

### Contact picker (privacy-first)

**Use when:** the user selects one or more contacts to share (invite, tag, forward) without `READ_CONTACTS`.

**Forbidden:** `READ_CONTACTS` when the system contact picker satisfies the UX.

Android 17 (API 37) picker: launch **`ContactsPickerSessionContract.ACTION_PICK_CONTACTS`** through the **`StartActivityForResult`** contract, declaring which data fields you need. The result is a **session URI** granting temporary read access to only the selected data. Official flow: [Contact picker (Android 17)](https://developer.android.com/about/versions/17/features/contact-picker).

Do **not** use `ActivityResultContracts.PickContact()` for this - it cannot carry the data-field extras and yields a single legacy contact URI.

Verify the requested-fields extra name against the installed SDK before relying on it: the platform documentation refers to it both as `ContactsPickerSessionContract.EXTRA_REQUESTED_DATA_FIELDS` (prose) and `EXTRA_PICK_CONTACTS_REQUESTED_DATA_FIELDS` (samples). Use whichever the `android.provider.ContactsPickerSessionContract` class on `compileSdk` 37 actually declares; do not hard-code the string literal.

```kotlin
import android.provider.ContactsContract
import android.provider.ContactsContract.CommonDataKinds.Email
import android.provider.ContactsContract.CommonDataKinds.Phone
import android.provider.ContactsPickerSessionContract

@Composable
fun ContactPickButton(
    onContactsPicked: (Uri) -> Unit,
    modifier: Modifier = Modifier
) {
    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            // Session URI: query it, then persist what you need before the grant expires.
            result.data?.data?.let(onContactsPicked)
        }
    }

    Button(
        onClick = {
            val requestedFields = arrayListOf(
                Phone.CONTENT_ITEM_TYPE,
                Email.CONTENT_ITEM_TYPE,
            )
            val intent = Intent(ContactsPickerSessionContract.ACTION_PICK_CONTACTS).apply {
                putExtra(ContactsContract.Contacts.EXTRA_USE_SYSTEM_CONTACTS_PICKER, true)
                putStringArrayListExtra(
                    ContactsPickerSessionContract.EXTRA_PICK_CONTACTS_REQUESTED_DATA_FIELDS,
                    requestedFields
                )
                // Multi-select is opt-in
                putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true)
                putExtra(ContactsPickerSessionContract.EXTRA_PICK_CONTACTS_SELECTION_LIMIT, 5)
                // true = only show contacts having every requested field
                putExtra(ContactsPickerSessionContract.EXTRA_PICK_CONTACTS_MATCH_ALL_DATA_FIELDS, false)
            }
            launcher.launch(intent)
        },
        modifier = modifier
    ) {
        Text("Choose contacts")
    }
}
```

Reading the session URI - the cursor follows the `ContactsContract.Data` schema, one row per data item:

```kotlin
private suspend fun readPickedContacts(
    sessionUri: Uri,
    context: Context
): List<PickedContact> = withContext(Dispatchers.IO) {
    val projection = arrayOf(
        ContactsContract.Contacts.LOOKUP_KEY,
        ContactsContract.Contacts.DISPLAY_NAME_PRIMARY,
        ContactsContract.Data.MIMETYPE,
        ContactsContract.Data.DATA1,
    )

    // Session URIs reject custom selection / selectionArgs - pass null for both.
    context.contentResolver.query(sessionUri, projection, null, null, null)?.use { cursor ->
        // Group rows by LOOKUP_KEY: one contact yields several rows (each phone, each email).
        buildPickedContacts(cursor)
    } ?: emptyList()
}
```

Required:

- **Request the narrowest field set.** The picker filters out contacts lacking the requested fields, which is both better UX and less data.
- **Group rows by `ContactsContract.Contacts.LOOKUP_KEY`** - a contact with three phone numbers returns three rows.
- **Persist what you need immediately.** The grant is temporary and does not survive process death.
- Pass `null` for `selection` / `selectionArgs`; supplying them **throws**.

Do not read account metadata from the result - it is stripped to prevent fingerprinting. At target SDK 37, `ACCOUNT_NAME` / `ACCOUNT_TYPE` are also removed from `ContactsContract.Data` generally ([migration.md → Contacts provider tightening](migration.md#contacts-provider-tightening-target-sdk-37)).

**Backward compatibility:** at target SDK 37 the system automatically upgrades an existing `Intent.ACTION_PICK` to the new picker UI, so a legacy call site is not broken - it just does not get multi-field requests, profile switching, or the single session URI. To trial the new UI while still targeting a lower SDK, add `EXTRA_USE_SYSTEM_CONTACTS_PICKER` to your existing `ACTION_PICK` intent.

## Requesting Runtime Permissions in Compose

Use `rememberLauncherForActivityResult` with `ActivityResultContracts.RequestPermission` or `RequestMultiplePermissions`.

Accompanist permission helpers are deprecated. Use the native Compose APIs below.

### Single Permission (Camera)

Place permission logic in Screen composables, never in ViewModels.

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

### Photo Picker (Android 13+)

Start here for **permission-free** picks. For a single router that also lists document contracts, FileProvider, URI grants, and sharesheet targets, see [android-media.md → Picking media and documents](android-media.md#picking-media-and-documents).

Photo Picker avoids permission requests entirely. Use this instead of requesting media permissions when possible.

Photo Picker requires API 33+. On API 24-32, fall back to the legacy media permission flow (`READ_EXTERNAL_STORAGE`).

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

### Embedded Photo Picker

**Use when:** the picker surface must render inside app layout (sheet, pane, or inline slot) instead of a full-screen system sheet.

**Use when:** full-screen Photo Picker is enough: stay on [Photo Picker (Android 13+)](#photo-picker-android-13) with `PickVisualMedia`.

Required: follow [Embedded photo picker](https://developer.android.com/training/data-storage/shared/photopicker#embedded-photo-picker) for API level gates and `ActivityResult` wiring; keep the same permission-free goal as standalone Photo Picker on supported releases.

Forbidden: `READ_MEDIA_*` when embedded or full-screen Photo Picker covers the UX on that API level.

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

### Rules

Required:
- Request only inside the user action that needs the capability (e.g., the "Take Photo" tap). Never on app startup or screen entry.
- Show a rationale dialog before the system prompt when `shouldShowRequestPermissionRationale()` returns `true`.
- After denial-then-rationale-then-denial, route to system Settings via `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`.
- Track denial count in `SavedStateHandle` (or a repository). `shouldShowRequestPermissionRationale` alone is unreliable across process death.

Forbidden:
- Requesting batches of unrelated permissions in a single launcher call.
- Re-prompting in a loop after the user denies - wait for the next contextual action.

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

**Required:** Apps declaring granular `android.permission.health.*` reads must register an activity that renders the privacy policy (Health Connect parity). Missing that activity yields revocation of health permissions.

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

### App-Owned Photos Pre-Selection

When targeting API 36, the photo picker pre-selects photos owned by the requesting app. Users can deselect these to revoke access. No code changes are needed, but be aware that users may deselect previously accessible photos.

## Android 17 (API 37) Permission Changes

### Local network access (API 37)

At **target SDK 37** local network access is blocked by default and gated by the runtime permission **`ACCESS_LOCAL_NETWORK`** (in the `NEARBY_DEVICES` permission group). Android 16 only had a temporary opt-in phase that reused `NEARBY_WIFI_DEVICES`; that is not the API to target now.

**What is affected:** every networking API - platform and managed sockets, OkHttp, Cronet - for TCP connect/accept, UDP unicast/multicast/broadcast, and `.local` mDNS resolution. WebViews inherit the host app's state.

**Exceptions:** a DNS server on the local network at port 53, and apps using the Output Switcher as an in-app picker. Ordinary internet traffic is unaffected.

**Failure modes are quiet:** UDP fails with `EPERM`, TCP simply times out. From native code, `android_getnetworkblockedreason(int sockFd)` returns `ANDROID_NETWORK_BLOCKED_REASON_LNP`.

#### Prefer a system picker (no permission)

Required: try this first. A system-mediated picker returns connectable addresses without any local-network permission.

```kotlin
// Addresses from NsdServiceInfo.getHostAddresses() are connectable without ACCESS_LOCAL_NETWORK.
val request = DiscoveryRequest.Builder("_http._tcp")
    .setFlags(DiscoveryRequest.FLAG_SHOW_PICKER)
    .build()

nsdManager.registerServiceInfoCallback(request, executor, callback)
```

For media, the Cast **output switcher** covers device selection with no permission.

#### Declaring the permission

Use only when a picker cannot express the feature (for example scanning an arbitrary subnet).

```xml
<uses-permission android:name="android.permission.ACCESS_LOCAL_NETWORK" />
```

```kotlin
@Composable
fun LocalNetworkPermissionRequest(
    onPermissionResult: (Boolean) -> Unit,
    modifier: Modifier = Modifier
) {
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        onPermissionResult(isGranted)
    }

    Button(
        onClick = { launcher.launch(Manifest.permission.ACCESS_LOCAL_NETWORK) },
        modifier = modifier
    ) {
        Text("Allow local network access")
    }
}
```

**Forbidden:** declaring or requesting `ACCESS_LOCAL_NETWORK` while `targetSdk` is 36 or lower - local network access is implicitly granted via `INTERNET` there, and requesting it adds a permission prompt for nothing.

Already-granted `NEARBY_DEVICES` permissions (for example Bluetooth) pre-grant this one. The group also gets a request-reset counter, so a prior group denial does not permanently consume the request.

Testing the restriction on Android 16 before you retarget:

```bash
adb shell am compat enable RESTRICT_LOCAL_NETWORK <package>
adb reboot                 # required for the change to take effect
# revert with: adb shell am compat disable RESTRICT_LOCAL_NETWORK <package>
```

Cross-links: [migration.md → Local network access (target SDK 37)](migration.md#local-network-access-target-sdk-37); Cast and media device selection in [android-media.md](android-media.md).

### Android 17 location privacy

Required at target SDK 37: request the narrowest location tier the feature needs; justify background and precise access in UX copy and Play declarations.

| Need | Permission / API | Rule |
|------|------------------|------|
| City-level or coarse map pin | `ACCESS_COARSE_LOCATION` only | Do not request `ACCESS_FINE_LOCATION` unless the feature fails with coarse |
| Turn-by-turn, geofence edge, sub-100 m accuracy | `ACCESS_FINE_LOCATION` | Pair with in-use rationale; drop to coarse when the screen leaves the map |
| Location while app is not visible | `ACCESS_BACKGROUND_LOCATION` | Separate runtime step after foreground grant; use only with a visible ongoing use case |
| Continuous background fixes | Foreground service with type `location` | Declare FGS permission and show a user-visible notification; see [android-notifications.md](android-notifications.md) |
| Periodic or deferrable work | WorkManager + last-known or fused one-shot | Forbidden: FGS or background permission for work that fits deferrable scheduling |

**Wrong:** request fine + background on first launch before the user starts a location-dependent action.

**Correct:** foreground coarse or fine in context, then background only after the user enables a feature that needs it.

### Coarse location is no longer a fixed grid

Android 17 replaces the static **2 km** coarse-location grid with a **population-density-dependent** area: sparsely populated regions get a larger area to keep the privacy guarantee consistent. Consequences for code that assumed a constant:

- Do not hard-code a 2 km radius for uncertainty circles, cache keys, or "is the user near X" checks derived from coarse fixes.
- Read the accuracy off the `Location` object (`Location.getAccuracy()`) rather than assuming a bound.
- A coarse fix in a rural area can now be far less precise than the same code saw on Android 16 - verify any distance threshold that gates UI.

### System location button (one-time precise access, no permission)

**Status: prerelease.** `androidx.core.locationbutton` is at **`1.0.0-alpha01`** with no stable release, so it is **not** in `assets/libs.versions.toml.template`. Do not add it to a production catalog without an explicit decision recorded per [dependencies.md → Pinned prerelease required for feature parity](dependencies.md#pinned-prerelease-required-for-feature-parity).

**Use when:** a single user action needs precise location and you would otherwise request `ACCESS_FINE_LOCATION` permanently - "locate me" on a map, autofill an address, share current position once.

The user taps a system-rendered button; the app receives session-scoped precise location with **no runtime permission and no prompt**, gated by `Manifest.permission.USE_LOCATION_BUTTON`. Because the system renders and validates the button, consent is tied to the tap.

| Artifact                                                | Use                                  |
|---------------------------------------------------------|--------------------------------------|
| `androidx.core.locationbutton:locationbutton`            | View-based                            |
| `androidx.core.locationbutton:locationbutton-compose`    | Compose                               |
| `androidx.core.locationbutton:locationbutton-testing`    | Test support                          |

Customization is deliberately bounded: background/icon colors, outline, size, shape, and a label chosen from a predefined list. The location **icon is mandatory and non-customizable**, and font size is system-managed for accessibility - do not attempt to restyle either.

The Jetpack library **falls back to the standard permission prompt automatically on Android 16 and below**, so the call site does not need a version branch.

**Forbidden:** using the location button as a substitute for `ACCESS_BACKGROUND_LOCATION` or continuous tracking - it is per-session, action-scoped access only.

### Location access transparency (Android 17)

A persistent indicator now appears whenever a non-system app accesses location, matching the existing microphone/camera treatment, and users can attribute and revoke from a "Recent app use" dialog. Practical effect: silent or speculative location reads become visible to the user, so remove background polling that is not tied to a feature the user turned on.

Cross-links: [android-performance.md → Excessive partial wake locks](android-performance.md#excessive-partial-wake-locks-play-vitals-core-metric) for wake-lock substitutes; [migration.md → Android 17 location privacy](migration.md#android-17-location-privacy); platform summary: [Redefining location privacy (Android 17)](https://developer.android.com/about/versions/17/behavior-changes-17).

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
- Embedded photo picker: https://developer.android.com/training/data-storage/shared/photopicker#embedded-photo-picker
- Contact picker (Android 17): https://developer.android.com/about/versions/17/features/contact-picker
- App permissions best practices: https://developer.android.com/training/permissions/best-practices
