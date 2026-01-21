# Android Runtime Permissions

Practical, Compose-first patterns for requesting permissions in an auth-focused app. This guide follows modern Android best practices and our modular architecture.

## Table of Contents
1. [Where Permissions Live](#where-permissions-live)
2. [Common Permission Sets](#common-permission-sets)
3. [Requesting Permissions in Compose](#requesting-permissions-in-compose)
4. [Rationale and "Don't Ask Again"](#rationale-and-dont-ask-again)
5. [Version-Specific Handling](#version-specific-handling)
6. [Testing](#testing)

## Where Permissions Live

- Declare permissions in the **app** module `AndroidManifest.xml`.
- Feature modules should expose capabilities (e.g., "requires camera") and the app decides whether to include and request them.

```xml
<!-- app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

## Common Permission Sets

### Network (Normal)
Auto-granted when declared. No runtime request needed.

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### Media + Camera (Runtime)
Use for QR login or profile photo capture.

```xml
<!-- Camera -->
<uses-permission android:name="android.permission.CAMERA" />

<!-- Media access (Android 13+) -->
<uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

<!-- Legacy storage (Android 12L and below) -->
<uses-permission
    android:name="android.permission.READ_EXTERNAL_STORAGE"
    android:maxSdkVersion="32" />
```

### Notifications (Android 13+)

```xml
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
```

### Location (Runtime)

```xml
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
```

## Requesting Permissions in Compose

Prefer the Activity Result APIs. No extra dependencies required.

### Single Permission (QR Login)

```kotlin
@Composable
fun QrLoginButton(
    onOpenScanner: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var hasRequested by rememberSaveable { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasRequested = true
        if (granted) onOpenScanner()
    }

    Button(
        modifier = modifier,
        onClick = {
            if (ContextCompat.checkSelfPermission(
                    context,
                    Manifest.permission.CAMERA
                ) == PackageManager.PERMISSION_GRANTED
            ) {
                onOpenScanner()
            } else {
                launcher.launch(Manifest.permission.CAMERA)
            }
        }
    ) {
        Text("Scan QR Code")
    }
}
```

### Multiple Permissions (Profile Photo Upload)

```kotlin
@Composable
fun ProfilePhotoAccess(
    onOpenPicker: () -> Unit,
    onShowRationale: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    val activity = context as? Activity
    val permissions = remember { buildMediaPermissions() }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { results ->
        if (results.values.all { it }) onOpenPicker()
    }

    Button(
        modifier = modifier,
        onClick = {
            val allGranted = permissions.all {
                ContextCompat.checkSelfPermission(context, it) ==
                    PackageManager.PERMISSION_GRANTED
            }
            if (allGranted) {
                onOpenPicker()
                return@Button
            }

            val shouldShowRationale = activity != null && permissions.any {
                ActivityCompat.shouldShowRequestPermissionRationale(activity, it)
            }
            if (shouldShowRationale) onShowRationale() else launcher.launch(permissions.toTypedArray())
        }
    ) {
        Text("Choose Profile Photo")
    }
}
```

## Rationale and "Don't Ask Again"

- Request permissions **contextually** (e.g., when the user taps "Scan QR Code").
- If the user denies and "Don't ask again" is selected, guide them to Settings.

```kotlin
@Composable
fun CameraAccessGate(
    onOpenScanner: () -> Unit,
    onOpenSettings: () -> Unit
) {
    val context = LocalContext.current
    val activity = context as? Activity
    var hasRequested by rememberSaveable { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasRequested = true
        if (granted) onOpenScanner()
    }

    val hasPermission = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.CAMERA
    ) == PackageManager.PERMISSION_GRANTED

    val shouldShowRationale = activity != null &&
        ActivityCompat.shouldShowRequestPermissionRationale(activity, Manifest.permission.CAMERA)

    when {
        hasPermission -> onOpenScanner()
        shouldShowRationale -> AuthPermissionRationale(onAllow = {
            launcher.launch(Manifest.permission.CAMERA)
        })
        hasRequested -> AuthPermissionSettingsPrompt(onOpenSettings = onOpenSettings)
        else -> AuthPermissionRequest(onRequest = {
            launcher.launch(Manifest.permission.CAMERA)
        })
    }
}
```

To open app settings:

```kotlin
fun openAppSettings(context: Context) {
    val intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS).apply {
        data = Uri.fromParts("package", context.packageName, null)
    }
    context.startActivity(intent)
}
```

## Version-Specific Handling

- Prefer the **Photo Picker** (`ActivityResultContracts.PickVisualMedia`) on Android 13+ to avoid storage permissions.
- Use `READ_MEDIA_IMAGES/VIDEO` on Android 13+, and `READ_EXTERNAL_STORAGE` on Android 12L and below.

```kotlin
fun buildMediaPermissions(): List<String> = when {
    Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU -> listOf(
        Manifest.permission.READ_MEDIA_IMAGES
    )
    Build.VERSION.SDK_INT <= Build.VERSION_CODES.S_V2 -> listOf(
        Manifest.permission.READ_EXTERNAL_STORAGE
    )
    else -> emptyList()
}
```

## Testing

Use `GrantPermissionRule` for instrumentation tests and keep permission logic in small helpers.

```kotlin
@get:Rule
val permissionRule = GrantPermissionRule.grant(Manifest.permission.CAMERA)
```

For additional testing patterns, see `references/testing.md`.
